# QC-Team：多模型学术作业质检工作流

QC-Team 是一个实验性的命令行质检骨架，把文献真实性核验、Claude 内容主审、Codex 证据复核和 MiniMax 报告整理串成一条可复用流程。

它关注的不是普通润色，而是更难发现、风险更高的问题：文献是否真实、引用是否支持当前论点、证据是否被过度外推，以及作业要求和交付物是否完整。

> 当前版本适合演示和内部试运行，不应替代人工学术判断，也不能自动宣布稿件“可提交”。

## 为什么做这个项目

直接让单个模型检查一篇作业，容易遇到两个问题：

- 模型可能把不存在的文献说得很像真的；
- 文献真实存在，也不代表它能支持稿件中的具体论点。

QC-Team 将两类任务分开处理：

- 可确定性查询的 DOI 存在性和 Crossref 元数据，交给程序；
- 需要语境判断的引用方向、论证质量和交付完整性，交给不同模型分工复核。

Crossref 返回“存在”只表示该 DOI 能查询到相应元数据，不等于引用方向已经正确，也不等于全文内容已经核验。

## 工作流程

```text
输入 TXT 稿件
     │
     ▼
Crossref DOI 核验 ──► reports/_refs_verified.json
     │
     ▼
Claude 主审（D1–D7）
     │
     ▼
Codex 复核主审结论和证据
     │
     ▼
MiniMax 整理最终报告
     │
     ▼
人工复核与决定
```

当前实现是单轮串联：Codex 会看到 Claude 的意见，MiniMax 会看到前两者的输出。因此它还不是真正的三方盲审，也没有实现“发现分歧 → 回到原始来源 → 多轮关闭异议”的循环。角色提示词要求保留不确定性，但程序结构本身尚未强制执行 2/2 放行门。

## 三个模型角色

| 角色 | 默认工具 | 主要职责 |
| --- | --- | --- |
| 主审 / Conductor | Claude Code | 审题、rubric 对齐、论证质量、引用方向和诚信边界 |
| 复核 / Evidence Engineer | Codex CLI | 复查文献元数据、引用方向、数据和定位，指出主审漏判或误判 |
| 整理 / Independent Checker | MiniMax API | 扫描格式与交付物，保留分歧并整理报告 |

角色规则保存在 [`roles/`](roles/) 中，可以独立维护和版本化。

## 环境要求

- Python 3.9 或更高版本；
- 已安装并登录的 [Claude Code](https://docs.anthropic.com/en/docs/claude-code)；
- 已安装并登录的 [Codex CLI](https://developers.openai.com/codex/cli/)；
- 可用的 MiniMax API Key、API 地址和模型名；
- 只有处理 Word 稿件时才需要 `python-docx`。

模型命令和 API 可能随版本变化。运行前建议先分别确认 `claude -p`、`codex exec` 和 MiniMax 接口可用。

## 快速开始

```bash
git clone https://github.com/wangfeifei-321/qc-team.git
cd qc-team
cp .env.example .env
```

编辑 `.env`，填写自己的 MiniMax 配置。不要把密钥写进代码、截图、Issue 或提交记录。

程序主入口接受 UTF-8 文本文件：

```bash
python3 qc.py "/绝对路径/稿件.txt"
```

如果稿件是 DOCX，先转换为 TXT：

```bash
python3 -m pip install python-docx
python3 scripts/docx2txt.py "/绝对路径/稿件.docx"
python3 qc.py "/绝对路径/稿件.txt"
```

文件路径含空格时，请用引号包住完整路径。

## 运行演示

```bash
python3 qc.py samples/demo_稿件样例.txt
```

该命令会调用外部模型/API，可能产生费用。演示稿件是虚构样例，故意包含可疑 DOI，用于观察核验流程。

输出写入 `reports/`，包括主审意见、复核意见、最终报告和 DOI 核验结果。该目录默认不会被 Git 跟踪。

## 质检范围

- D1：作业要求与 rubric 对齐；
- D2：文献真实性和元数据；
- D3：引用漂移、方向误用和过度外推；
- D4：无证据论断；
- D5：格式规范；
- D6：交付物完整性；
- D7：学术诚信与真实性风险。

## 目录结构

```text
qc-team/
├── qc.py                         # 主流程
├── roles/                        # 三个模型的角色与判断边界
├── scripts/
│   ├── docx2txt.py               # DOCX 转纯文本
│   └── verify_refs.py            # Crossref DOI 核验
├── samples/                      # 虚构演示稿件
├── reports/                      # 本地输出，不提交真实报告
├── .env.example                  # MiniMax 配置模板
└── 怎么用_看这个.md              # 中文操作说明
```

## 安全与隐私

- 不要提交真实学生稿件、客户资料、模型输出报告或 `.env`；
- `.gitignore` 已排除 `.env`、DOCX、真实 TXT 样本和 `reports/` 内容，但提交前仍应运行 `git status` 人工确认；
- 外部模型和 Crossref 会接收处理所必需的内容或标识符。使用前应确认所在机构的隐私、数据处理和学术诚信政策；
- 不要把自动报告当作事实终点。拿不到原文时，应保留 `EVIDENCE_UNAVAILABLE` 或人工复核标记。

## 已知限制

- 仅自动提取和核验文本中带 DOI 的文献；书籍、网页、无 DOI 论文需要另行核验；
- Crossref 元数据匹配不等于全文论点匹配；
- DOCX 转换只提取段落和表格文字，不保留图片、批注、脚注和复杂排版；
- 当前没有自动读取作业 brief/rubric，也没有保存完整证据链和文件 SHA-256；
- 当前没有多轮回源机制、并行盲审、自动重试或强制人工批准门；
- 模型输出具有随机性，角色固化可以提高一致性，但不能保证不同时间得到完全相同的结果。

## 路线图

- 将主审与复核改为基于同一原始材料的独立盲审；
- 增加结构化证据台账和逐项 2/2 状态门；
- 对分歧执行有限轮次的回源复核；
- 增加文件哈希、运行日志、失败重试和人工批准节点；
- 扩展无 DOI 文献与全文来源核验能力。

## 许可证

本仓库目前未附加开源许可证。公开可见不等于获得复制、修改、分发或商业使用授权；在许可证明确前，默认保留所有权利。

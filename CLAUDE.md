# QC-Team

三模型交叉核验的学术作业质检流水线。文献是否真实由程序走 Crossref 判定，引用方向与论证质量由三个不同厂商的模型分工复核。

## 前置条件

| 依赖 | 版本／要求 | 检查命令 |
|---|---|---|
| Python | 3.9 以上 | `python3 --version` |
| `claude` CLI | 已安装并登录 | `claude --version` |
| `codex` CLI | 已安装并登录 | `codex --version` |
| `python-docx` | 处理 `.docx` 稿件时必需 | `python3 -c "import docx"` |
| MiniMax API Key | 写在 `.env` 里 | `grep MINIMAX_API_KEY .env` |

## 安装

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env      # 然后在 .env 里填 MINIMAX_API_KEY / MINIMAX_API_URL / MINIMAX_MODEL
```

## 运行

```bash
python3 qc.py samples/demo_稿件样例.txt          # 跑内置样例
python3 qc.py "/绝对路径/稿件.docx"               # 跑真实稿件，.docx 会自动读正文和表格
./qc "/绝对路径/稿件.docx"                        # 等价的封装入口
```

路径含空格或中文时用引号包起来。产物落在 `reports/`，该目录被 `.gitignore` 排除。

## 测试

```bash
python3 -m unittest discover -s tests -v
```

## 两个入口，能力不同

| 入口 | 命令 | 状态机 | 闸门 | 首轮独立性 |
|---|---|---|---|---|
| legacy | `python3 qc.py <稿件>` | 无 | 无机械执行 | 否——复核拿到的 prompt 里带着主审答案 |
| audited | `python3 scripts/run_audited_qc.py <稿件>` | 有，`EvidenceRun` 强制五状态迁移 | 5 道，逐道要 evidence locator | 主审与复核首轮互不可见，只在整理阶段会合 |

引用运行结果时必须写清是哪个入口跑的。下面的架构图画的是 legacy 链路。

## 架构

```text
输入 .docx/.txt/.md
        │
        ▼
scripts/verify_refs.py ── Crossref 真实 API 核验 DOI ──► reports/_refs_verified.json   [闸门 1]
        │
        ▼
qc-conductor（claude -p）        主审 D1–D7          ──► reports/<稿件名>_1主审.md      [强核票 1/2]
        │
        ▼
qc-verifier（codex exec）        复核、挑主审的错（可见主审答案） ──► reports/<稿件名>_2复核.md [强核票 1/2]
        │
        ▼
qc-reporter（MiniMax HTTP API）  机械扫描 + 综合报告   ──► reports/<稿件名>_质检报告_<时间戳>.md  [闸门 3]
```

| 路径 | 作用 |
|---|---|
| `qc.py` | 编排器。读 `.env`、抽取稿件文本、按序调用四个环节、把 stdout 落盘 |
| `qc` | 一行 shell 封装，转调 `qc.py` |
| `.claude/agents/*.md` | 三个 Agent 定义。`qc.py` 用 `read_agent()` 剥掉 frontmatter 后当角色提示词；Claude Code 也能直接把它们当 subagent 调用 |
| `.claude/rules/agent-authority-contract.md` | 责权利契约：五状态机、三道闸门、放行权矩阵、受保护标注 |
| `.claude-plugin/plugin.json` | 插件清单，供 `claude plugin` 与静态校验工具识别 |
| `scripts/verify_refs.py` | 提取 DOI 并走 Crossref 核验，输出 `reports/_refs_verified.json` |
| `scripts/docx2txt.py` | 独立的 Word 转文本工具（`qc.py` 已内建同等能力，此脚本供手工排查使用） |
| `tests/test_qc.py` | 稿件读取、Agent 定义加载、环境检查的单元测试 |
| `samples/demo_稿件样例.txt` | 内置虚构样例，含一个故意植入的假 DOI |

## 修改本项目时的规则

- **改角色行为改 `.claude/agents/<slug>.md` 的正文，不要改 `qc.py` 里的 prompt 拼接。** 角色定义是单一事实来源，`qc.py` 只负责传递。
- **新增 Agent 必须同时在 `.claude/rules/agent-authority-contract.md` 的责权利矩阵里登记一行。** 未登记的角色没有放行权，等同于阻断性缺陷。
- **三个 Agent 都不声明 `Write` 或 `Edit`。** 产物由 `qc.py` 落盘，这样「谁写了什么」在文件系统层面唯一可追溯。
- **绝不把真实稿件、`.env`、`reports/` 里的内容提交进仓库。** 提交前跑一次 `git status --short` 确认。
- **改动后跑一次质量门**：`python3 -m unittest discover -s tests`。

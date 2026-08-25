---
marp: true
theme: default
paginate: true
---

# QC-Team

## 把上一个 agent team 升级成可审计的真实团队

**王彩迪** · 2026 年 8 月 25 日

> 本片凡是标 ✅ 的，都能在仓库里找到对应产物或命令输出；
> **还没跑出来的，标「未完成」，不标 ✅。**

<!--
本套幻灯片用 Marp CLI 从 Markdown 渲染，主题是可复用的 CSS：
marp presentation/slides.md --allow-local-files -o presentation/QC-Team.pptx
-->

---

## 解决的是什么真问题

留学作业质检真正的风险不在错别字，在两处最隐蔽的地方：

- **文献造假** —— 参考文献根本不存在。单个 AI 复查无效，它会幻觉出看似真实的假文献来附和提问者
- **引用漂移** —— 文献真实，但原文结论与稿件拿它支撑的论点方向相反

| 角色 | 由谁扮演 | 放行权 |
|---|---|---|
| `qc-conductor` 主审 | Claude | 强核票 1/2 |
| `qc-verifier` 复核 | Codex | 强核票 1/2 |
| `qc-reporter` 整理 | MiniMax | 无强核票，异议可阻断 |

选不同厂商的模型是刻意的：同一个模型跑三遍，盲区依旧。

---

## 责权利之一：一个 Agent 的一生只有五种状态

```
BLOCKED ──依赖齐了──▶ READY ──派发──▶ RUNNING ──产物已发布──▶ COMPLETED
   ▲                                     │
   └──────上游 FAILED 向下游传播──────── FAILED
```

每个状态的进入条件都写成**可机械判定**的：
`COMPLETED` = 子进程 exit code 为 0 **且**产物文件字节数大于 0。
状态由 `qc_evidence.py` 的 `EvidenceRun` 独占写入，不由 Agent 自报。

**三条硬规则**：① 依赖全部 COMPLETED 且产物可读才能进 RUNNING　② 读不到依赖就报 BLOCKED，不许自己重造　③ 上游 FAILED，下游一律 BLOCKED

---

## 责权利之二：闸门是许可制，「利」是被复用的资格

| 闸门 | 代码名 | 判据 |
|---|---|---|
| 1 来源 | `provenance` | 上游 DIP manifest 存在，或显式声明无上游 |
| 2 基线 | `baseline_integrity` | 稿件已冻结并记录 SHA-256 |
| 3 文献证据 | `reference_evidence` | 每个 DOI 都有 Crossref 结果，无一条留空 |
| 4 双强核 | `independent_dual_review` | 关键事实 2/2 一致，任一方 UNVERIFIED 即不通过 |
| 5 放行 | `release` | 八个板块齐全，且闸门 4 已通过 |

三个角色**都没有写文件的权限**，产物由编排器落盘，「谁写了什么」才唯一可追溯。
**「利」不是报酬，是被复用的资格**：产物可回溯的角色，下一次运行才会继续加载它。

---

## 本周升级：定义、单测、实跑不能混为一谈

「写下来了」「单元测试验证过」「真实跑过一次」是三件事。

| 项目 | 已定义 | 单测 | 实跑 |
|---|---|---|---|
| 正式 Agent 定义 `.claude/agents/` | ✅ | ✅ | ✅ |
| 插件清单 + `CLAUDE.md` | ✅ | ✅ | ✅ |
| 责权利契约 | ✅ | ✅ | 待生产 |
| 证据运行时与 SHA-256 | ✅ | ✅ | 仅演示 |
| DIP → QC 交接 | ✅ | ✅ | **未完成** |
| Claudepot | ✅ | — | ✅ 成功 |

---

## 运行证据

```bash
$ python3 -m unittest discover -s tests
Ran 16 tests ... OK
```

16 个测试覆盖：Agent 定义加载、非法状态跳转、阻断恢复、完成拒绝、产物篡改、事件日志篡改、DIP 交接、双审隔离。

**2026-08-25 那次由 Claudepot 触发的真实运行产出：**

```
reports/_refs_verified.json   Crossref: 10.1016/j.example.2016.01.001 → 查无此 DOI
reports/demo_稿件样例_1主审.md / _2复核.md / _质检报告_2026-08-25_120847.md
```

最终报告**红灯，不建议提交**：抓出 3 条 🔴 严重——杜撰 DOI、卷期页与官方目录冲突、引用方向绝对化误用。

---

## Agent View

启动命令 `claude agents`（功能全名 Agent View；`/bg` 丢后台、`claude attach <id>` 连回）。本机 Claude Code v2.1.233，满足 ≥ v2.1.139。

![width:680px](evidence/agent-view-completed.jpeg)

---

## Claudepot：真实跑通了

![width:800px](evidence/claudepot-success.jpeg)

---

## 这一条是修出来的，不是一次就对

| 版本 | 结果 | 原因 |
|---|---|---|
| v1 | **失败，退出码 127** | `~/.local/bin/claude` 指向已失效的旧扩展；修好后又被 Bash 权限门阻断 |
| v2 | **成功** | 新 Agent 用受限 prompt，权限收成精确 allowlist |

v2 权限只给到 `Read, Grep, Glob, Bash(python3 qc.py *)` 及其绝对路径形式。

**AI 只有提议权（draft），上膛必须人来点** —— 这不是我们设计的，是 Claudepot 写死的：CLI 里根本没有 `install` 这个动词。

> 最重要的一课：**自述是元数据，产物才是证据。**

---

## 还没做到的（不粉饰）与下一步

- **单轮串联**：legacy `qc.py` 里复核能看到主审答案，做不到真正的三方盲判
- **多轮回源闭环**：遇分歧反复回原文核实、三回合仍无共识才交人裁决 —— **尚未实现**
- **带 frozen DIP manifest 的真实 audited production run** —— **未完成**

下一步：把单轮串联改造成多轮循环，逐轮把原始判断与证据落盘；跑通 DIP → QC 生产 run；给 Claudepot agent 配 cron 做到无人值守。

**GitHub**：https://github.com/wangfeifei-321/qc-team

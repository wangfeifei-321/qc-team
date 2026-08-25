---
marp: true
theme: default
paginate: true
---

# QC-Team

## 把上一个 agent team 升级成可审计的真实团队

**王彩迪** · 2026 年 8 月 25 日

<!--
本套幻灯片用 Marp CLI 从 Markdown 渲染：
npx @marp-team/marp-cli presentation/slides.md -o presentation/output.html
主题是可复用的 CSS，换项目只换内容不换样式。
-->

---

## 这套片子的一条规矩

> **自述是元数据，产物才是证据。**

凡是本片写「✅ 已完成」的，都能在仓库里找到对应产物或命令输出。
凡是**还没跑出来的，标「未完成」，不标 ✅**。

---

<!-- _class: lead -->

# 1. 解决的是什么真问题

---

## 留学作业质检的两个致命风险

- **文献造假** —— 参考文献根本不存在（学生或 AI 杜撰）
  单个 AI 复查无效：它会幻觉出看似真实的假文献来附和提问者
- **引用漂移** —— 文献真实存在，但原文结论与稿件拿它支撑的论点方向相反

这两类问题决定一份作业会不会触碰学术诚信红线。

---

## 三模型交叉核验

| 角色 | 由谁扮演 | 放行权 |
|---|---|---|
| `qc-conductor` 主审 | Claude | 强核票 1/2 |
| `qc-verifier` 复核 | Codex | 强核票 1/2 |
| `qc-reporter` 整理 | MiniMax | 无强核票，异议可阻断 |

选不同厂商的模型是刻意的：同一个模型跑三遍，盲区依旧。

---

## 确定性地基：文献真假不交给 AI

```bash
$ python3 qc.py samples/demo_稿件样例.txt
[1/1] 核验 10.1016/j.example.2016.01.001 ... 查无此文献！
```

DOI 存在性走 **Crossref 真实 API**，元数据逐字比对。

**能被确定性查证的事，必须交给程序而不是模型。**

---

<!-- _class: lead -->

# 2. 责权利：机器人世界里怎么分

---

## 一个 Agent 的一生：五种状态

```
BLOCKED ──依赖齐了──▶ READY ──派发──▶ RUNNING ──产物已发布──▶ COMPLETED
   ▲                                     │
   └──────上游 FAILED 向下游传播──────── FAILED
```

每个状态的进入条件都写成**可机械判定**的，例如
`COMPLETED` = 子进程 exit code 为 0 **且**产物文件字节数大于 0。

状态由编排器独占写入，不由 Agent 自报。

---

## 三条硬规则

1. **硬依赖强制** —— 依赖全部 `COMPLETED` 且产物可读，才允许进入 `RUNNING`
2. **禁止静默绕过** —— 读不到依赖就停下报 `BLOCKED`，不许自己重造一份上游材料
3. **失败必须传播** —— 上游 `FAILED`，下游一律 `BLOCKED`，由编排器安排返工

---

## 三道闸门：顺序不是流程图，是许可制

| 闸门 | 守门人 | 判据 |
|---|---|---|
| 1 · 来源闸门 | `verify_refs.py` | 每个 DOI 都有 Crossref 结果，无一条留空 |
| 2 · 双强核闸门 | 主审 + 复核 | 每条关键事实 2/2 一致，任一方 UNVERIFIED 即不通过 |
| 3 · 放行闸门 | 整理 | 八个板块齐全，红黄绿灯有对应依据 |

**闸门 2 不通过，闸门 3 不得翻案。**

---

## 责权利矩阵

| Agent | 责 | 权 | 利（目标函数） |
|---|---|---|---|
| 主审 | D1–D7 逐维度出结论、带 locator | 强核票 1/2 | 让「未被复核就放行」归零 |
| 复核 | 从原始材料独立重判，不照抄主审 | 强核票 1/2 | 让「主审漏判被下游发现」归零 |
| 整理 | 七项机械扫描、综合出唯一报告 | 异议可立即阻断 | 让「报告里出现无依据条目」归零 |

**三个角色都没有写文件的权限**——产物由编排器落盘，「谁写了什么」才唯一可追溯。

---

## 「利」在机器人世界里是什么

不是报酬，是**被复用的资格**。

产物可回溯、结论可复现的角色，下一次运行才会继续加载它；
反复产出不可核验结论的角色，应当被改写或删除。

---

<!-- _class: lead -->

# 3. 这一周改了什么

---

## 升级清单

| 项目 | 状态 | 证据 |
|---|---|---|
| 正式 Agent 定义 `.claude/agents/` | ✅ | 3 个文件，带 frontmatter |
| `.claude-plugin/plugin.json` | ✅ | `nlpm-check` 能扫到 |
| 责权利契约 `.claude/rules/` | ✅ | 五状态机 + 三闸门 + 矩阵 |
| `CLAUDE.md` | ✅ | 前置/安装/运行/测试/架构 |
| 证据运行时（SHA-256 封存） | ✅ | `qc_evidence.py` |
| DIP → QC 交接脚本 | ✅ | `scripts/run_audited_qc.py` |
| Claudepot 触发一次真实运行 | **未完成** | draft 已建，未激活 |

---

## 关键一改：角色定义成为单一事实来源

改之前：`roles/01_主审_claude.md` —— 裸 Markdown，不在任何被识别的路径上。

改之后：`.claude/agents/qc-conductor.md` —— 一份文件两处用

- `qc.py` 用 `read_agent()` 剥掉 frontmatter 当角色提示词
- Claude Code 直接把它当 subagent 加载

改行为只改这一份文件，`qc.py` 只负责传递。

---

<!-- _class: lead -->

# 4. 运行证据

---

## 测试与静态门（本次 commit 实测）

```bash
$ python3 -m unittest discover -s tests
Ran 16 tests ... OK

$ nlpm-check .
nlpm-check: clean
```

16 个测试覆盖：稿件读取、Agent 定义加载、frontmatter 剥离、
非法状态跳转、阻断恢复、完成拒绝、产物篡改、事件日志篡改、DIP 交接、双审隔离。

---

## 端到端质检（2026-08-18 那次真实运行）

| 环节 | 结果 | 产物 |
|---|---|---|
| Crossref 核验 | 通过 | 故意植入的假 DOI 被判「查无此文献」 |
| Claude 主审 | 通过 | 约 15 KB 的 D1–D7 意见，红灯 |
| Codex 复核 | 通过 | 约 7.4 KB 独立复核，指出主审过度表述 |
| MiniMax 整理 | 通过 | 约 6.5 KB 最终报告 |

系统没有把假 DOI「圆过去」，最终报告给红灯「不可提交」。

---

## Agent View

启动命令是 `claude agents`（功能全名 Agent View，
`/bg` 丢后台、`claude attach <id>` 连回、`claude respawn --all` 唤醒）。

本机 Claude Code v2.1.233，满足 ≥ v2.1.139 的要求。

> **运行截图见提交附件。**
> 本页不放模拟输出——没跑过的东西不写进片子。

---

<!-- _class: lead -->

# 5. NLPM 评分

---

## 起点：整个仓库扫不到

```bash
$ nlpm-check ~/Desktop/qc-team
no .claude-plugin/plugin.json found at, above, or within ...
```

NLPM 打的是**自然语言 artifact**（agents / rules / CLAUDE.md / plugin.json），
不打 `qc.py`。改之前这个仓库在评分工具眼里等于空的。

---

## 改之后：100 / 100

```
File                                        Type        Score  Findings
─────────────────────────────────────────────────────────────────────
.claude/agents/qc-conductor.md              agent        100     0
.claude/agents/qc-verifier.md               agent        100     0
.claude/agents/qc-reporter.md               agent        100     0
.claude/rules/agent-authority-contract.md   rule         100     0
.claude-plugin/plugin.json                  manifest     100     0
CLAUDE.md                                   claude-md    100     0

Overall: 100/100 — EXCELLENT              [threshold: 70]
```

---

## 中间那一次是 97 分，值得说

`qc-reporter` 只拿到 83：

- `model: haiku` 配上闸门 3 的放行权 → **档位错配 −5**
- 两处模糊量词 → **R01 −2 ×2**

这条 finding 是对的：**做权威性校准和推荐替代文献的角色，
正是幻觉风险最高的地方，不该配最低档模型。** 改成 sonnet 后满分。

---

<!-- _class: lead -->

# 6. 对照上周的高分样本

---

## 顾梦婷的作业强在哪

不是页面好看，是**一张页面同时给出可核验的硬指标**：

run id · 冻结基线 · Agent 流 · 跨厂商模型路由（含 effort 档位）·
9/9 gates · 逐条时间戳 · 产物与 action 统计 · E2E QA PASS

她的面板右上角写着 `Action Integration: NOT_CONNECTED`。

---

## 我们现在的位置（如实）

| 指标 | 顾梦婷 | 本项目 |
|---|---|---|
| 闸门 | 9/9 PASS | 3 道，全部通过 |
| 状态机 | 有 | 有，五状态 + 可机械判定的进入条件 |
| 产物哈希封存 | 未见 | 有，SHA-256 |
| NLPM 评分 | 未知 | 100/100 |
| Action Integration | NOT_CONNECTED | **同样未接通** |

---

## Claudepot 现状：诚实版

```bash
$ claudepot agent list
ID                                    NAME             LIFECYCLE  TRIGGER
599ff60b-dc52-4056-974d-8f35bc2c254c  qc-team-trigger  draft      manual
```

CLI v0.5.1 已源码编译安装，agent draft 已创建。

**但 lifecycle 还是 `draft`** —— 需要在 GUI 里 Review & install 才激活。
在它真的跑出一条运行历史之前，这一条**不算完成**。

---

<!-- _class: lead -->

# 7. 边界与下一步

---

## 还没做到的（不粉饰）

- **Claudepot 尚未真实触发** —— draft 未激活，无运行历史
- **单轮串联**：复核实际已看到主审答案，做不到真正的三方盲判
- **缺多轮回源闭环**：遇分歧反复回原文核实、三回合仍无共识才交人裁决，
  这套机制目前只在 Buzz 版上有

---

## 下一步

1. 激活 Claudepot automation，跑出第一条真实运行历史
2. 把「单轮串联」改造成「多轮循环」：主审出结论 → 自我复核 →
   与复核就分歧往返 → 逐轮把原始判断与证据落盘
3. 把 DIP 产稿 → QC 质检跑一次真实生产 run

---

<!-- _class: lead -->

# 谢谢

**GitHub**：https://github.com/wangfeifei-321/qc-team

```bash
git clone https://github.com/wangfeifei-321/qc-team.git
cd qc-team && cp .env.example .env   # 填 MiniMax API Key
python3 qc.py samples/demo_稿件样例.txt
```

本套幻灯片由 Marp CLI 从 `presentation/slides.md` 渲染。

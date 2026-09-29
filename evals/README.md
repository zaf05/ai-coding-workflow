# evals/ · 行为评测用例库（v1.9.0，docs/13 F5 最小落地）

> 这不是自动跑分的 benchmark。本目录是**可观察决策用例库**：每条用例来自一次真实 run 中
> AI 做过的关键决策，写清楚"输入是什么 / 期望行为是什么 / 怎么判定"。判定方式两种：
>
> - **确定性判定**：能用脚本断言的（退出码、输出 key、护栏开火），直接进 selftest；
> - **LLM-as-a-judge（会话执行）**：需要语义判断的，由**独立只读会话**按用例的判定问题打
>   Verdict（APPROVE / REQUEST_CHANGES / BLOCKED），judge 本身也是 instruction-only——
>   不引入外部评分服务、不自动出分、不伪造统计。
>
> ## 纪律（与 docs/05 证据规则同源）
>
> 1. 用例只能来自真实 run（`source_run` 必填，可追溯 ledger/证据文件）。
> 2. 每次真实 run 复盘（G10）发现值得固化的决策，最多补一条用例（Add 信号，与 rule-lifecycle 同族）。
> 3. 用例不预言未来行为——它约束"下次遇到同场景时，判定标准是什么"。
> 4. **AI 初稿采纳率在本库中不可算**：runs/ 不入版本库、无初稿→定稿留痕，口径见 docs/36 §三、
>    docs/37。不造数。度量侧可用数据见 `scripts/metrics_summary.py`（token/返修/耗时诚实口径）。
>
> ## 目录
>
> - `cases/` · 用例文件（`NNN-<slug>.md`，编号递增，从真实 run 提取）：
>   - [001-resume-zero-side-effect.md](cases/001-resume-zero-side-effect.md) — 断点恢复零重复副作用
>   - [002-fanout-domain-recovery.md](cases/002-fanout-domain-recovery.md) — fan-out 按域回收不按份数
>   - [003-unknown-flag-explicit-fail.md](cases/003-unknown-flag-explicit-fail.md) — 未知 CLI 参数显式 FAIL
>
> ## judge 会话怎么跑（协议）
>
> 新起一个只读会话（非实现会话），输入 = 用例全文 + 被测对象（当前 run / diff / 命令输出），
> 要求输出：`verdict / 依据（引用用例哪一条期望）/ 证据锚点`。verdict 为 REQUEST_CHANGES 时
> 必须指向可复现步骤。judge 结论进 run 的 `evidence.md`，不回写本库。

# 37 · 首批运行度量基线（2026-09-24，list_runs.py 实测）

> 来源：docs/36 §三 收编的度量口径候选（阶段耗时/返工次数成指标）+ Codex 交叉建议 4/5。
> 工具：`scripts/list_runs.py`（v1.8.17 新增，纯只读，`_yaml_min` fallback）。
> 数据：`runs/` 下全部 28 个历史 run 的 `state.yaml`（27 个可解析 + 1 个占位白名单）。

## 一、结论（三个基线数 + 一个不可算）

| 指标 | 基线值 | 口径 |
|---|---|---|
| 一次通过率 | **15/16 = 93.8%** | 分母 = 终态 `completed` 且 ledger 有记录的 run（16 个）；分子 = 其中零返修（全块 `attempts==1`） |
| 返修次数（总量） | **5 次**（跨 3 个 run） | 每 run 各块 `max(0, attempts-1)` 之和，含非 completed run |
| 推进轮次（总量） | **72 轮**（跨 17 个有账本 run） | ledger 条目数；v1.7.2 之前的 run 无 ledger 字段，诚实计 0 |
| 阶段耗时（中位跨度） | **159.6 分钟**（13 个多轮 run） | ledger 首末轮 timestamp 差；≥2 轮才计入跨度 |
| AI 初稿采纳率 | **不可算** | `runs/` 被 gitignore、无版本历史，无法判定「定稿是否由初稿迭代演进而非推翻重写」；docs/36 §三口径留待 evals 建库（需要 evidence.md 的初稿→定稿 diff 证据），**不伪造** |

汇总行原文（`python3 scripts/list_runs.py` 输出）：

```text
汇总: runs_total=28 parsed=27 placeholder=1 canceled=3 completed=23 terminated=1 | runs_with_ledger=17 completed_with_ledger=16 total_rounds=72 total_retries=5 | first_pass=15/16 median_span_min=159.6
```

## 二、口径定义（随工具固化，后续复测直接对比）

1. **一次通过**：`status == completed` 且 `rounds > 0` 且 `retries == 0`。canceled/terminated run 不进分母（它们没有「通过」语义）；无 ledger 的 completed run 也不进分母（v1.7.2 之前引擎不写 ledger，无法证实轮次与返修，不冒充）。
2. **返修次数**：`sum(max(0, attempts-1))`。`attempts` 在块 mark-done 时递增（v1.8.12 起），1 = 首次通过。
3. **轮次**：ledger 条目数。ledger 自 v1.7.2 由 `--advance` 每轮自动写入（v1.8.7 起含 model 归因）。
4. **跨度**：ledger 首末轮 timestamp 差（ISO8601 解析）。**注意**：这是「首末推进间隔」，包含人在 ⭐ 门等待时间与会话间隔——RUN-20260921-002（3071 分钟≈51h）与 RUN-20260921-006（2875 分钟≈48h）是跨天挂机等待人工门的真实形态，不是机器执行耗时。机器执行耗时的口径需要 per-block timestamp（当前 schema 未记录，见 §五）。
5. **占位目录**：无 `state.yaml` 的 `RUN-*` 目录（runs/README.md 白名单），显式归类不冒充解析成功。

## 三、逐 run 数据（2026-09-24 实测）

```text
RUN-ID                DATE       WORKFLOW      STATUS      BLOCKS   ROUNDS  RETRIES  SPAN(min)  OWNER
RUN-20260914-001      2026-09-14 feature-deli  completed   11/11    0       2        -          codex
RUN-20260914-002      2026-09-14 tag-manageme  canceled    5/18     0       0        -          codex
RUN-20260915-001      2026-09-15 功能交付          terminated  11/16    0       0        -          codex-planne
RUN-20260916-001      2026-09-16 feature-deli  completed   16/16    19      1        159.6      codex-planne
RUN-20260916-002      2026-09-16 feature-deli  canceled    12/16    6       2        27.4       codex-planne
RUN-20260917-001..006 2026-09-17 （4 bugfix + 1 refactor + 1 feature） completed/canceled，rounds 0–1，retries 0
RUN-20260918-001/002  2026-09-18 页面验证          canceled/completed 3/5、5/5
RUN-20260920-001      2026-09-20 页面验证          completed   5/5      5       0        642.0      Codex
RUN-20260920-002      2026-09-20 页面验证          completed   5/5      5       0        47.0       Codex
RUN-20260920-003      2026-09-20 ui-verificat  completed   5/5      2       0        5.8        claude-code
RUN-20260921-001      2026-09-21 功能交付          completed   7/16     8       0        18.2       claude-code
RUN-20260921-002..006 2026-09-21 feature-deli  completed，rounds 2–4，retries 0，span 295.0–3071.3
RUN-20260921-007      -          （占位/白名单）
RUN-20260922-001      2026-09-22 环境修复          completed   4/4      0       0        -          claude-code
RUN-20260923-001..004 2026-09-23 缺陷归因×2+功能交付+bugfix completed，rounds 1–5，retries 0，span 0.0–31.7
```

（完整逐行输出以工具实时运行为准：`python3 scripts/list_runs.py`；上表为 2026-09-24 快照，17-001..006 与 21-002..006 为同型合并行。）

## 四、读数与诚实边界

1. **样本小且不同质**：16 个分母 run 里混着 bugfix、页面验证、功能交付、评审-only（RUN-20260921-001 只读评审天然零返修）。93.8% 不能外推为「交付质量」，它只是「引擎账本口径下的零返修占比」。
2. **跨度 ≠ 工时**：中位 159.6 分钟里含人工门等待（见 §二.4）。跨天 run（21-002/21-006）的真实含义是「等待人审跨夜」，恰是多天任务恢复链（docs/30）的实际负载形态。
3. **ledger 覆盖率有代际断层**：28 个 run 里 11 个零轮次（多为 v1.7.2 之前或快照收口 run）。趋势对比应从 v1.8.x 之后的 run 开始才公平。
4. **返修集中在早期**：5 次返修全部落在 2026-09-14/16 的 run（14-001 两次、16-001 一次、16-002 两次），v1.8.12 引擎完整性加固（2026-09-23）之后零返修——但样本只有 6 个 run，不足以宣称加固生效，只能说「无反例」。
5. **采纳率缺口是数据缺口不是口径缺口**：docs/36 已给判定口径（定稿由初稿迭代演进而非推翻重写），缺的是初稿版本留痕。若未来 run 在 evidence.md 按「初稿 SHA → 定稿 SHA」留版本对（如 git 化 runs 归档后），此指标才可算。

## 五、后续

- 每完成 5 个新 run 复测一次本表（工具一条命令，无手工成本）。
- per-block 耗时（真正的「阶段耗时」）：需要 state.yaml 块级记录 started_at/completed_at——出现真实的阶段瓶颈分析需求时再提 schema 变更（当前 `schema_version: 1` 不动）。
- 采纳率：等 runs 证据版本化（私有归档仓库是用户侧前置）后，在 evals 用例库建库时一并落地（docs/13 evals 行已更新为「首批基线已出」）。

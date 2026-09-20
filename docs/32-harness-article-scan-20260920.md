# 32 · 参考扫描：《删掉80%的Prompt规则，Agent交付成功率反而更高了》（2026-09-20）

> **证据分级**：L1 全文（webReader 直接抓取微信公众号正文，约 1.2 万字，无截断）。
> 作者蓝翔（腾讯云开发者公众号）；参考引用 OpenAI harness engineering、Anthropic
> effective harnesses / context engineering / agent evals、Building Claude Code。
> 结论先行：**文章三支柱与 AIWorflow 三层模型高度同构，且其核心论点与 v1.8.0 的
> P0（写入时拦截）互为印证**；真正的增量是 Add/Thin 修剪纪律与"任务后能力观察规则"两条。

## 一、文章主张（摘要）

1. **可信上下文**：知识库是地图不是百科；AGENTS.md 三跳路由（入口→context→专题/源码）；
   重要结论必须带现场（claim/source/revision/scope/observed_at/verification 最小记录）；
   重复路径沉淀为 Runbook→Skill→Script→Gate（渐进固化）。
2. **可执行约束**："一条规则能不能形成约束，取决于违反它以后会发生什么"——条件不满足
   就无法继续才是约束，否则只是提醒。检查放两处：**阶段之间**（证据不够不能进下一阶段）
   与**动作之前**（高风险操作先检查再执行，不能先做后补）。
3. **可恢复流程**：文档是任务正文、state 是书签、workflow 是交接协议（输入/输出合同）；
   "Agent 可以失忆，但项目不能失忆"；恢复=从项目工件重建，不是恢复会话。
4. **生长与修剪（Add/Thin）**：只增不减的 Harness 最终变成新负担；重复失败/缺证据/无法
   恢复 → Add；长期无人消费/重复实现/频繁误伤/负收益 → Thin；不照搬别的项目已长成的
   Harness，可带走的只有方法。

## 二、对照矩阵（文章主张 × AIWorflow 现状）

| 文章主张 | AIWorflow 对应物 | 判定 |
|---|---|---|
| 知识库是地图、入口分层收窄 | docs/ 编号 + README 索引（validate_package 机器强制）+ "规则只在唯一位置维护" | ✅ 已有 |
| claim 最小记录（来源/版本/范围/验证） | evidence.md 锚点 + SHA 绑定 + install 收据指纹 | ✅ 已有（收据侧更强：机器可核） |
| 阶段之间门禁（证据不够不能继续） | G0-G10 + validate_run（v1.8.0 补齐 R-1/R-2 DAG 语义一致性） | ✅ v1.8.0 补齐 |
| **动作之前拦截（先检查再执行）** | **validate_transition.py T-01..T-04（v1.8.0 P0）**；pre-commit；install 漂移检测 | ✅ v1.8.0 新增 |
| 文档正文 / state 书签 / 交接协议 三分离 | current.md / state.yaml / 块 inputs+handoff+task_resume（docs/30） | ✅ 已有（结构一致） |
| 恢复=重建不是续会话 | checkpoint + 账本 + 失败尝试防死路重试 | ✅ 已有 |
| 渐进固化：问题先修复→重复路径沉淀→机械判断成 Gate | author-time guardrail + selftest 反例触发哲学 | ✅ 已有 |
| 根因四步（读轨迹→找第一偏离层→分事实/推断→双向验证） | 失败归因枚举 + bug intake + ERRATA 机制 | ✅ 基本覆盖 |
| **Add/Thin 修剪纪律（删减也是日常动作）** | 仅 G10/rule-lifecycle 有"规则过期检查"，无系统性删减信号与流程 | ⚠️ **缺口，建议吸收** |
| **任务后能力观察规则（只在出现信号时建议沉淀）** | G10 lessons 为人工复盘；无"重复劳动/反复纠正/反复找同一上下文"触发式观察 | ⚠️ **缺口，建议吸收** |
| MVP 起步、不照搬他人 Harness | instruction-only 自建 + 27-gap-analysis 按需立项 | ✅ 已有 |

## 三、落地记录（2 条已于 v1.8.1 实施）

1. **Add/Thin 并入 rule-lifecycle 契约** ✅：`_shared/contracts/rule-lifecycle.md` 淘汰清单
   补齐四信号（误伤 ≥2 次 / 无人消费 / 重复实现 / 模型升级复检），删减明确为正常变更
   （同新增的提交、版本号与 selftest 更新）。v1.1.0→v1.8.0 全程只增不减，标题
   《删掉80%的Prompt规则》正是对这种轨迹的警告。
2. **能力观察规则加进 close（G10）** ✅：信号触发才输出、最多一条沉淀建议、只建议不
   自动改、记录在该 run `current.md#Change Log`（不新增账本第六类）；G10 行与 Planner
   SKILL Close 步骤已接线。确定性底线 = selftest 3h 存在性护栏（三处接线任一脱钩即 FAIL）。

## 四、与 v1.8.0 的互证

文章 §3 的分界句——"如果条件不满足，任务仍然可以继续，它就只是一句提醒；只有条件不满足
时下一步真的无法进行，它才是可执行的约束"——正是 docs/31 P0 的立项理由。v1.8.0 已把
G9 类越权从"事后 validate_run 发现"（文章所说的"事后 Review"）升级为"写入瞬间拒绝"
（"动作之前检查"）。剩余差距：宿主层没有 state.yaml 写入钩子，"写入时拦截"目前靠
Planner SKILL 步骤自律调用（软约束）+ P3 完成后的 pre-commit（提交时硬约束）。

## 来源

- URL：https://mp.weixin.qq.com/s/fV8qN6qs9ac-VXDwZCuaxA（L1，2026-09-20 抓取）

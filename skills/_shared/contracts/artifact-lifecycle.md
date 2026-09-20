# 产物生命周期契约

> 吸收自：a01 闫鹏「验证证据而非口头声明」、a03 仁「六层验证」、a10 丶单向箔「多天 AI Coding 工作流」
> 权威来源：`../../../docs/05-state-and-evidence.md`。本文件是执行摘要。

## Run 容器四文件

```text
runs/<RUN-ID>/state.yaml      当前索引（唯一由 Planner 写）
runs/<RUN-ID>/current.md      正文（Intake/Recon/Spec/Tasks/Decisions/Change Log/Failed Attempts）
runs/<RUN-ID>/test-plan.md    Tester 独立维护
runs/<RUN-ID>/evidence.md     只追加账本
runs/<RUN-ID>/attachments/    必要脱敏附件
runs/<RUN-ID>/.local/         临时物，永不作为正式证据
```

## 草稿 → 发布 → 取代

- 草稿可连续原地编辑，不能被当作有效门禁证据。
- 发布前固定对象修订与不可变身份（Git 完整 SHA + 路径 + 对象 ID；无 Git 时本地快照 + 内容哈希）。
- 一经交独立 Reviewer 或产生正式结论即已发布；被拒绝/阻塞的版本也必须可逐字恢复。
- 审核/测试/实现/缺陷记录一经发布不可修改；修正由原职责作者发布新 ID + `supersedes`。

## 局部修订，不版本连锁

每个 Task/块独立修订号；局部修改不递增无关对象版本；不生成 `tasks-v2.md` 之类版本矩阵。

## 有效性判定

证据是否仍有效看**对象真实影响**：SHA 前进、环境重建、必要输入变化 → 对应证据失效，需补充验证。不得篡改旧载荷、空写"继续有效"、把旧 `tested_sha` 换成新 SHA。

## 失败尝试必须入账（吸收自 GoPS/Harness Engineering 对照分析）

> 最值得吸收的想法 #2：**失败尝试必须入账。** `current.md` 应有固定字段记录失败路径；同一死路跨会话不得重试。

规则：
- 每个失败的尝试在 `current.md#Failed Attempts` 记录：对象/路径、试过的方案、失败证据、结论。
- 新会话启动时先扫描 `Failed Attempts`，匹配到同一死路 → 直接 `BLOCKED` 并说明原因，不得重试。
- 同一 Finding 第二次修复失败 → 不再原会话重试，改用全新会话 + 最小根因包。

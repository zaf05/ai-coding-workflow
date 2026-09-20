# 03 · 门禁、Verdict 与严重度

门禁的唯一目的：**防止某个角色把自己的断言直接变成交付事实**。

## G0–G10

| 门禁 | 必需输入 | 通过证据 | 决策所有者 |
|---|---|---|---|
| G0 需求接收 | 开发请求 | `current.md#Intake`（用户、场景、目标、非目标、验收方式、授权边界） | Planner |
| G1 仓库基线 | Brownfield 范围 | 仓库画像、接管评估、`base_commit` 完整 SHA、脏工作区处置；**读取 `context/` 中匹配的项目/模块画像**（首次进入记"无历史上下文"） | Reviewer（风险要求时） |
| G2 Spec | Spec、UI/技术决策、块 DAG | 对应 Spec 对象修订的 `SPEC_REVIEW: APPROVE` | Reviewer |
| G3 用户批准 `*` | 已审核的产品行为与重要取舍 | 绑定 Spec 修订的用户批准记录 | 用户 |
| G4 测试先行（TDD Red） | 已批准 Spec | 对应计划修订的 `TEST_REVIEW: APPROVE` + **测试文件已写入且执行输出 FAIL**（TDD Red 阶段证据，绑定精确 SHA） | Reviewer |
| G5 块代码 | 已批准块的实现 | 对应 `base_sha..head_sha` 的 `CODE_REVIEW: APPROVE` | Reviewer |
| G6 集成 | 块已合入集成分支 | 对应集成 SHA 的增量测试 `PASS` | Tester |
| G7 完整验证 | 所有块均已验证 | 对应集成 SHA 的完整测试报告 `PASS`（含页面真实浏览器 + 视口矩阵） | Tester |
| G8 发布 | 当前验证证据 + 迁移/配置/回滚/文档 | 对应 SHA 的 `RELEASE_REVIEW: APPROVE` | Reviewer |
| G9 合并后验证 | 已合入实际目标分支 | 对应目标 SHA 的冒烟 `PASS` | Tester |
| G10 完成 | 所有证据当前有效 | `completion_contract` 逐条判定 + 关闭记录 + `DONE`；**向 `context/` 追加本次 Run 学到的项目知识**（无新增也要记"无新增"）；**做一次能力观察并执行规则淘汰清单**（信号触发、最多一条建议、只建议不自动改，见 `skills/_shared/contracts/rule-lifecycle.md`） | Planner |

规则冲突时执行更严格的一项。目标仓库已有的证据（CI 结果、既有测试报告）只有在**语义范围、独立决策所有者、版本/SHA 绑定、时效性**四项都等价时，才能直接满足对应门禁；`state.yaml` 引用其原始身份，不复制内容。

**Review 前置确定性检查（v1.8.7 起）**：CODE_REVIEW / RELEASE_REVIEW 在 LLM 判断前必须运行 `scripts/review_preflight.py`。secret、禁改区、破坏性命令任一 FAIL 时不得 APPROVE；规模门 WARN 必须进入报告并说明拆包或审批处置。机器判定不因 Reviewer 主观复看而豁免。

**写入时强制（v1.8.0 起）**：门禁 owner 集合不只是事后校验——Planner 每次覆写 `state.yaml` 时由 `scripts/validate_transition.py` 的 T-01 规则在写入瞬间拦截越权代签（如 Planner 代签 Tester 的 G9），FAIL 必须回滚本次写入。快照契约与完整规则见 [05-state-and-evidence.md](05-state-and-evidence.md)。

## 适用性省略（门禁不递归）

- G0–G4 是当前 Run/阶段的**共享准备**，不为每个块或实现步骤重跑。
- G5/G6 面向**完整块候选**及其集成 SHA。
- G7–G10 面向**当前交付的最终验收**。
- 角色动作不是 DAG 节点；门禁不套在门禁动作上。

可以直接不发起额外审核调用（不必先请 Reviewer 批准"无需审核"）：

- 块内部实现顺序、检查点、自测、生成物与必要文档步骤 → 并入完整候选的 G5。
- 与本次变更无关的专项维度（无 UI/数据/权限边界时的 UI/权限审核），以及不满足 Brownfield 风险触发条件的额外基线审核 → 注明不适用依据。
- 对象与必要输入均未变、原绑定仍有效，或宿主已有等价独立证据 → 引用原身份与覆盖范围。
- 仅过程清单/进度变化，或明确无语义影响的 `EDITORIAL` 修订 → 按变更控制记录。

**"省略额外调用"不是新的 Verdict、状态或 APPROVE。** 仍适用的 G2/G3/G4/G5/G8 不能因"任务小、赶时间、DAG 已冻结"跳过；代码 SHA 改变、真实阻断 Finding、权限/行为/测试预期变化也不能沿用失效证据。

## Verdict（只有三值）

| Verdict | 条件 |
|---|---|
| `APPROVE` | 没有未解决的阻断 Finding，且所有必需证据当前有效 |
| `REQUEST_CHANGES` | 对象可修正，且至少存在一个阻断 Finding |
| `BLOCKED` | 目标、版本、SHA、权限、环境或证据不可用，无法完成可信审核 |

不得使用"基本批准""有条件通过""大体 OK"。任何角色都不能因"没有反馈"推定通过。身份/授权/关键证据缺失 → `BLOCKED`；对象可审但有阻断 Finding → `REQUEST_CHANGES`。

## 严重度

| 级别 | 含义 | 对门禁的影响 |
|---|---|---|
| P0 | 可利用的安全问题、数据丢失/损坏、严重生产风险 | 始终阻塞 |
| P1 | 必需行为不正确、重大回归、关键验证缺失 | 始终阻塞 |
| P2 | 具体的可维护性、可靠性、兼容性或一般风险 | 除非有权主体明确书面接受，否则阻塞 |
| P3 | 当前不存在发布风险的非阻塞改进 | 不阻塞，转技术债 |

每条 Finding 必须包含：稳定 ID、严重度、类别、精确位置、触发场景、证据、影响、安全的必要修复方向。不得把格式化器输出、个人偏好、推测性现代化、无关历史技术债写成 Finding。

风险接受记录必须写明：对应 P2 Finding ID、接受主体、理由、范围、到期或复审条件、缓解措施、回滚方案。**P0/P1 永不可接受**，绝不能为推动门禁而接受。

## 交付深度

| 深度 | 触发 | 允许压缩什么 | 绝不压缩什么 |
|---|---|---|---|
| `FAST` | 低风险、小范围、无契约/权限/数据变化 | Mini Spec、紧凑测试计划、合并审核轮次 | 角色分离、精确证据、行为变化的用户批准、所有适用门禁 |
| `STANDARD` | 默认 | — | — |
| `HIGH_RISK` | 权限、租户、数据、兼容、并发、安全、生产、部署、凭据 | 不压缩，且加厚 | 增加威胁/权限/迁移/回滚/失败恢复/审计/有依据的性能覆盖 |

深度与项目新旧（Greenfield / Brownfield / Brownfield Continuation）正交。重构不是功能的默认附赠。

## 与 WanGo 工作包状态的映射

| 本工作流 | WanGo `agent-delivery-protocol` | 说明 |
|---|---|---|
| G0–G2 通过、块 DAG 冻结 | `planned` → `ready` | `ready` 前必须验证前置能力已有 accepted target 进入 integration baseline |
| 开始实现 | `in_progress` | 一个实现会话只处理一个工作包 |
| G5 `CODE_REVIEW: APPROVE` + G6/G7 证据齐 | `implementer_verified` | 实现者自测最多到此，不得自标 accepted |
| 独立复核产生 review_passed target + 临时集成检查无冲突无行为变化 | → `accepted` | Standard/Strict 必须经独立复核；accepted 不回退，问题开新包 |
| `BLOCKED` | `blocked` | 记录精确解阻条件 |

在 WanGoPlatform 内工作时以右列为准；本工作流只能加严。详见 `10-wango-adapter.md`。

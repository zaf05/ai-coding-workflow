# 证据规则契约

> 吸收自：a03 仁「六层验证」、a01 闫鹏「验证证据而非口头声明」、a12 Hank「确定性规则引擎优先」、a17 就是克克「AI 降低执行成本不是质量标准」
> 权威来源：`../../../docs/05-state-and-evidence.md`、`../../../docs/03-gates.md`。本文件是执行摘要。

## 没有证据不得宣称

- 没有绑定 SHA / 版本 / 命令输出的结论，不得写成 `APPROVE`、`PASS`、`accepted`。
- 测试或构建通过不能单独证明页面可用；页面任务必须真实启动 + 浏览器 + 目标视口。
- 低权威 Mock/本地结果不能替代集成、live、目标分支证据。
- **AI 降低了执行成本，但没有降低质量标准**（a17）；证据门禁不得因"AI 写的"而降低要求。

## 六层验证框架（吸收自 a03 仁「Code Review 与 Verification Agent」）

任何交付产物须在适用的层次上有可核验证据，不得跳层或只用一层代替全部：

| 层次 | 验证内容 | 证据形式 | 适用场景 |
|---|---|---|---|
| L1 Requirement | 需求是否被正确理解、完整覆盖 | `current.md#Intake`、Spec AC 逐条对应 | 所有交付 |
| L2 Contract | API/接口/事件契约是否符合定义 | OpenAPI diff、Schema 校验、契约测试 | 有接口变更的交付 |
| L3 Behavior | 用户可观察行为是否符合预期 | 浏览器截图、视口矩阵、交互录屏 | 页面/交互变更 |
| L4 Evidence | 所有门禁声明是否有可追溯证据 | `evidence.md` 完整载荷 + SHA 绑定 | 所有交付 |
| L5 Security | 权限/认证/数据保护是否未被破坏 | 权限矩阵验证、敏感数据扫描、越权测试 | 权限/数据变更 |
| L6 Regression | 已有功能是否未被破坏 | 回归测试套件、diff 驱动 QA、golden master | 所有交付 |

规则：
- 每层证据独立，不得用 L4（"我写了 evidence.md"）替代 L1/L2/L3/L5/L6。
- 不适用层次显式标注 `N/A` + 简短理由，不得静默跳过。
- Reviewer 审核时逐层核验，缺层报告为 Finding（P1：安全层缺失；P2：其他层缺失）。

## 确定性规则优先（吸收自 a12 Hank「阿里 open-code-review」）

> 阿里内部用了两年的 open-code-review 核心经验：**确定性规则引擎先扫硬伤（零误报），LLM 只做深层判断。** 每条规则来自几十万真实 bug。

本工作流对应：
- **确定性层**：`scripts/validate_package.py`、`scripts/validate_workflow.py`、`scripts/selftest.sh`、`install_hooks.py` pre-commit——所有结构/语法/护栏/闸门层面的检查由脚本完成，不需模型参与。
- **LLM 层**：Reviewer 角色——只做语义判断（行为是否正确、设计是否合理），不重复脚本已完成的结构检查。

规则：脚本层未通过的提交不得进入 Reviewer 审核；Reviewer 不得接受未通过确定性检查的产物。

## 必须入账的记录类型

五类，没有第六类：`REVIEW-xxx`（审核报告）、`IMPL-xxx`（实现报告）、`CHECK-xxx`（命令对照表）、`APPROVAL-xxx`（用户批准转录）、`DEFECT-xxx`（独立缺陷）。不写 Per-block 状态迁移 EVENT——那由 `state.yaml` 追踪。完整规范见 `../../../docs/05-state-and-evidence.md` §必须入账本的五类记录。

## 账本追加顺序（不可颠倒）

1. 角色独立生成完整载荷（用对应模板：review.yaml / implementation-report.yaml / CHECK 格式 / DEFECT 格式）。
2. Planner 原样追加到 `evidence.md`（不改写、不摘要、不合并）。
3. 再更新 `state.yaml` 索引。
4. 中断恢复先核对记录 ID：同 ID 同载荷 → 复用；同 ID 异载荷 → 阻塞并向原作者求解。
5. 矛盾证据未解决前，对应门禁保持未通过。

## 记录身份

- 文档身份 = 完整 Commit SHA + 路径 + 对象 ID。
- 代码证据 = `base_sha / head_sha / tested_sha`（完整 SHA，不是分支名）。
- 后续记账提交不等于已受测候选。

## 脱敏

凭据、Cookie、私钥、生产数据、未脱敏日志不得进入任何受跟踪产物或外部上传。

## 周期性系统审计（吸收自 a01 闫鹏）

> a01「不做人工Code Review，如何保障 Vibe Coding 的项目质量？」指出：Agent 必须交付验证证据而非口头声明；**周期性系统审计防止代码退化**。

本工作流对应：
- 每次 Run 关闭前（G10），Planner 须完成一次周期性审计检查：所有 `state.yaml` 引用的证据 SHA 是否仍可访问、是否有过期证据未标记、是否有未解决的 Finding/Defect。
- 审计发现写入 `evidence.md` 的 `AUDIT-` 记录，作为 G10 `completion_contract` 的一个判定项。

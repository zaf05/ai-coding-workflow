# 38 · spec-superflow 对照扫描（2026-09-25）

> 来源：132 微信文章 L1 + 133 GitHub 仓库 L1（API + README 全文）
> 结论先行：**有用，值得收录，但主要价值是印证而非新方法论**。11 条设计对照中 9 条我们已有；2 条新概念（delta specs / verification fingerprint）值得登记。

## 一、项目概况

| 项 | 值 |
|---|---|
| 项目 | MageByte-Zero/spec-superflow |
| 定位 | OpenSpec 规划引擎 + Superpowers 执行纪律的融合插件 |
| 版本 | v2.0.1（2026-09-24 活跃推送） |
| Stars | 818 |
| 语言 | JavaScript（Node.js 20+，零运行时依赖） |
| 平台 | 19 个（Codex / Claude Code / Cursor / Copilot CLI / Gemini CLI 等） |
| 许可 | MIT |

## 二、核心设计对照（11 条）

| # | spec-superflow 设计 | 我们的状态 | 判定 |
|---|---|---|---|
| 1 | Direct/Planned 双路径按风险分流 | delivery_depth FAST/STANDARD/HIGH_RISK | ✅ 已有同构 |
| 2 | proposal.md + tasks.md 结构化工件 | current.md#Spec + #Tasks | ✅ 已有同构 |
| 3 | OpenSpec delta specs（ADDED/MODIFIED/REMOVED/RENAMED） | 无——specs 是整体式的，无增量表达 | 🆕 **新概念** |
| 4 | Schema v2 执行计划 = 唯一事实源 | workflow_sha256 冻结 + state.yaml | ✅ 同构 |
| 5 | 审查覆盖完整 Git range，拒绝空 range | review 块 base_sha..head_sha | ✅ 已有 |
| 6 | verified vs accepted-risk 双终态 | implementer_verified + 用户 approve | ✅ 同构 |
| 7 | 根因调试→修复→回到原链 | bugfix-triage 工作流 + retry | ✅ 已有 |
| 8 | 恢复校验仓库/分支/路径 | task_resume.py + repository.root | ✅ 已有 |
| 9 | 按需加载 skills（9 个职责模块） | 5 个 skill 按需路由 | ✅ 同构 |
| 10 | 验证结果绑定输入指纹（代码变→旧 pass 不可复用） | workflow_sha256 冻结但**不覆盖验证命令指纹** | 🆕 **新概念** |
| 11 | 路径边界验证（symlink/realpath/overlay） | 无 | 🆕 候选项（低优先级） |

## 三、两条新概念评估

### 3a. Delta Specs（增量规格表达）

**是什么**：用 `ADDED` / `MODIFIED` / `REMOVED` / `RENAMED` 四种操作表达"这次改了规格的哪些部分"，而不是每次重写完整规格。

**我们的差距**：current.md#Spec 是整体式，每次修订全量重写。跨多个 run 演进同一功能时，无法快速回答"第 3 个 run 相对第 2 个 run 改了规格的哪几条"。

**是否采纳**：暂缓。触发条件：出现同一功能 ≥3 个 run 连续演进且需要规格差异对比的真实场景。目前单 run 内 Spec 版本号 + Change Log 已够用。

### 3b. Verification Fingerprint（验证指纹绑定）

**是什么**：最终验证记录影响结果的输入指纹（代码 SHA + 环境配置）。代码或环境变了，旧的"通过"不能复用。

**我们的差距**：workflow_sha256 冻住了 DAG 定义，但 check 块的验证命令本身没有指纹。理论上可以改 check 命令后引用旧结果。

**是否采纳**：值得纳入路线图。实现方式：check 块执行时把 commands 列表的哈希也写入 evidence，validate_run 校验 evidence 中的命令哈希与 workflow 定义一致。触发条件：下次出现"check 命令被中途修改但旧结果仍被引用"的真实风险场景。

## 四、与既有参考的关系

- 与 Skyvern（a02）的 BlockType/completion_contract 同族：块编排 + 完成判据
- 与 ric-dev-workflow-skills（a03）的四角色分离同族：职责边界 + 所有权矩阵
- 与 AWS AI-DLC（a21）的 approval gate 同族：人工门 + 按需加载
- **新增差异**：spec-superflow 是唯一将 OpenSpec 的 delta specs 引入 AI 工作流的项目

## 五、证据级标注

| 来源 | 级别 | 获取方式 |
|---|---|---|
| 132 微信文章 | **L1**（全文 3.7MB HTML，curl + MicroMessenger UA 直抓，正文完整提取） | curl 200 |
| 133 GitHub 仓库 | **L1**（GitHub API 元数据 + README 全文 120 行；git clone 超时但 API 信息完整） | API 200 |

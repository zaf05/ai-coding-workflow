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

---

## 六、追加来源 134：Git worktree 并行开发实战（2026-09-25）

> 微信文章 L1（3.6MB 全文提取）。同一批提交但独立主题：Git worktree 多分支并行、AI 任务隔离、冲突合并与安全清理。

### 设计对照（8 条）

| # | 文章主张 | 我们的状态 | 判定 |
|---|---|---|---|
| 1 | worktree 隔离 AI 任务（一任务一 worktree） | `.worktree/<work-package>/` + 分支隔离 | ✅ 已有同构 |
| 2 | 文件所有权表：并行前画清各自负责的文件 | docs/25 拆分原则第 2 条"文件所有权不重叠" | ✅ 已有 |
| 3 | 一次只合并一个分支，main 每次重测 | 交付协议：串行集成 + 交叉检查 | ✅ 已有 |
| 4 | 端口/数据库/缓存按 worktree 独立分配 | canonical 单库四 schema（agentwan/core/agno/deck） | ✅ 已有 |
| 5 | 安全清理：remove 而非手动删除 + prune --dry-run | 工作包完成后 `git worktree remove` | ✅ 已有 |
| 6 | AI 任务提示中明确允许目录/目标分支/禁止资源 | handoff.md 允许路径 + 保护路径 | ✅ 已有 |
| 7 | **可量化效率实验**（连续两周记录切换次数/合并冲突数/磁盘占用） | list_runs.py 有度量但**未做过对照实验** | 🆕 值得借鉴 |
| 8 | **事故恢复演练**（故意移动目录→repair/删除→prune/制造冲突→abort） | 有 task_resume 但**未做过破坏性演练** | 🆕 值得借鉴 |

### 新概念评估

- **效率对照实验**：文章建议连续两周记录"上下文切换次数/热修复响应时间/冲突文件数/废弃 worktree 数"与旧方案对比。我们的 list_runs.py 已有数据采集能力，缺的是**设计一个 A/B 对照期**。触发条件：下次团队讨论"worktree 是否值得"时执行。
- **事故恢复演练**：在测试仓库故意触发三种事故（目录被移动/被删除/合并冲突），练习 repair/prune/abort。我们有恢复组件但从未故意破坏验证。可与 L3 断点演练合并为一次"灾难恢复日"。触发条件：列入 docs/13 路线图等真实需求。

---

## 七、追加来源 135：alibaba/open-code-review 开源（2026-09-25）

> GitHub 仓库 L1（API 元数据 + README 全文；commit e10f474 入附录）。这不是新文章，而是 **a12 的工具本体开源**：阿里内部用了两年的 open-code-review 以 CLI `ocr` 形式发布。

### 事实核验（GitHub API，2026-09-25）

- 仓库 `alibaba/open-code-review`；40,782 ⭐；License Apache-2.0。
- 官方描述：混合架构代码审查工具——确定性管线 + LLM Agent，行级精确评论，内置多语言规则集（NPE/线程安全/XSS/SQL 注入），OpenAI 与 Anthropic 兼容。
- 与 a36（AACR-Bench）同源工程：规则来自大规模真实评审数据。

### 归属判定

| 维度 | 判定 |
|---|---|
| 观点层 | 无新增观点——a12「确定性规则引擎先扫硬伤、LLM 只做深层」已在库并落地为 review_preflight.py；本条只把工具从"文章描述"升级为"可安装实体" |
| 吸收动作 | **不立即接入**。已有 review_preflight.py（secret/禁改区/破坏性命令/规模四规则）覆盖当前需求；引入 `ocr` 属于新增外部二进制依赖，违反 0 新增依赖边界，须走变更控制 |
| 触发条件 | 登记待评估：当确定性前置检查出现真实漏报（review_preflight 规则不够用）且愿意接受 npm 依赖时，评估 `ocr` 作为 Reviewer 第 0 步的可选增强 |
| 证据 | 核验表 row 114（GitHub API + README 全文，L1） |

# 20 · 外部 AI 工作流开源项目扫描（2026-09-14）

> 本文扫描 4 个 GitHub 开源 AI 工作流/编排项目，提取可吸收的设计思想，并逐条映射到本工作流（AIWorflow v1.7.0）。
> 所有信息来自 GitHub API 与 README 的实际提取，日期 2026-09-14，Asia/Shanghai。

---

## 一、项目总览

| # | 项目 | Stars | 语言 | 定位 | 与本工作流关系 |
|---|---|---|---|---|---|
| a21 | [awslabs/aidlc-workflows](https://github.com/awslabs/aidlc-workflows) | 4,598 | TypeScript | AWS 官方 AI 驱动开发生命周期工作流；一套核心适配 7 个宿主（Claude Code/Codex/Cursor/Kiro/Copilot 等） | **高度相关**：与 AIWorflow 的"多宿主薄配置"同向，AI-DLC 的 `aidlc` CLI + approval gate + workflow routing 可借鉴 |
| a22 | [langflow-ai/langflow](https://github.com/langflow-ai/langflow) | 154,789 | Python | 可视化 AI Agent 与工作流构建器，基于 React Flow 拖拽编排 | **中度相关**：可视化 DAG 编排思路可借鉴（但我们不做 Web UI）；155K stars 说明可视化编排是主流方向 |
| a23 | [fengshao1227/ccg-workflow](https://github.com/fengshao1227/ccg-workflow) | 5,884 | Go/Node.js | 多模型协作工作流引擎：`/ccg:go` 一个命令，AI 自动分析意图、选择策略、编排 Codex+Gemini+Claude 协作执行 | **高度相关**：多模型协作策略路由与 AIWorflow 的自动角色分发同向；CCG 的意图分析→策略选择→模型分派可作为 AIWorflow 入口路由的增强参考 |
| a24 | [nicepkg/ai-workflow](https://github.com/nicepkg/ai-workflow) | 283 | HTML | 170+ 预构建 Skill 集合，支持 Claude Code/Cursor/Codex 等 14+ AI 工具；一键注入领域专业知识 | **中度相关**：大规模 Skill 市场思路可借鉴（WanGo 的 Skill/Tool 管理）；但它是静态 Skill 集合而非编排引擎 |

---

## 二、逐项目深度分析

### a21 · AWS AI-DLC（aidlc-workflows）

**核心理念**：一套 workflow 定义（`workflows/` 下 YAML），通过 `aidlc` CLI 适配 7 个不同宿主。Workflow 含 approval gate，在关键决策点停下等人确认。

**关键设计**：

| 设计点 | AI-DLC 做法 | AIWorflow 对应 |
|---|---|---|
| 多宿主适配 | 一个 `aidlc config --harness <name>` 命令生成宿主专用薄配置 | `skills/` 目录结构 + `install_skills.py` 已支持 Codex/Claude/ZCode |
| 工作流选择 | AI 从请求中自动选择工作流（"Build a REST API" → 自动路由到 feature 工作流） | `aiworflow/SKILL.md` description 即路由逻辑，但缺少自动工作流选择的 Prompt 模板 |
| Approval Gate | 在不可逆操作前停下等人确认，类似 G3/G8 | 已有 `star:true` + `WAIT_USER` 信号，同向 |
| 安装方式 | `curl -fsSL URL | sh` 一键安装 native CLI | `install_skills.py --apply` + selftest 自证可用 |
| 版本管理 | GitHub Release + 语义化版本（v2.8.2） | `VERSION` + SHA256 收据，同向 |
| 项目配置 | `aidlc doctor` 诊断宿主/环境/权限就绪状态 | 无对应（`validate_package.py` 只测包本身，不测宿主环境） |

**可吸收的设计**：
1. **`aidlc doctor` 诊断命令**：检查宿主是否可用、权限是否到位。AIWorflow 可加 `scripts/diagnose.py`。
2. **自动工作流选择 Prompt 模板**：从自然语言请求自动匹配最佳工作流定义。当前 AIWorflow 靠 `aiworflow/SKILL.md` 的 description 做路由，可增强为结构化模板。
3. **`workflows/` 下按场景分类**：AI-DLC 的 `workflows/` 按场景（feature/bugfix/refactor）分目录，比 AIWorflow 当前平铺更清晰。

### a22 · Langflow

**核心理念**：可视化拖拽构建 Agent 工作流，节点即组件，连线即数据流。155K stars 证明市场对可视化编排的强烈需求。

**与本工作流的关系**：
- Langflow 是**可视化低代码平台**，解决"不会写代码也能编排 AI Agent"的问题
- AIWorflow 是**文件驱动控制层**，解决"AI 写代码时有迹可循、可验证"的问题
- **两者定位不同，不构成替代**，但 Langflow 的节点类型目录（Agent/Tool/Prompt/Memory/Output 等分类）可作为 AIWorflow 块类型目录（`02-block-catalog.md`）的扩展参考

### a23 · CCG Workflow（多模型协作）

**核心理念**：一个命令 `/ccg:go` → AI 分析意图 → 选择策略 → 分派给 Claude/Codex/Gemini 协作执行。

**关键设计**：

| 设计点 | CCG 做法 | AIWorflow 对应 |
|---|---|---|
| 意图分析 | 自然语言 → 自动分类（开发/审查/测试/部署） | `aiworflow/SKILL.md` 入口路由：根据场景选工作流定义 |
| 策略选择 | 按任务类型选择单模型/双模型/三模型协作策略 | `run_flow.py` loop_control 信号驱动角色分发 |
| 多模型分派 | Claude 负责规划、Codex 负责实现、Gemini 负责审查（可配置） | 四角色（Planner/Implementer/Reviewer/Tester）固定分工，不区分底层模型 |
| 模型无关设计 | 策略层与模型层解耦，换模型不改策略 | Prompt 模板 static/dynamic 分段，模型参数不入状态机 |

**可吸收的设计**：
1. **意图分析的 Prompt 模板**：CCG 的 `/ccg:go` 能从自然语言分析出"这是开发任务还是审查任务"，AIWorflow 入口可借鉴其 Prompt 结构。
2. **策略可配置**：CCG 的多模型策略可通过配置文件调整。AIWorflow 当前四角色是固定的，未来如果需要调整"哪些模型做哪些角色"，可借鉴策略配置层。

### a24 · AI Workflow（nicepkg）

**核心理念**：170+ 预构建 Skill，覆盖 SEO/营销/交易/视频/PM 等领域。用户一键安装，AI 直接具备领域知识。

**与本工作流的关系**：
- AI Workflow 是 **Skill 内容市场**，AIWorflow 是 **研发流程引擎**
- **两者互补**：WanGo 的 Skill/Tool 管理功能（标签分类、URL/Git 导入）可以借鉴 AI Workflow 的 Skill 组织方式
- AI Workflow 的 Skill 结构（`SKILL.md` + references + examples）与 AIWorflow 的 Skill 包结构一致

**可吸收的设计**：
1. **Skill 多领域分类**：Marketing/SEO/Trading/Video/PM 分类体系，可作为 WanGo Skill/Tool 标签初始词典的参考。
2. **一键安装体验**：`npx ai-workflow install <skill-name>` 直接注入到宿主。我们的 `install_skills.py` 已有类似能力。

---

## 三、四个项目对比矩阵

| 维度 | AIWorflow v1.7 | AWS AI-DLC | Langflow | CCG Workflow | AI Workflow |
|---|---|---|---|---|---|
| **定位** | AI 研发控制层 | AI 开发生命周期 | 可视化 Agent 编排 | 多模型协作引擎 | Skill 内容市场 |
| **编排方式** | 块 DAG (YAML) | Workflow YAML | 可视化拖拽 | 意图→策略→分派 | 无（Skill 集合） |
| **多宿主** | Codex/Claude/ZCode | 7 宿主（含 Codex/Claude/Cursor） | Web UI（自成一宿主） | Claude+Codex+Gemini | 14+ 宿主 |
| **执行引擎** | ✅ run_flow.py | ✅ aidlc CLI | ✅ Python 后端 | ✅ ccg CLI | ❌ 无 |
| **护栏** | ✅ 三层自动 | ✅ approval gate | ⚠️ 依赖 Langflow 平台 | ❌ 未明确 | ❌ 无 |
| **版本管理** | ✅ VERSION+SHA256 | ✅ GitHub Release | ✅ PyPI 版本 | ✅ npm 版本 | ❌ 无 |
| **selftest** | ✅ 50/50 PASS | ⚠️ 有 CI | ⚠️ 有 pytest | ⚠️ 有 CI+codecov | ❌ 无 |
| **证据/审计** | ✅ Evidence 层 | ❌ 未明确 | ❌ 运行日志 | ❌ 未明确 | ❌ 无 |
| **外部依赖** | **0** | Node.js/Bun | Python+React+DB | Node.js >=20 | Node.js |
| **AI 自动路由** | 入口 description | ✅ 自动选工作流 | 用户手动拖拽 | ✅ 意图分析 | 用户手动选择 |

---

## 四、应吸收的新设计决策

### 决策 1：自动工作流选择（吸收自 AI-DLC + CCG）

AI-DLC 从自然语言请求自动匹配工作流，CCG 从自然语言分析意图→选策略。AIWorflow 入口可在 `aiworflow/SKILL.md` 的 `prompts/` 中增加一个"工作流选择 Prompt 模板"：

```text
给定用户请求，判断属于以下哪类场景，输出工作流名称：
- feature-delivery：新功能开发
- bugfix-triage：缺陷归因与修复
- refactor-migration：重构或迁移
- ui-verification：页面验证
```

### 决策 2：宿主环境诊断（吸收自 AI-DLC `aidlc doctor`）

新增 `scripts/diagnose.py`：检查 Codex/Claude/ZCode 是否可用、Skills 是否正确安装、hooks 是否在位。当前 selftest 只测包本身，不测宿主环境。

### 决策 3：多模型协作策略层（吸收自 CCG）

当前四角色不区分底层模型。如果未来需要"Planner 用强模型、Implementer 用快模型"，CCG 的策略可配置设计值得参考。

### 决策 4：Skill 分类初始词典（吸收自 AI Workflow）

WanGo Skill/Tool 标签管理功能的初始标签词典，可参考 AI Workflow 的领域分类：开发/测试/运维/营销/数据/设计/安全/文档/部署/监控。

---

## 五、明确不吸收的

| 项目 | 为什么不吸收 |
|---|---|
| Langflow 可视化编排 | AIWorflow 明确规定"不做 Web UI"（`13-roadmap.md`），可视化编排是另一个赛道 |
| Langflow 拖拽即代码 | 文件驱动 > 可视化拖拽：文件可 Git 版本化、可 diff、可 review、可 CI，拖拽产生的 JSON 不可审查 |
| AI Workflow 的 npm 全局安装 | AIWorflow 是项目级工作流，不装在全局；`install_skills.py` 已支持 symlink 模式 |

---

## 六、核验记录

| # | URL | 核验方式 | 核验结果 | 核验日期 |
|---|---|---|---|---|
| a21 | https://github.com/awslabs/aidlc-workflows | GitHub API + README 提取 | HTTP 200, 4,598 stars, v2.8.2 | 2026-09-14 |
| a22 | https://github.com/langflow-ai/langflow | GitHub API + README 提取 | HTTP 200, 154,789 stars | 2026-09-14 |
| a23 | https://github.com/fengshao1227/ccg-workflow | GitHub API + README 提取 | HTTP 200, 5,884 stars | 2026-09-14 |
| a24 | https://github.com/nicepkg/ai-workflow | GitHub API + README 提取 | HTTP 200, 283 stars, 170+ skills | 2026-09-14 |
| 重复 | https://mp.weixin.qq.com/s/UE-RZH9hnbBd06CVapFGrA | curl + 移动端 UA | HTTP 200，标题"从AI Coding到Harness Engineering的端到端工程开发实践"——与 zhuanlan.zhihu.com/p/2056025288866378509 同文，已收录于核验表 row 2 | 2026-09-14 |
| 重复 | https://mp.weixin.qq.com/s/rlIyIIZOXFObNIXbPI7gDg | curl + 移动端 UA | HTTP 200，标题"Harness Engineering：耗时一周，我是如何将应用的AI Coding率提升至90%的"——与 uml.org.cn/ai/202605101.asp?artid=27372 同文，已收录于核验表 row 3 | 2026-09-14 |

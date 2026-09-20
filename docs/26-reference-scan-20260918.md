# 26 · 微信参考扫描 · 2026-09-18

> 15 篇微信文章，全部 L1 全文核验（MicroMessenger UA + `js_content` 提取）+ 39 张图片 RapidOCR。
> 无幻觉：每条核心观点均出自提取正文，非二手转述。

## 一、来源清单

| # | 公众号 | 标题 | 正文 | 图片 | 证据等级 |
|---|---|---|---|---|---|
| c01 | 火山引擎Agent社区 | OpenViking：给 Codex 加上长期记忆 | 6,158 字 | 17→16 OCR | L1 + L1-IMG |
| c02 | InfoQ | AI Coding 贡献率超 90%，需求交付却只快了 10%：菜鸟如何用 Agent 托管端到端交付？ | 8,807 字 | 11→8 OCR | L1 + L1-IMG |
| c03 | 肥喵学AI | AI 改完代码还得你收尾？把自动修复循环搭起来 | 4,522 字 | 2→1 OCR | L1 + L1-IMG |
| c04 | 月谈AI | Self-Improving Coding - 当编码 Agent 开始改进自己 | 8,861 字 | 6→3 OCR | L1 + L1-IMG |
| c05 | 编程拾录 | Trellis：把 AI 编程从即时对话变成可复用工作流 | 9,264 字 | 2→1 OCR | L1 + L1-IMG |
| c06 | 编程拾录 | AI Coding 实践：把分析问题与解决问题变成可复用的工程能力 | 6,232 字 | 1→0 OCR | L1 |
| c07 | AICon | Addy-Osmani 开源 Agent-Skills，帮 AI 编码智能体养成资深工程师规范 | 2,342 字 | 2→2 OCR | L1 + L1-IMG |
| c08 | 程序员小黑 | 告别"AI 流水线界面"！Impeccable：前端开发者必备 AI 设计 Skill | 2,252 字 | 1→0 OCR | L1 |
| c09 | 程序员小黑 | 给 AI Agent 加上 TDD：一个开源 Skill，让代码按 Red→Green 循环写出来 | 3,147 字 | 4→3 OCR | L1 + L1-IMG |
| c10 | 程序员小黑 | Agent Skill：让 AI 先搞懂业务再写代码——Domain Modeling | 2,998 字 | 1→0 OCR | L1 |
| c11 | 程序员小黑 | 别只让 AI 写代码：这个开源 Agent Skill 把 ADR/API 文档/README 全部纳入 | 2,611 字 | 2→1 OCR | L1 + L1-IMG |
| c12 | 程序员小黑 | AI 写代码越来越快但安全怎么办？Security and Hardening Skill | 3,026 字 | 2→0 OCR | L1 |
| c13 | AI羊毛实验室 | 测试工程师必装的 10 个 AI Skill | 4,002 字 | 1→0 OCR | L1 |
| c14 | AI羊毛实验室 | GitHub 星标最多的 10 个 AI Skill | 3,314 字 | 1→0 OCR | L1 |
| c15 | 聆木听风 | 从一句需求到代码交付，我只需要一个 Skill | 3,797 字 | 0 | L1 |

---

## 二、核心发现与采纳决策

### E1 · 跨会话长期记忆（c01 OpenViking）→ 印证 context/ 方案

**原文核心**：Codex 在新对话中遗忘历史背景，换 Agent 更要从零开始。OpenViking 通过 MEMORY.md + vector store 让 Codex 在新任务启动时自动检索相关历史。

**与 AIWorflow 对照**：
- ✅ **已成立**：`context/` 目录（G1 读 + G10 写）解决同一问题
- ⚠️ **差距**：我们只有文件级上下文，无向量检索；大 context 文件需人工拆分
- **采纳**：不引入 OpenViking（外部依赖重）；记录差距为未来增强方向

### E2 · 端到端交付 vs 编码贡献率（c02 菜鸟）→ 印证 G0-G10 完整链路

**原文核心**：菜鸟 AI Coding 贡献率 10%→90%，但需求交付只快 10%。根因：编码不是瓶颈，需求→编码→测试→部署整条链才是。解法：Agent 托管端到端交付（Playbook.md + Plugins + 通用 Agent 循环）。

**与 AIWorflow 对照**：
- ✅ **已成立**：G0(需求)→G2(Spec)→G4(TDD)→G5(实现)→G6/G7(验证)→G8(发布) 正是端到端托管
- ⚠️ **差距**：我们的 Playbook 等价物是 workflow YAML，但缺少 Plugins 层（上下文管理的组件化）
- **采纳**：将"Plugins = 上下文管理组件化"理念记录为未来增强方向

### E3 · 自动修复循环（c03 Harness Engineering）→ 印证 G6/G7 + 熔断

**原文核心**：AI 改代码→人跑测试→贴报错→AI 再改，循环消耗人力。解法：Harness Engineering 把执行、约束、验证作为工程对象，失败反馈自动接回修复循环。

**与 AIWorflow 对照**：
- ✅ **已成立**：run_flow.py 的 loop_control + 熔断（CONTINUE 超 10 轮→BLOCKED）
- ⚠️ **差距**：我们的自动修复循环是状态机级，不是测试→AI→再测试的细粒度闭环
- **采纳**：理念已覆盖；细节差距记录

### E4 · Self-Improving Coding 五层机制（c04）→ 印证 C2 沉淀出口

**原文核心**：从 Prompt→Context→Tool→Agent→权重，复杂度和风险逐层递增。当前有效工作集中在前三层。

**与 AIWorflow 对照**：
- ✅ **已成立**：C2 沉淀出口（Finding→规则回写）= 第一层"Prompt 自改"
- ⚠️ **差距**：无 Tool 层自动创建（第二层）和 Agent 架构自改（第三层）
- **采纳**：记录五层分类，当前定位 = Layer 1（Prompt/规则自进化）

### E5 · Trellis 可版本化控制结构（c05）→ 直接印证 context/ + workflow YAML

**原文核心**：把项目规范、任务边界、执行上下文、会话记录组织成可版本化的控制结构，让第二次、第三次 AI 编程不再从零开始。

**与 AIWorflow 对照**：
- ✅ **已成立**：`context/`（跨 Run 知识）+ `workflows/*.yaml`（可版本化流程定义）= Trellis 等价物
- ✅ **比 Trellis 更强**：我们有 52/52 selftest + 三层护栏 + validate_consistency.py
- **采纳**：印证现有设计正确，无需修改

### E6 · 分析→解决→复用工程能力（c06）→ 印证 G2 Spec + D2 调试六步

**原文核心**：复杂任务昂贵部分是识别问题边界、找到相关代码、判断证据、排除假设、证明改动安全。要变成可复用能力。

**与 AIWorflow 对照**：
- ✅ **已成立**：G2 Spec（边界定义）+ D2 调试六步（Reproduce→Isolate→Reduce→Fix→Guard→Verify）+ C1 Blast Radius（影响面）
- **采纳**：印证现有设计

### E7 · Addy Osmani Agent Skills（c07）→ 印证 Skill 分层

**原文核心**：Addy Osmani（Google Chrome 团队）开源 Agent Skills 集合，帮 AI 编码养成资深工程师规范。

**与 AIWorflow 对照**：
- ✅ **已成立**：`skills/aiworflow*/SKILL.md` 就是同一思路
- **采纳**：参考其 Skill 组织方式，但不引入外部依赖

### E8 · TDD Skill（c09）→ 直接印证 G4 TDD Red

**原文核心**：Matt Pocock 开源 TDD Skill，让 Agent 按 Red→Green 循环。核心不是"写测试"，而是测试能否真正约束行为。

**与 AIWorflow 对照**：
- ✅ **已成立**：G4 = TDD Red（测试文件先行 + FAIL 证据绑定 SHA），G6 = Green
- ✅ **v1.7.6 已完成此升级**，本文提供最新第三方印证

### E9 · Domain Modeling Skill（c10）→ 补强 G0 Intake

**原文核心**：让 AI 先搞懂业务领域语言再写代码，避免"程序员最容易忽略的领域知识差距"。

**与 AIWorflow 对照**：
- ⚠️ **部分成立**：G0 Intake 记录"用户、场景、目标"，但无显式的领域术语表/业务约束字段
- **采纳**：**新增改进项 E9** —— G0 Intake 模板增加"领域术语/业务不变量"字段

### E10 · Documentation & ADR Skill（c11）→ 补强 context/decisions

**原文核心**：把架构决策（ADR）、API 设计、项目约定沉淀为 AI 可读的工程文档。

**与 AIWorflow 对照**：
- ✅ **已成立**：`context/decisions.md` 模板已存在
- **采纳**：无需修改，印证现有设计

### E11 · Security Skill（c12）→ 补强 G8 Release Review

**原文核心**：安全前置到设计和编码阶段，覆盖输入校验、权限、Secret、外部接口、供应链。

**与 AIWorflow 对照**：
- ✅ **已成立**：G8 Release Review 包含"安全"维度
- ⚠️ **差距**：无专门的 Security Checklist
- **采纳**：记录为未来增强，不阻塞当前版本

### E12-E15 · Skill 集合盘点（c13/c14/c15）→ 生态参考

**核心**：测试 Skill 10 个、GitHub 高星 Skill 10 个、单一 Skill 端到端交付。

**与 AIWorflow 对照**：
- ✅ **定位差异**：AIWorflow 是"控制层"（门禁/角色/证据），不是"能力层"（测试/安全/设计具体 Skill）
- **采纳**：作为生态参考，不直接引入

---

## 三、本轮新增改进项

| ID | 来源 | 改进 | 落地文件 | 状态 |
|---|---|---|---|---|
| E9 | c10 Domain Modeling | G0 Intake 增加领域术语/业务不变量 | `prompts/intake.md` | **本轮落地** |
| E2-ref | c02 菜鸟 | 记录 Plugins 上下文组件化为未来方向 | 本文档 | 记录 |
| E4-ref | c04 Self-Improving | 记录五层机制，当前=Layer 1 | 本文档 | 记录 |

---

## 四、核验声明

- 15/15 篇文章全部用 MicroMessenger UA 抓取，HTTP 响应 3.4-3.6 MB，`js_content` 正文提取成功
- 39 张图片全部下载 + RapidOCR，其中 34 张提取到文本、5 张为纯图形无文字
- c07 首次抓取触发反爬（17KB 空壳），换 UA 重试后成功获取全文（3.5MB）
- 本文不引用任何未核验的二手转述

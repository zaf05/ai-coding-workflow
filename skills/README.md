# skills/ · 角色入口

**instruction-only**：这里没有 CLI、没有编排代码、没有状态机实现。宿主（Codex / Claude Code / ZCode / 任何能读 Markdown 的 Agent）发现 Skill 后，按正文语义执行；`../scripts/` 只做静态校验与安装。

**Skill description 是路由逻辑，不是营销文案**：它要让宿主把请求分给唯一正确的角色，必须写明"何时触发 / 何时不要触发 / 不做什么"。任何 description 都不写"万能""全方位"这类会扩大误触发的词。

```text
skills/
├── aiworflow/               入口路由 + Flow 引擎语义（不是第五角色，不写状态）
├── aiworflow-planner/       唯一状态写入者：需求、Spec、块 DAG、协调、归因、合并
├── aiworflow-implementer/   一次一个块：实现 + 块级自测 + 实现报告
├── aiworflow-reviewer/      只读独立结论：Finding + Verdict（APPROVE/REQUEST_CHANGES/BLOCKED）
├── aiworflow-tester/        测试计划 + 独立验证 + 缺陷证据（含真实浏览器与视口矩阵）
└── _shared/                 共享资源库：contracts / templates / references。**绝不能有 SKILL.md**
```

## 规则位置

正文规则在 `../docs/`，Skill 只保留触发条件、执行摘要与链接（避免两份正文漂移）：

| 主题 | 权威文件 |
|---|---|
| 块类型与字段 | `../docs/02-block-catalog.md` |
| 门禁 / Verdict / 严重度 | `../docs/03-gates.md` |
| 角色所有权与调度 | `../docs/04-roles.md` |
| 状态、证据、产物生命周期 | `../docs/05-state-and-evidence.md` |
| 参数与 Prompt | `../docs/06-parameters-and-prompts.md` |
| 失败、归因、恢复 | `../docs/07-failure-and-recovery.md` |
| 渐进确定性 | `../docs/08-determinism-and-caching.md` |
| AI 编写工作流的护栏 | `../docs/09-authoring-copilot.md` |
| WanGoPlatform 适配 | `../docs/10-wango-adapter.md` |
| 宿主安装 | `../docs/11-toolchain-install.md` |

## 硬约束（所有角色）

1. 任何角色不得批准自己创建或修改的产物。
2. 同一 Run 任一时刻只有一个 Planner 写 `state.yaml`。
3. 角色不派生角色链；需要别人时返回精确交接（`_shared/references/handoff-contract.md`），由主会话发起同级调用。
4. 缺身份/授权/证据 → `BLOCKED` 并写精确缺口，不猜、不代签、不用 Mock 冒充权威验收。
5. 5 分钟无可观察产物中断，30 分钟软检查点；同一 Finding 第二次失败换全新会话。
6. 凭据、Cookie、私钥、真实用户数据、未脱敏日志不得进入任何产物。
7. 在 WanGoPlatform 内，仓库 `AGENTS.md` 与 `docs/develop/agent-delivery-protocol.md` 优先（`../docs/10-wango-adapter.md`）。

## 校验

```bash
python3 ../scripts/validate_package.py     # 结构、frontmatter、相对链接、_shared 无 SKILL.md、模板与工作流一致性
```

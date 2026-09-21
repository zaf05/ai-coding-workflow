# 13 · 路线图（当前事实 vs 未实现）

## 已实现（有可复现证据）

| 能力 | 证据 |
|---|---|
| 两个参考工程完整 clone + 全面扫描 | `references/`；扫描索引 `docs/12-reference-scan.md` |
| 规则与设计文档 19 篇（00–18 + README） | `docs/`，链接、事实与**索引完整性**由 `scripts/validate_package.py` 校验（漏登记任一篇即 FAIL） |
| Skill 包：1 入口 + 4 角色 + `_shared`（8 契约 / 8 模板 / 1 参考） | `skills/`，frontmatter 与相对链接可解析 |
| 工作流定义：4 正例 + 7 反例 | `workflows/`，`validate_workflow.py` 正例通过、反例按预期拒绝；每条反例对应一个专属护栏 ID |
| author-time 硬护栏 7 条（代码强制，非文档承诺） | `scripts/validate_workflow.py`：`secret_inline` / `unsafe_command` / `star_bypass` / `banned_block` / `unbounded_loop` / `unbounded_retry` / `evidence_free_gate`；护栏 ID 必须在 `GUARDRAIL_IDS` 注册，错误输出带 ID；`selftest.sh` §9 逐条断言真实触发并检查无死护栏 |
| 静态校验器 + 安装器 + 自检 | `scripts/`，`bash scripts/selftest.sh` 全绿 |
| Prompt 模板 5 份（static/dynamic 分段，无模板引擎） | `prompts/` |
| 真实 run 记录 | `runs/RUN-20260908-002` doc_fix；`RUN-20260908-004` bugfix-triage pytest；`RUN-20260908-005` ui-verification 双视口；`RUN-20260908-006` feature-delivery 已完成 G0–G10 全链路闭环（intake→recon→spec→decision→approve→plan→implement→check→review→integrate→test→verify_ui→release_check→smoke→notify→close），`run.status=completed`；均 `validate_run.py` PASS（该批 run 磁盘已于 2026-09-20 维护处置后不存在，为历史记录；现行可验证 run 见 `runs/`） |
| Codex 宿主实机加载 | `~/.codex/skills/aiworflow*` 符号链接落地；Codex 以 `qwen3.7-flash + reasoning low` 实测触发 Reviewer 并输出 `verdict=APPROVE` |
| 2025–2026 主流实践调研与吸收 | `docs/14-current-practices.md`：8 条一手/官方来源，结论已对照三层模型 |
| 候选 DAG 编译器（LLM 候选 → 合法产物） | `scripts/compile_dag.py`：归一化已知漂移（id/type/next/字符串 schema_version/star）+ 块数预算上限，委托 `validate_workflow.py` 全量结构规则；正例编译 PASS、三类反例（approve 缺 star / 成环 / 超预算）按预期 REJECT，已并入 `scripts/selftest.sh` 第 6 节 |
| 候选 DAG 生成 Prompt 模板 + 示例 | `prompts/candidate-dag.md`（13 条规则 + STATIC/DYNAMIC 分段）；`prompts/examples/candidate-dag-bugfix.yaml` 完整示例，`compile_dag.py` 编译通过 |
| `run_flow.py` 条件分支 / 重试 / 账本 / 推进模式 | `--evaluate-conditional` 评估 conditional 块分支；`--retry` 回退 failed 块到 pending（attempts +1）；`--append-ledger` 追加账本条目；`--advance` 多轮自动推进（check 自动执行并标记 completed）；conditional 回边不误判为环 |
| 自动化推进闭环（v1.6） | `run_flow.py --advance` 输出 `loop_control` 信号（CONTINUE/DONE/WAIT_USER/WAIT_ROLE/BLOCKED）；`flow-engine.md` 定义完整推进协议（信号表、Agent 伪代码、熔断规则）；`aiworflow/SKILL.md` §3 改写为自动化循环模式；从「单轮决策算法手工推进」升级为「Agent 声明式推进 + 脚本逐轮驱动」 |
| 候选 DAG 全链路文档 | `docs/18-dag-pipeline.md`：意图层 → 编译层 → 冻结层 → 执行层完整说明 |
| 包版本管理与版本锁定（v1.2.0 起，当前 v1.6.0） | `VERSION`（semver 单一事实源）+ 独立 Git 仓库 tag `v1.4.1`（132 文件，`references/` 不入库）；`install_skills.py` 写安装收据 `aiworflow-install-receipt.json`（来源版本/整包指纹/逐文件 SHA256），`--check` 检出目标漂移，`--upgrade` 备份→替换→失败回滚且不触碰收据未登记文件，**存在冲突即拒绝部分安装（零落地、零收据、非 0 退出）**；`selftest.sh` §8 九项断言（含认领已装好但无收据的环境、外来目标拒绝部分安装）+ §9 八项护栏断言，全量 48/48 通过 |
| `runs/` 容器一致性护栏（v1.4.1） | `validate_package.py` 第 10 步：每个 `runs/<ID>` 要么通过 `validate_run.py`，要么在 `runs/README.md` 显式登记为占位；第三种状态（半清理的 run 恒定 FAIL）被拒。理由：恒定 FAIL 会让人和 Agent 习惯性忽略 FAIL，护栏一旦被当噪音就等于没有。`selftest.sh` §3b 用临时负例目录证明它真的会开火，用完即清理 |
| 运行期闸门（pre-commit，v1.4.0） | `scripts/hooks/pre-commit` + `scripts/install_hooks.py`（`--dry-run/--apply/--check/--uninstall`，原子替换、外来 hook 先备份、按标记+SHA 双确认才卸载）；`selftest.sh` §10 七项断言（本体合法、dry-run 不写盘、未装不得谎报、装后 check 通过且幂等、篡改一字节即报漂移、外来 hook 备份/恢复、本副本闸门在位）。端到端实测：干净改动放行；`gate` 缺 `evidence` / `commands` 含 `rm -rf` 的提交被拒且 HEAD 不前进，终端直接给出 `[evidence_free_gate]`、`[unsafe_command]` 与修复建议；补 evidence 后同一提交放行 |

## 未实现（不要用现在时态描述它们）

| 缺口 | 影响 | 下一步 |
|---|---|---|
| **多个 feature-delivery 工作包的连续真实 run** | 当前仅完成一个 FAST 测试文件工作包闭环；多包并行、跨页回归、冲突交叉验证还未被真实 run 覆盖 | 下一次真实业务工作包按入口重新 Entry，保持默认一个活动包，并行最多两个 |
| **GitHub Spec Kit 本地扫描** | 2026-09-08 clone 失败，官方文档已读但本地未扫描 | 网络可用后补 `git clone --depth 1 https://github.com/github/spec-kit.git` 到 `references/spec-kit`，新增 `docs/19-spec-kit-scan.md`（`docs/16` 已被 `16-legacy-and-dag-driving.md` 占用） |
| **Claude Code / ZCode 宿主实机加载** | 只完成文件系统级安装与静态校验，没有对应宿主会话内的真实触发记录 | 在对应宿主开一次会话，记录触发原文与角色交接作为证据 |
| **`run_flow.py` 语义自动化** | **已于 v1.6.0 闭环**：`--advance` 输出 `loop_control` 信号，`flow-engine.md` 定义完整推进协议（5 种信号 + Agent 伪代码 + 熔断）；Agent 根据信号自动循环推进，HANDOFF 后自动调用角色并继续 | 下一次真实 run 时端到端验证 v1.6 自动化推进闭环 |
| **「Planner 真实产出候选 DAG → compile → G4 冻结」链路取证** | 编译器、解释器与 prompt 模板都已就绪，但还没有一次真实 run 由 Planner 用 prompt 模板生成候选 YAML 并走完全链；当前 4 条工作流仍是人工编写模板 | 下一个真实业务工作包由 Planner 用 `prompts/candidate-dag.md` 产出候选 DAG，`compile_dag.py` 编译通过后冻结，记录到 run 证据 |
| **固化（`run_signature`）机制** | `docs/08` 只有规则，没有存固化产物、比对签名、回落 agent 的实现 | 等第一次 run 结束后，把重复出现的 `check` 命令写进工作流定义即可，暂不需要代码 |
| **Prompt 预算与丢弃优先级** | 模板声明了 `max_context_tokens` / `drop_priority`，但没有测量与执行 | 出现上下文超限的真实案例后再实现，避免为假想问题写代码 |
| **`validate_run.py` 的语义检查深度** | 当前只查容器结构、状态合法性、证据引用可达、SHA 格式；不判断证据是否"真的支持结论" | 语义判断留给 Reviewer 角色，脚本不越权 |
| **CI 侧再挂一次 `selftest.sh`** | pre-commit 闸门已于 v1.4.0 落地（`install_hooks.py`），但 `git commit --no-verify` 可绕过任何本地 hook，且换机器/新克隆时闸门需重新 `--apply` 才生效 | 在 CI job 里跑 `bash scripts/selftest.sh` + `python3 scripts/install_hooks.py --check`，失败即阻断合并；这样「绕过本地 hook」不再等于「绕过检查」 |
| **evals / 场景用例库** | 参考工程有 `evals/*.md` 场景用例，我这里还没有 | 每次真实 run 后补一条"可观察决策"用例，不比对精确措辞 |

## 演进顺序（建议）

```text
1. 下一真实 run：用一个纵向业务工作包（非纯测试文件）验证 feature-delivery 全链路，并在 Program 收口集中跑全量单测/构建/E2E
2. Claude Code / ZCode 宿主实机加载取证      → 只在对应宿主会话验证，不伪造
3. 三次 run 后抽取共性                       → 决定哪些块降级为 script/check
4. 出现重复劳动时，把 check/script 命令固化进 workflow 定义，并用 run_flow.py 确定性执行          → 引擎已实现，缓存仍以真实重复为准
5. 累积 5+ 条 evals                          → 才谈"流程回归测试"
```

## 明确不做

- 不做 Web UI、不做数据库、不做队列：本地文件 + Git 就够，多一层运行时多一层不可验证。
- 不做通用编排框架：只服务"一个人 + 若干 AI 角色"的软件交付场景。
- 不把本工作流强推给仓库：`.ai_worflow/` 被 `.gitignore` 忽略（`.gitignore:37`，提交 `d51eeaab`），仓库工作包证据仍按 `docs/develop/agent-delivery-protocol.md` 写入交付报告与计划文档。
- 不引入第三方 Python 依赖：`scripts/` 只用标准库（YAML 解析自带最小实现，检测到 PyYAML 时优先用它）。

## 2026-09-16 新增（来源：`23-reference-scan-20260916.md`）

### 已落地

| 能力 | 来源 | 位置 |
|---|---|---|
| 影响面范围（Blast Radius）：审前/测前产出确定性变更影响文件清单 | a2 code-review-graph + r4 context-mode | `docs/04-roles.md` §影响面范围 |
| 沉淀出口：Finding 修复后回写规则/检查清单/Skill description | a3 + a5 + a1 | `docs/07-failure-and-recovery.md` §沉淀出口 |
| 规则加载验证方法：新会话复述当前规则确认层级覆盖 | a4 AGENTS.md 六大原则 | `docs/11-toolchain-install.md` §验证规则加载 |
| 参考扫描文档（10 来源 + 28 图 OCR 识别 + 5 条改进决策） | 用户指令 | `docs/23-reference-scan-20260916.md` |

### 未来（不本轮实施）

| 能力 | 来源 | 前置条件 |
|---|---|---|
| 浏览器实时验证（console/截图/性能 trace） | r1 chrome-devtools-mcp | Chrome + Node.js + MCP 运行时可用；当前静态站 HTTP 检查已覆盖基线 |
| 全自动 Prompt 进化（反思式变异 + 帕累托择优） | a1 GEPA (arXiv:2507.19457) | 需要足量标注 Finding 数据和评估预算 |
| `<important if>` 指令格式 | r2 humanlayer/skills | 仅 Claude Code 宿主特定；当前多宿主架构优先 |

## 2026-09-17 新增（来源：`24-reference-scan-20260917.md`）

### 已落地

| 能力 | 来源 | 位置 |
|---|---|---|
| Spec 质量反馈：命中度/缺口/误导三维度打分 + 回写闭环 | b3 货拉拉 | `docs/07` §Spec 质量反馈 |
| 调试六步：Reproduce→Isolate→Reduce→Fix→Guard→Verify + Stop-the-Line | b11 Debug Skill | `docs/07` §调试六步 |
| G10 资产沉淀检查：关闭前评估是否产出可复用知识 | b3 货拉拉 | `docs/07` §全生命周期闭环 |
| 参考扫描文档（13 来源 + 126 图 OCR + 3 条改进） | 用户指令 | `docs/24-reference-scan-20260917.md` |

### 未来（不本轮实施）

| 能力 | 来源 | 前置条件 |
|---|---|---|
| Agent 自进化全景（Trace2Skill/RL/微调） | b5 | 需足量轨迹数据和训练预算 |
| Archify 架构图自动生成 | b12 | 站点需要动态架构图时再评估 |

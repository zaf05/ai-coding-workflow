# 17 · 实施证据与注意事项（2026-09-08）

本文记录当天“进行实施”的真实过程、可复现命令、结果与注意事项。结论只写当前事实，不把未实现能力写成已实现。

## 一、背景：本轮讨论结论

用户连续追问，结论已固化在 `16-legacy-and-dag-driving.md`：

1. “LLM 生成 DAG + deterministic 执行”不是 Claude Code 独有，是通用架构。
2. DAG 正确性不能押注单一模型临场脑补，要分层：LLM 意图/候选 → 确定性编译校验 → 冻结 → 执行。
3. 原型可 vibe coding，产品/存量代码必须“行为基线先行 + 小步迁移 + 保真验证 + 证据门禁”。

## 二、本次实施内容

本次在 Codex 上真实推进 `feature-delivery`，并实现 deterministic DAG 解释器 `scripts/run_flow.py`。

`RUN-20260908-006` 已真实跑完：
`intake(G0) → recon(G1) → spec(G2) → decision(G2) → approve(G3, star 真停) → plan(G4) → implement → check → review(G5) → integrate(G6) → test(G7) → verify_ui(G7) → release_check(G8, star 真停) → smoke(G9) → notify(G10) → close(G10)`。

当前状态：
- `run.status=completed`，`current_block_label=close`。
- `completion_contract` CC-01/CC-02/CC-03 全部 `pass`；`open_findings/open_defects/open_blockers` 均为空。
- 未合入 develop、未 push；`.ai_worflow/` 通过本地 `.git/info/exclude` 忽略。

## 三、可复现命令

统一使用 `qwen3.7-plus + high`（与 `~/.codex/config.toml` 一致）。

### 1. 角色会话（Codex 宿主）

```bash
cd /home/feifz/workspace/WanGoPlatform/.ai_worflow

timeout 900 codex exec \
  --ephemeral --skip-git-repo-check \
  -C /home/feifz/workspace/WanGoPlatform \
  -s danger-full-access \
  -m qwen3.7-plus \
  -c model_reasoning_effort=high \
  -o /tmp/<role>-006.out.txt \
  - < /tmp/<role>-006.prompt.txt
```

角色分离：
- Planner 只写 `state.yaml`，不自我 APPROVE；
- Reviewer 只读并输出 `review-xxx.yaml`，不更新 state；
- Tester 跑真实测试并输出 `test-report.yaml`，不改生产代码；
- Implementer 只实现委派块，改测试文件。

### 2. deterministic DAG 引擎

```bash
cd /home/feifz/workspace/WanGoPlatform/.ai_worflow
python3 -m py_compile scripts/run_flow.py

# 只看 frontier（不执行命令）
python3 scripts/run_flow.py workflows/feature-delivery.workflow.yaml runs/RUN-20260908-006

# 真实执行当前 frontier 中的 check/script 命令
python3 scripts/run_flow.py workflows/feature-delivery.workflow.yaml runs/RUN-20260908-006 --execute-check
```

本次已实跑：
- `check` 块执行 `pnpm type-check`，`workdir: wanGo/frontend`，`exit_code=0`，CHECK PASS。
- 已修复工作目录解析：相对路径 `workdir` 一律相对 `state.yaml.repository.root` 解析，不再相对调用脚本时的 CWD。

### 3. 静态校验

```bash
python3 scripts/validate_run.py runs/RUN-20260908-006
python3 scripts/validate_workflow.py workflows/feature-delivery.workflow.yaml
bash scripts/selftest.sh
```

结果：全部 PASS。

## 四、证据

| 证据 | 结果 |
|---|---|
| `run_flow.py` py_compile | PASS |
| `bash scripts/selftest.sh` | 10/10 PASS |
| `validate_workflow.py feature-delivery` | PASS |
| `validate_run.py RUN-20260908-006` | PASS |
| `review.yaml#REVIEW-001` SPEC_REVIEW | APPROVE |
| `review-002-test-plan.yaml` TEST_REVIEW | APPROVE |
| `review-003-code-review.yaml` CODE_REVIEW | APPROVE，0 P0/P1/P2，3 NB |
| `test-report.yaml` | INCREMENTAL PASS，6/6 case FULL coverage |
| `CreateTaskPage.test.tsx` vitest | 6/6 PASS，exit 0 |
| `pnpm type-check` | exit 0 |
| 真实浏览器 `verify_ui` | 1440x900 / 1024x768 / 390x844 三个视口，标题“创建任务”、按钮可见、无 console/pageerror |
| 截图证据 | `runs/RUN-20260908-006/attachments/verify-create-task-*.png` |
| Git | candidate commit `5b9b6941`；本地 integration 分支 `integration/feature-delivery-RUN-20260908-006`；未推远端、未合入 develop |

## 五、注意事项（必须遵守）

1. **沙箱会拒绝 `rm -f` 风格命令**。清理临时文件改用“写新路径/覆盖”，不要用 `rm -f`。
2. **把 prompt 写文件后从 stdin 喂给 codex exec**，避免命令行转义破坏多行中文 prompt。
3. **`codex exec` 输出混合 stdout 与 WARN**：`legacy_notify` hook 失败、MCP 初始化失败是环境噪音，不影响结果；拿最终消息用 `-o <file>` 更可靠。
4. **角色必须真实分离**：Planner 不能自我 APPROVE spec/test/code，必须单独开 Reviewer 会话产出 review 文件。
5. **star 门禁必须真停**：`release_check` 的 `role=reviewer`、`star=true`，在用户明确授权前不得代签，不得继续 smoke/notify/close。
6. **block status 只有 8 个合法值**：`pending/running/completed/failed/terminated/canceled/timed_out/skipped`；不要写 `in_progress`/`ready`。
7. **每步写完必跑 `validate_run.py`**；结构错误当场修，不要攒到最后。
8. **run_flow.py 只做确定性推进，不写 state.yaml**：状态唯一写入者是 Planner；它输出 frontier/STAR/HANDOFF/CHECK 结果。
9. **`workdir` 相对路径必须相对仓库根**，否则从 `.ai_worflow` 调用会跑到错误目录；本次已修复并回归。
10. **不合入 develop、不 push 远端**：这些是破坏性操作，需用户单独授权；本次只建本地 `integration/feature-delivery-RUN-20260908-006` 并 ff-only 合并候选提交。

## 六、当前事实 vs 未实现

- **已实现并有证据**：`scripts/run_flow.py` deterministic DAG 解释器（DAG 构图、环检测、frontier、STAR/HANDOFF/CHECK、check 执行）；`RUN-20260908-006` feature-delivery 全链路 G0–G10 已闭环，`run.status=completed`。
- **仍未实现**：LLM 候选 DAG 自动编译（`validate_workflow.py` 已能校验，但没有“Planner 直出候选 workflow YAML 并自动编译冻结”的确定性生成器）；`run_flow.py` 条件分支/失败重试/账本自动追加尚未由进程执行。
- **不要宣称**：已合入 develop 或已发布；当前只是本地 integration 分支完成一个测试文件工作包，未 merge/push。

## 七、下一步

1. 下一次真实 run：用纵向业务工作包验证 feature-delivery，而不是纯测试文件。
2. 若用户要求合入 `develop` 或 push，需要单独授权；当前本地只保留 integration 分支，已切回/进入 develop 但未合并。
3. DAG 自动拆分下一步：先做“Planner 生成候选 workflow YAML → validate_workflow.py 通过/拒绝 → G4 冻结”的可复现实验。

## 八、2026-09-10 补充实施

### 新增能力

1. **候选 DAG 生成 Prompt 模板**（`prompts/candidate-dag.md`）
   - 13 条规则 + STATIC/DYNAMIC 分段
   - 示例产物：`prompts/examples/candidate-dag-bugfix.yaml`（编译通过）

2. **run_flow.py 语义自动化增强**
   - `--evaluate-conditional <label> <key>`：评估 conditional 块，输出应走分支
   - `--retry <label>`：失败块 attempts +1，状态回退 pending（不超过 max_attempts）
   - `--append-ledger <json>`：向 state.yaml 追加 ledger 条目（带时间戳）
   - `--mark-running` / `--mark-done`：Planner 标记块状态
   - `--advance`：多轮自动推进（check 自动执行并标记 completed，STAR/HANDOFF 阻断）
   - 条件分支回边不再误判为环（`find_cycles` 跳过经过 conditional 块的路径）

3. **条件分支示例工作流**（`workflows/_examples/conditional-feature.workflow.yaml`）
   - 演示 review → conditional(verdict) → integrate / fix_and_re_review 路由

4. **文档**
   - `docs/18-dag-pipeline.md`：候选 DAG 全链路说明
   - `docs/13-roadmap.md`：更新已实现/未实现状态
   - `docs/README.md`：索引加入 doc 18
   - `scripts/README.md`：脚本清单与 run_flow.py 选项说明

### 验证结果

| 检查 | 结果 |
|---|---|
| `bash scripts/selftest.sh` | **18 通过 / 0 失败**（新增 5 项：条件分支、重试、账本、推进、候选编译） |
| `python3 scripts/validate_package.py` | PASS |
| `python3 scripts/validate_run.py runs/RUN-20260908-006` | PASS |
| `python3 scripts/run_flow.py ... RUN-006` | RUN completed，无待执行块 |
| `python3 scripts/compile_dag.py prompts/examples/candidate-dag-bugfix.yaml` | COMPILED |
| `python3 -m py_compile scripts/run_flow.py` | PASS |

### 注意事项

1. **conditional 块的环检测**：经过 conditional 块的循环路径不算真环（是有意循环分支），`find_cycles()` 会检查环路径中是否包含 conditional 块。
2. **`--advance` 的自动标记**：只有 check/script 块执行通过后会**自动标记 completed**并继续推进；STAR 和 HANDOFF 仍然阻断，需要角色会话处理。
3. **`--retry` 只写 state.yaml**：不自动重新执行块，只是把状态回退到 pending，让下一轮 frontier 计算重新包含它。
4. **`--append-ledger` 的 `appended_at`**：自动添加时间戳，不需要调用方提供。
5. **写操作需要 PyYAML**：`--retry`、`--append-ledger`、`--mark-*`、`--advance`（check 自动标记）都需要写 state.yaml，如果没有 PyYAML 会报错。只读操作（默认 frontier 报告、`--evaluate-conditional`）不需要 PyYAML。

## 九、2026-09-10 正确性验证（12 项）

用户要求「必须保证 AI 工作流正确」，执行全量正确性检查。

### 检查清单

| # | 检查项 | 结果 |
|---|---|---|
| 1 | `selftest.sh`（18 项：工作流校验、包校验、编译器、解释器新功能） | 18/18 PASS |
| 2 | 所有工作流定义校验（4 正例 + 1 示例 + 3 反例） | 全部 PASS/按预期拒绝 |
| 3 | `validate_package.py`（Skill 结构、链接、frontmatter、模板、Prompt、工作流） | PASS |
| 4 | `validate_run.py RUN-20260908-006` | PASS |
| 5 | `run_flow.py` 对 RUN-006（已完成 run） | completed，无待执行块 |
| 6 | Skill frontmatter 完整性（5 个 Skill） | 全部有 name+description |
| 7 | 文档内部链接一致性（docs/README.md → docs/*.md） | 全部有效 |
| 8 | Prompt 模板 STATIC/DYNAMIC 标记（7 个模板） | 全部正确 |
| 9 | 工作流块引用一致性（next_block_label / branch next / finally） | 全部一致 |
| 10 | RUN-006 state.yaml 完整性（16 块 / 11 门禁 / 4 审批 / 3 契约） | 完整且一致 |
| 11 | run_flow.py 边界条件（6 项：terminal / retry 超限 / invalid status / non-conditional / invalid JSON / STAR 阻断） | 6/6 正确处理 |

### 结论

**AI 工作流当前状态正确。** 所有自动化校验、结构一致性、逻辑边界条件均通过验证。

### 可复现命令

```bash
cd /home/feifz/workspace/WanGoPlatform/.ai_worflow
bash scripts/selftest.sh                    # 18/18
python3 scripts/validate_package.py         # PASS
python3 scripts/validate_run.py runs/RUN-20260908-006  # PASS
python3 scripts/run_flow.py workflows/feature-delivery.workflow.yaml runs/RUN-20260908-006
# → RUN completed 已终结；无待执行块。
```

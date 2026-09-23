# 项目画像：AIWorflow

> 首次记录：2026-09-17 | 最近更新：2026-09-23

## 架构概要

- 当前版本：v1.8.13。
- v1.8.13 真实断点恢复实证 + 条件求值修复：RUN-20260923-001（bugfix-triage）在 intake/recon/classify 完成后故意中断（ledger INTERRUPT + 五件套写全），全新零共享上下文恢复会话经 `task_resume.py` 接续 implement→test→close，F1-R 五条验收 C1..C5 全 PASS——L3 从"组件级机器断言"升级为"真实断点恢复已实证"（docs/29；多天 Session×Run 级联仍协议层）。同包修复 DEFECT-001：`--evaluate-conditional` 此前只实现 `equals`、expression 分支被静默忽略恒落 default；现为受限文法求值（`true` / `ident == 'literal'`，文法外 `AIW_INERT_CONDITIONAL` 显式 FAIL）+ 编写期护栏 `inert_conditional`（引擎与校验器共用 `parse_conditional_expression`，零文法漂移）。
- v1.8.12 引擎完整性加固（Codex）：workflow SHA 首触冻结 + `AIW_WORKFLOW_DRIFT` 拦截、mark-done 证据锚点门、implement 块强制 `--head-sha`、check/script 块禁止手工完成、全块终态自动收口（finally 被跳过时拒绝）、`--refreeze-workflow` 受控迁移；selftest 70→88。
- v1.8.11 参考收编：微信《Loop engineering》（淘天·苏雄）对照批入附录 124→130（`docs/35`）；五组件印证既有设计，automations 心跳层登记 `docs/13` 未实现表（触发条件绑定，不预写代码）。
- v1.8.10 真实任务闭环：RUN-20260921-001 首个以真实业务任务（六功能域只读评审）驱动完整走过 Planner 段→G3 用户亲签→评审-only 合法收尾的 run（validate_run PASS、`--advance` DONE）；沉淀规则见 `docs/07`（侦察 fan-out 启动清单）与 `docs/05`（评审-only 收尾处方）。
- 形态：纯文件驱动的块 DAG + 四角色门禁；`.ai_worflow/` 在 WanGoPlatform 主仓被 `.git/info/exclude` 忽略。**本目录是独立 git 仓库**（v1.8.2 自建 → v1.8.3 撤销 → 2026-09-20 21:02 重新自建 `d551273`，remote `zaf05/ai-coding-workflow`，2026-09-21 用户确认保留；pre-commit hook v3 双布局在位——主仓与本仓 `.git/hooks/` 各一份，布局 B 生效）。
- v1.8.0 运行期强制执行三件套：`validate_transition.py`（写入时 T-01..T-04，Planner 覆写 state 前先 `cp state.yaml state.prev.yaml`）、`validate_run.py` 新增 R-1/R-2/R-3（DAG 语义一致性）、`check_all.py` 全系统日检。
- v1.8.1 规则生命周期双向闭环：任务后能力观察（Add 发现机制）+ 删减判据四信号（误伤≥2/无人消费/重复实现/模型升级替换与供应商切换复检）。
- 2026-09-20 双宿主实测：Codex（`codex exec` 只读探针，默认模型）与 Claude Code（嵌套 `claude -p` 会话）均能发现/注册并实读 aiworflow* skill；两宿主 `install_skills.py --check` 收据 1.8.9 指纹一致。注意 Codex 探针的 `qwen3.7-flash` 模型已下线（模型不存在报错），需用 config.toml 默认模型。
- `selftest.sh` 当前 70/70（站点在线；离线 69/69 + 1 SKIP）。§4 同来源根时用 `install_skills.py --check` 硬断言收据指纹，修复 dry-run 假 PASS；§7d-ter 验证 `--session-meta` 归因与非法输入拒绝；§7d-quatro 验证 review preflight 正例/负例；§11 验证架构一致性、HTML/README 版本一致与 G4/TDD Red 篡改负例；§13 覆盖长周期恢复链，其中 §13c-bis 验证 task_resume 消费 checkpoint/state/ledger 与副作用不重复规则。

## 关键文件

| 文件 | 作用 | 注意事项 |
|---|---|---|
| `scripts/validate_consistency.py` | G0–G10/TDD/Review/context 三方一致 | 修改 docs、workflow 或 HTML 流程图后必须运行 |
| `scripts/validate_transition.py` | state.yaml 写入时迁移校验（T-01..T-04） | Planner 覆写 state 前先快照 `state.prev.yaml` |
| `scripts/review_preflight.py` | CODE/RELEASE Review 前置确定性检查 | 只读 diff；secret/禁改区/破坏性命令 FAIL，规模超限 WARN；默认 stdout |
| `scripts/check_all.py` | 全系统日检（逐 run + 陈旧检测 + 收据/闸门汇总） | 只读不代写；WARN 不拉低退出码 |
| `scripts/selftest.sh` | 95 项全量自检（站点在线口径） | §11 架构一致性护栏；§13 长周期恢复链护栏；§14 README/HTML 数字一致性 |
| `scripts/task_resume.py` | 长周期任务断点恢复提示词生成 | 消费 task/checkpoint/state/ledger；task.yaml 缺失或结构不可用退出 2；L3 断点恢复已由 RUN-20260923-001 实证 |
| `VERSION` | 单一版本事实源 | 变更后必须 `install_skills.py --upgrade --apply` 并 `--check` |
| `context/` | 跨 Run 知识库 | G1 必读，G10 必写 |

## 构建与验证命令

```bash
cd .ai_worflow
python3 scripts/validate_consistency.py
python3 scripts/validate_workflow.py workflows/feature-delivery.workflow.yaml
python3 scripts/validate_package.py
bash scripts/selftest.sh
python3 scripts/check_all.py
```

## 来源

- RUN-20260917-006：真实中型优化 Run，完成 TDD Red→Green 与跨 Run context 读写。
- docs/31（P0–P3 实施记录）与 2026-09-20 维护处置：v1.8.0–v1.8.6 演进依据见各对应文档。
- docs/29 §2026-09-20 修订与 docs/30 §十一/§十二：v1.8.7（session-meta + review_preflight）与 v1.8.8（checkpoint 消费 + 串行边界 + human_summary + 模型替换复检）依据；selftest §7d-ter/§7d-quatro/§13c-bis 为机器证据。
- docs/34（2026-09-20 全网检索批）与 docs/29 独立检查结论：v1.8.9（4 条 P3 收口 + 附录 087–124 入索引）依据；外部参考来源 86→124。
- docs/35（2026-09-21 Loop Engineering 收编批）：v1.8.11 依据；外部参考来源 124→130，心跳层缺口登记 docs/13。
- RUN-20260921-001：v1.8.10 依据——真实 G3 人工门评审 run 的事故与处方（fan-out 错域重试、skip 凭据、test-plan N/A、亲签出处落位）。
- RUN-20260923-001：v1.8.13 依据——L3 断点演练五条取证（C1..C5）、DEFECT-001 复现/修复/护栏反例全链证据；候选 b84a7b4。

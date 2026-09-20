# 项目画像：AIWorflow

> 首次记录：2026-09-17 | 最近更新：2026-09-20

## 架构概要

- 当前版本：v1.8.9。
- 形态：纯文件驱动的块 DAG + 四角色门禁；`.ai_worflow/` 在 WanGoPlatform 主仓被忽略，只作本地过程/规则索引。**本目录不是 git 仓库**（v1.8.3 按用户决定撤销本地仓库，本目录不入任何版本库；pre-commit hook v3 装于主仓 `.git/hooks/`，布局 A）。
- v1.8.0 运行期强制执行三件套：`validate_transition.py`（写入时 T-01..T-04，Planner 覆写 state 前先 `cp state.yaml state.prev.yaml`）、`validate_run.py` 新增 R-1/R-2/R-3（DAG 语义一致性）、`check_all.py` 全系统日检。
- v1.8.1 规则生命周期双向闭环：任务后能力观察（Add 发现机制）+ 删减判据四信号（误伤≥2/无人消费/重复实现/模型升级替换与供应商切换复检）。
- `selftest.sh` 当前 70/70（站点在线；离线 69/69 + 1 SKIP）。§4 同来源根时用 `install_skills.py --check` 硬断言收据指纹，修复 dry-run 假 PASS；§7d-ter 验证 `--session-meta` 归因与非法输入拒绝；§7d-quatro 验证 review preflight 正例/负例；§11 验证架构一致性、HTML/README 版本一致与 G4/TDD Red 篡改负例；§13 覆盖长周期恢复链，其中 §13c-bis 验证 task_resume 消费 checkpoint/state/ledger 与副作用不重复规则。

## 关键文件

| 文件 | 作用 | 注意事项 |
|---|---|---|
| `scripts/validate_consistency.py` | G0–G10/TDD/Review/context 三方一致 | 修改 docs、workflow 或 HTML 流程图后必须运行 |
| `scripts/validate_transition.py` | state.yaml 写入时迁移校验（T-01..T-04） | Planner 覆写 state 前先快照 `state.prev.yaml` |
| `scripts/review_preflight.py` | CODE/RELEASE Review 前置确定性检查 | 只读 diff；secret/禁改区/破坏性命令 FAIL，规模超限 WARN；默认 stdout |
| `scripts/check_all.py` | 全系统日检（逐 run + 陈旧检测 + 收据/闸门汇总） | 只读不代写；WARN 不拉低退出码 |
| `scripts/selftest.sh` | 70 项全量自检（13 分组，站点在线口径） | §11 是架构一致性护栏；§13 是长周期恢复链护栏 |
| `scripts/task_resume.py` | 长周期任务断点恢复提示词生成 | 消费 task/checkpoint/state/ledger；task.yaml 缺失或结构不可用退出 2；真实 L3 断点演练未执行 |
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

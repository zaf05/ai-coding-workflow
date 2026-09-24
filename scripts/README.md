# scripts/ · 校验器、编译器与执行器

运行环境：Python 3 + bash；复用当前环境已有 PyYAML，未新增 pip/npm/数据库依赖。部分只读脚本提供 `_yaml_min.py` fallback；`run_flow.py` 写 state、`review_preflight.py` 读取 state 时使用 PyYAML。

## 脚本清单

| 脚本 | 职责 | 用法 |
|---|---|---|
| `validate_workflow.py` | 校验工作流 DAG 与 7 条 author-time 硬护栏 | `python3 scripts/validate_workflow.py <file>` |
| `validate_package.py` | 校验 Skill 结构、链接、模板、docs 索引与 runs 容器 | `python3 scripts/validate_package.py` |
| `validate_run.py` | 校验 run 容器与 DAG 语义一致性 | `python3 scripts/validate_run.py <runs/RUN-ID>` |
| `validate_transition.py` | state 写入后校验 T-01..T-04 越权/状态机/gate/人工证据 | `python3 scripts/validate_transition.py <runs/RUN-ID>` |
| `validate_consistency.py` | 校验 G0–G10 三方一致，以及 VERSION/README/HTML 标题版本一致 | `python3 scripts/validate_consistency.py` |
| `validate_content_quality.py` | 在线检查文档站内容重复、矛盾与陈旧表述 | `python3 scripts/validate_content_quality.py --base <url>` |
| `validate_site_consistency.py` | 在线检查文档站页面、链接、权限与 API 引用 | `python3 scripts/validate_site_consistency.py --base <url>` |
| `compile_dag.py` | 候选 DAG 归一化、结构校验与预算检查 | `python3 scripts/compile_dag.py <candidate.yaml>` |
| `run_flow.py` | DAG frontier / check / 条件分支 / 重试 / 账本 / 自动推进 | `python3 scripts/run_flow.py <workflow> <run-dir>` |
| `review_preflight.py` | CODE/RELEASE Review 前置确定性检查：secret、禁改区、破坏性命令、规模 | `python3 scripts/review_preflight.py <run-dir>` |
| `task_resume.py` | 生成 task+checkpoint+state+ledger 恢复提示词 | `python3 scripts/task_resume.py <run-dir>` |
| `check_all.py` | 全系统日检：逐 run、陈旧 run、收据与 hook 汇总 | `python3 scripts/check_all.py` |
| `list_runs.py` | 只读 run 聚合视图：逐 run 状态/轮次/返修/跨度 + 汇总基线（`_yaml_min` fallback，不写任何文件） | `python3 scripts/list_runs.py [--runs-dir runs]` |
| `install_skills.py` | 双宿主 Skill 安装、收据、漂移检测与原子升级 | `python3 scripts/install_skills.py --check` |
| `install_hooks.py` | pre-commit 安装、校验、备份与卸载 | `python3 scripts/install_hooks.py --check` |
| `hooks/pre-commit` | 提交闸门，selftest 失败即拒绝提交 | 由 `install_hooks.py` 安装 |
| `selftest.sh` | 全量自检；当前站点在线 112/112，离线 111/111 + 1 SKIP | `bash scripts/selftest.sh` |
| `_yaml_min.py` | 最小 YAML 读取 fallback | 被脚本 import |

## run_flow.py 选项

| 选项 | 说明 | 写 state |
|---|---|---|
| 默认 | 输出 frontier 报告 | 否 |
| `--execute-check` | 真实执行 check/script 命令 | 否 |
| `--advance` | 按 ready 顺序自动推进 | 是（check 自动标记 + ledger） |
| `--session-meta <json>` | `model` 必填；`tokens_used` 为非负整数或 `null`，随 ledger 与报告归因 | 是（写入 ledger） |
| `--evaluate-conditional <label> <key>` | 评估条件分支 | 否 |
| `--retry <label>` | 重试失败块 | 是 |
| `--append-ledger <json>` | 追加账本条目 | 是 |
| `--mark-running <label>` | 标记块 running | 是 |
| `--mark-done <label> [--status ...]` | 标记块 completed/failed/skipped | 是 |

## review_preflight.py

- base/head/root 默认读 `state.yaml:repository`，也可用 `--base/--head/--root` 显式覆盖；
- 只检查已提交 diff，默认输出 stdout，保持 Reviewer 只读；Planner 明确授权时才用 `--output` 写持久报告；
- `SECRET_SCAN`、`PROTECTED_PATHS`、`DESTRUCTIVE_COMMANDS` 出现 FAIL 时退出 1；
- `REVIEW_SIZE` 超过文件数/变更行阈值时仅 WARN，不自动放行或阻断；
- 报告不回显 secret 原文，只给文件、行号和脱敏证据。

## 版本锁定

`VERSION` 是单一事实源。`install_skills.py --apply` 写 `aiworflow-install-receipt.json`（来源版本、指纹、逐文件 SHA256）；`--check` 判断来源升级或目标漂移；`--upgrade --apply` 只替换收据登记文件。未登记目标、外来冲突和漂移目标都拒绝部分安装或拒绝认领。

pre-commit hook 不能阻止 `git commit --no-verify`，换机器也需重新安装；因此规则变更后仍必须手动运行 `selftest.sh` 与 `check_all.py`。

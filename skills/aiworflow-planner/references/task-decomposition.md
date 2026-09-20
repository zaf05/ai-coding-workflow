# 拆块参考

权威来源：`../../../docs/02-block-catalog.md`、仓库交付协议切分门禁。本文件是执行摘要。

## 块粒度

一个块 = 一个完整纵向动作，不是实现步骤。块内步骤由角色自行分解，不升级成新块（否则门禁递归爆炸）。

## 切分门禁（WanGo 仓库口径）

目标 15 文件 / 1,500 行 / 80 KB，硬上限 25 文件 / 2,500 行 / 120 KB。
文件数计全部修改文件（生成物也计）；行数计非生成代码新增+修改行；Review Packet 计实际完整任务包字节数。
超硬上限不得开工，必须拆包；仅原子迁移或不可分割生成物一致性可经用户批准例外。

## 拆包原则

- 默认一个纵向业务场景或一个不可拆共享底座。
- 多文件/步骤多/交接材料多本身不是拆分理由。
- 只有真实依赖/发布/权限/所有权边界才拆分。
- 公共生成物与集成入口由协调者串行处理，并行包文件所有权不重叠。

## 冻结例外

初始 DAG 经 G2 冻结后，只有已证实无法在原块内安全完成 AC 的结构性障碍才改图，且只改受影响节点并复审，不重建全图。

## 候选 DAG 生成与编译（自动拆分层）

当需求没有匹配的现成 `workflows/*.workflow.yaml` 模板，或需要按本次业务裁剪块链时：

1. 你（Planner）按本文件的块粒度与拆包原则产出**候选** workflow YAML：
   - 顶层键与模板一致（`schema_version: 1`、`name`、`workflow_id`、`blocks`、`error_code_mapping`、`finally_block_label`）；
   - 每块必须有 `label`、`block_type`、`role`、`goal`、`complete_criterion`；`approve` 块必须 `role: user` + `star: true`；
   - 块数默认不超过 40（`compile_dag.py --max-blocks`），超过说明工作包本身该拆。
2. 候选写入 run 目录（如 `runs/<RUN-ID>/candidate.workflow.yaml`），然后执行：

```bash
python3 scripts/compile_dag.py runs/<RUN-ID>/candidate.workflow.yaml -o runs/<RUN-ID>/workflow.compiled.yaml
```

3. `COMPILED` 才可冻结：把 `workflow_path` 指向编译产物，走 SPEC_REVIEW（G2）→ 用户批准（G3）→ 冻结；`REJECT` 时按打印的违规项修正候选后重编译，不得绕过校验器手改产物。
4. 冻结后用 `python3 scripts/run_flow.py <workflow.compiled.yaml> runs/<RUN-ID>` 推进 frontier；check/script 块加 `--execute-check` 实跑命令。

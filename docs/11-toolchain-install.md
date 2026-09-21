# 11 · 宿主安装与发现

本工作流是 **instruction-only** 包：没有 CLI、没有守护进程、没有编排脚本。宿主发现 Skill → 角色按 `SKILL.md` 执行语义 → `scripts/` 只做静态校验与安装。

## 单一事实源与三份薄配置

参考 `references/ric-dev-workflow-skills` 的实测布局（95 文件，commit `84954fb`）：

```text
.agents/skills/<role>/SKILL.md        唯一事实源（正文）
.agents/skills/<role>/agents/openai.yaml   Codex 界面/策略元数据（4 行）
.claude/agents/<role>.md              Claude Code 原生子代理（薄，指回 SKILL.md）
.claude/skills -> ../.agents/skills    符号链接复用，不复制正文
.zcode/agents/<role>.md               ZCode 原生子代理（薄，指回 SKILL.md）
.codex/agents/<role>.toml             Codex 子代理（含 sandbox_mode / developer_instructions）
.codex/config.toml                    [agents] enabled = true
```

其 `AGENTS.md` 的硬规则我原样采纳：

- `_shared`（其 `_devflow_shared`）**绝不能包含 `SKILL.md`**，否则会被发现成第五角色。
- 薄配置只指回事实源，**不复制规则正文**；按真实路径去重计数，不创建 adapters 或额外规则副本。
- 目录存在 ≠ 实机加载。ZCode/Claude 的原生 agents 必须按官方文档安装到用户级后才承诺加载，"不能把目录存在当作实机验证"。
- 角色工具白名单按最小权限：Reviewer 只有 `Read, Grep, Glob`（实测 `.claude/agents/devflow-reviewer.md` frontmatter），Codex 侧 `sandbox_mode = "read-only"`（实测 `.codex/agents/devflow-reviewer.toml`）。白名单不是文件路径沙箱，不得夸大隔离保证。

## 安装模式

`scripts/install_skills.py` 支持三种模式，**默认 dry-run**：

| 模式 | 行为 | 用途 |
|---|---|---|
| `--dry-run`（默认） | 只打印将要创建的链接/文件与冲突 | 先看清单 |
| `symlink` | 目标目录下创建指向 `skills/<name>` 的符号链接 | 改一处全生效，推荐 |
| `copy` | 复制文件（跳过已存在且内容相同的） | 宿主不支持软链时 |

```bash
python3 scripts/install_skills.py --dry-run
python3 scripts/install_skills.py --target "$HOME/.codex/skills" --mode symlink --apply
python3 scripts/install_skills.py --target "/home/feifz/workspace/WanGoPlatform/.agents/skills" --mode symlink --apply
```

安全规则：不覆盖已存在的非本包文件——**存在冲突即拒绝部分安装**（一个文件都不装、不写收据、返回非 0；实测旧行为会装其余 5 个并写下覆盖全部 6 个 Skill 的收据、返回 0，等于收据为它没装的文件作伪证）；`--apply` 装完立刻用与 `--check` 相同的标准复核，任何缺失/不一致都不写收据；不删除任何目标目录内容；不写仓库受跟踪路径，除非 `--target` 显式指向它并经用户确认。

## 版本锁定（v1.2.0 起，v1.2.1 补认领路径，v1.3.0 落地硬护栏，v1.4.0 拒绝部分安装）

「目录存在 ≠ 实机加载」还有一半：**装上了 ≠ 装的是哪一版、有没有被手改**。v1.2.0 起安装即记账。

| 事实 | 位置 |
|---|---|
| 包版本单一事实源 | 仓库根 `VERSION`（semver） |
| 版本历史 | 本目录独立 Git 仓库（v1.8.2 自建 → v1.8.3 撤销 → 2026-09-20 21:02 重新自建，init import `d551273`，分支 `main`，remote `zaf05/ai-coding-workflow`，暂无 tag；2026-09-21 用户确认保留）；父仓库经 `.git/info/exclude` 排除本目录 |
| 目标机器安装事实 | `<target>/aiworflow-install-receipt.json`（收据，**不入来源库**） |

收据记录 `source_root` / `source_version` / `source_fingerprint` / `mode` / `installed_at` / `manifest`（逐文件 SHA256）。

| 要回答的问题 | 命令 |
|---|---|
| 目标装的是哪一版 | `install_skills.py --target <dir> --check` |
| 有没有人绕过流程手改 | 同上；输出会列出漂移文件 |
| 来源升级后如何同步 | `install_skills.py --target <dir> --upgrade --apply` |
| 已装好但没收据，怎么补 | `install_skills.py --target <dir> --apply`（认领：不改 Skill 文件，只补收据；与来源有漂移则拒绝并非零退出） |

`--upgrade` 的原子性：先把收据登记的 Skill 移到时间戳备份目录 → 安装新版本 → 回写收据；任一步失败则把备份原样搬回。**收据未登记的文件一律不动**，因此不会误删宿主自己的 Skill。

这些行为由 `scripts/selftest.sh` §8 的 9 项断言覆盖（semver 合法性、apply 写收据且 check 一致、手改必须被判漂移、upgrade 后恢复一致、宿主文件不受影响、认领已装好但无收据的环境、漂移目标拒绝认领、dry-run 认领不落盘、**外来目标拒绝部分安装且零收据零落地**），全量自检 48/48 通过（§3 另有 `runs/` 墓碑护栏负例、§9 另有 8 项硬护栏断言、§10 另有 7 项运行期闸门断言）。

## 运行期闸门（pre-commit，v1.4.0 起）

author-time 护栏解决了「写坏的定义过不了校验」，但**校验只在有人运行时才发生**。v1.4.0 把它下沉到提交动作本身：

```bash
python3 scripts/install_hooks.py --dry-run   # 先看将做什么
python3 scripts/install_hooks.py --apply     # 安装到 .git/hooks/pre-commit（原子替换）
python3 scripts/install_hooks.py --check     # 复核：未装/非本包产物/漂移/无执行位 → 全部非 0
python3 scripts/install_hooks.py --uninstall --apply   # 卸载自己的 hook 并恢复外来备份
```

为什么需要安装器而不是把 hook 直接放仓库根：`.git/hooks/` **不入版本库**，所以「hook 已装」必须是可验证事实，不能靠假设——与安装收据同一套思路。hook 本体版本化在 `scripts/hooks/pre-commit`。

| 事实 | 说明 |
|---|---|
| 阻断级 | `selftest.sh` 任一项失败即拒绝提交，并把 `[护栏ID] 位置: 具体问题 + 怎么改` 打到终端 |
| 警告级 | 安装收据与来源不一致时只警告不阻断：symlink 模式下已装副本内容始终与仓库同步，漂移只是版本台账滞后，发布前 `install_skills.py --apply` 刷新即可 |
| 不越界 | 发现外来 hook 先备份为 `pre-commit.foreign-backup-<ts>` 再安装，`--uninstall` 能原样恢复；卸载只删带标记的自己的产物 |
| 可移植 | `selftest.sh` §4 与 §10.7 只在「本机收据来源根＝本工作副本」时硬断言，换机/克隆/多副本并存时显式 SKIP——否则闸门会在任何非规范机器上把所有提交拦死 |
| 已知边界 | `git commit --no-verify` 可绕过任何 pre-commit hook。这是 Git 的既有设计，本包**不声称能阻止**；因此 `docs/13-roadmap` 把「CI 侧再挂一次」列为下一层 |

## Codex

- 发现路径：项目 `.agents/skills/`（当前仓库已有 `wango-delivery`）或用户 `$CODEX_HOME/skills/`。
- `SKILL.md` frontmatter 必需 `name` + `description`；`description` 必须具备区分度（写清"什么时候用/什么时候不用"），否则触发会漂移到别的 Skill。
- 需要子代理语义时，另写 `.codex/agents/<name>.toml`：`name`、`description`、`model_reasoning_effort`、`sandbox_mode`、`developer_instructions`。`developer_instructions` 只写"用哪个 Skill + 一次只做一个动作 + 输出契约"，不复制正文。
- `agents/openai.yaml`（Skill 内）写界面元数据：`interface.display_name`、`interface.short_description`、`policy.allow_implicit_invocation`。Reviewer/Tester 建议 `allow_implicit_invocation: false`（只在显式调用或精确委派时激活）。

## Claude Code

- `.claude/skills` 用符号链接指向 `.agents/skills`，避免两份正文漂移。
- 子代理写 `.claude/agents/<name>.md`，frontmatter：`name`、`description`、`model: inherit`、`tools:`。
- 薄配置正文四件事：只在被宿主实际启动时承担该身份；读事实源 SKILL.md 的绝对路径；不再派生同名或其他角色；缺身份信息就报缺口而不是猜。

## ZCode / 其他宿主

- ZCode 已支持发现 `.agents/skills`；用户级 agents 需按官方文档安装后才算加载。
- `.zcode/agents/<name>.md` frontmatter 可含 `injectAgentsMd: true`（注入不替代检查局部规则）。
- 通用宿主：只要能读 Markdown，就把 `skills/<role>/SKILL.md` 路径 + 交接身份（`_shared/references/handoff-contract.md`）作为系统提示喂进去。

## Skyvern 的多副本教训（反面参考）

`references/skyvern/skyvern/cli/skills/qa/SKILL.md` 顶部有一段 NOTE：`.agents/skills/qa/SKILL.md` 是仓库 canonical 源，另有两份同步副本（pip 包内 `skyvern/cli/skills/qa/SKILL.md`、MCP prompt 常量 `skyvern/cli/mcp_tools/prompts.py: QA_TEST_CONTENT`），要求三处保持同步。**多副本靠人肉同步必然漂移**；因此本工作流规定：正文只有一份，宿主侧一律软链或薄指针，任何"复制正文"的提案都要在 `evidence.md` 写明理由与同步责任人。

## 安装后验证（最小集）

```bash
python3 scripts/validate_package.py                       # 结构/frontmatter/链接/模板/工作流
python3 scripts/validate_workflow.py workflows/*.workflow.yaml
bash scripts/selftest.sh                                  # 正例 + 反例
ls -l "$HOME/.codex/skills" | grep aiworflow              # 链接是否落地
```

**当前事实**：Codex 已实机加载并产出真实 Run（历史 `RUN-20260908-002` 磁盘已不存在，现行可验证 Run 见 `runs/`，如 `RUN-20260920-003` `validate_run.py` PASS）。Claude Code 侧已于 2026-09-20 完成实机触发验证：嵌套 `claude -p` 只读探针会话的系统 skill 清单实际注册全部 5 个 `aiworflow*` skill，并经 `~/.claude/skills` 符号链接实读 SKILL.md / 安装收据（source_version 1.8.9）/ `_shared/contracts`；两宿主 `install_skills.py --check` 收据指纹一致。ZCode 侧仍只完成文件系统安装与静态校验，未做实机触发验证；该宿主的实机加载证据必须来自对应宿主会话内的真实触发记录，不能由目录或安装成功推断。模型/参数选择见 `15-execution-model.md`。

## 验证规则加载生效

> 依据：`23-reference-scan-20260916.md` C3（来源 a4 给 Codex 写高质量 AGENTS.md）。

安装完成后，不要凭感觉判断规则已生效。在仓库根目录启动一次新会话，要求 Agent 复述当前加载的规则：

```
Summarize the current instructions you have loaded.
```

如果项目使用了子目录覆盖，再从目标目录检查：

```
List the instruction sources you loaded and summarize the effective rules.
```

必须确认三件事：

1. 加载了正确的文件（全局 / 仓库 / 子目录层级齐全）；
2. 局部规则覆盖了冲突的上层规则（子目录 > 仓库 > 全局）；
3. 最关键的构建、测试和安全边界没有被遗漏或截断。

如果任一项不满足，检查 Skill 安装路径、符号链接和宿主的 instruction 发现机制。

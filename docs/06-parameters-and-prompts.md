# 06 · 参数系统与 Prompt 模板

## 参数类型

借自 Skyvern `ParameterType`（`references/skyvern/skyvern/forge/sdk/workflow/models/parameter.py`），去掉云厂商专有项，保留"秘密是一等公民"的设计。

| parameter_type | 语义 | 必填字段 | 约束 |
|---|---|---|---|
| `workflow` | Run 入参 | `key`、`value_type` | `value_type ∈ string/integer/float/boolean/json/file_url/secret_ref`；`required` 或 `default` 至少一项 |
| `context` | 由上游块输出注入 | `key`、`source` | `source` 必须是已声明的 `output_parameter` 或 `<label>.output` |
| `output` | 块输出键 | `key` | 每个 `output_parameter` 自动成为可引用输出 |
| `secret` | 凭据/密钥**引用** | `key`、`source` | `source` 形如 `env:NAME`、`file:PATH`、`vault:ID`；**禁止** `default`、`value`、内联字面量 |
| `env` | 运行环境事实 | `key`、`source` | 例如 `env:WANGO_DEV_DB`；只读，不得写入证据明文 |

设计要点（来自 Skyvern 的两个教训）：

1. **秘密必须走参数引用，不能内联。** Skyvern 用 `ParameterType.is_secret_or_credential()` 与 `is_sensitive_workflow_parameter()` 做单一事实源过滤，脚本生成、日志与审核路径都复用它，避免秘密被写进生成代码或持久化失败产物。我这里由 `validate_workflow.py` 以护栏 `secret_inline` 静态拒绝：`secret`/`credential` 类参数出现 `value`/`default`/`default_value`/`literal` 即拒绝；非 secret 参数的值与 `commands[].cmd` 若命中凭据字面量模式（`password=`、`api_key:`、`-----BEGIN`、`AKIA…`）同样拒绝；并在 Prompt 渲染时要求脱敏。
2. **保留字不可被用户参数覆盖。**

```text
current_item  current_value  current_index  current_date
run_id  workflow_id  workflow_permanent_id  block_label
run_outputs  run_summary  base_sha  head_sha  tested_sha
```

## 值类型转换与校验

`workflow` 参数在 Run 启动时按 `value_type` 转换；转换失败立即失败，不做静默兜底（Skyvern `WorkflowParameterType.convert_value` 的语义：布尔只接受 `true/false/1/0`，JSON 必须是合法结构，否则抛 `InvalidWorkflowParameter`）。

## 模板引用

块字段中可模板化的部分用 `{{ key }}` 引用参数或上游输出：

```yaml
- label: implement_wp1
  block_type: implement
  goal: "在 {{ target_module }} 内实现 {{ ac_summary }}"
  inputs: [target_module, ac_summary, "spec.output"]
```

规则：

- 只有声明为可模板化的字段才渲染（Skyvern 的 `TEMPLATABLE_FIELDS` 按 MRO 求并集，子类不能遮蔽父类）；未声明字段原样保留，避免把秘密或代码当模板执行。
- 渲染前先做**缺失变量预检**：引用了未声明的参数 → 校验期报错，而不是运行期渲染出空串。
- 渲染后做**秘密检测**：若渲染结果包含已注册秘密值，拒绝把它写入生成代码、错误码或持久化失败产物（Skyvern `_contains_registered_secret` 的无长度下限版本用于"拒绝写入"，带长度下限的版本用于"删除数据"，两种场景阈值不同，这个区分值得保留）。

## Prompt 模板规范

模板放 `prompts/`，纯 Markdown + `{{ 变量 }}` 占位，**不依赖任何模板引擎**（宿主的 Agent 直接读文本填充）。

### static / dynamic 分段

借自 Skyvern 的 prompt 缓存优化（`references/skyvern/skyvern/forge/prompts/skyvern/CLAUDE.md`：`extract-action.j2` 拆成 `-static.j2` 可缓存前缀 + `-dynamic.j2` 运行时后缀，且 static 必须与完整模板前缀**逐字一致**）。

每个模板文件内部用注释显式分段：

```markdown
<!-- STATIC-BEGIN  稳定前缀：角色、规则、输出契约。跨 Run 不变，可命中 prompt 缓存 -->
...
<!-- STATIC-END -->

<!-- DYNAMIC-BEGIN 运行时后缀：本次事实、证据、变量。每次不同 -->
...
<!-- DYNAMIC-END -->
```

硬规则：

- STATIC 段只放跨 Run 稳定的内容（角色定义、规则、输出格式契约、禁止项）。
- DYNAMIC 段只放本次事实（Run ID、SHA、diff、命令输出、AC 列表）。
- 修改 STATIC 段必须同步检查所有引用它的模板；**逐字一致**是缓存命中的前提，改一个字就整段失效。
- 变量清单写在模板头部 `variables:` 注释里，`validate_package.py` 检查占位符是否都已声明。

### 输出契约优先

每个模板必须声明期望输出结构（YAML 片段或字段表），因为下游要把它写进账本。Skyvern 的做法是让 LLM 返回 Pydantic 模型（例如 `MaxStepsReasonResponse` 带 `reasoning`、`errors`、`failure_categories`、`failure_category_source`），并且：

- 对 LLM 自由文本做**长度上限截断**而不是拒绝（拒绝会连带丢掉调用方真正要的 `error_code`）；
- 对 LLM 产出的错误码做**白名单过滤**（`filter_to_user_defined_codes`），因为模型会从失败分类学里幻觉出不存在的码；
- 显式记录来源（`failure_category_source`），避免调用方从"字段有值"反推"这是 LLM 说的"。

这三条在我的模板里是强制项：任何要求模型产出结构化结论的 Prompt，都必须写明"允许值白名单""字段长度上限""来源标注"。

### Prompt 预算

- Skyvern 有 `PROMPT_HARD_CEILING_TOKENS = 180_000` 与按模板定义的 `CEILING_FALLBACK_KEYS_BY_TEMPLATE`（超限时按优先级丢弃指定键，例如先丢 `action_history`），并保留安全边距与最少有用元素量。
- 对应到我的流程：每个 Prompt 模板声明 `max_context_tokens` 与 `drop_priority`（超限先丢什么）。**绝不**为了让上下文塞得下而丢掉 AC、Finding 或 SHA。

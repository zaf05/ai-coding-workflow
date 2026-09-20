# prompts/ · Prompt 模板

纯 Markdown + `{{ 变量 }}` 占位，**不依赖模板引擎**：宿主 Agent 直接读文本填充。

规范见 `../docs/06-parameters-and-prompts.md`：

- 每个模板显式 `STATIC-BEGIN/END` 与 `DYNAMIC-BEGIN/END` 分段。
- STATIC 只放跨 Run 稳定内容（角色、规则、输出契约、禁止项）。
- DYNAMIC 只放本次事实（Run ID、SHA、diff、命令输出、AC）。
- 变量清单写在头部 `variables:` 注释。
- 输出契约必须声明允许值白名单、字段长度上限、来源标注。

```text
prompts/
├── intake.md        需求接收
├── spec.md          行为规格
├── implement.md     单块实现
├── review.md        独立审核
└── test.md          测试执行
```

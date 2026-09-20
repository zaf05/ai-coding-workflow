# Handoff

```yaml
run_id: "RUN-YYYYMMDD-NNN"
block_label: ""
action: ""                     # 单一角色动作（做什么，不做什么）
spec_ref: ""                   # current.md#Spec@vN
base_sha: ""
head_sha: ""                   # 按需
tested_sha: ""                 # 按需
finding_defect_ids: []         # 适用 Finding / Defect ID
allowed_paths: []
protected_paths: []
output_contract: ""            # 用哪个模板、写到哪
budget:
  max_attempts: 1
  timeout_minutes: 30
  tokens_soft: 3000
stop_conditions: []
```

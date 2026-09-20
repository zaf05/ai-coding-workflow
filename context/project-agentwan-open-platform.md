# 项目画像：AgentWan 开放平台

> 首次记录：2026-09-17 | 最近更新：2026-09-17

## 架构概要

- 零构建静态文档站，位置：`.worktree/agentwan-open-platform-docs/site/`。
- 当前候选分支：`wp/agentwan-open-platform-docs`，基线：`origin/develop @ 55cf85b943b64e9aa510f560b24891096ca9e281`。
- 本地服务：`python3 -m http.server 8096 --bind 0.0.0.0`。
- 真实后端：`http://127.0.0.1:8191`；开放文档只描述 4 个只读查询 API。
- 凭证由管理员/运行环境分配；`AGENTWAN_TOKEN` 只是调用侧环境变量名，值不入库。

## 关键文件

| 文件 | 作用 | 注意事项 |
|---|---|---|
| `site/index.html` | 开放平台门户 | 品牌必须是 `AgentWan 开放平台` |
| `site/employee-api.html` | 4 个真实 API 文档 | 必须可提取真实 employee_id 后连续调用 |
| `site/scripts/check-links.py` | 静态门禁 | 禁止外链、死链、内部过程词 |
| `site/assets/nav.js` | 导航与搜索 | 搜索索引必须同步 |

## 构建与验证命令

```bash
cd .worktree/agentwan-open-platform-docs/site
python3 scripts/check-links.py
python3 -m http.server 8096 --bind 0.0.0.0
```

## 来源

- RUN-20260917-005：最终 v2 静态站迁移与真实 API/浏览器验收。

# 实现者自检参考

> 受约契约：`../../_shared/contracts/role-boundaries.md`（不自审、不给 APPROVE）
> 吸收自：a01 验证证据而非口头声明、a17 软件工程判断力

实现者只能自测，不能给自己发 `APPROVE`。提交前逐项确认：

- [ ] diff 范围与块目标一致，无无关重构。
- [ ] `git diff --check` 零报告（空白/冲突标记）。
- [ ] 敏感信息未入 diff/日志/报告。
- [ ] 关键命令有精确 exit_code 记录。
- [ ] 页面任务有真实浏览器 + 目标视口证据。
- [ ] 已知问题、未完成项、follow-ups 显式写进报告。
- [ ] base_sha/head_sha 完整且未漂移。

任一不满足 → 回 `in_progress` 继续，不得标记 `implementer_verified`。

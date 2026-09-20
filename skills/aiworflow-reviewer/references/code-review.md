# 代码审核参考

## 审核对象

精确 `base_sha..head_sha` 增量 + 当前开放 Finding。只审交接的完整对象或有依据的 Delta。

## 检查顺序

1. 正确性：是否满足 Spec/AC。
2. 数据安全：SQL 注入、秘密泄漏、脱敏。
3. 授权与租户隔离：越权、跨租户读。
4. 并发与事务：竞态、幂等、锁。
5. 兼容性：契约、Schema、版本。
6. 回归：受影响路径。
7. 资源生命周期：连接/文件/进程/定时器清理。
8. Brownfield 变更失控：是否把无关重构混入。

## 非阻断

格式化、个人偏好、推测性现代化、无关历史技术债 → 不放 Finding 或放 non_blocking_notes/Advisory。

## 证据不足

SHA 缺失/漂移、无法读原文、必要输入缺失 → `BLOCKED`，写 unblock_conditions。

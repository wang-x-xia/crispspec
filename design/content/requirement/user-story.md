# User Story — 用户故事

## 目标

将 Requirement 分解为面向实现的最小交付单元，连接需求层（L1）与架构层（L2）。每个 User Story 对应一个可独立验收的行为切片，通过结构化的验收条件（前置条件 + 预期结果）消除"完成"的歧义。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `US-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 简短标题 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话摘要 |
| `priority` | enum | `CRITICAL / HIGH / MEDIUM / LOW` | 优先级 |
| `status` | enum | 见下方 | 故事状态 |
| `story_points` | integer | Fibonacci: `1, 2, 3, 5, 8, 13, 21` | 复杂度估算 |
| `acceptance_criteria` | list\<Criterion\> | ≥ 1 条 | 结构化验收条件 |

### status 枚举

| 值 | 含义 |
|----|------|
| `BACKLOG` | 待排期 |
| `READY` | 已就绪（所有前置条件满足） |
| `IN_PROGRESS` | 开发中 |
| `DONE` | 已完成 |
| `BLOCKED` | 被阻塞 |

---

## 子结构定义

### Criterion（前置条件 / 预期结果）

| 字段 | 类型 | 约束 |
|------|------|------|
| `given` | [Condition](../concepts.md#condition) | 前置条件 |
| `then` | [Assertion](../concepts.md#assertion) | 预期结果 |

> 触发动作（哪个 Interface / Reaction / Schedule）是关系，
> 由 User Story 的 `IMPLEMENTED_BY` 边表达，不在字段里重复。

---

## 格式

```yaml
id: "US-301"
name: "VIP用户发起退款申请"
description: "钻石卡用户可在订单完成后发起退款，享受 24h SLA"

priority: HIGH
status: READY
story_points: 5

acceptance_criteria:
  - given:
      field: "user.membership_level"
      operator: IN
      values: ["GOLD", "DIAMOND"]
    then:
      field: "refund.sla"
      operator: "=="
      expected: "24h"

  - given:
      field: "user.membership_level"
      operator: NOT_IN
      values: ["GOLD", "DIAMOND"]
    then:
      field: "refund.sla"
      operator: "=="
      expected: "72h"
```

---

> **关系不在字段里。** 与其它制品的关系统一写在下面的 `## 关联` 表——
> 字段表只描述这件制品自己的数据，不重复声明"我引用了谁"。

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `DECOMPOSES_INTO` | [Requirement](requirement.md) |
| 出 → | `ACTED_BY` | [Role](../access/role.md) |
| 出 → | `IMPLEMENTED_BY` | [Interface](../contract/interface.md) / [Orchestration](../behavior/orchestration.md) / [Reaction](../behavior/reaction.md) / [Schedule](../behavior/schedule.md)（从 Criterion.when 派生） |
| 出 → | `TESTED_BY` | [Scenario Test](../test/scenario-test.md) |

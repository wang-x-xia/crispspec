# Acceptance Test — 验收测试

## 目标

验证 [Requirement](../requirement/requirement.md) 的业务意图是否被完整实现。验收测试从端到端视角检验需求的所有消歧维度（前置条件、后置条件、异常、副作用），通常跨越多个模块和接口。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `AT-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 用例名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `scope` | enum | 见下方 | 测试范围 |
| `preconditions` | list\<[Condition](../concepts.md#condition)\> | | 前置条件 |
| `steps` | list\<TestStep\> | ≥ 1 步 | 有序执行步骤 |
| `expected_outcomes` | list\<[Assertion](../concepts.md#assertion)\> | ≥ 1 条 | 最终预期结果 |

### scope 枚举

| 值 | 含义 |
|----|------|
| `E2E` | 端到端——从用户入口到最终副作用 |
| `CROSS_SERVICE` | 跨服务——涉及多个模块协作 |
| `SINGLE_SERVICE` | 单服务——在单一模块内验收 |

### TestStep

| 字段 | 类型 | 约束 |
|------|------|------|
| `order` | integer | 步骤序号（从 1 开始） |
| `input` | list\<[TypedField](../concepts.md#typedfield)\> | 输入参数（带测试值 `value`） |
| `checkpoint` | [Assertion](../concepts.md#assertion) | 可选，步骤级断言 |

---

## 格式

```yaml
id: "AT-1"
name: "VIP用户优先退款端到端验收"
description: "验证金卡用户从发起退款到完成的完整流程符合 24h SLA"

scope: E2E

preconditions:
  - field: "user.membership_level"
    operator: "=="
    value: "GOLD"
  - field: "order.status"
    operator: "=="
    value: "DELIVERED"

steps:
  - order: 1
    input:
      - name: order_id
        type: UUID
        value: "test-order-001"
      - name: reason
        type: ENUM
        value: "DEFECTIVE"
    checkpoint:
      field: "response.status"
      operator: "=="
      expected: "PROCESSING"

  - order: 2
    input:
      - name: timeout_seconds
        type: INTEGER
        value: 86400

expected_outcomes:
  - field: "refund.status"
    operator: "=="
    expected: "COMPLETED"
  - field: "refund.elapsed_time"
    operator: "<="
    expected: "24h"
  - field: "user.points_balance"
    operator: "=="
    expected: "original - order.earned_points"
```

---

> **关系不在字段里。** 与其它制品的关系统一写在下面的 `## 关联` 表——
> 字段表只描述这件制品自己的数据，不重复声明"我引用了谁"。

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `TESTED_BY` | [Requirement](../requirement/requirement.md) |

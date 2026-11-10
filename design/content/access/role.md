# Role — 角色

## 目标

定义系统中的参与者角色——谁、满足什么条件、拥有哪些权限。Role 将 Requirement 和 User Story 中的"执行主体"从内联枚举（`USER` / `ADMIN` / `SYSTEM`）提升为独立制品，使角色的识别条件、权限集合和继承关系均可追溯。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `ROLE-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 角色名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `type` | enum | 见下方 | 角色类别 |
| `qualifiers` | list\<[Condition](../concepts.md#condition)\> | ≥ 0 条 | 识别条件——全部满足时属于该角色 |

### type 枚举

| 值 | 含义 |
|----|------|
| `HUMAN` | 人类用户（终端消费者、管理员等） |
| `SYSTEM` | 系统内部角色（定时任务、后台服务） |
| `EXTERNAL_SERVICE` | 外部服务（第三方支付、物流 API） |

---

## 格式

```yaml
id: "ROLE-1"
name: "Regular User"
description: "普通注册用户"

type: HUMAN
qualifiers: []
```

```yaml
id: "ROLE-3"
name: "VIP User"
description: "金卡或钻石卡会员，享有优先退款等特权"

type: HUMAN
qualifiers:
  - field: "membership_level"
    operator: IN
    values: ["GOLD", "DIAMOND"]
```

```yaml
id: "ROLE-10"
name: "Payment Gateway"
description: "第三方支付网关回调身份"

type: EXTERNAL_SERVICE
qualifiers: []
```

---

> **关系不在字段里。** 与其它制品的关系统一写在下面的 `## 关联` 表——
> 字段表只描述这件制品自己的数据，不重复声明"我引用了谁"。

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| 出 → | `HAS_PERMISSION` | [Permission](permission.md) |
| 出 → | `INHERITS_FROM` | [Role](role.md) |
| 出 → | `IDENTIFIED_BY` | [Entity](../contract/entity.md) |
| ← 入 | `ACTED_BY` | [Requirement](../requirement/requirement.md)、[User Story](../requirement/user-story.md) |

# Business Concept — 业务概念

## 目标

定义业务概念，以及它与内部技术制品的**对应关系**——一个业务概念被映射为哪些内部制品。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `BC-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 简短标题 |
| `description` | string | 自由文本 | **描述性** — 一句话说明这个业务概念 |
| `defined` | boolean | — | 是否已完成消歧（未完成的概念可以被引用，但不可被映射） |
| `as` | list\<[Mapping]\> | ≥ 0 条 | 映射到的内部制品；可以为空 |

---

## 子结构定义

### Mapping

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `artifact_type` | enum | `ROLE` / `MODULE` / `ENTITY` / `INTERFACE` / `ORCHESTRATION` / `REACTION` / `SCHEDULE` / `EVENT` / `ERROR` | 映射目标的制品类型 |
| `artifact_id` | ref | `{PREFIX}-\d+` | 目标制品的 ID，必须真实存在 |

---

## 一、基于 SDS 实际制品的映射

根据 SDS 制品体系的实际设计，映射应直接对应到现有制品：

**SDS 现有制品**：
- **访问控制域**：Role, Permission
- **治理域**：Constraint, Dependency
- **契约域**：Entity, Interface, Event, Error
- **行为域**：Process, Orchestration, Reaction, Schedule
- **组织单元**：Module

---

## 二、映射关系：`as`

业务概念只有一个映射位置：**`as`**——它被映射为哪些内部制品。

```yaml
as:
  - {artifact_type: ENTITY, artifact_id: "ENT-3"}
  - {artifact_type: INTERFACE, artifact_id: "API-20"}
  - {artifact_type: ROLE, artifact_id: "ROLE-1"}
```

三个要点：

1. **是一个列表，不是七个固定槽位。** 一个业务概念可以同时被多个内部制品实现——
   "退款单"可能既是 Entity，也对应 Interface，还对应一个 Role。
2. **`artifact_type` 决定它落在哪个技术制品上。** 取值是
   `ROLE` / `MODULE` / `ENTITY` / `INTERFACE` / `ORCHESTRATION` / `REACTION` /
   `SCHEDULE` / `EVENT` / `ERROR`，以及四种非制品类型的落点
   （`ENTITY_FIELD` / `STATE_CHANGE` / `INTERFACE_RESPONSE` / `SIDE_EFFECT`）。
3. **映射不表达时间。** `as` 只说“它被映射成了什么”，不说“谁先存在”。
   业务概念可以早在需求之前就定义好；也可以在需要时才建。

> 早期版本把映射拆成 `as_actor` / `as_object` / `as_action` / `as_event` /
> `as_attribute` / `as_result` / `as_error` 七个语义位置，每个位置只能填一个目标。
> 但“语义位置”并不是制品体系的区分维度——同一个概念同时是 actor 和 object
> 并不矛盾，拆成七个槽位反而限制了能表达的东西，还让“同一个概念只能有一个目标”
> 这个约束凭空出现。合并成 `as` 之后，位置只是目标制品的属性。

---

## 三、业务概念层设计

### 3.1 为什么需要业务概念层？

**现实问题**：业务概念与技术概念的不对齐

```
业务概念                    技术概念
VIP会员        →?→    User.role_type IN ('GOLD', 'DIAMOND')
退款单         →?→    Refund 实体 + RefundLineItem 实体
退款SLA        →?→    Refund.expected_completion_time
```

**不对齐的原因**：
1. 一对多：一个业务"订单"可能拆分为多个技术实体
2. 多对一：业务"用户"和"会员"在技术上可能是同一个表
3. 语义漂移：技术重构时，Entity 名称变了，但业务概念不变

### 3.2 业务概念层的设计

```yaml
# BusinessConcept 制品 Schema
id: "BC-\d+"
name: string
description: string         # 一句话说明
defined: boolean             # 是否已定义

# 映射到哪些内部制品（可多个，可为空）
as:
  - artifact_type: ENTITY | MODULE | INTERFACE | ORCHESTRATION | REACTION
    | SCHEDULE | EVENT | ERROR | ENTITY_FIELD | STATE_CHANGE
    | INTERFACE_RESPONSE | SIDE_EFFECT
    artifact_id: string
```

### 3.3 渐进式引用策略

| 阶段 | 引用类型 | 示例 |
|------|---------|------|
| **Draft** | 无引用 | "VIP用户可以优先退款" |
| **Structured Draft** | 软引用（自然语言标识） | "Given [actor:VIP会员] When [action:发起退款]" |
| **Requirement** | 强引用（typed ID） | `actor_role_id: "ROLE-3"` |
| **User Story** | 强引用 | `when: "API-20"` |

---

## 四、映射的设计约束

> 这一节是**设计约束**，不是实现计划。具体的存储与接口形态属于实现期，
> 等制品体系定稿后再定。

### 4.1 允许的映射目标

业务概念可映射到的制品类型由制品登记表声明（`design/data/artifacts.yaml`
的 `mapping_targets`），当前为：

| 目标制品 | 类型键 | 含义 |
|----------|--------|------|
| Role | `role` | 这个概念是一个参与者的身份 |
| Module | `module` | 这个概念归属某个组织单元 |
| Entity | `entity` | 这个概念有独立的数据结构 |
| Interface | `interface` | 这个概念对外暴露为接口 |
| Orchestration | `orchestration` | 这个概念由跨模块流程实现 |
| Reaction | `reaction` | 这个概念由事件反应实现 |
| Schedule | `schedule` | 这个概念由定时任务实现 |
| Event | `event` | 这个概念是一个领域事件 |
| Error | `error` | 这个概念对应一类错误 |

### 4.2 约束

1. **映射是一个列表，不是固定槽位。** 一个业务概念可以同时被多个内部制品实现。
2. **映射只说"被映射成了什么"，不说"谁先存在"。** 映射不表达时间顺序。
3. **映射目标必须真实存在。** `artifact_id` 指向的制品必须在制品库中存在——
   这是跨制品引用校验层的职责（实现期）。
4. **同一个目标不可重复映射。** 同一对（类型, ID）只能出现一次。
5. **映射是业务概念唯一的结构化落点。** 它没有第二处需要填写"这个概念对应哪个技术制品"。

### 4.3 校验规则（待实现期落地）

| 规则 | 现状 |
|------|------|
| `artifact_type` 在允许集合内 | ✅ 已在制品登记表中声明 |
| `artifact_id` 格式合法（`{PREFIX}-\d+`） | ⏸ 待实现 |
| `artifact_id` 指向的制品存在 | ⏸ 待实现（需要跨制品引用校验层） |
| 同一目标不重复 | ⏸ 待实现 |
| 映射列表可为空 | ✅ 设计如此——业务概念可以先定义，映射后补 |



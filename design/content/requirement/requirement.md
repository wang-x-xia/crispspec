# Requirement — 需求制品

## 目标

承载**消歧之后的需求**。一条需求由若干个业务概念共同描述，
并向下拆分成若干个可交付的用户故事。

需求本身**不区分概念扮演什么语义角色**——执行者、条件、动作、结果这些位置，
由每个 Business Concept 自己的 `as` 映射决定：
映射到 Role 的就是执行者，映射到 Entity 字段的就是条件，映射到 Interface 的就是动作。

---

## 结构

Requirement 在体系里只做两件事：

| | 关系 | 基数 | 说明 |
|---|---|---|---|
| **被描述** | `DESCRIBED_BY` → Business Concept | 多个 | 这条需求涉及哪些业务概念 |
| **被拆解** | `DECOMPOSES_INTO` → User Story | 多个 | 这条需求拆成哪些可交付单元 |

加上执行角色与验证方式，需求的出向关系一共**四条**：

| 边 | 目标 | 基数 | 含义 |
|----|------|------|------|
| `DESCRIBED_BY` | Business Concept | 多个 | 描述这条需求的业务概念 |
| `DECOMPOSES_INTO` | User Story | 多个 | 拆解出来的可交付单元 |
| `ACTED_BY` | Role | 1 | 谁来执行 |
| `TESTED_BY` | Acceptance Test | 多个 | 怎么证明需求被满足 |

> **为什么不再有"语义槽位"？**
> 早期版本给需求准备了 `as_actor` / `as_object` / `as_action` 这样的固定位置，
> 每个位置只能填一个目标。但语义位置并不是制品体系的区分维度——
> 同一个概念既是 actor 又是 object 并不矛盾，固定槽位反而限制能表达的东西。
> 合并成"需求引用一批业务概念"之后，位置只是目标制品的属性。

> **拆解是多对多的。**
> 拆解关系写在关系表里（`DECOMPOSES_INTO`）：一条需求拆成多个故事，
> 一个故事也可以同时服务多条需求——所以它是多对多。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `REQ-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 简短标题 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话摘要 |
| `sentence_type` | enum | 见下方 | 句子类型 |
| `done` | boolean | - | 是否完成 |

### sentence_type 枚举

| 值 | 含义 |
|----|------|
| `GWT` | Given-When-Then 模式 |
| `EARS` | EARS 模式 |
| `SVO` | 主谓宾模式 |
| `CUSTOM` | 自定义模式 |

> 句式只是**分类标签**——它标记这句话属于哪种句式，不规定需求引用哪些制品。
> 句子怎么被解析成结构化制品，见 [自然语言结构化转译](natural-language-structuring.md)；
> 拆解出来的可交付单元带着真正的 Given / When / Then 验收条件，见 [User Story](user-story.md)。

---

## 格式

```yaml
id: "REQ-0078"
name: "VIP用户优先退款"
description: "金卡和钻石卡用户的退款 SLA 从 72h 缩短为 24h"

sentence_type: GWT
done: false

```

> 需求的字段里不再区分概念的语义位置，也不列出它引用了哪些概念——
> “被哪些业务概念描述”是关系（`DESCRIBED_BY`），写在 `## 关联` 表里。

---

> **关系不在字段里。** 与其它制品的关系统一写在下面的 `## 关联` 表——
> 字段表只描述这件制品自己的数据，不重复声明"我引用了谁"。

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| ← 入 | `DISAMBIGUATED_INTO` | [Draft](draft.md) |
| 出 → | `DESCRIBED_BY` | [Business Concept](business-concept.md)（多个） |
| 出 → | `DECOMPOSES_INTO` | [User Story](user-story.md)（多个） |
| 出 → | `ACTED_BY` | [Role](../access/role.md) |
| 出 → | `TESTED_BY` | [Acceptance Test](../test/acceptance-test.md) |

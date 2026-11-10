# Module — 模块制品

## 目标

定义系统的组织单元——按服务边界把制品分组。Module 类似文件夹：
它自己只声明身份（名字、类型、版本、负责人、状态），
“管哪些制品”“依赖谁”“对应哪些代码”全部由关系表达。

> **Module 是一个容器，不是一个普通节点。** 它把属于同一个服务边界的制品收在一起，
> 所以图上它画成一个框，而不是一个圆点。
> 归属关系统一用一条边 `CONTAINS` 表达——“这个制品属于这个模块”——
> 不再按制品类型分成 `EXPOSES` / `PUBLISHES` / `GOVERNED_BY` / `OWNS` / `MAPPED_TO` /
> `MANAGES` 等一堆同义反复的谓词。
> 归属只出现在关系表里：制品侧不声明 `module_id`，Module 侧也不维护反向列表。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `MOD-\d+` | 唯一标识符 |
| `name` | string | PascalCase，≤ 80 字符 | **描述性** — 服务 / 模块名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话职责说明 |
| `type` | enum | 见下方 | 模块类型 |
| `version` | string | semver（如 `2.1.0`） | 当前版本 |
| `owner` | string | 团队 / 人员 ID | 负责人 |
| `used` | boolean | 默认 `true` | 是否在使用 |
| `deprecated` | boolean | 默认 `false` | 是否已废弃 |

### type 枚举

| 值 | 含义 |
|----|------|
| `CLI` | 命令行模块 |
| `INTERNAL_LIB` | 内部功能模块 |
| `EXTERNAL_LIB` | 外部功能模块 |

---

## 格式

```yaml
id: "MOD-001"
name: "CrispSpec"
description: "CrispSpec 命令行工具主模块"

type: CLI
version: "0.1.0"
owner: "core-team"
used: true
deprecated: false
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| 出 → | `CONTAINS` | [Interface](../contract/interface.md) / [Entity](../contract/entity.md) / [Event](../contract/event.md) / [Process](../behavior/process.md) / [Orchestration](../behavior/orchestration.md) / [Reaction](../behavior/reaction.md) / [Schedule](../behavior/schedule.md) / [Code Ref](../code/code-ref.md) / [Incident](../incident/incident.md) / [Runbook](../incident/runbook.md) / [Playbook](../incident/playbook.md) |
| 出 ↔ | `DEPENDS_ON` | [Module](module.md)（自引用） |
| 出 → | `TESTED_BY` | [Integration Test](../test/integration-test.md) |

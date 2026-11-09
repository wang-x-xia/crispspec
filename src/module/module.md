# Module — 模块制品

## 目标

定义系统的组织单元——按服务边界将制品分组，声明模块间依赖，并将制品映射到具体的代码实现。Module 类似文件夹，负责回答三个问题：

1. **这个模块管哪些制品？**（契约域 + 行为域 + 代码域 + 故障域的制品归属）
2. **这个模块依赖谁？**（模块间运行时依赖）
3. **这些制品对应哪些代码？**（制品到源码的追溯）

> **Module 是一个容器，不是一个普通节点。** 它把属于同一个服务边界的制品收在一起，
> 所以图上它画成一个框，而不是一个圆点。
> 归属关系统一用一条边 `CONTAINS` 表达——“这个制品属于这个模块”——
> 不再按制品类型分成 `EXPOSES` / `PUBLISHES` / `GOVERNED_BY` / `OWNS` / `MAPPED_TO` /
> `MANAGES` 等一堆同义反复的谓词。
> 制品自己声明归属（`module_id` 字段），Module 这一侧的列表只是反向索引。

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
| `dependencies` | list\<Dependency\> | | 依赖的其他模块 |
| `interface_ids` | list\<ref\> | `API-\d+` | 本模块的接口 |
| `process_ids` | list\<ref\> | `PROC-\d+` | 本模块的流程 |
| `constraint_ids` | list\<ref\> | `CON-\d+` | 关联的约束 |
| `code_refs` | list\<[CodeRef](#coderef)\> | | 制品到源码的映射 |

### type 枚举

| 值 | 含义 |
|----|------|
| `CLI` | 命令行模块 |
| `INTERNAL_LIB` | 内部功能模块 |
| `EXTERNAL_LIB` | 外部功能模块 |

---

## 子结构定义

### Dependency

| 字段 | 类型 | 约束 |
|------|------|------|
| `module_id` | ref | `MOD-\d+` |
| `protocol` | enum | `PYTHON_API` |
| `required` | boolean | `true` = 强依赖（不可降级），`false` = 弱依赖 |

### CodeRef

将一个制品映射到其源码实现位置。

| 字段 | 类型 | 约束 |
|------|------|------|
| `artifact_id` | ref | 契约域或行为域制品 ID（`API-\d+` / `ENT-\d+` / `EVT-\d+` / `ERR-\d+` / `PROC-\d+` / `ORCH-\d+` / `SUB-\d+` / `SCH-\d+`） |
| `path` | string | 源代码文件路径（相对于仓库根目录） |
| `symbol` | string | 导出符号名（类名 / 函数名 / 常量名） |

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

dependencies:
  - module_id: "MOD-002"
    protocol: PYTHON_API
    required: true
  - module_id: "MOD-003"
    protocol: PYTHON_API
    required: true

interface_ids: ["API-001", "API-002"]
process_ids: ["PROC-001"]
constraint_ids: ["CON-001"]

code_refs:
  - artifact_id: "API-001"
    path: "src/cli/commands/create.py"
    symbol: "CreateCommand"

  - artifact_id: "API-002"
    path: "src/cli/commands/validate.py"
    symbol: "ValidateCommand"

  - artifact_id: "PROC-001"
    path: "src/cli/workflow/pipeline.py"
    symbol: "PipelineWorkflow"
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| 出 → | `CONTAINS` | [Interface](../contract/interface.md) / [Entity](../contract/entity.md) / [Event](../contract/event.md) / [Process](../behavior/process.md) / [Orchestration](../behavior/orchestration.md) / [Reaction](../behavior/reaction.md) / [Schedule](../behavior/schedule.md) / [Code Ref](../code/code-ref.md) / [Incident](../incident/incident.md) / [Runbook](../incident/runbook.md) / [Playbook](../incident/playbook.md) |
| 出 ↔ | `DEPENDS_ON` | [Module](module.md)（自引用） |
| 出 → | `TESTED_BY` | [Integration Test](../test/integration-test.md) |

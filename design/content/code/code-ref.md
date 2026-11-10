# Code Ref — 代码引用制品

## 目标

定义制品到源码位置的追溯引用——仓库、文件路径、导出符号。Code Ref 把逻辑制品（[Entity](../contract/entity.md)、[Interface](../contract/interface.md)、[Process](../behavior/process.md) 等）锚定到物理代码上，是"结构化制品驱动代码"这条链路里唯一的物理落点。

每个 Code Ref 指向一个制品在一个仓库中的一个符号。因为 Module 与 Repository 是 M:N 映射，同一个制品可能在多个仓库中各有实现，此时为每个实现各建一条 Code Ref。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `CREF-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 引用名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `path` | string | 相对仓库根目录的路径 | 源代码文件路径 |
| `symbol` | string | | 导出符号名（类名 / 函数名 / 常量名） |

---

## 格式

```yaml
id: "CREF-1"
name: "CreateCommand 实现"
description: "Module 创建接口的 CLI 命令实现"

path: "src/cli/commands/create.py"
symbol: "CreateCommand"
```

```yaml
id: "CREF-2"
name: "Order 实体实现"
description: "订单实体的持久化模型定义"

path: "src/db/models/order.py"
symbol: "Order"
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| 出 → | `LOCATED_IN` | [Repository](repository.md) |
| 出 → | `IMPLEMENTS` | 契约域 / 行为域制品 |
| ← 入 | `CONTAINS` | [Module](../module/module.md) |

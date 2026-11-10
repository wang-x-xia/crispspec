# Config Set — 配置集合制品

## 目标

定义配置集合——按环境或模块分组的配置项集合及其覆盖值。Config Set 是环境与配置域的组织单元，它将多个 Configuration 聚合成可部署的配置包，支持环境级覆盖。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `CSET-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 配置集合名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `scope` | enum | 见下方 | 作用范围 |

### scope 枚举

| 值 | 含义 |
|----|------|
| `ENVIRONMENT` | 环境级配置 |
| `MODULE` | 模块级配置 |

> 覆盖了哪些配置项、各自的值，暂时没有落点——那是实例级的引用，
> 而引用现在统一由关系表表达（`OVERRIDES`）。

---

## 格式

```yaml
id: "CSET-1"
name: "Production Config"
description: "生产环境配置集合"

scope: ENVIRONMENT
```

```yaml
id: "CSET-2"
name: "OrderService Config"
description: "订单服务模块配置"

scope: MODULE
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| 出 → | `APPLIES_TO` | [Module](../module/module.md) |
| 出 → | `OVERRIDES` | [Configuration](configuration.md) |

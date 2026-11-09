# Repository — 代码仓库制品

## 目标

定义代码仓库——地址、默认分支、语言栈。Repository 是代码域的物理容器，回答"代码实际存在哪里"这个问题。

Module 与 Repository 之间是 **M:N** 映射：同一个 Module 的代码可能散布在多个 Repository 中（monorepo 拆分、微服务多仓），同一个 Repository 也可能包含多个 Module 的代码（monorepo）。因此 Repository 通过 `module_ids` 反向声明它承载哪些 Module。

---

## 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | string | `REPO-\d+` | 唯一标识符 |
| `name` | string | ≤ 80 字符 | **描述性** — 仓库名称 |
| `description` | string | ≤ 200 字符 | **描述性** — 一句话说明 |
| `url` | string | URL | 仓库地址（如 `https://github.com/org/repo`） |
| `default_branch` | string | | 默认分支（如 `main`、`master`） |
| `language` | enum | 见下方 | 主要语言 |
| `visibility` | enum | 见下方 | 可见性 |
| `module_ids` | list\<ref\> | `MOD-\d+` | 本仓库承载的模块（可为空） |

### language 枚举

| 值 | 含义 |
|----|------|
| `PYTHON` | Python |
| `TYPESCRIPT` | TypeScript / JavaScript |
| `JAVA` | Java / Kotlin |
| `GO` | Go |
| `RUST` | Rust |
| `C_SHARP` | C# / .NET |
| `CPP` | C / C++ |
| `SHELL` | Shell 脚本 |
| `POLYGLOT` | 多语言仓库 |

### visibility 枚举

| 值 | 含义 |
|----|------|
| `PUBLIC` | 公开仓库 |
| `PRIVATE` | 私有仓库 |

---

## 格式

```yaml
id: "REPO-1"
name: "crispspec"
description: "CrispSpec 结构化制品体系的主仓库"

url: "https://github.com/org/crispspec"
default_branch: "main"
language: PYTHON
visibility: PUBLIC

module_ids:
  - "MOD-1"    # CrispSpec CLI 主模块
  - "MOD-2"    # 存储层模块
```

```yaml
id: "REPO-2"
name: "crispspec-schemas"
description: "各领域制品的 YAML schema 定义仓库"

url: "https://github.com/org/crispspec-schemas"
default_branch: "main"
language: PYTHON
visibility: PRIVATE

module_ids: []
```

---

## 关联

| 方向 | 边类型 | 目标制品 |
|------|--------|---------|
| 出 → | `HOSTS` | [Module](../module/module.md) |
| ← 入 | `LOCATED_IN` | [Code Ref](code-ref.md) |

# YAML Schema 设计文档

## 概述

这是一个基于 YAML 格式的 schema 定义语言，用于描述 YAML 文件的结构和类型约束。设计目标是提供简洁、易读、可扩展的类型定义方式。

每个 type YAML 文件对应一个类型，类型只有 ID 没有名字。

## 字段定义格式

### 基础语法

```
{type};{parameters};{description}
```

#### Type（类型）

- **基础类型**：`string` | `number` | `bool`
- **本地类型引用**：`@.{name}`，引用当前文件 `__typedefs` 中定义的类型
- **外部类型引用**：`@TYPE-{ID}`，引用另一个类型的 `__self`
- **外部类型引用（子类型）**：`@TYPE-{ID}.{name}`，引用另一个类型的 `__typedefs` 中的条目

#### Parameters（参数）

- 格式：逗号分隔的参数列表
- 参数值使用 `=` 连接，如 `@min=1`、`@max=65535`
- 支持校验器：`@required`、`@min`、`@max`、`@pattern` 等
- 可为空，但即使为空也需要保留分号，如 `type;;description`

#### Description（描述）

- 字段的可读描述
- 可为空，但即使为空也需要保留分号，如 `type;parameters;` 或 `type;;`
- 用于文档生成和 IDE 提示

#### 示例

```yaml
# 完整格式
name: string;@required;用户名称

# 无参数，有描述
age: number;;用户年龄

# 无参数，无描述
enabled: bool;;

# 多个参数
port: number;@min=1,@max=65535;服务端口

# 本地自定义类型引用
user: @.User;@required;用户对象

# 外部类型引用（引用 __self）
config: @TYPE-abc123;@required;配置

# 外部类型引用（引用 __typedefs 下的条目）
db: @TYPE-abc123.DatabaseConfig;@required;数据库配置
```

## Type YAML 结构

每个 type YAML 使用 `__self` 和 `__typedefs` 两个保留字段定义：

- **`__self`**：类型自身的定义（必选），可以是字符串、对象或数组
- **`__typedefs`**：本地可复用的子类型定义（可选）

当 `__self` 存在时，顶层只允许 `__self` 和 `__typedefs` 两个 key。

### 对象类型

```yaml
__self:
  name: string;@required;用户名称
  age: number;;用户年龄
  email: string;@required;用户邮箱
```

### 字符串类型

```yaml
__self: string;@pattern=^[^@]+@[^@]+$;邮箱地址
```

### 数组类型

```yaml
__self: [ string;@required;标签 ]
```

### 带 `__typedefs` 的定义

```yaml
__self:
  server: @.ServerConfig;@required;服务器
  database: @.DatabaseConfig;@required;数据库
  features: [ string;@required;功能列表 ]

__typedefs:
  ServerConfig:
    host: string;@required;主机地址
    port: number;@min=1,@max=65535;端口
    ssl:
      enabled: bool;;是否启用SSL
      cert: string;;证书路径

  DatabaseConfig:
    host: string;@required;数据库主机
    port: number;@min=1,@max=65535;数据库端口
    name: string;@required;数据库名称
```

### 数组类型带 `__typedefs`

```yaml
__self: [ @.Item;@required;项目列表 ]

__typedefs:
  Item:
    name: string;@required;项目名称
    value: number;;项目值
```

## 外部类型引用

### 引用 `__self`

`@TYPE-{ID}` 直接引用另一个类型的 `__self` 定义：

```yaml
# 假设 TYPE-abc123 的 __self 是一个对象
__self:
  config: @TYPE-abc123;@required;配置
```

### 引用 `__typedefs` 中的条目

`@TYPE-{ID}.{name}` 引用另一个类型的 `__typedefs` 下的具体子类型：

```yaml
# 假设 TYPE-abc123 的 __typedefs 中有 DatabaseConfig
__self:
  db: @TYPE-abc123.DatabaseConfig;@required;数据库
```

## 完整示例

### 示例 1：简单配置

```yaml
__self:
  name: string;@required;应用名称
  version: string;@required;应用版本
  enabled: bool;;是否启用
  port: number;@min=1,@max=65535;服务端口
```

对应数据：

```yaml
name: my-app
version: 1.0.0
enabled: true
port: 8080
```

### 示例 2：带子类型的复杂对象

```yaml
__self:
  server: @.ServerConfig;@required;服务器配置
  database: @.DatabaseConfig;@required;数据库配置
  features: [ string;@required;功能列表 ]

__typedefs:
  ServerConfig:
    host: string;@required;主机地址
    port: number;@min=1,@max=65535;端口
    ssl:
      enabled: bool;;是否启用SSL
      cert: string;;证书路径
      key: string;;密钥路径

  DatabaseConfig:
    host: string;@required;数据库主机
    port: number;@min=1,@max=65535;数据库端口
    name: string;@required;数据库名称
    username: string;@required;数据库用户名
    password: string;@required;数据库密码
```

### 示例 3：纯数组类型

```yaml
__self: [ @.Tag;@required;标签列表 ]

__typedefs:
  Tag:
    name: string;@required;标签名
    color: string;;标签颜色
```

### 示例 4：纯字符串类型

```yaml
__self: string;@required,@pattern=^[^@]+@[^@]+$;邮箱地址
```

### 示例 5：跨类型引用

```yaml
# TYPE-common
__self:
  app_name: string;@required;应用名称

__typedefs:
  DatabaseConfig:
    host: string;@required;数据库主机
    port: number;@min=1,@max=65535;数据库端口
    name: string;@required;数据库名称

  LoggerConfig:
    level: string;@required;日志级别
    path: string;;日志文件路径
```

```yaml
# TYPE-app（引用 TYPE-common）
__self:
  database: @TYPE-common.DatabaseConfig;@required;数据库
  logger: @TYPE-common.LoggerConfig;@required;日志
  base: @TYPE-common;@required;基础配置
```

## 设计原则

1. **简洁性**：语法简单直观，易于阅读和编写
2. **可扩展性**：通过 parameters 支持未来扩展
3. **兼容性**：基于 YAML，易于与现有工具集成
4. **类型安全**：支持基础类型验证和类型引用解析
5. **类型复用**：通过 `__typedefs` 和外部引用，避免重复定义
6. **统一结构**：所有类型 YAML 统一使用 `__self` + `__typedefs` 结构

## 注意事项

1. 分号 `;` 用作类型、参数和描述的分隔符，即使 parameters 为空也需要两个分号
2. 逗号 `,` 用作参数之间的分隔符
3. 参数值使用 `=` 连接，避免与 YAML 的冒号冲突
4. 方括号 `[]` 用于数组类型定义
5. 类型引用以 `@` 开头，避免与基础类型冲突
6. 校验器也以 `@` 开头，便于扩展
7. 描述字段支持中文和特殊字符，用于文档生成
8. 格式示例：`type;parameters;description` 或 `type;;description`（当 parameters 为空时）
9. 本地类型引用使用 `@.{name}` 格式，引用当前文件 `__typedefs` 下的定义
10. 外部类型引用使用 `@TYPE-{ID}` 引用目标类型的 `__self`，使用 `@TYPE-{ID}.{name}` 引用目标类型的 `__typedefs` 下的条目
11. `__self` 和 `__typedefs` 是保留字段，当 `__self` 出现时顶层不允许其他 key
12. 每个 type YAML 只有 ID 没有名字

# YAML Schema 设计文档

## 概述

这是一个基于 YAML 格式的 schema 定义语言，用于描述 YAML 文件的结构和类型约束。设计目标是提供简洁、易读、可扩展的类型定义方式。

## 类型定义格式

### 基础类型语法

对于基础类型和第三方类型，使用以下格式：

```
{type};{parameters};{description}
```

#### Type（类型）

- **基础类型**：`string` | `number` | `bool`
- **第三方类型**：以 `@` 开头，如 `@email`、`@url`、`@datetime`
- **本地自定义类型**：`@.{name}`，引用当前文件 `__typedefs` 中定义的类型
- **外部自定义类型**：`@TYPE-{ID}.{name}`，引用其他文件中定义的类型

#### Parameters（参数）

- 格式：逗号分隔的参数列表
- 参数值使用 `=` 连接，如 `@min=1`、`@max=65535`
- 支持校验器：`@required`、`@min`、`@max`、`@pattern` 等
- 支持类型扩展：枚举、条件、多态等
- 可为空，但即使为空也需要保留分号，如 `type;;description`

#### Description（描述）

- 字段的可读描述
- 可为空，但即使为空也需要保留分号，如 `type;parameters;` 或 `type;;`
- 用于文档生成和 IDE 提示

#### 格式示例

```yaml
# 完整格式
name: string;@required;用户名称

# 无参数，有描述
age: number;;用户年龄

# 有参数，无描述
email: @email;@required;

# 无参数，无描述
enabled: bool;;

# 多个参数
port: number;@min=1,@max=65535;服务端口

# 本地自定义类型
user: @.User;@required;用户对象

# 外部自定义类型
config: @TYPE-common.DatabaseConfig;@required;数据库配置
```

## 自定义类型

### 本地类型定义

在 YAML 文件中使用 `__typedefs` 字段定义本地复用的类型：

```yaml
__typedefs:
  User:
    name: string;@required;用户名称
    age: number;;用户年龄
    email: @email;@required;用户邮箱

  Address:
    street: string;@required;街道地址
    city: string;@required;城市
    zipcode: string;;邮编

# 使用本地自定义类型
user: @.User;@required;
address: @.Address;
```

### 外部类型引用

引用其他文件中定义的类型，格式为 `@TYPE-{ID}.{name}`：

```yaml
# 假设在 common.yaml 文件中定义了 DatabaseConfig
database: @TYPE-common.DatabaseConfig;@required;
```

外部类型文件格式：

```yaml
# common.yaml
__typedefs:
  DatabaseConfig:
    host: string;@required;数据库主机
    port: number;@min=1,@max=65535;数据库端口
    name: string;@required;数据库名称
```

## 数据结构表示

### 对象类型

对象类型直接使用键值对表示：

```yaml
# schema 定义
name: string;@required;用户名称
age: number;;用户年龄
email: @email;@required;用户邮箱地址

# 对应的 YAML 文件示例
name: John Doe
age: 30
email: john@example.com
```

### 数组类型

数组类型使用列表语法表示：

```yaml
# schema 定义
tags: [ string;@required;标签列表 ]
items: [ number;@required;数字项目列表 ]

# 对应的 YAML 文件示例
tags:
  - tag1
  - tag2
  - tag3
items:
  - 1
  - 2
  - 3
```

### 嵌套对象

```yaml
# schema 定义
user: 
  name: string;@required;用户名称
  age: number;;用户年龄
  email: @email;@required;用户邮箱地址

# 对应的 YAML 文件示例
user:
  name: John Doe
  age: 30
  email: john@example.com
```

## 完整示例

### 示例 1：简单配置

```yaml
# schema.yaml
name: string;@required;应用名称
version: string;@required;应用版本
enabled: bool;;是否启用
port: number;@min=1,@max=65535;服务端口
```

```yaml
# config.yaml
name: my-app
version: 1.0.0
enabled: true
port: 8080
```

### 示例 2：复杂对象

```yaml
# schema.yaml
__typedefs:
  ServerConfig:
    host: string;@required;服务器主机地址
    port: number;@min=1,@max=65535;服务器端口
    ssl:
      enabled: bool;;是否启用SSL
      cert: string;;SSL证书路径
      key: string;;SSL密钥路径

  DatabaseConfig:
    host: string;@required;数据库主机地址
    port: number;@min=1,@max=65535;数据库端口
    name: string;@required;数据库名称
    username: string;@required;数据库用户名
    password: string;@required;数据库密码

server: @.ServerConfig;@required;
database: @.DatabaseConfig;@required;
features: [ string;@required;功能特性列表 ]
```

### 示例 3：外部类型引用

```yaml
# common.yaml (类型库文件)
__typedefs:
  DatabaseConfig:
    host: string;@required;数据库主机
    port: number;@min=1,@max=65535;数据库端口
    name: string;@required;数据库名称

  LoggerConfig:
    level: string;@required,enum=debug,info,warn,error;日志级别
    path: string;;日志文件路径
```

```yaml
# app.yaml (使用外部类型)
database: @TYPE-common.DatabaseConfig;@required;
logger: @TYPE-common.LoggerConfig;@required;
app_name: string;@required;应用名称
```

## 设计原则

1. **简洁性**：语法简单直观，易于阅读和编写
2. **可扩展性**：通过 parameters 支持未来扩展
3. **兼容性**：基于 YAML，易于与现有工具集成
4. **类型安全**：支持基础类型和第三方类型验证
5. **类型复用**：通过本地和外部类型引用，避免重复定义

## 未来扩展

### 类型继承

```yaml
# 支持类型继承，扩展已有类型
__typedefs:
  BaseUser:
    name: string;@required;用户名称
    email: @email;@required;用户邮箱

  AdminUser: @.BaseUser
    permissions: [ string;@required;权限列表 ]
    role: string;@required;角色
```

### 泛型类型

```yaml
# 支持泛型类型定义
__typedefs:
  List<T>:
    items: [ T;@required;列表项 ]

  Response<T>:
    code: number;@required;状态码
    message: string;;消息
    data: T;;响应数据

# 使用泛型
user_list: @.List<@.User>;@required;
user_response: @.Response<@.User>;@required;
```

### 枚举类型

```yaml
status: string;@required,enum=active,inactive,pending;用户状态
```

### 条件类型

```yaml
# parameters 支持条件表达式
field: string;if=status==active then=@required else=optional;条件字段
```

### 多态类型

```yaml
# 支持联合类型
value: string|number;@required;字符串或数字值
```

### 自定义校验器

```yaml
# 扩展校验器
email: @email;@required,@pattern=^[^@]+@[^@]+$;用户邮箱
age: number;@min=0,@max=120;用户年龄
```

## 实现考虑

1. **解析器**：需要解析 `{type};{parameters};{description}` 格式
2. **验证器**：实现基础校验器和第三方类型验证
3. **类型解析**：
   - 支持本地类型引用（`@.{name}`）
   - 支持外部类型引用（`@TYPE-{ID}.{name}`）
   - 处理类型定义的嵌套和递归
4. **类型库管理**：支持加载和管理外部类型文件
5. **错误报告**：提供清晰的类型错误信息，包括类型未找到、循环引用等
6. **IDE 支持**：考虑提供语法高亮和自动完成
7. **性能优化**：缓存已解析的类型定义，避免重复加载

## 注意事项

1. 分号 `;` 用作类型、参数和描述的分隔符，即使 parameters 为空也需要两个分号
2. 逗号 `,` 用作参数之间的分隔符
3. 参数值使用 `=` 连接，避免与 YAML 的冒号冲突
4. 方括号 `[]` 用于数组类型定义
5. 第三方类型以 `@` 开头，避免与基础类型冲突
6. 校验器也以 `@` 开头，便于扩展
7. 描述字段支持中文和特殊字符，用于文档生成
8. 格式示例：`type;parameters;description` 或 `type;;description`（当 parameters 为空时）
9. 本地自定义类型使用 `@.{name}` 格式，引用当前文件的 `__typedefs` 定义
10. 外部自定义类型使用 `@TYPE-{ID}.{name}` 格式，引用其他文件的类型定义
11. `__typedefs` 字段必须在文件顶层定义，用于存放本地可复用的类型

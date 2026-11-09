# Business Concept — 业务概念

## 目标

定义业务概念的概念，包括语义位置、与技术制品的对齐关系，以及产品经理如何用业务概念来描述产品。

---

## 一、基于 SDS 实际制品的映射

根据 SDS 制品体系的实际设计，映射应直接对应到现有制品：

**SDS 现有制品**：
- **治理域**：Role, Permission, Constraint, Dependency
- **契约域**：Entity, Interface, Event, Error
- **行为域**：Process, Orchestration, Reaction, Schedule
- **组织单元**：Module

---

## 二、七个核心映射位置

| 映射位置 | 主要目标制品 | 对应 Requirement 字段 |
|---------|-------------|---------------------|
| **as_actor** | Rol../../ Module | `actor_role_id` |
| **as_object** | Entity | `preconditions../../ `postconditions` (field 路径) |
| **as_action** | Interfac../../ Orchestratio../../ Reactio../../ Schedule | `traces.modules` (间接) |
| **as_event** | Event | `exceptions.trigger_event_id../../ `side_effects.trigger_event_id` |
| **as_attribute** | Entity.field | `preconditions../../ `postconditions` (field 路径) |
| **as_result** | StateChang../../ Interface Respons../../ Even../../ SideEffect | `postconditions../../ `side_effects` |
| **as_error** | Error | Interface.error_codes |

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

# 七个语义位置的映射（每个概念只配置适用的语义位置，可不填）
as_actor:
  type: ROLE | MODULE
  artifact_id: string

as_object:
  type: ENTITY
  artifact_id: string

as_action:
  type: INTERFACE | ORCHESTRATION | REACTION | SCHEDULE
  artifact_id: string

as_event:
  type: EVENT
  artifact_id: string

as_attribute:
  type: ENTITY_FIELD        # Entity.field
  artifact_id: string       # "ENT-005.expected_completion"

as_result:
  type: STATE_CHANGE | INTERFACE_RESPONSE | EVENT | SIDE_EFFECT
  artifact_id: string

as_error:
  type: ERROR
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

## 四、实现计划

### 4.1 支持的操作

| 操作 | 说明 |
|------|------|
| `get_by_id` | 根据 ID 获取业务概念 |
| `get_by_name` | 根据名称获取业务概念 |
| `list_all` | 列出所有业务概念 |
| `create` | 创建业务概念（不提交映射） |
| `add_mapping` | 添加映射（暂不支持修改映射） |
| `update` | 修改非映射字段（name, description, defined） |

### 4.2 不支持的功能

| 功能 | 阶段 | 说明 |
|------|------|------|
| 删除 (delete) | Stage 2 | 暂未实现 |
| 修改映射 (update_mapping) | Stage 2 | 暂未实现 |
| artifact_id 校验 | Stage 1 后期 | 其他模块尚未完善 |

### 4.3 文件结构

```
src/requirement/
├── __init__.py
├── common.py              # 新增：共享枚举和异常（MappingType, ArtifactType, 异常类）
├── business-concept.md   # 本文档
├── business_concept.py    # BusinessConcept 模型 + IBusinessConceptStorage 接口
└── business_concept_storage.py  # Storage 实现
```

### 4.4 接口设计

**模型定义** (`business_concept.py`)：
```python
@dataclass(frozen=True)
class Mapping:
    artifact_type: ArtifactType   # 映射目标制品类型
    artifact_id: str              # 制品 ID

@dataclass
class BusinessConcept:
    id: str = ""                 # 格式：BC-\d+（由存储层分配）
    name: str = ""
    description: str = ""
    defined: bool = False
    mappings: dict = field(default_factory=dict)  # 键为 MappingType，值为 Mapping

class MappingType(Enum):       # 枚举类，供所有 artifact 复用
    AS_ACTOR = "as_actor"
    AS_OBJECT = "as_object"
    AS_ACTION = "as_action"
    AS_EVENT = "as_event"
    AS_ATTRIBUTE = "as_attribute"
    AS_RESULT = "as_result"
    AS_ERROR = "as_error"

class ArtifactType(Enum):      # 映射目标制品类型枚举
    ROLE = "ROLE"
    MODULE = "MODULE"
    ENTITY = "ENTITY"
    INTERFACE = "INTERFACE"
    ORCHESTRATION = "ORCHESTRATION"
    REACTION = "REACTION"
    SCHEDULE = "SCHEDULE"
    EVENT = "EVENT"
    ENTITY_FIELD = "ENTITY_FIELD"
    STATE_CHANGE = "STATE_CHANGE"
    INTERFACE_RESPONSE = "INTERFACE_RESPONSE"
    SIDE_EFFECT = "SIDE_EFFECT"
    ERROR = "ERROR"

class NotFoundError(Exception):
    """ID 不存在"""

class MappingAlreadyExistsError(Exception):
    """映射已存在"""

class InvalidMappingTypeError(Exception):
    """非法的 mapping type"""

class InvalidArtifactTypeError(Exception):
    """非法的 artifact type"""

interface IBusinessConceptStorage:
    def get_by_id(record_id: str) -> BusinessConcept | None
    def get_by_name(name: str) -> BusinessConcept | None
    def list_all() -> list[BusinessConcept]
    def create(bc: BusinessConcept) -> BusinessConcept
    def add_mapping(record_id: str, mapping_type: str, artifact_type: str, artifact_id: str) -> BusinessConcept
    def update(record_id: str, **fields: object) -> BusinessConcept | None
    # delete 暂不支持
```

> `MappingType`（七个语义位置）与 `ArtifactType`（映射目标制品类型）定义在
> `src/requirement/common.py`，供所有制品复用。每个语义位置允许的制品类型由
> `ALLOWED_ARTIFACT_TYPES` 约束，映射时校验。

### 4.5 技术要点

1. **ID 格式**：`BC-\d+`，自增（由存储层分配，制品内的 `id` 字段始终等于存储记录的规范 ID）
2. **依赖 Storage 接口**：`src.db.Storage` 负责存取与 ID 分配，本层负责领域对象的序列化与业务规则
3. **映射校验**：不检查 artifact_id 是否真实存在（Stage 1 后期实现），但校验 artifact_type 是否属于该语义位置允许的类型
4. **create 行为**：创建时 mappings 为空字典
5. **add_mapping**：只能新增已存在的映射 key，不支持修改
6. **异常类型**：`NotFoundError`（ID 不存在）、`MappingAlreadyExistsError`（映射已存在）、`InvalidMappingTypeError`（非法语义位置）、`InvalidArtifactTypeError`（非法制品类型）、`InvalidBusinessConceptError`（制品校验失败）
7. **使用 dataclass 做数据校验**（与 `src/module`、`src/schema` 保持一致，不引入 pydantic 依赖）

### 4.6 测试计划

```
tests/requirement/
├── __init__.py
└── test_business_concept.py   # 新增测试文件
```

**测试覆盖**：
- `test_get_by_id_found` - 根据 ID 获取
- `test_get_by_id_not_found` - ID 不存在返回 None
- `test_get_by_name_found` - 根据名称获取
- `test_get_by_name_not_found` - 名称不存在返回 None
- `test_list_all` - 列出所有
- `test_create` - 创建业务概念（ID 自增、mappings 为空）
- `test_add_mapping` - 添加映射
- `test_add_mapping_already_exists` - 映射已存在则报错
- `test_update` - 修改非映射字段



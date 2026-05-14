# DB Package 设计规划

## 1. 定位

存储抽象层，只负责存储本身，包括：
- **ID**：唯一标识符，格式为 `{TYPE_PREFIX}-{NUMBER}`
- **Type**：制品类型，如 `DRAFT`, `REQ`, `US`, `ENT` 等
- **Data**：YAML 格式的字符串内容

本层**不识别**具体数据的 schema，所有结构化解析由上层负责。

## 2. Type 与 ID 前缀映射

| Type (小写全名) | ID 前缀 | 说明 |
|----------------|---------|------|
| draft | DRAFT- | 需求草稿 |
| requirement | REQ- | 结构化需求 |
| user-story | US- | 用户故事 |
| business-concept | BC- | 业务概念 |
| entity | ENT- | 实体 |
| interface | API- | 接口 |
| event | EVT- | 事件 |
| error | ERR- | 错误码 |
| process | PROC- | 流程 |
| orchestration | ORCH- | 编排 |
| reaction | SUB- | 订阅者 |
| schedule | SCH- | 定时任务 |
| repository | REPO- | 代码仓库 |
| code-ref | CREF- | 代码引用 |
| incident | INC- | 故障 |
| runbook | RB- | 运行手册 |
| playbook | PB- | 预案 |
| constraint | CON- | 约束 |
| metric | MET- | 指标 |
| role | ROLE- | 角色 |
| permission | PERM- | 权限 |
| dependency | DEP- | 依赖 |
| module | MOD- | 模块 |
| environment | ENV- | 环境 |
| pipeline | PIPE- | 流水线 |
| configuration | CONF- | 配置 |
| config-set | CSET- | 配置集 |
| secret | SEC- | 密钥 |
| acceptance-test | AT- | 验收测试 |
| scenario-test | ST- | 场景测试 |
| integration-test | IT- | 集成测试 |
| contract-test | CT- | 契约测试 |
| transition-test | TT- | 转换测试 |
| benchmark | BM- | 基准测试 |

映射关系由 `db` 层自行管理。

## 3. Python Interface 定义

```python
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Optional

@dataclass
class Record:
    """存储记录"""
    id: str          # 完整 ID，如 "REQ-1"
    type: str        # 类型，如 "requirement"
    data: str        # YAML 格式的数据

class Storage(ABC):
    @abstractmethod
    def get_by_id(self, id: str) -> Optional[Record]:
        """根据 ID 获取记录，返回 None 若不存在"""

    @abstractmethod
    def list_by_type(self, type: str) -> list[Record]:
        """列出指定类型的所有记录"""

    @abstractmethod
    def create(self, type: str, data: str) -> Record:
        """创建新记录，返回包含新 ID 的 Record"""

    @abstractmethod
    def replace(self, id: str, data: str) -> bool:
        """替换指定 ID 的数据，返回是否成功"""

    @abstractmethod
    def delete(self, id: str) -> bool:
        """删除指定 ID 的记录，返回是否成功"""
```

## 4. SQLite 实现

### 表设计

每个 type 对应一张表，表名为 `t_{type}`（如 `t_REQ`, `t_ENT`）。

```sql
CREATE TABLE t_DRAFT (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL
);

CREATE TABLE t_REQ (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL
);

-- 以此类推
```

### ID 生成

- 自增整数 ID
- 完整 ID 格式：`{TYPE_PREFIX}-{AUTO_INCREMENT_ID}`
- 例如：`REQ-1`, `REQ-2`, `ENT-100`

### 文件结构

```
src/db/
├── __init__.py
├── types.py          # Type 常量定义
├── mapping.py        # Type <-> ID 前缀映射
├── interface.py      # Storage 抽象接口
└── sqlite.py         # SQLite 实现
```

## 5. 单元测试

### 测试框架

使用 `pytest`，测试文件放在 `tests/` 目录下。

### 测试覆盖

1. **types.py 测试**：验证所有 Type 常量存在且唯一
2. **mapping.py 测试**：验证 Type 到前缀的双向映射正确
3. **interface.py 测试**：通过 mock 验证 Storage 接口契约
4. **sqlite.py 测试**：
   - 临时数据库初始化
   - CRUD 操作
   - ID 自增正确性
   - 类型与表名映射正确性

### 目录结构

```
tests/
└── db/
    ├── __init__.py
    ├── test_types.py
    ├── test_mapping.py
    ├── test_interface.py
    └── test_sqlite.py
```
# CrispSpec 项目现状

> 最后更新：2026-11-09 · 分支 `fix/toolchain-and-consistency` · 基线 `a619395`
>
> 本文记录项目当前的实际状态、已解决的问题、遗留问题与后续路线。
> **它描述的是事实，不是计划**——计划见 [`TODO.md`](TODO.md)，制品体系见 [`concepts.md`](concepts.md)。

---

## 一、项目定位

CrispSpec 试图让软件由**结构化制品（Structured Artifacts）**定义而非由散落的源码定义：

> 除了最开始那份反映人类意图的、模糊的"需求初稿"之外，软件生命周期内的一切——从系统架构、API 接口、数据库设计、业务流程、模块依赖到测试用例和代码本身——都必须由严谨的结构化制品来定义和驱动。代码只是这些制品的"执行态副产品"。

制品分 8 个域（需求 / 契约 / 行为 / 代码 / 故障 / 治理 / 交付 / 测试），通过 typed ID 互相引用形成知识图谱。

---

## 二、状态快照

| 检查项 | 命令 | 结果 |
|--------|------|------|
| 静态检查 | `uv run ruff check --ignore-noqa` | ✅ All checks passed |
| 单元测试 | `uv run pytest` | ✅ 149 passed |
| 链接检查 | `uv run src/checker/main.py` | ✅ 43 文件 / 0 错误 |
| 依赖锁定 | `uv lock --check` | ✅ up-to-date |

已从**全新 venv** 验证过（删掉 `.venv` 后重跑上述三条命令），CI（`.github/workflows/check.yaml`）在 ubuntu 上等价。

代码规模：`src/` + `tests/` 共 **3665 行** Python。

---

## 三、架构分层

```
┌─────────────────────────────────────────────────────────┐
│ 制品定义层  src/<domain>/*.md                            │
│   35 份制品定义（每个制品一份，含字段表 / 枚举 / YAML 示例）  │
├─────────────────────────────────────────────────────────┤
│ 制品管理层  src/<domain>/*.py                            │
│   3 个制品有实现：module / business-concept / type-def    │
├─────────────────────────────────────────────────────────┤
│ 存储层      src/db/                                      │
│   Storage ABC + SqliteStorage + 类型/前缀映射 + SQL 生成   │
├─────────────────────────────────────────────────────────┤
│ 工具层      src/checker/                                 │
│   Markdown 链接检查器（CI 用）                            │
└─────────────────────────────────────────────────────────┘
```

**存储层契约**（`src/db/interface.py`）：

- 每个制品类型一张表 `t_<type>`，列 `id / data / version`
- `id` = `{TYPE_PREFIX}-{ROWID}`，例如 `REQ-1`、`BC-2`
- `data` = 制品的 YAML 文本；`version` = UUID，用于乐观锁（`replace` / `delete` 都校验）
- `src/db/types.py` 定义 35 个制品类型常量；`src/db/mapping.py` 维护类型 ↔ ID 前缀映射

**制品管理器契约**（`src/module/module.py` 是范式）：

```python
manager = ModuleManager(storage)
record_id = manager.create_module(raw_dict)   # 解析 → 校验 → 落库
data      = manager.get_module(record_id)      # → dict | None
errors    = manager.verify_module(record_id, data)  # → list[str]，空表示合法
```

---

## 四、制品覆盖度

db 层注册了 **35** 个制品类型，**每个都有一份 `.md` 定义**（`type-def` 的定义在 `src/schema/schema.md`）。
但只有 **3** 个制品有 Python 实现。

> 逐个制品的进度、Stage 归属、依赖关系见 [`artifacts.yaml`](artifacts.yaml)（机器可读，
> 由 `tests/registry/` 保证与代码不漂移）。下表是它的汇总视图。

| 域 | 制品 | 定义 | 实现 | 缺口 |
|----|------|:----:|:----:|------|
| 需求域 | Draft / Requirement / User Story | ✅ | ❌ | 3 个管理器 |
| 需求域 | **Business Concept** | ✅ | ✅ | — |
| 契约域 | Entity / Interface / Event / Error | ✅ | ❌ | **4 个管理器（最关键）** |
| 行为域 | Process / Orchestration / Reaction / Schedule | ✅ | ❌ | 4 个管理器 |
| 代码域 | Repository / Code Ref | ✅ | ❌ | 2 个管理器 |
| 故障域 | Incident / Runbook / Playbook | ✅ | ❌ | 3 个管理器 |
| 治理域 | Constraint / Metric / Dependency / Role / Permission | ✅ | ❌ | 5 个管理器 |
| 交付域 | Environment / Pipeline / Configuration / Config Set / Secret | ✅ | ❌ | 5 个管理器 |
| 测试域 | Acceptance / Scenario / Integration / Contract / Transition / Benchmark | ✅ | ❌ | 6 个管理器 |
| 组织 | **Module** | ✅ | ✅ | — |
| 元制品 | **Type Def（Schema）** | ✅ | ✅ | — |

> 契约域是当前的最大瓶颈：Business Concept 的七个语义位置里，`as_object` / `as_attribute` / `as_error`
> 直接指向 Entity / Error，`as_action` 指向 Interface / Orchestration / Reaction / Schedule。
> **这些制品不落地，BC 的映射就没有真实 ID 可挂。**

**Stage 归属**（依据 [`TODO.md`](TODO.md) 的验收标准倒推）：

| Stage | 制品数 | 已完成 | 说明 |
|-------|------:|------:|------|
| Stage 1 | 17 | 3 | 一个需求的 Python CLI 工具端到端：需求链 → 契约 → 行为 → 代码 → 验证 |
| Stage 2 | 18 | 0 | 多子命令 + 制品修改与级联：事件、编排、治理、交付、故障域 |

---

## 五、本轮已修复

分支 `fix/toolchain-and-consistency` 共 4 个提交：

### 5.1 工具链（`375e298`）

| 问题 | 症状 | 修复 |
|------|------|------|
| 项目未打包成发行版 | `ModuleNotFoundError: No module named 'src'`，**全部测试收集失败** | `pyproject.toml` 加 `[tool.pytest.ini_options] pythonpath = ["."]` |
| ruff 误判 import 归属 | `src.db.*` 被当成第三方，与 `yaml` 混在一组 → 2 个 I001 | 加 `[tool.ruff] src = ["."]` |
| 无效的 entry point | `[project.scripts] check = "sh:..."`（模块不存在、`sh:` 是 Linux 风格） | 删除，命令写进 `AGENTS.md` |
| 链接检查器在 Windows 崩溃 | `UnicodeEncodeError: 'gbk' codec can't encode '\u2713'` | stdout/stderr 重配为 UTF-8 + `errors="replace"` |
| 根目录逃逸检测是死代码 | `relative_to()` 的返回值被丢弃，检测从未生效 | 改为真实检查并报告 |

> venv 本身也指向了已被卸载的 Windows Store Python，已重建。

### 5.2 `secret` 命名三方漂移（`375e298`）

文档写 `SEC-\d+` / `secret`，代码里却是 `confidential` / `confidential_value` / `CONFIDENTIAL` 三种写法。
后果：`is_valid_type("confidential")` 返回 `False`，但 `ALL_TYPES` 里仍有它 → `SqliteStorage._ensure_table()`
直接抛 `ValueError`，**Secret 制品根本存不进库**。已统一为 `secret` / `SEC`。

### 5.3 代码域定义缺失（`568bea8`）

`concepts.md` 引用了 `src/code/repository.md` 和 `src/code/code-ref.md`，但两个文件根本不存在；
且那两行用的是纯反引号路径而非 markdown 链接，所以链接检查器抓不到这个洞。已补齐定义并统一为链接。

### 5.4 制品身份分裂（`568bea8`）

`ModuleManager.create_module` 存在两个身份：存储层按 rowid 分配 `MOD-1`，但 YAML 里的
`id: "MOD-001"` 被原样存下。已改为**存储分配的 ID 为准**，并由测试锁定。

### 5.5 Business Concept 实现（`6f4d4ea`）

- `src/requirement/common.py` — `MappingType`（七个语义位置）、`ArtifactType`（映射目标类型）、
  `ALLOWED_ARTIFACT_TYPES` 约束表、异常体系
- `src/requirement/business_concept.py` — `Mapping` / `BusinessConcept` 模型 + `IBusinessConceptStorage`
- `src/requirement/business_concept_storage.py` — SQLite 实现（`get_by_id` / `get_by_name` /
  `list_all` / `create` / `add_mapping` / `update`）

### 5.6 补测试（`568bea8` / `6f4d4ea`）

`tests/module/`（35 个）+ `tests/requirement/`（24 个）。此前 `src/module` 是唯一没有测试的制品管理器。

---

## 六、遗留问题与风险

### P0 —— 阻塞 Stage 1 验收

**6.1 制品实现覆盖率 3/35，还有 32 个管理器待建。**
Stage 1 的验收标准是"1 个新需求完整实现一个 Python CLI 工具"，需要
`Draft → Requirement → User Story → BC → Interface → Entity → Process → Module → Code Ref`
全链路打通。目前只有 BC、Module 两环。

**6.2 没有 CLI 层。**
所有能力目前只能通过 Python API 调用。根目录的 `main.py` 还是 `Hello from crispspec!` 的空壳。
Stage 1 要交付的正是命令行工具本身。

**6.3 契约域没有实现。**
见第四节。BC 的映射目标大半在契约域，这是最优先的缺口。

### P1 —— 架构缺口

**6.4 `artifact_id` 不做存在性校验。**
`BusinessConceptStorage.add_mapping` 接受任意字符串的 `artifact_id`，不检查目标制品是否真实存在。
设计文档标注为"Stage 1 后期"。等 Interface / Entity 落地后需要接上跨制品引用校验。

**6.5 缺少跨制品引用校验层。**
目前每个 manager 只能看到自己类型的表。`BC → ROLE`、`Module → API`、`Code Ref → ENT` 这类
引用**无法验证目标是否存在**。需要一个统一的 registry / validator。
（`Module.verify_module` 目前只校验格式，不校验被引用制品。）

**6.6 制品管理器的接口尚未统一。**
`ModuleManager` / `Schema` 是"薄 manager"（解析 + 校验 + 落库），
`BusinessConceptStorage` 是"领域仓储"（带 add_mapping / update 等业务方法）。
两种风格并存，新增管理器时需要先决定沿用哪一种。

**6.7 `src/db/plan.md` 与实际实现有偏差。**
`plan.md` 里的 `Record` 只有 `id / type / data`，实际实现多了 `version`（乐观锁）。
映射表也缺 `type-def`。文档没跟上代码。

### P2 —— 一致性与文案

**6.8 文档里 186 处 `../../` 字符损坏（25 份 `.md` 受影响）。**
损坏特征是 `../../` 粘在单词后面（合法的相对链接 `../module/module.md` 不算）；典型例子：

| 原文（损坏） | 应为 |
|-------------|------|
| `` `UUID../../ `STRING../../ `INTEGER` `` | `UUID` / `STRING` / `INTEGER` |
| `` `http../..//www.apache.o../../licens../../LICENSE-2.0` `` | `http://www.apache.org/licenses/LICENSE-2.0` |
| `` `As../../Shanghai` `` | `Asia/Shanghai` |
| `打包../../发布` | `打包/发布` |

看起来是文档生成时 `/` 被某个替换规则吃掉了。**纯文案问题，不影响结构**，但影响可读性。
可脚本批量修复（把枚举分隔用的 `../../` 还原成 `/ `，把 URL 里的还原成 `/`）。

**6.9 `concepts.md` 的 mermaid 关系图没画 BC 的映射边。**
图里 `BC["Business Concept"]` 是个孤立节点，只有 `DRAFT -.-> USES .-> BC` 两条虚线。
BC 的七条语义映射（`as_actor → ROLE/MODULE`、`as_object → ENTITY` 等）在图上完全没体现。

**6.10 `src/checker/` 没有测试。**
`tests/` 下有 `db / schema / module / requirement` 四个目录，唯独链接检查器没有。

**6.11 CI 只跑 ubuntu。**
链接检查器的编码问题正是 Windows 专属故障，却因为 CI 不跑 Windows 而漏网。
建议加一条 `runs-on: windows-latest` 的 job。

**6.12 `src/requirement/natural-language-structuring.md` 归属不明。**
它是过程文档而非制品，但放在制品目录里，且不在 `src/db/types.py` 注册。

---

## 七、Stage 1 路线图

按 `TODO.md` 的验收标准倒推，**建议的推进顺序**：

```
① 契约域     Entity → Interface → Error        ← 最高优先，BC 映射依赖它
② 行为域     Process → Orchestration            ← Process 支撑状态机
③ 代码域     Code Ref                          ← 制品到源码的落点
④ 需求域     Draft → Requirement → User Story   ← 消歧引擎的产物
⑤ CLI 壳     argparse/click 命令行骨架          ← 把已有能力暴露出去
⑥ 端到端     拿一个真实需求跑通全链路            ← Stage 1 验收
```

**关于"自举"的取舍**：Stage 1 的验收标准是端到端的，但接口契约（Interface 长什么样）
本身要靠真实用例才能定义。两种走法：

- **先契约域后 CLI**：先把 Interface / Entity / Process 定死，再写 CLI —— 契约稳定，但有"设计先行、
  脱离实际"的风险
- **先 CLI 骨架后契约域**：先搭出能跑的 CLI 骨架，用它倒逼出接口形态 —— 更贴近真实，但前期会有返工

建议：**先做 ① 的 Entity / Interface，但只做最小可用字段集**，同时用 ⑤ 的 CLI 骨架验证。

---

## 八、常用命令

```bash
uv sync --all-groups                              # 安装依赖

uv run ruff check --ignore-noqa                   # 静态检查
uv run pytest                                     # 单元测试
uv run pytest tests/module -q                     # 单个测试目录
uv run src/checker/main.py                        # Markdown 链接检查
uv run src/checker/main.py . -v                   # 带文件清单
```

项目**没有**打包成发行版，`src` 包不是靠安装引入的——pytest 靠
`[tool.pytest.ini_options] pythonpath = ["."]` 从仓库根目录导入。若将来改成正式打包，
这里需要重新处理。

---

## 九、决策记录

本分支做出的、可能影响后续设计的决定：

| 决定 | 理由 | 影响面 |
|------|------|--------|
| **制品管理器用 dataclass，不用 pydantic** | `src/module`、`src/schema` 都是纯 dataclass，pydantic 不在依赖里 | 后续管理器照此办理 |
| **参数名 `id` → `record_id`** | ruff `select = ["ALL"]` 会拦 A002；`src/db/interface.py` 本来就用 `record_id` | 全部新接口 |
| **存储分配的 ID 为准** | 存储层按 rowid 分配，制品 YAML 里的 `id` 不得与之冲突 | **所有**尚未实现的管理器都需遵守 |
| **ruff `src = ["."]`** | 让 `src.db.*` 被识别为 first-party | 全项目 |
| **`pytest pythonpath = ["."]`** | 项目未打包，避免为测试单独安装 | 全项目 |
| **BC 映射校验制品类型，不校验 ID 存在性** | 目标制品大多还没实现 | 待契约域落地后补 |
| **不动 `src/db/` 的存储契约** | 存储层是所有制品的地基，改动波及面大 | — |

---

## 十、相关文件

| 文件 | 内容 |
|------|------|
| [`README.md`](README.md) | 项目宏大目标与体系总览 |
| [`artifacts.yaml`](artifacts.yaml) | **制品实现进度登记表**（机器可读，含 Stage / 优先级 / 依赖） |
| [`concepts.md`](concepts.md) | 制品体系全景：域模型、制品总览、关系图、ID 规范 |
| [`TODO.md`](TODO.md) | Stage 1 / Stage 2 目标与验收标准 |
| [`AGENTS.md`](AGENTS.md) | 环境准备与工具用法 |
| [`src/db/plan.md`](src/db/plan.md) | 存储层设计规划（**部分过时，见 6.7**） |
| `src/<domain>/*.md` | 逐个制品的字段定义、枚举、YAML 格式示例 |

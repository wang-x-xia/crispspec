# CrispSpec 项目现状

> 最后更新：2026-11-09 · 分支 `feature/design-frontend`
>
> 本文记录项目当前的实际状态。**它描述的是事实，不是计划**——
> 计划见 [路线图](roadmap.md)，体系见 [制品体系概览](concepts.md)，
> 愿景见 [为什么是结构化制品](vision.md)。

---

## 一、项目定位

CrispSpec 试图让软件由**结构化制品（Structured Artifacts）**定义，而非由散落的源码定义：

> 除了最开始那份反映人类意图的、模糊的"需求初稿"之外，软件生命周期内的一切——从系统架构、API 接口、数据库设计、业务流程、模块依赖到测试用例和代码本身——都必须由严谨的结构化制品来定义和驱动。代码只是这些制品的"执行态副产品"。

制品分 11 个域（需求 / 契约 / 行为 / 代码 / 故障 / 治理 / 访问控制 / 交付 / 验证 / 组织 / 元制品），
通过 typed ID 互相引用形成知识图谱。

**当前阶段是设计期**：仓库只保留"制品体系"与"讲清楚它的工具"，不含任何实现代码。

---

## 二、仓库结构

```
crispspec/
├── README.md                 项目入口
├── AGENTS.md                 给 AI 协作者的工作说明
└── design/                   ← 唯一的工程：制品体系 + 它的可视化
    ├── content/              制品定义文档（唯一事实来源）
    │   ├── vision.md         愿景与目标全景
    │   ├── concepts.md       制品体系全景：域模型、制品总览、主线、关系图
    │   ├── roadmap.md        设计期路线图
    │   ├── status.md         本文
    │   ├── requirement/      需求域制品
    │   ├── contract/         契约域制品
    │   ├── behavior/         行为域制品
    │   ├── code/             代码域制品
    │   ├── module/           组织单元
    │   ├── governance/       治理域制品
    │   ├── access/           访问控制域制品（含 RBAC 子系统设计）
    │   ├── delivery/         交付域制品
    │   ├── incident/         故障域制品
    │   ├── test/             验证域制品
    │   ├── schema/           元制品：YAML Schema 设计
    │   └── archive/          历史文档（实现期遗留，不维护）
    ├── data/artifacts.yaml   制品登记表（类型 / 前缀 / 域 / 用途 / 主线）
    ├── scripts/              构建脚本：YAML + Markdown → 前端数据
    ├── tests/                数据一致性测试
    └── src/                  前端应用（React + TypeScript + Vite）
```

### 删掉了什么

| 删除内容 | 原因 |
|----------|------|
| `src/db/`、`src/module/`、`src/requirement/*.py`、`src/schema/*.py` | 实现期代码，设计定稿前不再维护 |
| `src/checker/`（Markdown 链接检查器） | 链接检查由前端构建脚本接管（解析时校验文档内链） |
| `tests/`（pytest） | 随实现代码一并移除；数据一致性改由 `design/tests/` 承担 |
| `.github/workflows/check.yaml`（ruff + pytest） | 没有 Python 了；CI 改为校验前端构建 |
| `pyproject.toml` / `uv.lock` | 依赖管理从 uv 切到 npm |
| `docs/artifact-graph.html` | 静态生成物被前端应用取代（它能看、能搜、还能读全文） |

> **这不是倒退，是把顺序摆正**：先把制品定义成可检验的形式，再写代码。

---

## 三、制品体系现状

| 检查项 | 手段 | 结果 |
|--------|------|------|
| 制品类型 | `design/data/artifacts.yaml` | 35 种，每种一份定义文档 |
| 域 | 同上 `domains:` | 11 个 |
| 关系边 | 各定义文档的 `## 关联` 表 | 83 条（含 Business Concept 的 9 条映射边） |
| 开发主线 | 同上 `mainline:` | 10 个纵向阶段 + 3 个横切阶段，39 次交接 |
| 字段与枚举 | 各定义文档的 `## 字段定义` | 逐制品解析，节点详情面板直接展示 |
| 子结构 | 各定义文档的 `## 子结构定义` | 同上 |

一致性由构建脚本与测试保证（见 [第六节](#六一致性保证)）：

- 每种制品**恰好**出现在一个阶段的 `produces` 或 `prepares` 里——主线不重不漏地串起全部 35 种制品
- 每条 `handoff` 都必须是制品定义里**真实存在**的关系边——主线不是编出来的
- 横切阶段只 `prepares`、不 `produces`——它们不推进主线
- 每份定义文档都存在，且能解析出字段表与关系表

---

## 四、前端应用

`design/` 是一个 **Vite + React + TypeScript** 应用，把制品体系变成可交互的网页：

| 视图 | 内容 |
|------|------|
| 概览 | 愿景、设计原则、域模型、制品总览（带用途）、主线表格、ID 规范 |
| 体系图 | 35 种制品 + 83 条关系的力导向图；按域/关系类型筛选、搜索、聚焦 |
| 开发主线 | 10 个阶段带 + 39 次交接；横切阶段单独标出 |
| 制品 | 35 种制品的字段、枚举、子结构、映射、出入关系，以及完整定义文档 |
| 文档 | 全部 Markdown 文档（愿景、体系、RBAC 子系统、自然语言结构化、路线图……） |

数据不是手写的：`scripts/build-content.mjs` 读 `data/artifacts.yaml` +
`content/**/*.md`，解析出字段表、枚举表、关系表，编译成前端消费的 JSON。
**改了定义文档，网页就变**——不存在"图和文档对不上"的可能。

---

## 五、已确定的决策

| 决定 | 理由 | 影响面 |
|------|------|--------|
| **制品管理器用 dataclass，不用 pydantic** | 依赖越少越好，实现期再定 | 实现期 |
| **存储分配的 ID 为准** | 制品 YAML 里的 `id` 不得与存储分配冲突 | 实现期 |
| **域是关注点的横向切分，主线是工作顺序的纵向推进** | 两者正交，混为一谈会让"谁产出什么"失真 | 全部制品定义、`artifacts.yaml`、前端 |
| **主线区分 `produces` 与 `prepares`** | 不是每件制品都由主线产出：业务概念可以预先定义好，错误目录通常先攒出来，环境与密钥由运维备好。硬说"这一步产出它"就是失真 | `artifacts.yaml` 的 `mainline:` 段、前端 |
| **Role / Permission 从治理域拆到访问控制域** | "谁能访问什么"和"必须做到什么、性能底线在哪"是两件事 | 全部制品定义、`artifacts.yaml`、前端 |
| **Business Concept 的映射是一个列表 `as`，不是七个语义槽位** | 语义位置不是制品体系的区分维度，拆成槽位反而限制了能表达的东西 | `business-concept.md`、`artifacts.yaml` |
| **制品定义文档是唯一事实来源** | 图、清单、主线都从 `## 字段定义` 与 `## 关联` 表生成，不维护第二份 | 全部 |
| **需求不区分概念的语义位置** | 早期版本给需求准备了 `as_actor` / `as_object` 这类固定槽位，每个只能填一个目标。但语义位置不是制品体系的区分维度——同一个概念既是 actor 又是 object 并不矛盾。合并成“需求引用一批业务概念”之后，位置只是目标制品的属性 | `requirement.md`、`business-concept.md`、需求域的关系边 |
| **一对制品之间只用一个关系名** | 同一事实起两个名字（`RESOLVED_BY` / `RESOLVES`、`USES_CONFIG` / `APPLIES_TO`）会让图读不懂。现在只允许“归属（`CONTAINS`）+ 一个行为关系”这种组合，构建时会报错 | 全部关系表 |
| **设计期不写实现代码** | 先把制品定义成可检验的形式，再写代码 | 仓库结构、CI |

---

## 六、一致性保证

```bash
cd design
npm install
npm run build      # 构建前端（同时跑数据一致性校验）
npm test           # 只跑一致性测试
```

构建脚本在生成数据前会校验：

- 每种制品恰好属于一个主线阶段
- 每条主线交接都是真实存在的关系边
- 横切阶段不产出制品
- 每份定义文档存在，且能解析出字段表与关系表
- 文档内部的相对链接指向存在的文件

---

## 七、遗留问题与风险

**P0 —— 影响体系完整性**

1. **35 种制品中，部分字段定义仍是"预留"状态。**
   `Requirement` 的 EARS / SVO 模式字段只有标题没有内容，`Process` 的 `Forbidden`
   子结构缺少枚举取值。定义补齐之前，这些制品还不能算"可实现"。

2. **跨制品引用只声明、不校验。**
   `module_id`、`actor_role_id`、`owner_module_id` 这些 typed reference 目前只有格式约束，
   没有"目标制品必须存在"的校验规则。实现期需要一个统一的引用校验层。

3. **制品与文档之间仍有少量措辞漂移。**
   例如 `concepts.md` 的主线表格是人工维护的副本，与 `artifacts.yaml` 的 `mainline:` 段
   靠人工保持同步。后续应让前端直接渲染登记表，前端已经是这么做的——
   文档里的表格只作离线阅读用。

**P1 —— 设计表达**

4. **`../../` 字符损坏已修复**（本轮完成）。
   历史文档中 60 余处 `/` 被替换成 `../../`，导致枚举值、URL、中文短语被截断。
   现已逐条修复为原文语义。

5. **需求的异常 / 副作用建模待定。**
   Event 曾声明过 `TRIGGERED_BY` 自 Requirement（表达“需求的异常会触发某个事件”），
   但 Requirement 侧从来没有对应的异常字段——这条边是悬空的，本轮已移除。
   要么给 Requirement 补一套异常建模，要么明确异常不属于需求层。

6. **历史实现期文档已归档。**
   `content/archive/db-plan.md` 记录了 Python 存储层的设计，属于实现期产物，
   只作参考，不维护。

7. **可观测域与变更域尚未定义。**
   见 [路线图](roadmap.md)。

---

## 八、常用命令

```bash
cd design
npm install          # 安装依赖
npm run dev          # 本地开发服务器（热更新）
npm run build        # 生成数据 + 类型检查 + 生产构建
npm run preview      # 预览生产构建
npm test             # 数据一致性测试
npm run lint         # ESLint
```

---

## 九、相关文件

| 文件 | 内容 |
|------|------|
| `design/README.md` | 项目入口与体系总览 |
| 仓库根目录的 `AGENTS.md` | 给 AI 协作者的工作说明 |
| [`design/content/vision.md`](vision.md) | 愿景与目标全景 |
| [`design/content/concepts.md`](concepts.md) | 制品体系全景：域模型、制品总览、主线、关系图、ID 规范 |
| [`design/content/roadmap.md`](roadmap.md) | 设计期路线图 |
| [`design/data/artifacts.yaml`](../data/artifacts.yaml) | 制品登记表（机器可读） |
| `design/content/<domain>/*.md` | 逐个制品的字段定义、枚举、关系表 |

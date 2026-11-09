# CrispSpec — Software Defined by Structured Artifacts

> **本项目当前处于设计期。** 仓库里没有实现代码，只有制品体系本身，
> 和一个把它讲清楚的交互式前端。

## 宏大目标

### 一句话定义

> **除了最开始那份反映人类意图的、模糊的"需求初稿"之外，软件生命周期内的一切——从系统架构、API 接口、数据库设计、业务流程、模块依赖到测试用例和代码本身——都必须由严谨的"结构化制品（Structured Artifacts）"来定义和驱动。**

### 目标全景

```
人类模糊的需求初稿（唯一允许非结构化的输入）
        │
        ▼
┌──────────────────────────────────────┐
│    消歧引擎（渐进式结构化转化）         │
│    将模糊需求转化为良好定义的制品        │
└──────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│    结构化制品体系（软件的真正"源码"）    │
│                                      │
│    需求制品 → 架构制品 → 数据制品       │
│    → 接口制品 → 流程制品 → 测试制品     │
│    → 代码制品                          │
│                                      │
│    所有制品之间通过严格的关系边互联       │
└──────────────────────────────────────┘
        │
        ▼
    代码仅仅是这些结构化制品的"执行态副产品"
```

### 核心信念

- **软件的本质不是一堆散乱的源代码文件，而是一个由高层结构化制品层层推演的确定性图谱。**
- **多义性不是需求的固有属性，而是信息不足的表现。** 通过在产品侧系统性地补充结构化信息，任何多义的需求都可以被收敛为良好定义的制品。
- **语义鸿沟不是不可逾越的天然屏障，而是应该被主动"填平"的沟壑。** 填充物就是结构化信息。

---

## 仓库结构

```
crispspec/
├── README.md          本文件
├── AGENTS.md          给 AI 协作者的工作说明
└── design/            制品体系 + 它的交互式前端
    ├── content/       设计文档（唯一事实来源）
    ├── data/          制品登记表
    ├── scripts/       编译脚本
    ├── tests/         一致性测试
    └── src/           前端应用
```

**整个工程都在 `design/` 里。** 它既是被展示的内容，也是展示内容的工具。

### 制品体系

35 种制品，分 11 个域：

- **需求域**：Draft、Requirement、User Story、Business Concept
- **契约域**：Entity、Interface、Event、Error
- **行为域**：Process、Orchestration、Reaction、Schedule
- **代码域**：Repository、Code Ref
- **故障域**：Incident、Runbook、Playbook
- **治理域**：Constraint、Metric、Dependency
- **访问控制域**：Role、Permission
- **交付域**：Environment、Pipeline、Configuration、Config Set、Secret
- **验证域**：Acceptance / Scenario / Integration / Contract / Transition Test、Benchmark
- **组织单元**：Module
- **元制品**：Type Def

它们通过 **89 条 typed ID 关系边**互相引用，形成一张知识图谱；
**10 个主线阶段**把 35 种制品串成一条不重不漏的链（外加 3 个横切阶段）。

---

## 交互式前端

```bash
cd design
npm install
npm run dev      # http://localhost:5173
```

前端把整个体系摊开：

| 视图 | 内容 |
|------|------|
| **概览** | 愿景、设计原则、域模型、35 种制品的用途清单、主线表格 |
| **体系图** | 制品全景关系图——按域着色，按关系类型筛选，搜索、缩放、拖拽；点开看完整字段表 |
| **开发主线** | 从意图到运维的纵向链路：每一步的产出、可提前准备的东西、交接边 |
| **制品** | 每种制品的字段、枚举、子结构、映射、出入关系，以及完整定义文档 |
| **文档** | 全部设计文档——愿景、体系概览、RBAC 子系统、自然语言结构化、路线图…… |

> 页面里的每个数字、每条边、每个字段都来自仓库自身：
> `design/data/artifacts.yaml`（登记表）+ 各制品定义文档里的 `## 字段定义` 与 `## 关联` 表。
> **没有第二份手写的数据**，所以图和文档不可能对不上。

---

## 为什么现在只有设计

设计期先把"制品应该长什么样"说清楚，并让这些说法**可被机器检查**：

- 每种制品恰好属于一个主线阶段
- 每条主线交接都是真实存在的关系边
- 横切阶段只准备、不产出
- 每份定义文档都存在，且能解析出字段表
- 文档内部的相对链接都指向存在的文件

这五条由 `design/scripts/build-content.mjs` 与 `design/tests/` 双重保证——
违反了，`npm run build` 直接失败。

实现期（存储、校验、CLI、代码生成）等制品定稿后再启动。

---

## 延伸阅读

| 文档 | 内容 |
|------|------|
| [`design/content/vision.md`](design/content/vision.md) | 愿景与目标全景 |
| [`design/content/concepts.md`](design/content/concepts.md) | 制品体系全景：域模型、制品总览、主线、关系图、ID 规范 |
| [`design/content/roadmap.md`](design/content/roadmap.md) | 路线图：设计期的验收标准与后续阶段 |
| [`design/content/status.md`](design/content/status.md) | 项目现状：仓库结构、已确定的决策、遗留问题 |
| [`design/data/artifacts.yaml`](design/data/artifacts.yaml) | 制品登记表（机器可读） |
| [`design/README.md`](design/README.md) | 前端工程说明：怎么跑、怎么加制品 |
| [`AGENTS.md`](AGENTS.md) | 给 AI 协作者的工作说明 |

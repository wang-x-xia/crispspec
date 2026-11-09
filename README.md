# CrispSpec — Software Defined by Structured Artifacts

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

## 项目结构

本项目定义了一套完整的结构化制品体系，用于描述软件系统的各个方面：

- **需求域**：Draft、Requirement、User Story、Business Concept
- **契约域**：Entity、Interface、Event、Error
- **行为域**：Process、Orchestration、Reaction、Schedule
- **代码域**：Repository、Code Ref
- **故障域**：Incident、Runbook、Playbook
- **治理域**：Constraint、Metric、Dependency
- **访问控制域**：Role、Permission
- **交付域**：Environment、Pipeline、Configuration、Config Set、Secret
- **测试域**：Acceptance Test、Scenario Test、Integration Test、Contract Test、Transition Test、Benchmark

详细的制品定义请参考 [`concepts.md`](concepts.md) 和 `src/` 目录下的各个子模块。

### 制品图谱（交互网页）

[`docs/artifact-graph.html`](docs/artifact-graph.html) 把整个制品体系渲染成一张可交互的关系图，
提供三种视图：

- **体系图** —— 35 种制品类型的全景网络：按域着色，标注 ID 前缀、实现状态、Stage；
  90 条关系边来自每份制品定义的 `## 关联` 表（不是另维护一份清单）
- **开发主线** —— 从意图到运维的**纵向链路**：10 个阶段把 35 种制品串成一条不重不漏的链；
  区分「产出」与「可提前准备」，39 次交接全部是真实存在的关系边；
  横切关注点（治理 / 访问控制 / 制品结构）单独标出
- **实例图** —— 传入制品数据库后，真实制品与它们之间的引用（含悬空引用标记）

点击节点看**完整字段表、枚举、映射、出入关系**；点击主线阶段看**该阶段的制品与交接**。
按域 / 关系类型 / 实现状态筛选，搜索、缩放、拖拽。

> 网页由 `src/viz/` 从仓库自身的数据生成，不手写、不依赖 CDN、不联网。
> 改了制品定义后重新生成即可：

```bash
uv run python -m src.viz.build
```

### 开发主线

主线是"工作顺序"，域是"关注点"——两者是正交的。主线声明在 `artifacts.yaml` 的 `mainline:` 段：

```yaml
mainline:
  - id: requirement
    label: 结构化需求
    question: 消歧之后的需求是什么？
    produces: [requirement]
    # 业务概念可以预先定义好，也可以在结构化需求时创建——它不是这一步的必然产物
    prepares: [business-concept]
    handoff:
      - {relation: DISAMBIGUATED_INTO, from: draft, to: requirement}
```

**`produces` 与 `prepares` 的区别是这张表的关键**：主线不声称自己产出所有制品。
业务概念可能半年前就定义好了，错误目录通常先攒出来，环境与密钥由运维预先备好——
主线只说它们在对应阶段已经就位，不规定它们何时产生。

三条约束由 `tests/registry/` 保证：

- 每种制品**恰好**出现在一个阶段的 `produces` 或 `prepares` 里——主线不重不漏地串起全部 35 种制品
- 每条 `handoff` 都必须是制品定义里**真实存在**的关系边——主线不是编出来的
- 横切阶段只 `prepares`、不 `produces`——它们不推进主线

### 延伸阅读

| 文档 | 内容 |
|------|------|
| [`docs/artifact-graph.html`](docs/artifact-graph.html) | **制品图谱**：体系图 / 开发主线 / 实例图 |
| [`STATUS.md`](STATUS.md) | **项目现状**：当前进度、制品覆盖度、遗留问题与风险 |
| [`artifacts.yaml`](artifacts.yaml) | **制品实现进度登记表**：35 个制品的定义 / 实现 / Stage / 依赖 / 主线阶段 |
| [`TODO.md`](TODO.md) | Stage 1 / Stage 2 的目标与验收标准 |
| [`concepts.md`](concepts.md) | 制品体系全景：域模型、关系图、ID 规范 |
| [`AGENTS.md`](AGENTS.md) | 环境准备与工具用法 |

---
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
- **治理域**：Constraint、Metric、RBAC、Dependency
- **交付域**：Environment、Pipeline、Configuration、Config Set、Secret
- **测试域**：Acceptance Test、Scenario Test、Integration Test、Contract Test、Transition Test、Benchmark

详细的制品定义请参考 [`concepts.md`](concepts.md) 和 `src/` 目录下的各个子模块。

---
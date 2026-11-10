# AGENTS.md — 给 AI 协作者的工作说明

> 本项目处于**设计期**：仓库里没有实现代码，只有制品体系与展示它的前端。
> 改动前先读 [`README.md`](README.md) 与 [`design/content/status.md`](design/content/status.md)。

---

## 仓库结构

```
crispspec/
├── README.md          项目入口
├── AGENTS.md          本文
└── design/            唯一的工程
    ├── content/       设计文档——唯一事实来源
    ├── data/artifacts.yaml   制品登记表
    ├── scripts/       编译脚本（登记表 + 文档 → 前端数据）
    ├── tests/         体系一致性测试
    └── src/           前端应用（React + TypeScript + Vite）
```

---

## 环境准备

```bash
cd design
npm install
```

---

## 代码检查

CI（`.github/workflows/design.yml`）执行以下四步，本地可用同样的命令验证：

```bash
cd design
npm run build     # 编译内容 + 类型检查 + 生产构建（编译内容时会校验体系一致性）
npm test          # 体系一致性测试
npm run lint      # ESLint
```

> **改完设计文档，一定要跑 `npm run build`。**
> 它会重新编译 `content/` + `data/`，并检查体系是否自洽——
> 改了关系却忘了改主线、链接指向不存在的文件，都会在这里报错。

---

## 制品体系

### 唯一事实来源

每种制品的**定义文档**（`design/content/<domain>/<artifact>.md`）是唯一事实来源。
前端展示的一切——图、清单、详情面板、字段表——都是从这些文档编译出来的：

| 文档小节 | 编译成什么 |
|----------|------------|
| `## 目标` | 制品的用途摘要 |
| `## 字段定义` | 字段表 + 枚举表 |
| `## 子结构定义` | 子结构表 |
| `## 关联` | 关系边（边类型、出入方向、目标制品） |
| `## 映射关系` | Business Concept 的 `as` 映射 |

**不要**在别处再维护一份字段清单或关系清单——它们会漂移。

### 关系外置，字段不重复声明

指向其它制品的字段（`xxx_id`、`xxx_ids`）**不写进字段表**：
关系只写在 `## 关联` 表里，字段表只描述这件制品自己的数据。
两者说同一件事，就是两处会漂移的副本。

### 登记表

`design/data/artifacts.yaml` 声明每种制品的：类型键、ID 前缀、ID 模式、所属域、
定义文档路径、**用途**（`purpose`，一句话说明它解决什么问题）、备注，
以及开发主线（`mainline:` 段）。

### 体系不变量

以下五条由构建脚本与测试保证，违反即构建失败：

1. 每种制品**恰好**出现在一个主线阶段的 `produces` 或 `prepares` 里
2. 每条 `handoff` 都必须是制品定义里**真实存在**的关系边
3. 横切阶段（`lateral: true`）只 `prepares`、不 `produces`
4. 每份定义文档都存在，且能解析出字段表
5. 文档内部的相对链接都指向存在的文件

---

## 改动的规矩

### 加一种制品

1. 写定义文档：`design/content/<domain>/<artifact>.md`，
   至少包含 `## 目标`、`## 字段定义`、`## 关联` 三节；
   `## 关联` 的表是三列：`| 方向 | 边类型 | 目标制品 |`，
   方向用 `出 →` / `← 入` / `出 ↔`，目标制品用 markdown 链接。
2. 在 `design/data/artifacts.yaml` 登记它（含 `purpose`）。
3. 归入主线阶段，并写清交接边。
4. `npm run build`。

### 改关系

改 `## 关联` 表就行——但要记得检查主线：如果这条边是交接边，
`mainline:` 里的 `handoff` 也要跟着改，否则构建会报"不是真实存在的关系边"。

### 改前端

- 视图组件在 `design/src/components/`
- 布局算法（力导向、主线排布）在 `design/src/graph/layout.ts`
- 路由在 `design/src/router.ts`
- 数据是 `design/src/generated/content.json` 的类型化外壳（`design/src/data.ts`），
  **由构建脚本生成，不要手改**

---

## 约定

- **页面是生成物，不是手写文件。** 改了制品定义后必须重新构建，
  `design/tests/` 里有测试锁定内容与源文档不漂移。
- **页面自包含**：不引用 CDN、不联网，构建产物可以直接双击打开。
- **中文优先**：界面文案、文档、注释都用中文；代码标识符用英文。
- **不引入实现期代码**：设计期不写 Python/后端代码，也不加实现期的流水线。

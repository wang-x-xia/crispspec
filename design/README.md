# CrispSpec Design — 制品体系的可交互前端

这个目录是 CrispSpec 的**全部工程**：制品体系（`content/` + `data/`），
以及把它讲清楚的工具（本目录的前端应用）。

```bash
npm install       # 安装依赖
npm run dev       # 本地开发服务器（http://localhost:5173）
npm run build     # 编译内容 + 类型检查 + 生产构建（输出到 dist/）
npm run preview   # 预览生产构建
npm test          # 体系一致性测试
npm run lint      # ESLint
```

## 目录

| 路径 | 内容 |
|------|------|
| `content/` | **设计文档**——制品定义与设计说明，唯一事实来源 |
| `data/artifacts.yaml` | **制品登记表**——35 种制品的类型、ID 前缀、域、用途，以及开发主线 |
| `scripts/` | 构建脚本：把登记表 + 文档编译成前端消费的 JSON |
| `tests/` | 体系一致性测试 |
| `src/` | 前端应用（React + TypeScript + Vite） |
| `src/generated/content.json` | 编译产物（构建时生成，不入库） |

## 数据是怎么流动的

```
data/artifacts.yaml  ┐
                     ├─→ scripts/build-content.mjs ─→ src/generated/content.json ─→ src/ (React)
content/**/*.md      ┘
```

构建脚本会解析每份定义文档里的 `## 字段定义`、`## 子结构定义` 与 `## 关联`，
把字段表、枚举表、关系边、主线阶段一起编译出来。
**图、清单、详情面板都是从这些表生成的**——没有第二份手写的数据。

关系全部外置在 `## 关联` 表里，字段表只描述制品自己的数据——
所以字段表里不会出现 `module_id`、`xxx_ids` 这类指向别的制品的字段。

它同时也是一道闸门：下面这些不一致会让构建直接失败。

- 每种制品恰好属于一个主线阶段
- 每条主线交接都是真实存在的关系边
- 横切阶段只准备、不产出
- 每份定义文档都存在，且能解析出字段表
- 文档内部的相对链接都指向存在的文件

## 前端的五个视图

| 视图 | 路由 | 内容 |
|------|------|------|
| 概览 | `#/` | 愿景、域模型、制品总览（带用途）、主线表格 |
| 体系图 | `#/graph` | 35 种制品 + 83 条关系的力导向图，可筛选、可搜索、可聚焦 |
| 开发主线 | `#/mainline` | 10 个纵向阶段 + 3 个横切阶段，39 次交接 |
| 制品 | `#/artifacts` | 制品清单 → 单品详情（字段 / 枚举 / 子结构 / 关系 / 全文） |
| 文档 | `#/docs` | 全部设计文档，带目录 |

## 加一份新制品

1. 在 `content/<domain>/<artifact>.md` 写定义文档——
   必须有 `## 目标`、`## 字段定义`、`## 关联` 三节。
2. 在 `data/artifacts.yaml` 的 `artifacts:` 里登记它：
   类型键、ID 前缀、ID 模式、域、定义文件路径、用途。
3. 如果它属于主线，在 `mainline:` 里把它放进某个阶段的 `produces` 或 `prepares`，
   并写清交接边（必须是关系表里真实存在的边）。
4. `npm run build` —— 不一致会在这里报错。

## 加一个视图

`src/components/` 下每个视图是一个组件，数据来自 `src/data.ts`
（它只是 `src/generated/content.json` 的类型化外壳）。
路由在 `src/router.ts` 里定义。

# 项目工具

## 环境准备

项目使用 [uv](https://docs.astral.sh/uv/) 管理依赖：

```bash
uv sync --all-groups
```

## 代码检查

CI（`.github/workflows/check.yaml`）执行以下三步，本地可用同样的命令验证：

```bash
uv run ruff check --ignore-noqa   # 静态检查
uv run pytest                     # 单元测试
uv run src/checker/main.py        # Markdown 链接检查
```

> 项目未打包为发行版，因此 `src` 包不是通过安装引入的。`pyproject.toml` 中已配置
> `[tool.pytest.ini_options] pythonpath = ["."]`，让 pytest 能从仓库根目录导入 `src`。

## 制品图谱网页

`src/viz/` 把制品体系渲染成一个自包含的交互网页（`docs/artifact-graph.html`）。

### 生成

```bash
uv run python -m src.viz.build                          # 体系图（默认写到 docs/）
uv run python -m src.viz.build --db crispspec.db        # 额外包含制品实例图
```

页面数据全部来自仓库自身：

| 来源 | 提供的内容 |
|------|-----------|
| `artifacts.yaml` | 35 种制品类型、所属域、ID 前缀、实现状态、Stage、**开发主线阶段** |
| `src/<domain>/*.md` 的 `## 关联` 表 | 关系边（边类型、出入方向） |
| `src/<domain>/*.md` 的 `## 字段定义` 表 | 字段、约束、枚举、语义位置 |
| `src/requirement/common.py` | Business Concept 的七个语义映射 |
| SQLite 数据库（可选） | 制品实例与实例之间的引用 |

### 开发主线

`artifacts.yaml` 的 `mainline:` 段声明开发的纵向顺序：10 个主线阶段 + 3 个横切阶段。
每个阶段分 `produces`（这一步产出的）与 `prepares`（可提前准备、不由这一步产出的）——
主线不声称自己产出所有制品，业务概念、错误目录、仓库、环境、权限都可以早就定义好。

三条约束都由 `tests/registry/test_artifacts.py` 保证：

- 每种制品恰好属于一个阶段的 `produces` 或 `prepares`
- 每条 `handoff` 都必须是一条真实存在的关系边
- 横切阶段只 `prepares`、不 `produces`

改动了制品关系却忘了更新主线，测试会报红。

### 约定

- **页面是生成物，不是手写文件**。改了制品定义后必须重新生成，
  `tests/viz/` 里有测试锁定 `docs/artifact-graph.html` 与源文档不漂移。
- **页面自包含**：不引用 CDN、不联网，双击即可打开。
- 数据库以**只读**方式打开，可视化器不会修改被查看的库。


## Markdown 链接检查器

项目包含一个 Markdown 链接检查器，用于验证文档中的链接是否正确。

### 使用方法

```bash
uv run src/checker/main.py
```

### 功能

- 递归检查项目中所有 `.md` 文件
- 验证本地文件链接是否存在
- 跳过 HTTP/HTTPS 链接（不进行网络请求）
- 跳过锚点链接
- 报告指向项目根目录之外的链接
- 生成详细的错误报告

### 输出示例

```
检查了 37 个markdown文件
发现 0 个错误

✓ 所有链接检查通过!
```

如果发现错误，会显示详细的文件路径、链接内容和错误信息。
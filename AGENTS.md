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
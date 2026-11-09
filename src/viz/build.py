"""Generate the artifact graph page.

Usage::

    uv run python -m src.viz.build
    uv run python -m src.viz.build --db crispspec.db --output docs/artifact-graph.html

The generated page is written to ``docs/artifact-graph.html`` by default.
"""

from __future__ import annotations

import argparse
import contextlib
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from .catalog import PROJECT_ROOT, load_catalog
from .graph import build_payload
from .render import render_page

if TYPE_CHECKING:
    from .catalog import Catalog

DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "artifact-graph.html"


def _base_path(output: Path) -> str:
    """Return the relative prefix from *output* to the project root."""
    output_dir = output.resolve().parent
    try:
        relative = output_dir.relative_to(PROJECT_ROOT)
    except ValueError:
        return ""
    depth = len(relative.parts)
    return "../" * depth


def render_for(output: Path, catalog: Catalog, db_path: Path | None = None) -> str:
    """Render the page that belongs at *output*.

    The output path matters: the links from the page back to the
    definition documents are relative to it.

    Args:
        output: Where the page will be written.
        catalog: The artifact catalog.
        db_path: Optional SQLite database holding artifact instances.

    Returns:
        The rendered HTML document.

    """
    payload = build_payload(catalog, db_path)
    payload["basePath"] = _base_path(output)
    return render_page(payload)


def build(output: Path = DEFAULT_OUTPUT, db_path: Path | None = None) -> str:
    """Build the page and write it to *output*.

    Args:
        output: Where to write the HTML page.
        db_path: Optional SQLite database holding artifact instances.

    Returns:
        The rendered HTML document.

    """
    catalog = load_catalog()
    html = render_for(output, catalog, db_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return html


def main(argv: list[str] | None = None) -> int:
    """Run the generator.

    Args:
        argv: Command line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        The process exit code.

    """
    parser = argparse.ArgumentParser(description="生成制品图谱网页")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="输出文件路径（默认 docs/artifact-graph.html）",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="可选 -- 包含制品实例的 SQLite 数据库（只读打开）",
    )
    args = parser.parse_args(argv)

    catalog = load_catalog()
    html = render_for(args.output, catalog, args.db)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")

    sys.stdout.write(f"已写入 {args.output}\n")
    return 0


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        sys.exit(main())

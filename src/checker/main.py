#!/usr/bin/env python3
"""Markdown link checker.

Check all markdown files in a project for broken links.
"""

from __future__ import annotations

import argparse
import contextlib
import re
import sys
from pathlib import Path


class MarkdownLinkChecker:
    """Checker for markdown file links."""

    def __init__(self, root_dir: str = ".") -> None:
        """Initialize the checker with a root directory."""
        self.root_dir = Path(root_dir).resolve()
        self.errors: list[tuple[str, str, str]] = []
        self.checked_files: set[str] = set()

    def find_markdown_files(self) -> list[Path]:
        """Find all markdown files recursively."""
        return [f for f in self.root_dir.rglob("*.md") if f.is_file()]

    def extract_links(self, content: str) -> list[str]:
        """Extract all links from markdown content."""
        pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        matches = re.findall(pattern, content)
        return [url for text, url in matches]

    def resolve_relative_link(self, base_file: Path, link: str) -> Path:
        """Resolve a relative link from a base file."""
        link_without_anchor = link.split("#", maxsplit=1)[0]

        if not link_without_anchor:
            return base_file.parent

        resolved_path = (base_file.parent / link_without_anchor).resolve()

        with contextlib.suppress(ValueError):
            resolved_path.relative_to(self.root_dir)
        return resolved_path

    def check_local_link(self, base_file: Path, link: str) -> tuple[bool, str]:
        """Check if a local link is valid."""
        if link.startswith(("http://", "https://", "mailto:", "ftp://")):
            return True, "HTTP link (skipped)"

        if link.startswith("#"):
            return True, "Anchor link (skipped)"

        resolved_path = self.resolve_relative_link(base_file, link)

        if resolved_path.exists():
            return True, "OK"
        return False, f"File not found: {resolved_path}"

    def check_file(self, file_path: Path) -> None:
        """Check a single file for broken links."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError as e:
            self.errors.append((str(file_path), "", f"Failed to read file: {e}"))
            return

        links = self.extract_links(content)

        for link in links:
            is_valid, message = self.check_local_link(file_path, link)
            if not is_valid:
                self.errors.append((str(file_path), link, message))

        self.checked_files.add(str(file_path))

    def check_all(self) -> None:
        """Check all markdown files in the root directory."""
        for file_path in self.find_markdown_files():
            self.check_file(file_path)

    def report(self) -> bool:
        """Generate and print the check report."""
        sys.stdout.write(f"检查了 {len(self.checked_files)} 个markdown文件\n")
        sys.stdout.write(f"发现 {len(self.errors)} 个错误\n\n")

        if self.errors:
            sys.stdout.write("错误详情:\n")
            sys.stdout.write("-" * 80 + "\n")

            for file_path, link, error in self.errors:
                sys.stdout.write(f"文件: {file_path}\n")
                if link:
                    sys.stdout.write(f"链接: [{link}]\n")
                sys.stdout.write(f"错误: {error}\n")
                sys.stdout.write("-" * 80 + "\n")

            return False
        sys.stdout.write("✓ 所有链接检查通过!\n")
        return True


def main() -> None:
    """Entry point for the markdown link checker."""
    parser = argparse.ArgumentParser(
        description="检查markdown文件中的链接",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="要检查的目录（默认为当前目录）",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="显示详细信息",
    )

    args = parser.parse_args()

    checker = MarkdownLinkChecker(args.directory)
    checker.check_all()

    if args.verbose:
        sys.stdout.write("\n检查的文件:\n")
        for file in sorted(checker.checked_files):
            sys.stdout.write(f"  {file}\n")
        sys.stdout.write("\n")

    success = checker.report()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

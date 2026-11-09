"""Repository-wide hygiene checks.

These guard against a class of problem that only shows up on CI: a file
whose shebang and executable bit disagree.  Ruff's EXE001 rule rejects a
shebang on a non-executable file, but on Windows the executable bit does not
exist, so the failure only ever appears on the Linux runner.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def python_files() -> list[Path]:
    """Return every Python file tracked in the project."""
    return sorted(
        p
        for p in PROJECT_ROOT.rglob("*.py")
        if ".venv" not in p.parts and "__pycache__" not in p.parts
    )


@pytest.mark.parametrize(
    "path",
    [p for p in python_files() if p.name == "__init__.py"],
    ids=lambda p: p.relative_to(PROJECT_ROOT).as_posix(),
)
def test_package_inits_have_no_shebang(path: Path) -> None:
    """A package __init__.py is imported, never run -- no shebang.

    EXE001 flags a shebang on a file that is not executable.  Package
    initialisers should not carry one at all.
    """
    first_line = path.read_text(encoding="utf-8").splitlines()[:1]
    assert not (first_line and first_line[0].startswith("#!")), path


@pytest.mark.parametrize(
    "path",
    [p for p in python_files() if p.read_text(encoding="utf-8").startswith("#!")],
    ids=lambda p: p.relative_to(PROJECT_ROOT).as_posix(),
)
def test_shebang_files_are_executable(path: Path) -> None:
    """A file with a shebang is executable.

    On Windows every file looks executable, so this assertion is only
    meaningful on the Linux runner -- which is exactly where it matters.
    """
    assert os.access(path, os.X_OK), path

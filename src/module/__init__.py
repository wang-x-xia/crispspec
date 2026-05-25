#!/usr/bin/env python3
"""Module artifact management."""

from __future__ import annotations

from .module import (
    CodeRef,
    Dependency,
    ModuleDef,
    ModuleManager,
    ModuleType,
    Protocol,
    parse_code_ref,
    parse_dependency,
    parse_module,
    validate_module,
)

__all__ = [
    "CodeRef",
    "Dependency",
    "ModuleDef",
    "ModuleManager",
    "ModuleType",
    "Protocol",
    "parse_code_ref",
    "parse_dependency",
    "parse_module",
    "validate_module",
]

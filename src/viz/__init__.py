"""Artifact graph visualiser.

Turns the artifact system described in ``concepts.md`` -- and the artifact
instances stored in a database -- into a single interactive web page.

The package has four layers:

``catalog``
    Reads ``artifacts.yaml`` (the machine-readable registry of artifact
    types) into typed data.
``relations``
    Parses the ``## 关联`` tables of every artifact definition document.
    Those tables are the single source of truth for the edges of the graph,
    so the visualiser never keeps a second, hand-maintained edge list.
``graph``
    Assembles nodes and edges into a JSON-serialisable payload.
``render``
    Writes the payload into a self-contained HTML page.
"""

from __future__ import annotations

__all__ = ["build_payload", "render_page"]

from .graph import build_payload
from .render import render_page

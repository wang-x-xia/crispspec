"""Rendering of the visualiser page.

The page is a single, self-contained HTML file: the graph data is embedded
as JSON, the layout engine and the interactions are plain JavaScript.  No
network access, no CDN, no build step -- open the file and it works.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "artifact-graph.html"

#: Marker replaced by the graph payload.
PLACEHOLDER = "__CRISP_SPEC_DATA__"


def render_page(payload: dict[str, Any]) -> str:
    """Render the visualiser page for *payload*.

    Args:
        payload: The graph payload, as built by :func:`src.viz.graph.build_payload`.

    Returns:
        The complete HTML document.

    Raises:
        ValueError: If the template does not contain the placeholder.

    """
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        msg = f"Template placeholder '{PLACEHOLDER}' not found in {TEMPLATE_PATH}"
        raise ValueError(msg)
    data = json.dumps(payload, ensure_ascii=False, indent=2)
    return template.replace(PLACEHOLDER, data)

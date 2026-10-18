"""
LogPulse CLI - SSG Template Renderer
Handles Jinja2 environment configuration, custom filters, and template evaluation.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    HAS_JINJA = True
except ImportError:
    HAS_JINJA = False

from .models import Document
from .tree import DocTree


def status_badge_filter(status: str) -> str:
    """Renders a colorful status badge HTML snippet."""
    status_lower = (status or "active").lower()
    color_map = {
        "active": "badge-success",
        "production": "badge-success",
        "draft": "badge-warning",
        "review": "badge-info",
        "deprecated": "badge-danger",
        "critical": "badge-danger",
    }
    css_class = color_map.get(status_lower, "badge-secondary")
    return f'<span class="badge {css_class}">{status.upper()}</span>'


def date_format_filter(val: str) -> str:
    """Formats date string nicely."""
    if not val:
        return datetime.date.today().strftime("%B %d, %Y")
    return val


class TemplateRenderer:
    """OOP renderer for documentation and audit portals."""

    def __init__(self, templates_dir: Path):
        self.templates_dir = Path(templates_dir)
        if HAS_JINJA:
            self.env = Environment(
                loader=FileSystemLoader(str(self.templates_dir)),
                autoescape=select_autoescape(["html", "xml"]),
            )
            self.env.filters["status_badge"] = status_badge_filter
            self.env.filters["date_format"] = date_format_filter
        else:
            self.env = None

    def render_document(self, document: Document, tree: DocTree) -> str:
        """Renders an individual SOP/Runbook document page."""
        nav_tree = tree.to_nav_tree(current_slug=document.slug)
        context = {
            "doc": document,
            "meta": document.metadata,
            "nav_tree": nav_tree,
            "breadcrumbs": document.breadcrumbs,
            "headings": document.headings,
            "prev_doc": document.prev_doc,
            "next_doc": document.next_doc,
            "total_docs": tree.total_documents(),
            "year": datetime.date.today().year,
        }

        if self.env:
            template = self.env.get_template("ssg/doc.html")
            return template.render(**context)
        else:
            return self._fallback_render_doc(context)

    def render_sitemap(self, tree: DocTree) -> str:
        """Renders comprehensive tree-based sitemap page."""
        nav_tree = tree.to_nav_tree()
        docs = tree.get_document_sequence()
        context = {
            "nav_tree": nav_tree,
            "docs": docs,
            "total_docs": tree.total_documents(),
            "total_categories": tree.total_categories(),
            "year": datetime.date.today().year,
        }

        if self.env:
            template = self.env.get_template("ssg/sitemap.html")
            return template.render(**context)
        else:
            return self._fallback_render_sitemap(context)

    def _fallback_render_doc(self, ctx: Dict[str, Any]) -> str:
        doc: Document = ctx["doc"]
        return f"""<!DOCTYPE html>
<html>
<head><title>{doc.metadata.title} - LogPulse</title></head>
<body>
<h1>{doc.metadata.title}</h1>
<div>{doc.html_content}</div>
</body>
</html>"""

    def _fallback_render_sitemap(self, ctx: Dict[str, Any]) -> str:
        docs = ctx["docs"]
        doc_links = "".join(f'<li><a href="{d.output_filename}">{d.metadata.title}</a></li>' for d in docs)
        return f"""<!DOCTYPE html>
<html>
<head><title>Sitemap - LogPulse</title></head>
<body>
<h1>Documentation Sitemap</h1>
<ul>{doc_links}</ul>
</body>
</html>"""

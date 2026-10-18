"""
LogPulse CLI - Markdown & Frontmatter Parser
Converts markdown SOP documents into structured HTML with deep-linking anchors,
TOC extraction, callout alerts, and code highlights.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .models import Document, DocumentMetadata, HeadingItem

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    from markdown_it import MarkdownIt
    HAS_MARKDOWN_IT = True
except ImportError:
    HAS_MARKDOWN_IT = False


def slugify(text: str) -> str:
    """Converts a title into a URL/anchor friendly slug."""
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


class MarkdownParser:
    """
    Parser that extracts YAML frontmatter and transforms Markdown into HTML.
    """

    def __init__(self):
        if HAS_MARKDOWN_IT:
            self.md_engine = MarkdownIt("commonmark", {"html": True, "breaks": True}).enable(["table"])
        else:
            self.md_engine = None

    def parse_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """
        Splits frontmatter delimited by `---` from markdown body.
        Supports both PyYAML and a lightweight native YAML parser.
        """
        if not content.startswith("---"):
            return {}, content

        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(pattern, content, re.DOTALL)
        if not match:
            return {}, content

        raw_yaml = match.group(1)
        body = match.group(2)

        if HAS_YAML:
            try:
                parsed = yaml.safe_load(raw_yaml)
                if isinstance(parsed, dict):
                    return parsed, body
            except Exception:
                pass

        # Lightweight fallback native parser for simple key: value
        result: Dict[str, Any] = {}
        for line in raw_yaml.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if v.startswith("[") and v.endswith("]"):
                    items = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
                    result[k] = items
                elif v.isdigit():
                    result[k] = int(v)
                else:
                    result[k] = v

        return result, body

    def extract_headings_and_inject_anchors(self, html: str) -> Tuple[str, List[HeadingItem]]:
        """
        Extracts H2 and H3 headings for the Table of Contents,
        and ensures all headers have an `id` attribute for direct anchor linking.
        """
        headings: List[HeadingItem] = []
        slug_counts: Dict[str, int] = {}

        def _replace_header(match: re.Match) -> str:
            tag = match.group(1).lower()
            level = int(tag[1])
            existing_attrs = match.group(2) or ""
            text = match.group(3).strip()
            clean_title = re.sub(r"<[^>]+>", "", text).strip()

            base_slug = slugify(clean_title) or f"heading-{len(headings) + 1}"
            slug_counts[base_slug] = slug_counts.get(base_slug, 0) + 1
            slug = base_slug if slug_counts[base_slug] == 1 else f"{base_slug}-{slug_counts[base_slug]}"

            if level in (2, 3, 4):
                headings.append(HeadingItem(level=level, title=clean_title, slug=slug))

            return f'<{tag} id="{slug}"{existing_attrs} class="anchor-heading"><a href="#{slug}" class="heading-anchor">#</a> {text}</{tag}>'

        pattern = r"<(h[1-6])([^>]*)>(.*?)</\1>"
        modified_html = re.sub(pattern, _replace_header, html, flags=re.IGNORECASE | re.DOTALL)
        return modified_html, headings

    def transform_callouts(self, html: str) -> str:
        """
        Converts GitHub/GitLab style callouts:
        > [!NOTE] -> <div class="callout callout-note">...
        > [!WARNING] -> <div class="callout callout-warning">...
        > [!IMPORTANT] -> <div class="callout callout-important">...
        > [!TIP] -> <div class="callout callout-tip">...
        """
        callout_types = {
            "NOTE": ("callout-note", "ℹ️", "Note"),
            "TIP": ("callout-tip", "💡", "Tip"),
            "IMPORTANT": ("callout-important", "⚡", "Important"),
            "WARNING": ("callout-warning", "⚠️", "Warning"),
            "CAUTION": ("callout-caution", "🛑", "Caution"),
        }

        for c_type, (css_class, icon, label) in callout_types.items():
            pattern = re.compile(
                r"<blockquote>\s*<p>\[!" + c_type + r"\]\s*(.*?)</p>\s*</blockquote>",
                re.IGNORECASE | re.DOTALL,
            )

            def _repl(m: re.Match) -> str:
                body = m.group(1).strip()
                return (
                    f'<div class="callout {css_class}">'
                    f'<div class="callout-header"><span class="callout-icon">{icon}</span> <strong>{label}</strong></div>'
                    f'<div class="callout-body"><p>{body}</p></div>'
                    f'</div>'
                )

            html = pattern.sub(_repl, html)

        return html

    def render_markdown(self, markdown_text: str) -> str:
        """Transforms raw markdown body into styled HTML."""
        if self.md_engine:
            raw_html = self.md_engine.render(markdown_text)
        else:
            raw_html = self._native_simple_markdown(markdown_text)

        html_with_callouts = self.transform_callouts(raw_html)
        html_with_anchors, _ = self.extract_headings_and_inject_anchors(html_with_callouts)
        return html_with_anchors

    def _native_simple_markdown(self, text: str) -> str:
        """Fallback markdown converter when external libraries are not present."""
        lines = text.splitlines()
        html_out = []
        in_code_block = False
        code_lang = ""
        code_lines = []

        for line in lines:
            if line.startswith("```"):
                if in_code_block:
                    in_code_block = False
                    escaped_code = (
                        "\n".join(code_lines)
                        .replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                    )
                    html_out.append(f'<pre><code class="language-{code_lang}">{escaped_code}</code></pre>')
                    code_lines = []
                else:
                    in_code_block = True
                    code_lang = line[3:].strip()
                continue

            if in_code_block:
                code_lines.append(line)
                continue

            # Headers
            if line.startswith("### "):
                html_out.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("## "):
                html_out.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("# "):
                html_out.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("> "):
                html_out.append(f"<blockquote><p>{line[2:]}</p></blockquote>")
            elif line.startswith("- ") or line.startswith("* "):
                html_out.append(f"<li>{line[2:]}</li>")
            elif line.strip() == "":
                html_out.append("<br/>")
            else:
                html_out.append(f"<p>{line}</p>")

        return "\n".join(html_out)

    def parse_file(self, file_path: Path, docs_root: Path) -> Document:
        """Parses a markdown file into a full Document instance."""
        content = file_path.read_text(encoding="utf-8")
        raw_meta, body = self.parse_frontmatter(content)

        rel_path = file_path.relative_to(docs_root)
        slug = str(rel_path.with_suffix("")).replace("\\", "/")

        # Infer title if not explicitly in metadata
        if "title" not in raw_meta:
            title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
            if title_match:
                raw_meta["title"] = title_match.group(1).strip()
            else:
                raw_meta["title"] = file_path.stem.replace("-", " ").replace("_", " ").title()

        metadata = DocumentMetadata.from_dict(raw_meta)
        html_content = self.render_markdown(body)
        _, headings = self.extract_headings_and_inject_anchors(html_content)

        return Document(
            source_path=file_path,
            relative_path=rel_path,
            slug=slug,
            metadata=metadata,
            raw_markdown=body,
            html_content=html_content,
            headings=headings,
        )

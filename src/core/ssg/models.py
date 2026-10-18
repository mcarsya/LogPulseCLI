from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DocumentMetadata:
    title: str = "Untitled Document"
    author: str = "Internal Engineering"
    version: str = "1.0.0"
    category: str = "General"
    tags: List[str] = field(default_factory=list)
    last_updated: str = ""
    status: str = "Active"
    summary: str = ""
    order: int = 100

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DocumentMetadata:
        tags = data.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        return cls(
            title=str(data.get("title", "Untitled Document")),
            author=str(data.get("author", "Internal Engineering")),
            version=str(data.get("version", "1.0.0")),
            category=str(data.get("category", "General")),
            tags=tags,
            last_updated=str(data.get("last_updated", "")),
            status=str(data.get("status", "Active")),
            summary=str(data.get("summary", "")),
            order=int(data.get("order", 100)),
        )


@dataclass
class HeadingItem:
    level: int
    title: str
    slug: str


@dataclass
class BreadcrumbItem:
    title: str
    url: str
    is_current: bool = False


@dataclass
class Document:
    source_path: Path
    relative_path: Path
    slug: str
    metadata: DocumentMetadata
    raw_markdown: str
    html_content: str = ""
    headings: List[HeadingItem] = field(default_factory=list)
    breadcrumbs: List[BreadcrumbItem] = field(default_factory=list)
    prev_doc: Optional[Document] = None
    next_doc: Optional[Document] = None

    @property
    def output_filename(self) -> str:
        if self.slug in ("index", "home", ""):
            return "index.html"
        return f"{self.slug}.html"

    @property
    def reading_time_minutes(self) -> int:
        words = len(self.raw_markdown.split())
        return max(1, round(words / 200))

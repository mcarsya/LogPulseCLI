"""
LogPulse CLI - Static Site Generator (SSG Orchestrator)
Orchestrates document parsing, Tree/Graph synthesis, breadcrumb resolution,
and output artifact generation.
"""

from __future__ import annotations

import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .models import Document
from .parser import MarkdownParser
from .renderer import TemplateRenderer
from .tree import DocTree


@dataclass
class BuildResult:
    total_documents: int
    total_categories: int
    output_directory: Path
    elapsed_seconds: float
    generated_files: List[Path]


class StaticSiteGenerator:
    """
    Enterprise-scale Static Site Generator using OOP architecture.
    """

    def __init__(
        self,
        docs_dir: str | Path,
        output_dir: str | Path,
        templates_dir: Optional[str | Path] = None,
    ):
        self.docs_dir = Path(docs_dir).resolve()
        self.output_dir = Path(output_dir).resolve()

        if templates_dir is None:
            self.templates_dir = Path(__file__).resolve().parent.parent.parent.parent / "templates"
        else:
            self.templates_dir = Path(templates_dir).resolve()

        self.parser = MarkdownParser()
        self.renderer = TemplateRenderer(self.templates_dir)
        self.tree = DocTree(root_title="LogPulse Enterprise Portal")

    def build(self) -> BuildResult:
        """Executes complete SSG pipeline."""
        start_time = time.perf_counter()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Discover all markdown files
        md_files = sorted(list(self.docs_dir.rglob("*.md")))
        if not md_files:
            raise FileNotFoundError(f"No markdown documents found in {self.docs_dir}")

        documents: List[Document] = []

        # 2. Parse documents and populate N-ary DocTree
        for file_path in md_files:
            doc = self.parser.parse_file(file_path, self.docs_dir)
            documents.append(doc)
            self.tree.insert(doc.relative_path, doc)

        # 3. Apply Tree Algorithms: Link next/prev chain & build breadcrumbs
        self.tree.link_sequential_documents()
        for doc in documents:
            node = self.tree.find_by_slug(doc.slug)
            if node:
                doc.breadcrumbs = self.tree.build_breadcrumbs(node)

        # 4. Render Document HTML Pages
        generated_files: List[Path] = []
        for doc in documents:
            html = self.renderer.render_document(doc, self.tree)
            target_file = self.output_dir / doc.output_filename
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(html, encoding="utf-8")
            generated_files.append(target_file)

        # 5. Render Tree-based Sitemap Page
        sitemap_html = self.renderer.render_sitemap(self.tree)
        sitemap_file = self.output_dir / "sitemap.html"
        sitemap_file.write_text(sitemap_html, encoding="utf-8")
        generated_files.append(sitemap_file)

        # 6. Copy static styling & scripts
        assets_src = self.templates_dir / "assets"
        assets_dst = self.output_dir / "assets"
        if assets_src.exists():
            if assets_dst.exists():
                shutil.rmtree(assets_dst)
            shutil.copytree(assets_src, assets_dst)

        elapsed = time.perf_counter() - start_time
        return BuildResult(
            total_documents=len(documents),
            total_categories=self.tree.total_categories(),
            output_directory=self.output_dir,
            elapsed_seconds=elapsed,
            generated_files=generated_files,
        )

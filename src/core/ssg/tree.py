from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Generator, List, Optional, Tuple, Dict, Any

from .models import BreadcrumbItem, Document


class DocTreeNode:
    def __init__(
        self,
        name: str,
        title: str,
        rel_path: str,
        is_directory: bool = False,
        document: Optional[Document] = None,
        parent: Optional[DocTreeNode] = None,
        order: int = 100,
    ):
        self.name: str = name
        self.title: str = title
        self.rel_path: str = rel_path
        self.is_directory: bool = is_directory
        self.document: Optional[Document] = document
        self.parent: Optional[DocTreeNode] = parent
        self.children: Dict[str, DocTreeNode] = {}
        self.order: int = order

    @property
    def is_root(self) -> bool:
        return self.parent is None

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0

    @property
    def depth(self) -> int:
        d = 0
        curr = self.parent
        while curr:
            d += 1
            curr = curr.parent
        return d

    def add_child(self, child: DocTreeNode) -> None:
        child.parent = self
        self.children[child.name] = child

    def get_sorted_children(self) -> List[DocTreeNode]:
        return sorted(
            self.children.values(),
            key=lambda n: (n.order, 0 if n.is_directory else 1, n.title.lower())
        )

    def get_url(self, base_prefix: str = "") -> str:
        if self.document:
            filename = self.document.output_filename
            if base_prefix:
                return f"{base_prefix}/{filename}".replace("//", "/")
            return filename
        return "#"

    def __repr__(self) -> str:
        kind = "DIR" if self.is_directory else "DOC"
        return f"<DocTreeNode [{kind}] '{self.name}' title='{self.title}'>"


class DocTree:
    def __init__(self, root_title: str = "Knowledge Base"):
        self.root = DocTreeNode(
            name="root",
            title=root_title,
            rel_path="",
            is_directory=True,
            order=0,
        )
        self._doc_map: Dict[str, DocTreeNode] = {}

    def insert(self, relative_path: Path, document: Document) -> DocTreeNode:
        parts = relative_path.parts
        curr = self.root

        accumulated_path = []
        for dir_name in parts[:-1]:
            accumulated_path.append(dir_name)
            rel_dir_str = "/".join(accumulated_path)
            if dir_name not in curr.children:
                dir_title = dir_name.replace("-", " ").replace("_", " ").title()
                dir_node = DocTreeNode(
                    name=dir_name,
                    title=dir_title,
                    rel_path=rel_dir_str,
                    is_directory=True,
                    parent=curr,
                    order=50,
                )
                curr.add_child(dir_node)
            curr = curr.children[dir_name]

        file_name = parts[-1]
        doc_node = DocTreeNode(
            name=file_name,
            title=document.metadata.title,
            rel_path=str(relative_path).replace("\\", "/"),
            is_directory=False,
            document=document,
            parent=curr,
            order=document.metadata.order,
        )
        curr.add_child(doc_node)
        self._doc_map[document.slug] = doc_node
        return doc_node

    def dfs_pre_order(
        self, start_node: Optional[DocTreeNode] = None
    ) -> Generator[DocTreeNode, None, None]:
        node = start_node or self.root
        yield node
        for child in node.get_sorted_children():
            yield from self.dfs_pre_order(child)

    def dfs_post_order(
        self, start_node: Optional[DocTreeNode] = None
    ) -> Generator[DocTreeNode, None, None]:
        node = start_node or self.root
        for child in node.get_sorted_children():
            yield from self.dfs_post_order(child)
        yield node

    def bfs_level_order(self) -> Generator[Tuple[int, DocTreeNode], None, None]:
        queue: deque[Tuple[int, DocTreeNode]] = deque([(0, self.root)])
        while queue:
            level, current = queue.popleft()
            yield level, current
            for child in current.get_sorted_children():
                queue.append((level + 1, child))

    def get_document_sequence(self) -> List[Document]:
        docs: List[Document] = []
        for node in self.dfs_pre_order():
            if not node.is_directory and node.document:
                docs.append(node.document)
        return docs

    def link_sequential_documents(self) -> None:
        docs = self.get_document_sequence()
        for i, doc in enumerate(docs):
            doc.prev_doc = docs[i - 1] if i > 0 else None
            doc.next_doc = docs[i + 1] if i < len(docs) - 1 else None

    def build_breadcrumbs(self, node: DocTreeNode) -> List[BreadcrumbItem]:
        items: List[BreadcrumbItem] = []
        curr: Optional[DocTreeNode] = node

        while curr is not None:
            if curr.is_root:
                items.append(BreadcrumbItem(title="Home", url="index.html", is_current=(curr == node)))
            elif curr.document:
                items.append(BreadcrumbItem(
                    title=curr.title,
                    url=curr.document.output_filename,
                    is_current=(curr == node)
                ))
            else:
                items.append(BreadcrumbItem(
                    title=curr.title,
                    url="#",
                    is_current=(curr == node)
                ))
            curr = curr.parent

        items.reverse()
        return items

    def to_nav_tree(self, current_slug: str = "") -> List[Dict[str, Any]]:
        def _node_to_dict(node: DocTreeNode) -> Dict[str, Any]:
            is_active = (node.document and node.document.slug == current_slug)
            return {
                "name": node.name,
                "title": node.title,
                "is_directory": node.is_directory,
                "url": node.get_url(),
                "is_active": is_active,
                "depth": node.depth,
                "children": [_node_to_dict(c) for c in node.get_sorted_children()],
            }

        return [_node_to_dict(child) for child in self.root.get_sorted_children()]

    def find_by_slug(self, slug: str) -> Optional[DocTreeNode]:
        return self._doc_map.get(slug)

    def total_documents(self) -> int:
        return len(self._doc_map)

    def total_categories(self) -> int:
        count = 0
        for node in self.dfs_pre_order():
            if node.is_directory and not node.is_root:
                count += 1
        return count

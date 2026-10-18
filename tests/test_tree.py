import unittest
from pathlib import Path
from src.core.ssg.models import Document, DocumentMetadata
from src.core.ssg.tree import DocTree, DocTreeNode


class TestDocTree(unittest.TestCase):
    def setUp(self):
        self.tree = DocTree(root_title="Enterprise Test KB")
        self.doc1 = Document(
            source_path=Path("docs/devops/k8s.md"),
            relative_path=Path("devops/k8s.md"),
            slug="devops/k8s",
            metadata=DocumentMetadata(title="Kubernetes SOP", order=10),
            raw_markdown="# Kubernetes SOP",
        )
        self.doc2 = Document(
            source_path=Path("docs/database/postgres.md"),
            relative_path=Path("database/postgres.md"),
            slug="database/postgres",
            metadata=DocumentMetadata(title="Postgres SOP", order=20),
            raw_markdown="# Postgres SOP",
        )
        self.doc3 = Document(
            source_path=Path("docs/index.md"),
            relative_path=Path("index.md"),
            slug="index",
            metadata=DocumentMetadata(title="Home Portal", order=1),
            raw_markdown="# Home",
        )

    def test_tree_insertion_and_directory_synthesis(self):
        node = self.tree.insert(self.doc1.relative_path, self.doc1)
        self.assertEqual(node.title, "Kubernetes SOP")
        self.assertEqual(node.depth, 2)
        self.assertIn("devops", self.tree.root.children)
        self.assertTrue(self.tree.root.children["devops"].is_directory)

    def test_dfs_pre_order_traversal(self):
        self.tree.insert(self.doc3.relative_path, self.doc3)
        self.tree.insert(self.doc1.relative_path, self.doc1)
        self.tree.insert(self.doc2.relative_path, self.doc2)

        visited_names = [n.name for n in self.tree.dfs_pre_order()]
        self.assertEqual(visited_names[0], "root")
        self.assertIn("index.md", visited_names)
        self.assertIn("k8s.md", visited_names)
        self.assertIn("postgres.md", visited_names)

    def test_bfs_level_order_traversal(self):
        self.tree.insert(self.doc1.relative_path, self.doc1)
        self.tree.insert(self.doc2.relative_path, self.doc2)

        levels = list(self.tree.bfs_level_order())
        root_level, root_node = levels[0]
        self.assertEqual(root_level, 0)
        self.assertEqual(root_node.name, "root")

        level1_names = [node.name for lvl, node in levels if lvl == 1]
        self.assertIn("devops", level1_names)
        self.assertIn("database", level1_names)

    def test_breadcrumbs_construction(self):
        node = self.tree.insert(self.doc1.relative_path, self.doc1)
        crumbs = self.tree.build_breadcrumbs(node)

        self.assertEqual(len(crumbs), 3)
        self.assertEqual(crumbs[0].title, "Home")
        self.assertEqual(crumbs[1].title, "Devops")
        self.assertEqual(crumbs[2].title, "Kubernetes SOP")
        self.assertTrue(crumbs[2].is_current)

    def test_link_sequential_documents(self):
        self.tree.insert(self.doc3.relative_path, self.doc3)
        self.tree.insert(self.doc1.relative_path, self.doc1)
        self.tree.insert(self.doc2.relative_path, self.doc2)
        self.tree.link_sequential_documents()

        docs = self.tree.get_document_sequence()
        self.assertEqual(len(docs), 3)
        self.assertIsNone(docs[0].prev_doc)
        self.assertEqual(docs[0].next_doc, docs[1])
        self.assertEqual(docs[1].prev_doc, docs[0])
        self.assertEqual(docs[1].next_doc, docs[2])
        self.assertIsNone(docs[2].next_doc)


if __name__ == "__main__":
    unittest.main()

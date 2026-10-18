"""
Unit Tests for Static Site Generator (SSG) Components.
"""

import unittest
from pathlib import Path
from src.core.ssg.parser import MarkdownParser, slugify
from src.core.ssg.models import DocumentMetadata


class TestSSGParser(unittest.TestCase):

    def setUp(self):
        self.parser = MarkdownParser()

    def test_slugify(self):
        self.assertEqual(slugify("Kubernetes Incident SOP!"), "kubernetes-incident-sop")
        self.assertEqual(slugify("CI/CD & Security Policy"), "cicd-security-policy")

    def test_frontmatter_extraction(self):
        raw = """---
title: "Redis Failover"
author: "SRE Team"
version: "1.0.0"
order: 5
tags: [redis, database]
---
# Main Content Here
This is a test.
"""
        meta_dict, body = self.parser.parse_frontmatter(raw)
        self.assertEqual(meta_dict["title"], "Redis Failover")
        self.assertEqual(meta_dict["author"], "SRE Team")
        self.assertEqual(meta_dict["order"], 5)
        self.assertIn("redis", meta_dict["tags"])
        self.assertIn("# Main Content Here", body)

    def test_callout_transformation(self):
        html_input = "<blockquote><p>[!NOTE]\nRemember to backup keys first.</p></blockquote>"
        transformed = self.parser.transform_callouts(html_input)
        self.assertIn('class="callout callout-note"', transformed)
        self.assertIn("Remember to backup keys first.", transformed)

    def test_heading_anchors_and_toc(self):
        raw_html = "<h2>Cluster Health</h2><p>text</p><h3>Recovery Steps</h3>"
        html_out, headings = self.parser.extract_headings_and_inject_anchors(raw_html)
        self.assertEqual(len(headings), 2)
        self.assertEqual(headings[0].slug, "cluster-health")
        self.assertEqual(headings[1].slug, "recovery-steps")
        self.assertIn('id="cluster-health"', html_out)


if __name__ == "__main__":
    unittest.main()

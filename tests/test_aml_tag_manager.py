"""
Unit Tests for AMLTagManager and dynamic AML grammar
"""

import unittest
import tempfile
import os
import shutil
from asma_core.aml_tag_manager import AMLTagManager, AMLTagDefinition
from asma_core.aml_parser import AMLParser, SectionNode, CustomTagNode, DirectiveNode


class TestAMLTagManager(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.data_file = os.path.join(self.test_dir, "aml_tags.json")
        AMLTagManager._instance = None
        self.mgr = AMLTagManager(data_file=self.data_file)

    def tearDown(self):
        AMLTagManager._instance = None
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_default_tags_initialized(self):
        tags = self.mgr.list_tags()
        self.assertGreaterEqual(len(tags), 20)

        tag_names = [t.tag for t in tags]
        # Check required tags from user request
        for req in ["title", "artist", "key", "tempo", "time", "intro", "verse", "chorus", "bridge", "solo", "outro", "guitar", "voice", "inline_chord", "harmonic_grid"]:
            self.assertIn(req, tag_names)

    def test_add_custom_section_and_parser_recognition(self):
        new_tag = AMLTagDefinition(
            tag="breakdown",
            category="section",
            display_name="Breakdown",
            syntax_pattern="{breakdown}",
            example="{breakdown: Solo Basso}",
            description="Sezione di breakdown ritmico"
        )
        self.mgr.add_tag(new_tag)
        self.assertIn("breakdown", self.mgr.get_known_sections())

        # Test AMLParser parses it as SectionNode
        doc = AMLParser.parse("{breakdown: Solo Basso}")
        self.assertEqual(len(doc.nodes), 1)
        self.assertIsInstance(doc.nodes[0], SectionNode)
        self.assertEqual(doc.nodes[0].section_name, "breakdown")
        self.assertEqual(doc.nodes[0].label, "Solo Basso")

    def test_add_instrumental_tag_and_parser_recognition(self):
        new_inst = AMLTagDefinition(
            tag="saxophone",
            category="instrumental_tag",
            display_name="Sassofono",
            syntax_pattern="{saxophone: Dettagli}",
            example="{saxophone: Solo Clarence}",
            description="Indicazioni per sax"
        )
        self.mgr.add_tag(new_inst)
        self.assertIn("saxophone", self.mgr.get_known_custom_tags())

        doc = AMLParser.parse("{saxophone: Solo Clarence}")
        self.assertEqual(len(doc.nodes), 1)
        self.assertIsInstance(doc.nodes[0], CustomTagNode)
        self.assertEqual(doc.nodes[0].tag_type, "saxophone")
        self.assertEqual(doc.nodes[0].content, "Solo Clarence")

    def test_update_tag(self):
        updated = self.mgr.update_tag(
            tag_name="guitar",
            display_name="Chitarre Soliste",
            syntax_pattern="{guitar: Guida}",
            example="{guitar: Solo Don Felder e Joe Walsh}",
            description="Indicazioni chitarristiche avanzate"
        )
        self.assertEqual(updated.display_name, "Chitarre Soliste")
        self.assertIn("Walsh", updated.example)

    def test_delete_tag_and_protection(self):
        # Cannot delete non-removable core tag
        with self.assertRaises(ValueError):
            self.mgr.delete_tag("title")

        # Can delete non-critical tag
        self.assertTrue(self.mgr.delete_tag("coda"))
        self.assertNotIn("coda", self.mgr.get_known_sections())

    def test_reset_defaults(self):
        self.mgr.delete_tag("intro")
        self.assertNotIn("intro", self.mgr.get_known_sections())
        restored = self.mgr.reset_to_defaults()
        self.assertIn("intro", [t.tag for t in restored])


if __name__ == "__main__":
    unittest.main()

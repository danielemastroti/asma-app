"""
Test Suite: Manual Engine Content & PDF Generation
Verifies chapters metadata, completeness status explanation, and PDF compilation.
"""

import unittest
from asma_core.manual_engine import ManualEngine


class TestManualEngineContent(unittest.TestCase):

    def test_chapters_metadata(self):
        chapters = ManualEngine.get_chapters_metadata()
        self.assertGreaterEqual(len(chapters), 16)
        
        # Check chapter 5
        ch5 = next(c for c in chapters if c["num"] == 5)
        self.assertIn("stati di completezza", ch5["desc"])
        self.assertIn("COMPLETO", ch5["desc"])
        
        # Check chapter 6
        ch6 = next(c for c in chapters if c["num"] == 6)
        self.assertIn("LRCLIB", ch6["desc"])
        self.assertIn("Medley", ch6["desc"])
        
        # Check chapter 7
        ch7 = next(c for c in chapters if c["num"] == 7)
        self.assertIn("inediti", ch7["desc"])

    def test_manual_markdown(self):
        md = ManualEngine.get_manual_markdown()
        self.assertIn("# Manuale Operativo Ufficiale", md)
        self.assertIn("Capitolo 5", md)
        self.assertIn("Capitolo 6", md)
        self.assertIn("Capitolo 7", md)

    def test_manual_pdf_compilation(self):
        pdf_bytes = ManualEngine.generate_manual_pdf()
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 500_000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()

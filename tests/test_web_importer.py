"""
Unit Tests for Web Song Importer, Manual Engine & Changelog Engine
Conforms to SRS Cap. 4.10, 4.11, 14.14, 14.15, 15.13, 15.14.
"""

import unittest
from asma_core.web_importer import WebSongImporter
from asma_core.manual_engine import ManualEngine
from asma_core.changelog_engine import ChangelogEngine
from asma_core.ai_service import BandAIService


class TestWebAndDocEngines(unittest.TestCase):

    def test_parse_html_to_song_traditional(self):
        """Test HTML scraping and heuristic chord extraction from HTML markup."""
        sample_html = """<!DOCTYPE html>
<html>
<head>
  <title>Nomadi - Canzone per un'amica - Accordi e Spartiti</title>
</head>
<body>
  <h1>Canzone per un'amica</h1>
  <div class="content">
    <pre>
        SOL           RE
Lunga e diritta correva la strada
        DO            SOL
L'auto veloce correva
    </pre>
  </div>
</body>
</html>"""
        song = WebSongImporter.parse_html_to_song(sample_html, source_url="https://test.accordi.it")
        self.assertEqual(song.title, "Canzone per un'amica")
        self.assertEqual(song.artist, "Nomadi")
        self.assertEqual(song.key_current, "SOL")
        self.assertIn("[SOL]", song.aml_content)
        self.assertIn("[RE]", song.aml_content)

    def test_manual_engine_html_and_pdf(self):
        """SRS Cap. 4.11: Generates both online markdown and printable ReportLab PDF for the user manual."""
        md = ManualEngine.get_manual_markdown()
        self.assertIn("Manuale Operativo Ufficiale", md)
        self.assertIn("AML (ASMA Markup Language)", md)

        pdf_bytes = ManualEngine.generate_manual_pdf()
        self.assertIsNotNone(pdf_bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))

    def test_changelog_engine(self):
        """SRS Cap. 4.10: Single version per day ISO format AAAA.MM.GG."""
        version = ChangelogEngine.get_latest_version()
        self.assertRegex(version, r"^\d{4}\.\d{2}\.\d{2}$")
        self.assertEqual(version, "2026.11.09")
        md = ChangelogEngine.get_changelog_markdown()
        self.assertIn("Versione 2026.11.09", md)
        self.assertIn("Versione 2026.11.08", md)
        self.assertIn("Versione 2026.11.05", md)
        self.assertIn("Nuove Funzionalità", md)

    def test_ultimate_guitar_json_parsing(self):
        """Test extraction from Ultimate Guitar js-store data structure."""
        import json
        ug_data = {
            "store": {
                "page": {
                    "data": {
                        "tab": {"song_name": "Hotel California", "artist_name": "Eagles"},
                        "tab_view": {
                            "meta": {"tonality": "Bm"},
                            "wiki_tab": {
                                "content": "[tab][Intro]\n[ch]Bm[/ch]   [ch]F#[/ch]   [ch]A[/ch]   [ch]E[/ch][/tab]\n[Verse]\n[ch]Bm[/ch]On a dark desert highway [ch]F#[/ch]cool wind in my hair"
                            }
                        }
                    }
                }
            }
        }
        json_blob = json.dumps(ug_data)
        sample_ug_html = f"""<html><body><div class="js-store" data-content='{json_blob}'></div></body></html>"""
        song = WebSongImporter.fetch_from_url("https://tabs.ultimate-guitar.com/tab/eagles/hotel-california-chords-1403188") if False else WebSongImporter._parse_ultimate_guitar(sample_ug_html, "https://tabs.ultimate-guitar.com/tab/test")
        self.assertEqual(song.title, "Hotel California")
        self.assertEqual(song.artist, "Eagles")
        self.assertEqual(song.key_current, "Bm")
        self.assertIn("[Bm]", song.aml_content)
        self.assertIn("desert highway", song.aml_content)

    def test_compute_relevance(self):
        """Test relevance ranking of candidate search results."""
        score_exact = WebSongImporter._compute_relevance("Albachiara", "Vasco Rossi", "Albachiara", "Vasco Rossi")
        score_partial = WebSongImporter._compute_relevance("Albachiara", "Vasco Rossi", "Albachiara (Live)", "Various")
        self.assertGreater(score_exact, score_partial)

    def test_search_online_fallback(self):
        """Test graceful fallback to editable draft when searching offline or non-existent song."""
        song = WebSongImporter.search_online_and_import("NonExistentSongXYZ12345", "UnknownBand")
        self.assertIsNotNone(song)
        self.assertIn("bozza-web-fallback", song.tags)
        self.assertIn("Nonexistentsongxyz12345", song.title)

    def test_band_ai_service_offline_fallback(self):
        """SRS Cap. 15.6: Creative advice operates deterministically when AI is OFF."""
        res = BandAIService.suggest_medley_transition("Song A", "C", 120, "Song B", "G", 125)
        self.assertIsNotNone(res["score"])
        self.assertIn("creative_advice", res)


if __name__ == "__main__":
    unittest.main()

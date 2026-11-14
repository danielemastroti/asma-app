import unittest
from asma_core.aml_parser import AMLParser, CustomTagNode, SectionNode, DirectiveNode
from asma_core.pdf_engine import PDFEngine
from asma_core.models import Song, DeviceProfile
from asma_core.changelog_engine import ChangelogEngine

class TestScenaAndStaccoDirectives(unittest.TestCase):

    def test_parse_scena_directive(self):
        aml = """{title: Test Scena}
{key: C}
{scena: 3}
[C]Canto una [G]canzone
{Scena: Setup Brass}
[Am]Seconda riga
{scena 7}
[F]Terza riga
"""
        doc = AMLParser.parse(aml)
        scena_nodes = [n for n in doc.nodes if (isinstance(n, (CustomTagNode, DirectiveNode)) and getattr(n, "tag_type", getattr(n, "name", "")).lower() == "scena")]
        self.assertEqual(len(scena_nodes), 3)
        self.assertEqual(getattr(scena_nodes[0], "content", getattr(scena_nodes[0], "value", "")), "3")
        self.assertEqual(getattr(scena_nodes[1], "content", getattr(scena_nodes[1], "value", "")), "Setup Brass")
        self.assertEqual(getattr(scena_nodes[2], "content", getattr(scena_nodes[2], "value", "")), "7")

    def test_parse_stacco_directive(self):
        aml = """{title: Test Stacco}
{key: C}
{stacco: guitar}
[C] [G]
{stacco organo}
[Am] [F]
{stacco: Tutti}
[G]
{stacco}
"""
        doc = AMLParser.parse(aml)
        stacco_nodes = [n for n in doc.nodes if (isinstance(n, (SectionNode, CustomTagNode, DirectiveNode)) and getattr(n, "section_name", getattr(n, "tag_type", getattr(n, "name", ""))).lower() == "stacco")]
        self.assertEqual(len(stacco_nodes), 4)
        self.assertEqual(getattr(stacco_nodes[0], "label", getattr(stacco_nodes[0], "content", getattr(stacco_nodes[0], "value", ""))), "guitar")
        self.assertEqual(getattr(stacco_nodes[1], "label", getattr(stacco_nodes[1], "content", getattr(stacco_nodes[1], "value", ""))), "organo")
        self.assertEqual(getattr(stacco_nodes[2], "label", getattr(stacco_nodes[2], "content", getattr(stacco_nodes[2], "value", ""))), "Tutti")

    def test_pdf_generation_with_scena_and_stacco(self):
        song = Song(
            uuid="test-scena-stacco-pdf",
            title="Brano Live Setup",
            artist="Band Live",
            key_current="G",
            bpm=128,
            time_signature="4/4",
            aml_content="""{title: Brano Live Setup}
{artist: Band Live}
{key: G}
{bpm: 128}

{scena: 4}
{stacco: Tutti}
[G]Intro potente [D]con tutta la band
{soc}
{scena: Piano Solo}
[Em]Ritornello [C]emozionante
{stacco: guitar}
{eoc}
[G] [D] [Em] [C]
"""
        )
        pdf_bytes = PDFEngine.generate_song_pdf(song, use_cache=False)
        self.assertIsNotNone(pdf_bytes)
        self.assertGreater(len(pdf_bytes), 1000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_medley_with_scena_and_stacco(self):
        song = Song(
            uuid="test-medley-scena-stacco",
            title="Medley Dance Live",
            artist="The Band",
            key_current="A",
            bpm=120,
            aml_content="""{title: Medley Dance Live}
{artist: The Band}
{key: A}

{start_of_song: Gloria | Umberto Tozzi | A}
{scena: 1}
{stacco: fiati}
[A]Gloria manchi tu nell'aria [D]
{end_of_song}

{start_of_song: Ti Amo | Umberto Tozzi | G}
{scena: 8}
{stacco: organo}
[G]Ti amo, un soldo, ti amo [C]
{end_of_song}
"""
        )
        pdf_bytes = PDFEngine.generate_song_pdf(song, use_cache=False)
        self.assertIsNotNone(pdf_bytes)
        self.assertGreater(len(pdf_bytes), 1000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_changelog_rule_and_entry(self):
        latest = ChangelogEngine.get_latest_version()
        self.assertEqual(latest, "2026.11.14")
        all_entries = ChangelogEngine.get_entries()
        today_entry = next((e for e in all_entries if e["version"] == "2026.11.14"), None)
        self.assertIsNotNone(today_entry)
        self.assertTrue(len(today_entry.get("new_features", [])) >= 3)
        self.assertTrue(len(today_entry.get("bug_fixes", [])) >= 1)

if __name__ == "__main__":
    unittest.main()

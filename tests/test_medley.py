import unittest
import io
from asma_core.models import Song, DeviceProfile
from asma_core.aml_parser import (
    AMLParser, AMLDocument, MedleySongStartNode, MedleySongEndNode
)
from asma_core.pdf_engine import PDFEngine, MEDLEY_COLORS


class TestMedleyFeature(unittest.TestCase):
    def test_parse_medley_start_value(self):
        # Format 1: Pipe separated
        t, a, k = AMLParser.parse_medley_start_value("Gloria | Umberto Tozzi | MI")
        self.assertEqual(t, "Gloria")
        self.assertEqual(a, "Umberto Tozzi")
        self.assertEqual(k, "MI")

        # Format 2: Hyphen separated
        t, a, k = AMLParser.parse_medley_start_value("Certe Notti - Ligabue")
        self.assertEqual(t, "Certe Notti")
        self.assertEqual(a, "Ligabue")
        self.assertEqual(k, "")

        # Format 3: Title only
        t, a, k = AMLParser.parse_medley_start_value("Ti Amo")
        self.assertEqual(t, "Ti Amo")
        self.assertEqual(a, "")
        self.assertEqual(k, "")

    def test_aml_parser_medley_nodes(self):
        aml = """{title: Medley Anni 80}
{artist: ASMA Band}

{start_of_song: Gloria | Umberto Tozzi | MI}
[INTRO]
| MI | LA | SI | MI |
{soc}
[MI]Gloria... [SI]manchi tu nell'aria
{eoc}
{end_of_song}

{sos: Gente di Mare | Raf & Tozzi | DO}
[INTRO]
| DO | SOL | LAm | FA |
{sov}
[DO]A tutti i marinai...
{eov}
{eos}
"""
        doc = AMLParser.parse(aml)
        self.assertTrue(doc.is_medley)
        self.assertEqual(len(doc.medley_fragments), 2)

        frag1 = doc.medley_fragments[0]
        self.assertIsInstance(frag1, MedleySongStartNode)
        self.assertEqual(frag1.title, "Gloria")
        self.assertEqual(frag1.artist, "Umberto Tozzi")
        self.assertEqual(frag1.key, "MI")

        frag2 = doc.medley_fragments[1]
        self.assertIsInstance(frag2, MedleySongStartNode)
        self.assertEqual(frag2.title, "Gente di Mare")
        self.assertEqual(frag2.artist, "Raf & Tozzi")
        self.assertEqual(frag2.key, "DO")

    def test_medley_up_to_20_fragments(self):
        fragments = []
        for i in range(1, 21):
            fragments.append(f"""{{start_of_song: Brano {i} | Artista {i} | DO}}
[INTRO]
| DO | SOL |
{{soc}}
[DO]Ritornello brano {i}
{{eoc}}
{{end_of_song}}""")
        full_aml = "\n\n".join(fragments)
        doc = AMLParser.parse(full_aml)
        self.assertTrue(doc.is_medley)
        self.assertEqual(len(doc.medley_fragments), 20)
        self.assertEqual(doc.medley_fragments[19].title, "Brano 20")

    def test_medley_transposition(self):
        aml = """{start_of_song: Gloria | Umberto Tozzi | MI}
[INTRO]
| MI | LA |
{soc}
[MI]Gloria...
{eoc}
{end_of_song}"""
        # Transpose by +2 semitones (MI -> FA#)
        transposed_text = AMLParser.transpose_preserving_format(aml, semitones=2)
        self.assertIn("{start_of_song: Gloria | Umberto Tozzi | FA#}", transposed_text)
        self.assertIn("[FA#]Gloria...", transposed_text)
        self.assertIn("| FA# | SI |", transposed_text)

        # Transpose AST document
        doc = AMLParser.parse(aml)
        transposed_doc = AMLParser.transpose_document(doc, semitones=2)
        self.assertEqual(transposed_doc.medley_fragments[0].key, "FA#")

    def test_pdf_generation_medley(self):
        song = Song(
            uuid="medley-test-uuid",
            title="SUPER MEDLEY LIVE",
            artist="ASMA BAND",
            key_original="DO",
            key_current="DO",
            aml_content="""{start_of_song: Gloria | Umberto Tozzi | MI}
[INTRO]
| MI | LA | SI | MI |
{soc}
[MI]Gloria... [SI]manchi tu nell'aria
{eoc}
{end_of_song}

{start_of_song: Gente di Mare | Raf & Tozzi | DO}
[INTRO]
| DO | SOL | LAm | FA |
{sov}
[DO]A tutti i marinai...
{eov}
{end_of_song}"""
        )
        pdf_bytes = PDFEngine.generate_song_pdf(song, use_cache=False)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000)

        # Ensure 20 colors are defined
        self.assertGreaterEqual(len(MEDLEY_COLORS), 20)

    def test_pdf_medley_20_fragments_and_invisible_directives(self):
        import fitz  # PyMuPDF
        fragments = []
        for i in range(1, 21):
            fragments.append(f"""{{start_of_song: Canzone {i} | Autore {i} | RE}}
[INTRO]
| RE | LA |
{{soc}}
[RE]Ritornello numero {i}...
{{eoc}}
{{end_of_song}}""")
        song_20 = Song(
            uuid="medley-20-test",
            title="MEGAMIX 20 BRANI",
            artist="ASMA BAND",
            key_original="RE",
            key_current="RE",
            aml_content="\n\n".join(fragments)
        )
        pdf_bytes = PDFEngine.generate_song_pdf(song_20, use_cache=False)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 2000)

        # Inspect extracted text via PyMuPDF to ensure {start_of_song} and {end_of_song} are hidden
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        full_text = "\n".join(page.get_text() for page in doc)
        doc.close()

        # Directive tags MUST be invisible as raw text
        self.assertNotIn("{start_of_song", full_text)
        self.assertNotIn("{end_of_song}", full_text)
        self.assertNotIn("{sos", full_text)
        self.assertNotIn("{eos}", full_text)

        # Titles of fragments MUST be present
        self.assertIn("1. CANZONE 1", full_text)
        self.assertIn("20. CANZONE 20", full_text)


if __name__ == "__main__":
    unittest.main()

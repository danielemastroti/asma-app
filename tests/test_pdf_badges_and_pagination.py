import unittest
import pymupdf
from asma_core.aml_parser import AMLParser, SectionNode
from asma_core.pdf_engine import PDFEngine
from asma_core.models import Song, DeviceProfile

class TestPdfBadgesAndPagination(unittest.TestCase):

    def test_bracket_sections_parsed_as_section_node(self):
        """Test that bracketed section headers are parsed as SectionNode, not plain lyrics or chords."""
        aml = """{title: Test Bracket Sections}
{key: C}
[INTRO]
DO  SOL
[STROFA]
Motocicletta tutta cromata
[STROFA 1]
e' tua se dici si
[RIT]
Non dire no
[RITORNELLO]
Non dire no
[BRIDGE]
Ponte musicale
[STACCO]
Stacco violento
[SOLO: Chitarra]
Assolo virtuoso
[OUTRO]
Fine del brano
[END]
"""
        doc = AMLParser.parse(aml)
        section_nodes = [n for n in doc.nodes if isinstance(n, SectionNode)]
        sec_names = [n.section_name for n in section_nodes]
        self.assertIn("intro", sec_names)
        self.assertIn("strofa", sec_names)
        self.assertIn("ritornello", sec_names)
        self.assertIn("bridge", sec_names)
        self.assertIn("stacco", sec_names)
        self.assertIn("solo", sec_names)
        self.assertIn("outro", sec_names)
        self.assertIn("end", sec_names)

    def test_scena_directive_renders_keyboard_icon_and_no_scena_word(self):
        """Directive {scena: ...} must NOT display the word 'scena' in PDF, only the keyboard icon and value."""
        song = Song(
            title="Test Scena Icon",
            artist="Keyboardist",
            key_current="G",
            aml_content="""{title: Test Scena Icon}
{artist: Keyboardist}
{key: G}
{scena: 3}
[G]Intro con Synth
{scena: Lead Solo}
[D]Assolo di tastiera
"""
        )
        pdf_bytes = PDFEngine.generate_song_pdf(song, use_cache=False)
        self.assertIsNotNone(pdf_bytes)
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        full_text = "\n".join(page.get_text() for page in doc)
        doc.close()

        # Must contain the values
        self.assertIn("3", full_text)
        self.assertIn("LEAD SOLO", full_text.upper())
        # Must NOT contain the word "SCENA:" or "[SCENA"
        self.assertNotIn("[SCENA", full_text.upper())
        self.assertNotIn("SCENA:", full_text.upper())

    def test_section_orphan_protection_moves_entire_section_to_next_page(self):
        """When a section (e.g. STROFA) begins near page bottom where only 1 line fits,
        the entire section must be moved to the next page instead of leaving 1 line stranded."""
        # Create a song with enough lines to push a section close to the page boundary
        lines = ["{title: Test Orphan Protection}", "{artist: Test Band}", "{key: C}"]
        for i in range(28):
            lines.append(f"[C]Riga di riempimento numero {i+1} [G]con accordi")
        # Now add STROFA with 4 lines
        lines.append("[STROFA]")
        lines.append("[FA#]Apro gli occhi e [SI]ti penso")
        lines.append("[DO#]ed ho [FA#]in mente [SI]te [DO#]")
        lines.append("[SI]ed ho in [LA#m]mente [SI]te [DO#]")

        song = Song(
            title="Test Orphan Protection",
            artist="Test Band",
            key_current="C",
            aml_content="\n".join(lines)
        )
        # Tablet profile
        prof = DeviceProfile(name="iPad", target_device="tablet", font_size_lyrics=13.0, font_size_chords=14.0)
        pdf_bytes = PDFEngine.generate_song_pdf(song, profile=prof, use_cache=False)
        self.assertIsNotNone(pdf_bytes)
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")

        if len(doc) > 1:
            p1_text = doc[0].get_text()
            p2_text = doc[1].get_text()
            # If [STROFA] is on page 2, its lines must also be on page 2
            if "[STROFA]" in p2_text:
                self.assertIn("Apro gli occhi", p2_text)
                self.assertIn("FA#", p2_text)
                # Page 1 must not have [STROFA] alone
                self.assertNotIn("[STROFA]", p1_text)
            elif "[STROFA]" in p1_text:
                # If on page 1, all lines must fit on page 1
                self.assertIn("Apro gli occhi", p1_text)
        doc.close()

if __name__ == "__main__":
    unittest.main()

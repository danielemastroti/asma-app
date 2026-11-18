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

    def test_section_with_directives_not_split_across_pages(self):
        """A section (e.g. STROFA) with directives/tags (e.g. {scena: ENTRA HAMMOND}) must never split badge and directive across pages."""
        aml = """Intro:
[LAm]     [FA]    [DO]    [SOL]     [DO]
{sov}
 [DO]Someone told me long ago
There's a calm before the storm
I [SOL]know.. It's been comin' [DO]for some time
{eov}
{sov}
When it's over, so they say
It'll rain a sunny day
I [SOL]know.. Shinin' down like [DO]water
{eov}
{soc}
 [FA]I want to [SOL]know
Have you [DO]ever [SOL/SI]seen the [LAm]rain  [LAm/SOL]
 [FA]I want to [SOL]know
Have you [DO]ever [SOL/SI]seen the [LAm]rain  [LAm/SOL]
 [FA]Comin' [SOL]down on a sunny [DO]day?
{eoc}
{sov}
{scena: ENTRA HAMMOND}
 [DO]Yesterday, and days before
Sun is cold and rain is hard,
I [SOL]know.. Been that way for [DO]all my time
{eov}
{sov}
'Til forever, on it goes
Through the circle, fast and slow,
I [SOL]know.. It can't stop, I [DO]wonder
{eov}
{soc}
 [FA]I want to [SOL]know
Have you [DO]ever [SOL/SI]seen the [LAm]rain  [LAm/SOL]
{eoc}"""
        prof = DeviceProfile(name='test_tablet', font_size_lyrics=18.0, font_size_chords=18.0, columns=1, margin_top_mm=8.0, margin_bottom_mm=8.0, margin_left_mm=10.0, margin_right_mm=10.0)
        song = Song(uuid='test-cvr', title='HAVE YOU EVER SEEN THE RAIN?', artist='CCR', aml_content=aml)
        pdf_bytes = PDFEngine.generate_song_pdf(song, profile=prof, user_name='Sentimental', use_cache=False)
        doc = pymupdf.open(stream=pdf_bytes, filetype='pdf')
        self.assertGreaterEqual(len(doc), 2)

        # STROFA and ENTRA HAMMOND must NEVER be separated onto different pages
        for page_idx, page in enumerate(doc):
            text = page.get_text()
            if "ENTRA HAMMOND" in text:
                # The STROFA badge and the first verse line must be on the EXACT SAME page as ENTRA HAMMOND
                self.assertIn("[STROFA]", text, f"ENTRA HAMMOND is on page {page_idx+1} but [STROFA] is missing from this page!")
                self.assertIn("Yesterday, and days before", text, f"ENTRA HAMMOND is on page {page_idx+1} but lyrics are missing from this page!")
            elif "Yesterday, and days before" in text:
                self.assertIn("ENTRA HAMMOND", text, f"Lyrics on page {page_idx+1} but ENTRA HAMMOND missing!")
                self.assertIn("[STROFA]", text, f"Lyrics on page {page_idx+1} but [STROFA] missing!")

        doc.close()

    def test_long_section_splits_across_pages_keeping_head_intact(self):
        """A long section (e.g. 15-line chorus in 50 Special) can split across pages, keeping badge and first 6 text lines intact."""
        import json
        with open('data/songs/50_special_bebdbb.json', encoding='utf-8') as f:
            d = json.load(f)
        prof = DeviceProfile(
            name='Huawei MediaPad M5',
            font_size_lyrics=13.0,
            font_size_chords=13.0,
            columns=1,
            margin_top_mm=10.0,
            margin_bottom_mm=8.0,
            margin_left_mm=10.0,
            margin_right_mm=10.0,
        )
        song = Song.from_dict(d)
        pdf_bytes = PDFEngine.generate_song_pdf(song, profile=prof, user_name='Cico', use_cache=False)
        doc = pymupdf.open(stream=pdf_bytes, filetype='pdf')

        p1_text = doc[0].get_text()
        p2_text = doc[1].get_text()
        doc.close()

        # Page 1 must not be left half-empty: it must contain Verse 1 AND the head of Ritornello
        self.assertIn("Dammi una special", p1_text)
        self.assertIn("[RITORNELLO]", p1_text)
        self.assertIn("Ma quant'è bello andare in giro", p1_text)
        self.assertIn("per i colli bolognesi", p1_text)  # 6th line of text

        # Page 2 continues with the rest of the ritornello and next verse
        self.assertIn("Esco di fretta dalla mia stanza", p2_text)

    def test_blank_line_directive_renders_successfully(self):
        """Directive {riga_bianca} or {blank_line} or {riga_bianca: 2} inserts spacing without errors."""
        aml = """{title: Test Blank Line}
{artist: Test}
{key: C}
[STROFA]
[C]Prima riga
{riga_bianca}
[G]Seconda riga dopo riga bianca
{blank_line: 2}
[F]Terza riga dopo due righe bianche
{riga_bianca: 15mm}
[C]Quarta riga dopo 15 millimetri
"""
        song = Song(title="Test Blank Line", artist="Test", key_current="C", aml_content=aml)
        pdf_bytes = PDFEngine.generate_song_pdf(song, use_cache=False)
        self.assertIsNotNone(pdf_bytes)
        self.assertGreater(len(pdf_bytes), 1000)
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        self.assertIn("Prima riga", text)
        self.assertIn("Seconda riga dopo riga bianca", text)
        self.assertIn("Terza riga dopo due righe bianche", text)
        self.assertIn("Quarta riga dopo 15 millimetri", text)


if __name__ == "__main__":
    unittest.main()

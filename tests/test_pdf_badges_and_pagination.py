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
        num_pages = len(doc)
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

        # The entire song and [END] must fit on 2 pages without creating an orphan 3rd page for [END] alone
        self.assertEqual(num_pages, 2, "50 Special with Huawei MediaPad M5 must fit on 2 pages without orphan END on page 3")
        self.assertIn("[END]", p2_text, "END badge must be on page 2")

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

    def test_burning_love_formatting_for_cico(self):
        """Verifies that Burning Love formats into balanced pages without orphan lines for Cico's Huawei MediaPad M5 profile."""
        from asma_core.storage_manager import StorageManager
        from asma_core.preferences_manager import PreferencesManager
        from asma_core.device_manager import DeviceManager

        storage = StorageManager()
        song = storage.get_song("burning_love_3f6762")
        self.assertIsNotNone(song)

        dev_mgr = DeviceManager()
        base_prof = dev_mgr.get_device_by_name("Huawei MediaPad M5")
        pref_mgr = PreferencesManager()
        user_prefs = pref_mgr.get_preferences("cico@band.org", "Huawei MediaPad M5")

        prof = DeviceProfile(
            name=base_prof.name,
            target_device=base_prof.target_device,
            device_type=base_prof.device_type,
            width_mm=base_prof.width_mm,
            height_mm=base_prof.height_mm,
            orientation=base_prof.orientation,
            columns=int(user_prefs.get("layout_columns", 2)),
            font_size_lyrics=float(user_prefs.get("layout_font_size", 11.5)),
            font_size_chords=float(user_prefs.get("layout_font_size_chords", 12.5)),
            margin_top_mm=float(user_prefs.get("layout_margin_top", 8.0)),
            margin_bottom_mm=float(user_prefs.get("layout_margin_bottom", 8.0)),
            margin_left_mm=float(user_prefs.get("layout_margin_lateral", 8.0)),
            margin_right_mm=float(user_prefs.get("layout_margin_lateral", 8.0)),
        )

        pdf_bytes = PDFEngine.generate_song_pdf(
            song,
            profile=prof,
            include_chords=True,
            use_cache=False,
            user_name="Cico"
        )
        self.assertIsNotNone(pdf_bytes)
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        self.assertEqual(len(doc), 2, "Burning Love should format cleanly onto exactly 2 balanced pages in 2-column mode")

        p1_text = doc[0].get_text()
        p2_text = doc[1].get_text()
        doc.close()

        self.assertIn("[INTRO]", p1_text)
        self.assertIn("[STROFA: 1]", p1_text)
        self.assertIn("[RITORNELLO]", p1_text)
        self.assertIn("[STRUMENTALE]", p1_text)
        self.assertIn("[STROFA: 3]", p1_text)

        self.assertIn("[RITORNELLO]", p2_text)
        self.assertTrue("[OUTRO]" in p2_text or "[FINALE]" in p2_text)
        self.assertIn("[END]", p2_text)

    def test_ipad_page_dimensions_and_footer_margins(self):
        """Verifies iPad 10.2 profile has 174.1 x 224.0 mm, margin_bottom_mm=14.0, and generated PDF has exact canvas dimensions and footer."""
        from asma_core.device_manager import DeviceManager
        dm = DeviceManager()
        prof = dm.get_device_by_name('IPad 10.2" (7/8/9 gen) & pro 2019')
        self.assertIsNotNone(prof)
        self.assertEqual(prof.width_mm, 174.1)
        self.assertEqual(prof.height_mm, 224.0)
        self.assertEqual(prof.margin_bottom_mm, 14.0)

        song = Song(
            uuid="test_ipad_song",
            title="TEST IPAD SONG",
            artist="Band",
            aml_content="[INTRO]\nDO SOL\n[STROFA 1]\nTesto di prova\n[END]"
        )
        pdf_bytes = PDFEngine.generate_song_pdf(song, profile=prof, user_name="Cico", use_cache=False)
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        self.assertEqual(len(doc), 1)
        page = doc[0]
        expected_w = 174.1 * (72.0 / 25.4)
        expected_h = 224.0 * (72.0 / 25.4)
        self.assertAlmostEqual(page.rect.width, expected_w, places=1)
        self.assertAlmostEqual(page.rect.height, expected_h, places=1)
        txt = page.get_text()
        self.assertIn("Pagina 1 di 1", txt)
        self.assertIn("Rev #", txt)
        doc.close()

    def test_cico_singer_view_deduplicates_consecutive_strumentale(self):
        """Verifies that in singer view (include_chords=False), consecutive Strumentale badges/directives appear only once."""
        aml = """{title: CON IL NASTRO ROSA}
{artist: Lucio Battisti}
{key: SOL}
[INTRO]
SOL | DO | MIm | RE
[STRUMENTALE]
SOL | DO | MIm | RE
[STROFA: 1]
Inseguendo una libellula in un prato
[STRUMENTALE]
MIm | DO | RE
[SOLO: Chitarra]
SOL | DO | RE
[STROFA: 2]
Un'altra riga di testo
[END]
"""
        song = Song(
            uuid="test_nastro_rosa",
            title="CON IL NASTRO ROSA",
            artist="Lucio Battisti",
            aml_content=aml
        )
        prof = DeviceProfile(
            name="Tablet Cico",
            columns=1,
            font_size_lyrics=14.0,
            font_size_chords=14.0,
            margin_bottom_mm=12.0
        )
        pdf_bytes = PDFEngine.generate_song_pdf(song, profile=prof, include_chords=False, user_name="Cico", use_cache=False)
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        full_text = "\n".join(p.get_text() for p in doc)
        doc.close()

        intro_to_strofa1 = full_text[full_text.find("[INTRO]"):full_text.find("[STROFA: 1]")]
        self.assertIn("(Strumentale)", intro_to_strofa1)
        self.assertNotIn("[STRUMENTALE]", intro_to_strofa1, "Consecutive [STRUMENTALE] badge must be suppressed after (Strumentale)")
        self.assertEqual(intro_to_strofa1.count("(Strumentale)"), 1, "There must be exactly one (Strumentale) indicator between INTRO and STROFA: 1")

        strofa1_to_strofa2 = full_text[full_text.find("[STROFA: 1]"):full_text.find("[STROFA: 2]")]
        self.assertIn("[STRUMENTALE]", strofa1_to_strofa2)
        self.assertNotIn("[SOLO: Chitarra]", strofa1_to_strofa2, "Consecutive solo badge must be suppressed when already in instrumental")
        self.assertEqual(strofa1_to_strofa2.count("[STRUMENTALE]"), 1)


if __name__ == "__main__":
    unittest.main()

"""
Unit Tests for Device-Aware PDF Engine
Conforms to SRS Cap. 13, 17.22 and Blueprint Sec. 7.
"""

import unittest
from asma_core.models import Song, DeviceProfile, Setlist, SetlistItem
from asma_core.pdf_engine import PDFEngine


class TestPDFEngine(unittest.TestCase):

    def setUp(self):
        PDFEngine.clear_cache()
        self.song = Song(
            title="Hotel California",
            artist="Eagles",
            author="Henley, Frey, Felder",
            key_current="Bm",
            bpm=74,
            time_signature="4/4",
            aml_content="""{title: Hotel California}
{artist: Eagles}
{key: Bm}
{tempo: 74}

{intro}
| Bm | F#7 | A | E |

{verse}
[Bm]On a dark desert highway, [F#7]cool wind in my hair
[A]Warm smell of colitas, [E]rising up through the air

{chorus}
[G]Welcome to the Hotel Cali[D]fornia
{guitar: Don Felder solo}
Such a [Em]lovely place, such a [F#7]lovely face
"""
        )

    def test_generate_song_pdf_basic(self):
        """Test generating standard A4 printable PDF."""
        pdf_bytes = PDFEngine.generate_song_pdf(self.song)
        self.assertIsNotNone(pdf_bytes)
        self.assertTrue(len(pdf_bytes) > 1000)
        # Check PDF header
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))

    def test_generate_pdf_across_device_profiles(self):
        """SRS Cap. 13.4: Device-aware PDF rendering for Smartphone, Tablet, iPad and A4."""
        profiles = [
            DeviceProfile(name="Smartphone", target_device="smartphone"),
            DeviceProfile(name="Tablet Stage", target_device="tablet", orientation="landscape"),
            DeviceProfile(name="iPad Pro", target_device="ipad"),
            DeviceProfile(name="PC A4", target_device="pc_a4")
        ]
        for prof in profiles:
            pdf_bytes = PDFEngine.generate_song_pdf(self.song, profile=prof, use_cache=False)
            self.assertIsNotNone(pdf_bytes, f"Failed for profile {prof.name}")
            self.assertTrue(pdf_bytes.startswith(b"%PDF-"))

    def test_watermark_rendering(self):
        """SRS Cap. 13.25: Watermark support on generated PDF."""
        pdf_bytes = PDFEngine.generate_song_pdf(self.song, watermark="Bozza Provvisoria", use_cache=False)
        self.assertIsNotNone(pdf_bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))

    def test_setlist_pdf_generation(self):
        """SRS Cap. 13.3 & 13.14: Setlist PDF with cover page, index and concatenated songs."""
        song2 = Song(
            title="Canzone per un'amica",
            artist="Nomadi",
            key_current="G",
            bpm=92,
            aml_content="{title: Canzone per un'amica}\n[SOL]Lunga e diritta correva la strada"
        )
        setlist = Setlist(
            title="Concerto Estate 2027",
            date="15/07/2027",
            description="Tour Estivo Band ASMA",
            items=[
                SetlistItem(song_uuid=self.song.uuid),
                SetlistItem(song_uuid=song2.uuid, is_medley=True, notes="Medley segue")
            ]
        )
        setlist_pdf = PDFEngine.generate_setlist_pdf(setlist, songs=[self.song, song2])
        self.assertIsNotNone(setlist_pdf)
        self.assertTrue(len(setlist_pdf) > 2000)
        self.assertTrue(setlist_pdf.startswith(b"%PDF-"))

    def test_generate_pdf_musician_vs_singer_modes(self):
        """SRS Cap. 13: PDF export supports Musician (with chords/grids) and Singer (lyrics only)."""
        pdf_musician = PDFEngine.generate_song_pdf(self.song, include_chords=True, use_cache=False)
        pdf_singer = PDFEngine.generate_song_pdf(self.song, include_chords=False, use_cache=False)

        self.assertTrue(pdf_musician.startswith(b"%PDF-"))
        self.assertTrue(pdf_singer.startswith(b"%PDF-"))
        self.assertGreater(len(pdf_musician), 1000)
        self.assertGreater(len(pdf_singer), 1000)

    def test_generate_pdf_device_awareness(self):
        """Test PDF rendering for specific hardware profiles."""
        p_ipad = DeviceProfile(name="iPad 10.2", width_mm=174.1, height_mm=250.6, orientation="portrait")
        p_huawei = DeviceProfile(name="Huawei M5", width_mm=172.0, height_mm=258.0, orientation="landscape")
        p_phone = DeviceProfile(name="Pixel 8 pro", width_mm=70.8, height_mm=153.4, orientation="portrait")

        for prof in [p_ipad, p_huawei, p_phone]:
            pdf_bytes = PDFEngine.generate_song_pdf(self.song, profile=prof, use_cache=False)
            self.assertTrue(pdf_bytes.startswith(b"%PDF-"))

    def test_custom_layout_columns_fonts_and_colors(self):
        """Test PDF generation with custom layout: 2 columns, custom font sizes, margins and colors."""
        prof_2col = DeviceProfile(
            name="Custom 2Col",
            columns=2,
            font_size_lyrics=18.0,
            font_size_chords=20.0,
            margin_left_mm=15.0,
            margin_right_mm=15.0,
            color_lyrics="#222222",
            color_chords="#0D47A1",
            color_aml_markup="#2E7D32"
        )
        pdf_2col = PDFEngine.generate_song_pdf(self.song, profile=prof_2col, use_cache=False)
        self.assertTrue(pdf_2col.startswith(b"%PDF-"))
        self.assertGreater(len(pdf_2col), 1000)

        # Test extreme font sizes (10 to 30 px)
        prof_min = DeviceProfile(name="MinFont", font_size_lyrics=10.0, font_size_chords=11.0)
        prof_max = DeviceProfile(name="MaxFont", font_size_lyrics=30.0, font_size_chords=32.0)
        pdf_min = PDFEngine.generate_song_pdf(self.song, profile=prof_min, use_cache=False)
        pdf_max = PDFEngine.generate_song_pdf(self.song, profile=prof_max, use_cache=False)
        self.assertTrue(pdf_min.startswith(b"%PDF-"))
        self.assertTrue(pdf_max.startswith(b"%PDF-"))

    def test_strictly_vertical_page_size_never_landscape(self):
        """Layout PDF must strictly be portrait/vertical, never landscape."""
        # Test default and custom profiles with reversed dimensions
        prof_landscape = DeviceProfile(name="Wide Screen", width_mm=280.0, height_mm=190.0, orientation="landscape")
        w, h = PDFEngine.get_page_size(prof_landscape)
        self.assertLess(w, h, "PDF width must be strictly less than height for vertical layout")

        for target in ["smartphone", "tablet", "ipad", "pc_a4"]:
            prof = DeviceProfile(target_device=target)
            pw, ph = PDFEngine.get_page_size(prof)
            self.assertLess(pw, ph, f"Profile {target} must have vertical portrait layout")

    def test_singer_mode_with_instrumental_markers_and_spacers(self):
        """In singer mode (include_chords=False), chord sequences, solos and grids are marked as (Strumentale)."""
        song_with_solos = Song(
            title="Solo Test",
            artist="Tester",
            key_current="C",
            bpm=120,
            time_signature="4/4",
            aml_content="""{title: Solo Test}
{intro}
| C | G | Am | F |

{verse}
Testo strofa 1
[C] [G] [Am]

{solo: Chitarra elettrica}
{bridge}
Testo bridge con finale
"""
        )
        pdf_singer = PDFEngine.generate_song_pdf(song_with_solos, include_chords=False, use_cache=False)
        self.assertTrue(pdf_singer.startswith(b"%PDF-"))
        self.assertGreater(len(pdf_singer), 1000)

        pdf_musician = PDFEngine.generate_song_pdf(song_with_solos, include_chords=True, use_cache=False)
        self.assertTrue(pdf_musician.startswith(b"%PDF-"))
        self.assertGreater(len(pdf_musician), 1000)

    def test_unlabeled_sections_heuristic_and_ai_fallback(self):
        """When sections are not indicated with AML tags, engine formats PDF with detected sections and spaces."""
        from asma_core.ai_service import BandAIService

        # Case 1: Textual section headings (e.g. Ritornello:, Strofa 1:) without AML braces
        raw_song_text = """{title: Canzone Senza Tag}
Ritornello:
[DO]Nel blu dipinto di blu
[FA]Felice di stare lassù

Strofa 1:
Penso che un sogno così non ritorni mai più
Mi dipingevo le mani e la faccia di blu
"""
        converted = BandAIService.ensure_section_spacing_aml(raw_song_text)
        self.assertIn("{chorus}", converted)
        self.assertIn("{verse: 1}", converted)

        song_raw = Song(title="Canzone Senza Tag", aml_content=raw_song_text)
        pdf_bytes = PDFEngine.generate_song_pdf(song_raw, use_cache=False)
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
        self.assertGreater(len(pdf_bytes), 1000)

    def test_unformatted_continuous_lines_spacing_fallback(self):
        """When song has no sections and no empty lines, engine provides stanza spacing every 4 lines."""
        from asma_core.ai_service import BandAIService

        continuous_text = """{title: Continuous Text}
[C]Riga uno della canzone
Riga due della canzone
[G]Riga tre della canzone
Riga quattro della canzone
[Am]Riga cinque della canzone
Riga sei della canzone
[F]Riga sette della canzone
Riga otto della canzone
"""
        enhanced = BandAIService.ensure_section_spacing_aml(continuous_text)
        # Should have inserted an empty line to separate into stanzas
        self.assertIn("\n\n", enhanced)

        song_cont = Song(title="Continuous Song", aml_content=continuous_text)
        pdf_bytes = PDFEngine.generate_song_pdf(song_cont, use_cache=False)
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
        self.assertGreater(len(pdf_bytes), 1000)


    def test_guitar_tablatures_strictly_eliminated_from_pdf(self):
        """User requirement: guitar tablatures must ALWAYS be completely eliminated from generated PDFs."""
        tab_song_text = """{title: Canzone Con Tablatura}
{artist: Test Artist}
{key: C}

{intro}
[C]  [G]
Tab Intro:
e|---0-1-0-1---|
B|---1-1-1-1---|
G|---0-2-0-2---|
D|---2-3-2-3---|
A|---3-3-3-3---|
E|-------------|

{verse}
[C]Testo cantato strofa [G]uno
Riga due di testo vero

{tab}
e|-------------------|
B|-------------------|
G|---2-2-4-2---------|
D|---0-0-0-0---------|
A|-------------------|
E|-------------------|
{end_of_tab}

{chorus}
[F]Testo del ritornello [G]qui
"""
        song_with_tab = Song(title="Canzone Con Tablatura", aml_content=tab_song_text)
        
        # Test detection function directly
        self.assertTrue(PDFEngine.is_guitar_tab_line("e|---0-1-0-1---|"))
        self.assertTrue(PDFEngine.is_guitar_tab_line("B|---1-1-1-1---|"))
        self.assertTrue(PDFEngine.is_guitar_tab_line("Tab Intro:"))
        self.assertTrue(PDFEngine.is_guitar_tab_line("|---0-1-0-1---|"))
        self.assertTrue(PDFEngine.is_guitar_tab_line("---------------------"))
        self.assertFalse(PDFEngine.is_guitar_tab_line("[C]Testo cantato strofa [G]uno"))
        self.assertFalse(PDFEngine.is_guitar_tab_line("| C | G | Am | F |"))

        # Render flowables and ensure NO tablature lines exist
        styles = PDFEngine._build_style_sheet(DeviceProfile(), "classic")
        from asma_core.aml_parser import AMLParser
        doc = AMLParser.parse(tab_song_text)
        flowables = PDFEngine._render_aml_nodes_to_flowables(doc, styles, 400.0, include_chords=True)
        
        # Flatten and inspect textual content in flowables
        def get_all_text(item):
            if hasattr(item, "text"):
                return item.text
            if hasattr(item, "_content"):
                return " ".join([get_all_text(x) for x in item._content])
            if hasattr(item, "_cellvalues"):
                return " ".join([get_all_text(c) for row in item._cellvalues for c in row])
            return ""

        joined_text = " ".join([get_all_text(f) for f in flowables])
        clean_joined = joined_text.replace("&nbsp;", " ")
        self.assertNotIn("e|---", clean_joined)
        self.assertNotIn("B|---", clean_joined)
        self.assertNotIn("G|---", clean_joined)
        self.assertNotIn("Tab Intro", clean_joined)
        self.assertIn("Testo cantato strofa", clean_joined)
        self.assertIn("Testo del ritornello", clean_joined)

        # Generate actual PDF bytes with chords and lyrics-only
        pdf_chords = PDFEngine.generate_song_pdf(song_with_tab, include_chords=True, use_cache=False)
        pdf_lyrics = PDFEngine.generate_song_pdf(song_with_tab, include_chords=False, use_cache=False)
        self.assertTrue(pdf_chords.startswith(b"%PDF-"))
        self.assertTrue(pdf_lyrics.startswith(b"%PDF-"))

    def test_bpm_estimation_not_defaulting_to_120(self):
        """Music service fetches verified BPM from SongBPM.com and falls back to 120 only when not found."""
        from asma_core.ai_service import BandAIService
        bpm_knock = BandAIService.estimate_song_bpm("KNOCK ON WOOD", "Amii Stewart")
        self.assertEqual(bpm_knock, 140)
        self.assertNotEqual(bpm_knock, 120)

        bpm_albachiara = BandAIService.estimate_song_bpm("Albachiara", "Vasco Rossi")
        self.assertEqual(bpm_albachiara, 145)

        bpm_unknown = BandAIService.estimate_song_bpm("Brano Inesistente 99999", "Artista Inesistente")
        self.assertEqual(bpm_unknown, 120)

    def test_songs_alphabetical_sorting(self):
        """All songs from storage are returned in case-insensitive alphabetical order."""
        from asma_core.storage_manager import StorageManager
        sm = StorageManager()
        songs = sm.list_songs()
        if len(songs) >= 2:
            titles = [s["title"].lower() for s in songs]
            self.assertEqual(titles, sorted(titles))

    def test_pdf_header_no_solo_testo_label_and_pseudonym_in_parens(self):
        """PDF removes 'Solo Testo'/'Accordi' label and wraps user pseudonym in parentheses."""
        import pymupdf
        song = Song(
            title="Test Header PDF",
            artist="Band",
            key_current="C",
            aml_content="[C]Prima [G]riga\n" + ("[Am]Riga lunga\n" * 60),
        )
        pdf_singer = PDFEngine.generate_song_pdf(
            song, include_chords=False, use_cache=False, user_name="Cico"
        )
        doc = pymupdf.open(stream=pdf_singer, filetype="pdf")
        full_text = "\n".join(page.get_text() for page in doc)
        doc.close()
        self.assertIn("(Cico)", full_text)
        self.assertNotIn("Solo Testo", full_text)
        self.assertNotIn("ASMA Accordi", full_text)

    def test_sob_renders_bridge_badge_in_pdf(self):
        """{sob} directive without explicit label renders [BRIDGE] instead of [SPECIALE] in PDF."""
        import pymupdf
        song = Song(
            title="Test Bridge PDF",
            artist="Band",
            key_current="C",
            aml_content="{sob}\n[DO]Parte strumentale\n{eob}",
        )
        pdf_bytes = PDFEngine.generate_song_pdf(song, include_chords=True, use_cache=False)
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        full_text = "\n".join(page.get_text() for page in doc)
        doc.close()
        self.assertIn("[BRIDGE]", full_text)
        self.assertNotIn("[SPECIALE]", full_text)

    def test_plain_text_chords_align_wysiwyg_with_lyrics_in_pdf(self):
        """Chords aligned over lyrics in monospace editor must align horizontally above the same lyric word in PDF."""
        import pymupdf
        aml = (
            "{sov}\n"
            "                              SOL SOL# LA\n"
            "Worryin' 'bout the way things might have been\n"
            "{eov}"
        )
        song = Song(title="Proud Mary Align", artist="CCR", key_current="D", aml_content=aml)
        prof = DeviceProfile(font_size_lyrics=14.0, font_size_chords=11.0)
        pdf_bytes = PDFEngine.generate_song_pdf(song, profile=prof, include_chords=True, use_cache=False)
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        words = doc[0].get_text("words")
        doc.close()

        sol_x = next(w[0] for w in words if w[4] == "SOL")
        might_x = next(w[0] for w in words if w[4] == "might")
        bout_x = next(w[0] for w in words if w[4] == "'bout")
        self.assertLess(abs(sol_x - might_x), 15.0)
        self.assertGreater(sol_x - bout_x, 80.0)

    def test_solo_directive_with_instrument_renders_in_pdf(self):
        """{solo: brass ensemble} and {solo: electric guitar} render full instrument label in PDF badge."""
        import pymupdf
        aml = (
            "{solo: brass ensemble}\n"
            "| DO | FA | SOL | DO |\n\n"
            "{solo: electric guitar}\n"
            "| LA | RE | MI | LA |"
        )
        song = Song(title="Solo Instruments Test", artist="Band", key_current="C", aml_content=aml)
        pdf_bytes = PDFEngine.generate_song_pdf(song, include_chords=True, use_cache=False)
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        full_text = "\n".join(page.get_text() for page in doc)
        doc.close()
        self.assertIn("[SOLO: BRASS ENSEMBLE]", full_text)
        self.assertIn("[SOLO: ELECTRIC GUITAR]", full_text)


if __name__ == "__main__":
    unittest.main()

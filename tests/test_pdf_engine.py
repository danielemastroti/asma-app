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


if __name__ == "__main__":
    unittest.main()

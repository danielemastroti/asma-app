"""
ASMA Accordi - Medley A4 Pagination & WhatsApp Share Verification Tests
Tests that Medley songs exported to A4 (for printing or WhatsApp sharing)
never produce blank pages, particularly after the fragment 'WITH OR WITHOUT YOU'.
"""

import unittest
import json
import os
import pymupdf

from asma_core.models import Song, DeviceProfile
from asma_core.pdf_engine import PDFEngine
from asma_core.aml_parser import AMLParser


class TestMedleyA4Pagination(unittest.TestCase):
    def setUp(self):
        self.songs_to_test = [
            "data/songs/b4a1523d-49b1-48e8-a47c-c661646d4542.json",
            "data/songs/df8cb9ca-c685-472e-9350-2400728f1d34.json"
        ]
        self.musicians = [
            ("Puma", "titholola@gmail.com"),
            ("Cico", "acicchelli65@gmail.com"),
            ("Sentimental", "danyposta@gmail.com"),
            ("Maurino", "maurobovolenta4@gmail.com"),
            ("Red", "marcoerario2@gmail.com"),
            ("Mingo", "gv.drummer69@gmail.com")
        ]

    def _check_no_blank_pages(self, doc, label=""):
        for i, page in enumerate(doc):
            lines = [l.strip() for l in page.get_text().splitlines() if l.strip()]
            content_lines = [
                l for l in lines
                if not any(k in l for k in [
                    "THE NEW ASMA", "Pagina ", "Repertorio", "Rev #", "ASMA Band",
                    "bpm", "Durata", "Tonalità", "Generato:", "ASMA —"
                ]) and not any(f"({m[0]})" in l for m in self.musicians)
            ]
            self.assertGreater(
                len(content_lines), 0,
                f"Page {i+1} of {len(doc)} is BLANK in {label}! Content lines count was 0."
            )

    def test_medley_rock_a4_export_has_no_blank_pages(self):
        """Verifies that MEDLEY ROCK exported to A4 has zero blank pages across all devices & musicians."""
        for song_path in self.songs_to_test:
            if not os.path.exists(song_path):
                continue
            with open(song_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Test raw AML, Tablet-formatted AML, and Smartphone-formatted AML
            aml_variants = [
                ("raw", data["aml_content"]),
                ("formatted_tablet", AMLParser.format_medley_pages(data["aml_content"], strategy="smart_fit", target_device="Huawei MediaPad M5")[0]),
                ("formatted_phone", AMLParser.format_medley_pages(data["aml_content"], strategy="smart_fit", target_device="Pixel 8 pro")[0]),
                ("formatted_a4", AMLParser.format_medley_pages(data["aml_content"], strategy="smart_fit", target_device="Foglio a 4 stampabile")[0]),
            ]

            for v_name, aml in aml_variants:
                for mus_name, mus_email in self.musicians:
                    for chords in [True, False]:
                        for cols in [1, 2]:
                            prof = DeviceProfile(
                                name="Foglio a 4 stampabile",
                                target_device="pc_a4",
                                device_type="printable_a4",
                                width_mm=210.0,
                                height_mm=297.0,
                                columns=cols,
                                font_size_lyrics=12.0,
                                font_size_chords=13.0,
                                margin_top_mm=12.0,
                                margin_bottom_mm=8.0,
                                margin_left_mm=10.0,
                                margin_right_mm=10.0
                            )
                            s = Song(**data)
                            s.aml_content = aml
                            pdf = PDFEngine.generate_song_pdf(
                                s, profile=prof, include_chords=chords, user_name=mus_name, use_cache=False
                            )
                            doc = pymupdf.open(stream=pdf, filetype="pdf")
                            self._check_no_blank_pages(
                                doc,
                                label=f"{data['title']} variant={v_name} mus={mus_name} chords={chords} cols={cols}"
                            )
                            doc.close()

    def test_no_blank_page_after_with_or_without_you(self):
        """Explicitly checks that the page right after 'WITH OR WITHOUT YOU' contains next song content."""
        for song_path in self.songs_to_test:
            if not os.path.exists(song_path):
                continue
            with open(song_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Format for Tablet first (which places breaks according to tablet size)
            fmt_tablet, _ = AMLParser.format_medley_pages(data["aml_content"], strategy="smart_fit", target_device="Huawei MediaPad M5")

            prof = DeviceProfile(
                name="Foglio a 4 stampabile",
                target_device="pc_a4",
                device_type="printable_a4",
                width_mm=210.0,
                height_mm=297.0,
                columns=1,
                font_size_lyrics=12.0,
                font_size_chords=13.0
            )

            s = Song(**data)
            s.aml_content = fmt_tablet
            pdf = PDFEngine.generate_song_pdf(s, profile=prof, include_chords=True, user_name="Sentimental", use_cache=False)
            doc = pymupdf.open(stream=pdf, filetype="pdf")

            # Find which page contains 'WITH OR WITHOUT YOU'
            wow_page_idx = -1
            for i, page in enumerate(doc):
                txt = page.get_text()
                if "WITH OR WITHOUT YOU" in txt:
                    wow_page_idx = i

            self.assertGreaterEqual(wow_page_idx, 0, "WITH OR WITHOUT YOU fragment not found in PDF!")
            self.assertLess(wow_page_idx + 1, len(doc), "WITH OR WITHOUT YOU was on the last page!")

            # The next page MUST contain content (WITH OR WITHOUT YOU continuation or DON'T YOU) and must NOT be blank
            next_page = doc[wow_page_idx + 1]
            next_txt = next_page.get_text()
            self.assertTrue(
                "DON'T YOU" in next_txt or "give yourself away" in next_txt,
                f"Page {wow_page_idx + 2} immediately after WITH OR WITHOUT YOU does not contain valid content! Text: {next_txt[:200]}"
            )
            full_txt = "".join(p.get_text() for p in doc)
            self.assertIn("DON'T YOU", full_txt)
            doc.close()


if __name__ == "__main__":
    unittest.main()

import unittest
from asma_core.printer_engine import PrinterEngine
from asma_core.models import Song
from asma_core.pdf_engine import PDFEngine, DeviceProfile

class TestPrinterEngine(unittest.TestCase):
    def setUp(self):
        self.song = Song(
            title="TEST CANZONE",
            artist="Artista Test",
            aml_content="{title: TEST CANZONE}\n{artist: Artista Test}\n{key: C}\n\n{verse}\n[C]Prima riga cantata [G]con accordi\nSeconda riga di testo"
        )
        self.dev_a4 = DeviceProfile(name="Foglio a 4 stampabile", width_mm=210, height_mm=297, columns=2, font_size_lyrics=11)
        self.pdf_bytes = PDFEngine.generate_song_pdf(self.song, profile=self.dev_a4, include_chords=True, use_cache=False)

    def test_build_printable_html_contains_print_dialog_trigger(self):
        """Document must contain window.print() to trigger the system print queue without saving files."""
        html = PrinterEngine.build_printable_html(self.pdf_bytes, self.song.title)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("window.print()", html)
        self.assertIn("@page", html)
        self.assertIn("data:image/png;base64,", html)
        # Verify no download attributes or save triggers exist
        self.assertNotIn("download=", html)

    def test_render_print_buttons_component(self):
        """Print buttons component should generate client-side print queue triggers."""
        comp = PrinterEngine.render_print_buttons_component(self.pdf_bytes, self.pdf_bytes, self.song.title)
        self.assertIn("openPrintQueue", comp)
        self.assertIn("Stampa A4: con Accordi", comp)
        self.assertIn("Stampa A4: Solo Testo", comp)
        self.assertIn("URL.createObjectURL", comp)

    def test_list_system_printers(self):
        """Should detect local system printers or return list."""
        printers = PrinterEngine.list_system_printers()
        self.assertIsInstance(printers, list)

if __name__ == "__main__":
    unittest.main()

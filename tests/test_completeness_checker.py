import unittest
import os
import shutil
import tempfile
from asma_core.completeness_checker import CompletenessChecker
from asma_core.models import Song
from asma_core.storage_manager import StorageManager

class TestCompletenessChecker(unittest.TestCase):

    def test_medley_detection(self):
        """Strict rule 0: Medleys must always be recognized and protected."""
        self.assertTrue(CompletenessChecker.is_medley("MEDLEY ROCK"))
        self.assertTrue(CompletenessChecker.is_medley("medley 80s"))
        self.assertTrue(CompletenessChecker.is_medley("Battisti Medley"))
        self.assertTrue(CompletenessChecker.is_medley("Canzone", "{start_of_medley: Brano 1}"))
        self.assertTrue(CompletenessChecker.is_medley("Canzone", "{sos: Brano 1}"))
        self.assertFalse(CompletenessChecker.is_medley("50 Special", "[DO] Vespe 50 special"))

    def test_sung_lyrics_extraction(self):
        """Extracts sung lyrics and strips chords and directives."""
        aml = """{title: 50 Special}
[INTRO]
[DO] [MIm] [FA] [SOL]
[STROFA]
[DO]Vespe [MIm]truccate [FA]anni [SOL]sessanta
Girano in [DO]centro sfiorando i [SOL]novanta
"""
        sung = CompletenessChecker.extract_sung_lyrics(aml)
        self.assertIn("Vespe", sung)
        self.assertIn("sessanta", sung)
        self.assertNotIn("[DO]", sung)
        self.assertNotIn("[INTRO]", sung)

    def test_clean_autocompleted_tags(self):
        """Cleans [AUTO-COMPLETATO] and [/AUTO-COMPLETATO] delimiters."""
        content = """[STROFA]
Line 1
[AUTO-COMPLETATO]
[MIm]Line added by AI
[/AUTO-COMPLETATO]
Line 3"""
        cleaned = CompletenessChecker.clean_autocompleted_tags(content)
        self.assertNotIn("[AUTO-COMPLETATO]", cleaned)
        self.assertNotIn("[/AUTO-COMPLETATO]", cleaned)
        self.assertIn("[MIm]Line added by AI", cleaned)
        self.assertIn("Line 1", cleaned)

    def test_song_model_and_storage_persistence(self):
        """Verifies new completeness and snapshot fields persist in StorageManager."""
        temp_dir = tempfile.mkdtemp()
        StorageManager._instance = None
        try:
            storage = StorageManager(data_dir=temp_dir)
            song = Song(
                title="TEST SONG COMPLETENESS",
                artist="Test Artist",
                aml_content="[DO]Test content",
                completeness_status="INCOMPLETO",
                completeness_ratio=0.65,
                official_lyrics="Official lyrics full version",
                previous_content="[DO]Original content before AI",
                previous_status="INCOMPLETO"
            )
            saved = storage.save_song(song, user_email="admin@test.com", user_name="Admin")
            loaded = storage.get_song(saved.uuid)
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.completeness_status, "INCOMPLETO")
            self.assertEqual(loaded.completeness_ratio, 0.65)
            self.assertEqual(loaded.official_lyrics, "Official lyrics full version")
            self.assertEqual(loaded.previous_content, "[DO]Original content before AI")
            self.assertEqual(loaded.previous_status, "INCOMPLETO")
        finally:
            StorageManager._instance = None
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_complete_song_with_llm_raises_when_no_api_key(self):
        """Verifies that missing GEMINI_API_KEY raises a descriptive RuntimeError."""
        old_key = os.environ.pop("GEMINI_API_KEY", None)
        try:
            with self.assertRaises(RuntimeError) as ctx:
                CompletenessChecker.complete_song_with_llm(
                    title="Canzone",
                    artist="Artista",
                    key="C",
                    aml_content="[DO]Testo",
                    official_lyrics=""
                )
            self.assertIn("Chiave API Gemini non configurata", str(ctx.exception))
        finally:
            if old_key:
                os.environ["GEMINI_API_KEY"] = old_key

    def test_discover_gemini_models_returns_fallbacks_on_invalid_key(self):
        """Verifies discover_gemini_models returns valid (ver, model) fallbacks if API call fails."""
        models = CompletenessChecker.discover_gemini_models("invalid_mock_key")
        self.assertTrue(len(models) > 0)
        self.assertTrue(any(ver == "v1" for ver, _ in models))
        self.assertTrue(any("flash" in name for _, name in models))

if __name__ == "__main__":
    unittest.main()

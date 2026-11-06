import unittest
from asma_core.ai_service import BandAIService

class TestSongBPMIntegration(unittest.TestCase):
    def test_fetch_songbpm_direct(self):
        # Knock on Wood by Amii Stewart should return 140 BPM from SongBPM
        info = BandAIService.fetch_songbpm_info("Knock On Wood", "Amii Stewart")
        if info:
            self.assertIn("bpm", info)
            self.assertEqual(info["bpm"], 140)
            self.assertEqual(info["source"], "SongBPM.com")

    def test_estimate_bpm_uses_songbpm(self):
        bpm = BandAIService.estimate_song_bpm("Baila Morena", "Zucchero")
        self.assertIsInstance(bpm, int)
        self.assertGreaterEqual(bpm, 40)
        self.assertLessEqual(bpm, 240)

    def test_suggest_arrangement_ideas_uses_songbpm(self):
        advice = BandAIService.suggest_arrangement_ideas(
            title="Knock On Wood",
            genre="Disco / Funk",
            key="D",
            bpm=0,
            artist="Amii Stewart"
        )
        self.assertIn("SongBPM: 140 BPM", advice)
        self.assertIn("140 BPM da SongBPM", advice)
        self.assertNotIn("120 BPM", advice)

if __name__ == "__main__":
    unittest.main()

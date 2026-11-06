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

if __name__ == "__main__":
    unittest.main()

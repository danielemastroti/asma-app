import unittest
from asma_core.music_engine import MusicEngine
from asma_core.ai_service import BandAIService


class TestKeyDetectorAndHarmonicAnalysis(unittest.TestCase):
    def test_detect_mim_vs_sol_lo_spettacolo(self):
        # Chords from 'Lo Spettacolo': starts on MIm, diatonic to SOL / MIm (degree 6)
        chords = ['MIm', 'SOL', 'RE', 'MIm', 'SOL', 'RE', 'LAm', 'MIm', 'DO', 'RE']
        res = MusicEngine.detect_probable_key(chords, current_hint="MI")
        self.assertEqual(res["probable_key"], "MIm")
        self.assertEqual(res["relative_key"], "SOL")
        self.assertEqual(res["mode"], "Minore")
        self.assertIn("6° grado di SOL", res["relationship"])

    def test_detect_mim_venus(self):
        # Chords from 'Venus': MIm, LA, LAm, RE
        chords = ['MIm', 'LA', 'MIm', 'LA', 'MIm', 'LA', 'LAm', 'RE']
        res = MusicEngine.detect_probable_key(chords, current_hint="SI")
        self.assertEqual(res["probable_key"], "MIm")
        self.assertEqual(res["mode"], "Minore")

    def test_detect_solm_hot_stuff(self):
        # Chords from 'Hot Stuff': SOLm, FA, MIb, FA
        chords = ['SOLm', 'FA', 'MIb', 'FA', 'SOLm', 'FA', 'MIb', 'RE7']
        res = MusicEngine.detect_probable_key(chords, current_hint="SOL")
        self.assertEqual(res["probable_key"], "SOLm")
        self.assertEqual(res["mode"], "Minore")

    def test_detect_major_im_a_believer(self):
        # Chords from 'I'm a Believer': SOL, RE, SOL, DO
        chords = ['SOL', 'RE', 'SOL', 'SOL', 'RE', 'SOL', 'DO', 'SOL']
        res = MusicEngine.detect_probable_key(chords, current_hint="SOL")
        self.assertEqual(res["probable_key"], "SOL")
        self.assertEqual(res["relative_key"], "MIm")
        self.assertEqual(res["mode"], "Maggiore")

    def test_detect_sweet_home_chicago_blues(self):
        # MI7, LA7, SI7 (Blues in E)
        chords = ['MI7', 'LA7', 'MI7', 'SI7', 'LA7', 'MI7']
        res = MusicEngine.detect_probable_key(chords, current_hint="MI")
        self.assertEqual(res["probable_key"], "MI")
        self.assertEqual(res["mode"], "Maggiore")

    def test_ai_fallback_service(self):
        chords = ['MIm', 'SOL', 'RE', 'MIm']
        res = BandAIService.analyze_probable_key_with_ai_fallback("Lo Spettacolo", "Litfiba", chords, "MI")
        self.assertEqual(res["probable_key"], "MIm")


if __name__ == '__main__':
    unittest.main()

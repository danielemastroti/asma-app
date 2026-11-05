"""
Unit and Regression Tests for Music Engine
Conforms to SRS Cap. 8, Cap. 17.5-17.9 and Blueprint Sec. 6.
Zero-AI Mathematical Verification Suite.
"""

import unittest
from asma_core.music_engine import MusicEngine, ParsedChord


class TestMusicEngine(unittest.TestCase):

    def test_parse_simple_chords(self):
        """Test parsing international basic chords."""
        for note in ["C", "D", "E", "F", "G", "A", "B"]:
            p = MusicEngine.parse_chord(note)
            self.assertIsNotNone(p)
            self.assertEqual(p.raw_root, note)
            self.assertFalse(p.is_italian)

    def test_parse_italian_chords(self):
        """Test parsing Italian solfège chords."""
        ita_notes = ["DO", "RE", "MI", "FA", "SOL", "LA", "SI"]
        for note in ita_notes:
            p = MusicEngine.parse_chord(note)
            self.assertIsNotNone(p)
            self.assertEqual(p.raw_root, note)
            self.assertTrue(p.is_italian)

    def test_parse_complex_and_extended_chords(self):
        """Test parsing complex chords with tensions, suspensions, and alterations."""
        test_cases = [
            ("Cmaj7", "C", "", "maj7"),
            ("Cm7", "C", "", "m7"),
            ("Csus4", "C", "", "sus4"),
            ("Cadd9", "C", "", "add9"),
            ("Cdim", "C", "", "dim"),
            ("Caug", "C", "", "aug"),
            ("Cm7b5", "C", "", "m7b5"),
            ("Bbmaj7", "B", "b", "maj7"),
            ("F#sus4", "F", "#", "sus4"),
            ("DO7+", "DO", "", "7+"),
            ("LA-", "LA", "", "-"),
            ("SIb", "SI", "b", ""),
            ("DO+", "DO", "", "+"),
            ("REsus4", "RE", "", "sus4")
        ]
        for chord_str, expected_root, expected_acc, expected_qual in test_cases:
            p = MusicEngine.parse_chord(chord_str)
            self.assertIsNotNone(p, f"Failed to parse '{chord_str}'")
            self.assertEqual(p.raw_root, expected_root)
            self.assertEqual(p.accidental, expected_acc)
            self.assertEqual(p.quality_and_extension, expected_qual)

    def test_slash_chords(self):
        """Test parsing chords with custom bass notes."""
        p = MusicEngine.parse_chord("C/E")
        self.assertIsNotNone(p)
        self.assertEqual(p.raw_root, "C")
        self.assertEqual(p.raw_bass, "E")

        p_ita = MusicEngine.parse_chord("SOLm/SIb")
        self.assertIsNotNone(p_ita)
        self.assertEqual(p_ita.raw_root, "SOL")
        self.assertEqual(p_ita.raw_bass, "SI")
        self.assertEqual(p_ita.bass_accidental, "b")

    def test_all_twelve_chromatic_transpositions(self):
        """Validates all 12 chromatic intervals from -12 to +12."""
        root = "C"
        expected_sharps = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        for delta in range(12):
            transposed = MusicEngine.transpose_chord(root, semitones=delta, prefer_flats=False)
            self.assertEqual(transposed, expected_sharps[delta])

        # Test negative semitones
        self.assertEqual(MusicEngine.transpose_chord("C", semitones=-1, prefer_flats=False), "B")
        self.assertEqual(MusicEngine.transpose_chord("C", semitones=-2, prefer_flats=True), "Bb")

    def test_italian_notation_transposition(self):
        """SRS Cap. 8.3 & 17.7: DO -> RE (+2), SOL -> LA (+2), Am -> Bm (+2)."""
        self.assertEqual(MusicEngine.transpose_chord("DO", semitones=2), "RE")
        self.assertEqual(MusicEngine.transpose_chord("SOL", semitones=2), "LA")
        self.assertEqual(MusicEngine.transpose_chord("Am", semitones=2), "Bm")
        self.assertEqual(MusicEngine.transpose_chord("LA-", semitones=2), "SIm")
        self.assertEqual(MusicEngine.transpose_chord("DO7+", semitones=2), "REmaj7")

    def test_slash_chord_transposition(self):
        """Verifies both root and bass note transpose by the exact same interval."""
        # D/F# transposed +2 semitones -> E/G#
        self.assertEqual(MusicEngine.transpose_chord("D/F#", semitones=2, prefer_flats=False), "E/G#")
        # DO/MI transposed +2 semitones -> RE/FA#
        self.assertEqual(MusicEngine.transpose_chord("DO/MI", semitones=2, prefer_flats=False), "RE/FA#")

    def test_bidirectional_notation_conversion(self):
        """SRS Cap. 8.3: DO <-> C, RE <-> D, LA- <-> Am."""
        self.assertEqual(MusicEngine.convert_notation("DO", to_system="INT"), "C")
        self.assertEqual(MusicEngine.convert_notation("C", to_system="ITA"), "DO")
        self.assertEqual(MusicEngine.convert_notation("LA-", to_system="INT"), "Am")
        self.assertEqual(MusicEngine.convert_notation("Am", to_system="ITA"), "LAm")
        self.assertEqual(MusicEngine.convert_notation("DO7+", to_system="INT"), "Cmaj7")

    def test_harmonic_compatibility_for_medleys(self):
        """SRS Cap. 11.6: Calculate medley affinity by circle of fifths and tempo."""
        # Same key, identical BPM -> Score 1.0 (perfect fit)
        score_exact, details_exact = MusicEngine.calculate_harmonic_compatibility("C", 120, "C", 120)
        self.assertEqual(score_exact, 1.0)
        self.assertEqual(details_exact["fifths_distance"], 0)

        # Dominant key (C to G, dist 1), BPM 120 to 125 (delta < 5%) -> High compatibility
        score_dom, details_dom = MusicEngine.calculate_harmonic_compatibility("C", 120, "G", 125)
        self.assertGreaterEqual(score_dom, 0.80)

        # Distant key (C to F#, dist 6 tritone), BPM 120 to 80 (delta > 30%) -> Incompatible
        score_distant, details_distant = MusicEngine.calculate_harmonic_compatibility("C", 120, "F#", 80)
        self.assertLess(score_distant, 0.3)

    def test_harmonic_progression_recognition(self):
        """SRS Cap. 8.8: Recognizes 'DO LA- FA SOL' or 'C Am F G' as classic progression."""
        prog_int = ["C", "Am", "F", "G"]
        res_int = MusicEngine.identify_progression(prog_int)
        self.assertTrue(res_int["is_progression"])
        self.assertIn("Giro di DO", res_int["description"])

        prog_ita = ["DO", "LA-", "FA", "SOL"]
        res_ita = MusicEngine.identify_progression(prog_ita)
        self.assertTrue(res_ita["is_progression"])
        self.assertIn("Giro di DO", res_ita["description"])

    def test_full_octave_transpositions_return_identical_pitch(self):
        """Transposing +12 or -12 semitones must return the exact same pitch class."""
        for chord in ["C", "F#m7", "Bbmaj7", "DO7+", "LAm", "SOL#sus4"]:
            plus_12 = MusicEngine.transpose_chord(chord, semitones=12)
            minus_12 = MusicEngine.transpose_chord(chord, semitones=-12)
            # Verify parsed pitch class is identical
            p_orig = MusicEngine.parse_chord(chord)
            p_plus = MusicEngine.parse_chord(plus_12)
            p_minus = MusicEngine.parse_chord(minus_12)
            self.assertEqual(p_orig.pitch_class, p_plus.pitch_class)
            self.assertEqual(p_orig.pitch_class, p_minus.pitch_class)

    def test_semitone_delta_calculation(self):
        """Tests delta calculation between keys."""
        # C to D -> +2
        self.assertEqual(MusicEngine.calculate_semitone_delta("C", "D"), 2)
        # C to B -> -1
        self.assertEqual(MusicEngine.calculate_semitone_delta("C", "B"), -1)
        # DO to FA -> +5
        self.assertEqual(MusicEngine.calculate_semitone_delta("DO", "FA"), 5)


if __name__ == "__main__":
    unittest.main()

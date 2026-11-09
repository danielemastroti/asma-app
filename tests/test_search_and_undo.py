import unittest
from asma_core.storage_manager import StorageManager
from asma_core.music_engine import MusicEngine
from asma_core.aml_parser import AMLParser
from asma_core.models import Song

class TestSearchAndUndo(unittest.TestCase):
    def setUp(self):
        self.sm = StorageManager()

    def test_search_songs_by_italian_key(self):
        # Searching by Italian key 'SOL' or 'DO' finds songs
        res_sol = self.sm.search_songs(key="SOL")
        self.assertIsInstance(res_sol, list)
        self.assertGreater(len(res_sol), 0)
        # All found songs have key SOL or G
        for r in res_sol:
            ita_curr = MusicEngine.convert_notation(r["key_current"], "ITA")
            ita_orig = MusicEngine.convert_notation(r["key_original"], "ITA")
            self.assertTrue(ita_curr == "SOL" or ita_orig == "SOL")

    def test_transposition_undo_returns_to_original_key(self):
        # Create a song in DO
        song = Song(title="Test Undo", key_original="DO", key_current="DO", aml_content="{title: Test Undo}\n{key: DO}\n\n[DO]Testo [SOL]Accordi")
        
        # Transpose +1 semitone to DO#
        doc = AMLParser.parse(song.aml_content)
        transposed_doc = AMLParser.transpose_document(doc, semitones=1)
        song.aml_content = transposed_doc.to_aml()
        song.key_current = MusicEngine.transpose_chord(song.key_current, semitones=1)
        self.assertEqual(song.key_current, "DO#")
        
        # Transpose +1 semitone to RE
        transposed_doc2 = AMLParser.transpose_document(AMLParser.parse(song.aml_content), semitones=1)
        song.aml_content = transposed_doc2.to_aml()
        song.key_current = MusicEngine.transpose_chord(song.key_current, semitones=1)
        self.assertEqual(song.key_current, "RE")

        # Now execute Undo back to original key (DO)
        delta = MusicEngine.calculate_semitone_delta(song.key_current, song.key_original)
        self.assertEqual(delta, -2) # RE to DO is -2 semitones
        undo_doc = AMLParser.transpose_document(AMLParser.parse(song.aml_content), semitones=delta)
        song.aml_content = undo_doc.to_aml()
        song.key_current = song.key_original

        self.assertEqual(song.key_current, "DO")
        self.assertIn("[DO]Testo", song.aml_content)
        self.assertIn("[SOL]Accordi", song.aml_content)

if __name__ == "__main__":
    unittest.main()

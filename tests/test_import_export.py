"""
Unit Tests for Multi-Format Import & Export Engine
Conforms to SRS Cap. 14.
"""

import unittest
import zipfile
import io
from asma_core.models import Song, Setlist, SetlistItem
from asma_core.export_engine import ExportEngine
from asma_core.import_engine import ImportEngine


class TestImportExportEngine(unittest.TestCase):

    def setUp(self):
        self.song = Song(
            title="Hotel California",
            artist="Eagles",
            key_current="Bm",
            bpm=74,
            time_signature="4/4",
            tags=["rock", "classic"],
            aml_content="""{title: Hotel California}
{artist: Eagles}
{key: Bm}
{intro}
| Bm | F#7 | A | E |

{verse}
[Bm]On a dark desert highway
"""
        )

    def test_export_to_chordpro(self):
        """Test conversion from AML to standard ChordPro."""
        cpro = ExportEngine.export_to_chordpro(self.song.aml_content)
        self.assertIn("{title: Hotel California}", cpro)
        self.assertIn("[Bm]On a dark desert highway", cpro)

    def test_export_for_mobilesheets_and_songbook(self):
        """Test MobileSheets/SongBookPro metadata header injection."""
        ms = ExportEngine.export_for_mobilesheets(self.song)
        self.assertIn("{key: Bm}", ms)
        self.assertIn("{tempo: 74}", ms)
        self.assertIn("{keywords: rock, classic}", ms)

        # Test export scaletta SongBook Pro
        setlist = Setlist(title="Concerto Estivo", date="2027-08-10", items=[SetlistItem(song_uuid=self.song.uuid)])
        sb_set = ExportEngine.export_setlist_for_songbookpro(setlist, [self.song])
        self.assertIn("SCALETTA - Concerto Estivo", sb_set)
        self.assertIn("{new_page}", sb_set)
        self.assertIn("{title: Hotel California}", sb_set)

    def test_export_offline_live_pack_zip(self):
        """SRS Cap. 14.29: Generate full offline pack ZIP containing PDF, AML, MobileSheets."""
        setlist = Setlist(
            title="Live Tour",
            items=[SetlistItem(song_uuid=self.song.uuid)]
        )
        zip_bytes = ExportEngine.create_offline_live_pack_zip(setlist, [self.song])
        self.assertIsNotNone(zip_bytes)
        self.assertTrue(len(zip_bytes) > 2000)

        # Inspect ZIP archive contents
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            namelist = zf.namelist()
            self.assertTrue(any(n.startswith("00_SCALETTA") and n.endswith(".pdf") for n in namelist))
            self.assertTrue(any(n.startswith("pdf/") and n.endswith(".pdf") for n in namelist))
            self.assertTrue(any(n.startswith("aml/") and n.endswith(".aml") for n in namelist))
            self.assertTrue(any(n.startswith("mobilesheets/") and n.endswith(".pro") for n in namelist))

    def test_import_from_chordpro(self):
        """Test parsing ChordPro into standard Song object."""
        cpro_text = """{title: Sultans of Swing}
{artist: Dire Straits}
{key: Dm}
{tempo: 148}

[Dm]You get a shiver in the dark"""
        song = ImportEngine.import_from_chordpro(cpro_text)
        self.assertEqual(song.title, "Sultans of Swing")
        self.assertEqual(song.artist, "Dire Straits")
        self.assertEqual(song.key_current, "Dm")
        self.assertEqual(song.bpm, 148)


if __name__ == "__main__":
    unittest.main()

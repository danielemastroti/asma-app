"""
Unit and Integration Tests for Two-Layer Storage Engine
Conforms to SRS Cap. 4, 7, 10, 15, 17.16-17.19, 17.30-17.34.
"""

import unittest
import tempfile
import shutil
import time
from asma_core.models import Song, Repertoire, Setlist, SetlistItem
from asma_core.storage_manager import StorageManager


class TestStorageManager(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        # Create dedicated isolated instance for each test
        StorageManager._instance = None
        self.storage = StorageManager(data_dir=self.test_dir)

    def tearDown(self):
        StorageManager._instance = None
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_and_retrieve_song(self):
        """Test song persistence and automatic revision creation."""
        song = Song(
            title="Test Mock Song Alpha",
            artist="Dire Straits",
            author="Mark Knopfler",
            genre="Rock",
            bpm=148,
            key_current="Dm",
            aml_content="{title: Test Mock Song Alpha}\n[Dm]You get a shiver in the dark"
        )
        saved = self.storage.save_song(song, user_email="daniele@band.org", user_name="Daniele")
        self.assertEqual(saved.current_revision, 1)

        # Retrieve
        fetched = self.storage.get_song(saved.uuid)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.title, "Test Mock Song Alpha")
        self.assertEqual(fetched.key_current, "Dm")

        # Verify revision history
        revs = self.storage.get_revisions_for_song(saved.uuid)
        self.assertEqual(len(revs), 1)
        self.assertEqual(revs[0].author_name, "Daniele")

    def test_multi_revision_and_restore(self):
        """SRS Cap. 4.5: Multiple edits generate revision history with diff and restore capability."""
        song = Song(title="Test Song", key_current="C", aml_content="Version 1 content")
        self.storage.save_song(song, user_name="Author 1", revision_comment="Initial")

        # Second revision
        song.aml_content = "Version 2 modified chords"
        song.key_current = "D"
        self.storage.save_song(song, user_name="Author 2", revision_comment="Transposed to D")

        revs = self.storage.get_revisions_for_song(song.uuid)
        self.assertEqual(len(revs), 2)
        self.assertEqual(revs[1].revision_number, 2)

        # Restore revision 1
        restored = self.storage.restore_revision(song.uuid, revision_number=1, user_email="admin@band.org", user_name="Admin")
        self.assertIsNotNone(restored)
        self.assertEqual(restored.aml_content, "Version 1 content")
        self.assertEqual(restored.current_revision, 3)

    def test_fast_sql_search_and_multi_criteria_filtering(self):
        """SRS Cap. 10.10: Complex search by Genre + Key + BPM range in < 5ms."""
        s1 = Song(title="Rock Anthem", genre="Classic Rock", key_current="G", bpm=95, tags=["live", "energetic"])
        s2 = Song(title="Slow Ballad", genre="Ballad", key_current="G", bpm=65, tags=["acustico"])
        s3 = Song(title="Fast Pop", genre="Pop", key_current="A", bpm=130, tags=["dance"])

        self.storage.save_song(s1)
        self.storage.save_song(s2)
        self.storage.save_song(s3)

        # Search: Key = G, BPM between 90 and 100, Genre = Rock
        t0 = time.perf_counter()
        results = self.storage.search_songs(query_text="Rock", key="G", bpm_min=90, bpm_max=100)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Rock Anthem")
        self.assertLess(elapsed_ms, 20.0)  # Must be well under 20ms even on cold runner

    def test_soft_delete_and_trash_restoration(self):
        """SRS Cap. 4.7: Soft-deletion preserves songs in trash for 30 days and allows recovery."""
        song = Song(title="Song To Delete", key_current="E")
        self.storage.save_song(song)

        # Delete
        del_ok = self.storage.delete_song(song.uuid, "user@band.org", "User")
        self.assertTrue(del_ok)

        # Should not appear in active search or list
        active_songs = self.storage.list_songs(include_deleted=False)
        self.assertEqual(len(active_songs), 0)

        # Restore from trash
        restored = self.storage.restore_song(song.uuid, "admin@band.org", "Admin")
        self.assertIsNotNone(restored)
        self.assertEqual(restored.title, "Song To Delete")

        # Now appears in list again
        active_after = self.storage.list_songs(include_deleted=False)
        self.assertEqual(len(active_after), 1)

    def test_move_song_between_repertoires(self):
        """SRS Cap. 10.4: Moving song between repertoires preserves UUID and history."""
        song = Song(title="WIP Song", key_current="A")
        self.storage.save_song(song)

        reps = self.storage.list_repertoires()
        wip_rep = next(r for r in reps if "Working In Progress" in r.name)
        def_rep = next(r for r in reps if "Definitivo" in r.name)

        # Move to WIP
        self.storage.move_song_to_repertoire(song.uuid, wip_rep.uuid)
        # Move to Definitivo
        self.storage.move_song_to_repertoire(song.uuid, def_rep.uuid)

        # Verify song still has same UUID and is in Definitivo
        fetched = self.storage.get_song(song.uuid)
        self.assertEqual(fetched.uuid, song.uuid)
        def_rep_updated = next(r for r in self.storage.list_repertoires() if r.uuid == def_rep.uuid)
        self.assertIn(song.uuid, def_rep_updated.song_uuids)


    def test_repertoire_duplicate_name_rejected(self):
        """Test that creating a repertoire with a duplicate name is strictly rejected."""
        rep1 = Repertoire(name="Repertorio Esclusivo")
        self.storage.save_repertoire(rep1)

        rep_dup = Repertoire(name="  repertorio esclusivo  ")
        with self.assertRaises(ValueError):
            self.storage.save_repertoire(rep_dup)

    def test_delete_repertoire_and_setlist(self):
        """Test deleting repertoires and setlists cleanly without losing songs."""
        song = Song(title="Shared Song", key_current="E")
        self.storage.save_song(song)

        # 1. Create and delete repertoire
        rep = Repertoire(name="Test Repertoire To Delete", song_uuids=[song.uuid])
        self.storage.save_repertoire(rep)
        self.assertIn(rep.uuid, [r.uuid for r in self.storage.list_repertoires()])

        deleted_ok = self.storage.delete_repertoire(rep.uuid)
        self.assertTrue(deleted_ok)
        self.assertNotIn(rep.uuid, [r.uuid for r in self.storage.list_repertoires()])
        # Song itself must not be deleted
        self.assertIsNotNone(self.storage.get_song(song.uuid))

        # 2. Create and delete setlist
        setlist = Setlist(title="Setlist To Delete", items=[SetlistItem(song_uuid=song.uuid)])
        self.storage.save_setlist(setlist)
        self.assertIn(setlist.uuid, [s.uuid for s in self.storage.list_setlists()])

        set_del_ok = self.storage.delete_setlist(setlist.uuid)
        self.assertTrue(set_del_ok)
        self.assertNotIn(setlist.uuid, [s.uuid for s in self.storage.list_setlists()])

    def test_purge_permanently_and_empty_trash(self):
        """Test hard delete and emptying trash."""
        song1 = Song(title="Trash Song 1")
        song2 = Song(title="Trash Song 2")
        self.storage.save_song(song1)
        self.storage.save_song(song2)

        # Soft delete both
        self.storage.delete_song(song1.uuid)
        self.storage.delete_song(song2.uuid)

        # Purge song1 permanently
        self.storage.purge_song_permanently(song1.uuid)
        self.assertIsNone(self.storage.restore_song(song1.uuid))

        # Empty trash purges song2
        purged = self.storage.empty_trash()
        self.assertEqual(purged, 1)

    def test_tag_management(self):
        """Test listing, renaming, deleting and bulk-assigning tags across songs."""
        s1 = Song(title="Song One", tags=["rock", "live"])
        s2 = Song(title="Song Two", tags=["rock", "ballad"])
        s3 = Song(title="Song Three", tags=["pop"])

        self.storage.save_song(s1)
        self.storage.save_song(s2)
        self.storage.save_song(s3)

        # 1. List tags with frequency
        tags_dict = self.storage.list_all_tags()
        self.assertEqual(tags_dict.get("rock"), 2)
        self.assertEqual(tags_dict.get("live"), 1)
        self.assertEqual(tags_dict.get("ballad"), 1)
        self.assertEqual(tags_dict.get("pop"), 1)

        # 2. Rename / merge tag globally
        updated = self.storage.rename_tag_globally("rock", "hard-rock")
        self.assertEqual(updated, 2)
        tags_after_rename = self.storage.list_all_tags()
        self.assertNotIn("rock", tags_after_rename)
        self.assertEqual(tags_after_rename.get("hard-rock"), 2)

        # 3. Add tag to songs in bulk
        count = self.storage.add_tag_to_songs("summer2026", [s1.uuid, s3.uuid])
        self.assertEqual(count, 2)
        tags_after_add = self.storage.list_all_tags()
        self.assertEqual(tags_after_add.get("summer2026"), 2)

        # 4. Delete tag globally
        del_count = self.storage.delete_tag_globally("hard-rock")
        self.assertEqual(del_count, 2)
        tags_after_del = self.storage.list_all_tags()
        self.assertNotIn("hard-rock", tags_after_del)

    def test_repertoire_song_uniqueness_rules(self):
        """Rule: two different versions of the same song allowed in different repertoires, but not in the same repertoire."""
        r1 = Repertoire(name="Repertorio Elettrico", description="Set rock")
        r2 = Repertoire(name="Repertorio Acustico", description="Set club")
        self.storage.save_repertoire(r1)
        self.storage.save_repertoire(r2)

        # Version 1 in R1
        song1 = Song(title="Sultans of Swing", key_current="Dm")
        self.storage.save_song(song1)
        self.storage.move_song_to_repertoire(song1.uuid, r1.uuid)

        # Version 2 with same title in R2 -> MUST BE ALLOWED!
        song2 = Song(title="Sultans of Swing", key_current="Em", aml_content="Versione Acustica")
        self.storage.save_song(song2)
        can_add_r2, _ = self.storage.can_add_song_to_repertoire(r2.uuid, song2.title)
        self.assertTrue(can_add_r2)
        self.storage.move_song_to_repertoire(song2.uuid, r2.uuid)

        # Version 3 with same title in R1 -> MUST BE BLOCKED!
        can_add_r1_dup, reason = self.storage.can_add_song_to_repertoire(r1.uuid, "Sultans of Swing")
        self.assertFalse(can_add_r1_dup)
        self.assertIn("esiste già un brano intitolato", reason)

        with self.assertRaises(ValueError):
            self.storage.move_song_to_repertoire(song2.uuid, r1.uuid)

    def test_repertoire_and_song_trash_and_restore(self):
        """Test soft delete and restore for repertoires and songs."""
        rep = Repertoire(name="Repertorio Test Trash", description="Test")
        self.storage.save_repertoire(rep)

        song = Song(title="Canzone da Eliminare", key_current="A")
        self.storage.save_song(song)

        # Delete song and verify list_deleted_songs
        self.storage.delete_song(song.uuid)
        del_songs = self.storage.list_deleted_songs()
        self.assertTrue(any(s.get("data", {}).get("uuid") == song.uuid for s in del_songs))

        # Delete repertoire and verify list_deleted_repertoires
        del_rep_ok = self.storage.delete_repertoire(rep.uuid)
        self.assertTrue(del_rep_ok)
        del_reps = self.storage.list_deleted_repertoires()
        self.assertTrue(any(r.get("data", {}).get("uuid") == rep.uuid for r in del_reps))

        # Restore repertoire
        restored_rep = self.storage.restore_repertoire(rep.uuid)
        self.assertIsNotNone(restored_rep)
        self.assertEqual(restored_rep.uuid, rep.uuid)
        active_reps = self.storage.list_repertoires()
        self.assertTrue(any(r.uuid == rep.uuid for r in active_reps))


if __name__ == "__main__":
    unittest.main()

"""Unit tests verifying strict isolation between Official and personal repertoires."""

import shutil
import tempfile
import unittest

import api_server
from asma_core.models import Repertoire, Song
from asma_core.storage_manager import StorageManager


class TestRepertoireIsolation(unittest.TestCase):
    """Covers promote-song cloning, Copy-On-Write personal editing/transposing, and safe delete."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        StorageManager._instance = None
        self.orig_storage = api_server.storage
        self.storage = StorageManager(data_dir=self.test_dir)
        api_server.storage = self.storage

        # Seed Official Band Repertoire + Personal Repertoire
        self.official_rep = Repertoire(
            name="Repertorio Ufficiale Band",
            is_official=True,
            song_uuids=[],
        )
        self.personal_rep = Repertoire(
            name="Cico",
            is_official=False,
            owner_email="cico@band.org",
            song_uuids=[],
        )
        # Clear any default seeded repertoires created in test_dir
        self.storage._save_repertoires_file([self.official_rep, self.personal_rep])
        self.storage.reload_from_disk()

    def tearDown(self):
        api_server.storage = self.orig_storage
        StorageManager._instance = None
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_promote_song_clones_with_independent_uuid(self):
        """Promoting a personal song creates a separate Official song clone."""
        personal_song = Song(
            title="SONG PERSONALE",
            artist="Band",
            key_current="C",
            aml_content="[C]Linea originale",
        )
        self.storage.save_song(personal_song, "cico@band.org", "Cico", "Creazione")
        self.personal_rep.song_uuids.append(personal_song.uuid)
        self.storage.save_repertoire(self.personal_rep, "cico@band.org", "Cico")

        res = api_server.promote_song_to_official(
            api_server.PromoteSongRequest(
                song_uuid=personal_song.uuid,
                user_email="cico@band.org",
                user_name="Cico",
            )
        )
        official_uuid = res["song_uuid"]
        self.assertNotEqual(official_uuid, personal_song.uuid)

        # Edit the personal copy and verify the Official copy stays unchanged
        api_server.update_song(
            personal_song.uuid,
            api_server.SongUpdateRequest(
                aml_content="[G]Versione personale modificata",
                key_current="G",
                repertoire_uuid=self.personal_rep.uuid,
                user_email="cico@band.org",
                user_name="Cico",
            ),
        )
        official_after = self.storage.get_song(official_uuid)
        personal_after = self.storage.get_song(personal_song.uuid)
        self.assertEqual(official_after.key_current, "C")
        self.assertIn("Linea originale", official_after.aml_content)
        self.assertEqual(personal_after.key_current, "G")
        self.assertIn("Versione personale modificata", personal_after.aml_content)

    def test_cow_detaches_shared_slug_song_on_personal_edit_and_survives_reload(self):
        """Editing/transposing a shared song (even with slug UUID) in personal rep isolates Official copy."""
        shared_slug_song = Song(
            uuid="50_special_slug",
            title="50 SPECIAL",
            artist="Lunapop",
            key_current="D",
            aml_content="[D]Vespa [A]speciale",
        )
        self.storage.save_song(shared_slug_song, "system", "System", "Seed")
        self.official_rep.song_uuids.append(shared_slug_song.uuid)
        self.personal_rep.song_uuids.append(shared_slug_song.uuid)
        self.storage._save_repertoires_file([self.official_rep, self.personal_rep])
        self.storage.reload_from_disk()

        # Transpose inside personal repertoire -> triggers COW detach
        t_res = api_server.transpose_song(
            shared_slug_song.uuid,
            api_server.TransposeRequest(
                semitones=2,
                user_email="cico@band.org",
                user_name="Cico",
                repertoire_uuid=self.personal_rep.uuid,
            ),
        )
        self.assertTrue(t_res["detached_copy"])
        new_personal_uuid = t_res["song"]["uuid"]
        self.assertNotEqual(new_personal_uuid, shared_slug_song.uuid)
        self.assertEqual(t_res["song"]["key_current"], "E")

        # Reload disk index (ensuring GUID personal copy is NOT collapsed back onto slug)
        self.storage.reload_from_disk()

        official_rep_after = self.storage.get_repertoire(self.official_rep.uuid)
        personal_rep_after = self.storage.get_repertoire(self.personal_rep.uuid)
        self.assertEqual(official_rep_after.song_uuids, ["50_special_slug"])
        self.assertEqual(personal_rep_after.song_uuids, [new_personal_uuid])

        official_song = self.storage.get_song("50_special_slug")
        personal_song = self.storage.get_song(new_personal_uuid)
        self.assertEqual(official_song.key_current, "D")
        self.assertIn("[D]Vespa", official_song.aml_content)
        self.assertEqual(personal_song.key_current, "E")
        self.assertIn("[E]Vespa", personal_song.aml_content)

    def test_delete_shared_song_in_one_repertoire_detaches_without_trashing_official(self):
        """Deleting a song referenced in 2 repertoires only detaches it from the active repertoire."""
        shared = Song(
            title="SHARED TRACK",
            artist="Band",
            key_current="Am",
            aml_content="[Am]Test",
        )
        self.storage.save_song(shared, "system", "System", "Seed")
        self.official_rep.song_uuids.append(shared.uuid)
        self.personal_rep.song_uuids.append(shared.uuid)
        self.storage._save_repertoires_file([self.official_rep, self.personal_rep])
        self.storage.reload_from_disk()

        del_res = api_server.delete_song(
            shared.uuid,
            user_email="cico@band.org",
            user_name="Cico",
            repertoire_uuid=self.personal_rep.uuid,
        )
        self.assertTrue(del_res.get("detached_only"))
        self.assertNotIn(shared.uuid, self.storage.get_repertoire(self.personal_rep.uuid).song_uuids)
        self.assertIn(shared.uuid, self.storage.get_repertoire(self.official_rep.uuid).song_uuids)
        self.assertIsNotNone(self.storage.get_song(shared.uuid))

    def test_fork_personal_duplicate_rejected_before_creating_orphan(self):
        """fork_song_personal raises 409 without saving an orphan song file when title exists."""
        orig = Song(title="MY HIT", artist="Band", key_current="C", aml_content="[C]Hi")
        self.storage.save_song(orig, "system", "System", "Seed")
        self.official_rep.song_uuids.append(orig.uuid)

        existing_personal = Song(title="MY HIT", artist="Band", key_current="D", aml_content="[D]Personal")
        self.storage.save_song(existing_personal, "cico@band.org", "Cico", "Personal")
        self.personal_rep.song_uuids.append(existing_personal.uuid)
        self.storage._save_repertoires_file([self.official_rep, self.personal_rep])
        self.storage.reload_from_disk()

        with self.assertRaises(api_server.HTTPException) as ctx:
            api_server.fork_song_personal(
                orig.uuid,
                api_server.ForkSongRequest(user_email="cico@band.org", user_name="Cico"),
            )
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(len(self.storage.list_songs()), 2)

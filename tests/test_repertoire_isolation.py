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

    def test_promote_new_song_moves_from_personal_to_official(self):
        """Promoting a brand-new personal song moves it out of personal rep into Official."""
        personal_song = Song(
            title="SONG NUOVA PERSONALE",
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
        self.assertEqual(res["action"], "moved")
        self.assertEqual(res["song_uuid"], personal_song.uuid)
        self.assertIn(personal_song.uuid, self.storage.get_repertoire(self.official_rep.uuid).song_uuids)
        self.assertNotIn(personal_song.uuid, self.storage.get_repertoire(self.personal_rep.uuid).song_uuids)

    def test_promote_existing_song_overwrites_official_and_deletes_personal_and_allows_refork(self):
        """Promoting a personal copy of an Official song overwrites Official, deletes personal, and allows re-forking."""
        official_song = Song(
            uuid="official_song_123",
            title="CANZONE BAND",
            artist="Band",
            bpm=110,
            key_current="C",
            aml_content="[C]Versione ufficiale vecchia",
        )
        self.storage.save_song(official_song, "system", "System", "Seed")
        self.official_rep.song_uuids.append(official_song.uuid)
        self.storage._save_repertoires_file([self.official_rep, self.personal_rep])
        self.storage.reload_from_disk()

        # 1. User creates personal copy & edits it without touching Official
        fork_res = api_server.fork_song_personal(
            official_song.uuid,
            api_server.ForkSongRequest(user_email="cico@band.org", user_name="Cico"),
        )
        personal_uuid = fork_res["cloned_song"]["uuid"]
        self.assertNotEqual(personal_uuid, official_song.uuid)

        api_server.update_song(
            personal_uuid,
            api_server.SongUpdateRequest(
                bpm=128,
                key_current="D",
                aml_content="[D]Versione personale perfezionata",
                repertoire_uuid=self.personal_rep.uuid,
                user_email="cico@band.org",
                user_name="Cico",
            ),
        )
        self.assertEqual(self.storage.get_song(official_song.uuid).key_current, "C")

        # 2. Promote personal copy -> overwrites Official (preserving Official UUID) and deletes personal copy
        promo_res = api_server.promote_song_to_official(
            api_server.PromoteSongRequest(
                song_uuid=personal_uuid,
                user_email="cico@band.org",
                user_name="Cico",
            )
        )
        self.assertEqual(promo_res["action"], "overwritten")
        self.assertEqual(promo_res["song_uuid"], official_song.uuid)

        official_after = self.storage.get_song(official_song.uuid)
        self.assertEqual(official_after.bpm, 128)
        self.assertEqual(official_after.key_current, "D")
        self.assertIn("Versione personale perfezionata", official_after.aml_content)
        self.assertEqual(official_after.shared_notes, "")

        self.assertIsNone(self.storage.get_song(personal_uuid))
        self.assertNotIn(personal_uuid, self.storage.get_repertoire(self.personal_rep.uuid).song_uuids)
        self.assertIn(official_song.uuid, self.storage.get_repertoire(self.official_rep.uuid).song_uuids)

        # 3. User can re-fork from Official again for subsequent edits
        refork_res = api_server.fork_song_personal(
            official_song.uuid,
            api_server.ForkSongRequest(user_email="cico@band.org", user_name="Cico"),
        )
        new_personal_uuid = refork_res["cloned_song"]["uuid"]
        self.assertNotEqual(new_personal_uuid, official_song.uuid)
        self.assertIn(new_personal_uuid, self.storage.get_repertoire(self.personal_rep.uuid).song_uuids)

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

    def test_promote_overwrite_remains_visible_in_official_even_with_orphans(self):
        """Regression test: save_song during promote overwrite keeps repertoire_uuids intact in index."""
        orphan = Song(uuid="aaa_orphan", title="50 SPECIAL", artist="Band", key_current="G", aml_content="[G]Orphan")
        official = Song(uuid="50_special_bebdbb", title="50 SPECIAL", artist="Lunapop", key_current="G", aml_content="[G]Old")
        personal = Song(uuid="ppp_personal", title="50 SPECIAL", artist="Lunapop", key_current="Ab", aml_content="[Ab]New")

        self.storage.save_song(orphan, "system", "System", "Orphan")
        self.storage.save_song(official, "system", "System", "Official")
        self.storage.save_song(personal, "cico@band.org", "Cico", "Personal")
        self.official_rep.song_uuids.append(official.uuid)
        self.personal_rep.song_uuids.append(personal.uuid)
        self.storage._save_repertoires_file([self.official_rep, self.personal_rep])
        self.storage.reload_from_disk()

        res = api_server.promote_song_to_official(
            api_server.PromoteSongRequest(song_uuid=personal.uuid, user_email="cico@band.org", user_name="Cico")
        )
        self.assertEqual(res["action"], "overwritten")
        visible_uuids = {s["uuid"] for s in self.storage.list_songs()}
        self.assertIn(official.uuid, visible_uuids)
        self.assertNotIn(personal.uuid, visible_uuids)
        official_listed = api_server.list_songs(
            repertoire_uuid=self.official_rep.uuid,
            search=None,
            user_email=None,
        )
        self.assertEqual([s["uuid"] for s in official_listed], [official.uuid])
        self.assertEqual(official_listed[0]["key_current"], "LAb")

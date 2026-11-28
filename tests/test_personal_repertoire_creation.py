"""Unit tests for automatic personal repertoire creation on musician first login."""
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

# Minimal mock for fastapi and pydantic if not installed locally
if 'fastapi' not in sys.modules:
    def fake_route_decorator(*args, **kwargs):
        def wrapper(f):
            return f
        return wrapper

    fastapi_mock = MagicMock()
    app_mock = MagicMock()
    app_mock.get = fake_route_decorator
    app_mock.post = fake_route_decorator
    app_mock.delete = fake_route_decorator
    app_mock.put = fake_route_decorator
    fastapi_mock.FastAPI = lambda *args, **kwargs: app_mock
    fastapi_mock.Query = lambda default=None, **kwargs: default
    fastapi_mock.HTTPException = Exception
    sys.modules['fastapi'] = fastapi_mock
    sys.modules['fastapi.responses'] = MagicMock()
    sys.modules['fastapi.staticfiles'] = MagicMock()
    sys.modules['fastapi.middleware'] = MagicMock()
    sys.modules['fastapi.middleware.cors'] = MagicMock()

if 'pydantic' not in sys.modules:
    class FakeBaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def dict(self):
            return self.__dict__
    pydantic_mock = MagicMock()
    pydantic_mock.BaseModel = FakeBaseModel
    pydantic_mock.Field = lambda *args, **kwargs: None
    sys.modules['pydantic'] = pydantic_mock

import api_server
from asma_core.audit_logger import AuditLogger
from asma_core.models import Repertoire, Song
from asma_core.storage_manager import StorageManager


class TestPersonalRepertoireCreation(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        StorageManager._instance = None
        AuditLogger._instance = None
        self.orig_storage = api_server.storage
        self.orig_audit = api_server.audit
        self.storage = StorageManager(data_dir=self.test_dir)
        api_server.storage = self.storage
        api_server.audit = self.storage.audit

        # Seed Official Band Repertoire
        self.official_rep = Repertoire(
            name="Repertorio Ufficiale Band",
            is_official=True,
            song_uuids=[],
            owner_email=None,
        )
        self.storage._save_repertoires_file([self.official_rep])
        self.storage.reload_from_disk()

    def tearDown(self):
        api_server.storage = self.orig_storage
        api_server.audit = self.orig_audit
        StorageManager._instance = None
        AuditLogger._instance = None
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_first_connection_creates_empty_personal_repertoire(self):
        """When a musician connects for the first time, an empty personal repertoire is auto-created."""
        new_musician_email = "nuovochitarrista@band.org"
        new_musician_name = "Jimmy"

        # Verify no personal repertoire exists yet
        all_reps_before = self.storage.list_repertoires()
        self.assertEqual(len(all_reps_before), 1)

        # Call ensure_user_personal_repertoire (simulating first connection / OAuth callback)
        rep = api_server.ensure_user_personal_repertoire(new_musician_email, new_musician_name)
        self.assertIsNotNone(rep)
        self.assertEqual(rep.name, "Jimmy")
        self.assertEqual(rep.owner_email, new_musician_email)
        self.assertFalse(rep.is_official)
        self.assertEqual(rep.song_uuids, [], "Initial personal repertoire must be strictly empty")

        # Verify it's persisted on disk
        all_reps_after = self.storage.list_repertoires()
        self.assertEqual(len(all_reps_after), 2)
        persisted = next(r for r in all_reps_after if r.owner_email == new_musician_email)
        self.assertEqual(persisted.uuid, rep.uuid)

    def test_subsequent_connections_do_not_duplicate_or_overwrite(self):
        """On subsequent connections, existing personal repertoire is returned without duplicates."""
        email = "bassista@band.org"
        name = "Flea"

        # 1. First connection
        rep1 = api_server.ensure_user_personal_repertoire(email, name)
        self.assertIsNotNone(rep1)

        # Add a song to their personal repertoire
        test_song = Song(title="Bass Groove", artist="Band", key_current="A", aml_content="[A]Slap")
        self.storage.save_song(test_song, email, name, "Copia personale")
        rep1.song_uuids.append(test_song.uuid)
        self.storage.save_repertoire(rep1, email, name)

        # 2. Second connection (subsequent login / page reload)
        rep2 = api_server.ensure_user_personal_repertoire(email, name)
        self.assertEqual(rep1.uuid, rep2.uuid)
        self.assertEqual(rep2.song_uuids, [test_song.uuid], "Existing songs in personal repertoire must NOT be overwritten")

        # Verify count of repertoires has not increased
        matching_reps = [r for r in self.storage.list_repertoires() if r.owner_email == email]
        self.assertEqual(len(matching_reps), 1)

    def test_case_insensitive_email_matching(self):
        """Repertoire ownership check is case-insensitive so mixed-case logins do not create duplicates."""
        email_lower = "drummer@band.org"
        email_mixed = "Drummer@Band.Org"

        rep1 = api_server.ensure_user_personal_repertoire(email_mixed, "Chad")
        self.assertIsNotNone(rep1)

        # Second connection with lowercase email
        rep2 = api_server.ensure_user_personal_repertoire(email_lower, "Chad")
        self.assertEqual(rep1.uuid, rep2.uuid)

        reps = [r for r in self.storage.list_repertoires() if (r.owner_email or "").lower() == email_lower]
        self.assertEqual(len(reps), 1)

    def test_musician_repertoire_scoping_official_and_personal_only(self):
        """A musician sees ONLY the Official Repertoire and their own Personal Repertoire."""
        cico_email = "cico@band.org"
        puma_email = "puma@band.org"

        # Create personal reps for both musicians
        api_server.ensure_user_personal_repertoire(cico_email, "Cico")
        api_server.ensure_user_personal_repertoire(puma_email, "Puma")

        # Cico calls list_repertoires
        reps_for_cico = api_server.list_repertoires(user_email=cico_email)
        rep_names_cico = [r["name"] for r in reps_for_cico]
        self.assertIn("Repertorio Ufficiale Band", rep_names_cico)
        self.assertIn("Cico", rep_names_cico)
        self.assertNotIn("Puma", rep_names_cico, "Cico must NOT see Puma's personal repertoire")

        # Puma calls list_repertoires
        reps_for_puma = api_server.list_repertoires(user_email=puma_email)
        rep_names_puma = [r["name"] for r in reps_for_puma]
        self.assertIn("Repertorio Ufficiale Band", rep_names_puma)
        self.assertIn("Puma", rep_names_puma)
        self.assertNotIn("Cico", rep_names_puma, "Puma must NOT see Cico's personal repertoire")

    def test_resolve_personal_repertoire_uses_isolated_user_repertoire(self):
        """_resolve_personal_repertoire never falls back to another musician's repertoire."""
        cico_email = "cico@band.org"
        puma_email = "puma@band.org"

        api_server.ensure_user_personal_repertoire(cico_email, "Cico")

        # Puma needs personal rep resolved (e.g. for import/copy)
        resolved_puma = api_server._resolve_personal_repertoire(puma_email, "Puma")
        self.assertEqual(resolved_puma.owner_email, puma_email)
        self.assertNotEqual(resolved_puma.owner_email, cico_email)


if __name__ == '__main__':
    unittest.main()

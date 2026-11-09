"""
Unit Tests for AuthManager (Google OAuth & RBAC) and BackupEngine (Disaster Recovery).
Conforms to SRS Cap. 3, 10, 17.5.
"""

import unittest
import shutil
import tempfile
from pathlib import Path
from asma_core.auth_manager import AuthManager, UserRole, User
from asma_core.backup_engine import BackupEngine
from asma_core.storage_manager import StorageManager
from asma_core.models import Song


class TestAuthAndBackup(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.auth_mgr = AuthManager(data_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_default_users_and_roles(self):
        """Test default pre-seeded users and role-based permissions."""
        admin = self.auth_mgr.get_user_by_email("danyposta@gmail.com")
        self.assertIsNotNone(admin)
        self.assertEqual(admin.role, UserRole.ADMIN)
        self.assertTrue(admin.can_admin())
        self.assertTrue(admin.can_edit())
        self.assertTrue(admin.can_delete())
        self.assertTrue(admin.can_force_unlock())

        band_mem = self.auth_mgr.get_user_by_email("acicchelli65@gmail.com")
        self.assertIsNotNone(band_mem)
        self.assertEqual(band_mem.role, UserRole.BAND_MEMBER)
        self.assertFalse(band_mem.can_admin())
        self.assertTrue(band_mem.can_edit())
        self.assertTrue(band_mem.can_delete())
        self.assertFalse(band_mem.can_force_unlock())

        viewer = self.auth_mgr.authenticate_or_register_google("fan_test@gmail.com", "Fan Test")
        self.assertIsNotNone(viewer)
        self.assertEqual(viewer.role, UserRole.VIEWER)
        self.assertFalse(viewer.can_admin())
        self.assertFalse(viewer.can_edit())
        self.assertFalse(viewer.can_delete())

    def test_authenticate_or_register_google(self):
        """Test automatic registration of new Google OAuth users with initial roles."""
        new_fan = self.auth_mgr.authenticate_or_register_google("fan123@gmail.com", "Fan Utente")
        self.assertEqual(new_fan.role, UserRole.VIEWER)

        band_collab = self.auth_mgr.authenticate_or_register_google("maurobovolenta4@gmail.com", "Maurino")
        self.assertEqual(band_collab.role, UserRole.BAND_MEMBER)

    def test_update_user_role_admin_guard(self):
        """Only ADMIN can change roles; non-admins raise PermissionError."""
        viewer = self.auth_mgr.authenticate_or_register_google("ospite_test@gmail.com", "Ospite")
        # Non-admin attempting to promote
        with self.assertRaises(PermissionError):
            self.auth_mgr.update_user_role("ospite_test@gmail.com", UserRole.ADMIN, admin_email="acicchelli65@gmail.com")

        # Real admin promotes viewer to band member
        success = self.auth_mgr.update_user_role("ospite_test@gmail.com", UserRole.BAND_MEMBER, admin_email="danyposta@gmail.com")
        self.assertTrue(success)
        promoted = self.auth_mgr.get_user_by_email("ospite_test@gmail.com")
        self.assertEqual(promoted.role, UserRole.BAND_MEMBER)

    def test_delete_user(self):
        """Test user deletion rules and admin constraints."""
        self.auth_mgr.authenticate_or_register_google("to_delete@gmail.com", "Da Eliminare")
        # Non-admin cannot delete
        with self.assertRaises(PermissionError):
            self.auth_mgr.delete_user("to_delete@gmail.com", admin_email="acicchelli65@gmail.com")

        # Admin cannot delete themselves
        with self.assertRaises(ValueError):
            self.auth_mgr.delete_user("danyposta@gmail.com", admin_email="danyposta@gmail.com")

        # Admin deletes user successfully
        del_ok = self.auth_mgr.delete_user("to_delete@gmail.com", admin_email="danyposta@gmail.com")
        self.assertTrue(del_ok)
        self.assertIsNone(self.auth_mgr.get_user_by_email("to_delete@gmail.com"))

    def test_backup_and_restore_cycle(self):
        """Test full atomic ZIP backup creation and disaster recovery restore."""
        # Setup storage in test dir
        songs_dir = Path(self.test_dir) / "songs"
        songs_dir.mkdir(parents=True, exist_ok=True)
        sample_song_file = songs_dir / "test_song.json"
        sample_song_file.write_text('{"uuid": "test-uuid-123", "title": "Canzone Backup", "key_current": "G", "aml_content": "{title: Canzone Backup}"}', encoding="utf-8")

        # 1. Create backup ZIP
        backup_zip = BackupEngine.create_full_backup_zip(data_dir=self.test_dir)
        self.assertIsNotNone(backup_zip)
        self.assertTrue(len(backup_zip) > 50)
        self.assertTrue(backup_zip.startswith(b"PK\x03\x04"))

        # 2. Wipe directory and restore
        restore_dir = tempfile.mkdtemp()
        try:
            ok, msg = BackupEngine.restore_from_backup_zip(backup_zip, target_data_dir=restore_dir)
            self.assertTrue(ok)
            restored_file = Path(restore_dir) / "songs" / "test_song.json"
            self.assertTrue(restored_file.exists())
            self.assertIn("Canzone Backup", restored_file.read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(restore_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()

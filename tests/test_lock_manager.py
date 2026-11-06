"""
Unit and Concurrency Tests for Distributed Lock Manager
Conforms to SRS Cap. 4.6, 7.7, 15.24, 17.33.
"""

import unittest
import time
from asma_core.lock_manager import LockManager


class TestLockManager(unittest.TestCase):

    def setUp(self):
        self.lock_mgr = LockManager()
        self.lock_mgr.clear_all_locks_for_testing()
        self.song_id = "song-test-123"

    def test_acquire_and_release_lock(self):
        """Test simple lock acquisition and manual release."""
        success, status, msg = self.lock_mgr.acquire_lock(
            song_uuid=self.song_id,
            user_email="roberto@band.org",
            user_name="Roberto",
            session_id="session-1"
        )
        self.assertTrue(success)
        self.assertTrue(status.is_locked)
        self.assertEqual(status.locked_by_name, "Roberto")

        # Check status
        cur = self.lock_mgr.check_lock(self.song_id)
        self.assertTrue(cur.is_locked)

        # Release
        rel_ok, rel_msg = self.lock_mgr.release_lock(self.song_id, "roberto@band.org")
        self.assertTrue(rel_ok)

        # Check status after release
        cur_after = self.lock_mgr.check_lock(self.song_id)
        self.assertFalse(cur_after.is_locked)

    def test_concurrent_lock_conflict(self):
        """SRS Cap. 4.6: If Roberto holds lock, Daniele cannot edit and is blocked."""
        # Roberto acquires lock
        self.lock_mgr.acquire_lock(self.song_id, "roberto@band.org", "Roberto", "sess-1")

        # Daniele attempts to acquire lock on same song
        dan_ok, dan_status, dan_msg = self.lock_mgr.acquire_lock(
            song_uuid=self.song_id,
            user_email="daniele@band.org",
            user_name="Daniele",
            session_id="sess-2"
        )
        self.assertFalse(dan_ok)
        self.assertIn("Roberto", dan_msg)

    def test_reacquire_same_user_refreshes_lock(self):
        """Owner can re-acquire without error to refresh heartbeat."""
        self.lock_mgr.acquire_lock(self.song_id, "roberto@band.org", "Roberto", "sess-1")
        ok, status, msg = self.lock_mgr.acquire_lock(self.song_id, "roberto@band.org", "Roberto", "sess-1")
        self.assertTrue(ok)
        self.assertIn("rinnovato", msg)

    def test_admin_force_release(self):
        """SRS Cap. 15.24: Administrator can force unlock any song."""
        self.lock_mgr.acquire_lock(self.song_id, "roberto@band.org", "Roberto", "sess-1")

        # Non-owner fails release without force
        fail_ok, _ = self.lock_mgr.release_lock(self.song_id, "daniele@band.org", force=False)
        self.assertFalse(fail_ok)

        # Admin force-releases
        force_ok, force_msg = self.lock_mgr.release_lock(self.song_id, "admin@band.org", force=True)
        self.assertTrue(force_ok)
        self.assertFalse(self.lock_mgr.check_lock(self.song_id).is_locked)

    def test_release_user_locks_auto_unlock(self):
        """User exiting 'Brani' menu automatically releases all locks owned by that user."""
        self.lock_mgr.acquire_lock("song-1", "user@band.org", "User", "sess-1")
        self.lock_mgr.acquire_lock("song-2", "other@band.org", "Other", "sess-2")
        
        # User exits Brani menu -> auto unlock
        released = self.lock_mgr.release_user_locks("user@band.org")
        self.assertEqual(released, ["song-1"])
        self.assertFalse(self.lock_mgr.check_lock("song-1").is_locked)
        # Other user's lock is unaffected
        self.assertTrue(self.lock_mgr.check_lock("song-2").is_locked)


if __name__ == "__main__":
    unittest.main()

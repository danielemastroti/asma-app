"""
Unit Tests for Immutable Audit Trail Logger
Conforms to SRS Cap. 4.9, 15.19, 16.16.
"""

import unittest
import tempfile
import os
from asma_core.audit_logger import AuditLogger


class TestAuditLogger(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmp_dir, "test_audit.jsonl")
        self.logger = AuditLogger(log_file_path=self.log_path)
        self.logger.clear_for_testing()

    def test_log_and_query_entries(self):
        """Test append-only record creation and reverse chronological query."""
        e1 = self.logger.log("LOGIN", "USER", "user-1", "daniele@band.org", "Daniele")
        e2 = self.logger.log("UPDATE", "SONG", "song-1", "daniele@band.org", "Daniele", {"title": "Hotel California"})

        entries = self.logger.get_entries(limit=10)
        self.assertEqual(len(entries), 2)
        # Most recent first
        self.assertEqual(entries[0].action, "UPDATE")
        self.assertEqual(entries[1].action, "LOGIN")

    def test_filter_entries(self):
        """Test filtering audit log by action and entity type."""
        self.logger.log("LOGIN", "USER", "u1", "a@b.com", "A")
        self.logger.log("CREATE", "SONG", "s1", "a@b.com", "A")
        self.logger.log("DELETE", "SONG", "s2", "b@b.com", "B")

        song_logs = self.logger.get_entries(entity_filter="SONG")
        self.assertEqual(len(song_logs), 2)

        login_logs = self.logger.get_entries(action_filter="LOGIN")
        self.assertEqual(len(login_logs), 1)

    def test_15_days_retention_pruning(self):
        """Test that records older than 15 days are automatically pruned."""
        from datetime import datetime, timezone, timedelta
        from asma_core.models import AuditEntry

        now = datetime.now(timezone.utc)
        old_ts = (now - timedelta(days=20)).isoformat()
        recent_ts = (now - timedelta(days=2)).isoformat()

        # Inject an expired entry and a valid entry
        e_old = AuditEntry(
            uuid="old-uuid",
            timestamp=old_ts,
            action="LOGIN",
            entity_type="AUTH",
            entity_id="user-old",
            user_email="old@band.org",
            user_name="OldUser"
        )
        e_recent = AuditEntry(
            uuid="recent-uuid",
            timestamp=recent_ts,
            action="UPDATE",
            entity_type="SONG",
            entity_id="song-recent",
            user_email="puma@band.org",
            user_name="Puma"
        )
        with self.logger._mutex:
            self.logger._memory_log.extend([e_old, e_recent])

        pruned = self.logger.prune_retention()
        self.assertEqual(pruned, 1)

        remaining = self.logger.get_entries(limit=10)
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].uuid, "recent-uuid")

    def test_statistics_calculation(self):
        """Test usage frequency and musician activity statistics."""
        self.logger.log("LOGIN", "AUTH", "u1", "cico@band.org", "Cico")
        self.logger.log("UPDATE", "SONG", "s1", "cico@band.org", "Cico", {"title": "Brano 1"})
        self.logger.log("UPDATE", "SONG", "s2", "puma@band.org", "Puma", {"title": "Brano 2"})

        stats = self.logger.get_statistics(days=15)
        self.assertEqual(stats["total_events"], 3)
        self.assertGreaterEqual(len(stats["active_users"]), 2)
        # Cico should have 2 actions, Puma 1
        top_user = stats["active_users"][0]
        self.assertEqual(top_user["name"], "Cico")
        self.assertEqual(top_user["count"], 2)
        self.assertEqual(stats["action_counts"]["UPDATE"], 2)
        self.assertEqual(stats["action_counts"]["LOGIN"], 1)


if __name__ == "__main__":
    unittest.main()

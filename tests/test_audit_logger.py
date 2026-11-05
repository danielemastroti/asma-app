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


if __name__ == "__main__":
    unittest.main()

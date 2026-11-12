import unittest
import json
import os
from fastapi.testclient import TestClient
from api_server import app, storage, auth_mgr, pref_mgr
from asma_core.changelog_engine import ChangelogEngine
from asma_core.backup_engine import BackupEngine


class TestChangelogAndBackup(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.admin_email = "danyposta@gmail.com"
        self.non_admin_email = "maurobovolenta4@gmail.com"

    def test_changelog_get_public(self):
        """Verify changelog is accessible to everyone without authentication."""
        res = self.client.get("/api/changelog")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("entries", data)
        self.assertIn("latest_version", data)
        self.assertGreaterEqual(len(data["entries"]), 1)
        # Verify 2026.11.12 is present
        versions = [e["version"] for e in data["entries"]]
        self.assertIn("2026.11.12", versions)

    def test_changelog_single_version_per_day_merge(self):
        """Verify adding features to the same date merges instead of duplicating version entries."""
        initial_len = len(ChangelogEngine.get_entries())
        today_ver = "2026.11.12"

        entry1 = ChangelogEngine.record_entry(
            version=today_ver,
            date_str="12/11/2026",
            title="Release Test",
            new_features=["Feature Alfa"],
            bug_fixes=["Fix Alfa"]
        )
        self.assertEqual(entry1["version"], today_ver)
        self.assertIn("Feature Alfa", entry1["new_features"])

        # Second record on the same day with more features
        entry2 = ChangelogEngine.record_entry(
            version=today_ver,
            date_str="12/11/2026",
            new_features=["Feature Beta"],
            bug_fixes=["Fix Beta"]
        )
        self.assertEqual(entry2["version"], today_ver)
        self.assertIn("Feature Alfa", entry2["new_features"])
        self.assertIn("Feature Beta", entry2["new_features"])
        self.assertIn("Fix Alfa", entry2["bug_fixes"])
        self.assertIn("Fix Beta", entry2["bug_fixes"])

        # Number of versions should not increase for the same date
        after_len = len(ChangelogEngine.get_entries())
        self.assertEqual(initial_len, after_len)

    def test_admin_backup_authorization(self):
        """Verify backup endpoint enforces strict admin role checks."""
        # Non-admin forbidden
        res_forbid = self.client.get(f"/api/admin/backup?user_email={self.non_admin_email}")
        self.assertEqual(res_forbid.status_code, 403)

        # Admin allowed
        res_ok = self.client.get(f"/api/admin/backup?user_email={self.admin_email}&user_name=Admin")
        self.assertEqual(res_ok.status_code, 200)
        self.assertIn("attachment", res_ok.headers.get("content-disposition", ""))
        payload = res_ok.json()
        self.assertEqual(payload["schema_version"], "2.0")
        self.assertIn("songs", payload["data"])
        self.assertIn("repertoires", payload["data"])
        self.assertIn("setlists", payload["data"])
        self.assertIn("users", payload["data"])
        self.assertIn("changelog", payload["data"])

    def test_admin_restore_authorization_and_execution(self):
        """Verify restore endpoint enforces admin authorization and restores data cleanly."""
        # Create valid backup dump
        backup = BackupEngine.create_backup(self.admin_email, "Admin", storage, auth_mgr, pref_mgr)

        # Non-admin forbidden
        res_forbid = self.client.post("/api/admin/restore", json={
            "user_email": self.non_admin_email,
            "backup_data": backup
        })
        self.assertEqual(res_forbid.status_code, 403)

        # Admin allowed
        res_ok = self.client.post("/api/admin/restore", json={
            "user_email": self.admin_email,
            "user_name": "Admin",
            "backup_data": backup
        })
        self.assertEqual(res_ok.status_code, 200)
        res_data = res_ok.json()
        self.assertEqual(res_data["status"], "success")
        self.assertIn("counts", res_data)
        self.assertGreater(res_data["counts"]["songs"], 0)
        self.assertGreater(res_data["counts"]["repertoires"], 0)
        self.assertGreater(res_data["counts"]["users"], 0)
        self.assertGreater(res_data["counts"]["changelog"], 0)


if __name__ == "__main__":
    unittest.main()

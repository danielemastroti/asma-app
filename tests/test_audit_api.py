import unittest
from fastapi.testclient import TestClient
from api_server import app

class TestAuditApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_client_audit_event_logging(self):
        res = self.client.post("/api/audit-log/event", json={
            "action": "STAGE_VIEW",
            "entity_type": "SONG",
            "entity_id": "test-song-uuid",
            "user_email": "puma@band.org",
            "user_name": "Puma",
            "details": {"title": "Acqua Azzurra Acqua Chiara", "mode": "teleprompter"}
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get("status"), "ok")

    def test_audit_log_access_permissions(self):
        # Non-admin musician must be rejected with 403
        res_non_admin = self.client.get("/api/audit-log?user_email=cico@band.org")
        self.assertEqual(res_non_admin.status_code, 403)

        # Admin must be granted access with 200 and complete stats
        res_admin = self.client.get("/api/audit-log?user_email=danyposta@gmail.com")
        self.assertEqual(res_admin.status_code, 200)
        data = res_admin.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("retention_days"), 15)
        self.assertIn("stats", data)
        self.assertIn("entries", data)
        self.assertIn("active_users", data["stats"])
        self.assertIn("action_counts", data["stats"])

    def test_audit_log_download(self):
        # Non-admin rejected
        res_forbidden = self.client.get("/api/audit-log/download?user_email=cico@band.org")
        self.assertEqual(res_forbidden.status_code, 403)

        # Admin download CSV
        res_csv = self.client.get("/api/audit-log/download?user_email=danyposta@gmail.com&format=csv")
        self.assertEqual(res_csv.status_code, 200)
        self.assertIn("text/csv", res_csv.headers.get("content-type", ""))
        self.assertIn("Timestamp (ISO)", res_csv.text)

        # Admin download JSON
        res_json = self.client.get("/api/audit-log/download?user_email=danyposta@gmail.com&format=json")
        self.assertEqual(res_json.status_code, 200)
        self.assertIn("application/json", res_json.headers.get("content-type", ""))

if __name__ == "__main__":
    unittest.main()

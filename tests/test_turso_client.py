"""
Unit tests for TursoClient (LibSQL Serverless Cloud SQLite).
Conforms to SRS Cap. 4, 18, 19.16.
"""

import unittest
from asma_core.turso_client import TursoClient


class TestTursoClient(unittest.TestCase):

    def setUp(self):
        self.turso = TursoClient()

    def test_configuration(self):
        """Verifies that TursoClient correctly detects configured credentials."""
        self.assertTrue(self.turso.is_configured)
        self.assertTrue(self.turso.http_url.startswith("https://"))

    def test_fetch_users(self):
        """Verifies fetching users from Turso Cloud."""
        users = self.turso.fetch_users()
        self.assertIsInstance(users, list)
        self.assertGreaterEqual(len(users), 1)
        emails = [u["email"] for u in users]
        self.assertIn("danyposta@gmail.com", emails)

    def test_fetch_songs(self):
        """Verifies fetching songs from Turso Cloud."""
        songs = self.turso.fetch_all_songs()
        self.assertIsInstance(songs, list)
        self.assertGreaterEqual(len(songs), 1)
        titles = [s["title"] for s in songs]
        self.assertTrue(any("UNCHAIN" in t.upper() or "BELIEVER" in t.upper() or "50" in t for t in titles))


if __name__ == '__main__':
    unittest.main()

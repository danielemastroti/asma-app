"""
Test Suite: Live Performance Suggestions (AI Gemini Free / Offline Heuristics) & Dynamic Auto-Updating User Manual (PDF).
"""

import unittest
from fastapi.testclient import TestClient

from asma_core.models import Song
from asma_core.ai_service import BandAIService
from asma_core.manual_engine import ManualEngine
from api_server import app, storage


class TestAISuggestionsAndManual(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.song = Song(
            uuid="test-ai-manual-uuid",
            title="Albachiara",
            artist="Vasco Rossi",
            key_current="DO",
            bpm=68,
            capo=0,
            aml_content=(
                "{title: Albachiara}\n"
                "{artist: Vasco Rossi}\n"
                "{key: DO}\n"
                "{scena: 3}\n"
                "{stacco: guitar}\n"
                "[INTRO]\n"
                "| DO | SOL | LAm | FA |\n"
                "[STROFA]\n"
                "[DO]Respiri piano per [SOL]non far rumore\n"
                "{solo: Red}\n"
                "[OUTRO]\n"
                "[DO]Respiri piano... [END]"
            )
        )
        storage.save_song(self.song)

    def tearDown(self):
        try:
            storage.delete_song("test-ai-manual-uuid", hard_delete=True)
        except Exception:
            pass

    def test_musicians_list(self):
        musicians = BandAIService.get_musician_list()
        self.assertGreaterEqual(len(musicians), 7)
        keys = [m["key"] for m in musicians]
        self.assertIn("band", keys)
        self.assertIn("cico", keys)
        self.assertIn("mingo", keys)
        self.assertIn("puma", keys)
        self.assertIn("red", keys)
        self.assertIn("maurino", keys)
        self.assertIn("sentimental", keys)

    def test_suggestions_for_all_musicians(self):
        for m_key in ["band", "cico", "mingo", "puma", "red", "maurino", "sentimental"]:
            res = BandAIService.generate_live_suggestions(self.song, m_key)
            self.assertEqual(res["musician_key"], m_key)
            self.assertTrue(len(res["summary"]) > 0)
            self.assertTrue(len(res["tips"]) >= 3)
            self.assertTrue(len(res["gear_advice"]) > 0)
            self.assertTrue(len(res["watchout"]) > 0)

    def test_suggestions_directives_awareness(self):
        # Sentimental should receive reference to Scena 3
        res_sent = BandAIService.generate_live_suggestions(self.song, "sentimental")
        combined_text = res_sent["summary"] + " " + res_sent["gear_advice"] + " " + " ".join(t["tip"] for t in res_sent["tips"])
        self.assertIn("Scena 3", combined_text)

        # Red should receive reference to guitar solo
        res_red = BandAIService.generate_live_suggestions(self.song, "red")
        combined_red = " ".join(t["tip"] for t in res_red["tips"])
        self.assertTrue("solo" in combined_red.lower() or "overdrive" in res_red["gear_advice"].lower())

    def test_suggestions_in_memory_cache(self):
        res1 = BandAIService.generate_live_suggestions(self.song, "cico")
        res2 = BandAIService.generate_live_suggestions(self.song, "cico")
        self.assertIs(res1, res2)

    def test_manual_chapters_metadata(self):
        chapters = ManualEngine.get_chapters_metadata()
        self.assertEqual(len(chapters), 16)
        titles = [c["title"] for c in chapters]
        self.assertTrue(any("Introduzione" in t for t in titles))
        self.assertTrue(any("Login" in t for t in titles))
        self.assertTrue(any("Elenco Utenti" in t for t in titles))
        self.assertTrue(any("Preferenze" in t for t in titles))
        self.assertTrue(any("Lista Brani" in t for t in titles))
        self.assertTrue(any("Importazione" in t for t in titles))
        self.assertTrue(any("Creazione Brani" in t for t in titles))
        self.assertTrue(any("Flusso di Lavoro" in t for t in titles))
        self.assertTrue(any("AML" in t for t in titles))
        self.assertTrue(any("Medley" in t for t in titles))
        self.assertTrue(any("Palco" in t for t in titles))
        self.assertTrue(any("Scalette" in t for t in titles))
        self.assertTrue(any("Suggerimenti Esecuzione Live" in t for t in titles))
        self.assertTrue(any("Amministrazione" in t for t in titles))
        self.assertTrue(any("Changelog" in t for t in titles))

    def test_manual_pdf_generation(self):
        pdf_bytes = ManualEngine.generate_manual_pdf()
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
        self.assertGreater(len(pdf_bytes), 100000)  # > 100 KB

    def test_api_song_ai_suggestions_endpoint(self):
        resp = self.client.get(f"/api/songs/{self.song.uuid}/ai-suggestions?musician=cico")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["suggestions"]["musician_name"], "Cico")

        resp_band = self.client.get(f"/api/songs/{self.song.uuid}/ai-suggestions?musician=band")
        self.assertEqual(resp_band.status_code, 200)
        data_band = resp_band.json()
        self.assertEqual(data_band["suggestions"]["musician_name"], "Tutta la Band")

    def test_api_manual_pdf_endpoint(self):
        resp = self.client.get("/api/manual/pdf")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("content-type"), "application/pdf")
        self.assertIn("attachment; filename=", resp.headers.get("content-disposition", ""))
        self.assertTrue(resp.content.startswith(b"%PDF-"))
        self.assertGreater(len(resp.content), 100000)

    def test_api_manual_metadata_endpoint(self):
        resp = self.client.get("/api/manual")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["chapters"]), 16)


if __name__ == "__main__":
    unittest.main()

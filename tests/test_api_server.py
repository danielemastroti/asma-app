"""
Unit and Integration Tests for FastAPI Backend (api_server.py)
Verifies REST API endpoints against asma_core services.
"""

import unittest
from fastapi.testclient import TestClient
from api_server import app, storage
from asma_core.models import Song, Repertoire, Setlist, SetlistItem


class TestApiServer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_health_endpoint(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "online")
        self.assertEqual(data["app"], "THE New ASMA")
        self.assertIn("counts", data)

    def test_02_repertoires_endpoint(self):
        resp = self.client.get("/api/repertoires")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        if data:
            self.assertIn("name", data[0])
            self.assertIn("song_count", data[0])

    def test_03_songs_list_and_search(self):
        resp = self.client.get("/api/songs")
        self.assertEqual(resp.status_code, 200)
        songs = resp.json()
        self.assertIsInstance(songs, list)
        self.assertGreater(len(songs), 0)

        # Search test
        first_title = songs[0]["title"]
        search_kw = first_title[:4]
        search_resp = self.client.get(f"/api/songs?search={search_kw}")
        self.assertEqual(search_resp.status_code, 200)
        found = search_resp.json()
        self.assertTrue(any(search_kw.lower() in s["title"].lower() for s in found))

    def test_04_single_song_and_pdf_generation(self):
        songs = self.client.get("/api/songs").json()
        song_uuid = songs[0]["uuid"]

        # Detail endpoint
        det_resp = self.client.get(f"/api/songs/{song_uuid}")
        self.assertEqual(det_resp.status_code, 200)
        song_data = det_resp.json()
        self.assertEqual(song_data["uuid"], song_uuid)
        self.assertIn("key_current_ita", song_data)

        # PDF streaming with chords
        pdf_chords_resp = self.client.get(f"/api/songs/{song_uuid}/pdf?chords=true")
        self.assertEqual(pdf_chords_resp.status_code, 200)
        self.assertEqual(pdf_chords_resp.headers["content-type"], "application/pdf")
        self.assertTrue(pdf_chords_resp.content.startswith(b"%PDF"))

        # PDF streaming lyrics only (cantante)
        pdf_lyrics_resp = self.client.get(f"/api/songs/{song_uuid}/pdf?chords=false")
        self.assertEqual(pdf_lyrics_resp.status_code, 200)
        self.assertEqual(pdf_lyrics_resp.headers["content-type"], "application/pdf")
        self.assertTrue(pdf_lyrics_resp.content.startswith(b"%PDF"))

    def test_05_setlists_endpoint(self):
        resp = self.client.get("/api/setlists")
        self.assertEqual(resp.status_code, 200)
        sets = resp.json()
        self.assertIsInstance(sets, list)
        if sets:
            set_uuid = sets[0]["uuid"]
            det_set = self.client.get(f"/api/setlists/{set_uuid}")
            self.assertEqual(det_set.status_code, 200)
            data = det_set.json()
            self.assertIn("items", data)
            self.assertIn("total_songs", data)

            # Consolidated setlist PDF test
            pdf_set = self.client.get(f"/api/setlists/{set_uuid}/pdf?chords=true")
            self.assertEqual(pdf_set.status_code, 200)
            self.assertEqual(pdf_set.headers["content-type"], "application/pdf")
            self.assertTrue(pdf_set.content.startswith(b"%PDF"))

    def test_06_devices_and_preferences(self):
        # Devices
        dev_resp = self.client.get("/api/devices")
        self.assertEqual(dev_resp.status_code, 200)
        devices = dev_resp.json()
        self.assertTrue(any("Huawei" in d["name"] for d in devices))

        # Preferences read & save
        email = "test_musician@band.org"
        save_resp = self.client.post(f"/api/preferences/{email}", json={
            "app_mode": "simplified",
            "score_display_mode": "lyrics",
            "device_name": "Huawei MediaPad M5",
            "layout_font_size": 14.0
        })
        self.assertEqual(save_resp.status_code, 200)

        get_resp = self.client.get(f"/api/preferences/{email}")
        self.assertEqual(get_resp.status_code, 200)
        prefs = get_resp.json()
        self.assertEqual(prefs["score_display_mode"], "lyrics")

    def test_07_stage_song_payload(self):
        songs = self.client.get("/api/songs").json()
        song_uuid = songs[0]["uuid"]

        stage_resp = self.client.get(f"/api/stage/song/{song_uuid}")
        self.assertEqual(stage_resp.status_code, 200)
        stage_data = stage_resp.json()
        self.assertIn("title", stage_data)
        self.assertIn("sections", stage_data)

    def test_08_pwa_static_files(self):
        # Index HTML
        idx_resp = self.client.get("/")
        self.assertEqual(idx_resp.status_code, 200)
        self.assertIn("THE New ASMA", idx_resp.text)
        self.assertIn("manifest.json", idx_resp.text)

        # Manifest
        man_resp = self.client.get("/manifest.json")
        self.assertEqual(man_resp.status_code, 200)
        man_data = man_resp.json()
        self.assertEqual(man_data["display"], "standalone")

        # Service Worker
        sw_resp = self.client.get("/sw.js")
        self.assertEqual(sw_resp.status_code, 200)
        self.assertIn("asma-pwa", sw_resp.text)

        # App JS
        js_resp = self.client.get("/app.js")
        self.assertEqual(js_resp.status_code, 200)
        self.assertIn("selectRepertoire", js_resp.text)

    def test_09_personalized_pdf_and_transpose(self):
        test_song = Song(
            title="Temp Transpose Song",
            artist="Band",
            key_original="SOL",
            key_current="SOL",
            aml_content="{title: Temp Transpose Song}\n{key: SOL}\n\n[SOL]Vespe [DO]special"
        )
        saved_song = storage.save_song(test_song, "cico@band.org", "Cico")
        song_uuid = saved_song.uuid
        email = "cico@band.org"

        try:
            # Transpose
            tr_resp = self.client.post(f"/api/songs/{song_uuid}/transpose", json={
                "semitones": 1,
                "user_email": email
            })
            self.assertEqual(tr_resp.status_code, 200)
            self.assertIn(tr_resp.json()["song"]["key_current"], ["SOL#", "LAb", "Ab", "G#"])

            # Personalized PDF streaming using user email and Huawei profile
            pdf_resp = self.client.get(f"/api/songs/{song_uuid}/pdf?email={email}&device=Huawei+MediaPad+M5&chords=true")
            self.assertEqual(pdf_resp.status_code, 200)
            self.assertEqual(pdf_resp.headers["content-type"], "application/pdf")
            self.assertTrue(pdf_resp.content.startswith(b"%PDF"))
        finally:
            storage.delete_song(song_uuid, email, "Cico")

    def test_10_users_endpoint(self):
        resp = self.client.get("/api/users")
        self.assertEqual(resp.status_code, 200)
        users = resp.json()
        self.assertIsInstance(users, list)
        self.assertTrue(any(u["name"] == "Cico" for u in users))

    def test_11_convert_text_endpoint(self):
        raw = """
        DO            SOL
        Vespe truccate anni sessanta
        FA            DO
        girano in centro sfiorando i novanta
        """
        resp = self.client.post("/api/songs/convert-text", json={
            "raw_text": raw,
            "title": "Vespa Test",
            "artist": "Lunapop"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("[DO]", data["aml"])
        self.assertIn("[SOL]", data["aml"])
        self.assertEqual(data["title"], "Vespa Test")
        self.assertEqual(data["artist"], "Lunapop")

    def test_12_web_search_endpoint(self):
        resp = self.client.get("/api/songs/web-search?title=50+Special&artist=Lunapop")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["query"]["title"], "50 Special")
        self.assertIsInstance(data["candidates"], list)
        self.assertGreater(data["count"], 0)

    def test_13_import_vision_validation(self):
        # Empty images list must return 400
        resp = self.client.post("/api/songs/import-vision", json={"images": []})
        self.assertEqual(resp.status_code, 400)

    def test_14_import_vision_mocked(self):
        from unittest.mock import patch
        mock_res = {
            "title": "Canzone Cartacea",
            "artist": "Cantautore",
            "key": "SOL",
            "bpm": 115,
            "capo": 2,
            "aml_content": "{title: Canzone Cartacea}\n[SOL]Strofa con accordi...\n"
        }
        with patch("asma_core.ai_service.BandAIService.transcribe_sheet_music_images", return_value=mock_res):
            resp = self.client.post("/api/songs/import-vision", json={
                "images": [{"data": "dummyBase64", "mime_type": "image/jpeg"}]
            })
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["status"], "success")
            self.assertEqual(data["title"], "Canzone Cartacea")
            self.assertEqual(data["key"], "SOL")
            self.assertEqual(data["bpm"], 115)
            self.assertEqual(data["capo"], 2)
            self.assertIn("[SOL]", data["aml"])

    def test_15_google_oauth_flow_and_allowlist(self):
        from unittest.mock import patch
        import api_server

        # 1. Unauthenticated /api/auth/me
        res_me = self.client.get("/api/auth/me")
        self.assertEqual(res_me.status_code, 200)
        self.assertFalse(res_me.json()["authenticated"])

        with patch.object(api_server, "_get_google_oauth_config", return_value=("test-client-id", "test-client-secret")):
            # 2. Login redirect points to Google Accounts with /oauth2callback
            res_login = self.client.get("/api/auth/google/login?mode=editing", follow_redirects=False)
            self.assertEqual(res_login.status_code, 302)
            loc = res_login.headers["location"]
            self.assertIn("accounts.google.com/o/oauth2/v2/auth", loc)
            self.assertIn("oauth2callback", loc)

            # 3. Unauthorized Google email is rejected with 403
            with patch.object(api_server.auth_mgr, "exchange_google_code_for_user", return_value={"email": "intruder@gmail.com", "name": "Intruder"}):
                res_bad = self.client.get("/oauth2callback?code=badcode&state=asma_auth:simplified")
                self.assertEqual(res_bad.status_code, 403)
                self.assertIn("Accesso negato", res_bad.text)

            # 4. Authorized band Google email sets session cookie and authenticates /api/auth/me with band pseudonym
            with patch.object(api_server.auth_mgr, "exchange_google_code_for_user", return_value={"email": "acicchelli65@gmail.com", "name": "Angelo Cicchelli"}):
                res_ok = self.client.get("/oauth2callback?code=goodcode&state=asma_auth:editing", follow_redirects=False)
                self.assertEqual(res_ok.status_code, 302)
                self.assertEqual(res_ok.headers["location"], "/?mode=editing")
                self.assertIn("asma_session", res_ok.cookies)

                res_me2 = self.client.get("/api/auth/me")
                self.assertEqual(res_me2.status_code, 200)
                me_data = res_me2.json()
                self.assertTrue(me_data["authenticated"])
                self.assertEqual(me_data["user"]["email"], "acicchelli65@gmail.com")
                self.assertEqual(me_data["user"]["name"], "Cico")

            # 5. Logout clears session
            res_out = self.client.post("/api/auth/logout")
            self.assertEqual(res_out.status_code, 200)
            res_me3 = self.client.get("/api/auth/me")
            self.assertFalse(res_me3.json()["authenticated"])


if __name__ == '__main__':
    unittest.main()

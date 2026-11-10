import unittest
from fastapi.testclient import TestClient
from api_server import app

class TestRepertoireScoping(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_repertoire_scoping_and_song_visibility(self):
        # 1. Test Repertoire Visibility for Musician vs Admin
        res_cico = self.client.get('/api/repertoires?user_email=acicchelli65@gmail.com')
        self.assertEqual(res_cico.status_code, 200, res_cico.text)
        reps_cico = res_cico.json()
        rep_names_cico = [r['name'] for r in reps_cico]
        self.assertIn('Repertorio Ufficiale Band', rep_names_cico)
        self.assertIn('Cico', rep_names_cico)
        self.assertNotIn('Daniele', rep_names_cico)

        res_admin = self.client.get('/api/repertoires?user_email=danyposta@gmail.com')
        self.assertEqual(res_admin.status_code, 200, res_admin.text)
        reps_admin = res_admin.json()
        rep_names_admin = [r['name'] for r in reps_admin]
        self.assertIn('Repertorio Ufficiale Band', rep_names_admin)
        self.assertIn('Daniele', rep_names_admin)
        self.assertIn('Cico', rep_names_admin)

        # 2. Test Song Visibility scoping for Musician vs Admin
        songs_cico = self.client.get('/api/songs?user_email=acicchelli65@gmail.com').json()
        songs_admin = self.client.get('/api/songs?user_email=danyposta@gmail.com').json()
        self.assertGreaterEqual(len(songs_admin), len(songs_cico))

        # Check assigned repertoires inside Cico's view never leak other musicians' repertoires
        for s in songs_cico:
            for rep_name in s.get('assigned_repertoires', []):
                self.assertNotIn('Daniele', rep_name)

        # 3. Test Add Song to Setlist endpoint with isolated temporary setlist
        s_res = self.client.post('/api/setlists', json={'title': '__TEMP_TEST_SETLIST__', 'items': []})
        self.assertEqual(s_res.status_code, 200)
        target_setlist = s_res.json()['setlist']

        songs = self.client.get('/api/songs').json()
        self.assertGreater(len(songs), 0, 'No songs found')
        test_song = songs[0]

        add_res = self.client.post(f"/api/setlists/{target_setlist['uuid']}/songs/{test_song['uuid']}")
        self.assertEqual(add_res.status_code, 200, add_res.text)
        self.assertEqual(add_res.json()['song_title'], test_song['title'])

        # Clean up temporary test setlist immediately
        self.client.delete(f"/api/setlists/{target_setlist['uuid']}")

        # 4. Test Promote Song
        promote_res = self.client.post('/api/repertoires/promote-song', json={'song_uuid': test_song['uuid']})
        self.assertEqual(promote_res.status_code, 200, promote_res.text)

        # 5. Test Soft Delete & Restore
        song_create_res = self.client.post('/api/songs', json={
            'title': 'TEST UNDO SONG',
            'artist': 'Band',
            'key_current': 'G',
            'aml_content': '[SOL]Test'
        })
        del_song_uuid = song_create_res.json()['song']['uuid']
        del_res = self.client.delete(f'/api/songs/{del_song_uuid}')
        self.assertEqual(del_res.status_code, 200)
        restore_res = self.client.post(f'/api/songs/{del_song_uuid}/restore')
        self.assertEqual(restore_res.status_code, 200)
        self.assertEqual(restore_res.json()['song']['title'], 'TEST UNDO SONG')

        # Cleanup test song
        self.client.delete(f'/api/songs/{del_song_uuid}')

def run_tests():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestRepertoireScoping)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    assert result.wasSuccessful()

if __name__ == '__main__':
    run_tests()

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

        # 5. Test Soft Delete & Restore with Admin Protection
        song_create_res = self.client.post('/api/songs', json={
            'title': 'TEST UNDO SONG',
            'artist': 'Band',
            'key_current': 'G',
            'aml_content': '[SOL]Test'
        })
        del_song_uuid = song_create_res.json()['song']['uuid']

        # Verify newly created/imported song goes strictly into personal repertoire, NEVER in official
        from api_server import storage
        all_reps = storage.list_repertoires()
        official_rep = next(r for r in all_reps if r.is_official)
        self.assertNotIn(del_song_uuid, official_rep.song_uuids, "Imported/new song must NEVER go directly to official repertoire")

        # Promote to Official Repertoire to test official song deletion protection
        promote_to_off = self.client.post('/api/repertoires/promote-song', json={'song_uuid': del_song_uuid, 'user_email': 'danyposta@gmail.com'})
        self.assertEqual(promote_to_off.status_code, 200)
        target_del_uuid = promote_to_off.json().get('song_uuid') or del_song_uuid

        # Non-admin musician cannot delete song belonging to Official Repertoire
        del_forbidden = self.client.delete(f'/api/songs/{target_del_uuid}?user_email=acicchelli65@gmail.com')
        self.assertEqual(del_forbidden.status_code, 403, "Non-admin must get 403 when deleting official song")

        # Admin can delete song from Official Repertoire
        del_res = self.client.delete(f'/api/songs/{target_del_uuid}?user_email=danyposta@gmail.com')
        self.assertEqual(del_res.status_code, 200)
        restore_res = self.client.post(f'/api/songs/{target_del_uuid}/restore')
        self.assertEqual(restore_res.status_code, 200)
        self.assertEqual(restore_res.json()['song']['title'], 'TEST UNDO SONG')

        # Cleanup test song (as admin)
        self.client.delete(f'/api/songs/{target_del_uuid}?user_email=danyposta@gmail.com')
        from api_server import storage
        all_reps = storage.list_repertoires()
        official_rep = next(r for r in all_reps if r.is_official)
        if target_del_uuid in official_rep.song_uuids:
            official_rep.song_uuids.remove(target_del_uuid)
            storage.save_repertoire(official_rep, 'admin', 'Admin')
        if getattr(storage, 'turso_client', None) and storage.turso_client.is_configured:
            storage.turso_client.push_repertoires([r.to_dict() for r in storage.list_repertoires()])
            storage.turso_client.soft_delete_song(target_del_uuid)
        storage.purge_song_permanently(target_del_uuid)

    def test_imported_song_never_goes_to_official_repertoire_without_promotion(self):
        """Strict Rule: New or imported songs NEVER go to the official band repertoire directly.
        They must always be placed into the user's personal repertoire, and enter official ONLY via promotion.
        """
        from api_server import storage
        official_rep = next(r for r in storage.list_repertoires() if r.is_official)
        official_count_before = len(official_rep.song_uuids)

        # 1. Create/import song without specifying repertoire
        res1 = self.client.post('/api/songs', json={
            'title': 'NUOVO BRANO IMPORT TEST 1',
            'artist': 'Test Band',
            'user_email': 'acicchelli65@gmail.com',
            'user_name': 'Cico'
        })
        self.assertEqual(res1.status_code, 200)
        song1_uuid = res1.json()['song']['uuid']

        # Verify not in official
        official_rep = next(r for r in storage.list_repertoires() if r.is_official)
        self.assertNotIn(song1_uuid, official_rep.song_uuids)
        self.assertEqual(len(official_rep.song_uuids), official_count_before)

        # 2. Try to directly target official repertoire during import/creation
        res2 = self.client.post('/api/songs', json={
            'title': 'NUOVO BRANO IMPORT TEST 2',
            'artist': 'Test Band',
            'repertoire_uuid': official_rep.uuid,
            'user_email': 'acicchelli65@gmail.com',
            'user_name': 'Cico'
        })
        self.assertEqual(res2.status_code, 200)
        song2_uuid = res2.json()['song']['uuid']

        # Verify song2 was intercepted and NOT placed in official
        official_rep = next(r for r in storage.list_repertoires() if r.is_official)
        self.assertNotIn(song2_uuid, official_rep.song_uuids)
        self.assertEqual(len(official_rep.song_uuids), official_count_before)

        # 3. Promote song1 to official
        prom_res = self.client.post('/api/repertoires/promote-song', json={
            'song_uuid': song1_uuid,
            'user_email': 'acicchelli65@gmail.com',
            'user_name': 'Cico'
        })
        self.assertEqual(prom_res.status_code, 200)

        # Now song1 MUST be in official
        official_rep = next(r for r in storage.list_repertoires() if r.is_official)
        self.assertIn(song1_uuid, official_rep.song_uuids)
        self.assertEqual(len(official_rep.song_uuids), official_count_before + 1)

        # Cleanup
        self.client.delete(f'/api/songs/{song1_uuid}?user_email=danyposta@gmail.com')
        self.client.delete(f'/api/songs/{song2_uuid}?user_email=danyposta@gmail.com')
        all_reps = storage.list_repertoires()
        official_rep = next(r for r in all_reps if r.is_official)
        if song1_uuid in official_rep.song_uuids:
            official_rep.song_uuids.remove(song1_uuid)
            storage.save_repertoire(official_rep, 'admin', 'Admin')
        if getattr(storage, 'turso_client', None) and storage.turso_client.is_configured:
            storage.turso_client.push_repertoires([r.to_dict() for r in storage.list_repertoires()])
            storage.turso_client.soft_delete_song(song1_uuid)
            storage.turso_client.soft_delete_song(song2_uuid)
        storage.purge_song_permanently(song1_uuid)
        storage.purge_song_permanently(song2_uuid)

def run_tests():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestRepertoireScoping)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    assert result.wasSuccessful()

if __name__ == '__main__':
    run_tests()

import unittest
from fastapi.testclient import TestClient
from api_server import app

def run_tests():
    client = TestClient(app)

    # 1. Test Repertoire Visibility for Musician vs Admin
    res_cico = client.get('/api/repertoires?user_email=acicchelli65@gmail.com')
    assert res_cico.status_code == 200, res_cico.text
    reps_cico = res_cico.json()
    rep_names_cico = [r['name'] for r in reps_cico]
    print('Cico visible repertoires:', rep_names_cico)
    assert 'Repertorio Ufficiale Band' in rep_names_cico, 'Missing official rep for Cico'
    assert 'Cico' in rep_names_cico, 'Missing personal rep for Cico'
    assert 'Daniele' not in rep_names_cico, 'Daniele personal rep leaked to Cico!'

    res_admin = client.get('/api/repertoires?user_email=danyposta@gmail.com')
    assert res_admin.status_code == 200, res_admin.text
    reps_admin = res_admin.json()
    rep_names_admin = [r['name'] for r in reps_admin]
    print('Admin visible repertoires:', rep_names_admin)
    assert 'Repertorio Ufficiale Band' in rep_names_admin
    assert 'Daniele' in rep_names_admin
    assert 'Cico' in rep_names_admin

    # 2. Test Add Song to Setlist endpoint
    setlists = client.get('/api/setlists').json()
    if not setlists:
        s_res = client.post('/api/setlists', json={'title': 'Scaletta Test', 'items': []})
        setlists = [s_res.json()['setlist']]

    target_setlist = setlists[0]
    songs = client.get('/api/songs').json()
    assert len(songs) > 0, 'No songs found'
    test_song = songs[0]

    add_res = client.post(f"/api/setlists/{target_setlist['uuid']}/songs/{test_song['uuid']}")
    assert add_res.status_code == 200, add_res.text
    assert add_res.json()['song_title'] == test_song['title']
    print('Add song to setlist test passed!')

    # 3. Test Promote Song
    promote_res = client.post('/api/repertoires/promote-song', json={'song_uuid': test_song['uuid']})
    assert promote_res.status_code == 200, promote_res.text
    print('Promote song test passed!')

    # 4. Test Soft Delete & Restore
    song_create_res = client.post('/api/songs', json={
        'title': 'TEST UNDO SONG',
        'artist': 'Band',
        'key_current': 'G',
        'aml_content': '[SOL]Test'
    })
    del_song_uuid = song_create_res.json()['song']['uuid']
    del_res = client.delete(f'/api/songs/{del_song_uuid}')
    assert del_res.status_code == 200
    restore_res = client.post(f'/api/songs/{del_song_uuid}/restore')
    assert restore_res.status_code == 200
    assert restore_res.json()['song']['title'] == 'TEST UNDO SONG'
    print('Delete & Undo Restore test passed!')

    # Cleanup test song
    client.delete(f'/api/songs/{del_song_uuid}')
    print('\nALL VERIFICATION TESTS COMPLETED WITH 100% SUCCESS!')

if __name__ == '__main__':
    run_tests()

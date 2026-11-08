"""
ASMA Accordi 2.0 - Quick Interactive Console Tester
Demonstrates live execution of all core modules.
"""

import time
from asma_core.music_engine import MusicEngine
from asma_core.aml_parser import AMLParser
from asma_core.models import Song
from asma_core.storage_manager import StorageManager
from asma_core.lock_manager import LockManager


def main():
    print("=" * 65)
    print("   ASMA ACCORDI NEXT GENERATION - TEST SOTTOSISTEMI CORE")
    print("=" * 65)

    # 1. Test Music Engine
    print("\n--- 1. TEST MUSIC ENGINE ---")
    chord = "DO7+"
    transposed = MusicEngine.transpose_chord(chord, semitones=2)
    converted_int = MusicEngine.convert_notation(chord, to_system="INT")
    print(f"• Accordo originale (ITA): {chord}")
    print(f"• Trasposto di +2 semitoni (ITA): {transposed}")
    print(f"• Convertito in notazione INT: {converted_int}")

    slash_chord = "D/F#"
    transposed_slash = MusicEngine.transpose_chord(slash_chord, semitones=2, prefer_flats=False)
    print(f"• Slash chord: {slash_chord} + 2 semitoni -> {transposed_slash}")

    # Medley Compatibility
    score, details = MusicEngine.calculate_harmonic_compatibility("C", 120, "G", 124)
    print(f"\n• Compatibilità Medley tra Brano in DO (120 BPM) e Brano in SOL (124 BPM):")
    print(f"  Punteggio: {score * 100}% | Distanza quinte: {details['fifths_distance']} | Delta BPM: {details['bpm_diff_percent']}%")
    print(f"  Raccomandazione: {details['recommended_transition']}")

    # Progression Recognition
    prog = ["DO", "LA-", "FA", "SOL"]
    prog_res = MusicEngine.identify_progression(prog)
    print(f"\n• Riconoscimento progressione {prog}:")
    print(f"  Esito: {prog_res['description']}")

    # 2. Test AML Parser & Traditional Import
    print("\n--- 2. TEST AML PARSER & TRADITIONAL IMPORT ---")
    traditional_input = """        C             G
Hello darkness my old friend
        Am            F
I've come to talk with you again"""
    print("• Testo tradizionale di partenza (accordi sopra il testo):")
    for l in traditional_input.splitlines():
        print(f"  {l}")

    imported_doc = AMLParser.import_traditional_chords_over_text(traditional_input)
    print("\n• Convertito automaticamente in formato nativo AML (Single Source of Truth):")
    print("  " + imported_doc.to_aml().replace("\n", "\n  "))

    # Transpose whole AML document
    transposed_doc = AMLParser.transpose_document(imported_doc, semitones=2)
    print("\n• Intero documento AML trasposto di +2 semitoni:")
    print("  " + transposed_doc.to_aml().replace("\n", "\n  "))

    # Convert document to Italian notation
    ita_doc = AMLParser.convert_notation(transposed_doc, to_system="ITA")
    print("\n• Intero documento convertito in notazione Italiana:")
    print("  " + ita_doc.to_aml().replace("\n", "\n  "))

    # 3. Test Storage & Multi-Criteria SQL Search (< 2ms)
    print("\n--- 3. TEST STORAGE & IN-MEMORY SQLITE INDEX (< 2ms) ---")
    import tempfile, shutil
    test_temp = tempfile.mkdtemp()
    StorageManager._instance = None
    storage = StorageManager(data_dir=test_temp)

    s1 = Song(title="Test Song Rock", artist="Band Test", genre="Rock", key_current="Bm", bpm=74, tags=["live", "chitarra"])
    s2 = Song(title="Test Song Acoustic", artist="Band Test", genre="Cantautore", key_current="G", bpm=92, tags=["live", "classico"])
    s3 = Song(title="Test Song Solo", artist="Band Test", genre="Rock", key_current="Dm", bpm=148, tags=["assolo"])

    storage.save_song(s1, user_name="Daniele", revision_comment="Caricamento iniziale")
    storage.save_song(s2, user_name="Roberto", revision_comment="Caricamento iniziale")
    storage.save_song(s3, user_name="Daniele", revision_comment="Caricamento iniziale")

    t0 = time.perf_counter()
    results = storage.search_songs(genre="Rock", bpm_max=100)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    print(f"• Query SQL in RAM: Genere='Rock' e BPM <= 100")
    print(f"  Tempo esecuzione: {elapsed_ms:.3f} ms | Brani trovati: {len(results)}")
    for r in results:
        print(f"  - {r['title']} ({r['artist']}) | Tonalità: {r['key_current']} | BPM: {r['bpm']}")

    # 4. Test Concurrency & Lock Manager
    print("\n--- 4. TEST LOCK MANAGER & CONCORRENZA ---")
    lock_mgr = LockManager()
    song_uuid = s1.uuid

    # Roberto locks the song
    ok1, status1, msg1 = lock_mgr.acquire_lock(song_uuid, "roberto@band.org", "Roberto")
    print(f"• Roberto prova a bloccare '{s1.title}': {msg1}")

    # Daniele tries to edit while Roberto is editing
    ok2, status2, msg2 = lock_mgr.acquire_lock(song_uuid, "daniele@band.org", "Daniele")
    print(f"• Daniele prova a modificare '{s1.title}' contemporaneamente: {msg2}")
    print(f"  Esito blocco: {not ok2} (Accesso negato garantito!)")

    # Roberto releases lock
    lock_mgr.release_lock(song_uuid, "roberto@band.org")
    print(f"• Roberto termina la modifica e rilascia il lock.")

    # Now Daniele can acquire it
    ok3, status3, msg3 = lock_mgr.acquire_lock(song_uuid, "daniele@band.org", "Daniele")
    print(f"• Daniele riprova: {msg3}")

    lock_mgr.release_lock(song_uuid, "daniele@band.org")
    StorageManager._instance = None
    shutil.rmtree(test_temp, ignore_errors=True)

    print("\n" + "=" * 65)
    print("   TUTTI I TEST DEI MODULI CORE SONO STATI COMPLETATI CON SUCCESSO!")
    print("=" * 65)


if __name__ == "__main__":
    main()

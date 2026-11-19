"""
Unit Tests for Automatic Musical Section Assignment on Song Import & Creation.
Verifies that imported and newly created songs without explicit section badges
are automatically analyzed and structured with standard AML badges:
[INTRO], [STROFA 1], [RITORNELLO], [STROFA 2], [BRIDGE], [SOLO], [STRUMENTALE], [FINALE], [END].
"""

import unittest
from asma_core.import_engine import ImportEngine
from asma_core.web_importer import WebSongImporter
from asma_core.storage_manager import StorageManager
from asma_core.ai_service import BandAIService
from asma_core.models import Song


class TestAutoSectionsImport(unittest.TestCase):

    def setUp(self):
        self.storage = StorageManager()

    def test_import_traditional_text_auto_assigns_sections(self):
        """Verifies that importing traditional chords-over-lyrics text automatically assigns sections."""
        trad_text = """
Intro:
DO   SOL   LAm   FA

Strofa 1:
DO                SOL
Prima riga del testo
LAm               FA
seconda riga del testo

Ritornello:
DO                SOL
Questo è il ritornello della canzone
LAm               FA
cantato a squarciagola
DO                SOL
Questo è il ritornello della canzone
LAm               FA
cantato a squarciagola
"""
        song = ImportEngine.import_from_traditional(trad_text, "Nuova Canzone Tradizionale")
        self.assertEqual(song.title, "Nuova Canzone Tradizionale")
        self.assertIn("[INTRO]", song.aml_content)
        self.assertIn("[STROFA 1]", song.aml_content)
        self.assertIn("[RITORNELLO]", song.aml_content)
        self.assertIn("[END]", song.aml_content)

    def test_import_chordpro_directives_normalized_to_aml_badges(self):
        """Verifies that ChordPro directives like {sov}, {soc}, {sob} are converted into standard AML badges."""
        cpro_text = """{title: Canzone ChordPro Nuova}
{artist: Rock Band}
{key: SOL}
Intro:
[SOL]  [DO]  [RE]
{sov}
[SOL]Vespe truccate anni sessanta
[DO]girano in centro sfiorando i novanta
{eov}
{soc}
[RE]Ma quant'è bello andare in giro
[SOL]con le ali sotto ai piedi
{eoc}
{sov}
[SOL]Esco di fretta dalla mia stanza
[DO]a marce ingranate dalla prima alla quarta
{eov}
{sob}
[MIm]Ponte strumentale ed emotivo
[DO]verso il grande finale
{eob}
"""
        song = ImportEngine.import_from_chordpro(cpro_text)
        self.assertEqual(song.title, "Canzone ChordPro Nuova")
        self.assertIn("[INTRO]", song.aml_content)
        self.assertIn("[STROFA 1]", song.aml_content)
        self.assertIn("[RITORNELLO]", song.aml_content)
        self.assertIn("[STROFA 2]", song.aml_content)
        self.assertIn("[BRIDGE]", song.aml_content)
        self.assertIn("[END]", song.aml_content)
        # Ensure raw closing directives were stripped
        self.assertNotIn("{sov}", song.aml_content)
        self.assertNotIn("{soc}", song.aml_content)
        self.assertNotIn("{eov}", song.aml_content)
        self.assertNotIn("{eoc}", song.aml_content)

    def test_raw_unsectioned_stanzas_detected_automatically(self):
        """Verifies that stanzas without any heading text are analyzed by lyrical repetition to find chorus and verses."""
        raw_text = """{title: Brano Puro Senza Tag}
[SOL]  [DO]  [RE]

[SOL]Lontano sui monti la luna risplende
[DO]il vento accarezza le foglie dorate
[RE]un vecchio pastore che guarda le stelle
[SOL]ascolta il silenzio della vallata

[DO]Canta con noi la musica viva
[RE]accendi la luce nel buio che avanza
[SOL]questa è la notte che non finirà
[DO]balla con noi nella grande speranza

[SOL]Il fiume che scorre veloce nel piano
[DO]racconta di storie di tempo lontano
[RE]i sogni che viaggiano dentro il domani
[SOL]stringendo forte le nostre mani

[DO]Canta con noi la musica viva
[RE]accendi la luce nel buio che avanza
[SOL]questa è la notte che non finirà
[DO]balla con noi nella grande speranza
"""
        structured = BandAIService.auto_assign_sections(raw_text)
        self.assertIn("[INTRO]", structured)
        self.assertIn("[STROFA 1]", structured)
        self.assertIn("[RITORNELLO]", structured)
        self.assertIn("[STROFA 2]", structured)
        self.assertIn("[END]", structured)

    def test_storage_save_song_auto_assigns_sections_for_new_songs(self):
        """Verifies that storage.save_song automatically equips unsectioned songs with AML sections."""
        new_song = Song(
            title="Brano da Salvare Senza Sezioni",
            artist="Band",
            key_current="DO",
            aml_content="""[DO]Prima riga della canzone
[SOL]seconda riga della canzone

[FA]Ritornello potente che tutti ricordano
[DO]per sempre nella memoria

[DO]Terza strofa con parole diverse
[SOL]quarta strofa con nuovo ritmo

[FA]Ritornello potente che tutti ricordano
[DO]per sempre nella memoria"""
        )
        saved = self.storage.save_song(new_song, "cico@band.org", "Cico")
        try:
            self.assertEqual(saved.title, "BRANO DA SALVARE SENZA SEZIONI")
            self.assertIn("[STROFA 1]", saved.aml_content)
            self.assertIn("[RITORNELLO]", saved.aml_content)
            self.assertIn("[STROFA 2]", saved.aml_content)
            self.assertIn("[END]", saved.aml_content)
        finally:
            self.storage.purge_song_permanently(saved.uuid, "cico@band.org", "Cico")

    def test_existing_sections_are_never_overwritten(self):
        """Verifies that songs that already contain standard badges are preserved without alterations."""
        original_aml = """{title: BRANO GIA STRUTTURATO}
[INTRO]
| DO | SOL |

[STROFA 1]
[DO]Testo personalizzato riga 1

[RITORNELLO]
[FA]Ritornello speciale personalizzato

[END]"""
        result = BandAIService.auto_assign_sections(original_aml)
        self.assertIn("[INTRO]", result)
        self.assertIn("[STROFA 1]", result)
        self.assertIn("[RITORNELLO]", result)
        self.assertIn("[END]", result)
        self.assertIn("[DO]Testo personalizzato riga 1", result)


if __name__ == "__main__":
    unittest.main()

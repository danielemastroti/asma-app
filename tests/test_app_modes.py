import unittest
import os
import shutil
import tempfile
from asma_core.preferences_manager import PreferencesManager

class TestAppModes(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.pref_file = os.path.join(self.test_dir, "test_app_modes.json")
        self.mgr = PreferencesManager(filepath=self.pref_file, turso_client=None, force_new=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_app_mode_default_and_persistence(self):
        email = "cico@band.org"
        # Default when not set
        mode = self.mgr.get_user_preference(email, "app_mode", default="simplified")
        self.assertEqual(mode, "simplified")

        # Set to editing
        self.mgr.set_user_preference(email, "app_mode", "editing")
        self.assertEqual(self.mgr.get_user_preference(email, "app_mode"), "editing")

        # Reload fresh instance
        fresh = PreferencesManager(filepath=self.pref_file, turso_client=None, force_new=True)
        self.assertEqual(fresh.get_user_preference(email, "app_mode"), "editing")

        # Set back to simplified
        fresh.set_user_preference(email, "app_mode", "simplified")
        self.assertEqual(fresh.get_user_preference(email, "app_mode"), "simplified")

    def test_simplified_menu_items_has_no_duplicate_logout(self):
        """Verifies simplified menu contains only the 5 core sections without duplicate logout."""
        with open("app.py", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn('"📖 Manuale & Changelog"', content)
        # Verify that SIMPLIFIED_MENU_ITEMS does not have "🚪 Logout"
        simp_def = content.split("SIMPLIFIED_MENU_ITEMS = [")[1].split("]")[0]
        self.assertNotIn("Logout", simp_def)
        # Should have 5 items
        items = [line.strip() for line in simp_def.splitlines() if line.strip() and not line.strip().startswith("#")]
        self.assertEqual(len(items), 5)

    def test_simplified_mode_repertoire_selector_present(self):
        """Verifies simplified mode includes repertoire filtering and selection."""
        with open("app.py", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn('simp_repertoire_filter', content)
        self.assertIn('📁 Seleziona Repertorio:', content)
        self.assertIn('🌐 Tutti i Repertori', content)
        self.assertIn('st.session_state["selected_repertoire_uuid"] = selected_rep_uuid', content)



if __name__ == '__main__':
    unittest.main()

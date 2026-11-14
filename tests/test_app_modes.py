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
        """Verifies PWA navbar contains core sections and single header logout button."""
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            content = f.read()
        header = content.split('<header class="app-header">')[1].split('</header>')[0]
        self.assertEqual(header.count('onclick="logoutGoogle()"'), 1)

    def test_simplified_mode_repertoire_selector_present(self):
        """Verifies simplified mode includes repertoire filtering in PWA."""
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn('repertoire-chips', content)
        with open("frontend/app.js", "r", encoding="utf-8") as f:
            js = f.read()
        self.assertIn('renderRepertoireChips', js)
        self.assertIn('setAppMode', js)



if __name__ == '__main__':
    unittest.main()

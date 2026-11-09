"""
Unit tests for PreferencesManager with Turso Cloud persistence and local cache.
Conforms to SRS Cap. 13, 17, 18, 19.16.
"""

import os
import shutil
import tempfile
import unittest
from asma_core.preferences_manager import PreferencesManager
from asma_core.device_manager import DeviceManager


class TestPreferencesManager(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.pref_file = os.path.join(self.test_dir, "test_user_device_prefs.json")
        # Initialize isolated manager without cloud sync for fast isolated testing
        self.manager = PreferencesManager(filepath=self.pref_file, turso_client=None, force_new=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_default_device_preferences(self):
        """Verifies that unconfigured device gets optimal hardware profile defaults."""
        user = "testuser@band.it"
        huawei_name = 'Huawei MatePad / Tablet (10.4"/11")'
        prefs_huawei = self.manager.get_preferences(user, huawei_name)
        prefs_pixel = self.manager.get_preferences(user, "Pixel 8 pro")

        self.assertIn("layout_font_size", prefs_huawei)
        self.assertIn("layout_columns", prefs_huawei)
        # Huawei tablet default columns is 2
        self.assertEqual(prefs_huawei["layout_columns"], 2)
        # Pixel smartphone default columns is 1
        self.assertEqual(prefs_pixel["layout_columns"], 1)

    def test_save_and_retrieve_preferences(self):
        """Verifies saving layout modifications persists to cache and reloads correctly."""
        user = "danyposta@gmail.com"
        device = 'Huawei MatePad / Tablet (10.4"/11")'

        # Update font size and margins
        self.manager.save_preferences(user, device, {
            "layout_font_size": 20.5,
            "layout_font_size_chords": 22.0,
            "layout_margin_lateral": 14.0,
            "layout_columns": 2,
            "layout_color_text": "#222222",
            "layout_color_chords": "#FF0000"
        })

        reloaded = self.manager.get_preferences(user, device)
        self.assertEqual(reloaded["layout_font_size"], 20.5)
        self.assertEqual(reloaded["layout_font_size_chords"], 22.0)
        self.assertEqual(reloaded["layout_margin_lateral"], 14.0)
        self.assertEqual(reloaded["layout_columns"], 2)
        self.assertEqual(reloaded["layout_color_text"], "#222222")
        self.assertEqual(reloaded["layout_color_chords"], "#FF0000")

    def test_multi_device_partitioning_per_user(self):
        """Verifies a user can have independent preferences across multiple devices."""
        user = "danyposta@gmail.com"
        tablet = 'Huawei MatePad / Tablet (10.4"/11")'
        phone = "Pixel 8 pro"

        # Set tablet to 2 columns, large fonts
        self.manager.save_preferences(user, tablet, {
            "layout_columns": 2,
            "layout_font_size": 18.0
        })

        # Set phone to 1 column, small fonts
        self.manager.save_preferences(user, phone, {
            "layout_columns": 1,
            "layout_font_size": 10.5
        })

        tablet_prefs = self.manager.get_preferences(user, tablet)
        phone_prefs = self.manager.get_preferences(user, phone)

        self.assertEqual(tablet_prefs["layout_columns"], 2)
        self.assertEqual(tablet_prefs["layout_font_size"], 18.0)

        self.assertEqual(phone_prefs["layout_columns"], 1)
        self.assertEqual(phone_prefs["layout_font_size"], 10.5)

    def test_last_active_device_tracking(self):
        """Verifies setting and retrieving the last active device for a user."""
        user = "acicchelli65@gmail.com"
        huawei_name = 'Huawei MatePad / Tablet (10.4"/11")'
        self.manager.set_last_active_device(user, huawei_name)
        self.assertEqual(self.manager.get_last_active_device(user), huawei_name)

        self.manager.set_last_active_device(user, "Foglio a 4 stampabile")
        self.assertEqual(self.manager.get_last_active_device(user), "Foglio a 4 stampabile")

    def test_persistence_across_instances(self):
        """Verifies preferences persist to file and load in a fresh instance."""
        user = "maurobovolenta4@gmail.com"
        device = "Pixel 8 pro"

        self.manager.save_preferences(user, device, {"layout_font_size": 14.5})

        # Create new manager pointing to the same file
        new_manager = PreferencesManager(filepath=self.pref_file, turso_client=None, force_new=True)
        loaded_prefs = new_manager.get_preferences(user, device)
        self.assertEqual(loaded_prefs["layout_font_size"], 14.5)

    def test_user_table_column_preferences(self):
        """Verifies storing and reloading user-specific table column preferences (e.g., hiding UUID)."""
        user = "marcoerario2@gmail.com"

        # Initially no preference, returns default
        default_cols = ["Titolo", "Artista", "Tonalità", "BPM", "Repertori"]
        loaded = self.manager.get_user_preference(user, "smistamento_columns", default=default_cols)
        self.assertEqual(loaded, default_cols)

        # User customizes columns to include UUID or remove UUID
        custom_cols = ["Titolo", "Artista", "Tonalità"]
        self.manager.set_user_preference(user, "smistamento_columns", custom_cols)

        # Fresh instance reloads from disk
        new_manager = PreferencesManager(filepath=self.pref_file, turso_client=None, force_new=True)
        persisted = new_manager.get_user_preference(user, "smistamento_columns")
        self.assertEqual(persisted, custom_cols)


if __name__ == '__main__':
    unittest.main()

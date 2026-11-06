"""
Unit Tests for DeviceManager and Hardware Profiles
"""

import unittest
import tempfile
import os
import shutil
from asma_core.device_manager import DeviceManager, DEFAULT_DEVICES
from asma_core.models import DeviceProfile
from asma_core.pdf_engine import PDFEngine


class TestDeviceManager(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.data_file = os.path.join(self.test_dir, "device_profiles.json")
        DeviceManager._instance = None
        self.mgr = DeviceManager(data_file=self.data_file)

    def tearDown(self):
        DeviceManager._instance = None
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_default_devices_initialized(self):
        devices = self.mgr.list_devices()
        self.assertEqual(len(devices), 9)
        names = [d.name for d in devices]

        expected_names = [
            "Pixel 8 pro",
            "IPad 10.2\" (7/8/9 gen) & pro 2019",
            "Samsung Galaxy tab s7,s8,s9 & A9+",
            "Foglio a 4 stampabile",
            "Xiaomi pad 8 pro",
            "Android smartphone generico",
            "Iphone smartphone generico",
            "oppo find x5",
            "Huawei MatePad / Tablet (10.4\"/11\")"
        ]
        for exp in expected_names:
            self.assertIn(exp, names)

    def test_add_and_remove_device_by_admin(self):
        new_dev = DeviceProfile(
            name="Stage Monitor 15.6",
            target_device="tablet",
            device_type="tablet",
            width_mm=345.0,
            height_mm=195.0,
            orientation="landscape",
            columns=2
        )
        added = self.mgr.add_device(new_dev, user_email="admin@band.org", user_name="Admin")
        self.assertIsNotNone(added.uuid)

        # Check retrieval
        fetched = self.mgr.get_device(added.uuid)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "Stage Monitor 15.6")

        # Test duplicate name prevention
        with self.assertRaises(ValueError):
            self.mgr.add_device(new_dev)

        # Test remove
        removed = self.mgr.remove_device(added.uuid, user_email="admin@band.org", user_name="Admin")
        self.assertTrue(removed)
        self.assertIsNone(self.mgr.get_device(added.uuid))

    def test_reset_defaults(self):
        devices = self.mgr.list_devices()
        self.mgr.remove_device(devices[0].uuid)
        self.assertEqual(len(self.mgr.list_devices()), 8)

        # Reset
        restored = self.mgr.reset_defaults()
        self.assertEqual(len(restored), 9)

    def test_pdf_engine_page_size_with_device_profile(self):
        pixel = self.mgr.get_device_by_name("Pixel 8 pro")
        self.assertIsNotNone(pixel)
        w, h = PDFEngine.get_page_size(pixel)
        self.assertGreater(h, w)  # portrait

        samsung = self.mgr.get_device_by_name("Samsung Galaxy tab s7,s8,s9 & A9+")
        self.assertIsNotNone(samsung)
        sw, sh = PDFEngine.get_page_size(samsung)
        self.assertGreater(sw, sh)  # landscape


if __name__ == "__main__":
    unittest.main()

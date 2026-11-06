"""
ASMA Accordi Next Generation - Device Profiles Manager
Manages hardware and screen profiles for tablets, smartphones, and printable media.
Conforms to SRS Cap. 5.3, 10.14, 16.14 and Blueprint Section 9.
"""

from __future__ import annotations
import os
import json
import threading
from typing import List, Dict, Any, Optional
from asma_core.models import DeviceProfile, generate_uuid
from asma_core.audit_logger import AuditLogger


DEFAULT_DEVICES = [
    {
        "name": "Pixel 8 pro",
        "target_device": "smartphone",
        "device_type": "smartphone",
        "width_mm": 76.5,
        "height_mm": 162.6,
        "orientation": "portrait",
        "columns": 1,
        "font_size_lyrics": 10.0,
        "font_size_chords": 11.0,
        "margin_top_mm": 6.0,
        "margin_bottom_mm": 6.0,
        "margin_left_mm": 6.0,
        "margin_right_mm": 6.0,
        "is_custom": False
    },
    {
        "name": "IPad 10.2\" (7/8/9 gen) & pro 2019",
        "target_device": "ipad",
        "device_type": "tablet",
        "width_mm": 174.1,
        "height_mm": 250.6,
        "orientation": "portrait",
        "columns": 2,
        "font_size_lyrics": 12.0,
        "font_size_chords": 13.0,
        "margin_top_mm": 10.0,
        "margin_bottom_mm": 10.0,
        "margin_left_mm": 10.0,
        "margin_right_mm": 10.0,
        "is_custom": False
    },
    {
        "name": "Samsung Galaxy tab s7,s8,s9 & A9+",
        "target_device": "tablet",
        "device_type": "tablet",
        "width_mm": 165.8,
        "height_mm": 253.8,
        "orientation": "landscape",
        "columns": 2,
        "font_size_lyrics": 11.5,
        "font_size_chords": 12.5,
        "margin_top_mm": 8.0,
        "margin_bottom_mm": 8.0,
        "margin_left_mm": 8.0,
        "margin_right_mm": 8.0,
        "is_custom": False
    },
    {
        "name": "Foglio a 4 stampabile",
        "target_device": "pc_a4",
        "device_type": "printable_a4",
        "width_mm": 210.0,
        "height_mm": 297.0,
        "orientation": "portrait",
        "columns": 1,
        "font_size_lyrics": 12.0,
        "font_size_chords": 13.0,
        "margin_top_mm": 12.0,
        "margin_bottom_mm": 12.0,
        "margin_left_mm": 12.0,
        "margin_right_mm": 12.0,
        "is_custom": False
    },
    {
        "name": "Xiaomi pad 8 pro",
        "target_device": "tablet",
        "device_type": "tablet",
        "width_mm": 166.0,
        "height_mm": 254.0,
        "orientation": "landscape",
        "columns": 2,
        "font_size_lyrics": 11.5,
        "font_size_chords": 12.5,
        "margin_top_mm": 8.0,
        "margin_bottom_mm": 8.0,
        "margin_left_mm": 8.0,
        "margin_right_mm": 8.0,
        "is_custom": False
    },
    {
        "name": "Android smartphone generico",
        "target_device": "smartphone",
        "device_type": "smartphone",
        "width_mm": 72.0,
        "height_mm": 160.0,
        "orientation": "portrait",
        "columns": 1,
        "font_size_lyrics": 10.0,
        "font_size_chords": 11.0,
        "margin_top_mm": 6.0,
        "margin_bottom_mm": 6.0,
        "margin_left_mm": 6.0,
        "margin_right_mm": 6.0,
        "is_custom": False
    },
    {
        "name": "Iphone smartphone generico",
        "target_device": "smartphone",
        "device_type": "smartphone",
        "width_mm": 71.5,
        "height_mm": 147.0,
        "orientation": "portrait",
        "columns": 1,
        "font_size_lyrics": 10.0,
        "font_size_chords": 11.0,
        "margin_top_mm": 6.0,
        "margin_bottom_mm": 6.0,
        "margin_left_mm": 6.0,
        "margin_right_mm": 6.0,
        "is_custom": False
    },
    {
        "name": "oppo find x5",
        "target_device": "smartphone",
        "device_type": "smartphone",
        "width_mm": 72.6,
        "height_mm": 160.3,
        "orientation": "portrait",
        "columns": 1,
        "font_size_lyrics": 10.0,
        "font_size_chords": 11.0,
        "margin_top_mm": 6.0,
        "margin_bottom_mm": 6.0,
        "margin_left_mm": 6.0,
        "margin_right_mm": 6.0,
        "is_custom": False
    },
    {
        "name": "Huawei MatePad / Tablet (10.4\"/11\")",
        "target_device": "tablet",
        "device_type": "tablet",
        "width_mm": 154.96,
        "height_mm": 245.2,
        "orientation": "landscape",
        "columns": 2,
        "font_size_lyrics": 11.5,
        "font_size_chords": 12.5,
        "margin_top_mm": 8.0,
        "margin_bottom_mm": 8.0,
        "margin_left_mm": 8.0,
        "margin_right_mm": 8.0,
        "is_custom": False
    }
]


class DeviceManager:
    """Thread-safe persistent manager for user and hardware device profiles."""
    _instance: Optional[DeviceManager] = None
    _singleton_lock = threading.Lock()

    def __new__(cls, data_file: Optional[str] = None) -> DeviceManager:
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_manager(data_file)
            return cls._instance

    def _init_manager(self, data_file: Optional[str] = None) -> None:
        self._mutex = threading.Lock()
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self._file_path = data_file or os.path.join(base_dir, "data", "device_profiles.json")
        self._profiles: List[DeviceProfile] = []
        self._audit = AuditLogger()
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._file_path):
            try:
                with open(self._file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._profiles = [DeviceProfile.from_dict(d) for d in data]
            except Exception:
                self._initialize_defaults()
        else:
            self._initialize_defaults()

    def _initialize_defaults(self) -> None:
        self._profiles = []
        for def_data in DEFAULT_DEVICES:
            prof = DeviceProfile.from_dict(def_data)
            self._profiles.append(prof)
        self._save_to_disk()

    def _save_to_disk(self) -> None:
        os.makedirs(os.path.dirname(self._file_path), exist_ok=True)
        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump([p.to_dict() for p in self._profiles], f, indent=2, ensure_ascii=False)

    def list_devices(self) -> List[DeviceProfile]:
        """Returns all configured device profiles."""
        with self._mutex:
            return list(self._profiles)

    def get_device(self, uuid: str) -> Optional[DeviceProfile]:
        """Retrieves a device profile by its UUID."""
        with self._mutex:
            return next((p for p in self._profiles if p.uuid == uuid), None)

    def get_device_by_name(self, name: str) -> Optional[DeviceProfile]:
        """Retrieves a device profile by its display name (case-insensitive)."""
        with self._mutex:
            name_clean = name.strip().lower()
            return next((p for p in self._profiles if p.name.strip().lower() == name_clean), None)

    def add_device(
        self,
        device: DeviceProfile,
        user_email: str = "system",
        user_name: str = "System"
    ) -> DeviceProfile:
        """Adds a new device profile configured by an Admin."""
        with self._mutex:
            existing = next((p for p in self._profiles if p.name.strip().lower() == device.name.strip().lower()), None)
            if existing:
                raise ValueError(f"Un profilo dispositivo denominato '{device.name}' è già presente.")

            device.is_custom = True
            if not device.uuid:
                device.uuid = generate_uuid()
            self._profiles.append(device)
            self._save_to_disk()

        self._audit.log(
            "ADD_DEVICE",
            "DEVICE_PROFILE",
            device.uuid,
            user_email,
            user_name,
            {"name": device.name, "device_type": device.device_type, "width_mm": device.width_mm, "height_mm": device.height_mm}
        )
        return device

    def remove_device(
        self,
        device_uuid: str,
        user_email: str = "system",
        user_name: str = "System"
    ) -> bool:
        """Removes an existing device profile by UUID."""
        with self._mutex:
            target = next((p for p in self._profiles if p.uuid == device_uuid), None)
            if not target:
                return False

            if len(self._profiles) <= 1:
                raise ValueError("Impossibile eliminare l'ultimo dispositivo: deve rimanere almeno un profilo configurato.")

            self._profiles = [p for p in self._profiles if p.uuid != device_uuid]
            self._save_to_disk()

        self._audit.log(
            "REMOVE_DEVICE",
            "DEVICE_PROFILE",
            device_uuid,
            user_email,
            user_name,
            {"removed_device_name": target.name}
        )
        return True

    def reset_defaults(self, user_email: str = "system", user_name: str = "System") -> List[DeviceProfile]:
        """Restores the standard 8 required device profiles."""
        with self._mutex:
            self._initialize_defaults()
            self._save_to_disk()
            profiles_copy = list(self._profiles)

        self._audit.log("RESET_DEFAULT_DEVICES", "DEVICE_PROFILE", "all", user_email, user_name, {"count": len(profiles_copy)})
        return profiles_copy

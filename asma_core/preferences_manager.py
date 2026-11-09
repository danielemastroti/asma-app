"""
ASMA Accordi Next Generation - User & Multi-Device Preferences Engine
Persists hardware display profiles, layout customizations (font sizes, columns,
margins, colors, zoom) and user-level UI configurations (visible table columns,
filters) partitioned by User and Device in Turso Cloud + Local Cache.
Conforms to SRS Cap. 3, 5.3, 10.14, 16.14.
"""

from __future__ import annotations
import os
import json
import threading
from typing import Dict, Any, Optional, List
from asma_core.turso_client import TursoClient
from asma_core.device_manager import DeviceManager


class PreferencesManager:
    """
    Singleton manager for User & Multi-Device display and UI preferences.
    Guarantees that each user has independent profiles for each of their devices
    and persistent view preferences (such as table columns visibility) across logins.
    """
    _instance: Optional[PreferencesManager] = None
    _singleton_lock = threading.Lock()

    def __new__(
        cls,
        data_file: Optional[str] = None,
        turso_client: Optional[TursoClient] = None,
        force_new: bool = False,
        filepath: Optional[str] = None
    ) -> PreferencesManager:
        actual_file = data_file or filepath
        with cls._singleton_lock:
            if cls._instance is None or actual_file is not None or force_new:
                inst = super().__new__(cls)
                inst._init_manager(actual_file, turso_client)
                if actual_file is None and not force_new:
                    cls._instance = inst
                return inst
            return cls._instance

    def _init_manager(
        self,
        data_file: Optional[str] = None,
        turso_client: Optional[TursoClient] = None,
        filepath: Optional[str] = None
    ) -> None:
        actual_file = data_file or filepath
        self._mutex = threading.Lock()
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self._file_path = actual_file or os.path.join(base_dir, "data", "user_device_preferences.json")
        # Structure: {
        #   "user_email": {
        #       "last_active_device": "...",
        #       "devices": { "device_name": { ... } },
        #       "user_prefs": { "smistamento_columns": [...], ... }
        #   }
        # }
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.turso = turso_client if turso_client is not None else TursoClient()
        self._load_cache()
        self._sync_from_cloud()

    def _load_cache(self) -> None:
        if os.path.exists(self._file_path):
            try:
                with open(self._file_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}
        else:
            self._cache = {}

    def _save_cache(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._file_path), exist_ok=True)
            with open(self._file_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _sync_from_cloud(self) -> None:
        """Pulls all user-device preference records from Turso Cloud on startup."""
        if not self.turso.is_configured:
            return

        def _bg_pull():
            try:
                records = self.turso.fetch_all_user_preferences()
                with self._mutex:
                    for rec in records:
                        email = rec.get("email", "").lower().strip()
                        dev_name = rec.get("device_name", "")
                        if not email or not dev_name:
                            continue
                        if email not in self._cache:
                            self._cache[email] = {
                                "last_active_device": dev_name,
                                "devices": {},
                                "user_prefs": {}
                            }

                        if "user_prefs" not in self._cache[email]:
                            self._cache[email]["user_prefs"] = {}

                        if rec.get("is_last_active"):
                            self._cache[email]["last_active_device"] = dev_name

                        # Extract layout preferences
                        dev_prefs = {
                            "layout_font_size": rec.get("font_size_lyrics", 12),
                            "layout_font_size_chords": rec.get("font_size_chords", 13),
                            "layout_columns": rec.get("columns", 1),
                            "layout_margin_lateral": rec.get("margin_lateral_mm", 10),
                            "layout_margin_top": rec.get("margin_top_mm", 8),
                            "layout_margin_bottom": rec.get("margin_bottom_mm", 8),
                            "layout_color_text": rec.get("color_text", "#111111"),
                            "layout_color_chords": rec.get("color_chords", "#B71C1C"),
                            "layout_color_aml": rec.get("color_aml", "#4A148C"),
                            "ui_zoom_level": rec.get("zoom_level", 1.0),
                            "updated_at": rec.get("updated_at", "")
                        }

                        # Also retain any extra custom keys in dev_prefs and user_prefs
                        for k, v in rec.items():
                            if k not in dev_prefs and k not in (
                                "email", "device_name", "font_size_lyrics", "font_size_chords",
                                "columns", "margin_lateral_mm", "margin_top_mm", "margin_bottom_mm",
                                "color_text", "color_chords", "color_aml", "zoom_level",
                                "is_last_active", "updated_at", "extra_json"
                            ):
                                dev_prefs[k] = v
                                # If it's a user preference like table columns, populate user_prefs
                                if k.startswith("table_") or k.endswith("_columns") or k == "user_prefs":
                                    if k == "user_prefs" and isinstance(v, dict):
                                        self._cache[email]["user_prefs"].update(v)
                                    else:
                                        self._cache[email]["user_prefs"][k] = v

                        self._cache[email]["devices"][dev_name] = dev_prefs
                    self._save_cache()
            except Exception:
                pass

        t = threading.Thread(target=_bg_pull, daemon=True)
        t.start()

    def get_last_active_device(self, user_email: str) -> Optional[str]:
        """Returns the last active device used by the specified user."""
        email_clean = user_email.lower().strip()
        with self._mutex:
            if email_clean in self._cache:
                return self._cache[email_clean].get("last_active_device")
        return None

    def set_last_active_device(self, user_email: str, device_name: str) -> None:
        """Marks the specified device as active for this user and pushes to Turso."""
        email_clean = user_email.lower().strip()
        with self._mutex:
            if email_clean not in self._cache:
                self._cache[email_clean] = {
                    "last_active_device": device_name,
                    "devices": {},
                    "user_prefs": {}
                }
            else:
                self._cache[email_clean]["last_active_device"] = device_name
            self._save_cache()

        if self.turso.is_configured:
            def _push_active():
                try:
                    self.turso.set_last_active_device(email_clean, device_name)
                except Exception:
                    pass
            threading.Thread(target=_push_active, daemon=True).start()

    def get_preferences(self, user_email: str, device_name: str) -> Dict[str, Any]:
        """
        Retrieves all layout & typography preferences for a specific (user, device) pair.
        If no customization exists yet, defaults to the optimal hardware profile from DeviceManager.
        """
        email_clean = user_email.lower().strip()
        with self._mutex:
            user_data = self._cache.get(email_clean, {})
            dev_data = user_data.get("devices", {}).get(device_name)
            if dev_data:
                return dict(dev_data)

        # Generate base hardware defaults for this specific device
        dev_mgr = DeviceManager()
        base_dev = dev_mgr.get_device_by_name(device_name)
        f_size = base_dev.font_size_lyrics if base_dev else 12.0
        fc_size = base_dev.font_size_chords if base_dev else 13.0
        cols = base_dev.columns if base_dev else 1
        m_lat = base_dev.margin_left_mm if base_dev else 10.0
        m_top = base_dev.margin_top_mm if base_dev else 8.0
        m_bot = base_dev.margin_bottom_mm if base_dev else 8.0
        zoom = 0.82 if base_dev and "huawei" in base_dev.name.lower() else 1.0

        default_prefs = {
            "layout_font_size": f_size,
            "layout_font_size_chords": fc_size,
            "layout_columns": cols,
            "layout_margin_lateral": m_lat,
            "layout_margin_top": m_top,
            "layout_margin_bottom": m_bot,
            "layout_color_text": "#111111",
            "layout_color_chords": "#B71C1C",
            "layout_color_aml": "#4A148C",
            "ui_zoom_level": zoom
        }

        # Save seeded defaults to cache
        with self._mutex:
            if email_clean not in self._cache:
                self._cache[email_clean] = {
                    "last_active_device": device_name,
                    "devices": {},
                    "user_prefs": {}
                }
            self._cache[email_clean]["devices"][device_name] = dict(default_prefs)
            self._save_cache()

        return default_prefs

    def save_preferences(
        self,
        user_email: str,
        device_name: str,
        updated_prefs: Dict[str, Any]
    ) -> None:
        """
        Saves layout preferences for (user, device) in local cache and pushes to Turso Cloud.
        """
        email_clean = user_email.lower().strip()
        with self._mutex:
            if email_clean not in self._cache:
                self._cache[email_clean] = {
                    "last_active_device": device_name,
                    "devices": {},
                    "user_prefs": {}
                }
            if device_name not in self._cache[email_clean]["devices"]:
                self._cache[email_clean]["devices"][device_name] = {}

            self._cache[email_clean]["devices"][device_name].update(updated_prefs)
            self._cache[email_clean]["last_active_device"] = device_name
            full_prefs = dict(self._cache[email_clean]["devices"][device_name])
            self._save_cache()

        # Push to Turso Cloud
        if self.turso.is_configured:
            def _bg_push():
                try:
                    self.turso.push_user_device_preference(
                        email=email_clean,
                        device_name=device_name,
                        prefs=full_prefs,
                        is_last_active=True
                    )
                except Exception:
                    pass
            threading.Thread(target=_bg_push, daemon=True).start()

    def get_user_preference(self, user_email: str, key: str, default: Any = None) -> Any:
        """
        Retrieves a persistent generic user preference (such as table column visibility, filters, etc.).
        """
        email_clean = user_email.lower().strip()
        with self._mutex:
            u_data = self._cache.get(email_clean, {})
            u_prefs = u_data.get("user_prefs", {})
            if key in u_prefs:
                return u_prefs[key]

            # Fallback to checking active device extra
            act_dev = u_data.get("last_active_device")
            if act_dev and act_dev in u_data.get("devices", {}):
                dev_data = u_data["devices"][act_dev]
                if key in dev_data:
                    return dev_data[key]
        return default

    def set_user_preference(self, user_email: str, key: str, value: Any) -> None:
        """
        Saves a persistent generic user preference (e.g. table columns) and pushes to Turso Cloud.
        """
        email_clean = user_email.lower().strip()
        with self._mutex:
            if email_clean not in self._cache:
                self._cache[email_clean] = {
                    "last_active_device": "",
                    "devices": {},
                    "user_prefs": {}
                }
            if "user_prefs" not in self._cache[email_clean]:
                self._cache[email_clean]["user_prefs"] = {}

            self._cache[email_clean]["user_prefs"][key] = value

            # Also associate with active device so it syncs to Turso extra_json
            act_dev = self._cache[email_clean].get("last_active_device")
            if not act_dev and self._cache[email_clean].get("devices"):
                act_dev = list(self._cache[email_clean]["devices"].keys())[0]

            target_dev = None
            dev_prefs = None
            if act_dev:
                if act_dev not in self._cache[email_clean]["devices"]:
                    self._cache[email_clean]["devices"][act_dev] = {}
                self._cache[email_clean]["devices"][act_dev][key] = value
                target_dev = act_dev
                dev_prefs = dict(self._cache[email_clean]["devices"][act_dev])

            self._save_cache()

        if self.turso.is_configured and target_dev and dev_prefs:
            def _push_user_pref():
                try:
                    self.turso.push_user_device_preference(
                        email=email_clean,
                        device_name=target_dev,
                        prefs=dev_prefs,
                        is_last_active=True
                    )
                except Exception:
                    pass
            threading.Thread(target=_push_user_pref, daemon=True).start()

    def list_user_device_profiles(self, user_email: str) -> List[str]:
        """Returns list of device names configured for this user."""
        email_clean = user_email.lower().strip()
        with self._mutex:
            user_data = self._cache.get(email_clean, {})
            return list(user_data.get("devices", {}).keys())

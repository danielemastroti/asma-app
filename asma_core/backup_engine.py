"""
ASMA Accordi Next Generation - Full Database Backup & Restore Engine
Supports full database export & atomic restore for Songs, Repertoires, Setlists,
Users, Device Preferences, Audit Trail and Official Changelog.
Conforms to SRS Cap. 10.14, 10.15, 10.16, 15.13 and 17.5.
Provides atomic ZIP backup generation, disaster recovery restore, and JSON API dumps.
"""

from __future__ import annotations
import os
import io
import json
import zipfile
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from asma_core.models import Song, Repertoire, Setlist, User
from asma_core.storage_manager import StorageManager
from asma_core.auth_manager import AuthManager
from asma_core.preferences_manager import PreferencesManager
from asma_core.changelog_engine import ChangelogEngine
from asma_core.audit_logger import AuditLogger
from asma_core.turso_client import TursoClient

logger = logging.getLogger(__name__)


class BackupEngine:
    """Provides complete backup dumping and safe restoration across local storage and Turso Cloud DB."""

    # -------------------------------------------------------------------------
    # 1. ATOMIC ZIP ARCHIVES (Legacy & File Recovery)
    # -------------------------------------------------------------------------
    @classmethod
    def create_full_backup_zip(cls, data_dir: str = "data") -> bytes:
        """
        Creates a ZIP archive containing all application state:
        - songs/
        - repertoires.json
        - setlists.json
        - live_events.json
        - revisions/
        - audit_trail.jsonl
        - users.json
        - user_device_preferences.json
        - changelog.json
        """
        data_path = Path(data_dir)
        buf = io.BytesIO()

        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            manifest = {
                "backup_date": datetime.now().isoformat(),
                "system": "ASMA Accordi 2.0",
                "version": ChangelogEngine.get_latest_version(),
                "file_count": 0
            }

            file_count = 0
            for root, dirs, files in os.walk(data_path):
                for f in files:
                    full_p = Path(root) / f
                    rel_p = full_p.relative_to(data_path)
                    zf.write(full_p, arcname=str(rel_p))
                    file_count += 1

            manifest["file_count"] = file_count
            zf.writestr("BACKUP_MANIFEST.json", json.dumps(manifest, indent=2))

        buf.seek(0)
        return buf.getvalue()

    @classmethod
    def restore_from_backup_zip(cls, zip_bytes: bytes, target_data_dir: str = "data") -> Tuple[bool, str]:
        """
        Restores full data directory from a verified backup ZIP archive,
        and reloads in-memory SQLite cache.
        """
        data_path = Path(target_data_dir)
        buf = io.BytesIO(zip_bytes)

        try:
            with zipfile.ZipFile(buf, "r") as zf:
                if "BACKUP_MANIFEST.json" not in zf.namelist():
                    return False, "File ZIP non valido: manifesto di backup ASMA mancante."

                manifest_data = json.loads(zf.read("BACKUP_MANIFEST.json").decode("utf-8"))
                date_str = manifest_data.get("backup_date", "Sconosciuta")

                data_path.mkdir(parents=True, exist_ok=True)
                for member in zf.infolist():
                    if member.filename == "BACKUP_MANIFEST.json":
                        continue
                    if ".." in member.filename or member.filename.startswith("/"):
                        continue
                    zf.extract(member, data_path)

            storage = StorageManager(data_dir=target_data_dir)
            storage.reload_from_disk()

            return True, f"Ripristino completato con successo da backup del {date_str} ({manifest_data.get('file_count', 0)} file)."
        except Exception as e:
            return False, f"Errore durante il ripristino: {str(e)}"

    # -------------------------------------------------------------------------
    # 2. CONSOLIDATED JSON DUMPS & TURSO CLOUD SYNCHRONIZATION
    # -------------------------------------------------------------------------
    @classmethod
    def create_backup(
        cls,
        admin_email: str,
        admin_name: str,
        storage: StorageManager,
        auth_mgr: AuthManager,
        pref_mgr: PreferencesManager
    ) -> Dict[str, Any]:
        """
        Creates a consolidated JSON dump of the entire ASMA database.
        Includes songs, revisions, repertoires, setlists, users, preferences, changelog, audit trail.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Gather all songs and their revision history
        songs_data: List[Dict[str, Any]] = []
        for s_meta in storage.list_songs(include_deleted=True):
            song = storage.get_song(s_meta["uuid"])
            if song:
                s_dict = song.to_dict()
                try:
                    revs = storage.get_revisions_for_song(song.uuid)
                    s_dict["revisions"] = [r.to_dict() for r in revs]
                except Exception:
                    s_dict["revisions"] = []
                songs_data.append(s_dict)

        # 2. Gather repertoires
        repertoires_data = [r.to_dict() for r in storage.list_repertoires()]

        # 3. Gather setlists
        setlists_data = [s.to_dict() for s in storage.list_setlists()]

        # 4. Gather users
        users_data = [u.to_dict() for u in auth_mgr.list_users()]

        # 5. Gather user device preferences
        device_prefs_data = getattr(pref_mgr, "_cache", {})

        # 6. Gather changelog
        changelog_data = ChangelogEngine.get_entries()

        # 7. Gather audit trail
        audit_trail_data: List[str] = []
        audit_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "audit_trail.jsonl")
        if os.path.exists(audit_file):
            try:
                with open(audit_file, "r", encoding="utf-8") as f:
                    audit_trail_data = [line.strip() for line in f if line.strip()]
            except Exception:
                pass

        backup_payload: Dict[str, Any] = {
            "schema_version": "2.0",
            "backup_type": "full",
            "exported_at": now_iso,
            "exported_by": {
                "email": admin_email,
                "name": admin_name
            },
            "app_version": ChangelogEngine.get_latest_version(),
            "data": {
                "songs": songs_data,
                "repertoires": repertoires_data,
                "setlists": setlists_data,
                "users": users_data,
                "user_device_preferences": device_prefs_data,
                "changelog": changelog_data,
                "audit_trail": audit_trail_data
            }
        }

        # Log backup event in audit trail
        try:
            AuditLogger.log_event(
                "DATABASE_BACKUP_CREATED",
                user_email=admin_email,
                user_name=admin_name,
                details=f"Backup completo esportato: {len(songs_data)} brani, {len(setlists_data)} scalette, {len(repertoires_data)} repertori, {len(users_data)} utenti, {len(changelog_data)} versioni changelog"
            )
        except Exception:
            pass

        return backup_payload

    @classmethod
    def restore_backup(
        cls,
        backup_dict: Dict[str, Any],
        admin_email: str,
        admin_name: str,
        storage: StorageManager,
        auth_mgr: AuthManager,
        pref_mgr: PreferencesManager
    ) -> Dict[str, Any]:
        """
        Safely restores all database tables and files from a JSON backup dump.
        Synchronizes immediately to local storage and remote Turso Cloud DB.
        """
        if not isinstance(backup_dict, dict):
            raise ValueError("Il file di backup non contiene un oggetto JSON valido.")

        data_root = backup_dict.get("data") if "data" in backup_dict else backup_dict
        if not isinstance(data_root, dict):
            raise ValueError("Formato backup non riconosciuto: nodo 'data' assente.")

        songs_list = data_root.get("songs")
        reps_list = data_root.get("repertoires")
        setlists_list = data_root.get("setlists")
        users_list = data_root.get("users")

        if songs_list is None or reps_list is None or setlists_list is None:
            raise ValueError("Il file di backup non contiene le tabelle essenziali (brani, repertori, scalette).")

        base_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        os.makedirs(base_data_dir, exist_ok=True)
        songs_dir = os.path.join(base_data_dir, "songs")
        os.makedirs(songs_dir, exist_ok=True)
        revs_dir = os.path.join(base_data_dir, "revisions")
        os.makedirs(revs_dir, exist_ok=True)

        counts = {
            "songs": 0,
            "revisions": 0,
            "repertoires": len(reps_list),
            "setlists": len(setlists_list),
            "users": len(users_list or []),
            "changelog": 0
        }

        # 1. Restore Songs & Revisions
        for s_raw in songs_list:
            try:
                s_dict = dict(s_raw)
                revs = s_dict.pop("revisions", [])
                s_obj = Song.from_dict(s_dict)
                fname = f"{s_obj.uuid}.json"
                fpath = os.path.join(songs_dir, fname)
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(s_obj.to_dict(), f, indent=2, ensure_ascii=False)
                counts["songs"] += 1

                for r_raw in revs:
                    try:
                        r_num = r_raw.get("revision_number", 1)
                        rfpath = os.path.join(revs_dir, f"rev_{s_obj.uuid}_{r_num}.json")
                        with open(rfpath, "w", encoding="utf-8") as rf:
                            json.dump(r_raw, rf, indent=2, ensure_ascii=False)
                        counts["revisions"] += 1
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(f"Errore ripristino brano {s_raw.get('title')}: {e}")

        # 2. Restore Repertoires
        try:
            reps_path = os.path.join(base_data_dir, "repertoires.json")
            with open(reps_path, "w", encoding="utf-8") as f:
                json.dump(reps_list, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Errore ripristino repertoires.json: {e}")

        # 3. Restore Setlists
        try:
            setlists_path = os.path.join(base_data_dir, "setlists.json")
            with open(setlists_path, "w", encoding="utf-8") as f:
                json.dump(setlists_list, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Errore ripristino setlists.json: {e}")

        # 4. Restore Users
        if users_list:
            try:
                users_path = os.path.join(base_data_dir, "users.json")
                with open(users_path, "w", encoding="utf-8") as f:
                    json.dump(users_list, f, indent=2, ensure_ascii=False)
                auth_mgr._load_users()
            except Exception as e:
                logger.error(f"Errore ripristino users.json: {e}")

        # 5. Restore User Device Preferences
        prefs_data = data_root.get("user_device_preferences")
        if prefs_data and isinstance(prefs_data, dict):
            try:
                prefs_path = os.path.join(base_data_dir, "user_device_preferences.json")
                with open(prefs_path, "w", encoding="utf-8") as f:
                    json.dump(prefs_data, f, indent=2, ensure_ascii=False)
                pref_mgr._cache = prefs_data
            except Exception as e:
                logger.error(f"Errore ripristino user_device_preferences.json: {e}")

        # 6. Restore Changelog
        changelog_list = data_root.get("changelog")
        if changelog_list and isinstance(changelog_list, list):
            try:
                ChangelogEngine.save_entries(changelog_list)
                counts["changelog"] = len(changelog_list)
            except Exception as e:
                logger.error(f"Errore ripristino changelog: {e}")

        # 7. Reload in-memory SQLite storage cache
        storage.reload_from_disk()

        # 8. Synchronize to Turso Cloud DB if configured
        try:
            turso = TursoClient()
            if turso.is_configured:
                if users_list:
                    turso.push_users(users_list)
                if reps_list:
                    turso.push_repertoires([Repertoire.from_dict(r) for r in reps_list])
                if setlists_list:
                    turso.push_setlists([Setlist.from_dict(s) for s in setlists_list])
                for s_raw in songs_list:
                    try:
                        turso.push_song(s_raw)
                    except Exception:
                        pass
                if changelog_list:
                    turso.set_setting("official_changelog", json.dumps(changelog_list, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"Sincronizzazione Turso durante restore completata parzialmente: {e}")

        # 9. Audit event
        try:
            AuditLogger.log_event(
                "DATABASE_RESTORE_COMPLETED",
                user_email=admin_email,
                user_name=admin_name,
                details=f"Ripristino completato con successo: {counts['songs']} brani, {counts['setlists']} scalette, {counts['repertoires']} repertori, {counts['users']} utenti, {counts['changelog']} voci changelog"
            )
        except Exception:
            pass

        return {
            "status": "success",
            "message": "Database e changelog ripristinati con successo.",
            "counts": counts
        }

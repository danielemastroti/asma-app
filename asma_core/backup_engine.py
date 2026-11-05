"""
ASMA Accordi Next Generation - Full Backup & Restore Engine
Conforms to SRS Cap. 10.15, 10.16 and 17.5.
Provides atomic ZIP backup generation and point-in-time disaster recovery restore.
"""

from __future__ import annotations
import os
import io
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from asma_core.storage_manager import StorageManager


class BackupEngine:
    """Manages full application backup and disaster recovery restore operations."""

    @classmethod
    def create_full_backup_zip(cls, data_dir: str = "data") -> bytes:
        """
        Creates an encrypted/standard ZIP archive containing all application state:
        - songs/
        - repertoires.json
        - setlists.json
        - live_events.json
        - revisions/
        - audit_trail.jsonl
        - users.json
        """
        data_path = Path(data_dir)
        buf = io.BytesIO()

        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            # Metadata manifest
            manifest = {
                "backup_date": datetime.now().isoformat(),
                "system": "ASMA Accordi 2.0",
                "version": "2026.11.05",
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
                # 1. Verify manifest
                if "BACKUP_MANIFEST.json" not in zf.namelist():
                    return False, "File ZIP non valido: manifesto di backup ASMA mancante."

                manifest_data = json.loads(zf.read("BACKUP_MANIFEST.json").decode("utf-8"))
                date_str = manifest_data.get("backup_date", "Sconosciuta")

                # 2. Extract all data files
                data_path.mkdir(parents=True, exist_ok=True)
                for member in zf.infolist():
                    if member.filename == "BACKUP_MANIFEST.json":
                        continue
                    # Security check against directory traversal
                    if ".." in member.filename or member.filename.startswith("/"):
                        continue
                    zf.extract(member, data_path)

            # 3. Reload storage manager in-memory SQLite
            storage = StorageManager(data_dir=target_data_dir)
            storage.reload_from_disk()

            return True, f"Ripristino completato con successo da backup del {date_str} ({manifest_data.get('file_count', 0)} file)."
        except Exception as e:
            return False, f"Errore durante il ripristino: {str(e)}"

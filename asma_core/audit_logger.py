"""
ASMA Accordi Next Generation - Immutable Audit Trail Logger
Append-Only, Thread-Safe Audit Trail for Security and Regulatory Compliance.
Conforms to SRS Cap. 4.9, 15.19, 16.16 and Blueprint Sec. 10.
"""

from __future__ import annotations
import threading
import json
import os
from typing import List, Dict, Any, Optional
from asma_core.models import AuditEntry, current_iso_timestamp, generate_uuid


class AuditLogger:
    """Thread-safe, append-only audit trail logger."""
    _instance: Optional[AuditLogger] = None
    _singleton_lock = threading.Lock()

    def __new__(cls, log_file_path: Optional[str] = None) -> AuditLogger:
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_logger(log_file_path)
            return cls._instance

    def _init_logger(self, log_file_path: Optional[str] = None) -> None:
        self._mutex = threading.Lock()
        self._log_file = log_file_path or os.path.join(os.path.dirname(__file__), "..", "data", "audit_trail.jsonl")
        self._memory_log: List[AuditEntry] = []
        self._load_existing_log()

    def _load_existing_log(self) -> None:
        if os.path.exists(self._log_file):
            try:
                with open(self._log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            data = json.loads(line)
                            self._memory_log.append(AuditEntry.from_dict(data))
            except Exception:
                pass

    def log(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        user_email: str,
        user_name: str,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEntry:
        """
        Appends an immutable audit record to both memory and the JSONL file.
        """
        entry = AuditEntry(
            uuid=generate_uuid(),
            timestamp=current_iso_timestamp(),
            action=action.upper(),
            entity_type=entity_type.upper(),
            entity_id=entity_id,
            user_email=user_email,
            user_name=user_name,
            details=details or {}
        )

        with self._mutex:
            self._memory_log.append(entry)
            try:
                os.makedirs(os.path.dirname(os.path.abspath(self._log_file)), exist_ok=True)
                with open(self._log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry.to_dict()) + "\n")
            except Exception:
                # Log persistence failure should not bring down the application
                pass

        return entry

    def get_entries(
        self,
        limit: int = 100,
        action_filter: Optional[str] = None,
        entity_filter: Optional[str] = None,
        user_filter: Optional[str] = None
    ) -> List[AuditEntry]:
        """Queries the audit trail in reverse chronological order."""
        with self._mutex:
            records = self._memory_log[:]

        filtered = []
        for r in reversed(records):
            if action_filter and r.action != action_filter.upper():
                continue
            if entity_filter and r.entity_type != entity_filter.upper():
                continue
            if user_filter and user_filter.lower() not in r.user_email.lower():
                continue
            filtered.append(r)
            if len(filtered) >= limit:
                break

        return filtered

    def clear_for_testing(self) -> None:
        """Utility for tests."""
        with self._mutex:
            self._memory_log.clear()
            if os.path.exists(self._log_file):
                try:
                    os.remove(self._log_file)
                except Exception:
                    pass

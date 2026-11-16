"""
ASMA Accordi Next Generation - Immutable Audit Trail Logger
Append-Only, Thread-Safe Audit Trail for Security, Activity Monitoring and Compliance.
Conforms to SRS Cap. 4.9, 15.19, 16.16 and Blueprint Sec. 10.
Includes 15-day retention policy and Turso cloud synchronization.
"""

from __future__ import annotations
import threading
import json
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from asma_core.models import AuditEntry, current_iso_timestamp, generate_uuid


class AuditLogger:
    """Thread-safe, append-only audit trail logger with 15-day retention."""
    _instance: Optional[AuditLogger] = None
    _singleton_lock = threading.Lock()
    RETENTION_DAYS: int = 15

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
        self.prune_retention()

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

        # If memory log is empty (e.g. fresh ephemeral container on Render), hydrate from Turso
        if not self._memory_log:
            try:
                from asma_core.turso_client import TursoClient
                tc = TursoClient()
                if tc.is_configured:
                    entries = tc.fetch_audit_entries(limit=1000)
                    for ed in reversed(entries):
                        self._memory_log.append(AuditEntry.from_dict(ed))
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
        Appends an immutable audit record to memory, disk file, and Turso cloud database.
        """
        entry = AuditEntry(
            uuid=generate_uuid(),
            timestamp=current_iso_timestamp(),
            action=action.upper(),
            entity_type=entity_type.upper(),
            entity_id=entity_id,
            user_email=user_email or "unknown",
            user_name=user_name or "Unknown",
            details=details or {}
        )

        with self._mutex:
            self._memory_log.append(entry)
            try:
                os.makedirs(os.path.dirname(os.path.abspath(self._log_file)), exist_ok=True)
                with open(self._log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
            except Exception:
                pass

        # Best-effort background push to Turso cloud
        try:
            from asma_core.turso_client import TursoClient
            tc = TursoClient()
            if tc.is_configured:
                threading.Thread(target=tc.push_audit_entry, args=(entry.to_dict(),), daemon=True).start()
        except Exception:
            pass

        return entry

    def prune_retention(self) -> int:
        """Prunes records older than RETENTION_DAYS (15 days) from memory, disk and Turso."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=self.RETENTION_DAYS)
        cutoff_iso = cutoff.isoformat()
        pruned_count = 0

        with self._mutex:
            valid_entries = []
            for e in self._memory_log:
                try:
                    ts = datetime.fromisoformat(e.timestamp)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    if ts >= cutoff:
                        valid_entries.append(e)
                    else:
                        pruned_count += 1
                except Exception:
                    valid_entries.append(e)

            if pruned_count > 0 or len(valid_entries) != len(self._memory_log):
                self._memory_log = valid_entries
                try:
                    os.makedirs(os.path.dirname(os.path.abspath(self._log_file)), exist_ok=True)
                    with open(self._log_file, "w", encoding="utf-8") as f:
                        for entry in self._memory_log:
                            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
                except Exception:
                    pass

        # Prune Turso cloud database
        try:
            from asma_core.turso_client import TursoClient
            tc = TursoClient()
            if tc.is_configured:
                threading.Thread(target=tc.prune_audit_entries, args=(cutoff_iso,), daemon=True).start()
        except Exception:
            pass

        return pruned_count

    def get_entries(
        self,
        limit: int = 500,
        action_filter: Optional[str] = None,
        entity_filter: Optional[str] = None,
        user_filter: Optional[str] = None,
        days_retention: int = 15
    ) -> List[AuditEntry]:
        """Queries the audit trail in reverse chronological order within days_retention."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=days_retention)

        with self._mutex:
            records = self._memory_log[:]

        filtered = []
        for r in reversed(records):
            try:
                ts = datetime.fromisoformat(r.timestamp)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts < cutoff:
                    continue
            except Exception:
                pass

            if action_filter and action_filter.upper() not in ("ALL", "") and r.action != action_filter.upper():
                continue
            if entity_filter and entity_filter.upper() not in ("ALL", "") and r.entity_type != entity_filter.upper():
                continue
            if user_filter and user_filter.strip():
                uf = user_filter.strip().lower()
                if uf not in (r.user_email or "").lower() and uf not in (r.user_name or "").lower():
                    continue

            filtered.append(r)
            if len(filtered) >= limit:
                break

        return filtered

    def get_statistics(self, days: int = 15) -> Dict[str, Any]:
        """Calculates audit trail analytics: usage frequency, active musicians, top functions."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=days)

        user_counts: Dict[str, Dict[str, Any]] = {}
        action_counts: Dict[str, int] = {}
        daily_counts: Dict[str, int] = {}
        total_events = 0
        last_event: Optional[AuditEntry] = None

        with self._mutex:
            records = self._memory_log[:]

        for r in records:
            try:
                ts = datetime.fromisoformat(r.timestamp)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts < cutoff:
                    continue
            except Exception:
                pass

            total_events += 1
            last_event = r

            act = r.action.upper()
            action_counts[act] = action_counts.get(act, 0) + 1

            u_email = (r.user_email or "anonimo").strip().lower()
            u_name = (r.user_name or u_email.split("@")[0]).strip()
            if u_email not in user_counts:
                user_counts[u_email] = {
                    "email": u_email,
                    "name": u_name,
                    "count": 0,
                    "last_active": r.timestamp
                }
            user_counts[u_email]["count"] += 1
            user_counts[u_email]["last_active"] = r.timestamp

            day_str = r.timestamp[:10]
            daily_counts[day_str] = daily_counts.get(day_str, 0) + 1

        sorted_users = sorted(user_counts.values(), key=lambda x: x["count"], reverse=True)
        sorted_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)

        return {
            "total_events": total_events,
            "period_days": days,
            "avg_events_per_day": round(total_events / max(days, 1), 1),
            "last_event": last_event.to_dict() if last_event else None,
            "active_users": sorted_users,
            "action_counts": dict(sorted_actions),
            "daily_timeline": daily_counts
        }

    def clear_for_testing(self) -> None:
        """Utility for tests."""
        with self._mutex:
            self._memory_log.clear()
            if os.path.exists(self._log_file):
                try:
                    os.remove(self._log_file)
                except Exception:
                    pass

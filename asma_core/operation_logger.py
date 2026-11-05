"""
ASMA Accordi Next Generation - Live Operation Logger & Status Console
Provides real-time tracing of user actions and background processes.
Conforms to SRS Cap. 4.9, 15.19 and User Interface Status Requirements.
"""

from __future__ import annotations
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class OperationLogEntry:
    timestamp: str
    icon: str
    category: str
    message: str
    level: str  # "SUCCESS", "INFO", "WARNING", "ERROR"
    user: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_terminal_line(self) -> str:
        color_map = {
            "SUCCESS": "#00E676",
            "INFO": "#00E5FF",
            "WARNING": "#FFD600",
            "ERROR": "#FF5252"
        }
        color = color_map.get(self.level, "#FFFFFF")
        return (
            f"<div style='font-family:monospace; font-size:12px; margin-bottom:4px; line-height:1.4;'>"
            f"<span style='color:#888888;'>[{self.timestamp}]</span> "
            f"<span>{self.icon}</span> "
            f"<span style='color:{color}; font-weight:bold;'>[{self.category}]</span> "
            f"<span style='color:#E0E0E0;'>{self.message}</span> "
            f"<span style='color:#757575; font-size:11px;'>— {self.user}</span>"
            f"</div>"
        )


class OperationLogger:
    """Singleton thread-safe in-memory circular operation logger."""
    _instance: Optional[OperationLogger] = None
    _singleton_lock = threading.Lock()
    MAX_ENTRIES = 150

    def __new__(cls) -> OperationLogger:
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_logger()
            return cls._instance

    def _init_logger(self) -> None:
        self._mutex = threading.Lock()
        self._entries: List[OperationLogEntry] = []
        # Pre-seed with system boot message
        now_time = datetime.now().strftime("%H:%M:%S")
        self._entries.append(
            OperationLogEntry(
                timestamp=now_time,
                icon="🟢",
                category="SISTEMA",
                message="Motore ASMA 2.0 avviato e pronto all'uso",
                level="SUCCESS",
                user="System"
            )
        )

    def log(
        self,
        icon: str,
        category: str,
        message: str,
        level: str = "SUCCESS",
        user: str = "System"
    ) -> OperationLogEntry:
        """Records a new human-readable operation log entry."""
        now_time = datetime.now().strftime("%H:%M:%S")
        entry = OperationLogEntry(
            timestamp=now_time,
            icon=icon,
            category=category.upper(),
            message=message,
            level=level.upper(),
            user=user
        )
        with self._mutex:
            self._entries.insert(0, entry)  # Most recent first
            if len(self._entries) > self.MAX_ENTRIES:
                self._entries = self._entries[:self.MAX_ENTRIES]
        return entry

    def get_entries(self, limit: int = 50, category: Optional[str] = None) -> List[OperationLogEntry]:
        """Returns the most recent entries, optionally filtered by category."""
        with self._mutex:
            if category and category != "TUTTE":
                filtered = [e for e in self._entries if e.category == category.upper()]
                return filtered[:limit]
            return list(self._entries[:limit])

    def get_categories(self) -> List[str]:
        """Returns unique categories logged so far."""
        with self._mutex:
            cats = sorted(list(set(e.category for e in self._entries)))
            return ["TUTTE"] + cats

    def clear(self) -> None:
        """Clears all entries except a clear confirmation entry."""
        with self._mutex:
            now_time = datetime.now().strftime("%H:%M:%S")
            self._entries = [
                OperationLogEntry(
                    timestamp=now_time,
                    icon="🧹",
                    category="CONSOLE",
                    message="Console operazioni resettata dall'utente",
                    level="INFO",
                    user="User"
                )
            ]

    def count(self) -> int:
        with self._mutex:
            return len(self._entries)

    def export_text(self) -> str:
        """Exports all recorded operations in plain text format."""
        with self._mutex:
            lines = [
                f"[{e.timestamp}] [{e.category}] ({e.level}) {e.message} — Operatore: {e.user}"
                for e in reversed(self._entries)
            ]
            return "\n".join(lines)


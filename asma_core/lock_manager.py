"""
ASMA Accordi Next Generation - Distributed In-Memory Lock & Session Manager
Thread-Safe In-Memory Singleton with Automatic Expiration.
Conforms to SRS Cap. 4.6, 7.7, 15.24 and Blueprint CRIT-01.
"""

from __future__ import annotations
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Tuple, List, Any
from asma_core.models import LockStatus, current_iso_timestamp


class LockManager:
    """
    Thread-safe In-Memory Lock Manager.
    Manages exclusive song edit locks and prevents concurrent overwrite collisions.
    """
    _instance: Optional[LockManager] = None
    _singleton_lock = threading.Lock()

    def __new__(cls) -> LockManager:
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_manager()
            return cls._instance

    def _init_manager(self) -> None:
        self._mutex = threading.Lock()
        self._locks: Dict[str, LockStatus] = {}
        self._default_timeout_minutes: int = 60

    def acquire_lock(
        self,
        song_uuid: str,
        user_email: str,
        user_name: str,
        session_id: Optional[str] = None,
        timeout_minutes: Optional[int] = None
    ) -> Tuple[bool, LockStatus, str]:
        """
        Attempts to acquire an exclusive editing lock on a song.
        Returns: (success: bool, status: LockStatus, message: str)
        """
        timeout_m = timeout_minutes or self._default_timeout_minutes
        with self._mutex:
            current_lock = self._locks.get(song_uuid)
            now = datetime.now(timezone.utc)

            # Check if an existing lock exists and is still valid
            if current_lock and current_lock.is_locked:
                # Check expiration
                if current_lock.locked_at:
                    try:
                        locked_time = datetime.fromisoformat(current_lock.locked_at)
                        if now - locked_time > timedelta(minutes=timeout_m):
                            # Lock expired -> auto release
                            pass
                        elif current_lock.locked_by_email == user_email:
                            # Same user re-acquiring / refreshing lock
                            current_lock.locked_at = now.isoformat()
                            current_lock.session_id = session_id
                            return True, current_lock, "Lock rinnovato con successo."
                        else:
                            # Locked by someone else
                            return False, current_lock, f"Brano bloccato da {current_lock.locked_by_name or current_lock.locked_by_email}."
                    except Exception:
                        pass

            # Acquire new lock
            new_lock = LockStatus(
                is_locked=True,
                locked_by_email=user_email,
                locked_by_name=user_name,
                locked_at=now.isoformat(),
                session_id=session_id
            )
            self._locks[song_uuid] = new_lock
            return True, new_lock, "Lock acquisito con successo."

    def release_lock(
        self,
        song_uuid: str,
        user_email: str,
        force: bool = False
    ) -> Tuple[bool, str]:
        """
        Releases an active editing lock on a song.
        Only the lock owner or an Admin with force=True can release.
        """
        with self._mutex:
            current_lock = self._locks.get(song_uuid)
            if not current_lock or not current_lock.is_locked:
                return True, "Il brano non era bloccato."

            if current_lock.locked_by_email == user_email or force:
                del self._locks[song_uuid]
                return True, "Lock rilasciato con successo."
            else:
                return False, f"Impossibile rilasciare il lock di un altro utente ({current_lock.locked_by_name})."

    def check_lock(self, song_uuid: str) -> LockStatus:
        """Checks the current lock status of a song, clearing expired locks if necessary."""
        with self._mutex:
            current_lock = self._locks.get(song_uuid)
            if not current_lock or not current_lock.is_locked:
                return LockStatus(is_locked=False)

            if current_lock.locked_at:
                try:
                    now = datetime.now(timezone.utc)
                    locked_time = datetime.fromisoformat(current_lock.locked_at)
                    if now - locked_time > timedelta(minutes=self._default_timeout_minutes):
                        # Expired
                        del self._locks[song_uuid]
                        return LockStatus(is_locked=False)
                except Exception:
                    pass

            return current_lock

    def heartbeat(self, song_uuid: str, user_email: str, session_id: Optional[str] = None) -> bool:
        """Extends lock lifespan during active editing session."""
        with self._mutex:
            current_lock = self._locks.get(song_uuid)
            if current_lock and current_lock.is_locked and current_lock.locked_by_email == user_email:
                current_lock.locked_at = current_iso_timestamp()
                if session_id:
                    current_lock.session_id = session_id
                return True
            return False

    def get_active_locks(self) -> List[Dict[str, Any]]:
        """Returns all currently active locks for Admin monitoring dashboard."""
        with self._mutex:
            active = []
            now = datetime.now(timezone.utc)
            to_delete = []
            for song_uuid, lock in self._locks.items():
                if lock.is_locked and lock.locked_at:
                    try:
                        locked_time = datetime.fromisoformat(lock.locked_at)
                        if now - locked_time > timedelta(minutes=self._default_timeout_minutes):
                            to_delete.append(song_uuid)
                        else:
                            active.append({
                                "song_uuid": song_uuid,
                                "locked_by_email": lock.locked_by_email,
                                "locked_by_name": lock.locked_by_name,
                                "locked_at": lock.locked_at,
                                "session_id": lock.session_id
                            })
                    except Exception:
                        to_delete.append(song_uuid)
            for s_id in to_delete:
                del self._locks[s_id]
            return active

    def clear_all_locks_for_testing(self) -> None:
        """Utility method for unit tests."""
        with self._mutex:
            self._locks.clear()

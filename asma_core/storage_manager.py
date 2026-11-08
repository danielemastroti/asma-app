"""
ASMA Accordi Next Generation - Two-Layer Storage Engine
Layer 1: In-Memory SQLite index for ultra-fast multi-criteria querying (< 2ms)
Layer 2: Partitioned JSON file persistence with GitHub Gist synchronization adapter.
Conforms to SRS Cap. 4, 7, 10, 15, 18, 22 and Blueprint CRIT-04.
"""

from __future__ import annotations
import os
import json
import sqlite3
import threading
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple

from asma_core.models import (
    Song, Repertoire, Setlist, LiveEvent, Revision, LockStatus,
    current_iso_timestamp, generate_uuid
)
from asma_core.audit_logger import AuditLogger
from asma_core.lock_manager import LockManager
from asma_core.gist_client import GistClient


class StorageManager:
    """
    Two-layer Storage Engine for ASMA 2.0.
    In-memory SQLite index cache + Local JSON Storage + GitHub Gist Adapter.
    """
    _instance: Optional[StorageManager] = None
    _singleton_lock = threading.Lock()

    def __new__(cls, data_dir: Optional[str] = None) -> StorageManager:
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_storage(data_dir)
            return cls._instance

    def _init_storage(self, data_dir: Optional[str] = None) -> None:
        self._mutex = threading.Lock()
        self._base_dir = data_dir or os.path.join(os.path.dirname(__file__), "..", "data")
        self._songs_dir = os.path.join(self._base_dir, "songs")
        self._revs_dir = os.path.join(self._base_dir, "revisions")
        self._trash_dir = os.path.join(self._base_dir, "trash")

        for d in [self._base_dir, self._songs_dir, self._revs_dir, self._trash_dir]:
            os.makedirs(d, exist_ok=True)

        self._repertoires_file = os.path.join(self._base_dir, "repertoires.json")
        self._setlists_file = os.path.join(self._base_dir, "setlists.json")
        self._events_file = os.path.join(self._base_dir, "live_events.json")
        self._config_file = os.path.join(self._base_dir, "system_config.json")

        self.audit = AuditLogger()
        self.lock_mgr = LockManager()
        self.gist_client = GistClient()

        # Initialize In-Memory SQLite Index
        self._db_conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._db_conn.row_factory = sqlite3.Row
        self._init_sqlite_schema()
        self._load_all_into_index()

        # Initial automatic cloud synchronization (prevent data loss on cloud deploy/restart)
        if self.gist_client.is_configured:
            try:
                self.sync_from_cloud()
            except Exception:
                pass

    def _init_sqlite_schema(self) -> None:
        with self._db_conn:
            self._db_conn.execute("""
                CREATE TABLE IF NOT EXISTS songs_index (
                    uuid TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    artist TEXT,
                    author TEXT,
                    genre TEXT,
                    year INTEGER,
                    duration_seconds INTEGER,
                    bpm INTEGER,
                    time_signature TEXT,
                    capo INTEGER,
                    key_original TEXT,
                    key_current TEXT,
                    notation_system TEXT,
                    tags TEXT,
                    current_revision INTEGER,
                    created_at TEXT,
                    updated_at TEXT,
                    is_deleted INTEGER DEFAULT 0,
                    repertoire_uuids TEXT
                )
            """)
            self._db_conn.execute("CREATE INDEX IF NOT EXISTS idx_title ON songs_index(title)")
            self._db_conn.execute("CREATE INDEX IF NOT EXISTS idx_key ON songs_index(key_current)")
            self._db_conn.execute("CREATE INDEX IF NOT EXISTS idx_bpm ON songs_index(bpm)")
            self._db_conn.execute("CREATE INDEX IF NOT EXISTS idx_genre ON songs_index(genre)")

    def _load_all_into_index(self) -> None:
        """Loads all existing song files from disk into the in-memory SQLite index."""
        repertoires = self.list_repertoires()
        song_rep_map: Dict[str, List[str]] = {}
        for r in repertoires:
            for s_id in r.song_uuids:
                song_rep_map.setdefault(s_id, []).append(r.uuid)

        if not os.path.exists(self._songs_dir):
            return

        with self._db_conn:
            self._db_conn.execute("DELETE FROM songs_index")
            for filename in os.listdir(self._songs_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(self._songs_dir, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            song = Song.from_dict(data)
                            reps = song_rep_map.get(song.uuid, [])
                            self._upsert_index_record(song, reps)
                    except Exception:
                        pass

    def reload_from_disk(self) -> None:
        """Forces full reload of in-memory SQLite index from JSON files on disk."""
        with self._mutex:
            self._load_all_into_index()

    def _upsert_index_record(self, song: Song, repertoire_uuids: Optional[List[str]] = None) -> None:
        reps_str = json.dumps(repertoire_uuids or [])
        tags_str = ",".join(song.tags)
        with self._db_conn:
            self._db_conn.execute("""
                INSERT OR REPLACE INTO songs_index (
                    uuid, title, artist, author, genre, year,
                    duration_seconds, bpm, time_signature, capo,
                    key_original, key_current, notation_system, tags,
                    current_revision, created_at, updated_at, is_deleted,
                    repertoire_uuids
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """, (
                song.uuid, song.title, song.artist, song.author, song.genre, song.year,
                song.duration_seconds, song.bpm, song.time_signature, song.capo,
                song.key_original, song.key_current, song.notation_system, tags_str,
                song.current_revision, song.created_at, song.updated_at, reps_str
            ))

    # --- SONGS CRUD ---

    def save_song(
        self,
        song: Song,
        user_email: str = "system",
        user_name: str = "System",
        revision_comment: str = "Salvataggio brano"
    ) -> Song:
        """
        Saves a song, registers an immutable revision, updates in-memory index, and writes to disk.
        """
        with self._mutex:
            song.updated_at = current_iso_timestamp()

            # Check existing revision number
            existing_revs = self.get_revisions_for_song(song.uuid)
            next_rev_num = len(existing_revs) + 1
            song.current_revision = next_rev_num

            # Save song JSON
            song_path = os.path.join(self._songs_dir, f"{song.uuid}.json")
            with open(song_path, "w", encoding="utf-8") as f:
                json.dump(song.to_dict(), f, indent=2, ensure_ascii=False)

            # Save revision snapshot
            rev = Revision(
                song_uuid=song.uuid,
                revision_number=next_rev_num,
                author_email=user_email,
                author_name=user_name,
                comment=revision_comment,
                aml_snapshot=song.aml_content,
                timestamp=song.updated_at
            )
            self._save_revision(rev)

            # Update SQLite Index
            self._upsert_index_record(song)

            # Audit
            self.audit.log(
                action="UPDATE" if next_rev_num > 1 else "CREATE",
                entity_type="SONG",
                entity_id=song.uuid,
                user_email=user_email,
                user_name=user_name,
                details={"title": song.title, "revision": next_rev_num, "key": song.key_current}
            )

            return song

    def get_song(self, song_uuid: str) -> Optional[Song]:
        """Retrieves a song by UUID."""
        song_path = os.path.join(self._songs_dir, f"{song_uuid}.json")
        if not os.path.exists(song_path):
            return None
        try:
            with open(song_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return Song.from_dict(data)
        except Exception:
            return None

    def list_songs(self, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """Fast listing of all songs from in-memory SQLite index in case-insensitive alphabetical order."""
        query = "SELECT * FROM songs_index WHERE is_deleted = 0 ORDER BY title COLLATE NOCASE ASC"
        if include_deleted:
            query = "SELECT * FROM songs_index ORDER BY title COLLATE NOCASE ASC"
        cursor = self._db_conn.cursor()
        rows = cursor.execute(query).fetchall()
        return [dict(r) for r in rows]

    def delete_song(
        self,
        song_uuid: str,
        user_email: str = "system",
        user_name: str = "System"
    ) -> bool:
        """Soft-deletes a song by moving it to the trash folder (30-day retention)."""
        with self._mutex:
            song = self.get_song(song_uuid)
            if not song:
                return False

            src_path = os.path.join(self._songs_dir, f"{song_uuid}.json")
            trash_path = os.path.join(self._trash_dir, f"song_{song_uuid}.json")

            trash_meta = {
                "deleted_at": current_iso_timestamp(),
                "entity_type": "SONG",
                "entity_uuid": song_uuid,
                "data": song.to_dict()
            }
            with open(trash_path, "w", encoding="utf-8") as f:
                json.dump(trash_meta, f, indent=2, ensure_ascii=False)

            if os.path.exists(src_path):
                os.remove(src_path)

            with self._db_conn:
                self._db_conn.execute("UPDATE songs_index SET is_deleted = 1 WHERE uuid = ?", (song_uuid,))

            self.audit.log(
                action="DELETE",
                entity_type="SONG",
                entity_id=song_uuid,
                user_email=user_email,
                user_name=user_name,
                details={"title": song.title}
            )
            return True

    def restore_song(
        self,
        song_uuid: str,
        user_email: str = "system",
        user_name: str = "System"
    ) -> Optional[Song]:
        """Restores a soft-deleted song from trash."""
        with self._mutex:
            trash_path = os.path.join(self._trash_dir, f"song_{song_uuid}.json")
            if not os.path.exists(trash_path):
                return None

            with open(trash_path, "r", encoding="utf-8") as f:
                trash_meta = json.load(f)

            song_data = trash_meta["data"]
            song = Song.from_dict(song_data)

            song_path = os.path.join(self._songs_dir, f"{song.uuid}.json")
            with open(song_path, "w", encoding="utf-8") as f:
                json.dump(song.to_dict(), f, indent=2, ensure_ascii=False)

            os.remove(trash_path)
            self._upsert_index_record(song)

            self.audit.log(
                action="RESTORE",
                entity_type="SONG",
                entity_id=song.uuid,
                user_email=user_email,
                user_name=user_name,
                details={"title": song.title}
            )
            return song

    def purge_song_permanently(
        self,
        song_uuid: str,
        user_email: str = "system",
        user_name: str = "System"
    ) -> bool:
        """Permanently deletes a soft-deleted song and its revisions from trash."""
        with self._mutex:
            trash_path = os.path.join(self._trash_dir, f"song_{song_uuid}.json")
            if os.path.exists(trash_path):
                os.remove(trash_path)
            rev_file = os.path.join(self._revs_dir, f"rev_{song_uuid}.json")
            if os.path.exists(rev_file):
                os.remove(rev_file)
            self.audit.log("PURGE", "SONG", song_uuid, user_email, user_name, {})
            return True

    def empty_trash(
        self,
        user_email: str = "system",
        user_name: str = "System"
    ) -> int:
        """Permanently purges all items currently in trash."""
        with self._mutex:
            count = 0
            if os.path.exists(self._trash_dir):
                for f in os.listdir(self._trash_dir):
                    if f.endswith(".json"):
                        try:
                            os.remove(os.path.join(self._trash_dir, f))
                            count += 1
                        except Exception:
                            pass
            self.audit.log("PURGE_ALL", "TRASH", "all", user_email, user_name, {"purged_count": count})
            return count

    # --- TAGS MANAGEMENT (SRS Cap. 4.3 & 17.30) ---

    def list_all_tags(self) -> Dict[str, int]:
        """Returns all distinct tags across active songs mapped to their usage count."""
        tag_counts: Dict[str, int] = {}
        for s_dict in self.list_songs(include_deleted=False):
            song = self.get_song(s_dict["uuid"])
            if song and song.tags:
                for t in song.tags:
                    clean_t = t.strip()
                    if clean_t:
                        tag_counts[clean_t] = tag_counts.get(clean_t, 0) + 1
        return dict(sorted(tag_counts.items(), key=lambda x: x[0]))

    def rename_tag_globally(
        self,
        old_tag: str,
        new_tag: str,
        user_email: str = "system",
        user_name: str = "System"
    ) -> int:
        """Renames or merges a tag across all active songs."""
        old_clean = old_tag.strip()
        new_clean = new_tag.strip()
        if not old_clean or not new_clean or old_clean == new_clean:
            return 0

        updated_count = 0
        for s_dict in self.list_songs(include_deleted=False):
            song = self.get_song(s_dict["uuid"])
            if song and old_clean in song.tags:
                new_tags: List[str] = []
                for t in song.tags:
                    t_str = t.strip()
                    if t_str == old_clean:
                        if new_clean not in new_tags:
                            new_tags.append(new_clean)
                    elif t_str not in new_tags:
                        new_tags.append(t_str)
                song.tags = new_tags
                self.save_song(song, user_email, user_name, f"Ridenominazione tag '{old_clean}' -> '{new_clean}'")
                updated_count += 1

        self.audit.log("RENAME_TAG", "SYSTEM", old_clean, user_email, user_name, {
            "old_tag": old_clean,
            "new_tag": new_clean,
            "updated_songs": updated_count
        })
        return updated_count

    def delete_tag_globally(
        self,
        target_tag: str,
        user_email: str = "system",
        user_name: str = "System"
    ) -> int:
        """Removes a tag from all active songs."""
        clean_tag = target_tag.strip()
        if not clean_tag:
            return 0

        updated_count = 0
        for s_dict in self.list_songs(include_deleted=False):
            song = self.get_song(s_dict["uuid"])
            if song and clean_tag in song.tags:
                song.tags = [t.strip() for t in song.tags if t.strip() != clean_tag]
                self.save_song(song, user_email, user_name, f"Rimozione globale tag '{clean_tag}'")
                updated_count += 1

        self.audit.log("DELETE_TAG", "SYSTEM", clean_tag, user_email, user_name, {
            "tag": clean_tag,
            "updated_songs": updated_count
        })
        return updated_count

    def add_tag_to_songs(
        self,
        tag: str,
        song_uuids: List[str],
        user_email: str = "system",
        user_name: str = "System"
    ) -> int:
        """Applies a tag to multiple songs in bulk."""
        clean_tag = tag.strip()
        if not clean_tag:
            return 0

        count = 0
        for uid in song_uuids:
            song = self.get_song(uid)
            if song and clean_tag not in song.tags:
                song.tags.append(clean_tag)
                self.save_song(song, user_email, user_name, f"Assegnazione tag '{clean_tag}'")
                count += 1
        return count

    # --- SEARCH & FILTER (SQL in-memory < 2ms) ---

    def search_songs(
        self,
        query_text: Optional[str] = None,
        key: Optional[str] = None,
        bpm_min: Optional[int] = None,
        bpm_max: Optional[int] = None,
        genre: Optional[str] = None,
        tag: Optional[str] = None,
        repertoire_uuid: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Ultra-fast multi-criteria search executed against in-memory SQLite."""
        conditions = ["is_deleted = 0"]
        params: List[Any] = []

        if query_text and query_text.strip():
            clean_q = f"%{query_text.strip()}%"
            conditions.append("(title LIKE ? OR artist LIKE ? OR author LIKE ?)")
            params.extend([clean_q, clean_q, clean_q])

        if key and key.strip():
            k_raw = key.strip()
            variants = {k_raw, k_raw.upper(), k_raw.capitalize()}
            try:
                from asma_core.music_engine import MusicEngine
                ita_v = MusicEngine.convert_notation(k_raw, "ITA")
                int_v = MusicEngine.convert_notation(k_raw, "INT")
                if ita_v:
                    variants.add(ita_v)
                if int_v:
                    variants.add(int_v)
            except Exception:
                pass
            v_list = list(variants)
            placeholders = ", ".join(["?"] * len(v_list))
            conditions.append(f"(key_current IN ({placeholders}) OR key_original IN ({placeholders}))")
            params.extend(v_list)
            params.extend(v_list)

        if bpm_min is not None:
            conditions.append("bpm >= ?")
            params.append(bpm_min)

        if bpm_max is not None:
            conditions.append("bpm <= ?")
            params.append(bpm_max)

        if genre and genre.strip():
            conditions.append("genre LIKE ?")
            params.append(f"%{genre.strip()}%")

        if tag and tag.strip():
            conditions.append("tags LIKE ?")
            params.append(f"%{tag.strip()}%")

        if repertoire_uuid and repertoire_uuid.strip():
            conditions.append("repertoire_uuids LIKE ?")
            params.append(f"%{repertoire_uuid.strip()}%")

        where_clause = " AND ".join(conditions)
        sql = f"SELECT * FROM songs_index WHERE {where_clause} ORDER BY title ASC"

        cursor = self._db_conn.cursor()
        rows = cursor.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    # --- REVISIONS ---

    def _save_revision(self, revision: Revision) -> None:
        rev_file = os.path.join(self._revs_dir, f"rev_{revision.song_uuid}.json")
        revs = []
        if os.path.exists(rev_file):
            try:
                with open(rev_file, "r", encoding="utf-8") as f:
                    revs = json.load(f)
            except Exception:
                revs = []
        revs.append(revision.to_dict())
        with open(rev_file, "w", encoding="utf-8") as f:
            json.dump(revs, f, indent=2, ensure_ascii=False)

    def get_revisions_for_song(self, song_uuid: str) -> List[Revision]:
        rev_file = os.path.join(self._revs_dir, f"rev_{song_uuid}.json")
        if not os.path.exists(rev_file):
            return []
        try:
            with open(rev_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Revision.from_dict(r) for r in data]
        except Exception:
            return []

    def restore_revision(
        self,
        song_uuid: str,
        revision_number: int,
        user_email: str,
        user_name: str
    ) -> Optional[Song]:
        """Restores a previous snapshot revision of a song as a new current revision."""
        revs = self.get_revisions_for_song(song_uuid)
        target_rev = next((r for r in revs if r.revision_number == revision_number), None)
        if not target_rev:
            return None

        song = self.get_song(song_uuid)
        if not song:
            return None

        song.aml_content = target_rev.aml_snapshot
        restored_song = self.save_song(
            song,
            user_email=user_email,
            user_name=user_name,
            revision_comment=f"Rollback alla revisione #{revision_number}"
        )
        return restored_song

    # --- REPERTOIRES CRUD ---

    def list_repertoires(self) -> List[Repertoire]:
        if not os.path.exists(self._repertoires_file):
            # Create default repertoires
            defaults = [
                Repertoire(name="Working In Progress", description="Brani in fase di studio e arrangiamento"),
                Repertoire(name="Repertorio Definitivo", description="Brani pronti per l'esecuzione live"),
                Repertoire(name="Acustico", description="Arrangiamenti acustici da club")
            ]
            self._save_repertoires_file(defaults)
            return defaults

        try:
            with open(self._repertoires_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Repertoire.from_dict(d) for d in data]
        except Exception:
            return []

    def save_repertoire(self, repertoire: Repertoire, user_email: str = "system", user_name: str = "System") -> Repertoire:
        clean_name = repertoire.name.strip()
        if not clean_name:
            raise ValueError("Il nome del repertorio non può essere vuoto.")
        repertoire.name = clean_name

        reps = self.list_repertoires()
        # Enforce unique repertoire name (case-insensitive)
        for existing in reps:
            if existing.uuid != repertoire.uuid and existing.name.strip().lower() == clean_name.lower():
                raise ValueError(f"Un repertorio con il nome '{clean_name}' esiste già. I nomi dei repertori devono essere univoci.")

        reps = [r for r in reps if r.uuid != repertoire.uuid]
        repertoire.updated_at = current_iso_timestamp()
        reps.append(repertoire)
        self._save_repertoires_file(reps)
        self._load_all_into_index()
        self.audit.log("UPDATE", "REPERTOIRE", repertoire.uuid, user_email, user_name, {"name": repertoire.name})
        self._trigger_background_gist_sync("ALL")
        return repertoire

    def _save_repertoires_file(self, repertoires: List[Repertoire]) -> None:
        with open(self._repertoires_file, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in repertoires], f, indent=2, ensure_ascii=False)

    def delete_repertoire(self, repertoire_uuid: str, user_email: str = "system", user_name: str = "System") -> bool:
        """Deletes a repertoire without deleting the songs contained within it."""
        reps = self.list_repertoires()
        target_rep = next((r for r in reps if r.uuid == repertoire_uuid), None)
        if not target_rep:
            return False
        reps = [r for r in reps if r.uuid != repertoire_uuid]
        self._save_repertoires_file(reps)
        self._load_all_into_index()
        self.audit.log("DELETE", "REPERTOIRE", repertoire_uuid, user_email, user_name, {"name": target_rep.name})
        return True

    def move_song_to_repertoire(
        self,
        song_uuid: str,
        target_repertoire_uuid: str,
        user_email: str = "system",
        user_name: str = "System"
    ) -> bool:
        """Moves a song between repertoires preserving UUID, revision history, and tags."""
        reps = self.list_repertoires()
        target_rep = next((r for r in reps if r.uuid == target_repertoire_uuid), None)
        if not target_rep:
            return False

        if song_uuid not in target_rep.song_uuids:
            target_rep.song_uuids.append(song_uuid)
            self._save_repertoires_file(reps)
            self._load_all_into_index()
            self.audit.log("UPDATE", "REPERTOIRE", target_rep.uuid, user_email, user_name, {"action": "song_added", "song_uuid": song_uuid})
            return True
        return True

    def remove_song_from_repertoire(
        self,
        song_uuid: str,
        repertoire_uuid: str,
        user_email: str = "system",
        user_name: str = "System"
    ) -> bool:
        """Removes a song from a specific repertoire without deleting the song from the system."""
        reps = self.list_repertoires()
        rep = next((r for r in reps if r.uuid == repertoire_uuid), None)
        if not rep or song_uuid not in rep.song_uuids:
            return False

        rep.song_uuids.remove(song_uuid)
        self._save_repertoires_file(reps)
        self._load_all_into_index()
        self.audit.log("UPDATE", "REPERTOIRE", rep.uuid, user_email, user_name, {"action": "song_removed", "song_uuid": song_uuid})
        return True

    # --- SETLISTS CRUD ---

    def list_setlists(self) -> List[Setlist]:
        if not os.path.exists(self._setlists_file):
            return []
        try:
            with open(self._setlists_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Setlist.from_dict(d) for d in data]
        except Exception:
            return []

    def get_setlist(self, setlist_uuid: str) -> Optional[Setlist]:
        for s in self.list_setlists():
            if s.uuid == setlist_uuid:
                return s
        return None

    def save_setlist(self, setlist: Setlist, user_email: str = "system", user_name: str = "System") -> Setlist:
        setlists = self.list_setlists()
        setlists = [s for s in setlists if s.uuid != setlist.uuid]
        setlist.updated_at = current_iso_timestamp()
        setlists.append(setlist)
        with open(self._setlists_file, "w", encoding="utf-8") as f:
            json.dump([s.to_dict() for s in setlists], f, indent=2, ensure_ascii=False)
        self.audit.log("UPDATE", "SETLIST", setlist.uuid, user_email, user_name, {"title": setlist.title, "songs_count": len(setlist.items)})
        self._trigger_background_gist_sync("SETLISTS")
        return setlist

    def delete_setlist(self, setlist_uuid: str, user_email: str = "system", user_name: str = "System") -> bool:
        setlists = self.list_setlists()
        target = next((s for s in setlists if s.uuid == setlist_uuid), None)
        if not target:
            return False

        # Soft delete into trash folder for instant and persistent undo
        trash_path = os.path.join(self._trash_dir, f"setlist_{setlist_uuid}.json")
        trash_meta = {
            "deleted_at": current_iso_timestamp(),
            "entity_type": "SETLIST",
            "entity_uuid": setlist_uuid,
            "data": target.to_dict()
        }
        with open(trash_path, "w", encoding="utf-8") as f:
            json.dump(trash_meta, f, indent=2, ensure_ascii=False)

        setlists = [s for s in setlists if s.uuid != setlist_uuid]
        with open(self._setlists_file, "w", encoding="utf-8") as f:
            json.dump([s.to_dict() for s in setlists], f, indent=2, ensure_ascii=False)
        self.audit.log("DELETE", "SETLIST", setlist_uuid, user_email, user_name, {"title": target.title})
        self._trigger_background_gist_sync("SETLISTS")
        return True

    def restore_setlist(self, setlist_uuid: str, user_email: str = "system", user_name: str = "System") -> Optional[Setlist]:
        """Restores a soft-deleted setlist from trash."""
        trash_path = os.path.join(self._trash_dir, f"setlist_{setlist_uuid}.json")
        if not os.path.exists(trash_path):
            return None
        try:
            with open(trash_path, "r", encoding="utf-8") as f:
                trash_meta = json.load(f)
            setlist_data = trash_meta["data"]
            restored = Setlist.from_dict(setlist_data)
            restored.updated_at = current_iso_timestamp()
            self.save_setlist(restored, user_email, user_name)
            os.remove(trash_path)
            self.audit.log("RESTORE", "SETLIST", setlist_uuid, user_email, user_name, {"title": restored.title})
            return restored
        except Exception:
            return None

    def list_deleted_setlists(self) -> list:
        """Lists all soft-deleted setlists currently in trash."""
        deleted = []
        if not os.path.exists(self._trash_dir):
            return []
        for f in os.listdir(self._trash_dir):
            if f.startswith("setlist_") and f.endswith(".json"):
                try:
                    with open(os.path.join(self._trash_dir, f), "r", encoding="utf-8") as fp:
                        meta = json.load(fp)
                        deleted.append(meta)
                except Exception:
                    pass
        deleted.sort(key=lambda x: x.get("deleted_at", ""), reverse=True)
        return deleted

    # --- LIVE EVENTS CRUD (SRS Cap. 4.4) ---

    def list_events(self) -> List[LiveEvent]:
        if not os.path.exists(self._events_file):
            return []
        try:
            with open(self._events_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [LiveEvent.from_dict(d) for d in data]
        except Exception:
            return []

    def save_event(self, event: LiveEvent, user_email: str = "system", user_name: str = "System") -> LiveEvent:
        events = self.list_events()
        events = [e for e in events if e.uuid != event.uuid]
        event.updated_at = current_iso_timestamp()
        events.append(event)
        with open(self._events_file, "w", encoding="utf-8") as f:
            json.dump([e.to_dict() for e in events], f, indent=2, ensure_ascii=False)
        self.audit.log("UPDATE", "EVENT", event.uuid, user_email, user_name, {"name": event.name, "venue": event.venue})
        return event

    def delete_event(self, event_uuid: str, user_email: str = "system", user_name: str = "System") -> bool:
        events = self.list_events()
        before_count = len(events)
        events = [e for e in events if e.uuid != event_uuid]
        if len(events) == before_count:
            return False
        with open(self._events_file, "w", encoding="utf-8") as f:
            json.dump([e.to_dict() for e in events], f, indent=2, ensure_ascii=False)
        self.audit.log("DELETE", "EVENT", event_uuid, user_email, user_name, {})
        return True

    # --- TRASH RETENTION ---

    def clean_trash_older_than(self, days: int = 30) -> int:
        """Removes items permanently only if older than retention days (Cap. 4.7)."""
        now = datetime.now(timezone.utc)
        deleted_count = 0
        if not os.path.exists(self._trash_dir):
            return 0

        for filename in os.listdir(self._trash_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self._trash_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    del_time = datetime.fromisoformat(meta["deleted_at"])
                    if now - del_time > timedelta(days=days):
                        os.remove(filepath)
                        deleted_count += 1
                except Exception:
                    pass
        return deleted_count

    # --- CLOUD SYNCHRONIZATION ENGINE (GitHub Gist Two-Way Persistence) ---

    def sync_from_cloud(self) -> Tuple[bool, str]:
        """
        Pulls data from remote GitHub Gist and hydrates local storage.
        Prevents data loss on ephemeral cloud deployments (Streamlit Cloud).
        """
        if not hasattr(self, "gist_client") or not self.gist_client.is_configured:
            return False, "Gist non configurato (modalità offline)."

        ok, remote_files, msg = self.gist_client.pull_all_files()
        if not ok:
            return False, f"Impossibile sincronizzare da Gist: {msg}"

        synced_setlists = 0
        synced_songs = 0

        with self._mutex:
            # 1. Hydrate songs from remote repertory.json if present
            if "repertory.json" in remote_files:
                try:
                    rep_data = json.loads(remote_files["repertory.json"])
                    if isinstance(rep_data, list):
                        from asma_core.import_engine import ImportEngine
                        for r_item in rep_data:
                            if not isinstance(r_item, dict):
                                continue
                            s_id = r_item.get("id") or r_item.get("uuid")
                            if not s_id:
                                continue
                            song_path = os.path.join(self._songs_dir, f"{s_id}.json")
                            if not os.path.exists(song_path):
                                raw_text = r_item.get("raw_text") or ""
                                title = r_item.get("title") or "Brano Senza Titolo"
                                try:
                                    song = ImportEngine.import_from_traditional(raw_text, default_title=title)
                                    song.uuid = s_id
                                    song.artist = r_item.get("artist") or song.artist
                                    song.key_current = r_item.get("key") or song.key_current
                                    song.key_original = r_item.get("key") or song.key_original
                                    if r_item.get("bpm"):
                                        try:
                                            song.bpm = int(r_item.get("bpm"))
                                        except Exception:
                                            pass
                                    if r_item.get("genre"):
                                        song.genre = str(r_item.get("genre"))
                                    if r_item.get("tags") and isinstance(r_item["tags"], list):
                                        song.tags = [str(t) for t in r_item["tags"]]

                                    with open(song_path, "w", encoding="utf-8") as sf:
                                        json.dump(song.to_dict(), sf, indent=2, ensure_ascii=False)
                                    self._upsert_index_record(song)
                                    synced_songs += 1
                                except Exception:
                                    pass
                except Exception:
                    pass

            # 2. Hydrate setlists from remote setlists.json
            if "setlists.json" in remote_files:
                try:
                    raw_sets = json.loads(remote_files["setlists.json"])
                    remote_setlists: List[Setlist] = []

                    if isinstance(raw_sets, dict):
                        for k, v in raw_sets.items():
                            if not isinstance(v, dict):
                                continue
                            s_id = v.get("uuid") or v.get("id") or k
                            s_title = v.get("title") or v.get("name") or k
                            s_date = v.get("date", "")
                            s_desc = v.get("description", "")
                            raw_items = v.get("items", [])
                            if not raw_items and "song_ids" in v:
                                raw_items = [{"song_uuid": sid} for sid in v.get("song_ids", [])]
                            items = [
                                SetlistItem.from_dict(it) if isinstance(it, dict) else SetlistItem(song_uuid=str(it))
                                for it in raw_items
                            ]
                            created_at = v.get("created_at") or current_iso_timestamp()
                            updated_at = v.get("updated_at") or created_at
                            remote_setlists.append(Setlist(
                                uuid=s_id,
                                title=s_title,
                                date=s_date,
                                description=s_desc,
                                items=items,
                                created_at=created_at,
                                updated_at=updated_at
                            ))
                    elif isinstance(raw_sets, list):
                        for it in raw_sets:
                            if isinstance(it, dict):
                                remote_setlists.append(Setlist.from_dict(it))

                    local_setlists = self.list_setlists()
                    merged_dict: Dict[str, Setlist] = {s.uuid: s for s in local_setlists}

                    for r_set in remote_setlists:
                        if r_set.uuid not in merged_dict:
                            merged_dict[r_set.uuid] = r_set
                            synced_setlists += 1
                        else:
                            local_up = merged_dict[r_set.uuid].updated_at or ""
                            remote_up = r_set.updated_at or ""
                            if remote_up > local_up:
                                merged_dict[r_set.uuid] = r_set
                                synced_setlists += 1

                    final_setlists = list(merged_dict.values())
                    with open(self._setlists_file, "w", encoding="utf-8") as f:
                        json.dump([s.to_dict() for s in final_setlists], f, indent=2, ensure_ascii=False)

                except Exception:
                    pass

        return True, f"Sincronizzazione completata: {synced_setlists} scalette, {synced_songs} nuovi brani importati dal Gist."

    def sync_push_setlists_to_gist(self) -> Tuple[bool, str]:
        """Pushes all local setlists to remote GitHub Gist in dual-compatible format."""
        if not hasattr(self, "gist_client") or not self.gist_client.is_configured:
            return False, "Gist non configurato."

        setlists = self.list_setlists()
        payload_dict = {}
        for s in setlists:
            payload_dict[s.uuid] = {
                "id": s.uuid,
                "uuid": s.uuid,
                "name": s.title,
                "title": s.title,
                "date": s.date,
                "description": s.description,
                "song_ids": [it.song_uuid for it in s.items],
                "items": [it.to_dict() for it in s.items],
                "created_at": s.created_at,
                "updated_at": s.updated_at
            }
        content = json.dumps(payload_dict, indent=2, ensure_ascii=False)
        return self.gist_client.push_files({"setlists.json": content})

    def sync_push_repertory_to_gist(self) -> Tuple[bool, str]:
        """Pushes active repertoire songs to remote GitHub Gist."""
        if not hasattr(self, "gist_client") or not self.gist_client.is_configured:
            return False, "Gist non configurato."

        songs = [self.get_song(s["uuid"]) for s in self.list_songs(include_deleted=False)]
        songs = [s for s in songs if s is not None]
        rep_list = []
        for s in songs:
            rep_list.append({
                "id": s.uuid,
                "title": s.title,
                "artist": s.artist,
                "key": s.key_current,
                "bpm": s.bpm,
                "genre": s.genre,
                "tags": s.tags,
                "raw_text": s.aml_content,
                "updated_at": s.updated_at
            })
        content = json.dumps(rep_list, indent=2, ensure_ascii=False)
        return self.gist_client.push_files({"repertory.json": content})

    def _trigger_background_gist_sync(self, target: str = "SETLISTS") -> None:
        """Launches a non-blocking daemon thread to sync changes with GitHub Gist."""
        if not hasattr(self, "gist_client") or not self.gist_client.is_configured:
            return

        def _worker():
            try:
                if target in ("SETLISTS", "ALL"):
                    self.sync_push_setlists_to_gist()
                if target in ("SONGS", "ALL"):
                    self.sync_push_repertory_to_gist()
            except Exception:
                pass

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

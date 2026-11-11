"""
ASMA Accordi Next Generation - Turso Cloud Database Client
Connects ASMA 2.0 to Turso (LibSQL Serverless Cloud SQLite).
Zero-Sleep, Zero-Rate-Limit, ACID transactional cloud persistence.
Conforms to SRS Cap. 4, 18, 19.16 and Blueprint CRIT-01/CRIT-04.
"""

from __future__ import annotations
import os
import json
import glob
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import libsql_client


class TursoClient:
    """
    Client for Turso / LibSQL Cloud SQLite database.
    Operates over HTTP Hrana protocol for maximum reliability across
    local Windows, Linux, and Streamlit Community Cloud without WebSocket overhead.
    """
    _instance: Optional[TursoClient] = None

    def __new__(cls) -> TursoClient:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self) -> None:
        self.url = self._get_secret("database_url")
        self.token = self._get_secret("auth_token")

        if self.url and self.url.startswith("libsql://"):
            # Use https:// for stateless HTTP Hrana pipelining (rock-solid on Streamlit Cloud & local)
            self.http_url = self.url.replace("libsql://", "https://")
        else:
            self.http_url = self.url or ""

    @classmethod
    def _get_secret(cls, key: str) -> Optional[str]:
        # 1. Environment variable
        env_map = {
            "database_url": ["TURSO_DATABASE_URL", "LIBSQL_URL"],
            "auth_token": ["TURSO_AUTH_TOKEN", "LIBSQL_AUTH_TOKEN"]
        }
        for env_k in env_map.get(key, []):
            val = os.environ.get(env_k)
            if val and not val.startswith("YOUR_"):
                return val.strip()

        # 2. Streamlit runtime secrets
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "turso" in st.secrets:
                val = st.secrets["turso"].get(key)
                if val and not str(val).startswith("YOUR_"):
                    return str(val).strip()
        except Exception:
            pass

        # 3. Direct .streamlit/secrets.toml reading
        try:
            import tomllib
            secrets_path = os.path.join(os.getcwd(), ".streamlit", "secrets.toml")
            if os.path.exists(secrets_path):
                with open(secrets_path, "rb") as f:
                    data = tomllib.load(f)
                    val = data.get("turso", {}).get(key)
                    if val and not str(val).startswith("YOUR_"):
                        return str(val).strip()
        except Exception:
            pass

        return None

    @property
    def is_configured(self) -> bool:
        return bool(self.http_url and self.token)

    def _get_connection(self) -> libsql_client.ClientSync:
        if not self.is_configured:
            raise RuntimeError("Turso client non configurato. Verifica .streamlit/secrets.toml [turso].")
        return libsql_client.create_client_sync(url=self.http_url, auth_token=self.token)

    def init_schema(self) -> Tuple[bool, str]:
        """Creates all necessary relational tables in Turso if they do not exist."""
        if not self.is_configured:
            return False, "Turso non configurato."

        try:
            client = self._get_connection()
            client.batch([
                """
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    name TEXT,
                    role TEXT,
                    pseudonym TEXT,
                    instrument TEXT,
                    picture_url TEXT,
                    is_active INTEGER DEFAULT 1,
                    provider TEXT DEFAULT 'google',
                    updated_at TEXT
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS songs (
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
                    shared_notes TEXT,
                    aml_content TEXT,
                    lock_status TEXT,
                    current_revision INTEGER,
                    created_at TEXT,
                    updated_at TEXT,
                    is_deleted INTEGER DEFAULT 0
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS revisions (
                    song_uuid TEXT,
                    revision_number INTEGER,
                    aml_content TEXT,
                    edited_by_email TEXT,
                    edited_by_name TEXT,
                    comment TEXT,
                    created_at TEXT,
                    PRIMARY KEY (song_uuid, revision_number)
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS repertoires (
                    uuid TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    song_uuids TEXT,
                    owner_email TEXT,
                    is_official BOOLEAN DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS setlists (
                    uuid TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    date TEXT,
                    event_name TEXT,
                    items TEXT,
                    created_at TEXT,
                    updated_at TEXT
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS live_events (
                    uuid TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    event_date TEXT,
                    venue TEXT,
                    repertoire_uuid TEXT,
                    setlist_uuid TEXT,
                    notes TEXT,
                    created_at TEXT,
                    updated_at TEXT
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS user_device_preferences (
                    email TEXT NOT NULL,
                    device_name TEXT NOT NULL,
                    font_size_lyrics REAL,
                    font_size_chords REAL,
                    columns INTEGER,
                    margin_lateral_mm REAL,
                    margin_top_mm REAL,
                    margin_bottom_mm REAL,
                    color_text TEXT,
                    color_chords TEXT,
                    color_aml TEXT,
                    zoom_level REAL,
                    is_last_active INTEGER DEFAULT 0,
                    app_mode TEXT DEFAULT 'simplified',
                    score_display_mode TEXT DEFAULT 'chords',
                    extra_json TEXT,
                    updated_at TEXT,
                    PRIMARY KEY (email, device_name)
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS band_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT
                );
                """
            ])
            try:
                client.execute("ALTER TABLE repertoires ADD COLUMN owner_email TEXT;")
            except Exception:
                pass
            try:
                client.execute("ALTER TABLE repertoires ADD COLUMN is_official BOOLEAN DEFAULT 0;")
            except Exception:
                pass
            client.close()
            return True, "Schema Turso inizializzato con successo."
        except Exception as e:
            return False, f"Errore inizializzazione schema Turso: {e}"

    # ---------------- USER OPERATIONS ----------------
    def push_users(self, users: List[Dict[str, Any]]) -> Tuple[bool, str]:
        if not self.is_configured:
            return False, "Turso non configurato."
        try:
            client = self._get_connection()
            statements = []
            for u in users:
                sql = """
                INSERT INTO users (email, name, role, pseudonym, instrument, picture_url, is_active, provider, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(email) DO UPDATE SET
                    name=excluded.name,
                    role=excluded.role,
                    pseudonym=excluded.pseudonym,
                    instrument=excluded.instrument,
                    picture_url=excluded.picture_url,
                    is_active=excluded.is_active,
                    provider=excluded.provider,
                    updated_at=datetime('now');
                """
                statements.append((sql, [
                    u.get("email"),
                    u.get("name"),
                    u.get("role"),
                    u.get("pseudonym"),
                    u.get("instrument"),
                    u.get("picture_url"),
                    1 if u.get("is_active", True) else 0,
                    u.get("provider", "google")
                ]))
            client.batch(statements)
            client.close()
            return True, f"Sincronizzati {len(users)} utenti su Turso."
        except Exception as e:
            return False, f"Errore push utenti Turso: {e}"

    def fetch_users(self) -> List[Dict[str, Any]]:
        if not self.is_configured:
            return []
        try:
            client = self._get_connection()
            res = client.execute("SELECT email, name, role, pseudonym, instrument, picture_url, is_active, provider FROM users ORDER BY name ASC;")
            users = []
            for r in res.rows:
                users.append({
                    "email": r[0],
                    "name": r[1],
                    "role": r[2],
                    "pseudonym": r[3],
                    "instrument": r[4],
                    "picture_url": r[5],
                    "is_active": bool(r[6]),
                    "provider": r[7]
                })
            client.close()
            return users
        except Exception:
            return []

    # ---------------- SONG OPERATIONS ----------------
    def push_song(self, song_dict: Dict[str, Any]) -> Tuple[bool, str]:
        if not self.is_configured:
            return False, "Turso non configurato."
        try:
            client = self._get_connection()
            tags_json = json.dumps(song_dict.get("tags", [])) if isinstance(song_dict.get("tags"), list) else "[]"
            lock_json = json.dumps(song_dict.get("lock_status", {})) if isinstance(song_dict.get("lock_status"), dict) else "{}"

            sql = """
            INSERT INTO songs (
                uuid, title, artist, author, genre, year, duration_seconds, bpm,
                time_signature, capo, key_original, key_current, notation_system,
                tags, shared_notes, aml_content, lock_status, current_revision,
                created_at, updated_at, is_deleted
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(uuid) DO UPDATE SET
                title=excluded.title,
                artist=excluded.artist,
                author=excluded.author,
                genre=excluded.genre,
                year=excluded.year,
                duration_seconds=excluded.duration_seconds,
                bpm=excluded.bpm,
                time_signature=excluded.time_signature,
                capo=excluded.capo,
                key_original=excluded.key_original,
                key_current=excluded.key_current,
                notation_system=excluded.notation_system,
                tags=excluded.tags,
                shared_notes=excluded.shared_notes,
                aml_content=excluded.aml_content,
                lock_status=excluded.lock_status,
                current_revision=excluded.current_revision,
                updated_at=excluded.updated_at,
                is_deleted=excluded.is_deleted;
            """
            client.execute(sql, [
                song_dict.get("uuid"),
                song_dict.get("title"),
                song_dict.get("artist", ""),
                song_dict.get("author", ""),
                song_dict.get("genre", ""),
                song_dict.get("year", 0),
                song_dict.get("duration_seconds", 0),
                song_dict.get("bpm", 120),
                song_dict.get("time_signature", "4/4"),
                song_dict.get("capo", 0),
                song_dict.get("key_original", "DO"),
                song_dict.get("key_current", "DO"),
                song_dict.get("notation_system", "ITA"),
                tags_json,
                song_dict.get("shared_notes", ""),
                song_dict.get("aml_content", ""),
                lock_json,
                song_dict.get("current_revision", 1),
                song_dict.get("created_at"),
                song_dict.get("updated_at"),
                1 if song_dict.get("is_deleted") else 0
            ])
            client.close()
            return True, f"Brano '{song_dict.get('title')}' salvato su Turso."
        except Exception as e:
            return False, f"Errore push brano Turso: {e}"

    def soft_delete_song(self, song_uuid: str) -> Tuple[bool, str]:
        if not self.is_configured:
            return False, "Turso non configurato."
        try:
            client = self._get_connection()
            client.execute("UPDATE songs SET is_deleted = 1, updated_at = datetime('now') WHERE uuid = ?;", [song_uuid])
            client.close()
            return True, f"Brano {song_uuid} soft-deleted su Turso."
        except Exception as e:
            return False, f"Errore soft delete Turso: {e}"

    def fetch_all_songs(self) -> List[Dict[str, Any]]:
        if not self.is_configured:
            return []
        try:
            client = self._get_connection()
            sql = """
            SELECT uuid, title, artist, author, genre, year, duration_seconds, bpm,
                   time_signature, capo, key_original, key_current, notation_system,
                   tags, shared_notes, aml_content, lock_status, current_revision,
                   created_at, updated_at, is_deleted
            FROM songs
            WHERE is_deleted = 0;
            """
            res = client.execute(sql)
            songs = []
            for r in res.rows:
                tags = json.loads(r[13]) if r[13] else []
                lock_st = json.loads(r[16]) if r[16] else {}
                songs.append({
                    "uuid": r[0],
                    "title": r[1],
                    "artist": r[2],
                    "author": r[3],
                    "genre": r[4],
                    "year": r[5],
                    "duration_seconds": r[6],
                    "bpm": r[7],
                    "time_signature": r[8],
                    "capo": r[9],
                    "key_original": r[10],
                    "key_current": r[11],
                    "notation_system": r[12],
                    "tags": tags,
                    "shared_notes": r[14],
                    "aml_content": r[15],
                    "lock_status": lock_st,
                    "current_revision": r[17],
                    "created_at": r[18],
                    "updated_at": r[19],
                    "is_deleted": bool(r[20])
                })
            client.close()
            return songs
        except Exception:
            return []

    def fetch_deleted_song_map(self) -> Dict[str, str]:
        """Returns mapping {uuid: updated_at} for songs marked is_deleted=1 on Turso."""
        if not self.is_configured:
            return {}
        try:
            client = self._get_connection()
            res = client.execute("SELECT uuid, updated_at FROM songs WHERE is_deleted = 1;")
            deleted = {r[0]: (r[1] or "") for r in res.rows if r[0]}
            client.close()
            return deleted
        except Exception:
            return {}

    # ---------------- REPERTOIRES & SETLISTS ----------------
    def push_repertoires(self, repertoires: List[Dict[str, Any]]) -> Tuple[bool, str]:
        if not self.is_configured:
            return False, "Turso non configurato."
        try:
            client = self._get_connection()
            statements = []
            for rep in repertoires:
                s_uuids_json = json.dumps(rep.get("song_uuids", []))
                sql = """
                INSERT INTO repertoires (uuid, name, description, song_uuids, owner_email, is_official, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(uuid) DO UPDATE SET
                    name=excluded.name,
                    description=excluded.description,
                    song_uuids=excluded.song_uuids,
                    owner_email=excluded.owner_email,
                    is_official=excluded.is_official,
                    updated_at=excluded.updated_at;
                """
                statements.append((sql, [
                    rep.get("uuid"),
                    rep.get("name"),
                    rep.get("description", ""),
                    s_uuids_json,
                    rep.get("owner_email"),
                    1 if rep.get("is_official") else 0,
                    rep.get("created_at"),
                    rep.get("updated_at")
                ]))
            client.batch(statements)
            # Prune any repertoires from Turso that are no longer active
            active_uuids = [r.get("uuid") for r in repertoires if r.get("uuid")]
            if active_uuids:
                placeholders = ",".join("?" * len(active_uuids))
                client.execute(f"DELETE FROM repertoires WHERE uuid NOT IN ({placeholders}) OR LOWER(name) = 'provvisorio';", active_uuids)
            client.close()
            return True, f"Sincronizzati {len(repertoires)} repertori su Turso."
        except Exception as e:
            return False, f"Errore push repertori Turso: {e}"

    def delete_repertoire(self, uuid: str) -> Tuple[bool, str]:
        if not self.is_configured:
            return False, "Turso non configurato."
        try:
            client = self._get_connection()
            client.execute("DELETE FROM repertoires WHERE uuid = ? OR LOWER(name) = 'provvisorio';", [uuid])
            client.close()
            return True, f"Repertorio {uuid} eliminato da Turso."
        except Exception as e:
            return False, f"Errore eliminazione repertorio da Turso: {e}"

    def fetch_repertoires(self) -> List[Dict[str, Any]]:
        if not self.is_configured:
            return []
        try:
            client = self._get_connection()
            try:
                res = client.execute("SELECT uuid, name, description, song_uuids, created_at, updated_at, owner_email, is_official FROM repertoires;")
                reps = []
                for r in res.rows:
                    s_uuids = json.loads(r[3]) if r[3] else []
                    reps.append({
                        "uuid": r[0],
                        "name": r[1],
                        "description": r[2],
                        "song_uuids": s_uuids,
                        "created_at": r[4],
                        "updated_at": r[5],
                        "owner_email": r[6] if len(r) > 6 else None,
                        "is_official": bool(r[7]) if len(r) > 7 and r[7] is not None else False
                    })
            except Exception:
                res = client.execute("SELECT uuid, name, description, song_uuids, created_at, updated_at FROM repertoires;")
                reps = []
                for r in res.rows:
                    s_uuids = json.loads(r[3]) if r[3] else []
                    reps.append({
                        "uuid": r[0],
                        "name": r[1],
                        "description": r[2],
                        "song_uuids": s_uuids,
                        "created_at": r[4],
                        "updated_at": r[5]
                    })
            client.close()
            return reps
        except Exception:
            return []

    def push_setlists(self, setlists: List[Dict[str, Any]]) -> Tuple[bool, str]:
        if not self.is_configured:
            return False, "Turso non configurato."
        try:
            client = self._get_connection()
            statements = []
            for s in setlists:
                items_json = json.dumps(s.get("items", []))
                sql = """
                INSERT INTO setlists (uuid, title, date, event_name, items, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(uuid) DO UPDATE SET
                    title=excluded.title,
                    date=excluded.date,
                    event_name=excluded.event_name,
                    items=excluded.items,
                    updated_at=excluded.updated_at;
                """
                statements.append((sql, [
                    s.get("uuid"),
                    s.get("title"),
                    s.get("date", ""),
                    s.get("description") or s.get("event_name", ""),
                    items_json,
                    s.get("created_at"),
                    s.get("updated_at")
                ]))
            client.batch(statements)
            client.close()
            return True, f"Sincronizzate {len(setlists)} scalette su Turso."
        except Exception as e:
            return False, f"Errore push scalette Turso: {e}"

    def delete_setlist(self, setlist_uuid: str) -> bool:
        if not self.is_configured or not setlist_uuid:
            return False
        try:
            client = self._get_connection()
            client.execute("DELETE FROM setlists WHERE uuid = ?;", [setlist_uuid])
            client.close()
            return True
        except Exception:
            return False

    def fetch_setlists(self) -> List[Dict[str, Any]]:
        if not self.is_configured:
            return []
        try:
            client = self._get_connection()
            res = client.execute("SELECT uuid, title, date, event_name, items, created_at, updated_at FROM setlists;")
            sets = []
            for r in res.rows:
                items = json.loads(r[4]) if r[4] else []
                desc = r[3] or ""
                sets.append({
                    "uuid": r[0],
                    "title": r[1],
                    "date": r[2],
                    "description": desc,
                    "event_name": desc,
                    "items": items,
                    "created_at": r[5],
                    "updated_at": r[6]
                })
            client.close()
            return sets
        except Exception:
            return []

    # ---------------- MIGRATION UTILITY ----------------
    def migrate_all_local_data_to_turso(self, data_dir: str) -> Dict[str, Any]:
        """
        One-shot automated migration utility:
        Reads all local JSON files in data/ and safely uploads them to Turso.
        """
        self.init_schema()
        results = {
            "users_count": 0,
            "songs_count": 0,
            "revisions_count": 0,
            "repertoires_count": 0,
            "setlists_count": 0,
            "errors": []
        }

        # 1. Users
        users_file = os.path.join(data_dir, "users.json")
        if os.path.exists(users_file):
            try:
                with open(users_file, "r", encoding="utf-8") as f:
                    users_data = json.load(f)
                ok, msg = self.push_users(users_data)
                if ok:
                    results["users_count"] = len(users_data)
                else:
                    results["errors"].append(f"Users: {msg}")
            except Exception as e:
                results["errors"].append(f"Users load error: {e}")

        # 2. Repertoires
        rep_file = os.path.join(data_dir, "repertoires.json")
        if os.path.exists(rep_file):
            try:
                with open(rep_file, "r", encoding="utf-8") as f:
                    rep_data = json.load(f)
                ok, msg = self.push_repertoires(rep_data)
                if ok:
                    results["repertoires_count"] = len(rep_data)
                else:
                    results["errors"].append(f"Repertoires: {msg}")
            except Exception as e:
                results["errors"].append(f"Repertoires error: {e}")

        # 3. Setlists
        set_file = os.path.join(data_dir, "setlists.json")
        if os.path.exists(set_file):
            try:
                with open(set_file, "r", encoding="utf-8") as f:
                    set_data = json.load(f)
                if isinstance(set_data, list):
                    ok, msg = self.push_setlists(set_data)
                    if ok:
                        results["setlists_count"] = len(set_data)
            except Exception as e:
                results["errors"].append(f"Setlists error: {e}")

        # 4. Songs
        songs_dir = os.path.join(data_dir, "songs")
        if os.path.exists(songs_dir):
            song_files = glob.glob(os.path.join(songs_dir, "*.json"))
            for sf in song_files:
                try:
                    with open(sf, "r", encoding="utf-8") as f:
                        s_data = json.load(f)
                    ok, msg = self.push_song(s_data)
                    if ok:
                        results["songs_count"] += 1
                    else:
                        results["errors"].append(f"Song {s_data.get('title')}: {msg}")
                except Exception as e:
                    results["errors"].append(f"Song file {sf}: {e}")

        # 5. Revisions
        revs_dir = os.path.join(data_dir, "revisions")
        if os.path.exists(revs_dir):
            rev_files = glob.glob(os.path.join(revs_dir, "*.json"))
            client = self._get_connection()
            rev_stmts = []
            for rf in rev_files:
                try:
                    with open(rf, "r", encoding="utf-8") as f:
                        r_data = json.load(f)
                    rev_list = r_data if isinstance(r_data, list) else [r_data]
                    for r_item in rev_list:
                        sql = """
                        INSERT INTO revisions (song_uuid, revision_number, aml_content, edited_by_email, edited_by_name, comment, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(song_uuid, revision_number) DO NOTHING;
                        """
                        rev_stmts.append((sql, [
                            r_item.get("song_uuid") or r_item.get("uuid"),
                            r_item.get("revision_number", 1),
                            r_item.get("aml_content", ""),
                            r_item.get("edited_by_email", ""),
                            r_item.get("edited_by_name", ""),
                            r_item.get("comment", ""),
                            r_item.get("created_at") or r_item.get("timestamp")
                        ]))
                except Exception as e:
                    results["errors"].append(f"Rev file {rf}: {e}")
            if rev_stmts:
                try:
                    client.batch(rev_stmts)
                    results["revisions_count"] = len(rev_stmts)
                except Exception as e:
                    results["errors"].append(f"Batch revisions error: {e}")
            client.close()

        return results

    # ---------------- USER & MULTI-DEVICE PREFERENCES ----------------
    def push_user_device_preference(
        self,
        email: str,
        device_name: str,
        prefs: Dict[str, Any],
        is_last_active: bool = False
    ) -> Tuple[bool, str]:
        if not self.is_configured:
            return False, "Turso non configurato."
        try:
            client = self._get_connection()
            email_clean = email.lower().strip()

            if is_last_active:
                client.execute(
                    "UPDATE user_device_preferences SET is_last_active = 0 WHERE email = ?;",
                    [email_clean]
                )

            sql = """
            INSERT INTO user_device_preferences (
                email, device_name, font_size_lyrics, font_size_chords,
                columns, margin_lateral_mm, margin_top_mm, margin_bottom_mm,
                color_text, color_chords, color_aml, zoom_level,
                is_last_active, app_mode, score_display_mode, extra_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(email, device_name) DO UPDATE SET
                font_size_lyrics=excluded.font_size_lyrics,
                font_size_chords=excluded.font_size_chords,
                columns=excluded.columns,
                margin_lateral_mm=excluded.margin_lateral_mm,
                margin_top_mm=excluded.margin_top_mm,
                margin_bottom_mm=excluded.margin_bottom_mm,
                color_text=excluded.color_text,
                color_chords=excluded.color_chords,
                color_aml=excluded.color_aml,
                zoom_level=excluded.zoom_level,
                is_last_active=excluded.is_last_active,
                app_mode=excluded.app_mode,
                score_display_mode=excluded.score_display_mode,
                extra_json=excluded.extra_json,
                updated_at=datetime('now');
            """
            extra = {k: v for k, v in prefs.items() if k not in [
                "layout_font_size", "layout_font_size_chords", "layout_columns",
                "layout_margin_lateral", "layout_margin_top", "layout_margin_bottom",
                "layout_color_text", "layout_color_chords", "layout_color_aml",
                "ui_zoom_level", "app_mode", "score_display_mode"
            ]}
            client.execute(sql, [
                email_clean,
                device_name,
                float(prefs.get("layout_font_size", 12.0)),
                float(prefs.get("layout_font_size_chords", 13.0)),
                int(prefs.get("layout_columns", 1)),
                float(prefs.get("layout_margin_lateral", 10.0)),
                float(prefs.get("layout_margin_top", 8.0)),
                float(prefs.get("layout_margin_bottom", 8.0)),
                str(prefs.get("layout_color_text", "#111111")),
                str(prefs.get("layout_color_chords", "#B71C1C")),
                str(prefs.get("layout_color_aml", "#4A148C")),
                float(prefs.get("ui_zoom_level", 1.0)),
                1 if is_last_active else 0,
                str(prefs.get("app_mode", "simplified")),
                str(prefs.get("score_display_mode", "chords")),
                json.dumps(extra)
            ])
            client.close()
            return True, f"Preferenze salvate per {email_clean} su {device_name}."
        except Exception as e:
            return False, f"Errore salvataggio preferenze Turso: {e}"

    def fetch_user_device_preference(self, email: str, device_name: str) -> Optional[Dict[str, Any]]:
        if not self.is_configured:
            return None
        try:
            client = self._get_connection()
            sql = """
            SELECT font_size_lyrics, font_size_chords, columns, margin_lateral_mm,
                   margin_top_mm, margin_bottom_mm, color_text, color_chords, color_aml,
                   zoom_level, is_last_active, app_mode, score_display_mode, extra_json, updated_at
            FROM user_device_preferences
            WHERE email = ? AND device_name = ?;
            """
            res = client.execute(sql, [email.lower().strip(), device_name])
            client.close()
            if not res.rows:
                return None
            r = res.rows[0]
            extra = json.loads(r[13]) if r[13] else {}
            data = {
                "layout_font_size": r[0],
                "layout_font_size_chords": r[1],
                "layout_columns": r[2],
                "layout_margin_lateral": r[3],
                "layout_margin_top": r[4],
                "layout_margin_bottom": r[5],
                "layout_color_text": r[6],
                "layout_color_chords": r[7],
                "layout_color_aml": r[8],
                "ui_zoom_level": r[9],
                "is_last_active": bool(r[10]),
                "app_mode": r[11] or "simplified",
                "score_display_mode": r[12] or "chords",
                "updated_at": r[14]
            }
            data.update(extra)
            return data
        except Exception:
            return None

    def fetch_all_user_preferences(self, email: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.is_configured:
            return []
        try:
            client = self._get_connection()
            if email:
                sql = """
                SELECT email, device_name, font_size_lyrics, font_size_chords, columns,
                       margin_lateral_mm, margin_top_mm, margin_bottom_mm, color_text,
                       color_chords, color_aml, zoom_level, is_last_active,
                       app_mode, score_display_mode, extra_json, updated_at
                FROM user_device_preferences
                WHERE email = ?;
                """
                res = client.execute(sql, [email.lower().strip()])
            else:
                sql = """
                SELECT email, device_name, font_size_lyrics, font_size_chords, columns,
                       margin_lateral_mm, margin_top_mm, margin_bottom_mm, color_text,
                       color_chords, color_aml, zoom_level, is_last_active,
                       app_mode, score_display_mode, extra_json, updated_at
                FROM user_device_preferences;
                """
                res = client.execute(sql)
            client.close()
            records = []
            for r in res.rows:
                extra = json.loads(r[15]) if r[15] else {}
                item = {
                    "email": r[0],
                    "device_name": r[1],
                    "font_size_lyrics": r[2],
                    "font_size_chords": r[3],
                    "columns": r[4],
                    "margin_lateral_mm": r[5],
                    "margin_top_mm": r[6],
                    "margin_bottom_mm": r[7],
                    "color_text": r[8],
                    "color_chords": r[9],
                    "color_aml": r[10],
                    "zoom_level": r[11],
                    "is_last_active": bool(r[12]),
                    "app_mode": r[13] or "simplified",
                    "score_display_mode": r[14] or "chords",
                    "updated_at": r[16]
                }
                item.update(extra)
                records.append(item)
            return records
        except Exception:
            return []

    def set_last_active_device(self, email: str, device_name: str) -> bool:
        if not self.is_configured:
            return False
        try:
            client = self._get_connection()
            email_clean = email.lower().strip()
            client.execute("UPDATE user_device_preferences SET is_last_active = 0 WHERE email = ?;", [email_clean])
            client.execute("UPDATE user_device_preferences SET is_last_active = 1 WHERE email = ? AND device_name = ?;", [email_clean, device_name])
            client.close()
            return True
        except Exception:
            return False

    def get_setting(self, key: str) -> Optional[str]:
        """Retrieves a persistent key-value setting from Turso band_settings table."""
        if not self.is_configured:
            return None
        try:
            client = self._get_connection()
            client.execute("CREATE TABLE IF NOT EXISTS band_settings (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT);")
            res = client.execute("SELECT value FROM band_settings WHERE key = ?;", [key])
            client.close()
            if res.rows and res.rows[0][0] is not None:
                return str(res.rows[0][0])
            return None
        except Exception:
            return None

    def set_setting(self, key: str, value: str) -> bool:
        """Stores a persistent key-value setting in Turso band_settings table."""
        if not self.is_configured:
            return False
        try:
            client = self._get_connection()
            client.execute("CREATE TABLE IF NOT EXISTS band_settings (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT);")
            now_iso = datetime.now(timezone.utc).isoformat()
            client.execute(
                "INSERT INTO band_settings (key, value, updated_at) VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at;",
                [key, value, now_iso]
            )
            client.close()
            return True
        except Exception:
            return False


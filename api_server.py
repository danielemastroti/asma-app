"""
ASMA 2.0 - High Performance FastAPI Backend API
Conforms to SRS & PWA Architecture Blueprint.
Provides clean REST API endpoints for all asma_core services.
Deploy test: verify personal repertoire persistence across cloud deploys.
"""

from __future__ import annotations
import os
import io
import re
import json
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from asma_core.models import Song, Repertoire, Setlist, SetlistItem, DeviceProfile, generate_uuid
from asma_core.storage_manager import StorageManager
from asma_core.music_engine import MusicEngine
from asma_core.aml_parser import AMLParser
from asma_core.pdf_engine import PDFEngine
from asma_core.printer_engine import PrinterEngine
from asma_core.export_engine import ExportEngine
from asma_core.import_engine import ImportEngine
from asma_core.web_importer import WebSongImporter
from asma_core.auth_manager import AuthManager
from asma_core.preferences_manager import PreferencesManager
from asma_core.device_manager import DeviceManager
from asma_core.audit_logger import AuditLogger
from asma_core.operation_logger import OperationLogger

app = FastAPI(
    title="THE New ASMA - Live Band API",
    description="High-performance backend API for Live Stage, Setlists, AML and Device-Aware Sheet Music",
    version="2.0.0"
)

# Enable CORS for any frontend (localhost, Vercel, Cloudflare, tablet browsers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_cache_control_header(request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.endswith((".html", ".js", ".css", ".json")):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Core Singletons
storage = StorageManager()
auth_mgr = AuthManager()
pref_mgr = PreferencesManager()
device_mgr = DeviceManager()
audit = AuditLogger()
op_logger = OperationLogger()


# -----------------------------------------------------------------------------
# PYDANTIC SCHEMAS
# -----------------------------------------------------------------------------

class SongCreateRequest(BaseModel):
    title: str
    artist: Optional[str] = "Band"
    author: Optional[str] = ""
    genre: Optional[str] = ""
    bpm: Optional[int] = 120
    time_signature: Optional[str] = "4/4"
    capo: Optional[int] = 0
    key_current: Optional[str] = "C"
    aml_content: Optional[str] = ""
    repertoire_uuid: Optional[str] = None
    user_email: Optional[str] = "cico@band.org"
    user_name: Optional[str] = "Cico"
    comment: Optional[str] = "Nuovo brano"

class SongUpdateRequest(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    author: Optional[str] = None
    genre: Optional[str] = None
    bpm: Optional[int] = None
    time_signature: Optional[str] = None
    capo: Optional[int] = None
    key_current: Optional[str] = None
    aml_content: Optional[str] = None
    tags: Optional[List[str]] = None
    user_email: Optional[str] = "cico@band.org"
    user_name: Optional[str] = "Cico"
    comment: Optional[str] = "Modifica brano"

class TransposeRequest(BaseModel):
    semitones: int
    user_email: Optional[str] = "cico@band.org"
    user_name: Optional[str] = "Cico"

class RepertoireCreateRequest(BaseModel):
    uuid: Optional[str] = None
    name: str
    description: Optional[str] = ""
    song_uuids: Optional[List[str]] = []
    is_official: Optional[bool] = False
    owner_email: Optional[str] = None
    user_email: Optional[str] = "cico@band.org"
    user_name: Optional[str] = "Cico"

class PromoteSongRequest(BaseModel):
    song_uuid: str
    user_email: Optional[str] = "cico@band.org"
    user_name: Optional[str] = "Cico"

class ForkSongRequest(BaseModel):
    user_email: Optional[str] = "cico@band.org"
    user_name: Optional[str] = "Cico"

class SetlistItemSchema(BaseModel):
    song_uuid: str
    is_medley: Optional[bool] = False
    medley_group_id: Optional[str] = None
    custom_key: Optional[str] = None
    custom_bpm: Optional[int] = None
    notes: Optional[str] = ""

class SetlistSaveRequest(BaseModel):
    uuid: Optional[str] = None
    title: str
    date: Optional[str] = ""
    description: Optional[str] = ""
    items: List[SetlistItemSchema] = []
    user_email: Optional[str] = "cico@band.org"
    user_name: Optional[str] = "Cico"

class ConvertTextRequest(BaseModel):
    raw_text: str
    title: Optional[str] = "Nuovo Brano"
    artist: Optional[str] = "Band"

class VisionImageItem(BaseModel):
    data: str
    mime_type: Optional[str] = "image/jpeg"

class VisionImportRequest(BaseModel):
    images: List[VisionImageItem]
    user_email: Optional[str] = "cico@band.org"
    user_name: Optional[str] = "Cico"

class ImportUrlRequest(BaseModel):
    url: str
    user_email: Optional[str] = "cico@band.org"
    user_name: Optional[str] = "Cico"

class UserPreferencesRequest(BaseModel):
    app_mode: Optional[str] = "simplified"
    score_display_mode: Optional[str] = "chords"
    device_name: Optional[str] = "Huawei MediaPad M5"
    layout_font_size: Optional[float] = 12.0
    layout_font_size_chords: Optional[float] = 13.0
    layout_columns: Optional[int] = 1
    layout_margin_lateral: Optional[float] = 10.0
    layout_margin_top: Optional[float] = 10.0
    color_lyrics: Optional[str] = "#111111"
    color_chords: Optional[str] = "#B71C1C"
    color_aml_markup: Optional[str] = "#4A148C"
    stage_color_lyrics: Optional[str] = "#FFFFFF"
    stage_color_chords: Optional[str] = "#FFD600"
    stage_color_aml_markup: Optional[str] = "#38BDF8"

class AISettingsRequest(BaseModel):
    gemini_api_key: str


# -----------------------------------------------------------------------------
# 1. HEALTH & SYSTEM ENDPOINTS
# -----------------------------------------------------------------------------

@app.get("/api/health")
def get_health():
    """Healthcheck and database status."""
    songs = storage.list_songs()
    reps = storage.list_repertoires()
    sets = storage.list_setlists()
    turso_status = "connected" if storage.turso_client else "local_only"
    return {
        "status": "online",
        "app": "THE New ASMA",
        "version": "2.0.0",
        "turso_status": turso_status,
        "counts": {
            "songs": len(songs),
            "repertoires": len(reps),
            "setlists": len(sets)
        }
    }

@app.get("/api/auth/users")
def get_authorized_users():
    """Returns the list of authorized band members."""
    users = auth_mgr.list_users()
    return [{"email": u.email, "name": u.name, "role": u.role.value if hasattr(u.role, "value") else str(u.role)} for u in users]


# -----------------------------------------------------------------------------
# 2. REPERTOIRE ENDPOINTS
# -----------------------------------------------------------------------------

@app.get("/api/repertoires")
def list_repertoires(user_email: Optional[str] = Query(None)):
    """Lists all repertoires with accurate valid song counts, respecting access rules:
       - Official repertoire: visible to all musicians.
       - Personal repertoire: visible only to owner and admin.
       - Admin: sees all repertoires.
    """
    all_reps = storage.list_repertoires()
    all_songs = storage.list_songs()
    valid_song_uuids = {s["uuid"] for s in all_songs}

    is_admin = False
    if user_email:
        u = auth_mgr.get_user_by_email(user_email)
        if u and u.can_admin():
            is_admin = True
        elif user_email in ["danyposta@gmail.com", "danyposta@yahoo.it"]:
            is_admin = True
    else:
        is_admin = True

    result = []
    has_user_personal = False
    for r in all_reps:
        is_off = getattr(r, "is_official", False)
        owner = getattr(r, "owner_email", None)

        if not is_admin and user_email:
            if not is_off and owner != user_email:
                continue

        if owner == user_email:
            has_user_personal = True

        valid_count = len([uid for uid in r.song_uuids if uid in valid_song_uuids])
        result.append({
            "uuid": r.uuid,
            "name": r.name,
            "description": r.description,
            "is_official": is_off,
            "owner_email": owner,
            "song_count": valid_count,
            "song_uuids": [uid for uid in r.song_uuids if uid in valid_song_uuids],
            "updated_at": r.updated_at
        })

    # If user is a logged-in band member and doesn't have a personal repertoire yet, auto-create one
    if user_email and not has_user_personal and not is_admin:
        u = auth_mgr.get_user_by_email(user_email)
        u_name = u.name if u else user_email.split("@")[0].capitalize()
        new_personal = Repertoire(
            name=f"{u_name}",
            description=f"Repertorio personale di {u_name}",
            is_official=False,
            owner_email=user_email,
            song_uuids=[]
        )
        saved = storage.save_repertoire(new_personal, user_email, u_name)
        result.append({
            "uuid": saved.uuid,
            "name": saved.name,
            "description": saved.description,
            "is_official": False,
            "owner_email": user_email,
            "song_count": 0,
            "song_uuids": [],
            "updated_at": saved.updated_at
        })

    def _rep_sort_key(x):
        if x["is_official"]:
            return (0, x["name"])
        if user_email and x.get("owner_email") == user_email:
            return (1, x["name"])
        return (2, x["name"])

    result.sort(key=_rep_sort_key)
    return result

@app.get("/api/repertoires/{uuid}")
def get_repertoire(uuid: str):
    """Gets repertoire details and full song summaries inside it."""
    rep = storage.get_repertoire(uuid)
    if not rep:
        raise HTTPException(status_code=404, detail="Repertorio non trovato")

    songs_in_rep = []
    for uid in rep.song_uuids:
        s = storage.get_song(uid)
        if s:
            songs_in_rep.append({
                "uuid": s.uuid,
                "title": s.title,
                "artist": s.artist,
                "author": s.author,
                "key_current": s.key_current,
                "bpm": s.bpm,
                "duration_seconds": s.duration_seconds
            })
    return {
        "uuid": rep.uuid,
        "name": rep.name,
        "description": rep.description,
        "is_official": getattr(rep, "is_official", False),
        "owner_email": getattr(rep, "owner_email", None),
        "song_count": len(songs_in_rep),
        "songs": songs_in_rep,
        "updated_at": rep.updated_at
    }

def is_admin_email(email: Optional[str]) -> bool:
    if not email:
        return False
    u = auth_mgr.get_user_by_email(email)
    if u and u.can_admin():
        return True
    return email.lower() in ["danyposta@gmail.com", "danyposta@yahoo.it"]

@app.post("/api/repertoires")
def save_repertoire(req: RepertoireCreateRequest):
    """Creates or updates a repertoire (Admin only for non-personal repertoires)."""
    is_admin = is_admin_email(req.user_email)

    if req.uuid:
        existing = storage.get_repertoire(req.uuid)
        if existing:
            if getattr(existing, "is_official", False) and not is_admin:
                raise HTTPException(status_code=403, detail="Solo l'amministratore può modificare il Repertorio Ufficiale")
            if getattr(existing, "owner_email", None) and getattr(existing, "owner_email") != req.user_email and not is_admin:
                raise HTTPException(status_code=403, detail="Permesso negato per questo repertorio")

            existing.name = req.name.strip()
            if req.description is not None:
                existing.description = req.description.strip()
            saved = storage.save_repertoire(existing, req.user_email, req.user_name)
            return {"status": "success", "repertoire": saved.to_dict()}

    if not is_admin and req.is_official:
        raise HTTPException(status_code=403, detail="Solo l'amministratore può creare repertori ufficiali")

    rep = Repertoire(
        uuid=req.uuid or "",
        name=req.name.strip(),
        description=req.description.strip() if req.description else "",
        song_uuids=req.song_uuids or [],
        is_official=req.is_official or False,
        owner_email=req.owner_email or (None if req.is_official else req.user_email)
    )
    saved = storage.save_repertoire(rep, req.user_email, req.user_name)
    return {"status": "success", "repertoire": saved.to_dict()}

@app.post("/api/repertoires/promote-song")
def promote_song_to_official(req: PromoteSongRequest):
    """Adds a song from a personal repertoire into the Official Band Repertoire."""
    all_reps = storage.list_repertoires()
    official_rep = next((r for r in all_reps if getattr(r, "is_official", False)), None)
    if not official_rep:
        official_rep = all_reps[0] if all_reps else None
    if not official_rep:
        raise HTTPException(status_code=404, detail="Repertorio Ufficiale non trovato")
    song = storage.get_song(req.song_uuid)
    if not song:
        raise HTTPException(status_code=404, detail="Brano non trovato")

    if req.song_uuid not in official_rep.song_uuids:
        official_rep.song_uuids.append(req.song_uuid)
        storage.save_repertoire(official_rep, req.user_email, req.user_name)

    return {
        "status": "success",
        "song_uuid": req.song_uuid,
        "song_title": song.title,
        "repertoire_uuid": official_rep.uuid,
        "repertoire_name": official_rep.name
    }

@app.delete("/api/repertoires/{uuid}")
def delete_repertoire(uuid: str, user_email: str = "cico@band.org", user_name: str = "Cico"):
    """Deletes a repertoire safely (Admin only or owner of personal repertoire)."""
    rep = storage.get_repertoire(uuid)
    if not rep:
        raise HTTPException(status_code=404, detail="Repertorio non trovato")
    if getattr(rep, "is_official", False):
        raise HTTPException(status_code=400, detail="Il Repertorio Ufficiale della Band non può essere eliminato")

    is_admin = is_admin_email(user_email)
    is_owner = getattr(rep, "owner_email", None) == user_email
    if not (is_admin or is_owner):
        raise HTTPException(status_code=403, detail="Solo l'amministratore può eliminare questo repertorio")

    success = storage.delete_repertoire(uuid, user_email, user_name)
    if not success:
        raise HTTPException(status_code=404, detail="Repertorio non trovato")
    return {"status": "success", "deleted_uuid": uuid}

@app.post("/api/songs/{uuid}/fork-personal")
def fork_song_personal(uuid: str, req: ForkSongRequest):
    """Creates an independent personal copy of the song in the user's personal repertoire."""
    source_song = storage.get_song(uuid)
    if not source_song:
        raise HTTPException(status_code=404, detail="Brano sorgente non trovato")

    all_reps = storage.list_repertoires()
    target_rep = next((r for r in all_reps if getattr(r, "owner_email", None) == req.user_email), None)
    if not target_rep:
        u = auth_mgr.get_user_by_email(req.user_email)
        u_name = u.name if u else req.user_name
        target_rep = Repertoire(
            name=f"{u_name}",
            description=f"Repertorio personale di {u_name}",
            is_official=False,
            owner_email=req.user_email,
            song_uuids=[]
        )
        target_rep = storage.save_repertoire(target_rep, req.user_email, req.user_name)

    cloned_song = Song(
        title=source_song.title,
        artist=source_song.artist,
        author=source_song.author,
        genre=source_song.genre,
        year=source_song.year,
        duration_seconds=source_song.duration_seconds,
        bpm=source_song.bpm,
        time_signature=source_song.time_signature,
        capo=source_song.capo,
        key_original=source_song.key_original,
        key_current=source_song.key_current,
        notation_system=source_song.notation_system,
        tags=list(source_song.tags) if source_song.tags else [],
        aml_content=source_song.aml_content,
        shared_notes=f"Versione personale di {req.user_name}"
    )
    saved = storage.save_song(cloned_song, req.user_email, req.user_name, f"Copia personale creata da {req.user_name}")
    try:
        storage.move_song_to_repertoire(saved.uuid, target_rep.uuid, req.user_email, req.user_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "status": "success",
        "cloned_song": saved.to_dict(),
        "target_repertoire_uuid": target_rep.uuid,
        "target_repertoire_name": target_rep.name
    }


# -----------------------------------------------------------------------------
# 3. SONGS ENDPOINTS
# -----------------------------------------------------------------------------

@app.get("/api/songs")
def list_songs(
    repertoire_uuid: Optional[str] = Query(None, description="Filtra per repertorio (__ALL__ per archivio intero)"),
    search: Optional[str] = Query(None, description="Filtra per testo nel titolo o autore"),
    user_email: Optional[str] = Query(None, description="Email musicista per scoping permessi")
):
    """Lists songs filtered by repertoire, user role, and optional text search."""
    all_songs = sorted(storage.list_songs(), key=lambda s: s["title"].lower())
    all_reps = storage.list_repertoires()

    is_admin = is_admin_email(user_email) if user_email else True

    if user_email and not is_admin:
        # Non-admin musician: can ONLY see songs in Official Repertoire and their own Personal Repertoire
        visible_reps = [
            r for r in all_reps
            if getattr(r, "is_official", False) or getattr(r, "owner_email", None) == user_email
        ]
        visible_song_uuids = set()
        for r in visible_reps:
            visible_song_uuids.update(r.song_uuids)

        if repertoire_uuid and repertoire_uuid != "__ALL__":
            target_rep = next((r for r in visible_reps if r.uuid == repertoire_uuid), None)
            if target_rep:
                allowed_uids = set(target_rep.song_uuids)
                all_songs = [s for s in all_songs if s["uuid"] in allowed_uids]
            else:
                all_songs = []
        else:
            all_songs = [s for s in all_songs if s["uuid"] in visible_song_uuids]

        # In assigned_repertoires, only include repertoires visible to this user
        for s in all_songs:
            s_reps = [r.name for r in visible_reps if s["uuid"] in r.song_uuids]
            s["assigned_repertoires"] = s_reps
    else:
        # Admin or unscoped API call
        if repertoire_uuid and repertoire_uuid != "__ALL__":
            rep = storage.get_repertoire(repertoire_uuid)
            if rep:
                allowed_uids = set(rep.song_uuids)
                all_songs = [s for s in all_songs if s["uuid"] in allowed_uids]
            else:
                all_songs = []

        # Include repertoire names for each song
        for s in all_songs:
            s_reps = [r.name for r in all_reps if s["uuid"] in r.song_uuids]
            s["assigned_repertoires"] = s_reps

    from asma_core.music_engine import MusicEngine
    for s in all_songs:
        raw_k = s.get("key_current", "C")
        s["key_current"] = MusicEngine.convert_notation(raw_k, "ITA") if raw_k else "DO"

    if search and search.strip():
        kw = search.strip().lower()
        all_songs = [
            s for s in all_songs
            if (kw in s["title"].lower() or kw in s.get("artist", "").lower() or kw in s.get("author", "").lower())
        ]

    return all_songs

@app.get("/api/songs/web-search")
def search_songs_online(
    title: str = Query(..., description="Titolo del brano"),
    artist: Optional[str] = Query("", description="Artista opzionale"),
    limit: int = Query(10, ge=1, le=20)
):
    """Searches online chord portals (Accordi e Spartiti, Ultimate Guitar) for candidate charts."""
    clean_title = title.strip()
    if not clean_title:
        raise HTTPException(status_code=400, detail="Il titolo del brano è obbligatorio")

    clean_artist = (artist or "").strip()
    try:
        candidates = WebSongImporter.search_online_candidates(clean_title, clean_artist, limit=limit)
        return {
            "status": "success",
            "query": {"title": clean_title, "artist": clean_artist},
            "count": len(candidates),
            "candidates": candidates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore ricerca online: {str(e)}")

@app.get("/api/songs/{uuid}")
def get_song(uuid: str):
    """Returns single song data, revisions count, and assigned repertoires."""
    song = storage.get_song(uuid)
    if not song:
        raise HTTPException(status_code=404, detail="Brano non trovato")

    all_reps = storage.list_repertoires()
    assigned = [r.name for r in all_reps if song.uuid in r.song_uuids]
    
    ita_key = MusicEngine.convert_notation(song.key_current, "ITA") if song.key_current else "-"
    orig_ita = MusicEngine.convert_notation(song.key_original, "ITA") if song.key_original else "-"

    res = song.to_dict()
    res["key_current"] = ita_key
    res["key_original"] = orig_ita
    res["key_current_ita"] = ita_key
    res["key_original_ita"] = orig_ita
    res["assigned_repertoires"] = assigned
    return res

@app.post("/api/songs")
def create_song(req: SongCreateRequest):
    """Creates a new song, stores AML, and adds to repertoire if specified."""
    song = Song(
        title=req.title.strip().upper(),
        artist=req.artist.strip() if req.artist else "Band",
        author=req.author.strip() if req.author else "",
        genre=req.genre.strip() if req.genre else "",
        bpm=req.bpm or 120,
        time_signature=req.time_signature or "4/4",
        capo=req.capo or 0,
        key_original=req.key_current or "C",
        key_current=req.key_current or "C",
        aml_content=req.aml_content or "{verse}\n[DO]Testo iniziale...\n"
    )
    target_rep_uuid = req.repertoire_uuid
    if not target_rep_uuid or target_rep_uuid == "__ALL__":
        all_reps = storage.list_repertoires()
        if all_reps:
            official_rep = next((r for r in all_reps if getattr(r, "is_official", False)), all_reps[0])
            target_rep_uuid = official_rep.uuid

    if target_rep_uuid:
        can_add, reason = storage.can_add_song_to_repertoire(target_rep_uuid, song.title)
        if not can_add:
            raise HTTPException(status_code=409, detail=reason)

    saved = storage.save_song(song, req.user_email, req.user_name, req.comment or "Creazione brano")
    if target_rep_uuid:
        storage.move_song_to_repertoire(saved.uuid, target_rep_uuid, req.user_email, req.user_name)
    return {"status": "success", "song": saved.to_dict()}

@app.put("/api/songs/{uuid}")
def update_song(uuid: str, req: SongUpdateRequest):
    """Updates song attributes and AML body, creating a new revision snapshot."""
    song = storage.get_song(uuid)
    if not song:
        raise HTTPException(status_code=404, detail="Brano non trovato")

    if req.title is not None and req.title.strip().upper() != song.title.strip().upper():
        new_title = req.title.strip().upper()
        all_reps = storage.list_repertoires()
        for r in all_reps:
            if uuid in r.song_uuids:
                can_add, reason = storage.can_add_song_to_repertoire(r.uuid, new_title, exclude_song_uuid=uuid)
                if not can_add:
                    raise HTTPException(status_code=409, detail=reason)
        song.title = new_title
    if req.artist is not None:
        song.artist = req.artist.strip()
    if req.author is not None:
        song.author = req.author.strip()
    if req.genre is not None:
        song.genre = req.genre.strip()
    if req.bpm is not None:
        song.bpm = req.bpm
    if req.time_signature is not None:
        song.time_signature = req.time_signature
    if req.capo is not None:
        song.capo = req.capo
    if req.key_current is not None:
        song.key_current = req.key_current
    if req.aml_content is not None:
        song.aml_content = req.aml_content
    if req.tags is not None:
        song.tags = req.tags

    saved = storage.save_song(song, req.user_email, req.user_name, req.comment or "Modifica brano")
    return {"status": "success", "song": saved.to_dict()}

@app.delete("/api/songs/{uuid}")
def delete_song(uuid: str, user_email: str = "cico@band.org", user_name: str = "Cico"):
    """Soft deletes song into trash with protected undo/restore capability."""
    success = storage.delete_song(uuid, user_email, user_name)
    if not success:
        raise HTTPException(status_code=404, detail="Brano non trovato")
    return {"status": "success", "deleted_uuid": uuid}

@app.post("/api/songs/{uuid}/restore")
def restore_song(uuid: str, user_email: str = "cico@band.org", user_name: str = "Cico"):
    """Restores a soft-deleted song from trash (Immediate protected Undo)."""
    restored = storage.restore_song(uuid, user_email, user_name)
    if not restored:
        raise HTTPException(status_code=404, detail="Brano non trovato nel cestino o già ripristinato")
    return {"status": "success", "song": restored.to_dict()}

@app.post("/api/songs/convert-text")
def convert_raw_text(req: ConvertTextRequest):
    """Converts traditional chords-over-lyrics or ChordPro into official AML markup."""
    text = req.raw_text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Testo non fornito")

    # If already bracketed ChordPro with metadata directives
    if "{" in text and "}" in text and any(d in text.lower() for d in ["title:", "t:", "artist:", "key:"]):
        song = ImportEngine.import_from_chordpro(text)
    else:
        song = ImportEngine.import_from_traditional(text, default_title=req.title or "Nuovo Brano")

    return {
        "status": "success",
        "title": song.title or req.title or "Nuovo Brano",
        "artist": song.artist or req.artist or "Band",
        "key": song.key_current or "C",
        "bpm": song.bpm or 120,
        "capo": song.capo or 0,
        "aml": song.aml_content
    }

@app.post("/api/songs/import-url")
def import_song_from_url(req: ImportUrlRequest):
    """Fetches chords and lyrics from public URL and returns AML-ready structure."""
    if not req.url or not req.url.startswith("http"):
        raise HTTPException(status_code=400, detail="URL non valido")
    try:
        song = WebSongImporter.fetch_from_url(req.url)
        return {
            "status": "success",
            "title": song.title or "Nuovo Brano",
            "artist": song.artist or "Band",
            "key": song.key_current or "C",
            "bpm": song.bpm or 120,
            "capo": song.capo or 0,
            "aml": song.aml_content
        }
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Errore importazione web: {str(e)}")

@app.post("/api/songs/import-vision")
def import_song_from_vision(req: VisionImportRequest):
    """Transcribes photographed sheet music pages into AML format using Gemini Vision."""
    if not req.images:
        raise HTTPException(status_code=400, detail="Nessuna immagine fornita")
    try:
        from asma_core.ai_service import BandAIService
        image_dicts = [{"data": img.data, "mime_type": img.mime_type or "image/jpeg"} for img in req.images]
        res = BandAIService.transcribe_sheet_music_images(image_dicts)
        return {
            "status": "success",
            "title": res.get("title", "Nuovo Brano"),
            "artist": res.get("artist", ""),
            "key": res.get("key", "DO"),
            "bpm": res.get("bpm", 120),
            "capo": res.get("capo", 0),
            "aml": res.get("aml_content", "")
        }
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Errore trascrizione Vision: {str(e)}")

@app.post("/api/songs/{uuid}/transpose")
def transpose_song(uuid: str, req: TransposeRequest):
    """Transposes song AML and keys by +/- N semitones."""
    song = storage.get_song(uuid)
    if not song:
        raise HTTPException(status_code=404, detail="Brano non trovato")

    if req.semitones == 0:
        return {"status": "noop", "song": song.to_dict()}

    doc = AMLParser.parse(song.aml_content)
    new_doc = AMLParser.transpose_document(doc, semitones=req.semitones)
    song.aml_content = new_doc.to_aml()
    if song.key_current and song.key_current != "-":
        try:
            song.key_current = MusicEngine.transpose_chord(song.key_current, req.semitones)
        except Exception:
            pass

    saved = storage.save_song(song, req.user_email, req.user_name, f"Trasposizione ({req.semitones:+d} semitoni)")
    return {"status": "success", "song": saved.to_dict()}


# -----------------------------------------------------------------------------
# 4. PDF GENERATION & PRINT ENDPOINTS
# -----------------------------------------------------------------------------

def resolve_user_pseudonym(email: Optional[str] = None, fallback_name: Optional[str] = None) -> str:
    """Resolves the musician's pseudonym (e.g. Cico, Sentimental, Maurino) based on email or name."""
    if fallback_name and fallback_name.strip():
        clean = re.sub(r'\(.*?\)', '', fallback_name).strip()
        if clean:
            return clean
    if not email:
        return ""
    email_clean = email.strip().lower()
    users_path = os.path.join(os.path.dirname(__file__), "data", "users.json")
    if os.path.exists(users_path):
        try:
            with open(users_path, "r", encoding="utf-8") as f:
                users = json.load(f)
                for u in users:
                    if u.get("email", "").strip().lower() == email_clean:
                        n = u.get("name", "").strip()
                        clean_n = re.sub(r'\(.*?\)', '', n).strip()
                        if clean_n:
                            return clean_n
        except Exception:
            pass
    try:
        all_reps = storage.list_repertoires()
        for r in all_reps:
            if getattr(r, "owner_email", None) == email_clean and not getattr(r, "is_official", False):
                clean_r = re.sub(r'\(.*?\)', '', r.name).strip()
                if clean_r:
                    return clean_r
    except Exception:
        pass
    local = email_clean.split("@")[0]
    return local.capitalize()


def resolve_device_profile(device_name: Optional[str]) -> DeviceProfile:
    """Finds exact or fuzzy matched device profile, supporting common aliases."""
    if not device_name:
        return device_mgr.get_device_by_name("Huawei MediaPad M5") or DeviceProfile(name="Huawei MediaPad M5")
    prof = device_mgr.get_device_by_name(device_name)
    if prof:
        return prof
    d_clean = device_name.strip().lower()
    if "a4" in d_clean:
        prof = device_mgr.get_device_by_name("Foglio a 4 stampabile")
        if prof:
            return prof
    for d in device_mgr.list_devices():
        if d_clean in d.name.lower() or d.name.lower() in d_clean:
            return d
    return device_mgr.get_device_by_name("Huawei MediaPad M5") or DeviceProfile(name=device_name)


@app.get("/api/songs/{uuid}/pdf")
def get_song_pdf(
    uuid: str,
    device: str = Query("Huawei MediaPad M5", description="Nome profilo hardware di destinazione"),
    chords: bool = Query(True, description="True per spartito con accordi, False per solo testo cantante"),
    columns: Optional[int] = Query(None, description="Forza 1 o 2 colonne"),
    email: Optional[str] = Query(None, description="Email musicista per caricare preferenze da Turso DB"),
    user_name: Optional[str] = Query(None, description="Pseudonimo musicista (es. Cico, Sentimental)"),
    download: bool = Query(False, description="True per forzare il download con header attachment"),
    font_size: Optional[float] = Query(None, description="Override dimensione font testo"),
    font_size_chords: Optional[float] = Query(None, description="Override dimensione font accordi"),
    margin_lateral: Optional[float] = Query(None, description="Override margini laterali (mm)"),
    margin_top: Optional[float] = Query(None, description="Override margine superiore (mm)"),
    a4: bool = Query(False, description="True per impaginare su foglio A4 mantenendo la formattazione del device"),
    autoprint: bool = Query(False, description="True per iniettare comando di stampa automatica diretta")
):
    """Generates and streams formatted device-aware PDF for display or download."""
    import pymupdf
    song = storage.get_song(uuid)
    if not song:
        raise HTTPException(status_code=404, detail="Brano non trovato")

    base_prof = resolve_device_profile(device)

    # Clona il profilo per non mutare l'istanza globale
    prof = DeviceProfile(
        name=base_prof.name,
        target_device=base_prof.target_device,
        device_type=base_prof.device_type,
        width_mm=base_prof.width_mm,
        height_mm=base_prof.height_mm,
        orientation=base_prof.orientation,
        columns=base_prof.columns,
        font_size_lyrics=base_prof.font_size_lyrics,
        font_size_chords=base_prof.font_size_chords,
        margin_top_mm=base_prof.margin_top_mm,
        margin_bottom_mm=base_prof.margin_bottom_mm,
        margin_left_mm=base_prof.margin_left_mm,
        margin_right_mm=base_prof.margin_right_mm,
        color_lyrics=getattr(base_prof, "color_lyrics", "#111111"),
        color_chords=getattr(base_prof, "color_chords", "#B71C1C"),
        color_aml_markup=getattr(base_prof, "color_aml_markup", "#4A148C")
    )

    # Se passata l'email del musicista, applica le preferenze personali caricate da Turso DB
    if email:
        user_prefs = pref_mgr.get_preferences(email, prof.name)
        if user_prefs:
            if "layout_font_size" in user_prefs:
                prof.font_size_lyrics = float(user_prefs["layout_font_size"])
            if "layout_font_size_chords" in user_prefs:
                prof.font_size_chords = float(user_prefs["layout_font_size_chords"])
            if "layout_columns" in user_prefs:
                prof.columns = int(user_prefs["layout_columns"])
            if "layout_margin_lateral" in user_prefs:
                lat = float(user_prefs["layout_margin_lateral"])
                prof.margin_left_mm = lat
                prof.margin_right_mm = lat
            if "layout_margin_top" in user_prefs:
                prof.margin_top_mm = float(user_prefs["layout_margin_top"])
            if "color_lyrics" in user_prefs:
                prof.color_lyrics = user_prefs["color_lyrics"]
            elif "layout_color_text" in user_prefs:
                prof.color_lyrics = user_prefs["layout_color_text"]
            if "color_chords" in user_prefs:
                prof.color_chords = user_prefs["color_chords"]
            elif "layout_color_chords" in user_prefs:
                prof.color_chords = user_prefs["layout_color_chords"]
            if "color_aml_markup" in user_prefs:
                prof.color_aml_markup = user_prefs["color_aml_markup"]
            elif "layout_color_aml" in user_prefs:
                prof.color_aml_markup = user_prefs["layout_color_aml"]

    if columns is not None:
        prof.columns = columns
    if font_size is not None:
        prof.font_size_lyrics = font_size
    if font_size_chords is not None:
        prof.font_size_chords = font_size_chords
    if margin_lateral is not None:
        prof.margin_left_mm = margin_lateral
        prof.margin_right_mm = margin_lateral
    if margin_top is not None:
        prof.margin_top_mm = margin_top

    if a4 or "foglio" in device.lower():
        prof.width_mm = 210.0
        prof.height_mm = 297.0
        prof.target_device = "pc_a4"
        prof.device_type = "printable_a4"

    pseudonym = resolve_user_pseudonym(email, user_name)
    pdf_bytes = PDFEngine.generate_song_pdf(song, profile=prof, include_chords=chords, use_cache=not (a4 or autoprint), user_name=pseudonym)

    if autoprint:
        try:
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
            cat = doc.pdf_catalog()
            action_xref = doc.get_new_xref()
            doc.update_object(action_xref, "<< /S /JavaScript /JS (print\\(\\);) >>")
            doc.xref_set_key(cat, "OpenAction", f"{action_xref} 0 R")
            pdf_bytes = doc.tobytes(garbage=3)
        except Exception:
            pass
    filename = re.sub(r'[^a-zA-Z0-9_\-]', '_', song.title).strip('_') or "brano"

    disp = "attachment" if download else "inline"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{disp}; filename="{filename}.pdf"'
        }
    )

_pdf_pages_cache: Dict[str, List[str]] = {}

@app.get("/api/songs/{uuid}/pdf/preview")
def get_song_pdf_preview(
    uuid: str,
    device: str = Query("Huawei MediaPad M5", description="Nome profilo hardware di destinazione"),
    chords: bool = Query(True, description="True per spartito con accordi, False per solo testo"),
    columns: Optional[int] = Query(None, description="Forza 1 o 2 colonne"),
    email: Optional[str] = Query(None, description="Email musicista per preferenze"),
    user_name: Optional[str] = Query(None, description="Pseudonimo musicista"),
    font_size: Optional[float] = Query(None, description="Override dimensione font testo"),
    font_size_chords: Optional[float] = Query(None, description="Override dimensione font accordi"),
    margin_lateral: Optional[float] = Query(None, description="Override margini laterali"),
    margin_top: Optional[float] = Query(None, description="Override margine superiore (mm)")
):
    """
    Renders high-resolution formatted PDF pages as base64 images for real sheet-music preview.
    Matches 100% the layout, font size, chord wrapping, and page distribution of exported PDF.
    """
    import base64
    import pymupdf

    song = storage.get_song(uuid)
    if not song:
        raise HTTPException(status_code=404, detail="Brano non trovato")

    base_prof = resolve_device_profile(device)
    prof = DeviceProfile(
        name=base_prof.name,
        target_device=base_prof.target_device,
        device_type=base_prof.device_type,
        width_mm=base_prof.width_mm,
        height_mm=base_prof.height_mm,
        orientation=base_prof.orientation,
        columns=base_prof.columns,
        font_size_lyrics=base_prof.font_size_lyrics,
        font_size_chords=base_prof.font_size_chords,
        margin_top_mm=base_prof.margin_top_mm,
        margin_bottom_mm=base_prof.margin_bottom_mm,
        margin_left_mm=base_prof.margin_left_mm,
        margin_right_mm=base_prof.margin_right_mm,
        color_lyrics=getattr(base_prof, "color_lyrics", "#111111"),
        color_chords=getattr(base_prof, "color_chords", "#B71C1C"),
        color_aml_markup=getattr(base_prof, "color_aml_markup", "#4A148C")
    )

    if email:
        user_prefs = pref_mgr.get_preferences(email, prof.name)
        if user_prefs:
            if "layout_font_size" in user_prefs:
                prof.font_size_lyrics = float(user_prefs["layout_font_size"])
            if "layout_font_size_chords" in user_prefs:
                prof.font_size_chords = float(user_prefs["layout_font_size_chords"])
            if "layout_columns" in user_prefs:
                prof.columns = int(user_prefs["layout_columns"])
            if "layout_margin_lateral" in user_prefs:
                lat = float(user_prefs["layout_margin_lateral"])
                prof.margin_left_mm = lat
                prof.margin_right_mm = lat
            if "layout_margin_top" in user_prefs:
                prof.margin_top_mm = float(user_prefs["layout_margin_top"])
            if "color_lyrics" in user_prefs:
                prof.color_lyrics = user_prefs["color_lyrics"]
            elif "layout_color_text" in user_prefs:
                prof.color_lyrics = user_prefs["layout_color_text"]
            if "color_chords" in user_prefs:
                prof.color_chords = user_prefs["color_chords"]
            elif "layout_color_chords" in user_prefs:
                prof.color_chords = user_prefs["layout_color_chords"]
            if "color_aml_markup" in user_prefs:
                prof.color_aml_markup = user_prefs["color_aml_markup"]
            elif "layout_color_aml" in user_prefs:
                prof.color_aml_markup = user_prefs["layout_color_aml"]

    if columns is not None:
        prof.columns = columns
    if font_size is not None:
        prof.font_size_lyrics = font_size
    if font_size_chords is not None:
        prof.font_size_chords = font_size_chords
    if margin_lateral is not None:
        prof.margin_left_mm = margin_lateral
        prof.margin_right_mm = margin_lateral
    if margin_top is not None:
        prof.margin_top_mm = margin_top

    pseudonym = resolve_user_pseudonym(email, user_name)
    cache_key = (
        f"{song.uuid}_{song.updated_at}_{prof.name}_{prof.columns}_{prof.font_size_lyrics}_"
        f"{prof.font_size_chords}_{prof.margin_left_mm}_{prof.margin_top_mm}_{prof.color_lyrics}_{prof.color_chords}_"
        f"{prof.color_aml_markup}_{chords}_{pseudonym}"
    )

    if cache_key in _pdf_pages_cache:
        cached_pages = _pdf_pages_cache[cache_key]
        return {
            "uuid": song.uuid,
            "title": song.title,
            "total_pages": len(cached_pages),
            "device": prof.name,
            "chords": chords,
            "columns": prof.columns,
            "pages": cached_pages
        }

    pdf_bytes = PDFEngine.generate_song_pdf(song, profile=prof, include_chords=chords, use_cache=True, user_name=pseudonym)
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    pages_b64 = []
    for page in doc:
        pix = page.get_pixmap(dpi=125)
        png_data = pix.tobytes("png")
        b64 = "data:image/png;base64," + base64.b64encode(png_data).decode("ascii")
        pages_b64.append(b64)

    if len(_pdf_pages_cache) > 100:
        _pdf_pages_cache.clear()
    _pdf_pages_cache[cache_key] = pages_b64

    return {
        "uuid": song.uuid,
        "title": song.title,
        "total_pages": len(pages_b64),
        "device": prof.name,
        "chords": chords,
        "columns": prof.columns,
        "pages": pages_b64
    }

@app.get("/api/songs/{uuid}/export/{export_format}")
def export_song_file(uuid: str, export_format: str):
    """Exports song in standard music formats (songbook, mobilesheets, chordpro, onsong)."""
    song = storage.get_song(uuid)
    if not song:
        raise HTTPException(status_code=404, detail="Brano non trovato")

    clean_t = re.sub(r'[\\/*?:"<>|]', '', song.title).strip() or "brano"
    fmt = export_format.lower()

    if fmt in ["songbook", "sb"]:
        content = ExportEngine.export_for_songbookpro(song)
        ext = "pro"
    elif fmt in ["mobilesheets", "ms"]:
        content = ExportEngine.export_for_mobilesheets(song)
        ext = "pro"
    elif fmt in ["chordpro", "cho"]:
        content = ExportEngine.export_to_chordpro(song.aml_content)
        ext = "cho"
    elif fmt in ["onsong", "os"]:
        content = ExportEngine.export_for_onsong(song)
        ext = "onsong"
    else:
        raise HTTPException(status_code=400, detail="Formato di esportazione non supportato")

    return Response(
        content=content.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{clean_t}.{ext}"'
        }
    )


# -----------------------------------------------------------------------------
# 5. SETLISTS ENDPOINTS
# -----------------------------------------------------------------------------

def format_date_ddmmyyyy(date_val: Optional[str]) -> str:
    if not date_val:
        return ""
    s = str(date_val).strip()
    parts = s.split("T")[0].split("-")
    if len(parts) == 3 and len(parts[0]) == 4:
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    return s


@app.get("/api/setlists")
def list_setlists():
    """Lists all active setlists with item counts and total duration."""
    all_sets = storage.list_setlists()
    result = []
    for s in all_sets:
        result.append({
            "uuid": s.uuid,
            "title": s.title,
            "date": format_date_ddmmyyyy(s.date),
            "raw_date": s.date,
            "description": s.description,
            "item_count": len(s.items),
            "updated_at": s.updated_at
        })
    return result

@app.get("/api/setlists/{uuid}")
def get_setlist(uuid: str):
    """Gets setlist with full resolved song details for every item."""
    s = storage.get_setlist(uuid)
    if not s:
        raise HTTPException(status_code=404, detail="Scaletta non trovata")

    from asma_core.music_engine import MusicEngine
    resolved_items = []
    total_duration = 0
    for idx, item in enumerate(s.items):
        song = storage.get_song(item.song_uuid)
        dur = song.duration_seconds if song else 0
        total_duration += dur
        raw_k = item.custom_key or (song.key_current if song else "-")
        ita_k = MusicEngine.convert_notation(raw_k, "ITA") if raw_k and raw_k != "-" else "-"
        resolved_items.append({
            "index": idx + 1,
            "song_uuid": item.song_uuid,
            "title": song.title if song else "Brano non trovato",
            "artist": song.artist if song else "",
            "key": ita_k,
            "bpm": item.custom_bpm or (song.bpm if song else 120),
            "duration_seconds": dur,
            "is_medley": item.is_medley,
            "medley_group_id": item.medley_group_id,
            "notes": item.notes
        })

    return {
        "uuid": s.uuid,
        "title": s.title,
        "date": format_date_ddmmyyyy(s.date),
        "raw_date": s.date,
        "description": s.description,
        "total_songs": len(resolved_items),
        "total_duration_seconds": total_duration,
        "items": resolved_items,
        "updated_at": s.updated_at
    }

@app.post("/api/setlists")
def save_setlist(req: SetlistSaveRequest):
    """Creates or updates a setlist without intrusive popovers."""
    items = [
        SetlistItem(
            song_uuid=it.song_uuid,
            is_medley=it.is_medley or False,
            medley_group_id=it.medley_group_id,
            custom_key=it.custom_key,
            custom_bpm=it.custom_bpm,
            notes=it.notes or ""
        )
        for it in req.items
    ]
    setlist_uuid = req.uuid.strip() if (req.uuid and req.uuid.strip()) else generate_uuid()
    setlist = Setlist(
        uuid=setlist_uuid,
        title=req.title.strip(),
        date=req.date.strip() if req.date else "",
        description=req.description.strip() if req.description else "",
        items=items
    )
    saved = storage.save_setlist(setlist, req.user_email, req.user_name)
    return {"status": "success", "setlist": saved.to_dict()}

@app.post("/api/setlists/{uuid}/songs/{song_uuid}")
def add_song_to_setlist(uuid: str, song_uuid: str, user_email: str = "cico@band.org", user_name: str = "Cico"):
    """Adds a single song to the end of a setlist in 1 click."""
    s = storage.get_setlist(uuid)
    if not s:
        raise HTTPException(status_code=404, detail="Scaletta non trovata")
    song = storage.get_song(song_uuid)
    if not song:
        raise HTTPException(status_code=404, detail="Brano non trovato")

    s.items.append(SetlistItem(song_uuid=song_uuid))
    saved = storage.save_setlist(s, user_email, user_name)
    return {
        "status": "success",
        "setlist_uuid": s.uuid,
        "setlist_title": s.title,
        "song_uuid": song.uuid,
        "song_title": song.title,
        "total_items": len(s.items)
    }

@app.delete("/api/setlists/{uuid}")
def delete_setlist(uuid: str, user_email: str = "cico@band.org", user_name: str = "Cico"):
    """Deletes setlist into trash."""
    success = storage.delete_setlist(uuid, user_email, user_name)
    if not success:
        raise HTTPException(status_code=404, detail="Scaletta non trovata")
    return {"status": "success", "deleted_uuid": uuid}

@app.get("/api/setlists/{uuid}/pdf")
def get_setlist_pdf(
    uuid: str,
    device: str = Query("Huawei MediaPad M5", description="Nome profilo hardware di destinazione"),
    chords: bool = Query(True, description="True per spartiti con accordi, False per solo testi cantante"),
    columns: Optional[int] = Query(None, description="Forza 1 o 2 colonne"),
    email: Optional[str] = Query(None, description="Email musicista per caricare preferenze da Turso DB"),
    user_name: Optional[str] = Query(None, description="Pseudonimo musicista"),
    download: bool = Query(False, description="True per forzare il download con header attachment"),
    font_size: Optional[float] = Query(None, description="Override dimensione font testo"),
    font_size_chords: Optional[float] = Query(None, description="Override dimensione font accordi"),
    margin_lateral: Optional[float] = Query(None, description="Override margini laterali (mm)"),
    margin_top: Optional[float] = Query(None, description="Override margine superiore (mm)"),
    a4: bool = Query(False, description="True per impaginare su foglio A4 mantenendo la formattazione del device"),
    autoprint: bool = Query(False, description="True per iniettare comando di stampa automatica diretta")
):
    """Generates consolidated setlist PDF (cover + index + songs) for tablet display or print."""
    import pymupdf
    s = storage.get_setlist(uuid)
    if not s:
        raise HTTPException(status_code=404, detail="Scaletta non trovata")

    resolved_songs = []
    for item in s.items:
        song = storage.get_song(item.song_uuid)
        if song:
            resolved_songs.append(song)

    base_prof = resolve_device_profile(device)
    prof = DeviceProfile(
        name=base_prof.name,
        target_device=base_prof.target_device,
        device_type=base_prof.device_type,
        width_mm=base_prof.width_mm,
        height_mm=base_prof.height_mm,
        orientation=base_prof.orientation,
        columns=base_prof.columns,
        font_size_lyrics=base_prof.font_size_lyrics,
        font_size_chords=base_prof.font_size_chords,
        margin_top_mm=base_prof.margin_top_mm,
        margin_bottom_mm=base_prof.margin_bottom_mm,
        margin_left_mm=base_prof.margin_left_mm,
        margin_right_mm=base_prof.margin_right_mm,
        color_lyrics=getattr(base_prof, "color_lyrics", "#111111"),
        color_chords=getattr(base_prof, "color_chords", "#B71C1C"),
        color_aml_markup=getattr(base_prof, "color_aml_markup", "#4A148C")
    )

    if email:
        user_prefs = pref_mgr.get_preferences(email, prof.name)
        if user_prefs:
            if "layout_font_size" in user_prefs:
                prof.font_size_lyrics = float(user_prefs["layout_font_size"])
            if "layout_font_size_chords" in user_prefs:
                prof.font_size_chords = float(user_prefs["layout_font_size_chords"])
            if "layout_columns" in user_prefs:
                prof.columns = int(user_prefs["layout_columns"])
            if "layout_margin_lateral" in user_prefs:
                lat = float(user_prefs["layout_margin_lateral"])
                prof.margin_left_mm = lat
                prof.margin_right_mm = lat
            if "layout_margin_top" in user_prefs:
                prof.margin_top_mm = float(user_prefs["layout_margin_top"])
            if "color_lyrics" in user_prefs:
                prof.color_lyrics = user_prefs["color_lyrics"]
            elif "layout_color_text" in user_prefs:
                prof.color_lyrics = user_prefs["layout_color_text"]
            if "color_chords" in user_prefs:
                prof.color_chords = user_prefs["color_chords"]
            elif "layout_color_chords" in user_prefs:
                prof.color_chords = user_prefs["layout_color_chords"]
            if "color_aml_markup" in user_prefs:
                prof.color_aml_markup = user_prefs["color_aml_markup"]
            elif "layout_color_aml" in user_prefs:
                prof.color_aml_markup = user_prefs["layout_color_aml"]

    if columns is not None:
        prof.columns = columns
    if font_size is not None:
        prof.font_size_lyrics = font_size
    if font_size_chords is not None:
        prof.font_size_chords = font_size_chords
    if margin_lateral is not None:
        prof.margin_left_mm = margin_lateral
        prof.margin_right_mm = margin_lateral
    if margin_top is not None:
        prof.margin_top_mm = margin_top

    if a4 or "foglio" in device.lower():
        prof.width_mm = 210.0
        prof.height_mm = 297.0
        prof.target_device = "pc_a4"
        prof.device_type = "printable_a4"

    pseudonym = resolve_user_pseudonym(email, user_name)
    pdf_bytes = PDFEngine.generate_setlist_pdf(s, resolved_songs, profile=prof, include_chords=chords, user_name=pseudonym)

    if autoprint:
        try:
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
            cat = doc.pdf_catalog()
            action_xref = doc.get_new_xref()
            doc.update_object(action_xref, "<< /S /JavaScript /JS (print\\(\\);) >>")
            doc.xref_set_key(cat, "OpenAction", f"{action_xref} 0 R")
            pdf_bytes = doc.tobytes(garbage=3)
        except Exception:
            pass
    disp = "attachment" if download else "inline"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{disp}; filename="SCALETTA_LIVE.pdf"'
        }
    )


# -----------------------------------------------------------------------------
# 6. HARDWARE DEVICES & USER PREFERENCES
# -----------------------------------------------------------------------------

@app.get("/api/users")
def list_users():
    """Lists registered band members and their roles."""
    users = auth_mgr.list_users()
    return [
        {
            "name": u.name,
            "email": u.email,
            "role": u.role.value if hasattr(u.role, 'value') else str(u.role),
            "picture_url": getattr(u, "picture_url", "")
        }
        for u in users
    ]

@app.get("/api/devices")
def list_devices():
    """Lists all pre-configured hardware profiles (Huawei, iPad, A4, etc.)."""
    profiles = device_mgr.list_devices()
    return [
        {
            "name": p.name,
            "target_device": p.target_device,
            "device_type": p.device_type,
            "width_mm": p.width_mm,
            "height_mm": p.height_mm,
            "orientation": p.orientation,
            "columns": p.columns
        }
        for p in profiles
    ]

@app.get("/api/preferences/{email}")
def get_user_preferences(email: str, device: Optional[str] = "Huawei MediaPad M5"):
    """Retrieves synced preferences for user and device category."""
    prof = resolve_device_profile(device)
    dev_name = prof.name if prof else (device or "Huawei MediaPad M5")
    prefs = pref_mgr.get_preferences(email, dev_name)
    app_mode = prefs.get("app_mode") or pref_mgr.get_user_preference(email, "app_mode", default="simplified")
    default_score_mode = "lyrics" if ("cico" in email.lower() or "acicchelli" in email.lower()) else "chords"
    score_mode = prefs.get("score_display_mode") or pref_mgr.get_user_preference(email, "score_display_mode", default=default_score_mode)
    prefs["app_mode"] = app_mode
    prefs["score_display_mode"] = score_mode
    # Normalizza i campi colore per compatibilità incrociata Streamlit & PWA
    if "layout_color_text" in prefs and "color_lyrics" not in prefs:
        prefs["color_lyrics"] = prefs["layout_color_text"]
    if "layout_color_chords" in prefs and "color_chords" not in prefs:
        prefs["color_chords"] = prefs["layout_color_chords"]
    if "layout_color_aml" in prefs and "color_aml_markup" not in prefs:
        prefs["color_aml_markup"] = prefs["layout_color_aml"]

    # Valori predefiniti per la palette Teleprompter Modalità Palco (sfondo nero)
    prefs.setdefault("stage_color_lyrics", "#FFFFFF")
    prefs.setdefault("stage_color_chords", "#FFD600")
    prefs.setdefault("stage_color_aml_markup", "#38BDF8")
    return prefs

@app.post("/api/preferences/{email}")
def save_user_preferences(email: str, req: UserPreferencesRequest):
    """Persists user & device preferences to Turso Cloud DB."""
    prof = resolve_device_profile(req.device_name)
    dev_name = prof.name if prof else (req.device_name or "Huawei MediaPad M5")
    c_lyric = req.color_lyrics or "#111111"
    c_chord = req.color_chords or "#B71C1C"
    c_aml = req.color_aml_markup or "#4A148C"
    c_stage_lyric = req.stage_color_lyrics or "#FFFFFF"
    c_stage_chord = req.stage_color_chords or "#FFD600"
    c_stage_aml = req.stage_color_aml_markup or "#38BDF8"
    payload = {
        "app_mode": req.app_mode or "simplified",
        "score_display_mode": req.score_display_mode or "chords",
        "layout_font_size": req.layout_font_size or 12.0,
        "layout_font_size_chords": req.layout_font_size_chords or 13.0,
        "layout_columns": req.layout_columns or 1,
        "layout_margin_lateral": req.layout_margin_lateral if req.layout_margin_lateral is not None else 10.0,
        "layout_margin_top": req.layout_margin_top if req.layout_margin_top is not None else 10.0,
        "color_lyrics": c_lyric,
        "layout_color_text": c_lyric,
        "color_chords": c_chord,
        "layout_color_chords": c_chord,
        "color_aml_markup": c_aml,
        "layout_color_aml": c_aml,
        "stage_color_lyrics": c_stage_lyric,
        "stage_color_chords": c_stage_chord,
        "stage_color_aml_markup": c_stage_aml
    }
    pref_mgr.set_user_preference(email, "app_mode", payload["app_mode"])
    pref_mgr.set_user_preference(email, "score_display_mode", payload["score_display_mode"])
    pref_mgr.save_preferences(email, dev_name, payload)
    return {"status": "success", "saved": payload}


@app.get("/api/settings/ai")
def get_ai_settings():
    """Returns whether Gemini Vision AI API key is configured (masked)."""
    from asma_core.ai_service import BandAIService
    k = BandAIService.get_api_key()
    masked = f"{k[:6]}...{k[-4:]}" if k and len(k) > 10 else ("Configurata" if k else "")
    return {"configured": bool(k), "masked_key": masked}


@app.post("/api/settings/ai")
def save_ai_settings(req: AISettingsRequest):
    """Saves Gemini Vision AI API key persistently into Turso band_settings."""
    from asma_core.ai_service import BandAIService
    if not req.gemini_api_key or not req.gemini_api_key.strip():
        raise HTTPException(status_code=400, detail="Chiave API non valida")
    ok = BandAIService.save_api_key(req.gemini_api_key.strip())
    if not ok:
        raise HTTPException(status_code=500, detail="Impossibile salvare la chiave su Turso DB")
    return {"status": "success", "configured": True}


# -----------------------------------------------------------------------------
# 7. LIVE STAGE TELEPROMPTER PAYLOAD
# -----------------------------------------------------------------------------

@app.get("/api/stage/song/{uuid}")
def get_stage_song_payload(uuid: str):
    """Provides high-performance pre-parsed lines and chords for 60fps teleprompter."""
    song = storage.get_song(uuid)
    if not song:
        raise HTTPException(status_code=404, detail="Brano non trovato")

    # Parse AML directly into structured sections
    try:
        doc = AMLParser.parse(song.aml_content)
        sections = []
        for sec in doc.sections:
            lines = []
            for item in sec.items:
                aml_str = item.to_aml() if hasattr(item, "to_aml") else str(item)
                lines.append(aml_str)
            sections.append({
                "type": sec.section_type.value if hasattr(sec.section_type, "value") else str(sec.section_type),
                "title": getattr(sec, "title", None) or sec.section_type.value,
                "lines": lines
            })
    except Exception:
        sections = []

    return {
        "uuid": song.uuid,
        "title": song.title,
        "artist": song.artist,
        "key_current": song.key_current,
        "bpm": song.bpm,
        "capo": song.capo,
        "aml_content": song.aml_content,
        "sections": sections
    }


# -----------------------------------------------------------------------------
# 8. PWA STATIC FILES MOUNT (Serves PWA directly from FastAPI)
# -----------------------------------------------------------------------------
from fastapi.staticfiles import StaticFiles

if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=False)

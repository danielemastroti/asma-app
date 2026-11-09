"""
ASMA 2.0 - High Performance FastAPI Backend API
Conforms to SRS & PWA Architecture Blueprint.
Provides clean REST API endpoints for all asma_core services.
"""

from __future__ import annotations
import os
import io
import re
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from asma_core.models import Song, Repertoire, Setlist, SetlistItem, DeviceProfile
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
    name: str
    description: Optional[str] = ""
    song_uuids: Optional[List[str]] = []
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

class UserPreferencesRequest(BaseModel):
    app_mode: Optional[str] = "simplified"
    score_display_mode: Optional[str] = "chords"
    device_name: Optional[str] = "Huawei MediaPad M5"
    layout_font_size: Optional[float] = 12.0
    layout_font_size_chords: Optional[float] = 13.0
    layout_columns: Optional[int] = 1
    layout_margin_lateral: Optional[float] = 10.0
    color_lyrics: Optional[str] = "#111111"
    color_chords: Optional[str] = "#B71C1C"
    color_aml_markup: Optional[str] = "#4A148C"


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
def list_repertoires():
    """Lists all repertoires with accurate valid song counts."""
    all_reps = storage.list_repertoires()
    all_songs = storage.list_songs()
    valid_song_uuids = {s["uuid"] for s in all_songs}

    result = []
    for r in all_reps:
        valid_count = len([uid for uid in r.song_uuids if uid in valid_song_uuids])
        result.append({
            "uuid": r.uuid,
            "name": r.name,
            "description": r.description,
            "song_count": valid_count,
            "song_uuids": [uid for uid in r.song_uuids if uid in valid_song_uuids],
            "updated_at": r.updated_at
        })
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
        "song_count": len(songs_in_rep),
        "songs": songs_in_rep,
        "updated_at": rep.updated_at
    }

@app.post("/api/repertoires")
def save_repertoire(req: RepertoireCreateRequest):
    """Creates or updates a repertoire."""
    rep = Repertoire(
        name=req.name.strip(),
        description=req.description.strip(),
        song_uuids=req.song_uuids or []
    )
    saved = storage.save_repertoire(rep, req.user_email, req.user_name)
    return {"status": "success", "repertoire": saved.to_dict()}

@app.delete("/api/repertoires/{uuid}")
def delete_repertoire(uuid: str, user_email: str = "cico@band.org", user_name: str = "Cico"):
    """Deletes a repertoire safely."""
    success = storage.delete_repertoire(uuid, user_email, user_name)
    if not success:
        raise HTTPException(status_code=404, detail="Repertorio non trovato")
    return {"status": "success", "deleted_uuid": uuid}


# -----------------------------------------------------------------------------
# 3. SONGS ENDPOINTS
# -----------------------------------------------------------------------------

@app.get("/api/songs")
def list_songs(
    repertoire_uuid: Optional[str] = Query(None, description="Filtra per repertorio (__ALL__ per archivio intero)"),
    search: Optional[str] = Query(None, description="Filtra per testo nel titolo o autore")
):
    """Lists songs filtered by repertoire and optional text search."""
    all_songs = sorted(storage.list_songs(), key=lambda s: s["title"].lower())

    if repertoire_uuid and repertoire_uuid != "__ALL__":
        rep = storage.get_repertoire(repertoire_uuid)
        if rep:
            allowed_uids = set(rep.song_uuids)
            all_songs = [s for s in all_songs if s["uuid"] in allowed_uids]
        else:
            all_songs = []

    if search and search.strip():
        kw = search.strip().lower()
        all_songs = [
            s for s in all_songs
            if (kw in s["title"].lower() or kw in s.get("artist", "").lower() or kw in s.get("author", "").lower())
        ]

    # Include repertoire names for each song
    all_reps = storage.list_repertoires()
    for s in all_songs:
        s_reps = [r.name for r in all_reps if s["uuid"] in r.song_uuids]
        s["assigned_repertoires"] = s_reps

    return all_songs

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
    saved = storage.save_song(song, req.user_email, req.user_name, req.comment or "Creazione brano")
    if req.repertoire_uuid:
        storage.move_song_to_repertoire(saved.uuid, req.repertoire_uuid, req.user_email, req.user_name)
    return {"status": "success", "song": saved.to_dict()}

@app.put("/api/songs/{uuid}")
def update_song(uuid: str, req: SongUpdateRequest):
    """Updates song attributes and AML body, creating a new revision snapshot."""
    song = storage.get_song(uuid)
    if not song:
        raise HTTPException(status_code=404, detail="Brano non trovato")

    if req.title is not None:
        song.title = req.title.strip().upper()
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
    """Soft deletes song into trash."""
    success = storage.delete_song(uuid, user_email, user_name)
    if not success:
        raise HTTPException(status_code=404, detail="Brano non trovato")
    return {"status": "success", "deleted_uuid": uuid}

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
    email: Optional[str] = Query(None, description="Email musicista per caricare preferenze da Turso DB")
):
    """Generates and streams formatted device-aware PDF for display or download."""
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

    pdf_bytes = PDFEngine.generate_song_pdf(song, profile=prof, include_chords=chords, use_cache=True)
    filename = re.sub(r'[^a-zA-Z0-9_\-]', '_', song.title).strip('_') or "brano"
    mode_suffix = "accordi" if chords else "testo"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}_{mode_suffix}.pdf"'
        }
    )

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

@app.get("/api/setlists")
def list_setlists():
    """Lists all active setlists with item counts and total duration."""
    all_sets = storage.list_setlists()
    result = []
    for s in all_sets:
        result.append({
            "uuid": s.uuid,
            "title": s.title,
            "date": s.date,
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

    resolved_items = []
    total_duration = 0
    for idx, item in enumerate(s.items):
        song = storage.get_song(item.song_uuid)
        dur = song.duration_seconds if song else 0
        total_duration += dur
        resolved_items.append({
            "index": idx + 1,
            "song_uuid": item.song_uuid,
            "title": song.title if song else "Brano non trovato",
            "artist": song.artist if song else "",
            "key": item.custom_key or (song.key_current if song else "-"),
            "bpm": item.custom_bpm or (song.bpm if song else 120),
            "duration_seconds": dur,
            "is_medley": item.is_medley,
            "medley_group_id": item.medley_group_id,
            "notes": item.notes
        })

    return {
        "uuid": s.uuid,
        "title": s.title,
        "date": s.date,
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
    setlist = Setlist(
        uuid=req.uuid or "",
        title=req.title.strip(),
        date=req.date.strip() if req.date else "",
        description=req.description.strip() if req.description else "",
        items=items
    )
    saved = storage.save_setlist(setlist, req.user_email, req.user_name)
    return {"status": "success", "setlist": saved.to_dict()}

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
    email: Optional[str] = Query(None, description="Email musicista per caricare preferenze da Turso DB")
):
    """Generates consolidated setlist PDF (cover + index + songs) for tablet display or print."""
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

    pdf_bytes = PDFEngine.generate_setlist_pdf(s, resolved_songs, profile=prof, include_chords=chords)
    filename = re.sub(r'[^a-zA-Z0-9_\-]', '_', s.title).strip('_') or "scaletta"
    mode_suffix = "accordi" if chords else "testo"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}_{mode_suffix}.pdf"'
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
    app_mode = pref_mgr.get_user_preference(email, "app_mode", default="simplified")
    score_mode = pref_mgr.get_user_preference(email, "score_display_mode", default="chords")
    prefs["app_mode"] = app_mode
    prefs["score_display_mode"] = score_mode
    # Normalizza i campi colore per compatibilità incrociata Streamlit & PWA
    if "layout_color_text" in prefs and "color_lyrics" not in prefs:
        prefs["color_lyrics"] = prefs["layout_color_text"]
    if "layout_color_chords" in prefs and "color_chords" not in prefs:
        prefs["color_chords"] = prefs["layout_color_chords"]
    if "layout_color_aml" in prefs and "color_aml_markup" not in prefs:
        prefs["color_aml_markup"] = prefs["layout_color_aml"]
    return prefs

@app.post("/api/preferences/{email}")
def save_user_preferences(email: str, req: UserPreferencesRequest):
    """Persists user & device preferences to Turso Cloud DB."""
    prof = resolve_device_profile(req.device_name)
    dev_name = prof.name if prof else (req.device_name or "Huawei MediaPad M5")
    c_lyric = req.color_lyrics or "#111111"
    c_chord = req.color_chords or "#B71C1C"
    c_aml = req.color_aml_markup or "#4A148C"
    payload = {
        "app_mode": req.app_mode or "simplified",
        "score_display_mode": req.score_display_mode or "chords",
        "layout_font_size": req.layout_font_size or 12.0,
        "layout_font_size_chords": req.layout_font_size_chords or 13.0,
        "layout_columns": req.layout_columns or 1,
        "layout_margin_lateral": req.layout_margin_lateral if req.layout_margin_lateral is not None else 10.0,
        "color_lyrics": c_lyric,
        "layout_color_text": c_lyric,
        "color_chords": c_chord,
        "layout_color_chords": c_chord,
        "color_aml_markup": c_aml,
        "layout_color_aml": c_aml
    }
    pref_mgr.set_user_preference(email, "app_mode", payload["app_mode"])
    pref_mgr.set_user_preference(email, "score_display_mode", payload["score_display_mode"])
    pref_mgr.save_preferences(email, dev_name, payload)
    return {"status": "success", "saved": payload}


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

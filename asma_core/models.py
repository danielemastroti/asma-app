"""
ASMA Accordi Next Generation - Core Domain Models
Entities, Schemas, and Serializers conforming to SRS v1.0
"""

from __future__ import annotations
import dataclasses
from dataclasses import dataclass, field
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


def current_iso_timestamp() -> str:
    """Returns current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def generate_uuid() -> str:
    """Generates a UUIDv4 string."""
    return str(uuid.uuid4())


@dataclass
class LockStatus:
    is_locked: bool = False
    locked_by_email: Optional[str] = None
    locked_by_name: Optional[str] = None
    locked_at: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LockStatus:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Song:
    uuid: str = field(default_factory=generate_uuid)
    title: str = ""
    artist: str = ""
    author: str = ""
    genre: str = ""
    year: Optional[int] = None
    duration_seconds: int = 0
    bpm: int = 120
    time_signature: str = "4/4"
    capo: int = 0
    key_original: str = "C"
    key_current: str = "C"
    notation_system: str = "INT"  # "INT" or "ITA"
    tags: List[str] = field(default_factory=list)
    shared_notes: str = ""
    aml_content: str = ""
    lock_status: LockStatus = field(default_factory=LockStatus)
    current_revision: int = 1
    created_at: str = field(default_factory=current_iso_timestamp)
    updated_at: str = field(default_factory=current_iso_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        d = dataclasses.asdict(self)
        d["lock_status"] = self.lock_status.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Song:
        c = dict(data)
        if "lock_status" in c and isinstance(c["lock_status"], dict):
            c["lock_status"] = LockStatus.from_dict(c["lock_status"])
        elif "lock_status" not in c:
            c["lock_status"] = LockStatus()
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in c.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class Revision:
    song_uuid: str
    revision_number: int
    author_email: str
    author_name: str
    comment: str
    aml_snapshot: str
    timestamp: str = field(default_factory=current_iso_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Revision:
        valid_keys = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_keys})


@dataclass
class Repertoire:
    uuid: str = field(default_factory=generate_uuid)
    name: str = ""
    description: str = ""
    song_uuids: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=current_iso_timestamp)
    updated_at: str = field(default_factory=current_iso_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Repertoire:
        valid_keys = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_keys})


@dataclass
class SetlistItem:
    song_uuid: str
    is_medley: bool = False
    medley_group_id: Optional[str] = None
    custom_key: Optional[str] = None
    custom_bpm: Optional[int] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SetlistItem:
        valid_keys = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_keys})


@dataclass
class Setlist:
    uuid: str = field(default_factory=generate_uuid)
    title: str = ""
    date: str = ""
    description: str = ""
    items: List[SetlistItem] = field(default_factory=list)
    created_at: str = field(default_factory=current_iso_timestamp)
    updated_at: str = field(default_factory=current_iso_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        d = dataclasses.asdict(self)
        d["items"] = [item.to_dict() for item in self.items]
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Setlist:
        c = dict(data)
        if "items" in c and isinstance(c["items"], list):
            c["items"] = [
                SetlistItem.from_dict(item) if isinstance(item, dict) else item
                for item in c["items"]
            ]
        valid_keys = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in c.items() if k in valid_keys})


@dataclass
class LiveEvent:
    uuid: str = field(default_factory=generate_uuid)
    name: str = ""
    venue: str = ""
    event_date: str = ""
    setlist_uuid: Optional[str] = None
    logistics_notes: str = ""
    created_at: str = field(default_factory=current_iso_timestamp)
    updated_at: str = field(default_factory=current_iso_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LiveEvent:
        valid_keys = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_keys})


@dataclass
class DeviceProfile:
    uuid: str = field(default_factory=generate_uuid)
    name: str = "Standard Profile"
    target_device: str = "pc_a4"  # smartphone, tablet, ipad, pc_a4
    device_type: str = "printable_a4"  # smartphone, tablet, printable_a4
    width_mm: float = 210.0
    height_mm: float = 297.0
    font_lyrics: str = "Helvetica"
    font_chords: str = "Helvetica-Bold"
    font_size_lyrics: float = 12.0
    font_size_chords: float = 13.0
    margin_top_mm: float = 10.0
    margin_bottom_mm: float = 10.0
    margin_left_mm: float = 10.0
    margin_right_mm: float = 10.0
    zoom: float = 1.0
    orientation: str = "portrait"  # portrait, landscape
    columns: int = 1
    is_custom: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DeviceProfile:
        valid_keys = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_keys})


@dataclass
class User:
    email: str
    name: str
    role: str = "MUSICIAN"  # ADMIN, EDITOR, MUSICIAN
    is_active: bool = True
    created_at: str = field(default_factory=current_iso_timestamp)
    last_login: Optional[str] = None
    last_device: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> User:
        valid_keys = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_keys})


@dataclass
class AuditEntry:
    uuid: str = field(default_factory=generate_uuid)
    timestamp: str = field(default_factory=current_iso_timestamp)
    action: str = ""  # LOGIN, LOGOUT, CREATE, UPDATE, DELETE, RESTORE, BACKUP, LOCK_ACQUIRE, LOCK_RELEASE
    entity_type: str = ""  # SONG, REPERTOIRE, SETLIST, EVENT, USER, SYSTEM
    entity_id: str = ""
    user_email: str = ""
    user_name: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AuditEntry:
        valid_keys = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_keys})

"""
ASMA Accordi Next Generation - Core Package
"""

from asma_core.models import (
    Song, Repertoire, Setlist, SetlistItem, LiveEvent,
    DeviceProfile, Revision, LockStatus, User, AuditEntry
)
from asma_core.music_engine import MusicEngine, ParsedChord
from asma_core.aml_parser import (
    AMLParser, AMLDocument, ASTNode, DirectiveNode, SectionNode,
    CustomTagNode, ChordLyricLineNode, ChordGridLineNode, ChordToken, LyricSegment
)
from asma_core.lock_manager import LockManager
from asma_core.audit_logger import AuditLogger

try:
    from asma_core.storage_manager import StorageManager
except ImportError:
    StorageManager = None

try:
    from asma_core.pdf_engine import PDFEngine
except ImportError:
    PDFEngine = None

try:
    from asma_core.live_stage_component import LiveStageComponent
except ImportError:
    LiveStageComponent = None

try:
    from asma_core.export_engine import ExportEngine
except ImportError:
    ExportEngine = None

try:
    from asma_core.import_engine import ImportEngine
except ImportError:
    ImportEngine = None

try:
    from asma_core.printer_engine import PrinterEngine
except ImportError:
    PrinterEngine = None

__all__ = [
    "Song", "Repertoire", "Setlist", "SetlistItem", "LiveEvent",
    "DeviceProfile", "Revision", "LockStatus", "User", "AuditEntry",
    "MusicEngine", "ParsedChord", "AMLParser", "AMLDocument",
    "ASTNode", "DirectiveNode", "SectionNode", "CustomTagNode",
    "ChordLyricLineNode", "ChordGridLineNode", "ChordToken", "LyricSegment",
    "LockManager", "AuditLogger", "StorageManager",
    "PDFEngine", "LiveStageComponent", "ExportEngine", "ImportEngine",
    "PrinterEngine"
]

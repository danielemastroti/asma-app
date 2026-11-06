"""
ASMA Accordi Next Generation - AML Syntax & Tag Manager
Manages AML (ASMA Markup Language) directives, section headers, instrumental tags and syntax elements.
Conforms to SRS Cap. 4, Cap. 10.14 and User AML Configuration Requirements.
"""

from __future__ import annotations
import os
import json
import threading
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, asdict
from asma_core.audit_logger import AuditLogger


@dataclass
class AMLTagDefinition:
    tag: str
    category: str  # "directive", "section", "instrumental_tag", "structural_syntax"
    display_name: str
    syntax_pattern: str
    example: str
    description: str
    is_removable: bool = True
    is_builtin: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AMLTagDefinition:
        valid_keys = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_keys})


DEFAULT_AML_TAGS = [
    # -------------------------------------------------------------
    # 1. DIRETTIVE GENERALI {tag: valore}
    # -------------------------------------------------------------
    {
        "tag": "title",
        "category": "directive",
        "display_name": "Titolo Brano",
        "syntax_pattern": "{title: Titolo}",
        "example": "{title: Lo Spettacolo}",
        "description": "Definisce il titolo del brano per il catalogo, l'indice e l'intestazione PDF.",
        "is_removable": False,
        "is_builtin": True
    },
    {
        "tag": "artist",
        "category": "directive",
        "display_name": "Artista / Band",
        "syntax_pattern": "{artist: Artista}",
        "example": "{artist: Litfiba}",
        "description": "Definisce l'interprete, gruppo o compositore originale del brano.",
        "is_removable": False,
        "is_builtin": True
    },
    {
        "tag": "key",
        "category": "directive",
        "display_name": "Tonalità",
        "syntax_pattern": "{key: Tonalità}",
        "example": "{key: MIm}",
        "description": "Tonalità di riferimento (Italiana o Internazionale) per le trasposizioni automatiche.",
        "is_removable": False,
        "is_builtin": True
    },
    {
        "tag": "tempo",
        "category": "directive",
        "display_name": "Velocità BPM",
        "syntax_pattern": "{tempo: BPM}",
        "example": "{tempo: 128}",
        "description": "Velocità metronomica in battiti per minuto (BPM).",
        "is_removable": True,
        "is_builtin": True
    },
    {
        "tag": "time",
        "category": "directive",
        "display_name": "Metro / Tempo",
        "syntax_pattern": "{time: 4/4}",
        "example": "{time: 4/4}",
        "description": "Suddivisione metrica della battuta (es. 4/4, 3/4, 6/8, 12/8).",
        "is_removable": True,
        "is_builtin": True
    },
    {
        "tag": "capo",
        "category": "directive",
        "display_name": "Capotasto",
        "syntax_pattern": "{capo: Tasto}",
        "example": "{capo: 2}",
        "description": "Posizione del capotasto mobile sulla chitarra (tasto numerico).",
        "is_removable": True,
        "is_builtin": True
    },
    {
        "tag": "duration",
        "category": "directive",
        "display_name": "Durata",
        "syntax_pattern": "{duration: mm:ss}",
        "example": "{duration: 4:15}",
        "description": "Durata complessiva del brano per il calcolo dei tempi della scaletta live.",
        "is_removable": True,
        "is_builtin": True
    },
    {
        "tag": "source",
        "category": "directive",
        "display_name": "Fonte / URL",
        "syntax_pattern": "{source: URL o Archivio}",
        "example": "{source: https://www.accordiespartiti.it/...}",
        "description": "Origine o link dello spartito web importato.",
        "is_removable": True,
        "is_builtin": True
    },

    # -------------------------------------------------------------
    # 2. SEZIONI MUSICALI {sezione} o {sezione: etichetta}
    # -------------------------------------------------------------
    {
        "tag": "intro",
        "category": "section",
        "display_name": "Introduzione",
        "syntax_pattern": "{intro}",
        "example": "{intro: Chitarre e Batteria}",
        "description": "Sezione introduttiva iniziale del brano.",
        "is_removable": True,
        "is_builtin": True
    },
    {
        "tag": "verse",
        "category": "section",
        "display_name": "Strofa / Verse",
        "syntax_pattern": "{verse}",
        "example": "{verse: Strofa 1}",
        "description": "Strofa cantata con progressione armonica e testo.",
        "is_removable": True,
        "is_builtin": True
    },
    {
        "tag": "chorus",
        "category": "section",
        "display_name": "Ritornello / Chorus",
        "syntax_pattern": "{chorus}",
        "example": "{chorus}",
        "description": "Ritornello principale della canzone (hook melodico).",
        "is_removable": True,
        "is_builtin": True
    },
    {
        "tag": "bridge",
        "category": "section",
        "display_name": "Ponte / Bridge",
        "syntax_pattern": "{bridge}",
        "example": "{bridge: Variazione Armonica}",
        "description": "Sezione di passaggio o ponte armonico tra strofa e ritornello.",
        "is_removable": True,
        "is_builtin": True
    },
    {
        "tag": "solo",
        "category": "section",
        "display_name": "Assolo / Solo",
        "syntax_pattern": "{solo}",
        "example": "{solo: Chitarra solista}",
        "description": "Sezione dedicata all'assolo di chitarra, sax, tastiera o altro strumento.",
        "is_removable": True,
        "is_builtin": True
    },
    {
        "tag": "outro",
        "category": "section",
        "display_name": "Conclusione / Outro",
        "syntax_pattern": "{outro}",
        "example": "{outro: Sfumando}",
        "description": "Parte finale o dissolvenza del brano.",
        "is_removable": True,
        "is_builtin": True
    },
    {
        "tag": "pre-chorus",
        "category": "section",
        "display_name": "Pre-Ritornello",
        "syntax_pattern": "{pre-chorus}",
        "example": "{pre-chorus}",
        "description": "Sezione propulsiva che precede immediatamente il ritornello.",
        "is_removable": True,
        "is_builtin": True
    },
    {
        "tag": "coda",
        "category": "section",
        "display_name": "Coda",
        "syntax_pattern": "{coda}",
        "example": "{coda: Ripetere ad libitum}",
        "description": "Coda di chiusura formale o loop finale.",
        "is_removable": True,
        "is_builtin": True
    },
    {
        "tag": "interlude",
        "category": "section",
        "display_name": "Interludio",
        "syntax_pattern": "{interlude}",
        "example": "{interlude: Ripresa tema}",
        "description": "Intermezzo musicale tra due sezioni del brano.",
        "is_removable": True,
        "is_builtin": True
    },

    # -------------------------------------------------------------
    # 3. TAG STRUMENTALI & PERFORMANCE {strumento: istruzioni}
    # -------------------------------------------------------------
    {
        "tag": "guitar",
        "category": "instrumental_tag",
        "display_name": "Chitarra",
        "syntax_pattern": "{guitar: Istruzioni}",
        "example": "{guitar: Solo Don Felder}",
        "description": "Indicazioni specifiche di arpeggio, pedali, assolo o suoni per i chitarristi.",
        "is_removable": True,
        "is_builtin": True
    },
    {
        "tag": "voice",
        "category": "instrumental_tag",
        "display_name": "Voce & Cori",
        "syntax_pattern": "{voice: Istruzioni}",
        "example": "{voice: Armonizzazione a 3}",
        "description": "Indicazioni vocali per cantante solista, doppie voci o cori.",
        "is_removable": True,
        "is_builtin": True
    },
    {
        "tag": "bass",
        "category": "instrumental_tag",
        "display_name": "Basso",
        "syntax_pattern": "{bass: Istruzioni}",
        "example": "{bass: Slap groove}",
        "description": "Indicazioni ritmiche, slap o riff per il bassista.",
        "is_removable": True,
        "is_builtin": True
    },
    {
        "tag": "drums",
        "category": "instrumental_tag",
        "display_name": "Batteria",
        "syntax_pattern": "{drums: Istruzioni}",
        "example": "{drums: 4/4 con hi-hat aperto}",
        "description": "Indicazioni per il batterista (groove, pause, accenti, piatto ride).",
        "is_removable": True,
        "is_builtin": True
    },
    {
        "tag": "keys",
        "category": "instrumental_tag",
        "display_name": "Tastiere / Piano",
        "syntax_pattern": "{keys: Istruzioni}",
        "example": "{keys: Synth Pad caldo}",
        "description": "Preset, pad o parti di pianoforte e sintetizzatore.",
        "is_removable": True,
        "is_builtin": True
    },
    {
        "tag": "note",
        "category": "instrumental_tag",
        "display_name": "Nota di Regia",
        "syntax_pattern": "{note: Testo}",
        "example": "{note: Rallentare sul finale}",
        "description": "Annotazione generale per l'intera band o la regia audio/luci.",
        "is_removable": True,
        "is_builtin": True
    },

    # -------------------------------------------------------------
    # 4. SINTASSI STRUTTURALE SPECIALE (Inline Chords & Griglia)
    # -------------------------------------------------------------
    {
        "tag": "inline_chord",
        "category": "structural_syntax",
        "display_name": "Accordi Inline",
        "syntax_pattern": "[Accordo]",
        "example": "[Am]On a dark desert highway, [F#7]cool wind in my hair",
        "description": "Accordo racchiuso tra parentesi quadre, posizionato immediatamente prima della sillaba esatta.",
        "is_removable": False,
        "is_builtin": True
    },
    {
        "tag": "harmonic_grid",
        "category": "structural_syntax",
        "display_name": "Griglia Armonica a Battute",
        "syntax_pattern": "| Accordo | Accordo |",
        "example": "| DO | LAm | FA | SOL |",
        "description": "Rappresentazione di battute e misure strumentali delimitate da barre verticali (pipe).",
        "is_removable": False,
        "is_builtin": True
    }
]


class AMLTagManager:
    """Thread-safe persistent manager for AML markup tags and language grammar."""
    _instance: Optional[AMLTagManager] = None
    _singleton_lock = threading.Lock()

    def __new__(cls, data_file: Optional[str] = None) -> AMLTagManager:
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_manager(data_file)
            return cls._instance

    def _init_manager(self, data_file: Optional[str] = None) -> None:
        self._mutex = threading.Lock()
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self._file_path = data_file or os.path.join(base_dir, "data", "aml_syntax_tags.json")
        self._tags: Dict[str, AMLTagDefinition] = {}
        self._audit = AuditLogger()
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._file_path):
            try:
                with open(self._file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._tags = {item["tag"].lower(): AMLTagDefinition.from_dict(item) for item in data}
            except Exception:
                self._initialize_defaults()
        else:
            self._initialize_defaults()

    def _initialize_defaults(self) -> None:
        self._tags = {}
        for d in DEFAULT_AML_TAGS:
            obj = AMLTagDefinition.from_dict(d)
            self._tags[obj.tag.lower()] = obj
        self._save_to_disk()

    def _save_to_disk(self) -> None:
        os.makedirs(os.path.dirname(self._file_path), exist_ok=True)
        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump([t.to_dict() for t in self._tags.values()], f, indent=2, ensure_ascii=False)

    def list_tags(self, category: Optional[str] = None) -> List[AMLTagDefinition]:
        """Returns all configured AML tags, optionally filtered by category."""
        with self._mutex:
            all_list = list(self._tags.values())
            if category and category.lower() != "tutte":
                return [t for t in all_list if t.category.lower() == category.lower()]
            return all_list

    def get_tag(self, tag_name: str) -> Optional[AMLTagDefinition]:
        """Retrieves an AML tag by name."""
        with self._mutex:
            return self._tags.get(tag_name.strip().lower())

    def add_tag(
        self,
        tag_def: AMLTagDefinition,
        user_email: str = "system",
        user_name: str = "System"
    ) -> AMLTagDefinition:
        """Adds a new AML directive, section or instrumental tag."""
        clean_tag = tag_def.tag.strip().lower()
        if not clean_tag:
            raise ValueError("Il nome del tag non può essere vuoto.")

        with self._mutex:
            if clean_tag in self._tags:
                raise ValueError(f"Un tag AML denominato '{clean_tag}' è già presente nel dizionario.")

            tag_def.tag = clean_tag
            tag_def.is_builtin = False
            tag_def.is_removable = True
            self._tags[clean_tag] = tag_def
            self._save_to_disk()

        self._audit.log(
            "ADD_AML_TAG",
            "AML_TAG",
            clean_tag,
            user_email,
            user_name,
            {"tag": clean_tag, "category": tag_def.category, "display_name": tag_def.display_name}
        )
        return tag_def

    def update_tag(
        self,
        tag_name: str,
        display_name: str,
        syntax_pattern: str,
        example: str,
        description: str,
        user_email: str = "system",
        user_name: str = "System"
    ) -> AMLTagDefinition:
        """Modifies an existing AML tag's metadata and examples."""
        clean_tag = tag_name.strip().lower()
        with self._mutex:
            if clean_tag not in self._tags:
                raise ValueError(f"Tag AML '{clean_tag}' non trovato.")

            target = self._tags[clean_tag]
            target.display_name = display_name.strip()
            target.syntax_pattern = syntax_pattern.strip()
            target.example = example.strip()
            target.description = description.strip()
            self._save_to_disk()

        self._audit.log(
            "UPDATE_AML_TAG",
            "AML_TAG",
            clean_tag,
            user_email,
            user_name,
            {"tag": clean_tag, "display_name": display_name}
        )
        return target

    def delete_tag(
        self,
        tag_name: str,
        user_email: str = "system",
        user_name: str = "System"
    ) -> bool:
        """Removes a tag definition from the AML dictionary."""
        clean_tag = tag_name.strip().lower()
        with self._mutex:
            if clean_tag not in self._tags:
                return False

            target = self._tags[clean_tag]
            if not target.is_removable:
                raise ValueError(f"Il tag '{clean_tag}' è fondamentale per la sintassi AML e non può essere rimosso.")

            del self._tags[clean_tag]
            self._save_to_disk()

        self._audit.log(
            "DELETE_AML_TAG",
            "AML_TAG",
            clean_tag,
            user_email,
            user_name,
            {"tag": clean_tag}
        )
        return True

    def reset_to_defaults(
        self,
        user_email: str = "system",
        user_name: str = "System"
    ) -> List[AMLTagDefinition]:
        """Restores the standard AML syntax and tag catalogue."""
        with self._mutex:
            self._initialize_defaults()
            all_copy = list(self._tags.values())

        self._audit.log("RESET_DEFAULT_AML_TAGS", "AML_TAG", "all", user_email, user_name, {"count": len(all_copy)})
        return all_copy

    def get_known_sections(self) -> Set[str]:
        """Returns the set of active section tags."""
        with self._mutex:
            return {t.tag for t in self._tags.values() if t.category == "section"}

    def get_known_custom_tags(self) -> Set[str]:
        """Returns the set of active instrumental/performance tags."""
        with self._mutex:
            return {t.tag for t in self._tags.values() if t.category == "instrumental_tag"}

    def get_known_directives(self) -> Set[str]:
        """Returns the set of active metadata directives."""
        with self._mutex:
            return {t.tag for t in self._tags.values() if t.category == "directive"}

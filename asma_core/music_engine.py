"""
ASMA Accordi Next Generation - Music Engine
Mathematical, Deterministic Pure-Python Music Theory Engine
Zero-AI Dependency. Conforms to SRS Cap. 8 and Blueprint Sec. 6.
"""

from __future__ import annotations
import re
from typing import Tuple, Optional, List, Dict, Union

# Pitch Class Mapping (0 = C / DO)
PITCH_CLASSES_INT_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
PITCH_CLASSES_INT_FLAT  = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

PITCH_CLASSES_ITA_SHARP = ["DO", "DO#", "RE", "RE#", "MI", "FA", "FA#", "SOL", "SOL#", "LA", "LA#", "SI"]
PITCH_CLASSES_ITA_FLAT  = ["DO", "REb", "RE", "MIb", "MI", "FA", "SOLb", "SOL", "LAb", "LA", "SIb", "SI"]

# Root note to Pitch Class index
ROOT_TO_PC: Dict[str, int] = {
    # International
    "C": 0, "B#": 0,
    "C#": 1, "DB": 1,
    "D": 2,
    "D#": 3, "EB": 3,
    "E": 4, "FB": 4,
    "F": 5, "E#": 5,
    "F#": 6, "GB": 6,
    "G": 7,
    "G#": 8, "AB": 8,
    "A": 9,
    "A#": 10, "BB": 10,
    "B": 11, "CB": 11,
    # Italian
    "DO": 0, "SI#": 0,
    "DO#": 1, "REB": 1,
    "RE": 2,
    "RE#": 3, "MIB": 3,
    "MI": 4, "FAB": 4,
    "FA": 5, "MI#": 5,
    "FA#": 6, "SOLB": 6,
    "SOL": 7,
    "SOL#": 8, "LAB": 8,
    "LA": 9,
    "LA#": 10, "SIB": 10,
    "SI": 11, "DOB": 11,
}

# Circle of fifths positions (0 = C, 1 = G, 2 = D, 3 = A, 4 = E, 5 = B, 6 = F#/Gb, 7 = Db/C#, 8 = Ab/G#, 9 = Eb/D#, 10 = Bb/A#, 11 = F)
CIRCLE_OF_FIFTHS: Dict[int, int] = {
    0: 0,   # C
    7: 1,   # G
    2: 2,   # D
    9: 3,   # A
    4: 4,   # E
    11: 5,  # B
    6: 6,   # F#
    1: 7,   # C# / Db
    8: 8,   # Ab
    3: 9,   # Eb
    10: 10, # Bb
    5: 11,  # F
}

# Keys preferring sharps vs flats in standard circle of fifths
SHARP_KEYS = {7, 2, 9, 4, 11, 6}  # G, D, A, E, B, F#
FLAT_KEYS  = {5, 10, 3, 8, 1}     # F, Bb, Eb, Ab, Db

# Root note extraction regex pattern (case-insensitive)
# Supports Italian (DO, RE, MI, FA, SOL, LA, SI) and International (C, D, E, F, G, A, B)
ROOT_REGEX = re.compile(
    r"^(SOL|DO|RE|MI|FA|LA|SI|[A-G])(#|b|bb|##)?",
    re.IGNORECASE
)

# Valid musical chord qualities, extensions, and alteration suffixes
VALID_CHORD_SUFFIX_REGEX = re.compile(
    r"^("
    r"|"  # empty string = standard major triad (e.g. C, DO, G#, F#)
    r"m|min|minor|-|"
    r"maj|major|M|\+|7\+|aug|"
    r"dim|dim7|°|o|"
    r"sus|sus2|sus4|"
    r"2|4|5|6|6/9|m6|"
    r"7|m7|maj7|M7|mM7|m\(maj7\)|-7|7-|\+7|7\+|"
    r"7/9\+|7/9-|7/9b|7/9#|7/9|7/4|7/5\+|7/5-|m7/9|7/13|7/11|"
    r"7b5|7#5|7b9|7#9|7#11|7b13|7sus4|7sus2|"
    r"m7b5|m7-5|ø|"
    r"9|m9|maj9|M9|add9|madd9|add2|9\+|9-|"
    r"11|m11|maj11|add11|"
    r"13|m13|maj13|add13|"
    r"alt|"
    r"b5|#5|b9|#9|#11|b13|"
    r"(\((b5|#5|b9|#9|#11|b13|add9|add2|add4|add11|add13|sus4|sus2|omit3|omit5|[2-9]|1[1-3])\))+"
    r")$",
    re.IGNORECASE
)

# Italian words that clash with notes when written in all-lowercase lyrics
ITALIAN_LOWERCASE_WORDS = {
    "da", "di", "ha", "ho", "ma", "se", "un", "il", "lo", "la",
    "i", "gli", "le", "ne", "ti", "ci", "vi", "che", "chi", "per",
    "con", "su", "tra", "fra", "non", "piu", "più", "del", "dei", "della",
    "delle", "nel", "nei", "nella", "nelle", "come", "dove", "quando", "fa",
    "me", "te", "si", "se", "va", "sa", "so"
}


class ParsedChord:
    """Represents a structured, parsed musical chord."""
    def __init__(
        self,
        raw_root: str,
        accidental: str,
        quality_and_extension: str,
        raw_bass: Optional[str] = None,
        bass_accidental: Optional[str] = None,
        is_italian: bool = False
    ):
        self.raw_root = raw_root.upper()
        self.accidental = accidental
        self.quality_and_extension = quality_and_extension
        self.raw_bass = raw_bass.upper() if raw_bass else None
        self.bass_accidental = bass_accidental or ""
        self.is_italian = is_italian

    @property
    def full_root(self) -> str:
        return f"{self.raw_root}{self.accidental}"

    @property
    def pitch_class(self) -> int:
        norm = self.full_root.upper()
        if norm in ROOT_TO_PC:
            return ROOT_TO_PC[norm]
        raise ValueError(f"Root note sconosciuta: '{self.full_root}'")

    @property
    def bass_pitch_class(self) -> Optional[int]:
        if not self.raw_bass:
            return None
        norm = f"{self.raw_bass}{self.bass_accidental}".upper()
        if norm in ROOT_TO_PC:
            return ROOT_TO_PC[norm]
        return None

    def __repr__(self) -> str:
        bass_part = f"/{self.raw_bass}{self.bass_accidental}" if self.raw_bass else ""
        return f"ParsedChord({self.full_root}{self.quality_and_extension}{bass_part}, ita={self.is_italian})"


class MusicEngine:
    """Core Mathematical Music Theory Engine."""

    @staticmethod
    def is_italian_note(note_str: str) -> bool:
        """Determines whether a note or chord begins with Italian solfège nomenclature."""
        upper = note_str.strip().upper()
        for prefix in ["SOL", "DO", "RE", "MI", "FA", "LA", "SI"]:
            if upper.startswith(prefix):
                return True
        return False

    @classmethod
    def parse_chord(cls, chord_str: str) -> Optional[ParsedChord]:
        """
        Parses a chord string into its constituent parts:
        root, accidental, quality/extension, and optional slash bass.
        Example: 'DO7+', 'F#m7b5', 'C/E', 'SOLm/SIb', 'LA-'
        """
        clean = chord_str.strip()
        if not clean or clean in ["/", "%", "|", "-", "--"]:
            return None

        # Exclude lowercase Italian words that collide with chord notes (e.g. "da", "fa", "la", "di", "ha", "si")
        if clean.islower() and clean in ITALIAN_LOWERCASE_WORDS:
            return None

        # Check for slash bass vs alteration:
        # A slash indicates bass ONLY if what follows the slash is a valid musical note (e.g. C/E, SIb/FA).
        # Otherwise, the slash is part of the extension/alteration (e.g. RE7/9+, C6/9, A7/4).
        main_part = clean
        bass_part = None
        if "/" in clean:
            r_parts = clean.rsplit("/", 1)
            candidate_bass = r_parts[1].strip()
            b_match = ROOT_REGEX.match(candidate_bass)
            if b_match and b_match.end() == len(candidate_bass):
                main_part = r_parts[0].strip()
                bass_part = candidate_bass

        # Match root note
        match = ROOT_REGEX.match(main_part)
        if not match:
            return None

        raw_root = match.group(1).upper()
        accidental = match.group(2) or ""
        remainder = main_part[match.end():]

        # Ensure chord suffix / extension is musically valid (prevents "da", "fare", "casa", "s'ha")
        if remainder and not VALID_CHORD_SUFFIX_REGEX.match(remainder):
            return None

        is_italian = raw_root in ["DO", "RE", "MI", "FA", "SOL", "LA", "SI"]

        # Parse bass if present
        raw_bass = None
        bass_accidental = ""
        if bass_part:
            bass_match = ROOT_REGEX.match(bass_part)
            if bass_match:
                raw_bass = bass_match.group(1).upper()
                bass_accidental = bass_match.group(2) or ""
            else:
                return None

        return ParsedChord(
            raw_root=raw_root,
            accidental=accidental,
            quality_and_extension=remainder,
            raw_bass=raw_bass,
            bass_accidental=bass_accidental,
            is_italian=is_italian
        )

    @classmethod
    def normalize_italian_qualities(cls, quality_ext: str) -> str:
        """
        Normalizes Italian informal shorthand qualities into international standard:
        LA- -> LAm
        DO7+ -> DOmaj7
        DO+ -> DOaug
        """
        q = quality_ext
        # Replace trailing or leading minus with 'm' (e.g. '-' -> 'm', '-7' -> 'm7')
        if q == "-":
            return "m"
        if q.startswith("-"):
            return "m" + q[1:]
        # Replace 7+ with maj7
        if "7+" in q:
            return q.replace("7+", "maj7")
        # Replace + with aug when isolated
        if q == "+":
            return "aug"
        return q

    @classmethod
    def convert_quality_to_italian(cls, quality_ext: str, prefer_traditional: bool = False) -> str:
        """Converts international qualities into Italian conventions if preferred."""
        if not prefer_traditional:
            return quality_ext
        q = quality_ext
        if q == "m":
            return "-"
        if q == "maj7":
            return "7+"
        if q == "aug":
            return "+"
        return q

    @classmethod
    def format_pitch_class(
        cls,
        pc: int,
        target_system: str = "INT",  # "INT" or "ITA"
        prefer_flats: Optional[bool] = None,
        key_context_pc: Optional[int] = None
    ) -> str:
        """
        Formats a Pitch Class integer [0-11] into a formatted note name.
        Uses circle-of-fifths key context and explicit flat/sharp overrides.
        """
        norm_pc = pc % 12
        use_flats = False

        if prefer_flats is not None:
            use_flats = prefer_flats
        elif key_context_pc is not None and key_context_pc in FLAT_KEYS:
            use_flats = True
        elif norm_pc in [10, 3, 8]:  # Bb, Eb, Ab are universally preferred as flats in common music
            use_flats = True

        if target_system.upper() == "ITA":
            return PITCH_CLASSES_ITA_FLAT[norm_pc] if use_flats else PITCH_CLASSES_ITA_SHARP[norm_pc]
        else:
            return PITCH_CLASSES_INT_FLAT[norm_pc] if use_flats else PITCH_CLASSES_INT_SHARP[norm_pc]

    @classmethod
    def transpose_chord(
        cls,
        chord_str: str,
        semitones: int,
        target_system: Optional[str] = None,  # "INT", "ITA" or None (preserve)
        prefer_flats: Optional[bool] = None,
        destination_key: Optional[str] = None
    ) -> str:
        """
        Transposes an individual chord by a given number of semitones [-12, +12].
        Correctly preserves qualities, extensions, and transposes slash bass.
        """
        parsed = cls.parse_chord(chord_str)
        if not parsed:
            return chord_str

        # Calculate new pitch class
        new_pc = (parsed.pitch_class + semitones) % 12

        # Determine target naming system (ITA or INT)
        if target_system is not None:
            out_system = target_system.upper()
        else:
            out_system = "ITA" if parsed.is_italian else "INT"

        # Determine destination key context PC if provided
        dest_key_pc = None
        if destination_key:
            dest_parsed = cls.parse_chord(destination_key)
            if dest_parsed:
                dest_key_pc = dest_parsed.pitch_class

        # Format new root
        new_root = cls.format_pitch_class(
            new_pc,
            target_system=out_system,
            prefer_flats=prefer_flats,
            key_context_pc=dest_key_pc
        )

        # Quality normalization
        norm_quality = cls.normalize_italian_qualities(parsed.quality_and_extension)

        # Transpose bass note if present
        new_bass_str = ""
        if parsed.bass_pitch_class is not None:
            new_bass_pc = (parsed.bass_pitch_class + semitones) % 12
            new_bass_note = cls.format_pitch_class(
                new_bass_pc,
                target_system=out_system,
                prefer_flats=prefer_flats,
                key_context_pc=dest_key_pc
            )
            new_bass_str = f"/{new_bass_note}"

        return f"{new_root}{norm_quality}{new_bass_str}"

    @classmethod
    def convert_notation(
        cls,
        chord_str: str,
        to_system: str  # "ITA" or "INT"
    ) -> str:
        """Converts chord notation system without changing pitch (0 semitones)."""
        return cls.transpose_chord(chord_str, semitones=0, target_system=to_system)

    @classmethod
    def calculate_semitone_delta(cls, from_key: str, to_key: str) -> int:
        """
        Calculates the minimum semitone difference between two keys:
        Returns value in range [-5, +6].
        """
        p_from = cls.parse_chord(from_key)
        p_to = cls.parse_chord(to_key)
        if not p_from or not p_to:
            raise ValueError(f"Tonalità invalida: '{from_key}' o '{to_key}'")

        diff = (p_to.pitch_class - p_from.pitch_class) % 12
        if diff > 6:
            diff -= 12
        return diff

    @classmethod
    def calculate_harmonic_compatibility(
        cls,
        key_a: str,
        bpm_a: int,
        key_b: str,
        bpm_b: int
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculates medley compatibility between two songs based on Circle of Fifths
        harmonic distance and tempo difference (Cap. 11.6).
        Returns a score from 0.0 (incompatible) to 1.0 (perfect fit).
        """
        p_a = cls.parse_chord(key_a)
        p_b = cls.parse_chord(key_b)
        if not p_a or not p_b:
            return 0.0, {"error": "Invalid keys"}

        # Circle of fifths distance
        pos_a = CIRCLE_OF_FIFTHS.get(p_a.pitch_class, 0)
        pos_b = CIRCLE_OF_FIFTHS.get(p_b.pitch_class, 0)
        fifths_dist = min(abs(pos_a - pos_b), 12 - abs(pos_a - pos_b))

        # Harmonic score: 1.0 for distance 0, 0.8 for dist 1 (subdominant/dominant/relative), decreases further
        harmonic_score = max(0.0, 1.0 - (fifths_dist * 0.2))

        # BPM difference percentage
        max_bpm = max(bpm_a, bpm_b, 1)
        bpm_diff_pct = (abs(bpm_a - bpm_b) / max_bpm) * 100.0
        rhythm_score = max(0.0, 1.0 - (bpm_diff_pct / 30.0))

        total_score = (harmonic_score * 0.6) + (rhythm_score * 0.4)

        return round(total_score, 2), {
            "fifths_distance": fifths_dist,
            "bpm_diff_percent": round(bpm_diff_pct, 1),
            "harmonic_score": round(harmonic_score, 2),
            "rhythm_score": round(rhythm_score, 2),
            "recommended_transition": (
                "Transizione diretta fluida" if fifths_dist <= 1 and bpm_diff_pct <= 10.0
                else "Consigliata modulazione o pausa ritmica"
            )
        }

    @classmethod
    def identify_progression(cls, chord_sequence: List[str]) -> Dict[str, Any]:
        """
        Identifies whether a sequence of chords represents a standard harmonic turnaround
        (e.g., I-V-vi-IV, I-vi-IV-V, ii-V-I).
        """
        parsed_list = [cls.parse_chord(c) for c in chord_sequence if cls.parse_chord(c)]
        if not parsed_list or len(parsed_list) < 2:
            return {"is_progression": False, "chords": chord_sequence}

        # Root pitch classes
        pcs = [p.pitch_class for p in parsed_list]
        base_pc = pcs[0]

        # Intervals relative to base
        intervals = [(pc - base_pc) % 12 for pc in pcs]

        known_patterns = {
            (0, 9, 5, 7): "Giro di DO classico (I - vi - IV - V)",
            (0, 7, 9, 5): "Pop Progression (I - V - vi - IV)",
            (0, 5, 7):    "Blues / Rock Cadence (I - IV - V)",
            (2, 7, 0):    "Jazz Turnaround (ii - V - I)",
            (9, 5, 0, 7): "Andalusia / Minor progression (vi - IV - I - V)"
        }

        pattern_tuple = tuple(intervals)
        description = known_patterns.get(pattern_tuple, "Progressione armonica personalizzata")

        return {
            "is_progression": True,
            "pattern_intervals": intervals,
            "description": description,
            "chords": [p.full_root + p.quality_and_extension for p in parsed_list]
        }

    @classmethod
    def detect_probable_key(cls, chords: List[str], current_hint: str = "") -> Dict[str, Any]:
        """
        Analisi armonica deterministica per identificare la tonalita piu probabile di un brano.
        Distingue accuratamente tra:
        - Tonalita Minore (es. MIm) e relativo Maggiore (es. SOL, dove MIm e il 6° grado).
        - Errori di notazione (es. 'MI' memorizzato al posto di 'MIm').
        Restituisce un dizionario con la tonalita primaria in formato italiano, il relativo e la relazione armonica.
        """
        parsed = [cls.parse_chord(c) for c in chords if cls.parse_chord(c)]
        if not parsed:
            fallback = current_hint or "DO"
            return {
                "probable_key": cls.convert_notation(fallback, "ITA"),
                "relative_key": "",
                "mode": "Maggiore",
                "relationship": "Nessun accordo valido analizzabile"
            }

        major_steps = [0, 2, 4, 5, 7, 9, 11]
        major_qualities = [False, True, True, False, False, True, True]
        minor_steps = [0, 2, 3, 5, 7, 8, 10]
        minor_qualities = [True, True, False, True, True, False, False]

        first_p = parsed[0]
        first_is_min = first_p.quality_and_extension.startswith("m") and not first_p.quality_and_extension.startswith("maj")
        last_p = parsed[-1]
        last_is_min = last_p.quality_and_extension.startswith("m") and not last_p.quality_and_extension.startswith("maj")

        hint_p = cls.parse_chord(current_hint) if current_hint else None

        scores: Dict[Tuple[int, bool], float] = {}

        for pc in range(12):
            for is_min in (False, True):
                steps = minor_steps if is_min else major_steps
                qualities = minor_qualities if is_min else major_qualities
                scale_pcs = set((pc + s) % 12 for s in steps)
                dominant_pc = (pc + 7) % 12

                score = 0.0
                tonic_count = 0

                for p in parsed:
                    p_pc = p.pitch_class
                    p_min = p.quality_and_extension.startswith("m") and not p.quality_and_extension.startswith("maj")

                    if p_pc in scale_pcs:
                        score += 2.0
                        deg_idx = steps.index((p_pc - pc) % 12)
                        if p_min == qualities[deg_idx]:
                            score += 1.0
                        # Dominante armonica per tonalita minore (es. SI/SI7 in MIm)
                        if is_min and p_pc == dominant_pc and not p_min:
                            score += 4.0
                    else:
                        score -= 2.5

                    if p_pc == pc and p_min == is_min:
                        tonic_count += 1
                        score += 2.5

                if tonic_count == 0:
                    score -= 10.0

                if first_p.pitch_class == pc and first_is_min == is_min:
                    score += 20.0
                if last_p.pitch_class == pc and last_is_min == is_min:
                    score += 10.0

                if hint_p:
                    if hint_p.pitch_class == pc:
                        score += 15.0
                        if is_min:
                            score += 5.0

                scores[(pc, is_min)] = score

        # Trova la migliore scala candidata
        best_candidate = max(scores.keys(), key=lambda k: scores[k])
        best_pc, best_is_min = best_candidate

        # Arbitraggio Tonalita Minore vs Relativo Maggiore (es. MIm vs SOL, dove MIm e il 6° grado)
        if not best_is_min:
            rel_minor_pc = (best_pc + 9) % 12
            minor_cand = (rel_minor_pc, True)
            if minor_cand in scores:
                if (first_p.pitch_class == rel_minor_pc and first_is_min) or                    (hint_p and hint_p.pitch_class == rel_minor_pc) or                    (scores[minor_cand] >= scores[best_candidate] * 0.85 and first_is_min):
                    best_candidate = minor_cand
                    best_pc, best_is_min = best_candidate

        # Calcola relativo (relazione I - vi)
        if best_is_min:
            rel_pc = (best_pc + 3) % 12
            rel_key = PITCH_CLASSES_ITA_SHARP[rel_pc]
            key_name = f"{PITCH_CLASSES_ITA_SHARP[best_pc]}m"
            mode = "Minore"
            note_rel = f"{key_name} è il 6° grado di {rel_key}"
        else:
            rel_pc = (best_pc + 9) % 12
            rel_key = f"{PITCH_CLASSES_ITA_SHARP[rel_pc]}m"
            key_name = PITCH_CLASSES_ITA_SHARP[best_pc]
            mode = "Maggiore"
            note_rel = f"Relativo minore (6° grado): {rel_key}"

        return {
            "probable_key": key_name,
            "relative_key": rel_key,
            "mode": mode,
            "score": scores[best_candidate],
            "relationship": note_rel
        }

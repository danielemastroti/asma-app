"""
ASMA Accordi Next Generation - AML Parser & AST Engine
Defines the official ASMA Markup Language (AML) AST, Tokenizer,
Serializer, Validator, and Importer from ChordPro / Traditional Chords-Over-Text.
Zero-AI Dependency. Conforms to SRS Cap. 5, 14 and Blueprint Sec. 5.
"""

from __future__ import annotations
import re
from typing import List, Dict, Any, Optional, Tuple, Union, Set
from asma_core.music_engine import MusicEngine, ParsedChord


# AST Node Base
class ASTNode:
    """Base class for all Abstract Syntax Tree nodes in an AML document."""
    def to_aml(self) -> str:
        raise NotImplementedError


class DirectiveNode(ASTNode):
    """Represents a header directive: {name: value}"""
    def __init__(self, name: str, value: str = ""):
        self.name = name.strip().lower()
        self.value = value.strip()

    def to_aml(self) -> str:
        if self.value:
            return f"{{{self.name}: {self.value}}}"
        return f"{{{self.name}}}"

    def __repr__(self) -> str:
        return f"DirectiveNode({self.name}={self.value})"


class MedleySongStartNode(DirectiveNode):
    """Represents the beginning of a song fragment in a Medley: {start_of_song: Title | Artist | Key}"""
    def __init__(self, title: str, artist: str = "", key: str = "", raw_value: str = ""):
        self.title = title.strip()
        self.artist = artist.strip()
        self.key = key.strip()
        parts = [p for p in [self.title, self.artist, self.key] if p]
        val = " | ".join(parts) if parts else (raw_value.strip() or self.title)
        super().__init__(name="start_of_song", value=val)

    def to_aml(self) -> str:
        parts = [self.title]
        if self.artist:
            parts.append(self.artist)
        if self.key:
            parts.append(self.key)
        val = " | ".join(parts)
        return f"{{start_of_song: {val}}}"

    def __repr__(self) -> str:
        return f"MedleySongStartNode(title='{self.title}', artist='{self.artist}', key='{self.key}')"


class MedleySongEndNode(DirectiveNode):
    """Represents the end of a song fragment in a Medley: {end_of_song}"""
    def __init__(self):
        super().__init__(name="end_of_song", value="")

    def to_aml(self) -> str:
        return "{end_of_song}"

    def __repr__(self) -> str:
        return "MedleySongEndNode()"


class SectionNode(ASTNode):
    """Represents a musical section header: {intro}, {verse}, {chorus}, {bridge}, {solo}, {outro}"""
    def __init__(self, section_name: str, label: Optional[str] = None):
        self.section_name = section_name.strip().lower()
        self.label = label.strip() if label else None

    def to_aml(self) -> str:
        if self.label:
            return f"{{{self.section_name}: {self.label}}}"
        return f"{{{self.section_name}}}"

    def __repr__(self) -> str:
        return f"SectionNode({self.section_name}, label={self.label})"


class CustomTagNode(ASTNode):
    """Represents a specialized instrumental or performance tag: {guitar: Solo}, {voice: Harmonies}"""
    def __init__(self, tag_type: str, content: str):
        self.tag_type = tag_type.strip().lower()
        self.content = content.strip()

    def to_aml(self) -> str:
        return f"{{{self.tag_type}: {self.content}}}"

    def __repr__(self) -> str:
        return f"CustomTagNode({self.tag_type}={self.content})"


class ChordToken:
    """Represents an inline chord token: [Am]"""
    def __init__(self, chord_text: str):
        self.chord_text = chord_text.strip()

    def __repr__(self) -> str:
        return f"ChordToken([{self.chord_text}])"


class LyricSegment:
    """Represents a slice of lyrics text associated with or following an inline chord."""
    def __init__(self, text: str, chord: Optional[ChordToken] = None):
        self.text = text
        self.chord = chord

    def __repr__(self) -> str:
        c_str = f"[{self.chord.chord_text}]" if self.chord else ""
        return f"LyricSegment({c_str}{self.text})"


class ChordLyricLineNode(ASTNode):
    """Represents a line containing lyrics interwoven with chords: [Am]On a dark desert..."""
    def __init__(self, segments: List[LyricSegment], inline_comment: Optional[str] = None, comment_on_chords: bool = False):
        self.segments = segments
        self.inline_comment = inline_comment
        self.comment_on_chords = comment_on_chords

    def to_aml(self) -> str:
        parts = []
        for seg in self.segments:
            if seg.chord:
                parts.append(f"[{seg.chord.chord_text}]")
            parts.append(seg.text)
        res = "".join(parts)
        if self.inline_comment:
            res = f"{res.rstrip()} {{c: {self.inline_comment}}}" if res.strip() else f"{{c: {self.inline_comment}}}"
        return res

    def __repr__(self) -> str:
        return f"ChordLyricLineNode({len(self.segments)} segments)"


class ChordGridLineNode(ASTNode):
    """Represents a measure grid line without lyrics: | Bm | F#7 | A | E |"""
    def __init__(self, measures: List[List[str]], inline_comment: Optional[str] = None):
        self.measures = measures  # List of measures, each measure is a list of chords or symbols
        self.inline_comment = inline_comment

    def to_aml(self) -> str:
        measure_strs = []
        for m in self.measures:
            measure_strs.append(" ".join(m))
        res = f"| {' | '.join(measure_strs)} |"
        if self.inline_comment:
            res = f"{res} {{c: {self.inline_comment}}}"
        return res

    def __repr__(self) -> str:
        return f"ChordGridLineNode({self.measures})"


class CommentNode(ASTNode):
    """Represents a line comment: # this is a comment"""
    def __init__(self, text: str):
        self.text = text

    def to_aml(self) -> str:
        return f"# {self.text}"

    def __repr__(self) -> str:
        return f"CommentNode({self.text})"


class EmptyLineNode(ASTNode):
    """Represents a blank line separator."""
    def to_aml(self) -> str:
        return ""

    def __repr__(self) -> str:
        return "EmptyLineNode()"


# Regular expressions for line parsing
DIRECTIVE_REGEX = re.compile(r"^\{([a-zA-Z0-9_-]+)(?:[:\s]\s*([^\}]+))?\}$")
INLINE_COMMENT_REGEX = re.compile(r"\{(?:c|comment|ci|cb)\s*:\s*([^\}]+)\}", re.IGNORECASE)
CHORD_TOKEN_REGEX = re.compile(r"\[([^\]]+)\]")
GRID_LINE_REGEX = re.compile(r"^\|(.+)\|$")

KNOWN_SECTIONS = {
    "intro", "verse", "chorus", "bridge", "solo", "outro",
    "coda", "interlude", "pre-chorus", "medley_start", "medley_transition",
    "strofa", "ritornello", "assolo", "finale", "end", "fine", "stacco", "ponte", "rit",
    "strumentale", "intermezzo"
}

KNOWN_CUSTOM_TAGS = {"note", "voice", "guitar", "drums", "bass", "keys", "chitarra", "voce", "batteria", "scena", "scene"}


def get_active_sections() -> Set[str]:
    try:
        from asma_core.aml_tag_manager import AMLTagManager
        return AMLTagManager().get_known_sections() | KNOWN_SECTIONS
    except Exception:
        return KNOWN_SECTIONS


def get_active_custom_tags() -> Set[str]:
    try:
        from asma_core.aml_tag_manager import AMLTagManager
        return AMLTagManager().get_known_custom_tags()
    except Exception:
        return KNOWN_CUSTOM_TAGS


class AMLDocument:
    """Represents a complete parsed AML document."""
    def __init__(self, nodes: Optional[List[ASTNode]] = None):
        self.nodes: List[ASTNode] = nodes or []

    @property
    def metadata(self) -> Dict[str, str]:
        """Extracts standard metadata directives from the document."""
        meta: Dict[str, str] = {}
        for node in self.nodes:
            if isinstance(node, DirectiveNode):
                meta[node.name] = node.value
        return meta

    @property
    def is_medley(self) -> bool:
        """Returns True if this document contains one or more medley song fragments."""
        return any(isinstance(node, MedleySongStartNode) for node in self.nodes)

    @property
    def medley_fragments(self) -> List[MedleySongStartNode]:
        """Returns all MedleySongStartNode fragments found in the document."""
        return [node for node in self.nodes if isinstance(node, MedleySongStartNode)]

    def get_directive(self, name: str, default: str = "") -> str:
        return self.metadata.get(name.lower(), default)

    def to_aml(self) -> str:
        """Serializes the entire AST back into a clean AML formatted string."""
        lines = [node.to_aml() for node in self.nodes]
        return "\n".join(lines)


class AMLParser:
    """Parser and AST manipulator for ASMA Markup Language."""

    @classmethod
    def parse_medley_start_value(cls, tag_value: str) -> tuple[str, str, str]:
        """Parses 'Title | Artist | Key' or 'Title - Artist' into (title, artist, key)."""
        raw = (tag_value or "").strip()
        if "|" in raw:
            parts = [p.strip() for p in raw.split("|")]
            title = parts[0] if len(parts) > 0 else ""
            artist = parts[1] if len(parts) > 1 else ""
            key = parts[2] if len(parts) > 2 else ""
            return title, artist, key
        elif " - " in raw:
            parts = [p.strip() for p in raw.split(" - ")]
            title = parts[0]
            artist = parts[1] if len(parts) > 1 else ""
            return title, artist, ""
        else:
            return raw, "", ""

    @classmethod
    def parse(cls, aml_text: str) -> AMLDocument:
        """Parses a full AML text string into an AMLDocument AST, supporting interleaved chords and traditional chord-over-lyric pairs."""
        lines = aml_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        nodes: List[ASTNode] = []

        def _is_raw_chord_line(l: str) -> bool:
            clean_l = l.strip()
            if not clean_l or clean_l.startswith("{") or clean_l.startswith("#") or clean_l.startswith("|"):
                return False
            if "[" in clean_l and "]" in clean_l:
                return False
            if re.search(r"\b\w+'\w+\b|[.,!?;:]", clean_l):
                return False
            tokens = clean_l.split()
            if not tokens:
                return False
            from asma_core.music_engine import ITALIAN_LOWERCASE_WORDS, MusicEngine
            if any(t.islower() and t in ITALIAN_LOWERCASE_WORDS for t in tokens):
                return False
            valid_chords = sum(1 for t in tokens if MusicEngine.parse_chord(t.strip("[](),|")))
            return valid_chords > 0 and (valid_chords / len(tokens)) >= 0.70

        idx = 0
        while idx < len(lines):
            raw_line = lines[idx]
            line = raw_line.strip()

            if not line:
                nodes.append(EmptyLineNode())
                idx += 1
                continue

            if line.startswith("#"):
                nodes.append(CommentNode(line.lstrip("#").strip()))
                idx += 1
                continue

            # Check for directive or section tag: {tag} or {tag: value}
            dir_match = DIRECTIVE_REGEX.match(line)
            if dir_match:
                tag_name = dir_match.group(1).strip().lower()
                tag_value = (dir_match.group(2) or "").strip()

                active_sections = get_active_sections()
                active_custom_tags = get_active_custom_tags()

                if tag_name in ["start_of_song", "sos", "start_of_medley", "start_of_medley_song", "soms"]:
                    t_title, t_artist, t_key = cls.parse_medley_start_value(tag_value)
                    nodes.append(MedleySongStartNode(t_title, t_artist, t_key, raw_value=tag_value))
                    idx += 1
                    continue
                elif tag_name in ["end_of_song", "eos", "end_of_medley", "end_of_medley_song", "eoms"]:
                    nodes.append(MedleySongEndNode())
                    idx += 1
                    continue
                elif tag_name in ["sov", "start_of_verse"]:
                    nodes.append(SectionNode("strofa", label=tag_value or None))
                    idx += 1
                    continue
                elif tag_name in ["soc", "start_of_chorus"]:
                    nodes.append(SectionNode("ritornello", label=tag_value or None))
                    idx += 1
                    continue
                elif tag_name in ["sob", "start_of_bridge"]:
                    nodes.append(SectionNode("bridge", label=tag_value or None))
                    idx += 1
                    continue
                elif tag_name in ["eov", "end_of_verse", "eoc", "end_of_chorus", "eob", "end_of_bridge", "doc"]:
                    idx += 1
                    continue
                elif tag_name in active_sections:
                    nodes.append(SectionNode(tag_name, label=tag_value or None))
                    idx += 1
                    continue
                elif tag_name in active_custom_tags:
                    nodes.append(CustomTagNode(tag_name, content=tag_value))
                    idx += 1
                    continue
                else:
                    nodes.append(DirectiveNode(tag_name, tag_value))
                    idx += 1
                    continue

            # Ignore AI autocompletion boundary markers in PDF and AST parsing
            if re.match(r"^\[/?AUTO-COMPLETATO(?:\s*.*)?\]$", line, re.IGNORECASE):
                idx += 1
                continue

            # Check for bracketed section header on its own line: [INTRO], [STROFA], [RIT], [RITORNELLO], [VERSE], [CHORUS], etc.
            bracket_sec_match = re.match(
                r"^\[(INTRO|STROFA|VERSE|RITORNELLO|RIT\.?|CHORUS|BRIDGE|PONTE|SOLO|ASSOLO|STACCO|OUTRO|FINALE|CODA|INTERLUDE|PRE-CHORUS|STRUMENTALE|INTERMEZZO|END|FINE)(?:\s*[:\-]?\s*(.*?))?\](?:\s*\(?[xX]?\d+[xX]?\)?)?$",
                line,
                re.IGNORECASE
            )
            if bracket_sec_match:
                sec_type = bracket_sec_match.group(1).strip().rstrip('.').lower()
                sec_label = bracket_sec_match.group(2).strip() if bracket_sec_match.group(2) else None
                if sec_type == "rit":
                    sec_type = "ritornello"
                nodes.append(SectionNode(sec_type, label=sec_label or None))
                idx += 1
                continue

            # Check for bare section header on its own line: STROFA:, INTRO:, RITORNELLO:, etc.
            bare_sec_match = re.match(
                r"^(INTRO|STROFA|VERSE|RITORNELLO|RIT\.?|CHORUS|BRIDGE|PONTE|SOLO|ASSOLO|STACCO|OUTRO|FINALE|CODA|INTERLUDE|PRE-CHORUS|STRUMENTALE|INTERMEZZO)\s*:(?:\s*(.*?))?$",
                line,
                re.IGNORECASE
            )
            if bare_sec_match:
                sec_type = bare_sec_match.group(1).strip().rstrip('.').lower()
                sec_label = bare_sec_match.group(2).strip() if bare_sec_match.group(2) else None
                if sec_type == "rit":
                    sec_type = "ritornello"
                nodes.append(SectionNode(sec_type, label=sec_label or None))
                idx += 1
                continue

            # Extract inline {c: ...} / {comment: ...} if present on a chord/grid/lyric line
            inline_comments = [m.strip() for m in INLINE_COMMENT_REGEX.findall(raw_line) if m.strip()]
            inline_comment = " ".join(inline_comments) if inline_comments else None
            if inline_comment:
                raw_line = INLINE_COMMENT_REGEX.sub("", raw_line).rstrip()
                line = raw_line.strip()

            # Check for chord grid line: | C | Am | F | G | or DO | LA | SOL | FA | RE
            if "|" in line and len(line) > 2 and not re.match(r"^[eEaAdDgGbB]\|", line):
                is_wrapped_grid = line.startswith("|") and line.endswith("|")
                grid_content = line.strip("|").strip()
                measure_chunks = grid_content.split("|")
                measures = []
                for chunk in measure_chunks:
                    tokens = [t.strip() for t in chunk.split() if t.strip()]
                    if tokens:
                        measures.append(tokens)
                if measures:
                    all_tokens = [t for m in measures for t in m if t not in ["/", "%", "-", "|", "NC", "N.C."]]
                    valid_chords = sum(1 for t in all_tokens if MusicEngine.parse_chord(t))
                    if all_tokens and (valid_chords / len(all_tokens)) >= 0.5:
                        nodes.append(ChordGridLineNode(measures, inline_comment=inline_comment))
                        idx += 1
                        continue
                    elif is_wrapped_grid:
                        cleaned_pipe_lyric = " ".join([t for m in measures for t in m])
                        nodes.append(ChordLyricLineNode([LyricSegment(cleaned_pipe_lyric, chord=None)], inline_comment=inline_comment))
                        idx += 1
                        continue

            # Check for chord/lyric line with [Chord]
            if "[" in raw_line and "]" in raw_line:
                segments = cls._parse_chord_lyric_line(raw_line)
                nodes.append(ChordLyricLineNode(segments, inline_comment=inline_comment))
                idx += 1
                continue

            # Check if line is traditional chord line positioned over a subsequent lyric line
            if _is_raw_chord_line(raw_line):
                # Check if next line is a lyric line without brackets
                if (idx + 1 < len(lines)) and lines[idx + 1].strip() and not _is_raw_chord_line(lines[idx + 1]):
                    next_line_clean = INLINE_COMMENT_REGEX.sub("", lines[idx + 1]).strip()
                    next_is_grid = ("|" in next_line_clean) and not re.match(r"^[eEaAdDgGbB]\|", next_line_clean) and any(
                        MusicEngine.parse_chord(t) for t in next_line_clean.replace("|", " ").split()
                    )
                    if next_line_clean and not next_line_clean.startswith(("{", "#", "|")) and ("[" not in next_line_clean) and not next_is_grid:
                        # Merge traditional chord line over lyric line!
                        next_raw = lines[idx + 1]
                        next_comments = [m.strip() for m in INLINE_COMMENT_REGEX.findall(next_raw) if m.strip()]
                        if next_comments:
                            next_raw = INLINE_COMMENT_REGEX.sub("", next_raw).rstrip()
                        merged = cls._merge_chords_into_lyrics(raw_line, next_raw)
                        segments = cls._parse_chord_lyric_line(merged)
                        if inline_comment:
                            nodes.append(ChordLyricLineNode(segments, inline_comment=inline_comment, comment_on_chords=True))
                        elif next_comments:
                            nodes.append(ChordLyricLineNode(segments, inline_comment=" ".join(next_comments), comment_on_chords=False))
                        else:
                            nodes.append(ChordLyricLineNode(segments))
                        idx += 2
                        continue

                # Isolated chord line without lyrics
                tokens = [t.strip("[](),|") for t in line.split() if t.strip("[](),|")]
                chord_segs = [LyricSegment("   ", chord=ChordToken(t)) for t in tokens]
                nodes.append(ChordLyricLineNode(chord_segs, inline_comment=inline_comment))
                idx += 1
                continue

            # Default plain lyric line without chords
            nodes.append(ChordLyricLineNode([LyricSegment(raw_line, chord=None)], inline_comment=inline_comment))
            idx += 1

        return AMLDocument(nodes)

    @classmethod
    def _parse_chord_lyric_line(cls, line: str) -> List[LyricSegment]:
        """Parses a line containing interleaved chords and lyrics into LyricSegment items."""
        segments: List[LyricSegment] = []
        pos = 0
        matches = list(CHORD_TOKEN_REGEX.finditer(line))

        if not matches:
            return [LyricSegment(line)]

        # If there is lyric text before the first chord
        if matches[0].start() > 0:
            initial_text = line[0:matches[0].start()]
            segments.append(LyricSegment(initial_text, chord=None))

        for i, match in enumerate(matches):
            chord_content = match.group(1).strip()
            chord_token = ChordToken(chord_content)

            # Determine where the lyrics for this chord end (at the next chord or end of line)
            lyric_start = match.end()
            lyric_end = matches[i + 1].start() if i + 1 < len(matches) else len(line)
            lyric_text = line[lyric_start:lyric_end]

            segments.append(LyricSegment(lyric_text, chord=chord_token))

        return segments

    @classmethod
    def transpose_document(
        cls,
        doc: AMLDocument,
        semitones: int,
        target_system: Optional[str] = None,  # "INT", "ITA" or None (preserve)
        prefer_flats: Optional[bool] = None,
        destination_key: Optional[str] = None
    ) -> AMLDocument:
        """
        Transposes all chords in an AMLDocument by the specified semitone delta.
        Updates key directive and all chord tokens.
        """
        new_nodes: List[ASTNode] = []

        for node in doc.nodes:
            if isinstance(node, MedleySongStartNode):
                old_key = node.key
                new_key = ""
                if old_key:
                    new_key = MusicEngine.transpose_chord(
                        old_key,
                        semitones=semitones,
                        target_system=target_system,
                        prefer_flats=prefer_flats,
                        destination_key=destination_key
                    )
                new_nodes.append(MedleySongStartNode(node.title, node.artist, new_key, raw_value=node.value))

            elif isinstance(node, MedleySongEndNode):
                new_nodes.append(MedleySongEndNode())

            elif isinstance(node, DirectiveNode) and node.name == "key":
                # Transpose the key directive
                old_key = node.value
                new_key = MusicEngine.transpose_chord(
                    old_key,
                    semitones=semitones,
                    target_system=target_system,
                    prefer_flats=prefer_flats,
                    destination_key=destination_key
                )
                new_nodes.append(DirectiveNode("key", new_key))

            elif isinstance(node, ChordLyricLineNode):
                # Transpose all inline chords
                new_segments = []
                for seg in node.segments:
                    if seg.chord:
                        transposed_chord = MusicEngine.transpose_chord(
                            seg.chord.chord_text,
                            semitones=semitones,
                            target_system=target_system,
                            prefer_flats=prefer_flats,
                            destination_key=destination_key
                        )
                        new_segments.append(LyricSegment(seg.text, chord=ChordToken(transposed_chord)))
                    else:
                        new_segments.append(seg)
                new_nodes.append(ChordLyricLineNode(new_segments, inline_comment=getattr(node, "inline_comment", None), comment_on_chords=getattr(node, "comment_on_chords", False)))

            elif isinstance(node, ChordGridLineNode):
                # Transpose all chords in the grid
                new_measures = []
                for measure in node.measures:
                    new_m = []
                    for token in measure:
                        if token in ["/", "%", "-"]:
                            new_m.append(token)
                        else:
                            transposed_chord = MusicEngine.transpose_chord(
                                token,
                                semitones=semitones,
                                target_system=target_system,
                                prefer_flats=prefer_flats,
                                destination_key=destination_key
                            )
                            new_m.append(transposed_chord)
                    new_measures.append(new_m)
                new_nodes.append(ChordGridLineNode(new_measures, inline_comment=getattr(node, "inline_comment", None)))

            else:
                new_nodes.append(node)

        return AMLDocument(new_nodes)

    @classmethod
    def transpose_preserving_format(
        cls,
        aml_text: str,
        semitones: int,
        target_system: Optional[str] = None,
        prefer_flats: bool = False,
        destination_key: Optional[str] = None
    ) -> str:
        """
        Transposes chords in an AML document while strictly preserving the user's
        original writing format (plain-text chords above lyrics, grids without outer pipes,
        inline {c: ...} comments, [Chord] brackets, whitespace, and directives).
        """
        if not aml_text or (semitones == 0 and target_system is None):
            return aml_text

        from asma_core.music_engine import ITALIAN_LOWERCASE_WORDS, MusicEngine

        def _is_raw_chord_line(l: str) -> bool:
            clean_l = l.strip()
            if not clean_l or clean_l.startswith(("{", "#", "|")):
                return False
            if "[" in clean_l and "]" in clean_l:
                return False
            if re.search(r"\b\w+'\w+\b|[.,!?;:]", clean_l):
                return False
            tokens = clean_l.split()
            if not tokens:
                return False
            if any(t.islower() and t in ITALIAN_LOWERCASE_WORDS for t in tokens):
                return False
            valid_chords = sum(1 for t in tokens if MusicEngine.parse_chord(t.strip("[](),|")))
            return valid_chords > 0 and (valid_chords / len(tokens)) >= 0.70

        def _tr(tok: str) -> str:
            return MusicEngine.transpose_chord(
                tok,
                semitones=semitones,
                target_system=target_system,
                prefer_flats=prefer_flats,
                destination_key=destination_key,
            )

        out_lines: List[str] = []
        for line_with_end in aml_text.splitlines(keepends=True):
            ending = ""
            if line_with_end.endswith("\r\n"):
                ending = "\r\n"
                raw = line_with_end[:-2]
            elif line_with_end.endswith(("\n", "\r")):
                ending = line_with_end[-1]
                raw = line_with_end[:-1]
            else:
                raw = line_with_end

            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                out_lines.append(line_with_end)
                continue

            # Standalone directive (transpose {key: ...} / {tonalita: ...} and medley {start_of_song: ... | ... | key})
            dir_match = DIRECTIVE_REGEX.match(stripped)
            if dir_match:
                tag_name = dir_match.group(1).strip().lower()
                tag_val = (dir_match.group(2) or "").strip()
                if tag_name in ("key", "tonalita") and tag_val:
                    new_key = _tr(tag_val)
                    raw = re.sub(
                        r"^(\s*\{(?:key|tonalita)\s*:\s*)([^\}]+)(\}\s*)$",
                        rf"\g<1>{new_key}\g<3>",
                        raw,
                        flags=re.IGNORECASE,
                    )
                elif tag_name in ("start_of_song", "sos", "start_of_medley", "start_of_medley_song", "soms") and tag_val:
                    t_title, t_artist, t_key = cls.parse_medley_start_value(tag_val)
                    if t_key:
                        new_key = _tr(t_key)
                        parts = [t_title]
                        if t_artist:
                            parts.append(t_artist)
                        parts.append(new_key)
                        new_val = " | ".join(parts)
                        raw = re.sub(
                            r"^(\s*\{(?:start_of_song|sos|start_of_medley|start_of_medley_song|soms)\s*:\s*)([^\}]+)(\}\s*)$",
                            rf"\g<1>{new_val}\g<3>",
                            raw,
                            flags=re.IGNORECASE,
                        )
                out_lines.append(raw + ending)
                continue

            # Separate inline {c: ...} comments so they are never altered
            comment_spans: List[tuple[int, int]] = [m.span() for m in INLINE_COMMENT_REGEX.finditer(raw)]
            if comment_spans:
                # Split around first inline comment (common case: trailing {c: brass})
                first_c_start = comment_spans[0][0]
                code_part = raw[:first_c_start]
                comment_suffix = raw[first_c_start:]
            else:
                code_part = raw
                comment_suffix = ""

            code_stripped = code_part.strip()

            # 1. Bracketed [Chord] tokens
            if "[" in code_part and "]" in code_part:
                def _repl_bracket(m: re.Match) -> str:
                    inner = m.group(1).strip()
                    if MusicEngine.parse_chord(inner):
                        return f"[{_tr(inner)}]"
                    return m.group(0)
                new_code = CHORD_TOKEN_REGEX.sub(_repl_bracket, code_part)
                out_lines.append(new_code + comment_suffix + ending)
                continue

            # 2. Chord grid line (with |)
            if "|" in code_stripped and len(code_stripped) > 2 and not re.match(r"^[eEaAdDgGbB]\|", code_stripped):
                grid_tokens = [
                    t for t in code_stripped.replace("|", " ").split()
                    if t not in ["/", "%", "-", "|", "NC", "N.C."]
                ]
                if grid_tokens and (sum(1 for t in grid_tokens if MusicEngine.parse_chord(t)) / len(grid_tokens)) >= 0.5:
                    new_code = re.sub(
                        r"\S+",
                        lambda m: _tr(m.group(0)) if MusicEngine.parse_chord(m.group(0)) else m.group(0),
                        code_part,
                    )
                    out_lines.append(new_code + comment_suffix + ending)
                    continue

            # 3. Plain-text chord line (without brackets or pipes)
            if _is_raw_chord_line(code_part):
                new_code = re.sub(
                    r"\S+",
                    lambda m: _tr(m.group(0)) if MusicEngine.parse_chord(m.group(0).strip("[](),|")) else m.group(0),
                    code_part,
                )
                out_lines.append(new_code + comment_suffix + ending)
                continue

            out_lines.append(line_with_end)

        return "".join(out_lines)

    @classmethod
    def convert_notation(
        cls,
        doc: AMLDocument,
        to_system: str  # "ITA" or "INT"
    ) -> AMLDocument:
        """Converts an entire document to either Italian or International chord notation."""
        return cls.transpose_document(doc, semitones=0, target_system=to_system)

    @classmethod
    def validate(cls, doc: AMLDocument) -> List[Dict[str, Any]]:
        """
        Validates an AML document AST and returns a list of warnings and errors.
        Does not raise exceptions.
        """
        issues: List[Dict[str, Any]] = []

        # Validate mandatory directives
        meta = doc.metadata
        if "title" not in meta or not meta["title"].strip():
            issues.append({"level": "WARNING", "message": "Direttiva {title: ...} mancante."})
        if "key" not in meta or not meta["key"].strip():
            issues.append({"level": "WARNING", "message": "Direttiva {key: ...} mancante."})
        elif not MusicEngine.parse_chord(meta["key"]):
            issues.append({"level": "ERROR", "message": f"Tonalità non valida: '{meta['key']}'."})

        # Validate all chords
        for line_idx, node in enumerate(doc.nodes, start=1):
            if isinstance(node, ChordLyricLineNode):
                for seg in node.segments:
                    if seg.chord:
                        parsed = MusicEngine.parse_chord(seg.chord.chord_text)
                        if not parsed:
                            issues.append({
                                "level": "WARNING",
                                "line": line_idx,
                                "message": f"Accordo non riconosciuto: '{seg.chord.chord_text}'"
                            })
            elif isinstance(node, ChordGridLineNode):
                for measure in node.measures:
                    for token in measure:
                        if token not in ["/", "%", "-"] and not MusicEngine.parse_chord(token):
                            issues.append({
                                "level": "WARNING",
                                "line": line_idx,
                                "message": f"Simbolo o accordo non valido nella griglia: '{token}'"
                            })

        return issues

    @classmethod
    def import_traditional_chords_over_text(cls, text: str) -> AMLDocument:
        """
        Imports traditional chords-above-lyrics text and converts it into standard AML.
        Identifies chord lines by analyzing token ratio of valid chords.
        """
        raw_lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        aml_lines: List[str] = []
        i = 0

        def is_chord_line(l: str) -> bool:
            clean_l = l.strip()
            if not clean_l or clean_l.startswith("{") or clean_l.startswith("#"):
                return False
            # If line contains contractions with apostrophe (e.g. "s'ha", "c'è", "l'ora") or sentence punctuation, it's lyrics
            if re.search(r"\b\w+'\w+\b|[.,!?;:]", clean_l):
                return False
            tokens = clean_l.split()
            if not tokens:
                return False
            # Check for non-chord Italian grammatical words that indicate a spoken/sung line
            non_chord_words = {"da", "ha", "ho", "non", "con", "per", "tra", "fra", "che", "chi", "s'ha", "del", "della", "dei"}
            if any(t.lower() in non_chord_words for t in tokens):
                return False
            valid_chords = sum(1 for t in tokens if MusicEngine.parse_chord(t.strip("[](),|")))
            return (valid_chords / len(tokens)) >= 0.75

        while i < len(raw_lines):
            curr_line = raw_lines[i]
            # Check if this line is a chord line and next line is lyrics (must not be empty)
            if is_chord_line(curr_line) and (i + 1 < len(raw_lines)) and raw_lines[i + 1].strip() and not is_chord_line(raw_lines[i + 1]):
                chord_line = curr_line
                lyric_line = raw_lines[i + 1]

                # Merge chords into lyrics using column indices
                merged_line = cls._merge_chords_into_lyrics(chord_line, lyric_line)
                aml_lines.append(merged_line)
                i += 2
            elif is_chord_line(curr_line):
                # Isolated chord line without lyrics -> convert to grid line
                chords = [t.strip("[](),|") for t in curr_line.strip().split() if t.strip("[](),|")]
                aml_lines.append(f"| {' | '.join(chords)} |")
                i += 1
            else:
                # Regular line or directive
                aml_lines.append(curr_line)
                i += 1

        return cls.parse("\n".join(aml_lines))

    @classmethod
    def _merge_chords_into_lyrics(cls, chord_line: str, lyric_line: str) -> str:
        """
        Merges a line of chords with a line of lyrics using column positions.
        Includes intelligent word-boundary snapping to avoid splitting syllables unnaturally.
        """
        # Find positions of all chord tokens
        tokens = []
        for match in re.finditer(r"\S+", chord_line):
            chord_str = match.group(0).strip("[](),|")
            if chord_str:
                tokens.append((match.start(), chord_str))

        # Find word boundaries in lyric_line
        words = []
        for match in re.finditer(r"\S+", lyric_line):
            words.append((match.start(), match.end()))

        # Determine effective insertion point for each chord
        adjusted_tokens = []
        for col, chord in tokens:
            target_col = col
            # If col falls inside a word or immediately adjacent, snap to word start if close
            for w_start, w_end in words:
                if w_start <= col < w_end:
                    # If within 3 chars of start of word, snap to start
                    if col - w_start <= 3:
                        target_col = w_start
                    break
                elif 0 <= w_start - col <= 2:
                    # If chord is 1-2 chars before word start, snap to word start
                    target_col = w_start
                    break
            adjusted_tokens.append((target_col, chord))

        # Insert chords from right to left into lyric_line to keep indices stable
        result = list(lyric_line)
        # Pad lyric line if necessary
        max_col = max([t[0] for t in adjusted_tokens], default=0)
        if max_col > len(result):
            result.extend([" "] * (max_col - len(result)))

        # Sort descending by column index
        for col, chord in sorted(adjusted_tokens, key=lambda x: x[0], reverse=True):
            insert_str = f"[{chord}]"
            clamped_col = min(col, len(result))
            result.insert(clamped_col, insert_str)

        return "".join(result).rstrip()

    @classmethod
    def split_medley_fragments(cls, aml_text: str) -> tuple[str, List[Dict[str, Any]]]:
        """
        Splits an AML text into header metadata and structured medley fragments.
        Identifies fragment titles, artists, keys, line counts, and whether a page break
        directive ({np}, {new_page}, etc.) precedes each fragment.
        """
        pattern = re.compile(
            r'(\n?[ \t]*\{(?:np|new_page|page_break|salto_pagina|salto_di_pagina)[^\}]*\}\s*)?'
            r'(\{(?:start_of_song|sos|start_of_medley|start_of_medley_song|soms)(?:[:\s]\s*([^\}]+))?\})',
            re.IGNORECASE
        )
        matches = list(pattern.finditer(aml_text))
        if not matches:
            return aml_text, []

        header = aml_text[:matches[0].start()].rstrip()
        fragments: List[Dict[str, Any]] = []

        for i, m in enumerate(matches):
            next_start = matches[i + 1].start() if i + 1 < len(matches) else len(aml_text)
            has_np = bool(m.group(1))
            tag_val = m.group(3) or ""
            title, artist, key = cls.parse_medley_start_value(tag_val)

            body_start = m.start() + (len(m.group(1)) if m.group(1) else 0)
            frag_raw = aml_text[body_start:next_start].rstrip()
            frag_clean = re.sub(
                r'\n?[ \t]*\{(?:np|new_page|page_break|salto_pagina|salto_di_pagina)[^\}]*\}\s*$',
                '',
                frag_raw,
                flags=re.IGNORECASE
            ).rstrip()

            lines = [l for l in frag_clean.splitlines() if l.strip()]
            fragments.append({
                "index": i + 1,
                "title": title or f"Spezzone {i + 1}",
                "artist": artist,
                "key": key,
                "has_page_break": has_np,
                "raw_content": frag_clean,
                "line_count": len(lines)
            })

        return header, fragments

    @classmethod
    def format_medley_pages(
        cls,
        aml_text: str,
        strategy: str = "smart_fit",
        target_device: Optional[str] = None,
        custom_breaks: Optional[List[int]] = None
    ) -> tuple[str, List[Dict[str, Any]]]:
        """
        Applies device-aware page formatting to a medley AML document.
        Strategies:
          - 'one_per_page': each fragment starts on a new page ({np} before fragments 2..N)
          - 'smart_fit': computes line capacity for target device and packs fragments onto pages
          - 'custom': explicitly sets {np} before fragments in custom_breaks
          - 'clear': removes all page breaks between fragments
        Returns (formatted_aml, fragments_meta).
        """
        header, fragments = cls.split_medley_fragments(aml_text)
        if not fragments:
            return aml_text, []

        dev_str = (target_device or "").lower()
        if any(s in dev_str for s in ["smartphone", "pixel", "iphone", "oppo"]):
            cap = 22
        elif any(s in dev_str for s in ["a4", "foglio"]):
            cap = 40
        else:
            # Tablet default (e.g. 2 columns, height ~250mm)
            cap = 52

        break_indices: Set[int] = set()

        if strategy == "one_per_page":
            for i in range(2, len(fragments) + 1):
                break_indices.add(i)
        elif strategy == "custom" and custom_breaks is not None:
            break_indices = {int(b) for b in custom_breaks if int(b) > 1}
        elif strategy == "smart_fit":
            cur_lines = 0
            for i, f in enumerate(fragments):
                idx = i + 1
                overhead = 3  # banner + spacing
                needed = f["line_count"] + overhead
                if i == 0:
                    cur_lines = needed
                else:
                    if cur_lines + needed > cap:
                        break_indices.add(idx)
                        cur_lines = needed
                    else:
                        cur_lines += needed
        elif strategy == "clear":
            break_indices = set()

        output_parts: List[str] = [header] if header else []
        cur_page = 1

        for i, f in enumerate(fragments):
            idx = i + 1
            if idx in break_indices and i > 0:
                cur_page += 1
                f["page"] = cur_page
                f["has_page_break"] = True
                output_parts.append("\n{np}\n" + f["raw_content"])
            else:
                f["page"] = cur_page
                f["has_page_break"] = False
                output_parts.append(("\n\n" if output_parts else "") + f["raw_content"])

        formatted_aml = "\n".join(output_parts).strip() + "\n"
        return formatted_aml, fragments

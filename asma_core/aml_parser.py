"""
ASMA Accordi Next Generation - AML Parser & AST Engine
Defines the official ASMA Markup Language (AML) AST, Tokenizer,
Serializer, Validator, and Importer from ChordPro / Traditional Chords-Over-Text.
Zero-AI Dependency. Conforms to SRS Cap. 5, 14 and Blueprint Sec. 5.
"""

from __future__ import annotations
import re
from typing import List, Dict, Any, Optional, Tuple, Union
from asma_core.music_engine import MusicEngine, ParsedChord


# AST Node Base
class ASTNode:
    """Base class for all Abstract Syntax Tree nodes in an AML document."""
    def to_aml(self) -> str:
        raise NotImplementedError


class DirectiveNode(ASTNode):
    """Represents a header directive: {name: value}"""
    def __init__(self, name: str, value: str):
        self.name = name.strip().lower()
        self.value = value.strip()

    def to_aml(self) -> str:
        return f"{{{self.name}: {self.value}}}"

    def __repr__(self) -> str:
        return f"DirectiveNode({self.name}={self.value})"


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
    def __init__(self, segments: List[LyricSegment]):
        self.segments = segments

    def to_aml(self) -> str:
        parts = []
        for seg in self.segments:
            if seg.chord:
                parts.append(f"[{seg.chord.chord_text}]")
            parts.append(seg.text)
        return "".join(parts)

    def __repr__(self) -> str:
        return f"ChordLyricLineNode({len(self.segments)} segments)"


class ChordGridLineNode(ASTNode):
    """Represents a measure grid line without lyrics: | Bm | F#7 | A | E |"""
    def __init__(self, measures: List[List[str]]):
        self.measures = measures  # List of measures, each measure is a list of chords or symbols

    def to_aml(self) -> str:
        measure_strs = []
        for m in self.measures:
            measure_strs.append(" ".join(m))
        return f"| {' | '.join(measure_strs)} |"

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
DIRECTIVE_REGEX = re.compile(r"^\{([a-zA-Z0-9_-]+)(?::\s*([^\}]+))?\}$")
CHORD_TOKEN_REGEX = re.compile(r"\[([^\]]+)\]")
GRID_LINE_REGEX = re.compile(r"^\|(.+)\|$")

KNOWN_SECTIONS = {
    "intro", "verse", "chorus", "bridge", "solo", "outro",
    "coda", "interlude", "pre-chorus", "medley_start", "medley_transition",
    "strofa", "ritornello", "assolo", "finale"
}

KNOWN_CUSTOM_TAGS = {"note", "voice", "guitar", "drums", "bass", "keys", "chitarra", "voce", "batteria"}


def get_active_sections() -> Set[str]:
    try:
        from asma_core.aml_tag_manager import AMLTagManager
        return AMLTagManager().get_known_sections()
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

    def get_directive(self, name: str, default: str = "") -> str:
        return self.metadata.get(name.lower(), default)

    def to_aml(self) -> str:
        """Serializes the entire AST back into a clean AML formatted string."""
        lines = [node.to_aml() for node in self.nodes]
        return "\n".join(lines)


class AMLParser:
    """Parser and AST manipulator for ASMA Markup Language."""

    @classmethod
    def parse(cls, aml_text: str) -> AMLDocument:
        """Parses a full AML text string into an AMLDocument AST."""
        lines = aml_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        nodes: List[ASTNode] = []

        for raw_line in lines:
            line = raw_line.strip()

            if not line:
                nodes.append(EmptyLineNode())
                continue

            if line.startswith("#"):
                nodes.append(CommentNode(line.lstrip("#").strip()))
                continue

            # Check for directive or section tag: {tag} or {tag: value}
            dir_match = DIRECTIVE_REGEX.match(line)
            if dir_match:
                tag_name = dir_match.group(1).strip().lower()
                tag_value = (dir_match.group(2) or "").strip()

                active_sections = get_active_sections()
                active_custom_tags = get_active_custom_tags()

                if tag_name in active_sections:
                    nodes.append(SectionNode(tag_name, label=tag_value or None))
                    continue
                elif tag_name in active_custom_tags:
                    nodes.append(CustomTagNode(tag_name, content=tag_value))
                    continue
                else:
                    nodes.append(DirectiveNode(tag_name, tag_value))
                    continue

            # Check for chord grid line: | C | Am | F | G |
            if line.startswith("|") and line.endswith("|") and len(line) > 2:
                grid_content = line[1:-1].strip()
                measure_chunks = grid_content.split("|")
                measures = []
                for chunk in measure_chunks:
                    tokens = [t.strip() for t in chunk.split() if t.strip()]
                    if tokens:
                        measures.append(tokens)
                if measures:
                    # Validate that the measures actually contain valid chords or standard chord symbols
                    all_tokens = [t for m in measures for t in m if t not in ["/", "%", "-", "|", "NC", "N.C."]]
                    valid_chords = sum(1 for t in all_tokens if MusicEngine.parse_chord(t))
                    if all_tokens and (valid_chords / len(all_tokens)) >= 0.5:
                        nodes.append(ChordGridLineNode(measures))
                        continue
                    else:
                        # Line has pipes but contains lyrics/words rather than chords (e.g. "| Almeno | adesso | che |")
                        cleaned_pipe_lyric = " ".join([t for m in measures for t in m])
                        nodes.append(ChordLyricLineNode([LyricSegment(cleaned_pipe_lyric, chord=None)]))
                        continue

            # Check for chord/lyric line with [Chord]
            if "[" in raw_line and "]" in raw_line:
                segments = cls._parse_chord_lyric_line(raw_line)
                nodes.append(ChordLyricLineNode(segments))
                continue

            # Check if line without brackets is purely chords (e.g. "SIb/FA  DO/MI   RE7/9+" or "RE7/9+" or "MI | DO | LA")
            tokens = [t.strip("[](),|") for t in line.split() if t.strip("[](),|")]
            if tokens and not re.search(r"\b\w+'\w+\b|[.,!?;:]", line):
                valid_chords = sum(1 for t in tokens if MusicEngine.parse_chord(t))
                if valid_chords > 0 and (valid_chords == len(tokens) or (valid_chords / len(tokens)) >= 0.75):
                    chord_segs = []
                    for t in tokens:
                        chord_segs.append(LyricSegment("   ", chord=ChordToken(t)))
                    nodes.append(ChordLyricLineNode(chord_segs))
                    continue

            # Default plain lyric line without chords
            nodes.append(ChordLyricLineNode([LyricSegment(raw_line, chord=None)]))

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
            if isinstance(node, DirectiveNode) and node.name == "key":
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
                new_nodes.append(ChordLyricLineNode(new_segments))

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
                new_nodes.append(ChordGridLineNode(new_measures))

            else:
                new_nodes.append(node)

        return AMLDocument(new_nodes)

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
            # Check if this line is a chord line and next line is lyrics
            if is_chord_line(curr_line) and (i + 1 < len(raw_lines)) and not is_chord_line(raw_lines[i + 1]):
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

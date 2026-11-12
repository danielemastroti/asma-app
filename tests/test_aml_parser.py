"""
Unit and Regression Tests for AML Parser & AST Engine
Conforms to SRS Cap. 5, 14, 17.10-17.14 and Blueprint Sec. 5.
"""

import unittest
from asma_core.aml_parser import (
    AMLParser, AMLDocument, DirectiveNode, SectionNode,
    CustomTagNode, ChordLyricLineNode, ChordGridLineNode
)


class TestAMLParser(unittest.TestCase):

    def setUp(self):
        self.sample_aml = """{title: Hotel California}
{artist: Eagles}
{key: Bm}
{tempo: 74}
{time: 4/4}

{intro}
| Bm | F#7 | A | E |

{verse}
[Bm]On a dark desert highway, [F#7]cool wind in my hair
[A]Warm smell of colitas, [E]rising up through the air

{chorus}
[G]Welcome to the Hotel Cali[D]fornia
{guitar: Don Felder intro riff}
Such a [Em]lovely place, such a [F#7]lovely face
"""

    def test_parse_document_metadata(self):
        """Test extraction of directives and metadata."""
        doc = AMLParser.parse(self.sample_aml)
        self.assertEqual(doc.get_directive("title"), "Hotel California")
        self.assertEqual(doc.get_directive("artist"), "Eagles")
        self.assertEqual(doc.get_directive("key"), "Bm")
        self.assertEqual(doc.get_directive("tempo"), "74")
        self.assertEqual(doc.get_directive("time"), "4/4")

    def test_sections_and_custom_tags(self):
        """Test parsing of musical sections and instrumental custom tags."""
        doc = AMLParser.parse(self.sample_aml)
        sections = [n for n in doc.nodes if isinstance(n, SectionNode)]
        self.assertEqual(len(sections), 3)
        self.assertEqual(sections[0].section_name, "intro")
        self.assertEqual(sections[1].section_name, "verse")
        self.assertEqual(sections[2].section_name, "chorus")

        custom_tags = [n for n in doc.nodes if isinstance(n, CustomTagNode)]
        self.assertEqual(len(custom_tags), 1)
        self.assertEqual(custom_tags[0].tag_type, "guitar")
        self.assertEqual(custom_tags[0].content, "Don Felder intro riff")

    def test_chord_grid_line_parsing(self):
        """Test parsing measure grids without lyrics."""
        doc = AMLParser.parse(self.sample_aml)
        grids = [n for n in doc.nodes if isinstance(n, ChordGridLineNode)]
        self.assertEqual(len(grids), 1)
        self.assertEqual(grids[0].measures, [["Bm"], ["F#7"], ["A"], ["E"]])
        self.assertEqual(grids[0].to_aml(), "| Bm | F#7 | A | E |")

    def test_roundtrip_serialization_fidelity(self):
        """SRS Cap. 17.10: Document parsing, serializing, and re-parsing must preserve 100% of tokens."""
        doc1 = AMLParser.parse(self.sample_aml)
        serialized_aml = doc1.to_aml()
        doc2 = AMLParser.parse(serialized_aml)

        self.assertEqual(doc1.metadata, doc2.metadata)
        self.assertEqual(len(doc1.nodes), len(doc2.nodes))

    def test_document_transposition(self):
        """Test transposing an entire document +2 semitones: Bm -> C#m."""
        doc = AMLParser.parse(self.sample_aml)
        transposed_doc = AMLParser.transpose_document(doc, semitones=2, prefer_flats=False)

        # Check key directive transposed
        self.assertEqual(transposed_doc.get_directive("key"), "C#m")

        # Check grid line transposed: Bm -> C#m, F#7 -> G#7, A -> B, E -> F#
        grid = [n for n in transposed_doc.nodes if isinstance(n, ChordGridLineNode)][0]
        self.assertEqual(grid.measures, [["C#m"], ["G#7"], ["B"], ["F#"]])

        # Check inline chords in verse transposed
        verse_lines = [n for n in transposed_doc.nodes if isinstance(n, ChordLyricLineNode)]
        chords_in_line1 = [s.chord.chord_text for s in verse_lines[0].segments if s.chord]
        self.assertEqual(chords_in_line1, ["C#m", "G#7"])

    def test_document_notation_conversion_ita_int(self):
        """Test converting whole document between INT and ITA."""
        doc_int = AMLParser.parse(self.sample_aml)
        doc_ita = AMLParser.convert_notation(doc_int, to_system="ITA")

        self.assertEqual(doc_ita.get_directive("key"), "SIm")
        grid = [n for n in doc_ita.nodes if isinstance(n, ChordGridLineNode)][0]
        self.assertEqual(grid.measures, [["SIm"], ["FA#7"], ["LA"], ["MI"]])

    def test_import_traditional_chords_over_text(self):
        """SRS Cap. 14.6: Imports traditional chord rows over lyric rows and converts to [Chord] inline."""
        traditional_text = """        C             G
Hello darkness my old friend
        Am            F
I've come to talk with you again"""

        imported_doc = AMLParser.import_traditional_chords_over_text(traditional_text)
        aml_out = imported_doc.to_aml()

        self.assertIn("[C]", aml_out)
        self.assertIn("[G]", aml_out)
        self.assertIn("[Am]", aml_out)
        self.assertIn("[F]", aml_out)
        self.assertIn("Hello [C]darkness", aml_out)

    def test_validate_aml_document(self):
        """Test AST validation detecting unrecognized chords or missing title."""
        invalid_aml = """{key: Bm}
[Xnotachord]This has a fake chord
"""
        doc = AMLParser.parse(invalid_aml)
        issues = AMLParser.validate(doc)

        # Should warn about missing {title:...} and unrecognized chord
        messages = [i["message"] for i in issues]
        self.assertTrue(any("title" in m.lower() for m in messages))
        self.assertTrue(any("Xnotachord" in m for m in messages))

    def test_grid_vs_lyrics_pipe_disambiguation(self):
        """Lines with pipes containing regular text should not become ChordGridLineNode."""
        aml = """| DO#m | SI | LA |
| Almeno | adesso | che |
| GUARDAMI |
[LA]Siamo seduti qui"""
        doc = AMLParser.parse(aml)
        grids = [n for n in doc.nodes if isinstance(n, ChordGridLineNode)]
        self.assertEqual(len(grids), 1)
        self.assertEqual(grids[0].measures, [["DO#m"], ["SI"], ["LA"]])

        lyrics = [n for n in doc.nodes if isinstance(n, ChordLyricLineNode)]
        self.assertEqual(len(lyrics), 3)
        self.assertEqual(lyrics[0].segments[0].text, "Almeno adesso che")
        self.assertEqual(lyrics[1].segments[0].text, "GUARDAMI")

    def test_traditional_chord_over_lyric_merge(self):
        """Test that AMLParser automatically merges traditional chord lines over lyric lines."""
        aml = """SOL            SOL4+
Vespe truccate anni sessanta"""
        doc = AMLParser.parse(aml)
        lines = [n for n in doc.nodes if isinstance(n, ChordLyricLineNode)]
        self.assertEqual(len(lines), 1)
        segs = lines[0].segments
        self.assertEqual(len(segs), 2)
        self.assertEqual(segs[0].chord.chord_text, "SOL")
        self.assertEqual(segs[0].text, "Vespe truccate ")
        self.assertEqual(segs[1].chord.chord_text, "SOL4+")
        self.assertEqual(segs[1].text, "anni sessanta")

    def test_plain_text_italian_chords_recognized_without_brackets(self):
        """Plain-text uppercase Italian chords like DO LA are parsed as chords, while lowercase Italian words remain lyrics."""
        aml = """DO  LA
Nel blu dipinto di blu

DO  LA  FA  SOL

la casa va
do la mano"""
        doc = AMLParser.parse(aml)
        lines = [n for n in doc.nodes if isinstance(n, ChordLyricLineNode)]
        self.assertEqual(len(lines), 4)

        # Line 0: DO LA merged over lyric line
        self.assertEqual(lines[0].segments[0].chord.chord_text, "DO")
        self.assertEqual(lines[0].segments[1].chord.chord_text, "LA")

        # Line 1: standalone DO LA FA SOL chord line
        standalone_chords = [s.chord.chord_text for s in lines[1].segments if s.chord]
        self.assertEqual(standalone_chords, ["DO", "LA", "FA", "SOL"])

        # Lines 2 & 3: lowercase Italian words stay plain lyrics (no chords)
        self.assertTrue(all(s.chord is None for s in lines[2].segments))
        self.assertEqual(lines[2].segments[0].text, "la casa va")
        self.assertTrue(all(s.chord is None for s in lines[3].segments))
        self.assertEqual(lines[3].segments[0].text, "do la mano")


if __name__ == "__main__":
    unittest.main()

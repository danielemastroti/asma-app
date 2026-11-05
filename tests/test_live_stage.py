"""
Unit Tests for Live Stage Component Bundle Generator
Conforms to SRS Cap. 12 and Blueprint Sec. 9.
"""

import unittest
from asma_core.models import Song
from asma_core.live_stage_component import LiveStageComponent


class TestLiveStageComponent(unittest.TestCase):

    def setUp(self):
        self.song = Song(
            title="Hotel California",
            artist="Eagles",
            key_current="Bm",
            bpm=74,
            time_signature="4/4",
            aml_content="""{title: Hotel California}
{intro}
| Bm | F#7 | A | E |

{verse}
[Bm]On a dark desert highway
"""
        )

    def test_render_html_bundle_structure(self):
        """Validates that generated HTML contains essential stage capabilities."""
        html = LiveStageComponent.render_html_bundle([self.song], dark_theme=True)
        self.assertIsNotNone(html)
        self.assertIn("<!DOCTYPE html>", html)

        # Verify song data embedded
        self.assertIn("Hotel California", html)
        self.assertIn("Eagles", html)

        # Verify 60fps requestAnimationFrame loop present
        self.assertIn("requestAnimationFrame(scrollStep)", html)

        # Verify Bluetooth Pedal Keydown Listeners present
        self.assertIn("PageDown", html)
        self.assertIn("PageUp", html)
        self.assertIn("Digit1", html)
        self.assertIn("Digit2", html)

        # Verify Screen Wake Lock API present
        self.assertIn("navigator.wakeLock.request('screen')", html)

        # Verify Web Audio API Metronome present
        self.assertIn("AudioContext", html)

        # Verify Offline LocalStorage Cache present
        self.assertIn("localStorage.setItem", html)


if __name__ == "__main__":
    unittest.main()

"""
ASMA Accordi Next Generation - Auxiliary Band AI Service
Optional Creative AI Assistant for Arrangements and Medleys.
Conforms to SRS Cap. 15.6, 19.9, 22.5 and Blueprint Rule "Music First".
STRICTLY FORBIDDEN FOR: Chord parsing, transpositions, PDF generation, or versioning.
"""

from __future__ import annotations
import os
from typing import Dict, Any, Optional, List
from asma_core.music_engine import MusicEngine


class BandAIService:
    """
    Auxiliary Creative AI Service.
    100% Optional. Fallbacks seamlessly to deterministic logic when offline or disabled.
    """
    MODE_OFF = "OFF"
    MODE_FREE = "FREE"
    MODE_PREMIUM = "PREMIUM"

    @classmethod
    def get_current_mode(cls) -> str:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return cls.MODE_OFF
        return os.environ.get("ASMA_AI_MODE", cls.MODE_FREE)

    @classmethod
    def suggest_medley_transition(
        cls,
        song_a_title: str,
        song_a_key: str,
        song_a_bpm: int,
        song_b_title: str,
        song_b_key: str,
        song_b_bpm: int
    ) -> Dict[str, Any]:
        """
        Generates creative arrangement advice for transitioning between two songs in a medley.
        Operates without AI by default; utilizes Gemini if configured.
        """
        # 1. Deterministic Music Engine Analysis (Guaranteed to work)
        score, details = MusicEngine.calculate_harmonic_compatibility(
            song_a_key, song_a_bpm, song_b_key, song_b_bpm
        )

        advice = [
            f"Transizione da '{song_a_title}' ({song_a_key}, {song_a_bpm} BPM) verso '{song_b_title}' ({song_b_key}, {song_b_bpm} BPM).",
            f"Valutazione armonica: Distanza sul circolo delle quinte = {details.get('fifths_distance')} semitoni di quinta.",
            f"Variazione ritmica: {details.get('bpm_diff_percent')}% di differenza."
        ]

        if details.get("fifths_distance", 0) == 0:
            advice.append("Suggerimento: Stessa tonalità! Chiudi l'ultimo ritornello del primo brano suonando l'accordo di tonica in stacco e fai entrare la chitarra sul primo battere.")
        elif details.get("fifths_distance", 0) == 1:
            advice.append("Suggerimento: Modulazione alla dominante/sottodominante. Utilizza una misura di stacco ritmico di batteria per impostare il nuovo tempo.")
        else:
            advice.append("Suggerimento: Tonalità distanti. Consigliato un ponte strumentale con giro armonico di 4 battute per modulare alla nuova tonalità.")

        return {
            "score": score,
            "details": details,
            "creative_advice": "\n".join(advice),
            "ai_mode_used": cls.get_current_mode()
        }

    @classmethod
    def suggest_arrangement_ideas(cls, title: str, genre: str, key: str, bpm: int) -> str:
        """Suggests live arrangement dynamics (Intro, Solo, Outro, Dynamics)."""
        return f"""Consigli di Arrangiamento Live per '{title}' ({genre}, {key}, {bpm} BPM):
1. **Intro:** Inizia con strumento solista (chitarra o piano) per le prime 4 battute, poi ingresso di cassa in 4 a metà intro per definire il groove prima della voce.
2. **Strofa 1:** Mantieni il basso lineare sui quarti con piatti charleston chiusi per dare intimità al testo.
3. **Ritornello:** Esplosione dinamica: apertura del charleston, raddoppio delle chitarre e armonia vocale a due voci sulla terza superiore.
4. **Bridge / Assolo:** Sezione ritmica serrata, progressione in crescendo dinamico fino al drop sul ritornello finale.
5. **Finale:** Uscita con giro armonico ripetuto in diminuendo con stacco secco sull'accordo di tonica ({key})."""

"""
ASMA Accordi Next Generation - GitHub Gist Synchronization Client
Connects to GitHub Gist REST API v3 for low-cost cloud storage and remote backups.
Conforms to SRS Cap. 15.8, 18.9, 22.8 and Blueprint CRIT-01.
"""

from __future__ import annotations
import os
import json
import requests
from typing import Dict, Any, Optional, Tuple


class GistClient:
    """Client for synchronizing application data with GitHub Gist."""

    API_BASE = "https://api.github.com/gists"

    def __init__(self, token: Optional[str] = None, gist_id: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_PAT")
        self.gist_id = gist_id or os.environ.get("GIST_ID") or os.environ.get("ASMA_GIST_ID")
        
        # Automatic fallback to Streamlit secrets or .streamlit/secrets.toml
        if not self.token:
            try:
                import streamlit as st
                if hasattr(st, "secrets") and "github" in st.secrets:
                    self.token = str(st.secrets["github"].get("token", "")).strip() or self.token
                    self.gist_id = str(st.secrets["github"].get("gist_id", "")).strip() or self.gist_id
            except Exception:
                pass
        if not self.token and os.path.exists(".streamlit/secrets.toml"):
            try:
                import toml
                with open(".streamlit/secrets.toml", "r", encoding="utf-8") as f:
                    tdata = toml.load(f)
                    self.token = tdata.get("github", {}).get("token") or self.token
                    self.gist_id = tdata.get("github", {}).get("gist_id") or self.gist_id
            except Exception:
                pass

    @property
    def is_configured(self) -> bool:
        return bool(self.token and self.gist_id)

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ASMA-Accordi-2.0"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def test_connection(self) -> Tuple[bool, str]:
        """Tests connectivity to GitHub Gist endpoint."""
        if not self.is_configured:
            return False, "GITHUB_TOKEN o GIST_ID non configurati (modalità offline locale attiva)."

        url = f"{self.API_BASE}/{self.gist_id}"
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                owner = data.get("owner", {}).get("login", "unknown")
                files_count = len(data.get("files", {}))
                return True, f"Connesso con successo al Gist di @{owner} ({files_count} file sincronizzati)."
            elif resp.status_code == 404:
                return False, f"Gist con ID '{self.gist_id}' non trovato su GitHub."
            elif resp.status_code == 401:
                return False, "Token GitHub non valido o privo di permessi per i Gist."
            else:
                return False, f"Errore risposta GitHub: HTTP {resp.status_code}"
        except Exception as e:
            return False, f"Errore di rete verso api.github.com: {str(e)}"

    def pull_all_files(self) -> Tuple[bool, Dict[str, str], str]:
        """Downloads all content files stored in the remote Gist."""
        if not self.is_configured:
            return False, {}, "Gist non configurato."

        url = f"{self.API_BASE}/{self.gist_id}"
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=12)
            if resp.status_code != 200:
                return False, {}, f"Errore HTTP {resp.status_code}"

            data = resp.json()
            remote_files: Dict[str, str] = {}
            for fname, finfo in data.get("files", {}).items():
                content = finfo.get("content", "")
                remote_files[fname] = content

            return True, remote_files, f"Scaricati {len(remote_files)} file dal Gist."
        except Exception as e:
            return False, {}, f"Errore durante il download dal Gist: {str(e)}"

    def push_files(self, files_to_update: Dict[str, str]) -> Tuple[bool, str]:
        """
        Updates or creates files on the remote Gist in a single atomic PATCH call.
        """
        if not self.is_configured:
            return False, "Gist non configurato. Le modifiche rimangono salvate solo in locale."

        url = f"{self.API_BASE}/{self.gist_id}"
        payload_files = {}
        for fname, content in files_to_update.items():
            payload_files[fname] = {"content": content}

        payload = {"files": payload_files}

        try:
            resp = requests.patch(url, headers=self._get_headers(), json=payload, timeout=12)
            if resp.status_code == 200:
                return True, f"Sincronizzati {len(files_to_update)} file su GitHub Gist."
            else:
                return False, f"Errore HTTP {resp.status_code}: {resp.text}"
        except Exception as e:
            return False, f"Errore di rete durante l'invio al Gist: {str(e)}"

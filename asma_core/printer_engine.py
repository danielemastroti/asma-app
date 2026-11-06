"""
ASMA Accordi Next Generation - Printer Engine
Handles direct printing to system print queues and browser print spoolers.
Guarantees NO PDF file is saved/downloaded when the user requests printing.
Conforms to SRS Cap. 10.4 and User Directives.
"""

from __future__ import annotations
import os
import sys
import base64
import tempfile
import subprocess
from typing import List, Dict, Any, Optional, Tuple


class PrinterEngine:
    """
    Engine to manage direct printing to printer queues without saving/downloading PDF files.
    """

    @classmethod
    def build_printable_html(cls, pdf_bytes: bytes, title: str, subtitle: str = "") -> str:
        """
        Converts the formatted ReportLab PDF into an A4 print-ready HTML document.
        Automatically opens the system / browser print spooler dialog (window.print())
        without downloading or saving any PDF file to disk.
        """
        import pymupdf

        doc_pdf = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        num_pages = len(doc_pdf)

        pages_b64: List[str] = []
        for page in doc_pdf:
            pix = page.get_pixmap(dpi=200)
            img_b64 = base64.b64encode(pix.tobytes("png")).decode("utf-8")
            pages_b64.append(img_b64)

        pages_html = []
        for i, b64 in enumerate(pages_b64):
            pages_html.append(f"""
            <div class="print-page">
                <img src="data:image/png;base64,{b64}" alt="Pagina {i+1} di {num_pages}" />
            </div>
            """)

        html_content = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stampa: {title}</title>
    <style>
        @page {{
            size: A4 portrait;
            margin: 0;
        }}
        @media print {{
            html, body {{
                margin: 0 !important;
                padding: 0 !important;
                background: #FFFFFF !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            .no-print {{
                display: none !important;
            }}
            .print-page {{
                page-break-after: always;
                page-break-inside: avoid;
                width: 100vw;
                height: 100vh;
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .print-page img {{
                width: 100%;
                height: 100%;
                object-fit: contain;
                display: block;
            }}
        }}
        @media screen {{
            body {{
                margin: 0;
                padding: 16px;
                background: #0F172A;
                color: #F8FAFC;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
            }}
            .toolbar {{
                position: sticky;
                top: 10px;
                z-index: 9999;
                background: #1E293B;
                border: 1px solid #334155;
                padding: 12px 20px;
                border-radius: 10px;
                display: flex;
                align-items: center;
                gap: 16px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.5);
                margin-bottom: 20px;
            }}
            .toolbar-title {{
                font-size: 15px;
                font-weight: 700;
                color: #F8FAFC;
            }}
            .toolbar-subtitle {{
                font-size: 12px;
                color: #94A3B8;
            }}
            .btn-action {{
                background: #2563EB;
                color: #FFFFFF;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: background 0.2s;
            }}
            .btn-action:hover {{
                background: #1D4ED8;
            }}
            .btn-close {{
                background: #475569;
            }}
            .btn-close:hover {{
                background: #334155;
            }}
            .print-page {{
                background: #FFFFFF;
                box-shadow: 0 4px 20px rgba(0,0,0,0.4);
                margin-bottom: 24px;
                border-radius: 4px;
                overflow: hidden;
                max-width: 820px;
                width: 100%;
            }}
            .print-page img {{
                width: 100%;
                height: auto;
                display: block;
            }}
        }}
    </style>
    <script>
        window.addEventListener('load', function() {{
            // Avvia automaticamente il dialogo/spooler di stampa di sistema
            setTimeout(function() {{
                window.focus();
                window.print();
            }}, 350);
        }});
    </script>
</head>
<body>
    <div class="toolbar no-print">
        <div>
            <div class="toolbar-title">🖨️ Coda di Stampa: {title}</div>
            <div class="toolbar-subtitle">{subtitle or f'Documento pronto per la stampante ({num_pages} pag.)'}</div>
        </div>
        <button class="btn-action" onclick="window.print()">🖨️ Invia alla Stampante</button>
        <button class="btn-action btn-close" onclick="window.close()">Chiudi</button>
    </div>
    {''.join(pages_html)}
</body>
</html>"""
        return html_content

    @classmethod
    def render_print_buttons_component(
        cls,
        pdf_chords_bytes: bytes,
        pdf_lyrics_bytes: bytes,
        title: str
    ) -> str:
        """
        Renders interactive HTML buttons that invoke the client/system print queue directly.
        Bypasses file downloads completely using Blob URLs and window.print().
        """
        html_chords = cls.build_printable_html(pdf_chords_bytes, title, "Versione con Accordi (A4)")
        html_lyrics = cls.build_printable_html(pdf_lyrics_bytes, title, "Versione Solo Testo (A4)")

        b64_html_chords = base64.b64encode(html_chords.encode("utf-8")).decode("utf-8")
        b64_html_lyrics = base64.b64encode(html_lyrics.encode("utf-8")).decode("utf-8")

        component_html = f"""
        <div style="display: flex; gap: 8px; width: 100%; margin: 4px 0 10px 0;">
            <button id="btn_print_chords" onclick="openPrintQueue('{b64_html_chords}')" style="
                flex: 1;
                background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%);
                color: #FFFFFF;
                border: 1px solid #3B82F6;
                padding: 10px 14px;
                border-radius: 8px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 13px;
                font-weight: 700;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                box-shadow: 0 2px 6px rgba(29, 78, 216, 0.3);
                transition: transform 0.1s, background 0.2s;
            ">
                <span>🎸</span>
                <span>Stampa A4: con Accordi</span>
            </button>
            <button id="btn_print_lyrics" onclick="openPrintQueue('{b64_html_lyrics}')" style="
                flex: 1;
                background: linear-gradient(135deg, #334155 0%, #475569 100%);
                color: #F8FAFC;
                border: 1px solid #64748B;
                padding: 10px 14px;
                border-radius: 8px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 13px;
                font-weight: 700;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
                transition: transform 0.1s, background 0.2s;
            ">
                <span>🎤</span>
                <span>Stampa A4: Solo Testo</span>
            </button>
        </div>

        <script>
            function b64ToUtf8(str) {{
                return decodeURIComponent(escape(window.atob(str)));
            }}

            function openPrintQueue(b64Content) {{
                try {{
                    const htmlText = b64ToUtf8(b64Content);
                    const blob = new Blob([htmlText], {{ type: 'text/html;charset=utf-8' }});
                    const url = URL.createObjectURL(blob);
                    
                    // Apri il visualizzatore di stampa in una nuova scheda che avvia subito window.print()
                    const printWindow = window.open(url, '_blank');
                    if (!printWindow || printWindow.closed || typeof printWindow.closed == 'undefined') {{
                        // Fallback in caso di blocco popup: usa un iframe nascosto
                        const iframe = document.createElement('iframe');
                        iframe.style.position = 'fixed';
                        iframe.style.right = '0';
                        iframe.style.bottom = '0';
                        iframe.style.width = '0';
                        iframe.style.height = '0';
                        iframe.style.border = '0';
                        iframe.src = url;
                        document.body.appendChild(iframe);
                        iframe.onload = function() {{
                            setTimeout(function() {{
                                iframe.contentWindow.focus();
                                iframe.contentWindow.print();
                            }}, 300);
                        }};
                    }}
                }} catch (err) {{
                    console.error('Errore durante invio alla stampante:', err);
                }}
            }}
        </script>
        """
        return component_html

    @classmethod
    def list_system_printers(cls) -> List[Dict[str, Any]]:
        """
        Rileva le stampanti fisiche o di rete installate sul sistema host (Windows/Linux/Mac).
        """
        printers: List[Dict[str, Any]] = []
        if sys.platform == "win32":
            try:
                cmd = ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_Printer | Select-Object Name, Default, PortName | ConvertTo-Json"]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if res.returncode == 0 and res.stdout.strip():
                    import json
                    raw = json.loads(res.stdout)
                    items = [raw] if isinstance(raw, dict) else raw
                    for item in items:
                        printers.append({
                            "name": item.get("Name", "Stampante"),
                            "is_default": bool(item.get("Default", False)),
                            "port": item.get("PortName", "")
                        })
            except Exception:
                pass
        return printers

    @classmethod
    def send_to_windows_spooler(cls, pdf_bytes: bytes, printer_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Invia direttamente i byte PDF allo spooler di stampa di Windows senza salvare file definitivi.
        Utilizza un file temporaneo effimero che viene rimosso al termine dell'operazione.
        """
        if sys.platform != "win32":
            return False, "La stampa diretta da spooler server è supportata su ambienti Windows."

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(pdf_bytes)
                tmp_path = f.name

            target_printer = printer_name
            if not target_printer:
                all_p = cls.list_system_printers()
                defaults = [p["name"] for p in all_p if p.get("is_default")]
                target_printer = defaults[0] if defaults else (all_p[0]["name"] if all_p else None)

            if not target_printer:
                return False, "Nessuna stampante rilevata sul sistema host."

            # Comando PowerShell per inviare allo spooler senza GUI
            ps_cmd = f'Start-Process -FilePath "{tmp_path}" -Verb PrintTo -ArgumentList "{target_printer}" -PassThru | Wait-Process -Timeout 10'
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=12)

            return True, f"Inviato con successo alla coda di stampa '{target_printer}'."
        except Exception as ex:
            return False, f"Errore invio spooler: {str(ex)}"
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

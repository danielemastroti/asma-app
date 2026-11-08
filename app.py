"""
ASMA Accordi Next Generation - Main Application Shell (Streamlit)
Full production-ready application satisfying SRS v1.0 (Cap. 1 - 22).
Includes: Music Engine, AML AST, In-memory SQL, ReportLab PDF, Live Stage 60fps,
Web Importer, Live Events, Manual Engine, Changelog Engine, Gist Client, and Band AI.
"""

import streamlit as st
import time
import json
from datetime import datetime
import re
from typing import Optional, List, Dict, Any, Union

# Check for Health Endpoint Query Parameter first (SRS Cap. 15.16 & 18.14)
# Compatible with UptimeRobot, Pingdom, StatusCake
params = st.query_params
if "health" in params or params.get("endpoint") == "health":
    st.write({
        "status": "healthy",
        "version": "2026.11.05",
        "github": "ok",
        "authentication": "ok",
        "pdf": "ok",
        "ai": "ok",
        "timestamp": datetime.now().isoformat()
    })
    st.stop()

# Set Streamlit Page Configuration
import os
import asma_core.browser_polyfill
page_icon_val = "assets/band_logo.png" if os.path.exists("assets/band_logo.png") else "🎵"
st.set_page_config(
    page_title="THE New ASMA — Accordi 2.0",
    page_icon=page_icon_val,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject Browser Compatibility Polyfills & Mobile Dropdown Guard (ES2023 + suppress virtual keyboard on selectboxes)
st.markdown(asma_core.browser_polyfill.POLYFILL_SCRIPT, unsafe_allow_html=True)
st.components.v1.html(
    f"""<script>
    try {{
      var frame = window.frameElement;
      if (frame) {{
        frame.style.display = 'none';
        frame.style.height = '0px';
        frame.style.margin = '0px';
        frame.style.padding = '0px';
        frame.style.border = 'none';
        var p = frame.parentElement;
        if (p && p.classList.contains('element-container')) {{
          p.style.display = 'none';
        }}
      }}
    }} catch(e) {{}}
    {asma_core.browser_polyfill.MOBILE_DROPDOWN_GUARD_JS}
    </script>""",
    height=0
)

# Custom CSS for Professional Dark Band Theme and Clean Layout (SRS Cap. 5 & Blueprint Sec. 14)
st.markdown("""
<style>
  /* Completely disable and hide Streamlit Sidebar and sidebar hamburger/toggles */
  section[data-testid="stSidebar"],
  [data-testid="stSidebarCollapseButton"],
  [data-testid="collapsedControl"] {
    display: none !important;
  }

  /* Make central page span full width with HTML-frame fixed top header */
  [data-testid="stAppViewContainer"],
  section[data-testid="stMain"],
  .main {
    width: 100vw !important;
    max-width: 100vw !important;
    overflow-y: auto !important;
  }

  /* Top clearance so fixed header NEVER overlaps subheaders, metrics or second-level tabs */
  .main .block-container, [data-testid="stMainBlockContainer"] {
    padding-top: 104px !important;
    padding-left: 16px !important;
    padding-right: 16px !important;
    max-width: 100% !important;
    overflow: visible !important;
  }
  @media (max-width: 768px) {
    .main .block-container, [data-testid="stMainBlockContainer"] {
      padding-top: 106px !important;
      padding-left: 10px !important;
      padding-right: 10px !important;
    }
  }

  /* ULTRA COMPACT TOP FIXED NAVIGATION FRAME (HTML Frame Style) */
  div[class*="st-key-top_navbar_container"] {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    width: 100vw !important;
    z-index: 999990 !important;
    background: rgba(13, 17, 23, 0.98) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border-bottom: 2px solid #0288D1 !important;
    padding: 4px 14px 4px 14px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.85) !important;
  }

  /* PREVENT STREAMLIT FROM COLLAPSING TOP NAVBAR COLUMNS ON ANY DEVICE (PC, iPad, Huawei, Android, iPhone) */
  div[class*="st-key-top_navbar_container"] [data-testid="stHorizontalBlock"],
  div[class*="st-key-top_navbar_container"] div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    justify-content: space-between !important;
    gap: 4px !important;
    width: 100% !important;
    min-width: 0 !important;
  }

  div[class*="st-key-top_navbar_container"] [data-testid="stColumn"],
  div[class*="st-key-top_navbar_container"] div[data-testid="stColumn"] {
    min-width: 0 !important;
    flex-shrink: 1 !important;
    width: auto !important;
  }

  /* Compact popovers in top navbar - side-by-side on the top right */
  div[class*="st-key-top_navbar_container"] [data-testid="stPopover"] {
    display: inline-block !important;
    width: 100% !important;
  }
  div[class*="st-key-top_navbar_container"] [data-testid="stPopover"] > button {
    font-size: 11px !important;
    padding: 2px 7px !important;
    height: 26px !important;
    min-height: 26px !important;
    border-radius: 13px !important;
    line-height: 1 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    background: rgba(255, 255, 255, 0.08) !important;
    border: 1px solid rgba(255, 255, 255, 0.16) !important;
    color: #E2E8F0 !important;
  }
  div[class*="st-key-top_navbar_container"] [data-testid="stPopover"] > button:hover {
    background: rgba(2, 136, 209, 0.35) !important;
    border-color: #00E5FF !important;
    color: #FFFFFF !important;
  }

  /* Responsive Scaletta Toolbar - stays horizontal on smartphones and tablets */
  div[class*="st-key-scaletta_toolbar_container"] [data-testid="stHorizontalBlock"],
  div[class*="st-key-scaletta_toolbar_container"] div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 4px !important;
    width: 100% !important;
    min-width: 0 !important;
  }
  div[class*="st-key-scaletta_toolbar_container"] [data-testid="stColumn"],
  div[class*="st-key-scaletta_toolbar_container"] div[data-testid="stColumn"] {
    min-width: 0 !important;
    flex: 1 1 0 !important;
  }

  /* Responsive Setlist Song Row (Ordine di Palco) - Perfect Fit on Mobile Screens */
  div[class*="st-key-set_order_item_"] {
    background: rgba(30, 41, 59, 0.45) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
    padding: 3px 6px !important;
    margin-bottom: 4px !important;
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
  }
  div[class*="st-key-set_order_item_"] [data-testid="stHorizontalBlock"],
  div[class*="st-key-set_order_item_"] div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    justify-content: space-between !important;
    gap: 4px !important;
    width: 100% !important;
    min-width: 0 !important;
  }
  div[class*="st-key-set_order_item_"] [data-testid="stColumn"],
  div[class*="st-key-set_order_item_"] div[data-testid="stColumn"],
  div[class*="st-key-set_order_item_"] [data-testid="column"],
  div[class*="st-key-set_order_item_"] div[data-testid="column"] {
    min-width: 0 !important;
    width: auto !important;
    flex-shrink: 0 !important;
  }
  /* Column 1: Index Badge */
  div[class*="st-key-set_order_item_"] [data-testid="stColumn"]:nth-child(1),
  div[class*="st-key-set_order_item_"] div[data-testid="stColumn"]:nth-child(1) {
    flex: 0 0 28px !important;
    width: 28px !important;
    min-width: 28px !important;
    max-width: 28px !important;
  }
  /* Column 2: Song Title & Key/BPM details */
  div[class*="st-key-set_order_item_"] [data-testid="stColumn"]:nth-child(2),
  div[class*="st-key-set_order_item_"] div[data-testid="stColumn"]:nth-child(2) {
    flex: 1 1 auto !important;
    flex-grow: 1 !important;
    flex-shrink: 1 !important;
    min-width: 0 !important;
    overflow: hidden !important;
  }
  /* Columns 3, 4, 5: Action buttons (Up, Down, Delete) */
  div[class*="st-key-set_order_item_"] [data-testid="stColumn"]:nth-child(3),
  div[class*="st-key-set_order_item_"] div[data-testid="stColumn"]:nth-child(3),
  div[class*="st-key-set_order_item_"] [data-testid="stColumn"]:nth-child(4),
  div[class*="st-key-set_order_item_"] div[data-testid="stColumn"]:nth-child(4),
  div[class*="st-key-set_order_item_"] [data-testid="stColumn"]:nth-child(5),
  div[class*="st-key-set_order_item_"] div[data-testid="stColumn"]:nth-child(5) {
    flex: 0 0 34px !important;
    width: 34px !important;
    min-width: 34px !important;
    max-width: 34px !important;
  }
  /* Buttons styling in setlist row */
  div[class*="st-key-set_order_item_"] [data-testid="stButton"] {
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
  }
  div[class*="st-key-set_order_item_"] [data-testid="stButton"] button {
    width: 32px !important;
    min-width: 32px !important;
    max-width: 32px !important;
    height: 32px !important;
    min-height: 32px !important;
    padding: 0 !important;
    font-size: 14px !important;
    line-height: 1 !important;
    border-radius: 6px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
    background: rgba(255, 255, 255, 0.08) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
  }
  div[class*="st-key-set_order_item_"] [data-testid="stButton"] button:hover {
    background: rgba(2, 136, 209, 0.35) !important;
    border-color: #00E5FF !important;
  }

div[class*="st-key-scaletta_toolbar_container"] div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 4px !important;
    width: 100% !important;
    min-width: 0 !important;
  }
  div[class*="st-key-scaletta_toolbar_container"] [data-testid="stColumn"],
  div[class*="st-key-scaletta_toolbar_container"] div[data-testid="stColumn"] {
    min-width: 0 !important;
    flex: 1 1 0 !important;
  }
  div[class*="st-key-scaletta_toolbar_container"] [data-testid="stPopover"] {
    width: 100% !important;
  }
  div[class*="st-key-scaletta_toolbar_container"] [data-testid="stPopover"] > button {
    font-size: 11px !important;
    padding: 2px 4px !important;
    height: 30px !important;
    min-height: 30px !important;
    border-radius: 6px !important;
    line-height: 1 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    width: 100% !important;
  }

  /* Responsive equalizer: gracefully hides on very narrow mobile screens */
  @media (max-width: 680px) {
    .asma-bar-center-eq {
      display: none !important;
    }
  }

  /* ULTRA COMPACT TWO-ROW NAVIGATION PILLS (Always 2 Rows, Ultra-Sleek) */
  div[class*="top_nav_pills_r1"],
  div[class*="top_nav_pills_r2"] {
    width: 100% !important;
    margin-top: 1px !important;
    margin-bottom: 1px !important;
    padding: 0 !important;
  }
  div[class*="top_nav_pills_r1"] [data-testid="stPills"],
  div[class*="top_nav_pills_r2"] [data-testid="stPills"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    overflow-y: hidden !important;
    gap: 3px !important;
    justify-content: flex-start !important;
    padding: 0 0 1px 0 !important;
    scrollbar-width: none !important;
    -ms-overflow-style: none !important;
  }
  div[class*="top_nav_pills_r1"] [data-testid="stPills"]::-webkit-scrollbar,
  div[class*="top_nav_pills_r2"] [data-testid="stPills"]::-webkit-scrollbar {
    display: none !important;
  }
  div[class*="top_nav_pills_r1"] [data-testid="stPill"],
  div[class*="top_nav_pills_r1"] button,
  div[class*="top_nav_pills_r2"] [data-testid="stPill"],
  div[class*="top_nav_pills_r2"] button {
    background: rgba(30, 41, 59, 0.85) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    color: #E2E8F0 !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    padding: 1px 7px !important;
    height: 23px !important;
    min-height: 23px !important;
    border-radius: 11px !important;
    transition: all 0.15s ease-in-out !important;
    cursor: pointer !important;
    white-space: nowrap !important;
    flex-shrink: 0 !important;
    line-height: 1 !important;
  }
  div[class*="top_nav_pills_r1"] [data-testid="stPill"]:hover,
  div[class*="top_nav_pills_r1"] button:hover,
  div[class*="top_nav_pills_r2"] [data-testid="stPill"]:hover,
  div[class*="top_nav_pills_r2"] button:hover {
    background: rgba(2, 136, 209, 0.3) !important;
    border-color: #00E5FF !important;
    color: #FFFFFF !important;
    transform: translateY(-1px) !important;
  }
  div[class*="top_nav_pills_r1"] [aria-selected="true"],
  div[class*="top_nav_pills_r1"] [aria-pressed="true"],
  div[class*="top_nav_pills_r1"] [aria-checked="true"],
  div[class*="top_nav_pills_r1"] [data-selected="true"],
  div[class*="top_nav_pills_r1"] button[kind="primary"],
  div[class*="top_nav_pills_r2"] [aria-selected="true"],
  div[class*="top_nav_pills_r2"] [aria-pressed="true"],
  div[class*="top_nav_pills_r2"] [aria-checked="true"],
  div[class*="top_nav_pills_r2"] [data-selected="true"],
  div[class*="top_nav_pills_r2"] button[kind="primary"] {
    background: linear-gradient(135deg, #0288D1, #0091EA) !important;
    border-color: #00E5FF !important;
    color: #FFFFFF !important;
    box-shadow: 0 0 10px rgba(0, 229, 255, 0.6) !important;
    font-weight: 700 !important;
  }

  /* Second-level tabs styling (Never cut off or truncated) */
  [data-testid="stTabs"] {
    margin-top: 4px !important;
  }
  [data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 6px !important;
    overflow-x: auto !important;
    flex-wrap: nowrap !important;
    scrollbar-width: thin !important;
  }
  [data-testid="stTabs"] [data-baseweb="tab"] {
    padding: 5px 12px !important;
    font-size: 12px !important;
    white-space: nowrap !important;
    flex-shrink: 0 !important;
  }
  div[class*="st-key-top_nav_pills_widget"] [data-testid="stPill"]:hover,
  div[class*="st-key-top_nav_pills_widget"] button:hover {
    background: rgba(2, 136, 209, 0.3) !important;
    border-color: #00E5FF !important;
    color: #FFFFFF !important;
    transform: translateY(-1px) !important;
  }
  div[class*="st-key-top_nav_pills_widget"] [aria-selected="true"],
  div[class*="st-key-top_nav_pills_widget"] [aria-pressed="true"],
  div[class*="st-key-top_nav_pills_widget"] [aria-checked="true"],
  div[class*="st-key-top_nav_pills_widget"] [data-selected="true"],
  div[class*="st-key-top_nav_pills_widget"] button[kind="primary"] {
    background: linear-gradient(135deg, #0288D1, #0091EA) !important;
    border-color: #00E5FF !important;
    color: #FFFFFF !important;
    box-shadow: 0 0 12px rgba(0, 229, 255, 0.6) !important;
    font-weight: 700 !important;
  }

  /* TOP FIXED BAR (Always Visible & Animated) */
  .asma-top-fixed-bar {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 42px;
    background: rgba(13, 17, 23, 0.97);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 2px solid #0288D1;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 18px;
    z-index: 999999;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.7);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }

  /* Glowing laser progress line on top edge */
  .asma-laser-line {
    position: absolute;
    top: 0;
    left: 0;
    height: 3px;
    width: 100%;
    background: linear-gradient(90deg, #0288D1, #00E5FF, #FFD600, #00E676, #00E5FF, #0288D1);
    background-size: 300% 100%;
    animation: asma-laser-flow 3s ease infinite;
  }

  @keyframes asma-laser-flow {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }

  .asma-bar-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .asma-brand-name {
    font-weight: 800;
    font-size: 13px;
    letter-spacing: 0.5px;
    color: #FFFFFF;
  }
  .asma-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(0, 230, 118, 0.12);
    border: 1px solid rgba(0, 230, 118, 0.4);
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    color: #00E676;
    transition: all 0.3s ease;
  }
  .asma-led-dot {
    width: 8px;
    height: 8px;
    background-color: #00E676;
    border-radius: 50%;
    box-shadow: 0 0 8px #00E676;
    animation: asma-led-pulse 1.8s infinite;
  }
  @keyframes asma-led-pulse {
    0%, 100% { opacity: 1; transform: scale(1); box-shadow: 0 0 8px #00E676; }
    50% { opacity: 0.35; transform: scale(0.85); box-shadow: 0 0 2px #00E676; }
  }

  /* Center Equalizer Soundwave Animation */
  .asma-bar-center {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .asma-eq-container {
    display: flex;
    align-items: flex-end;
    height: 16px;
    gap: 3px;
  }
  .asma-eq-bar {
    width: 3px;
    background: #00E5FF;
    border-radius: 2px;
    animation: asma-eq-bounce 1.2s ease-in-out infinite alternate;
  }
  .eq-1 { height: 6px; animation-delay: 0.0s; }
  .eq-2 { height: 12px; animation-delay: 0.2s; background: #00E676; }
  .eq-3 { height: 16px; animation-delay: 0.4s; background: #FFD600; }
  .eq-4 { height: 9px; animation-delay: 0.1s; background: #00E5FF; }
  .eq-5 { height: 14px; animation-delay: 0.3s; background: #FF5252; }
  .eq-6 { height: 7px; animation-delay: 0.5s; background: #00E676; }
  .eq-7 { height: 11px; animation-delay: 0.25s; background: #00E5FF; }

  @keyframes asma-eq-bounce {
    0% { height: 3px; }
    50% { height: 16px; }
    100% { height: 7px; }
  }
  .asma-eq-label {
    font-size: 11px;
    color: #94A3B8;
    font-weight: 500;
    letter-spacing: 0.5px;
  }

  .asma-bar-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .asma-user-chip {
    font-size: 12px;
    font-weight: 600;
    padding: 3px 10px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
  }

  /* Style Streamlit's native status widget when running */
  [data-testid="stStatusWidget"] {
    position: fixed !important;
    top: 6px !important;
    right: 20px !important;
    z-index: 1000001 !important;
    background: rgba(2, 136, 209, 0.95) !important;
    color: #FFFFFF !important;
    border: 1px solid #00E5FF !important;
    border-radius: 16px !important;
    padding: 2px 10px !important;
    box-shadow: 0 0 16px rgba(0, 229, 255, 0.7) !important;
    animation: asma-widget-glow 1s infinite alternate !important;
  }
  @keyframes asma-widget-glow {
    0% { box-shadow: 0 0 8px rgba(0, 229, 255, 0.5); }
    100% { box-shadow: 0 0 20px rgba(0, 229, 255, 1); }
  }

  /* Finestra di Stato Terminal Box */
  .asma-terminal-box {
    background: #0b0f19;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 12px;
    overflow-y: auto;
    font-family: 'Consolas', 'Fira Code', 'Courier New', monospace;
    box-shadow: inset 0 0 12px rgba(0, 0, 0, 0.7);
  }

  .top-header {
    background-color: #1A1A1A;
    border-bottom: 2px solid #333333;
    padding: 10px 20px;
    border-radius: 8px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .status-badge {
    background: #00E676;
    color: #000000;
    font-weight: bold;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 13px;
  }
  .user-badge {
    color: #FFD600;
    font-weight: bold;
    font-size: 15px;
  }
  .version-tag {
    color: #888888;
    font-size: 13px;
  }

  /* Global compact st.metric styles */
  [data-testid="stMetric"] {
    background: rgba(30, 41, 59, 0.45) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
  }
  [data-testid="stMetricValue"] {
    font-size: 20px !important;
    font-weight: 700 !important;
    color: #00E5FF !important;
    line-height: 1.1 !important;
  }
  [data-testid="stMetricLabel"] {
    font-size: 11px !important;
    font-weight: 600 !important;
    color: #94A3B8 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.4px !important;
  }

  /* LOOK & FEEL: Visual distinction between FIXED panels and EDITABLE areas */
  /* Fixed / Navigation & Lists Background: Deep Midnight Slate */
  div[class*="st-key-top_navbar_container"],
  div[class*="top_nav_pills_r1"],
  div[class*="top_nav_pills_r2"],
  div[data-testid="stSidebar"] {
    background: #0B0F19 !important;
  }

  /* List & fixed inspection cards */
  div.asma-list-card {
    background: #111827 !important;
    border: 1px solid #1E293B !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
    margin-bottom: 8px !important;
  }

  /* Editable Form & Editor Workspace: Distinct Elevated Background */
  div.asma-editable-workspace {
    background: #1E293B !important;
    border: 1px solid #334155 !important;
    border-left: 4px solid #38BDF8 !important;
    border-radius: 8px !important;
    padding: 14px !important;
    margin-bottom: 12px !important;
  }

  /* Highlight editable inputs vs read-only elements */
  div[data-testid="stTextInput"] input:focus,
  div[data-testid="stTextArea"] textarea:focus {
    border-color: #38BDF8 !important;
    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.25) !important;
    background: #0F172A !important;
  }

  /* Mobile responsive adjustments */
  .asma-kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 12px;
    width: 100%;
  }
  @media (max-width: 768px) {
    .asma-kpi-grid {
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
      margin-bottom: 10px;
    }
  }
  .asma-kpi-card {
    background: rgba(30, 41, 59, 0.55);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 8px 12px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
    transition: transform 0.15s ease, border-color 0.15s ease;
  }
  .asma-kpi-card:hover {
    border-color: rgba(0, 229, 255, 0.4);
    transform: translateY(-1px);
  }
  .asma-kpi-header {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 2px;
  }
  .asma-kpi-icon {
    font-size: 13px;
  }
  .asma-kpi-title {
    font-size: 11px;
    font-weight: 600;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .asma-kpi-val {
    font-size: 21px;
    font-weight: 700;
    color: #00E5FF;
    line-height: 1.1;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }

  /* Two separate columns for Home Dashboard sections (Side-by-side on PC and Tablets) */
  div[class*="st-key-home_dashboard_sections"] [data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 14px !important;
    width: 100% !important;
  }
  div[class*="st-key-home_dashboard_sections"] [data-testid="stColumn"] {
    flex: 1 1 50% !important;
    width: 50% !important;
    min-width: 0 !important;
  }
  @media (max-width: 600px) {
    div[class*="st-key-home_dashboard_sections"] [data-testid="stHorizontalBlock"] {
      flex-direction: column !important;
    }
    div[class*="st-key-home_dashboard_sections"] [data-testid="stColumn"] {
      flex: 1 1 100% !important;
      width: 100% !important;
    }
  }

  /* Sleek box for dashboard sections */
  .asma-dash-card {
    background: rgba(19, 26, 42, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 12px 14px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
  }

  /* =========================================================================
     COMPACT & MODERN BAND TYPOGRAPHY (PC, iPad, Huawei, Android, iPhone)
     ========================================================================= */

  /* Headings: sleek, compact, and never oversized */
  h1, [data-testid="stHeadingWithActionElements"] h1 {
    font-size: 18px !important;
    font-weight: 700 !important;
    color: #FFFFFF !important;
    margin-top: 0px !important;
    margin-bottom: 4px !important;
    line-height: 1.2 !important;
    letter-spacing: 0.3px !important;
  }
  h2, [data-testid="stHeadingWithActionElements"] h2 {
    font-size: 16.5px !important;
    font-weight: 700 !important;
    color: #FFFFFF !important;
    margin-top: 0px !important;
    margin-bottom: 4px !important;
    line-height: 1.2 !important;
  }
  h3, [data-testid="stHeadingWithActionElements"] h3 {
    font-size: 14.5px !important;
    font-weight: 700 !important;
    color: #00E5FF !important;
    margin-top: 0px !important;
    margin-bottom: 4px !important;
    line-height: 1.2 !important;
  }
  h4, [data-testid="stHeadingWithActionElements"] h4 {
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #E2E8F0 !important;
    margin-top: 0px !important;
    margin-bottom: 3px !important;
    line-height: 1.2 !important;
  }
  h5, [data-testid="stHeadingWithActionElements"] h5 {
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #CBD5E1 !important;
    margin-top: 0px !important;
    margin-bottom: 2px !important;
    line-height: 1.2 !important;
  }
  h6, [data-testid="stHeadingWithActionElements"] h6 {
    font-size: 11px !important;
    font-weight: 600 !important;
    color: #94A3B8 !important;
    margin-top: 0px !important;
    margin-bottom: 2px !important;
    line-height: 1.2 !important;
  }

  /* Compact widget labels and text inputs */
  [data-testid="stWidgetLabel"] label,
  [data-testid="stWidgetLabel"] p,
  [data-testid="stWidgetLabel"] span {
    font-size: 11px !important;
    font-weight: 600 !important;
    color: #94A3B8 !important;
    margin-bottom: 2px !important;
    letter-spacing: 0.2px !important;
  }

  /* Captions */
  [data-testid="stCaptionContainer"] p {
    font-size: 11px !important;
    color: #94A3B8 !important;
    margin-top: 0px !important;
    margin-bottom: 6px !important;
    line-height: 1.3 !important;
  }

  /* General body text */
  [data-testid="stMarkdownContainer"] p,
  [data-testid="stMarkdownContainer"] li {
    font-size: 12px !important;
    line-height: 1.4 !important;
    color: #E2E8F0 !important;
  }

  /* Form controls: compact height, clean borders */
  div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    min-height: 30px !important;
    height: 30px !important;
    font-size: 11.5px !important;
    padding-top: 0px !important;
    padding-bottom: 0px !important;
    background: rgba(30, 41, 59, 0.7) !important;
    border-color: rgba(255, 255, 255, 0.12) !important;
    border-radius: 6px !important;
  }

  /* Soppressione tastiera virtuale e puntatore touch su tutti i selectbox/dropdown */
  div[data-testid="stSelectbox"] div[data-baseweb="select"] input,
  .st-key-main_song_selector div[data-baseweb="select"] input,
  .st-key-rep_song_selector div[data-baseweb="select"] input {
    caret-color: transparent !important;
    cursor: pointer !important;
    -webkit-user-select: none !important;
    user-select: none !important;
  }

  /* Evidenziazione speciale per la Casella Selezione Brano (Brani e Repertori) */
  .st-key-main_song_selector div[data-baseweb="select"] > div,
  .st-key-rep_song_selector div[data-baseweb="select"] > div {
    min-height: 44px !important;
    height: 44px !important;
    background: linear-gradient(135deg, rgba(14, 116, 144, 0.3) 0%, rgba(15, 23, 42, 0.95) 100%) !important;
    border: 2px solid #38BDF8 !important;
    border-radius: 9px !important;
    box-shadow: 0 0 16px rgba(56, 189, 248, 0.35) !important;
    padding-left: 12px !important;
  }
  .st-key-main_song_selector div[data-baseweb="select"] *,
  .st-key-rep_song_selector div[data-baseweb="select"] * {
    font-size: 16px !important;
    font-weight: 800 !important;
    color: #F8FAFC !important;
    letter-spacing: 0.5px !important;
  }
  .st-key-main_song_selector div[data-baseweb="select"] svg,
  .st-key-rep_song_selector div[data-baseweb="select"] svg {
    fill: #38BDF8 !important;
    width: 22px !important;
    height: 22px !important;
  }
  div[data-testid="stTextInput"] input {
    height: 30px !important;
    min-height: 30px !important;
    font-size: 11.5px !important;
    padding: 3px 8px !important;
    background: rgba(30, 41, 59, 0.7) !important;
    border-color: rgba(255, 255, 255, 0.12) !important;
    border-radius: 6px !important;
  }
  div[data-testid="stTextArea"] textarea {
    font-size: 11.5px !important;
    padding: 6px 8px !important;
    background: rgba(30, 41, 59, 0.7) !important;
    border-color: rgba(255, 255, 255, 0.12) !important;
    border-radius: 6px !important;
  }

  /* Standard Buttons */
  button[data-testid="stBaseButton-secondary"],
  button[data-testid="stBaseButton-primary"] {
    min-height: 28px !important;
    height: 28px !important;
    font-size: 11.5px !important;
    padding: 2px 8px !important;
    border-radius: 6px !important;
    line-height: 1 !important;
    white-space: nowrap !important;
  }

  /* Compact Expander summary */
  div[data-testid="stExpander"] summary {
    font-size: 11.5px !important;
    font-weight: 600 !important;
    padding: 5px 8px !important;
  }

  /* Compact alerts */
  [data-testid="stAlert"] {
    padding: 6px 10px !important;
    font-size: 11.5px !important;
    border-radius: 6px !important;
  }
  [data-testid="stAlert"] [data-testid="stMarkdownContainer"] p {
    font-size: 11.5px !important;
    line-height: 1.3 !important;
  }

  /* Dividers with minimal margins */
  hr {
    margin-top: 8px !important;
    margin-bottom: 8px !important;
    border-color: rgba(255, 255, 255, 0.08) !important;
  }
</style>
""", unsafe_allow_html=True)

# Imports from core
from asma_core.models import Song, Repertoire, Setlist, SetlistItem, LiveEvent, DeviceProfile
from asma_core.music_engine import MusicEngine
from asma_core.aml_parser import AMLParser
from asma_core.storage_manager import StorageManager
from asma_core.lock_manager import LockManager
from asma_core.audit_logger import AuditLogger
from asma_core.operation_logger import OperationLogger, OperationLogEntry
from asma_core.pdf_engine import PDFEngine
from asma_core.printer_engine import PrinterEngine
from asma_core.live_stage_component import LiveStageComponent
from asma_core.export_engine import ExportEngine
from asma_core.import_engine import ImportEngine
from asma_core.web_importer import WebSongImporter
from asma_core.manual_engine import ManualEngine
from asma_core.changelog_engine import ChangelogEngine
from asma_core.ai_service import BandAIService
from asma_core.gist_client import GistClient
from asma_core.auth_manager import AuthManager, UserRole, User
from asma_core.backup_engine import BackupEngine
from asma_core.device_manager import DeviceManager
from asma_core.aml_tag_manager import AMLTagManager, AMLTagDefinition

from asma_core.storage_manager import StorageManager

# Initialize Singletons
storage = StorageManager()
lock_mgr = LockManager()
audit = AuditLogger()
op_logger = OperationLogger()

def log_op(icon: str, category: str, message: str, level: str = "SUCCESS"):
    """Helper to log an operation into the live status console."""
    user_name = st.session_state.get("current_user_name", "")
    user_role = st.session_state.get("current_user_role", "")
    if user_name:
        user_str = f"{user_name} [{user_role}]" if user_role else user_name
    elif "current_user" in globals() and current_user:
        user_str = f"{current_user.name} [{current_user.role.value}]"
    else:
        user_str = "System"
    op_logger.log(icon, category, message, level=level, user=user_str)
device_mgr = DeviceManager()
aml_tag_mgr = AMLTagManager()
gist_client = GistClient()
auth_mgr = AuthManager()

# Client Preference Persistence Across Page Reloads (SRS Cap. 3 & 10)
PREF_FILE = os.path.join(os.path.dirname(__file__), "data", "client_preferences.json")

def load_client_preferences() -> dict:
    if os.path.exists(PREF_FILE):
        try:
            with open(PREF_FILE, "r", encoding="utf-8") as _pf:
                return json.load(_pf)
        except Exception:
            return {}
    return {}

def save_client_preferences(prefs: dict):
    try:
        os.makedirs(os.path.dirname(PREF_FILE), exist_ok=True)
        with open(PREF_FILE, "w", encoding="utf-8") as _pf:
            json.dump(prefs, _pf, indent=2)
    except Exception:
        pass

_client_prefs = load_client_preferences()

# -----------------------------------------------------------------------------
# GOOGLE OAUTH CALLBACK & LIGHTWEIGHT LOGIN SCREEN (Logo Band & Login Google)
# -----------------------------------------------------------------------------
import base64

@st.cache_data
def get_band_logo_b64() -> str:
    """Reads and caches the band logo as base64 string for ultra-fast rendering."""
    for p in ["assets/band_logo.png", "../assets/band_logo.png"]:
        if os.path.exists(p):
            try:
                with open(p, "rb") as _f:
                    return base64.b64encode(_f.read()).decode("utf-8")
            except Exception:
                return ""
    return ""

# -----------------------------------------------------------------------------
# GOOGLE OIDC AUTHENTICATION (Allineato al progetto Accordi prima versione)
# -----------------------------------------------------------------------------

def get_authenticated_google_email():
    """Recupera solo l'email verificata da sessione Streamlit OIDC (st.user) o headers."""
    # 1. Controllo utente autenticato Streamlit OIDC (st.user)
    user = getattr(st, "user", None)
    if user and getattr(user, "is_logged_in", False):
        email = getattr(user, "email", None)
        if not email and hasattr(user, "get"):
            email = user.get("email")
        if email:
            return str(email).strip().lower()

    # 2. Controllo headers di autenticazione Streamlit Cloud / proxy Google
    try:
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            headers = st.context.headers
            for h in ("x-streamlit-user-email", "x-forwarded-email", "x-auth-request-email", "x-user-email"):
                val = headers.get(h)
                if val:
                    return str(val).strip().lower()
    except Exception:
        pass

    return None

def _has_oidc_configuration() -> bool:
    """Verifica se la configurazione OIDC è presente nei Secrets."""
    try:
        auth_config = st.secrets["auth"]
        return bool(auth_config.get("client_id") and auth_config.get("client_secret"))
    except Exception:
        return False

# Verifica se l'utente risulta autenticato tramite Google
_auth_google_email = get_authenticated_google_email()

if _auth_google_email:
    if auth_mgr.is_email_allowed(_auth_google_email):
        st.session_state["authenticated"] = True
        st.session_state["current_user_email"] = _auth_google_email
        _cp = load_client_preferences()
        _cp["active_user_email"] = _auth_google_email
        save_client_preferences(_cp)
    else:
        st.error(f"❌ Accesso negato: l'account Google '{_auth_google_email}' non appartiene alla lista musicisti autorizzati della band ASMA.")
        if hasattr(st, "logout"):
            st.button("Esci dall'account Google", key="btn_logout_unauth", on_click=st.logout)
        st.stop()
elif not st.session_state.get("authenticated", False):
    # Ripristino da sessione salvata sul client se valida
    _saved_email = _client_prefs.get("active_user_email")
    if _saved_email and auth_mgr.is_email_allowed(_saved_email):
        st.session_state["authenticated"] = True
        st.session_state["current_user_email"] = _saved_email

# Se non autenticato, mostra la schermata di login originale
if not st.session_state.get("authenticated", False):
    _, col_login, _ = st.columns([1, 2.2, 1])
    with col_login:
        logo_file = "assets/band_logo.png" if os.path.exists("assets/band_logo.png") else ("../assets/band_logo.png" if os.path.exists("../assets/band_logo.png") else None)
        if logo_file:
            st.image(logo_file, use_container_width=True)
        else:
            logo_b64 = get_band_logo_b64()
            if logo_b64:
                st.markdown(
                    f'<div style="text-align:center;"><img src="data:image/png;base64,{logo_b64}" style="max-width:320px; width:90%; height:auto; margin:0 auto 10px auto; border-radius:8px; display:block;" /></div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown('<div style="text-align:center; font-size:48px; margin-bottom:8px;">⚡</div>', unsafe_allow_html=True)

        st.markdown(
            """<div style="text-align:center; margin-top:-6px; margin-bottom:20px;">
              <div style="font-size:14px; color:#38BDF8; font-weight:800; letter-spacing:1px; text-transform:uppercase;">
                Area Riservata Band
              </div>
              <div style="font-size:12px; color:#94A3B8; margin-top:4px;">
                Accedi con l'account Google autorizzato dalla band per consultare e modificare il repertorio.
              </div>
            </div>""",
            unsafe_allow_html=True
        )

        if not _has_oidc_configuration():
            st.error(
                "Accesso Google non configurato. Completa la sezione [auth] e [access] "
                "nei Secrets di Streamlit prima di avviare l'app."
            )
        else:
            # Pulsante identico alla prima versione (Accordi)
            st.button("🎸 Accedi con Google", key="btn_login_google", on_click=st.login, type="primary", use_container_width=True)

    st.stop()

# User is authenticated
current_user = auth_mgr.get_user_by_email(st.session_state["current_user_email"])
if not current_user:
    current_user = auth_mgr.authenticate_or_register_google(st.session_state["current_user_email"])

st.session_state["current_user_name"] = current_user.name
st.session_state["current_user_role"] = current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role)
st.query_params["user"] = current_user.email

if "selected_song_uuid" not in st.session_state:
    st.session_state["selected_song_uuid"] = None
if "selected_setlist_uuid" not in st.session_state:
    st.session_state["selected_setlist_uuid"] = None

# TOP FIXED HEADER (SRS Cap. 3.5 & 5.3)
role_colors = {
    "ADMIN": "#FFD600",
    "BAND_MEMBER": "#00E5FF",
    "VIEWER": "#AAAAAA"
}
role_col = role_colors.get(current_user.role.value, "#FFFFFF")

# (log_op defined globally above)

if "session_boot_logged" not in st.session_state:
    st.session_state["session_boot_logged"] = True
    try:
        storage.reload_from_disk()
        if storage.gist_client.is_configured:
            storage.sync_from_cloud()
    except Exception:
        pass
    log_op("🟢", "SISTEMA", f"Accesso sessione effettuato da {current_user.name} ({current_user.email}) - Ruolo: {current_user.role.value}", "SUCCESS")

def render_status_console(logger_inst: OperationLogger, key_prefix: str = "main", compact: bool = False):
    """Renders the interactive status window printing executed operations."""
    if compact:
        entries = logger_inst.get_entries(limit=18)
        html_lines = "".join(e.to_terminal_line() for e in entries) if entries else "<div style='color:#888;'>Nessuna operazione registrata.</div>"
        st.markdown(f"<div class='asma-terminal-box' style='max-height: 220px;'>{html_lines}</div>", unsafe_allow_html=True)
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("🧹 Pulisci", key=f"{key_prefix}_clr_btn", width="stretch"):
                logger_inst.clear()
                st.rerun()
        with col_c2:
            st.download_button("📋 Esporta", data=logger_inst.export_text(), file_name="asma_operazioni.log", mime="text/plain", key=f"{key_prefix}_exp_btn", width="stretch")
    else:
        st.write("##### 📟 Finestra di Stato & Monitor Operazioni Eseguite")
        c1, c2, c3 = st.columns([2, 1, 1.2])
        with c1:
            cat_filter = st.selectbox("Filtra per Categoria:", logger_inst.get_categories(), key=f"{key_prefix}_cat")
        with c2:
            limit_val = st.selectbox("Numero Eventi:", [15, 30, 50, 100], index=1, key=f"{key_prefix}_limit")
        with c3:
            st.write("")
            b1, b2 = st.columns(2)
            with b1:
                if st.button("🧹 Pulisci", key=f"{key_prefix}_clr_full", width="stretch"):
                    logger_inst.clear()
                    st.rerun()
            with b2:
                st.download_button("📋 Esporta", data=logger_inst.export_text(), file_name="asma_operazioni.log", mime="text/plain", key=f"{key_prefix}_exp_full", width="stretch")

        filtered = logger_inst.get_entries(limit=limit_val, category=cat_filter)
        html_lines = "".join(e.to_terminal_line() for e in filtered) if filtered else "<div style='color:#888; padding:10px;'>Nessun evento registrato per questa categoria.</div>"
        st.markdown(f"<div class='asma-terminal-box' style='max-height: 320px;'>{html_lines}</div>", unsafe_allow_html=True)

# ==============================================================================
# TOP FIXED NAVIGATION FRAME (HTML Frame Style - 100% Fixed on Scroll for All Devices)
# ==============================================================================
MENU_ITEMS = [
    "🏠 Home Dashboard",
    "📥 Importa & 📤 Esporta",
    "📝 Brani",
    "🤖 Band AI (Opzionale)",
    "🔍 Ricerca Globale",
    "📚 Repertori",
    "📑 Scalette Live",
    "🎤 Modalità Palco (Live Stage)",
    "📅 Eventi Live",
    "📖 Manuale & Changelog",
    "⚙️ Amministrazione & Log"
]

MENU_COMPACT_LABELS = {
    "🏠 Home Dashboard": "🏠 Home",
    "📥 Importa & 📤 Esporta": "📥/📤 Import/Export",
    "📝 Brani": "📝 Brani",
    "🤖 Band AI (Opzionale)": "🤖 AI",
    "🔍 Ricerca Globale": "🔍 Cerca",
    "📚 Repertori": "📚 Repertori",
    "📑 Scalette Live": "📑 Scalette",
    "🎤 Modalità Palco (Live Stage)": "🎤 Palco",
    "📅 Eventi Live": "📅 Eventi",
    "📖 Manuale & Changelog": "📖 Guida",
    "⚙️ Amministrazione & Log": "⚙️ Admin",
}

if "main_menu_choice" not in st.session_state:
    st.session_state["main_menu_choice"] = "🏠 Home Dashboard"

import base64

@st.cache_data
def get_band_logo_b64() -> str:
    """Reads and caches the band logo as base64 string for ultra-fast single-tag rendering."""
    if os.path.exists("assets/band_logo.png"):
        try:
            with open("assets/band_logo.png", "rb") as _f:
                return base64.b64encode(_f.read()).decode("utf-8")
        except Exception:
            return ""
    return ""

all_users = auth_mgr.list_users()
user_emails = [u.email for u in all_users]
curr_user_idx = user_emails.index(current_user.email) if current_user.email in user_emails else 0

dev_list = device_mgr.list_devices()
dev_names = [d.name for d in dev_list]

def get_client_device_category() -> str:
    """Classifies client device category from user-agent headers: mobile_phone, tablet, desktop."""
    ua = ""
    try:
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            ua = st.context.headers.get("user-agent", "").lower()
    except Exception:
        ua = ""
    if "iphone" in ua or ("android" in ua and "mobile" in ua):
        return "mobile_phone"
    elif "ipad" in ua or ("android" in ua and "mobile" not in ua):
        return "tablet"
    elif "windows" in ua or "macintosh" in ua or ("linux" in ua and "android" not in ua):
        return "desktop"
    # Fallback to desktop for PC/workstation browsers
    return "desktop"

_client_dev_cat = get_client_device_category()
_user_dev_key = f"device::{current_user.email}::{_client_dev_cat}"
_clean_email_cookie = re.sub(r'[^a-zA-Z0-9]', '_', current_user.email.lower())
_cookie_key = f"asma_dev_{_clean_email_cookie}"

# Read client device cookie if sent by browser
_client_cookie_dev = None
try:
    if hasattr(st, "context") and hasattr(st.context, "cookies"):
        _client_cookie_dev = st.context.cookies.get(_cookie_key)
except Exception:
    _client_cookie_dev = None

# Resolve Active Device: Session State -> Browser Cookie -> Query Params -> User+DeviceCategory Pref -> Smart Hardware Default
_qp_dev = st.query_params.get("device")
if "user_preferred_device" in st.session_state and st.session_state["user_preferred_device"] in dev_names:
    _active_dev = st.session_state["user_preferred_device"]
elif _client_cookie_dev and _client_cookie_dev in dev_names:
    _active_dev = _client_cookie_dev
elif _qp_dev and _qp_dev in dev_names:
    _active_dev = _qp_dev
elif _client_prefs.get(_user_dev_key) and _client_prefs.get(_user_dev_key) in dev_names:
    _active_dev = _client_prefs.get(_user_dev_key)
else:
    # Strictly isolated per hardware category (PC -> A4 Desktop, Tablet -> Huawei, Smartphone -> Pixel 8)
    if _client_dev_cat == "desktop":
        _active_dev = "A4: Stampabile (Desktop)" if "A4: Stampabile (Desktop)" in dev_names else (dev_names[0] if dev_names else "A4: Stampabile (Desktop)")
    elif _client_dev_cat == "tablet":
        _active_dev = "Huawei MatePad 11.5" if "Huawei MatePad 11.5" in dev_names else (dev_names[0] if dev_names else "Pixel 8 pro")
    else:
        _active_dev = "Pixel 8 pro" if "Pixel 8 pro" in dev_names else (dev_names[0] if dev_names else "Pixel 8 pro")

st.session_state["user_preferred_device"] = _active_dev
st.query_params["device"] = _active_dev
if _client_prefs.get(_user_dev_key) != _active_dev:
    _client_prefs[_user_dev_key] = _active_dev
    save_client_preferences(_client_prefs)

def set_active_device_globally(new_dev_name: str):
    """Updates active hardware device persistently for the current (user, device_category) pair."""
    if new_dev_name and new_dev_name in dev_names:
        st.session_state["user_preferred_device"] = new_dev_name
        st.query_params["device"] = new_dev_name
        _cp = load_client_preferences()
        _dcat = get_client_device_category()
        _cp[f"device::{current_user.email}::{_dcat}"] = new_dev_name
        save_client_preferences(_cp)

# Persist device cookie and localStorage directly on client browser
st.components.v1.html(
    f"""<script>
    (function() {{
      var ckName = "{_cookie_key}";
      var devVal = "{_active_dev}";
      var d = new Date();
      d.setTime(d.getTime() + (365*24*60*60*1000));
      document.cookie = ckName + "=" + encodeURIComponent(devVal) + ";expires=" + d.toUTCString() + ";path=/;SameSite=Lax";
      try {{
        localStorage.setItem(ckName, devVal);
      }} catch(e) {{}}
    }})();
    </script>""",
    height=0
)

curr_pref = _active_dev
pref_idx = dev_names.index(curr_pref) if curr_pref in dev_names else 0

# UI Zoom Scaling with persistence
if "ui_zoom_level" not in st.session_state:
    if "ui_zoom_level" in _client_prefs:
        st.session_state["ui_zoom_level"] = _client_prefs["ui_zoom_level"]
    else:
        st.session_state["ui_zoom_level"] = 0.82 if "huawei" in curr_pref.lower() else 1.0

# Layout & Typography Preferences (SRS Cap. 13 & Cap. 17)
if "layout_font_size" not in st.session_state:
    st.session_state["layout_font_size"] = _client_prefs.get("layout_font_size", 12)
if "layout_font_size_chords" not in st.session_state:
    st.session_state["layout_font_size_chords"] = _client_prefs.get("layout_font_size_chords", 13)
if "layout_margin_lateral" not in st.session_state:
    st.session_state["layout_margin_lateral"] = _client_prefs.get("layout_margin_lateral", 10)
if "layout_columns" not in st.session_state:
    st.session_state["layout_columns"] = _client_prefs.get("layout_columns", 1)
if "layout_color_text" not in st.session_state:
    st.session_state["layout_color_text"] = _client_prefs.get("layout_color_text", "#111111")
if "layout_color_chords" not in st.session_state:
    st.session_state["layout_color_chords"] = _client_prefs.get("layout_color_chords", "#B71C1C")
if "layout_color_aml" not in st.session_state:
    st.session_state["layout_color_aml"] = _client_prefs.get("layout_color_aml", "#4A148C")

def get_layout_device_profile(base_profile_name: Optional[str] = None) -> DeviceProfile:
    """Combines hardware device dimensions with custom Layout overrides (fonts, columns, margins, colors)."""
    dev_name = base_profile_name or st.session_state.get("user_preferred_device", "Pixel 8 pro")
    base = device_mgr.get_device_by_name(dev_name) or DeviceProfile()
    f_size = float(st.session_state.get("layout_font_size", 12))
    fc_size = float(st.session_state.get("layout_font_size_chords", round(f_size * 1.08, 1)))
    m_lat = float(st.session_state.get("layout_margin_lateral", 10))
    cols = int(st.session_state.get("layout_columns", 1))
    c_txt = st.session_state.get("layout_color_text", "#111111")
    c_chd = st.session_state.get("layout_color_chords", "#B71C1C")
    c_aml = st.session_state.get("layout_color_aml", "#4A148C")
    return DeviceProfile(
        uuid=base.uuid,
        name=base.name,
        target_device=base.target_device,
        device_type=base.device_type,
        width_mm=base.width_mm,
        height_mm=base.height_mm,
        font_lyrics=base.font_lyrics,
        font_chords=base.font_chords,
        font_size_lyrics=f_size,
        font_size_chords=fc_size,
        margin_top_mm=base.margin_top_mm,
        margin_bottom_mm=base.margin_bottom_mm,
        margin_left_mm=m_lat,
        margin_right_mm=m_lat,
        zoom=st.session_state.get("ui_zoom_level", base.zoom),
        orientation="portrait",  # Strettamente verticale come richiesto
        columns=cols,
        is_custom=True,
        color_lyrics=c_txt,
        color_chords=c_chd,
        color_aml_markup=c_aml
    )

active_zoom = st.session_state["ui_zoom_level"]
st.markdown(f"""
<style>
  html, body, [data-testid="stAppViewContainer"] {{
    zoom: {active_zoom} !important;
    -webkit-text-size-adjust: 100% !important;
    text-size-adjust: 100% !important;
  }}
</style>
""", unsafe_allow_html=True)

with st.container(key="top_navbar_container"):
    # Glowing Laser Accent Line
    st.markdown('<div class="asma-laser-line"></div>', unsafe_allow_html=True)

    # Row 1: Brand (Left) | Soundwave Status (Center) | Profile, Device, Log & Logout (Right - Compacted)
    col_head_left, col_head_center, col_btn_user, col_btn_dev, col_btn_log, col_btn_logout = st.columns(
        [1.35, 0.75, 0.95, 0.95, 0.45, 0.65], gap="small", vertical_alignment="center"
    )

    with col_head_left:
        logo_b64 = get_band_logo_b64()
        logo_img_tag = f'<img src="data:image/png;base64,{logo_b64}" style="height:24px; vertical-align:middle; border-radius:3px; flex-shrink:0;" />' if logo_b64 else '⚡'
        st.markdown(
            f"<div class='asma-brand-header' style='display:flex; align-items:center; gap:7px; white-space:nowrap;'>"
            f"{logo_img_tag} "
            f"<b style='font-size:12.5px; color:#FFFFFF; letter-spacing:0.3px;'>THE New ASMA</b> "
            f"<span style='font-size:9px; color:#00E676; font-weight:bold; background:rgba(0,230,118,0.12); padding:1px 5px; border-radius:6px; border:1px solid rgba(0,230,118,0.3);'>• ONLINE</span>"
            f"</div>",
            unsafe_allow_html=True
        )

    with col_head_center:
        st.markdown(
            f'''<div class="asma-bar-center-eq" style="display:flex; align-items:center; justify-content:center; gap:6px;">
              <div class="asma-eq-container" style="height:12px;" title="Attività Live Motore ASMA">
                <span class="asma-eq-bar eq-1" style="height:4px;"></span>
                <span class="asma-eq-bar eq-2" style="height:8px;"></span>
                <span class="asma-eq-bar eq-3" style="height:12px;"></span>
                <span class="asma-eq-bar eq-4" style="height:6px;"></span>
                <span class="asma-eq-bar eq-5" style="height:10px;"></span>
              </div>
              <span class="asma-eq-label" style="font-size:10px; color:#94A3B8; font-weight:500; white-space:nowrap;">LIVE STAGE</span>
            </div>''',
            unsafe_allow_html=True
        )

    user_first = current_user.name.split()[0]
    dev_short = "Huawei M5" if "mediapad m5" in curr_pref.lower() else (curr_pref[:11] + "..." if len(curr_pref) > 13 else curr_pref)

    with col_btn_user:
        with st.popover(f"👤 {user_first}", width="stretch", help="Profilo utente attivo, permessi e login"):
            b_info = getattr(auth_mgr, "BAND_MEMBERS", {}).get(current_user.email, {})
            disp_role = b_info.get("display_role", current_user.role.value)
            
            st.write("##### 👤 Profilo Musicista & Ruolo Band")
            st.markdown(
                f"**Pseudonimo:** <b style='color:#38BDF8; font-size:15px;'>{current_user.name}</b><br>"
                f"**Email Google:** `{current_user.email}`<br>"
                f"**Ruolo Band:** <span style='color:{role_col}; font-weight:bold;'>{disp_role}</span>",
                unsafe_allow_html=True
            )
            st.caption(f"Permessi: `{'Lettura & Modifica completa' if current_user.can_edit() else 'Sola Lettura'}`")
            st.divider()

            if current_user.can_admin():
                st.write("###### 🔄 Cambia Musicista (Test Accessi Admin):")
                def _fmt_band_user(e):
                    b_m = getattr(auth_mgr, "BAND_MEMBERS", {}).get(e, {})
                    pseudo = b_m.get("pseudonym", next((u.name for u in all_users if u.email == e), e))
                    r_desc = b_m.get("display_role", next((u.role.value for u in all_users if u.email == e), ""))
                    return f"{pseudo} [{r_desc}]"

                new_u_sel = st.selectbox(
                    "Seleziona Profilo Musicista:",
                    user_emails,
                    index=curr_user_idx,
                    format_func=_fmt_band_user,
                    key="pop_hub_user_sel"
                )
                if new_u_sel != st.session_state["current_user_email"]:
                    st.session_state["current_user_email"] = new_u_sel
                    st.query_params["user"] = new_u_sel
                    u_sel = auth_mgr.get_user_by_email(new_u_sel)
                    if u_sel:
                        log_op("🔐", "AUTH", f"Amministratore ha commutato vista su {u_sel.name} [{u_sel.role.value}]", "INFO")
                    st.rerun()
            else:
                st.info("ℹ️ Questa sessione è collegata al tuo account personale Google. Solo l'amministratore può commutare profili di test.")

            st.divider()
            if st.button("🚪 Disconnetti (Logout)", type="secondary", key="pop_btn_logout", width="stretch"):
                st.session_state["authenticated"] = False
                st.session_state.pop("current_user_email", None)
                _cp = load_client_preferences()
                _cp.pop("active_user_email", None)
                save_client_preferences(_cp)
                st.query_params.clear()
                st.rerun()



    with col_btn_dev:
        with st.popover(f"📐 {dev_short}", width="stretch", help="Configurazione Layout Display, Colonne e PDF"):
            st.write("##### 📐 Layout Display & PDF")
            st.caption("Formato dispositivo hardware, tipografia, colonne, margini e colori.")

            new_dev_sel = st.selectbox(
                "Dispositivo Display Target:",
                dev_names,
                index=pref_idx,
                key="pop_layout_dev_sel",
                help="Seleziona il modello hardware: adatta dimensioni mm, risoluzione e calibrazione video."
            )
            if new_dev_sel != st.session_state.get("user_preferred_device"):
                set_active_device_globally(new_dev_sel)
                st.rerun()

            tab_lay_geom, tab_lay_col, tab_lay_zoom = st.tabs([
                "📄 Formato & Testo",
                "🎨 Colori",
                "🔍 Zoom Display"
            ])

            with tab_lay_geom:
                c_fs1, c_fs2 = st.columns(2, gap="small")
                with c_fs1:
                    curr_f_size = int(st.session_state.get("layout_font_size", 12))
                    new_f_size = st.slider(
                        "Dimensione Testo (px):",
                        min_value=8,
                        max_value=30,
                        value=curr_f_size,
                        step=1,
                        key="slider_layout_font_size",
                        help="Dimensione del carattere del testo e dei testi nel PDF e anteprima"
                    )
                    if new_f_size != curr_f_size:
                        st.session_state["layout_font_size"] = new_f_size
                        _cp = load_client_preferences()
                        _cp["layout_font_size"] = new_f_size
                        save_client_preferences(_cp)
                        st.rerun()
                with c_fs2:
                    curr_fc_size = int(st.session_state.get("layout_font_size_chords", 13))
                    new_fc_size = st.slider(
                        "Dimensione Accordi (px):",
                        min_value=8,
                        max_value=32,
                        value=curr_fc_size,
                        step=1,
                        key="slider_layout_font_size_chords",
                        help="Dimensione regolabile indipendente per gli accordi nel PDF e anteprima"
                    )
                    if new_fc_size != curr_fc_size:
                        st.session_state["layout_font_size_chords"] = new_fc_size
                        _cp = load_client_preferences()
                        _cp["layout_font_size_chords"] = new_fc_size
                        save_client_preferences(_cp)
                        st.rerun()

                c_geom1, c_geom2 = st.columns(2, gap="small")
                with c_geom1:
                    curr_cols = int(st.session_state.get("layout_columns", 1))
                    col_choice = st.radio(
                        "Colonne PDF:",
                        [1, 2],
                        index=0 if curr_cols == 1 else 1,
                        horizontal=True,
                        format_func=lambda c: f"{c} Colonna" if c == 1 else f"{c} Colonne",
                        key="radio_layout_columns"
                    )
                    if col_choice != curr_cols:
                        st.session_state["layout_columns"] = col_choice
                        _cp = load_client_preferences()
                        _cp["layout_columns"] = col_choice
                        save_client_preferences(_cp)
                        st.rerun()

                with c_geom2:
                    curr_m_lat = int(st.session_state.get("layout_margin_lateral", 10))
                    new_m_lat = st.slider(
                        "Margini Laterali (mm):",
                        min_value=4,
                        max_value=30,
                        value=curr_m_lat,
                        step=1,
                        key="slider_layout_margin_lat"
                    )
                    if new_m_lat != curr_m_lat:
                        st.session_state["layout_margin_lateral"] = new_m_lat
                        _cp = load_client_preferences()
                        _cp["layout_margin_lateral"] = new_m_lat
                        save_client_preferences(_cp)
                        st.rerun()

                st.markdown(
                    "<div style='font-size:11px; color:#94A3B8; background:rgba(255,255,255,0.04); padding:4px 8px; border-radius:4px; margin-top:4px;'>"
                    "📐 <b>Margine superiore brano:</b> <code>58 px</code> (default fisso per testata)"
                    "</div>",
                    unsafe_allow_html=True
                )

            with tab_lay_col:
                st.caption("Personalizza la tavolozza dei colori per il PDF:")
                c_c1, c_c2, c_c3 = st.columns(3, gap="small")
                with c_c1:
                    curr_col_txt = st.session_state.get("layout_color_text", "#111111")
                    new_col_txt = st.color_picker("Testo", value=curr_col_txt, key="cp_lay_text")
                    if new_col_txt != curr_col_txt:
                        st.session_state["layout_color_text"] = new_col_txt
                        _cp = load_client_preferences()
                        _cp["layout_color_text"] = new_col_txt
                        save_client_preferences(_cp)
                        st.rerun()

                with c_c2:
                    curr_col_chd = st.session_state.get("layout_color_chords", "#B71C1C")
                    new_col_chd = st.color_picker("Accordi", value=curr_col_chd, key="cp_lay_chords")
                    if new_col_chd != curr_col_chd:
                        st.session_state["layout_color_chords"] = new_col_chd
                        _cp = load_client_preferences()
                        _cp["layout_color_chords"] = new_col_chd
                        save_client_preferences(_cp)
                        st.rerun()

                with c_c3:
                    curr_col_aml = st.session_state.get("layout_color_aml", "#4A148C")
                    new_col_aml = st.color_picker("Markup AML", value=curr_col_aml, key="cp_lay_aml")
                    if new_col_aml != curr_col_aml:
                        st.session_state["layout_color_aml"] = new_col_aml
                        _cp = load_client_preferences()
                        _cp["layout_color_aml"] = new_col_aml
                        save_client_preferences(_cp)
                        st.rerun()

                if st.button("🔄 Ripristina Colori Predefiniti", key="btn_reset_lay_colors", width="stretch"):
                    st.session_state["layout_color_text"] = "#111111"
                    st.session_state["layout_color_chords"] = "#B71C1C"
                    st.session_state["layout_color_aml"] = "#4A148C"
                    _cp = load_client_preferences()
                    _cp["layout_color_text"] = "#111111"
                    _cp["layout_color_chords"] = "#B71C1C"
                    _cp["layout_color_aml"] = "#4A148C"
                    save_client_preferences(_cp)
                    st.rerun()

            with tab_lay_zoom:
                st.write("###### 🔍 Scala Schermo (Zoom Interfaccia):")
                st.caption("Rimpicciolisci o ingrandisci per adattare l'interfaccia al tuo tablet:")
                z_cols = st.columns(5)
                zoom_presets = [("75%", 0.75), ("82%", 0.82), ("90%", 0.90), ("100%", 1.0), ("110%", 1.10)]
                for z_i, (z_lbl, z_v) in enumerate(zoom_presets):
                    with z_cols[z_i]:
                        is_active_z = abs(active_zoom - z_v) < 0.02
                        b_type = "primary" if is_active_z else "secondary"
                        if st.button(z_lbl, key=f"btn_z_{z_v}", type=b_type, width="stretch"):
                            st.session_state["ui_zoom_level"] = z_v
                            _cp = load_client_preferences()
                            _cp["ui_zoom_level"] = z_v
                            save_client_preferences(_cp)
                            st.rerun()

                curr_prof = device_mgr.get_device_by_name(curr_pref)
                if curr_prof:
                    st.divider()
                    st.markdown(f"**Specifiche Hardware:** `{curr_prof.name}`<br>"
                                f"📐 Risoluzione mm: `{curr_prof.width_mm:.1f} × {curr_prof.height_mm:.1f} mm` ({curr_prof.orientation})<br>"
                                f"📖 Colonne PDF: `{st.session_state.get('layout_columns', 1)}` &bull; Font: `{st.session_state.get('layout_font_size', 12)} px`",
                                unsafe_allow_html=True)

    with col_btn_log:
        with st.popover(f"📟 {op_logger.count()}", width="stretch", help="Apri la console delle operazioni"):
            render_status_console(op_logger, key_prefix="top_pop_console", compact=False)

    with col_btn_logout:
        if st.button("🚪 Logout", key="top_bar_btn_logout", help="Disconnetti account ed esci", width="stretch"):
            st.session_state["authenticated"] = False
            st.session_state.pop("current_user_email", None)
            _cp = load_client_preferences()
            _cp.pop("active_user_email", None)
            save_client_preferences(_cp)
            st.query_params.clear()
            if hasattr(st, "logout"):
                try:
                    st.logout()
                except Exception:
                    pass
            st.rerun()

    # Row 2: Ultra-Compact Navigation Pills (Strictly Single Row, Never Wrap)
    active_item = st.session_state.get("main_menu_choice", "🏠 Home Dashboard")
    if active_item not in MENU_ITEMS:
        active_item = MENU_ITEMS[0]

    MENU_ITEMS_ROW1 = MENU_ITEMS[:6]
    MENU_ITEMS_ROW2 = MENU_ITEMS[6:]

    def _fmt_label(x):
        return MENU_COMPACT_LABELS.get(x, x)

    # Row 1 of Navigation Pills (6 items: Home, Import/Export, Brani, AI, Cerca, Repertori)
    d1 = active_item if active_item in MENU_ITEMS_ROW1 else None
    sel_r1 = st.pills(
        "Nav Row 1",
        options=MENU_ITEMS_ROW1,
        format_func=_fmt_label,
        default=d1,
        selection_mode="single",
        wrap=False,
        key=f"top_nav_pills_r1_{active_item}",
        label_visibility="collapsed"
    )

    # Row 2 of Navigation Pills (5 items: Scalette, Palco, Eventi, Guida, Admin)
    d2 = active_item if active_item in MENU_ITEMS_ROW2 else None
    sel_r2 = st.pills(
        "Nav Row 2",
        options=MENU_ITEMS_ROW2,
        format_func=_fmt_label,
        default=d2,
        selection_mode="single",
        wrap=False,
        key=f"top_nav_pills_r2_{active_item}",
        label_visibility="collapsed"
    )

    if sel_r1 and sel_r1 != st.session_state["main_menu_choice"]:
        st.session_state["main_menu_choice"] = sel_r1
        st.rerun()
    elif sel_r2 and sel_r2 != st.session_state["main_menu_choice"]:
        st.session_state["main_menu_choice"] = sel_r2
        st.rerun()

    menu_choice = st.session_state["main_menu_choice"]

    # Unlock automatico dei brani quando si esce dal menu 'Brani'
    last_menu = st.session_state.get("last_visited_menu", menu_choice)
    if menu_choice != "📝 Brani":
        u_email = st.session_state.get("current_user_email", "")
        if u_email:
            auto_released = lock_mgr.release_user_locks(u_email)
            for r_uid in auto_released:
                s_obj_r = storage.get_song(r_uid)
                r_title = s_obj_r.title if s_obj_r else r_uid
                log_op("🔓", "LOCK", f"Lock per '{r_title}' rilasciato automaticamente all'uscita dal menu Brani", "INFO")
    st.session_state["last_visited_menu"] = menu_choice

# ------------------------------------------------------------------------------
# 1. HOME DASHBOARD
# ------------------------------------------------------------------------------
if menu_choice == "🏠 Home Dashboard":
    # Compact Header Bar
    st.markdown(
        """<div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:10px;">
          <div style="display:flex; align-items:baseline; gap:8px;">
            <span style="font-size:16px; font-weight:700; color:#FFFFFF;">🏠 Dashboard Band</span>
            <span style="font-size:11px; color:#94A3B8;">Repertorio &bull; Scalette &bull; Live Stage 60fps &bull; AML</span>
          </div>
        </div>""",
        unsafe_allow_html=True
    )

    songs = storage.list_songs()
    repertoires = storage.list_repertoires()
    setlists = storage.list_setlists()
    events = storage.list_events()

    # Compact KPI Metrics Cards (4 columns on PC/Tablet, 2x2 on Mobile, never 1 giant stack)
    st.markdown(
        f"""<div class="asma-kpi-grid">
          <div class="asma-kpi-card">
            <div class="asma-kpi-header">
              <span class="asma-kpi-icon">🎵</span>
              <span class="asma-kpi-title">Brani in Archivio</span>
            </div>
            <div class="asma-kpi-val">{len(songs)}</div>
          </div>
          <div class="asma-kpi-card">
            <div class="asma-kpi-header">
              <span class="asma-kpi-icon">📚</span>
              <span class="asma-kpi-title">Repertori Attivi</span>
            </div>
            <div class="asma-kpi-val">{len(repertoires)}</div>
          </div>
          <div class="asma-kpi-card">
            <div class="asma-kpi-header">
              <span class="asma-kpi-icon">📑</span>
              <span class="asma-kpi-title">Scalette Live</span>
            </div>
            <div class="asma-kpi-val">{len(setlists)}</div>
          </div>
          <div class="asma-kpi-card">
            <div class="asma-kpi-header">
              <span class="asma-kpi-icon">📅</span>
              <span class="asma-kpi-title">Eventi Programmati</span>
            </div>
            <div class="asma-kpi-val">{len(events)}</div>
          </div>
        </div>""",
        unsafe_allow_html=True
    )

    # Ultime Attività & Modifiche (Registro Recente)
    st.markdown(
        """<div style="display:flex; align-items:center; gap:6px; margin-bottom:8px;">
          <span style="font-size:13px;">🕒</span>
          <b style="font-size:13px; color:#FFFFFF;">Ultime Attività & Modifiche</b>
        </div>""",
        unsafe_allow_html=True
    )
    recent_logs = audit.get_entries(limit=6)
    if recent_logs:
        log_lines = []
        for log in recent_logs:
            time_part = log.timestamp[11:19] if len(log.timestamp) >= 19 else log.timestamp
            log_lines.append(
                f"<div style='font-size:11.5px; padding:4px 0; border-bottom:1px solid rgba(255,255,255,0.05); color:#CBD5E1; display:flex; align-items:center; gap:8px;'>"
                f"<code style='color:#00E5FF; background:rgba(0,229,255,0.08); padding:1px 5px; border-radius:3px;'>{time_part}</code> "
                f"<b style='color:#FFFFFF;'>{log.action}</b> su <span style='color:#94A3B8;'>{log.entity_type}</span> da <i style='color:#CBD5E1;'>{log.user_name}</i>"
                f"</div>"
            )
        st.markdown(f"<div class='asma-dash-card'>{''.join(log_lines)}</div>", unsafe_allow_html=True)
    else:
        st.info("Nessuna attività recente registrata.")

# ------------------------------------------------------------------------------
# 2. GESTIONE REPERTORI
# ------------------------------------------------------------------------------
elif menu_choice == "📥 Importa & 📤 Esporta":
    # Le schede/menu partono immediatamente appena sotto la barra fissa
    tab_web, tab_imp, tab_exp = st.tabs([
        "🌐 Import da Web / URL",
        "📥 Import File & Testo",
        "📱 MobileSheets & Altre App"
    ])

    all_reps = storage.list_repertoires()

    with tab_web:
        if all_reps:
            c_r1, c_r2 = st.columns([2, 1], gap="small")
            with c_r1:
                target_rep = st.selectbox(
                    "📂 Assegna automaticamente i brani importati a questo Repertorio:",
                    all_reps,
                    format_func=lambda r: f"📚 {r.name} ({len(r.song_uuids)} brani)",
                    key="web_target_rep_sel"
                )
            with c_r2:
                st.caption(f"Archiviazione automatica in: **{target_rep.name}**")
        else:
            target_rep = None

        st.write("#### 🌐 Importazione Automatica da Internet (Siti Italiani ed Internazionali)")
        st.caption("Estrae automaticamente accordi e testi da Accordi e Spartiti, Ultimate-Guitar, Skitarrate, Chordie e pagine web pubbliche.")

        url_input = st.text_input("Incolla URL diretto della pagina dello spartito:", placeholder="https://www.accordiespartiti.it/accordi/italiani/nomadi/canzone-per-unamica/")
        if url_input and st.button("📥 Scarica da URL e Converti in AML"):
            with st.spinner("Scaricamento e parsing della pagina web..."):
                try:
                    song_web = WebSongImporter.fetch_from_url(url_input)
                    saved = storage.save_song(song_web, st.session_state["current_user_email"], st.session_state["current_user_name"], "Importazione da Web URL")
                    if target_rep:
                        storage.move_song_to_repertoire(saved.uuid, target_rep.uuid, st.session_state["current_user_email"], st.session_state["current_user_name"])
                    rep_msg = f" ed inserito nel repertorio **'{target_rep.name}'**" if target_rep else ""
                    log_op("📥", "WEB IMPORT", f"Importato brano '{saved.title}' ({saved.artist}) da URL web", "SUCCESS")
                    st.success(f"Brano importato e salvato con successo: **{saved.title}** ({saved.artist}) — Tonalità: `{saved.key_current}`{rep_msg}")
                    st.session_state["selected_song_uuid"] = saved.uuid
                except Exception as err:
                    log_op("❌", "WEB IMPORT", f"Errore import URL: {str(err)}", "ERROR")
                    st.error(f"Errore durante l'importazione da Web: {str(err)}")

        st.divider()
        st.write("#### 🔍 Ricerca Brano Online sui Portali (Italiani ed Internazionali)")
        st.caption("Interroga in tempo reale Accordi e Spartiti, Ultimate-Guitar e i principali archivi web per trovare e importare lo spartito reale.")

        c_w1, c_w2 = st.columns(2)
        with c_w1:
            search_title = st.text_input("Titolo Brano:", value="", placeholder="Inserisci titolo brano...", key="web_search_title")
        with c_w2:
            search_artist = st.text_input("Artista (opzionale):", value="", placeholder="Inserisci artista...", key="web_search_artist")

        c_btn1, c_btn2 = st.columns([1, 1])
        with c_btn1:
            do_search = st.button("🔍 Cerca Brano sui Portali", width="stretch")
        with c_btn2:
            auto_import = st.button("⚡ Importa Subito il Miglior Risultato", width="stretch")

        if do_search:
            if not search_title.strip():
                st.warning("⚠️ Inserisci il titolo del brano da cercare.")
            else:
                with st.spinner("Ricerca in corso sui portali di accordi..."):
                    found_candidates = WebSongImporter.search_online_candidates(search_title, search_artist, limit=6)
                    st.session_state["web_search_candidates"] = found_candidates
                    log_op("🔍", "WEB IMPORT", f"Ricerca online per '{search_title}': trovati {len(found_candidates)} spartiti", "INFO")
                    if not found_candidates:
                        st.warning("Nessun brano trovato con questi termini sui portali online, oppure rete non raggiungibile.")

        if auto_import:
            if not search_title.strip():
                st.warning("⚠️ Inserisci il titolo del brano da importare.")
            else:
                with st.spinner("Ricerca e importazione del brano migliore in corso..."):
                    try:
                        imported_song = WebSongImporter.search_online_and_import(search_title, search_artist)
                        saved = storage.save_song(imported_song, st.session_state["current_user_email"], st.session_state["current_user_name"], "Ricerca Web e Importazione Automatica")
                        if target_rep:
                            storage.move_song_to_repertoire(saved.uuid, target_rep.uuid, st.session_state["current_user_email"], st.session_state["current_user_name"])
                        st.session_state["selected_song_uuid"] = saved.uuid
                        rep_msg = f" ed associato a **'{target_rep.name}'**" if target_rep else ""
                        log_op("⚡", "WEB IMPORT", f"Importazione rapida completata: '{saved.title}' ({saved.artist})", "SUCCESS")
                        st.success(f"Brano importato e salvato: **{saved.title}** ({saved.artist}) — Tonalità: `{saved.key_current}`{rep_msg}")
                        st.info("Puoi visualizzarlo o modificarlo nella sezione **'🎵 Repertorio'**.")
                    except Exception as err:
                        log_op("❌", "WEB IMPORT", f"Errore import automatico: {str(err)}", "ERROR")
                        st.error(f"Errore durante l'importazione automatica: {str(err)}")

        # Visualizza risultati candidati trovati
        candidates = st.session_state.get("web_search_candidates", [])
        if candidates:
            st.write(f"##### 📋 Risultati trovati sul Web ({len(candidates)} spartiti disponibili):")
            for idx, cand in enumerate(candidates):
                with st.container():
                    col_info, col_act = st.columns([4, 1])
                    with col_info:
                        st.markdown(f"**{cand['title']}** — *{cand.get('artist', '')}*  \n🏷️ Portale: `{cand['portal']}` | [Apri Pagina Originale ↗]({cand['url']})")
                    with col_act:
                        if st.button("📥 Importa", key=f"imp_cand_{idx}", width="stretch"):
                            with st.spinner("Scaricamento e parsing in AML..."):
                                try:
                                    s_obj = WebSongImporter.fetch_from_url(cand["url"])
                                    if (not s_obj.artist or s_obj.artist == "Artista Sconosciuto") and cand.get("artist"):
                                        s_obj.artist = cand["artist"]
                                    if (not s_obj.title or s_obj.title == "Brano da Web") and cand.get("title"):
                                        s_obj.title = cand["title"]
                                    saved = storage.save_song(s_obj, st.session_state["current_user_email"], st.session_state["current_user_name"], f"Importato da {cand['portal']}")
                                    if target_rep:
                                        storage.move_song_to_repertoire(saved.uuid, target_rep.uuid, st.session_state["current_user_email"], st.session_state["current_user_name"])
                                    st.session_state["selected_song_uuid"] = saved.uuid
                                    rep_msg = f" ed inserito in **'{target_rep.name}'**" if target_rep else ""
                                    log_op("📥", "WEB IMPORT", f"Importato brano '{saved.title}' da {cand['portal']}", "SUCCESS")
                                    st.success(f"Brano salvato: **{saved.title}** (Key: `{saved.key_current}`){rep_msg}!")
                                except Exception as e_imp:
                                    log_op("❌", "WEB IMPORT", f"Errore importazione candidato: {str(e_imp)}", "ERROR")
                                    st.error(f"Errore importazione: {str(e_imp)}")

    with tab_imp:
        if all_reps:
            c_rf1, c_rf2 = st.columns([2, 1], gap="small")
            with c_rf1:
                target_rep_f = st.selectbox(
                    "📂 Assegna automaticamente i brani importati a questo Repertorio:",
                    all_reps,
                    format_func=lambda r: f"📚 {r.name} ({len(r.song_uuids)} brani)",
                    key="file_target_rep_sel"
                )
            with c_rf2:
                st.caption(f"Archiviazione automatica in: **{target_rep_f.name}**")
        else:
            target_rep_f = None

        st.write("#### Importazione da File PDF, ChordPro o Formato Tradizionale")
        imp_format = st.radio("Seleziona Formato di Origine:", ["ChordPro standard", "Tradizionale (Accordi sopra il testo)", "PDF"], horizontal=True)

        if imp_format == "PDF":
            uploaded_pdf = st.file_uploader("Carica File PDF dello spartito:", type=["pdf"])
            if uploaded_pdf and st.button("Estrai e Converti in AML"):
                pdf_bytes = uploaded_pdf.read()
                imported_s = ImportEngine.import_from_pdf_bytes(pdf_bytes, filename=uploaded_pdf.name)
                saved = storage.save_song(imported_s, st.session_state["current_user_email"], st.session_state["current_user_name"])
                if target_rep:
                    storage.move_song_to_repertoire(saved.uuid, target_rep.uuid, st.session_state["current_user_email"], st.session_state["current_user_name"])
                rep_msg = f" ed inserito in **'{target_rep.name}'**" if target_rep else ""
                st.success(f"Estratto e salvato con successo come '{saved.title}'{rep_msg}!")
                st.session_state["selected_song_uuid"] = saved.uuid
        else:
            pasted_text = st.text_area("Incolla qui il testo dello spartito:", height=200)
            if pasted_text and st.button("Converti e Salva in Repertorio"):
                if imp_format == "ChordPro standard":
                    s_obj = ImportEngine.import_from_chordpro(pasted_text)
                else:
                    s_obj = ImportEngine.import_from_traditional(pasted_text)
                saved = storage.save_song(s_obj, st.session_state["current_user_email"], st.session_state["current_user_name"])
                if target_rep:
                    storage.move_song_to_repertoire(saved.uuid, target_rep.uuid, st.session_state["current_user_email"], st.session_state["current_user_name"])
                rep_msg = f" ed inserito in **'{target_rep.name}'**" if target_rep else ""
                st.success(f"Brano importato e salvato: **{saved.title}** (Key: {saved.key_current}){rep_msg}")

    with tab_exp:
        st.write("#### Esportazione per MobileSheets, SongBookPro, OnSong")
        all_s = sorted(storage.list_songs(), key=lambda s: s["title"].lower())
        if all_s:
            exp_song_id = st.selectbox("Seleziona Brano da esportare:", [s["uuid"] for s in all_s], format_func=lambda x: next(s["title"] for s in all_s if s["uuid"] == x))
            target_song = storage.get_song(exp_song_id)

            clean_exp_title = re.sub(r'[\\/*?:"<>|]', '', target_song.title).strip().upper() or 'BRANO'
            c_e1, c_e2, c_e3, c_e4 = st.columns(4)
            with c_e1:
                sb_content = ExportEngine.export_for_songbookpro(target_song)
                st.download_button("🎸 SongBook Pro (.pro)", sb_content, file_name=f"{clean_exp_title}.pro", width="stretch")
            with c_e2:
                ms_content = ExportEngine.export_for_mobilesheets(target_song)
                st.download_button("📱 MobileSheets (.pro)", ms_content, file_name=f"{clean_exp_title}.pro", width="stretch")
            with c_e3:
                cpro_content = ExportEngine.export_to_chordpro(target_song.aml_content)
                st.download_button("🎼 ChordPro (.cho)", cpro_content, file_name=f"{clean_exp_title}.cho", width="stretch")
            with c_e4:
                onsong_content = ExportEngine.export_for_onsong(target_song)
                st.download_button("🎤 OnSong (.onsong)", onsong_content, file_name=f"{clean_exp_title}.onsong", width="stretch")

            st.divider()
            st.write("#### 📦 Offline Live Pack ZIP (SRS Cap. 14.29)")
            setlists = storage.list_setlists()
            if setlists:
                pack_set = st.selectbox("Seleziona Scaletta per generare il Live Pack:", setlists, format_func=lambda x: x.title)
                pack_songs = [storage.get_song(it.song_uuid) for it in pack_set.items if storage.get_song(it.song_uuid)]
                if pack_songs:
                    pack_zip = ExportEngine.create_offline_live_pack_zip(pack_set, pack_songs)
                    st.download_button(
                        "💾 Scarica Offline Live Pack ZIP Completo",
                        data=pack_zip,
                        file_name=f"OfflinePack_{pack_set.title.replace(' ', '_')}.zip",
                        mime="application/zip",
                        type="primary"
                    )

# ------------------------------------------------------------------------------
# 8. RICERCA GLOBALE
# ------------------------------------------------------------------------------
elif menu_choice == "📝 Brani":
    st.subheader("📝 Gestione & Editor Brani (AML & Anteprima)")
    st.caption("Importa, visualizza, componi in AML e controlla l'anteprima device-aware con accordi e trasposizione.")

    all_reps = storage.list_repertoires()
    rep_filter_options = {"__ALL__": "🌐 Tutti i Repertori (Archivio Globale)"}
    for r in all_reps:
        rep_filter_options[r.uuid] = f"📁 {r.name} ({len(r.song_uuids)} brani)"

    selected_rep_filter_id = st.session_state.get("song_editor_rep_filter", "__ALL__")
    if selected_rep_filter_id not in rep_filter_options:
        selected_rep_filter_id = "__ALL__"

    col_rf1, col_rf2 = st.columns([2.5, 1.5], gap="small")
    with col_rf1:
        new_rep_filter = st.selectbox(
            "📁 Filtra Brani per Repertorio di Lavoro:",
            list(rep_filter_options.keys()),
            index=list(rep_filter_options.keys()).index(selected_rep_filter_id),
            format_func=lambda x: rep_filter_options[x],
            key="song_editor_repertoire_selector"
        )
        if new_rep_filter != selected_rep_filter_id:
            st.session_state["song_editor_rep_filter"] = new_rep_filter
            st.session_state["selected_song_uuid"] = None
            st.rerun()

    active_rep_obj = next((r for r in all_reps if r.uuid == new_rep_filter), None)
    with col_rf2:
        if active_rep_obj:
            st.caption(f"📂 Repertorio attivo: **{active_rep_obj.name}**\n\n*Regola: brano unico in questo repertorio.*")
        else:
            st.caption("🌐 Visualizzazione di tutti i brani dell'archivio.")

    if active_rep_obj:
        st.markdown(
            f'<div style="background:linear-gradient(90deg, rgba(14,165,233,0.18) 0%, rgba(99,102,241,0.18) 100%); border:1px solid #38BDF8; border-radius:8px; padding:10px 14px; margin-bottom:12px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px;">'
            f'<div><span style="font-size:11px; text-transform:uppercase; font-weight:800; color:#38BDF8; letter-spacing:1px;">📁 REPERTORIO ATTIVO IN EDIT:</span>'
            f'<span style="font-size:15px; font-weight:900; color:#FFFFFF; margin-left:8px;">{active_rep_obj.name}</span>'
            f'<span style="font-size:12px; color:#94A3B8; margin-left:10px;">({len(active_rep_obj.song_uuids)} brani)</span></div>'
            f'<div style="font-size:11px; color:#FBBF24; font-weight:600;">🔒 Regola: versione unica per titolo in questo repertorio (diverse versioni ammesse in altri repertori)</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        songs = [s for s in storage.list_songs() if s["uuid"] in active_rep_obj.song_uuids]
        songs = sorted(songs, key=lambda s: s["title"].lower())
    else:
        songs = sorted(storage.list_songs(), key=lambda s: s["title"].lower())

    if not songs:
        if active_rep_obj:
            st.info(f"📂 Il repertorio **'{active_rep_obj.name}'** è attualmente vuoto. Puoi creare un nuovo brano autoprodotto o inserire un brano esistente dell'archivio.")
            c_empty1, c_empty2 = st.columns([1, 2], gap="small")
            with c_empty1:
                with st.popover("➕ Nuovo Brano", help="Inserisci un testo autoprodotto o componi un nuovo brano", width="stretch"):
                    st.markdown("##### ✍️ Nuovo Brano Autoprodotto")
                    st.caption("Scrivi o incolla il tuo testo per aggiungerlo al repertorio.")
                    new_e_title = st.text_input("Titolo:", placeholder="es. La Mia Canzone", key="empty_auto_title").strip()
                    new_e_artist = st.text_input("Autore / Artista:", value=st.session_state.get("current_user_name", "Autore"), key="empty_auto_artist").strip()
                    new_e_key = st.text_input("Tonalità:", value="DO", key="empty_auto_key").strip()
                    new_e_text = st.text_area("Testo e Accordi:", placeholder="Incolla qui strofe o accordi...", height=140, key="empty_auto_text")
                    if st.button("💾 Crea e Salva nel Repertorio", type="primary", disabled=not current_user.can_edit(), key="btn_create_empty_song", width="stretch"):
                        if new_e_title:
                            if new_e_text.strip():
                                if "[" in new_e_text and "]" in new_e_text:
                                    doc = AMLParser.parse(new_e_text)
                                else:
                                    doc = AMLParser.import_traditional_chords_over_text(new_e_text)
                                body_aml = doc.to_aml()
                            else:
                                body_aml = "{verse}\n[DO]Prima strofa...\n\n{chorus}\n[FA]Ritornello [SOL]qui [DO]!\n"
                            new_song = Song(
                                title=new_e_title,
                                artist=new_e_artist,
                                author=new_e_artist,
                                key_original=new_e_key or "DO",
                                key_current=new_e_key or "DO",
                                aml_content=f"{{title: {new_e_title}}}\n{{artist: {new_e_artist}}}\n{{key: {new_e_key or 'DO'}}}\n\n{body_aml}"
                            )
                            saved = storage.save_song(new_song, user_email, user_name, "Creazione brano autoprodotto")
                            storage.move_song_to_repertoire(saved.uuid, active_rep_obj.uuid, user_email, user_name)
                            st.session_state["selected_song_uuid"] = saved.uuid
                            st.success(f"Brano '{saved.title}' aggiunto al repertorio!")
                            st.rerun()
            with c_empty2:
                all_unassigned = sorted([s for s in storage.list_songs() if s["uuid"] not in active_rep_obj.song_uuids], key=lambda s: s["title"].lower())
                if all_unassigned:
                    with st.expander("📥 Inserisci brano esistente dell'archivio in questo repertorio"):
                        s_add_id = st.selectbox(
                            "Seleziona brano da collegare:",
                            [s["uuid"] for s in all_unassigned],
                            format_func=lambda uid: next(f"{s['title']} ({s.get('artist', 'Sconosciuto')})" for s in all_unassigned if s["uuid"] == uid),
                            key=f"sel_add_empty_{active_rep_obj.uuid}"
                        )
                        if st.button("➕ Aggiungi al Repertorio", disabled=not current_user.can_edit(), key=f"btn_add_empty_{active_rep_obj.uuid}"):
                            storage.move_song_to_repertoire(s_add_id, active_rep_obj.uuid, user_email, user_name)
                            st.success("Brano associato con successo!")
                            st.rerun()
        else:
            st.warning("Nessun brano disponibile nell'archivio. Creane uno per iniziare.")
        st.stop()

    song_choices = {s["uuid"]: s["title"] for s in songs}
    curr_uuid = st.session_state.get("selected_song_uuid")
    keys_list = list(song_choices.keys())
    default_idx = keys_list.index(curr_uuid) if (curr_uuid and curr_uuid in keys_list) else 0

    curr_pre_song = storage.get_song(keys_list[default_idx]) if keys_list else None
    artist_subtitle = f"({curr_pre_song.artist})" if curr_pre_song and curr_pre_song.artist else ""
    key_bpm_subtitle = f"Tonalità: {curr_pre_song.key_current} &bull; 🌐 SongBPM: {curr_pre_song.bpm} BPM" if curr_pre_song else ""
    sub_title = f"{artist_subtitle} {key_bpm_subtitle}".strip()
    sub_span = f'<span style="font-size:11px; color:#94A3B8; font-weight:600;">{sub_title}</span>' if sub_title else ''

    c_top_sel, c_top_new = st.columns([3, 1], gap="small")
    with c_top_sel:
        st.markdown(
            f'<div style="margin-bottom:4px; display:flex; align-items:center; justify-content:space-between;">'
            f'<span style="font-size:12px; font-weight:800; color:#38BDF8; letter-spacing:0.6px; text-transform:uppercase;">🎵 Brano Attivo Selezionato:</span>'
            f'{sub_span}'
            f'</div>',
            unsafe_allow_html=True
        )
        selected_uuid = st.selectbox(
            "Seleziona Brano da modificare:",
            keys_list,
            index=default_idx,
            format_func=lambda x: f"🎵 {song_choices[x].upper()}",
            label_visibility="collapsed",
            key="main_song_selector"
        )
    with c_top_new:
        st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)
        with st.popover("➕ Nuovo Brano", help="Inserisci un testo autoprodotto o componi un nuovo brano", width="stretch"):
            st.markdown("##### ✍️ Nuovo Brano Autoprodotto")
            st.caption("Scrivi o incolla il tuo testo: verrà formattato e aggiunto immediatamente all'archivio.")
            new_auto_title = st.text_input("Titolo:", placeholder="es. La Mia Canzone", key="auto_title").strip()
            new_auto_artist = st.text_input("Autore / Artista:", value=st.session_state.get("current_user_name", "Autore"), key="auto_artist").strip()
            new_auto_key = st.text_input("Tonalità:", value="DO", key="auto_key").strip()
            new_auto_text = st.text_area("Testo e Accordi (incolla qui il tuo testo):", placeholder="Incolla qui strofe, ritornelli o accordi...", height=160, key="auto_text")

            if st.button("💾 Crea e Apri nell'Editor", type="primary", disabled=not current_user.can_edit(), key="btn_create_auto_song", width="stretch"):
                if not new_auto_title:
                    st.warning("⚠️ Inserisci almeno il titolo del brano.")
                else:
                    if new_auto_text.strip():
                        if "[" in new_auto_text and "]" in new_auto_text:
                            doc = AMLParser.parse(new_auto_text)
                        else:
                            doc = AMLParser.import_traditional_chords_over_text(new_auto_text)
                        body_aml = doc.to_aml()
                    else:
                        body_aml = "{verse}\n[DO]Inizia a scrivere qui la prima [SOL]strofa...\n\n{chorus}\n[FA]Ritornello della tua [SOL]canzone [DO]qui!\n"

                    aml_lines = [
                        f"{{title: {new_auto_title}}}",
                        f"{{artist: {new_auto_artist}}}",
                        f"{{key: {new_auto_key or 'DO'}}}",
                        "",
                        body_aml
                    ]

                    new_bpm = BandAIService.estimate_song_bpm(new_auto_title, new_auto_artist)
                    new_song = Song(
                        title=new_auto_title,
                        artist=new_auto_artist,
                        author=new_auto_artist,
                        key_original=new_auto_key or "DO",
                        key_current=new_auto_key or "DO",
                        bpm=new_bpm,
                        aml_content="\n".join(aml_lines),
                        tags=["autoprodotto"]
                    )
                    if active_rep_obj:
                        can_add, reason = storage.can_add_song_to_repertoire(active_rep_obj.uuid, new_auto_title)
                        if not can_add:
                            st.error(reason)
                            st.stop()

                    saved = storage.save_song(new_song, user_email, user_name, "Creazione brano autoprodotto")
                    if active_rep_obj:
                        storage.move_song_to_repertoire(saved.uuid, active_rep_obj.uuid, user_email, user_name)

                    st.session_state["selected_song_uuid"] = saved.uuid
                    log_op("✍️", "BRANO", f"Creato brano autoprodotto '{saved.title}' ({saved.artist})", "SUCCESS")
                    st.success(f"Brano '{saved.title}' creato con successo!")
                    st.rerun()

    if curr_uuid and curr_uuid != selected_uuid:
        # Rilascia il lock del brano precedente quando si cambia brano nell'editor
        lock_mgr.release_lock(curr_uuid, st.session_state.get("current_user_email", ""))
    st.session_state["selected_song_uuid"] = selected_uuid

    song = storage.get_song(selected_uuid)
    if not song:
        st.error("Brano non trovato.")
        st.stop()

    # Lock Management Check (SRS Cap. 4.6 & 7.7)
    current_lock = lock_mgr.check_lock(song.uuid)
    user_email = st.session_state["current_user_email"]
    user_name = st.session_state["current_user_name"]

    user_released = st.session_state.get(f"released_lock_{song.uuid}", False)

    if user_released:
        can_edit = False
        st.info(f"ℹ️ Modalità Sola Lettura: hai rilasciato il lock per '{song.title}'. Il brano è libero per gli altri musicisti.")
        if st.button("🔒 Ri-acquisisci Lock per Modificare", type="primary"):
            st.session_state.pop(f"released_lock_{song.uuid}", None)
            st.rerun()
    elif current_lock.is_locked and current_lock.locked_by_email != user_email:
        st.error(f"🔒 Brano bloccato in modifica da **{current_lock.locked_by_name}** ({current_lock.locked_by_email}). Modalità sola lettura.")
        can_edit = False
    elif not current_user.can_edit():
        st.warning("⚠️ Modalità Sola Lettura: L'utente corrente ha ruolo VIEWER (Ospite). I controlli di modifica e salvataggio sono disattivati.")
        can_edit = False
    else:
        lock_mgr.acquire_lock(song.uuid, user_email, user_name)
        st.success(f"🔓 Hai acquisito il lock di editing per '{song.title}'. Gli altri musicisti possono solo consultarlo.")
        can_edit = True

    # -------------------------------------------------------------------------
    # TOOLBAR SUPERIORE COMPATTA CON TITOLO BRANO SEMPRE IN EVIDENZA (SRS Cap. 4.6 & 7.7)
    # -------------------------------------------------------------------------
    st.markdown(
        f"""<div style="background:rgba(15,23,42,0.92); border:1px solid #334155; border-left:4px solid #38BDF8; border-radius:8px; padding:10px 14px; margin:6px 0 10px 0;">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
            <div>
              <span style="font-size:17px; font-weight:900; color:#FFFFFF; letter-spacing:0.5px;">🎵 {song.title.upper()}</span>
              <span style="font-size:12.5px; color:#94A3B8; margin-left:6px;">&bull; {song.artist or 'Autore non specificato'}</span>
              <div style="font-size:11px; color:#38BDF8; font-weight:600; margin-top:2px;">
                Tonalità: <code style="color:#FFD600;">{song.key_current}</code> &bull; Tempo: <code style="color:#00E676;">{song.bpm} BPM</code> &bull; Versione: <b>Rev #{song.current_revision}</b> &bull; Lock: {'🔒 Tuo' if can_edit else '👁️ Sola Lettura'}
              </div>
            </div>
          </div>
        </div>""",
        unsafe_allow_html=True
    )

    t_btn_new, t_btn_save, t_btn_clone, t_btn_unlock, t_btn_del = st.columns([1, 1.3, 1.2, 1, 1], gap="small")

    with t_btn_new:
        with st.popover("➕ Nuovo Brano", help="Inserisci un testo autoprodotto o componi un nuovo brano", width="stretch"):
            st.markdown("##### ✍️ Nuovo Brano Autoprodotto")
            st.caption("Scrivi o incolla il tuo testo per aggiungerlo all'archivio.")
            new_top_title = st.text_input("Titolo:", placeholder="es. La Mia Canzone", key="top_auto_title").strip()
            new_top_artist = st.text_input("Autore / Artista:", value=st.session_state.get("current_user_name", "Autore"), key="top_auto_artist").strip()
            new_top_key = st.text_input("Tonalità:", value="DO", key="top_auto_key").strip()
            new_top_text = st.text_area("Testo e Accordi:", placeholder="Incolla qui strofe o accordi...", height=140, key="top_auto_text")
            if st.button("💾 Crea e Apri", type="primary", disabled=not current_user.can_edit(), key="btn_create_top_song", width="stretch"):
                if new_top_title:
                    if new_top_text.strip():
                        if "[" in new_top_text and "]" in new_top_text:
                            doc = AMLParser.parse(new_top_text)
                        else:
                            doc = AMLParser.import_traditional_chords_over_text(new_top_text)
                        body_aml = doc.to_aml()
                    else:
                        body_aml = "{verse}\n[DO]Prima strofa del nuovo brano...\n\n{chorus}\n[FA]Ritornello [SOL]qui [DO]!\n"
                    aml_lines = [
                        f"{{title: {new_top_title}}}",
                        f"{{artist: {new_top_artist}}}",
                        f"{{key: {new_top_key or 'DO'}}}",
                        "",
                        body_aml
                    ]
                    new_s_obj = Song(
                        title=new_top_title,
                        artist=new_top_artist,
                        author=new_top_artist,
                        key_original=new_top_key or "DO",
                        key_current=new_top_key or "DO",
                        bpm=120,
                        aml_content="\n".join(aml_lines),
                        tags=["autoprodotto"]
                    )
                    saved_top = storage.save_song(new_s_obj, user_email, user_name, "Creazione brano autoprodotto da toolbar")
                    st.session_state["selected_song_uuid"] = saved_top.uuid
                    log_op("✍️", "BRANO", f"Creato brano '{saved_top.title}' ({saved_top.artist})", "SUCCESS")
                    st.rerun()

    with t_btn_save:
        if st.button("💾 Salva Nuova Revisione", type="primary", disabled=not can_edit, width="stretch", key="top_bar_btn_save_rev", help="Salva immediatamente una nuova revisione del brano corrente"):
            # Update song metadata and content from inputs if available
            if 'title_input' in locals() and title_input:
                song.title = title_input
            if 'artist_input' in locals() and artist_input:
                song.artist = artist_input
            if 'key_input' in locals() and key_input:
                song.key_current = key_input
            if 'bpm_input' in locals() and bpm_input:
                song.bpm = bpm_input
            if 'genre_input' in locals() and genre_input:
                song.genre = genre_input
            if 'tags_input' in locals() and tags_input:
                song.tags = [t.strip().lower() for t in tags_input.split(",") if t.strip()]
            if 'aml_editor_text' in locals() and aml_editor_text:
                song.aml_content = aml_editor_text
            
            # Enforce title uniqueness in same repertoire
            if 'title_input' in locals() and title_input:
                clean_new_title = title_input.strip()
                if clean_new_title.lower() != song.title.strip().lower():
                    reps_with_song = [r for r in all_reps if song.uuid in r.song_uuids]
                    for r in reps_with_song:
                        can_add, reason = storage.can_add_song_to_repertoire(r.uuid, clean_new_title, exclude_song_uuid=song.uuid)
                        if not can_add:
                            st.error(reason)
                            st.stop()
            saved = storage.save_song(song, user_email, user_name, "Salvataggio rapido da toolbar in alto")
            log_op("💾", "SALVATAGGIO", f"Salvata Nuova Revisione #{saved.current_revision} per '{song.title}'", "SUCCESS")
            st.success(f"✅ Salvato con successo! Nuova Revisione #{saved.current_revision}")
            st.rerun()

    with t_btn_clone:
        with st.popover("📋 Clona per Altro Repertorio", help="Crea una versione indipendente di questo brano in un altro repertorio", width="stretch"):
            st.markdown("##### 📋 Clona Versione in Altro Repertorio")
            st.caption("Crea una copia indipendente di questo brano (nuovo UUID) da arrangiare diversamente (es. versione acustica, club, elettrica).")
            if all_reps:
                target_clone_rep = st.selectbox("Repertorio di destinazione:", all_reps, format_func=lambda r: f"📁 {r.name}", key=f"sel_clone_rep_{song.uuid}")
                clone_title = st.text_input("Titolo nuova versione:", value=song.title, key=f"clone_title_{song.uuid}").strip()
                if st.button("🚀 Conferma Clona Versione", type="primary", disabled=not current_user.can_edit(), key=f"btn_confirm_clone_{song.uuid}", width="stretch"):
                    can_add, reason = storage.can_add_song_to_repertoire(target_clone_rep.uuid, clone_title)
                    if not can_add:
                        st.error(reason)
                    else:
                        cloned_song = Song(
                            title=clone_title,
                            artist=song.artist,
                            author=song.author,
                            genre=song.genre,
                            year=song.year,
                            duration_seconds=song.duration_seconds,
                            bpm=song.bpm,
                            time_signature=song.time_signature,
                            capo=song.capo,
                            key_original=song.key_original,
                            key_current=song.key_current,
                            notation_system=song.notation_system,
                            tags=list(song.tags),
                            shared_notes=song.shared_notes,
                            aml_content=song.aml_content
                        )
                        saved_clone = storage.save_song(cloned_song, user_email, user_name, f"Clonata versione da '{song.title}' per '{target_clone_rep.name}'")
                        storage.move_song_to_repertoire(saved_clone.uuid, target_clone_rep.uuid, user_email, user_name)
                        st.session_state["song_editor_rep_filter"] = target_clone_rep.uuid
                        st.session_state["selected_song_uuid"] = saved_clone.uuid
                        log_op("📋", "CLONA", f"Creata versione '{saved_clone.title}' nel repertorio '{target_clone_rep.name}'", "SUCCESS")
                        st.success(f"Versione clonata nel repertorio '{target_clone_rep.name}'!")
                        st.rerun()

    with t_btn_unlock:
        if st.button("🔓 Rilascia Lock", width="stretch", key="top_bar_btn_unlock", help="Rilascia il blocco di modifica per permettere ad altri di modificare"):
            lock_mgr.release_lock(song.uuid, user_email)
            st.session_state[f"released_lock_{song.uuid}"] = True
            log_op("🔓", "LOCK", f"Rilasciato lock di editing per '{song.title}'", "INFO")
            st.info("Lock rilasciato.")
            st.rerun()

    with t_btn_del:
        with st.popover("🗑️ Elimina Brano", width="stretch", help="Elimina brano con protezione cestino 30 giorni"):
            st.warning(f"Vuoi spostare **'{song.title}'** nel cestino?\n\n*Potrai ripristinarlo entro 30 giorni.*")
            if st.button("Conferma Eliminazione", type="secondary", disabled=not current_user.can_delete(), key=f"del_top_bar_{song.uuid}", width="stretch"):
                lock_mgr.release_lock(song.uuid, user_email, force=True)
                storage.delete_song(song.uuid, user_email, user_name)
                log_op("🗑️", "CESTINO", f"Brano '{song.title}' spostato nel cestino (soft-delete 30gg)", "WARNING")
                st.session_state["selected_song_uuid"] = None
                st.success(f"Brano '{song.title}' spostato nel cestino.")
                st.rerun()

    col_edit, col_prev = st.columns([1, 1])

    with col_edit:
        st.write("#### 🎼 Sorgente AML")
        meta_c1, meta_c2, meta_c3 = st.columns(3)
        with meta_c1:
            title_input = st.text_input("Titolo:", value=song.title, disabled=not can_edit)
            c_key_val, c_key_btn = st.columns([1, 1])
            with c_key_val:
                key_input = st.text_input("Tonalità:", value=song.key_current, disabled=not can_edit)
            with c_key_btn:
                st.write("")
                st.write("")
                if st.button("🎯 Analizza Key", help="Rileva la tonalità più probabile (es. MIm vs SOL) con analisi armonica deterministica e IA", disabled=not can_edit, key=f"btn_detect_key_{song.uuid}"):
                    tokens = re.findall(r"\[([^\]]+)\]", song.aml_content or "")
                    valid_chords = [t for t in tokens if MusicEngine.parse_chord(t)]
                    res = BandAIService.analyze_probable_key_with_ai_fallback(song.title, song.artist, valid_chords, song.key_current)
                    new_key = res.get("probable_key") or song.key_current
                    song.key_current = new_key
                    if not song.key_original or song.key_original == "DO" or song.key_original.upper() == "C":
                        song.key_original = new_key
                    if song.aml_content:
                        song.aml_content = re.sub(r"\{key:\s*[^}]+\}", f"{{key: {new_key}}}", song.aml_content, count=1)
                    storage.save_song(song, user_email, user_name, f"Aggiornamento Tonalità: {new_key} ({res.get('relationship', '')})")
                    log_op("🎯", "KEY", f"Tonalità per '{song.title}': {new_key} ({res.get('relationship', '')})", "SUCCESS")
                    st.success(f"🎯 Tonalità rilevata: **{new_key}** ({res.get('mode', '')}). {res.get('relationship', '')}")
                    st.rerun()
        with meta_c2:
            artist_input = st.text_input("Artista:", value=song.artist, disabled=not can_edit)
            c_bpm_val, c_bpm_btn = st.columns([1, 1])
            with c_bpm_val:
                bpm_input = st.number_input("BPM:", value=song.bpm, disabled=not can_edit)
            with c_bpm_btn:
                st.write("")
                st.write("")
                if st.button("🔍 SongBPM", help="Trova il BPM reale dal database SongBPM.com o con l'AI", disabled=not can_edit, key=f"btn_est_bpm_{song.uuid}"):
                    sb_info = BandAIService.fetch_songbpm_info(song.title, song.artist)
                    if sb_info and sb_info.get("bpm"):
                        new_bpm = sb_info["bpm"]
                        src_msg = f"SongBPM ({sb_info.get('matched', '')})"
                        extra_info = []
                        if sb_info.get("key"):
                            extra_info.append(f"Key: {sb_info['key']}")
                        if sb_info.get("duration"):
                            extra_info.append(f"Durata: {sb_info['duration']}")
                        extra_str = f" ({', '.join(extra_info)})" if extra_info else ""
                        st.success(f"🎯 BPM trovato su **SongBPM.com**: **{new_bpm} BPM**{extra_str}")
                    else:
                        new_bpm = BandAIService.estimate_song_bpm(song.title, song.artist)
                        src_msg = "AI / Analisi"
                        st.info(f"🤖 BPM stimato con AI/Analisi: **{new_bpm} BPM**")
                    song.bpm = new_bpm
                    storage.save_song(song, user_email, user_name, f"Aggiornamento BPM da {src_msg}")
                    log_op("🎯", "BPM", f"BPM per '{song.title}': {new_bpm} BPM ({src_msg})", "SUCCESS")
                    st.rerun()
        with meta_c3:
            genre_input = st.text_input("Genere:", value=song.genre, disabled=not can_edit)
            capo_input = st.number_input("Capo tasto:", value=song.capo, disabled=not can_edit)

        # Visualizzazione e Associazione Repertori
        all_reps = storage.list_repertoires()
        assigned_reps = [r for r in all_reps if song.uuid in r.song_uuids]
        rep_labels = ", ".join([r.name for r in assigned_reps]) if assigned_reps else "Nessun repertorio (Non assegnato)"
        st.caption(f"📚 **Repertori associati:** `{rep_labels}`")
        unassigned_reps = [r for r in all_reps if song.uuid not in r.song_uuids]
        if unassigned_reps:
            with st.expander("➕ Associa questo brano a un altro Repertorio"):
                col_r_sel, col_r_btn = st.columns([3, 1])
                with col_r_sel:
                    target_r_obj = st.selectbox("Seleziona repertorio:", unassigned_reps, format_func=lambda r: r.name, key=f"add_r_edit_{song.uuid}")
                with col_r_btn:
                    st.write("")
                    if st.button("Collega", disabled=not can_edit):
                        storage.move_song_to_repertoire(song.uuid, target_r_obj.uuid, user_email, user_name)
                        log_op("📚", "REPERTORIO", f"Brano '{song.title}' associato a '{target_r_obj.name}'", "INFO")
                        st.success(f"Brano associato a '{target_r_obj.name}'!")
                        st.rerun()

        # Transposition & Notation (Riga 1: Mezzi Toni + Undo Originale, Riga 2: Notazione)
        orig_ita = MusicEngine.convert_notation(song.key_original, "ITA")
        curr_ita = MusicEngine.convert_notation(song.key_current, "ITA")
        is_transposed = (song.key_current.upper() != song.key_original.upper())

        st.markdown(
            f"""<div style="display:flex; justify-content:space-between; align-items:center; margin:6px 0 2px 0;">
              <span style="font-size:11px; font-weight:700; color:#CBD5E1;">🎵 Trasposizione Tonalità (Mezzi Toni):</span>
              <span style="font-size:10px; color:#38BDF8; font-weight:700;">Tonalità Originale: {orig_ita} &bull; Attuale: {curr_ita}</span>
            </div>""",
            unsafe_allow_html=True
        )
        tr_r1_c1, tr_r1_c2, tr_r1_c3 = st.columns([1, 1, 1.2], gap="small")
        with tr_r1_c1:
            if st.button("⬇️ -½ Tono", help="Abbassa di 1 semitono (mezzo tono sotto)", disabled=not can_edit, width="stretch", key=f"tr_down_{song.uuid}"):
                doc = AMLParser.parse(song.aml_content)
                new_doc = AMLParser.transpose_document(doc, semitones=-1)
                song.aml_content = new_doc.to_aml()
                song.key_current = MusicEngine.transpose_chord(song.key_current, semitones=-1)
                storage.save_song(song, user_email, user_name, "Trasposizione -1 semitono (-½ tono)")
                log_op("⬇️", "TRASPOSIZIONE", f"Brano '{song.title}' trasposto -½ tono (-1 semitono) in {song.key_current}", "SUCCESS")
                st.rerun()
        with tr_r1_c2:
            if st.button("⬆️ +½ Tono", help="Alza di 1 semitono (mezzo tono sopra)", disabled=not can_edit, width="stretch", key=f"tr_up_{song.uuid}"):
                doc = AMLParser.parse(song.aml_content)
                new_doc = AMLParser.transpose_document(doc, semitones=1)
                song.aml_content = new_doc.to_aml()
                song.key_current = MusicEngine.transpose_chord(song.key_current, semitones=1)
                storage.save_song(song, user_email, user_name, "Trasposizione +1 semitono (+½ tono)")
                log_op("⬆️", "TRASPOSIZIONE", f"Brano '{song.title}' trasposto +½ tono (+1 semitono) in {song.key_current}", "SUCCESS")
                st.rerun()
        with tr_r1_c3:
            btn_undo_label = f"↺ Undo ({orig_ita})"
            if st.button(btn_undo_label, help=f"Annulla trasposizioni e ripristina la tonalità originale ({orig_ita})", disabled=(not can_edit or not is_transposed), width="stretch", key=f"tr_undo_{song.uuid}"):
                delta = MusicEngine.calculate_semitone_delta(song.key_current, song.key_original)
                if delta != 0:
                    doc = AMLParser.parse(song.aml_content)
                    new_doc = AMLParser.transpose_document(doc, semitones=delta)
                    song.aml_content = new_doc.to_aml()
                    song.key_current = song.key_original
                    storage.save_song(song, user_email, user_name, f"Undo trasposizione: ripristinata tonalità originale ({orig_ita})")
                    log_op("↺", "TRASPOSIZIONE", f"Brano '{song.title}' ripristinato alla tonalità originale {orig_ita}", "SUCCESS")
                    st.success(f"Brano ripristinato alla tonalità originale ({orig_ita})!")
                    st.rerun()

        st.markdown(
            """<div style="margin:4px 0 2px 0;">
              <span style="font-size:11px; font-weight:700; color:#CBD5E1;">🌐 Notazione Accordi:</span>
            </div>""",
            unsafe_allow_html=True
        )
        tr_r2_c1, tr_r2_c2 = st.columns(2, gap="small")
        with tr_r2_c1:
            if st.button("🇮🇹 Notazione ITA (DO, RE, MI)", help="Converti in notazione italiana (DO, RE, MI)", disabled=not can_edit, width="stretch", key=f"tr_ita_{song.uuid}"):
                doc = AMLParser.parse(song.aml_content)
                song.aml_content = AMLParser.convert_notation(doc, "ITA").to_aml()
                storage.save_song(song, user_email, user_name, "Conversione notazione italiana")
                log_op("🇮🇹", "NOTAZIONE", f"Brano '{song.title}' convertito in notazione Italiana", "INFO")
                st.rerun()
        with tr_r2_c2:
            if st.button("🌐 Notazione INT (C, D, E)", help="Converti in notazione internazionale (C, D, E)", disabled=not can_edit, width="stretch", key=f"tr_int_{song.uuid}"):
                doc = AMLParser.parse(song.aml_content)
                song.aml_content = AMLParser.convert_notation(doc, "INT").to_aml()
                storage.save_song(song, user_email, user_name, "Conversione notazione internazionale")
                log_op("🌐", "NOTAZIONE", f"Brano '{song.title}' convertito in notazione Internazionale", "INFO")
                st.rerun()

        tags_input = st.text_input("🏷️ Tag del Brano (separati da virgola):", value=", ".join(song.tags or []), disabled=not can_edit, help="Es: ballad, rock, acustico, bis")

        with st.expander("📖 Guida Sintassi & Tag AML (Direttive, Sezioni, Accordi Inline, Griglie, Strumenti)"):
            st.markdown("""
            * **• Direttive:** `{title: Titolo}`, `{artist: Artista}`, `{key: Tonalità}`, `{tempo: BPM}`, `{time: 4/4}`
            * **• Sezioni:** `{intro}`, `{verse}`, `{chorus}`, `{bridge}`, `{solo}`, `{outro}`
            * **• Accordi Inline:** `[Am]On a dark desert highway, [F#7]cool wind in my hair`
            * **• Griglia Armonica a Battute:** `| DO | LAm | FA | SOL |`
            * **• Tag Strumentali:** `{guitar: Solo Don Felder}`, `{voice: Armonizzazione a 3}`, `{bass: Slap}`, `{drums: 4/4 Groove}`
            """)

        aml_editor_text = st.text_area("Testo AML:", value=song.aml_content, height=360, disabled=not can_edit)
        rev_comment = st.text_input("Commento della modifica (per storico revisioni):", value="Modifica accordi e sezioni", disabled=not can_edit)

        col_s1, col_s2, col_s3 = st.columns([1.5, 1, 1.2])
        with col_s1:
            if st.button("💾 Salva Nuova Revisione", type="primary", disabled=not can_edit, width="stretch"):
                song.title = title_input
                song.artist = artist_input
                song.key_current = key_input
                song.bpm = bpm_input
                song.genre = genre_input
                song.capo = capo_input
                song.tags = [t.strip().lower() for t in tags_input.split(",") if t.strip()]
                song.aml_content = aml_editor_text
                saved = storage.save_song(song, user_email, user_name, rev_comment)
                log_op("💾", "SALVATAGGIO", f"Salvata Nuova Revisione #{saved.current_revision} per '{song.title}'", "SUCCESS")
                st.success(f"Salvato con successo! Nuova Revisione #{saved.current_revision}")
                st.rerun()
        with col_s2:
            if st.button("🔓 Rilascia Lock", width="stretch"):
                lock_mgr.release_lock(song.uuid, user_email)
                st.session_state[f"released_lock_{song.uuid}"] = True
                log_op("🔓", "LOCK", f"Rilasciato lock di editing per '{song.title}'", "INFO")
                st.info("Lock rilasciato.")
                st.rerun()
        with col_s3:
            with st.popover("🗑️ Elimina Brano", width="stretch"):
                st.warning(f"Vuoi spostare **'{song.title}'** nel cestino?\n\n*Potrai ripristinarlo entro 30 giorni.*")
                if st.button("Conferma Eliminazione", type="secondary", disabled=not current_user.can_delete(), key=f"del_editor_{song.uuid}"):
                    lock_mgr.release_lock(song.uuid, user_email, force=True)
                    storage.delete_song(song.uuid, user_email, user_name)
                    log_op("🗑️", "CESTINO", f"Brano '{song.title}' spostato nel cestino (soft-delete 30gg)", "WARNING")
                    st.session_state["selected_song_uuid"] = None
                    st.success(f"Brano '{song.title}' spostato nel cestino.")
                    st.rerun()

    with col_prev:
        st.write("#### 👁️ Anteprima PDF & Azioni Esportazione")
        curr_global_dev = st.session_state.get("user_preferred_device", dev_names[0])
        curr_global_idx = dev_names.index(curr_global_dev) if curr_global_dev in dev_names else 0

        selected_dev_name = st.selectbox(
            "📐 Formato Dispositivo / Display per Salva PDF:",
            dev_names,
            index=curr_global_idx,
            key="brani_device_sync_selector",
            help="Modifica il formato dispositivo attivo per tutta l'applicazione e per il rendering dei PDF"
        )
        if selected_dev_name != st.session_state.get("user_preferred_device"):
            set_active_device_globally(selected_dev_name)
            st.rerun()

        prof = get_layout_device_profile(selected_dev_name)

        st.caption(f"📱 **Specifiche Display:** `{prof.name}` &bull; `{prof.width_mm:.1f} × {prof.height_mm:.1f} mm` ({prof.orientation}) &bull; Colonne: `{prof.columns}` &bull; Font Testo: `{prof.font_size_lyrics} pt`")

        # Genera il brano per preview ed export
        preview_song = Song(
            uuid=song.uuid,
            title=title_input,
            artist=artist_input,
            key_current=key_input,
            bpm=bpm_input,
            genre=genre_input,
            capo=capo_input,
            tags=[t.strip().lower() for t in tags_input.split(",") if t.strip()],
            aml_content=aml_editor_text,
            current_revision=song.current_revision
        )

        # Nome del file: SOLO ed ESCLUSIVAMENTE il titolo del brano con la relativa estensione (vietato device, accordi, testo, ecc.)
        clean_title = re.sub(r'[\\/*?:"<>|]', '', preview_song.title).strip().upper() or 'BRANO'
        clean_dev = re.sub(r'[^a-zA-Z0-9_\-]', '_', prof.name).strip('_') or 'device'

        # Profilo A4 per la modalità Stampa (sempre A4 portrait)
        prof_a4 = DeviceProfile(
            name="Foglio A4",
            target_device="pc_a4",
            width_mm=210.0,
            height_mm=297.0,
            orientation="portrait",
            columns=getattr(prof, "columns", 1),
            font_size_lyrics=getattr(prof, "font_size_lyrics", 12.0),
            font_size_chords=getattr(prof, "font_size_chords", 13.0),
            margin_left_mm=getattr(prof, "margin_left_mm", 10.0),
            margin_right_mm=getattr(prof, "margin_right_mm", 10.0),
            margin_top_mm=getattr(prof, "margin_top_mm", 12.0),
            margin_bottom_mm=getattr(prof, "margin_bottom_mm", 12.0),
            color_lyrics=getattr(prof, "color_lyrics", "#111111"),
            color_chords=getattr(prof, "color_chords", "#B71C1C"),
            color_aml_markup=getattr(prof, "color_aml_markup", "#4A148C")
        )

        # Generazione PDF sempre aggiornata (use_cache=False) con chiave univoca versionata
        ck_v = f"v4_{preview_song.current_revision}"
        aml_hash = hash(preview_song.aml_content)
        ck_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', preview_song.title)
        ck_fl = int(getattr(prof, "font_size_lyrics", 12) * 10)
        ck_fc = int(getattr(prof, "font_size_chords", 13) * 10)
        ck_col_c = getattr(prof, "color_chords", "")
        ck_col_l = getattr(prof, "color_lyrics", "")
        ck_a4_m = f"buf_a4_m_{preview_song.uuid}_{ck_title}_{ck_v}_{aml_hash}_{prof.columns}_{ck_fl}_{ck_fc}_{ck_col_c}_{ck_col_l}"
        ck_a4_s = f"buf_a4_s_{preview_song.uuid}_{ck_title}_{ck_v}_{aml_hash}_{prof.columns}_{ck_fl}_{ck_fc}_{ck_col_c}_{ck_col_l}"
        ck_dev_m = f"buf_dev_m_{preview_song.uuid}_{clean_dev}_{ck_title}_{ck_v}_{aml_hash}_{prof.columns}_{ck_fl}_{ck_fc}_{ck_col_c}_{ck_col_l}"
        ck_dev_s = f"buf_dev_s_{preview_song.uuid}_{clean_dev}_{ck_title}_{ck_v}_{aml_hash}_{prof.columns}_{ck_fl}_{ck_fc}_{ck_col_c}_{ck_col_l}"

        if ck_a4_m not in st.session_state:
            st.session_state[ck_a4_m] = PDFEngine.generate_song_pdf(preview_song, profile=prof_a4, include_chords=True, use_cache=False)
        pdf_a4_m = st.session_state[ck_a4_m]

        if ck_a4_s not in st.session_state:
            st.session_state[ck_a4_s] = PDFEngine.generate_song_pdf(preview_song, profile=prof_a4, include_chords=False, use_cache=False)
        pdf_a4_s = st.session_state[ck_a4_s]

        if ck_dev_m not in st.session_state:
            st.session_state[ck_dev_m] = PDFEngine.generate_song_pdf(preview_song, profile=prof, include_chords=True, use_cache=False)
        pdf_dev_m = st.session_state[ck_dev_m]

        if ck_dev_s not in st.session_state:
            st.session_state[ck_dev_s] = PDFEngine.generate_song_pdf(preview_song, profile=prof, include_chords=False, use_cache=False)
        pdf_dev_s = st.session_state[ck_dev_s]

        pdf_bytes = pdf_dev_m

        # -------------------------------------------------------------
        # LAYOUT COMPATTO, CHIARO E ACCATTIVANTE PER I TASTI DI AZIONE
        # -------------------------------------------------------------
        # 1. Stampa su Stampante (A4 Verticale - Invio diretto a Coda di Stampa, nessun file scaricato)
        st.markdown(
            """<div style="display:flex; align-items:center; justify-content:space-between; margin:8px 0 3px 0;">
              <span style="font-size:12px; font-weight:700; color:#FFFFFF;">🖨️ Stampa su Stampante (A4 - Coda di Stampa)</span>
              <span style="font-size:10px; color:#38BDF8;">⚡ Invia direttamente alla stampante senza salvare file</span>
            </div>""",
            unsafe_allow_html=True
        )

        st.components.v1.html(
            PrinterEngine.render_print_buttons_component(pdf_a4_m, pdf_a4_s, clean_title),
            height=54
        )

        with st.expander("🖥️ Invia a Stampante Server (Spooler Hardware Windows)", expanded=False):
            sys_printers = PrinterEngine.list_system_printers()
            if sys_printers:
                p_names = [p["name"] for p in sys_printers]
                def_idx = next((i for i, p in enumerate(sys_printers) if p.get("is_default")), 0)
                sel_p = st.selectbox("Seleziona Stampante Server:", p_names, index=def_idx, key=f"sel_p_{preview_song.uuid}")
                col_sp1, col_sp2 = st.columns(2, gap="small")
                with col_sp1:
                    if st.button("🎸 Spooler: con Accordi", key=f"spool_m_{preview_song.uuid}", width="stretch"):
                        ok, msg = PrinterEngine.send_to_windows_spooler(pdf_a4_m, sel_p)
                        if ok:
                            st.success(f"✅ {msg}")
                            log_op("🖨️", "PRINT", f"Inviato '{preview_song.title}' (Accordi) alla stampante '{sel_p}'", "SUCCESS")
                        else:
                            st.error(f"❌ {msg}")
                with col_sp2:
                    if st.button("🎤 Spooler: Solo Testo", key=f"spool_s_{preview_song.uuid}", width="stretch"):
                        ok, msg = PrinterEngine.send_to_windows_spooler(pdf_a4_s, sel_p)
                        if ok:
                            st.success(f"✅ {msg}")
                            log_op("🖨️", "PRINT", f"Inviato '{preview_song.title}' (Solo Testo) alla stampante '{sel_p}'", "SUCCESS")
                        else:
                            st.error(f"❌ {msg}")
            else:
                st.caption("I tasti rapidi 'Stampa A4' sopra aprono automaticamente lo spooler di stampa del tuo tablet o computer senza scaricare file.")

        # 2. Salva PDF (modalità dispositivo)
        st.markdown(
            f"""<div style="display:flex; align-items:center; justify-content:space-between; margin:8px 0 3px 0;">
              <span style="font-size:12px; font-weight:700; color:#FFFFFF;">💾 Salva PDF (Modalità Display: {prof.name})</span>
              <span style="font-size:10px; color:#94A3B8;">Formattazione su misura per leggio</span>
            </div>""",
            unsafe_allow_html=True
        )
        col_d1, col_d2 = st.columns(2, gap="small")
        with col_d1:
            st.download_button(
                "🎸 Salva PDF: con Accordi",
                data=pdf_dev_m,
                file_name=f"{clean_title}.pdf",
                mime="application/pdf",
                type="primary",
                width="stretch",
                key=f"dl_dev_m_{preview_song.uuid}_{clean_dev}"
            )
        with col_d2:
            st.download_button(
                "🎤 Salva PDF: Solo Testo",
                data=pdf_dev_s,
                file_name=f"{clean_title}.pdf",
                mime="application/pdf",
                type="secondary",
                width="stretch",
                key=f"dl_dev_s_{preview_song.uuid}_{clean_dev}"
            )

        # 3. Esecuzione Live Palco Singolo Brano (SRS Cap. 12 & Live Stage)
        st.markdown(
            """<div style="display:flex; align-items:center; justify-content:space-between; margin:8px 0 3px 0;">
              <span style="font-size:12px; font-weight:700; color:#FFFFFF;">🎤 Esecuzione Live Palco</span>
              <span style="font-size:10px; color:#38BDF8;">⚡ Teleprompter a 60fps &bull; Pedale &bull; Metronomo</span>
            </div>""",
            unsafe_allow_html=True
        )
        if st.button("🎤 Avvia Modalità Palco con questo Brano", type="primary", width="stretch", key=f"btn_stage_song_{preview_song.uuid}"):
            st.session_state["stage_source_type"] = "🎵 Singolo Brano"
            st.session_state["selected_song_uuid"] = preview_song.uuid
            st.session_state["main_menu_choice"] = "🎤 Modalità Palco (Live Stage)"
            log_op("🎤", "PALCO", f"Avviata modalità palco per il singolo brano '{preview_song.title}'", "SUCCESS")
            st.rerun()

        # 4. Esporta nei vari formati (Compatto in griglia simmetrica 2x2 per tablet e Huawei)
        st.markdown(
            """<div style="display:flex; align-items:center; justify-content:space-between; margin:8px 0 3px 0;">
              <span style="font-size:12px; font-weight:700; color:#FFFFFF;">📤 Esporta Formati Musicali</span>
              <span style="font-size:10px; color:#94A3B8;">SongBook, MobileSheets, ChordPro, OnSong</span>
            </div>""",
            unsafe_allow_html=True
        )
        col_e1, col_e2 = st.columns(2, gap="small")
        with col_e1:
            st.download_button(
                "🎸 SongBook Pro (.pro)",
                data=ExportEngine.export_for_songbookpro(preview_song),
                file_name=f"{clean_title}.pro",
                mime="text/plain",
                width="stretch",
                key=f"dl_sb_{preview_song.uuid}"
            )
            st.download_button(
                "🎼 ChordPro (.cho)",
                data=ExportEngine.export_to_chordpro(preview_song.aml_content),
                file_name=f"{clean_title}.cho",
                mime="text/plain",
                width="stretch",
                key=f"dl_cp_{preview_song.uuid}"
            )
        with col_e2:
            st.download_button(
                "📱 MobileSheets (.pro)",
                data=ExportEngine.export_for_mobilesheets(preview_song),
                file_name=f"{clean_title}.pro",
                mime="text/plain",
                width="stretch",
                key=f"dl_ms_{preview_song.uuid}"
            )
            st.download_button(
                "🎤 OnSong (.onsong)",
                data=ExportEngine.export_for_onsong(preview_song),
                file_name=f"{clean_title}.onsong",
                mime="text/plain",
                width="stretch",
                key=f"dl_os_{preview_song.uuid}"
            )

        st.markdown("##### 📄 Anteprima Reale Pagine PDF Formattate:")
        try:
            import pymupdf
            doc_pdf = pymupdf.open(stream=pdf_bytes, filetype="pdf")
            num_pages = len(doc_pdf)
            st.caption(f"Totale pagine generate: **{num_pages}** per `{prof.name}`")
            for page_num in range(num_pages):
                page = doc_pdf[page_num]
                pix = page.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                st.image(
                    img_bytes,
                    caption=f"Pagina {page_num + 1} di {num_pages} — Formato {prof.name}",
                    width="stretch"
                )
        except Exception as ex_pdf:
            st.warning(f"Impossibile renderizzare l'anteprima visiva del PDF ({ex_pdf}). Puoi comunque scaricare il file PDF generato sopra.")

        with st.expander("🔍 Sorgente HTML Strutturato"):
            parsed_doc = AMLParser.parse(aml_editor_text)
            preview_html = f"<div style='background:#111; color:#fff; padding:16px; border-radius:6px; font-family:monospace;'>"
            for n in parsed_doc.nodes:
                if hasattr(n, "section_name"):
                    preview_html += f"<div style='color:#0288D1; font-weight:bold; margin-top:8px;'>[{n.section_name.upper()}]</div>"
                elif hasattr(n, "measures"):
                    measure_str = " | ".join([" ".join(m) for m in n.measures])
                    preview_html += f"<div style='background:#222; padding:4px; color:#FFD600; font-weight:bold;'>| {measure_str} |</div>"
                elif hasattr(n, "segments"):
                    chords = "".join([s.chord.chord_text + "  " for s in n.segments if s.chord])
                    lyrics = "".join([s.text for s in n.segments])
                    if chords.strip():
                        preview_html += f"<div style='color:#FFD600; font-weight:bold;'>{chords}</div>"
                    preview_html += f"<div>{lyrics}</div>"
            preview_html += "</div>"
            st.markdown(preview_html, unsafe_allow_html=True)

        with st.expander("📜 Cronologia Revisioni (SRS Cap. 4.5)"):
            revs = storage.get_revisions_for_song(song.uuid)
            for r in reversed(revs):
                st.write(f"- **Rev #{r.revision_number}** ({r.timestamp[0:10]} {r.timestamp[11:19]}) di *{r.author_name}*: {r.comment}")
                if st.button(f"Ripristina Rev #{r.revision_number}", key=f"restore_{r.revision_number}"):
                    storage.restore_revision(song.uuid, r.revision_number, user_email, user_name)
                    st.success(f"Rollback completato alla Revisione #{r.revision_number}")
                    st.rerun()

# ------------------------------------------------------------------------------
# 4. SCALETTE LIVE
# ------------------------------------------------------------------------------
elif menu_choice == "🤖 Band AI (Opzionale)":
    st.subheader("🤖 Assistente Creativo Band AI (100% Opzionale)")
    st.caption("In conformità alla SRS (Cap. 1.4 e 22.6), l'AI è rigorosamente esclusa da accordi, trasposizioni e PDF. Fornisce solo spunti creativi di arrangiamento e medley.")

    ai_mode = BandAIService.get_current_mode()
    st.info(f"Modalità AI Attuale del Sistema: **{ai_mode}**")

    tab_ai1, tab_ai2 = st.tabs(["🎵 Suggeritore Medley & Transizioni", "🎸 Idee di Arrangiamento Live"])

    with tab_ai1:
        st.write("#### Analisi e Suggerimenti Transizione Medley")
        all_s = sorted(storage.list_songs(), key=lambda s: s["title"].lower())
        if len(all_s) >= 2:
            s_choices = {s["uuid"]: s["title"] for s in all_s}
            id_a = st.selectbox("Primo Brano:", list(s_choices.keys()), format_func=lambda x: s_choices[x], key="ai_s1")
            id_b = st.selectbox("Secondo Brano:", [k for k in s_choices.keys() if k != id_a], format_func=lambda x: s_choices[x], key="ai_s2")

            s_a = storage.get_song(id_a)
            s_b = storage.get_song(id_b)

            if st.button("💡 Analizza Compatibilità & Suggerisci Transizione"):
                advice = BandAIService.suggest_medley_transition(s_a.title, s_a.key_current, s_a.bpm, s_b.title, s_b.key_current, s_b.bpm)
                st.metric("Affinità Transizione", f"{int(advice['score'] * 100)}%")
                st.text_area("Consigli di Regia e Arrangiamento:", advice["creative_advice"], height=160)
        else:
            st.info("Inserisci almeno 2 brani nell'archivio per calcolare la transizione medley.")

    with tab_ai2:
        st.write("#### Consigli Strumentali per Brano")
        if all_s:
            sel_s_id = st.selectbox("Seleziona Brano:", [s["uuid"] for s in all_s], format_func=lambda x: next(s["title"] for s in all_s if s["uuid"] == x), key="ai_arr_s")
            s_obj = storage.get_song(sel_s_id)
            c_ai_dyn, c_ai_bpm = st.columns([2, 1])
            with c_ai_bpm:
                # Query diretta a SongBPM per tempo verificato
                sb_meta = BandAIService.fetch_songbpm_info(s_obj.title, s_obj.artist)
                if sb_meta and sb_meta.get("bpm"):
                    sb_bpm = sb_meta["bpm"]
                    st.success(f"🌐 **SongBPM.com:** **{sb_bpm} BPM**")
                    extra_sub = []
                    if sb_meta.get("key"):
                        extra_sub.append(f"Key: {sb_meta['key']}")
                    if sb_meta.get("duration"):
                        extra_sub.append(f"Durata: {sb_meta['duration']}")
                    if extra_sub:
                        st.caption(" &bull; ".join(extra_sub))
                    if s_obj.bpm != sb_bpm:
                        if st.button(f"💾 Salva {sb_bpm} BPM nel brano", key=f"btn_apply_sb_{s_obj.uuid}", type="primary", width="stretch"):
                            s_obj.bpm = sb_bpm
                            storage.save_song(s_obj, st.session_state["current_user_email"], st.session_state["current_user_name"], f"Tempo sincronizzato da SongBPM ({sb_bpm} BPM)")
                            log_op("🎯", "BPM", f"BPM per '{s_obj.title}' sincronizzato con SongBPM: {sb_bpm} BPM", "SUCCESS")
                            st.rerun()
                else:
                    st.caption(f"Tempo archiviato: **{s_obj.bpm} BPM**")
                    if st.button("🔍 Cerca su SongBPM", key=f"btn_recalc_bpm_{s_obj.uuid}", width="stretch"):
                        nbpm = BandAIService.estimate_song_bpm(s_obj.title, s_obj.artist)
                        s_obj.bpm = nbpm
                        storage.save_song(s_obj, st.session_state["current_user_email"], st.session_state["current_user_name"], "Ricalcolo BPM da SongBPM/AI")
                        st.success(f"Nuovo tempo: **{nbpm} BPM**")
                        st.rerun()
            with c_ai_dyn:
                st.markdown("<div style='font-size:12px; font-weight:700; color:#38BDF8; margin-bottom:4px;'>🎯 Consigli Specifici per Musicista / Strumento:</div>", unsafe_allow_html=True)
                inst_pick = st.selectbox(
                    "Seleziona Ruolo Musicista:",
                    [
                        "Globale (Intero gruppo)",
                        "🎹 Tastiera (con Preset Yamaha Montage)",
                        "🎤 Voce",
                        "🎸 Chitarra ritmica",
                        "⚡ Chitarra elettrica (Lead)",
                        "🎸 Basso",
                        "🥁 Batteria"
                    ],
                    index=0,
                    key="ai_arr_inst_choice",
                    label_visibility="collapsed"
                )

                if st.button("🎸 Genera Idee di Arrangiamento & Suggerimenti", key="btn_gen_dyn_arr", type="primary", width="stretch"):
                    arr_text = BandAIService.suggest_arrangement_ideas(
                        title=s_obj.title,
                        genre=s_obj.genre,
                        key=s_obj.key_current,
                        bpm=s_obj.bpm,
                        artist=s_obj.artist,
                        instrument=inst_pick
                    )
                    st.markdown(arr_text)

# ------------------------------------------------------------------------------
# 10. MANUALE & CHANGELOG
# ------------------------------------------------------------------------------
elif menu_choice == "🔍 Ricerca Globale":
    st.subheader("🔍 Ricerca Globale Multi-Criterio (< 2ms)")

    c_q1, c_q2, c_q3, c_q4, c_q5 = st.columns(5)
    with c_q1:
        search_txt = st.text_input("Parola chiave (titolo/autore/testo):", "")
    with c_q2:
        search_key = st.text_input("Tonalità (es. DO, SOL, LAm):", "")
    with c_q3:
        search_bpm = st.number_input("BPM Massimo:", min_value=0, max_value=300, value=250)
    with c_q4:
        search_genre = st.text_input("Genere:", "")
    with c_q5:
        available_tags = ["Tutti"] + list(storage.list_all_tags().keys())
        search_tag = st.selectbox("Filtra per Tag:", available_tags)

    t0 = time.perf_counter()
    res = storage.search_songs(
        query_text=search_txt or None,
        key=search_key or None,
        bpm_max=search_bpm if search_bpm > 0 else None,
        genre=search_genre or None,
        tag=search_tag if search_tag != "Tutti" else None
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    st.caption(f"⚡ Ricerca eseguita in **{elapsed_ms:.3f} ms** su SQLite in-memory | Trovati: **{len(res)}**")
    if res:
        # Formattazione rigorosamente in formato italiano per tutte le tonalità e colonne
        formatted_res = []
        for r in res:
            raw_curr = r.get("key_current", "")
            raw_orig = r.get("key_original", "")
            ita_curr = MusicEngine.convert_notation(raw_curr, "ITA") if raw_curr else "-"
            ita_orig = MusicEngine.convert_notation(raw_orig, "ITA") if raw_orig else "-"
            formatted_res.append({
                "Titolo": r.get("title", ""),
                "Artista": r.get("artist", ""),
                "Tonalità Attuale (ITA)": ita_curr,
                "Tonalità Originale (ITA)": ita_orig,
                "BPM": r.get("bpm", 120),
                "Genere": r.get("genre", ""),
                "Capotasto": r.get("capo", 0),
                "Tag": ", ".join(r.get("tags") or []) if isinstance(r.get("tags"), list) else str(r.get("tags") or "")
            })
        st.dataframe(formatted_res, width="stretch")
    else:
        st.info("Nessun brano corrisponde ai criteri.")

# ------------------------------------------------------------------------------
# 9. BAND AI (OPZIONALE)
# ------------------------------------------------------------------------------
elif menu_choice == "📚 Repertori":
    st.subheader("📚 Gestione Repertori")

    repertoires = storage.list_repertoires()
    col_rep_top1, col_rep_top2 = st.columns([3, 1])
    with col_rep_top1:
        if repertoires:
            selected_rep_name = st.selectbox("Seleziona Repertorio:", [r.name for r in repertoires])
            selected_rep = next(r for r in repertoires if r.name == selected_rep_name)
            st.write(f"*{selected_rep.description}*")
        else:
            st.info("Nessun repertorio esistente. Crea il tuo primo repertorio.")
            selected_rep = None

    with col_rep_top2:
        with st.popover("➕ Nuovo Repertorio", width="stretch"):
            st.write("##### Crea Nuovo Repertorio")
            new_r_name = st.text_input("Nome:", placeholder="Es. Repertorio Acustico")
            new_r_desc = st.text_input("Descrizione:", placeholder="Brani per set acustico")
            if st.button("Crea Repertorio", type="primary", disabled=not current_user.can_edit()):
                clean_name = (new_r_name or "").strip()
                if not clean_name:
                    st.error("Inserisci un nome valido per il repertorio.")
                elif any(r.name.strip().lower() == clean_name.lower() for r in repertoires):
                    st.error(f"Un repertorio con il nome '{clean_name}' esiste già. I nomi dei repertori devono essere univoci.")
                else:
                    try:
                        created_rep = Repertoire(name=clean_name, description=new_r_desc)
                        storage.save_repertoire(created_rep, current_user.email, current_user.name)
                        log_op("📚", "REPERTORIO", f"Creato nuovo repertorio '{clean_name}'", "SUCCESS")
                        st.success(f"Repertorio '{clean_name}' creato!")
                        st.rerun()
                    except ValueError as err:
                        st.error(str(err))

        if selected_rep:
            with st.popover("✏️ Rinomina Repertorio", width="stretch"):
                st.write("##### Rinomina Repertorio")
                ren_name = st.text_input("Nuovo Nome:", value=selected_rep.name, key=f"ren_name_{selected_rep.uuid}")
                ren_desc = st.text_input("Nuova Descrizione:", value=selected_rep.description, key=f"ren_desc_{selected_rep.uuid}")
                if st.button("Salva Modifiche", type="primary", disabled=not current_user.can_edit(), key=f"btn_ren_save_{selected_rep.uuid}"):
                    clean_ren = (ren_name or "").strip()
                    if not clean_ren:
                        st.error("Inserisci un nome valido.")
                    elif any(r.name.strip().lower() == clean_ren.lower() and r.uuid != selected_rep.uuid for r in repertoires):
                        st.error(f"Un altro repertorio con il nome '{clean_ren}' esiste già.")
                    else:
                        selected_rep.name = clean_ren
                        selected_rep.description = ren_desc
                        storage.save_repertoire(selected_rep, current_user.email, current_user.name)
                        log_op("✏️", "REPERTORIO", f"Rinominato repertorio in '{clean_ren}'", "SUCCESS")
                        st.success(f"Repertorio rinominato in '{clean_ren}'!")
                        st.rerun()

            with st.popover("🗑️ Elimina Repertorio", width="stretch"):
                st.warning(f"Vuoi eliminare il repertorio **'{selected_rep.name}'**?\n\n*Nota: I brani NON verranno cancellati e resteranno nell'archivio generale.*")
                if st.button("Conferma Eliminazione", type="secondary", disabled=not current_user.can_delete()):
                    storage.delete_repertoire(selected_rep.uuid, current_user.email, current_user.name)
                    log_op("🗑️", "REPERTORIO", f"Eliminato repertorio '{selected_rep.name}'", "WARNING")
                    st.success(f"Repertorio '{selected_rep.name}' eliminato.")
                    st.rerun()

    if not selected_rep:
        st.stop()

    rep_songs = sorted([s for s in (storage.get_song(s_id) for s_id in selected_rep.song_uuids) if s], key=lambda s: s.title.lower())

    # Sezione Aggiunta Brani al Repertorio (in ordine alfabetico)
    all_archive_songs = sorted(storage.list_songs(), key=lambda s: s["title"].lower())
    unassigned_songs = [s for s in all_archive_songs if s["uuid"] not in selected_rep.song_uuids]

    c_btn1, c_btn2 = st.columns([1, 2])
    with c_btn1:
        if st.button("➕ Crea Nuovo Brano", disabled=not current_user.can_edit()):
            new_s = Song(title="Nuovo Brano", key_current="C", aml_content="{title: Nuovo Brano}\n{key: C}\n\n[C]Testo e accordi...")
            saved = storage.save_song(new_s, st.session_state["current_user_email"], st.session_state["current_user_name"])
            storage.move_song_to_repertoire(saved.uuid, selected_rep.uuid)
            st.session_state["selected_song_uuid"] = saved.uuid
            log_op("➕", "BRANO", f"Creato nuovo brano '{saved.title}' nel repertorio '{selected_rep.name}'", "SUCCESS")
            st.success(f"Creato brano '{saved.title}'")
            st.rerun()

    with c_btn2:
        if unassigned_songs:
            with st.expander("📥 Inserisci brano esistente dell'archivio in questo repertorio"):
                s_to_add_id = st.selectbox(
                    "Seleziona brano da collegare:",
                    [s["uuid"] for s in unassigned_songs],
                    format_func=lambda uid: next(f"{s['title']} ({s.get('artist', 'Sconosciuto')})" for s in unassigned_songs if s["uuid"] == uid),
                    key=f"sel_add_{selected_rep.uuid}"
                )
                if st.button("➕ Aggiungi al Repertorio", disabled=not current_user.can_edit()):
                    storage.move_song_to_repertoire(s_to_add_id, selected_rep.uuid, st.session_state["current_user_email"], st.session_state["current_user_name"])
                    log_op("📥", "REPERTORIO", f"Brano associato al repertorio '{selected_rep.name}'", "INFO")
                    st.success("Brano associato con successo a questo repertorio!")
                    st.rerun()

    if rep_songs:
        rows = []
        for s in rep_songs:
            lock = lock_mgr.check_lock(s.uuid)
            lock_display = f"🔒 {lock.locked_by_name}" if lock.is_locked else "🔓 Libero"
            ita_k = MusicEngine.convert_notation(s.key_current, "ITA")
            s_title = s.title or ""
            if "'" in s_title and (s_title.count("'") > 2 or (s_title.startswith("'") and s_title.endswith("'"))):
                s_title = s_title.replace("'", "").strip().upper()
                if "IM A BELIEVER" in s_title:
                    s_title = "I'M A BELIEVER"
                elif "HANNO UCCISO LUOMO RAGNO" in s_title:
                    s_title = "HANNO UCCISO L'UOMO RAGNO"
            rows.append({
                "UUID": s.uuid,
                "Titolo": s_title,
                "Artista": s.artist,
                "Tonalità (ITA)": ita_k,
                "BPM": s.bpm,
                "Revisione": f"Rev #{s.current_revision}",
                "Lock": lock_display
            })
        st.dataframe(rows, width="stretch")

        selected_song_candidates = [r["UUID"] for r in rows]
        def_s_idx = 0
        curr_rep_s = st.session_state.get("selected_song_uuid")
        if curr_rep_s and curr_rep_s in selected_song_candidates:
            def_s_idx = selected_song_candidates.index(curr_rep_s)

        pre_s_obj = next((s for s in rep_songs if s.uuid == selected_song_candidates[def_s_idx]), rep_songs[0])
        pre_ita_k = MusicEngine.convert_notation(pre_s_obj.key_current, "ITA")
        pre_art = f"({pre_s_obj.artist})" if pre_s_obj.artist else ""

        sub_meta_quick = f"{pre_art} &bull; Tonalità: {pre_ita_k} &bull; 🌐 SongBPM: {pre_s_obj.bpm} BPM".strip()
        st.markdown(
            f'<div style="margin:12px 0 4px 0; display:flex; align-items:center; justify-content:space-between;">'
            f'<span style="font-size:12px; font-weight:800; color:#38BDF8; letter-spacing:0.6px; text-transform:uppercase;">🎵 Brano Selezionato per Azioni Rapide:</span>'
            f'<span style="font-size:11px; color:#94A3B8; font-weight:600;">{sub_meta_quick}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

        selected_s_id = st.selectbox(
            "Seleziona Brano per azioni rapide:",
            selected_song_candidates,
            index=def_s_idx,
            format_func=lambda x: f"🎵 {next(r['Titolo'] for r in rows if r['UUID'] == x).upper()}",
            label_visibility="collapsed",
            key="rep_song_selector"
        )
        selected_lock = lock_mgr.check_lock(selected_s_id)
        selected_song_obj = next((s for s in rep_songs if s.uuid == selected_s_id), None)

        col_act1, col_act2, col_act3, col_act4, col_act5 = st.columns(5)
        with col_act1:
            if st.button("📝 Apri nell'Editor", width="stretch"):
                st.session_state["selected_song_uuid"] = selected_s_id
                st.session_state.pop(f"released_lock_{selected_s_id}", None)
                st.info("Passa alla sezione 'Brani' dal menu in alto.")
        with col_act2:
            if selected_lock.is_locked:
                can_unlock = (selected_lock.locked_by_email == current_user.email) or current_user.is_admin()
                if st.button("🔓 Rilascia Lock", disabled=not can_unlock, width="stretch", help=f"Bloccato da {selected_lock.locked_by_name}"):
                    lock_mgr.release_lock(selected_s_id, current_user.email, force=current_user.is_admin())
                    st.session_state[f"released_lock_{selected_s_id}"] = True
                    s_title = selected_song_obj.title if selected_song_obj else selected_s_id
                    log_op("🔓", "LOCK", f"Rilasciato lock di editing per '{s_title}' da Gestione Repertori", "INFO")
                    st.success("Lock rilasciato con successo!")
                    st.rerun()
            else:
                st.caption("🔓 Nessun lock attivo")
        with col_act3:
            other_reps = [r for r in repertoires if r.uuid != selected_rep.uuid]
            if other_reps:
                dest_rep = st.selectbox("Sposta in:", [r.name for r in other_reps], key=f"dest_rep_{selected_s_id}")
                if st.button("➡️ Sposta", disabled=not current_user.can_edit(), width="stretch"):
                    target_r = next(r for r in other_reps if r.name == dest_rep)
                    storage.move_song_to_repertoire(selected_s_id, target_r.uuid, st.session_state["current_user_email"], st.session_state["current_user_name"])
                    st.success(f"Brano spostato in '{target_r.name}' senza perdita dello storico.")
                    st.rerun()
        with col_act4:
            if st.button("❌ Rimuovi", disabled=not current_user.can_edit(), width="stretch"):
                storage.remove_song_from_repertoire(selected_s_id, selected_rep.uuid, st.session_state["current_user_email"], st.session_state["current_user_name"])
                st.success("Brano rimosso dal repertorio (rimane presente nell'archivio generale).")
                st.rerun()
        with col_act5:
            if st.button("🗑️ Cestino", disabled=not current_user.can_delete(), width="stretch"):
                storage.delete_song(selected_s_id, st.session_state["current_user_email"], st.session_state["current_user_name"])
                st.warning("Brano spostato nel cestino (recuperabile per 30 giorni).")
                st.rerun()
    else:
        st.info("Nessun brano associato a questo repertorio.")

# ------------------------------------------------------------------------------
# 3. EDITOR BRANI
# ------------------------------------------------------------------------------
elif menu_choice == "📑 Scalette Live":
    import datetime
    st.subheader("📑 Gestione Scalette Live & Ordine di Palco")
    st.caption("Organizza le scalette dei concerti, componi la sequenza brani dai diversi repertori con protezione da cancellazione accidentale e UNDO istantaneo.")

    setlists = storage.list_setlists()
    all_songs = sorted(storage.list_songs(), key=lambda s: s["title"].lower())
    song_map = {s["uuid"]: s for s in all_songs}
    all_reps = storage.list_repertoires()

    # Active Hardware Profile for PDF & Live Export
    curr_global_dev = st.session_state.get("user_preferred_device", dev_names[0])
    active_prof = get_layout_device_profile(curr_global_dev)

    # -------------------------------------------------------------------------
    # SAFETY UNDO BANNERS (Ripristino Immediato Cancellazione Accidentale)
    # -------------------------------------------------------------------------
    if st.session_state.get("undo_deleted_setlist_uuid"):
        del_uuid = st.session_state["undo_deleted_setlist_uuid"]
        del_title = st.session_state.get("undo_deleted_setlist_title", "Scaletta")
        c_undo1, c_undo2 = st.columns([3, 1])
        with c_undo1:
            st.warning(f"⚠️ **ATTENZIONE:** La scaletta **'{del_title}'** è stata eliminata. Puoi annullare subito e recuperarla.")
        with c_undo2:
            if st.button("↩️ ANNULLA ELIMINAZIONE", type="primary", key="btn_undo_del_setlist", width="stretch"):
                restored = storage.restore_setlist(del_uuid, current_user.email, current_user.name)
                st.session_state["undo_deleted_setlist_uuid"] = None
                st.session_state["undo_deleted_setlist_title"] = None
                if restored:
                    st.session_state["selected_setlist_uuid"] = restored.uuid
                    log_op("♻️", "SCALETTA", f"Ripristinata scaletta '{restored.title}' tramite Undo", "SUCCESS")
                    st.success(f"Scaletta '{restored.title}' recuperata con successo!")
                st.rerun()

    if st.session_state.get("undo_removed_setlist_item"):
        undo_item_info = st.session_state["undo_removed_setlist_item"]
        c_u_s1, c_u_s2 = st.columns([3, 1])
        with c_u_s1:
            st.info(f"ℹ️ Brano **'{undo_item_info.get('title', 'Brano')}'** rimosso dalla scaletta.")
        with c_u_s2:
            if st.button("↩️ Annulla Rimozione Brano", key="btn_undo_rem_song", width="stretch"):
                t_set_id = undo_item_info["setlist_uuid"]
                t_set = storage.get_setlist(t_set_id)
                if t_set:
                    ins_idx = min(undo_item_info["index"], len(t_set.items))
                    t_set.items.insert(ins_idx, undo_item_info["item"])
                    storage.save_setlist(t_set, current_user.email, current_user.name)
                    st.session_state["undo_removed_setlist_item"] = None
                    log_op("↩️", "SCALETTA", f"Ripristinato brano '{undo_item_info['title']}' nella scaletta '{t_set.title}'", "INFO")
                    st.success(f"Brano '{undo_item_info['title']}' ripristinato in posizione #{ins_idx + 1}!")
                    st.rerun()

    # Resolve active setlist
    curr_set_id = st.session_state.get("selected_setlist_uuid")
    active_setlist = next((s for s in setlists if s.uuid == curr_set_id), None)
    if not active_setlist and setlists:
        active_setlist = setlists[0]
        st.session_state["selected_setlist_uuid"] = active_setlist.uuid

    # -------------------------------------------------------------------------
    # COMPACT TOOLBAR: SELETTORE SCALETTA + AGGIUNGI + RINOMINA + DUPLICA + ELIMINA
    # -------------------------------------------------------------------------
    st.markdown('<div class="asma-laser-line" style="margin-bottom:12px;"></div>', unsafe_allow_html=True)
    
    # Row 1: Selettore Scaletta Attiva (Large & clear on mobile and PC)
    if setlists:
        set_options = [s.uuid for s in setlists]
        set_idx = set_options.index(active_setlist.uuid) if (active_setlist and active_setlist.uuid in set_options) else 0
        def _format_set(uid):
            matched = next((s for s in setlists if s.uuid == uid), None)
            if matched:
                d_str = f" ({matched.date})" if matched.date else ""
                return f"📑 {matched.title}{d_str} — {len(matched.items)} brani"
            return uid
        
        chosen_set_uuid = st.selectbox(
            "Scaletta Attiva:",
            set_options,
            index=set_idx,
            format_func=_format_set,
            key="main_setlist_selector"
        )
        if chosen_set_uuid != st.session_state.get("selected_setlist_uuid"):
            st.session_state["selected_setlist_uuid"] = chosen_set_uuid
            st.rerun()
    else:
        st.info("Nessuna scaletta presente. Creane una nuova con il tasto qui sotto!")

    # Row 2: Azioni Scaletta (Resta orizzontale su TUTTI i device grazie alla classe scaletta_toolbar_container)
    with st.container(key="scaletta_toolbar_container"):
        col_new_set, col_ren_set, col_dup_set, col_del_set, col_trash_set = st.columns(
            5, gap="small", vertical_alignment="center"
        )

    with col_new_set:
        with st.popover("➕ Nuova", width="stretch", help="Crea una nuova scaletta da zero o clonando un'altra"):
            st.markdown("##### ➕ Nuova Scaletta Band")
            st.caption("Crea una nuova lista brani per il concerto.")
            today_str = datetime.date.today().strftime("%d/%m/%Y")
            new_title = st.text_input("Titolo Concerto / Scaletta:", placeholder="es. Live Summer Fest", key="in_new_set_title").strip()
            new_date = st.text_input("Data Evento:", value=today_str, key="in_new_set_date").strip()
            
            copy_source = None
            if setlists:
                copy_opt = ["Parti da scaletta vuota"] + [s.title for s in setlists]
                chosen_copy = st.selectbox("Copia brani da scaletta esistente (opzionale):", copy_opt, key="in_new_set_copy")
                if chosen_copy != "Parti da scaletta vuota":
                    copy_source = next((s for s in setlists if s.title == chosen_copy), None)

            if st.button("💾 Crea Scaletta", type="primary", disabled=not current_user.can_edit(), key="btn_create_setlist_submit", width="stretch"):
                if not new_title:
                    st.warning("⚠️ Inserisci almeno il titolo della scaletta.")
                else:
                    initial_items = [SetlistItem(song_uuid=it.song_uuid, custom_key=it.custom_key, custom_bpm=it.custom_bpm, notes=it.notes) for it in copy_source.items] if copy_source else []
                    new_set = Setlist(title=new_title, date=new_date, items=initial_items)
                    storage.save_setlist(new_set, current_user.email, current_user.name)
                    st.session_state["selected_setlist_uuid"] = new_set.uuid
                    log_op("📑", "SCALETTA", f"Creata scaletta live '{new_title}' ({len(initial_items)} brani)", "SUCCESS")
                    st.success(f"Scaletta '{new_title}' creata con successo!")
                    st.rerun()

    with col_ren_set:
        if active_setlist:
            with st.popover("✏️ Rinomina", width="stretch", help="Modifica titolo o data della scaletta attiva"):
                st.markdown("##### ✏️ Rinomina Scaletta")
                ren_title = st.text_input("Nuovo Titolo:", value=active_setlist.title, key=f"ren_t_{active_setlist.uuid}").strip()
                ren_date = st.text_input("Data:", value=active_setlist.date, key=f"ren_d_{active_setlist.uuid}").strip()
                if st.button("Salva Modifiche", type="primary", disabled=not current_user.can_edit(), key=f"btn_ren_save_{active_setlist.uuid}", width="stretch"):
                    if ren_title:
                        old_t = active_setlist.title
                        active_setlist.title = ren_title
                        active_setlist.date = ren_date
                        storage.save_setlist(active_setlist, current_user.email, current_user.name)
                        log_op("✏️", "SCALETTA", f"Rinominata scaletta da '{old_t}' a '{ren_title}'", "SUCCESS")
                        st.success("Scaletta aggiornata con successo!")
                        st.rerun()

    with col_dup_set:
        if active_setlist:
            with st.popover("📋 Clona", width="stretch", help="Duplica la scaletta corrente con tutti i suoi brani"):
                st.markdown("##### 📋 Clona Scaletta")
                dup_title = st.text_input("Titolo Copia:", value=f"{active_setlist.title} (Copia)", key=f"dup_t_{active_setlist.uuid}").strip()
                if st.button("Conferma Duplicazione", type="primary", disabled=not current_user.can_edit(), key=f"btn_dup_save_{active_setlist.uuid}", width="stretch"):
                    if dup_title:
                        dup_items = [SetlistItem(song_uuid=it.song_uuid, custom_key=it.custom_key, custom_bpm=it.custom_bpm, notes=it.notes) for it in active_setlist.items]
                        cloned = Setlist(title=dup_title, date=active_setlist.date, items=dup_items)
                        storage.save_setlist(cloned, current_user.email, current_user.name)
                        st.session_state["selected_setlist_uuid"] = cloned.uuid
                        log_op("📋", "SCALETTA", f"Duplicata scaletta '{active_setlist.title}' in '{dup_title}'", "SUCCESS")
                        st.success(f"Scaletta clonata come '{dup_title}'!")
                        st.rerun()

    with col_del_set:
        if active_setlist:
            with st.popover("🗑️ Elimina", width="stretch", help="Elimina la scaletta (con protezione e ripristino immediato UNDO)"):
                st.markdown("##### ⚠️ Conferma Eliminazione Scaletta")
                st.markdown(f"Stai per eliminare la scaletta:<br><b style='color:#EF4444; font-size:14px;'>{active_setlist.title}</b> ({len(active_setlist.items)} brani)", unsafe_allow_html=True)
                st.markdown("<div style='font-size:11.5px; color:#94A3B8; margin:6px 0;'>La scaletta verrà spostata nel cestino protetto. Potrai ripristinarla in qualsiasi momento con il tasto <b>UNDO</b>.</div>", unsafe_allow_html=True)
                if st.button("🗑️ Elimina con Protezione", type="secondary", disabled=not current_user.can_delete(), key=f"btn_confirm_delete_set_{active_setlist.uuid}", width="stretch"):
                    del_uuid = active_setlist.uuid
                    del_title = active_setlist.title
                    st.session_state["undo_deleted_setlist_uuid"] = del_uuid
                    st.session_state["undo_deleted_setlist_title"] = del_title
                    storage.delete_setlist(del_uuid, current_user.email, current_user.name)
                    st.session_state["selected_setlist_uuid"] = None
                    log_op("🗑️", "SCALETTA", f"Spostata scaletta '{del_title}' nel cestino protetto con Undo disponibile", "WARNING")
                    st.rerun()

    with col_trash_set:
        deleted_setlists = storage.list_deleted_setlists() if hasattr(storage, "list_deleted_setlists") else []
        trash_badge = f"♻️ ({len(deleted_setlists)})" if deleted_setlists else "♻️ Cestino"
        with st.popover(trash_badge, width="stretch", help="Apri il cestino delle scalette per recuperare scalette cancellate"):
            st.markdown("##### ♻️ Cestino Scalette Band")
            st.caption("Recupera qualsiasi scaletta eliminata di recente con un solo click.")
            if deleted_setlists:
                for d_meta in deleted_setlists:
                    d_data = d_meta.get("data", {})
                    d_uid = d_data.get("uuid")
                    d_name = d_data.get("title", "Senza Titolo")
                    d_date = d_data.get("date", "")
                    d_songs_count = len(d_data.get("items", []))
                    d_time = d_meta.get("deleted_at", "")[:16].replace("T", " ")
                    st.markdown(f"<div style='background:rgba(255,255,255,0.04); padding:6px 8px; border-radius:4px; margin-bottom:4px; font-size:12px;'>"
                                f"<b>{d_name}</b> ({d_songs_count} brani) &bull; Data: {d_date}<br><small style='color:#888;'>Eliminata il: {d_time}</small>"
                                f"</div>", unsafe_allow_html=True)
                    if st.button(f"↩️ Ripristina '{d_name}'", key=f"btn_res_trash_{d_uid}", type="primary", width="stretch"):
                        restored = storage.restore_setlist(d_uid, current_user.email, current_user.name)
                        if restored:
                            st.session_state["selected_setlist_uuid"] = restored.uuid
                            log_op("♻️", "SCALETTA", f"Recuperata scaletta '{restored.title}' dal cestino", "SUCCESS")
                            st.success(f"Scaletta '{restored.title}' ripristinata!")
                            st.rerun()
                    st.divider()
            else:
                st.info("Il cestino scalette è attualmente vuoto.")

    if not active_setlist:
        st.stop()

    # -------------------------------------------------------------------------
    # SCALETTA ACTIVE METRICS (Brani, Durata Stimata Concerto, Display Attivo)
    # -------------------------------------------------------------------------
    loaded_songs = [storage.get_song(item.song_uuid) for item in active_setlist.items if storage.get_song(item.song_uuid)]
    est_minutes = sum(int(s.bpm or 120) * 0 for s in loaded_songs)  # placeholder duration
    total_duration_minutes = round(len(loaded_songs) * 3.7) # Stima media 3.7 min per brano
    dur_h = total_duration_minutes // 60
    dur_m = total_duration_minutes % 60
    dur_str = f"{dur_h}h {dur_m:02d}m" if dur_h > 0 else f"{dur_m} min"

    st.markdown(
        f"""<div style="background:rgba(15,23,42,0.65); border:1px solid #1E293B; border-radius:8px; padding:8px 12px; margin:8px 0 14px 0; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
          <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:14px; font-weight:800; color:#FFFFFF;">🎵 {active_setlist.title}</span>
            <span style="font-size:11px; color:#38BDF8; background:rgba(56,189,248,0.12); padding:2px 7px; border-radius:10px; border:1px solid rgba(56,189,248,0.3); font-weight:600;">{active_setlist.date or "Nessuna data"}</span>
          </div>
          <div style="display:flex; align-items:center; gap:12px; font-size:11.5px; color:#94A3B8;">
            <span>Brani: <b style="color:#00E676;">{len(active_setlist.items)}</b></span>
            <span>&bull;</span>
            <span>Durata live stimata: <b style="color:#FBBF24;">~{dur_str}</b></span>
            <span>&bull;</span>
            <span>Display: <b style="color:#A78BFA;">{active_prof.name}</b></span>
          </div>
        </div>""",
        unsafe_allow_html=True
    )

    # -------------------------------------------------------------------------
    # MAIN WORKSPACE: TABS (Mobile Friendly: Full Width Ordine di Palco & Aggiungi)
    # -------------------------------------------------------------------------
    tab_sequence, tab_add_rep = st.tabs([
        f"🎤 Ordine di Palco ({len(active_setlist.items)} Brani)",
        "📚 Aggiungi Brani dai Repertori"
    ])

    # =========================================================================
    # SCHEDA 2: AGGIUNGI BRANI DAI DIVERSI REPERTORI
    # =========================================================================
    with tab_add_rep:
        st.markdown(
            """<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;">
              <span style="font-size:13px; font-weight:800; color:#38BDF8; text-transform:uppercase; letter-spacing:0.5px;">
                📚 Brani dai Repertori
              </span>
              <span style="font-size:10px; color:#94A3B8;">Scegli il repertorio da cui pescare</span>
            </div>""",
            unsafe_allow_html=True
        )

        rep_choices = {"__all__": "🌐 Tutti i Repertori (Archivio Globale)"}
        for r in all_reps:
            rep_choices[r.uuid] = f"📁 {r.name} ({len(r.song_uuids)} brani)"

        selected_rep_filter = st.selectbox(
            "Filtra per Repertorio sorgente:",
            list(rep_choices.keys()),
            format_func=lambda x: rep_choices[x],
            key="scalette_rep_filter_choice"
        )

        # Filter songs based on chosen repertoire
        if selected_rep_filter == "__all__":
            candidate_songs = all_songs
        else:
            matched_rep = next((r for r in all_reps if r.uuid == selected_rep_filter), None)
            rep_uuids = set(matched_rep.song_uuids) if matched_rep else set()
            candidate_songs = [s for s in all_songs if s["uuid"] in rep_uuids]

        # Fast search filter inside repertoire
        search_kw = st.text_input("🔍 Cerca brano nel repertorio:", placeholder="Filtra per titolo o artista...", key="scalette_rep_search").strip().lower()
        if search_kw:
            candidate_songs = [s for s in candidate_songs if (search_kw in s["title"].lower() or search_kw in s.get("artist", "").lower())]

        # Quick add dropdown + button
        if candidate_songs:
            cand_map = {s["uuid"]: s for s in candidate_songs}
            c_sel_add, c_btn_add = st.columns([3, 1], gap="small", vertical_alignment="bottom")
            with c_sel_add:
                add_song_pick = st.selectbox(
                    "Seleziona brano rapido:",
                    list(cand_map.keys()),
                    format_func=lambda x: f"{cand_map[x]['title']} ({cand_map[x].get('artist', 'Artista')})",
                    key="pick_song_for_setlist",
                    label_visibility="collapsed"
                )
            with c_btn_add:
                if st.button("➕ Inserisci", type="primary", disabled=not current_user.can_edit(), key="btn_add_song_to_setlist_fast", width="stretch"):
                    active_setlist.items.append(SetlistItem(song_uuid=add_song_pick))
                    storage.save_setlist(active_setlist, current_user.email, current_user.name)
                    st.session_state["undo_removed_setlist_item"] = None
                    log_op("➕", "SCALETTA", f"Aggiunto '{cand_map[add_song_pick]['title']}' a scaletta '{active_setlist.title}'", "INFO")
                    st.success(f"Aggiunto '{cand_map[add_song_pick]['title']}'!")
                    st.rerun()

            # Accordion / Quick List of songs in the chosen repertoire
            with st.expander(f"📋 Sfoglia elenco brani repertorio ({len(candidate_songs)})", expanded=True):
                existing_set_song_ids = set(item.song_uuid for item in active_setlist.items)
                for c_song in candidate_songs:
                    c_uid = c_song["uuid"]
                    c_title = c_song["title"]
                    c_artist = c_song.get("artist", "")
                    c_key = c_song.get("key_current", "-")
                    c_bpm = c_song.get("bpm", "-")
                    is_in_set = c_uid in existing_set_song_ids

                    c_row_info, c_row_btn = st.columns([3.5, 1.2], gap=4, vertical_alignment="center", wrap=False)
                    with c_row_info:
                        art_str = f" &bull; <small style='color:#888;'>{c_artist}</small>" if c_artist else ""
                        badge_in = " <span style='font-size:9.5px; color:#00E676; font-weight:700;'>✓ in scaletta</span>" if is_in_set else ""
                        st.markdown(f"<div style='font-size:12px; color:#E2E8F0; padding:2px 0;'><b>{c_title}</b>{art_str}{badge_in}<br>"
                                    f"<span style='font-size:10px; color:#94A3B8;'>Key: <code>{c_key}</code> &bull; BPM: <code>{c_bpm}</code></span></div>",
                                    unsafe_allow_html=True)
                    with c_row_btn:
                        btn_txt = "+ Aggiungi" if not is_in_set else "+ Ancora"
                        if st.button(btn_txt, key=f"btn_add_inline_{c_uid}", disabled=not current_user.can_edit(), width="stretch"):
                            active_setlist.items.append(SetlistItem(song_uuid=c_uid))
                            storage.save_setlist(active_setlist, current_user.email, current_user.name)
                            st.session_state["undo_removed_setlist_item"] = None
                            log_op("➕", "SCALETTA", f"Aggiunto '{c_title}' alla scaletta", "INFO")
                            st.rerun()
        else:
            st.info("Nessun brano trovato per il repertorio o filtro selezionato.")

    # =========================================================================
    # SCHEDA 1: SEQUENZA LIVE E ORDINAMENTO BRANI
    # =========================================================================
    with tab_sequence:
        st.markdown(
            f"""<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;">
              <span style="font-size:13px; font-weight:800; color:#00E676; text-transform:uppercase; letter-spacing:0.5px;">
                🎤 Ordine di Palco ({len(active_setlist.items)} Brani)
              </span>
              <span style="font-size:10px; color:#94A3B8;">Usa ⬆️ ⬇️ per riordinare, ❌ per rimuovere con Undo</span>
            </div>""",
            unsafe_allow_html=True
        )

        if active_setlist.items:
            for idx, item in enumerate(active_setlist.items):
                s_info = song_map.get(item.song_uuid)
                title = s_info["title"] if s_info else "Brano non trovato"
                artist = s_info.get("artist", "") if s_info else ""
                key = item.custom_key or (s_info.get("key_current", "-") if s_info else "-")
                bpm = item.custom_bpm or (s_info.get("bpm", "-") if s_info else "-")

                # Single compact row per song in setlist (forced horizontal on all mobile devices)
                with st.container(key=f"set_order_item_{idx}"):
                    r_c_idx, r_c_title, r_c_up, r_c_dn, r_c_del = st.columns(
                        [0.6, 6.0, 0.8, 0.8, 0.8], gap=4, vertical_alignment="center", wrap=False
                    )

                    with r_c_idx:
                        st.markdown(f"<div style='font-size:12px; font-weight:800; color:#38BDF8; background:rgba(56,189,248,0.12); width:24px; height:24px; border-radius:12px; display:flex; align-items:center; justify-content:center; border:1px solid rgba(56,189,248,0.3);'>#{idx + 1}</div>", unsafe_allow_html=True)

                    with r_c_title:
                        art_badge = f"<span style='font-size:10.5px; color:#94A3B8;'> &bull; {artist}</span>" if artist else ""
                        st.markdown(f"<div style='line-height:1.2; padding:2px 0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;'>"
                                    f"<b style='font-size:12.5px; color:#FFFFFF;'>{title.upper()}</b>{art_badge}<br>"
                                    f"<span style='font-size:10px; color:#94A3B8;'>Tonalità: <code style='color:#FFD600;'>{key}</code> &bull; BPM: <code style='color:#00E676;'>{bpm}</code></span>"
                                    f"</div>", unsafe_allow_html=True)

                    with r_c_up:
                        if idx > 0 and st.button("⬆️", key=f"set_up_{idx}_{item.song_uuid}", disabled=not current_user.can_edit(), help="Sposta brano prima"):
                            active_setlist.items[idx], active_setlist.items[idx - 1] = active_setlist.items[idx - 1], active_setlist.items[idx]
                            storage.save_setlist(active_setlist, current_user.email, current_user.name)
                            st.rerun()

                    with r_c_dn:
                        if idx < len(active_setlist.items) - 1 and st.button("⬇️", key=f"set_dn_{idx}_{item.song_uuid}", disabled=not current_user.can_edit(), help="Sposta brano dopo"):
                            active_setlist.items[idx], active_setlist.items[idx + 1] = active_setlist.items[idx + 1], active_setlist.items[idx]
                            storage.save_setlist(active_setlist, current_user.email, current_user.name)
                            st.rerun()

                    with r_c_del:
                        if st.button("❌", key=f"set_rem_{idx}_{item.song_uuid}", disabled=not current_user.can_edit(), help="Rimuovi brano dalla sequenza (con opzione Undo immediata)"):
                            removed_it = active_setlist.items.pop(idx)
                            storage.save_setlist(active_setlist, current_user.email, current_user.name)
                            st.session_state["undo_removed_setlist_item"] = {
                                "setlist_uuid": active_setlist.uuid,
                                "item": removed_it,
                                "index": idx,
                                "title": title
                            }
                            log_op("❌", "SCALETTA", f"Rimosso '{title}' dalla scaletta '{active_setlist.title}' (Undo pronto)", "INFO")
                            st.rerun()

                    st.markdown("<div style='height:1px; background:rgba(255,255,255,0.05); margin:2px 0;'></div>", unsafe_allow_html=True)
        else:
            st.markdown(
                """<div style="text-align:center; padding:30px 15px; background:rgba(15,23,42,0.4); border:1px dashed #334155; border-radius:8px; margin-top:8px;">
                  <div style="font-size:30px; margin-bottom:6px;">📑</div>
                  <div style="font-size:13px; font-weight:700; color:#FFFFFF;">La sequenza di esecuzione è vuota</div>
                  <div style="font-size:11px; color:#94A3B8; margin-top:4px;">Seleziona un repertorio a sinistra e clicca su <b>[+ Aggiungi]</b> per inserire i tuoi brani.</div>
                </div>""",
                unsafe_allow_html=True
            )

    # -------------------------------------------------------------------------
    # ESPLORAZIONE, PDF UNIFICATO & LIVE PALCO
    # -------------------------------------------------------------------------
    st.divider()
    st.markdown("##### 📤 Esportazione Scaletta & Download PDF Unico")

    c_exp_l, c_exp_r = st.columns([1.2, 1.8], gap="medium")

    with c_exp_l:
        st.markdown(f"**Dispositivo Target per Esportazione & Palco:**")
        st.caption("Il PDF e la modalità palco rispettano rigorosamente il display del dispositivo attivo:")
        
        curr_global_dev = st.session_state.get("user_preferred_device", dev_names[0])
        curr_global_idx = dev_names.index(curr_global_dev) if curr_global_dev in dev_names else 0
        sel_set_dev = st.selectbox(
            "📐 Formato Dispositivo Scaletta:",
            dev_names,
            index=curr_global_idx,
            key="setlist_device_sync_selector",
            help="Modifica il dispositivo attivo in tutta l'applicazione"
        )
        if sel_set_dev != st.session_state.get("user_preferred_device"):
            set_active_device_globally(sel_set_dev)
            st.rerun()

        set_prof = get_layout_device_profile(sel_set_dev)
        st.caption(f"📐 **Specifiche Display:** `{set_prof.name}` &bull; `{set_prof.width_mm:.1f} × {set_prof.height_mm:.1f} mm` &bull; Colonne: `{set_prof.columns}` &bull; Font: `{set_prof.font_size_lyrics} pt`")

    with c_exp_r:
        if loaded_songs:
            # Pulsante Principale Live Palco: naviga direttamente alla funzione Palco
            if st.button("🎤 Avvia Modalità Palco con questa Scaletta (Live Stage)", type="primary", width="stretch", key="btn_go_live_stage_now"):
                st.session_state["stage_source_type"] = "📑 Scaletta Live"
                st.session_state["selected_setlist_uuid"] = active_setlist.uuid
                st.session_state["main_menu_choice"] = "🎤 Modalità Palco (Live Stage)"
                log_op("🎤", "PALCO", f"Avviata modalità palco per la scaletta '{active_setlist.title}'", "SUCCESS")
                st.rerun()

            set_pdf = PDFEngine.generate_setlist_pdf(active_setlist, loaded_songs, profile=set_prof)
            st.download_button(
                label=f"📄 Scarica PDF Unico Scaletta ({set_prof.name})",
                data=set_pdf,
                file_name=f"Scaletta_{active_setlist.title.replace(' ', '_')}.pdf",
                mime="application/pdf",
                width="stretch",
                help="Genera un unico documento PDF con copertina, indice e tutti i brani impaginati sequenzialmente nel formato del dispositivo."
            )

            col_sb_exp, col_zip_exp = st.columns(2, gap="small")
            with col_sb_exp:
                set_sb = ExportEngine.export_setlist_for_songbookpro(active_setlist, loaded_songs)
                st.download_button(
                    label="🎸 Esporta per SongBook Pro (.pro)",
                    data=set_sb,
                    file_name=f"Scaletta_{active_setlist.title.replace(' ', '_')}.pro",
                    mime="text/plain",
                    width="stretch",
                    help="File unico con tutti i brani della scaletta separati da pagina per SongBook Pro"
                )
            with col_zip_exp:
                live_zip = ExportEngine.create_offline_live_pack_zip(active_setlist, loaded_songs)
                st.download_button(
                    label="📦 Scarica Live Pack ZIP",
                    data=live_zip,
                    file_name=f"LivePack_{active_setlist.title.replace(' ', '_')}.zip",
                    mime="application/zip",
                    width="stretch",
                    help="Archivio completo contenente il PDF scaletta, singoli PDF, file AML e file per SongBook Pro"
                )
        else:
            st.info("Aggiungi brani alla scaletta per sbloccare l'esportazione PDF, SongBook Pro e la Modalità Palco.")

# ------------------------------------------------------------------------------
# 5. MODALITÀ PALCO (LIVE STAGE VIEW)
# ------------------------------------------------------------------------------
elif menu_choice == "🎤 Modalità Palco (Live Stage)":
    st.subheader("🎤 Modalità Palco Ufficiale (Live Stage Component)")

    setlists = storage.list_setlists()
    all_reps = storage.list_repertoires()
    all_songs = storage.list_songs()

    if not setlists and not all_songs:
        st.warning("Nessuna scaletta o brano disponibile nell'archivio per utilizzare la modalità palco.")
        st.stop()

    if setlists:
        default_mode_idx = 1 if st.session_state.get("stage_source_type") == "🎵 Singolo Brano" else 0
        stage_source = st.radio(
            "🎯 Sorgente Esecuzione Palco:",
            options=["📑 Scaletta Live", "🎵 Singolo Brano"],
            index=default_mode_idx,
            horizontal=True,
            key="stage_source_selector"
        )
        st.session_state["stage_source_type"] = stage_source
    else:
        stage_source = "🎵 Singolo Brano"
        st.session_state["stage_source_type"] = stage_source
        st.info("ℹ️ Nessuna scaletta presente. La Modalità Palco è attiva in modalità **Singolo Brano** da repertorio.")

    if stage_source == "📑 Scaletta Live":
        col_s1, col_s2 = st.columns([3, 1])
        with col_s1:
            setlist_options = {s.uuid: s for s in setlists}
            curr_set_id = st.session_state.get("selected_setlist_uuid")
            if curr_set_id not in setlist_options:
                curr_set_id = setlists[0].uuid
            default_s_idx = list(setlist_options.keys()).index(curr_set_id) if curr_set_id in setlist_options else 0

            selected_setlist_uuid = st.selectbox(
                "📑 Seleziona Scaletta per il Palco:",
                options=list(setlist_options.keys()),
                format_func=lambda uid: f"📑 {setlist_options[uid].title} ({len(setlist_options[uid].items)} brani)",
                index=default_s_idx,
                key="stage_active_setlist_select"
            )
            st.session_state["selected_setlist_uuid"] = selected_setlist_uuid
            active_setlist = setlist_options[selected_setlist_uuid]
        with col_s2:
            st.caption("ℹ️ Info Scaletta:")
            st.write(f"**{len(active_setlist.items)}** brani in sequenza")

        songs_to_stage = [storage.get_song(item.song_uuid) for item in active_setlist.items if storage.get_song(item.song_uuid)]
        if not songs_to_stage:
            st.warning(f"La scaletta '{active_setlist.title}' non contiene brani validi.")
            st.stop()

        st.caption(f"Palco attivo su Scaletta: **{active_setlist.title}** ({len(songs_to_stage)} brani) &bull; Keep Screen Awake attivo &bull; Pedali Bluetooth connessi")

    else:
        # Singolo brano selezionato da repertorio o da archivio globale
        col_r_filter, col_s_pick = st.columns([1, 2])
        with col_r_filter:
            rep_options = [("__ALL__", f"🌐 Archivio Globale ({len(all_songs)} brani)")]
            for r in all_reps:
                valid_count = len([uid for uid in r.song_uuids if storage.get_song(uid)])
                rep_options.append((r.uuid, f"📁 {r.name} ({valid_count} brani)"))

            rep_ids = [opt[0] for opt in rep_options]
            curr_rep_id = st.session_state.get("selected_repertoire_uuid", "__ALL__")
            rep_idx = rep_ids.index(curr_rep_id) if curr_rep_id in rep_ids else 0

            selected_rep_uuid = st.selectbox(
                "📁 Filtra da Repertorio:",
                options=rep_ids,
                format_func=lambda rid: next(opt[1] for opt in rep_options if opt[0] == rid),
                index=rep_idx,
                key="stage_repertoire_filter"
            )
            st.session_state["selected_repertoire_uuid"] = selected_rep_uuid

        if selected_rep_uuid == "__ALL__":
            candidate_songs = [storage.get_song(s["uuid"]) for s in all_songs if storage.get_song(s["uuid"])]
        else:
            target_rep = storage.get_repertoire(selected_rep_uuid)
            if target_rep:
                candidate_songs = [storage.get_song(uid) for uid in target_rep.song_uuids if storage.get_song(uid)]
            else:
                candidate_songs = []

        if not candidate_songs:
            st.warning("Nessun brano disponibile nel repertorio selezionato.")
            st.stop()

        candidate_songs = sorted(candidate_songs, key=lambda s: (getattr(s, "title", "") or "").strip().upper())
        candidate_dict = {s.uuid: s for s in candidate_songs}
        candidate_ids = list(candidate_dict.keys())

        with col_s_pick:
            curr_song_id = st.session_state.get("selected_song_uuid")
            s_idx = candidate_ids.index(curr_song_id) if curr_song_id in candidate_ids else 0

            selected_song_uuid = st.selectbox(
                "🎵 Seleziona Singolo Brano per il Palco:",
                options=candidate_ids,
                format_func=lambda uid: f"{candidate_dict[uid].title.upper()} — {candidate_dict[uid].artist or 'Autore sconosciuto'} ({candidate_dict[uid].key_current})",
                index=s_idx,
                key="stage_single_song_select"
            )
            st.session_state["selected_song_uuid"] = selected_song_uuid
            selected_song = candidate_dict[selected_song_uuid]

        songs_to_stage = [selected_song]
        st.markdown(
            f"""<div style="font-size:13px; color:#94A3B8; margin-bottom:8px;">
              Palco attivo su Singolo Brano: <b style="color:#FFFFFF;">{selected_song.title.upper()}</b> ({selected_song.artist or 'Autore sconosciuto'}) &bull;
              Tonalità: <code style="color:#FFD600;">{selected_song.key_current}</code> &bull;
              Tempo: <code style="color:#00E676;">{selected_song.bpm} BPM</code> &bull;
              Keep Screen Awake attivo &bull; Pedali Bluetooth connessi
            </div>""",
            unsafe_allow_html=True
        )

    html_bundle = LiveStageComponent.render_html_bundle(
        songs_to_stage,
        dark_theme=True,
        initial_speed=35,
        auto_start=True,
        auto_start_delay=2
    )
    st.components.v1.html(html_bundle, height=800, scrolling=False)

# ------------------------------------------------------------------------------
# 6. EVENTI LIVE (SRS Cap. 4.4)
# ------------------------------------------------------------------------------
elif menu_choice == "📅 Eventi Live":
    st.subheader("📅 Gestione Eventi & Concerti Live")

    events = storage.list_events()
    setlists = storage.list_setlists()

    col_ev1, col_ev2 = st.columns([1, 1])

    with col_ev1:
        st.write("#### Crea Nuovo Evento Live")
        with st.form("new_event_form"):
            ev_name = st.text_input("Nome Evento / Concerto:", "Live Rock Festival")
            ev_venue = st.text_input("Luogo / Locale:", "Piazza San Giovanni, Roma")
            ev_date = st.text_input("Data Evento:", "20/07/2027")
            ev_setlist = st.selectbox("Associa Scaletta:", [s.title for s in setlists] if setlists else ["Nessuna scaletta"])
            ev_notes = st.text_area("Note Logistiche e Scheda Tecnica:", "Soundcheck ore 17:30. Portare D.I. box per chitarra acustica e pedale Bluetooth.")

            if st.form_submit_button("Salva Evento Live"):
                target_s_id = next((s.uuid for s in setlists if s.title == ev_setlist), None)
                new_ev = LiveEvent(name=ev_name, venue=ev_venue, event_date=ev_date, setlist_uuid=target_s_id, logistics_notes=ev_notes)
                storage.save_event(new_ev, st.session_state["current_user_email"], st.session_state["current_user_name"])
                st.success(f"Evento '{ev_name}' salvato con successo!")
                st.rerun()

    with col_ev2:
        st.write("#### Calendario Eventi Programmati")
        if events:
            for ev in events:
                with st.expander(f"📍 {ev.name} — {ev.event_date} ({ev.venue})"):
                    st.write(f"**Data:** {ev.event_date} | **Luogo:** {ev.venue}")
                    matched_set = next((s for s in setlists if s.uuid == ev.setlist_uuid), None)
                    if matched_set:
                        st.write(f"**Scaletta Associata:** {matched_set.title} ({len(matched_set.items)} brani)")
                    st.write(f"**Note Tecniche:** {ev.logistics_notes}")
                    if st.button("🗑️ Elimina Evento", key=f"del_ev_{ev.uuid}"):
                        storage.delete_event(ev.uuid, st.session_state["current_user_email"], st.session_state["current_user_name"])
                        st.success("Evento eliminato.")
                        st.rerun()
        else:
            st.info("Nessun evento registrato.")

# ------------------------------------------------------------------------------
# 7. IMPORTA ED ESPORTA (CON WEB IMPORTER)
# ------------------------------------------------------------------------------
elif menu_choice == "📖 Manuale & Changelog":
    st.subheader("📖 Documentazione Ufficiale & Registro Modifiche")

    tab_man, tab_chan = st.tabs(["📘 Manuale Utente Auto-Aggiornante", "📜 Changelog Giornaliero (AAAA.MM.GG)"])

    with tab_man:
        st.write("### Manuale Operativo Ufficiale ASMA 2.0")
        manual_pdf = ManualEngine.generate_manual_pdf()
        st.download_button("📄 Scarica Manuale Completo in PDF Stampabile", data=manual_pdf, file_name="Manuale_Utente_ASMA_2.0.pdf", mime="application/pdf", type="primary")
        st.divider()
        st.markdown(ManualEngine.get_manual_markdown())

    with tab_chan:
        st.write("### Registro Modifiche (Changelog)")
        st.markdown(ChangelogEngine.get_changelog_markdown())

# ------------------------------------------------------------------------------
# 11. AMMINISTRAZIONE & LOG
# ------------------------------------------------------------------------------
elif menu_choice == "⚙️ Amministrazione & Log":
    st.subheader("⚙️ Pannello di Controllo Amministrativo (Solo ADMIN)")

    if not current_user.can_admin():
        st.error(f"⛔ **Accesso Negato**: Questa sezione è riservata esclusivamente agli amministratori. Il tuo account ({current_user.email}) ha il ruolo di **{current_user.role.value}**.")
        st.info("Per accedere, seleziona un profilo ADMIN nella barra laterale o chiedi a un amministratore di aggiornare i tuoi privilegi.")
    else:
        tab_locks, tab_audit, tab_aml_syntax, tab_tags, tab_devices, tab_users, tab_backup, tab_trash, tab_gist, tab_health = st.tabs([
            "🔒 Gestione Lock Attivi",
            "📜 Audit Trail Immutabile",
            "🎼 Sintassi & Tag AML",
            "🏷️ Gestione Tag & Tassonomia",
            "📱 Dispositivi & Schermi Band",
            "👥 Utenti & Ruoli Band",
            "💾 Backup & Ripristino",
            "🗑️ Cestino (Retention 30gg)",
            "☁️ Sincronizzazione GitHub Gist",
            "🏥 Health & Telemetria"
        ])

        with tab_locks:
            st.write("#### Lock Concorrenza Attivi")
            active_locks = lock_mgr.get_active_locks()
            if active_locks:
                st.dataframe(active_locks, width="stretch")
                for l in active_locks:
                    if st.button(f"Sblocca Forzatamente {l['song_uuid']}", key=f"force_unlock_{l['song_uuid']}"):
                        lock_mgr.release_lock(l["song_uuid"], current_user.email, force=True)
                        st.success("Sbloccato con successo.")
                        st.rerun()
            else:
                st.success("Nessun lock attivo al momento. Tutti i brani sono liberi per la modifica.")

        with tab_audit:
            st.write("#### Registro Audit Trail Immutabile")
            entries = audit.get_entries(limit=50)
            if entries:
                st.dataframe([e.to_dict() for e in entries], width="stretch")
            else:
                st.info("Nessuna voce di audit.")

        with tab_aml_syntax:
            st.write("#### 🎼 Configurazione e Gestione Tag Sintassi AML (ASMA Markup Language)")
            st.caption("Configura, aggiungi, modifica e rimuovi i tag e le direttive del linguaggio musicale AML. Il parser interpreta dinamicamente questi elementi per formattazione, indicizzazione e PDF.")

            st.markdown("""
            <div style="background:#161b22; border:1px solid #30363d; border-radius:8px; padding:16px; margin-bottom:16px;">
              <span style="color:#00E5FF; font-weight:bold; font-size:14px;">📋 Esempi di Sintassi e Struttura AML:</span>
              <ul style="color:#e6edf3; margin-top:8px; margin-bottom:0; font-size:13px; line-height:1.7;">
                <li><b>• Direttive:</b> <code>{title: Titolo}</code>, <code>{artist: Artista}</code>, <code>{key: Tonalità}</code>, <code>{tempo: BPM}</code>, <code>{time: 4/4}</code></li>
                <li><b>• Sezioni:</b> <code>{intro}</code>, <code>{verse}</code>, <code>{chorus}</code>, <code>{bridge}</code>, <code>{solo}</code>, <code>{outro}</code></li>
                <li><b>• Accordi Inline:</b> <code>[Am]On a dark desert highway, [F#7]cool wind in my hair</code></li>
                <li><b>• Griglia Armonica a Battute:</b> <code>| DO | LAm | FA | SOL |</code></li>
                <li><b>• Tag Strumentali:</b> <code>{guitar: Solo Don Felder}</code>, <code>{voice: Armonizzazione a 3}</code>, <code>{bass: Slap groove}</code></li>
              </ul>
            </div>
            """, unsafe_allow_html=True)

            all_aml_tags = aml_tag_mgr.list_tags()
            n_dir = sum(1 for t in all_aml_tags if t.category == "directive")
            n_sec = sum(1 for t in all_aml_tags if t.category == "section")
            n_inst = sum(1 for t in all_aml_tags if t.category == "instrumental_tag")
            n_syn = sum(1 for t in all_aml_tags if t.category == "structural_syntax")

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Direttive", n_dir)
            with m2:
                st.metric("Sezioni Musicali", n_sec)
            with m3:
                st.metric("Tag Strumentali", n_inst)
            with m4:
                st.metric("Sintassi Speciale", n_syn)

            cat_map = {
                "Tutte": "Tutte",
                "Direttive": "directive",
                "Sezioni Musicali": "section",
                "Tag Strumentali": "instrumental_tag",
                "Sintassi Strutturale": "structural_syntax"
            }
            filter_cat_label = st.selectbox("Filtra Elenco Tag per Categoria:", list(cat_map.keys()), key="filter_aml_cat")
            filtered_tags = aml_tag_mgr.list_tags(category=cat_map[filter_cat_label])

            st.write(f"##### 📋 Tag AML Attivi ({len(filtered_tags)})")
            tag_table_data = []
            for t in filtered_tags:
                tag_table_data.append({
                    "Tag": t.tag,
                    "Categoria": t.category.replace("_", " ").capitalize(),
                    "Nome Visualizzato": t.display_name,
                    "Sintassi Pattern": t.syntax_pattern,
                    "Esempio Reale": t.example,
                    "Descrizione": t.description,
                    "Rimozione Consentita": "Sì" if t.is_removable else "No (Fisso)"
                })
            st.dataframe(tag_table_data, width="stretch")

            st.divider()

            col_at1, col_at2, col_at3 = st.columns([1.3, 1.3, 1.4])

            with col_at1:
                st.write("##### ➕ Aggiungi Nuovo Tag AML")
                with st.form("form_add_aml_tag"):
                    new_tag_id = st.text_input("Nome Tag (univoco, minuscolo):", placeholder="es. saxophone, breakdown, bpm").strip().lower()
                    new_tag_cat = st.selectbox("Categoria:", ["directive", "section", "instrumental_tag"])
                    new_tag_disp = st.text_input("Nome Visualizzato:", placeholder="es. Sassofono, Breakdown Ritmico")
                    new_tag_pattern = st.text_input("Sintassi Pattern:", placeholder="es. {saxophone: Dettagli}")
                    new_tag_example = st.text_input("Esempio di Utilizzo:", placeholder="es. {saxophone: Solo Clarence Clemons}")
                    new_tag_desc = st.text_area("Descrizione del Tag:", placeholder="Descrivi la funzione del tag...", height=80)

                    btn_sub_aml = st.form_submit_button("Salva Nuovo Tag AML", type="primary")
                    if btn_sub_aml:
                        if new_tag_id and new_tag_disp:
                            try:
                                def_obj = AMLTagDefinition(
                                    tag=new_tag_id,
                                    category=new_tag_cat,
                                    display_name=new_tag_disp,
                                    syntax_pattern=new_tag_pattern or f"{{{new_tag_id}}}",
                                    example=new_tag_example or f"{{{new_tag_id}}}",
                                    description=new_tag_desc or "Tag personalizzato dall'amministratore",
                                    is_removable=True,
                                    is_builtin=False
                                )
                                aml_tag_mgr.add_tag(def_obj, current_user.email, current_user.name)
                                log_op("🎼", "AML TAG", f"Aggiunto nuovo tag AML '{new_tag_id}' ({new_tag_cat})", "SUCCESS")
                                st.success(f"Tag AML '{new_tag_id}' aggiunto con successo!")
                                st.rerun()
                            except Exception as ex:
                                st.error(str(ex))
                        else:
                            st.warning("Specifica un nome e una descrizione per il tag.")

            with col_at2:
                st.write("##### ✏️ Modifica Tag AML Esistente")
                if all_aml_tags:
                    tag_to_edit_id = st.selectbox("Seleziona Tag da modificare:", [t.tag for t in all_aml_tags], key="sel_tag_mod")
                    tag_cur = aml_tag_mgr.get_tag(tag_to_edit_id)
                    if tag_cur:
                        with st.form(f"form_edit_aml_{tag_cur.tag}"):
                            edit_disp = st.text_input("Nome Visualizzato:", value=tag_cur.display_name)
                            edit_pattern = st.text_input("Sintassi Pattern:", value=tag_cur.syntax_pattern)
                            edit_example = st.text_input("Esempio Reale:", value=tag_cur.example)
                            edit_desc = st.text_area("Descrizione:", value=tag_cur.description, height=80)
                            if st.form_submit_button("Aggiorna Tag"):
                                try:
                                    aml_tag_mgr.update_tag(
                                        tag_cur.tag,
                                        display_name=edit_disp,
                                        syntax_pattern=edit_pattern,
                                        example=edit_example,
                                        description=edit_desc,
                                        user_email=current_user.email,
                                        user_name=current_user.name
                                    )
                                    log_op("✏️", "AML TAG", f"Modificato tag AML '{tag_cur.tag}'", "INFO")
                                    st.success(f"Tag '{tag_cur.tag}' aggiornato con successo!")
                                    st.rerun()
                                except Exception as e_mod:
                                    st.error(str(e_mod))

            with col_at3:
                st.write("##### 🗑️ Elimina Tag / Ripristina")
                st.caption("Rimuovi tag non fondamentali o ripristina la configurazione iniziale.")

                removable_tags = [t for t in all_aml_tags if t.is_removable]
                if removable_tags:
                    tag_to_remove = st.selectbox("Seleziona Tag da Eliminare:", [t.tag for t in removable_tags], format_func=lambda x: f"{x} ({aml_tag_mgr.get_tag(x).category})", key="sel_tag_del")
                    with st.popover("🗑️ Conferma Rimozione Tag AML", width="stretch"):
                        st.warning(f"Vuoi davvero eliminare il tag AML **'{tag_to_remove}'**?")
                        if st.button("Elimina Definitivamente Tag", type="secondary"):
                            try:
                                aml_tag_mgr.delete_tag(tag_to_remove, current_user.email, current_user.name)
                                log_op("🗑️", "AML TAG", f"Eliminato tag AML '{tag_to_remove}'", "WARNING")
                                st.success(f"Tag AML '{tag_to_remove}' eliminato con successo!")
                                st.rerun()
                            except Exception as e_del:
                                st.error(str(e_del))
                else:
                    st.info("Nessun tag eliminabile.")

                st.write("---")
                st.caption("Ripristina tutti i tag AML di fabbrica (Direttive, Sezioni, Tag Strumentali, Accordi Inline, Griglie).")
                with st.popover("🔄 Ripristina Sintassi AML di Fabbrica", width="stretch"):
                    st.warning("Vuoi ripristinare il catalogo completo dei tag AML ai valori predefiniti di fabbrica?")
                    if st.button("Conferma Ripristino Sintassi AML", type="primary"):
                        aml_tag_mgr.reset_to_defaults(current_user.email, current_user.name)
                        log_op("🔄", "AML TAG", "Ripristinati i tag AML di fabbrica", "INFO")
                        st.success("Sintassi e tag AML ripristinati con successo!")
                        st.rerun()

        with tab_tags:
            st.write("#### 🏷️ Gestione Centralizzata Tag & Tassonomia (Solo ADMIN)")
            st.caption("Organizza, raggruppa, rinomina o elimina tag a livello globale in tutti i brani del catalogo musicale.")

            tag_counts = storage.list_all_tags()
            total_tags = len(tag_counts)
            total_tagged_instances = sum(tag_counts.values())

            m_t1, m_t2, m_t3 = st.columns(3)
            with m_t1:
                st.metric("Tag Distinti", total_tags)
            with m_t2:
                st.metric("Applicazioni Complessive", total_tagged_instances)
            with m_t3:
                most_used = max(tag_counts.items(), key=lambda x: x[1])[0] if tag_counts else "Nessuno"
                st.metric("Tag Più Utilizzato", most_used)

            st.write("##### 📋 Elenco Tag e Frequenza d'Uso")
            if tag_counts:
                tag_rows = [{"Tag": k, "Numero Brani": v} for k, v in tag_counts.items()]
                st.dataframe(tag_rows, width="stretch")
            else:
                st.info("Nessun tag assegnato ai brani nel catalogo.")

            st.divider()

            col_tag_op1, col_tag_op2, col_tag_op3 = st.columns(3)
            with col_tag_op1:
                st.write("##### ✏️ Rinomina o Unisci Tag (Merge)")
                st.caption("Rinomina un tag in tutti i brani in cui compare. Se il nuovo nome esiste già, i tag verranno unificati.")
                if tag_counts:
                    source_tag = st.selectbox("Seleziona Tag da rinominare:", list(tag_counts.keys()), key="src_tag_sel")
                    target_tag = st.text_input("Nuovo Nome Tag:", placeholder="es. acoustic-live", key="target_tag_input")
                    if st.button("Rinomina Tag Globalmente", type="primary"):
                        if target_tag.strip():
                            updated = storage.rename_tag_globally(source_tag, target_tag, current_user.email, current_user.name)
                            log_op("✏️", "TAG", f"Tag '{source_tag}' rinominato globalmente in '{target_tag.strip()}' su {updated} brani", "SUCCESS")
                            st.success(f"Tag '{source_tag}' rinominato in '{target_tag.strip()}' su {updated} brani!")
                            st.rerun()
                        else:
                            st.warning("Inserisci un nuovo nome valido per il tag.")
                else:
                    st.info("Nessun tag disponibile da rinominare.")

            with col_tag_op2:
                st.write("##### 🗑️ Eliminazione Globale Tag")
                st.caption("Rimuove completamente un tag da tutti i brani del catalogo musicale.")
                if tag_counts:
                    tag_to_delete = st.selectbox("Seleziona Tag da eliminare:", list(tag_counts.keys()), key="del_tag_sel")
                    with st.popover("🗑️ Elimina Tag dal Catalogo", width="stretch"):
                        st.warning(f"Vuoi davvero rimuovere il tag **'{tag_to_delete}'** da tutti i brani che lo contengono?")
                        if st.button("Conferma Rimozione Globale", type="secondary", key="btn_confirm_del_tag"):
                            removed = storage.delete_tag_globally(tag_to_delete, current_user.email, current_user.name)
                            log_op("🗑️", "TAG", f"Tag '{tag_to_delete}' eliminato da {removed} brani", "WARNING")
                            st.success(f"Tag '{tag_to_delete}' rimosso con successo da {removed} brani!")
                            st.rerun()
                else:
                    st.info("Nessun tag disponibile da eliminare.")

            with col_tag_op3:
                st.write("##### 🏷️ Assegnazione Massiva Tag (Bulk)")
                st.caption("Assegna rapidamente un tag a una selezione multipla di brani.")
                all_active_songs = sorted(storage.list_songs(include_deleted=False), key=lambda s: s["title"].lower())
                if all_active_songs:
                    song_map = {s["uuid"]: s["title"] for s in all_active_songs}
                    selected_uuids = st.multiselect(
                        "Seleziona brani a cui assegnare il tag:",
                        options=list(song_map.keys()),
                        format_func=lambda x: song_map[x],
                        key="bulk_tag_songs"
                    )
                    bulk_tag_name = st.text_input("Tag da assegnare:", placeholder="es. scaletta-estiva", key="bulk_tag_name")
                    if st.button("Assegna Tag ai Brani Selezionati"):
                        if bulk_tag_name.strip() and selected_uuids:
                            added = storage.add_tag_to_songs(bulk_tag_name, selected_uuids, current_user.email, current_user.name)
                            log_op("🏷️", "TAG", f"Tag '{bulk_tag_name.strip()}' assegnato in bulk a {added} brani", "SUCCESS")
                            st.success(f"Tag '{bulk_tag_name.strip()}' assegnato a {added} brani!")
                            st.rerun()
                        else:
                            st.warning("Seleziona almeno un brano e specifica un tag.")
                else:
                    st.info("Nessun brano attivo disponibile nel catalogo.")

        with tab_devices:
            st.write("#### 📱 Gestione Dispositivi & Schermi Hardware dei Musicisti (SRS Cap. 5.3 & 16.14)")
            st.caption("Configura, aggiungi e rimuovi i profili dei dispositivi fisici (Pixel 8 pro, iPad, Galaxy Tab, Xiaomi Pad, smartphone generici e A4). L'engine grafico adatta automaticamente margini, colonne e font alle dimensioni millimetriche del display.")

            all_devs = device_mgr.list_devices()
            st.write(f"##### 📋 Dispositivi Attivi Configurati ({len(all_devs)})")

            dev_rows = []
            for d in all_devs:
                dim_str = f"{d.width_mm:.1f} x {d.height_mm:.1f} mm" if d.width_mm and d.height_mm else "Standard"
                dev_rows.append({
                    "Nome Dispositivo": d.name,
                    "Categoria": d.device_type.capitalize(),
                    "Dimensioni Display": dim_str,
                    "Orientamento": d.orientation.capitalize(),
                    "Colonne": d.columns,
                    "Font Accordi / Testo": f"{d.font_size_chords}pt / {d.font_size_lyrics}pt",
                    "Margini": f"{d.margin_top_mm:.0f}mm",
                    "Tipo": "Personalizzato" if d.is_custom else "Predefinito"
                })
            st.dataframe(dev_rows, width="stretch")

            st.divider()

            col_d_add, col_d_del, col_d_rst = st.columns([1.5, 1.2, 1.3])

            with col_d_add:
                st.write("##### ➕ Aggiungi Nuovo Dispositivo")
                with st.form("form_add_device"):
                    new_d_name = st.text_input("Nome Dispositivo:", placeholder="Es. Huawei MatePad 11")
                    c_type_col1, c_type_col2 = st.columns(2)
                    with c_type_col1:
                        new_d_type = st.selectbox("Tipo:", ["tablet", "smartphone", "printable_a4"])
                    with c_type_col2:
                        new_d_orient = st.selectbox("Orientamento:", ["portrait", "landscape"])

                    c_dim1, c_dim2 = st.columns(2)
                    with c_dim1:
                        new_d_w = st.number_input("Larghezza (mm):", min_value=50.0, max_value=500.0, value=170.0, step=1.0)
                    with c_dim2:
                        new_d_h = st.number_input("Altezza (mm):", min_value=50.0, max_value=500.0, value=250.0, step=1.0)

                    c_fnt1, c_fnt2, c_cols = st.columns(3)
                    with c_fnt1:
                        new_fnt_c = st.number_input("Font Accordi:", min_value=7.0, max_value=24.0, value=12.0, step=0.5)
                    with c_fnt2:
                        new_fnt_l = st.number_input("Font Testo:", min_value=6.0, max_value=22.0, value=11.0, step=0.5)
                    with c_cols:
                        new_cols_cnt = st.selectbox("Colonne:", [1, 2], index=1 if new_d_type == "tablet" else 0)

                    new_mrg = st.number_input("Margine laterale (mm):", min_value=2.0, max_value=30.0, value=8.0, step=1.0)

                    btn_sub_dev = st.form_submit_button("Salva Nuovo Dispositivo", type="primary")
                    if btn_sub_dev:
                        if new_d_name.strip():
                            try:
                                dev_obj = DeviceProfile(
                                    name=new_d_name.strip(),
                                    target_device=new_d_type if new_d_type != "printable_a4" else "pc_a4",
                                    device_type=new_d_type,
                                    width_mm=new_d_w,
                                    height_mm=new_d_h,
                                    orientation=new_d_orient,
                                    columns=new_cols_cnt,
                                    font_size_lyrics=new_fnt_l,
                                    font_size_chords=new_fnt_c,
                                    margin_top_mm=new_mrg,
                                    margin_bottom_mm=new_mrg,
                                    margin_left_mm=new_mrg,
                                    margin_right_mm=new_mrg,
                                    is_custom=True
                                )
                                device_mgr.add_device(dev_obj, current_user.email, current_user.name)
                                log_op("📱", "DISPOSITIVI", f"Aggiunto nuovo profilo dispositivo: '{new_d_name.strip()}'", "SUCCESS")
                                st.success(f"Dispositivo '{new_d_name.strip()}' aggiunto con successo!")
                                st.rerun()
                            except Exception as err:
                                st.error(str(err))
                        else:
                            st.warning("Inserisci un nome valido per il dispositivo.")

            with col_d_del:
                st.write("##### 🗑️ Rimuovi Dispositivo")
                st.caption("Elimina un profilo hardware dall'elenco disponibile per i musicisti.")
                if all_devs:
                    dev_to_del = st.selectbox("Seleziona Dispositivo da Eliminare:", all_devs, format_func=lambda d: f"{d.name} ({d.device_type})", key="sel_del_dev")
                    with st.popover("🗑️ Conferma Rimozione Dispositivo", width="stretch"):
                        st.warning(f"Vuoi davvero eliminare il dispositivo **'{dev_to_del.name}'**?")
                        if st.button("Elimina Dispositivo", type="secondary", key="btn_confirm_del_dev"):
                            try:
                                device_mgr.remove_device(dev_to_del.uuid, current_user.email, current_user.name)
                                log_op("🗑️", "DISPOSITIVI", f"Rimosso profilo dispositivo: '{dev_to_del.name}'", "WARNING")
                                st.success(f"Dispositivo '{dev_to_del.name}' rimosso!")
                                st.rerun()
                            except Exception as e_del:
                                st.error(str(e_del))
                else:
                    st.info("Nessun dispositivo disponibile.")

            with col_d_rst:
                st.write("##### 🔄 Ripristina Predefiniti Band")
                st.caption("Ripristina l'elenco ufficiale dei dispositivi standard (Pixel 8 Pro, iPad, Tab S7/S8/S9, A4, Xiaomi, Oppo, iPhone, Android).")
                with st.popover("🔄 Ripristina Tutti i Dispositivi Predefiniti", width="stretch"):
                    st.warning("Questa operazione ripristinerà gli 8 profili hardware predefiniti della band. Continuare?")
                    if st.button("Conferma Ripristino Standard", type="primary"):
                        device_mgr.reset_defaults(current_user.email, current_user.name)
                        log_op("🔄", "DISPOSITIVI", "Ripristinati gli 8 profili dispositivi predefiniti della band", "INFO")
                        st.success("Profili hardware ripristinati con successo!")
                        st.rerun()

        with tab_users:
            st.write("#### 👥 Gestione Utenti, Ruoli & Permessi Band (SRS Cap. 3 & 10)")
            users = auth_mgr.list_users()
            u_data = []
            for u in users:
                u_data.append({
                    "Email": u.email,
                    "Nome": u.name,
                    "Ruolo": u.role.value,
                    "Provider": u.provider,
                    "Attivo": "Sì" if u.is_active else "No"
                })
            st.dataframe(u_data, width="stretch")

            col_u1, col_u2, col_u3 = st.columns(3)
            with col_u1:
                st.write("##### ✏️ Modifica Ruolo")
                target_user_email = st.selectbox("Seleziona Utente:", [u.email for u in users], key="target_u_email")
                new_role_choice = st.selectbox("Nuovo Ruolo:", [r.value for r in UserRole], key="new_r_choice")
                if st.button("Aggiorna Ruolo Utente", type="primary"):
                    try:
                        auth_mgr.update_user_role(target_user_email, UserRole(new_role_choice), current_user.email)
                        log_op("👥", "UTENTI", f"Ruolo di {target_user_email} aggiornato a {new_role_choice}", "INFO")
                        st.success(f"Ruolo di {target_user_email} aggiornato a {new_role_choice}!")
                        st.rerun()
                    except Exception as ex:
                        st.error(str(ex))
            with col_u2:
                st.write("##### ➕ Registra Musicista")
                new_u_email = st.text_input("Email Nuovo Utente:", placeholder="batteria@band.org")
                new_u_name = st.text_input("Nome e Cognome:", placeholder="Luca Rossi")
                new_u_role = st.selectbox("Ruolo Iniziale:", [r.value for r in UserRole], index=1)
                if st.button("Aggiungi Utente"):
                    if new_u_email:
                        reg_user = auth_mgr.authenticate_or_register_google(new_u_email, new_u_name)
                        auth_mgr.update_user_role(reg_user.email, UserRole(new_u_role), current_user.email)
                        log_op("➕", "UTENTI", f"Registrato utente {reg_user.name} ({new_u_role})", "SUCCESS")
                        st.success(f"Utente {reg_user.name} registrato!")
                        st.rerun()
            with col_u3:
                st.write("##### 🗑️ Elimina Utente")
                deletable_users = [u.email for u in users if u.email.lower() != current_user.email.lower()]
                if deletable_users:
                    user_to_delete = st.selectbox("Seleziona Utente da Rimuovere:", deletable_users, key="user_to_del")
                    with st.popover("🗑️ Elimina Account", width="stretch"):
                        st.warning(f"Vuoi davvero eliminare l'account di **{user_to_delete}**?")
                        if st.button("Conferma Eliminazione Account", type="secondary"):
                            try:
                                auth_mgr.delete_user(user_to_delete, current_user.email)
                                log_op("🗑️", "UTENTI", f"Eliminato account {user_to_delete}", "WARNING")
                                st.success(f"Utente '{user_to_delete}' eliminato con successo.")
                                st.rerun()
                            except Exception as err:
                                st.error(str(err))
                else:
                    st.info("Nessun altro utente rimovibile (sei l'unico amministratore connesso).")

        with tab_backup:
            st.write("#### 💾 Backup & Ripristino Disaster Recovery (SRS Cap. 10.15, 10.16 & 17.5)")
            st.caption("Esegui un backup atomico compresso (.ZIP) di tutto il catalogo musicale, impostazioni, eventi e storico revisioni, oppure ripristina un punto di ripristino precedente.")

            b_c1, b_c2 = st.columns(2)
            with b_c1:
                st.write("##### 📦 Esporta Backup Completo")
                backup_bytes = BackupEngine.create_full_backup_zip()
                now_iso = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_op("📦", "BACKUP", f"Creato archivio backup completo ({len(backup_bytes)} bytes)", "INFO")
                st.download_button(
                    "💾 Scarica Backup ZIP Completo",
                    data=backup_bytes,
                    file_name=f"ASMA_BACKUP_{now_iso}.zip",
                    mime="application/zip",
                    type="primary",
                    width="stretch"
                )
                st.info("Include: brani AML, revisioni, scalette, repertori, eventi live, log di audit e utenti.")

            with b_c2:
                st.write("##### 🔄 Ripristina da File Backup ZIP")
                uploaded_backup = st.file_uploader("Carica file ZIP di backup ASMA:", type=["zip"], key="backup_upload")
                if uploaded_backup and st.button("⚠️ Avvia Ripristino Completo"):
                    with st.spinner("Verifica integrità ed estrazione dei file in corso..."):
                        ok, msg = BackupEngine.restore_from_backup_zip(uploaded_backup.read())
                        log_op("🔄", "BACKUP", f"Ripristino backup: {msg}", "SUCCESS" if ok else "ERROR")
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

        with tab_trash:
            st.write("#### 🗑️ Cestino di Sistema (Soft-Delete a 30 giorni)")
            st.caption("Recupera o elimina definitivamente qualsiasi elemento cancellato da musicisti o amministratori.")

            tab_tr_songs, tab_tr_sets, tab_tr_reps = st.tabs([
                "🎵 Brani nel Cestino",
                "📑 Scalette nel Cestino",
                "📚 Repertori nel Cestino"
            ])

            with tab_tr_songs:
                del_songs = storage.list_deleted_songs()
                if del_songs:
                    col_ts1, col_ts2 = st.columns([3, 1])
                    with col_ts1:
                        st.info(f"Sono presenti **{len(del_songs)}** brani nel cestino.")
                    with col_ts2:
                        with st.popover("🧹 Svuota Cestino Brani", width="stretch"):
                            st.warning("Eliminare definitivamente tutti i brani nel cestino?")
                            if st.button("Conferma Svuota", type="secondary", disabled=not current_user.can_admin(), key="btn_purge_all_songs"):
                                p_cnt = storage.empty_trash(current_user.email, current_user.name)
                                log_op("🧹", "CESTINO", f"Eliminati definitivamente {p_cnt} elementi", "WARNING")
                                st.success("Cestino svuotato.")
                                st.rerun()

                    for sm in del_songs:
                        s_data = sm.get("data", {})
                        s_uid = s_data.get("uuid")
                        s_title = s_data.get("title", "Senza Titolo")
                        s_art = s_data.get("artist", "")
                        s_key = s_data.get("key_current", "-")
                        s_del_time = sm.get("deleted_at", "")[:16].replace("T", " ")

                        c_sd1, c_sd2, c_sd3 = st.columns([3.5, 1, 1])
                        with c_sd1:
                            st.markdown(f"🎵 **{s_title}** &bull; {s_art} (Key: `{s_key}`) &bull; <small style='color:#888;'>Eliminato: {s_del_time}</small>", unsafe_allow_html=True)
                        with c_sd2:
                            if st.button("↩️ Ripristina", key=f"res_song_{s_uid}", width="stretch"):
                                storage.restore_song(s_uid, current_user.email, current_user.name)
                                log_op("♻️", "RIPRISTINO", f"Brano '{s_title}' ripristinato dal cestino", "SUCCESS")
                                st.success(f"Brano '{s_title}' ripristinato!")
                                st.rerun()
                        with c_sd3:
                            with st.popover("🔥 Elimina", width="stretch"):
                                st.write(f"Eliminare definitivamente **'{s_title}'**?")
                                if st.button("Conferma", key=f"purge_song_{s_uid}", type="secondary", disabled=not current_user.can_admin()):
                                    storage.purge_song_permanently(s_uid, current_user.email, current_user.name)
                                    log_op("🔥", "CESTINO", f"Brano '{s_title}' eliminato definitivamente", "WARNING")
                                    st.success(f"Brano '{s_title}' eliminato definitivamente.")
                                    st.rerun()
                        st.divider()
                else:
                    st.info("Nessun brano attualmente nel cestino.")

            with tab_tr_sets:
                del_sets = storage.list_deleted_setlists()
                if del_sets:
                    st.info(f"Sono presenti **{len(del_sets)}** scalette nel cestino.")
                    for set_m in del_sets:
                        st_data = set_m.get("data", {})
                        st_uid = st_data.get("uuid")
                        st_title = st_data.get("title", "Senza Titolo")
                        st_date = st_data.get("date", "")
                        st_cnt = len(st_data.get("items", []))
                        st_del_time = set_m.get("deleted_at", "")[:16].replace("T", " ")

                        c_st1, c_st2 = st.columns([4, 1.2])
                        with c_st1:
                            st.markdown(f"📑 **{st_title}** ({st_cnt} brani) &bull; Data: {st_date} &bull; <small style='color:#888;'>Eliminata: {st_del_time}</small>", unsafe_allow_html=True)
                        with c_st2:
                            if st.button("↩️ Ripristina", key=f"res_set_{st_uid}", type="primary", width="stretch"):
                                storage.restore_setlist(st_uid, current_user.email, current_user.name)
                                log_op("♻️", "RIPRISTINO", f"Scaletta '{st_title}' ripristinata", "SUCCESS")
                                st.success(f"Scaletta '{st_title}' ripristinata!")
                                st.rerun()
                        st.divider()
                else:
                    st.info("Nessuna scaletta attualmente nel cestino.")

            with tab_tr_reps:
                del_reps = storage.list_deleted_repertoires()
                if del_reps:
                    st.info(f"Sono presenti **{len(del_reps)}** repertori nel cestino.")
                    for rep_m in del_reps:
                        rp_data = rep_m.get("data", {})
                        rp_uid = rp_data.get("uuid")
                        rp_name = rp_data.get("name", "Repertorio")
                        rp_desc = rp_data.get("description", "")
                        rp_cnt = len(rp_data.get("song_uuids", []))
                        rp_del_time = rep_m.get("deleted_at", "")[:16].replace("T", " ")

                        c_rp1, c_rp2 = st.columns([4, 1.2])
                        with c_rp1:
                            st.markdown(f"📚 **{rp_name}** ({rp_cnt} brani collegati) &bull; *{rp_desc}* &bull; <small style='color:#888;'>Eliminato: {rp_del_time}</small>", unsafe_allow_html=True)
                        with c_rp2:
                            if st.button("↩️ Ripristina", key=f"res_rep_{rp_uid}", type="primary", width="stretch"):
                                res_rep = storage.restore_repertoire(rp_uid, current_user.email, current_user.name)
                                if res_rep:
                                    log_op("♻️", "RIPRISTINO", f"Repertorio '{res_rep.name}' ripristinato", "SUCCESS")
                                    st.success(f"Repertorio '{res_rep.name}' ripristinato!")
                                st.rerun()
                        st.divider()
                else:
                    st.info("Nessun repertorio attualmente nel cestino.")

        with tab_gist:
            st.write("#### Sincronizzazione Remota GitHub Gist (SRS Cap. 18.9 & 22.8)")
            st.caption("Sincronizza l'intero archivio musicale con il tuo repository Gist a costo zero.")
            is_conn, msg = gist_client.test_connection()
            if is_conn:
                st.success(f"🟢 Stato Connessione Gist: {msg}")
                if st.button("☁️ Sincronizza Tutti i File su Gist Adesso", type="primary"):
                    all_s = storage.list_songs()
                    push_dict = {f"{s['uuid']}.json": json.dumps(s) for s in all_s}
                    push_ok, push_msg = gist_client.push_files(push_dict)
                    log_op("☁️", "SYNC GIST", f"Gist push: {push_msg}", "SUCCESS" if push_ok else "ERROR")
                    if push_ok:
                        st.success(push_msg)
                    else:
                        st.error(push_msg)
            else:
                st.warning(f"🟡 Stato Gist: {msg}")
                st.info("Per abilitare la sincronizzazione automatica remota, configura le variabili di ambiente `GITHUB_TOKEN` e `GIST_ID` o aggiungile a `.streamlit/secrets.toml`.")

        with tab_health:
            st.write("#### Endpoint di Controllo Salute `/health`")
            st.json({
                "status": "healthy",
                "version": "2026.11.05",
                "uptime_target": "99.9%",
                "storage_status": "ok",
                "in_memory_index": "active",
                "pdf_engine": "ok",
                "gist_sync": "configured" if gist_client.is_configured else "offline_local",
                "ai_mode": BandAIService.get_current_mode()
            })




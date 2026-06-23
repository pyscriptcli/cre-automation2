import streamlit as st
import requests
import re
import json
import os
import time
import math
from datetime import datetime
from difflib import SequenceMatcher

# --- PROGRAMMATIC LIGHT MODE LOCK (Must execute before st.set_page_config) ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"light\"\n")

# -----------------------------------------------------------------------------
# 1. BRANDED THEME & STRUCTURAL FULL OVERRIDES
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Open Node",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Montserrat:wght@400;500;600;700;800&display=swap');

        :root {
            --brand-midnight: #003366 !important;
            --brand-gold: #C9AB4C !important;
            --white-clean: #ffffff !important;
            --bg-offwhite: #f8fafc !important;
            --text-muted: #888780 !important;
            --soft-shadow: 0 4px 12px rgba(0, 51, 102, 0.08) !important;
        }
        
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
            background-color: var(--white-clean) !important;
            color: var(--brand-midnight) !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: var(--bg-offwhite) !important;
            color: var(--brand-midnight) !important;
            border-right: 1px solid rgba(0, 51, 102, 0.08) !important;
            width: 280px !important;
            min-width: 280px !important;
            max-width: 280px !important;
            transform: none !important;
            visibility: visible !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            box-shadow: 2px 0 15px rgba(0,0,0,0.03) !important;
            transition: width 0.3s ease, min-width 0.3s ease, max-width 0.3s ease, margin-left 0.3s ease, opacity 0.3s ease !important;
            position: relative !important;
            z-index: 100 !important;
            flex-shrink: 0 !important;
        }
        
        /* Sidebar collapsed state - dynamic */
        .sidebar-collapsed [data-testid="stSidebar"] {
            width: 0px !important;
            min-width: 0px !important;
            max-width: 0px !important;
            margin-left: -280px !important;
            padding: 0 !important;
            border-right: none !important;
            overflow: hidden !important;
            opacity: 0 !important;
        }
        .sidebar-collapsed [data-testid="stMain"] {
            width: 100vw !important;
            margin-left: 0 !important;
        }
        
        /* Sidebar toggle button - floating on left edge */
        .sidebar-toggle-btn {
            position: fixed;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            z-index: 99999;
            background: rgba(0, 51, 102, 0.85);
            color: #ffffff;
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 4px;
            padding: 8px 4px;
            font-family: 'Montserrat', sans-serif;
            font-size: 7px;
            font-weight: 600;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            cursor: pointer;
            backdrop-filter: blur(4px);
            transition: all 0.25s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.12);
            writing-mode: vertical-rl;
            text-orientation: mixed;
            line-height: 1.2;
            min-height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .sidebar-toggle-btn:hover {
            background: rgba(201, 171, 76, 0.9);
            border-color: rgba(255,255,255,0.25);
            transform: translateY(-50%) scale(1.05);
        }
        .sidebar-toggle-btn.sidebar-hidden {
            left: 12px;
        }
        
        /* Hide Streamlit's default sidebar toggle */
        [data-testid="stSidebarCollapseButton"], 
        [data-testid="collapsedControl"],
        .st-emotion-cache-1cypcdb,
        .st-emotion-cache-6qob1r {
            display: none !important;
        }
        
        ::-webkit-scrollbar { width: 0px !important; background: transparent !important; }
        * { scrollbar-width: none !important; -ms-overflow-style: none !important; }
        
        p, label, h1, h2, h3, h4, h5, h6, .stMarkdown, [data-testid="stExpander"] summary p {
            color: var(--brand-midnight) !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        
        [data-testid="stHeader"], header, #stDecoration { display: none !important; }
        
        [data-testid="stAppViewContainer"] { 
            display: flex !important; 
            flex-direction: row !important; 
            width: 100vw !important; 
            height: 100vh !important; 
            overflow: hidden !important; 
        }
        [data-testid="stMain"] { 
            flex-grow: 1 !important; 
            width: calc(100vw - 280px) !important; 
            height: 100vh !important; 
            overflow: hidden !important; 
            margin: 0px !important; 
            padding: 0px !important; 
            transition: width 0.3s ease, margin-left 0.3s ease !important;
        }
        .block-container, [data-testid="stAppViewBlockContainer"], [data-testid="stVerticalBlock"], .stElementContainer { 
            padding: 0px !important; 
            margin: 0px !important; 
            max-width: 100% !important; 
            gap: 0rem !important; 
        }
        iframe { 
            height: 100vh !important; 
            width: 100% !important; 
            border: none !important; 
            display: block !important; 
        }
        
        div[data-baseweb="input"], div[data-baseweb="select"] { 
            background-color: transparent !important; 
            border: none !important; 
            border-bottom: 1px solid rgba(201, 171, 76, 0.5) !important; 
            border-radius: 0px !important; 
            box-shadow: none !important; 
        }
        
        div.stButton > button[kind="secondary"], [data-testid="stPopover"] > button { 
            background-color: var(--brand-midnight) !important; 
            border: 1px solid var(--brand-midnight) !important; 
            border-radius: 2px !important; 
            width: 100% !important; 
            padding: 4px !important; 
            box-shadow: var(--soft-shadow) !important; 
        }
        div.stButton > button[kind="secondary"]:hover, [data-testid="stPopover"] > button:hover { 
            background-color: var(--brand-gold) !important; 
            border-color: var(--brand-gold) !important; 
        }
        div.stButton > button[kind="secondary"] p, [data-testid="stPopover"] > button p, [data-testid="stPopover"] > button div, div.stDownloadButton > button p { 
            color: var(--white-clean) !important; 
            font-weight: 700 !important; 
            font-size: 9px !important; 
            text-transform: uppercase !important; 
            letter-spacing: 1px; 
        }
        
        div.stDownloadButton > button { 
            background-color: var(--brand-midnight) !important; 
            border: none !important; 
            border-radius: 2px !important; 
            width: 100% !important; 
            padding: 4px !important; 
        }
        div.stDownloadButton > button:hover { 
            background-color: var(--brand-gold) !important; 
        }
        
        div.stButton > button[kind="primary"] { 
            background: transparent !important; 
            border: none !important; 
            color: var(--text-muted) !important; 
            padding: 0 !important; 
            margin-top: 2px; 
        }
        div.stButton > button[kind="primary"] p { 
            color: var(--text-muted) !important; 
            font-size: 9px !important; 
            font-weight: 600; 
            text-transform: uppercase; 
        }
        
        [data-testid="stSidebar"] .st-expander { 
            border: 1px solid rgba(0, 51, 102, 0.05) !important; 
            background-color: var(--white-clean) !important; 
            border-radius: 2px !important; 
            margin-bottom: 2px !important; 
        }
        
        .stCheckbox { 
            display: flex !important; 
            align-items: center !important; 
            margin-bottom: 2px !important; 
        }
        .stCheckbox label { 
            display: inline-flex !important; 
            align-items: center !important; 
            gap: 6px !important; 
            margin: 0px !important; 
            padding: 0px !important; 
        }
        .stCheckbox label p { 
            font-size: 10px !important; 
            font-weight: 500 !important; 
            color: var(--brand-midnight) !important; 
            display: inline-block !important; 
            margin: 0 !important; 
            line-height: 1.2 !important; 
        }
        div[data-baseweb="checkbox"] { 
            align-self: center !important; 
        }
        
        div[data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"] { 
            background-color: #003366 !important; 
            border-color: #003366 !important; 
        }
        div[data-baseweb="checkbox"] input:checked + div, 
        div[data-baseweb="checkbox"] div[aria-checked="true"], 
        div[data-baseweb="checkbox"] [role="checkbox"][aria-checked="true"] > div { 
            background-color: #003366 !important; 
            border-color: #003366 !important; 
        }
        
        .brand-title { 
            font-family: 'Cormorant Garamond', serif !important; 
            font-style: italic; 
            color: var(--brand-midnight); 
            font-size: 30px; 
            text-align: center; 
            border-bottom: 1px solid var(--brand-gold); 
            padding-bottom: 6px; 
            margin-bottom: 10px; 
        }
        .stTextInput label p, .stNumberInput label p { 
            font-size: 9px !important; 
            font-weight: 500 !important; 
            color: var(--text-muted) !important; 
        }

        /* Search bar styles */
        .search-container {
            background: #ffffff;
            border: 2px solid rgba(0, 51, 102, 0.1);
            border-radius: 6px;
            padding: 2px 8px;
            transition: all 0.3s ease;
            margin-bottom: 4px;
        }
        .search-container:focus-within {
            border-color: #003366;
            box-shadow: 0 0 0 3px rgba(0, 51, 102, 0.08);
        }
        .search-char-counter {
            text-align: right;
            font-size: 7px;
            color: #888780;
            padding: 0 0 2px 0;
        }
        .search-char-counter.warning {
            color: #AA2E20;
        }
        .search-error {
            color: #AA2E20;
            font-size: 8px;
            padding: 2px 0;
        }
        .search-success {
            color: #2e7d32;
            font-size: 8px;
            padding: 2px 0;
        }
        .search-cooldown {
            color: #888780;
            font-size: 8px;
            padding: 2px 0;
        }

        /* Workspace in sidebar */
        .workspace-section {
            margin-top: 10px;
            border-top: 1px solid rgba(0, 51, 102, 0.08);
            padding-top: 8px;
        }
        .workspace-header {
            font-size: 9px;
            font-weight: 700;
            color: #003366;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4px;
        }
        .workspace-count {
            background: rgba(0, 51, 102, 0.08);
            padding: 0 6px;
            border-radius: 2px;
            font-size: 8px;
        }
        .workspace-item {
            font-size: 8px;
            padding: 2px 4px;
            border-bottom: 1px solid rgba(0, 51, 102, 0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
        }
        .workspace-item:hover {
            background: rgba(0, 51, 102, 0.03);
        }
        .workspace-item-name {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 180px;
        }

        /* Python Engine Core Centered Progress Stopwatch HUD Panel Overlay */
        .py-loading-container {
            position: absolute; top: 40%; left: 50%; transform: translate(-50%, -50%);
            width: 340px; background: #ffffff; padding: 24px; border-radius: 4px;
            border: 1px solid rgba(0, 51, 102, 0.15); box-shadow: 0 10px 30px rgba(0, 51, 102, 0.15);
            text-align: center; z-index: 999999; font-family: 'Montserrat', sans-serif;
        }
        .py-spinner {
            width: 40px; height: 40px; border: 4px solid rgba(0, 51, 102, 0.1);
            border-left-color: #003366; border-radius: 50%; animation: spin 1s linear infinite;
            margin: 0 auto 16px auto;
        }
        .py-loading-title { font-size: 11px; font-weight: 800; color: #003366; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 6px; }
        .py-loading-subtitle { font-size: 10px; font-weight: 600; color: #C9AB4C; font-family: monospace; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        
        /* API LOG PANEL */
        .api-log-container {
            position: absolute; bottom: 12px; right: 12px; width: 340px; max-height: 220px;
            background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(8px); border-radius: 4px;
            border-left: 2px solid #C9AB4C; z-index: 10000; font-family: 'Monaco', monospace;
            font-size: 9px; display: flex; flex-direction: column; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transition: all 0.2s ease; color: #e0e0e0;
        }
        .api-log-header {
            padding: 4px 8px; background: rgba(0,0,0,0.6); border-radius: 4px 4px 0 0;
            font-weight: 600; font-size: 8px; letter-spacing: 0.5px; text-transform: uppercase;
            display: flex; justify-content: space-between; align-items: center; cursor: pointer;
            color: #C9AB4C; border-bottom: 1px solid rgba(201, 171, 76, 0.2);
        }
        .api-log-content {
            overflow-y: auto; padding: 4px; flex-grow: 1; max-height: 170px;
            scrollbar-width: thin;
        }
        .api-log-entry {
            border-bottom: 1px solid rgba(255,255,255,0.05); padding: 4px 4px;
            font-family: monospace; font-size: 8px; word-break: break-word;
        }
        .api-log-time { color: #C9AB4C; font-weight: 600; margin-right: 6px; }
        .api-log-info { color: #88ffaa; }
        .api-log-error { color: #ff8888; }
        .api-log-warning { color: #ffaa66; }
        .api-log-close { cursor: pointer; padding: 0 4px; font-size: 12px; line-height: 1; }
        .api-log-close:hover { color: #ff8888; }
        
        .color-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; border: 1px solid rgba(0,0,0,0.1); flex-shrink: 0; }
        
        /* Fullscreen toggle button on map - top left */
        .map-fullscreen-btn {
            position: absolute;
            top: 12px;
            left: 12px;
            z-index: 9999;
            background: rgba(255,255,255,0.92);
            color: #003366;
            border: 1px solid rgba(0, 51, 102, 0.15);
            border-radius: 3px;
            padding: 0;
            width: 28px;
            height: 28px;
            font-family: 'Montserrat', sans-serif;
            font-size: 11px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 2px 6px rgba(0,0,0,0.12);
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            line-height: 1;
        }
        .map-fullscreen-btn:hover {
            background: #003366;
            color: #ffffff;
            border-color: #003366;
        }
        
        .fullscreen-mode #apiLogPanel {
            display: none !important;
        }
        .fullscreen-mode #mapFullscreenBtn {
            background: rgba(0, 51, 102, 0.9) !important;
            color: #ffffff !important;
            border-color: rgba(255,255,255,0.3) !important;
        }

        /* Label size slider in basemap controller - smaller */
        .label-size-row {
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 1px 0 1px 18px;
            font-size: 6px;
            font-weight: 600;
            color: #888780;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }
        .label-size-row input[type="range"] {
            flex-grow: 1;
            height: 2px;
            -webkit-appearance: none;
            background: rgba(0,51,102,0.15);
            border-radius: 1px;
            outline: none;
            margin: 0;
            max-width: 60px;
        }
        .label-size-row input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 5px;
            height: 5px;
            border-radius: 50%;
            background: #003366;
            cursor: pointer;
        }
        .label-size-row input[type="range"]::-moz-range-thumb {
            width: 5px;
            height: 5px;
            border-radius: 50%;
            background: #003366;
            cursor: pointer;
            border: none;
        }
        .label-size-row .label-size-value {
            color: #003366;
            font-weight: 700;
            min-width: 10px;
            text-align: center;
            font-size: 6px;
        }
        
        .config-block-wrapper { padding: 4px 8px; background: #f8fafc; border-bottom: 1px solid rgba(0, 51, 102, 0.05); display: flex; flex-direction: column; gap: 3px; }
        .config-headline { font-size: 7px; font-weight: 800; color: #003366; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 1px; }
        .config-flex-row { display: flex; align-items: center; justify-content: space-between; font-size: 8px; font-weight: 600; color: #003366; gap: 4px; }
        .config-flex-row select, .config-flex-row input { font-size: 8px; font-family: 'Montserrat', sans-serif; color: #003366; background: #ffffff; border: 1px solid rgba(0, 51, 102, 0.15); border-radius: 2px; padding: 1px 2px; outline: none; }
        .slider-control-element { flex-grow: 1; margin: 0; -webkit-appearance: none; height: 3px; background: rgba(0,51,102,0.1); border-radius: 2px; outline: none; }
        .slider-control-element::-webkit-slider-thumb { -webkit-appearance: none; width: 8px; height: 8px; border-radius: 50%; background: #003366; cursor: pointer; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. STATE PERSISTENCE
# -----------------------------------------------------------------------------
DEFAULT_COORDS = "14.5995, 120.9842"
DEFAULT_RADIUS = 1000

if 'geo_coords' not in st.session_state: st.session_state.geo_coords = DEFAULT_COORDS
if 'geo_radius' not in st.session_state: st.session_state.geo_radius = DEFAULT_RADIUS
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []

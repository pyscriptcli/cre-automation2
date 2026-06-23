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
            display: flex !important;
            flex-direction: column !important;
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
            margin-top: 8px;
            border-top: 1px solid rgba(0, 51, 102, 0.08);
            padding-top: 8px;
            flex: 1;
            overflow-y: auto;
            min-height: 100px;
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
            margin-bottom: 6px;
            padding-bottom: 4px;
            border-bottom: 1px solid rgba(0, 51, 102, 0.05);
        }
        .workspace-count {
            background: rgba(0, 51, 102, 0.08);
            padding: 0 6px;
            border-radius: 2px;
            font-size: 8px;
        }
        .workspace-layer {
            margin-bottom: 4px;
        }
        .workspace-layer-header {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 8px;
            font-weight: 600;
            color: #003366;
            padding: 2px 0;
        }
        .workspace-item {
            font-size: 8px;
            padding: 2px 4px 2px 16px;
            border-bottom: 1px solid rgba(0, 51, 102, 0.03);
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            color: #555;
        }
        .workspace-item:hover {
            background: rgba(0, 51, 102, 0.03);
            color: #003366;
        }
        .workspace-item-name {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 200px;
        }
        .workspace-item-type {
            font-size: 6px;
            color: #888780;
            background: rgba(0, 51, 102, 0.05);
            padding: 0 4px;
            border-radius: 2px;
        }
        .color-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            border: 1px solid rgba(0,0,0,0.08);
            flex-shrink: 0;
        }
        
        /* Empty workspace state */
        .workspace-empty {
            font-size: 8px;
            color: #888780;
            padding: 16px 4px;
            text-align: center;
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
        
        /* Button row for search */
        .search-button-row {
            display: flex;
            gap: 4px;
            margin-top: 2px;
        }
        .search-button-row .stButton {
            flex: 1;
        }
        .search-button-row .stButton button {
            padding: 4px 8px !important;
            font-size: 8px !important;
            min-height: 28px !important;
        }
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
if 'last_scan_lat' not in st.session_state: st.session_state.last_scan_lat = 14.5995
if 'last_scan_lon' not in st.session_state: st.session_state.last_scan_lon = 120.9842
if 'layer_meta' not in st.session_state: st.session_state.layer_meta = {}
if 'scan_active_loading' not in st.session_state: st.session_state.scan_active_loading = False
if 'label_size' not in st.session_state: st.session_state.label_size = 9
if 'fullscreen_active' not in st.session_state: st.session_state.fullscreen_active = False
if 'sidebar_collapsed' not in st.session_state: st.session_state.sidebar_collapsed = False
if 'api_logs' not in st.session_state: st.session_state.api_logs = []
if 'search_cooldown_until' not in st.session_state: st.session_state.search_cooldown_until = 0
if 'search_count' not in st.session_state: st.session_state.search_count = 0
if 'search_reset_time' not in st.session_state: st.session_state.search_reset_time = time.time()
if 'last_search_query' not in st.session_state: st.session_state.last_search_query = ""

if 'target_config' not in st.session_state:
    st.session_state.target_config = {"size": 24, "color": "#003366", "style": "star"}
if 'radius_config' not in st.session_state:
    st.session_state.radius_config = {"color": "#003366", "fill_opacity": 0.08, "weight": 1.5}
if 'global_marker_style' not in st.session_state: st.session_state.global_marker_style = "dots"
if 'global_marker_size' not in st.session_state: st.session_state.global_marker_size = 12
if 'global_marker_color' not in st.session_state: st.session_state.global_marker_color = "#003366"

# -----------------------------------------------------------------------------
# 3. API LOGGING
# -----------------------------------------------------------------------------
def add_api_log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.api_logs.append({"time": timestamp, "message": message, "level": level})
    if len(st.session_state.api_logs) > 100:
        st.session_state.api_logs = st.session_state.api_logs[-100:]

def clear_api_logs():
    st.session_state.api_logs = []

# -----------------------------------------------------------------------------
# 4. SEARCH GUARDRAILS
# -----------------------------------------------------------------------------
class SearchGuardrails:
    MAX_QUERY_LENGTH = 100
    MIN_QUERY_LENGTH = 2
    RATE_LIMIT_PER_MINUTE = 5
    COOLDOWN_SECONDS = 5
    
    BLOCKED_PATTERNS = [
        r'(.)\1{10,}',
        r'\b(\w+)\s+\1{3,}\b',
        r'[<>{}()\[\]|\\;]',
        r'\b(select|insert|update|delete|drop|union|exec|script|javascript)\b',
    ]
    
    # Brand name variations for better matching
    BRAND_VARIATIONS = {
        'jollibee': ['jolibee', 'jbee', 'jfc', 'jollibee foods'],
        'mcdonalds': ['mcdonald', 'mcdo', 'mcd', 'golden arches'],
        '7-eleven': ['7/11', '7-11', '711', 'seven eleven'],
        'kfc': ['kentucky fried chicken', 'kfc'],
        'greenwich': ['greenwich pizza'],
        'chowking': ['chow king'],
        'burger king': ['bk', 'burgerking'],
        'starbucks': ['starbucks coffee'],
        'ministop': ['mini stop'],
        'family mart': ['family mart'],
        'lawson': ['lawson'],
        'shell': ['shell gas', 'shell station'],
        'petron': ['petron gas'],
        'caltex': ['caltex gas'],
    }
    
    @classmethod
    def validate_query(cls, query):
        if not query or not query.strip():
            return False, "Please enter a search term"
        
        query = query.strip()
        
        if len(query) < cls.MIN_QUERY_LENGTH:
            return False, f"Minimum {cls.MIN_QUERY_LENGTH} characters required"
        
        if len(query) > cls.MAX_QUERY_LENGTH:
            return False, f"Maximum {cls.MAX_QUERY_LENGTH} characters allowed"
        
        for pattern in cls.BLOCKED_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return False, "Invalid characters in search"
        
        return True, "Valid"
    
    @classmethod
    def check_rate_limit(cls):
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - st.session_state.search_reset_time > 60:
            st.session_state.search_count = 0
            st.session_state.search_reset_time = current_time
        
        # Check cooldown
        if current_time < st.session_state.search_cooldown_until:
            remaining = int(st.session_state.search_cooldown_until - current_time)
            return False, f"Please wait {remaining}s before searching again"
        
        # Check rate limit
        if st.session_state.search_count >= cls.RATE_LIMIT_PER_MINUTE:
            return False, f"Rate limit: {cls.RATE_LIMIT_PER_MINUTE} searches per minute"
        
        return True, "OK"
    
    @classmethod
    def normalize_query(cls, query):
        query = ' '.join(query.split())
        query = query.lower()
        
        # Common replacements
        replacements = {
            '7/11': '7-eleven',
            '7-11': '7-eleven',
            '711': '7-eleven',
            'seven eleven': '7-eleven',
            'mcdo': 'mcdonalds',
            'jbee': 'jollibee',
            '&': 'and',
            '+': 'and',
        }
        
        for orig, repl in replacements.items():
            query = query.replace(orig, repl)
        
        return query
    
    @classmethod
    def get_brand_variations(cls, query):
        """Get brand variations for better fuzzy matching"""
        query_lower = query.lower()
        variations = [query_lower]
        
        # Check if query matches any known brand
        for brand, variants in cls.BRAND_VARIATIONS.items():
            if query_lower in [brand] + variants:
                variations.extend([brand] + variants)
                break
        
        # Check for partial matches
        for brand, variants in cls.BRAND_VARIATIONS.items():
            for variant in variants:
                if variant in query_lower or query_lower in variant:
                    variations.extend([brand] + variants)
                    break
        
        return list(set(variations))
    
    @classmethod
    def sanitize_for_overpass(cls, query):
        sanitized = re.sub(r'[^a-zA-Z0-9\s\-/.]', '', query)
        if len(sanitized) > 50:
            sanitized = sanitized[:50]
        return sanitized

# -----------------------------------------------------------------------------
# 5. OVERPASS API
# -----------------------------------------------------------------------------
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

def build_overpass_query(lat, lon, radius, search_terms):
    """Build Overpass QL from search terms with improved fuzzy matching"""
    
    # Get brand variations
    variations = SearchGuardrails.get_brand_variations(search_terms)
    terms = search_terms.lower().split()
    
    statements = []
    seen_statements = set()
    
    # 1. Tag mappings (amenity, shop, tourism, etc.)
    tag_mappings = {
        'restaurant': 'amenity=restaurant',
        'cafe': 'amenity=cafe',
        'coffee': 'amenity=cafe',
        'bakery': 'shop=bakery',
        'supermarket': 'shop=supermarket',
        'grocery': 'shop=supermarket',
        'pharmacy': 'amenity=pharmacy',
        'hospital': 'amenity=hospital',
        'clinic': 'amenity=clinic',
        'school': 'amenity=school',
        'university': 'amenity=university',
        'college': 'amenity=college',
        'hotel': 'tourism=hotel',
        'motel': 'tourism=motel',
        'gas': 'amenity=fuel',
        'fuel': 'amenity=fuel',
        'parking': 'amenity=parking',
        'bank': 'amenity=bank',
        'atm': 'amenity=atm',
        'police': 'amenity=police',
        'fire': 'amenity=fire_station',
        'library': 'amenity=library',
        'post': 'amenity=post_office',
        'mall': 'shop=mall',
        'cinema': 'amenity=cinema',
        'theatre': 'amenity=theatre',
        'park': 'leisure=park',
        'gym': 'leisure=fitness_centre',
        'church': 'amenity=place_of_worship',
        'mosque': 'amenity=place_of_worship',
        'bar': 'amenity=bar',
        'pub': 'amenity=pub',
        'fast food': 'amenity=fast_food',
        'convenience': 'shop=convenience',
        'market': 'shop=market',
    }
    
    # 2. Build tag-based queries
    for term in terms:
        term_lower = term.lower()
        
        # Exact match
        if term_lower in tag_mappings:
            stmt = f"nwr[{tag_mappings[term_lower]}](around:{radius},{lat},{lon});"
            if stmt not in seen_statements:
                seen_statements.add(stmt)
                statements.append(stmt)
        
        # Fuzzy match (lower threshold for better matching)
        for key, tag in tag_mappings.items():
            if SequenceMatcher(None, term_lower, key).ratio() > 0.5:
                stmt = f"nwr[{tag}](around:{radius},{lat},{lon});"
                if stmt not in seen_statements:
                    seen_statements.add(stmt)
                    statements.append(stmt)
    
    # 3. Brand variations (important for Jollibee, 7-Eleven, etc.)
    for variation in variations:
        if len(variation) >= 2:
            escaped = re.escape(variation)
            # Brand tag
            stmt = f'nwr[~"brand"~"{escaped}",i](around:{radius},{lat},{lon});'
            if stmt not in seen_statements:
                seen_statements.add(stmt)
                statements.append(stmt)
            
            # Name tag
            stmt = f'nwr[~"name"~"{escaped}",i](around:{radius},{lat},{lon});'
            if stmt not in seen_statements:
                seen_statements.add(stmt)
                statements.append(stmt)
            
            # Operator tag (some places use operator)
            stmt = f'nwr[~"operator"~"{escaped}",i](around:{radius},{lat},{lon});'
            if stmt not in seen_statements:
                seen_statements.add(stmt)
                statements.append(stmt)
    
    # 4. Name search for each term
    for term in terms:
        if len(term) >= 3:
            escaped = re.escape(term)
            stmt = f'nwr[~"name"~"{escaped}",i](around:{radius},{lat},{lon});'
            if stmt not in seen_statements:
                seen_statements.add(stmt)
                statements.append(stmt)
    
    # 5. Generic fallback if no statements were generated
    if not statements:
        for term in terms:
            if len(term) >= 3:
                escaped = re.escape(term)
                stmt = f'nwr[~".*"~"{escaped}",i](around:{radius},{lat},{lon});'
                if stmt not in seen_statements:
                    seen_statements.add(stmt)
                    statements.append(stmt)
    
    # Deduplicate and limit
    statements = statements[:20]
    
    ql = f'[out:json][timeout:90];(\n' + '\n'.join(statements) + '\n);out center;'
    return ql

def execute_overpass_query(ql, timeout=90):
    """Execute Overpass query with fallback endpoints"""
    
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            add_api_log(f"Querying {endpoint}", "INFO")
            start_time = time.time()
            res = requests.post(
                endpoint,
                data={"data": ql},
                headers={"User-Agent": "OpenNode/2.0"},
                timeout=timeout
            )
            elapsed = time.time() - start_time
            
            if res.status_code == 200:
                data = res.json()
                elements = data.get("elements", [])
                add_api_log(f"Retrieved {len(elements)} elements in {elapsed:.2f}s", "INFO")
                return elements
            elif res.status_code == 429:
                add_api_log(f"Rate limited, waiting...", "WARNING")
                time.sleep(2)
            else:
                add_api_log(f"HTTP {res.status_code}", "ERROR")
        except Exception as e:
            add_api_log(f"Error: {str(e)[:100]}", "ERROR")
            continue
    
    add_api_log("All endpoints failed", "ERROR")
    return []

def process_overpass_results(elements):
    """Process Overpass results into records with better name handling"""
    records = []
    
    for idx, el in enumerate(elements):
        e_lat = el.get('lat') or el.get('center', {}).get('lat')
        e_lon = el.get('lon') or el.get('center', {}).get('lon')
        
        if e_lat and e_lon:
            tags = el.get('tags', {})
            name = tags.get('name', '')
            
            # Try multiple sources for name
            if not name or str(name).strip().lower() in ['unknown', '', 'nan', 'none']:
                name = tags.get('brand', '')
            
            if not name or str(name).strip().lower() in ['unknown', '', 'nan', 'none']:
                name = tags.get('operator', '')
            
            if not name or str(name).strip().lower() in ['unknown', '', 'nan', 'none']:
                # Use tag value as name
                poi_type = tags.get('amenity') or tags.get('shop') or tags.get('tourism') or tags.get('leisure') or ''
                if poi_type:
                    name = poi_type.capitalize()
                else:
                    continue
            
            poi_type = tags.get('amenity') or tags.get('shop') or tags.get('tourism') or tags.get('leisure') or 'Node'
            
            records.append({
                "lat": e_lat,
                "lon": e_lon,
                "name": str(name)[:50],
                "type": str(poi_type),
                "source": "overpass",
                "has_footprint": False,
                "footprint_geojson": None,
                "visible": True,
                "uid": idx
            })
    
    return records

# -----------------------------------------------------------------------------
# 6. SIDEBAR - SEARCH + WORKSPACE
# -----------------------------------------------------------------------------

# Sidebar toggle button - floating on left edge
st.markdown("""
    <button class="sidebar-toggle-btn" id="sidebarToggleBtn" onclick="toggleSidebarDynamic()">SIDEBAR</button>
    <script>
        function toggleSidebarDynamic() {
            const container = document.querySelector('[data-testid="stAppViewContainer"]');
            const btn = document.getElementById('sidebarToggleBtn');
            
            container.classList.toggle('sidebar-collapsed');
            
            if (container.classList.contains('sidebar-collapsed')) {
                btn.textContent = 'OPEN';
                btn.style.background = 'rgba(201, 171, 76, 0.9)';
            } else {
                btn.textContent = 'SIDEBAR';
                btn.style.background = 'rgba(0, 51, 102, 0.85)';
            }
            
            const isCollapsed = container.classList.contains('sidebar-collapsed');
            container.dataset.sidebarCollapsed = isCollapsed ? 'true' : 'false';
            
            const hiddenInput = document.getElementById('sidebar_state_input');
            if (hiddenInput) {
                hiddenInput.value = isCollapsed ? 'collapsed' : 'expanded';
                hiddenInput.dispatchEvent(new Event('change'));
            }
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            const container = document.querySelector('[data-testid="stAppViewContainer"]');
            const savedState = container.dataset.sidebarCollapsed;
            const btn = document.getElementById('sidebarToggleBtn');
            
            if (savedState === 'true') {
                container.classList.add('sidebar-collapsed');
                if (btn) {
                    btn.textContent = 'OPEN';
                    btn.style.background = 'rgba(201, 171, 76, 0.9)';
                }
            }
        });
    </script>
""", unsafe_allow_html=True)

sidebar_state = st.text_input("", key="sidebar_state_input", label_visibility="collapsed", placeholder="sidebar_state")

if sidebar_state == "collapsed":
    st.session_state.sidebar_collapsed = True
elif sidebar_state == "expanded":
    st.session_state.sidebar_collapsed = False

if st.session_state.sidebar_collapsed:
    st.markdown("""
        <script>
            const container = document.querySelector('[data-testid="stAppViewContainer"]');
            if (!container.classList.contains('sidebar-collapsed')) {
                container.classList.add('sidebar-collapsed');
                const btn = document.getElementById('sidebarToggleBtn');
                if (btn) {
                    btn.textContent = 'OPEN';
                    btn.style.background = 'rgba(201, 171, 76, 0.9)';
                }
                container.dataset.sidebarCollapsed = 'true';
            }
        </script>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SIDEBAR CONTENT
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="brand-title">Open Node</div>', unsafe_allow_html=True)
    
    # ========================================================================
    # SEARCH BAR
    # ========================================================================
    st.markdown("""
        <div style='font-size: 9px; font-weight: 700; color: #003366; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px;'>
            🔍 Search
        </div>
    """, unsafe_allow_html=True)
    
    # Search input with character limit
    search_query = st.text_input(
        "",
        placeholder="e.g., coffee, 7-eleven, jollibee, clinic...",
        key="search_bar_input",
        label_visibility="collapsed",
        max_chars=SearchGuardrails.MAX_QUERY_LENGTH
    )
    
    # Character counter
    if search_query:
        char_count = len(search_query.strip())
        if char_count > 0:
            remaining = SearchGuardrails.MAX_QUERY_LENGTH - char_count
            if remaining < 20:
                st.markdown(f'<div class="search-char-counter warning">{char_count}/{SearchGuardrails.MAX_QUERY_LENGTH}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="search-char-counter">{char_count}/{SearchGuardrails.MAX_QUERY_LENGTH}</div>', unsafe_allow_html=True)
    
    # Search button row
    col_search, col_clear = st.columns([3, 1])
    
    with col_search:
        search_clicked = st.button("🔍 SEARCH", use_container_width=True, type="secondary", key="search_btn")
    
    with col_clear:
        clear_clicked = st.button("✕", use_container_width=True, key="clear_search_btn")
        if clear_clicked:
            st.session_state.search_bar_input = ""
            st.session_state.last_search_query = ""
            st.rerun()
    
    # Process search
    if search_clicked and search_query.strip():
        # Store the search query
        st.session_state.last_search_query = search_query
        
        # Validate
        is_valid, error_msg = SearchGuardrails.validate_query(search_query)
        if not is_valid:
            st.markdown(f'<div class="search-error">⚠️ {error_msg}</div>', unsafe_allow_html=True)
        else:
            # Rate limit
            is_allowed, rate_msg = SearchGuardrails.check_rate_limit()
            if not is_allowed:
                st.markdown(f'<div class="search-error">⏳ {rate_msg}</div>', unsafe_allow_html=True)
            else:
                # Execute search
                normalized = SearchGuardrails.normalize_query(search_query)
                sanitized = SearchGuardrails.sanitize_for_overpass(normalized)
                
                add_api_log(f"Search: '{search_query}'", "INFO")
                
                # Update rate limiting
                st.session_state.search_count += 1
                st.session_state.search_cooldown_until = time.time() + SearchGuardrails.COOLDOWN_SECONDS
                st.session_state.scan_active_loading = True
                st.rerun()
    
    # Show cooldown message
    if time.time() < st.session_state.search_cooldown_until:
        remaining = int(st.session_state.search_cooldown_until - time.time())
        st.markdown(f'<div class="search-cooldown">⏳ Cooldown: {remaining}s</div>', unsafe_allow_html=True)
    
    # Show last search
    if st.session_state.last_search_query:
        st.markdown(f'<div style="font-size:7px; color:#888780; margin-top:2px;">Last search: "{st.session_state.last_search_query}"</div>', unsafe_allow_html=True)
    
    # ========================================================================
    # COORDINATES & RADIUS
    # ========================================================================
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    
    location_input = st.text_input("COORDINATES", value=st.session_state.geo_coords, key="geo_coords_input")
    radius_val = st.number_input("RADIUS (METERS)", min_value=100, max_value=50000, value=st.session_state.geo_radius, key="geo_radius_input", step=100)
    st.session_state.geo_radius = radius_val

    coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", location_input)
    if coord_match:
        lat_coord, lon_coord = float(coord_match.group(1)), float(coord_match.group(2))
        st.session_state.geo_coords = location_input
    else:
        fallback_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", st.session_state.geo_coords)
        lat_coord, lon_coord = (float(fallback_match.group(1)), float(fallback_match.group(2))) if fallback_match else (14.5995, 120.9842)
    
    # ========================================================================
    # WORKSPACE (in sidebar)
    # ========================================================================
    st.markdown("""
        <div style='height: 8px;'></div>
        <div class="workspace-section">
            <div class="workspace-header">
                <span>📋 Workspace</span>
                <span class="workspace-count">{}</span>
            </div>
        </div>
    """.format(len(st.session_state.scanned_records)), unsafe_allow_html=True)
    
    # Display workspace items
    if st.session_state.scanned_records:
        # Group by type
        grouped = {}
        for record in st.session_state.scanned_records:
            rec_type = record.get('type', 'Unclassified')
            if rec_type not in grouped:
                grouped[rec_type] = []
            grouped[rec_type].append(record)
        
        # Show layers with color dots and items
        for rec_type, items in grouped.items():
            color = st.session_state.layer_meta.get(rec_type, {}).get('color', '#003366')
            
            # Layer header
            st.markdown(f"""
                <div class="workspace-layer">
                    <div class="workspace-layer-header">
                        <span class="color-dot" style="background-color:{color};"></span>
                        {rec_type}
                        <span style='font-weight:400; color:#888780; font-size:7px; margin-left:auto;'>({len(items)})</span>
                    </div>
            """, unsafe_allow_html=True)
            
            # Show items (limit to first 10 for performance)
            display_items = items[:10]
            for item in display_items:
                name = item.get('name', 'Unknown')[:30]
                if len(item.get('name', '')) > 30:
                    name += '...'
                st.markdown(f"""
                    <div class="workspace-item">
                        <span class="workspace-item-name">{name}</span>
                        <span class="workspace-item-type">{item.get('type', '')[:15]}</span>
                    </div>
                """, unsafe_allow_html=True)
            
            if len(items) > 10:
                st.markdown(f"""
                    <div style='font-size:7px; color:#888780; padding:2px 4px 2px 16px;'>
                        + {len(items) - 10} more
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="workspace-empty">
                No items found.<br>
                Search to populate workspace.
            </div>
        """, unsafe_allow_html=True)
    
    # ========================================================================
    # DOWNLOAD & CLEAR
    # ========================================================================
    st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.08);'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    visible_only_records = [p for p in st.session_state.scanned_records if p.get('visible', True)]
    with col1:
        st.download_button(
            "📥 EXPORT",
            json.dumps(visible_only_records),
            "scan.json",
            "application/json",
            use_container_width=True
        )
    with col2:
        if st.button("🗑️ CLEAR", type="primary", key="clear_btn", use_container_width=True):
            st.session_state.scanned_records = []
            st.session_state.layer_meta = {}
            st.session_state.scan_active_loading = False
            st.session_state.last_search_query = ""
            clear_api_logs()
            add_api_log("Cleared all data", "INFO")
            st.rerun()
    
    # ========================================================================
    # SESSION LOGS
    # ========================================================================
    st.markdown("<hr style='margin: 8px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.08);'>", unsafe_allow_html=True)
    
    with st.expander("📋 LOGS", expanded=False):
        col_log1, col_log2 = st.columns(2)
        with col_log1:
            if st.button("🔄 REFRESH", key="refresh_logs", use_container_width=True):
                st.rerun()
        with col_log2:
            if st.button("🧹 CLEAR", key="clear_logs_btn", use_container_width=True):
                st.session_state.api_logs = []
                st.rerun()
        
        if st.session_state.api_logs:
            log_text = ""
            for log in st.session_state.api_logs[-20:]:
                prefix = "[ERR]" if log['level'] == 'ERROR' else "[WRN]" if log['level'] == 'WARNING' else "[INF]"
                log_text += f"{prefix} [{log['time']}] {log['message']}\n"
            st.code(log_text, language="text", line_numbers=False)
        else:
            st.info("No logs")

# -----------------------------------------------------------------------------
# 7. PIPELINE - SEARCH EXECUTION
# -----------------------------------------------------------------------------
main_canvas = st.empty()

if st.session_state.scan_active_loading:
    # Show loading overlay
    main_canvas.markdown(f'''
        <div class="py-loading-container">
            <div class="py-spinner"></div>
            <div class="py-loading-title">SEARCHING...</div>
            <div class="py-loading-subtitle">Radius: {radius_val}m | Query: "{st.session_state.last_search_query[:30]}"</div>
            <div class="py-loading-subtitle" id="scan-status-text">Connecting to Overpass...</div>
        </div>
        <script>
            const statusDiv = document.getElementById('scan-status-text');
            const statusMessages = [
                "Connecting to Overpass...",
                "Fetching POI data...",
                "Processing results...",
                "Building workspace...",
                "Ready!"
            ];
            let idx = 0;
            if(statusDiv) {{
                setInterval(() => {{
                    idx = (idx + 1) % statusMessages.length;
                    statusDiv.innerText = statusMessages[idx];
                }}, 800);
            }}
        </script>
    ''', unsafe_allow_html=True)
    
    search_term = st.session_state.last_search_query or st.session_state.search_bar_input or ""
    add_api_log(f"Searching: '{search_term}'", "INFO")
    
    # Build query with improved fuzzy search
    normalized = SearchGuardrails.normalize_query(search_term)
    sanitized = SearchGuardrails.sanitize_for_overpass(normalized)
    
    ql = build_overpass_query(lat_coord, lon_coord, radius_val, sanitized)
    add_api_log(f"Query built with {ql.count('nwr')} statements", "INFO")
    
    # Execute
    elements = execute_overpass_query(ql)
    
    if elements:
        records = process_overpass_results(elements)
        if records:
            st.session_state.scanned_records = records
            st.session_state.last_scan_lat = lat_coord
            st.session_state.last_scan_lon = lon_coord
            
            # Assign colors to layers
            unique_layers = list(set([r.get('type', 'Unclassified') for r in records]))
            cat_palette = ["#003366", "#C9AB4C", "#1A5A8A", "#A8862E", "#3D7DA8", "#7A5C10", "#6A94B0", "#D4B85A", "#001F3F", "#E8D494"]
            for idx, layer in enumerate(unique_layers):
                if layer not in st.session_state.layer_meta:
                    st.session_state.layer_meta[layer] = {
                        "color": cat_palette[idx % len(cat_palette)],
                        "style": st.session_state.global_marker_style,
                        "size": st.session_state.global_marker_size
                    }
            
            add_api_log(f"Found {len(records)} POIs", "INFO")
            st.session_state.scan_active_loading = False
            st.rerun()
        else:
            add_api_log("No valid POIs found", "WARNING")
            st.session_state.scan_active_loading = False
            st.rerun()
    else:
        add_api_log("Search returned no results", "WARNING")
        st.session_state.scan_active_loading = False
        st.rerun()

# -----------------------------------------------------------------------------
# 8. MAP RENDERING
# -----------------------------------------------------------------------------
def compile_features_kml(features):
    kml = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Scanned POIs</name>'
    for f in features:
        if not f.get('visible', True): continue
        name = f.get('name', 'Asset').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        class_type = f.get('type', 'Node').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        kml += f"<Placemark><name>{name}</name><description>{class_type}</description><Point><coordinates>{f['lon']},{f['lat']},0</coordinates></Point></Placemark>"
    return kml + '</Document></kml>'

# Prepare map data
pts_active = st.session_state.scanned_records
layer_meta_json = json.dumps(st.session_state.layer_meta)
target_config_json = json.dumps(st.session_state.target_config)
radius_config_json = json.dumps(st.session_state.radius_config)
geojson_str = json.dumps(pts_active)

render_lat, render_lon = lat_coord, lon_coord
is_stale = "true" if (lat_coord != st.session_state.last_scan_lat or lon_coord != st.session_state.last_scan_lon) else "false"
show_loading = "true" if st.session_state.scan_active_loading else "false"

# API logs panel
api_logs_html = ""
for log in st.session_state.api_logs[-20:]:
    level_class = f"api-log-{log['level'].lower()}"
    api_logs_html += f'<div class="api-log-entry"><span class="api-log-time">[{log["time"]}]</span> <span class="{level_class}">{log["message"]}</span></div>'

api_log_panel = f'''
<div class="api-log-container" id="apiLogPanel">
    <div class="api-log-header" onclick="toggleApiLog()">
        <span>API LOG</span>
        <span class="api-log-close" onclick="event.stopPropagation(); clearApiLogsFromUI();">×</span>
    </div>
    <div class="api-log-content" id="apiLogContent">
        {api_logs_html if api_logs_html else '<div class="api-log-entry"><span class="api-log-time">[--:--:--]</span> <span>No logs.</span></div>'}
    </div>
</div>
<script>
    function toggleApiLog() {{
        const content = document.getElementById('apiLogContent');
        if (content) {{
            if (content.style.display === 'none') {{
                content.style.display = 'block';
            }} else {{
                content.style.display = 'none';
            }}
        }}
    }}
    function clearApiLogsFromUI() {{
        const content = document.getElementById('apiLogContent');
        if (content) {{
            content.innerHTML = '<div class="api-log-entry"><span class="api-log-time">[--:--:--]</span> <span>Logs cleared.</span></div>';
        }}
    }}
</script>
'''

fullscreen_class = "fullscreen-mode" if st.session_state.get('fullscreen_active', False) else ""

# Leaflet HTML template
leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; background: #ffffff; overflow: hidden; font-family: 'Montserrat', sans-serif; }
        #map-container { position: relative; width: 100%; height: 100vh; }
        #map { height: 100vh; width: 100%; z-index: 1; }
        #map-loading-overlay {
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            width: 340px; background: #ffffff; z-index: 99999; 
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            padding: 24px; border-radius: 4px; border: 1px solid rgba(0, 51, 102, 0.15);
            box-shadow: 0 10px 25px rgba(0, 51, 102, 0.15); pointer-events: all;
        }
        .loading-spinner { width: 44px; height: 44px; border: 4px solid rgba(0, 51, 102, 0.1); border-left-color: #003366; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 16px; }
        .loading-text { font-size: 11px; font-weight: 800; color: #003366; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 4px; }
        .loading-subtitle { font-size: 10px; font-weight: 600; color: #C9AB4C; font-family: monospace; margin-top: 6px; }
        .elapsed-timer { font-size: 10px; font-weight: 600; color: #C9AB4C; font-family: monospace; letter-spacing: 0.5px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        
        .color-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; border: 1px solid rgba(0,0,0,0.1); flex-shrink: 0; }
        .poi-text-label { background: #fff; border: 1px solid #003366; padding: 1px 3px; border-radius: 2px; font-size: __LABEL_SIZE__px; font-family: 'Montserrat', sans-serif; font-weight: 700; white-space: nowrap; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .hide-labels .poi-text-label { display: none !important; }
        
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
        
        .config-block-wrapper { padding: 4px 8px; background: #f8fafc; border-bottom: 1px solid rgba(0, 51, 102, 0.05); display: flex; flex-direction: column; gap: 3px; }
        .config-headline { font-size: 7px; font-weight: 800; color: #003366; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 1px; }
        .config-flex-row { display: flex; align-items: center; justify-content: space-between; font-size: 8px; font-weight: 600; color: #003366; gap: 4px; }
        .config-flex-row select, .config-flex-row input { font-size: 8px; font-family: 'Montserrat', sans-serif; color: #003366; background: #ffffff; border: 1px solid rgba(0, 51, 102, 0.15); border-radius: 2px; padding: 1px 2px; outline: none; }
        .slider-control-element { flex-grow: 1; margin: 0; -webkit-appearance: none; height: 3px; background: rgba(0,51,102,0.1); border-radius: 2px; outline: none; }
        .slider-control-element::-webkit-slider-thumb { -webkit-appearance: none; width: 8px; height: 8px; border-radius: 50%; background: #003366; cursor: pointer; }
        
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
    </style>
</head>
<body>
    <div id="map-container" class="__FULLSCREEN_CLASS__">
        <div id="map-loading-overlay" style="display: __SHOW_LOADING_DISPLAY__;">
            <div class="loading-spinner"></div>
            <div class="loading-text">Searching...</div>
            <div class="loading-subtitle" id="scan-status-text-map">Initializing queries...</div>
            <div class="elapsed-timer" id="timer-output">Elapsed: 0.0s</div>
        </div>
        <div id="map"></div>
        
        <!-- Fullscreen toggle button on map - top left -->
        <button class="map-fullscreen-btn" id="mapFullscreenBtn" onclick="toggleFullscreen()">⛶</button>
        
        <!-- Basemap controls overlay -->
        <div style="position:absolute; bottom:30px; right:10px; z-index:1000; background:rgba(255,255,255,0.92); border-radius:4px; padding:6px 10px; border:1px solid rgba(0,51,102,0.1); box-shadow:0 2px 8px rgba(0,0,0,0.08);">
            <div style="font-size:6px; font-weight:800; color:#003366; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:2px;">Basemap</div>
            <div class="config-flex-row" style="font-size:7px;">
                <select id="basemap-select" onchange="switchActiveBasemap(this.value)" style="font-size:7px; padding:1px 4px;">
                    <option value="osm">OSM</option>
                    <option value="satellite">Satellite</option>
                    <option value="carto">Carto</option>
                </select>
                <label style="font-size:7px; font-weight:700; color:#003366; display:flex; align-items:center; gap:2px; cursor:pointer;">
                    <input type="checkbox" id="label-toggle-chk" onchange="toggleLabelsMatrix(this.checked)" style="accent-color:#003366;"> Labels
                </label>
            </div>
            <div class="label-size-row">
                <span>size</span>
                <input type="range" id="labelSizeSlider" min="6" max="20" value="__LABEL_SIZE__" oninput="updateLabelSize(this.value)">
                <span class="label-size-value" id="labelSizeValue">__LABEL_SIZE__</span>
            </div>
            <div class="config-flex-row" style="font-size:7px; margin-top:2px; border-top:1px solid rgba(0,51,102,0.05); padding-top:2px;">
                <span>Markers:</span>
                <select id="gl-marker-style" onchange="patchGlobalMarkerStyle(this.value)" style="font-size:7px; padding:1px 4px;">
                    <option value="dots">Dots</option>
                    <option value="pin">Pin</option>
                    <option value="modern-pin">Modern</option>
                </select>
                <input type="color" id="gl-marker-color" value="__GLOBAL_MARKER_COLOR__" onchange="patchGlobalMarkerColor(this.value)" style="width:20px; height:16px; padding:0; border:none;">
            </div>
        </div>
        
        __API_LOG_PANEL__
    </div>

    <script>
        const map = L.map('map', { zoomControl: false, attributionControl: false, preferCanvas: true }).setView([__LAT__, __LON__], 14);
        let layerMeta = __LAYER_META_JSON__; let targetConfig = __TARGET_CONFIG_JSON__; let radiusConfig = __RADIUS_CONFIG_JSON__; let pts = __GEOJSON__; 
        let labelSize = __LABEL_SIZE__;
        
        L.control.zoom({ position: 'topright' }).addTo(map);
        
        if (__SHOW_LOADING__) {
            const overlay = document.getElementById('map-loading-overlay');
            if (overlay) overlay.style.display = 'flex';
            const timerInterval = setInterval(() => {
                const timerEl = document.getElementById('timer-output');
                if (timerEl) {
                    let current = parseFloat(timerEl.innerText.replace('Elapsed: ', '').replace('s', '')) || 0;
                    timerEl.innerText = "Elapsed: " + (current + 0.5).toFixed(1) + "s";
                }
            }, 500);
        }

        const basemaps = {
            osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }),
            satellite: L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', { maxZoom: 20 }),
            carto: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 })
        };
        basemaps[(localStorage.getItem('ts_persistent_basemap') || 'osm')].addTo(map);
        
        function switchActiveBasemap(targetKey) {
            Object.keys(basemaps).forEach(k => { if(map.hasLayer(basemaps[k])) map.removeLayer(basemaps[k]); });
            basemaps[targetKey].addTo(map); localStorage.setItem('ts_persistent_basemap', targetKey);
        }

        let labelsActive = localStorage.getItem('ts_persistent_labels') !== 'false';
        document.getElementById('label-toggle-chk').checked = labelsActive;
        if (!labelsActive) document.getElementById('map').classList.add('hide-labels');
        
        function toggleLabelsMatrix(isShown) {
            if (isShown) document.getElementById('map').classList.remove('hide-labels');
            else document.getElementById('map').classList.add('hide-labels');
            localStorage.setItem('ts_persistent_labels', isShown);
        }

        let radiusCircle = null;
        function renderRadiusCircleBounds() {
            if (radiusCircle) map.removeLayer(radiusCircle);
            radiusCircle = L.circle([__LAT__, __LON__], { radius: __RADIUS__, color: radiusConfig.color, weight: parseFloat(radiusConfig.weight), fillColor: radiusConfig.color, fillOpacity: parseFloat(radiusConfig.fill_opacity) }).addTo(map);
        }

        let centerMarker = null;
        function renderTargetCenterIcon() {
            if (centerMarker) map.removeLayer(centerMarker);
            const d = targetConfig.size; const c = targetConfig.color;
            const htmlElement = targetConfig.style === "star" ? `<div style="background-color: ${c}; color: #ffffff; width: ${d}px; height: ${d}px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: ${d*0.5}px; border: 2px solid #ffffff; box-shadow: 0 2px 6px rgba(0, 51, 102, 0.4);">★</div>` : `<div style="background-color: ${c}; width: ${d}px; height: ${d}px; border-radius: 50%; border: 3px solid #ffffff; box-shadow: 0 2px 6px rgba(0, 51, 102, 0.4);"></div>`;
            centerMarker = L.marker([__LAT__, __LON__], { icon: L.divIcon({ className: 'custom-center-icon', html: htmlElement, iconSize: [d, d], iconAnchor: [d/2, d/2] }), zIndexOffset: 999999 }).addTo(map);
        }

        const generateMarkerElement = (color, styleMode, sizeDimension) => {
            const d = parseInt(sizeDimension);
            if (styleMode === "pin") {
                return L.divIcon({ html: `<div class="custom-pin-container"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${d*1.3}" height="${d*1.3}"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" fill="${color}" stroke="#ffffff" stroke-width="1.5"/></svg></div>`, className: '', iconSize: [d*1.3, d*1.3], iconAnchor: [d*0.65, d*1.3] });
            } else if (styleMode === "modern-pin") {
                const w = d * 1.5; const h = d * 2.5; const r = d * 0.45; 
                const customSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 65" width="${w}" height="${h}"><defs><radialGradient id="groundShadow" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#000000" stop-opacity="1.0"/><stop offset="100%" stop-color="#000000" stop-opacity="0"/></radialGradient><radialGradient id="sphereGloss-${color.replace('#','')}" cx="35%" cy="35%" r="65%"><stop offset="0%" stop-color="#ffffff" stop-opacity="0.9"/><stop offset="50%" stop-color="${color}"/><stop offset="100%" stop-color="${color}" stop-opacity="0.75"/></radialGradient></defs><ellipse cx="20" cy="44" rx="12" ry="3.5" fill="url(#groundShadow)" /><path d="M20 20 L20 44" stroke="#222222" stroke-width="2.5" stroke-linecap="round"/><path d="M20 20 L20 44" stroke="#888888" stroke-width="0.8" stroke-linecap="round"/><circle cx="20" cy="20" r="${r}" fill="url(#sphereGloss-${color.replace('#','')})"/></svg>`;
                return L.divIcon({ html: `<div style="transform: translate(-50%, -92%); width: ${w}px; height: ${h}px;">${customSvg}</div>`, className: '', iconSize: [w, h], iconAnchor: [0, 0] });
            }
            return L.divIcon({ html: `<div style="background-color: ${color}; width: ${d}px; height: ${d}px; border-radius: 50%; border: 1.5px solid #ffffff; box-shadow: 0 1px 4px rgba(0,0,0,0.2);"></div>`, className: '', iconSize: [d, d], iconAnchor: [d/2, d/2] });
        };

        const layerGroupsRef = {}; const categoryMap = {};

        function compileLayersAndRenderPoints() {
            Object.keys(layerGroupsRef).forEach(k => { map.removeLayer(layerGroupsRef[k]); delete layerGroupsRef[k]; });
            Object.keys(categoryMap).forEach(k => delete categoryMap[k]);
            pts.forEach(p => {
                const layerKey = p.type || 'Unclassified';
                if (!categoryMap[layerKey]) categoryMap[layerKey] = []; categoryMap[layerKey].push(p);
            });
            Object.keys(categoryMap).forEach(key => {
                layerGroupsRef[key] = L.layerGroup().addTo(map);
                const meta = layerMeta[key] || { color: "#003366", style: "dots", size: 12 };
                categoryMap[key].forEach(p => {
                    if (p.visible === false) return;
                    const marker = L.marker([p.lat, p.lon], { icon: generateMarkerElement(meta.color, meta.style, meta.size) }).bindPopup(`<b>${p.name}</b><br><span style="color:#888780;font-size:8px;">${p.type}</span>`);
                    if (p.name && p.name !== 'Unknown') marker.bindTooltip(p.name, { permanent: true, direction: 'top', offset: [0, -10], className: 'poi-text-label' });
                    marker.addTo(layerGroupsRef[key]);
                });
            });
        }

        window.patchGlobalMarkerStyle = function(v) { Object.keys(layerMeta).forEach(k => layerMeta[k].style = v); compileLayersAndRenderPoints(); };
        window.patchGlobalMarkerSize = function(v) { Object.keys(layerMeta).forEach(k => layerMeta[k].size = parseInt(v)); compileLayersAndRenderPoints(); };
        window.patchGlobalMarkerColor = function(v) { Object.keys(layerMeta).forEach(k => layerMeta[k].color = v); compileLayersAndRenderPoints(); };
        window.patchTargetCenterConfig = function(key, val) { targetConfig[key] = val; renderTargetCenterIcon(); };
        window.patchRadiusLayerConfig = function(key, val) { radiusConfig[key] = val; renderRadiusCircleBounds(); };
        window.updateLabelSize = function(val) {
            labelSize = val;
            document.getElementById('labelSizeValue').textContent = val;
            document.querySelectorAll('.poi-text-label').forEach(el => {
                el.style.fontSize = val + 'px';
            });
        };

        map.on('contextmenu', function(e) {
            const lat = e.latlng.lat; const lng = e.latlng.lng;
            const menuHtml = `<div style="font-family: Montserrat, sans-serif; font-size: 9px; color: #003366; min-width: 120px; background:#fff; padding:4px;"><div style="font-weight: 800; border-bottom: 1px solid #C9AB4C; padding-bottom: 3px; margin-bottom: 4px; letter-spacing: 0.5px;">MAP</div><div style="padding: 4px 2px; cursor: pointer; font-weight: 700;" onclick="navigator.clipboard.writeText('${lat.toFixed(5)}, ${lng.toFixed(5)}'); map.closePopup();">Copy Coords</div><div style="padding: 4px 2px; cursor: pointer; font-weight: 700;" onclick="window.open('https://www.google.com/maps/search/?api=1&query=${lat},${lng}', '_blank'); map.closePopup();">Google Maps</div><div style="padding: 4px 2px; cursor: pointer; font-weight: 700;" onclick="window.open('https://www.google.com/maps?layer=c&cbll=${lat},${lng}', '_blank'); map.closePopup();">Streetview</div></div>`;
            L.popup().setLatLng(e.latlng).setContent(menuHtml).openOn(map);
        });
        
        function toggleFullscreen() {
            const container = document.getElementById('map-container');
            container.classList.toggle('fullscreen-mode');
            const btn = document.getElementById('mapFullscreenBtn');
            if (container.classList.contains('fullscreen-mode')) {
                btn.textContent = '⛶';
                btn.style.background = 'rgba(0, 51, 102, 0.9)';
                btn.style.color = '#ffffff';
                btn.style.borderColor = 'rgba(255,255,255,0.3)';
            } else {
                btn.textContent = '⛶';
                btn.style.background = 'rgba(255,255,255,0.92)';
                btn.style.color = '#003366';
                btn.style.borderColor = 'rgba(0, 51, 102, 0.15)';
            }
            setTimeout(function() {
                map.invalidateSize();
            }, 350);
        }

        renderTargetCenterIcon(); renderRadiusCircleBounds(); compileLayersAndRenderPoints();
        if (pts.length > 0 && !__IS_STALE__) {
            const validPts = pts.filter(p => p.visible !== false); if (validPts.length > 0) map.fitBounds(L.featureGroup([L.marker([__LAT__, __LON__]), ...validPts.map(p => L.marker([p.lat, p.lon]))]).getBounds().pad(0.05));
        }
    </script>
</body>
</html>
"""

fallback_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", st.session_state.geo_coords)
render_lat, render_lon = (float(fallback_match.group(1)), float(fallback_match.group(2))) if fallback_match else (14.5995, 120.9842)

show_loading_display = "flex" if st.session_state.scan_active_loading else "none"
label_size = st.session_state.get('label_size', 9)

leaflet_html = (leaflet_template
                .replace("__LAT__", str(render_lat))
                .replace("__LON__", str(render_lon))
                .replace("__RADIUS__", str(radius_val))
                .replace("__IS_STALE__", is_stale)
                .replace("__SHOW_LOADING__", "true" if st.session_state.scan_active_loading else "false")
                .replace("__SHOW_LOADING_DISPLAY__", show_loading_display)
                .replace("__GLOBAL_MARKER_SIZE__", str(st.session_state.global_marker_size))
                .replace("__GLOBAL_MARKER_COLOR__", str(st.session_state.global_marker_color))
                .replace("__TARGET_CONFIG_JSON__", target_config_json)
                .replace("__RADIUS_CONFIG_JSON__", radius_config_json)
                .replace("__LAYER_META_JSON__", layer_meta_json)
                .replace("__GEOJSON__", geojson_str)
                .replace("__API_LOG_PANEL__", api_log_panel)
                .replace("__LABEL_SIZE__", str(label_size))
                .replace("__FULLSCREEN_CLASS__", fullscreen_class))

st.components.v1.html(leaflet_html, height=850, scrolling=False)

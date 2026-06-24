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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

        /* Reset & Base */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
            background-color: #ffffff !important;
            color: #000000 !important;
            font-family: 'Inter', sans-serif !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
            height: 100vh !important;
            width: 100vw !important;
        }

        /* Hide Streamlit default elements */
        [data-testid="stSidebarCollapseButton"], 
        [data-testid="collapsedControl"],
        .st-emotion-cache-1cypcdb,
        .st-emotion-cache-6qob1r,
        [data-testid="stHeader"], header, #stDecoration,
        .stAppHeader, .st-emotion-cache-12fmjuu {
            display: none !important;
        }

        /* Main canvas full screen */
        [data-testid="stMain"] { 
            width: 100vw !important;
            min-width: 100vw !important;
            max-width: 100vw !important;
            height: 100vh !important;
            overflow: hidden !important; 
            margin: 0px !important; 
            padding: 0px !important; 
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

        /* Utility Classes */
        .panel-shadow { box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .bg-navy { background-color: #003366; }
        .text-navy { color: #003366; }
        .border-navy { border-color: #003366; }
        .hover\\:bg-navy-dark:hover { background-color: #002244; }
        .sidebar-transition { transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1); }

        /* Floating Controls Container */
        .floating-controls {
            position: fixed;
            top: 16px;
            left: 16px;
            right: 16px;
            display: flex;
            align-items: flex-start;
            gap: 12px;
            z-index: 99999;
            pointer-events: none;
        }
        .floating-controls > * {
            pointer-events: auto;
        }

        /* Search Container */
        .search-container {
            display: flex;
            flex: 1;
            max-width: 560px;
            align-items: center;
            gap: 8px;
        }

        .search-wrapper {
            position: relative;
            flex: 1;
        }
        .search-wrapper .search-icon {
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: #9ca3af;
            font-size: 18px;
            pointer-events: none;
            transition: color 0.2s;
        }
        .search-wrapper:focus-within .search-icon {
            color: #000000;
        }

        #search-input {
            width: 100%;
            padding: 10px 16px 10px 40px;
            border: 1.5px solid #000000;
            background: #ffffff;
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            outline: none;
            transition: box-shadow 0.2s;
            border-radius: 8px;
        }
        #search-input:focus {
            box-shadow: 0 0 0 3px rgba(0, 51, 102, 0.15);
        }
        #search-input::placeholder {
            color: #9ca3af;
        }

        #search-btn {
            background: #003366;
            color: #ffffff;
            padding: 10px 24px;
            font-family: 'Inter', sans-serif;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border: 1.5px solid #000000;
            cursor: pointer;
            transition: background 0.2s;
            white-space: nowrap;
            border-radius: 8px;
        }
        #search-btn:hover {
            background: #002244;
        }

        /* Menu Button */
        #toggle-sidebar {
            background: #ffffff;
            border: 1.5px solid #000000;
            padding: 10px 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: background 0.2s;
            color: #003366;
            border-radius: 8px;
            flex-shrink: 0;
        }
        #toggle-sidebar:hover {
            background: #f3f4f6;
        }
        #toggle-sidebar .menu-icon {
            font-size: 20px;
            line-height: 1;
        }

        /* Edit Button */
        #toggle-styling {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 10px 16px;
            background: #ffffff;
            border: 1.5px solid #000000;
            cursor: pointer;
            transition: background 0.2s;
            font-family: 'Inter', sans-serif;
            font-size: 12px;
            font-weight: 700;
            color: #003366;
            border-radius: 8px;
            flex-shrink: 0;
        }
        #toggle-styling:hover {
            background: #f3f4f6;
        }
        #toggle-styling .edit-icon {
            font-size: 18px;
            line-height: 1;
        }

        /* Styling Panel */
        #styling-panel {
            position: fixed;
            right: 16px;
            top: 76px;
            width: 288px;
            background: #ffffff;
            border: 1.5px solid #000000;
            padding: 20px;
            z-index: 99998;
            display: none;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            max-height: calc(100vh - 120px);
            overflow-y: auto;
        }
        #styling-panel.open {
            display: block;
        }
        #styling-panel section {
            margin-bottom: 16px;
        }
        #styling-panel section:last-child {
            margin-bottom: 0;
        }
        #styling-panel h2 {
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #9ca3af;
            margin-bottom: 12px;
        }
        #styling-panel label {
            display: block;
            font-size: 12px;
            font-weight: 500;
            margin-bottom: 4px;
            color: #000000;
        }
        #styling-panel .color-options {
            display: flex;
            gap: 8px;
        }
        #styling-panel .color-options button {
            width: 24px;
            height: 24px;
            border: 1.5px solid #d1d5db;
            cursor: pointer;
            transition: ring 0.2s;
            border-radius: 4px;
            padding: 0;
        }
        #styling-panel .color-options button.active {
            ring: 2px solid #000000;
            ring-offset: 2px;
        }
        #styling-panel .color-options button:hover {
            ring: 2px solid #000000;
            ring-offset: 2px;
        }
        #styling-panel select {
            width: 100%;
            border: 1.5px solid #d1d5db;
            padding: 6px 12px;
            font-family: 'Inter', sans-serif;
            font-size: 13px;
            outline: none;
            transition: border-color 0.2s;
            border-radius: 4px;
            background: #ffffff;
        }
        #styling-panel select:focus {
            border-color: #000000;
        }
        #styling-panel .toggle-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        #styling-panel .toggle-row span {
            font-size: 12px;
            color: #000000;
        }
        #styling-panel .toggle-row input[type="checkbox"] {
            accent-color: #003366;
            width: 16px;
            height: 16px;
            cursor: pointer;
        }
        #styling-panel hr {
            border: none;
            border-top: 1px solid #f3f4f6;
            margin: 16px 0;
        }
        #styling-panel .basemap-option {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px 12px;
            border: 1px solid #f3f4f6;
            cursor: pointer;
            transition: background 0.2s;
            border-radius: 4px;
        }
        #styling-panel .basemap-option:hover {
            background: #f9fafb;
        }
        #styling-panel .basemap-option input[type="radio"] {
            accent-color: #003366;
            cursor: pointer;
        }
        #styling-panel .basemap-option span {
            font-size: 12px;
            color: #000000;
        }

        /* Footer Bar */
        .map-footer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: 32px;
            border-top: 1.5px solid #000000;
            background: #ffffff;
            display: flex;
            align-items: center;
            padding: 0 16px;
            justify-content: space-between;
            z-index: 99998;
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            color: #6b7280;
            text-transform: uppercase;
        }
        .map-footer .footer-left {
            display: flex;
            gap: 16px;
        }
        .map-footer .footer-right .status {
            color: #000000;
            font-weight: 700;
        }

        /* Sidebar */
        #sidebar {
            position: fixed;
            top: 0;
            left: 0;
            height: 100vh;
            width: 320px;
            background: #ffffff;
            border-right: 1.5px solid #000000;
            z-index: 999999;
            transform: translateX(0);
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            overflow-y: auto;
            overflow-x: hidden;
            padding: 20px 16px;
            display: flex;
            flex-direction: column;
        }
        #sidebar.collapsed {
            transform: translateX(-320px);
        }

        #sidebar .brand-title {
            font-family: 'Inter', sans-serif;
            font-weight: 800;
            font-size: 20px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #003366;
            padding-bottom: 12px;
            border-bottom: 1.5px solid #000000;
            margin-bottom: 16px;
        }

        #sidebar .sidebar-section {
            margin-bottom: 16px;
        }
        #sidebar .sidebar-section:last-child {
            margin-bottom: 0;
        }
        #sidebar .sidebar-section-title {
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #9ca3af;
            margin-bottom: 8px;
        }

        #sidebar .workspace-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        #sidebar .workspace-header span {
            font-size: 11px;
            font-weight: 700;
            color: #000000;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        #sidebar .workspace-header .count {
            background: #f3f4f6;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: 700;
            color: #000000;
        }

        #sidebar .workspace-layer {
            margin-bottom: 8px;
            border: 1px solid #f3f4f6;
            padding: 8px;
            border-radius: 4px;
        }
        #sidebar .workspace-layer-header {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 11px;
            font-weight: 700;
            color: #000000;
            padding-bottom: 4px;
            border-bottom: 1px solid #f3f4f6;
            margin-bottom: 4px;
        }
        #sidebar .workspace-layer-header .color-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            border: 1px solid rgba(0,0,0,0.08);
            flex-shrink: 0;
        }
        #sidebar .workspace-layer-header .layer-count {
            font-weight: 500;
            color: #6b7280;
            font-size: 10px;
            margin-left: auto;
        }
        #sidebar .workspace-item {
            font-size: 11px;
            padding: 4px 6px 4px 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #374151;
        }
        #sidebar .workspace-item:hover {
            background: #f9fafb;
        }
        #sidebar .workspace-item .item-name {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 170px;
        }
        #sidebar .workspace-item .item-type {
            font-size: 9px;
            color: #6b7280;
            background: #f3f4f6;
            padding: 1px 8px;
            border-radius: 4px;
        }
        #sidebar .workspace-empty {
            font-size: 12px;
            color: #6b7280;
            padding: 24px 8px;
            text-align: center;
            border: 1px dashed #e5e7eb;
            border-radius: 6px;
        }

        #sidebar .sidebar-actions {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 8px;
        }
        #sidebar .sidebar-actions button {
            padding: 8px 12px;
            font-family: 'Inter', sans-serif;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border: 1.5px solid #000000;
            cursor: pointer;
            transition: background 0.2s;
            border-radius: 4px;
        }
        #sidebar .sidebar-actions .btn-export {
            background: #003366;
            color: #ffffff;
        }
        #sidebar .sidebar-actions .btn-export:hover {
            background: #002244;
        }
        #sidebar .sidebar-actions .btn-clear {
            background: #ffffff;
            color: #000000;
        }
        #sidebar .sidebar-actions .btn-clear:hover {
            background: #f3f4f6;
        }

        #sidebar .log-section {
            margin-top: 12px;
            border-top: 1px solid #f3f4f6;
            padding-top: 12px;
        }
        #sidebar .log-section .log-toggle {
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #6b7280;
            cursor: pointer;
            background: none;
            border: none;
            font-family: 'Inter', sans-serif;
        }
        #sidebar .log-section .log-toggle:hover {
            color: #000000;
        }
        #sidebar .log-section .log-content {
            margin-top: 8px;
            background: #f9fafb;
            padding: 8px 12px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            color: #374151;
            max-height: 120px;
            overflow-y: auto;
            border-radius: 4px;
            border: 1px solid #f3f4f6;
        }
        #sidebar .log-section .log-content .log-entry {
            padding: 2px 0;
            border-bottom: 1px solid #f3f4f6;
        }
        #sidebar .log-section .log-content .log-entry:last-child {
            border-bottom: none;
        }
        #sidebar .log-section .log-content .log-time {
            color: #6b7280;
            margin-right: 6px;
        }
        #sidebar .log-section .log-content .log-info {
            color: #059669;
        }
        #sidebar .log-section .log-content .log-warning {
            color: #d97706;
        }
        #sidebar .log-section .log-content .log-error {
            color: #dc2626;
        }

        /* Loading Overlay */
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255,255,255,0.9);
            z-index: 9999999;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            gap: 12px;
            backdrop-filter: blur(4px);
        }
        .loading-overlay .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid #f3f4f6;
            border-top-color: #003366;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        .loading-overlay .loading-text {
            font-family: 'Inter', sans-serif;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #003366;
        }
        .loading-overlay .loading-sub {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: #6b7280;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 2px; }
        ::-webkit-scrollbar-track { background: transparent; }
        * { scrollbar-width: thin !important; }

        /* Responsive */
        @media (max-width: 768px) {
            .search-container { max-width: 100%; }
            #search-input { font-size: 13px; padding: 8px 12px 8px 36px; }
            #search-btn { padding: 8px 16px; font-size: 10px; }
            #toggle-styling span { display: none; }
            #styling-panel { right: 8px; width: 260px; }
            #sidebar { width: 280px; }
            #sidebar.collapsed { transform: translateX(-280px); }
            .map-footer { font-size: 8px; padding: 0 8px; }
            .map-footer .footer-left { gap: 8px; }
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. STATE PERSISTENCE
# -----------------------------------------------------------------------------
DEFAULT_COORDS = "14.64650, 121.05804"
DEFAULT_RADIUS = 1000

if 'geo_coords' not in st.session_state: st.session_state.geo_coords = DEFAULT_COORDS
if 'geo_radius' not in st.session_state: st.session_state.geo_radius = DEFAULT_RADIUS
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'last_scan_lat' not in st.session_state: st.session_state.last_scan_lat = 14.64650
if 'last_scan_lon' not in st.session_state: st.session_state.last_scan_lon = 121.05804
if 'layer_meta' not in st.session_state: st.session_state.layer_meta = {}
if 'scan_active_loading' not in st.session_state: st.session_state.scan_active_loading = False
if 'sidebar_collapsed' not in st.session_state: st.session_state.sidebar_collapsed = True
if 'api_logs' not in st.session_state: st.session_state.api_logs = []
if 'search_cooldown_until' not in st.session_state: st.session_state.search_cooldown_until = 0
if 'search_count' not in st.session_state: st.session_state.search_count = 0
if 'search_reset_time' not in st.session_state: st.session_state.search_reset_time = time.time()
if 'last_search_query' not in st.session_state: st.session_state.last_search_query = ""
if 'styling_panel_open' not in st.session_state: st.session_state.styling_panel_open = False
if 'basemap_choice' not in st.session_state: st.session_state.basemap_choice = "osm"
if 'show_labels' not in st.session_state: st.session_state.show_labels = True
if 'label_size' not in st.session_state: st.session_state.label_size = 10
if 'marker_style' not in st.session_state: st.session_state.marker_style = "pin"
if 'marker_color' not in st.session_state: st.session_state.marker_color = "#003366"

# -----------------------------------------------------------------------------
# 3. INTERACTIVE LOG PANEL DEFINITION
# -----------------------------------------------------------------------------
def add_api_log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.api_logs.append({"time": timestamp, "message": message, "level": level})
    if len(st.session_state.api_logs) > 100:
        st.session_state.api_logs = st.session_state.api_logs[-100:]

def clear_api_logs():
    st.session_state.api_logs = []

# -----------------------------------------------------------------------------
# 4. SEARCH PROTECTION GUARDRAILS
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
    
    BRAND_VARIATIONS = {
        'jollibee': ['jolibee', 'jbee', 'jfc', 'jollibee foods', 'jollibee food corporation'],
        'mcdonalds': ['mcdonald', 'mcdo', 'mcd', 'golden arches', 'mickey d'],
        '7-eleven': ['7/11', '7-11', '711', 'seven eleven', 'seven-eleven'],
        'kfc': ['kentucky fried chicken', 'kfc', 'kentucky'],
        'greenwich': ['greenwich pizza', 'greenwich'],
        'chowking': ['chow king', 'chowking'],
        'burger king': ['bk', 'burgerking', 'burger king'],
        'starbucks': ['starbucks coffee', 'starbucks'],
        'ministop': ['mini stop', 'ministop'],
        'family mart': ['family mart', 'familymart'],
        'lawson': ['lawson'],
        'shell': ['shell gas', 'shell station', 'shell'],
        'petron': ['petron gas', 'petron'],
        'caltex': ['caltex gas', 'caltex'],
    }
    
    CATEGORY_MAPPINGS = {
        'veterinary': ['vet', 'veterinary', 'animal clinic', 'pet clinic', 'animal hospital'],
        'clinic': ['clinic', 'medical clinic', 'health clinic', 'doctor'],
        'restaurant': ['restaurant', 'eatery', 'dining', 'food place'],
        'cafe': ['cafe', 'coffee', 'coffee shop', 'cafeteria'],
        'bakery': ['bakery', 'bread', 'pastry'],
        'supermarket': ['supermarket', 'grocery', 'market', 'store'],
        'pharmacy': ['pharmacy', 'drugstore', 'chemist', 'medicine'],
        'hospital': ['hospital', 'medical center', 'health center'],
        'school': ['school', 'academy', 'learning center'],
        'hotel': ['hotel', 'motel', 'lodging', 'inn'],
        'gas': ['gas', 'fuel', 'petrol', 'gas station'],
        'parking': ['parking', 'car park', 'parking lot'],
        'bank': ['bank', 'financial', 'credit union'],
        'police': ['police', 'police station', 'precinct'],
        'fire': ['fire station', 'fire department'],
        'library': ['library', 'bookstore'],
        'mall': ['mall', 'shopping center', 'shopping mall'],
        'cinema': ['cinema', 'movie theater', 'theater'],
        'park': ['park', 'garden', 'recreation'],
        'gym': ['gym', 'fitness', 'exercise'],
        'church': ['church', 'place of worship', 'cathedral'],
        'bar': ['bar', 'pub', 'tavern', 'nightclub'],
        'fast food': ['fast food', 'fastfood', 'quick service'],
        'convenience': ['convenience store', 'convenience', 'mini mart'],
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
        if current_time - st.session_state.search_reset_time > 60:
            st.session_state.search_count = 0
            st.session_state.search_reset_time = current_time
        if current_time < st.session_state.search_cooldown_until:
            remaining = int(st.session_state.search_cooldown_until - current_time)
            return False, f"Please wait {remaining}s before searching again"
        if st.session_state.search_count >= cls.RATE_LIMIT_PER_MINUTE:
            return False, f"Rate limit: {cls.RATE_LIMIT_PER_MINUTE} searches per minute"
        return True, "OK"
    
    @classmethod
    def normalize_query(cls, query):
        query = ' '.join(query.split())
        query = query.lower()
        replacements = {
            '7/11': '7-eleven', '7-11': '7-eleven', '711': '7-eleven',
            'seven eleven': '7-eleven', 'mcdo': 'mcdonalds', 'jbee': 'jollibee',
            '&': 'and', '+': 'and',
        }
        for orig, repl in replacements.items():
            query = query.replace(orig, repl)
        return query
    
    @classmethod
    def get_brand_variations(cls, query):
        query_lower = query.lower().strip()
        variations = []
        
        for brand, variants in cls.BRAND_VARIATIONS.items():
            if query_lower == brand or query_lower in variants:
                variations = [brand] + variants
                break
        
        if not variations:
            for brand, variants in cls.BRAND_VARIATIONS.items():
                for variant in variants:
                    if variant in query_lower or query_lower in variant:
                        variations = [brand] + variants
                        break
                if variations:
                    break
        
        if not variations:
            variations = [query_lower]
        
        return list(set(variations))
    
    @classmethod
    def get_category_match(cls, query):
        query_lower = query.lower().strip()
        
        for category, terms in cls.CATEGORY_MAPPINGS.items():
            if query_lower == category or query_lower in terms:
                return category
        
        best_match = None
        best_score = 0.0
        
        for category, terms in cls.CATEGORY_MAPPINGS.items():
            score = SequenceMatcher(None, query_lower, category).ratio()
            if score > best_score:
                best_score = score
                best_match = category
            
            for term in terms:
                score = SequenceMatcher(None, query_lower, term).ratio()
                if score > best_score:
                    best_score = score
                    best_match = category
        
        if best_score >= 0.6:
            return best_match
        
        return None
    
    @classmethod
    def sanitize_for_overpass(cls, query):
        sanitized = re.sub(r'[^a-zA-Z0-9\s\-/.]', '', query)
        if len(sanitized) > 50:
            sanitized = sanitized[:50]
        return sanitized

# -----------------------------------------------------------------------------
# 5. OVERPASS QUERY PIPELINE MODULE
# -----------------------------------------------------------------------------
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

def build_overpass_query(lat, lon, radius, search_terms):
    add_api_log(f"Building query for: '{search_terms}'", "INFO")
    
    brand_variations = SearchGuardrails.get_brand_variations(search_terms)
    add_api_log(f"Brand variations: {brand_variations}", "INFO")
    
    category_match = SearchGuardrails.get_category_match(search_terms)
    if category_match:
        add_api_log(f"Category match: {category_match}", "INFO")
    
    terms = search_terms.lower().split()
    statements = []
    seen_statements = set()
    
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
        'veterinary': 'amenity=veterinary',
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
        'grooming': 'shop=pet_grooming',
    }
    
    for variation in brand_variations:
        if len(variation) >= 2:
            escaped = re.escape(variation)
            stmt = f'nwr[~"brand"~"^{escaped}$",i](around:{radius},{lat},{lon});'
            if stmt not in seen_statements:
                seen_statements.add(stmt)
                statements.append(stmt)
            
            stmt = f'nwr[~"name"~"^{escaped}$",i](around:{radius},{lat},{lon});'
            if stmt not in seen_statements:
                seen_statements.add(stmt)
                statements.append(stmt)
            
            stmt = f'nwr[~"name"~"{escaped}",i](around:{radius},{lat},{lon});'
            if stmt not in seen_statements:
                seen_statements.add(stmt)
                statements.append(stmt)
            
            stmt = f'nwr[~"operator"~"{escaped}",i](around:{radius},{lat},{lon});'
            if stmt not in seen_statements:
                seen_statements.add(stmt)
                statements.append(stmt)
    
    if len(statements) < 2:
        if category_match and category_match in tag_mappings:
            stmt = f"nwr[{tag_mappings[category_match]}](around:{radius},{lat},{lon});"
            if stmt not in seen_statements:
                seen_statements.add(stmt)
                statements.append(stmt)
    
    if len(statements) < 3:
        for term in terms:
            term_lower = term.lower()
            if term_lower in tag_mappings:
                stmt = f"nwr[{tag_mappings[term_lower]}](around:{radius},{lat},{lon});"
                if stmt not in seen_statements:
                    seen_statements.add(stmt)
                    statements.append(stmt)
            
            for key, tag in tag_mappings.items():
                if SequenceMatcher(None, term_lower, key).ratio() > 0.65:
                    stmt = f"nwr[{tag}](around:{radius},{lat},{lon});"
                    if stmt not in seen_statements:
                        seen_statements.add(stmt)
                        statements.append(stmt)
    
    if len(statements) < 3:
        for term in terms:
            if len(term) >= 3:
                escaped = re.escape(term)
                stmt = f'nwr[~"name"~"{escaped}",i](around:{radius},{lat},{lon});'
                if stmt not in seen_statements:
                    seen_statements.add(stmt)
                    statements.append(stmt)
    
    if not statements:
        for term in terms:
            if len(term) >= 3:
                escaped = re.escape(term)
                stmt = f'nwr[~".*"~"{escaped}",i](around:{radius},{lat},{lon});'
                if stmt not in seen_statements:
                    seen_statements.add(stmt)
                    statements.append(stmt)
    
    statements = statements[:25]
    
    ql = f'[out:json][timeout:90];(\n' + '\n'.join(statements) + '\n);out center;'
    
    add_api_log(f"Generated query with {len(statements)} statements", "INFO")
    if len(statements) > 0:
        add_api_log(f"First statement: {statements[0][:50]}", "INFO")
    
    return ql

def execute_overpass_query(ql, timeout=90):
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            add_api_log(f"Querying endpoint: {endpoint.split('/')[2]}", "INFO")
            res = requests.post(endpoint, data={"data": ql}, headers={"User-Agent": "OpenNode/3.0"}, timeout=timeout)
            if res.status_code == 200:
                return res.json().get("elements", [])
            elif res.status_code == 429:
                add_api_log("Endpoint throttled, backing off...", "WARNING")
                time.sleep(2)
        except Exception as e:
            add_api_log(f"Connection failure: {str(e)[:40]}", "ERROR")
            continue
    return []

def process_overpass_results(elements):
    records = []
    for idx, el in enumerate(elements):
        e_lat = el.get('lat') or el.get('center', {}).get('lat')
        e_lon = el.get('lon') or el.get('center', {}).get('lon')
        if e_lat and e_lon:
            tags = el.get('tags', {})
            name = tags.get('name') or tags.get('brand') or tags.get('operator')
            if not name or str(name).strip().lower() in ['unknown', '', 'none', 'nan']:
                poi_type = tags.get('amenity') or tags.get('shop') or tags.get('leisure') or 'POI Node'
                name = poi_type.replace('_', ' ').capitalize()
            poi_type = tags.get('amenity') or tags.get('shop') or tags.get('tourism') or tags.get('leisure') or 'Asset'
            records.append({
                "lat": e_lat, "lon": e_lon, "name": str(name)[:50],
                "type": str(poi_type).replace('_', ' ').capitalize(),
                "source": "overpass", "visible": True, "uid": idx
            })
    return records

# -----------------------------------------------------------------------------
# 6. STREAMLIT DYNAMIC INTERACTION INJECTION LAYER
# -----------------------------------------------------------------------------
# Inject HTML for floating UI
st.markdown("""
    <!-- Floating Controls -->
    <div class="floating-controls">
        <!-- Menu Button -->
        <button id="toggle-sidebar" onclick="toggleSidebar()">
            <span class="menu-icon">☰</span>
        </button>

        <!-- Search Container -->
        <div class="search-container">
            <div class="search-wrapper">
                <span class="search-icon">🔍</span>
                <input id="search-input" type="text" placeholder="Search establishments..." 
                       onkeydown="if(event.key==='Enter'){document.getElementById('search-btn').click()}">
            </div>
            <button id="search-btn">Search</button>
        </div>

        <!-- Edit Button -->
        <button id="toggle-styling" onclick="toggleStylingPanel()">
            <span class="edit-icon">⚙</span>
            <span>EDIT</span>
        </button>
    </div>

    <!-- Styling Panel -->
    <div id="styling-panel">
        <section>
            <h2>Pin Aesthetics</h2>
            <div style="margin-bottom: 12px;">
                <label>Marker Color</label>
                <div class="color-options">
                    <button class="active" style="background-color:#003366;" data-color="#003366" onclick="setMarkerColor('#003366', this)"></button>
                    <button style="background-color:#6b7280;" data-color="#6b7280" onclick="setMarkerColor('#6b7280', this)"></button>
                    <button style="background-color:#dc2626;" data-color="#dc2626" onclick="setMarkerColor('#dc2626', this)"></button>
                    <button style="background-color:#2563eb;" data-color="#2563eb" onclick="setMarkerColor('#2563eb', this)"></button>
                    <button style="background-color:#059669;" data-color="#059669" onclick="setMarkerColor('#059669', this)"></button>
                </div>
            </div>
            <div style="margin-bottom: 12px;">
                <label>Icon Type</label>
                <select id="marker-style-select" onchange="setMarkerStyle(this.value)">
                    <option value="pin">Standard Pin</option>
                    <option value="dot" selected>Circle Dot</option>
                    <option value="square">Square Box</option>
                    <option value="diamond">Diamond</option>
                </select>
            </div>
            <div class="toggle-row">
                <span>Show Labels</span>
                <input type="checkbox" id="labels-toggle" checked onchange="setLabels(this.checked)">
            </div>
        </section>

        <hr>

        <section>
            <h2>Base Map</h2>
            <div style="display:flex; flex-direction:column; gap:4px;">
                <label class="basemap-option">
                    <input type="radio" name="basemap" value="osm" checked onchange="setBasemap('osm')">
                    <span>OpenStreetMap</span>
                </label>
                <label class="basemap-option">
                    <input type="radio" name="basemap" value="carto" onchange="setBasemap('carto')">
                    <span>Carto Light</span>
                </label>
                <label class="basemap-option">
                    <input type="radio" name="basemap" value="satellite" onchange="setBasemap('satellite')">
                    <span>Satellite</span>
                </label>
            </div>
        </section>
    </div>

    <!-- Footer -->
    <footer class="map-footer" id="map-footer">
        <div class="footer-left">
            <span id="footer-lat">LAT: --</span>
            <span id="footer-lng">LNG: --</span>
            <span id="footer-zoom">ZOOM: --</span>
        </div>
        <div class="footer-right">
            API ENDPOINT: <span class="status" id="api-status">CONNECTED</span>
        </div>
    </footer>

    <!-- Sidebar -->
    <div id="sidebar" class="collapsed">
        <div class="brand-title">Open Node</div>
        
        <div class="sidebar-section">
            <div class="sidebar-section-title">Location</div>
            <input id="sidebar-coords" type="text" value="14.64650, 121.05804" 
                   style="width:100%; padding:6px 10px; border:1.5px solid #000; font-family:'JetBrains Mono',monospace; font-size:12px; border-radius:4px; margin-bottom:8px;">
            <input id="sidebar-radius" type="number" value="1000" min="100" max="50000" step="100"
                   style="width:100%; padding:6px 10px; border:1.5px solid #000; font-family:'Inter',sans-serif; font-size:12px; border-radius:4px;">
        </div>

        <div class="sidebar-section" style="flex:1; overflow-y:auto;">
            <div class="workspace-header">
                <span>Workspace Assets</span>
                <span class="count" id="asset-count">0</span>
            </div>
            <div id="workspace-content">
                <div class="workspace-empty">No active vectors inside workspace.<br>Execute spatial search profile.</div>
            </div>
        </div>

        <div class="sidebar-actions">
            <button class="btn-export" id="export-btn">Export</button>
            <button class="btn-clear" id="clear-btn">Clear</button>
        </div>

        <div class="log-section">
            <button class="log-toggle" id="log-toggle" onclick="toggleLogs()">▼ Pipeline Logs</button>
            <div class="log-content" id="log-content" style="display:none;">
                <div class="log-entry">Engine state clear.</div>
            </div>
        </div>
    </div>

    <script>
        // Sidebar toggle
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('collapsed');
            const hiddenInput = document.getElementById('sidebar_state_input');
            if (hiddenInput) {
                hiddenInput.value = sidebar.classList.contains('collapsed') ? 'collapsed' : 'expanded';
                hiddenInput.dispatchEvent(new Event('change'));
            }
        }

        // Styling panel toggle
        function toggleStylingPanel() {
            const panel = document.getElementById('styling-panel');
            panel.classList.toggle('open');
        }

        // Styling functions
        function setMarkerColor(color, btn) {
            document.querySelectorAll('.color-options button').forEach(b => b.classList.remove('active'));
            if (btn) btn.classList.add('active');
            const input = document.getElementById('marker_color_input');
            if (input) { input.value = color; input.dispatchEvent(new Event('change')); }
        }

        function setMarkerStyle(value) {
            const input = document.getElementById('marker_style_input');
            if (input) { input.value = value; input.dispatchEvent(new Event('change')); }
        }

        function setLabels(checked) {
            const input = document.getElementById('labels_input');
            if (input) { input.value = checked ? 'true' : 'false'; input.dispatchEvent(new Event('change')); }
        }

        function setBasemap(value) {
            const input = document.getElementById('basemap_input');
            if (input) { input.value = value; input.dispatchEvent(new Event('change')); }
        }

        function toggleLogs() {
            const content = document.getElementById('log-content');
            const toggle = document.getElementById('log-toggle');
            if (content.style.display === 'none') {
                content.style.display = 'block';
                toggle.textContent = '▲ Pipeline Logs';
            } else {
                content.style.display = 'none';
                toggle.textContent = '▼ Pipeline Logs';
            }
        }

        // Footer update function
        function updateFooter(lat, lng, zoom) {
            document.getElementById('footer-lat').textContent = 'LAT: ' + (lat ? lat.toFixed(5) : '--');
            document.getElementById('footer-lng').textContent = 'LNG: ' + (lng ? lng.toFixed(5) : '--');
            document.getElementById('footer-zoom').textContent = 'ZOOM: ' + (zoom || '--');
        }

        // Initial sidebar state
        document.addEventListener('DOMContentLoaded', function() {
            const sidebar = document.getElementById('sidebar');
            const hiddenInput = document.getElementById('sidebar_state_input');
            if (hiddenInput && hiddenInput.value === 'collapsed') {
                sidebar.classList.add('collapsed');
            }
        });

        // Close styling panel on outside click
        document.addEventListener('click', function(e) {
            const panel = document.getElementById('styling-panel');
            const btn = document.getElementById('toggle-styling');
            if (panel && !panel.contains(e.target) && !btn.contains(e.target)) {
                panel.classList.remove('open');
            }
        });
    </script>
""", unsafe_allow_html=True)

# Hidden inputs for Streamlit state - using st.text_input with labels
st.text_input("Sidebar State", key="sidebar_state_input", label_visibility="collapsed", placeholder="sidebar_state")
st.text_input("Marker Color", key="marker_color_input", label_visibility="collapsed", placeholder="marker_color")
st.text_input("Marker Style", key="marker_style_input", label_visibility="collapsed", placeholder="marker_style")
st.text_input("Labels", key="labels_input", label_visibility="collapsed", placeholder="labels")
st.text_input("Basemap", key="basemap_input", label_visibility="collapsed", placeholder="basemap")

# Update state from hidden inputs
if st.session_state.get('sidebar_state_input') == "collapsed":
    st.session_state.sidebar_collapsed = True
elif st.session_state.get('sidebar_state_input') == "expanded":
    st.session_state.sidebar_collapsed = False

if st.session_state.get('marker_color_input'):
    st.session_state.marker_color = st.session_state.marker_color_input

if st.session_state.get('marker_style_input'):
    st.session_state.marker_style = st.session_state.marker_style_input

if st.session_state.get('labels_input') == 'false':
    st.session_state.show_labels = False
elif st.session_state.get('labels_input') == 'true':
    st.session_state.show_labels = True

if st.session_state.get('basemap_input'):
    st.session_state.basemap_choice = st.session_state.basemap_input

# -----------------------------------------------------------------------------
# 7. HIGH-LEVEL CONFIGURATION (Hidden - controlled by UI)
# -----------------------------------------------------------------------------
# Get coords and radius from sidebar inputs via JavaScript will update these
coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", st.session_state.geo_coords)
lat_coord, lon_coord = (float(coord_match.group(1)), float(coord_match.group(2))) if coord_match else (14.64650, 121.05804)
radius_val = st.session_state.geo_radius

# Handle search from UI - using proper labels
search_query = st.text_input("Search", key="search_bar_input", label_visibility="collapsed", placeholder="Search establishments...", max_chars=SearchGuardrails.MAX_QUERY_LENGTH)
search_clicked = st.button("SEARCH", key="search_btn")

if search_clicked and search_query.strip():
    st.session_state.last_search_query = search_query
    is_valid, error_msg = SearchGuardrails.validate_query(search_query)
    if not is_valid:
        st.error(error_msg)
    else:
        is_allowed, rate_msg = SearchGuardrails.check_rate_limit()
        if not is_allowed:
            st.error(rate_msg)
        else:
            st.session_state.search_count += 1
            st.session_state.search_cooldown_until = time.time() + SearchGuardrails.COOLDOWN_SECONDS
            st.session_state.scan_active_loading = True
            st.rerun()

# Clear button handler
if st.button("✕", key="clear_search_btn"):
    st.session_state.search_bar_input = ""
    st.session_state.last_search_query = ""
    st.rerun()

# -----------------------------------------------------------------------------
# 8. PIPELINE RUNTIME EVALUATION LOOP
# -----------------------------------------------------------------------------
main_canvas = st.empty()

if st.session_state.scan_active_loading:
    main_canvas.markdown(f'''
        <div class="loading-overlay">
            <div class="spinner"></div>
            <div class="loading-text">Scanning Node Cluster</div>
            <div class="loading-sub">Radius: {radius_val}m | Profile: "{st.session_state.last_search_query[:25]}"</div>
        </div>
    ''', unsafe_allow_html=True)
    
    search_term = st.session_state.last_search_query or ""
    normalized = SearchGuardrails.normalize_query(search_term)
    sanitized = SearchGuardrails.sanitize_for_overpass(normalized)
    
    ql = build_overpass_query(lat_coord, lon_coord, radius_val, sanitized)
    elements = execute_overpass_query(ql)
    
    if elements:
        records = process_overpass_results(elements)
        if records:
            st.session_state.scanned_records = records
            st.session_state.last_scan_lat = lat_coord
            st.session_state.last_scan_lon = lon_coord
            
            unique_layers = list(set([r.get('type', 'Unclassified') for r in records]))
            palette = ["#003366", "#C9AB4C", "#1E40AF", "#B45309", "#0369A1", "#78350F", "#334155"]
            for idx, layer in enumerate(unique_layers):
                st.session_state.layer_meta[layer] = {
                    "color": palette[idx % len(palette)],
                    "style": st.session_state.marker_style,
                    "size": 12
                }
            add_api_log(f"Successfully integrated {len(records)} map records", "INFO")
        else:
            add_api_log("Zero valid POI records found after processing", "WARNING")
    else:
        add_api_log("No data returned from Overpass endpoints", "WARNING")
        
    st.session_state.scan_active_loading = False
    st.rerun()

# -----------------------------------------------------------------------------
# 9. ENGINE TEMPLATE COMPILER & RENDER
# -----------------------------------------------------------------------------
fallback_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", st.session_state.geo_coords)
render_lat, render_lon = (float(fallback_match.group(1)), float(fallback_match.group(2))) if fallback_match else (14.64650, 121.05804)

layer_meta_json = json.dumps(st.session_state.layer_meta)
geojson_str = json.dumps(st.session_state.scanned_records)
is_stale = "true" if (lat_coord != st.session_state.last_scan_lat or lon_coord != st.session_state.last_scan_lon) else "false"

# Use the marker_color from session state
marker_color = st.session_state.marker_color

leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@500;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; background: #ffffff; overflow: hidden; }
        #map { height: 100vh; width: 100vw; z-index: 1; }
        .poi-text-label { 
            background: #ffffff; 
            border: 1px solid #000000; 
            padding: 2px 6px; 
            font-family: 'Inter', sans-serif; 
            font-size: __LABEL_SIZE__px; 
            font-weight: 700; 
            white-space: nowrap; 
            box-shadow: 0 2px 6px rgba(0,0,0,0.15); 
            color: #000000;
            border-radius: 3px;
        }
        .hide-labels .poi-text-label { display: none !important; }
        .leaflet-control-zoom a { 
            background: #ffffff !important; 
            color: #000000 !important; 
            border: 1.5px solid #000000 !important;
            border-radius: 0 !important;
        }
        .leaflet-control-zoom a:hover { background: #f3f4f6 !important; }
        .leaflet-control-zoom { border-radius: 4px !important; overflow: hidden; }
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        const map = L.map('map', { zoomControl: false, attributionControl: false, preferCanvas: true }).setView([__LAT__, __LON__], 14);
        L.control.zoom({ position: 'topright' }).addTo(map);

        const basemaps = {
            osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }),
            satellite: L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', { maxZoom: 20 }),
            carto: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 })
        };
        basemaps["__BASEMAP_CHOICE__"].addTo(map);
        
        if (!__LABELS_ACTIVE__) { document.getElementById('map').classList.add('hide-labels'); }

        L.circle([__LAT__, __LON__], { 
            radius: __RADIUS__, 
            color: "#003366", 
            weight: 1.5, 
            fillColor: "#003366", 
            fillOpacity: 0.05,
            opacity: 0.3
        }).addTo(map);
        
        L.marker([__LAT__, __LON__], { 
            icon: L.divIcon({ 
                html: '<div style="background-color: #003366; color: #ffffff; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 10px; border: 2px solid #ffffff; box-shadow: 0 2px 8px rgba(0,0,0,0.3)">★</div>', 
                className: '', 
                iconSize: [20, 20], 
                iconAnchor: [10, 10] 
            }) 
        }).addTo(map);

        const generateMarker = (color, mode, size) => {
            const s = size || 12;
            if (mode === "pin") {
                return L.divIcon({ 
                    html: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${s*1.5}" height="${s*1.5}"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" fill="${color}" stroke="#ffffff" stroke-width="1.5"/></svg>`, 
                    className: '', 
                    iconSize: [s*1.5, s*1.5], 
                    iconAnchor: [s*0.75, s*1.5] 
                });
            } else if (mode === "square") {
                return L.divIcon({ 
                    html: `<div style="background-color: ${color}; width: ${s}px; height: ${s}px; border: 1.5px solid #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.25); transform: rotate(45deg);"></div>`, 
                    className: '', 
                    iconSize: [s, s], 
                    iconAnchor: [s/2, s/2] 
                });
            } else if (mode === "diamond") {
                return L.divIcon({ 
                    html: `<div style="background-color: ${color}; width: ${s}px; height: ${s}px; border: 1.5px solid #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.25); clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);"></div>`, 
                    className: '', 
                    iconSize: [s, s], 
                    iconAnchor: [s/2, s/2] 
                });
            }
            return L.divIcon({ 
                html: `<div style="background-color: ${color}; width: ${s}px; height: ${s}px; border-radius: 50%; border: 1.5px solid #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.25);"></div>`, 
                className: '', 
                iconSize: [s, s], 
                iconAnchor: [s/2, s/2] 
            });
        };

        const pts = __GEOJSON__;
        const layerMeta = __LAYER_META_JSON__;
        let markers = [];
        
        pts.forEach(p => {
            const meta = layerMeta[p.type] || { color: "__MARKER_COLOR__", style: "__MARKER_STYLE__", size: 12 };
            const m = L.marker([p.lat, p.lon], { icon: generateMarker(meta.color, meta.style, meta.size) });
            m.bindPopup(`<b>${p.name}</b><br><span style="font-size:10px; color:#6b7280;">${p.type}</span>`);
            if (p.name) {
                m.bindTooltip(p.name, { permanent: true, direction: 'top', offset: [0, -6], className: 'poi-text-label' });
            }
            m.addTo(map);
            markers.push(m);
        });

        // Update footer with map info
        function updateFooter() {
            const center = map.getCenter();
            const zoom = map.getZoom();
            if (window.parent && window.parent.updateFooter) {
                window.parent.updateFooter(center.lat, center.lng, zoom);
            }
        }
        map.on('moveend', updateFooter);
        map.on('zoomend', updateFooter);
        setTimeout(updateFooter, 500);

        // Fit bounds if there are points
        if (pts.length > 0 && !__IS_STALE__) {
            const group = L.featureGroup([L.marker([__LAT__, __LON__]), ...pts.map(p => L.marker([p.lat, p.lon]))]);
            map.fitBounds(group.getBounds().pad(0.05));
        }
    </script>
</body>
</html>
"""

leaflet_html = (leaflet_template
                .replace("__LAT__", str(render_lat))
                .replace("__LON__", str(render_lon))
                .replace("__RADIUS__", str(radius_val))
                .replace("__IS_STALE__", is_stale)
                .replace("__GEOJSON__", geojson_str)
                .replace("__LAYER_META_JSON__", layer_meta_json)
                .replace("__BASEMAP_CHOICE__", st.session_state.basemap_choice)
                .replace("__LABELS_ACTIVE__", "true" if st.session_state.show_labels else "false")
                .replace("__LABEL_SIZE__", str(st.session_state.label_size))
                .replace("__MARKER_STYLE__", st.session_state.marker_style)
                .replace("__MARKER_COLOR__", marker_color))

# Use st.iframe instead of st.components.v1.html (deprecated) - removed scrolling parameter
st.iframe(leaflet_html, height=900)

# Update sidebar via Streamlit (workspace content)
# This runs after the HTML is rendered
if st.session_state.scanned_records:
    grouped = {}
    for record in st.session_state.scanned_records:
        rec_type = record.get('type', 'Unclassified')
        if rec_type not in grouped: grouped[rec_type] = []
        grouped[rec_type].append(record)
    
    workspace_html = ""
    for rec_type, items in grouped.items():
        if rec_type not in st.session_state.layer_meta:
            st.session_state.layer_meta[rec_type] = {"color": marker_color, "style": st.session_state.marker_style, "size": 12}
        current_color = st.session_state.layer_meta[rec_type].get('color', marker_color)
        
        workspace_html += f'''
            <div class="workspace-layer">
                <div class="workspace-layer-header">
                    <span class="color-dot" style="background-color:{current_color};"></span>
                    <span>{rec_type}</span>
                    <span class="layer-count">({len(items)})</span>
                </div>
        '''
        for item in items[:12]:
            name = item.get('name', 'Unknown Target')[:26]
            workspace_html += f'''
                <div class="workspace-item">
                    <span class="item-name">{name}</span>
                    <span class="item-type">{item.get('type', '')[:12]}</span>
                </div>
            '''
        if len(items) > 12:
            workspace_html += f'<div style="font-size:9px; color:#6b7280; padding:4px 12px;">+ {len(items) - 12} more</div>'
        workspace_html += '</div>'
    
    # Update workspace content via JavaScript
    st.markdown(f"""
        <script>
            const workspaceContent = document.getElementById('workspace-content');
            if (workspaceContent) {{
                workspaceContent.innerHTML = `{workspace_html}`;
            }}
            const assetCount = document.getElementById('asset-count');
            if (assetCount) {{
                assetCount.textContent = '{len(st.session_state.scanned_records)}';
            }}
        </script>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <script>
            const workspaceContent = document.getElementById('workspace-content');
            if (workspaceContent) {
                workspaceContent.innerHTML = `<div class="workspace-empty">No active vectors inside workspace.<br>Execute spatial search profile.</div>`;
            }
            const assetCount = document.getElementById('asset-count');
            if (assetCount) {
                assetCount.textContent = '0';
            }
        </script>
    """, unsafe_allow_html=True)

# Update logs
if st.session_state.api_logs:
    log_entries_html = "".join([f'<div class="log-entry"><span class="log-time">[{l["time"]}]</span> <span class="log-{l["level"].lower()}">{l["message"]}</span></div>' for l in st.session_state.api_logs[-15:]])
    st.markdown(f"""
        <script>
            const logContent = document.getElementById('log-content');
            if (logContent) {{
                logContent.innerHTML = `{log_entries_html}`;
            }}
        </script>
    """, unsafe_allow_html=True)

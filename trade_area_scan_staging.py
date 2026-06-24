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
            --soft-shadow: 0 4px 20px rgba(0, 51, 102, 0.12) !important;
        }
        
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
            background-color: var(--white-clean) !important;
            color: var(--brand-midnight) !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        
        /* FLOATING SIDEBAR ENGINE */
        [data-testid="stSidebar"] {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100vh !important;
            background-color: rgba(248, 250, 252, 0.95) !important;
            backdrop-filter: blur(12px) !important;
            color: var(--brand-midnight) !important;
            border-right: 1px solid rgba(0, 51, 102, 0.08) !important;
            width: 320px !important;
            min-width: 320px !important;
            max-width: 320px !important;
            transform: none !important;
            visibility: visible !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            box-shadow: 4px 0 25px rgba(0, 31, 63, 0.08) !important;
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            z-index: 99999 !important;
            display: flex !important;
            flex-direction: column !important;
        }
        
        /* Sidebar collapsed state via dynamic classes */
        .sidebar-collapsed [data-testid="stSidebar"] {
            transform: translateX(-320px) !important;
        }
        
        /* MAIN CANVAS OVERLAY COMPLIANCE */
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
        
        /* FLOATING SIDEBAR TOGGLE MECHANICS - FIXED POSITIONING */
        .sidebar-toggle-btn {
            position: fixed;
            left: 16px;
            top: 24px;
            z-index: 999999;
            background: var(--brand-midnight);
            color: #ffffff;
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 4px;
            padding: 8px 14px;
            font-family: 'Montserrat', sans-serif;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: all 0.2s ease;
            pointer-events: auto;
        }
        .sidebar-toggle-btn:hover {
            background: var(--brand-gold);
            transform: scale(1.03);
        }
        
        /* When sidebar is collapsed, move button to visible position */
        .sidebar-collapsed .sidebar-toggle-btn {
            left: 16px !important;
            background: var(--brand-midnight);
        }
        
        /* Hide default elements */
        [data-testid="stSidebarCollapseButton"], 
        [data-testid="collapsedControl"],
        .st-emotion-cache-1cypcdb,
        .st-emotion-cache-6qob1r,
        [data-testid="stHeader"], header, #stDecoration { 
            display: none !important; 
        }
        
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-thumb { background: rgba(0, 51, 102, 0.15); border-radius: 2px; }
        * { scrollbar-width: thin !important; }
        
        p, label, h1, h2, h3, h4, h5, h6, .stMarkdown, [data-testid="stExpander"] summary p {
            color: var(--brand-midnight) !important;
            font-family: 'Montserrat', sans-serif !important;
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
            border-radius: 4px !important; 
            width: 100% !important; 
            padding: 6px !important; 
            box-shadow: var(--soft-shadow) !important; 
        }
        div.stButton > button[kind="secondary"]:hover, [data-testid="stPopover"] > button:hover { 
            background-color: var(--brand-gold) !important; 
            border-color: var(--brand-gold) !important; 
        }
        div.stButton > button[kind="secondary"] p, [data-testid="stPopover"] > button p, [data-testid="stPopover"] > button div, div.stDownloadButton > button p { 
            color: var(--white-clean) !important; 
            font-weight: 700 !important; 
            font-size: 10px !important; 
            text-transform: uppercase !important; 
            letter-spacing: 0.5px; 
        }
        
        div.stDownloadButton > button { 
            background-color: var(--brand-midnight) !important; 
            border: none !important; 
            border-radius: 4px !important; 
            width: 100% !important; 
            padding: 6px !important; 
        }
        div.stDownloadButton > button:hover { background-color: var(--brand-gold) !important; }
        
        div.stButton > button[kind="primary"] { 
            background: transparent !important; 
            border: 1px solid rgba(170, 46, 32, 0.2) !important; 
            color: #AA2E20 !important; 
            padding: 4px !important; 
            border-radius: 4px;
        }
        div.stButton > button[kind="primary"]:hover {
            background: rgba(170, 46, 32, 0.05) !important;
        }
        div.stButton > button[kind="primary"] p { 
            color: #AA2E20 !important; 
            font-size: 10px !important; 
            font-weight: 600; 
            text-transform: uppercase; 
        }
        
        [data-testid="stSidebar"] .st-expander { 
            border: 1px solid rgba(0, 51, 102, 0.08) !important; 
            background-color: var(--white-clean) !important; 
            border-radius: 6px !important; 
            margin-bottom: 8px !important; 
            box-shadow: 0 2px 6px rgba(0,0,0,0.01) !important;
        }
        
        .brand-title { 
            font-family: 'Cormorant Garamond', serif !important; 
            font-style: italic; 
            color: var(--brand-midnight); 
            font-size: 32px; 
            text-align: center; 
            border-bottom: 1px solid var(--brand-gold); 
            padding-bottom: 8px; 
            margin-bottom: 16px; 
            margin-top: 48px;
        }
        .stTextInput label p, .stNumberInput label p, .stSelectbox label p { 
            font-size: 10px !important; 
            font-weight: 600 !important; 
            color: var(--brand-midnight) !important; 
            letter-spacing: 0.3px;
        }

        /* WORKSPACE MODERN ARCHITECTURE */
        .workspace-section {
            margin-top: 14px;
            border-top: 1px solid rgba(0, 51, 102, 0.08);
            padding-top: 12px;
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        .workspace-header {
            font-size: 11px;
            font-weight: 700;
            color: #003366;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .workspace-count {
            background: rgba(0, 51, 102, 0.08);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 9px;
            font-weight: 700;
        }
        .workspace-layer {
            margin-bottom: 8px;
            background: #ffffff;
            border: 1px solid rgba(0, 51, 102, 0.04);
            border-radius: 4px;
            padding: 4px;
        }
        .workspace-layer-header {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            font-weight: 700;
            color: #003366;
            padding: 4px 2px;
            border-bottom: 1px solid rgba(0, 51, 102, 0.03);
        }
        .workspace-item {
            font-size: 11px;
            padding: 5px 6px 5px 14px;
            border-bottom: 1px solid rgba(0, 51, 102, 0.02);
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #475569;
        }
        .workspace-item:hover {
            background: rgba(0, 51, 102, 0.02);
            color: #003366;
        }
        .workspace-item-name {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 170px;
        }
        .workspace-item-type {
            font-size: 9px;
            color: #64748b;
            background: #f1f5f9;
            padding: 1px 6px;
            border-radius: 4px;
        }
        .color-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            border: 1px solid rgba(0,0,0,0.08);
            flex-shrink: 0;
        }
        .workspace-empty {
            font-size: 11px;
            color: var(--text-muted);
            padding: 24px 8px;
            text-align: center;
            border: 1px dashed rgba(0, 51, 102, 0.1);
            border-radius: 6px;
        }

        /* LOADING SPINNER OVERLAYS */
        .py-loading-container {
            position: absolute; top: 40%; left: 50%; transform: translate(-50%, -50%);
            width: 340px; background: #ffffff; padding: 24px; border-radius: 6px;
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
        
        /* TIMEOUT HINT HUD PANEL OVERLAY */
        .api-log-container {
            position: absolute; bottom: 24px; right: 24px; width: 340px; max-height: 220px;
            background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(8px); border-radius: 6px;
            border-left: 3px solid #C9AB4C; z-index: 10000; font-family: monospace;
            font-size: 10px; display: flex; flex-direction: column; box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            transition: all 0.2s ease; color: #e2e8f0;
        }
        .api-log-header {
            padding: 6px 12px; background: rgba(0,0,0,0.2); border-radius: 6px 6px 0 0;
            font-weight: 700; font-size: 9px; letter-spacing: 0.5px; text-transform: uppercase;
            display: flex; justify-content: space-between; align-items: center; cursor: pointer;
            color: #C9AB4C; border-bottom: 1px solid rgba(201, 171, 76, 0.15);
        }
        .api-log-content { overflow-y: auto; padding: 6px 12px; flex-grow: 1; max-height: 170px; }
        .api-log-entry { border-bottom: 1px solid rgba(255,255,255,0.05); padding: 4px 0; font-size: 9px; }
        .api-log-time { color: #C9AB4C; font-weight: 600; margin-right: 6px; }
        .api-log-info { color: #34d399; }
        .api-log-error { color: #f87171; }
        .api-log-warning { color: #fb923c; }
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
# 4. SEARCH PROTECTION GUARDRAILS - IMPROVED FUZZY SEARCH
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
    
    # EXPANDED BRAND VARIATIONS WITH PRIORITY
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
    
    # CATEGORY MAPPINGS WITH WEIGHTS
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
        """Get brand variations with exact matching priority"""
        query_lower = query.lower().strip()
        variations = []
        
        # Check exact brand matches first (highest priority)
        for brand, variants in cls.BRAND_VARIATIONS.items():
            # Check if query exactly matches brand or any variant
            if query_lower == brand or query_lower in variants:
                variations = [brand] + variants
                break
        
        # If no exact match, check for partial matches
        if not variations:
            for brand, variants in cls.BRAND_VARIATIONS.items():
                for variant in variants:
                    if variant in query_lower or query_lower in variant:
                        variations = [brand] + variants
                        break
                if variations:
                    break
        
        # If still no variations, just use the original query
        if not variations:
            variations = [query_lower]
        
        return list(set(variations))
    
    @classmethod
    def get_category_match(cls, query):
        """Get category match from query with fuzzy matching"""
        query_lower = query.lower().strip()
        
        # Check exact category matches first
        for category, terms in cls.CATEGORY_MAPPINGS.items():
            if query_lower == category or query_lower in terms:
                return category
        
        # Check partial matches with SequenceMatcher
        best_match = None
        best_score = 0.0
        
        for category, terms in cls.CATEGORY_MAPPINGS.items():
            # Check against category name
            score = SequenceMatcher(None, query_lower, category).ratio()
            if score > best_score:
                best_score = score
                best_match = category
            
            # Check against terms
            for term in terms:
                score = SequenceMatcher(None, query_lower, term).ratio()
                if score > best_score:
                    best_score = score
                    best_match = category
        
        # Return match if score is above threshold
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
# 5. OVERPASS QUERY PIPELINE MODULE - IMPROVED
# -----------------------------------------------------------------------------
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

def build_overpass_query(lat, lon, radius, search_terms):
    """Build Overpass QL with improved brand and category matching"""
    add_api_log(f"Building query for: '{search_terms}'", "INFO")
    
    # Get brand variations (high priority)
    brand_variations = SearchGuardrails.get_brand_variations(search_terms)
    add_api_log(f"Brand variations: {brand_variations}", "INFO")
    
    # Get category match
    category_match = SearchGuardrails.get_category_match(search_terms)
    if category_match:
        add_api_log(f"Category match: {category_match}", "INFO")
    
    terms = search_terms.lower().split()
    statements = []
    seen_statements = set()
    
    # TAG MAPPINGS FOR CATEGORIES
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
    
    # 1. BRAND SEARCH (Highest Priority)
    # Search for brand tags with exact and partial matching
    for variation in brand_variations:
        if len(variation) >= 2:
            escaped = re.escape(variation)
            # Brand tag (primary)
            stmt = f'nwr[~"brand"~"^{escaped}$",i](around:{radius},{lat},{lon});'
            if stmt not in seen_statements:
                seen_statements.add(stmt)
                statements.append(stmt)
            
            # Name tag with exact match
            stmt = f'nwr[~"name"~"^{escaped}$",i](around:{radius},{lat},{lon});'
            if stmt not in seen_statements:
                seen_statements.add(stmt)
                statements.append(stmt)
            
            # Name tag with partial match (for cases like "Jollibee Restaurant")
            stmt = f'nwr[~"name"~"{escaped}",i](around:{radius},{lat},{lon});'
            if stmt not in seen_statements:
                seen_statements.add(stmt)
                statements.append(stmt)
            
            # Operator tag
            stmt = f'nwr[~"operator"~"{escaped}",i](around:{radius},{lat},{lon});'
            if stmt not in seen_statements:
                seen_statements.add(stmt)
                statements.append(stmt)
    
    # 2. CATEGORY SEARCH (if no brand matches found or as fallback)
    if len(statements) < 2:
        if category_match and category_match in tag_mappings:
            stmt = f"nwr[{tag_mappings[category_match]}](around:{radius},{lat},{lon});"
            if stmt not in seen_statements:
                seen_statements.add(stmt)
                statements.append(stmt)
    
    # 3. FUZZY TAG MATCHING
    if len(statements) < 3:
        for term in terms:
            term_lower = term.lower()
            # Check exact tag mappings
            if term_lower in tag_mappings:
                stmt = f"nwr[{tag_mappings[term_lower]}](around:{radius},{lat},{lon});"
                if stmt not in seen_statements:
                    seen_statements.add(stmt)
                    statements.append(stmt)
            
            # Fuzzy match against tag keys
            for key, tag in tag_mappings.items():
                if SequenceMatcher(None, term_lower, key).ratio() > 0.65:
                    stmt = f"nwr[{tag}](around:{radius},{lat},{lon});"
                    if stmt not in seen_statements:
                        seen_statements.add(stmt)
                        statements.append(stmt)
    
    # 4. NAME SEARCH FALLBACK
    if len(statements) < 3:
        for term in terms:
            if len(term) >= 3:
                escaped = re.escape(term)
                stmt = f'nwr[~"name"~"{escaped}",i](around:{radius},{lat},{lon});'
                if stmt not in seen_statements:
                    seen_statements.add(stmt)
                    statements.append(stmt)
    
    # 5. GENERIC FALLBACK (only if absolutely no statements)
    if not statements:
        for term in terms:
            if len(term) >= 3:
                escaped = re.escape(term)
                stmt = f'nwr[~".*"~"{escaped}",i](around:{radius},{lat},{lon});'
                if stmt not in seen_statements:
                    seen_statements.add(stmt)
                    statements.append(stmt)
    
    # Limit to 25 statements
    statements = statements[:25]
    
    ql = f'[out:json][timeout:90];(\n' + '\n'.join(statements) + '\n);out center;'
    
    # Log the query for debugging
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
# 6. STREAMLIT DYNAMIC INTERACTION INJECTION LAYER - FIXED
# -----------------------------------------------------------------------------
st.markdown("""
    <button class="sidebar-toggle-btn" id="sidebarToggleBtn" onclick="toggleSidebarDynamic()">CLOSE PANEL</button>
    <script>
        function toggleSidebarDynamic() {
            const container = document.querySelector('[data-testid="stAppViewContainer"]');
            const btn = document.getElementById('sidebarToggleBtn');
            container.classList.toggle('sidebar-collapsed');
            
            const isCollapsed = container.classList.contains('sidebar-collapsed');
            btn.textContent = isCollapsed ? 'OPEN PANEL' : 'CLOSE PANEL';
            
            // Send state to Streamlit
            const hiddenInput = document.getElementById('sidebar_state_input');
            if (hiddenInput) {
                hiddenInput.value = isCollapsed ? 'collapsed' : 'expanded';
                hiddenInput.dispatchEvent(new Event('change'));
            }
        }
        
        // Initialize button text based on current state
        document.addEventListener('DOMContentLoaded', function() {
            const container = document.querySelector('[data-testid="stAppViewContainer"]');
            const btn = document.getElementById('sidebarToggleBtn');
            if (container && btn) {
                const isCollapsed = container.classList.contains('sidebar-collapsed');
                btn.textContent = isCollapsed ? 'OPEN PANEL' : 'CLOSE PANEL';
            }
        });
    </script>
""", unsafe_allow_html=True)

sidebar_state = st.text_input("", key="sidebar_state_input", label_visibility="collapsed", placeholder="sidebar_state")
if sidebar_state == "collapsed":
    st.session_state.sidebar_collapsed = True
elif sidebar_state == "expanded":
    st.session_state.sidebar_collapsed = False

# Apply collapsed state with JavaScript
if st.session_state.sidebar_collapsed:
    st.markdown("""
        <script>
            (function() {
                const container = document.querySelector('[data-testid="stAppViewContainer"]');
                const btn = document.getElementById('sidebarToggleBtn');
                if (container && !container.classList.contains('sidebar-collapsed')) {
                    container.classList.add('sidebar-collapsed');
                }
                if (btn) {
                    btn.textContent = 'OPEN PANEL';
                }
            })();
        </script>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 7. HIGH-LEVEL CONFIGURATION DRAWER
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="brand-title">Open Node</div>', unsafe_allow_html=True)
    
    # SEARCH ENGINE COMPONENT BLOCK
    st.markdown("<div style='font-size: 10px; font-weight: 700; color: #003366; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;'>Discovery Engine</div>", unsafe_allow_html=True)
    search_query = st.text_input("", placeholder="e.g., jollibee, veterinary, 7-eleven", key="search_bar_input", label_visibility="collapsed", max_chars=SearchGuardrails.MAX_QUERY_LENGTH)
    
    col_search, col_clear = st.columns([3, 1])
    with col_search:
        search_clicked = st.button("SEARCH", use_container_width=True, type="secondary", key="search_btn")
    with col_clear:
        if st.button("X", use_container_width=True, key="clear_search_btn"):
            st.session_state.search_bar_input = ""
            st.session_state.last_search_query = ""
            st.rerun()
            
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

    # LOCATION BOUNDARY PARAMETERS
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
        lat_coord, lon_coord = (float(fallback_match.group(1)), float(fallback_match.group(2))) if fallback_match else (14.64650, 121.05804)

    # REPOSITIONED BASEMAP & CANVAS CONTROLLER LAYOUT MODULE
    with st.expander("BASEMAP CONTROLS", expanded=True):
        basemap_choice = st.selectbox("ACTIVE BASEMAP", ["osm", "satellite", "carto"], index=0, key="persistent_basemap")
        show_labels = st.checkbox("Enable Overlay Typography", value=True, key="persistent_labels")
        label_size = st.slider("Typography Size Bounds", min_value=6, max_value=20, value=10, key="label_size")
        
        st.markdown("<hr style='margin: 8px 0; border:0; border-top:1px solid rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
        marker_style = st.selectbox("MARKER ICON DESIGN", ["dots", "pin", "modern-pin"], key="global_marker_style")
        marker_color = st.color_picker("MARKER PRIMARY HEX", "#003366", key="global_marker_color")

    # WORKSPACE MODULE
    st.markdown(f"""
        <div class="workspace-section">
            <div class="workspace-header">
                <span>Workspace Assets</span>
                <span class="workspace-count">{len(st.session_state.scanned_records)}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.scanned_records:
        grouped = {}
        for record in st.session_state.scanned_records:
            rec_type = record.get('type', 'Unclassified')
            if rec_type not in grouped: grouped[rec_type] = []
            grouped[rec_type].append(record)
            
        for rec_type, items in grouped.items():
            if rec_type not in st.session_state.layer_meta:
                st.session_state.layer_meta[rec_type] = {"color": marker_color, "style": marker_style, "size": 12}
            current_layer_color = st.session_state.layer_meta[rec_type].get('color', marker_color)
            
            st.markdown(f"""
                <div class="workspace-layer">
                    <div class="workspace-layer-header">
                        <span class="color-dot" style="background-color:{current_layer_color};"></span>
                        <span>{rec_type}</span>
                        <span style='font-weight:500; color:#64748b; font-size:10px; margin-left:auto;'>({len(items)})</span>
                    </div>
            """, unsafe_allow_html=True)
            
            for item in items[:12]:
                name = item.get('name', 'Unknown Target')[:26]
                st.markdown(f"""
                    <div class="workspace-item">
                        <span class="workspace-item-name">{name}</span>
                        <span class="workspace-item-type">{item.get('type', '')[:12]}</span>
                    </div>
                """, unsafe_allow_html=True)
            if len(items) > 12:
                st.markdown(f"<div style='font-size:9px; color:#888780; padding:4px 14px;'>+ {len(items) - 12} additional features</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="workspace-empty">No active vectors inside workspace.<br>Execute spatial search profile.</div>', unsafe_allow_html=True)

    # PERSISTENT STORAGE EXPORT INTERFACE
    st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.08);'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("EXPORT", json.dumps([p for p in st.session_state.scanned_records]), "spatial_scan.json", "application/json", use_container_width=True)
    with col2:
        if st.button("CLEAR", type="primary", use_container_width=True):
            st.session_state.scanned_records = []
            st.session_state.layer_meta = {}
            st.session_state.scan_active_loading = False
            clear_api_logs()
            st.rerun()
            
    with st.expander("PIPELINE LOGS", expanded=False):
        if st.session_state.api_logs:
            log_text = "".join([f"[{l['level']}] [{l['time']}] {l['message']}\n" for l in st.session_state.api_logs[-15:]])
            st.code(log_text, language="text")
        else:
            st.caption("Pipeline diagnostics clear.")

# -----------------------------------------------------------------------------
# 8. PIPELINE RUNTIME EVALUATION LOOP
# -----------------------------------------------------------------------------
main_canvas = st.empty()

if st.session_state.scan_active_loading:
    main_canvas.markdown(f'''
        <div class="py-loading-container">
            <div class="py-spinner"></div>
            <div class="py-loading-title">Scanning Node Cluster</div>
            <div class="py-loading-subtitle">Radius: {radius_val}m | Profile: "{st.session_state.last_search_query[:25]}"</div>
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
                    "style": marker_style,
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
# Fix: Define render_lat and render_lon before using them
fallback_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", st.session_state.geo_coords)
render_lat, render_lon = (float(fallback_match.group(1)), float(fallback_match.group(2))) if fallback_match else (14.64650, 121.05804)

layer_meta_json = json.dumps(st.session_state.layer_meta)
geojson_str = json.dumps(st.session_state.scanned_records)
is_stale = "true" if (lat_coord != st.session_state.last_scan_lat or lon_coord != st.session_state.last_scan_lon) else "false"

api_logs_html = "".join([f'<div class="api-log-entry"><span class="api-log-time">[{l["time"]}]</span> <span class="api-log-{l["level"].lower()}">{l["message"]}</span></div>' for l in st.session_state.api_logs[-10:]])
api_log_panel = f'''
<div class="api-log-container" id="apiLogPanel">
    <div class="api-log-header" onclick="document.getElementById('apiLogContent').style.display = document.getElementById('apiLogContent').style.display === 'none' ? 'block' : 'none'">
        <span>Diagnostics Payload</span>
    </div>
    <div class="api-log-content" id="apiLogContent">{api_logs_html if api_logs_html else '<div class="api-log-entry">Engine state clear.</div>'}</div>
</div>
'''

leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link href="https://fonts.googleapis.com/css2 family=Montserrat:wght@500;700&display=swap" rel="stylesheet">
    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; background: #ffffff; overflow: hidden; }
        #map { height: 100vh; width: 100vw; z-index: 1; }
        .poi-text-label { background: #ffffff; border: 1px solid #003366; padding: 2px 4px; border-radius: 3px; font-size: __LABEL_SIZE__px; font-family: 'Montserrat', sans-serif; font-weight: 700; white-space: nowrap; box-shadow: 0 2px 6px rgba(0,0,0,0.15); color: #003366; }
        .hide-labels .poi-text-label { display: none !important; }
    </style>
</head>
<body>
    <div id="map"></div>
    __API_LOG_PANEL__
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

        L.circle([__LAT__, __LON__], { radius: __RADIUS__, color: "#003366", weight: 1.5, fillColor: "#003366", fillOpacity: 0.05 }).addTo(map);
        L.marker([__LAT__, __LON__], { icon: L.divIcon({ html: '<div style="background-color: #003366; color: #ffffff; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; border: 2px solid #ffffff; box-shadow: 0 2px 8px rgba(0,0,0,0.3)">★</div>', className: '', iconSize: [24, 24], iconAnchor: [12, 12] }) }).addTo(map);

        const generateMarker = (color, mode, size) => {
            if (mode === "pin" || mode === "modern-pin") {
                return L.divIcon({ html: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${size*1.5}" height="${size*1.5}"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" fill="${color}" stroke="#ffffff" stroke-width="1.5"/></svg>`, className: '', iconSize: [size*1.5, size*1.5], iconAnchor: [size*0.75, size*1.5] });
            }
            return L.divIcon({ html: `<div style="background-color: ${color}; width: ${size}px; height: ${size}px; border-radius: 50%; border: 1.5px solid #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.25);"></div>`, className: '', iconSize: [size, size], iconAnchor: [size/2, size/2] });
        };

        const pts = __GEOJSON__;
        const layerMeta = __LAYER_META_JSON__;
        
        pts.forEach(p => {
            const meta = layerMeta[p.type] || { color: "__MARKER_COLOR__", style: "__MARKER_STYLE__", size: 12 };
            const m = L.marker([p.lat, p.lon], { icon: generateMarker(meta.color, meta.style, meta.size) }).bindPopup(`<b>${p.name}</b><br><span style="font-size:10px; color:#64748b;">${p.type}</span>`);
            if (p.name) m.bindTooltip(p.name, { permanent: true, direction: 'top', offset: [0, -6], className: 'poi-text-label' });
            m.addTo(map);
        });

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
                .replace("__BASEMAP_CHOICE__", basemap_choice)
                .replace("__LABELS_ACTIVE__", "true" if show_labels else "false")
                .replace("__LABEL_SIZE__", str(label_size))
                .replace("__MARKER_STYLE__", marker_style)
                .replace("__MARKER_COLOR__", marker_color)
                .replace("__API_LOG_PANEL__", api_log_panel))

st.components.v1.html(leaflet_html, height=900, scrolling=False)

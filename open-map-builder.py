"""
Fullscreen Streamlit map with a slim left icon toolbar (geojson.io style).
Install: pip install streamlit folium streamlit-folium
Run:     streamlit run app.py
"""
import logging

import folium
import streamlit as st
from streamlit_folium import st_folium

log = logging.getLogger("map-console")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

st.set_page_config(page_title="Map Console", layout="wide", initial_sidebar_state="expanded")

# ---------------------------------------------------------------------------
# CONFIG (data-driven: extend by appending entries)
# ---------------------------------------------------------------------------
BASEMAPS = {
    "CARTO Dark": {"url": "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
                   "attr": "© OpenStreetMap contributors © CARTO", "subdomains": "abcd"},
    "CARTO Light": {"url": "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
                    "attr": "© OpenStreetMap contributors © CARTO", "subdomains": "abcd"},
    "OSM Standard": {"url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                     "attr": "© OpenStreetMap contributors"},
    "Esri Satellite": {"url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                       "attr": "© Esri, Maxar, Earthstar Geographics"},
    "OpenTopoMap": {"url": "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
                    "attr": "© OpenTopoMap (CC-BY-SA)", "subdomains": "abc"},
}

THEMES = {
    "CARRARA":      {"filter": "grayscale(1) contrast(1.1) brightness(0.92)", "bg": "#101112",
                     "swatches": ["#1e1e1e", "#f5f5f5", "#232323", "#2b2b2b", "#3d3d3d"]},
    "SANDSTONE":    {"filter": "sepia(0.7) saturate(1.3) contrast(0.95) brightness(0.9)", "bg": "#221a10",
                     "swatches": ["#4b3a26", "#ded8cf", "#55432c", "#4a3a26", "#5c4c36"]},
    "MIDNIGHT BLUE":{"filter": "saturate(1.4) hue-rotate(180deg) brightness(0.75) contrast(1.1)", "bg": "#0d1626",
                     "swatches": ["#b3994d", "#0e1726", "#a78a3e", "#7d5f20", "#262b2e"]},
    "CONTRAST":     {"filter": "grayscale(1) contrast(1.9) brightness(0.85)", "bg": "#000000",
                     "swatches": ["#101010", "#f7f7f7", "#171717", "#262626", "#4c4c4c"]},
    "ORIGINAL":     {"filter": "none", "bg": "#0b0e12",
                     "swatches": ["#243447", "#8fb6d9", "#1a2430", "#2e4054", "#405a72"]},
}

DEFAULT_CENTER, DEFAULT_ZOOM = (14.6, 121.0), 10  # Manila, matches reference shot

# ---------------------------------------------------------------------------
# STATE
# ---------------------------------------------------------------------------
ss = st.session_state
ss.setdefault("zoom", DEFAULT_ZOOM)
ss.setdefault("lat", DEFAULT_CENTER[0])
ss.setdefault("lon", DEFAULT_CENTER[1])
ss.setdefault("panel", None)          # None | "basemap" | "theme"
ss.setdefault("basemap", "OSM Standard")
ss.setdefault("theme", "ORIGINAL")

# ---------------------------------------------------------------------------
# CHROME CSS: hide Streamlit header, full-bleed map, sidebar -> icon rail
# ---------------------------------------------------------------------------
RAIL_W = "300px" if ss.panel else "52px"   # rail widens into a panel
st.markdown(f"""
<style>
#MainMenu, header[data-testid="stHeader"], footer {{visibility: hidden;}}
.main .block-container {{padding:0 !important; max-width:100%;}}
div[data-testid="stVerticalBlock"] {{gap:0 !important;}}
div[data-testid="stIFrame"], div[data-testid="stIFrame"] iframe {{height:100vh !important; width:100%; border:none;}}

/* --- left icon rail (white strip like reference) --- */
section[data-testid="stSidebar"] {{
    width:{RAIL_W} !important; min-width:{RAIL_W} !important;
    background:#fff !important; border-right:1px solid #d0d0d0;
}}
section[data-testid="stSidebar"] .block-container {{padding:6px 4px; gap:2px;}}
section[data-testid="stSidebar"] div[data-testid="stSidebarHeader"],
section[data-testid="stSidebar"] button[kind="headerNoBorder"] {{display:none;}}

/* icon buttons: square, borderless, hover grey */
section[data-testid="stSidebar"] div[data-testid="stButton"] button {{
    width:100%; min-height:0; padding:8px 0; border:none; border-radius:4px;
    background:transparent; color:#222; font-size:17px; line-height:1;
}}
section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {{background:#e8e8e8;}}
section[data-testid="stSidebar"] div[data-testid="stButton"] button p {{margin:0;}}
section[data-testid="stSidebar"] div[data-testid="stButton"] {{margin:0;}}

/* active tool highlight */
section[data-testid="stSidebar"] div[data-testid="stButton"] button[aria-pressed="true"] {{background:#dcdcdc;}}

/* panel widgets spacing when rail expanded */
section[data-testid="stSidebar"] label {{font-size:12px;}}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TOOLBAR (icon rail)
# ---------------------------------------------------------------------------
def tool(icon: str, tip: str, key: str) -> bool:
    return st.sidebar.button(icon, help=tip, key=key)

def toggle(panel: str):
    ss.panel = None if ss.panel == panel else panel

if tool("☰", "Basemap", "t_bm"):        toggle("basemap")
if tool("🎨", "Basemap colors", "t_th"): toggle("theme")
if tool("＋", "Zoom in",  "t_zi"):  ss.zoom = min(19, ss.zoom + 1)
if tool("－", "Zoom out", "t_zo"):  ss.zoom = max(1,  ss.zoom - 1)
if tool("⌂", "Reset view", "t_rs"):
    ss.zoom, ss.lat, ss.lon = DEFAULT_ZOOM, *DEFAULT_CENTER
if ss.panel and tool("✕", "Close panel", "t_cl"):
    ss.panel = None

# --- expandable panel content (only when rail is wide) ---
if ss.panel == "basemap":
    st.sidebar.selectbox("Basemap", list(BASEMAPS.keys()), key="basemap",
                         index=list(BASEMAPS.keys()).index(ss.basemap))
elif ss.panel == "theme":
    st.sidebar.radio("Basemap colors", list(THEMES.keys()), key="theme",
                     index=list(THEMES.keys()).index(ss.theme))
    cells = "".join(f'<div style="flex:1;height:20px;background:{c};"></div>'
                    for c in THEMES[ss.theme]["swatches"])
    st.sidebar.markdown(
        f'<div style="display:flex;border-radius:4px;overflow:hidden;">{cells}</div>',
        unsafe_allow_html=True)

theme = THEMES[ss.theme]

# ---------------------------------------------------------------------------
# MAP BUILD
# ---------------------------------------------------------------------------
def build_map(basemap_name: str, theme: dict, center: tuple, zoom: int) -> folium.Map:
    # zoom_control off: the rail owns zoom, like the reference UI
    m = folium.Map(location=center, zoom_start=zoom, prefer_canvas=True, zoom_control=False)
    cfg = BASEMAPS[basemap_name]
    folium.TileLayer(tiles=cfg["url"], attr=cfg["attr"],
                     subdomains=cfg.get("subdomains", "abc"),
                     max_zoom=19, name=basemap_name).add_to(m)
    # Theme = CSS filter on the tile PANE (not per-tile) -> no seam artifacts
    css = ("<style>"
           "html,body,.leaflet-container{background:" + theme["bg"] + " !important;}"
           ".leaflet-tile-pane{filter:" + theme["filter"] + ";}"
           "</style>")
    m.get_root().html.add_child(folium.Element(css))
    return m

# ---------------------------------------------------------------------------
# RENDER
# ---------------------------------------------------------------------------
try:
    fmap = build_map(ss.basemap, theme, (ss.lat, ss.lon), ss.zoom)
    st_folium(fmap, use_container_width=True, height=900, returned_objects=[])
    log.info("rendered basemap=%s theme=%s zoom=%s", ss.basemap, ss.theme, ss.zoom)
except Exception as exc:
    log.exception("Map render failed")
    st.error(f"Map render failed: {exc}")

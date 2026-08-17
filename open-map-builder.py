"""
Fullscreen Streamlit map, slim left icon toolbar (geojson.io style).
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
# CONFIG
# ---------------------------------------------------------------------------
BASEMAPS = {
    "OSM Standard": {"url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                     "attr": "© OpenStreetMap contributors"},
    "CARTO Dark": {"url": "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
                   "attr": "© OpenStreetMap contributors © CARTO", "subdomains": "abcd"},
    "CARTO Light": {"url": "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
                    "attr": "© OpenStreetMap contributors © CARTO", "subdomains": "abcd"},
    "Esri Satellite": {"url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                       "attr": "© Esri, Maxar, Earthstar Geographics"},
    "OpenTopoMap": {"url": "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
                    "attr": "© OpenTopoMap (CC-BY-SA)", "subdomains": "abc"},
}

THEMES = {
    "ORIGINAL":      {"filter": "none", "bg": "#ffffff",
                      "swatches": ["#243447", "#8fb6d9", "#1a2430", "#2e4054", "#405a72"]},
    "CARRARA":       {"filter": "grayscale(1) contrast(1.1) brightness(0.92)", "bg": "#101112",
                      "swatches": ["#1e1e1e", "#f5f5f5", "#232323", "#2b2b2b", "#3d3d3d"]},
    "SANDSTONE":     {"filter": "sepia(0.7) saturate(1.3) contrast(0.95) brightness(0.9)", "bg": "#221a10",
                      "swatches": ["#4b3a26", "#ded8cf", "#55432c", "#4a3a26", "#5c4c36"]},
    "MIDNIGHT BLUE": {"filter": "saturate(1.4) hue-rotate(180deg) brightness(0.75) contrast(1.1)", "bg": "#0d1626",
                      "swatches": ["#b3994d", "#0e1726", "#a78a3e", "#7d5f20", "#262b2e"]},
    "CONTRAST":      {"filter": "grayscale(1) contrast(1.9) brightness(0.85)", "bg": "#000000",
                      "swatches": ["#101010", "#f7f7f7", "#171717", "#262626", "#4c4c4c"]},
}

DEFAULT_CENTER, DEFAULT_ZOOM = (14.6, 121.0), 10

# ---------------------------------------------------------------------------
# STATE
# ---------------------------------------------------------------------------
ss = st.session_state
ss.setdefault("zoom", DEFAULT_ZOOM)
ss.setdefault("lat", DEFAULT_CENTER[0])
ss.setdefault("lon", DEFAULT_CENTER[1])
ss.setdefault("panel", None)            # None | "basemap" | "theme"
ss.setdefault("basemap", "OSM Standard")
ss.setdefault("theme", "ORIGINAL")

# ---------------------------------------------------------------------------
# CHROME CSS
# ---------------------------------------------------------------------------
RAIL_W = "300px" if ss.panel else "52px"
st.markdown(f"""
<style>
/* hide chrome: display:none (NOT visibility) so no layout space remains */
#MainMenu, footer, header[data-testid="stHeader"] {{display:none !important;}}
html, body, [data-testid="stAppViewContainer"], section[data-testid="stMain"] {{
    overflow:hidden !important; background:#fff !important;
}}
/* zero every padding/gap layer between app root and the component iframe */
section.main .block-container, [data-testid="stMainBlockContainer"] {{
    padding:0 !important; max-width:100% !important; min-height:100vh;
}}
div[data-testid="stVerticalBlock"] {{gap:0 !important;}}
div[data-testid="stIFrame"] {{height:100vh !important; width:100%;}}
div[data-testid="stIFrame"] iframe {{height:100vh !important; width:100% !important; border:none;}}

/* --- left icon rail --- */
section[data-testid="stSidebar"] {{
    width:{RAIL_W} !important; min-width:{RAIL_W} !important;
    background:#fff !important; border-right:1px solid #d0d0d0; overflow:hidden;
}}
section[data-testid="stSidebar"] .block-container {{padding:8px 4px !important; gap:2px;}}
section[data-testid="stSidebar"] div[data-testid="stSidebarHeader"],
section[data-testid="stSidebar"] button[kind="headerNoBorder"] {{display:none !important;}}
/* kill the rail scrollbar (the black pill in the old build) */
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{overflow:hidden !important; scrollbar-width:none;}}
section[data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar {{display:none;}}

/* icon buttons: square, borderless, monochrome */
section[data-testid="stSidebar"] div[data-testid="stButton"] {{margin:0;}}
section[data-testid="stSidebar"] div[data-testid="stButton"] button {{
    width:100%; min-height:0; padding:8px 0; border:none; border-radius:4px;
    background:transparent; color:#222; font-size:17px; line-height:1;
}}
section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {{background:#e8e8e8;}}
section[data-testid="stSidebar"] div[data-testid="stButton"] button p {{margin:0;}}
section[data-testid="stSidebar"] label {{font-size:12px;}}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TOOLBAR
# ---------------------------------------------------------------------------
def tool(icon: str, tip: str, key: str) -> bool:
    return st.sidebar.button(icon, help=tip, key=key, use_container_width=True)

def toggle(panel: str):
    ss.panel = None if ss.panel == panel else panel

if tool("☰", "Basemap", "t_bm"):         toggle("basemap")
if tool("▨", "Basemap colors", "t_th"):  toggle("theme")
if tool("＋", "Zoom in",  "t_zi"):        ss.zoom = min(19, ss.zoom + 1)
if tool("－", "Zoom out", "t_zo"):        ss.zoom = max(1,  ss.zoom - 1)
if tool("⌂", "Reset view", "t_rs"):
    ss.zoom, ss.lat, ss.lon = DEFAULT_ZOOM, *DEFAULT_CENTER
if ss.panel and tool("✕", "Close panel", "t_cl"):
    ss.panel = None

# panel content only exists while open -> nothing leaks into the narrow rail
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
    m = folium.Map(location=center, zoom_start=zoom, prefer_canvas=True, zoom_control=False)
    cfg = BASEMAPS[basemap_name]
    folium.TileLayer(tiles=cfg["url"], attr=cfg["attr"],
                     subdomains=cfg.get("subdomains", "abc"),
                     max_zoom=19, name=basemap_name).add_to(m)

    # filter on the tile PANE (not per tile) -> no seams
    # invalidateSize after load -> tiles fill the iframe even after CSS resize
    js_css = ("<style>"
              "html,body,.leaflet-container{background:" + theme["bg"] + " !important;}"
              ".leaflet-tile-pane{filter:" + theme["filter"] + ";}"
              "</style>"
              "<script>"
              "window.addEventListener('load',function(){"
              "setTimeout(function(){"
              "for(var k in window){if(k.indexOf('map_')===0&&window[k]&&window[k].invalidateSize){window[k].invalidateSize();}}"
              "},250);});"
              "</script>")
    m.get_root().html.add_child(folium.Element(js_css))
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

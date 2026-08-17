"""
Fullscreen Streamlit map + sidebar toolbar (basemap & color theme selector).
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
    "CARTO Dark": {
        "url": "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        "attr": "© OpenStreetMap contributors © CARTO", "subdomains": "abcd",
    },
    "CARTO Light": {
        "url": "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        "attr": "© OpenStreetMap contributors © CARTO", "subdomains": "abcd",
    },
    "OSM Standard": {
        "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attr": "© OpenStreetMap contributors",
    },
    "Esri Satellite": {
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attr": "© Esri, Maxar, Earthstar Geographics",
    },
    "OpenTopoMap": {
        "url": "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        "attr": "© OpenTopoMap (CC-BY-SA)", "subdomains": "abc",
    },
}

# Color themes = CSS filter on tile pane + page background + preview swatches.
# Tune `filter` strings freely; they are the whole theming mechanism.
THEMES = {
    "CARRARA": {
        "filter": "grayscale(1) contrast(1.1) brightness(0.92)",
        "bg": "#101112",
        "swatches": ["#1e1e1e", "#f5f5f5", "#232323", "#2b2b2b", "#3d3d3d"],
    },
    "SANDSTONE": {
        "filter": "sepia(0.7) saturate(1.3) contrast(0.95) brightness(0.9)",
        "bg": "#221a10",
        "swatches": ["#4b3a26", "#ded8cf", "#55432c", "#4a3a26", "#5c4c36"],
    },
    "MIDNIGHT BLUE": {
        "filter": "saturate(1.4) hue-rotate(180deg) brightness(0.75) contrast(1.1)",
        "bg": "#0d1626",
        "swatches": ["#b3994d", "#0e1726", "#a78a3e", "#7d5f20", "#262b2e"],
    },
    "CONTRAST": {
        "filter": "grayscale(1) contrast(1.9) brightness(0.85)",
        "bg": "#000000",
        "swatches": ["#101010", "#f7f7f7", "#171717", "#262626", "#4c4c4c"],
    },
    "ORIGINAL": {
        "filter": "none",
        "bg": "#0b0e12",
        "swatches": ["#243447", "#8fb6d9", "#1a2430", "#2e4054", "#405a72"],
    },
}

DEFAULT_CENTER = (40.7128, -74.0060)  # NYC

# ---------------------------------------------------------------------------
# FULLSCREEN CHROME: hide Streamlit header/menu, stretch map iframe to viewport
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    #MainMenu, header[data-testid="stHeader"], footer {visibility: hidden;}
    .main .block-container {padding: 0 !important; max-width: 100%;}
    div[data-testid="stVerticalBlock"] {gap: 0 !important;}
    div[data-testid="stIFrame"], div[data-testid="stIFrame"] iframe {
        height: 100vh !important; width: 100% !important; border: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# SIDEBAR TOOLBAR
# ---------------------------------------------------------------------------
def swatch_row(colors: list) -> str:
    """HTML preview strip mirroring the palette cards."""
    cells = "".join(f'<div style="flex:1;height:22px;background:{c};"></div>' for c in colors)
    return f'<div style="display:flex;border-radius:4px;overflow:hidden;margin:2px 0 10px;">{cells}</div>'

st.session_state.setdefault("zoom", 12)
st.session_state.setdefault("lat", DEFAULT_CENTER[0])
st.session_state.setdefault("lon", DEFAULT_CENTER[1])

with st.sidebar:
    st.title("🗺️ Map Console")
    basemap = st.selectbox("Basemap", list(BASEMAPS.keys()), index=0)
    theme_name = st.radio("Basemap colors", list(THEMES.keys()), index=0)
    theme = THEMES[theme_name]
    st.markdown(swatch_row(theme["swatches"]), unsafe_allow_html=True)
    st.slider("Zoom", 1, 19, key="zoom")
    st.number_input("Latitude", -90.0, 90.0, key="lat", format="%.4f")
    st.number_input("Longitude", -180.0, 180.0, key="lon", format="%.4f")
    if st.button("Reset view"):
        st.session_state.zoom = 12
        st.session_state.lat, st.session_state.lon = DEFAULT_CENTER
        st.rerun()

# ---------------------------------------------------------------------------
# MAP BUILD
# ---------------------------------------------------------------------------
def build_map(basemap_name: str, theme: dict, center: tuple, zoom: int) -> folium.Map:
    m = folium.Map(location=center, zoom_start=zoom, prefer_canvas=True)
    cfg = BASEMAPS[basemap_name]
    folium.TileLayer(
        tiles=cfg["url"],
        attr=cfg["attr"],
        subdomains=cfg.get("subdomains", "abc"),
        max_zoom=19,
        name=basemap_name,
    ).add_to(m)

    # Theme injected as CSS inside the map iframe. Filtering the pane (not each
    # tile img) prevents visible seams at tile borders.
    css = (
        "<style>"
        "html,body,.leaflet-container{background:" + theme["bg"] + " !important;}"
        ".leaflet-tile-pane{filter:" + theme["filter"] + ";}"
        "</style>"
    )
    m.get_root().html.add_child(folium.Element(css))
    return m

# ---------------------------------------------------------------------------
# RENDER
# ---------------------------------------------------------------------------
try:
    fmap = build_map(basemap, theme, (st.session_state.lat, st.session_state.lon), st.session_state.zoom)
    # returned_objects=[] skips shipping map state back -> faster reruns.
    st_folium(fmap, use_container_width=True, height=900, returned_objects=[])
    log.info("rendered basemap=%s theme=%s", basemap, theme_name)
except Exception as exc:  # keep app alive if map construction fails
    log.exception("Map render failed")
    st.error(f"Map render failed: {exc}")

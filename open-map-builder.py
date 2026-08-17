import json
import streamlit as st
import streamlit.components.v1 as components

# ------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & FELT.COM-STYLE UI
# ------------------------------------------------------------------------
st.set_page_config(
    page_title="Felt Map Studio",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .block-container { padding: 0rem !important; max-width: 100% !important; }
    header { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    [data-testid="stSidebar"] { background-color: #0d1117; border-right: 1px solid #21262d; }
    [data-testid="stSidebar"] * { color: #f0f6fc; }
    div.row-widget.stRadio > div {
        background: #161b22; padding: 12px; border-radius: 8px; border: 1px solid #30363d;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------
# 2. SIDEBAR TOOLBAR
# ------------------------------------------------------------------------
st.sidebar.markdown("### 🗺️ **Basemap Layer**")

basemap_options = [
    "Midnight Blue",
    "Carto DB Light",
    "Carto DB Dark",
    "Satellite",
    "OSM"
]

selected_basemap = st.sidebar.radio("Select Layer", options=basemap_options, index=0)
st.sidebar.markdown("---")

if selected_basemap == "Midnight Blue":
    st.sidebar.markdown(
        """
        <div style="background-color: #0a1628; padding: 12px; border-radius: 6px; border-left: 4px solid #c99c37;">
            <strong style="color: #c99c37;">Midnight Blue Active</strong><br>
            <span style="font-size: 12px; color: #8b949e;">Vector-rendered. Zero gridlines. Exact palette.</span>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.sidebar.caption(f"Active basemap: **{selected_basemap}**")

# ------------------------------------------------------------------------
# 3. STYLE BUILDERS (MapLibre GL style spec v8)
# ------------------------------------------------------------------------
CENTER = [121.0359, 14.5794]  # [lon, lat] Mandaluyong / Metro Manila
ZOOM = 14

# --- Palette sampled from the reference swatch sheet ---
C = {
    "base":      "#0a1628",  # Land / background
    "landcover": "#0e1a2e",
    "landuse":   "#0d1a2f",
    "water":     "#0a1424",
    "waterway":  "#071019",
    "park":      "#14243e",
    "building":  "#8d7156",
    "aeroway":   "#14243c",
    "rail":      "#d9b451",
    "rd_major":  "#c99c37",  # motorway / trunk / primary
    "rd_min_hi": "#a8801f",  # secondary / tertiary
    "rd_min_md": "#494941",  # minor streets
    "rd_min_lo": "#32322d",  # service / track
    "rd_path":   "#4c4535",
    "rd_case":   "#6a5e39",  # road outline / casing
}

def w(*stops):
    """Zoom-interpolated line width helper (exponential 1.2)."""
    out = ["interpolate", ["exponential", 1.2], ["zoom"]]
    for z, val in stops:
        out += [z, val]
    return out

def road_layer(lid, classes, color, widths, minzoom=0, casing=False):
    """One transportation line layer filtered by OMT class."""
    lyr = {
        "id": lid, "type": "line", "source": "omt", "source-layer": "transportation",
        "filter": ["match", ["get", "class"], classes, True, False],
        "layout": {"line-cap": "round", "line-join": "round"},
        "paint": {"line-color": color, "line-width": w(*widths)},
    }
    if minzoom:
        lyr["minzoom"] = minzoom
    if casing:  # draw the olive outline under the fill
        lyr["paint"]["line-color"] = C["rd_case"]
        lyr["paint"]["line-width"] = w(*[(z, val + 2.0) for z, val in widths])
        lyr["id"] = lid + "_casing"
    return lyr

def midnight_style():
    """Custom vector style. Vector tiles = no raster seams/gridlines, ever."""
    return {
        "version": 8,
        "sources": {
            # Free OpenMapTiles vector planet, no API key (OpenFreeMap)
            "omt": {"type": "vector", "url": "https://tiles.openfreemap.org/planet"}
        },
        "layers": [
            {"id": "bg", "type": "background", "paint": {"background-color": C["base"]}},
            {"id": "landcover", "type": "fill", "source": "omt", "source-layer": "landcover",
             "paint": {"fill-color": C["landcover"], "fill-opacity": 0.6}},
            {"id": "landuse", "type": "fill", "source": "omt", "source-layer": "landuse",
             "paint": {"fill-color": C["landuse"], "fill-opacity": 0.8}},
            {"id": "park", "type": "fill", "source": "omt", "source-layer": "park",
             "paint": {"fill-color": C["park"]}},
            {"id": "water", "type": "fill", "source": "omt", "source-layer": "water",
             "paint": {"fill-color": C["water"]}},
            {"id": "waterway", "type": "line", "source": "omt", "source-layer": "waterway",
             "paint": {"line-color": C["waterway"], "line-width": w((9, 1), (20, 6))}},
            {"id": "aeroway", "type": "line", "source": "omt", "source-layer": "aeroway",
             "paint": {"line-color": C["aeroway"], "line-width": w((11, 1), (20, 12))}},
            {"id": "building", "type": "fill", "source": "omt", "source-layer": "building",
             "minzoom": 14,
             "paint": {"fill-color": C["building"], "fill-opacity": 0.85,
                        "fill-outline-color": "#6f5844"}},
            # Casings first (road outline), then fills low->high so majors sit on top
            road_layer("case_major", ["motorway", "trunk", "primary"], None,
                       [(6, 1.0), (14, 4.0), (20, 22)], casing=True),
            road_layer("case_minhi", ["secondary", "tertiary"], None,
                       [(8, 0.8), (14, 3.0), (20, 16)], casing=True),
            road_layer("rd_path", ["path", "pedestrian", "footway"], C["rd_path"],
                       [(14, 0.6), (20, 6)], minzoom=14),
            road_layer("rd_min_lo", ["service", "track"], C["rd_min_lo"],
                       [(14, 0.6), (20, 7)], minzoom=14),
            road_layer("rd_min_md", ["minor"], C["rd_min_md"],
                       [(13, 0.8), (16, 4.0), (20, 12)], minzoom=13),
            road_layer("rd_min_hi", ["secondary", "tertiary"], C["rd_min_hi"],
                       [(8, 0.8), (14, 3.0), (20, 16)]),
            road_layer("rd_major", ["motorway", "trunk", "primary"], C["rd_major"],
                       [(6, 1.0), (14, 4.0), (20, 22)]),
            road_layer("rail", ["rail"], C["rail"], [(13, 0.5), (20, 2.5)], minzoom=13),
        ],
    }

def raster_style(tile_urls, bg, maxzoom=20):
    """Plain raster basemaps (also seam-free: single canvas renderer)."""
    return {
        "version": 8,
        "sources": {"r": {"type": "raster", "tiles": tile_urls, "tileSize": 256, "maxzoom": maxzoom}},
        "layers": [
            {"id": "bg", "type": "background", "paint": {"background-color": bg}},
            {"id": "r", "type": "raster", "source": "r"},
        ],
    }

STYLES = {
    "Midnight Blue": midnight_style,
    "Carto DB Light": lambda: raster_style(
        ["https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
         "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"], "#f8f9fa"),
    "Carto DB Dark": lambda: raster_style(
        ["https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
         "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"], "#000000"),
    "OSM": lambda: raster_style(
        ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"], "#f2efe9", maxzoom=19),
    "Satellite": lambda: raster_style(
        ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
        "#000000", maxzoom=19),
}

# ------------------------------------------------------------------------
# 4. MAPLIBRE GL RENDERER (replaces folium entirely)
# ------------------------------------------------------------------------
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<script src="https://unpkg.com/maplibre-gl@5/dist/maplibre-gl.js"></script>
<link href="https://unpkg.com/maplibre-gl@5/dist/maplibre-gl.css" rel="stylesheet"/>
<style>
  html, body { margin: 0; padding: 0; background: __BG__; }
  #map { position: absolute; width: 100%; height: 100%; }
  #attr { position: absolute; bottom: 4px; left: 6px; z-index: 2;
          font: 10px sans-serif; color: #8b949e; pointer-events: none; }
  #err { display: none; position: absolute; top: 10px; left: 10px; z-index: 3;
         background: #3d1111; color: #ffb4b4; padding: 8px 12px;
         border-radius: 6px; font: 12px monospace; }
</style>
</head>
<body>
<div id="map"></div>
<div id="attr">© OpenStreetMap contributors · OpenFreeMap</div>
<div id="err"></div>
<script>
try {
  const map = new maplibregl.Map({
    container: 'map',
    style: __STYLE__,
    center: __CENTER__,
    zoom: __ZOOM__,
    attributionControl: false,
    fadeDuration: 0
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
  map.on('error', (e) => {
    // Log tile/network failures without killing the app
    console.warn('map error:', e);
  });
} catch (e) {
  const box = document.getElementById('err');
  box.style.display = 'block';
  box.textContent = 'Map init failed: ' + e.message;
}
</script>
</body>
</html>"""

try:
    style_json = json.dumps(STYLES[selected_basemap]())
    bg = "#0a1628" if selected_basemap == "Midnight Blue" else "#000000"
    html = (HTML_TEMPLATE
            .replace("__STYLE__", style_json)
            .replace("__CENTER__", json.dumps(CENTER))
            .replace("__ZOOM__", str(ZOOM))
            .replace("__BG__", bg))
    components.html(html, height=950, scrolling=False)
except Exception as e:
    st.error(f"Map render failed: {e}")

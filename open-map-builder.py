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
    "White Gold",
    "Carto DB Light",
    "Carto DB Dark",
    "Satellite",
    "OSM"
]

selected_basemap = st.sidebar.radio("Select Layer", options=basemap_options, index=0)

# Initial label state; live tweaks happen in the in-map panel (no reload)
show_labels = st.sidebar.checkbox("🏷️ Show Labels", value=True)

st.sidebar.markdown("---")
st.sidebar.caption("Live **opacity sliders** and label toggle are in the map panel (bottom-right) — no reload, camera stays put.")

# ------------------------------------------------------------------------
# 3. THEME PALETTES & STYLE BUILDERS (MapLibre GL style spec v8)
# ------------------------------------------------------------------------
CENTER = [121.0359, 14.5794]  # [lon, lat] Mandaluyong / Metro Manila
ZOOM = 14

# Vector themes: one palette dict per theme, one shared style builder
THEMES = {
    "Midnight Blue": {
        "overlay": "#0a1628", "text": "#d9b451", "land": "#0d1830",
        "landcover": "#0f1d33", "water": "#0a1424", "waterway": "#081120",
        "parks": "#142440", "buildings": "#8e7258", "aeroway": "#152640",
        "rail": "#d9b451",
        "rd_major": "#e8b84a",   # bright gold
        "rd_min_hi": "#7d5f14",  # darker gold, drawn faded
        "rd_min_md": "#46463e", "rd_min_lo": "#2f2f2a", "rd_path": "#4a4333",
        "rd_case": "#685c37",
        "sec_opacity": 0.7,      # secondary roads sit back
        "building_opacity": 0.07,
        "muted": "#8b949e",
    },
    "White Gold": {
        "overlay": "#ffffff", "text": "#a07d1c", "land": "#fafafa",
        "landcover": "#f1f1ec", "water": "#d4dadc", "waterway": "#c2c9cc",
        "parks": "#e6ebe4", "buildings": "#d8d8d4", "aeroway": "#e4e4e4",
        "rail": "#c99c37",
        "rd_major": "#e5a91d",   # bright gold pops on white
        "rd_min_hi": "#9c7a1a",  # darker gold, drawn faded
        "rd_min_md": "#e0be74", "rd_min_lo": "#ead9b0", "rd_path": "#e6dabd",
        "rd_case": "#b08a24",
        "sec_opacity": 0.6,
        "building_opacity": 0.5,
        "muted": "#6b7280",
    },
}

def w(*stops):
    """Zoom-interpolated line width helper (exponential 1.2)."""
    out = ["interpolate", ["exponential", 1.2], ["zoom"]]
    for z, val in stops:
        out += [z, val]
    return out

def road_layer(p, lid, classes, color, widths, minzoom=0, casing=False, opacity=1.0):
    """One transportation line layer filtered by OMT class."""
    lyr = {
        "id": lid, "type": "line", "source": "omt", "source-layer": "transportation",
        "filter": ["match", ["get", "class"], classes, True, False],
        "layout": {"line-cap": "round", "line-join": "round"},
        "paint": {"line-color": color, "line-width": w(*widths), "line-opacity": opacity},
    }
    if minzoom:
        lyr["minzoom"] = minzoom
    if casing:  # outline drawn under the road fill
        lyr["paint"]["line-color"] = p["rd_case"]
        lyr["paint"]["line-width"] = w(*[(z, val + 2.0) for z, val in widths])
        lyr["id"] = lid + "_casing"
    return lyr

def vector_style(p, show_labels):
    """Custom vector style from a palette. Vector tiles = zero gridlines."""
    sec = p["sec_opacity"]
    return {
        "version": 8,
        "glyphs": "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
        "sources": {
            # Free OpenMapTiles vector planet, no API key (OpenFreeMap)
            "omt": {"type": "vector", "url": "https://tiles.openfreemap.org/planet"}
        },
        "layers": [
            {"id": "bg", "type": "background", "paint": {"background-color": p["overlay"]}},
            {"id": "landcover", "type": "fill", "source": "omt", "source-layer": "landcover",
             "paint": {"fill-color": p["landcover"], "fill-opacity": 0.6}},
            {"id": "landuse", "type": "fill", "source": "omt", "source-layer": "landuse",
             "paint": {"fill-color": p["land"], "fill-opacity": 0.8}},
            {"id": "park", "type": "fill", "source": "omt", "source-layer": "park",
             "paint": {"fill-color": p["parks"]}},
            {"id": "water", "type": "fill", "source": "omt", "source-layer": "water",
             "paint": {"fill-color": p["water"]}},
            {"id": "waterway", "type": "line", "source": "omt", "source-layer": "waterway",
             "paint": {"line-color": p["waterway"], "line-width": w((9, 1), (20, 6))}},
            {"id": "aeroway", "type": "line", "source": "omt", "source-layer": "aeroway",
             "paint": {"line-color": p["aeroway"], "line-width": w((11, 1), (20, 12))}},
            {"id": "building", "type": "fill", "source": "omt", "source-layer": "building",
             "minzoom": 14,
             "paint": {"fill-color": p["buildings"],
                        "fill-opacity": p["building_opacity"],
                        "fill-outline-color": p["buildings"]}},
            # Casings first (Road Outline), then fills low->high so majors sit on top
            road_layer(p, "case_major", ["motorway", "trunk", "primary"], None,
                       [(6, 1.0), (14, 4.0), (20, 22)], casing=True),
            road_layer(p, "case_minhi", ["secondary", "tertiary"], None,
                       [(8, 0.8), (14, 3.0), (20, 16)], casing=True, opacity=sec),
            road_layer(p, "rd_path", ["path", "pedestrian", "footway"], p["rd_path"],
                       [(14, 0.6), (20, 6)], minzoom=14),
            road_layer(p, "rd_min_lo", ["service", "track"], p["rd_min_lo"],
                       [(14, 0.6), (20, 7)], minzoom=14),
            road_layer(p, "rd_min_md", ["minor"], p["rd_min_md"],
                       [(13, 0.8), (16, 4.0), (20, 12)], minzoom=13),
            road_layer(p, "rd_min_hi", ["secondary", "tertiary"], p["rd_min_hi"],
                       [(8, 0.8), (14, 3.0), (20, 16)], opacity=sec),
            road_layer(p, "rd_major", ["motorway", "trunk", "primary"], p["rd_major"],
                       [(6, 1.0), (14, 4.0), (20, 22)]),
            road_layer(p, "rail", ["rail"], p["rail"], [(13, 0.5), (20, 2.5)], minzoom=13),
            # Place labels; visibility from checkbox, opacity live from panel slider
            {"id": "label_place", "type": "symbol", "source": "omt", "source-layer": "place",
             "minzoom": 6,
             "layout": {
                 "visibility": "visible" if show_labels else "none",
                 "text-field": ["coalesce", ["get", "name_en"], ["get", "name"]],
                 "text-font": ["Noto Sans Regular"],
                 "text-size": ["interpolate", ["linear"], ["zoom"], 6, 10, 12, 14, 16, 18],
                 "text-transform": "uppercase",
                 "text-letter-spacing": 0.05,
                 "text-max-width": 8,
             },
             "paint": {
                 "text-color": p["text"],
                 "text-halo-color": p["overlay"],
                 "text-halo-width": 1.5,
                 "text-opacity": 1.0,
             }},
        ],
    }

def raster_style(tile_urls, bg, maxzoom=20):
    """Plain raster basemaps (single canvas renderer, seam-free)."""
    return {
        "version": 8,
        "sources": {"r": {"type": "raster", "tiles": tile_urls, "tileSize": 256, "maxzoom": maxzoom}},
        "layers": [
            {"id": "bg", "type": "background", "paint": {"background-color": bg}},
            {"id": "r", "type": "raster", "source": "r"},
        ],
    }

STYLES = {
    "Midnight Blue": lambda lb: vector_style(THEMES["Midnight Blue"], lb),
    "White Gold":    lambda lb: vector_style(THEMES["White Gold"], lb),
    "Carto DB Light": lambda lb: raster_style(
        ["https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
         "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"], "#f8f9fa"),
    "Carto DB Dark": lambda lb: raster_style(
        ["https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
         "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"], "#000000"),
    "OSM": lambda lb: raster_style(
        ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"], "#f2efe9", maxzoom=19),
    "Satellite": lambda lb: raster_style(
        ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
        "#000000", maxzoom=19),
}

# Sidebar status card for vector themes
if selected_basemap in THEMES:
    p = THEMES[selected_basemap]
    st.sidebar.markdown(
        f"""
        <div style="background-color: {p['overlay']}; padding: 12px; border-radius: 6px;
                    border: 1px solid {p['muted']}33; border-left: 4px solid {p['rd_major']};">
            <strong style="color: {p['text']};">{selected_basemap} Active</strong><br>
            <span style="font-size: 12px; color: {p['muted']};">
                Vector-rendered. Zero gridlines. Exact palette.
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.sidebar.caption(f"Active basemap: **{selected_basemap}**")

# ------------------------------------------------------------------------
# 4. MAPLIBRE GL RENDERER
# ------------------------------------------------------------------------

# Live control panel (vector themes only): label toggle + opacity sliders.
# Applied client-side via setPaintProperty -> no reload, no camera reset.
PANEL_HTML = """
<div id="panel">
  <button id="lblToggle"></button>
  <div class="row"><span>Roads</span><input id="rdOp" type="range" min="0" max="1" step="0.05" value="1"></div>
  <div class="row"><span>Labels</span><input id="lbOp" type="range" min="0" max="1" step="0.05" value="1"></div>
</div>
"""

PANEL_JS = """
  // Base opacities baked into the style; sliders scale on top of them
  const ROAD_BASE = {
    'case_major_casing': 1, 'case_minhi_casing': __SEC__,
    'rd_path': 1, 'rd_min_lo': 1, 'rd_min_md': 1,
    'rd_min_hi': __SEC__, 'rd_major': 1, 'rail': 1
  };
  const rdOp = document.getElementById('rdOp');
  const lbOp = document.getElementById('lbOp');
  rdOp.addEventListener('input', () => {
    for (const [id, base] of Object.entries(ROAD_BASE)) {
      if (map.getLayer(id)) map.setPaintProperty(id, 'line-opacity', base * parseFloat(rdOp.value));
    }
  });
  lbOp.addEventListener('input', () => {
    if (map.getLayer('label_place')) map.setPaintProperty('label_place', 'text-opacity', parseFloat(lbOp.value));
  });
"""

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
          font: 10px sans-serif; color: __MUTED__; pointer-events: none; }
  #panel { position: absolute; bottom: 10px; right: 10px; z-index: 2;
           background: #161b22ee; border: 1px solid #30363d; border-radius: 8px;
           padding: 8px 10px; display: flex; flex-direction: column; gap: 6px;
           font: 11px sans-serif; color: #f0f6fc; width: 160px; }
  #panel .row { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
  #panel input[type=range] { width: 95px; accent-color: #c99c37; }
  #lblToggle { background: #21262d; color: #f0f6fc; border: 1px solid #30363d;
               border-radius: 6px; padding: 4px 8px; font: 11px sans-serif; cursor: pointer; }
  #err { display: none; position: absolute; top: 10px; left: 10px; z-index: 3;
         background: #3d1111; color: #ffb4b4; padding: 8px 12px;
         border-radius: 6px; font: 12px monospace; }
</style>
</head>
<body>
<div id="map"></div>
<div id="attr">© OpenStreetMap contributors · OpenFreeMap</div>
__PANEL__
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

  // Label visibility toggle (instant, no reload)
  let labelsOn = __LABELS_JS__;
  const btn = document.getElementById('lblToggle');
  if (btn) {
    const applyLabels = () => {
      if (map.getLayer('label_place')) {
        map.setLayoutProperty('label_place', 'visibility', labelsOn ? 'visible' : 'none');
      }
      btn.textContent = 'Labels: ' + (labelsOn ? 'ON' : 'OFF');
    };
    btn.onclick = () => { labelsOn = !labelsOn; applyLabels(); };
    map.on('load', applyLabels);
  }

__PANEL_JS__

  map.on('error', (e) => console.warn('map error:', e));
} catch (e) {
  const box = document.getElementById('err');
  box.style.display = 'block';
  box.textContent = 'Map init failed: ' + e.message;
}
</script>
</body>
</html>"""

try:
    is_vector = selected_basemap in THEMES
    style_json = json.dumps(STYLES[selected_basemap](show_labels))

    if is_vector:
        body_bg = THEMES[selected_basemap]["overlay"]
        muted = THEMES[selected_basemap]["muted"]
        sec = THEMES[selected_basemap]["sec_opacity"]
        panel_html, panel_js = PANEL_HTML, PANEL_JS.replace("__SEC__", str(sec))
    else:
        body_bg = "#000000" if selected_basemap in ("Carto DB Dark", "Satellite") else "#f8f9fa"
        muted = "#8b949e"
        panel_html, panel_js = "", ""  # sliders only make sense on vector themes

    html = (HTML_TEMPLATE
            .replace("__STYLE__", style_json)
            .replace("__CENTER__", json.dumps(CENTER))
            .replace("__ZOOM__", str(ZOOM))
            .replace("__BG__", body_bg)
            .replace("__MUTED__", muted)
            .replace("__LABELS_JS__", "true" if show_labels else "false")
            .replace("__PANEL__", panel_html)
            .replace("__PANEL_JS__", panel_js))
    components.html(html, height=950, scrolling=False)
except Exception as e:
    st.error(f"Map render failed: {e}")

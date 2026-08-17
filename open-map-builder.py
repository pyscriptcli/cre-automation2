import json
import streamlit as st
import streamlit.components.v1 as components

# ------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# ------------------------------------------------------------------------
st.set_page_config(
    page_title="Open Map Builder",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    [data-testid="stSidebar"], section[data-testid="stSidebar"] { display: none !important; }
    .block-container { padding: 0rem !important; margin: 0rem !important; max-width: 100% !important; height: 100vh !important; overflow: hidden !important; }
    header, #MainMenu, footer { visibility: hidden !important; height: 0 !important; }
    html, body, iframe { overflow: hidden !important; height: 100vh !important; width: 100vw !important; margin: 0 !important; padding: 0 !important; }
    </style>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------------
# 2. STYLES & VECTOR PALETTES
# ------------------------------------------------------------------------
CENTER = [121.0359, 14.5794]
ZOOM = 14

THEMES = {
    "Midnight Blue": {
        "overlay": "#0a1628",
        "text": "#d9b451",
        "land": "#0d1830",
        "landcover": "#0f1d33",
        "water": "#0a1424",
        "waterway": "#081120",
        "parks": "#142440",
        "buildings": "#8e7258",
        "aeroway": "#152640",
        "rail": "#d9b451",
        "rd_major": "#e8b84a",
        "rd_min_hi": "#7d5f14",
        "rd_min_md": "#46463e",
        "rd_min_lo": "#2f2f2a",
        "rd_path": "#4a4333",
        "rd_case": "#685c37",
        "sec_opacity": 0.7,
        "building_opacity": 0.25,
        "muted": "#8b949e",
    },
    "White Gold": {
        "overlay": "#ffffff",
        "text": "#a07d1c",
        "land": "#fafafa",
        "landcover": "#f1f1ec",
        "water": "#d4dadc",
        "waterway": "#c2c9cc",
        "parks": "#e6ebe4",
        "buildings": "#d8d8d4",
        "aeroway": "#e4e4e4",
        "rail": "#c99c37",
        "rd_major": "#e5a91d",
        "rd_min_hi": "#9c7a1a",
        "rd_min_md": "#e0be74",
        "rd_min_lo": "#ead9b0",
        "rd_path": "#e6dabd",
        "rd_case": "#b08a24",
        "sec_opacity": 0.6,
        "building_opacity": 0.5,
        "muted": "#6b7280",
    },
}


def w(*stops):
    out = ["interpolate", ["exponential", 1.2], ["zoom"]]
    for z, val in stops:
        out += [z, val]
    return out


def road_layer(
    p, lid, classes, color, widths, minzoom=0, casing=False, opacity=1.0
):
    lyr = {
        "id": lid,
        "type": "line",
        "source": "omt",
        "source-layer": "transportation",
        "filter": ["match", ["get", "class"], classes, True, False],
        "layout": {"line-cap": "round", "line-join": "round"},
        "paint": {
            "line-color": color,
            "line-width": w(*widths),
            "line-opacity": opacity,
        },
    }
    if minzoom:
        lyr["minzoom"] = minzoom
    if casing:
        lyr["paint"]["line-color"] = p["rd_case"]
        lyr["paint"]["line-width"] = w(*[(z, val + 2.0) for z, val in widths])
        lyr["id"] = lid + "_casing"
    return lyr


def vector_style(p):
    sec = p["sec_opacity"]
    return {
        "version": 8,
        "glyphs": (
            "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf"
        ),
        "sources": {
            "omt": {
                "type": "vector",
                "url": "https://tiles.openfreemap.org/planet",
            }
        },
        "layers": [
            {
                "id": "bg",
                "type": "background",
                "paint": {"background-color": p["overlay"]},
            },
            {
                "id": "landcover",
                "type": "fill",
                "source": "omt",
                "source-layer": "landcover",
                "paint": {"fill-color": p["landcover"], "fill-opacity": 0.6},
            },
            {
                "id": "landuse",
                "type": "fill",
                "source": "omt",
                "source-layer": "landuse",
                "paint": {"fill-color": p["land"], "fill-opacity": 0.8},
            },
            {
                "id": "park",
                "type": "fill",
                "source": "omt",
                "source-layer": "park",
                "paint": {"fill-color": p["parks"]},
            },
            {
                "id": "water",
                "type": "fill",
                "source": "omt",
                "source-layer": "water",
                "paint": {"fill-color": p["water"]},
            },
            {
                "id": "waterway",
                "type": "line",
                "source": "omt",
                "source-layer": "waterway",
                "paint": {
                    "line-color": p["waterway"],
                    "line-width": w((9, 1), (20, 6)),
                },
            },
            {
                "id": "aeroway",
                "type": "line",
                "source": "omt",
                "source-layer": "aeroway",
                "paint": {
                    "line-color": p["aeroway"],
                    "line-width": w((11, 1), (20, 12)),
                },
            },
            {
                "id": "building",
                "type": "fill",
                "source": "omt",
                "source-layer": "building",
                "minzoom": 13,
                "paint": {
                    "fill-color": p["buildings"],
                    "fill-opacity": p["building_opacity"],
                    "fill-outline-color": p["buildings"],
                },
            },
            road_layer(
                p,
                "case_major",
                ["motorway", "trunk", "primary"],
                None,
                [(6, 1.0), (14, 4.0), (20, 22)],
                casing=True,
            ),
            road_layer(
                p,
                "case_minhi",
                ["secondary", "tertiary"],
                None,
                [(8, 0.8), (14, 3.0), (20, 16)],
                casing=True,
                opacity=sec,
            ),
            road_layer(
                p,
                "rd_path",
                ["path", "pedestrian", "footway"],
                p["rd_path"],
                [(14, 0.6), (20, 6)],
                minzoom=14,
            ),
            road_layer(
                p,
                "rd_min_lo",
                ["service", "track"],
                p["rd_min_lo"],
                [(14, 0.6), (20, 7)],
                minzoom=14,
            ),
            road_layer(
                p,
                "rd_min_md",
                ["minor"],
                p["rd_min_md"],
                [(13, 0.8), (16, 4.0), (20, 12)],
                minzoom=13,
            ),
            road_layer(
                p,
                "rd_min_hi",
                ["secondary", "tertiary"],
                p["rd_min_hi"],
                [(8, 0.8), (14, 3.0), (20, 16)],
                opacity=sec,
            ),
            road_layer(
                p,
                "rd_major",
                ["motorway", "trunk", "primary"],
                p["rd_major"],
                [(6, 1.0), (14, 4.0), (20, 22)],
            ),
            road_layer(
                p,
                "rail",
                ["rail"],
                p["rail"],
                [(13, 0.5), (20, 2.5)],
                minzoom=13,
            ),
            {
                "id": "label_place",
                "type": "symbol",
                "source": "omt",
                "source-layer": "place",
                "minzoom": 6,
                "layout": {
                    "text-field": [
                        "coalesce",
                        ["get", "name_en"],
                        ["get", "name"],
                    ],
                    "text-font": ["Noto Sans Regular"],
                    "text-size": [
                        "interpolate",
                        ["linear"],
                        ["zoom"],
                        6,
                        10,
                        12,
                        14,
                        16,
                        18,
                    ],
                    "text-transform": "uppercase",
                    "text-letter-spacing": 0.05,
                    "text-max-width": 8,
                },
                "paint": {
                    "text-color": p["text"],
                    "text-halo-color": p["overlay"],
                    "text-halo-width": 1.5,
                },
            },
        ],
    }


def raster_style(tile_urls, bg, maxzoom=20):
    return {
        "version": 8,
        "sources": {
            "r": {
                "type": "raster",
                "tiles": tile_urls,
                "tileSize": 256,
                "maxzoom": maxzoom,
            }
        },
        "layers": [
            {"id": "bg", "type": "background", "paint": {"background-color": bg}},
            {"id": "r", "type": "raster", "source": "r"},
        ],
    }


ALL_STYLES = {
    "Midnight Blue": vector_style(THEMES["Midnight Blue"]),
    "White Gold": vector_style(THEMES["White Gold"]),
    "Carto DB Light": raster_style(
        [
            "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
            "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
        ],
        "#f8f9fa",
    ),
    "Carto DB Dark": raster_style(
        [
            "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
            "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
        ],
        "#000000",
    ),
    "OSM": raster_style(
        ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"], "#f2efe9", 19
    ),
    "Satellite": raster_style(
        [
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ],
        "#000000",
        19,
    ),
}

INITIAL_BASEMAP = "Midnight Blue"

# ------------------------------------------------------------------------
# 3. OPEN MAP BUILDER APP ENGINE
# ------------------------------------------------------------------------
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"/>
<script src="https://unpkg.com/maplibre-gl@5/dist/maplibre-gl.js"></script>
<link href="https://unpkg.com/maplibre-gl@5/dist/maplibre-gl.css" rel="stylesheet"/>
<style>
  @font-face {
    font-family: 'Century Gothic Custom';
    src: local('Century Gothic'), local('CenturyGothic'), local('AppleGothic'), sans-serif;
  }
  * { box-sizing: border-box; user-select: none; }
  html, body { margin: 0; padding: 0; width: 100vw; height: 100vh; overflow: hidden; background: __BG__; font-family: 'Century Gothic Custom', system-ui, -apple-system, sans-serif; }
  #map { position: absolute; inset: 0; width: 100%; height: 100%; }

  /* Left Vertical Sidebar Rail */
  #side-rail {
    position: absolute; top: 0; left: 0; bottom: 0; width: 46px; z-index: 10;
    background: #ffffff; border-right: 1px solid #e1e4e8;
    display: flex; flex-direction: column; align-items: center; padding: 8px 0; gap: 4px;
    box-shadow: 2px 0 8px rgba(0,0,0,0.06);
  }
  .rail-btn {
    width: 36px; height: 36px; display: grid; place-items: center;
    background: transparent; border: none; color: #4a5568; border-radius: 6px;
    cursor: pointer; transition: all 0.15s ease;
  }
  .rail-btn:hover { background: #f0f2f5; color: #1a202c; }
  .rail-btn.active { background: #e2e8f0; color: #0f172a; }
  .rail-btn.primary-active { background: #0f172a; color: #ffffff; }
  .rail-sep { width: 28px; height: 1px; background: #e2e8f0; margin: 4px 0; }

  /* Flyout / Data Browser Sidebar Panel */
  #browser-panel {
    position: absolute; top: 0; left: 46px; bottom: 0; width: 340px; z-index: 9;
    background: #ffffff; border-right: 1px solid #e1e4e8;
    box-shadow: 4px 0 16px rgba(0,0,0,0.08);
    display: flex; flex-direction: column; overflow: hidden;
    transform: translateX(0); transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  }
  #browser-panel.collapsed { transform: translateX(-100%); }

  .panel-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 16px; border-bottom: 1px solid #eef0f2;
  }
  .panel-title { display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 15px; color: #1a202c; }
  .panel-actions { display: flex; gap: 4px; }
  .icon-action-btn { width: 28px; height: 28px; display: grid; place-items: center; border: 1px solid #e2e8f0; background: #ffffff; border-radius: 6px; cursor: pointer; color: #4a5568; }
  .icon-action-btn:hover { background: #f8fafc; color: #1a202c; }

  .panel-content { flex: 1; overflow-y: auto; padding: 12px 16px; display: flex; flex-direction: column; gap: 14px; }

  /* Accordion Sections */
  .acc-item { border-bottom: 1px solid #edf2f7; padding-bottom: 8px; }
  .acc-header { display: flex; align-items: center; justify-content: space-between; font-size: 13px; font-weight: 600; color: #2d3748; cursor: pointer; padding: 6px 0; }
  .acc-body { padding: 8px 0 4px 0; display: flex; flex-direction: column; gap: 8px; }
  .acc-body.hidden { display: none; }

  .layer-row { display: flex; align-items: center; justify-content: space-between; font-size: 12px; color: #4a5568; }
  .layer-row input[type=checkbox] { accent-color: #0f172a; cursor: pointer; }

  /* Layers Group in Panel */
  .layers-heading { display: flex; align-items: center; justify-content: space-between; font-weight: 700; font-size: 14px; color: #1a202c; margin-top: 6px; }
  .badge-count { background: #0f172a; color: #ffffff; border-radius: 12px; font-size: 11px; padding: 1px 8px; font-weight: 600; }

  .layer-card {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 10px;
    display: flex; flex-direction: column; gap: 6px; margin-top: 6px;
  }
  .layer-card-top { display: flex; align-items: center; gap: 6px; }
  .layer-name-input {
    flex: 1; border: 1px solid transparent; background: transparent; font-weight: 600;
    font-size: 12px; color: #1a202c; padding: 2px 4px; border-radius: 4px; font-family: inherit;
  }
  .layer-name-input:focus { border-color: #cbd5e1; background: #ffffff; outline: none; }
  .card-btn { background: transparent; border: none; color: #64748b; cursor: pointer; padding: 2px 4px; border-radius: 4px; }
  .card-btn:hover { color: #0f172a; background: #e2e8f0; }

  /* Floating Popups & Draw Tool Setting Panels */
  .float-card {
    position: absolute; z-index: 12; background: #ffffff; border: 1px solid #e2e8f0;
    border-radius: 10px; padding: 12px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.15);
    display: none; flex-direction: column; gap: 8px; font-size: 12px; color: #2d3748;
  }
  .float-card.open { display: flex; }
  .float-card .f-row { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
  .float-card input[type=range] { accent-color: #0f172a; width: 100px; cursor: pointer; }
  .float-card input[type=color] { border: none; width: 26px; height: 26px; border-radius: 4px; cursor: pointer; background: transparent; }
  .float-card input[type=text], .float-card select { border: 1px solid #cbd5e1; border-radius: 6px; padding: 5px 8px; font-family: inherit; font-size: 12px; }

  #popup-marker-settings { top: 60px; left: 56px; width: 220px; }
  #popup-text-settings { top: 100px; left: 56px; width: 240px; }
  #popup-shape-editor { top: 20px; right: 20px; width: 280px; }
  #popup-custom-map { top: 20px; right: 20px; width: 270px; max-height: 85vh; overflow-y: auto; }
  #popup-search { top: 46px; left: 56px; width: 280px; }

  .icon-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
  .icon-grid button { width: 34px; height: 34px; display: grid; place-items: center; border: 1px solid #e2e8f0; border-radius: 6px; background: #ffffff; color: #4a5568; cursor: pointer; }
  .icon-grid button.active { border-color: #0f172a; background: #0f172a; color: #ffffff; }

  #hint-toast {
    position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); z-index: 15;
    background: #0f172ae6; color: #ffffff; border-radius: 20px; padding: 7px 18px;
    font-size: 12px; backdrop-filter: blur(4px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); display: none;
  }
  #err { position: absolute; top: 10px; right: 10px; z-index: 20; background: #fee2e2; color: #991b1b; padding: 8px 12px; border-radius: 6px; font-size: 12px; display: none; }
</style>
</head>
<body>
<div id="map"></div>

<!-- Left Vertical Orientation Toolbar Rail -->
<div id="side-rail">
  <button class="rail-btn" id="btn-browser-toggle" title="Data Browser / Layers">
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"></path><path d="M2 12l10 6 10-6"></path><path d="M2 16l10 6 10-6"></path></svg>
  </button>
  <button class="rail-btn" id="btn-search" title="Search Location">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"></circle><line x1="21" y1="21" x2="16.5" y2="16.5"></line></svg>
  </button>
  <button class="rail-btn tool" data-tool="marker" title="Marker Pin">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"></path><circle cx="12" cy="10" r="2.5"></circle></svg>
  </button>
  <button class="rail-btn tool" data-tool="textbox" title="Text Label">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 7 4 4 20 4 20 7"></polyline><line x1="9" y1="20" x2="15" y2="20"></line><line x1="12" y1="4" x2="12" y2="20"></line></svg>
  </button>
  <button class="rail-btn tool" data-tool="polyline" title="Draw Polyline">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"></path></svg>
  </button>
  <button class="rail-btn tool" data-tool="polygon" title="Draw Polygon">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l8 6-3 10H7L4 9z"></path></svg>
  </button>
  <button class="rail-btn tool" data-tool="rectangle" title="Draw Rectangle">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16"></rect></svg>
  </button>
  <button class="rail-btn tool" data-tool="circle" title="Draw Circle (with Radius)">
    <svg viewBox="0 0 24 24" width="16" height="16"><circle cx="12" cy="12" r="8" fill="currentColor"></circle></svg>
  </button>
  <button class="rail-btn tool" data-tool="route" title="Multi-Point Route">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="5" cy="19" r="2.5"></circle><circle cx="19" cy="5" r="2.5"></circle><path d="M7 17c4-1 3-8 8-9"></path></svg>
  </button>
  <div class="rail-sep"></div>
  <button class="rail-btn" id="btn-custom-map" title="Basemap & Vector Styling">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon><line x1="8" y1="2" x2="8" y2="18"></line><line x1="16" y1="6" x2="16" y2="22"></line></svg>
  </button>
  <button class="rail-btn" id="btn-edit-mode" title="Select, Drag & Edit Features">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4v16h16v-7"></path><path d="M18 2l4 4-10 10H8v-4z"></path></svg>
  </button>
  <button class="rail-btn" id="btn-clear-all" title="Clear All Drawings">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
  </button>
</div>

<!-- Flyout Data Browser Panel -->
<div id="browser-panel">
  <div class="panel-header">
    <div class="panel-title">
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"></path><path d="M2 12l10 6 10-6"></path><path d="M2 16l10 6 10-6"></path></svg>
      <span>Data browser</span>
    </div>
    <div class="panel-actions">
      <button class="icon-action-btn" id="btn-collapse-browser" title="Collapse Panel">‹</button>
      <button class="icon-action-btn" id="btn-close-browser" title="Close">✕</button>
    </div>
  </div>

  <div class="panel-content">
    <!-- Category: Data Layers -->
    <div class="acc-item">
      <div class="acc-header" data-target="body-data-layers">
        <span>Data Layers</span><span>▾</span>
      </div>
      <div class="acc-body" id="body-data-layers">
        <label class="layer-row"><span>Main Roads</span><input type="checkbox" data-g="main" checked></label>
        <label class="layer-row"><span>Secondary Roads</span><input type="checkbox" data-g="secondary" checked></label>
        <label class="layer-row"><span>Buildings</span><input type="checkbox" data-g="buildings" checked></label>
        <label class="layer-row"><span>Water</span><input type="checkbox" data-g="water" checked></label>
        <label class="layer-row"><span>Labels</span><input type="checkbox" data-g="labels" checked></label>
      </div>
    </div>

    <!-- Category: Custom Layers / Drawings -->
    <div class="layers-heading">
      <span>My Layers</span>
      <span class="badge-count" id="layer-badge-count">0</span>
    </div>
    <div id="my-layers-list">
      <div style="font-size:12px; color:#94a3b8; padding: 6px 0;">No drawings yet. Use the tools to create shapes.</div>
    </div>
  </div>
</div>

<!-- Search Panel Floating Card -->
<div id="popup-search" class="float-card">
  <input type="text" id="searchInput" placeholder="Search location (Press Enter)…" />
</div>

<!-- Marker Settings Card -->
<div id="popup-marker-settings" class="float-card">
  <div style="font-weight:600; font-size:11px; color:#64748b;">CHOOSE MARKER ICON</div>
  <div class="icon-grid" id="markerIconGrid"></div>
  <div class="f-row"><span>Icon Color</span><input type="color" id="mColor" value="#0f172a"></div>
</div>

<!-- Text Tool Configuration Card -->
<div id="popup-text-settings" class="float-card">
  <div style="font-weight:600; font-size:11px; color:#64748b;">TEXT CONFIGURATION</div>
  <input type="text" id="tContent" value="Custom Label" placeholder="Text content…"/>
  <div class="f-row"><span>Font</span>
    <select id="tFont" style="width:130px;">
      <option value="Century Gothic Custom" selected>Century Gothic</option>
      <option value="sans-serif">System Sans</option>
      <option value="serif">Serif</option>
      <option value="monospace">Monospace</option>
    </select>
  </div>
  <div class="f-row"><span>Font Size</span><input type="range" id="tSize" min="10" max="42" step="1" value="16"></div>
  <div class="f-row"><span>Color</span><input type="color" id="tColor" value="#0f172a"></div>
  <div class="f-row"><span>Opacity</span><input type="range" id="tOp" min="0.1" max="1" step="0.05" value="1"></div>
</div>

<!-- Feature Property / Polygon Customizer Editor Card -->
<div id="popup-shape-editor" class="float-card">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <span style="font-weight:700;" id="editShapeTitle">Edit Layer</span>
    <button class="card-btn" id="closeEditorBtn">✕</button>
  </div>
  <div class="f-row"><span>Name</span><input type="text" id="eName" style="width:140px;"></div>
  <div class="f-row" id="eColorRow"><span>Color</span><input type="color" id="eColor"></div>
  <div class="f-row" id="eWidthRow"><span>Thickness</span><input type="range" id="eWidth" min="1" max="16" step="1"></div>
  <div class="f-row" id="eOpRow"><span>Opacity</span><input type="range" id="eOp" min="0.05" max="1" step="0.05"></div>
  <div class="f-row" id="eFillColorRow"><span>Fill Color</span><input type="color" id="eFillColor"></div>
  <div class="f-row" id="eFillOpRow"><span>Fill Opacity</span><input type="range" id="eFillOp" min="0" max="1" step="0.05"></div>
  <div class="f-row" id="eTextRow" style="display:none;"><span>Text</span><input type="text" id="eTextVal" style="width:140px;"></div>
  <div class="f-row" id="eFontSizeRow" style="display:none;"><span>Size</span><input type="range" id="eFontSize" min="10" max="42" step="1"></div>
  <div style="display:flex; justify-content:space-between; margin-top:6px;">
    <button id="eDeleteBtn" style="color:#ef4444; border:1px solid #fecaca; background:#fef2f2; padding:5px 10px; border-radius:6px; cursor:pointer;">Delete</button>
    <button id="eDoneBtn" style="background:#0f172a; color:#fff; border:none; padding:5px 14px; border-radius:6px; cursor:pointer;">Save</button>
  </div>
</div>

<!-- Basemap Background & Vector Customizer Panel -->
<div id="popup-custom-map" class="float-card">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <span style="font-weight:700;">Vector & Basemap Style</span>
    <button class="card-btn" id="closeCustomMapBtn">✕</button>
  </div>
  <div style="font-weight:600; font-size:11px; color:#64748b; margin-top:4px;">BASEMAP PRESETS</div>
  <div style="display:flex; flex-wrap:wrap; gap:4px;" id="presetBtnList"></div>

  <div style="font-weight:600; font-size:11px; color:#64748b; margin-top:6px;">BACKGROUND</div>
  <div class="f-row"><span>Color</span><input type="color" id="cBgColor" value="#0a1628"></div>

  <div style="font-weight:600; font-size:11px; color:#64748b; margin-top:6px;">MAIN ROADS</div>
  <div class="f-row"><span>Color</span><input type="color" id="cMainColor" value="#e8b84a"></div>
  <div class="f-row"><span>Thickness</span><input type="range" id="cMainWidth" min="1" max="10" step="0.5" value="4"></div>
  <div class="f-row"><span>Opacity</span><input type="range" id="cMainOp" min="0" max="1" step="0.1" value="1"></div>

  <div style="font-weight:600; font-size:11px; color:#64748b; margin-top:6px;">SECONDARY ROADS</div>
  <div class="f-row"><span>Color</span><input type="color" id="cSecColor" value="#7d5f14"></div>
  <div class="f-row"><span>Thickness</span><input type="range" id="cSecWidth" min="0.5" max="8" step="0.5" value="3"></div>
  <div class="f-row"><span>Opacity</span><input type="range" id="cSecOp" min="0" max="1" step="0.1" value="0.7"></div>

  <div style="font-weight:600; font-size:11px; color:#64748b; margin-top:6px;">BUILDINGS</div>
  <div class="f-row"><span>Color</span><input type="color" id="cBldColor" value="#8e7258"></div>
  <div class="f-row"><span>Opacity</span><input type="range" id="cBldOp" min="0" max="1" step="0.05" value="0.25"></div>

  <div style="font-weight:600; font-size:11px; color:#64748b; margin-top:6px;">WATER</div>
  <div class="f-row"><span>Color</span><input type="color" id="cWaterColor" value="#0a1424"></div>
  <div class="f-row"><span>Opacity</span><input type="range" id="cWaterOp" min="0" max="1" step="0.1" value="1"></div>

  <div style="font-weight:600; font-size:11px; color:#64748b; margin-top:6px;">LABELS</div>
  <div class="f-row"><span>Color</span><input type="color" id="cLblColor" value="#d9b451"></div>
</div>

<div id="hint-toast"></div>
<div id="err"></div>

<script>
try {
const ALL_STYLES = __ALL_STYLES__;
let currentStyleName = "Midnight Blue";

const map = new maplibregl.Map({
  container: 'map',
  style: __STYLE__,
  center: __CENTER__,
  zoom: __ZOOM__,
  attributionControl: false,
  fadeDuration: 0
});
map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
map.getCanvas().addEventListener('contextmenu', e => e.preventDefault());

// ----------------- State Machine -----------------
let features = [], fid = 0;
let activeTool = null, editMode = false;
let draft = [], cursorLL = null, selectedId = null;
let markerShape = 'pin', markerColor = '#0f172a';

const textSettings = {
  content: 'Custom Label',
  font: 'Century Gothic Custom',
  size: 16,
  color: '#0f172a',
  opacity: 1.0
};

// Dragging feature state
let isDragging = false, dragFeatureId = null, dragStartCoord = null, dragOriginalCoords = null;

const vis = { main: true, secondary: true, buildings: true, water: true, labels: true };
const VIS_MAP = {
  main: ['case_major_casing', 'rd_major'],
  secondary: ['case_minhi_casing', 'rd_min_hi', 'rd_min_md', 'rd_min_lo', 'rd_path'],
  buildings: ['building'],
  water: ['water', 'waterway'],
  labels: ['label_place']
};

const $ = id => document.getElementById(id);
const hint = t => { $('hint-toast').style.display = t ? 'block' : 'none'; $('hint-toast').textContent = t || ''; };

const closeFloatingCards = () => {
  ['popup-marker-settings','popup-text-settings','popup-shape-editor','popup-custom-map','popup-search'].forEach(id => $(id).classList.remove('open'));
};

// ----------------- Marker Canvas Icon Pipeline -----------------
function renderIconCanvas(shape, color) {
  const c = document.createElement('canvas');
  c.width = 64; c.height = 64;
  const ctx = c.getContext('2d');
  ctx.clearRect(0,0,64,64);
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 3;
  ctx.fillStyle = color;
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';

  ctx.beginPath();
  if (shape === 'pin') {
    ctx.arc(32, 24, 16, Math.PI * 0.8, Math.PI * 0.2, false);
    ctx.lineTo(32, 58);
    ctx.closePath();
  } else if (shape === 'star') {
    for (let i = 0; i < 10; i++) {
      const r = i % 2 ? 12 : 26, a = -Math.PI / 2 + i * Math.PI / 5;
      const px = 32 + r * Math.cos(a), py = 32 + r * Math.sin(a);
      i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
    }
    ctx.closePath();
  } else if (shape === 'circle') {
    ctx.arc(32, 32, 22, 0, Math.PI * 2);
  } else if (shape === 'square') {
    ctx.rect(12, 12, 40, 40);
  } else if (shape === 'flag') {
    ctx.moveTo(18, 58); ctx.lineTo(18, 10); ctx.lineTo(48, 22); ctx.lineTo(18, 34);
  } else if (shape === 'heart') {
    ctx.moveTo(32, 54);
    ctx.bezierCurveTo(6, 34, 14, 10, 32, 22);
    ctx.bezierCurveTo(50, 10, 58, 34, 32, 54);
  }
  ctx.fill(); ctx.stroke();

  // Draw inner contrasting dot
  ctx.beginPath();
  ctx.fillStyle = '#ffffff';
  ctx.arc(32, shape === 'pin' ? 24 : 32, 5, 0, Math.PI * 2);
  ctx.fill();
  return c;
}

function getIconKey(shape, color) {
  const key = `ico_${shape}_${color.replace('#','')}`;
  if (!map.hasImage(key)) {
    const cv = renderIconCanvas(shape, color);
    const imgData = cv.getContext('2d').getImageData(0,0,64,64);
    try { map.addImage(key, imgData, { pixelRatio: 2 }); } catch(e) {}
  }
  return key;
}

const ICON_SVGS = {
  pin: '<path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"></path><circle cx="12" cy="10" r="2.5"></circle>',
  star: '<path d="M12 2l2.9 6.3 6.9.8-5.1 4.7 1.4 6.8-6.1-3.4-6.1 3.4 1.4-6.8L2.2 9.1l6.9-.8z"></path>',
  circle: '<circle cx="12" cy="12" r="8"></circle>',
  square: '<rect x="5" y="5" width="14" height="14"></rect>',
  flag: '<path d="M6 21V4"></path><path d="M6 4l12 3-12 3"></path>',
  heart: '<path d="M12 20s-7-4.6-7-10a4 4 0 0 1 7-2.5A4 4 0 0 1 19 10c0 5.4-7 10-7 10z"></path>'
};

$('markerIconGrid').innerHTML = Object.keys(ICON_SVGS).map(s =>
  `<button data-s="${s}" class="${s === markerShape ? 'active' : ''}">
     <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">${ICON_SVGS[s]}</svg>
   </button>`).join('');

$('markerIconGrid').querySelectorAll('button').forEach(b => b.onclick = () => {
  markerShape = b.dataset.s;
  $('markerIconGrid').querySelectorAll('button').forEach(x => x.classList.toggle('active', x === b));
});
$('mColor').oninput = e => { markerColor = e.target.value; };

// ----------------- Vector Layers Pipeline -----------------
const fc = list => ({
  type: 'FeatureCollection',
  features: list.map(f => ({
    type: 'Feature',
    geometry: f.geometry,
    properties: Object.assign({ id: f.id, name: f.name, kind: f.kind }, f.props)
  }))
});

function addDrawStack() {
  if (!map.getSource('draw')) {
    map.addSource('draw', { type: 'geojson', data: fc(features) });

    // Polygon Fills
    map.addLayer({
      id: 'draw-fill', type: 'fill', source: 'draw',
      filter: ['==', ['geometry-type'], 'Polygon'],
      paint: {
        'fill-color': ['coalesce', ['get', 'fillColor'], ['get', 'color'], '#0f172a'],
        'fill-opacity': ['*', ['coalesce', ['get', 'fillOpacity'], 0.35], ['get', 'visible']]
      }
    });

    // Polygon Outlines
    map.addLayer({
      id: 'draw-outline', type: 'line', source: 'draw',
      filter: ['==', ['geometry-type'], 'Polygon'],
      paint: {
        'line-color': ['coalesce', ['get', 'color'], '#0f172a'],
        'line-width': ['coalesce', ['get', 'width'], 3],
        'line-opacity': ['*', ['coalesce', ['get', 'opacity'], 0.9], ['get', 'visible']]
      }
    });

    // Polylines / Routes
    map.addLayer({
      id: 'draw-line', type: 'line', source: 'draw',
      filter: ['==', ['geometry-type'], 'LineString'],
      layout: { 'line-cap': 'round', 'line-join': 'round' },
      paint: {
        'line-color': ['coalesce', ['get', 'color'], '#0f172a'],
        'line-width': ['coalesce', ['get', 'width'], 4],
        'line-opacity': ['*', ['coalesce', ['get', 'opacity'], 0.9], ['get', 'visible']]
      }
    });

    // Marker Pins
    map.addLayer({
      id: 'draw-marker', type: 'symbol', source: 'draw',
      filter: ['all', ['==', ['geometry-type'], 'Point'], ['!=', ['get', 'kind'], 'text']],
      layout: {
        'icon-image': ['get', 'iconKey'],
        'icon-size': 0.8,
        'icon-allow-overlap': true,
        'icon-anchor': 'bottom'
      },
      paint: { 'icon-opacity': ['get', 'visible'] }
    });

    // Custom Text Labels
    map.addLayer({
      id: 'draw-text', type: 'symbol', source: 'draw',
      filter: ['all', ['==', ['geometry-type'], 'Point'], ['==', ['get', 'kind'], 'text']],
      layout: {
        'text-field': ['get', 'text'],
        'text-font': ['Noto Sans Regular'],
        'text-size': ['coalesce', ['get', 'fontSize'], 16],
        'text-allow-overlap': true,
        'text-anchor': 'center'
      },
      paint: {
        'text-color': ['coalesce', ['get', 'color'], '#0f172a'],
        'text-opacity': ['*', ['coalesce', ['get', 'opacity'], 1], ['get', 'visible']],
        'text-halo-color': '#ffffff',
        'text-halo-width': 2
      }
    });
  } else {
    map.getSource('draw').setData(fc(features));
  }

  // Live Construction Draft Preview Source
  if (!map.getSource('draft')) {
    map.addSource('draft', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addLayer({
      id: 'draft-line', type: 'line', source: 'draft',
      filter: ['==', ['geometry-type'], 'LineString'],
      paint: { 'line-color': '#0f172a', 'line-width': 2, 'line-dasharray': [2, 2] }
    });
    map.addLayer({
      id: 'draft-point', type: 'circle', source: 'draft',
      filter: ['==', ['geometry-type'], 'Point'],
      paint: { 'circle-color': '#0f172a', 'circle-radius': 4, 'circle-stroke-color': '#ffffff', 'circle-stroke-width': 2 }
    });
  }
}

const syncDraw = () => { if (map.getSource('draw')) map.getSource('draw').setData(fc(features)); };

function renderDraft() {
  if (!map.getSource('draft')) return;
  const f = [];
  const pt = c => ({ type: 'Feature', geometry: { type: 'Point', coordinates: c }, properties: {} });
  const ln = c => ({ type: 'Feature', geometry: { type: 'LineString', coordinates: c }, properties: {} });

  draft.forEach(p => f.push(pt(p)));

  if ((activeTool === 'polyline' || activeTool === 'route') && draft.length) {
    f.push(ln(cursorLL ? [...draft, cursorLL] : draft));
  }
  if (activeTool === 'polygon' && draft.length) {
    const pts = cursorLL ? [...draft, cursorLL] : draft;
    if (pts.length > 1) f.push(ln([...pts, pts[0]]));
  }
  if (activeTool === 'rectangle' && draft.length === 1 && cursorLL) {
    f.push(ln(rectCoords(draft[0], cursorLL)[0]));
  }
  if (activeTool === 'circle' && draft.length === 1 && cursorLL) {
    const { coords, r } = circleCoords(draft[0], cursorLL);
    f.push(ln(coords[0]));
    const distText = r > 1000 ? `${(r/1000).toFixed(2)} km` : `${Math.round(r)} m`;
    hint(`Radius: ${distText} · Click to finalize`);
  }
  map.getSource('draft').setData({ type: 'FeatureCollection', features: f });
}

function applyVis() {
  for (const g in VIS_MAP) {
    VIS_MAP[g].forEach(id => {
      if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', vis[g] ? 'visible' : 'none');
    });
  }
}

map.on('load', () => { addDrawStack(); applyVis(); });

// ----------------- Geometry Utilities -----------------
function haversineDist(a, b) {
  const R = 6371000, dLa = (b[1]-a[1]) * Math.PI/180, dLo = (b[0]-a[0]) * Math.PI/180;
  const s = Math.sin(dLa/2)**2 + Math.cos(a[1]*Math.PI/180) * Math.cos(b[1]*Math.PI/180) * Math.sin(dLo/2)**2;
  return 2 * R * Math.asin(Math.sqrt(s));
}

function rectCoords(a, b) {
  return [[[a[0],a[1]],[a[0],b[1]],[b[0],b[1]],[b[0],a[1]],[a[0],a[1]]]];
}

function circleCoords(c, edge) {
  const r = haversineDist(c, edge), coords = [];
  for (let i = 0; i <= 64; i++) {
    const a = (i / 64) * 2 * Math.PI;
    coords.push([
      c[0] + (r / (111320 * Math.cos(c[1]*Math.PI/180))) * Math.cos(a),
      c[1] + (r / 111320) * Math.sin(a)
    ]);
  }
  return { coords: [coords], r };
}

function fetchMultiPointRoute(pts) {
  hint('Calculating routing paths…');
  const coordStr = pts.map(p => `${p[0]},${p[1]}`).join(';');
  fetch(`https://router.project-osrm.org/route/v1/driving/${coordStr}?overview=full&geometries=geojson`)
    .then(r => r.json())
    .then(j => {
      const geom = (j.routes && j.routes[0]) ? j.routes[0].geometry : { type: 'LineString', coordinates: pts };
      addFeatureRecord('route', geom, { color: '#0f172a', width: 4, opacity: 0.9 });
      hint('');
    })
    .catch(() => {
      addFeatureRecord('route', { type: 'LineString', coordinates: pts }, { color: '#0f172a', width: 3, opacity: 0.8 });
      hint('OSRM direct line connection fallback');
    });
}

function addFeatureRecord(kind, geometry, customProps = {}) {
  const newId = ++fid;
  const feat = {
    id: newId,
    name: `${kind.charAt(0).toUpperCase() + kind.slice(1)} ${newId}`,
    kind: kind,
    geometry: geometry,
    props: {
      color: '#0f172a',
      width: 3,
      opacity: 0.9,
      fillColor: '#0f172a',
      fillOpacity: 0.3,
      visible: 1,
      ...customProps
    }
  };
  features.push(feat);
  syncDraw();
  renderMyLayers();
  return feat;
}

// ----------------- Tool Handlers & Drawing Engine -----------------
document.querySelectorAll('.tool').forEach(btn => {
  btn.onclick = () => {
    const t = btn.dataset.tool;
    if (activeTool === t) {
      activeTool = null;
      btn.classList.remove('primary-active');
      closeFloatingCards();
      hint('');
    } else {
      document.querySelectorAll('.tool').forEach(b => b.classList.remove('primary-active'));
      $('btn-edit-mode').classList.remove('primary-active');
      editMode = false;
      closeFloatingCards();

      activeTool = t;
      btn.classList.add('primary-active');
      draft = [];
      renderDraft();

      if (t === 'marker') $('popup-marker-settings').classList.add('open');
      if (t === 'textbox') $('popup-text-settings').classList.add('open');

      if (t === 'polyline') hint('Click points · Right-click: undo · Double-click / Enter: finish');
      if (t === 'polygon') hint('Click polygon vertices · Right-click: undo · Double-click / Enter: close');
      if (t === 'rectangle') hint('Click 1st corner, then opposite corner');
      if (t === 'circle') hint('Click circle center, then outer edge');
      if (t === 'route') hint('Click route points A, B, C… Double-click last point to finish route');
    }
  };
});

map.on('mousemove', e => {
  cursorLL = [e.lngLat.lng, e.lngLat.lat];
  if (activeTool) renderDraft();

  // Handling feature dragging
  if (isDragging && dragFeatureId) {
    const dx = cursorLL[0] - dragStartCoord[0];
    const dy = cursorLL[1] - dragStartCoord[1];
    const f = features.find(x => x.id === dragFeatureId);
    if (!f) return;

    const translateCoords = coords => {
      if (typeof coords[0] === 'number') return [coords[0] + dx, coords[1] + dy];
      return coords.map(translateCoords);
    };
    f.geometry.coordinates = translateCoords(dragOriginalCoords);
    syncDraw();
  }
});

map.on('click', e => {
  if (editMode) {
    const fs = map.queryRenderedFeatures(e.point, { layers: ['draw-fill','draw-line','draw-outline','draw-marker','draw-text'] });
    if (fs.length && fs[0].properties.id != null) {
      openShapeEditor(parseInt(fs[0].properties.id, 10));
    }
    return;
  }
  if (!activeTool) return;
  const ll = [e.lngLat.lng, e.lngLat.lat];

  if (activeTool === 'marker') {
    addFeatureRecord('marker', { type: 'Point', coordinates: ll }, {
      shape: markerShape,
      color: markerColor,
      iconKey: getIconKey(markerShape, markerColor)
    });
  } else if (activeTool === 'textbox') {
    addFeatureRecord('text', { type: 'Point', coordinates: ll }, {
      text: $('tContent').value || 'Label',
      fontSize: parseInt($('tSize').value, 10),
      color: $('tColor').value,
      opacity: parseFloat($('tOp').value)
    });
  } else if (activeTool === 'polyline' || activeTool === 'polygon') {
    draft.push(ll);
  } else if (activeTool === 'rectangle') {
    draft.push(ll);
    if (draft.length === 2) {
      addFeatureRecord('rectangle', { type: 'Polygon', coordinates: rectCoords(draft[0], draft[1]) });
      draft = [];
      renderDraft();
    }
  } else if (activeTool === 'circle') {
    draft.push(ll);
    if (draft.length === 2) {
      const { coords, r } = circleCoords(draft[0], draft[1]);
      addFeatureRecord('circle', { type: 'Polygon', coordinates: coords }, { radiusMeters: r });
      draft = [];
      renderDraft();
      hint('');
    }
  } else if (activeTool === 'route') {
    draft.push(ll);
  }
  renderDraft();
});

map.on('dblclick', () => {
  if (activeTool === 'polyline' && draft.length >= 2) {
    draft.pop();
    addFeatureRecord('polyline', { type: 'LineString', coordinates: draft });
    draft = []; renderDraft(); hint('');
  } else if (activeTool === 'polygon' && draft.length >= 3) {
    draft.pop();
    addFeatureRecord('polygon', { type: 'Polygon', coordinates: [[...draft, draft[0]]] });
    draft = []; renderDraft(); hint('');
  } else if (activeTool === 'route' && draft.length >= 2) {
    draft.pop();
    fetchMultiPointRoute(draft);
    draft = []; renderDraft();
  }
});

map.on('contextmenu', () => {
  if (!activeTool) return;
  if (draft.length) { draft.pop(); renderDraft(); }
});

document.addEventListener('keydown', e => {
  if (/INPUT|TEXTAREA|SELECT/.test(e.target.tagName)) return;
  if (e.key === 'Enter') map.fire('dblclick');
  if (e.key === 'Escape') {
    draft = []; renderDraft(); closeFloatingCards();
    document.querySelectorAll('.tool').forEach(b => b.classList.remove('primary-active'));
    activeTool = null; hint('');
  }
});

// ----------------- Edit & Drag Engine -----------------
$('btn-edit-mode').onclick = () => {
  editMode = !editMode;
  $('btn-edit-mode').classList.toggle('primary-active', editMode);
  activeTool = null;
  document.querySelectorAll('.tool').forEach(b => b.classList.remove('primary-active'));
  closeFloatingCards();
  hint(editMode ? 'Drag any drawing to move it · Click pencil in My Layers to edit properties' : '');
};

map.on('mousedown', e => {
  if (!editMode) return;
  const fs = map.queryRenderedFeatures(e.point, { layers: ['draw-fill','draw-line','draw-outline','draw-marker','draw-text'] });
  if (fs.length && fs[0].properties.id != null) {
    isDragging = true;
    dragFeatureId = parseInt(fs[0].properties.id, 10);
    dragStartCoord = [e.lngLat.lng, e.lngLat.lat];
    const f = features.find(x => x.id === dragFeatureId);
    if (f) dragOriginalCoords = JSON.parse(JSON.stringify(f.geometry.coordinates));
    map.dragPan.disable();
  }
});

map.on('mouseup', () => {
  if (isDragging) {
    isDragging = false;
    dragFeatureId = null;
    map.dragPan.enable();
  }
});

// ----------------- Feature Customizer / Shape Editor -----------------
function openShapeEditor(id) {
  const f = features.find(x => x.id === id);
  if (!f) return;
  selectedId = id;
  $('editShapeTitle').textContent = `Edit ${f.name}`;
  $('eName').value = f.name;
  $('eColor').value = f.props.color || '#0f172a';
  $('eWidth').value = f.props.width || 3;
  $('eOp').value = f.props.opacity != null ? f.props.opacity : 0.9;
  $('eFillColor').value = f.props.fillColor || f.props.color || '#0f172a';
  $('eFillOp').value = f.props.fillOpacity != null ? f.props.fillOpacity : 0.3;

  const isText = f.kind === 'text';
  $('eTextRow').style.display = isText ? 'flex' : 'none';
  $('eFontSizeRow').style.display = isText ? 'flex' : 'none';
  if (isText) {
    $('eTextVal').value = f.props.text || '';
    $('eFontSize').value = f.props.fontSize || 16;
  }

  const isPolygon = ['polygon', 'rectangle', 'circle'].includes(f.kind);
  $('eFillColorRow').style.display = isPolygon ? 'flex' : 'none';
  $('eFillOpRow').style.display = isPolygon ? 'flex' : 'none';

  $('popup-shape-editor').classList.add('open');
}

$('eName').oninput = e => {
  const f = features.find(x => x.id === selectedId);
  if (f) { f.name = e.target.value; renderMyLayers(); }
};
$('eColor').oninput = e => {
  const f = features.find(x => x.id === selectedId);
  if (!f) return;
  f.props.color = e.target.value;
  if (f.kind === 'marker') f.props.iconKey = getIconKey(f.props.shape || 'pin', e.target.value);
  syncDraw();
};
$('eWidth').oninput = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.width = parseFloat(e.target.value); syncDraw(); } };
$('eOp').oninput = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.opacity = parseFloat(e.target.value); syncDraw(); } };
$('eFillColor').oninput = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.fillColor = e.target.value; syncDraw(); } };
$('eFillOp').oninput = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.fillOpacity = parseFloat(e.target.value); syncDraw(); } };
$('eTextVal').oninput = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.text = e.target.value; syncDraw(); renderMyLayers(); } };
$('eFontSize').oninput = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.fontSize = parseInt(e.target.value, 10); syncDraw(); } };

$('eDeleteBtn').onclick = () => {
  features = features.filter(x => x.id !== selectedId);
  syncDraw();
  renderMyLayers();
  $('popup-shape-editor').classList.remove('open');
};
$('eDoneBtn').onclick = () => { $('popup-shape-editor').classList.remove('open'); };
$('closeEditorBtn').onclick = () => { $('popup-shape-editor').classList.remove('open'); };

// ----------------- My Layers Rendering Pipeline -----------------
function renderMyLayers() {
  const container = $('my-layers-list');
  $('layer-badge-count').textContent = features.length;

  if (!features.length) {
    container.innerHTML = '<div style="font-size:12px; color:#94a3b8; padding:6px 0;">No drawings yet. Use the tools to create shapes.</div>';
    return;
  }

  container.innerHTML = features.slice().reverse().map(f => {
    let subInfo = f.kind;
    if (f.kind === 'circle' && f.props.radiusMeters) {
      subInfo = `Radius: ${f.props.radiusMeters > 1000 ? (f.props.radiusMeters/1000).toFixed(2)+' km' : Math.round(f.props.radiusMeters)+' m'}`;
    }
    return `
      <div class="layer-card">
        <div class="layer-card-top">
          <input class="layer-name-input" data-id="${f.id}" value="${f.name}" title="Click to rename" />
          <button class="card-btn" data-act="edit" data-id="${f.id}" title="Edit Properties">✎</button>
          <button class="card-btn" data-act="eye" data-id="${f.id}" title="Toggle Visibility">${f.props.visible ? '👁' : '–'}</button>
          <button class="card-btn" data-act="zoom" data-id="${f.id}" title="Zoom To">⤢</button>
          <button class="card-btn" data-act="del" data-id="${f.id}" title="Delete">✕</button>
        </div>
        <div style="font-size:11px; color:#64748b; padding-left:4px;">${subInfo}</div>
      </div>
    `;
  }).join('');

  container.querySelectorAll('.layer-name-input').forEach(inp => {
    inp.onchange = e => {
      const id = parseInt(e.target.dataset.id, 10);
      const f = features.find(x => x.id === id);
      if (f) { f.name = e.target.value; syncDraw(); }
    };
  });

  container.querySelectorAll('button[data-act]').forEach(b => {
    b.onclick = () => {
      const id = parseInt(b.dataset.id, 10);
      const act = b.dataset.act;
      const f = features.find(x => x.id === id);
      if (!f) return;
      if (act === 'edit') openShapeEditor(id);
      if (act === 'eye') { f.props.visible = f.props.visible ? 0 : 1; syncDraw(); renderMyLayers(); }
      if (act === 'del') { features = features.filter(x => x.id !== id); syncDraw(); renderMyLayers(); }
      if (act === 'zoom') {
        const bnd = calcBounds(f);
        if (bnd) map.fitBounds(bnd, { padding: 60, maxZoom: 17 });
      }
    };
  });
}

function calcBounds(f) {
  let minX = 1e9, minY = 1e9, maxX = -1e9, maxY = -1e9, ok = false;
  const walk = c => {
    if (typeof c[0] === 'number') {
      ok = true;
      minX = Math.min(minX, c[0]); maxX = Math.max(maxX, c[0]);
      minY = Math.min(minY, c[1]); maxY = Math.max(maxY, c[1]);
    } else c.forEach(walk);
  };
  walk(f.geometry.coordinates);
  if (!ok) return null;
  if (minX === maxX && minY === maxY) return [[minX - 0.005, minY - 0.005], [maxX + 0.005, maxY + 0.005]];
  return [[minX, minY], [maxX, maxY]];
}

// ----------------- UI / Rail / Accordion Controls -----------------
$('btn-browser-toggle').onclick = () => {
  $('browser-panel').classList.toggle('collapsed');
};
$('btn-collapse-browser').onclick = () => { $('browser-panel').classList.add('collapsed'); };
$('btn-close-browser').onclick = () => { $('browser-panel').classList.add('collapsed'); };

document.querySelectorAll('.acc-header').forEach(h => {
  h.onclick = () => {
    const body = $(h.dataset.target);
    body.classList.toggle('hidden');
    h.querySelector('span:last-child').textContent = body.classList.contains('hidden') ? '▸' : '▾';
  };
});

document.querySelectorAll('#body-data-layers input[data-g]').forEach(cb => {
  cb.onchange = () => {
    vis[cb.dataset.g] = cb.checked;
    applyVis();
  };
});

// Search bar toggle
$('btn-search').onclick = () => {
  const p = $('popup-search');
  p.classList.toggle('open');
  if (p.classList.contains('open')) $('searchInput').focus();
};
$('searchInput').addEventListener('keydown', e => {
  if (e.key !== 'Enter') return;
  const q = e.target.value.trim();
  if (!q) return;
  hint('Searching location…');
  fetch(`https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(q)}`)
    .then(r => r.json())
    .then(j => {
      if (j.length) {
        map.flyTo({ center: [parseFloat(j[0].lon), parseFloat(j[0].lat)], zoom: 15 });
        hint('');
        $('popup-search').classList.remove('open');
      } else { hint('Location not found'); }
    })
    .catch(() => hint('Search request failed'));
});

// Basemap vector customizer
$('btn-custom-map').onclick = () => { $('popup-custom-map').classList.toggle('open'); };
$('closeCustomMapBtn').onclick = () => { $('popup-custom-map').classList.remove('open'); };

$('presetBtnList').innerHTML = Object.keys(ALL_STYLES).map(n =>
  `<button style="border:1px solid #e2e8f0; background:#f8fafc; border-radius:4px; padding:4px 8px; font-size:11px; cursor:pointer;" data-n="${n}">${n}</button>`
).join('');

$('presetBtnList').querySelectorAll('button').forEach(b => {
  b.onclick = () => {
    currentStyleName = b.dataset.n;
    map.setStyle(ALL_STYLES[currentStyleName]);
    map.once('idle', () => { addDrawStack(); applyVis(); });
  };
});

const setMapPaint = (id, prop, val) => { if (map.getLayer(id)) map.setPaintProperty(id, prop, val); };
$('cBgColor').oninput = e => setMapPaint('bg', 'background-color', e.target.value);
$('cMainColor').oninput = e => setMapPaint('rd_major', 'line-color', e.target.value);
$('cMainWidth').oninput = e => setMapPaint('rd_major', 'line-width', parseFloat(e.target.value));
$('cMainOp').oninput = e => setMapPaint('rd_major', 'line-opacity', parseFloat(e.target.value));
$('cSecColor').oninput = e => ['rd_min_hi','rd_min_md','rd_min_lo','rd_path'].forEach(id => setMapPaint(id, 'line-color', e.target.value));
$('cSecWidth').oninput = e => ['rd_min_hi','rd_min_md'].forEach(id => setMapPaint(id, 'line-width', parseFloat(e.target.value)));
$('cSecOp').oninput = e => ['rd_min_hi','rd_min_md','rd_min_lo','rd_path'].forEach(id => setMapPaint(id, 'line-opacity', parseFloat(e.target.value)));
$('cBldColor').oninput = e => { setMapPaint('building', 'fill-color', e.target.value); setMapPaint('building', 'fill-outline-color', e.target.value); };
$('cBldOp').oninput = e => setMapPaint('building', 'fill-opacity', parseFloat(e.target.value));
$('cWaterColor').oninput = e => { setMapPaint('water', 'fill-color', e.target.value); setMapPaint('waterway', 'line-color', e.target.value); };
$('cWaterOp').oninput = e => { setMapPaint('water', 'fill-opacity', parseFloat(e.target.value)); setMapPaint('waterway', 'line-opacity', parseFloat(e.target.value)); };
$('cLblColor').oninput = e => setMapPaint('label_place', 'text-color', e.target.value);

$('btn-clear-all').onclick = () => {
  features = [];
  draft = [];
  renderDraft();
  syncDraw();
  renderMyLayers();
  closeFloatingCards();
};

map.on('error', e => console.warn('Map Notice:', e));
} catch (e) {
  const box = document.getElementById('err');
  box.style.display = 'block';
  box.textContent = 'App init error: ' + e.message;
}
</script>
</body>
</html>"""

try:
    body_bg = THEMES[INITIAL_BASEMAP]["overlay"]
    muted = THEMES[INITIAL_BASEMAP]["muted"]
    html = (
        HTML_TEMPLATE.replace("__ALL_STYLES__", json.dumps(ALL_STYLES))
        .replace("__STYLE__", json.dumps(ALL_STYLES[INITIAL_BASEMAP]))
        .replace("__CENTER__", json.dumps(CENTER))
        .replace("__ZOOM__", str(ZOOM))
        .replace("__BG__", body_bg)
        .replace("__MUTED__", muted)
    )
    components.html(html, height=1000, scrolling=False)
except Exception as e:
    st.error(f"Studio failed to load: {e}")

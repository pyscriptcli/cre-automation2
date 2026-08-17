import json
import streamlit as st
import streamlit.components.v1 as components

# ------------------------------------------------------------------------
# 1. PAGE CONFIGURATION (no sidebar — all controls live in the map toolbar)
# ------------------------------------------------------------------------
st.set_page_config(page_title="Open Map Builder", page_icon="🗺️",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .block-container { padding: 0rem !important; max-width: 100% !important; }
    header { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
    [data-testid="stCollapsedControl"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------
# 2. THEME PALETTES & STYLE BUILDERS
# ------------------------------------------------------------------------
CENTER = [121.0359, 14.5794]
ZOOM = 14

THEMES = {
    "Midnight Blue": {
        "overlay": "#0a1628", "text": "#d9b451", "land": "#0d1830",
        "landcover": "#0f1d33", "water": "#0a1424", "waterway": "#081120",
        "parks": "#142440", "buildings": "#8e7258", "aeroway": "#152640",
        "rail": "#d9b451", "rd_major": "#e8b84a", "rd_min_hi": "#7d5f14",
        "rd_min_md": "#46463e", "rd_min_lo": "#2f2f2a", "rd_path": "#4a4333",
        "rd_case": "#685c37", "sec_opacity": 0.7,
        "building_opacity": 0.07, "muted": "#8b949e",
    },
    "White Gold": {
        "overlay": "#ffffff", "text": "#a07d1c", "land": "#fafafa",
        "landcover": "#f1f1ec", "water": "#d4dadc", "waterway": "#c2c9cc",
        "parks": "#e6ebe4", "buildings": "#d8d8d4", "aeroway": "#e4e4e4",
        "rail": "#c99c37", "rd_major": "#e5a91d", "rd_min_hi": "#9c7a1a",
        "rd_min_md": "#e0be74", "rd_min_lo": "#ead9b0", "rd_path": "#e6dabd",
        "rd_case": "#b08a24", "sec_opacity": 0.6,
        "building_opacity": 0.5, "muted": "#6b7280",
    },
}

def w(*stops):
    out = ["interpolate", ["exponential", 1.2], ["zoom"]]
    for z, val in stops:
        out += [z, val]
    return out

def road_layer(p, lid, classes, color, widths, minzoom=0, casing=False, opacity=1.0):
    lyr = {
        "id": lid, "type": "line", "source": "omt", "source-layer": "transportation",
        "filter": ["match", ["get", "class"], classes, True, False],
        "layout": {"line-cap": "round", "line-join": "round"},
        "paint": {"line-color": color, "line-width": w(*widths), "line-opacity": opacity},
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
        "glyphs": "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
        "sources": {"omt": {"type": "vector", "url": "https://tiles.openfreemap.org/planet"}},
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
             "paint": {"fill-color": p["buildings"], "fill-opacity": p["building_opacity"],
                        "fill-outline-color": p["buildings"]}},
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
            {"id": "label_place", "type": "symbol", "source": "omt", "source-layer": "place",
             "minzoom": 6,
             "layout": {
                 "text-field": ["coalesce", ["get", "name_en"], ["get", "name"]],
                 "text-font": ["Noto Sans Regular"],
                 "text-size": ["interpolate", ["linear"], ["zoom"], 6, 10, 12, 14, 16, 18],
                 "text-transform": "uppercase", "text-letter-spacing": 0.05,
                 "text-max-width": 8,
             },
             "paint": {"text-color": p["text"], "text-halo-color": p["overlay"],
                        "text-halo-width": 1.5}},
        ],
    }

def raster_style(tile_urls, bg, maxzoom=20):
    return {
        "version": 8,
        "sources": {"r": {"type": "raster", "tiles": tile_urls, "tileSize": 256, "maxzoom": maxzoom}},
        "layers": [
            {"id": "bg", "type": "background", "paint": {"background-color": bg}},
            {"id": "r", "type": "raster", "source": "r"},
        ],
    }

ALL_STYLES = {
    "Midnight Blue": vector_style(THEMES["Midnight Blue"]),
    "White Gold": vector_style(THEMES["White Gold"]),
    "Carto DB Light": raster_style(
        ["https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
         "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"], "#f8f9fa"),
    "Carto DB Dark": raster_style(
        ["https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
         "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"], "#000000"),
    "OSM": raster_style(["https://tile.openstreetmap.org/{z}/{x}/{y}.png"], "#f2efe9", 19),
    "Satellite": raster_style(
        ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
        "#000000", 19),
}

# ------------------------------------------------------------------------
# 3. MAP + TOOLBAR RENDERER
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
          font: 10px sans-serif; color: __MUTED__; pointer-events: none; }
  #toolbar { position: absolute; top: 10px; left: 50%; transform: translateX(-50%);
             z-index: 3; display: flex; align-items: center; gap: 2px;
             background: #161b22ee; border: 1px solid #30363d; border-radius: 10px; padding: 4px; }
  #toolbar button { width: 28px; height: 28px; display: grid; place-items: center;
                    background: transparent; border: none; color: #c9d1d9;
                    border-radius: 6px; cursor: pointer; }
  #toolbar button:hover { background: #21262d; color: #f0f6fc; }
  #toolbar button.active { background: #c99c37; color: #0a1628; }
  .tsep { width: 1px; height: 18px; background: #30363d; margin: 0 3px; }
  .panelbox { position: absolute; top: 52px; left: 50%; transform: translateX(-50%);
              z-index: 3; background: #161b22f2; border: 1px solid #30363d;
              border-radius: 10px; padding: 10px; display: none; flex-direction: column;
              gap: 6px; font: 12px sans-serif; color: #f0f6fc; min-width: 200px;
              max-height: 70vh; overflow-y: auto; }
  .panelbox.open { display: flex; }
  .panelbox .row { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
  .panelbox input[type=range] { width: 100px; accent-color: #c99c37; }
  .panelbox button { background: #21262d; color: #f0f6fc; border: 1px solid #30363d;
                     border-radius: 6px; padding: 4px 8px; cursor: pointer; font: 11px sans-serif; }
  #editor, #markerOpts { left: auto; transform: none; right: 10px; }
  .ph { font: 11px sans-serif; color: #8b949e; text-transform: uppercase;
        letter-spacing: .06em; margin-top: 4px; }
  #searchBox input { width: 100%; box-sizing: border-box; background: #0d1117;
                     color: #f0f6fc; border: 1px solid #30363d; border-radius: 6px; padding: 6px; }
  .srow { display: flex; align-items: center; gap: 4px; }
  .srow .sname { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .srow button { padding: 2px 6px !important; }
  .shp { width: 24px; height: 24px; display: grid; place-items: center; cursor: pointer;
         background: #21262d; border: 1px solid #30363d; border-radius: 6px; color: #c9d1d9; }
  .shp.active { background: #c99c37; color: #0a1628; border-color: #c99c37; }
  .shprow { display: flex; gap: 4px; }
  #hint { position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%);
          z-index: 2; background: #161b22cc; color: #d9b451; border: 1px solid #30363d;
          border-radius: 6px; padding: 4px 10px; font: 11px sans-serif; display: none; }
  #err { display: none; position: absolute; top: 10px; left: 10px; z-index: 4;
         background: #3d1111; color: #ffb4b4; padding: 8px 12px; border-radius: 6px;
         font: 12px monospace; }
</style>
</head>
<body>
<div id="map"></div>
<div id="attr">© OpenStreetMap contributors · OpenFreeMap · OSRM · Nominatim</div>

<div id="toolbar">
  <button id="db-toggle" title="Manage layers & shapes"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"></path><path d="M2 12l10 6 10-6"></path><path d="M2 16l10 6 10-6"></path></svg></button>
  <div class="tsep"></div>
  <button id="searchbtn" title="Search"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"></circle><line x1="21" y1="21" x2="16.5" y2="16.5"></line></svg></button>
  <button class="tool" data-tool="marker" title="Place marker"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"></path><circle cx="12" cy="10" r="2.5"></circle></svg></button>
  <button class="tool" data-tool="polyline" title="Draw line"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"></path></svg></button>
  <button class="tool" data-tool="polygon" title="Draw polygon"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l8 6-3 10H7L4 9z"></path></svg></button>
  <button class="tool" data-tool="rectangle" title="Draw rectangle"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16"></rect></svg></button>
  <button class="tool" data-tool="circle" title="Draw circle"><svg viewBox="0 0 24 24" width="14" height="14"><circle cx="12" cy="12" r="8" fill="currentColor"></circle></svg></button>
  <button class="tool" data-tool="route" title="Route A to B"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="5" cy="19" r="2.5"></circle><circle cx="19" cy="5" r="2.5"></circle><path d="M7 17c4-1 3-8 8-9"></path></svg></button>
  <button id="basemap-btn" title="Basemap"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 6v16l7-4 8 4 7-4V2l-7 4-8-4z"></path><line x1="8" y1="2" x2="8" y2="18"></line><line x1="16" y1="6" x2="16" y2="22"></line></svg></button>
  <div class="tsep"></div>
  <button id="editbtn" title="Edit drawings"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4v16h16v-7"></path><path d="M18 2l4 4-10 10H8v-4z"></path></svg></button>
  <button id="clearbtn" title="Clear drawings"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"></path><path d="M8 6V4h8v2"></path><path d="M6 6l1 14h10l1-14"></path></svg></button>
</div>

<div id="layersPanel" class="panelbox">
  <div class="ph">Basemap layers</div>
  <div id="bmGroups"></div>
  <div class="ph">Your shapes (<span id="shapeCount">0</span>)</div>
  <div id="shapesList"></div>
</div>
<div id="searchBox" class="panelbox"><input id="searchInput" placeholder="Search place… (Enter)"/></div>
<div id="bmMenu" class="panelbox"></div>
<div id="markerOpts" class="panelbox">
  <div class="ph">Marker icon</div>
  <div class="shprow" id="mkShapes"></div>
  <div class="row"><span>Color</span><input type="color" id="mkColor" value="#c99c37"></div>
</div>
<div id="editor" class="panelbox">
  <div class="ph">Edit shape</div>
  <div class="shprow" id="eIcons" style="display:none"></div>
  <div class="row"><span>Color</span><input type="color" id="eColor"></div>
  <div class="row"><span>Width</span><input type="range" id="eWidth" min="1" max="12" step="1"></div>
  <div class="row"><span>Opacity</span><input type="range" id="eOp" min="0.05" max="1" step="0.05"></div>
  <div class="row"><button id="eDelete">Delete</button><button id="eClose">Close</button></div>
</div>
<div id="hint"></div>
<div id="err"></div>

<script>
try {
const ALL_STYLES = __ALL_STYLES__;
const map = new maplibregl.Map({
  container: 'map', style: __STYLE__, center: __CENTER__, zoom: __ZOOM__,
  attributionControl: false, fadeDuration: 0
});
map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');

// ---------------- state ----------------
const DEF = { color: '#c99c37', width: 3, opacity: 0.9 };
let features = [], fid = 0, activeTool = null, editMode = false;
let draft = [], routeA = null, selectedId = null;
let mkIcon = 'pin', mkColor = '#c99c37';
const vis = { roads: true, rail: true, buildings: true, water: true, parks: true, labels: __LABELS_JS__ };
const VIS_MAP = {
  roads: ['case_major_casing','case_minhi_casing','rd_path','rd_min_lo','rd_min_md','rd_min_hi','rd_major'],
  rail: ['rail'], buildings: ['building'], water: ['water','waterway'],
  parks: ['park','landcover'], labels: ['label_place']
};
const HINTS = {
  marker: 'Click to place markers', polyline: 'Click vertices · Enter/double-click finishes · Backspace undo',
  polygon: 'Click vertices · Enter/double-click closes · Backspace undo', rectangle: 'Click two corners',
  circle: 'Click center, then edge', route: 'Click point A, then point B'
};
const $ = id => document.getElementById(id);
const hint = t => { $('hint').style.display = t ? 'block' : 'none'; $('hint').textContent = t || ''; };
const SHAPES = ['pin','dot','square','star','triangle','diamond'];
const SHAPE_SVG = {
  pin: '<svg viewBox="0 0 24 24" width="13" height="13"><path d="M12 22s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z" fill="currentColor"/></svg>',
  dot: '<svg viewBox="0 0 24 24" width="13" height="13"><circle cx="12" cy="12" r="7" fill="currentColor"/></svg>',
  square: '<svg viewBox="0 0 24 24" width="13" height="13"><rect x="5" y="5" width="14" height="14" fill="currentColor"/></svg>',
  star: '<svg viewBox="0 0 24 24" width="13" height="13"><path d="M12 2l2.9 6.6 7.1.6-5.4 4.7 1.6 7-6.2-3.7-6.2 3.7 1.6-7L2 9.2l7.1-.6z" fill="currentColor"/></svg>',
  triangle: '<svg viewBox="0 0 24 24" width="13" height="13"><path d="M12 4l9 16H3z" fill="currentColor"/></svg>',
  diamond: '<svg viewBox="0 0 24 24" width="13" height="13"><path d="M12 2l9 10-9 10-9-10z" fill="currentColor"/></svg>'
};

// ---------------- runtime icon factory (canvas -> sprite, no external assets) ----
const iconCache = {};
function makeIcon(shape, color) {
  const key = shape + '|' + color;
  if (iconCache[key]) { if (!map.hasImage(key)) map.addImage(key, iconCache[key]); return key; }
  const s = 32, c = document.createElement('canvas'); c.width = s; c.height = s;
  const x = c.getContext('2d');
  x.translate(s/2, s/2); x.fillStyle = color; x.strokeStyle = '#0a1628'; x.lineWidth = 2;
  x.beginPath();
  if (shape === 'pin')          { x.moveTo(0, 14); x.bezierCurveTo(-11, 1, -9, -13, 0, -13); x.bezierCurveTo(9, -13, 11, 1, 0, 14); }
  else if (shape === 'dot')     x.arc(0, 0, 10, 0, 7);
  else if (shape === 'square')  x.rect(-9, -9, 18, 18);
  else if (shape === 'star')    { for (let i = 0; i < 10; i++) { const r = i % 2 ? 5 : 11, a = Math.PI/5*i - Math.PI/2; x.lineTo(Math.cos(a)*r, Math.sin(a)*r); } }
  else if (shape === 'triangle'){ x.moveTo(0, -11); x.lineTo(10, 9); x.lineTo(-10, 9); }
  else                          { x.moveTo(0, -11); x.lineTo(10, 0); x.lineTo(0, 11); x.lineTo(-10, 0); }
  x.closePath(); x.fill(); x.stroke();
  const img = { width: s, height: s, data: x.getImageData(0, 0, s, s).data };
  iconCache[key] = img; map.addImage(key, img);
  return key;
}

// ---------------- draw stack ----------------
const fc = list => ({ type: 'FeatureCollection',
  features: list.map(f => ({ type: 'Feature', geometry: f.geometry,
    properties: Object.assign({ kind: f.kind }, f.props) })) });

function addDrawStack() {
  Object.keys(iconCache).forEach(k => { if (!map.hasImage(k)) map.addImage(k, iconCache[k]); });
  if (!map.getSource('draw')) {
    map.addSource('draw', { type: 'geojson', data: fc(features) });
    const visF = ['==', ['get', 'visible'], true];
    map.addLayer({ id: 'draw-fill', type: 'fill', source: 'draw',
      filter: ['all', ['==', ['geometry-type'], 'Polygon'], visF],
      paint: { 'fill-color': ['get','color'], 'fill-opacity': ['*', ['get','opacity'], 0.25] } });
    map.addLayer({ id: 'draw-line', type: 'line', source: 'draw',
      filter: ['all', ['==', ['geometry-type'], 'LineString'], visF],
      layout: { 'line-cap': 'round', 'line-join': 'round' },
      paint: { 'line-color': ['get','color'], 'line-width': ['get','width'], 'line-opacity': ['get','opacity'] } });
    map.addLayer({ id: 'draw-outline', type: 'line', source: 'draw',
      filter: ['all', ['==', ['geometry-type'], 'Polygon'], visF],
      paint: { 'line-color': ['get','color'], 'line-width': ['get','width'], 'line-opacity': ['get','opacity'] } });
    map.addLayer({ id: 'draw-marker', type: 'symbol', source: 'draw',
      filter: ['all', ['==', ['geometry-type'], 'Point'], ['==', ['get','kind'], 'marker'], visF],
      layout: { 'icon-image': ['get','iconkey'], 'icon-size': ['/', ['get','width'], 5],
                'icon-allow-overlap': true, 'icon-anchor': 'bottom' } });
  } else map.getSource('draw').setData(fc(features));

  if (!map.getSource('draft')) {
    map.addSource('draft', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addLayer({ id: 'draft-fill', type: 'fill', source: 'draft',
      filter: ['==', ['geometry-type'], 'Polygon'],
      paint: { 'fill-color': '#d9b451', 'fill-opacity': 0.1 } });
    map.addLayer({ id: 'draft-line', type: 'line', source: 'draft',
      filter: ['==', ['geometry-type'], 'LineString'],
      paint: { 'line-color': '#d9b451', 'line-width': 2, 'line-dasharray': [2, 2] } });
    map.addLayer({ id: 'draft-point', type: 'circle', source: 'draft',
      filter: ['==', ['geometry-type'], 'Point'],
      paint: { 'circle-color': '#d9b451', 'circle-radius': 4, 'circle-stroke-color': '#0a1628', 'circle-stroke-width': 1 } });
  }
}
function syncDraw() {
  features.forEach(f => { if (f.kind === 'marker') f.props.iconkey = makeIcon(f.props.icon || 'pin', f.props.color); });
  if (map.getSource('draw')) map.getSource('draw').setData(fc(features));
  refreshShapes();
}
const P = c => ({ type: 'Feature', geometry: { type: 'Point', coordinates: c }, properties: {} });
const L = c => ({ type: 'Feature', geometry: { type: 'LineString', coordinates: c }, properties: {} });
const POLY = g => ({ type: 'Feature', geometry: g, properties: {} });
function renderDraft(extra) {
  if (!map.getSource('draft')) return;
  const f = draft.map(P);
  if (draft.length >= 2) f.push(L(draft));
  if (extra) f.push(extra);
  map.getSource('draft').setData({ type: 'FeatureCollection', features: f });
}
const resetDraft = () => { draft = []; routeA = null; renderDraft(); };
function applyVis() {
  for (const g in VIS_MAP) VIS_MAP[g].forEach(id => {
    if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', vis[g] ? 'visible' : 'none');
  });
}
map.on('load', () => { addDrawStack(); applyVis(); });

// ---------------- geometry helpers ----------------
const addFeature = f => { f.props.id = ++fid; f.props.visible = true; features.push(f); syncDraw(); };
function rectFrom(a, b) {
  return { kind: 'rect', props: { ...DEF }, geometry: { type: 'Polygon',
    coordinates: [[[a[0],a[1]],[a[0],b[1]],[b[0],b[1]],[b[0],a[1]],[a[0],a[1]]]] } };
}
function haversine(a, b) {
  const R = 6371000, dLa = (b[1]-a[1]) * Math.PI/180, dLo = (b[0]-a[0]) * Math.PI/180;
  const s = Math.sin(dLa/2)**2 + Math.cos(a[1]*Math.PI/180) * Math.cos(b[1]*Math.PI/180) * Math.sin(dLo/2)**2;
  return 2 * R * Math.asin(Math.sqrt(s));
}
function circleFrom(c, edge) {
  const r = haversine(c, edge), coords = [];
  for (let i = 0; i <= 64; i++) {
    const a = (i / 64) * 2 * Math.PI;
    coords.push([ c[0] + (r / (111320 * Math.cos(c[1]*Math.PI/180))) * Math.cos(a),
                  c[1] + (r / 111320) * Math.sin(a) ]);
  }
  return { kind: 'circle', props: { ...DEF }, geometry: { type: 'Polygon', coordinates: [coords] } };
}
function bboxOf(g) {
  let b = [1e9, 1e9, -1e9, -1e9];
  const scan = c => { if (typeof c[0] === 'number') { b[0]=Math.min(b[0],c[0]); b[1]=Math.min(b[1],c[1]); b[2]=Math.max(b[2],c[0]); b[3]=Math.max(b[3],c[1]); } else c.forEach(scan); };
  scan(g.coordinates);
  return b;
}
function zoomTo(f) {
  if (f.geometry.type === 'Point') map.flyTo({ center: f.geometry.coordinates, zoom: 16 });
  else { const b = bboxOf(f.geometry); map.fitBounds([[b[0],b[1]],[b[2],b[3]]], { padding: 80, maxZoom: 17 }); }
}
function fetchRoute(a, b) {
  hint('Routing A → B…');
  fetch(`https://router.project-osrm.org/route/v1/driving/${a[0]},${a[1]};${b[0]},${b[1]}?overview=full&geometries=geojson`)
    .then(r => r.json())
    .then(j => {
      const geom = (j.routes && j.routes[0]) ? j.routes[0].geometry : { type: 'LineString', coordinates: [a, b] };
      addFeature({ kind: 'route', geometry: geom, props: { color: '#e8b84a', width: 4, opacity: 0.9 } });
      hint('');
    })
    .catch(() => {
      addFeature({ kind: 'route', geometry: { type: 'LineString', coordinates: [a, b] },
                   props: { color: '#e8b84a', width: 3, opacity: 0.8 } });
      hint('OSRM unreachable — straight line used');
    });
}

// ---------------- tools + live previews ----------------
document.querySelectorAll('.tool').forEach(btn => btn.addEventListener('click', () => {
  const t = btn.dataset.tool;
  activeTool = (activeTool === t) ? null : t;
  editMode = false; $('editbtn').classList.remove('active');
  resetDraft(); closeEditor();
  document.querySelectorAll('.tool').forEach(b => b.classList.toggle('active', b.dataset.tool === activeTool));
  map.getCanvas().style.cursor = activeTool ? 'crosshair' : '';
  activeTool ? map.doubleClickZoom.disable() : map.doubleClickZoom.enable();
  $('markerOpts').classList.toggle('open', activeTool === 'marker');
  hint(activeTool ? HINTS[activeTool] : '');
}));

// Cursor-following preview while drafting
map.on('mousemove', e => {
  if (editMode) {
    const ids = ['draw-fill','draw-line','draw-outline','draw-marker'].filter(l => map.getLayer(l));
    map.getCanvas().style.cursor = map.queryRenderedFeatures(e.point, { layers: ids }).length ? 'pointer' : '';
    return;
  }
  if (!activeTool) return;
  const ll = [e.lngLat.lng, e.lngLat.lat];
  let extra = null;
  if ((activeTool === 'polyline' || activeTool === 'polygon') && draft.length) extra = L([...draft, ll]);
  else if (activeTool === 'rectangle' && draft.length === 1) extra = POLY(rectFrom(draft[0], ll).geometry);
  else if (activeTool === 'circle' && draft.length === 1) extra = POLY(circleFrom(draft[0], ll).geometry);
  else if (activeTool === 'route' && routeA) extra = L([routeA, ll]);
  renderDraft(extra);
});

map.on('click', e => {
  if (editMode) { pickFeature(e); return; }
  if (!activeTool) return;
  const ll = [e.lngLat.lng, e.lngLat.lat];
  if (activeTool === 'marker')
    addFeature({ kind: 'marker', geometry: { type: 'Point', coordinates: ll },
                 props: { color: mkColor, width: 5, opacity: 1, icon: mkIcon } });
  else if (activeTool === 'polyline' || activeTool === 'polygon') draft.push(ll);
  else if (activeTool === 'rectangle') { draft.push(ll); if (draft.length === 2) { addFeature(rectFrom(draft[0], draft[1])); resetDraft(); } }
  else if (activeTool === 'circle')    { draft.push(ll); if (draft.length === 2) { addFeature(circleFrom(draft[0], draft[1])); resetDraft(); } }
  else if (activeTool === 'route') {
    if (!routeA) { routeA = ll; draft = [ll]; hint('Now click point B'); }
    else { const a = routeA; resetDraft(); fetchRoute(a, ll); }
  }
  renderDraft();
});
map.on('dblclick', () => {
  if (activeTool === 'polyline' && draft.length >= 2) {
    draft.pop();
    addFeature({ kind: 'polyline', props: { ...DEF }, geometry: { type: 'LineString', coordinates: draft } });
    resetDraft();
  } else if (activeTool === 'polygon' && draft.length >= 3) {
    draft.pop();
    addFeature({ kind: 'polygon', props: { ...DEF }, geometry: { type: 'Polygon', coordinates: [[...draft, draft[0]]] } });
    resetDraft();
  }
});
document.addEventListener('keydown', e => {
  if (e.key === 'Enter') map.fire('dblclick');
  else if (e.key === 'Backspace' && draft.length) { e.preventDefault(); draft.pop(); renderDraft(); }
  else if (e.key === 'Escape') { resetDraft(); closeEditor(); }
});

// ---------------- marker icon options ----------------
$('mkShapes').innerHTML = SHAPES.map(s =>
  `<button class="shp ${s === mkIcon ? 'active' : ''}" data-s="${s}" title="${s}">${SHAPE_SVG[s]}</button>`).join('');
$('mkShapes').querySelectorAll('button').forEach(b => b.onclick = () => {
  mkIcon = b.dataset.s;
  $('mkShapes').querySelectorAll('button').forEach(x => x.classList.toggle('active', x === b));
};
$('mkColor').oninput = e => mkColor = e.target.value;

// ---------------- edit mode + editor ----------------
$('editbtn').onclick = () => {
  editMode = !editMode; activeTool = null;
  document.querySelectorAll('.tool').forEach(b => b.classList.remove('active'));
  $('markerOpts').classList.remove('open');
  $('editbtn').classList.toggle('active', editMode);
  map.getCanvas().style.cursor = editMode ? 'pointer' : '';
  hint(editMode ? 'Click a shape to edit · Esc to exit' : '');
};
function pickFeature(e) {
  const ids = ['draw-fill','draw-line','draw-outline','draw-marker'].filter(l => map.getLayer(l));
  const fs = map.queryRenderedFeatures(e.point, { layers: ids });
  if (fs.length && fs[0].properties.id != null) openEditor(fs[0].properties.id);
  else closeEditor();
}
function openEditor(id) {
  const f = features.find(x => x.props.id === id);
  if (!f) return;
  selectedId = id;
  $('eColor').value = f.props.color;
  $('eWidth').value = f.props.width;
  $('eOp').value = f.props.opacity;
  const isMk = f.kind === 'marker';
  $('eIcons').style.display = isMk ? 'flex' : 'none';
  if (isMk) {
    $('eIcons').innerHTML = SHAPES.map(s =>
      `<button class="shp ${s === f.props.icon ? 'active' : ''}" data-s="${s}">${SHAPE_SVG[s]}</button>`).join('');
    $('eIcons').querySelectorAll('button').forEach(b => b.onclick = () => {
      f.props.icon = b.dataset.s; f.props.iconkey = makeIcon(f.props.icon, f.props.color);
      $('eIcons').querySelectorAll('button').forEach(x => x.classList.toggle('active', x === b));
      syncDraw();
    });
  }
  $('editor').classList.add('open');
}
function closeEditor() { selectedId = null; $('editor').classList.remove('open'); }
function editProp(k, v) {
  const f = features.find(x => x.props.id === selectedId);
  if (!f) return;
  f.props[k] = v;
  if (k === 'color' && f.kind === 'marker') f.props.iconkey = makeIcon(f.props.icon, f.props.color);
  syncDraw();
}
$('eColor').oninput = e => editProp('color', e.target.value);
$('eWidth').oninput = e => editProp('width', parseFloat(e.target.value));
$('eOp').oninput   = e => editProp('opacity', parseFloat(e.target.value));
$('eDelete').onclick = () => { features = features.filter(x => x.props.id !== selectedId); syncDraw(); closeEditor(); };
$('eClose').onclick = closeEditor;
$('clearbtn').onclick = () => { features = []; resetDraft(); syncDraw(); closeEditor(); };

// ---------------- layers & shapes manager ----------------
$('bmGroups').innerHTML = Object.keys(VIS_MAP).map(g => {
  const names = { roads: 'Roads', rail: 'Rail', buildings: 'Buildings', water: 'Water', parks: 'Parks', labels: 'Labels' };
  return `<label class="row"><span>${names[g]}</span><input type="checkbox" data-g="${g}" ${vis[g] ? 'checked' : ''}></label>`;
}).join('');
$('bmGroups').querySelectorAll('input').forEach(cb => cb.onchange = () => { vis[cb.dataset.g] = cb.checked; applyVis(); });

function refreshShapes() {
  $('shapeCount').textContent = features.length;
  $('shapesList').innerHTML = features.length ? features.map(f => `
    <div class="srow">
      <button data-a="eye" data-id="${f.props.id}" title="show/hide">${f.props.visible ? '👁' : '—'}</button>
      <span class="sname">${f.kind} #${f.props.id}</span>
      <button data-a="zoom" data-id="${f.props.id}" title="zoom to">⌖</button>
      <button data-a="edit" data-id="${f.props.id}" title="edit">✎</button>
      <button data-a="del" data-id="${f.props.id}" title="delete">✕</button>
    </div>`).join('') : '<div class="row"><span style="color:#8b949e">Nothing drawn yet</span></div>';
}
$('shapesList').onclick = e => {
  const b = e.target.closest('button'); if (!b) return;
  const f = features.find(x => x.props.id == b.dataset.id); if (!f) return;
  if (b.dataset.a === 'eye')  { f.props.visible = !f.props.visible; syncDraw(); }
  if (b.dataset.a === 'zoom') zoomTo(f);
  if (b.dataset.a === 'edit') openEditor(f.props.id);
  if (b.dataset.a === 'del')  { features = features.filter(x => x.props.id !== f.props.id); syncDraw(); }
};
$('db-toggle').onclick = () => { refreshShapes(); $('layersPanel').classList.toggle('open'); };

// ---------------- search (Nominatim, keyless) ----------------
$('searchbtn').onclick = () => { $('searchBox').classList.toggle('open'); $('searchInput').focus(); };
$('searchInput').addEventListener('keydown', e => {
  if (e.key !== 'Enter') return;
  const q = e.target.value.trim(); if (!q) return;
  hint('Searching…');
  fetch(`https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(q)}`)
    .then(r => r.json())
    .then(j => { if (j.length) { map.flyTo({ center: [parseFloat(j[0].lon), parseFloat(j[0].lat)], zoom: 15 }); hint(''); } else hint('No results'); })
    .catch(() => hint('Search failed'));
});

// ---------------- live basemap switcher ----------------
$('basemap-btn').onclick = () => {
  const m = $('bmMenu');
  if (!m.innerHTML) {
    m.innerHTML = Object.keys(ALL_STYLES).map(n => `<button data-n="${n}">${n}</button>`).join('');
    m.querySelectorAll('button').forEach(b => b.onclick = () => {
      map.setStyle(ALL_STYLES[b.dataset.n]);
      map.once('idle', () => { addDrawStack(); applyVis(); syncDraw(); });
      m.classList.remove('open');
    });
  }
  m.classList.toggle('open');
};

map.on('error', e => console.warn('map error:', e));
} catch (e) {
  const box = document.getElementById('err');
  box.style.display = 'block';
  box.textContent = 'Map init failed: ' + e.message;
}
</script>
</body>
</html>"""

try:
    html = (HTML_TEMPLATE
            .replace("__ALL_STYLES__", json.dumps(ALL_STYLES))
            .replace("__STYLE__", json.dumps(ALL_STYLES["Midnight Blue"]))
            .replace("__CENTER__", json.dumps(CENTER))
            .replace("__ZOOM__", str(ZOOM))
            .replace("__BG__", "#0a1628")
            .replace("__MUTED__", "#8b949e")
            .replace("__LABELS_JS__", "true"))
    components.html(html, height=950, scrolling=False)
except Exception as e:
    st.error(f"Map render failed: {e}")

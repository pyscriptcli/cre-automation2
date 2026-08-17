import json
import streamlit as st
import streamlit.components.v1 as components

# ------------------------------------------------------------------------
# 1. PAGE CONFIGURATION (no sidebar)
# ------------------------------------------------------------------------
st.set_page_config(page_title="Felt Map Studio", page_icon="🗺️",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .block-container { padding: 0rem !important; max-width: 100% !important; }
    header { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
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

INITIAL_BASEMAP = "Midnight Blue"

# ------------------------------------------------------------------------
# 3. MAP + LEFT RAIL + DATA BROWSER PANEL
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
  #attr { position: absolute; bottom: 4px; right: 6px; z-index: 2;
          font: 10px sans-serif; color: __MUTED__; pointer-events: none; }
  /* Left icon rail (orientation copied from reference) */
  #rail { position: absolute; left: 8px; top: 8px; bottom: 8px; width: 44px; z-index: 4;
          background: #161b22ee; border: 1px solid #30363d; border-radius: 10px;
          display: flex; flex-direction: column; align-items: center;
          padding: 6px 0; gap: 2px; overflow-y: auto; }
  #rail button { width: 32px; height: 32px; flex: 0 0 auto; display: grid; place-items: center;
                 background: transparent; border: none; color: #c9d1d9;
                 border-radius: 8px; cursor: pointer; }
  #rail button:hover { background: #21262d; color: #f0f6fc; }
  #rail button.active { background: #c99c37; color: #0a1628; }
  #rail .tsep { width: 20px; height: 1px; background: #30363d; margin: 4px 0; flex: 0 0 auto; }
  /* Data browser panel */
  #panel { position: absolute; left: 60px; top: 8px; bottom: 8px; width: 300px; z-index: 3;
           background: #161b22f5; border: 1px solid #30363d; border-radius: 10px;
           padding: 12px; overflow-y: auto; display: none; flex-direction: column; gap: 8px;
           font: 12px sans-serif; color: #f0f6fc; }
  #panel.open { display: flex; }
  .phead { display: flex; justify-content: space-between; align-items: center; }
  .phead button { background: #21262d; color: #f0f6fc; border: 1px solid #30363d;
                  border-radius: 6px; padding: 2px 8px; cursor: pointer; }
  .sec { font-size: 10px; letter-spacing: 1px; color: #8b949e; margin-top: 6px; }
  .row { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
  #panel input[type=range] { width: 110px; accent-color: #c99c37; }
  #panel input[type=text] { width: 100%; box-sizing: border-box; background: #0d1117;
                            color: #f0f6fc; border: 1px solid #30363d; border-radius: 6px; padding: 6px; }
  #panel button.small { background: #21262d; color: #f0f6fc; border: 1px solid #30363d;
                        border-radius: 6px; padding: 3px 7px; cursor: pointer; font: 11px sans-serif; }
  .bmgrid { display: flex; flex-wrap: wrap; gap: 4px; }
  .bmgrid button { background: #21262d; color: #f0f6fc; border: 1px solid #30363d;
                   border-radius: 6px; padding: 4px 8px; cursor: pointer; font: 11px sans-serif; }
  .bmgrid button.active { background: #c99c37; color: #0a1628; }
  #iconRow { display: flex; gap: 4px; }
  #iconRow button { width: 30px; height: 30px; display: grid; place-items: center;
                    background: #21262d; border: 1px solid #30363d; color: #c9d1d9;
                    border-radius: 6px; cursor: pointer; }
  #iconRow button.active { background: #c99c37; color: #0a1628; }
  .listitem { display: flex; align-items: center; gap: 4px; }
  .listitem .nm { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .badge { background: #c99c37; color: #0a1628; border-radius: 10px; padding: 0 7px; font-weight: 700; }
  #hint { position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%);
          z-index: 2; background: #161b22cc; color: #d9b451; border: 1px solid #30363d;
          border-radius: 6px; padding: 4px 10px; font: 11px sans-serif; display: none; }
  #measure { position: absolute; z-index: 5; display: none; pointer-events: none;
             background: #c99c37; color: #0a1628; border-radius: 6px; padding: 2px 8px;
             font: 11px sans-serif; font-weight: 700; }
  #err { display: none; position: absolute; top: 10px; right: 10px; z-index: 6;
         background: #3d1111; color: #ffb4b4; padding: 8px 12px; border-radius: 6px;
         font: 12px monospace; }
</style>
</head>
<body>
<div id="map"></div>
<div id="attr">© OpenStreetMap · OpenFreeMap · OSRM · Nominatim</div>

<div id="rail">
  <button id="db-toggle" class="active" title="Data browser"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"></path><path d="M2 12l10 6 10-6"></path><path d="M2 16l10 6 10-6"></path></svg></button>
  <div class="tsep"></div>
  <button id="searchbtn" title="Search"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"></circle><line x1="21" y1="21" x2="16.5" y2="16.5"></line></svg></button>
  <button class="tool" data-tool="marker" title="Place marker"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"></path><circle cx="12" cy="10" r="2.5"></circle></svg></button>
  <button class="tool" data-tool="polyline" title="Draw line"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"></path></svg></button>
  <button class="tool" data-tool="polygon" title="Draw polygon"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l8 6-3 10H7L4 9z"></path></svg></button>
  <button class="tool" data-tool="rectangle" title="Draw rectangle"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16"></rect></svg></button>
  <button class="tool" data-tool="circle" title="Draw circle"><svg viewBox="0 0 24 24" width="14" height="14"><circle cx="12" cy="12" r="8" fill="currentColor"></circle></svg></button>
  <button class="tool" data-tool="route" title="Route A to B"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="5" cy="19" r="2.5"></circle><circle cx="19" cy="5" r="2.5"></circle><path d="M7 17c4-1 3-8 8-9"></path></svg></button>
  <div class="tsep"></div>
  <button id="basemap-btn" title="Basemap"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 6v16l7-4 8 4 7-4V2l-7 4-8-4z"></path><line x1="8" y1="2" x2="8" y2="18"></line><line x1="16" y1="6" x2="16" y2="22"></line></svg></button>
  <button id="editbtn" title="Pick shape to edit"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4v16h16v-7"></path><path d="M18 2l4 4-10 10H8v-4z"></path></svg></button>
  <button id="clearbtn" title="Clear drawings"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"></path><path d="M8 6V4h8v2"></path><path d="M6 6l1 14h10l1-14"></path></svg></button>
</div>

<div id="panel" class="open">
  <div class="phead"><strong>🗂️ Data browser</strong><button id="panelClose">✕</button></div>

  <div class="sec">SEARCH</div>
  <input id="searchInput" type="text" placeholder="Search place… (Enter)"/>

  <div class="sec">BASEMAP</div>
  <div id="bmGrid" class="bmgrid"></div>

  <div class="sec">MARKER ICON</div>
  <div id="iconRow"></div>

  <div class="sec">DATA LAYERS</div>
  <div id="dataLayers"></div>

  <div class="sec">MY LAYERS <span id="lyrCount" class="badge">0</span></div>
  <div id="myLayers"><div style="color:#8b949e">No drawings yet. Use the draw tools to add shapes.</div></div>

  <div id="editSec" style="display:none">
    <div class="sec">EDIT SHAPE · <span id="editName"></span></div>
    <div class="row"><span>Color</span><input type="color" id="eColor"></div>
    <div class="row"><span>Width</span><input type="range" id="eWidth" min="1" max="12" step="1"></div>
    <div class="row"><span>Opacity</span><input type="range" id="eOp" min="0.05" max="1" step="0.05"></div>
    <div class="row"><button class="small" id="eDone">Done</button>
    <span style="color:#8b949e;font-size:10px">drag shape · drag points · right-click point = delete</span></div>
  </div>
</div>

<div id="hint"></div>
<div id="measure"></div>
<div id="err"></div>

<script>
try {
const ALL_STYLES = __ALL_STYLES__;
const map = new maplibregl.Map({
  container: 'map', style: __STYLE__, center: __CENTER__, zoom: __ZOOM__,
  attributionControl: false, fadeDuration: 0
});
map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
map.getCanvas().addEventListener('contextmenu', e => e.preventDefault());

// ---------------- state ----------------
const DEF = { color: '#c99c37', width: 3, opacity: 0.9 };
let features = [], fid = 0, activeTool = null, pickMode = false;
let draft = [], routeA = null, cursorLL = null;
let editingId = null, drag = null;
let markerShape = 'pin';
const usedIcons = new Map();
const vis = { main: true, secondary: true, buildings: true, water: true, labels: true };
const VIS_MAP = {
  main: ['case_major_casing', 'rd_major'],
  secondary: ['case_minhi_casing', 'rd_min_hi', 'rd_min_md', 'rd_min_lo', 'rd_path'],
  buildings: ['building'], water: ['water', 'waterway'], labels: ['label_place']
};
const DATA_NAMES = { main: 'Main Roads', secondary: 'Secondary Roads', buildings: 'Buildings', water: 'Water', labels: 'Labels' };
const HINTS = {
  marker: 'Click to place markers',
  polyline: 'Click vertices · right-click undo · double-click/Enter finish',
  polygon: 'Click vertices · right-click undo · double-click/Enter close',
  rectangle: 'Click two corners · right-click cancels',
  circle: 'Click center, then edge · right-click cancels',
  route: 'Click point A, then point B'
};
const $ = id => document.getElementById(id);
const hint = t => { $('hint').style.display = t ? 'block' : 'none'; $('hint').textContent = t || ''; };
const byId = id => features.find(x => x.props.id === id);
const drawLayers = () => ['draw-fill','draw-line','draw-outline','draw-marker'].filter(l => map.getLayer(l));
const fmtDist = m => m < 1000 ? Math.round(m) + ' m' : (m / 1000).toFixed(2) + ' km';

// ---------------- marker icons (canvas -> ImageData, sanitized ids) ----------------
function drawIcon(shape, color) {
  const c = document.createElement('canvas'); c.width = c.height = 48;
  const x = c.getContext('2d');
  x.strokeStyle = '#0a1628'; x.lineWidth = 3; x.fillStyle = color; x.lineJoin = 'round';
  x.beginPath();
  if (shape === 'pin')        { x.arc(24, 18, 12, Math.PI, 0); x.lineTo(36, 20); x.lineTo(24, 44); x.lineTo(12, 20); x.closePath(); }
  else if (shape === 'star')  { for (let i = 0; i < 10; i++) { const r = i % 2 ? 9 : 20, a = -Math.PI / 2 + i * Math.PI / 5; const px = 24 + r * Math.cos(a), py = 26 + r * Math.sin(a); i ? x.lineTo(px, py) : x.moveTo(px, py); } x.closePath(); }
  else if (shape === 'circle'){ x.arc(24, 24, 16, 0, 7); }
  else if (shape === 'square'){ x.rect(9, 9, 30, 30); }
  else if (shape === 'flag')  { x.moveTo(14, 44); x.lineTo(14, 6); x.lineTo(36, 12); x.lineTo(14, 20); }
  else if (shape === 'heart') { x.moveTo(24, 42); x.bezierCurveTo(4, 26, 10, 6, 24, 16); x.bezierCurveTo(38, 6, 44, 26, 24, 42); }
  x.fill(); x.stroke();
  return c;
}
function ensureIcon(shape, color) {
  const key = 'mk_' + shape + '_' + color.replace('#', '');
  if (!map.hasImage(key)) {
    // ImageData is the most reliably supported addImage input across builds
    map.addImage(key, drawIcon(shape, color).getContext('2d').getImageData(0, 0, 48, 48));
  }
  usedIcons.set(key, { shape, color });
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
$('iconRow').innerHTML = Object.keys(ICON_SVGS).map(s =>
  `<button data-s="${s}" class="${s === markerShape ? 'active' : ''}" title="${s}">
     <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">${ICON_SVGS[s]}</svg>
   </button>`).join('');
$('iconRow').querySelectorAll('button').forEach(b => b.onclick = () => {
  markerShape = b.dataset.s;
  $('iconRow').querySelectorAll('button').forEach(x => x.classList.toggle('active', x === b));
});

// ---------------- draw stack ----------------
const fc = list => ({ type: 'FeatureCollection',
  features: list.map(f => ({ type: 'Feature', geometry: f.geometry,
    properties: Object.assign({ kind: f.kind }, f.props) })) });

function addDrawStack() {
  if (!map.getSource('draw')) {
    map.addSource('draw', { type: 'geojson', data: fc(features) });
    map.addLayer({ id: 'draw-fill', type: 'fill', source: 'draw',
      filter: ['==', ['geometry-type'], 'Polygon'],
      paint: { 'fill-color': ['get','color'], 'fill-opacity': ['*', ['get','opacity'], 0.25, ['get','visible']] } });
    map.addLayer({ id: 'draw-line', type: 'line', source: 'draw',
      filter: ['==', ['geometry-type'], 'LineString'],
      layout: { 'line-cap': 'round', 'line-join': 'round' },
      paint: { 'line-color': ['get','color'], 'line-width': ['get','width'],
               'line-opacity': ['*', ['get','opacity'], ['get','visible']] } });
    map.addLayer({ id: 'draw-outline', type: 'line', source: 'draw',
      filter: ['==', ['geometry-type'], 'Polygon'],
      paint: { 'line-color': ['get','color'], 'line-width': ['get','width'],
               'line-opacity': ['*', ['get','opacity'], ['get','visible']] } });
    map.addLayer({ id: 'draw-marker', type: 'symbol', source: 'draw',
      filter: ['==', ['geometry-type'], 'Point'],
      layout: { 'icon-image': ['get','icon'], 'icon-size': ['/', ['get','width'], 6],
                'icon-allow-overlap': true },
      paint: { 'icon-opacity': ['get','visible'] } });
  } else map.getSource('draw').setData(fc(features));

  if (!map.getSource('draft')) {
    map.addSource('draft', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addLayer({ id: 'draft-line', type: 'line', source: 'draft',
      filter: ['==', ['geometry-type'], 'LineString'],
      paint: { 'line-color': '#d9b451', 'line-width': 2, 'line-dasharray': [2, 2] } });
    map.addLayer({ id: 'draft-point', type: 'circle', source: 'draft',
      filter: ['==', ['geometry-type'], 'Point'],
      paint: { 'circle-color': '#d9b451', 'circle-radius': 4,
               'circle-stroke-color': '#0a1628', 'circle-stroke-width': 1 } });
  } else renderDraft();

  if (!map.getSource('handles')) {
    map.addSource('handles', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addLayer({ id: 'handles', type: 'circle', source: 'handles',
      paint: { 'circle-color': '#ffffff', 'circle-radius': 5,
               'circle-stroke-color': '#c99c37', 'circle-stroke-width': 2 } });
  } else renderHandles();
}
const syncDraw = () => { if (map.getSource('draw')) map.getSource('draw').setData(fc(features)); };

function renderDraft() {
  if (!map.getSource('draft')) return;
  const f = [];
  const pt = c => ({ type: 'Feature', geometry: { type: 'Point', coordinates: c }, properties: {} });
  const ln = c => ({ type: 'Feature', geometry: { type: 'LineString', coordinates: c }, properties: {} });
  draft.forEach(p => f.push(pt(p)));
  if (activeTool === 'polyline' && draft.length) f.push(ln(cursorLL ? [...draft, cursorLL] : draft));
  if (activeTool === 'polygon' && draft.length) {
    const pts = cursorLL ? [...draft, cursorLL] : draft;
    if (pts.length > 1) f.push(ln([...pts, pts[0]]));
  }
  if (activeTool === 'rectangle' && draft.length === 1 && cursorLL)
    f.push(ln(rectFrom(draft[0], cursorLL).geometry.coordinates[0]));
  if (activeTool === 'circle' && draft.length === 1 && cursorLL)
    f.push(ln(circleFrom(draft[0], cursorLL).geometry.coordinates[0]));
  if (activeTool === 'route' && routeA && cursorLL) f.push(ln([routeA, cursorLL]));
  map.getSource('draft').setData({ type: 'FeatureCollection', features: f });
}
const resetDraft = () => { draft = []; routeA = null; hideMeasure(); renderDraft(); };
function applyVis() {
  for (const g in VIS_MAP) VIS_MAP[g].forEach(id => {
    if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', vis[g] ? 'visible' : 'none');
  });
}
map.on('load', () => { addDrawStack(); applyVis(); });

// ---------------- geometry helpers ----------------
const addFeature = f => { f.props.id = ++fid; f.props.visible = 1; features.push(f); syncDraw(); refreshManager(); };
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
function fetchRoute(a, b) {
  hint('Routing A → B…');
  fetch(`https://router.project-osrm.org/route/v1/driving/${a[0]},${a[1]};${b[0]},${b[1]}?overview=full&geometries=geojson`)
    .then(r => r.json())
    .then(j => {
      const geom = (j.routes && j.routes[0]) ? j.routes[0].geometry
                   : { type: 'LineString', coordinates: [a, b] };
      addFeature({ kind: 'route', geometry: geom, props: { color: '#e8b84a', width: 4, opacity: 0.9 } });
      hint('');
    })
    .catch(() => {
      addFeature({ kind: 'route', geometry: { type: 'LineString', coordinates: [a, b] },
                   props: { color: '#e8b84a', width: 3, opacity: 0.8 } });
      hint('OSRM unreachable — straight line used');
    });
}

// ---------------- vertex handles / move editing ----------------
function handlesFor(f) {
  const pts = [];
  if (f.geometry.type === 'Point') pts.push({ idx: 0, c: f.geometry.coordinates });
  else {
    const isPoly = f.geometry.type === 'Polygon';
    const ring = isPoly ? f.geometry.coordinates[0] : f.geometry.coordinates;
    const n = isPoly ? ring.length - 1 : ring.length;
    for (let i = 0; i < n; i++) pts.push({ idx: i, c: ring[i] });
  }
  return pts;
}
function renderHandles() {
  if (!map.getSource('handles')) return;
  const f = byId(editingId);
  const feats = f ? handlesFor(f).map(h => ({ type: 'Feature',
    geometry: { type: 'Point', coordinates: h.c }, properties: { idx: h.idx } })) : [];
  map.getSource('handles').setData({ type: 'FeatureCollection', features: feats });
}
function setCoord(f, idx, ll) {
  if (f.geometry.type === 'Point') { f.geometry.coordinates = ll; return; }
  const isPoly = f.geometry.type === 'Polygon';
  const ring = isPoly ? f.geometry.coordinates[0] : f.geometry.coordinates;
  ring[idx] = ll;
  if (isPoly && idx === 0) ring[ring.length - 1] = [...ll];
}
function translate(f, dLng, dLat) {
  const walk = c => { if (typeof c[0] === 'number') { c[0] += dLng; c[1] += dLat; } else c.forEach(walk); };
  walk(f.geometry.coordinates);
}
function startEditing(id) {
  editingId = id;
  const f = byId(id);
  if (!f) return;
  $('panel').classList.add('open'); $('db-toggle').classList.add('active');
  $('editSec').style.display = 'block';
  $('editName').textContent = f.kind + ' ' + id;
  $('eColor').value = f.props.color; $('eWidth').value = f.props.width; $('eOp').value = f.props.opacity;
  renderHandles();
  map.getCanvas().style.cursor = 'pointer';
  hint('Drag shape to move · drag white points · right-click point deletes');
}
function stopEditing() {
  editingId = null; drag = null;
  $('editSec').style.display = 'none';
  renderHandles();
  map.getCanvas().style.cursor = activeTool ? 'crosshair' : '';
  hint(activeTool ? HINTS[activeTool] : '');
}
map.on('mousedown', e => {
  if (editingId == null || activeTool) return;
  const hf = map.getLayer('handles') ? map.queryRenderedFeatures(e.point, { layers: ['handles'] }) : [];
  if (hf.length) drag = { mode: 'vertex', idx: hf[0].properties.idx, last: [e.lngLat.lng, e.lngLat.lat] };
  else {
    const sf = map.queryRenderedFeatures(e.point, { layers: drawLayers() }).filter(x => x.properties.id === editingId);
    if (sf.length) drag = { mode: 'move', last: [e.lngLat.lng, e.lngLat.lat] };
  }
  if (drag) { map.dragPan.disable(); map.getCanvas().style.cursor = 'grabbing'; }
});
map.on('mouseup', () => {
  if (drag) { drag = null; map.dragPan.enable();
    map.getCanvas().style.cursor = editingId != null ? 'pointer' : (activeTool ? 'crosshair' : ''); }
});

// ---------------- circle radius indicator ----------------
function showMeasure(e) {
  const el = $('measure');
  el.style.display = 'block';
  el.style.left = (e.point.x + 14) + 'px';
  el.style.top = (e.point.y + 14) + 'px';
  el.textContent = 'R = ' + fmtDist(haversine(draft[0], cursorLL));
}
const hideMeasure = () => { $('measure').style.display = 'none'; };

// ---------------- tools ----------------
document.querySelectorAll('.tool').forEach(btn => btn.addEventListener('click', () => {
  const t = btn.dataset.tool;
  activeTool = (activeTool === t) ? null : t;
  pickMode = false; $('editbtn').classList.remove('active');
  if (!activeTool) stopEditing();
  resetDraft();
  document.querySelectorAll('.tool').forEach(b => b.classList.toggle('active', b.dataset.tool === activeTool));
  map.getCanvas().style.cursor = activeTool ? 'crosshair' : '';
  activeTool ? map.doubleClickZoom.disable() : map.doubleClickZoom.enable();
  hint(activeTool ? HINTS[activeTool] : '');
}));

map.on('mousemove', e => {
  cursorLL = [e.lngLat.lng, e.lngLat.lat];
  if (activeTool) {
    renderDraft();
    (activeTool === 'circle' && draft.length === 1) ? showMeasure(e) : hideMeasure();
  }
  if (drag && editingId != null) {
    const f = byId(editingId); if (!f) return;
    const ll = [e.lngLat.lng, e.lngLat.lat];
    if (drag.mode === 'vertex') setCoord(f, drag.idx, ll);
    else translate(f, ll[0] - drag.last[0], ll[1] - drag.last[1]);
    drag.last = ll;
    syncDraw(); renderHandles();
  }
});
map.on('click', e => {
  if (pickMode && !activeTool) {
    const fs = map.queryRenderedFeatures(e.point, { layers: drawLayers() });
    if (fs.length && fs[0].properties.id != null) startEditing(fs[0].properties.id);
    return;
  }
  if (!activeTool) return;
  const ll = [e.lngLat.lng, e.lngLat.lat];
  if (activeTool === 'marker') {
    addFeature({ kind: 'marker', geometry: { type: 'Point', coordinates: ll },
                 props: { ...DEF, shape: markerShape, icon: ensureIcon(markerShape, DEF.color) } });
  }
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
map.on('contextmenu', e => {
  // While editing: right-click a handle to delete the vertex
  if (editingId != null && !activeTool) {
    const hf = map.getLayer('handles') ? map.queryRenderedFeatures(e.point, { layers: ['handles'] }) : [];
    if (hf.length) {
      const f = byId(editingId), idx = hf[0].properties.idx;
      if (f.geometry.type === 'Polygon' && f.geometry.coordinates[0].length > 4) {
        const r = f.geometry.coordinates[0];
        r.splice(idx, 1);
        r[r.length - 1] = [...r[0]];
        syncDraw(); renderHandles();
      } else if (f.geometry.type === 'LineString' && f.geometry.coordinates.length > 2) {
        f.geometry.coordinates.splice(idx, 1);
        syncDraw(); renderHandles();
      }
    }
    return;
  }
  if (!activeTool) return;  // drafting: right-click = undo vertex
  if (activeTool === 'route' && routeA) { routeA = null; draft = []; hint(HINTS.route); }
  else if (draft.length) draft.pop();
  renderDraft();
});
document.addEventListener('keydown', e => {
  if (/INPUT|TEXTAREA/.test(e.target.tagName)) return;
  if (e.key === 'Enter') map.fire('dblclick');
  if (e.key === 'Escape') { resetDraft(); stopEditing(); pickMode = false; $('editbtn').classList.remove('active'); }
  if (e.key === 'Backspace' && draft.length) { draft.pop(); renderDraft(); }
});

// ---------------- editor bindings ----------------
const editProp = (k, v) => {
  const f = byId(editingId); if (!f) return;
  f.props[k] = v;
  if (k === 'color' && f.kind === 'marker') f.props.icon = ensureIcon(f.props.shape, v);
  syncDraw();
};
$('eColor').oninput = e => editProp('color', e.target.value);
$('eWidth').oninput = e => editProp('width', parseFloat(e.target.value));
$('eOp').oninput   = e => editProp('opacity', parseFloat(e.target.value));
$('eDone').onclick = stopEditing;
$('editbtn').onclick = () => {
  pickMode = !pickMode;
  $('editbtn').classList.toggle('active', pickMode);
  if (pickMode) { activeTool = null; document.querySelectorAll('.tool').forEach(b => b.classList.remove('active')); }
  hint(pickMode ? 'Click a shape to edit' : '');
};
$('clearbtn').onclick = () => { features = []; resetDraft(); stopEditing(); syncDraw(); refreshManager(); };

// ---------------- data browser panel ----------------
$('db-toggle').onclick = () => {
  const open = $('panel').classList.toggle('open');
  $('db-toggle').classList.toggle('active', open);
  refreshManager();
};
$('panelClose').onclick = () => { $('panel').classList.remove('open'); $('db-toggle').classList.remove('active'); };

$('dataLayers').innerHTML = Object.keys(VIS_MAP).map(g =>
  `<label class="row"><span>${DATA_NAMES[g]}</span><input type="checkbox" data-g="${g}" ${vis[g] ? 'checked' : ''}></label>`).join('');
$('dataLayers').querySelectorAll('input').forEach(cb => cb.onchange = () => { vis[cb.dataset.g] = cb.checked; applyVis(); });

function refreshManager() {
  $('lyrCount').textContent = features.length;
  const box = $('myLayers');
  if (!features.length) { box.innerHTML = '<div style="color:#8b949e">No drawings yet. Use the draw tools to add shapes.</div>'; return; }
  box.innerHTML = features.slice().reverse().map(f =>
    `<div class="listitem">
       <button class="small" data-act="eye" data-id="${f.props.id}" title="Show/hide">${f.props.visible ? '👁' : '–'}</button>
       <span class="nm">${f.kind} ${f.props.id}</span>
       <button class="small" data-act="edit" data-id="${f.props.id}" title="Edit">✎</button>
       <button class="small" data-act="zoom" data-id="${f.props.id}" title="Zoom to">⤢</button>
       <button class="small" data-act="del" data-id="${f.props.id}" title="Delete">✕</button>
     </div>`).join('');
  box.querySelectorAll('button[data-act]').forEach(b => b.onclick = () => {
    const id = parseInt(b.dataset.id, 10);
    const f = byId(id); if (!f) return;
    if (b.dataset.act === 'eye')  { f.props.visible = f.props.visible ? 0 : 1; syncDraw(); refreshManager(); }
    if (b.dataset.act === 'edit') startEditing(id);
    if (b.dataset.act === 'del')  { features = features.filter(x => x.props.id !== id); if (editingId === id) stopEditing(); syncDraw(); refreshManager(); }
    if (b.dataset.act === 'zoom') { const bnd = boundsOf(f); if (bnd) map.fitBounds(bnd, { padding: 60, maxZoom: 17 }); }
  });
}
function boundsOf(f) {
  let minX = 1e9, minY = 1e9, maxX = -1e9, maxY = -1e9, ok = false;
  const walk = c => { if (typeof c[0] === 'number') { ok = true;
    minX = Math.min(minX, c[0]); maxX = Math.max(maxX, c[0]);
    minY = Math.min(minY, c[1]); maxY = Math.max(maxY, c[1]); } else c.forEach(walk); };
  walk(f.geometry.coordinates);
  if (!ok) return null;
  if (minX === maxX && minY === maxY) return [[minX - 0.005, minY - 0.005], [maxX + 0.005, maxY + 0.005]];
  return [[minX, minY], [maxX, maxY]];
}

// ---------------- search ----------------
$('searchbtn').onclick = () => { $('panel').classList.add('open'); $('db-toggle').classList.add('active'); $('searchInput').focus(); };
$('searchInput').addEventListener('keydown', e => {
  if (e.key !== 'Enter') return;
  const q = e.target.value.trim(); if (!q) return;
  hint('Searching…');
  fetch(`https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(q)}`)
    .then(r => r.json())
    .then(j => { if (j.length) { map.flyTo({ center: [parseFloat(j[0].lon), parseFloat(j[0].lat)], zoom: 15 }); hint(''); } else hint('No results'); })
    .catch(() => hint('Search failed'));
});

// ---------------- basemap switcher ----------------
$('basemap-btn').onclick = () => { $('panel').classList.add('open'); $('db-toggle').classList.add('active'); };
$('bmGrid').innerHTML = Object.keys(ALL_STYLES).map(n =>
  `<button data-n="${n}" class="${n === __INIT_NAME__ ? 'active' : ''}">${n}</button>`).join('');
$('bmGrid').querySelectorAll('button').forEach(b => b.onclick = () => {
  $('bmGrid').querySelectorAll('button').forEach(x => x.classList.toggle('active', x === b));
  map.setStyle(ALL_STYLES[b.dataset.n]);
  map.once('idle', () => {
    // setStyle wipes layers + images -> rebuild icons, draw stack, visibility
    usedIcons.forEach((v, key) => { if (!map.hasImage(key)) {
      try { map.addImage(key, drawIcon(v.shape, v.color).getContext('2d').getImageData(0, 0, 48, 48)); } catch (e) {} } });
    addDrawStack(); applyVis(); renderHandles();
  });
});

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
    body_bg = THEMES[INITIAL_BASEMAP]["overlay"]
    muted = THEMES[INITIAL_BASEMAP]["muted"]
    html = (HTML_TEMPLATE
            .replace("__ALL_STYLES__", json.dumps(ALL_STYLES))
            .replace("__STYLE__", json.dumps(ALL_STYLES[INITIAL_BASEMAP]))
            .replace("__INIT_NAME__", json.dumps(INITIAL_BASEMAP))
            .replace("__CENTER__", json.dumps(CENTER))
            .replace("__ZOOM__", str(ZOOM))
            .replace("__BG__", body_bg)
            .replace("__MUTED__", muted))
    components.html(html, height=950, scrolling=False)
except Exception as e:
    st.error(f"Map render failed: {e}")

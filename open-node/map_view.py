"""
map_view.py – builds and renders the Leaflet HTML iframe.

Security: all Python→JS data passes through json.dumps(ensure_ascii=True),
then is assigned to a JS variable block at the top of the <script> section.
No user data is interpolated into raw JS expression positions.
"""

import json
import streamlit as st
import streamlit.components.v1 as components

# ─────────────────────────────────────────────────────────────────────────────
# PALETTE  (Google My Maps accent colours)
# ─────────────────────────────────────────────────────────────────────────────
LAYER_PALETTE = [
    "#1a73e8", "#34a853", "#ea4335", "#fbbc04",
    "#9334e6", "#00897b", "#e64a19", "#039be5",
    "#43a047", "#8d6e63",
]


def _safe_json(obj) -> str:
    """JSON-encode and HTML-escape closing script tags to prevent XSS."""
    return json.dumps(obj, ensure_ascii=True).replace("</", r"<\/")


def render_leaflet_component_iframe(
    lat: float,
    lon: float,
    radius: int,
    pts_active: list[dict],
) -> None:
    unique_layers = list({p.get("type", "Unclassified") for p in pts_active})
    for idx, layer in enumerate(unique_layers):
        if layer not in st.session_state.layer_meta:
            st.session_state.layer_meta[layer] = {
                "color": LAYER_PALETTE[idx % len(LAYER_PALETTE)],
                "style": st.session_state.global_marker_style,
                "size":  st.session_state.global_marker_size,
            }

    is_stale    = lat != st.session_state.last_scan_lat or lon != st.session_state.last_scan_lon
    show_loading = st.session_state.scan_active_loading

    # ── Safe JS variable block ──────────────────────────────────────────────
    js_vars = f"""
    const LAT           = {_safe_json(lat)};
    const LON           = {_safe_json(lon)};
    const RADIUS        = {_safe_json(radius)};
    const IS_STALE      = {_safe_json(is_stale)};
    const SHOW_LOADING  = {_safe_json(show_loading)};
    const LAYER_META    = {_safe_json(st.session_state.layer_meta)};
    const TARGET_CFG    = {_safe_json(st.session_state.target_config)};
    const RADIUS_CFG    = {_safe_json(st.session_state.radius_config)};
    const PTS_RAW       = {_safe_json(pts_active)};
    const LEGEND_LAYERS = {_safe_json(st.session_state.legend_layers)};
    const MARKER_SIZE   = {_safe_json(st.session_state.global_marker_size)};
    const MARKER_COLOR  = {_safe_json(st.session_state.global_marker_color)};
    """

    html = _build_html(js_vars)
    components.html(html, height=800, scrolling=False)


# ─────────────────────────────────────────────────────────────────────────────
# HTML BUILDER
# ─────────────────────────────────────────────────────────────────────────────
def _build_html(js_vars: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body,html{{height:100%;width:100%;background:#e8eaed;overflow:hidden;font-family:'Roboto',Arial,sans-serif;}}
#map{{height:100vh;width:100%;z-index:1;}}

/* Loading overlay */
#loading-overlay{{
  position:fixed;inset:0;background:rgba(255,255,255,0.82);z-index:9999;
  display:none;flex-direction:column;align-items:center;justify-content:center;gap:12px;
}}
.spinner{{width:36px;height:36px;border:3px solid rgba(26,115,232,0.15);border-left-color:#1a73e8;border-radius:50%;animation:spin 0.8s linear infinite;}}
.loading-label{{font-size:12px;font-weight:500;color:#1a73e8;letter-spacing:0.3px;}}
@keyframes spin{{to{{transform:rotate(360deg);}}}}

/* Right panel */
#panel{{
  position:fixed;top:0;right:0;bottom:0;width:320px;
  background:#fff;z-index:1000;display:flex;flex-direction:column;
  box-shadow:-2px 0 8px rgba(0,0,0,0.15);overflow:hidden;
}}
.panel-header{{
  background:#1a73e8;color:#fff;padding:0 16px;height:56px;
  display:flex;align-items:center;justify-content:space-between;flex-shrink:0;
}}
.panel-header-title{{font-size:14px;font-weight:500;letter-spacing:0.1px;}}
.panel-count{{font-size:11px;background:rgba(255,255,255,0.2);padding:2px 8px;border-radius:12px;}}
.panel-body{{flex:1;overflow-y:auto;scrollbar-width:thin;scrollbar-color:rgba(0,0,0,0.2) transparent;}}
.panel-body::-webkit-scrollbar{{width:4px;}}
.panel-body::-webkit-scrollbar-thumb{{background:rgba(0,0,0,0.2);border-radius:2px;}}

/* Section headers inside panel */
.section-label{{
  font-size:10px;font-weight:700;color:#5f6368;text-transform:uppercase;
  letter-spacing:0.8px;padding:12px 16px 6px;background:#f8f9fa;
  border-bottom:1px solid #e8eaed;
}}
.config-row{{
  display:flex;align-items:center;gap:8px;padding:8px 16px;
  border-bottom:1px solid #f1f3f4;font-size:11px;color:#3c4043;
}}
.config-row label{{flex-shrink:0;font-size:10px;color:#5f6368;min-width:52px;}}
.config-row select,.config-row input[type=color]{{
  font-size:10px;font-family:Roboto,sans-serif;color:#202124;
  background:#fff;border:1px solid #dadce0;border-radius:4px;padding:2px 6px;outline:none;
  cursor:pointer;
}}
.config-row select:focus{{border-color:#1a73e8;}}
.slider{{flex:1;-webkit-appearance:none;height:3px;background:#dadce0;border-radius:2px;outline:none;}}
.slider::-webkit-slider-thumb{{-webkit-appearance:none;width:14px;height:14px;border-radius:50%;background:#1a73e8;cursor:pointer;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,0.3);}}

/* Layer rows */
.layer-block{{border-bottom:1px solid #e8eaed;}}
.layer-header{{
  display:flex;align-items:center;padding:10px 16px;cursor:pointer;
  gap:10px;transition:background 0.15s;
}}
.layer-header:hover{{background:#f8f9fa;}}
.layer-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0;border:1.5px solid rgba(0,0,0,0.1);}}
.layer-name{{flex:1;font-size:12px;font-weight:500;color:#202124;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.layer-count{{font-size:10px;color:#1a73e8;font-weight:600;margin-right:4px;}}
.layer-actions{{display:flex;align-items:center;gap:2px;}}
.icon-btn{{
  width:28px;height:28px;border-radius:50%;border:none;background:transparent;
  cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background 0.15s;
}}
.icon-btn:hover{{background:#f1f3f4;}}
.icon-btn svg{{width:14px;height:14px;fill:#5f6368;}}
.icon-btn.del:hover svg{{fill:#ea4335;}}
.icon-btn.legend-on svg{{fill:#1a73e8;}}
.layer-style-row{{
  display:flex;align-items:center;gap:6px;padding:4px 16px 8px 36px;
}}
.layer-style-row select{{font-size:10px;font-family:Roboto;border:1px solid #dadce0;border-radius:4px;padding:2px 4px;color:#202124;background:#fff;outline:none;}}
.layer-items{{background:#f8f9fa;}}
.layer-items.collapsed{{display:none;}}
.poi-item{{
  display:flex;align-items:center;padding:6px 16px 6px 36px;
  border-bottom:1px solid #f1f3f4;cursor:pointer;transition:background 0.12s;gap:8px;
}}
.poi-item:hover{{background:#fff;}}
.poi-name{{flex:1;font-size:11px;color:#3c4043;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.poi-item.hidden .poi-name{{opacity:0.4;}}
.poi-actions{{display:flex;gap:1px;}}

/* Export FAB */
#export-fab{{
  position:fixed;bottom:24px;left:24px;z-index:999;
  width:48px;height:48px;border-radius:50%;background:#1a73e8;border:none;
  display:flex;align-items:center;justify-content:center;cursor:pointer;
  box-shadow:0 2px 8px rgba(0,0,0,0.3);transition:background 0.15s,transform 0.15s;
}}
#export-fab:hover{{background:#1557b0;transform:scale(1.05);}}
#export-fab svg{{fill:#fff;width:22px;height:22px;}}

/* Group cluster */
.cluster-block{{border-left:3px solid #1a73e8;background:#f0f7ff;border-bottom:1px solid #e8eaed;}}
.cluster-header{{display:flex;align-items:center;padding:8px 16px;gap:8px;cursor:pointer;}}
.cluster-name{{flex:1;font-size:11px;font-weight:600;color:#1a73e8;}}
.cluster-items{{background:#e8f0fe;padding:0 0 0 12px;}}
.cluster-items.collapsed{{display:none;}}

/* Tooltip labels */
.poi-label{{
  background:#fff;border:1px solid rgba(0,0,0,0.15);padding:2px 6px;
  border-radius:3px;font-size:10px;font-family:Roboto,sans-serif;
  font-weight:500;white-space:nowrap;box-shadow:0 1px 3px rgba(0,0,0,0.15);
}}
#map.hide-labels .poi-label{{display:none!important;}}

/* Group layer modal */
#group-modal{{
  display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:99999;
  align-items:center;justify-content:center;
}}
#group-modal.open{{display:flex;}}
.modal-card{{
  background:#fff;border-radius:8px;width:340px;max-height:80vh;overflow:hidden;
  display:flex;flex-direction:column;box-shadow:0 8px 24px rgba(0,0,0,0.2);
}}
.modal-header{{background:#1a73e8;color:#fff;padding:14px 18px;font-size:13px;font-weight:500;display:flex;justify-content:space-between;align-items:center;}}
.modal-body{{padding:16px;overflow-y:auto;flex:1;}}
.modal-input{{width:100%;border:1px solid #dadce0;border-radius:4px;padding:8px 10px;font-size:12px;font-family:Roboto;outline:none;}}
.modal-input:focus{{border-color:#1a73e8;}}
.modal-chk-row{{display:flex;align-items:center;gap:8px;padding:6px 0;font-size:11px;color:#202124;border-bottom:1px solid #f1f3f4;}}
.modal-chk-row input{{accent-color:#1a73e8;}}
.modal-footer{{padding:12px 16px;border-top:1px solid #e8eaed;display:flex;gap:8px;justify-content:flex-end;}}
.btn-primary{{background:#1a73e8;color:#fff;border:none;padding:8px 20px;border-radius:4px;font-size:12px;font-weight:500;cursor:pointer;}}
.btn-primary:hover{{background:#1557b0;}}
.btn-ghost{{background:transparent;color:#5f6368;border:1px solid #dadce0;padding:8px 16px;border-radius:4px;font-size:12px;cursor:pointer;}}
.btn-ghost:hover{{background:#f1f3f4;}}
</style>
</head>
<body>

<div id="loading-overlay">
  <div class="spinner"></div>
  <div class="loading-label" id="loading-msg">Scanning area...</div>
</div>

<div id="map"></div>

<div id="panel">
  <div class="panel-header">
    <span class="panel-header-title">Open Node</span>
    <div style="display:flex;align-items:center;gap:8px;">
      <span id="group-layers-btn" onclick="openGroupModal()" style="font-size:10px;font-weight:600;cursor:pointer;padding:4px 10px;border:1px solid rgba(255,255,255,0.4);border-radius:12px;">Group layers</span>
      <span class="panel-count" id="results-count">0</span>
    </div>
  </div>
  <div class="panel-body" id="panel-body">

    <!-- Basemap -->
    <div class="section-label">Basemap</div>
    <div class="config-row">
      <label>Tiles</label>
      <select id="basemap-sel" onchange="switchBasemap(this.value)">
        <option value="osm">OpenStreetMap</option>
        <option value="satellite">Satellite</option>
        <option value="carto">Carto Light</option>
      </select>
      <label style="margin-left:auto;display:flex;align-items:center;gap:4px;cursor:pointer;">
        <input type="checkbox" id="labels-chk" onchange="toggleLabels(this.checked)" style="accent-color:#1a73e8;"> Labels
      </label>
    </div>

    <!-- Global markers -->
    <div class="section-label">Global Markers</div>
    <div class="config-row">
      <label>Style</label>
      <select id="gl-style" onchange="patchAllStyle(this.value)">
        <option value="dots">Dot</option>
        <option value="pin">Pin</option>
        <option value="modern-pin">Drop Pin</option>
      </select>
      <label>Size</label>
      <input type="range" min="8" max="36" value="12" step="1" class="slider" id="gl-size" oninput="patchAllSize(this.value)">
    </div>
    <div class="config-row">
      <label>Color</label>
      <input type="color" id="gl-color" value="#1a73e8" onchange="patchAllColor(this.value)">
      <select onchange="document.getElementById('gl-color').value=this.value;patchAllColor(this.value);" style="font-size:10px;border:1px solid #dadce0;border-radius:4px;padding:2px 4px;">
        <option value="">Preset</option>
        <option value="#1a73e8">Blue</option>
        <option value="#34a853">Green</option>
        <option value="#ea4335">Red</option>
        <option value="#fbbc04">Yellow</option>
        <option value="#9334e6">Purple</option>
      </select>
    </div>

    <!-- Target + Radius -->
    <div class="section-label">Target & Radius</div>
    <div class="config-row">
      <label>Target</label>
      <select onchange="patchTarget('style',this.value)"><option value="star">Star</option><option value="circle">Dot</option></select>
      <input type="color" value="#1a73e8" onchange="patchTarget('color',this.value)">
      <input type="range" min="10" max="56" value="24" step="1" class="slider" oninput="patchTarget('size',this.value)">
    </div>
    <div class="config-row">
      <label>Fill</label>
      <input type="color" value="#1a73e8" onchange="patchRadius('color',this.value)">
      <label>Opacity</label>
      <input type="range" min="0" max="1" step="0.01" value="0.08" class="slider" oninput="patchRadius('fill_opacity',this.value)">
    </div>
    <div class="config-row">
      <label>Weight</label>
      <input type="range" min="0.5" max="8" step="0.5" value="1.5" class="slider" oninput="patchRadius('weight',this.value)">
    </div>

    <!-- Layers list -->
    <div class="section-label" style="display:flex;justify-content:space-between;align-items:center;">
      <span>Layers</span>
    </div>
    <div id="layers-list"></div>

  </div>
</div>

<!-- Group layer modal -->
<div id="group-modal">
  <div class="modal-card">
    <div class="modal-header">
      <span>Create layer group</span>
      <span onclick="closeGroupModal()" style="cursor:pointer;font-size:18px;opacity:0.8;">✕</span>
    </div>
    <div class="modal-body">
      <input type="text" id="group-name-input" class="modal-input" placeholder="Group name..." style="margin-bottom:12px;">
      <div id="group-chk-list"></div>
    </div>
    <div class="modal-footer">
      <button class="btn-ghost" onclick="closeGroupModal()">Cancel</button>
      <button class="btn-primary" onclick="commitGroup()">Create group</button>
    </div>
  </div>
</div>

<button id="export-fab" onclick="runExport()" title="Export map">
  <svg viewBox="0 0 24 24"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM17 13l-5 5-5-5h3V9h4v4h3z"/></svg>
</button>

<script>
// ── Safe JS data injected by Python ─────────────────────────────────────────
{js_vars}

// ── Mutable state (copies from injected consts) ──────────────────────────────
let layerMeta    = JSON.parse(JSON.stringify(LAYER_META));
let targetCfg    = JSON.parse(JSON.stringify(TARGET_CFG));
let radiusCfg    = JSON.parse(JSON.stringify(RADIUS_CFG));
let pts          = JSON.parse(JSON.stringify(PTS_RAW));
let legendLayers = JSON.parse(JSON.stringify(LEGEND_LAYERS));
let clusters     = {{}};
const categoryMap = {{}};

// ── Map init ─────────────────────────────────────────────────────────────────
const map = L.map('map', {{zoomControl:true, attributionControl:false, preferCanvas:true}})
             .setView([LAT, LON], 14);

map.zoomControl.setPosition('bottomleft');

const basemaps = {{
  osm:       L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{maxZoom:19}}),
  satellite: L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={{x}}&y={{y}}&z={{z}}', {{maxZoom:20}}),
  carto:     L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{maxZoom:20}}),
}};

const storedBm = (() => {{ try {{ return localStorage.getItem('on_basemap') || 'osm'; }} catch(e) {{ return 'osm'; }} }})();
try {{ document.getElementById('basemap-sel').value = storedBm; }} catch(e) {{}}
basemaps[storedBm].addTo(map);

function switchBasemap(k) {{
  Object.keys(basemaps).forEach(b => {{ if(map.hasLayer(basemaps[b])) map.removeLayer(basemaps[b]); }});
  basemaps[k].addTo(map);
  try {{ localStorage.setItem('on_basemap', k); }} catch(e) {{}}
}}

let labelsOn = true;
try {{ labelsOn = localStorage.getItem('on_labels') !== 'false'; }} catch(e) {{}}
document.getElementById('labels-chk').checked = labelsOn;
if (!labelsOn) map.getContainer().classList.add('hide-labels');

function toggleLabels(v) {{
  map.getContainer().classList.toggle('hide-labels', !v);
  try {{ localStorage.setItem('on_labels', v); }} catch(e) {{}}
}}

if (SHOW_LOADING) {{
  document.getElementById('loading-overlay').style.display = 'flex';
}}

// ── Radius + target ───────────────────────────────────────────────────────────
let radiusCircle = null, centerMarker = null;

function drawRadius() {{
  if (radiusCircle) map.removeLayer(radiusCircle);
  radiusCircle = L.circle([LAT, LON], {{
    radius: RADIUS, color: radiusCfg.color,
    weight: parseFloat(radiusCfg.weight),
    fillColor: radiusCfg.color, fillOpacity: parseFloat(radiusCfg.fill_opacity),
  }}).addTo(map);
}}

function drawCenter() {{
  if (centerMarker) map.removeLayer(centerMarker);
  const d = parseInt(targetCfg.size), c = targetCfg.color;
  const inner = targetCfg.style === 'star'
    ? `<div style="background:${{c}};color:#fff;width:${{d}}px;height:${{d}}px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:${{d*0.5}}px;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.3);">★</div>`
    : `<div style="background:${{c}};width:${{d}}px;height:${{d}}px;border-radius:50%;border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.4);"></div>`;
  centerMarker = L.marker([LAT, LON], {{
    icon: L.divIcon({{className:'', html: inner, iconSize:[d,d], iconAnchor:[d/2,d/2]}}),
    zIndexOffset: 99999,
  }}).addTo(map);
}}

window.patchTarget = (k,v) => {{ targetCfg[k]=v; drawCenter(); }};
window.patchRadius = (k,v) => {{ radiusCfg[k]=v; drawRadius(); if(centerMarker) centerMarker.bringToFront(); }};

// ── Marker factory ────────────────────────────────────────────────────────────
function makeIcon(color, style, size) {{
  const d = parseInt(size);
  if (style === 'pin') {{
    return L.divIcon({{
      html: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${{d*1.4}}" height="${{d*1.4}}"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" fill="${{color}}" stroke="#fff" stroke-width="1"/></svg>`,
      className:'', iconSize:[d*1.4,d*1.4], iconAnchor:[d*0.7,d*1.4],
    }});
  }} else if (style === 'modern-pin') {{
    const w=d*1.5, h=d*2.2;
    return L.divIcon({{
      html:`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 60" width="${{w}}" height="${{h}}"><circle cx="20" cy="20" r="14" fill="${{color}}" stroke="#fff" stroke-width="2"/><line x1="20" y1="34" x2="20" y2="56" stroke="${{color}}" stroke-width="3" stroke-linecap="round"/></svg>`,
      className:'', iconSize:[w,h], iconAnchor:[w/2,h],
    }});
  }}
  return L.divIcon({{
    html:`<div style="background:${{color}};width:${{d}}px;height:${{d}}px;border-radius:50%;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.25);"></div>`,
    className:'', iconSize:[d,d], iconAnchor:[d/2,d/2],
  }});
}}

// ── Layer rendering ────────────────────────────────────────────────────────────
const layerGroups = {{}};

function rebuildMap() {{
  Object.keys(categoryMap).forEach(k => delete categoryMap[k]);
  pts.forEach(p => {{
    const t = p.type || 'Unclassified';
    if (!categoryMap[t]) categoryMap[t] = [];
    categoryMap[t].push(p);
  }});
  Object.keys(layerGroups).forEach(k => {{ map.removeLayer(layerGroups[k]); delete layerGroups[k]; }});
  Object.keys(categoryMap).forEach(key => {{
    layerGroups[key] = L.layerGroup().addTo(map);
    const meta = layerMeta[key] || {{color:'#1a73e8',style:'dots',size:12}};
    categoryMap[key].forEach(p => {{
      if (p.visible === false) return;
      const m = L.marker([p.lat,p.lon], {{icon: makeIcon(meta.color, meta.style, meta.size)}})
                 .bindPopup(`<b style="font-size:12px;">${{p.name}}</b><br><span style="font-size:10px;color:#5f6368;">${{p.type}}</span>`);
      if (p.name && p.name !== 'Unknown') {{
        const zoom = map.getZoom();
        if (zoom >= 15) {{
          m.bindTooltip(p.name, {{permanent:true, direction:'top', offset:[0,-8], className:'poi-label'}});
        }}
      }}
      m.addTo(layerGroups[key]);
    }});
  }});
  if (centerMarker) centerMarker.bringToFront();
}}

map.on('zoomend', rebuildMap);

// ── Panel rendering ────────────────────────────────────────────────────────────
const SVG_TRASH = `<svg viewBox="0 0 24 24"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>`;
const SVG_EYE   = `<svg viewBox="0 0 24 24"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>`;
const SVG_EDIT  = `<svg viewBox="0 0 24 24"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>`;
const SVG_LIST  = `<svg viewBox="0 0 24 24"><path d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z"/></svg>`;
const SVG_CHEV  = (open) => `<svg viewBox="0 0 24 24" style="transition:transform .2s;transform:rotate(${{open?180:0}}deg)"><path d="M7 10l5 5 5-5z"/></svg>`;

function buildPanel() {{
  const list = document.getElementById('layers-list');
  document.getElementById('results-count').textContent = pts.length;
  if (pts.length === 0) {{
    list.innerHTML = '<div style="padding:24px 16px;text-align:center;font-size:12px;color:#5f6368;">No layers scanned yet.<br>Select POIs and scan an area.</div>';
    return;
  }}
  let html = '';

  // Cluster groups first
  Object.keys(clusters).forEach(cname => {{
    const assigned = clusters[cname] || [];
    let total = 0, visible = false, legActive = false;
    assigned.forEach(lk => {{
      if (categoryMap[lk]) {{
        total += categoryMap[lk].length;
        if (categoryMap[lk].some(p => p.visible !== false)) visible = true;
        if (legendLayers.includes(lk)) legActive = true;
      }}
    }});

    html += `
    <div class="cluster-block" id="cluster-${{cname}}">
      <div class="cluster-header">
        <span class="cluster-name" onclick="toggleEl('cluster-items-${{cname}}',${{JSON.stringify(cname)}})">📁 ${{cname}} <span style="font-size:10px;opacity:.7;">(${{total}})</span></span>
        <div class="layer-actions">
          <button class="icon-btn${{legActive?' legend-on':''}}" title="Toggle legend" onclick="toggleClusterLegend('${{cname}}',${{legActive}})">${{SVG_LIST}}</button>
          <button class="icon-btn" title="Toggle visibility" onclick="toggleClusterVis('${{cname}}',${{visible}})">${{SVG_EYE}}</button>
          <button class="icon-btn del" title="Dissolve group" onclick="dissolveCluster('${{cname}}')">${{SVG_TRASH}}</button>
          <button class="icon-btn" style="font-size:11px;" onclick="toggleEl('cluster-items-${{cname}}',${{JSON.stringify(cname)}})"><svg viewBox="0 0 24 24" id="chev-cluster-${{cname}}"><path d="M7 10l5 5 5-5z"/></svg></button>
        </div>
      </div>
      <div class="config-row" style="padding-left:16px;background:#e8f0fe;">
        <label>Batch</label>
        <select onchange="batchCluster('${{cname}}','style',this.value)"><option value="dots">Dot</option><option value="pin">Pin</option><option value="modern-pin">Drop</option></select>
        <input type="range" min="8" max="36" step="1" value="12" class="slider" oninput="batchCluster('${{cname}}','size',this.value)">
        <input type="color" value="#1a73e8" onchange="batchCluster('${{cname}}','color',this.value)">
      </div>
      <div class="cluster-items collapsed" id="cluster-items-${{cname}}">
    `;
    assigned.forEach(lk => {{
      if (!categoryMap[lk]) return;
      html += layerItemHTML(lk, true);
    }});
    html += '</div></div>';
  }});

  // Loose layers
  Object.keys(categoryMap).forEach(cat => {{
    const inCluster = Object.values(clusters).some(arr => arr.includes(cat));
    if (inCluster) return;
    html += `<div class="layer-block" id="layer-block-${{cat}}">${{layerItemHTML(cat, false)}}</div>`;
  }});

  list.innerHTML = html;
}}

function layerItemHTML(cat, nested) {{
  const meta = layerMeta[cat] || {{color:'#1a73e8',style:'dots',size:12}};
  const layerPts = categoryMap[cat] || [];
  const vis  = layerPts.some(p => p.visible !== false);
  const legOn = legendLayers.includes(cat);
  const safeId = CSS.escape(cat);

  return `
  <div style="border-bottom:1px solid #e8eaed;">
    <div class="layer-header" onclick="toggleEl('layer-items-${{cat}}',${{JSON.stringify(cat)}})">
      <span class="layer-dot" style="background:${{meta.color}};"></span>
      <span class="layer-name">${{cat}}</span>
      <span class="layer-count">${{layerPts.length}}</span>
      <div class="layer-actions" onclick="event.stopPropagation()">
        <button class="icon-btn${{legOn?' legend-on':''}}" title="Toggle legend" onclick="toggleLayerLegend(${{JSON.stringify(cat)}})">${{SVG_LIST}}</button>
        <button class="icon-btn" title="Rename" onclick="renameLayer(${{JSON.stringify(cat)}})">${{SVG_EDIT}}</button>
        <button class="icon-btn" title="Toggle visibility" onclick="toggleLayerVis(${{JSON.stringify(cat)}},${{vis}})">${{SVG_EYE}}</button>
        <button class="icon-btn del" title="Delete layer" onclick="deleteLayer(${{JSON.stringify(cat)}})">${{SVG_TRASH}}</button>
        <button class="icon-btn"><svg viewBox="0 0 24 24" id="chev-layer-${{cat}}"><path d="M7 10l5 5 5-5z"/></svg></button>
      </div>
    </div>
    <div class="layer-style-row" onclick="event.stopPropagation()">
      <select onchange="patchLayer(${{JSON.stringify(cat)}},'style',this.value)">
        <option value="dots" ${{meta.style==='dots'?'selected':''}}>Dot</option>
        <option value="pin" ${{meta.style==='pin'?'selected':''}}>Pin</option>
        <option value="modern-pin" ${{(meta.style==='modern-pin'||meta.style==='drop-pin')?'selected':''}}>Drop</option>
      </select>
      <input type="range" min="8" max="36" step="1" value="${{meta.size}}" class="slider" style="flex:1;" oninput="patchLayer(${{JSON.stringify(cat)}},'size',this.value)">
      <input type="color" value="${{meta.color}}" onchange="patchLayer(${{JSON.stringify(cat)}},'color',this.value);buildPanel();">
    </div>
    <div class="layer-items collapsed" id="layer-items-${{cat}}">
      ${{layerPts.map(p => `
        <div class="poi-item${{p.visible===false?' hidden':''}}" id="poi-${{p.uid}}">
          <span class="poi-name" title="${{p.name||'Unknown'}}" onclick="map.flyTo([${{p.lat}},${{p.lon}}],17)">${{p.name||'Unknown'}}</span>
          <div class="poi-actions">
            <button class="icon-btn" style="width:22px;height:22px;" onclick="renamePoi('${{p.uid}}','${{(p.name||'').replace(/'/g,'&#39;')}}')">${{SVG_EDIT}}</button>
            <button class="icon-btn" style="width:22px;height:22px;" onclick="togglePoiVis('${{p.uid}}')">${{SVG_EYE}}</button>
            <button class="icon-btn del" style="width:22px;height:22px;" onclick="deletePoi('${{p.uid}}',${{JSON.stringify(cat)}})">${{SVG_TRASH}}</button>
          </div>
        </div>
      `).join('')}}
    </div>
  </div>`;
}}

function toggleEl(id, key) {{
  const el = document.getElementById('layer-items-'+key) || document.getElementById(id);
  if (!el) return;
  el.classList.toggle('collapsed');
  const chev = document.getElementById('chev-layer-'+key) || document.getElementById('chev-cluster-'+key);
  if (chev) chev.style.transform = el.classList.contains('collapsed') ? '' : 'rotate(180deg)';
}}

// ── Layer/POI mutations ────────────────────────────────────────────────────────
window.patchLayer = (cat,k,v) => {{ if(!layerMeta[cat]) layerMeta[cat]={{}}; layerMeta[cat][k]=k==='size'?parseInt(v):v; rebuildMap(); }};
window.toggleLayerVis = (cat,vis) => {{ pts.forEach(p=>{{if(p.type===cat)p.visible=!vis;}}); rebuildMap(); buildPanel(); }};
window.deleteLayer = (cat) => {{ if(!confirm(`Delete layer "${{cat}}"?`)) return; pts=pts.filter(p=>p.type!==cat); delete layerMeta[cat]; Object.keys(clusters).forEach(c=>{{clusters[c]=clusters[c].filter(x=>x!==cat);}});rebuildMap();buildPanel(); }};
window.renameLayer = (old) => {{ const n=prompt('Rename layer:',old); if(!n||!n.trim()||n===old) return; pts.forEach(p=>{{if(p.type===old)p.type=n;}}); layerMeta[n]=layerMeta[old]; delete layerMeta[old]; Object.keys(clusters).forEach(c=>{{clusters[c]=clusters[c].map(x=>x===old?n:x);}});rebuildMap();buildPanel(); }};
window.toggleLayerLegend = (cat) => {{ window.parent.location.search=`?toggle_legend_layer=${{encodeURIComponent(cat)}}`; }};
window.togglePoiVis = (uid) => {{ const p=pts.find(x=>x.uid===uid); if(p){{p.visible=(p.visible===false);rebuildMap();buildPanel();}} }};
window.renamePoi = (uid,old) => {{ const n=prompt('Rename:',old); if(!n||!n.trim()) return; const p=pts.find(x=>x.uid===uid); if(p){{p.name=n;rebuildMap();buildPanel();}} }};
window.deletePoi = (uid) => {{ pts=pts.filter(x=>x.uid!==uid); rebuildMap();buildPanel(); }};

window.patchAllStyle = (v) => {{ Object.keys(layerMeta).forEach(k=>layerMeta[k].style=v); rebuildMap(); }};
window.patchAllSize  = (v) => {{ Object.keys(layerMeta).forEach(k=>layerMeta[k].size=parseInt(v)); rebuildMap(); }};
window.patchAllColor = (v) => {{ Object.keys(layerMeta).forEach(k=>layerMeta[k].color=v); rebuildMap(); buildPanel(); }};

// ── Clusters ───────────────────────────────────────────────────────────────────
window.openGroupModal = () => {{
  const chk = document.getElementById('group-chk-list');
  chk.innerHTML = Object.keys(categoryMap).map(l=>`
    <div class="modal-chk-row">
      <input type="checkbox" class="gchk" value="${{l}}" style="accent-color:#1a73e8;">
      <span>${{l}} (${{(categoryMap[l]||[]).length}})</span>
    </div>`).join('') || '<div style="font-size:11px;color:#5f6368;">No layers available.</div>';
  document.getElementById('group-name-input').value='';
  document.getElementById('group-modal').classList.add('open');
}};

window.closeGroupModal = () => document.getElementById('group-modal').classList.remove('open');

window.commitGroup = () => {{
  const name = document.getElementById('group-name-input').value.trim();
  if (!name) {{ alert('Enter a group name.'); return; }}
  const selected = [...document.querySelectorAll('.gchk:checked')].map(c=>c.value);
  if (!selected.length) {{ alert('Select at least one layer.'); return; }}
  clusters[name] = selected;
  closeGroupModal();
  buildPanel();
}};

window.dissolveCluster  = (n) => {{ delete clusters[n]; buildPanel(); }};
window.toggleClusterVis = (n,vis) => {{ (clusters[n]||[]).forEach(lk=>{{pts.forEach(p=>{{if(p.type===lk)p.visible=!vis;}});}});rebuildMap();buildPanel(); }};
window.toggleClusterLegend = (n,on) => {{ (clusters[n]||[]).forEach(lk=>{{on?legendLayers=legendLayers.filter(x=>x!==lk):(legendLayers.includes(lk)||legendLayers.push(lk));}});buildPanel(); }};
window.batchCluster = (n,k,v) => {{ (clusters[n]||[]).forEach(lk=>{{if(!layerMeta[lk])layerMeta[lk]={{}};layerMeta[lk][k]=k==='size'?parseInt(v):v;}});rebuildMap(); }};

// ── Right-click context menu ───────────────────────────────────────────────────
map.on('contextmenu', e => {{
  const lat = e.latlng.lat, lng = e.latlng.lng;
  L.popup().setLatLng(e.latlng).setContent(`
    <div style="font-family:Roboto,sans-serif;font-size:11px;color:#202124;min-width:160px;">
      <div style="font-weight:600;border-bottom:1px solid #e8eaed;padding-bottom:6px;margin-bottom:6px;">Map options</div>
      <div style="padding:5px 0;cursor:pointer;" onclick="window.parent.location.search='?lat=${{lat.toFixed(5)}}&lon=${{lng.toFixed(5)}}'; map.closePopup();">📍 Set as target</div>
      <div style="padding:5px 0;cursor:pointer;" onclick="navigator.clipboard.writeText('${{lat.toFixed(5)}}, ${{lng.toFixed(5)}}');map.closePopup();">📋 Copy coordinates</div>
      <div style="padding:5px 0;cursor:pointer;" onclick="window.open('https://www.google.com/maps/search/?api=1&query=${{lat}},${{lng}}','_blank');map.closePopup();">🗺 Open in Google Maps</div>
      <div style="padding:5px 0;cursor:pointer;" onclick="window.open('https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${{lat}},${{lng}}','_blank');map.closePopup();">📸 Street View</div>
    </div>`).openOn(map);
}});

// ── Export ─────────────────────────────────────────────────────────────────────
window.runExport = () => {{
  const overlay = document.getElementById('loading-overlay');
  document.getElementById('loading-msg').textContent = 'Exporting map...';
  overlay.style.display = 'flex';
  const bm = document.getElementById('basemap-sel').value;
  if (bm === 'satellite') {{
    alert('Satellite tiles are cross-origin and cannot be exported due to browser CORS restrictions. Switch to OpenStreetMap or Carto for export.');
    overlay.style.display = 'none';
    return;
  }}
  html2canvas(document.getElementById('map'), {{useCORS: true, allowTaint: false, scale:2}})
    .then(canvas => {{
      const a = document.createElement('a');
      a.download = `opennode-export-${{Date.now()}}.png`;
      a.href = canvas.toDataURL('image/png');
      a.click();
    }})
    .catch(err => console.error('Export error:', err))
    .finally(() => {{ overlay.style.display = 'none'; }});
}};

// ── Boot ───────────────────────────────────────────────────────────────────────
drawRadius();
drawCenter();
rebuildMap();
buildPanel();

if (pts.length > 0 && !IS_STALE) {{
  const valid = pts.filter(p => p.visible !== false);
  if (valid.length > 0) {{
    const grp = L.featureGroup([L.marker([LAT,LON]), ...valid.map(p=>L.marker([p.lat,p.lon]))]);
    map.fitBounds(grp.getBounds().pad(0.05));
  }}
}}
</script>
</body>
</html>"""

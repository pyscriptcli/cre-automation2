import streamlit as st
import streamlit.components.v1 as components

# Requires: pip install streamlit
# Run: streamlit run app.py
# Internet needed at runtime for Leaflet CDN + OSM tiles.

st.set_page_config(page_title="Industrial Intelligence", layout="wide", initial_sidebar_state="collapsed")

# Hide Streamlit chrome, disable scrolling on the main window, and aggressively 
# force the injected iframe to fixed full-screen dimensions.
st.markdown("""
<style>
/* Reset all margins, paddings, and hide overflow globally */
html, body, [data-testid="stAppViewContainer"], .main, .block-container {
    margin: 0 !important;
    padding: 0 !important;
    max-width: 100% !important;
    width: 100% !important;
    height: 100% !important;
    overflow: hidden !important;
    background: #2a2a2a;
}

/* Hide header and footer */
header, footer, #MainMenu {
    display: none !important;
}

/* Remove scrollbars */
::-webkit-scrollbar {
    display: none !important;
}

/* Aggressively force the iframe to lock to the viewport boundaries */
iframe {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    border: none !important;
    margin: 0 !important;
    padding: 0 !important;
    z-index: 999999 !important;
}
</style>
""", unsafe_allow_html=True)

APP_HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.css">
<style>
* {box-sizing:border-box; margin:0; padding:0; font-family:'Segoe UI', -apple-system, Helvetica, Arial, sans-serif;}
html, body {height:100%; width:100%; overflow:hidden;}
body {background:#2a2a2a;}

/* Removed inset to make the UI true full-screen */
#app {position:absolute; top:0; left:0; right:0; bottom:0; overflow:hidden; background:#fff;}

svg {vertical-align:middle;}
button {background:none; border:none; cursor:pointer; color:inherit; font:inherit;}

/* ---------- Top bar ---------- */
#topbar {position:absolute; top:0; left:0; right:0; height:34px; background:#141414; color:#ddd;
  display:flex; align-items:center; justify-content:space-between; padding:0 10px; z-index:1200; font-size:12px;}
.tb-left, .tb-right {display:flex; align-items:center; gap:8px;}
.logo {width:20px; height:20px; background:#fff; border-radius:50%; display:flex; align-items:center; justify-content:center;}
.app-title {font-weight:700; color:#fff; font-size:12px;}
.vis-badge {display:flex; align-items:center; gap:5px; background:#262626; border:1px solid #3a3a3a; color:#bbb;
  padding:2px 8px; border-radius:3px; font-size:11px;}
.tb-icon {color:#8a8a8a; padding:2px;}
.tb-icon:hover {color:#fff;}
.user {display:flex; align-items:center; gap:5px; color:#ccc; font-size:11px;}
.vsep {width:1px; height:14px; background:#444;}
.help {display:flex; align-items:center; gap:5px; color:#ccc; font-size:11px;}
.pill {display:flex; align-items:center; gap:6px; background:#2e2e2e; border:1px solid #555; color:#ddd;
  padding:3px 12px; border-radius:12px; font-size:11px;}
.pill:hover {background:#3a3a3a;}
.pill.save {background:#242424; border-color:#333; color:#666; cursor:default;}

/* ---------- Left toolbar ---------- */
#toolbar {position:absolute; top:34px; left:0; bottom:0; width:38px; background:#fff; border-right:1px solid #bbb;
  display:flex; flex-direction:column; align-items:center; padding-top:6px; gap:2px; z-index:1100;}
#toolbar button {width:28px; height:28px; display:flex; align-items:center; justify-content:center; color:#444; border-radius:3px;}
#toolbar button:hover {background:#eee;}
#toolbar button.active {background:#e0e0e0; box-shadow:inset 0 0 0 1px #888;}
.tsep {width:22px; height:1px; background:#ddd; margin:4px 0;}

/* ---------- Data browser ---------- */
#databrowser {position:absolute; top:42px; left:46px; bottom:120px; width:300px; background:#fff;
  box-shadow:0 1px 4px rgba(0,0,0,.3); z-index:1100; display:flex; flex-direction:column;}
.db-head {display:flex; align-items:center; gap:8px; padding:12px 12px 8px 12px; font-size:14px; position:relative;}
.db-head b {font-size:14px;}
.db-actions {position:absolute; right:8px; top:8px; display:flex; gap:4px;}
.db-actions button {width:22px; height:22px; border:1px solid #ccc; background:#fff; color:#555; border-radius:2px;
  display:flex; align-items:center; justify-content:center;}
.db-actions button:hover {background:#eee;}
.db-body {padding:4px 12px; overflow:auto; flex:1;}
.filters-btn {display:flex; align-items:center; gap:6px; border:1px solid #ccc; background:#fff; color:#333;
  padding:5px 12px; border-radius:3px; font-size:12px; margin:6px 0 12px 0;}
.filters-btn:hover {background:#f2f2f2;}
.layers-head {display:flex; justify-content:space-between; align-items:center; border-top:1px solid #ddd; padding-top:10px;}
.layers-head span:first-child {font-weight:700; font-size:13px;}
.lh-icons {display:flex; gap:8px; color:#777;}
.layer-row {display:flex; align-items:center; gap:8px; background:#ededed; border:2px solid transparent;
  border-radius:2px; padding:7px 8px; margin:8px 0; font-size:12px; color:#333; cursor:pointer;}
.layer-row.selected {border-color:#222;}
.layer-row.disabled {color:#a5a5a5; background:#ececec;}
.lname {flex:1;}
.row-icons {display:flex; gap:6px; color:#b5b5b5;}

/* ---------- Details panel ---------- */
#details {position:absolute; top:42px; right:10px; width:292px; background:#fff; box-shadow:0 1px 4px rgba(0,0,0,.3);
  z-index:1100; padding:16px; max-height:calc(100% - 160px); overflow:auto;}
#details-close {position:absolute; right:10px; top:10px; color:#999;}
#details-close:hover {color:#333;}
#details h1 {font-size:22px; font-weight:600; color:#1a1a1a; border-bottom:2px solid #3f8fd2; padding-bottom:8px; margin-bottom:12px;}
#details h2 {font-size:15px; font-weight:600; color:#1a1a1a; border-bottom:2px solid #3f8fd2; padding-bottom:6px; margin-top:14px;}
.hint {font-size:13px; color:#6b7c93; line-height:1.5; margin-bottom:10px;}
.lbl {font-size:10px; letter-spacing:.5px; color:#8a8a8a; text-transform:uppercase; margin-top:10px;}
.val {font-size:13px; color:#333; margin-top:2px;}
#details hr {border:none; border-top:1px solid #ddd; margin:12px 0;}
.metrics {display:grid; grid-template-columns:1fr 1fr; gap:14px 10px; margin-top:12px;}
.metric .lbl {margin-top:0; font-size:9px;}
.metric .mval {font-size:13px; font-weight:700; color:#222; margin-top:3px;}
.delta {font-size:11px; font-weight:600; margin-left:4px;}
.up {color:#188038;} .down {color:#d93025;} .flat {color:#80868b;}
.foot {font-size:11px; color:#8a8a8a; line-height:1.5; margin-top:10px;}

/* ---------- Map ---------- */
#map {position:absolute; top:34px; left:0; right:0; bottom:0; z-index:1; background:#cfe9e4;}
.leaflet-container {font:inherit;}
</style>
</head>
<body>
<div id="app">

  <!-- Top bar -->
  <div id="topbar">
    <div class="tb-left">
      <div class="logo"><svg viewBox="0 0 24 24" width="12" height="12"><path d="M12 2l7 10-7 10L5 12z" fill="#111"/></svg></div>
      <span class="app-title">Industrial Intelligence</span>
      <span class="vis-badge"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/></svg>Visibility: Draft (private)</span>
      <button class="tb-icon" title="Undo"><svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 7 4 7 10"/><path d="M3.5 15a9 9 0 1 0 2-9.4L1 10"/></svg></button>
      <button class="tb-icon" title="Redo"><svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 17 4 17 10"/><path d="M20.5 15a9 9 0 1 1-2-9.4L23 10"/></svg></button>
    </div>
    <div class="tb-right">
      <span class="user"><svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/></svg>User1306</span>
      <span class="vsep"></span>
      <span class="help"><svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 0 1 5 0c0 2-2.5 2-2.5 4"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>Help</span>
      <button class="pill"><svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/></svg>View</button>
      <button class="pill save" disabled><svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>Save draft</button>
    </div>
  </div>

  <!-- Map -->
  <div id="map"></div>

  <!-- Left toolbar -->
  <div id="toolbar">
    <button id="zoomin" title="Zoom in"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg></button>
    <button id="zoomout" title="Zoom out"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/></svg></button>
    <div class="tsep"></div>
    <button id="searchbtn" title="Search"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.5" y2="16.5"/></svg></button>
    <button class="tool" data-tool="polyline" title="Draw line"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"/></svg></button>
    
    <!-- Data Browser icon -->
    <button id="togglebrowser" title="Toggle Data Browser"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"/><path d="M2 12l10 6 10-6"/><path d="M2 16l10 6 10-6"/></svg></button>
    
    <button class="tool" data-tool="polygon" title="Draw polygon"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l8 6-3 10H7L4 9z"/></svg></button>
    <button class="tool" data-tool="rectangle" title="Draw rectangle"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16"/></svg></button>
    <button class="tool" data-tool="circle" title="Draw circle"><svg viewBox="0 0 24 24" width="14" height="14"><circle cx="12" cy="12" r="8" fill="currentColor"/></svg></button>
    <button class="tool" data-tool="marker" title="Place marker"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg></button>
    <div class="tsep"></div>
    <button id="editbtn" title="Edit drawings"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4v16h16v-7"/><path d="M18 2l4 4-10 10H8v-4z"/></svg></button>
    <button id="clearbtn" title="Clear drawings"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/></svg></button>
  </div>

  <!-- Data browser -->
  <div id="databrowser">
    <div class="db-head">
      <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="#333" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"/><path d="M2 12l10 6 10-6"/><path d="M2 16l10 6 10-6"/></svg>
      <b>Data browser</b>
      <div class="db-actions">
        <button id="db-collapse" title="Collapse"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polyline points="14 6 8 12 14 18"/></svg></button>
        <button id="db-close" title="Close"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg></button>
      </div>
    </div>
    <div class="db-body" id="db-body">
      <button class="filters-btn"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 3H2l8 9v7l4 2v-9z"/></svg>Filters</button>
      <div class="layers-head">
        <span>Layers</span>
        <span class="lh-icons">
          <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>
          <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/></svg>
          <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><circle cx="7.5" cy="15.5" r="4.5"/><path d="M11 12l9-9"/><path d="M17 6l3 3"/></svg>
        </span>
      </div>

      <div class="layer-row selected" id="layer-roads">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M22 19V7H12l-2-2H2v14z"/></svg>
        <span class="lname">Roads</span>
        <span class="row-icons">
          <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"/></svg>
          <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/></svg>
          <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><circle cx="7.5" cy="15.5" r="4.5"/><path d="M11 12l9-9"/></svg>
          <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"/></svg>
          <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/></svg>
        </span>
      </div>

      <div class="layer-row disabled" id="layer-boundaries">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M22 19V7H12l-2-2H2v14z"/></svg>
        <span class="lname">Boundaries</span>
        <span class="row-icons">
          <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"/></svg>
          <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/></svg>
          <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><circle cx="7.5" cy="15.5" r="4.5"/><path d="M11 12l9-9"/></svg>
          <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"/></svg>
          <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/></svg>
        </span>
      </div>
    </div>
  </div>

  <!-- Details panel -->
  <div id="details">
    <button id="details-close"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg></button>
    <h1>Details</h1>
    <p class="hint">Click on a marker, polygon, or draw on the map to see details here.</p>
    <div class="lbl">Last click</div>
    <div class="val" id="lastclick">-</div>
    <div class="lbl">Active drawings</div>
    <div class="val" id="drawcount">0</div>
    <hr>
    <h2>Advanced Analytics</h2>
    <div class="metrics">
      <div class="metric"><div class="lbl">Avg rental rate</div><div class="mval">&#8369; 850/m&#178;<span class="delta up">+3.2%</span></div></div>
      <div class="metric"><div class="lbl">Prime core index</div><div class="mval">87.5<span class="delta up">+1.8%</span></div></div>
      <div class="metric"><div class="lbl">Road density</div><div class="mval">2.4 km/km&#178;<span class="delta up">+0.3</span></div></div>
      <div class="metric"><div class="lbl">Zoning compliance</div><div class="mval">94%<span class="delta up">+2%</span></div></div>
      <div class="metric"><div class="lbl">Flood risk index</div><div class="mval">Medium (4.2)<span class="delta down">+0.5</span></div></div>
      <div class="metric"><div class="lbl">Earthquake suscept.</div><div class="mval">Low (2.1)<span class="delta flat">+0.0</span></div></div>
    </div>
    <hr>
    <p class="foot">Smart Comparable Analysis: Advanced scoring algorithms for property valuation</p>
  </div>

</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.js"></script>
<script>
try {
  // Map centered on Metro Manila to mirror the screenshot view
  var map = L.map('map', {zoomControl: false}).setView([14.63, 121.00], 11);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors under ODbL'
  }).addTo(map);
  L.control.scale({position: 'bottomleft'}).addTo(map);

  // Green boundary polygons (east metro / eco parks), visible like the photo
  var boundaries = L.layerGroup([
    L.polygon([[14.72,121.02],[14.76,121.03],[14.78,121.06],[14.74,121.07],[14.71,121.05]], {color:'#2f9e44', weight:2, fillColor:'#66bb6a', fillOpacity:0.6}),
    L.polygon([[14.75,121.10],[14.80,121.12],[14.85,121.15],[14.80,121.18],[14.70,121.16],[14.68,121.12]], {color:'#2f9e44', weight:2, fillColor:'#66bb6a', fillOpacity:0.6}),
    L.polygon([[14.60,121.10],[14.64,121.11],[14.66,121.14],[14.62,121.16],[14.58,121.13],[14.57,121.11]], {color:'#2f9e44', weight:2, fillColor:'#66bb6a', fillOpacity:0.5}),
    L.polygon([[14.52,121.11],[14.55,121.12],[14.56,121.15],[14.52,121.16],[14.50,121.13]], {color:'#2f9e44', weight:2, fillColor:'#66bb6a', fillOpacity:0.5})
  ]).addTo(map);

  // Hatched blue shipping lane across Manila Bay
  L.polyline([[14.30,120.82],[14.40,120.87],[14.50,120.93],[14.585,120.985]],
    {color:'#7ea6e0', weight:8, opacity:0.7, dashArray:'2 6', lineCap:'butt'}).addTo(map);

  // Roads highlight overlay (toggled by the Roads layer row)
  var roads = L.layerGroup([
    L.polyline([[14.67,121.03],[14.63,121.01],[14.58,120.99],[14.53,120.98],[14.50,120.96]], {color:'#e07b39', weight:3, opacity:0.7}),
    L.polyline([[14.55,121.00],[14.60,121.05],[14.65,121.10]], {color:'#e07b39', weight:3, opacity:0.7})
  ]);

  // Drawn shapes storage
  var drawnItems = L.featureGroup().addTo(map);
  function updateCount() {
    document.getElementById('drawcount').textContent = drawnItems.getLayers().length;
  }
  map.on(L.Draw.Event.CREATED, function (e) { drawnItems.addLayer(e.layer); updateCount(); });

  // Last click readout
  map.on('click', function (e) {
    document.getElementById('lastclick').textContent = e.latlng.lat.toFixed(4) + ', ' + e.latlng.lng.toFixed(4);
  });

  // Toolbar wiring
  document.getElementById('zoomin').onclick = function () { map.zoomIn(); };
  document.getElementById('zoomout').onclick = function () { map.zoomOut(); };
  document.getElementById('clearbtn').onclick = function () { drawnItems.clearLayers(); updateCount(); };
  
  // Data browser toggle wiring
  document.getElementById('togglebrowser').onclick = function () { 
      var db = document.getElementById('databrowser');
      db.style.display = (db.style.display === 'none' || db.style.display === '') ? 'flex' : 'none';
  };

  // Drawing tools via Leaflet.draw handlers (default toolbar hidden, custom buttons used)
  var drawOpts = {shapeOptions: {color: '#d33', weight: 3}};
  var handlers = {
    polyline:  new L.Draw.Polyline(map, drawOpts),
    polygon:   new L.Draw.Polygon(map, drawOpts),
    rectangle: new L.Draw.Rectangle(map, drawOpts),
    circle:    new L.Draw.Circle(map, drawOpts),
    marker:    new L.Draw.Marker(map)
  };
  var activeHandler = null;
  document.querySelectorAll('.tool').forEach(function (btn) {
    btn.onclick = function () {
      document.querySelectorAll('.tool').forEach(function (b) { b.classList.remove('active'); });
      if (activeHandler) { activeHandler.disable(); activeHandler = null; }
      activeHandler = handlers[btn.dataset.tool];
      activeHandler.enable();
      btn.classList.add('active');
    };
  });

  // Vertex editing toggle for drawn shapes
  var editMode = null, editing = false;
  document.getElementById('editbtn').onclick = function () {
    try {
      if (!editMode) editMode = new L.EditToolbar.Edit(map, {featureGroup: drawnItems});
      editing = !editing;
      editing ? editMode.enable() : editMode.disable();
      this.classList.toggle('active', editing);
    } catch (err) { console.warn('Edit mode unavailable:', err); }
  };

  // Layer rows: toggle visibility + selected/disabled styling
  function bindLayer(id, layer, initialOn) {
    var row = document.getElementById(id);
    var on = initialOn;
    row.onclick = function () {
      on = !on;
      if (on) { map.addLayer(layer); row.classList.remove('disabled'); row.classList.add('selected'); }
      else { map.removeLayer(layer); row.classList.add('disabled'); row.classList.remove('selected'); }
    };
  }
  bindLayer('layer-roads', roads, false);      // selected in photo but base map already shows roads
  bindLayer('layer-boundaries', boundaries, true); // visible in photo, row styled disabled

  // Panel controls
  document.getElementById('db-close').onclick = function () { document.getElementById('databrowser').style.display = 'none'; };
  document.getElementById('db-collapse').onclick = function () {
    var b = document.getElementById('db-body');
    b.style.display = (b.style.display === 'none') ? '' : 'none';
  };
  document.getElementById('details-close').onclick = function () { document.getElementById('details').style.display = 'none'; };
} catch (err) {
  console.error('Map init failed:', err); // UI panels still render if CDN is blocked
}
</script>
</body>
</html>
"""

# Re-added the explicit height=1080 parameter as a fallback just in case Streamlit wrappers block the CSS.
# The CSS hides the native scrollbars, so it will still behave natively.
components.html(APP_HTML, height=1080, scrolling=False)

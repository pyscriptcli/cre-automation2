import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Project Apex", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
html, body, #root, .stApp {
  height:100% !important; margin:0 !important; padding:0 !important;
  overflow:hidden !important; background:#111 !important;
}
header, footer, #MainMenu,
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDeployButton"],
[data-testid="stStatusWidget"], [data-testid="stDecoration"], [data-testid="stMainMenu"] {
  display:none !important; height:0 !important;
}
section.main, section[data-testid="stAppViewContainer"],
div[data-testid="stAppViewBlockContainer"], div[data-testid="stVerticalBlock"],
.main, .block-container {
  overflow:hidden !important; margin:0 !important; padding:0 !important;
  max-width:none !important; width:100% !important; background:transparent !important;
}
div[data-testid="stIFrame"] {
  position:fixed !important; top:0 !important; left:0 !important;
  margin:0 !important; padding:0 !important; width:100vw !important; height:100vh !important;
  border:none !important;
}
div[data-testid="stIFrame"] iframe, iframe {
  position:fixed !important; top:0 !important; left:0 !important;
  width:100vw !important; height:100vh !important; border:none !important; z-index:999990 !important;
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
html, body {height:100%; overflow:hidden;}
body {background:#2a2a2a;}
#app {position:absolute; inset:0px; overflow:hidden; background:#fff;}

svg {vertical-align:middle;}
button {background:none; border:none; cursor:pointer; color:inherit; font:inherit;}

/* ---------- Top bar ---------- */
#topbar {position:absolute; top:0; left:0; right:0; height:34px; background:#021a3d; color:#ddd;
  display:flex; align-items:center; justify-content:space-between; padding:0 10px; z-index:1200; font-size:12px;}
.tb-left, .tb-right {display:flex; align-items:center; gap:8px;}
.logo {width:20px; height:20px; background:#fff; border-radius:50%; display:flex; align-items:center; justify-content:center;}
.app-title {font-weight:700; color:#fff; font-size:12px;}
.tb-icon {color:#9fb2cc; padding:2px;}
.tb-icon:hover {color:#fff;}
.user {display:flex; align-items:center; gap:5px; color:#cdd7e6; font-size:11px;}
.vsep {width:1px; height:14px; background:#33466b;}
.help {display:flex; align-items:center; gap:5px; color:#cdd7e6; font-size:11px;}

/* ---------- Left toolbar ---------- */
#toolbar {position:absolute; top:34px; left:0; bottom:0; width:38px; background:#fff; border-right:1px solid #bbb;
  display:flex; flex-direction:column; align-items:center; padding-top:6px; gap:2px; z-index:1100;}
#toolbar button {width:28px; height:28px; display:flex; align-items:center; justify-content:center; color:#444; border-radius:3px;}
#toolbar button:hover {background:#eee;}
#toolbar button.active {background:#e0e0e0; box-shadow:inset 0 0 0 1px #888;}
.tsep {width:22px; height:1px; background:#ddd; margin:4px 0;}

/* ---------- Modals (Drawing Save/Cancel + Group Layer) ---------- */
.modal-overlay {position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.4); z-index:3000; display:none; align-items:center; justify-content:center;}
.modal-content {background:#fff; border-radius:6px; padding:20px; width:320px; max-width:90%; box-shadow:0 4px 12px rgba(0,0,0,0.3);}
.modal-content.wide {width:420px;}
.modal-title {font-size:15px; font-weight:600; color:#222; margin-bottom:12px;}
.modal-actions {display:flex; gap:10px; justify-content:flex-end; margin-top:16px;}
.modal-btn {padding:6px 14px; border-radius:3px; font-size:13px; cursor:pointer;}
.modal-btn.primary {background:#021a3d; color:#fff;}
.modal-btn.secondary {background:#eee; color:#444;}
.modal-btn.primary:hover {opacity:0.9;}
.modal-btn.secondary:hover {background:#ddd;}
.modal-input {width:100%; padding:6px; border:1px solid #ccc; border-radius:3px; font-size:13px; margin-bottom:8px;}
.group-check-list {max-height:180px; overflow-y:auto; margin:8px 0; border:1px solid #eee; padding:6px; border-radius:3px;}
.group-check-item {display:flex; align-items:center; gap:8px; padding:4px 0; font-size:12px;}

/* ---------- Basemap panel ---------- */
#basemap-panel {position:absolute; left:46px; top:140px; width:180px; background:#fff; z-index:1150;
  box-shadow:0 1px 5px rgba(0,0,0,.35); border-radius:3px; padding:6px; display:none;}
#basemap-panel.open {display:block;}
.bm-title {font-size:10px; letter-spacing:.5px; color:#8a8a8a; text-transform:uppercase; padding:4px 8px 6px 8px;}
.bm-opt {display:flex; align-items:center; gap:8px; padding:6px 8px; font-size:12px; color:#333; cursor:pointer; border-radius:3px;}
.bm-opt:hover {background:#eee;}
.bm-opt .dot {width:12px; height:12px; border-radius:50%; border:2px solid #999; flex-shrink:0;}
.bm-opt.active .dot {border-color:#021a3d; background:#021a3d; box-shadow:inset 0 0 0 2px #fff;}

/* ---------- Search panel (Container like Data Browser) ---------- */
#search-panel {position:absolute; top:42px; left:46px; width:340px; background:#fff; z-index:1150;
  box-shadow:0 1px 4px rgba(0,0,0,.3); display:none; flex-direction:column; max-height:calc(100% - 160px);}
#search-panel.open {display:flex;}
.search-head {display:flex; align-items:center; gap:8px; padding:12px 12px 8px 12px; font-size:14px; position:relative;}
.search-head b {font-size:14px;}
.search-actions {position:absolute; right:8px; top:8px; display:flex; gap:4px;}
.search-actions button {width:22px; height:22px; border:1px solid #ccc; background:#fff; color:#555; border-radius:2px; display:flex; align-items:center; justify-content:center;}
.search-actions button:hover {background:#eee;}
.search-body {padding:4px 12px 12px 12px;}
.search-input {width:100%; padding:8px; border:1px solid #ddd; border-radius:3px; font-size:13px; outline:none;}
.search-input:focus {border-color:#555;}
.search-results {margin-top:10px; max-height:200px; overflow-y:auto; border:1px solid #eee; border-radius:3px; display:none;}
.search-results.open {display:block;}
.result-item {padding:8px; border-bottom:1px solid #eee; cursor:pointer; font-size:12px; color:#222;}
.result-item:last-child {border-bottom:none;}
.result-item:hover {background:#f2f2f2;}

/* ---------- Data browser ---------- */
#databrowser {position:absolute; top:42px; left:46px; bottom:60px; width:300px; background:#fff;
  box-shadow:0 1px 4px rgba(0,0,0,.3); z-index:1100; display:flex; flex-direction:column;}
.db-head {display:flex; align-items:center; gap:8px; padding:12px 12px 8px 12px; font-size:14px; position:relative;}
.db-head b {font-size:14px;}
.db-actions {position:absolute; right:8px; top:8px; display:flex; gap:4px;}
.db-actions button {width:22px; height:22px; border:1px solid #ccc; background:#fff; color:#555; border-radius:2px;
  display:flex; align-items:center; justify-content:center;}
.db-actions button:hover {background:#eee;}
.db-body {padding:4px 12px; overflow:auto; flex:1;}

/* layer groups (dropdowns) */
.group-head {display:flex; align-items:center; gap:6px; font-weight:700; font-size:12px; color:#222;
  padding:8px 4px 4px 4px; margin-top:4px; border-top:1px solid #eee; cursor:pointer; user-select:none;}
.group-head .chev {transition:transform .15s; color:#555;}
.layer-group.collapsed .chev {transform:rotate(-90deg);}
.layer-group.collapsed .group-body {display:none;}
.group-body {padding-left:10px;}

.layers-head {display:flex; justify-content:space-between; align-items:center; border-top:1px solid #ddd; padding-top:10px; margin-top:8px;}
.layers-head span:first-child {font-weight:700; font-size:13px;}
.count-badge {background:#021a3d; color:#fff; font-size:10px; padding:1px 8px; border-radius:9px;}

.layer-row {display:flex; align-items:center; gap:8px; background:#ededed; border:2px solid transparent;
  border-radius:2px; padding:6px 8px; margin:6px 0; font-size:12px; color:#333; cursor:pointer;}
.layer-row.selected {border-color:#222;}
.layer-row.disabled {color:#a5a5a5; background:#ececec;}
.lname {flex:1; line-height:1.3;}
.row-icons {display:flex; gap:6px; color:#b5b5b5; flex-shrink:0;}
.row-icons svg {cursor:pointer;}
.row-icons svg:hover {color:#333;}
.empty-note {font-size:11px; color:#999; padding:8px 4px;}

/* ---------- Hazard Panel ---------- */
#hazard-panel {position:absolute; top:42px; right:10px; width:340px; background:#fff; 
  box-shadow:0 1px 4px rgba(0,0,0,.3); z-index:1100; padding:16px; max-height:calc(100% - 80px); overflow:auto; display:none;}
#hazard-panel.open {display:block;}
.hazard-title {font-weight:600; font-size:18px; color:#222; margin-bottom:12px;}
.hazard-card {display:flex; align-items:center; justify-content:space-between; background:#fff; border-radius:4px; 
  margin-bottom:8px; padding:10px; box-shadow:0 1px 3px rgba(0,0,0,0.15); border-left:4px solid #021a3d; position:relative;}
.hazard-card-left {display:flex; align-items:center; gap:12px;}
.hazard-icon {display:flex; align-items:center; justify-content:center; width:40px; height:40px; flex-shrink:0; color:#0066cc;}
.hazard-text-wrap {display:flex; flex-direction:column;}
.hazard-label {font-size:13px; font-weight:500; color:#444;}
.hazard-level {font-size:13px; font-weight:700; color:#222; text-transform:uppercase;}
.hazard-info {display:flex; align-items:center; justify-content:center; width:20px; height:20px; border:1px solid #555; border-radius:50%; color:#444; font-size:12px; font-weight:bold; cursor:pointer; margin-left:8px;}
.hazard-notes {margin-top:12px; font-size:11px; color:#444; line-height:1.6;}
.hazard-notes ul {padding-left:16px; margin:4px 0; list-style-type:disc;}
.hazard-notes ul li {margin-bottom:2px;}
.hazard-db-list {margin-top:8px; font-size:11px; font-weight:600; color:#555; line-height:1.5;}

/* ---------- Details panel (Dynamic layout) ---------- */
#details {position:absolute; top:42px; right:10px; width:292px; background:#fff; box-shadow:0 1px 4px rgba(0,0,0,.3);
  z-index:1090; padding:16px; max-height:calc(100% - 160px); overflow:auto; display:block;}
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
      <div class="logo"><svg viewBox="0 0 24 24" width="12" height="12"><path d="M12 2l7 10-7 10L5 12z" fill="#021a3d"/></svg></div>
      <span class="app-title">Project Apex</span>
      <button class="tb-icon" title="Undo"><svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 7 4 7 10"/><path d="M3.5 15a9 9 0 1 0 2-9.4L1 10"/></svg></button>
      <button class="tb-icon" title="Redo"><svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 17 4 17 10"/><path d="M20.5 15a9 9 0 1 1-2-9.4L23 10"/></svg></button>
    </div>
    <div class="tb-right">
      <span class="user"><svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/></svg>User1306</span>
      <span class="vsep"></span>
      <span class="help"><svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 0 1 5 0c0 2-2.5 2-2.5 4"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>Help</span>
    </div>
  </div>

  <!-- Map -->
  <div id="map"></div>

  <!-- Left toolbar -->
  <div id="toolbar">
    <button id="db-toggle" class="active" title="Toggle data browser"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"/><path d="M2 12l10 6 10-6"/><path d="M2 16l10 6 10-6"/></svg></button>
    <div class="tsep"></div>
    <button id="zoomin" title="Zoom in"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg></button>
    <button id="zoomout" title="Zoom out"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/></svg></button>
    <div class="tsep"></div>
    <button id="searchbtn" title="Search"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.5" y2="16.5"/></svg></button>
    <button id="basemap-btn" title="Basemap"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 6v16l7-4 8 4 7-4V2l-7 4-8-4z"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/></svg></button>
    <div class="tsep"></div>
    <button class="tool" data-tool="polyline" title="Draw line"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"/></svg></button>
    <button class="tool" data-tool="polygon" title="Draw polygon"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l8 6-3 10H7L4 9z"/></svg></button>
    <button class="tool" data-tool="rectangle" title="Draw rectangle"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16"/></svg></button>
    <button class="tool" data-tool="circle" title="Draw circle"><svg viewBox="0 0 24 24" width="14" height="14"><circle cx="12" cy="12" r="8" fill="currentColor"/></svg></button>
    <button class="tool" data-tool="marker" title="Place marker"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg></button>
    <div class="tsep"></div>
    <button id="editbtn" title="Edit drawings"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4v16h16v-7"/><path d="M18 2l4 4-10 10H8v-4z"/></svg></button>
    <button id="clearbtn" title="Clear drawings"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/></svg></button>
  </div>

  <!-- Basemap picker -->
  <div id="basemap-panel">
    <div class="bm-title">Basemap</div>
    <div class="bm-opt active" data-bm="osm"><span class="dot"></span>OpenStreetMap</div>
    <div class="bm-opt" data-bm="satellite"><span class="dot"></span>Satellite</div>
    <div class="bm-opt" data-bm="carto"><span class="dot"></span>CartoDB</div>
  </div>

  <!-- Search Panel (Container like Data Browser) -->
  <div id="search-panel">
    <div class="search-head">
      <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="#333" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.5" y2="16.5"/></svg>
      <b>Search places</b>
      <div class="search-actions">
        <button id="search-close" title="Close"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg></button>
      </div>
    </div>
    <div class="search-body">
      <input type="text" class="search-input" id="search-input" placeholder="Enter city, barangay, or landmark...">
      <div class="search-results" id="search-results"></div>
    </div>
  </div>

  <!-- Drawing Save/Cancel Modal -->
  <div class="modal-overlay" id="draw-modal">
    <div class="modal-content">
      <div class="modal-title">Save Drawing?</div>
      <p style="font-size:13px; color:#555; margin-bottom:12px;">Do you want to keep this shape on the map?</p>
      <div class="modal-actions">
        <button class="modal-btn secondary" id="draw-cancel">Cancel</button>
        <button class="modal-btn primary" id="draw-save">Save Drawing</button>
      </div>
    </div>
  </div>

  <!-- Group Layers Modal -->
  <div class="modal-overlay" id="group-modal">
    <div class="modal-content wide">
      <div class="modal-title">Create Layer Group</div>
      <input type="text" class="modal-input" id="group-name-input" placeholder="Group name">
      <div class="group-check-list" id="group-layer-list"></div>
      <div class="modal-actions">
        <button class="modal-btn secondary" id="group-cancel">Cancel</button>
        <button class="modal-btn primary" id="group-save">Save Group</button>
      </div>
    </div>
  </div>

  <!-- Hazard Levels Panel -->
  <div id="hazard-panel">
    <div class="hazard-title">Hazard Levels In Your Area</div>
    
    <div class="hazard-card">
      <div class="hazard-card-left">
        <div class="hazard-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16" rx="2"/><path d="M8 12h8"/><path d="M12 8v8"/><path d="M8 16h8"/></svg></div>
        <div class="hazard-text-wrap">
          <div class="hazard-label">Flood Hazard Level</div>
          <div class="hazard-level">LITTLE TO NONE</div>
        </div>
      </div>
      <div class="hazard-info">i</div>
    </div>

    <div class="hazard-card">
      <div class="hazard-card-left">
        <div class="hazard-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg></div>
        <div class="hazard-text-wrap">
          <div class="hazard-label">Earthquake Hazard Level</div>
          <div class="hazard-level">LITTLE TO NONE</div>
        </div>
      </div>
      <div class="hazard-info">i</div>
    </div>

    <div class="hazard-card">
      <div class="hazard-card-left">
        <div class="hazard-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12h20"/><path d="M12 2v20"/><path d="M4 4l16 16"/><path d="M20 4L4 20"/></svg></div>
        <div class="hazard-text-wrap">
          <div class="hazard-label">Storm Surge Hazard Level</div>
          <div class="hazard-level">LITTLE TO NONE</div>
        </div>
      </div>
      <div class="hazard-info">i</div>
    </div>

    <div class="hazard-notes">
      <div style="font-weight:600; margin-bottom:4px;">Note:</div>
      <ul>
        <li>If you want an independent assessment of flood, landslide, or storm surge, then click on the tabs above.</li>
        <li>Assessment is for a point location. Please refer to map for visual evaluation.</li>
      </ul>
      <div class="hazard-db-list">Hazards included in map database are:<br>
        1) 100-year rain return for floods;<br>
        2) Shallow and structurally-controlled landslides;<br>
        3) 5-meters for storm surges.
      </div>
    </div>
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

      <!-- Layer Grouping Button -->
      <div style="display:flex; justify-content:flex-end; padding-top:8px;">
        <button id="group-btn" style="background:#021a3d; color:#fff; padding:4px 10px; border-radius:3px; font-size:11px; font-weight:600;">+ Group Layers</button>
      </div>
      <div id="grouped-layers-container" style="border-bottom:1px solid #eee; margin-bottom:6px;"></div>

      <!-- Groups sit directly under the Data browser header -->
      <div class="layer-group" id="grp-hazards">
        <div class="group-head"><span class="chev"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg></span>Hazards</div>
        <div class="group-body">
          <div class="layer-row disabled" data-key="earthquake">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><path d="M22 19V7H12l-2-2H2v14z"/></svg>
            <span class="lname">Earthquake</span>
            <span class="row-icons"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"/></svg><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"/></svg><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/></svg></span>
          </div>
          <div class="layer-row disabled" data-key="floods">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><path d="M22 19V7H12l-2-2H2v14z"/></svg>
            <span class="lname">Floods</span>
            <span class="row-icons"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"/></svg><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"/></svg><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/></svg></span>
          </div>
        </div>
      </div>

      <div class="layer-group" id="grp-infrastructure">
        <div class="group-head"><span class="chev"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg></span>Infrastructure</div>
        <div class="group-body">
          <div class="layer-row selected" data-key="roads">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><path d="M22 19V7H12l-2-2H2v14z"/></svg>
            <span class="lname">Roads</span>
            <span class="row-icons"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"/></svg><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"/></svg><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/></svg></span>
          </div>
          <div class="layer-row selected" data-key="boundaries">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><path d="M22 19V7H12l-2-2H2v14z"/></svg>
            <span class="lname">Boundaries (Cities, Province, Region)</span>
            <span class="row-icons"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"/></svg><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"/></svg><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/></svg></span>
          </div>
          <div class="layer-row disabled" data-key="zoning">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><path d="M22 19V7H12l-2-2H2v14z"/></svg>
            <span class="lname">Zoning (LGU Restrictions, CLUP)</span>
            <span class="row-icons"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"/></svg><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"/></svg><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/></svg></span>
          </div>
        </div>
      </div>

      <div class="layer-group" id="grp-valuation">
        <div class="group-head"><span class="chev"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg></span>Valuation</div>
        <div class="group-body">
          <div class="layer-row disabled" data-key="rental">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><path d="M22 19V7H12l-2-2H2v14z"/></svg>
            <span class="lname">Rental Rate</span>
            <span class="row-icons"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"/></svg><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"/></svg><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/></svg></span>
          </div>
          <div class="layer-row disabled" data-key="prime">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><path d="M22 19V7H12l-2-2H2v14z"/></svg>
            <span class="lname">PRIME Core</span>
            <span class="row-icons"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"/></svg><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"/></svg><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/></svg></span>
          </div>
          <div class="layer-row disabled" data-key="lamudi">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><path d="M22 19V7H12l-2-2H2v14z"/></svg>
            <span class="lname">Lamudi and other property platforms (Scraper)</span>
            <span class="row-icons"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"/></svg><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"/></svg><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/></svg></span>
          </div>
          <div class="layer-row disabled" data-key="tiering">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><path d="M22 19V7H12l-2-2H2v14z"/></svg>
            <span class="lname">Tiering of data from Primary, secondary sources</span>
            <span class="row-icons"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"/></svg><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"/></svg><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/></svg></span>
          </div>
        </div>
      </div>

      <!-- Layers section: live list of user-drawn shapes -->
      <div class="layers-head">
        <span>Layers</span>
        <span class="count-badge" id="layer-count">0</span>
      </div>
      <div id="drawn-list">
        <div class="empty-note" id="drawn-empty">No drawings yet. Use the draw tools to add shapes.</div>
      </div>

    </div>
  </div>

  <!-- Details panel (Dynamic) -->
  <div id="details">
    <button id="details-close"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><line x1="6" y1="6" x2="18" y2="18"></line><line x1="18" y1="6" x2="6" y2="18"></line></svg></button>
    <h1>Details</h1>
    <p class="hint">Click on a marker, polygon, or draw on the map to see details here.</p>
    <div class="lbl">Last click</div>
    <div class="val" id="lastclick">14.6142, 121.0110</div>
    <div class="lbl">Active drawings</div>
    <div class="val" id="drawcount">0</div>
    <hr>
    <h2>Advanced Analytics</h2>
    <div class="metrics">
      <div class="metric"><div class="lbl">Avg rental rate</div><div class="mval">₱ 850/m²<span class="delta up">+3.2%</span></div></div>
      <div class="metric"><div class="lbl">Prime core index</div><div class="mval">87.5<span class="delta up">+1.8%</span></div></div>
      <div class="metric"><div class="lbl">Road density</div><div class="mval">2.4 km/km²<span class="delta up">+0.3</span></div></div>
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
  var map = L.map('map', {zoomControl: false}).setView([14.63, 121.00], 11);

  // ----- Basemaps -----
  var basemaps = {
    osm: L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom:19, attribution:'&copy; OpenStreetMap contributors under ODbL'}),
    satellite: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {maxZoom:19, attribution:'Tiles &copy; Esri - Source: Esri, Maxar, Earthstar Geographics'}),
    carto: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {maxZoom:20, subdomains:'abcd', attribution:'&copy; OpenStreetMap contributors &copy; CARTO'})
  };
  var currentBase = basemaps.osm.addTo(map);
  L.control.scale({position: 'bottomleft'}).addTo(map);

  var bmBtn = document.getElementById('basemap-btn');
  var bmPanel = document.getElementById('basemap-panel');
  bmBtn.onclick = function (e) {
    e.stopPropagation();
    bmPanel.classList.toggle('open');
    bmPanel.style.top = (34 + bmBtn.offsetTop - 4) + 'px'; 
    bmBtn.classList.toggle('active', bmPanel.classList.contains('open'));
  };
  document.querySelectorAll('.bm-opt').forEach(function (o) {
    o.onclick = function () {
      map.removeLayer(currentBase);
      currentBase = basemaps[this.dataset.bm].addTo(map);
      document.querySelectorAll('.bm-opt').forEach(function (x) { x.classList.remove('active'); });
      this.classList.add('active');
    };
  });
  document.addEventListener('click', function (e) {
    if (!bmPanel.contains(e.target) && !e.target.closest('#basemap-btn')) {
      bmPanel.classList.remove('open');
      bmBtn.classList.remove('active');
    }
  });

  // ----- Thematic overlays -----
  var boundaries = L.layerGroup([
    L.polygon([[14.72,121.02],[14.76,121.03],[14.78,121.06],[14.74,121.07],[14.71,121.05]], {color:'#2f9e44', weight:2, fillColor:'#66bb6a', fillOpacity:0.6}),
    L.polygon([[14.75,121.10],[14.80,121.12],[14.85,121.15],[14.80,121.18],[14.70,121.16],[14.68,121.12]], {color:'#2f9e44', weight:2, fillColor:'#66bb6a', fillOpacity:0.6}),
    L.polygon([[14.60,121.10],[14.64,121.11],[14.66,121.14],[14.62,121.16],[14.58,121.13],[14.57,121.11]], {color:'#2f9e44', weight:2, fillColor:'#66bb6a', fillOpacity:0.5}),
    L.polygon([[14.52,121.11],[14.55,121.12],[14.56,121.15],[14.52,121.16],[14.50,121.13]], {color:'#2f9e44', weight:2, fillColor:'#66bb6a', fillOpacity:0.5})
  ]);
  var roads = L.layerGroup([
    L.polyline([[14.67,121.03],[14.63,121.01],[14.58,120.99],[14.53,120.98],[14.50,120.96]], {color:'#e07b39', weight:3, opacity:0.7}),
    L.polyline([[14.55,121.00],[14.60,121.05],[14.65,121.10]], {color:'#e07b39', weight:3, opacity:0.7})
  ]);
  var earthquake = L.layerGroup([
    L.polyline([[14.75,121.08],[14.70,121.06],[14.65,121.05],[14.60,121.06],[14.55,121.05],[14.50,121.04]], {color:'#d93025', weight:3, dashArray:'6 4'}),
    L.circle([14.65,121.05], {radius:1500, color:'#d93025', weight:1, fillColor:'#d93025', fillOpacity:0.15})
  ]);
  var floods = L.layerGroup([
    L.polygon([[14.55,121.08],[14.60,121.09],[14.62,121.08],[14.58,121.07]], {color:'#1a73e8', weight:1, fillColor:'#4285f4', fillOpacity:0.35}),
    L.polygon([[14.48,120.96],[14.52,120.97],[14.55,120.96],[14.50,120.95]], {color:'#1a73e8', weight:1, fillColor:'#4285f4', fillOpacity:0.35}),
    L.polygon([[14.35,121.00],[14.40,121.02],[14.42,121.00],[14.38,120.98]], {color:'#1a73e8', weight:1, fillColor:'#4285f4', fillOpacity:0.35})
  ]);
  var zoning = L.layerGroup([
    L.polygon([[14.62,120.98],[14.66,120.99],[14.67,121.02],[14.63,121.02],[14.61,121.00]], {color:'#8e24aa', weight:2, dashArray:'4 4', fillColor:'#ba68c8', fillOpacity:0.25}),
    L.polygon([[14.52,121.00],[14.56,121.01],[14.57,121.04],[14.53,121.04]], {color:'#8e24aa', weight:2, dashArray:'4 4', fillColor:'#ba68c8', fillOpacity:0.25})
  ]);
  function dots(coords, fill) {
    return L.layerGroup(coords.map(function (c) {
      return L.circleMarker(c, {radius:6, color:'#021a3d', weight:2, fillColor:fill, fillOpacity:0.9});
    }));
  }
  var rental = dots([[14.58,120.98],[14.62,121.01],[14.67,121.03],[14.52,121.00]], '#fbbc04');
  var prime  = dots([[14.55,121.02],[14.60,120.99],[14.65,121.05]], '#34a853');
  var lamudi  = L.layerGroup(); 
  var tiering = L.layerGroup(); 

  // Add Valuation Popups
  rental.eachLayer(function(l) { l.bindPopup('<b>Property Price</b><br>₱ 850/m²'); });
  prime.eachLayer(function(l) { l.bindPopup('<b>Property Price</b><br>₱ 1,200/m²'); });

  var overlays = {earthquake:earthquake, floods:floods, roads:roads, boundaries:boundaries,
                  zoning:zoning, rental:rental, prime:prime, lamudi:lamudi, tiering:tiering};
  var initialOn = {roads:true, boundaries:true};
  Object.keys(overlays).forEach(function (k) { if (initialOn[k]) overlays[k].addTo(map); });

  // Basemap decor: hatched shipping lane
  L.polyline([[14.30,120.82],[14.40,120.87],[14.50,120.93],[14.585,120.985]],
    {color:'#7ea6e0', weight:8, opacity:0.7, dashArray:'2 6', lineCap:'butt'}).addTo(map);

  // ----- Dropdown group heads -----
  document.querySelectorAll('.group-head').forEach(function (h) {
    h.onclick = function () { h.parentElement.classList.toggle('collapsed'); };
  });

  // ----- Thematic sublayer toggling & Hazard Widget -----
  var hazardPanel = document.getElementById('hazard-panel');
  function checkHazardPanel() {
    var eqRow = document.querySelector('.layer-row[data-key="earthquake"]');
    var floodRow = document.querySelector('.layer-row[data-key="floods"]');
    var eqActive = eqRow && eqRow.classList.contains('selected');
    var floodActive = floodRow && floodRow.classList.contains('selected');
    if (eqActive || floodActive) hazardPanel.classList.add('open');
    else hazardPanel.classList.remove('open');
  }

  document.querySelectorAll('.layer-row[data-key]').forEach(function (row) {
    row.onclick = function () {
      var key = row.dataset.key;
      var on = row.classList.contains('disabled');
      if (on) { overlays[key].addTo(map); row.classList.remove('disabled'); row.classList.add('selected'); }
      else { map.removeLayer(overlays[key]); row.classList.add('disabled'); row.classList.remove('selected'); }
      if (key === 'earthquake' || key === 'floods') checkHazardPanel();
    };
  });

  // ----- Dynamic Details Panel Logic -----
  var detailsPanel = document.getElementById('details');
  var lastClickSpan = document.getElementById('lastclick');
  function updateDetails(lat, lng, count) {
    lastClickSpan.textContent = lat.toFixed(4) + ', ' + lng.toFixed(4);
    document.getElementById('drawcount').textContent = count || '0';
  }

  // ----- Drawing Save/Cancel Modal Logic -----
  var drawModal = document.getElementById('draw-modal');
  var pendingLayer = null;
  var drawSaveBtn = document.getElementById('draw-save');
  var drawCancelBtn = document.getElementById('draw-cancel');

  drawSaveBtn.onclick = function() {
    if (pendingLayer) {
      drawnItems.addLayer(pendingLayer);
      var t = pendingLayer.layerType || 'polygon'; // fallback
      addDrawnUIItem(pendingLayer, t);
      refreshDrawnUI();
      pendingLayer = null;
    }
    drawModal.style.display = 'none';
  };

  drawCancelBtn.onclick = function() {
    if (pendingLayer) {
      map.removeLayer(pendingLayer);
      pendingLayer = null;
    }
    drawModal.style.display = 'none';
  };

  // ----- Drawings + Layers section list -----
  var drawnItems = L.featureGroup().addTo(map);
  var drawnList = document.getElementById('drawn-list');
  var emptyNote = document.getElementById('drawn-empty');
  var counters = {};

  var typeMeta = {
    polyline:  {name:'Line',      svg:'<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"/></svg>'},
    polygon:   {name:'Polygon',   svg:'<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l8 6-3 10H7L4 9z"/></svg>'},
    rectangle: {name:'Rectangle', svg:'<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16"/></svg>'},
    circle:    {name:'Circle',    svg:'<svg viewBox="0 0 24 24" width="13" height="13"><circle cx="12" cy="12" r="8" fill="currentColor"/></svg>'},
    marker:    {name:'Marker',    svg:'<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>'}
  };
  var eyeSvg = '<svg class="ic-eye" title="Show/hide" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/></svg>';
  var trashSvg = '<svg class="ic-trash" title="Delete" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/></svg>';

  function refreshDrawnUI() {
    var n = drawnItems.getLayers().length;
    document.getElementById('drawcount').textContent = n;
    document.getElementById('layer-count').textContent = n;
    emptyNote.style.display = n ? 'none' : '';
  }

  function addDrawnUIItem(layer, t) {
    counters[t] = (counters[t] || 0) + 1;
    var meta = typeMeta[t] || {name:t, svg:''};

    var row = document.createElement('div');
    row.className = 'layer-row selected';
    row.innerHTML = meta.svg + '<span class="lname">' + meta.name + ' ' + counters[t] + '</span>' +
      '<span class="row-icons">' + eyeSvg + trashSvg + '</span>';

    // Zoom to shape
    row.onclick = function () {
      try {
        if (layer.getBounds) map.fitBounds(layer.getBounds(), {padding:[30,30]});
        else map.setView(layer.getLatLng(), 15);
      } catch (err) { console.warn('Zoom failed:', err); }
    };
    // eye = show/hide
    row.querySelector('.ic-eye').onclick = function (ev) {
      ev.stopPropagation();
      var visible = map.hasLayer(layer);
      if (visible) map.removeLayer(layer); else map.addLayer(layer);
      row.classList.toggle('disabled', visible);
      row.classList.toggle('selected', !visible);
    };
    // trash = delete
    row.querySelector('.ic-trash').onclick = function (ev) {
      ev.stopPropagation();
      drawnItems.removeLayer(layer);
      row.remove();
      refreshDrawnUI();
    };
    drawnList.appendChild(row);
  }

  // Intercept drawing creation with modal
  map.on(L.Draw.Event.CREATED, function (e) {
    pendingLayer = e.layer;
    var t = e.layerType;
    drawModal.style.display = 'flex';
  });

  // Add standard map Click
  map.on('click', function (e) {
    var lat = e.latlng.lat;
    var lng = e.latlng.lng;
    var count = drawnItems.getLayers().length;
    updateDetails(lat, lng, count);
  });

  // ----- Toolbar -----
  document.getElementById('zoomin').onclick = function () { map.zoomIn(); };
  document.getElementById('zoomout').onclick = function () { map.zoomOut(); };
  document.getElementById('clearbtn').onclick = function () {
    drawnItems.clearLayers();
    drawnList.querySelectorAll('.layer-row').forEach(function (r) { r.remove(); });
    counters = {};
    refreshDrawnUI();
  };
  document.getElementById('db-toggle').onclick = function () {
    var db = document.getElementById('databrowser');
    db.style.display = (db.style.display === 'none') ? 'flex' : 'none';
    this.classList.toggle('active', db.style.display !== 'none');
  };

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

  var editMode = null, editing = false;
  document.getElementById('editbtn').onclick = function () {
    try {
      if (!editMode) editMode = new L.EditToolbar.Edit(map, {featureGroup: drawnItems});
      editing = !editing;
      editing ? editMode.enable() : editMode.disable();
      this.classList.toggle('active', editing);
    } catch (err) { console.warn('Edit mode unavailable:', err); }
  };

  // ----- Search Panel Logic -----
  var searchPanel = document.getElementById('search-panel');
  var searchInput = document.getElementById('search-input');
  var searchResults = document.getElementById('search-results');

  document.getElementById('searchbtn').onclick = function (e) {
    e.stopPropagation();
    var isOpen = searchPanel.classList.contains('open');
    searchPanel.classList.toggle('open', !isOpen);
    if (!isOpen) { searchInput.focus(); }
  };

  document.getElementById('search-close').onclick = function () {
    searchPanel.classList.remove('open');
    searchResults.classList.remove('open');
    searchResults.innerHTML = '';
    searchInput.value = '';
  };

  searchInput.addEventListener('input', function() {
    var q = this.value.trim();
    if(q.length < 3) { searchResults.classList.remove('open'); searchResults.innerHTML = ''; return; }
    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${q}&limit=5`)
    .then(res => res.json())
    .then(data => {
      if(data.length === 0) { searchResults.classList.remove('open'); return; }
      var html = '';
      data.forEach(item => {
        html += `<div class="result-item" data-lat="${item.lat}" data-lon="${item.lon}">${item.display_name}</div>`;
      });
      searchResults.innerHTML = html;
      searchResults.classList.add('open');
      document.querySelectorAll('.result-item').forEach(el => {
        el.onclick = function() {
          map.setView([parseFloat(this.dataset.lat), parseFloat(this.dataset.lon)], 14);
          searchPanel.classList.remove('open');
          searchResults.classList.remove('open');
          searchResults.innerHTML = '';
          searchInput.value = '';
        };
      });
    }).catch(() => { searchResults.classList.remove('open'); });
  });

  // ----- Layer Grouping Logic -----
  var groupModal = document.getElementById('group-modal');
  var groupNameInput = document.getElementById('group-name-input');
  var groupLayerList = document.getElementById('group-layer-list');
  var groupedContainer = document.getElementById('grouped-layers-container');
  var groupCount = 0;

  document.getElementById('group-btn').onclick = function() {
    groupNameInput.value = '';
    groupLayerList.innerHTML = '';
    // Populate available layers
    var availableLayerNames = Object.keys(overlays);
    availableLayerNames.forEach(function(key) {
      var div = document.createElement('div');
      div.className = 'group-check-item';
      div.innerHTML = '<input type="checkbox" value="'+key+'"> <label>'+key.charAt(0).toUpperCase() + key.slice(1)+'</label>';
      groupLayerList.appendChild(div);
    });
    groupModal.style.display = 'flex';
  };

  document.getElementById('group-cancel').onclick = function() {
    groupModal.style.display = 'none';
  };

  document.getElementById('group-save').onclick = function() {
    var name = groupNameInput.value.trim();
    if (!name) { alert('Please enter a group name.'); return; }
    var selectedKeys = [];
    groupLayerList.querySelectorAll('input[type="checkbox"]:checked').forEach(function(cb) {
      selectedKeys.push(cb.value);
    });
    if (selectedKeys.length === 0) { alert('Please select at least one layer.'); return; }
    
    // Create Group
    var layersToGroup = selectedKeys.map(function(k) { return overlays[k]; });
    var newGroup = L.layerGroup(layersToGroup);
    map.addLayer(newGroup);
    
    // Add UI group container
    var groupDiv = document.createElement('div');
    groupDiv.className = 'layer-row selected';
    groupDiv.style.marginTop = '4px';
    groupDiv.innerHTML = '<svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><path d="M4 4h16v16H4z"/></svg><span class="lname">'+name+'</span>';
    groupDiv.onclick = function() {
      if (map.hasLayer(newGroup)) {
        map.removeLayer(newGroup);
        groupDiv.classList.remove('selected');
        groupDiv.classList.add('disabled');
      } else {
        map.addLayer(newGroup);
        groupDiv.classList.remove('disabled');
        groupDiv.classList.add('selected');
      }
    };
    groupedContainer.appendChild(groupDiv);
    groupModal.style.display = 'none';
  };

  // ----- Panel controls -----
  document.getElementById('db-close').onclick = function () { document.getElementById('databrowser').style.display = 'none'; };
  document.getElementById('db-collapse').onclick = function () {
    var b = document.getElementById('db-body');
    b.style.display = (b.style.display === 'none') ? '' : 'none';
  };
  document.getElementById('details-close').onclick = function () { document.getElementById('details').style.display = 'none'; };

  refreshDrawnUI();
  checkHazardPanel();
} catch (err) {
  console.error('Map init failed:', err);
}
</script>
</body>
</html>
"""

components.html(APP_HTML, height=1080, scrolling=False)

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
<!-- Libraries for KML & KMZ support -->
<script src="https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/leaflet-kml@1.0.0/dist/leaflet-kml.min.js"></script>
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

/* ---------- Basemap panel ---------- */
#basemap-panel {position:absolute; left:46px; top:140px; width:180px; background:#fff; z-index:1150;
  box-shadow:0 1px 5px rgba(0,0,0,.35); border-radius:3px; padding:6px; display:none;}
#basemap-panel.open {display:block;}
.bm-title {font-size:10px; letter-spacing:.5px; color:#8a8a8a; text-transform:uppercase; padding:4px 8px 6px 8px;}
.bm-opt {display:flex; align-items:center; gap:8px; padding:6px 8px; font-size:12px; color:#333; cursor:pointer; border-radius:3px;}
.bm-opt:hover {background:#eee;}
.bm-opt .dot {width:12px; height:12px; border-radius:50%; border:2px solid #999; flex-shrink:0;}
.bm-opt.active .dot {border-color:#021a3d; background:#021a3d; box-shadow:inset 0 0 0 2px #fff;}

/* ---------- Floating panels ---------- */
.panel {position:absolute; top:42px; left:46px; width:300px; background:#fff;
  box-shadow:0 1px 4px rgba(0,0,0,.3); display:none; flex-direction:column;}
.panel.open, #databrowser {display:flex;}
#databrowser {bottom:60px; z-index:1100;}
#search-panel {z-index:1120; max-height:70%;}
.db-head {display:flex; align-items:center; gap:8px; padding:12px 12px 8px 12px; font-size:14px; position:relative;}
.db-head b {font-size:14px;}
.db-actions {position:absolute; right:8px; top:8px; display:flex; gap:4px;}
.db-actions button {width:22px; height:22px; border:1px solid #ccc; background:#fff; color:#555; border-radius:2px;
  display:flex; align-items:center; justify-content:center;}
.db-actions button:hover {background:#eee;}
.db-body {padding:4px 12px; overflow:auto; flex:1;}

/* search panel body */
.sp-body {padding:10px 12px;}
.search-row {display:flex; gap:6px;}
#search-input {flex:1; border:1px solid #ccc; border-radius:3px; padding:6px 8px; font-size:12px; outline:none;}
#search-input:focus {border-color:#021a3d;}
#search-go {background:#021a3d; color:#fff; border-radius:3px; width:32px; display:flex; align-items:center; justify-content:center;}
#search-results {margin-top:8px; overflow:auto; max-height:280px;}
.sr-item {padding:6px; border-top:1px solid #eee; cursor:pointer; font-size:12px; color:#333;}
.sr-item:hover {background:#eef4fb;}
.sr-sub {color:#888; font-size:10px;}

/* layer groups (dropdowns) */
.group-head {display:flex; align-items:center; gap:6px; font-weight:700; font-size:12px; color:#222;
  padding:8px 4px 4px 4px; margin-top:4px; border-top:1px solid #eee; cursor:pointer; user-select:none;}
.group-head .chev {transition:transform .15s; color:#555;}
.layer-group.collapsed .chev {transform:rotate(-90deg);}
.layer-group.collapsed .group-body {display:none;}
.group-body {padding-left:10px;}
.drawn-group .group-head {background:#f7f9fc;}
.gh-actions {margin-left:auto; display:flex; gap:6px; color:#777;}
.gh-actions button:hover {color:#021a3d;}

.layers-head {display:flex; justify-content:space-between; align-items:center; border-top:1px solid #ddd; padding-top:10px; margin-top:8px;}
.layers-head span:first-child {font-weight:700; font-size:13px;}
.lh-right {display:flex; align-items:center; gap:8px;}
#add-group-btn {width:22px; height:22px; border:1px solid #ccc; border-radius:2px; color:#555;
  display:flex; align-items:center; justify-content:center;}
#add-group-btn:hover {background:#eee;}
#add-group-btn.active {background:#e0e0e0; box-shadow:inset 0 0 0 1px #888;}
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
.gcheck {display:none; flex-shrink:0;}
#drawn-list.grouping .gcheck {display:inline-block;}

/* grouping bar */
#group-bar {display:none; background:#eaf1fb; border:1px solid #bcd2f0; border-radius:3px;
  padding:6px; margin:6px 0; gap:6px; align-items:center;}
#group-bar.open {display:flex;}
#group-name {flex:1; border:1px solid #ccc; border-radius:3px; padding:4px 6px; font-size:12px; outline:none;}
.gb-btn {border:1px solid #ccc; background:#fff; border-radius:3px; padding:3px 8px; font-size:11px;}
#group-create {background:#021a3d; color:#fff; border-color:#021a3d;}

/* ---------- Details Panel (Dual Mode) ---------- */
#details {position:absolute; top:42px; right:10px; width:292px; background:#fff; box-shadow:0 1px 4px rgba(0,0,0,.3);
  z-index:1100; padding:16px; max-height:calc(100% - 160px); overflow:auto;}
#details-close {position:absolute; right:10px; top:10px; color:#999;}
#details-close:hover {color:#333;}

#standard-panel h1 {font-size:22px; font-weight:600; color:#1a1a1a; border-bottom:2px solid #3f8fd2; padding-bottom:8px; margin-bottom:12px;}
#standard-panel h2 {font-size:15px; font-weight:600; color:#1a1a1a; border-bottom:2px solid #3f8fd2; padding-bottom:6px; margin-top:14px;}
.hint {font-size:13px; color:#6b7c93; line-height:1.5; margin-bottom:10px;}
.lbl {font-size:10px; letter-spacing:.5px; color:#8a8a8a; text-transform:uppercase; margin-top:10px;}
.val {font-size:13px; color:#333; margin-top:2px; word-break:break-word;}
#details hr {border:none; border-top:1px solid #ddd; margin:12px 0;}
.metrics {display:grid; grid-template-columns:1fr 1fr; gap:14px 10px; margin-top:12px;}
.metric .lbl {margin-top:0; font-size:9px;}
.metric .mval {font-size:13px; font-weight:700; color:#222; margin-top:3px;}
.delta {font-size:11px; font-weight:600; margin-left:4px;}
.up {color:#188038;} .down {color:#d93025;} .flat {color:#80868b;}
.foot {font-size:11px; color:#8a8a8a; line-height:1.5; margin-top:10px;}

#hazard-panel .hazard-title {font-weight:600; font-size:18px; color:#333; margin-bottom:12px;}
.hazard-card {display:flex; align-items:center; justify-content:space-between; background:#fff; border-radius:4px; 
  margin-bottom:8px; padding:10px; box-shadow:0 1px 3px rgba(0,0,0,0.15); position:relative;}
.hazard-card-left {display:flex; align-items:center; gap:12px;}
.hazard-icon {display:flex; align-items:center; justify-content:center; width:44px; height:44px; background:#fff; border:2px solid #0056b3; border-radius:6px; flex-shrink:0; color:#0056b3;}
.hazard-text-wrap {display:flex; flex-direction:column;}
.hazard-label {font-size:13px; font-weight:500; color:#444;}
.hazard-level {font-size:13px; font-weight:700; color:#222; text-transform:uppercase;}
.hazard-info {display:flex; align-items:center; justify-content:center; width:20px; height:20px; border:1px solid #555; border-radius:50%; color:#444; font-size:12px; font-weight:bold; cursor:pointer; margin-left:8px;}
.hazard-notes {margin-top:12px; font-size:11px; color:#444; line-height:1.6;}
.hazard-notes ul {padding-left:16px; margin:4px 0; list-style-type:disc;}
.hazard-notes ul li {margin-bottom:2px;}
.hazard-db-list {margin-top:8px; font-size:11px; font-weight:600; color:#555; line-height:1.5;}

/* price tooltips */
.leaflet-tooltip.price-tip {background:#021a3d; color:#fff; border:1px solid #021a3d; font-size:10px;
  font-weight:700; padding:2px 6px; border-radius:3px; box-shadow:none;}
.leaflet-tooltip.price-tip::before {display:none;}

/* ---------- Map ---------- */
#map {position:absolute; top:34px; left:0; right:0; bottom:0; z-index:1; background:#cfe9e4;}
.leaflet-container {font:inherit;}

/* ---------- Style Editor Modal ---------- */
#style-modal {position:absolute; top:60px; left:310px; width:220px; background:#fff; z-index:1200;
  box-shadow:0 2px 10px rgba(0,0,0,0.25); border-radius:4px; padding:14px; display:none; border:1px solid #ddd;}
#style-modal.open {display:flex; flex-direction:column; gap:8px;}
.style-title {font-size:12px; font-weight:700; color:#333; margin-bottom:4px;}
.style-row {display:flex; justify-content:space-between; align-items:center; font-size:11px; color:#555;}
.style-row input[type="range"] {width:80px; accent-color:#021a3d;}
.style-row input[type="color"] {width:24px; height:24px; padding:0; border:none; cursor:pointer;}
.style-presets {display:flex; gap:6px; margin:4px 0 6px 0;}
.style-presets div {width:22px; height:22px; border-radius:50%; border:2px solid #eee; cursor:pointer;}
.style-presets div.active, .style-presets div:hover {border-color:#333;}
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
    <button id="searchbtn" title="Search"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.5" y2="16.5"/></svg></button>
    <button class="tool" data-tool="marker" title="Place marker"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg></button>
    <button class="tool" data-tool="polyline" title="Draw line"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"/></svg></button>
    <button class="tool" data-tool="polygon" title="Draw polygon"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l8 6-3 10H7L4 9z"/></svg></button>
    <button class="tool" data-tool="rectangle" title="Draw rectangle"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16"/></svg></button>
    <button class="tool" data-tool="circle" title="Draw circle"><svg viewBox="0 0 24 24" width="14" height="14"><circle cx="12" cy="12" r="8" fill="currentColor"/></svg></button>
    <button id="basemap-btn" title="Basemap"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 6v16l7-4 8 4 7-4V2l-7 4-8-4z"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/></svg></button>
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

  <!-- Search panel -->
  <div id="search-panel" class="panel">
    <div class="db-head">
      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#333" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.5" y2="16.5"/></svg>
      <b>Search</b>
      <div class="db-actions">
        <button id="search-close" title="Close"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg></button>
      </div>
    </div>
    <div class="sp-body">
      <div class="search-row">
        <input id="search-input" type="text" placeholder="Search place or address...">
        <button id="search-go" title="Search"><svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.5" y2="16.5"/></svg></button>
      </div>
      <div id="search-results"></div>
    </div>
  </div>

  <!-- Style Editor Modal -->
  <div id="style-modal">
    <div class="style-title">Layer Style</div>
    <div class="style-presets">
      <div style="background:#d33;" data-color="#d33"></div>
      <div style="background:#333;" data-color="#333"></div>
      <div style="background:#2f9e44;" data-color="#2f9e44"></div>
      <div style="background:#1a73e8;" data-color="#1a73e8"></div>
      <div style="background:#fbbc04;" data-color="#fbbc04"></div>
      <div style="background:#8e24aa;" data-color="#8e24aa"></div>
    </div>
    <div class="style-row"><span>Custom Hex</span><input type="color" id="style-custom-color" value="#d33"></div>
    <div class="style-row"><span>Fill</span><input type="checkbox" id="style-fill" checked></div>
    <div class="style-row"><span>Outline</span><input type="checkbox" id="style-outline" checked></div>
    <div class="style-row"><span>Thickness</span><input type="range" id="style-thickness" min="0.5" max="15" step="0.5" value="3"></div>
    <div class="style-row"><span>Opacity</span><input type="range" id="style-opacity" min="0" max="1" step="0.05" value="1"></div>
    <div style="display:flex; justify-content:flex-end; margin-top:6px;"><button id="style-close-btn" style="background:#ddd; padding:2px 8px; border-radius:3px; font-size:11px;">Close</button></div>
  </div>

  <!-- Data browser -->
  <div id="databrowser" class="panel">
    <div class="db-head">
      <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="#333" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"/><path d="M2 12l10 6 10-6"/><path d="M2 16l10 6 10-6"/></svg>
      <b>Data browser</b>
      <div class="db-actions">
        <button id="db-collapse" title="Collapse"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polyline points="14 6 8 12 14 18"/></svg></button>
        <button id="db-close" title="Close"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg></button>
      </div>
    </div>
    <div class="db-body" id="db-body">

      <!-- Hazards -->
      <div class="layer-group" id="grp-hazards">
        <div class="group-head"><span class="chev"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg></span>Hazards</div>
        <div class="group-body">
          <div class="layer-row disabled" data-key="earthquake">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><path d="M22 19V7H12l-2-2H2v14z"/></svg>
            <span class="lname">Earthquake</span>
          </div>
          <div class="layer-row disabled" data-key="floods">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><path d="M22 19V7H12l-2-2H2v14z"/></svg>
            <span class="lname">Floods</span>
          </div>
        </div>
      </div>

      <!-- Infrastructure -->
      <div class="layer-group" id="grp-infrastructure">
        <div class="group-head"><span class="chev"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg></span>Infrastructure</div>
        <div class="group-body">
          <div class="layer-row selected" data-key="roads">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><path d="M22 19V7H12l-2-2H2v14z"/></svg>
            <span class="lname">Roads</span>
          </div>
          <div class="layer-row selected" data-key="boundaries">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><path d="M22 19V7H12l-2-2H2v14z"/></svg>
            <span class="lname">Boundaries (Cities, Province, Region)</span>
          </div>
          <div class="layer-row disabled" data-key="zoning">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><path d="M22 19V7H12l-2-2H2v14z"/></svg>
            <span class="lname">Zoning (LGU Restrictions, CLUP)</span>
          </div>
        </div>
      </div>

      <!-- Valuation (Rates tool + Map Overlays) -->
      <div class="layer-group" id="grp-valuation">
        <div class="group-head"><span class="chev"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg></span>Valuation
          <span class="gh-actions"><button id="price-popups" title="Show price popups"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg></button></span>
        </div>
        <div class="group-body">
          
          <!-- Nested Rates Dropdown -->
          <div class="layer-group" id="grp-rates">
            <div class="group-head"><span class="chev"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg></span>Rates</div>
            <div class="group-body">
              <div style="font-size:12px; padding:4px 0;">
                <span style="font-weight:600;">Purpose</span><br>
                <label style="margin-right:10px;"><input type="radio" name="rate-purpose" value="lease" checked> For Lease</label>
                <label><input type="radio" name="rate-purpose" value="sale"> For Sale</label>
              </div>
              <div style="font-size:12px; padding:4px 0;">
                <span style="font-weight:600;">Property Type</span><br>
                <select id="prop-type" style="width:100%; padding:4px; border:1px solid #ccc; border-radius:3px;">
                  <option>Commercial Lot</option>
                  <option>Retail Space</option>
                  <option>Industrial Warehouse</option>
                  <option>Industrial Lot</option>
                  <option>Office Space</option>
                </select>
              </div>
              <div style="font-size:12px; padding:4px 0;">
                <span style="font-weight:600;">Sources</span><br>
                <label style="display:block;"><input type="checkbox" id="src-prime"> PRIME Core</label>
                <label style="display:block;"><input type="checkbox" id="src-lamudi"> Lamudi</label>
              </div>
              <div style="font-size:12px; padding:4px 0; background:#f0f2f5; border-radius:3px; text-align:center;">
                <span style="font-weight:600;">Average Rate</span><br>
                <span id="display-rate" style="font-size:16px; font-weight:700; color:#222;">₱ 500 /sqm</span>
              </div>
            </div>
          </div>
          
          <!-- Map Overlays for Pricing Data -->
          <div class="layer-row disabled" data-key="rental"><span class="lname">Rental Map Overlay</span></div>
          <div class="layer-row disabled" data-key="prime"><span class="lname">PRIME Map Overlay</span></div>
        </div>
      </div>

      <!-- Community Layers / Add Data Layer -->
      <div class="layer-group" id="grp-community">
        <div class="group-head"><span class="chev"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg></span>Add Data Layer (Community)</div>
        <div class="group-body">
          <input type="file" id="community-file" accept=".geojson,.kml,.kmz" style="width:100%; padding:4px; border:1px solid #ccc; border-radius:3px; font-size:12px; background:#fff;">
          <div id="community-status" style="font-size:11px; color:#666; margin-top:4px;">Supports GeoJSON, KML, KMZ</div>
          <div id="community-list" style="margin-top:6px; border-top:1px solid #eee; padding-top:6px; min-height:20px;"></div>
        </div>
      </div>

      <!-- User drawn layers -->
      <div class="layers-head">
        <span>Layers</span>
        <span class="lh-right">
          <button id="add-group-btn" title="Add group layer"><svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19V7H12l-2-2H2v14z"/><line x1="12" y1="11" x2="12" y2="17"/><line x1="9" y1="14" x2="15" y2="14"/></svg></button>
          <span class="count-badge" id="layer-count">0</span>
        </span>
      </div>
      <div id="group-bar">
        <input id="group-name" type="text" placeholder="Group name">
        <button id="group-create" class="gb-btn">Create</button>
        <button id="group-cancel" class="gb-btn">Cancel</button>
      </div>
      <div id="drawn-list">
        <div class="empty-note" id="drawn-empty">No drawings yet. Use the draw tools to add shapes.</div>
      </div>
      <div id="drawn-groups"></div>

    </div>
  </div>

  <!-- Details panel (Dual Mode) -->
  <div id="details">
    <button id="details-close"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg></button>
    
    <div id="standard-panel">
      <h1>Details</h1>
      <p class="hint">Click on a marker, polygon, or draw on the map to see details here.</p>
      <div id="feature-block" style="display:none">
        <div class="lbl">Selected feature</div>
        <div class="val" id="f-name">-</div>
        <div class="lbl">Type</div>
        <div class="val" id="f-type">-</div>
        <div class="lbl">Area</div>
        <div class="val" id="f-area">-</div>
        <div class="lbl">Centroid</div>
        <div class="val" id="f-centroid">-</div>
        <hr>
      </div>
      <div class="lbl">Last click</div>
      <div class="val" id="lastclick">-</div>
      <div class="lbl">Active drawings</div>
      <div class="val" id="drawcount">0</div>
      <hr>
      <h2>Advanced Analytics</h2>
      <div class="metrics">
        <div class="metric"><div class="lbl">Avg rental rate</div><div class="mval"><span id="m-rental">&#8369; 850/m&#178;</span><span class="delta up" id="d-rental">+3.2%</span></div></div>
        <div class="metric"><div class="lbl">Prime core index</div><div class="mval"><span id="m-prime">87.5</span><span class="delta up" id="d-prime">+1.8%</span></div></div>
        <div class="metric"><div class="lbl">Road density</div><div class="mval"><span id="m-road">2.4 km/km&#178;</span><span class="delta up" id="d-road">+0.3</span></div></div>
        <div class="metric"><div class="lbl">Zoning compliance</div><div class="mval"><span id="m-zoning">94%</span><span class="delta up" id="d-zoning">+2%</span></div></div>
        <div class="metric"><div class="lbl">Flood risk index</div><div class="mval"><span id="m-flood">Medium (4.2)</span><span class="delta down" id="d-flood">+0.5</span></div></div>
        <div class="metric"><div class="lbl">Earthquake suscept.</div><div class="mval"><span id="m-quake">Low (2.1)</span><span class="delta flat" id="d-quake">+0.0</span></div></div>
      </div>
      <hr>
      <p class="foot">Smart Comparable Analysis: Advanced scoring algorithms for property valuation</p>
    </div>

    <div id="hazard-panel" style="display:none;">
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
            <div class="hazard-label">Landslide Hazard Level</div>
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

  </div>

</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.js"></script>
<script>
try {
  var map = L.map('map', {zoomControl: false}).setView([14.63, 121.00], 11);

  // ---------- helpers ----------
  function esc(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function prng(seed) { return function () { seed = (seed * 9301 + 49297) % 233280; return seed / 233280; }; }

  // ---------- basemaps ----------
  var basemaps = {
    osm: L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom:19, attribution:'&copy; OpenStreetMap contributors under ODbL'}),
    satellite: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {maxZoom:19, attribution:'Tiles &copy; Esri'}),
    carto: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {maxZoom:20, subdomains:'abcd', attribution:'&copy; OpenStreetMap contributors &copy; CARTO'})
  };
  var currentBase = basemaps.osm.addTo(map);
  L.control.scale({position: 'bottomleft'}).addTo(map);

  var bmBtn = document.getElementById('basemap-btn'), bmPanel = document.getElementById('basemap-panel');
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
      bmPanel.classList.remove('open'); bmBtn.classList.remove('active');
    }
  });

  // ---------- dynamic details & hazard panel logic ----------
  function setM(key, valText, delta, unit, goodPositive) {
    document.getElementById('m-' + key).textContent = valText;
    var el = document.getElementById('d-' + key);
    var v = Math.round(delta * 10) / 10;
    el.textContent = (v > 0 ? '+' : '') + v + unit;
    var cls = 'delta ';
    if (Math.abs(v) < 0.05) cls += 'flat';
    else if (v > 0) cls += goodPositive ? 'up' : 'down';
    else cls += goodPositive ? 'down' : 'up';
    el.className = cls;
  }
  function showFeature(layer, name, type) {
    var c = null, areaTxt = '-';
    try {
      if (layer instanceof L.Circle && !(layer instanceof L.CircleMarker)) {
        var r = layer.getRadius();
        areaTxt = (Math.PI * r * r / 1e6).toFixed(2) + ' km\u00B2';
        c = layer.getLatLng();
      } else if (layer instanceof L.Polygon) {
        var ring = layer.getLatLngs();
        if (Array.isArray(ring[0])) ring = ring[0];
        if (L.GeometryUtil && L.GeometryUtil.geodesicArea) {
          var a = L.GeometryUtil.geodesicArea(ring);
          areaTxt = (a / 1e6).toFixed(2) + ' km\u00B2 (' + Math.round(a / 100) + ' ha)';
        }
        c = layer.getBounds().getCenter();
      } else if (layer.getLatLng) { c = layer.getLatLng(); }
    } catch (err) { console.warn('measure failed', err); }

    document.getElementById('feature-block').style.display = '';
    document.getElementById('f-name').textContent = name;
    document.getElementById('f-type').textContent = type;
    document.getElementById('f-area').textContent = areaTxt;
    document.getElementById('f-centroid').textContent = c ? c.lat.toFixed(4) + ', ' + c.lng.toFixed(4) : '-';

    var seed = Math.abs(Math.round((c ? c.lat : 14.6) * 7919 + (c ? c.lng : 121) * 104729));
    var rnd = prng(seed);
    setM('rental', '\u20B1 ' + Math.round(600 + rnd() * 600) + '/m\u00B2', rnd() * 6 - 3, '%', true);
    setM('prime', (70 + rnd() * 25).toFixed(1), rnd() * 4 - 2, '%', true);
    setM('road', (1 + rnd() * 3).toFixed(1) + ' km/km\u00B2', rnd() - 0.5, '', true);
    setM('zoning', Math.round(80 + rnd() * 19) + '%', rnd() * 4 - 2, '%', true);
    var fv = 1 + rnd() * 7;
    setM('flood', (fv < 3 ? 'Low' : fv < 5 ? 'Medium' : 'High') + ' (' + fv.toFixed(1) + ')', rnd() * 2 - 1, '', false);
    var qv = 1 + rnd() * 4;
    setM('quake', (qv < 2.5 ? 'Low' : qv < 3.5 ? 'Medium' : 'High') + ' (' + qv.toFixed(1) + ')', rnd() - 0.5, '', false);
    document.getElementById('details').style.display = '';
  }
  function bindFeature(layer, name, type) {
    layer.on('click', function (e) {
      if (e.originalEvent) L.DomEvent.stopPropagation(e.originalEvent);
      showFeature(layer, name, type);
    });
  }

  // ---------- thematic overlays ----------
  var NB = {bubblingMouseEvents: false};
  function namedPoly(coords, style, name, type, group) {
    var p = L.polygon(coords, Object.assign({}, style, NB));
    p.apexName = name; bindFeature(p, name, type); group.push(p); return p;
  }
  var bLayers = [], fLayers = [], zLayers = [];
  namedPoly([[14.72,121.02],[14.76,121.03],[14.78,121.06],[14.74,121.07],[14.71,121.05]], {color:'#2f9e44', weight:2, fillColor:'#66bb6a', fillOpacity:0.6}, 'Boundary zone 1', 'Boundary', bLayers);
  namedPoly([[14.75,121.10],[14.80,121.12],[14.85,121.15],[14.80,121.18],[14.70,121.16],[14.68,121.12]], {color:'#2f9e44', weight:2, fillColor:'#66bb6a', fillOpacity:0.6}, 'Boundary zone 2', 'Boundary', bLayers);
  namedPoly([[14.60,121.10],[14.64,121.11],[14.66,121.14],[14.62,121.16],[14.58,121.13],[14.57,121.11]], {color:'#2f9e44', weight:2, fillColor:'#66bb6a', fillOpacity:0.5}, 'Boundary zone 3', 'Boundary', bLayers);
  namedPoly([[14.52,121.11],[14.55,121.12],[14.56,121.15],[14.52,121.16],[14.50,121.13]], {color:'#2f9e44', weight:2, fillColor:'#66bb6a', fillOpacity:0.5}, 'Boundary zone 4', 'Boundary', bLayers);
  var boundaries = L.layerGroup(bLayers);

  var rLayers = [
    L.polyline([[14.67,121.03],[14.63,121.01],[14.58,120.99],[14.53,120.98],[14.50,120.96]], Object.assign({color:'#e07b39', weight:3, opacity:0.7}, NB)),
    L.polyline([[14.55,121.00],[14.60,121.05],[14.65,121.10]], Object.assign({color:'#e07b39', weight:3, opacity:0.7}, NB))
  ];
  rLayers.forEach(function (l, i) { bindFeature(l, 'Road corridor ' + (i + 1), 'Road'); });
  var roads = L.layerGroup(rLayers);

  var eLayers = [
    L.polyline([[14.75,121.08],[14.70,121.06],[14.65,121.05],[14.60,121.06],[14.55,121.05],[14.50,121.04]], Object.assign({color:'#d93025', weight:3, dashArray:'6 4'}, NB)),
    L.circle([14.65,121.05], Object.assign({radius:1500, color:'#d93025', weight:1, fillColor:'#d93025', fillOpacity:0.15}, NB))
  ];
  eLayers.forEach(function (l, i) { bindFeature(l, 'Fault segment ' + (i + 1), 'Earthquake'); });
  var earthquake = L.layerGroup(eLayers);

  namedPoly([[14.55,121.08],[14.60,121.09],[14.62,121.08],[14.58,121.07]], {color:'#1a73e8', weight:1, fillColor:'#4285f4', fillOpacity:0.35}, 'Flood zone 1', 'Floods', fLayers);
  namedPoly([[14.48,120.96],[14.52,120.97],[14.55,120.96],[14.50,120.95]], {color:'#1a73e8', weight:1, fillColor:'#4285f4', fillOpacity:0.35}, 'Flood zone 2', 'Floods', fLayers);
  namedPoly([[14.35,121.00],[14.40,121.02],[14.42,121.00],[14.38,120.98]], {color:'#1a73e8', weight:1, fillColor:'#4285f4', fillOpacity:0.35}, 'Flood zone 3', 'Floods', fLayers);
  var floods = L.layerGroup(fLayers);

  namedPoly([[14.62,120.98],[14.66,120.99],[14.67,121.02],[14.63,121.02],[14.61,121.00]], {color:'#8e24aa', weight:2, dashArray:'4 4', fillColor:'#ba68c8', fillOpacity:0.25}, 'Zoning district 1', 'Zoning', zLayers);
  namedPoly([[14.52,121.00],[14.56,121.01],[14.57,121.04],[14.53,121.04]], {color:'#8e24aa', weight:2, dashArray:'4 4', fillColor:'#ba68c8', fillOpacity:0.25}, 'Zoning district 2', 'Zoning', zLayers);
  var zoning = L.layerGroup(zLayers);

  function pricedDots(data, fill, label) {
    var out = [];
    data.forEach(function (d, i) {
      var m = L.circleMarker([d[0], d[1]], Object.assign({radius:6, color:'#021a3d', weight:2, fillColor:fill, fillOpacity:0.9}, NB));
      m.apexPrice = d[2];
      bindFeature(m, label + ' ' + (i + 1), label);
      out.push(m);
    });
    return L.layerGroup(out);
  }
  var rental = pricedDots([[14.58,120.98,'\u20B1 780/m\u00B2'],[14.62,121.01,'\u20B1 850/m\u00B2'],[14.67,121.03,'\u20B1 920/m\u00B2'],[14.52,121.00,'\u20B1 810/m\u00B2']], '#fbbc04', 'Rental listing');
  var prime  = pricedDots([[14.55,121.02,'\u20B1 14.2M'],[14.60,120.99,'\u20B1 8.6M'],[14.65,121.05,'\u20B1 21.4M']], '#34a853', 'Prime asset');
  var lamudi = L.layerGroup(), tiering = L.layerGroup();

  var overlays = {earthquake:earthquake, floods:floods, roads:roads, boundaries:boundaries,
                  zoning:zoning, rental:rental, prime:prime, lamudi:lamudi, tiering:tiering};
  var initialOn = {roads:true, boundaries:true};
  Object.keys(overlays).forEach(function (k) { if (initialOn[k]) overlays[k].addTo(map); });

  L.polyline([[14.30,120.82],[14.40,120.87],[14.50,120.93],[14.585,120.985]],
    {color:'#7ea6e0', weight:8, opacity:0.7, dashArray:'2 6', lineCap:'butt'}).addTo(map);

  // price popups toggle (Valuation)
  var pricesOn = false;
  document.getElementById('price-popups').onclick = function (ev) {
    ev.stopPropagation();
    pricesOn = !pricesOn;
    this.classList.toggle('active', pricesOn);
    [rental, prime].forEach(function (lg) {
      lg.eachLayer(function (m) {
        if (pricesOn) {
          if (!m.getTooltip()) m.bindTooltip(m.apexPrice || '', {permanent:true, direction:'top', className:'price-tip', offset:[0,-8]});
          m.openTooltip();
        } else m.closeTooltip();
      });
    });
  };

  // ---------- group heads (thematic) ----------
  // Adding #grp-rates and #grp-community to the click handler
  document.querySelectorAll('#grp-hazards .group-head, #grp-infrastructure .group-head, #grp-valuation .group-head, #grp-rates .group-head, #grp-community .group-head').forEach(function (h) {
    h.onclick = function () { h.parentElement.classList.toggle('collapsed'); };
  });

  // ---------- thematic row toggling & Hazard Details Swap ----------
  function updateHazardVisibility() {
    var eqRow = document.querySelector('.layer-row[data-key="earthquake"]');
    var floodRow = document.querySelector('.layer-row[data-key="floods"]');
    var eqActive = eqRow && eqRow.classList.contains('selected');
    var floodActive = floodRow && floodRow.classList.contains('selected');
    var showHazard = eqActive || floodActive;

    var standardPanel = document.getElementById('standard-panel');
    var hazardPanel = document.getElementById('hazard-panel');

    if (showHazard) {
      standardPanel.style.display = 'none';
      hazardPanel.style.display = '';
    } else {
      standardPanel.style.display = '';
      hazardPanel.style.display = 'none';
    }
  }

  document.querySelectorAll('.layer-row[data-key]').forEach(function (row) {
    row.onclick = function () {
      var key = row.dataset.key, on = row.classList.contains('disabled');
      if (on) { overlays[key].addTo(map); row.classList.remove('disabled'); row.classList.add('selected'); }
      else { map.removeLayer(overlays[key]); row.classList.add('disabled'); row.classList.remove('selected'); }
      updateHazardVisibility();
    };
  });
  updateHazardVisibility();

  // ---------- Rate Estimator ----------
  function updateRate() {
    var purpose = document.querySelector('input[name="rate-purpose"]:checked').value;
    var type = document.getElementById('prop-type').value;
    var srcPrime = document.getElementById('src-prime').checked;
    var srcLamudi = document.getElementById('src-lamudi').checked;
    
    var base = 0;
    var rates = {
      'Commercial Lot': {lease: 500, sale: 15000},
      'Retail Space': {lease: 800, sale: 20000},
      'Industrial Warehouse': {lease: 350, sale: 9000},
      'Industrial Lot': {lease: 400, sale: 11000},
      'Office Space': {lease: 1200, sale: 30000}
    };
    if(rates[type]) base = rates[type][purpose];
    
    var multiplier = 1.0;
    if(srcPrime) multiplier += 0.2;
    if(srcLamudi) multiplier += 0.1;
    
    var finalRate = Math.round(base * multiplier);
    document.getElementById('display-rate').textContent = '₱ ' + finalRate.toLocaleString() + ' /sqm';
  }
  document.querySelectorAll('input[name="rate-purpose"]').forEach(function(el){ el.onchange = updateRate; });
  document.getElementById('prop-type').onchange = updateRate;
  document.getElementById('src-prime').onchange = updateRate;
  document.getElementById('src-lamudi').onchange = updateRate;
  updateRate(); // initial calculation

  // ---------- Community Layers ----------
  var communityLayerGroup = L.layerGroup().addTo(map);
  var communityList = document.getElementById('community-list');
  var communityStatus = document.getElementById('community-status');

  // Reuse icons for community layers
  var eyeSvgComm = '<svg class="ic-eye" title="Show/hide" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/></svg>';
  var trashSvgComm = '<svg class="ic-trash" title="Delete" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/></svg>';

  function addCommunityLayer(name, layer) {
    communityLayerGroup.addLayer(layer);
    
    var row = document.createElement('div');
    row.className = 'layer-row selected';
    row._layer = layer;
    row.style.marginTop = '4px';
    row.innerHTML = '<span class="lname">' + esc(name) + '</span>' +
      '<span class="row-icons">' + eyeSvgComm + trashSvgComm + '</span>';
    
    // Toggle visibility
    row.querySelector('.ic-eye').onclick = function (ev) {
      ev.stopPropagation();
      var vis = map.hasLayer(layer);
      if(vis) map.removeLayer(layer); else map.addLayer(layer);
      row.classList.toggle('disabled', vis);
      row.classList.toggle('selected', !vis);
    };
    
    // Remove layer
    row.querySelector('.ic-trash').onclick = function (ev) {
      ev.stopPropagation();
      communityLayerGroup.removeLayer(layer);
      row.remove();
    };
    
    communityList.appendChild(row);
    communityStatus.textContent = 'Loaded: ' + esc(name);
  }

  document.getElementById('community-file').addEventListener('change', function(e) {
    var file = e.target.files[0];
    if(!file) return;
    var ext = file.name.split('.').pop().toLowerCase();
    var reader = new FileReader();
    
    reader.onload = function(ev) {
      try {
        var layer;
        if (ext === 'geojson' || ext === 'json') {
          var data = JSON.parse(ev.target.result);
          layer = L.geoJSON(data);
          addCommunityLayer(file.name, layer);
        } else if (ext === 'kml') {
          if(typeof L.KML === 'undefined') {
             communityStatus.textContent = 'Error: KML library failed to load.';
             return;
          }
          var parser = new DOMParser();
          var kmlDoc = parser.parseFromString(ev.target.result, 'text/xml');
          layer = new L.KML(kmlDoc);
          addCommunityLayer(file.name, layer);
        } else if (ext === 'kmz') {
          if(typeof JSZip === 'undefined' || typeof L.KML === 'undefined') {
             communityStatus.textContent = 'Error: KMZ libraries (JSZip/KML) failed to load.';
             return;
          }
          JSZip.loadAsync(ev.target.result).then(function(zipFile) {
            var kmlFile = zipFile.file(/\.kml$/i)[0];
            if(kmlFile) {
              kmlFile.async('text').then(function(kmlString) {
                var parser = new DOMParser();
                var kmlDoc = parser.parseFromString(kmlString, 'text/xml');
                var layer = new L.KML(kmlDoc);
                addCommunityLayer(file.name, layer);
              });
            } else {
              communityStatus.textContent = 'Error: No KML file found inside the KMZ archive.';
            }
          }).catch(function(err) {
             communityStatus.textContent = 'Error reading KMZ: ' + err.message;
          });
          return; // async, don't proceed past here
        } else {
          communityStatus.textContent = 'Unsupported file type.';
          return;
        }
        communityStatus.textContent = 'Successfully added ' + esc(file.name);
      } catch(err) {
        communityStatus.textContent = 'Error parsing file: ' + err.message;
      }
    };
    
    if (ext === 'kmz') {
      reader.readAsArrayBuffer(file);
    } else {
      reader.readAsText(file);
    }
  });

  // ---------- drawings (RENAME AND STYLE ICONS) ----------
  var drawnItems = L.featureGroup().addTo(map);
  var drawnList = document.getElementById('drawn-list');
  var drawnGroups = document.getElementById('drawn-groups');
  var emptyNote = document.getElementById('drawn-empty');
  var counters = {};

  var typeMeta = {
    polyline:  {name:'Line',      svg:'<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"/></svg>'},
    polygon:   {name:'Polygon',   svg:'<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l8 6-3 10H7L4 9z"/></svg>'},
    rectangle: {name:'Rectangle', svg:'<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16"/></svg>'},
    circle:    {name:'Circle',    svg:'<svg viewBox="0 0 24 24" width="13" height="13"><circle cx="12" cy="12" r="8" fill="currentColor"/></svg>'},
    marker:    {name:'Marker',    svg:'<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>'}
  };
  var renameSvg = '<svg class="ic-rename" title="Rename" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4v16h16v-7"/><path d="M18 2l4 4-10 10H8v-4z"/></svg>';
  var styleSvg = '<svg class="ic-style" title="Style" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>';
  var eyeSvg = '<svg class="ic-eye" title="Show/hide" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/></svg>';
  var trashSvg = '<svg class="ic-trash" title="Delete" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/></svg>';
  var ungroupSvg = '<svg class="ic-ungroup" title="Ungroup" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="8" height="8"/><rect x="13" y="13" width="8" height="8"/></svg>';

  function refreshDrawnUI() {
    var n = drawnItems.getLayers().length;
    document.getElementById('drawcount').textContent = n;
    document.getElementById('layer-count').textContent = n;
    emptyNote.style.display = n ? 'none' : '';
  }
  function setRowVisible(row, visible) {
    var ly = row._layer;
    if (visible) map.addLayer(ly); else map.removeLayer(ly);
    row.classList.toggle('disabled', !visible);
    row.classList.toggle('selected', visible);
  }
  function deleteRow(row) {
    drawnItems.removeLayer(row._layer);
    row.remove();
    refreshDrawnUI();
  }
  function renameRow(row) {
    var currentName = row.querySelector('.lname').textContent;
    var newName = prompt('Enter new name:', currentName);
    if (newName && newName.trim() !== '') {
      row.querySelector('.lname').textContent = newName.trim();
    }
  }

  // Style Modal logic
  var styleModal = document.getElementById('style-modal');
  var activeStyleLayer = null;
  var activeStyleRow = null;
  var colorPresets = document.querySelectorAll('.style-presets div');
  var customColorInput = document.getElementById('style-custom-color');
  var styleFill = document.getElementById('style-fill');
  var styleOutline = document.getElementById('style-outline');
  var styleThickness = document.getElementById('style-thickness');
  var styleOpacity = document.getElementById('style-opacity');
  
  function applyStyle() {
    if (!activeStyleLayer) return;
    var hex = customColorInput.value;
    var fill = styleFill.checked;
    var outline = styleOutline.checked;
    var thickness = parseFloat(styleThickness.value);
    var opacity = parseFloat(styleOpacity.value);
    
    var isPoly = activeStyleLayer instanceof L.Polygon || activeStyleLayer instanceof L.Polyline || activeStyleLayer instanceof L.Circle;
    if (isPoly) {
      var newStyle = {
        color: outline ? hex : 'transparent',
        weight: thickness,
        opacity: outline ? opacity : 0,
        fillColor: fill ? hex : 'transparent',
        fillOpacity: fill ? opacity : 0
      };
      activeStyleLayer.setStyle(newStyle);
    } else if (activeStyleLayer instanceof L.CircleMarker) {
      activeStyleLayer.setStyle({color: hex, fillColor: hex, radius: Math.max(2, thickness)});
    }
  }

  function openStyleModal(layer, row) {
    activeStyleLayer = layer;
    activeStyleRow = row;
    var currentColor = layer.options.color || '#d33';
    customColorInput.value = currentColor;
    styleThickness.value = layer.options.weight || 3;
    styleOpacity.value = layer.options.opacity || 1;
    styleFill.checked = (layer.options.fillOpacity || 0) > 0;
    styleOutline.checked = (layer.options.opacity || 0) > 0;
    
    colorPresets.forEach(function(p){ p.classList.remove('active'); });
    styleModal.classList.add('open');
  }
  
  colorPresets.forEach(function(p) {
    p.onclick = function() {
      colorPresets.forEach(function(c){ c.classList.remove('active'); });
      this.classList.add('active');
      customColorInput.value = this.dataset.color;
      applyStyle();
    };
  });
  customColorInput.oninput = applyStyle;
  styleFill.onchange = applyStyle;
  styleOutline.onchange = applyStyle;
  styleThickness.oninput = applyStyle;
  styleOpacity.oninput = applyStyle;
  document.getElementById('style-close-btn').onclick = function() { styleModal.classList.remove('open'); };

  function addDrawnRow(layer, t, name) {
    var meta = typeMeta[t] || {name:t, svg:''};
    var row = document.createElement('div');
    row.className = 'layer-row selected';
    row._layer = layer;
    row.innerHTML = '<input type="checkbox" class="gcheck">' + meta.svg +
      '<span class="lname">' + esc(name) + '</span>' +
      '<span class="row-icons">' + renameSvg + styleSvg + eyeSvg + trashSvg + '</span>';
    
    row.querySelector('.gcheck').onclick = function (ev) { ev.stopPropagation(); };
    row.onclick = function () {
      try {
        if (layer.getBounds) map.fitBounds(layer.getBounds(), {padding:[30,30]});
        else map.setView(layer.getLatLng(), 15);
      } catch (err) {}
    };
    row.querySelector('.ic-rename').onclick = function (ev) { ev.stopPropagation(); renameRow(row); };
    row.querySelector('.ic-style').onclick = function (ev) { ev.stopPropagation(); openStyleModal(layer, row); };
    row.querySelector('.ic-eye').onclick = function (ev) {
      ev.stopPropagation(); setRowVisible(row, !map.hasLayer(layer));
    };
    row.querySelector('.ic-trash').onclick = function (ev) { ev.stopPropagation(); deleteRow(row); };
    drawnList.appendChild(row);
    refreshDrawnUI();
    return row;
  }

  map.on(L.Draw.Event.CREATED, function (e) {
    var layer = e.layer;
    var t = e.layerType;
    drawnItems.addLayer(layer);
    counters[t] = (counters[t] || 0) + 1;
    var name = (typeMeta[t] ? typeMeta[t].name : t) + ' ' + counters[t];
    bindFeature(layer, name, typeMeta[t] ? typeMeta[t].name : t);
    addDrawnRow(layer, t, name);
  });

  map.on('click', function (e) {
    document.getElementById('lastclick').textContent = e.latlng.lat.toFixed(4) + ', ' + e.latlng.lng.toFixed(4);
  });

  // ---------- layer grouping ----------
  var addGroupBtn = document.getElementById('add-group-btn');
  var groupBar = document.getElementById('group-bar');
  var groupCount = 0;
  function setGrouping(on) {
    drawnList.classList.toggle('grouping', on);
    groupBar.classList.toggle('open', on);
    addGroupBtn.classList.toggle('active', on);
    if (!on) drawnList.querySelectorAll('.gcheck').forEach(function (c) { c.checked = false; });
  }
  addGroupBtn.onclick = function () {
    if (!drawnList.querySelectorAll('.layer-row').length) { console.warn('Nothing to group'); return; }
    setGrouping(!drawnList.classList.contains('grouping'));
  };
  document.getElementById('group-cancel').onclick = function () { setGrouping(false); };
  document.getElementById('group-create').onclick = function () {
    var sel = drawnList.querySelectorAll('.gcheck:checked');
    if (!sel.length) { setGrouping(false); return; }
    groupCount++;
    var name = document.getElementById('group-name').value.trim() || ('Group ' + groupCount);
    document.getElementById('group-name').value = '';

    var grp = document.createElement('div');
    grp.className = 'layer-group drawn-group';
    grp.innerHTML = '<div class="group-head"><span class="chev"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg></span>' +
      '<span>' + esc(name) + '</span>' +
      '<span class="row-icons">' + renameSvg + eyeSvg + ungroupSvg + '</span></div><div class="group-body"></div>';
    var body = grp.querySelector('.group-body');
    sel.forEach(function (cb) { var r = cb.closest('.layer-row'); cb.checked = false; body.appendChild(r); });

    var gVisible = true;
    grp.querySelector('.group-head').onclick = function () { grp.classList.toggle('collapsed'); };
    grp.querySelector('.ic-rename').onclick = function (ev) {
      ev.stopPropagation();
      var currentName = grp.querySelector('.group-head span').textContent;
      var newName = prompt('Enter new group name:', currentName);
      if (newName && newName.trim() !== '') {
        grp.querySelector('.group-head span').textContent = newName.trim();
      }
    };
    grp.querySelector('.ic-eye').onclick = function (ev) {
      ev.stopPropagation();
      gVisible = !gVisible;
      body.querySelectorAll('.layer-row').forEach(function (r) { setRowVisible(r, gVisible); });
    };
    grp.querySelector('.ic-ungroup').onclick = function (ev) {
      ev.stopPropagation();
      body.querySelectorAll('.layer-row').forEach(function (r) { drawnList.appendChild(r); });
      grp.remove();
    };
    drawnGroups.appendChild(grp);
    setGrouping(false);
  };

  // ---------- toolbar ----------
  document.getElementById('clearbtn').onclick = function () {
    drawnItems.clearLayers();
    drawnList.querySelectorAll('.layer-row').forEach(function (r) { r.remove(); });
    drawnGroups.querySelectorAll('.layer-row').forEach(function (r) { r.remove(); });
    drawnGroups.querySelectorAll('.drawn-group').forEach(function (g) { g.remove(); });
    counters = {};
    refreshDrawnUI();
  };
  document.getElementById('db-toggle').onclick = function () {
    var db = document.getElementById('databrowser');
    var show = db.style.display === 'none';
    db.style.display = show ? 'flex' : 'none';
    this.classList.toggle('active', show);
  };

  var drawOpts = {shapeOptions: {color:'#d33', weight:3, bubblingMouseEvents:false}};
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
      var toolName = btn.dataset.tool;
      var isActive = btn.classList.contains('active');

      if (isActive) {
        btn.classList.remove('active');
        if (activeHandler) { activeHandler.disable(); activeHandler = null; }
        return;
      }

      document.querySelectorAll('.tool').forEach(function (b) { b.classList.remove('active'); });
      if (activeHandler) { activeHandler.disable(); activeHandler = null; }

      activeHandler = handlers[toolName];
      if (activeHandler) { activeHandler.enable(); }
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

  // ---------- search panel (Nominatim geocoding) + AUTO CLOSE DATA BROWSER ----------
  var searchPanel = document.getElementById('search-panel');
  var searchMarker = null;
  document.getElementById('searchbtn').onclick = function () {
    // Auto-close databrowser
    var db = document.getElementById('databrowser');
    var dbToggle = document.getElementById('db-toggle');
    if(db.style.display === 'flex') {
        db.style.display = 'none';
        dbToggle.classList.remove('active');
    }

    searchPanel.classList.toggle('open');
    this.classList.toggle('active', searchPanel.classList.contains('open'));
    if (searchPanel.classList.contains('open')) document.getElementById('search-input').focus();
  };
  document.getElementById('search-close').onclick = function () {
    searchPanel.classList.remove('open');
    document.getElementById('searchbtn').classList.remove('active');
  };
  function doSearch() {
    var q = document.getElementById('search-input').value.trim();
    if (!q) return;
    var res = document.getElementById('search-results');
    res.innerHTML = '<div class="sr-item">Searching...</div>';
    fetch('https://nominatim.openstreetmap.org/search?format=json&limit=6&q=' + encodeURIComponent(q))
      .then(function (r) { return r.json(); })
      .then(function (rows) {
        res.innerHTML = '';
        if (!rows.length) { res.innerHTML = '<div class="sr-item">No results found</div>'; return; }
        rows.forEach(function (row) {
          var d = document.createElement('div');
          d.className = 'sr-item';
          d.innerHTML = '<div>' + esc(row.display_name.split(',')[0]) + '</div><div class="sr-sub">' + esc(row.type) + '</div>';
          d.onclick = function () {
            var ll = [parseFloat(row.lat), parseFloat(row.lon)];
            map.flyTo(ll, 14);
            if (searchMarker) map.removeLayer(searchMarker);
            searchMarker = L.marker(ll).addTo(map);
            showFeature(searchMarker, row.display_name.split(',')[0], 'Search result');
          };
          res.appendChild(d);
        });
      })
      .catch(function () { res.innerHTML = '<div class="sr-item">Search failed (network)</div>'; });
  }
  document.getElementById('search-go').onclick = doSearch;
  document.getElementById('search-input').addEventListener('keydown', function (e) { if (e.key === 'Enter') doSearch(); });

  // ---------- panel controls ----------
  document.getElementById('db-close').onclick = function () { document.getElementById('databrowser').style.display = 'none'; document.getElementById('db-toggle').classList.remove('active'); };
  document.getElementById('db-collapse').onclick = function () {
    var b = document.getElementById('db-body');
    b.style.display = (b.style.display === 'none') ? '' : 'none';
  };
  document.getElementById('details-close').onclick = function () { document.getElementById('details').style.display = 'none'; };

  refreshDrawnUI();
} catch (err) {
  console.error('Map init failed:', err);
}
</script>
</body>
</html>
"""

components.html(APP_HTML, height=1080, scrolling=False)

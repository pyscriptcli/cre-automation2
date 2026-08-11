import streamlit as st
import folium
from streamlit_folium import st_folium

# 1. Page Configuration
st.set_page_config(
    page_title="Industrial Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Custom CSS and HTML UI Overlay
# We inject fixed-position HTML elements to perfectly clone the floating panels and navbar
ui_overlay = """
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
/* Reset Streamlit default paddings */
.block-container {
    padding-top: 0rem !important;
    padding-bottom: 0rem !important;
    padding-left: 0rem !important;
    padding-right: 0rem !important;
    max-width: 100% !important;
}
header { visibility: hidden !important; }
footer { visibility: hidden !important; }

/* Top Navigation Bar */
.top-navbar {
    position: fixed;
    top: 0; left: 0; width: 100%; height: 45px;
    background: #2b2b2b;
    border-bottom: 1px solid #1a1a1a;
    display: flex; justify-content: space-between; align-items: center;
    padding: 0 20px; box-sizing: border-box;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    z-index: 999999;
}
.top-navbar-left, .top-navbar-right {
    display: flex; align-items: center; gap: 20px;
}
.logo-title {
    color: white; font-weight: 600; font-size: 14px;
    display: flex; align-items: center; gap: 8px;
}
.logo-icon {
    background: white; color: #2b2b2b; 
    border-radius: 50%; width: 22px; height: 22px;
    display: flex; justify-content: center; align-items: center;
    font-size: 12px;
}
.badge-draft { color: #999; font-size: 12px; display: flex; align-items: center; gap: 5px; }
.nav-actions { display: flex; gap: 8px; color: #666; margin-left: 10px; }
.user-info { color: #ccc; font-size: 13px; display: flex; align-items: center; gap: 5px; }
.btn-view {
    background: #4a4a4a; color: white; border: 1px solid #555;
    padding: 4px 12px; border-radius: 3px; font-size: 13px;
    cursor: pointer; display: flex; align-items: center; gap: 6px;
}
.btn-save {
    background: #2b2b2b; color: #555; border: 1px solid #444;
    padding: 4px 12px; border-radius: 3px; font-size: 13px;
}

/* Left Map Tools & Panel */
.left-panel-wrapper {
    position: fixed; top: 60px; left: 20px; z-index: 999999;
    display: flex; height: calc(100vh - 100px);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.map-toolbar {
    width: 40px; background: white;
    border: 1px solid #ccc; border-radius: 4px 0 0 4px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    display: flex; flex-direction: column; align-items: center;
    padding: 8px 0; gap: 12px;
}
.map-toolbar i { color: #444; font-size: 14px; cursor: pointer; }
.map-toolbar hr { width: 60%; border: none; border-top: 1px solid #eee; margin: 4px 0; }
.left-panel-content {
    width: 320px; background: white;
    border: 1px solid #ccc; border-left: none; border-radius: 0 4px 4px 4px;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    padding: 20px; box-sizing: border-box;
}
.panel-header { font-size: 16px; font-weight: 600; color: #222; margin-bottom: 20px; display: flex; align-items: center; gap: 8px; }
.panel-header .controls { margin-left: auto; color: #999; font-size: 12px; display: flex; gap: 10px; }
.btn-filter {
    background: white; border: 1px solid #ccc; color: #444;
    padding: 6px 12px; border-radius: 4px; font-size: 13px;
    display: inline-flex; align-items: center; gap: 6px; margin-bottom: 15px; cursor: pointer;
}
.section-title { font-size: 13px; font-weight: 600; color: #222; border-bottom: 1px solid #eee; padding-bottom: 8px; margin-bottom: 10px; display: flex; justify-content: space-between; }
.section-title .icons { color: #999; font-weight: normal; display: flex; gap: 8px; }
.layer-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 10px; font-size: 13px; border-radius: 4px; margin-bottom: 4px; }
.layer-row.active { background: #e8e8e8; color: #222; border: 1px solid #bbb; }
.layer-row.inactive { background: #f9f9f9; color: #999; border: 1px solid #eee; }
.layer-actions i { color: #999; margin-left: 10px; cursor: pointer; }

/* Right Details Panel */
.right-panel {
    position: fixed; top: 60px; right: 20px; z-index: 999999;
    width: 360px; background: white;
    border: 1px solid #ccc; border-radius: 4px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    padding: 20px; box-sizing: border-box;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.right-panel .close-btn { position: absolute; top: 20px; right: 20px; color: #aaa; cursor: pointer; }
.right-panel h2 { margin: 0 0 15px 0; font-size: 20px; color: #222; border-bottom: 2px solid #5a98d3; padding-bottom: 10px; font-weight: normal;}
.right-panel .desc { font-size: 13px; color: #666; margin-bottom: 25px; line-height: 1.4; }
.metric-label { font-size: 11px; color: #777; text-transform: uppercase; margin-bottom: 4px; letter-spacing: 0.5px; }
.metric-value { font-size: 14px; color: #222; margin-bottom: 15px; }
.right-panel h3 { margin: 15px 0 15px 0; font-size: 15px; color: #222; border-bottom: 2px solid #5a98d3; padding-bottom: 8px; font-weight: normal;}
.analytics-grid { display: grid; grid-template-columns: 1fr 1fr; row-gap: 15px; column-gap: 10px; }
.val-main { font-size: 14px; font-weight: 600; color: #222; }
.val-up { color: #35a84b; font-size: 12px; margin-left: 2px; font-weight: normal; }
.val-down { color: #e04b4b; font-size: 12px; margin-left: 2px; font-weight: normal; }
.val-neutral { color: #888; font-size: 12px; margin-left: 2px; font-weight: normal; }
.footer-text { font-size: 11px; color: #888; margin-top: 25px; line-height: 1.4; }
</style>

<!-- Top Navbar -->
<div class="top-navbar">
    <div class="top-navbar-left">
        <div class="logo-title"><div class="logo-icon"><i class="fas fa-map-marker-alt"></i></div> Industrial Intelligence</div>
        <div class="badge-draft">
            <i class="far fa-eye" style="margin-right:2px"></i> Visibility: Draft (private)
            <div class="nav-actions"><i class="fas fa-undo"></i> <i class="fas fa-redo"></i></div>
        </div>
    </div>
    <div class="top-navbar-right">
        <div class="user-info"><i class="far fa-user-circle"></i> Dave7305 &nbsp;|&nbsp; Help</div>
        <div class="btn-view"><i class="far fa-eye"></i> View</div>
        <div class="btn-save">Save draft</div>
    </div>
</div>

<!-- Left Interface -->
<div class="left-panel-wrapper">
    <div class="map-toolbar">
        <i class="fas fa-plus"></i>
        <i class="fas fa-minus"></i>
        <hr>
        <i class="fas fa-search"></i>
        <i class="fas fa-pencil-alt"></i>
        <i class="fas fa-home"></i>
        <i class="fas fa-layer-group"></i>
        <i class="fas fa-map-marker-alt"></i>
        <hr>
        <i class="far fa-square"></i>
        <i class="far fa-trash-alt"></i>
    </div>
    <div class="left-panel-content">
        <div class="panel-header">
            <i class="fas fa-layer-group"></i> Data browser
            <div class="controls"><i class="fas fa-expand-arrows-alt"></i> <i class="fas fa-times"></i></div>
        </div>
        <div class="btn-filter"><i class="fas fa-filter"></i> Filters</div>
        <div class="section-title">Layers <div class="icons"><i class="far fa-copy"></i> <i class="far fa-eye"></i> <i class="fas fa-pen"></i> <i class="far fa-trash-alt"></i></div></div>
        
        <div class="layer-row active">
            <span><i class="fas fa-folder" style="color:#666; margin-right:6px"></i> Roads</span>
            <div class="layer-actions"><i class="far fa-eye"></i> <i class="fas fa-pencil-alt"></i> <i class="far fa-trash-alt"></i></div>
        </div>
        <div class="layer-row inactive">
            <span><i class="fas fa-folder" style="color:#999; margin-right:6px"></i> Boundaries</span>
            <div class="layer-actions"><i class="far fa-eye-slash"></i> <i class="fas fa-pencil-alt"></i> <i class="far fa-trash-alt"></i></div>
        </div>
    </div>
</div>

<!-- Right Interface -->
<div class="right-panel">
    <i class="fas fa-times close-btn"></i>
    <h2>Details</h2>
    <div class="desc">Click on a marker, polygon, or draw on the map to see details here.</div>
    
    <div class="metric-label">LAST CLICK</div>
    <div class="metric-value">-</div>
    
    <div class="metric-label">ACTIVE DRAWINGS</div>
    <div class="metric-value">0</div>
    
    <h3>Advanced Analytics</h3>
    <div class="analytics-grid">
        <div>
            <div class="metric-label">AVG RENTAL RATE</div>
            <div class="val-main">&#8369; 850/m&sup2; <span class="val-up">&uarr;3.2%</span></div>
        </div>
        <div>
            <div class="metric-label">PRIME CORE INDEX</div>
            <div class="val-main">87.5 <span class="val-up">&uarr;1.8%</span></div>
        </div>
        <div>
            <div class="metric-label">ROAD DENSITY</div>
            <div class="val-main">2.4 km/km&sup2; <span class="val-up">&uarr;0.3</span></div>
        </div>
        <div>
            <div class="metric-label">ZONING COMPLIANCE</div>
            <div class="val-main">94% <span class="val-up">&uarr;2%</span></div>
        </div>
        <div>
            <div class="metric-label">FLOOD RISK INDEX</div>
            <div class="val-main">Medium (4.2) <span class="val-down">&uarr;0.5</span></div>
        </div>
        <div>
            <div class="metric-label">EARTHQUAKE SUSCEPT.</div>
            <div class="val-main">Low (2.1) <span class="val-neutral">&rarr;0.0</span></div>
        </div>
    </div>
    
    <div class="footer-text">Smart Comparable Analysis: Advanced scoring algorithms for property valuation</div>
</div>
"""

st.markdown(ui_overlay, unsafe_allow_html=True)

# 3. Render the Base Map
# Centered on Metro Manila/Bulacan area as shown in the screenshot
m = folium.Map(location=[14.73, 121.05], zoom_start=11, tiles="OpenStreetMap")

# Add some mock green polygons to replicate the visual data boundaries on the map (San Jose del Monte, etc.)
folium.Polygon(
    locations=[
        [14.740, 121.050], [14.780, 121.090], 
        [14.810, 121.070], [14.800, 121.020]
    ],
    color="green", fill=True, fill_color="green", fill_opacity=0.4, weight=1
).add_to(m)

folium.Polygon(
    locations=[
        [14.720, 121.120], [14.780, 121.140], 
        [14.800, 121.180], [14.750, 121.220],
        [14.680, 121.180]
    ],
    color="green", fill=True, fill_color="green", fill_opacity=0.4, weight=1
).add_to(m)

# Render map utilizing the entire screen space natively
st_folium(m, width="100%", height=1000, returned_objects=[])

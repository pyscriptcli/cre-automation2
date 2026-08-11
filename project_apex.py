import streamlit as st
import pandas as pd
import pydeck as pdk

# Page configuration
st.set_page_config(layout="wide", page_title="Industrial Intelligence", initial_sidebar_state="collapsed")

# Inject CSS
st.markdown("""
<style>
    /* Hide Streamlit defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Reset block container to fill screen */
    .block-container {
        padding-top: 0rem !important;
        padding-right: 0rem !important;
        padding-left: 0rem !important;
        max-width: 100% !important;
    }
    .stApp {
        background-color: #f0f2f5;
        margin: 0;
        overflow: hidden;
    }

    /* Top Bar */
    .top-bar {
        background-color: #ffffff;
        border-bottom: 1px solid #eaeaea;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 20px;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 2000;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        box-sizing: border-box;
    }
    .top-bar-left { display: flex; align-items: center; gap: 15px; }
    .logo { display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 14px; color: #333; }
    .logo-svg { width: 18px; height: 18px; }
    .breadcrumb { background: #f5f5f5; padding: 3px 12px; border-radius: 4px; font-size: 11px; color: #666; border: 1px solid #e0e0e0; display: flex; align-items: center; gap: 5px; }
    .breadcrumb-dot { width: 6px; height: 6px; background: #8bc34a; border-radius: 50%; display: inline-block; }
    .top-bar-right { display: flex; align-items: center; gap: 15px; font-size: 12px; color: #666; }
    .top-bar-btn { padding: 4px 8px; border: 1px solid #e0e0e0; border-radius: 4px; background: white; font-size: 11px; color: #555; display: flex; align-items: center; gap: 5px; }
    .profile-circle { width: 28px; height: 28px; background: #333; color: white; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 12px; font-weight: 500; }
    .top-separator { color: #e0e0e0; }

    /* Floating Left Panel */
    .left-panel {
        position: fixed;
        top: 65px;
        left: 15px;
        width: 320px;
        max-height: calc(100vh - 80px);
        background: white;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        padding: 15px;
        z-index: 1000;
        overflow-y: auto;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        border: 1px solid #f0f0f0;
        box-sizing: border-box;
    }
    
    /* Floating Right Panel */
    .right-panel {
        position: fixed;
        top: 65px;
        right: 15px;
        width: 350px;
        max-height: calc(100vh - 80px);
        background: white;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        padding: 15px;
        z-index: 1000;
        overflow-y: auto;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        border: 1px solid #f0f0f0;
        box-sizing: border-box;
    }

    /* Left Panel Components */
    .panel-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f0f0f0; padding-bottom: 12px; margin-bottom: 12px; }
    .panel-title { font-weight: 600; font-size: 16px; color: #333; }
    .close-btn { cursor: pointer; display: flex; align-items: center; }
    
    .filter-section { border: 1px solid #f0f0f0; border-radius: 4px; padding: 6px 10px; margin-bottom: 15px; display: flex; align-items: center; gap: 8px; font-size: 13px; color: #555; background: #fafafa; }
    .filter-icon { display: flex; align-items: center; }

    .layer-header { display: flex; justify-content: space-between; font-size: 11px; font-weight: bold; color: #333; margin-bottom: 8px; }
    .layer-actions { display: flex; gap: 6px; color: #888; }
    
    .layer-item { display: flex; align-items: center; justify-content: space-between; padding: 6px 0; font-size: 13px; color: #444; }
    .layer-item-left { display: flex; align-items: center; gap: 10px; }
    .layer-color { width: 14px; height: 14px; border-radius: 2px; border: 1px solid #ddd; }
    .layer-item-right { display: flex; align-items: center; gap: 8px; color: #888; }
    .layer-item-right .icon { cursor: pointer; display: flex; align-items: center; }

    /* Right Panel Components */
    .details-placeholder {
        background: #f9f9f9;
        border-radius: 6px;
        padding: 15px;
        text-align: center;
        font-size: 13px;
        color: #666;
        margin-bottom: 15px;
        line-height: 1.4;
        border: 1px solid #f0f0f0;
    }
    .detail-row { margin-bottom: 12px; }
    .detail-label { font-weight: bold; color: #333; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
    .detail-value { color: #999; font-size: 13px; margin-top: 2px; display: block; }

    .analytics-wrap { margin-top: 15px; }
    .analytics-title {
        color: #2c6eb2;
        font-size: 16px;
        font-weight: 500;
        border-bottom: 2px solid #2c6eb2;
        padding-bottom: 8px;
        margin-bottom: 15px;
        display: inline-block;
    }

    .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
    .stat-item { display: flex; flex-direction: column; }
    .stat-label { font-size: 10px; font-weight: bold; color: #888; text-transform: uppercase; margin-bottom: 3px; letter-spacing: 0.3px; }
    .stat-value { font-size: 18px; font-weight: 500; color: #222; margin-bottom: 1px; }
    .stat-delta { font-size: 11px; color: #4caf50; font-weight: 500; }
    
    .footer-text {
        margin-top: 20px;
        font-size: 10px;
        color: #999;
        border-top: 1px solid #f0f0f0;
        padding-top: 12px;
        line-height: 1.4;
    }

    /* Map Wrapper */
    .map-container {
        position: fixed;
        top: 50px;
        left: 0;
        width: 100%;
        height: calc(100vh - 50px);
        z-index: 1;
    }
</style>
""", unsafe_allow_html=True)

# Top Bar HTML
st.markdown("""
<div class="top-bar">
    <div class="top-bar-left">
        <div class="logo">
            <svg class="logo-svg" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="12" fill="#222"/>
                <path d="M8 8L16 12L8 16V8Z" fill="white"/>
            </svg>
            Industrial Intelligence
        </div>
        <div class="breadcrumb">
            <span class="breadcrumb-dot"></span> Visibility: Simple (private)
        </div>
    </div>
    <div class="top-bar-right">
        <span>Saved</span>
        <span class="top-separator">|</span>
        <span>Help</span>
        <span class="top-separator">|</span>
        <span>View</span>
        <span class="top-separator">|</span>
        <span>Save as...</span>
        <div class="profile-circle">U</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Left Panel HTML
st.markdown("""
<div class="left-panel">
    <div class="panel-header">
        <div class="panel-title">Data browser</div>
        <div class="close-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#999" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
        </div>
    </div>
    
    <div class="filter-section">
        <span class="filter-icon">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#555" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="22 3 2 3 10 13 10 21 14 18 14 13 22 3"></polygon>
            </svg>
        </span>
        <span>Filters</span>
    </div>

    <div class="layer-header">
        <span>Layers</span>
        <div class="layer-actions">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
            </svg>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
            </svg>
        </div>
    </div>

    <div class="layer-item">
        <div class="layer-item-left">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#666" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <path d="M9 12l2 2 4-4"></path>
            </svg>
            <div class="layer-color" style="background:#6b6b6b;"></div>
            <span>Roads</span>
        </div>
        <div class="layer-item-right">
            <span class="icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                </svg>
            </span>
            <span class="icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 3l4 4-10 10-4-4 10-10z"></path>
                    <path d="M21 15v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5"></path>
                </svg>
            </span>
            <span class="icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
            </span>
        </div>
    </div>

    <div class="layer-item">
        <div class="layer-item-left">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#666" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <path d="M9 12l2 2 4-4"></path>
            </svg>
            <div class="layer-color" style="background:#8bc34a;"></div>
            <span>Boundaries</span>
        </div>
        <div class="layer-item-right">
            <span class="icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                </svg>
            </span>
            <span class="icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 3l4 4-10 10-4-4 10-10z"></path>
                    <path d="M21 15v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5"></path>
                </svg>
            </span>
            <span class="icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Right Panel HTML
st.markdown("""
<div class="right-panel">
    <div class="panel-header">
        <div class="panel-title">Details</div>
        <div class="close-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#999" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
        </div>
    </div>
    
    <div class="details-placeholder">
        Click on a marker, polygon, or draw on the map to see details here.
    </div>
    
    <div class="detail-row">
        <span class="detail-label">LAST CLICK</span>
        <span class="detail-value">-</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">ACTIVE DRAWINGS</span>
        <span class="detail-value">0</span>
    </div>

    <div class="analytics-wrap">
        <div class="analytics-title">Advanced Analytics</div>
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-label">AVG RENTAL RATE</div>
                <div class="stat-value">&#8369; 850/m&sup2;</div>
                <div class="stat-delta">+3.2%</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">PRIME CORE INDEX</div>
                <div class="stat-value">87.5</div>
                <div class="stat-delta">+1.8%</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">ROAD DENSITY</div>
                <div class="stat-value">2.4 km/km&sup2;</div>
                <div class="stat-delta">+0.3</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">ZONING COMPLIANCE</div>
                <div class="stat-value">94%</div>
                <div class="stat-delta">+2%</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">FLOOD RISK INDEX</div>
                <div class="stat-value" style="font-size: 15px;">Medium (4.2)</div>
                <div class="stat-delta">+0.5</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">EARTHQUAKE SUSCEPT.</div>
                <div class="stat-value" style="font-size: 15px;">Low (2.1)</div>
                <div class="stat-delta">+0.0</div>
            </div>
        </div>
    </div>

    <div class="footer-text">
        Smart Comparable Analysis: Advanced scoring algorithms for property valuation
    </div>
</div>
""", unsafe_allow_html=True)

# Define Map Data
# Approximate coordinates for Manila, Philippines
view_state = pdk.ViewState(
    latitude=14.55,
    longitude=121.03,
    zoom=11,
    pitch=0
)

# Generate dummy polygons (Boundaries)
polygons_data = [
    {"polygon": [[121.00, 14.58], [121.04, 14.58], [121.05, 14.62], [121.01, 14.63]]},
    {"polygon": [[121.05, 14.55], [121.09, 14.56], [121.10, 14.59], [121.06, 14.60]]},
    {"polygon": [[121.11, 14.61], [121.15, 14.62], [121.16, 14.65], [121.12, 14.66]]},
    {"polygon": [[121.02, 14.50], [121.06, 14.51], [121.07, 14.54], [121.03, 14.55]]},
]
poly_df = pd.DataFrame(polygons_data)

# Polygons Layer (Green Overlay)
polygon_layer = pdk.Layer(
    "PolygonLayer",
    poly_df,
    get_polygon="polygon",
    get_fill_color=[139, 195, 74, 150],
    get_line_color=[0, 0, 0, 0],
    pickable=True
)

# Generate dummy paths (Roads)
roads_data = [
    {"path": [[121.00, 14.54], [121.02, 14.54], [121.05, 14.54], [121.08, 14.54]]},
    {"path": [[121.03, 14.53], [121.03, 14.56], [121.03, 14.59], [121.03, 14.62]]},
    {"path": [[121.01, 14.59], [121.04, 14.60], [121.07, 14.59], [121.10, 14.58]]},
    {"path": [[121.05, 14.55], [121.05, 14.58], [121.05, 14.61]]},
    {"path": [[121.01, 14.52], [121.04, 14.53], [121.07, 14.52]]},
]
road_df = pd.DataFrame(roads_data)

# Paths Layer (Grey Lines)
path_layer = pdk.Layer(
    "PathLayer",
    road_df,
    get_path="path",
    get_width=2,
    get_color=[80, 80, 80, 150],
    width_min_pixels=1.5
)

# Compose Deck
deck = pdk.Deck(
    layers=[path_layer, polygon_layer],
    initial_view_state=view_state,
    map_style="light"
)

# Render Map (Must be the last element to sit behind the fixed panels)
st.pydeck_chart(deck, height=1200, use_container_width=True)

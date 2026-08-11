import streamlit as st
import streamlit.components.v1 as components

# Configure the page layout to wide and remove default padding to fit the dashboard look
st.set_page_config(layout="wide", page_title="Industrial Intelligence - Visuality")

# Custom CSS to mimic the exact dark header, panels, fonts, and layout of the reference image
st.markdown("""
<style>
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    
    /* Global styling */
    body {
        background-color: #1e1e1e;
        color: #333333;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Top Navigation Bar */
    .top-nav {
        background-color: #262626;
        color: #d1d5db;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 16px;
        font-size: 13px;
        border-bottom: 1px solid #383838;
        height: 40px;
    }
    .top-nav-left {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .brand-title {
        color: #ffffff;
        font-weight: 600;
        font-size: 14px;
        letter-spacing: 0.3px;
    }
    .sub-title {
        color: #9ca3af;
        font-style: italic;
    }
    .top-nav-right {
        display: flex;
        align-items: center;
        gap: 20px;
        color: #9ca3af;
    }
    .user-profile {
        display: flex;
        align-items: center;
        gap: 6px;
        color: #d1d5db;
    }
    .action-btn {
        background: #374151;
        color: #ffffff;
        border: none;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 12px;
        cursor: pointer;
    }

    /* Floating Data Browser Panel */
    .data-browser-panel {
        position: absolute;
        top: 60px;
        left: 20px;
        width: 320px;
        background: #ffffff;
        border-radius: 4px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 999;
        border: 1px solid #e5e7eb;
    }
    .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        border-bottom: 1px solid #f3f4f6;
        font-weight: 600;
        font-size: 14px;
        color: #1f2937;
    }
    .panel-controls {
        padding: 12px 16px;
        border-bottom: 1px solid #f3f4f6;
    }
    .filter-btn {
        background: #f3f4f6;
        border: 1px solid #d1d5db;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
        color: #374151;
        cursor: pointer;
    }
    .layers-section {
        padding: 12px 16px;
    }
    .layer-title {
        font-size: 12px;
        font-weight: 700;
        color: #4b5563;
        text-transform: uppercase;
        margin-bottom: 8px;
        letter-spacing: 0.5px;
    }
    .layer-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #f9fafb;
        padding: 8px 10px;
        border-radius: 4px;
        margin-bottom: 6px;
        border: 1px solid #e5e7eb;
        font-size: 13px;
        color: #374151;
    }

    /* Floating Details Panel */
    .details-panel {
        position: absolute;
        top: 60px;
        right: 20px;
        width: 360px;
        background: #ffffff;
        border-radius: 4px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 999;
        border: 1px solid #e5e7eb;
        padding: 16px;
    }
    .details-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        border-bottom: 1px solid #e5e7eb;
        padding-bottom: 12px;
        margin-bottom: 12px;
    }
    .details-title {
        font-size: 18px;
        font-weight: 600;
        color: #111827;
    }
    .details-instruction {
        font-size: 12px;
        color: #6b7280;
        margin-top: 4px;
    }
    .metric-section-title {
        font-size: 13px;
        font-weight: 700;
        color: #1f2937;
        margin-top: 16px;
        margin-bottom: 12px;
        border-bottom: 1px solid #e5e7eb;
        padding-bottom: 4px;
    }
    .analytics-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-bottom: 12px;
    }
    .analytics-card {
        background: #ffffff;
    }
    .analytics-label {
        font-size: 11px;
        color: #6b7280;
        text-transform: uppercase;
        font-weight: 600;
    }
    .analytics-value {
        font-size: 15px;
        font-weight: 600;
        color: #111827;
        margin-top: 2px;
    }
    .trend-positive {
        color: #10b981;
        font-size: 11px;
        font-weight: 500;
        margin-left: 4px;
    }
    .trend-negative {
        color: #ef4444;
        font-size: 11px;
        font-weight: 500;
        margin-left: 4px;
    }
    .trend-neutral {
        color: #6b7280;
        font-size: 11px;
        font-weight: 500;
        margin-left: 4px;
    }
    .footer-note {
        font-size: 11px;
        color: #6b7280;
        border-top: 1px solid #e5e7eb;
        padding-top: 10px;
        margin-top: 10px;
        line-height: 1.4;
    }
</style>

<!-- Top Navigation Bar -->
<div class="top-nav">
    <div class="top-nav-left">
        <span class="brand-title">Industrial Intelligence</span>
        <span style="color: #4b5563;">|</span>
        <span class="sub-title">Visuality: Draft (rebuild)</span>
    </div>
    <div class="top-nav-right">
        <div class="user-profile">
            <span>Dewet73M</span>
        </div>
        <span>|</span>
        <span>Help</span>
        <span>|</span>
        <button class="action-btn">View</button>
        <button class="action-btn" style="background: #2563eb;">Save draft</button>
    </div>
</div>
""", unsafe_allow_html=True)

# Leaflet Map integrated via HTML/JS Component mimicking the exact Manila/Metro area view and polygon overlays
leaflet_map_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        html, body, #map {
            width: 100%;
            height: 100vh;
            margin: 0;
            padding: 0;
            background: #f2efe9;
        }
        /* Custom styling for leaflet controls to match interface */
        .leaflet-control-zoom {
            border: 1px solid #ccc !important;
            box-shadow: 0 1px 5px rgba(0,0,0,0.2) !important;
            border-radius: 4px !important;
        }
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        // Initialize map centered around Metro Manila / San Jose del Monte area matching the image
        var map = L.map('map', {
            zoomControl: false,
            attributionControl: false
        }).setView([14.75, 121.05], 11);

        // Add standard OSM tile layer styled similar to the reference map background
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
        }).addTo(map);

        // Add custom zoom control to top-left area below UI elements
        L.control.zoom({
            position: 'topleft'
        }).addTo(map);

        // Custom polygon overlays simulating the green zones shown in the image
        var greenStyle = {
            color: '#2d8a39',
            weight: 2,
            fillColor: '#43a047',
            fillOpacity: 0.4
        };

        // Polygon 1 (San Jose del Monte / Montalban area simulation)
        var polyCoords1 = [
            [14.82, 121.02],
            [14.80, 121.07],
            [14.73, 121.08],
            [14.73, 121.03],
            [14.78, 121.01]
        ];
        L.polygon(polyCoords1, greenStyle).addTo(map);

        // Polygon 2 (Rodriguez / Wawa area simulation)
        var polyCoords2 = [
            [14.78, 121.12],
            [14.79, 121.16],
            [14.73, 121.18],
            [14.70, 121.14],
            [14.72, 121.10]
        ];
        L.polygon(polyCoords2, greenStyle).addTo(map);

        // Blue dashed line simulation across Manila Bay area
        var lineCoords = [
            [14.50, 120.90],
            [14.58, 120.98],
            [14.62, 121.02]
        ];
        L.polyline(lineCoords, {
            color: '#3b82f6',
            weight: 3,
            dashArray: '5, 10'
        }).addTo(map);
    </script>
</body>
</html>
"""

# Render the interactive map filling the screen
components.html(leaflet_map_html, height=920, scrolling=False)

# Floating Data Browser Panel (HTML Overlay)
st.markdown("""
<div class="data-browser-panel">
    <div class="panel-header">
        <span>Data browser</span>
        <span style="cursor: pointer; color: #9ca3af; font-size: 16px;">&times;</span>
    </div>
    <div class="panel-controls">
        <button class="filter-btn">Filters</button>
    </div>
    <div class="layers-section">
        <div class="layer-title">Layers</div>
        <div class="layer-item">
            <span>Roads</span>
            <div style="display: flex; gap: 10px; color: #6b7280; font-size: 12px;">
                <span>&#128065;</span>
                <span>&#9998;</span>
                <span>&#128465;</span>
            </div>
        </div>
        <div class="layer-item">
            <span>Boundaries</span>
            <div style="display: flex; gap: 10px; color: #6b7280; font-size: 12px;">
                <span>&#128065;</span>
                <span>&#9998;</span>
                <span>&#128465;</span>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Floating Details & Advanced Analytics Panel (HTML Overlay)
st.markdown("""
<div class="details-panel">
    <div class="details-header">
        <div>
            <div class="details-title">Details</div>
            <div class="details-instruction">Click on a marker, polygon, or draw on the map to see details here.</div>
        </div>
        <span style="cursor: pointer; color: #9ca3af; font-size: 16px;">&times;</span>
    </div>
    
    <div style="margin-bottom: 16px;">
        <div class="analytics-label">LAST CLICK</div>
        <div class="analytics-value" style="font-weight: 400; color: #6b7280; font-size: 14px; margin-top: 4px;">-</div>
    </div>
    
    <div style="margin-bottom: 16px;">
        <div class="analytics-label">ACTIVE DRAWINGS</div>
        <div class="analytics-value" style="font-weight: 400; color: #111827; font-size: 14px; margin-top: 4px;">0</div>
    </div>
    
    <div class="metric-section-title">Advanced Analytics</div>
    
    <div class="analytics-grid">
        <div class="analytics-card">
            <div class="analytics-label">AVG RENTAL RATE</div>
            <div class="analytics-value">P 850/m&sup2;<span class="trend-positive">&uarr;3.2%</span></div>
        </div>
        <div class="analytics-card">
            <div class="analytics-label">PRIME CORE INDEX</div>
            <div class="analytics-value">87.5<span class="trend-positive">&uarr;1.8%</span></div>
        </div>
    </div>
    
    <div class="analytics-grid">
        <div class="analytics-card">
            <div class="analytics-label">ROAD DENSITY</div>
            <div class="analytics-value">2.4 km/km&sup2;<span class="trend-positive">&uarr;0.3</span></div>
        </div>
        <div class="analytics-card">
            <div class="analytics-label">ZONING COMPLIANCE</div>
            <div class="analytics-value">94%<span class="trend-positive">&uarr;2%</span></div>
        </div>
    </div>
    
    <div class="analytics-grid">
        <div class="analytics-card">
            <div class="analytics-label">FLOOD RISK INDEX</div>
            <div class="analytics-value" style="font-size: 14px;">Medium (4.2)<span class="trend-negative">&darr;0.5</span></div>
        </div>
        <div class="analytics-card">
            <div class="analytics-label">EARTHQUAKE SUSCEPT.</div>
            <div class="analytics-value" style="font-size: 14px;">Low (2.1)<span class="trend-neutral">&rarr;0.0</span></div>
        </div>
    </div>
    
    <div class="footer-note">
        Smart Comparable Analysis: Advanced scoring algorithms for property valuation
    </div>
</div>
""", unsafe_allow_html=True)

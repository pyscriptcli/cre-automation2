import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import streamlit as st
import json
import re
from config import load_poi_configuration
from scraper import run_spatial_layer_scan, compile_features_kml

def render_unified_dashboard_sidebar():
    config_data = load_poi_configuration()
    poi_config = config_data.get("POI_CONFIG", {})
    
    with st.sidebar:
        st.markdown('<div class="brand-title">Open Node</div>', unsafe_allow_html=True)
        
        if st.session_state.sidebar_error_msg:
            st.error(st.session_state.sidebar_error_msg)
            
        selected_tuples = []
        scan_triggered = st.button("SCAN AREA", type="secondary", use_container_width=True, key="scan_btn")
        
        location_input = st.text_input("COORDINATES", value=st.session_state.geo_coords, key="geo_coords_input")
        radius_val = st.number_input("RADIUS (METERS)", min_value=100, max_value=50000, value=st.session_state.geo_radius, step=100)
        st.session_state.geo_radius = radius_val

        coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", location_input)
        if coord_match:
            lat_coord, lon_coord = float(coord_match.group(1)), float(coord_match.group(2))
            st.session_state.geo_coords = location_input
        else:
            fallback_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", st.session_state.geo_coords)
            lat_coord, lon_coord = (float(fallback_match.group(1)), float(fallback_match.group(2))) if fallback_match else (14.5995, 120.9842)

        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
        search_query = st.text_input("SEARCH TAGS", placeholder="Search parameters...").lower()
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
        
        for cat_name, node_items in poi_config.items():
            matched = [item for item in node_items if search_query in item[0].lower()]
            if matched:
                with st.expander(cat_name, expanded=(len(search_query) > 0)):
                    for label, key_tag, val_tag in matched:
                        if st.checkbox(label, key=f"chk_{cat_name}_{label}"):
                            selected_tuples.append((label, key_tag, val_tag))

        if scan_triggered:
            if not selected_tuples:
                st.session_state.sidebar_error_msg = "Select ≥ 1 layer."
                st.rerun()
            else:
                st.session_state.sidebar_error_msg = None
                st.session_state.scan_active_loading = True
                st.rerun()

        # Dynamic Execution Pipeline Block triggered cleanly post rerun state tracking
        if st.session_state.scan_active_loading and selected_tuples:
            records = run_spatial_layer_scan(lat_coord, lon_coord, radius_val, selected_tuples)
            st.session_state.scanned_records = records
            st.session_state.geo_coords = f"{lat_coord}, {lon_coord}"
            st.session_state.last_scan_lat = lat_coord
            st.session_state.last_scan_lon = lon_coord
            st.session_state.scan_active_loading = False
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("CLEAR ALL", type="primary", key="clear_btn"):
            st.session_state.scanned_records = []
            st.session_state.layer_meta = {}
            st.session_state.legend_layers = []
            st.session_state.sidebar_error_msg = None
            st.session_state.scan_active_loading = False
            for key in list(st.session_state.keys()):
                if key.startswith("chk_"):
                    st.session_state[key] = False
            st.rerun()

        st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.08);'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        visible_only_records = [p for p in st.session_state.scanned_records if p.get('visible', True)]
        
        with col1:
            st.download_button("RADIUS", json.dumps(visible_only_records), "scan.json", "application/json", use_container_width=True)
        with col2:
            st.download_button("MARKERS", compile_features_kml(st.session_state.scanned_records), "POIs.kml", "application/vnd.google-earth.kml+xml", use_container_width=True)

        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
        with st.popover("IMPORT FILE", use_container_width=True):
            imported_file = st.file_uploader("Select JSON", type=["json"], label_visibility="collapsed")
            if imported_file is not None:
                if st.button("LOAD", type="secondary", use_container_width=True):
                    try:
                        data = json.load(imported_file)
                        st.session_state.scanned_records = data.get("scanned_records", data)
                        st.session_state.geo_coords = data.get("coords", st.session_state.geo_coords)
                        st.session_state.geo_radius = data.get("radius", st.session_state.geo_radius)
                        st.rerun()
                    except Exception:
                        st.error("Invalid File Format Input.")
                        
    return lat_coord, lon_coord, radius_val

import sys
import os

# FIXED: Force append the 'open-node' subfolder directory to the system path
# prior to executing any modular library imports to prevent container deployment failures.
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import streamlit as st
from config import initialize_session_states
from sidebar import render_unified_dashboard_sidebar
from map_view import render_leaflet_component_iframe

def main():
    # 1. Programmatically verify and populate default global session variables
    initialize_session_states()

    # 2. Mount sidebar component arrays, file configurations, and scan controllers
    lat, lon, radius = render_unified_dashboard_sidebar()

    # 3. Compile map frame interface and pull raw scanned results dynamically
    render_leaflet_component_iframe(
        lat=lat, 
        lon=lon, 
        radius=radius, 
        pts_active=st.session_state.scanned_records
    )

if __name__ == "__main__":
    main()

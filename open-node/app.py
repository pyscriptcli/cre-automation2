import os
import sys

# Core Environment Enforcer Block: Overcomes Streamlit Cloud folder mounting quirks
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import streamlit as st
from config import initialize_session_states
from sidebar import render_unified_dashboard_sidebar
from map_view import render_leaflet_component_iframe

def main():
    initialize_session_states()
    lat, lon, radius = render_unified_dashboard_sidebar()
    render_leaflet_component_iframe(
        lat=lat, 
        lon=lon, 
        radius=radius, 
        pts_active=st.session_state.scanned_records
    )

if __name__ == "__main__":
    main()

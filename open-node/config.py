import streamlit as st
import json
import os
from pathlib import Path

DEFAULT_COORDS = "14.5995, 120.9842"
DEFAULT_RADIUS = 1000

DEFAULTS = {
    "geo_coords": DEFAULT_COORDS,
    "geo_radius": DEFAULT_RADIUS,
    "scanned_records": [],
    "last_scan_lat": 14.5995,
    "last_scan_lon": 120.9842,
    "layer_meta": {},
    "scan_active_loading": False,
    "legend_layers": [],
    "sidebar_error_msg": None,
    "target_config": {"size": 24, "color": "#003366", "style": "star"},
    "radius_config": {"color": "#003366", "fill_opacity": 0.08, "weight": 1.5},
    "global_marker_style": "dots",
    "global_marker_size": 12,
    "global_marker_color": "#003366"
}

def load_poi_configuration() -> dict:
    current_dir = Path(__file__).parent
    config_path = current_dir / "config.json"
    if not config_path.exists():
        return {"POI_CONFIG": {}}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"POI_CONFIG": {}}

def initialize_session_states():
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)

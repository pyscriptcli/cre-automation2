"""
sidebar.py – Google My Maps-style floating sidebar panel.
All scan logic, POI selection, and workspace actions live here.
"""

import re
import json
import streamlit as st
from config import POI_CONFIG, ADVANCED_CONFIG
from scraper import fetch_pois
from kml_export import compile_features_kml


# ─────────────────────────────────────────────────────────────────────────────
# COORDINATE PARSER
# ─────────────────────────────────────────────────────────────────────────────
_COORD_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$")


def parse_coords(text: str) -> tuple[float, float] | None:
    m = _COORD_RE.match(text)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR RENDER
# ─────────────────────────────────────────────────────────────────────────────
def render_unified_dashboard_sidebar() -> tuple[float, float, int]:
    """
    Render the full sidebar. Returns (lat, lon, radius) for the map renderer.
    """
    with st.sidebar:
        # ── Header ────────────────────────────────────────────────────────────
        st.markdown(
            '<div class="brand-title">🗺 Open Node</div>',
            unsafe_allow_html=True,
        )

        # ── Location + Radius inputs ──────────────────────────────────────────
        coords_input = st.text_input(
            "Coordinates",
            value=st.session_state.geo_coords,
            placeholder="lat, lon",
            key="coords_text_input",
        )
        radius_val = st.number_input(
            "Radius (meters)",
            min_value=100,
            max_value=50_000,
            value=st.session_state.geo_radius,
            step=100,
            key="radius_number_input",
        )
        st.session_state.geo_radius = radius_val

        parsed = parse_coords(coords_input)
        if parsed:
            lat_coord, lon_coord = parsed
        else:
            fallback = parse_coords(st.session_state.geo_coords)
            lat_coord, lon_coord = fallback if fallback else (14.5995, 120.9842)

        # ── Persistent error banner ────────────────────────────────────────────
        if st.session_state.scan_error:
            st.error(st.session_state.scan_error)

        # ── Scan button ───────────────────────────────────────────────────────
        scan_clicked = st.button(
            "SCAN AREA",
            type="secondary",
            use_container_width=True,
            key="scan_btn",
        )

        # ── POI search filter ─────────────────────────────────────────────────
        search_q = st.text_input(
            "Search layers",
            placeholder="Filter POI types...",
            key="poi_search",
        ).lower().strip()

        # ── POI checkboxes ────────────────────────────────────────────────────
        selected_tags: list[str] = []

        def _render_category(cat_name: str, items: list[tuple], prefix: str):
            matched = [item for item in items if search_q in item[0].lower()]
            if not matched:
                return
            with st.expander(cat_name, expanded=bool(search_q)):
                for label, tag in matched:
                    key = f"chk_{prefix}_{cat_name}_{label}"
                    if st.checkbox(label, key=key):
                        selected_tags.append(tag)

        st.markdown(
            "<div style='font-size:10px;font-weight:600;color:#5f6368;padding:8px 0 4px;letter-spacing:0.5px;'>POI CATEGORIES</div>",
            unsafe_allow_html=True,
        )
        for cat, items in POI_CONFIG.items():
            _render_category(cat, items, "poi")

        st.markdown(
            "<div style='font-size:10px;font-weight:600;color:#5f6368;padding:8px 0 4px;letter-spacing:0.5px;'>ADVANCED</div>",
            unsafe_allow_html=True,
        )
        for cat, items in ADVANCED_CONFIG.items():
            _render_category(cat, items, "adv")

        # ── Scan logic ────────────────────────────────────────────────────────
        if scan_clicked:
            if not selected_tags:
                st.session_state.scan_error = "Select at least one layer before scanning."
            else:
                st.session_state.scan_error = None
                st.session_state.scan_active_loading = True

                records, error = fetch_pois(lat_coord, lon_coord, radius_val, selected_tags)

                st.session_state.scan_active_loading = False

                if error and not records:
                    st.session_state.scan_error = f"Scan failed: {error}"
                else:
                    st.session_state.scan_error = None
                    st.session_state.scanned_records = records
                    st.session_state.geo_coords      = f"{lat_coord:.5f}, {lon_coord:.5f}"
                    st.session_state.last_scan_lat   = lat_coord
                    st.session_state.last_scan_lon   = lon_coord
                    # Reset layer meta so new layers pick fresh colours
                    st.session_state.layer_meta = {}
                st.rerun()

        # ── Workspace actions ─────────────────────────────────────────────────
        st.markdown("<hr style='margin:12px 0;border:0;border-top:1px solid #e8eaed;'>", unsafe_allow_html=True)

        visible_records = [p for p in st.session_state.scanned_records if p.get("visible", True)]

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "JSON",
                data=json.dumps(visible_records, ensure_ascii=True),
                file_name="scan.json",
                mime="application/json",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                "KML",
                data=compile_features_kml(st.session_state.scanned_records),
                file_name="POIs.kml",
                mime="application/vnd.google-earth.kml+xml",
                use_container_width=True,
            )

        with st.popover("IMPORT JSON", use_container_width=True):
            uploaded = st.file_uploader("Select JSON", type=["json"], label_visibility="collapsed")
            if uploaded is not None:
                if st.button("Load file", type="secondary", use_container_width=True):
                    try:
                        data = json.load(uploaded)
                        # Support both bare list and structured export
                        if isinstance(data, list):
                            st.session_state.scanned_records = data
                        elif isinstance(data, dict):
                            st.session_state.scanned_records = data.get("scanned_records", data)
                            if "coords" in data:
                                st.session_state.geo_coords = data["coords"]
                            if "radius" in data:
                                st.session_state.geo_radius = data["radius"]
                        st.session_state.layer_meta = {}
                        st.rerun()
                    except (ValueError, KeyError) as exc:
                        st.error(f"Invalid file: {exc}")

        if st.button("CLEAR ALL", type="primary", key="clear_btn", use_container_width=True):
            st.session_state.scanned_records = []
            st.session_state.layer_meta      = {}
            st.session_state.legend_layers   = []
            st.session_state.scan_error      = None
            st.session_state.scan_active_loading = False
            # Clear all checkbox states
            for k in list(st.session_state.keys()):
                if k.startswith("chk_"):
                    st.session_state[k] = False
            st.rerun()

    return lat_coord, lon_coord, radius_val

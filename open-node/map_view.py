import streamlit as st
import json
import html
from jinja2 import Environment, FileSystemLoader

def render_leaflet_component_iframe(lat: float, lon: float, radius: int, pts_active: list):
    # Enforce safe HTML asset validation constraints via structural pre-escaping blocks
    safe_pts = []
    for p in pts_active:
        safe_pts.append({
            "lat": float(p["lat"]),
            "lon": float(p["lon"]),
            "name": html.escape(p["name"]),
            "type": html.escape(p["type"]),
            "visible": bool(p.get("visible", True)),
            "uid": html.escape(str(p["uid"]))
        })

    unique_layers = list(set([p["type"] for p in safe_pts]))
    cat_palette = ["#003366", "#C9AB4C", "#1A5A8A", "#A8862E", "#3D7DA8", "#7A5C10", "#6A94B0", "#D4B85A", "#001F3F", "#E8D494"]
    
    for idx, layer in enumerate(unique_layers):
        if layer not in st.session_state.layer_meta:
            st.session_state.layer_meta[layer] = {
                "color": cat_palette[idx % len(cat_palette)],
                "style": st.session_state.global_marker_style,
                "size": st.session_state.global_marker_size
            }

    # Bind Jinja2 environment parameters safely
    env = Environment(loader=FileSystemLoader('.'))
    try:
        template = env.get_template('template.html')
    except Exception as e:
        st.error("Fatal: Visual asset deployment file matrix template.html was not found.")
        return

    # Pack the payload variables safely without risk of code injection
    html_payload = template.render(
        LAT=lat,
        LON=lon,
        RADIUS=radius,
        IS_STALE="true" if (lat != st.session_state.last_scan_lat or lon != st.session_state.last_scan_lon) else "false",
        SHOW_LOADING="true" if st.session_state.scan_active_loading else "false",
        GLOBAL_MARKER_SIZE=st.session_state.global_marker_size,
        GLOBAL_MARKER_COLOR=st.session_state.global_marker_color,
        TARGET_CONFIG_JSON=json.dumps(st.session_state.target_config, ensure_ascii=True),
        RADIUS_CONFIG_JSON=json.dumps(st.session_state.radius_config, ensure_ascii=True),
        LAYER_META_JSON=json.dumps(st.session_state.layer_meta, ensure_ascii=True),
        GEOJSON=json.dumps(safe_pts, ensure_ascii=True),
        LEGEND_LAYERS_JSON=json.dumps(st.session_state.legend_layers, ensure_ascii=True)
    )

    st.components.v1.html(html_payload, height=850, scrolling=False)
  

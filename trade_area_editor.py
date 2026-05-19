import streamlit as st
import json
import re

def render_editor_workspace():
    st.markdown("""
        <style>
            div.stButton > button { border-radius: 2px !important; letter-spacing: 1px; text-transform: uppercase; font-family: 'Montserrat', sans-serif !important; }
            .brand-title { font-family: 'Cormorant Garamond', serif !important; font-style: italic; color: #003366; font-size: 32px; text-align: center; font-weight: 600; margin-bottom: 5px; }
            .brand-subtitle { font-family: 'Montserrat', sans-serif !important; font-size: 9px; text-align: center; color: #888780; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 20px; }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown('<div class="brand-title">TRADE AREA</div>', unsafe_allow_html=True)
        st.markdown('<div class="brand-subtitle">Spatial Intelligence Engine</div>', unsafe_allow_html=True)
        
        # IMPROVED BICHROMATIC ROW SELECTOR
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("SCANNER", use_container_width=True, type="primary"):
                st.session_state.active_module = "SCANNER"
                st.rerun()
        with btn_col2:
            if st.button("EDITOR", use_container_width=True, type="secondary"):
                st.session_state.active_module = "EDITOR"
                st.rerun()
                
        st.markdown("<hr style='margin: 15px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.1);'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:10px; font-weight:600; color:#888780; text-transform:uppercase; text-align:center;'>Vector Editing Environment Active</div>", unsafe_allow_html=True)

    coords_val = st.session_state.get("geo_coords", "14.5995, 120.9842")
    radius_val = st.session_state.get("geo_radius", 1000)
    scanned_records = st.session_state.get("scanned_records", [])

    coord_match = re.match(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", coords_val)
    lat_coord, lon_coord = (float(coord_match.group(1)), float(coord_match.group(2))) if coord_match else (14.5995, 120.9842)

    render_lat = lat_coord
    render_lon = lon_coord

    for idx, record in enumerate(scanned_records):
        if "_uid" not in record: record["_uid"] = idx
        if "visible" not in record: record["visible"] = True
        if "style" not in record:
            record["style"] = {
                "color": "#003366",
                "icon_shape": "circle",
                "icon_size": 24,
                "icon_symbol": "location_on",
                "icon_opacity": 1.0,
                "fill_color": "#C9AB4C",
                "fill_opacity": 0.4,
                "weight": 2.0,
                "fill": True
            }

    geojson_str = json.dumps(scanned_records)

    editor_leaflet_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <link rel="stylesheet" href="https://unpkg.com/@geoman-io/leaflet-geoman-free@latest/dist/leaflet-geoman.css" />
        <script src="https://unpkg.com/@geoman-io/leaflet-geoman-free@latest/dist/leaflet-geoman.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            body, html { margin: 0; padding: 0; height: 100%; width: 100%; overflow: hidden; font-family: 'Montserrat', sans-serif; }
            #map { height: 100vh; width: 100%; z-index: 1; }
            
            #scan-results-panel { position: absolute; top: 15px; right: 15px; z-index: 1000; background: #ffffff; width: 280px; max-height: calc(50vh - 20px); border-radius: 4px; border: 1px solid rgba(0, 51, 102, 0.1); display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 20px rgba(0, 51, 102, 0.15); }
            .results-header { background: #003366; color: #ffffff; padding: 12px; font-size: 11px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; border-bottom: 2px solid #C9AB4C; letter-spacing: 1px; }
            .results-list { overflow-y: auto; flex-grow: 1; background: #ffffff; }
            .layer-category-block { border-bottom: 1px solid #f1f5f9; }
            .layer-category-header { background: #f8fafc; padding: 10px 12px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; user-select: none; }
            .layer-header-left { display: flex; align-items: center; gap: 8px; font-size: 10px; font-weight: 700; color: #003366; text-transform: uppercase;}
            
            .results-item { padding: 8px 12px; font-size: 10px; font-weight: 600; color: #475569; display: flex; justify-content: space-between; align-items: center; cursor: pointer; border-bottom: 1px solid #f8fafc; }
            .results-item:hover { background: #f1f5f9; color: #003366; }
            .visibility-toggle-icon { cursor: pointer; display: flex; align-items: center; color: #94a3b8; }
            .visibility-toggle-icon:hover { color: #003366; }
            .color-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; border: 1px solid rgba(0,0,0,0.15); }
            
            #feature-properties-panel { position: absolute; bottom: 15px; right: 15px; z-index: 1000; background: #ffffff; width: 280px; height: calc(50vh - 20px); border-radius: 4px; border: 1px solid rgba(0, 51, 102, 0.1); box-shadow: 0 -4px 20px rgba(0, 51, 102, 0.15); display: none; flex-direction: column; overflow: hidden; }
            .panel-header { background: #003366; color: #ffffff; padding: 12px; font-size: 11px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; border-bottom: 2px solid #C9AB4C; letter-spacing: 0.5px;}
            .panel-body { padding: 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
            .control-group { display: flex; flex-direction: column; gap: 4px; }
            .control-group label { font-size: 9px; font-weight: 700; color: #64748b; text-transform: uppercase; }
            .control-group input[type="text"], .control-group select, .control-group input[type="number"] { padding: 6px; font-size: 11px; font-family: 'Montserrat', sans-serif; color: #003366; border: 1px solid #e2e8f0; border-radius: 3px; outline: none; }
        </style>
    </head>
    <body>
        <div id="map"></div>
        
        <div id="scan-results-panel">
            <div class="results-header">
                <span>Active Workspace Grid</span>
                <span id="results-count" style="background:#C9AB4C; color:#003366; padding:2px 8px; border-radius:10px; font-size:9px;">0</span>
            </div>
            <div class="results-list" id="results-list-box"></div>
        </div>

        <div id="feature-properties-panel">
            <div class="panel-header">
                <span>Mutate Geometric Attributes</span>
                <span style="cursor:pointer;color:#C9AB4C;" onclick="dismissPropertiesPanel()">✖</span>
            </div>
            <div class="panel-body">
                <div class="control-group">
                    <label>Feature Title</label>
                    <input type="text" id="prop-name" onblur="commitActiveStyleModifications()">
                </div>
                <div class="control-group">
                    <label>Hex Color Target</label>
                    <input type="text" id="prop-color" onblur="commitActiveStyleModifications()">
                </div>
                <div class="control-group" id="group-icon-shape">
                    <label>Icon Canvas Shape</label>
                    <select id="prop-icon-shape" onchange="commitActiveStyleModifications()">
                        <option value="pin">PIN EMBLEM</option>
                        <option value="circle">RADIUS CIRCLE</option>
                    </select>
                </div>
                <div class="control-group" id="group-icon-size">
                    <label>Scale Bounds (PX)</label>
                    <input type="number" id="prop-icon-size" min="12" max="64" value="24" onchange="commitActiveStyleModifications()">
                </div>
            </div>
        </div>

        <script>
            const map = L.map('map', { zoomControl: true, attributionControl: false }).setView([__LAT__, __LON__], 14);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(map);

            map.pm.addControls({ position: 'topleft', drawMarker: true, drawPolygon: true, editMode: true, removalMode: true });
            L.circle([__LAT__, __LON__], { radius: __RADIUS__, color: "#003366", weight: 1.5, fillColor: "#003366", fillOpacity: 0.03 }).addTo(map);

            let pts = __GEOJSON__;
            let selectedFeatureReference = null;
            let selectedLayerReference = null;

            function renderVectorPinIcon(color, shape, size) {
                const baseSize = size || 24;
                let svg = shape === 'circle' 
                    ? `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${baseSize}" height="${baseSize}"><circle cx="12" cy="12" r="10" fill="${color}" stroke="#ffffff" stroke-width="2"/></svg>`
                    : `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${baseSize}" height="${baseSize}"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" fill="${color}" stroke="#ffffff" stroke-width="1.5"/></svg>`;
                return L.divIcon({ html: `<div style="display:flex;align-items:center;justify-content:center;">${svg}</div>`, className: '', iconSize: [baseSize, baseSize], iconAnchor: [baseSize/2, baseSize] });
            }

            function initializeFeaturesOnCanvas() {
                pts.forEach(p => {
                    let layerInstance = L.marker([p.lat, p.lon], { icon: renderVectorPinIcon(p.style.color, p.style.icon_shape, p.style.icon_size) });
                    p._layer = layerInstance;
                    layerInstance._uid = p._uid;
                    if (p.visible) { layerInstance.addTo(map); }

                    layerInstance.on('click', function(e) {
                        L.DomEvent.stopPropagation(e);
                        loadFeatureToPropertiesPanel(p, layerInstance);
                    });
                });
                generateAccordionWorkspaceList();
            }

            function loadFeatureToPropertiesPanel(feature, layer) {
                selectedFeatureReference = feature;
                selectedLayerReference = layer;
                document.getElementById('prop-name').value = feature.name;
                document.getElementById('prop-color').value = feature.style.color;
                document.getElementById('prop-icon-shape').value = feature.style.icon_shape;
                document.getElementById('prop-icon-size').value = feature.style.icon_size;
                document.getElementById('feature-properties-panel').style.display = 'flex';
            }

            function dismissPropertiesPanel() {
                document.getElementById('feature-properties-panel').style.display = 'none';
            }

            function commitActiveStyleModifications() {
                if (!selectedFeatureReference) return;
                const f = selectedFeatureReference;
                f.name = document.getElementById('prop-name').value;
                f.style.color = document.getElementById('prop-color').value;
                f.style.icon_shape = document.getElementById('prop-icon-shape').value;
                f.style.icon_size = parseInt(document.getElementById('prop-icon-size').value);

                if (selectedLayerReference.setIcon) {
                    selectedLayerReference.setIcon(renderVectorPinIcon(f.style.color, f.style.icon_shape, f.style.icon_size));
                }
                generateAccordionWorkspaceList();
            }

            function generateAccordionWorkspaceList() {
                const listBox = document.getElementById('results-list-box');
                document.getElementById('results-count').innerText = pts.length;
                
                const categorizedData = {};
                pts.forEach(p => {
                    const catKey = p.type || 'Custom Structural Layer';
                    if (!categorizedData[catKey]) categorizedData[catKey] = [];
                    categorizedData[catKey].push(p);
                });

                let listHtml = '';
                Object.keys(categorizedData).forEach(catName => {
                    listHtml += `
                        <div class="layer-category-block">
                            <div class="layer-category-header">
                                <div class="layer-header-left">
                                    <span class="color-dot" style="background:${categorizedData[catName][0].style.color};"></span>
                                    <span>${catName} (${categorizedData[catName].length})</span>
                                </div>
                            </div>
                            <div class="layer-category-items">
                    `;
                    categorizedData[catName].forEach(p => {
                        listHtml += `
                        <div class="results-item" onclick="map.flyTo([${p.lat}, ${p.lon}], 17);">
                            <div style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${p.name}</div>
                        </div>`;
                    });
                    listHtml += '</div></div>';
                });
                listBox.innerHTML = listHtml;
            }

            window.onload = () => { initializeFeaturesOnCanvas(); };
        </script>
    </body>
    </html>
    """

    leaflet_html_rendered = (editor_leaflet_template
                             .replace("__LAT__", str(render_lat))
                             .replace("__LON__", str(render_lon))
                             .replace("__RADIUS__", str(radius_val))
                             .replace("__GEOJSON__", geojson_str))

    st.components.v1.html(leaflet_html_rendered, height=850, scrolling=False)

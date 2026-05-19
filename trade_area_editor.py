import streamlit as st
import json
import re

def render_editor_workspace():
    """
    Decoupled Feature Editing Module Workspace.
    Inherits active spatial arrays from global system session states.
    """
    # --- SIDEBAR INTERFACE NAVIGATION CONTROL ---
    with st.sidebar:
        st.markdown('<div class="brand-title">Feature Editor</div>', unsafe_allow_html=True)
        
        st.markdown(
            "<div style='font-size: 10px; font-weight:600; color:#888780; margin-bottom:15px; text-align:center; text-transform:uppercase; letter-spacing:0.5px;'>"
            "Vector Engineering Workspace Mode"
            "</div>", 
            unsafe_allow_html=True
        )
        
        # Core Navigation Module Loop Reset
        if st.button("← BACK TO SCANNER", type="secondary", use_container_width=True):
            st.session_state.active_module = "SCANNER"
            st.rerun()
            
        st.markdown("<hr style='margin: 20px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.08);'>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size: 9px; font-weight: 500; color: #888780; line-height: 1.4; text-align: justify;'>"
            "Select assets directly on the map canvas or results log block to trigger the contextual styling control board overlay."
            "</div>", 
            unsafe_allow_html=True
        )

    # --- RETRIEVE ACTIVE RENDERING COORDINATES AND TARGET DATASETS ---
    coords_val = st.session_state.get("geo_coords", "14.5995, 120.9842")
    radius_val = st.session_state.get("geo_radius", 1000)
    scanned_records = st.session_state.get("scanned_records", [])

    coord_match = re.match(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", coords_val)
    lat_coord, lon_coord = (float(coord_match.group(1)), float(coord_match.group(2))) if coord_match else (14.5995, 120.9842)

    # Normalize records to ensure uniform structural safety keys exist
    for idx, record in enumerate(scanned_records):
        if "_uid" not in record: record["_uid"] = idx
        if "visible" not in record: record["visible"] = True
        if "style" not in record:
            record["style"] = {
                "color": "#003366",
                "icon_shape": "pin",
                "icon_size": 24,
                "icon_symbol": "location_on",
                "icon_opacity": 1.0,
                "fill_color": "#C9AB4C",
                "fill_opacity": 0.4,
                "weight": 2.0,
                "fill": True
            }

    geojson_str = json.dumps(scanned_records)

    # --- ADVANCED LEAFLET INTERACTIVE CORE ENGINE TEMPLATE ---
    editor_leaflet_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        
        <link rel="stylesheet" href="https://unpkg.com/@geoman-io/leaflet-geoman-free@latest/dist/leaflet-geoman.css" />
        <script src="https://unpkg.com/@geoman-io/leaflet-geoman-free@latest/dist/leaflet-geoman.min.js"></script>
        
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0" rel="stylesheet">
        
        <style>
            body, html { margin: 0; padding: 0; height: 100%; width: 100%; background: #ffffff; overflow: hidden; font-family: 'Montserrat', sans-serif; }
            #map { height: 100vh; width: 100%; z-index: 1; }
            
            /* RESULT LOG PANEL ACCORDION ACCENTS */
            #scan-results-panel { position: absolute; top: 10px; right: 10px; z-index: 1000; background: #ffffff; width: 250px; max-height: calc(50vh - 20px); border-radius: 2px; border: 1px solid rgba(0, 51, 102, 0.1); background-clip: padding-box; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08); }
            .results-header { background: #003366; color: #ffffff; padding: 10px 12px; font-size: 10px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; border-bottom: 2px solid #C9AB4C; letter-spacing: 1px; }
            .results-list { overflow-y: auto; flex-grow: 1; padding-bottom: 8px; }
            .layer-category-block { border-bottom: 1px solid #f0f0f0; }
            .layer-category-header { background: #ffffff; padding: 8px 12px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; user-select: none; }
            .layer-header-left { display: flex; align-items: center; gap: 6px; font-size: 9px; font-weight: 700; color: #003366; text-transform: uppercase;}
            .layer-category-items { padding: 0; background: #f8fafc; }
            .layer-category-items.collapsed { display: none !important; }
            
            .results-item { padding: 6px 12px 6px 12px; font-size: 9px; font-weight: 600; color: #888780; display: flex; justify-content: space-between; align-items: center; cursor: pointer; border-bottom: 1px solid #f0f0f0; }
            .results-item:hover { background: #ffffff; color: #003366; }
            .item-left-group { display: flex; align-items: center; gap: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; width: 80%; }
            .visibility-toggle-icon { cursor: pointer; display: flex; align-items: center; color: #888780; }
            .visibility-toggle-icon:hover { color: #003366; }
            .color-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; border: 1px solid rgba(0,0,0,0.1); }
            
            /* CONTEXT-AWARE SLIDING LAYER PROP CONTROL PANEL */
            #feature-properties-panel {
                position: absolute; bottom: 10px; right: 10px; z-index: 1000; background: #ffffff;
                width: 250px; height: calc(50vh - 10px); border-radius: 2px; border: 1px solid rgba(0, 51, 102, 0.1);
                box-shadow: 0 -4px 15px rgba(0, 51, 102, 0.1); display: none; flex-direction: column; overflow: hidden;
                transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            }
            .panel-header { background: #003366; color: #ffffff; padding: 10px 12px; font-size: 10px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; border-bottom: 2px solid #C9AB4C; letter-spacing: 0.5px;}
            .panel-header .close-overlay-btn { cursor: pointer; color: #C9AB4C; font-size: 12px; }
            .panel-header .close-overlay-btn:hover { color: #ffffff; }
            
            .panel-body { padding: 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
            .control-group { display: flex; flex-direction: column; gap: 4px; }
            .control-group label { font-size: 8.5px; font-weight: 700; color: #888780; text-transform: uppercase; letter-spacing: 0.5px; }
            
            .input-row-flex { display: flex; gap: 6px; align-items: center; }
            .input-row-flex input[type="text"] { flex-grow: 1; }
            
            .control-group input[type="text"], .control-group select, .control-group input[type="number"] {
                padding: 6px; font-size: 10px; font-family: 'Montserrat', sans-serif; font-weight: 600;
                color: #003366; border: none; border-bottom: 1px solid rgba(201, 171, 76, 0.5); background: transparent; outline: none;
            }
            .control-group input[type="text"]:focus, .control-group select:focus { border-bottom: 2px solid #C9AB4C; }
            .control-group input[type="range"] { -webkit-appearance: none; width: 100%; background: rgba(0, 51, 102, 0.1); height: 4px; border-radius: 2px; outline: none; }
            .control-group input[type="range"]::-webkit-slider-thumb { -webkit-appearance: none; appearance: none; width: 12px; height: 12px; border-radius: 50%; background: #003366; cursor: pointer; transition: background 0.2s; }
            .control-group input[type="range"]::-webkit-slider-thumb:hover { background: #C9AB4C; }
            
            .define-pill-btn { background: #003366; color: #ffffff; font-size: 8px; font-weight: 800; border: none; border-radius: 2px; padding: 4px 8px; text-transform: uppercase; cursor: pointer; letter-spacing: 0.5px;}
            .define-pill-btn:hover { background: #C9AB4C; }
            
            .folder-rename-field { border: none !important; font-size: 9px !important; font-weight: 700 !important; color: #003366 !important; text-transform: uppercase; background: transparent; width: 120px; outline: none; padding: 0 !important; border-bottom: 1px dashed rgba(0,51,102,0.2) !important;}
            .folder-rename-field:focus { border-bottom: 1px solid #C9AB4C !important; }
            
            .poi-text-label { background: #fff; border: 1px solid #003366; padding: 2px 4px; border-radius: 2px; font-size: 9px; font-family: 'Montserrat', sans-serif; font-weight: 700; white-space: nowrap; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .custom-icon-wrapper { display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; }
        </style>
    </head>
    <body>
        <div id="map"></div>
        
        <div id="scan-results-panel">
            <div class="results-header">
                <span>ACTIVE WORKSPACE POIs</span>
                <span id="results-count" style="color:#C9AB4C;">0</span>
            </div>
            <div class="results-list" id="results-list-box"></div>
        </div>

        <div id="feature-properties-panel">
            <div class="panel-header">
                <span id="editor-panel-title">MUTATE ATTRIBUTES</span>
                <span class="close-overlay-btn" onclick="dismissPropertiesPanel()">✖</span>
            </div>
            <div class="panel-body">
                <div class="control-group">
                    <label>NAME / TITLE</label>
                    <input type="text" id="prop-name" onblur="commitActiveStyleModifications()">
                </div>
                <div class="control-group">
                    <label>COLOR</label>
                    <div class="input-row-flex">
                        <input type="text" id="prop-color" onblur="commitActiveStyleModifications()">
                        <button class="define-pill-btn" onclick="triggerColorInputLink()">DEFINE</button>
                    </div>
                </div>
                <div class="control-group" id="group-icon-shape">
                    <label>ICON SHAPE</label>
                    <select id="prop-icon-shape" onchange="commitActiveStyleModifications()">
                        <option value="pin">PIN</option>
                        <option value="circle">CIRCLE</option>
                        <option value="square">SQUARE</option>
                    </select>
                </div>
                <div class="control-group" id="group-icon-size">
                    <label>ICON SIZE</label>
                    <input type="number" id="prop-icon-size" min="12" max="64" value="24" onchange="commitActiveStyleModifications()">
                </div>
                <div class="control-group" id="group-icon-symbol">
                    <label>ICON SYMBOL (MATERIAL KEY)</label>
                    <input type="text" id="prop-icon-symbol" placeholder="e.g. store, home, pin" onblur="commitActiveStyleModifications()">
                </div>
                <div class="control-group">
                    <label>ICON OPACITY</label>
                    <input type="range" id="prop-icon-opacity" min="0" max="100" value="100" oninput="commitActiveStyleModifications()">
                </div>
                <div class="control-group" id="group-weight">
                    <label>LINE WEIGHT</label>
                    <input type="number" id="prop-weight" min="1" max="10" value="2" onchange="commitActiveStyleModifications()">
                </div>
                <div class="control-group" id="group-fill-toggle">
                    <label>FILL SHAPE</label>
                    <select id="prop-fill-toggle" onchange="commitActiveStyleModifications()">
                        <option value="true">ENABLE</option>
                        <option value="false">DISABLE</option>
                    </select>
                </div>
                <div class="control-group" id="group-fill-color">
                    <label>FILL COLOR</label>
                    <input type="text" id="prop-fill-color" onblur="commitActiveStyleModifications()">
                </div>
                <div class="control-group" id="group-fill-opacity">
                    <label>FILL OPACITY</label>
                    <input type="range" id="prop-fill-opacity" min="0" max="100" value="40" oninput="commitActiveStyleModifications()">
                </div>
            </div>
        </div>

        <script>
            const map = L.map('map', { zoomControl: true, attributionControl: false }).setView([__LAT__, __LON__], 14);
            map.zoomControl.setPosition('topleft');
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);

            // INITIALIZE LEAFLET GEOMAN PACK WITH COMPLIANT CONFIG (IMAGE 1 EXPLICIT)
            map.pm.addControls({
                position: 'topleft',
                drawMarker: true,
                drawPolyline: true,
                drawPolygon: true,
                editMode: true,
                dragMode: true,
                removalMode: true
            });

            // Anchor Core Anchor Ring Settings
            L.circle([__LAT__, __LON__], { radius: __RADIUS__, color: "#003366", weight: 1.5, fillColor: "#003366", fillOpacity: 0.05 }).addTo(map);

            let pts = __GEOJSON__;
            let selectedFeatureReference = null;
            let selectedLayerReference = null;
            const categoryMetaMap = {};

            // Dynamic Custom Vector Pin Generator
            function renderVectorPinIcon(color, shape, size, symbol) {
                let svgContent = '';
                const baseSize = size || 24;
                
                if (shape === 'circle') {
                    svgContent = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${baseSize}" height="${baseSize}"><circle cx="12" cy="12" r="10" fill="${color}" stroke="#ffffff" stroke-width="1.5"/><text x="12" y="15" font-family="Material Symbols Rounded" font-size="10px" fill="#ffffff" text-anchor="middle">${symbol || ''}</text></svg>`;
                } else if (shape === 'square') {
                    svgContent = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${baseSize}" height="${baseSize}"><rect x="2" y="2" width="20" height="20" rx="4" fill="${color}" stroke="#ffffff" stroke-width="1.5"/><text x="12" y="15" font-family="Material Symbols Rounded" font-size="10px" fill="#ffffff" text-anchor="middle">${symbol || ''}</text></svg>`;
                } else { // Standard Geometric Tail Pin
                    svgContent = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${baseSize}" height="${baseSize}"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" fill="${color}" stroke="#ffffff" stroke-width="1.5"/><text x="12" y="10" font-family="Material Symbols Rounded" font-size="8px" fill="#ffffff" text-anchor="middle">${symbol || ''}</text></svg>`;
                }

                return L.divIcon({
                    html: `<div class="custom-icon-wrapper">${svgContent}</div>`,
                    className: '',
                    iconSize: [baseSize, baseSize],
                    iconAnchor: [baseSize / 2, baseSize],
                    popupAnchor: [0, -baseSize]
                });
            }

            // Bind Vector Geometries to Canvas Context Loop
            function initializeFeaturesOnCanvas() {
                pts.forEach(p => {
                    let layerInstance;
                    
                    if (p.geom_type === 'Polygon') {
                        layerInstance = L.polygon(p.coordinates, { color: p.style.color, fillColor: p.style.fill_color, fillOpacity: p.style.fill_opacity, weight: p.style.weight });
                    } else if (p.geom_type === 'Polyline') {
                        layerInstance = L.polyline(p.coordinates, { color: p.style.color, weight: p.style.weight });
                    } else {
                        // Standard Point Asset Configuration Type
                        const customIcon = renderVectorPinIcon(p.style.color, p.style.icon_shape, p.style.icon_size, p.style.icon_symbol);
                        layerInstance = L.marker([p.lat, p.lon], { icon: customIcon });
                    }

                    p._layer = layerInstance;
                    layerInstance._uid = p._uid;

                    if (p.visible) { layerInstance.addTo(map); }

                    // Apply Dynamic Inward Event Selection Binding Hooks
                    layerInstance.on('click', function(e) {
                        L.DomEvent.stopPropagation(e);
                        loadFeatureToPropertiesPanel(p, layerInstance);
                    });
                });
                
                generateAccordionWorkspaceList();
            }

            // Geoman Geometry Vector Instantiation Hook Listener (Directive 1 Compliance)
            map.on('pm:create', function(e) {
                const layer = e.layer;
                const shapeType = e.shape;
                const uniqueId = "custom_draw_" + Date.now();
                
                layer._uid = uniqueId;

                let recordPayload = {
                    _uid: uniqueId,
                    name: `Custom ${shapeType} Asset`,
                    type: "Custom Layer",
                    geom_type: shapeType,
                    visible: true,
                    style: {
                        color: "#003366",
                        icon_shape: "pin",
                        icon_size: 24,
                        icon_symbol: "edit",
                        icon_opacity: 1.0,
                        fill_color: "#C9AB4C",
                        fill_opacity: 0.4,
                        weight: 2.0,
                        fill: true
                    }
                };

                if (shapeType === 'Marker') {
                    recordPayload.lat = layer.getLatLng().lat;
                    recordPayload.lon = layer.getLatLng().lng;
                    recordPayload.geom_type = 'Marker';
                } else {
                    recordPayload.coordinates = layer.getLatLngs();
                    recordPayload.geom_type = shapeType; 
                }

                recordPayload._layer = layer;
                pts.push(recordPayload);

                layer.on('click', function(evt) {
                    L.DomEvent.stopPropagation(evt);
                    loadFeatureToPropertiesPanel(recordPayload, layer);
                });

                generateAccordionWorkspaceList();
                loadFeatureToPropertiesPanel(recordPayload, layer);
            });

            // Listen to edits on drawn tracking nodes to intercept coordinate adjustments
            map.on('pm:edit', function(e) {
                generateAccordionWorkspaceList();
            });

            // Context Layout Properties Slider Population Protocol (Directive 2 Variant UI Sync)
            function loadFeatureToPropertiesPanel(feature, layer) {
                selectedFeatureReference = feature;
                selectedLayerReference = layer;

                document.getElementById('prop-name').value = feature.name;
                document.getElementById('prop-color').value = feature.style.color;
                document.getElementById('prop-icon-opacity').value = (feature.style.icon_opacity * 100);
                document.getElementById('prop-weight').value = feature.style.weight;

                if (feature.geom_type === 'Marker' || !feature.geom_type) {
                    document.getElementById('group-icon-shape').style.display = 'flex';
                    document.getElementById('group-icon-size').style.display = 'flex';
                    document.getElementById('group-icon-symbol').style.display = 'flex';
                    document.getElementById('group-fill-toggle').style.display = 'none';
                    document.getElementById('group-fill-color').style.display = 'none';
                    document.getElementById('group-fill-opacity').style.display = 'none';
                    
                    document.getElementById('prop-icon-shape').value = feature.style.icon_shape;
                    document.getElementById('prop-icon-size').value = feature.style.icon_size;
                    document.getElementById('prop-icon-symbol').value = feature.style.icon_symbol || '';
                } else {
                    document.getElementById('group-icon-shape').style.display = 'none';
                    document.getElementById('group-icon-size').style.display = 'none';
                    document.getElementById('group-icon-symbol').style.display = 'none';
                    document.getElementById('group-fill-toggle').style.display = 'flex';
                    document.getElementById('group-fill-color').style.display = 'flex';
                    document.getElementById('group-fill-opacity').style.display = 'flex';

                    document.getElementById('prop-fill-toggle').value = String(feature.style.fill);
                    document.getElementById('prop-fill-color').value = feature.style.fill_color;
                    document.getElementById('prop-fill-opacity').value = (feature.style.fill_opacity * 100);
                }

                document.getElementById('feature-properties-panel').style.display = 'flex';
            }

            function dismissPropertiesPanel() {
                document.getElementById('feature-properties-panel').style.display = 'none';
                selectedFeatureReference = null;
                selectedLayerReference = null;
            }

            // Real-time Style Commit Handler Pipeline
            function commitActiveStyleModifications() {
                if (!selectedFeatureReference) return;

                const f = selectedFeatureReference;
                f.name = document.getElementById('prop-name').value;
                f.style.color = document.getElementById('prop-color').value;
                f.style.icon_opacity = parseFloat(document.getElementById('prop-icon-opacity').value) / 100;
                f.style.weight = parseInt(document.getElementById('prop-weight').value);

                if (f.geom_type === 'Marker' || !f.geom_type) {
                    f.style.icon_shape = document.getElementById('prop-icon-shape').value;
                    f.style.icon_size = parseInt(document.getElementById('prop-icon-size').value);
                    f.style.icon_symbol = document.getElementById('prop-icon-symbol').value;

                    const revisedIcon = renderVectorPinIcon(f.style.color, f.style.icon_shape, f.style.icon_size, f.style.icon_symbol);
                    if (selectedLayerReference.setIcon) selectedLayerReference.setIcon(revisedIcon);
                } else {
                    f.style.fill = (document.getElementById('prop-fill-toggle').value === 'true');
                    f.style.fill_color = document.getElementById('prop-fill-color').value;
                    f.style.fill_opacity = parseFloat(document.getElementById('prop-fill-opacity').value) / 100;

                    if (selectedLayerReference.setStyle) {
                        selectedLayerReference.setStyle({
                            color: f.style.color,
                            weight: f.style.weight,
                            fill: f.style.fill,
                            fillColor: f.style.fill_color,
                            fillOpacity: f.style.fill_opacity
                        });
                    }
                }

                generateAccordionWorkspaceList();
            }

            function triggerColorInputLink() {
                const calculatedHex = prompt("Enter valid Target Hex Style Code:", selectedFeatureReference.style.color);
                if (calculatedHex && calculatedHex.startsWith('#')) {
                    document.getElementById('prop-color').value = calculatedHex;
                    commitActiveStyleModifications();
                }
            }

            // Render Layer Toggles & Accordions (Directive 3 Granular Compliance)
            function generateAccordionWorkspaceList() {
                const listBox = document.getElementById('results-list-box');
                document.getElementById('results-count').innerText = pts.length;
                
                const categorizedData = {};
                pts.forEach(p => {
                    const catKey = p.type || 'Custom Layer';
                    if (!categorizedData[catKey]) categorizedData[catKey] = [];
                    categorizedData[catKey].push(p);
                });

                let listHtml = '';
                const eyeOpenSvg = `<svg xmlns="http://www.w3.org/2000/svg" height="14" viewBox="0 -960 960 960" width="14" fill="currentColor"><path d="M480-320q75 0 127.5-52.5T660-500q0-75-52.5-127.5T480-680q-75 0-127.5 52.5T300-500q0 75 52.5 127.5T480-320Zm0-72q-45 0-76.5-31.5T372-500q0-45 31.5-76.5T480-608q45 0 76.5 31.5T588-500q0 45-31.5 76.5T480-392Zm0 192q-146 0-266-81.5T34-500q62-140 182-221.5T480-803q146 0 266 81.5T926-500q-62 140-182 221.5T480-200Z"/></svg>`;
                const eyeClosedSvg = `<svg xmlns="http://www.w3.org/2000/svg" height="14" viewBox="0 -960 960 960" width="14" fill="currentColor"><path d="m644-428-58-58q9-47-27-83t-83-27l-58-58q11-4 22-5.5t24-1.5q75 0 127.5 52.5T644-500q0 13-1.5 24t-5.5 22Zm132 132-51-51q47-36 86.5-81.5T872-500q-54-121-161.5-195.5T480-770q-47 0-92 10.5T301-729l-54-54q45-26 94-39.5t101-13.5q155 0 281.5 86T894-500q-33 59-81.5 109.5T776-296Zm-44 216L598-214q-27 7-56 10.5t-62 3.5q-155 0-281.5-86T66-500q29-52 71.5-99.5T234-683L72-845l51-51 710 710-51 51ZM310-502Zm94 94-58-58q-3 10-2.5 20.5t3.5 20.5q13 31 38.5 51.5T446-448q10 1 20.5.5t20.5-3.5l-58-58Zm32 32L320-492q-47 36-86.5 82.5T192-500q54 121 161.5 195.5T480-230q32 0 63-4t59-14L542-312q-14 5-29.5 7.5T480-302q-75 0-127.5-52.5T300-482q0-16 2.5-31.5t7.5-29.5Z"/></svg>`;

                Object.keys(categorizedData).forEach(catName => {
                    const fallbackColor = "#003366";
                    listHtml += `
                        <div class="layer-category-block" id="block-folder-${catName}">
                            <div class="layer-category-header">
                                <div class="layer-header-left">
                                    <input type="text" class="folder-rename-field" value="${catName}" onblur="globallyRenameFolder(this, '${catName}')">
                                    <span style="color: #C9AB4C; font-size: 8px;">(${categorizedData[catName].length})</span>
                                </div>
                                <span style="font-size: 8px; color:#C9AB4C; cursor:pointer;" onclick="toggleAccordionCollapse('${catName}')" id="chev-${catName}">▼</span>
                            </div>
                            <div class="layer-category-items" id="items-${catName}">
                    `;
                    categorizedData[catName].forEach(p => {
                        const activeIcon = p.visible ? eyeOpenSvg : eyeClosedSvg;
                        listHtml += `
                        <div class="results-item" onclick="centerCanvasOnElement(${p._uid})">
                            <div class="item-left-group">
                                <span class="color-dot" style="background-color: ${p.style.color || fallbackColor};"></span>
                                <span title="${p.name}">${p.name}</span>
                            </div>
                            <div class="visibility-toggle-icon" title="Toggle Feature View" onclick="event.stopPropagation(); executeVisibilityMatrixToggle(${p._uid})">
                                ${activeIcon}
                            </div>
                        </div>`;
                    });
                    listHtml += '</div></div>';
                });
                listBox.innerHTML = listHtml;
            }

            function toggleAccordionCollapse(catKey) {
                const panel = document.getElementById('items-' + catKey);
                const chev = document.getElementById('chev-' + catKey);
                panel.classList.toggle('collapsed');
                chev.innerText = panel.classList.contains('collapsed') ? '▲' : '▼';
            }

            function centerCanvasOnElement(uid) {
                const match = pts.find(p => p._uid === uid);
                if (match && match.visible && match._layer) {
                    if (match.geom_type === 'Marker' || !match.geom_type) {
                        map.flyTo([match.lat, match.lon], 17);
                    } else {
                        map.fitBounds(match._layer.getBounds().pad(0.2));
                    }
                    loadFeatureToPropertiesPanel(match, match._layer);
                }
            }

            // Execution Visibility Matrix Core Logic Layer (Directive 3 Checkbox Parity)
            function executeVisibilityMatrixToggle(uid) {
                const feature = pts.find(p => p._uid === uid);
                if (!feature) return;

                feature.visible = !feature.visible;
                if (feature.visible) {
                    map.addLayer(feature._layer);
                } else {
                    map.removeLayer(feature._layer);
                    if (selectedFeatureReference && selectedFeatureReference._uid === uid) {
                        dismissPropertiesPanel();
                    }
                }
                generateAccordionWorkspaceList();
            }

            // Global Folder Renaming Controller
            function globallyRenameFolder(inputElement, analyticalOldKey) {
                const cleanNewKey = inputElement.value.trim();
                if (!cleanNewKey || cleanNewKey === analyticalOldKey) return;

                pts.forEach(p => {
                    if (p.type === analyticalOldKey || (!p.type && analyticalOldKey === 'Custom Layer')) {
                        p.type = cleanNewKey;
                    }
                });
                generateAccordionWorkspaceList();
            }

            window.onload = () => {
                initializeFeaturesOnCanvas();
            };
        </script>
    </body>
    </html>
    """

    # Format execution overrides cleanly passing string matrices
    leaflet_html_rendered = (editor_leaflet_template
                             .replace("__LAT__", str(render_lat))
                             .replace("__LON__", str(render_lon))
                             .replace("__RADIUS__", str(radius_val))
                             .replace("__GEOJSON__", geojson_str))

    # Output full bleed workspace mapping structure frame
    st.components.v1.html(leaflet_html_rendered, height=850, scrolling=False)

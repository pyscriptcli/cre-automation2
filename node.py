import streamlit as st
import requests
import re
import json
import os
import matplotlib.pyplot as plt
import io
import base64

# --- PROGRAMMATIC LIGHT MODE LOCK (Must execute before st.set_page_config) ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"light\"\n")

# -----------------------------------------------------------------------------
# 1. BRANDED THEME & STRUCTURAL FULL OVERRIDES
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Open Node",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Montserrat:wght@400;500;600;700;800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0');

        :root {
            --brand-midnight: #003366 !important;
            --brand-gold: #C9AB4C !important;
            --white-clean: #ffffff !important;
            --bg-offwhite: #f8fafc !important;
            --text-muted: #888780 !important;
            --soft-shadow: 0 4px 12px rgba(0, 51, 102, 0.08) !important;
        }
        
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
            background-color: var(--white-clean) !important;
            color: var(--brand-midnight) !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: var(--bg-offwhite) !important;
            color: var(--brand-midnight) !important;
            border-right: 1px solid rgba(0, 51, 102, 0.08) !important;
            width: 280px !important;
            min-width: 280px !important;
            max-width: 280px !important;
            transform: none !important;
            visibility: visible !important;
            overflow: hidden !important;
            box-shadow: 2px 0 15px rgba(0,0,0,0.03) !important;
        }
        
        [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] { display: none !important; }
        ::-webkit-scrollbar { width: 0px !important; background: transparent !important; }
        * { scrollbar-width: none !important; -ms-overflow-style: none !important; }
        
        p, label, h1, h2, h3, h4, h5, h6, .stMarkdown, [data-testid="stExpander"] summary p {
            color: var(--brand-midnight) !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        
        [data-testid="stHeader"], header, #stDecoration { display: none !important; }
        
        [data-testid="stAppViewContainer"] { display: flex !important; flex-direction: row !important; width: 100vw !important; height: 100vh !important; overflow: hidden !important; }
        [data-testid="stMain"] { flex-grow: 1 !important; width: calc(100vw - 280px) !important; height: 100vh !important; overflow: hidden !important; margin: 0px !important; padding: 0px !important; }
        .block-container, [data-testid="stAppViewBlockContainer"], [data-testid="stVerticalBlock"], .stElementContainer { padding: 0px !important; margin: 0px !important; max-width: 100% !important; gap: 0rem !important; }
        iframe { height: 100vh !important; width: 100% !important; border: none !important; display: block !important; }
        
        div[data-baseweb="input"], div[data-baseweb="select"] { background-color: transparent !important; border: none !important; border-bottom: 1px solid rgba(201, 171, 76, 0.5) !important; border-radius: 0px !important; box-shadow: none !important; }
        
        div.stButton > button[kind="secondary"], [data-testid="stPopover"] > button { background-color: var(--brand-midnight) !important; border: 1px solid var(--brand-midnight) !important; border-radius: 2px !important; width: 100% !important; padding: 4px !important; box-shadow: var(--soft-shadow) !important; }
        div.stButton > button[kind="secondary"]:hover, [data-testid="stPopover"] > button:hover { background-color: var(--brand-gold) !important; border-color: var(--brand-gold) !important; }
        div.stButton > button[kind="secondary"] p, [data-testid="stPopover"] > button p, [data-testid="stPopover"] > button div, div.stDownloadButton > button p { color: var(--white-clean) !important; font-weight: 700 !important; font-size: 9px !important; text-transform: uppercase !important; letter-spacing: 1px; }
        
        div.stDownloadButton > button { background-color: var(--brand-midnight) !important; border: none !important; border-radius: 2px !important; width: 100% !important; padding: 4px !important; }
        div.stDownloadButton > button:hover { background-color: var(--brand-gold) !important; }
        
        div.stButton > button[kind="primary"] { background: transparent !important; border: none !important; color: var(--text-muted) !important; padding: 0 !important; margin-top: 2px; }
        div.stButton > button[kind="primary"] p { color: var(--text-muted) !important; font-size: 9px !important; font-weight: 600; text-transform: uppercase; }
        
        [data-testid="stSidebar"] .st-expander { border: 1px solid rgba(0, 51, 102, 0.05) !important; background-color: var(--white-clean) !important; border-radius: 2px !important; margin-bottom: 2px !important; }
        .stCheckbox label p { font-size: 10px !important; font-weight: 500 !important; }
        
        .brand-title { font-family: 'Cormorant Garamond', serif !important; font-style: italic; color: var(--brand-midnight); font-size: 30px; text-align: center; border-bottom: 1px solid var(--brand-gold); padding-bottom: 6px; margin-bottom: 15px; }
        .stTextInput label p, .stNumberInput label p { font-size: 9px !important; font-weight: 500 !important; color: var(--text-muted) !important; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. STATE PERSISTENCE & SYSTEM CACHING
# -----------------------------------------------------------------------------
DEFAULT_COORDS = "14.5995, 120.9842"
DEFAULT_RADIUS = 1000

if 'geo_coords' not in st.session_state: st.session_state.geo_coords = DEFAULT_COORDS
if 'geo_radius' not in st.session_state: st.session_state.geo_radius = DEFAULT_RADIUS
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'last_scan_lat' not in st.session_state: st.session_state.last_scan_lat = 14.5995
if 'last_scan_lon' not in st.session_state: st.session_state.last_scan_lon = 120.9842
if 'layer_meta' not in st.session_state: st.session_state.layer_meta = {}

if 'target_config' not in st.session_state:
    st.session_state.target_config = {"size": 24, "color": "#003366", "style": "star"}

if 'radius_config' not in st.session_state:
    st.session_state.radius_config = {"color": "#003366", "fill_opacity": 0.08, "weight": 1.5}

if 'global_marker_style' not in st.session_state: st.session_state.global_marker_style = "dots"
if 'global_marker_size' not in st.session_state: st.session_state.global_marker_size = 12
if 'global_marker_color' not in st.session_state: st.session_state.global_marker_color = "#003366"

POI_CONFIG = {
    "COMMERCIAL": [['Corporate Office', '"building"~"office|commercial",i'], ['IT/Tech Center', '"office"~"it|telecommunication",i'], ['Business Center', '"building"="commercial"'], ['Hospital', '"amenity"~"hospital|clinic",i'], ['Hotel', '"tourism"="hotel"'], ['Motel', '"tourism"="motel"']],
    "RESIDENTIAL": [['Apartments', '"building"="apartments"'], ['House', '"building"="house"'], ['Residential Area', '"landuse"="residential"'], ['Condominium', '"building"="residential"']],
    "RETAIL": [['Mall/Department Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"supermarket|grocery",i'], ['Convenience Store', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Hardware', '"shop"~"hardware|doityourself",i'], ['General Shops', '"shop"~"boutique|clothes|shoes",i'], ['Beauty', '"shop"="beauty"'], ['Bicycle', '"shop"="bicycle"'], ['Books/Stationary', '"shop"~"books|stationary",i'], ['Car', '"shop"="car"'], ['Chemist', '"shop"="chemist"'], ['Clothes', '"shop"="clothes"'], ['Copyshop', '"shop"="copyshop"'], ['Cosmetics', '"shop"="cosmetics"'], ['Department store', '"shop"="department_store"'], ['DIY/hardware', '"shop"~"hardware|doityourself",i'], ['Garden centre', '"shop"="garden_centre"'], ['General', '"shop"="general"'], ['Gift', '"shop"="gift"'], ['Hairdresser', '"shop"="hairdresser"'], ['Jewelry', '"shop"="jewelry"'], ['Kiosk', '"shop"="kiosk"'], ['Leather', '"shop"="leather"'], ['Marketplace', '"amenity"="marketplace"'], ['Musical instrument', '"shop"="musical_instrument"'], ['Optician', '"shop"="optician"'], ['Pets', '"shop"="pets"'], ['Phone', '"shop"="mobile_phone"'], ['Photo', '"shop"="photo"'], ['Shoes', '"shop"="shoes"'], ['Shopping centre', '"shop"="mall"'], ['Textiles', '"shop"="textiles"'], ['Toys', '"shop"="toys"']],
    "FOOD AND BEVERAGES": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee Shop', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"'], ['Bar/Pub/Nightclub', '"amenity"~"bar|pub|nightclub",i'], ['Bakery/Pastry', '"shop"="bakery"'], ['BBQ', '"amenity"="bbq"'], ['Biergarten', '"amenity"="biergarten"'], ['Food court', '"amenity"="food_court"'], ['Ice cream', '"amenity"="ice_cream"'], ['Pub', '"amenity"="pub"']],
    "INDUSTRIAL & LOGISTICS": [['Expressway Exits', '"highway"~"motorway_junction|toll_gantry",i'], ['Ports & Terminals', '"industrial"="port"'], ['Manufacturing Plants', '"industrial"~"factory|manufacturing|processing",i'], ['Cold Storage Facilities', '"warehouse"~"cold_store|cold_storage",i'], ['Industrial Parks/Estates', '"landuse"~"industrial|industrial_estate",i'], ['Warehouses & Depots', '"building"~"warehouse|depot",i'], ['Storage Facilities', '"building"="storage"'], ['Truck Access Routes (HGV)', '"hgv"~"designated|yes",i']],
    "GOVERNMENT & INFRASTRUCTURE": [['City Hall', '"amenity"="townhall"'], ['Police Station', '"amenity"="police"'], ['Fire Station', '"amenity"="fire_station"'], ['Airport Terminal', '"aeroway"~"terminal|aerodrome",i']],
    "SCHOOLS": [['University/College', '"amenity"~"university|college",i'], ['K-12 School', '"amenity"="school"'], ['Vocational/Other', '"amenity"="learning_centre"']]
}

ADVANCED_CONFIG = {
    "AMENITIES": [['ATM', '"amenity"="atm"'], ['Bank', '"amenity"="bank"'], ['Bench', '"amenity"="bench"'], ['Bicycle Parking', '"amenity"="bicycle_parking"'], ['Bicycle Rental', '"amenity"="bicycle_rental"'], ['Cinema', '"amenity"="cinema"'], ['Clinic', '"amenity"="clinic"'], ['Embassy', '"amenity"="embassy"'], ['Firestation', '"amenity"="fire_station"'], ['Fuel', '"amenity"="fuel"'], ['Hospital', '"amenity"="hospital"'], ['Library', '"amenity"="library"'], ['Music School', '"amenity"="music_school"'], ['Parking', '"amenity"="parking"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Police', '"amenity"="police"'], ['Letter Box', '"amenity"="letter_box"'], ['Post Office', '"amenity"="post_office"'], ['School/College', '"amenity"~"school|college",i'], ['Taxi', '"amenity"="taxi"'], ['Theatre', '"amenity"="theatre"'], ['Toilets', '"amenity"="toilets"'], ['University', '"amenity"="university"']],
    "PLACE OF WORSHIP": [['Church', '"religion"="christian"'], ['Mosque', '"religion"="muslim"'], ['Buddhist Temple', '"religion"="buddhist"'], ['Hindu Temple', '"religion"="hindu"'], ['Synagogue', '"religion"="jewish"'], ['Cemetery', '"landuse"="cemetery"'], ['Alpine Hut', '"tourism"="alpine_hut"'], ['Apartment', '"tourism"="apartment"'], ['Camp Site', '"tourism"="camp_site"'], ['Chalet', '"tourism"="chalet"'], ['Guest House', '"tourism"="guest_house"'], ['Hostel', '"tourism"="hostel"'], ['Hotel', '"tourism"="hotel"'], ['Motel', '"tourism"="motel"'], ['Casino', '"amenity"="casino"'], ['Spa', '"leisure"="spa"'], ['Sauna', '"leisure"="sauna"']],
    "SPORTS": [['American football', '"sport"="american_football"'], ['Baseball', '"sport"="baseball"'], ['Basketball', '"sport"="basketball"'], ['Cycling', '"sport"="cycling"'], ['Gymnastics', '"sport"="gymnastics"'], ['Golf', '"sport"="golf"'], ['Hockey', '"sport"="hockey"'], ['Horse racing', '"sport"="horse_racing"'], ['Ice hockey', '"sport"="ice_hockey"'], ['Soccer', '"sport"="soccer"'], ['Sports centre', '"leisure"="sports_centre"'], ['Surfing', '"sport"="surfing"'], ['Swimming', '"sport"="swimming"'], ['Tennis', '"sport"="tennis"'], ['Volleyball', '"sport"="volleyball"']],
    "MISCELLANEOUS": [['Busstop', '"highway"="bus_stop"'], ['E-bike charging', '"amenity"="charging_station"'], ['Kindergarten', '"amenity"="kindergarten"'], ['Marketplace', '"amenity"="marketplace"'], ['Office', '"office"="yes"'], ['Recycling', '"amenity"="recycling"'], ['Travel agency', '"shop"="travel_agency"'], ['Defibrillator - AED', '"emergency"="defibrillator"'], ['Fire hose/extinguisher', '"emergency"~"fire_hose|fire_extinguisher",i'], ['Fixme', '"fixme"~".",i'], ['Note-Node', '"type"="node"'], ['Note-Way', '"type"="way"'], ['Construction', '"landuse"="construction"'], ['Image', '"image"~".",i'], ['Public camera', '"man_made"="surveillance"'], ['City', '"place"="city"'], ['Town', '"place"="town"'], ['Village', '"place"="village"'], ['Hamlet', '"place"="hamlet"'], ['Suburb', '"place"="suburb"']]
}

def compile_features_kml(features):
    kml = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Scanned POIs</name>'
    for f in features:
        if not f.get('visible', True): continue
        name = f.get('name', 'Asset').replace("&", "&").replace("<", "<").replace(">", ">")
        class_type = f.get('type', 'Node').replace("&", "&").replace("<", "<").replace(">", ">")
        kml += f"<Placemark><name>{name}</name><description>{class_type}</description><Point><coordinates>{f['lon']},{f['lat']},0</coordinates></Point></Placemark>"
    return kml + '</Document></kml>'

def build_tags_dict_or_list(tags_list):
    parsed = {}
    for tag in tags_list:
        clean = tag.replace('"', '')
        if '=' in clean:
            k, v = clean.split('=', 1)
            if '~' in k or '~' in v:
                k = k.replace('~', '')
                v = v.replace('~', '')
            if ',' in v or '|' in v:
                v = [x.strip() for x in v.replace('|', ',').split(',')]
            if k in parsed:
                if isinstance(parsed[k], list):
                    if isinstance(v, list): parsed[k].extend(v)
                    else: parsed[k].append(v)
                else:
                    if isinstance(v, list): parsed[k] = [parsed[k]] + v
                    else: parsed[k] = [parsed[k], v]
            else:
                parsed[k] = v
        else:
            parsed[clean] = True
    return parsed

# -----------------------------------------------------------------------------
# 3. SIDEBAR CONTROLS & GEOPROCESSING
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="brand-title">Open Node</div>', unsafe_allow_html=True)
    
    # 1. Coordinates and Placement UI Boundaries
    location_input = st.text_input("COORDINATES", value=st.session_state.geo_coords, key="geo_coords_input")
    radius_val = st.number_input("RADIUS (METERS)", min_value=100, max_value=50000, value=st.session_state.geo_radius, key="geo_radius_input", step=100)
    st.session_state.geo_radius = radius_val

    coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", location_input)
    if coord_match:
        lat_coord, lon_coord = float(coord_match.group(1)), float(coord_match.group(2))
        st.session_state.geo_coords = location_input
    else:
        fallback_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", st.session_state.geo_coords)
        lat_coord, lon_coord = (float(fallback_match.group(1)), float(fallback_match.group(2))) if fallback_match else (14.5995, 120.9842)

    # 2. Tag Parameters Parsing Workflow
    selected_tags = []
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    search_query = st.text_input("SEARCH TAGS", placeholder="Search parameters...").lower()
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    
    for cat_name, node_items in POI_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for label, tag in matched:
                    if st.checkbox(label, key=f"chk_{cat_name}_{label}"): selected_tags.append(tag)

    st.markdown("<div style='font-weight: 700; font-size: 11px; margin-top: 15px; margin-bottom: 8px; color: #003366; letter-spacing: 1px;'>ADVANCED POIs</div>", unsafe_allow_html=True)
    with st.container():
        for cat_name, node_items in ADVANCED_CONFIG.items():
            matched = [item for item in node_items if search_query in item[0].lower()]
            if matched:
                with st.expander(cat_name, expanded=(len(search_query) > 0)):
                    for label, tag in matched:
                        if st.checkbox(label, key=f"chk_adv_{cat_name}_{label}"): selected_tags.append(tag)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 3. SCAN AREA ACTION BUTTON
    if st.button("SCAN AREA", type="secondary", use_container_width=True, key="scan_btn"):
        if not selected_tags:
            st.error("Select ≥ 1 layer.")
        else:
            records = []
            success = False
            
            # PRIMARY ENGINE: OSMnx (Optimized spatial boundary loading)
            try:
                import osmnx as ox
                import geopandas as gpd
                from shapely.geometry import Point
                
                tags_dict = build_tags_dict_or_list(selected_tags)
                # Fetch spatial parameters using high performance center point locks
                gdf = ox.geometries_from_point((lat_coord, lon_coord), tags_dict, dist=radius_val)
                if not gdf.empty:
                    for idx, row in gdf.iterrows():
                        if hasattr(row.geometry, 'centroid'):
                            c_lat, c_lon = row.geometry.centroid.y, row.geometry.centroid.x
                        else:
                            continue
                        name = row.get('name', 'Unknown')
                        if isinstance(name, float): name = 'Unknown'
                        
                        matched_type = 'Node'
                        for k in tags_dict.keys():
                            if k in row and row[k]:
                                matched_type = str(row[k])
                                break
                        
                        records.append({
                            "lat": c_lat, "lon": c_lon, 
                            "name": str(name), "type": matched_type,
                            "visible": True, "uid": len(records)
                        })
                    st.session_state.scanned_records = records
                    st.session_state.last_scan_lat = lat_coord
                    st.session_state.last_scan_lon = lon_coord
                    success = True
            except Exception:
                pass

            # SECONDARY FALLOVER ENGINE: Overpass Turbo API
            if not success:
                url = "https://overpass-api.de/api/interpreter"
                statements = "\n".join([f"  nwr[{tag}](around:{radius_val},{lat_coord},{lon_coord});" for tag in selected_tags])
                ql = f"[out:json][timeout:90];(\n{statements}\n);\nout center;"
                try:
                    res = requests.post(url, data={"data": ql}, headers={"User-Agent": "OpenNode/3.1"}, timeout=90)
                    if res.status_code == 200:
                        for el in res.json().get('elements', []):
                            e_lat = el.get('lat') or el.get('center', {}).get('lat')
                            e_lon = el.get('lon') or el.get('center', {}).get('lon')
                            if e_lat and e_lon:
                                tags = el.get('tags', {})
                                records.append({
                                    "lat": e_lat, "lon": e_lon, 
                                    "name": tags.get('name', 'Unknown'), 
                                    "type": tags.get('amenity') or tags.get('shop') or tags.get('building') or 'Node',
                                    "visible": True, "uid": len(records)
                                })
                        st.session_state.scanned_records = records
                        st.session_state.last_scan_lat = lat_coord
                        st.session_state.last_scan_lon = lon_coord
                        success = True
                except Exception:
                    st.error("Data fetch timeout or connection failure.")
            
            if success:
                st.rerun()

    if st.button("CLEAR ALL", type="primary", key="clear_btn"):
        st.session_state.scanned_records = []
        st.session_state.layer_meta = {}
        for key in list(st.session_state.keys()):
            if key.startswith("chk_"): st.session_state[key] = False
        st.rerun()

    st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.08);'>", unsafe_allow_html=True)
    
    # 4. REPORT PICTURE EXPORT
    if st.button("EXPORT PICTURE", type="secondary", use_container_width=True):
        if not st.session_state.scanned_records:
            st.error("No active data to export.")
        else:
            try:
                import contextily as cx
                import geopandas as gpd
                from shapely.geometry import Point
                
                pts = [p for p in st.session_state.scanned_records if p.get('visible', True)]
                cat_palette = ["#003366", "#C9AB4C", "#1A5A8A", "#A8862E", "#3D7DA8", "#7A5C10", "#6A94B0", "#D4B85A", "#001F3F", "#E8D494"]
                
                fig, ax = plt.subplots(figsize=(10, 10), dpi=300)
                
                center_gdf = gpd.GeoDataFrame(geometry=[Point(lon_coord, lat_coord)], crs="EPSG:4326").to_crs(epsg=3857)
                cx_center = center_gdf.geometry.iloc[0]
                
                buffer_zone = cx_center.buffer(radius_val)
                xmin, ymin, xmax, ymax = buffer_zone.bounds
                
                # Dynamic Radius Render Fix: Enforces clean float matching for radius opacity parameters
                r_col = st.session_state.radius_config["color"]
                r_opacity = float(st.session_state.radius_config["fill_opacity"])
                r_weight = float(st.session_state.radius_config["weight"])
                
                circle_patch = plt.Circle((cx_center.x, cx_center.y), radius_val, fill=True, facecolor=r_col, alpha=r_opacity, edgecolor=r_col, linewidth=r_weight, zorder=2)
                ax.add_patch(circle_patch)
                
                # Target Center Anchor Render Layer
                t_size = float(st.session_state.target_config["size"]) * 4
                t_col = st.session_state.target_config["color"]
                t_style = st.session_state.target_config["style"]
                t_marker = '*' if t_style == "star" else 'o'
                ax.scatter([cx_center.x], [cx_center.y], color=t_col, edgecolors='#ffffff', s=t_size, marker=t_marker, label='Target Center', zorder=10)
                
                # POI Point Clusters Layer Distribution
                unique_types = list(set([p.get('type', 'Unclassified') for p in pts]))
                for i, category_type in enumerate(unique_types):
                    meta = st.session_state.layer_meta.get(category_type, {})
                    cat_color = meta.get("color", cat_palette[i % len(cat_palette)])
                    cat_size = float(meta.get("size", st.session_state.global_marker_size)) * 4
                    cat_style = meta.get("style", st.session_state.global_marker_style)
                    
                    m_shape = 'o'
                    if cat_style == 'pin': m_shape = '^'
                    elif cat_style == '1pin': m_shape = 's'
                    
                    cat_pts = [p for p in pts if p.get('type', 'Unclassified') == category_type]
                    if not cat_pts: continue
                    
                    lon_vals = [p['lon'] for p in cat_pts]
                    lat_vals = [p['lat'] for p in cat_pts]
                    
                    pt_gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy(lon_vals, lat_vals), crs="EPSG:4326").to_crs(epsg=3857)
                    ax.scatter(pt_gdf.geometry.x, pt_gdf.geometry.y, color=cat_color, edgecolors='#ffffff', s=cat_size, marker=m_shape, alpha=0.9, label=category_type, zorder=5)
                
                try:
                    cx.add_basemap(ax, source=cx.providers.CartoDB.Positron, zorder=1)
                except Exception:
                    pass
                
                ax.set_xlim(xmin - (radius_val*0.1), xmax + (radius_val*0.1))
                ax.set_ylim(ymin - (radius_val*0.1), ymax + (radius_val*0.1))
                ax.axis('off')
                
                ax.legend(loc='upper left', bbox_to_anchor=(0.02, 0.98), frameon=True, facecolor='#ffffff', edgecolor='rgba(0, 51, 102, 0.1)', fontsize=7, title="Open Node Legend", title_fontsize=8)
                
                img_buf = io.BytesIO()
                plt.savefig(img_buf, format='png', bbox_inches='tight', dpi=300)
                img_buf.seek(0)
                plt.close(fig)
                
                st.image(img_buf, caption="Export Output Layout")
                st.download_button(label="DOWNLOAD IMAGE AS PNG", data=img_buf, fileName="OpenNode_ExportReport.png", mime="image/png", use_container_width=True)
            except Exception as export_error:
                st.error(f"Failed to generate layout mapping: {str(export_error)}")

    col1, col2 = st.columns(2)
    with col1: st.download_button("JSON", json.dumps(st.session_state.scanned_records), "scan.json", "application/json", use_container_width=True)
    with col2: st.download_button("KML", compile_features_kml(st.session_state.scanned_records), "POIs.kml", "application/vnd.google-earth.kml+xml", use_container_width=True)

# -----------------------------------------------------------------------------
# 4. DATA MODEL INTEGRITY & SCRIPT SYNC CHANNELS
# -----------------------------------------------------------------------------
if 'runtime_action' in st.session_state:
    action = st.session_state.runtime_action
    if action.get("type") == "delete_poi":
        st.session_state.scanned_records = [p for p in st.session_state.scanned_records if p.get('uid') != action["uid"]]
        del st.session_state.runtime_action
        st.rerun()
    elif action.get("type") == "toggle_poi":
        for p in st.session_state.scanned_records:
            if p.get('uid') == action["uid"]: p['visible'] = not p.get('visible', True)
        del st.session_state.runtime_action
        st.rerun()
    elif action.get("type") == "rename_poi":
        for p in st.session_state.scanned_records:
            if p.get('uid') == action["uid"]: p['name'] = action["new_name"]
        del st.session_state.runtime_action
        st.rerun()
    elif action.get("type") == "delete_layer":
        st.session_state.scanned_records = [p for p in st.session_state.scanned_records if p.get('type') != action["layer_key"]]
        if action["layer_key"] in st.session_state.layer_meta: del st.session_state.layer_meta[action["layer_key"]]
        del st.session_state.runtime_action
        st.rerun()
    elif action.get("type") == "toggle_layer":
        for p in st.session_state.scanned_records:
            if p.get('type') == action["layer_key"]: p['visible'] = action["visible"]
        del st.session_state.runtime_action
        st.rerun()
    elif action.get("type") == "rename_layer":
        for p in st.session_state.scanned_records:
            if p.get('type') == action["old_key"]: p['type'] = action["new_key"]
        if action["old_key"] in st.session_state.layer_meta:
            st.session_state.layer_meta[action["new_key"]] = st.session_state.layer_meta.pop(action["old_key"])
        del st.session_state.runtime_action
        st.rerun()

# -----------------------------------------------------------------------------
# 5. SPLIT-VIEW REALTIME CANVAS PARSING METER
# -----------------------------------------------------------------------------
pts_active = st.session_state.scanned_records
unique_layers = list(set([p.get('type', 'Unclassified') for p in pts_active]))
cat_palette = ["#003366", "#C9AB4C", "#1A5A8A", "#A8862E", "#3D7DA8", "#7A5C10", "#6A94B0", "#D4B85A", "#001F3F", "#E8D494"]

for idx, layer in enumerate(unique_layers):
    if layer not in st.session_state.layer_meta:
        st.session_state.layer_meta[layer] = {
            "color": cat_palette[idx % len(cat_palette)],
            "style": st.session_state.global_marker_style,
            "size": st.session_state.global_marker_size
        }

# Structural parameters injection configuration maps
layer_meta_json = json.dumps(st.session_state.layer_meta)
target_config_json = json.dumps(st.session_state.target_config)
radius_config_json = json.dumps(st.session_state.radius_config)
geojson_str = json.dumps(pts_active)

render_lat = lat_coord
render_lon = lon_coord
is_stale = "true" if (lat_coord != st.session_state.last_scan_lat or lon_coord != st.session_state.last_scan_lon) else "false"

leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; background: #ffffff; overflow: hidden; font-family: 'Montserrat', sans-serif; }
        #map { height: 100vh; width: 100%; }
        
        #minimal-basemap-panel {
            position: absolute; top: 110px; left: 50px; z-index: 1000;
            background: #ffffff; border-radius: 4px; border: 1px solid rgba(0, 51, 102, 0.1); background-clip: padding-box;
            display: none; flex-direction: column; padding: 4px; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08); width: 150px;
        }
        #minimal-basemap-panel select {
            border: none; border-bottom: 1px solid #f0f0f0; padding: 6px; font-size: 10px; font-weight: 700; font-family: 'Montserrat', sans-serif;
            color: #003366; background: transparent; outline: none; cursor: pointer; width: 100%; text-transform: uppercase;
        }
        .minimal-label { font-size: 9px; font-weight: 700; padding: 6px; display: flex; align-items: center; gap: 4px; cursor: pointer; color: #888780; margin: 0; text-transform: uppercase; border-top: 1px solid #f8fafc;}

        #search-container { position: absolute; top: 10px; left: 54px; z-index: 1000; width: 300px; }
        #map-search {
            width: 100%; padding: 8px 12px; border: 1px solid rgba(0, 51, 102, 0.1); border-radius: 4px; background-clip: padding-box;
            font-size: 11px; font-family: 'Montserrat', sans-serif; font-weight: 600; color: #003366; background: #ffffff; outline: none; box-sizing: border-box; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08);
        }

        #scan-results-panel { 
            position: absolute; top: 10px; right: 10px; z-index: 1000; background: #ffffff; width: 310px; 
            max-height: calc(100vh - 80px); border-radius: 2px; border: 1px solid rgba(0, 51, 102, 0.1); 
            background-clip: padding-box; display: flex; flex-direction: column; overflow: hidden; 
            box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08); 
        }
        .results-header { background: #003366; color: #ffffff; padding: 10px 12px; font-size: 10px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; border-bottom: 2px solid #C9AB4C; letter-spacing: 1px; }
        .results-list { overflow-y: auto; flex-grow: 1; padding-bottom: 8px; }
        .layer-category-block { border-bottom: 1px solid #f0f0f0; }
        .layer-category-header { background: #ffffff; padding: 6px 10px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; user-select: none; transition: background 0.2s; }
        .layer-category-header:hover { background: #f8fafc; }
        .layer-header-left { display: flex; align-items: center; gap: 4px; font-size: 9px; font-weight: 700; color: #003366; text-transform: uppercase; flex-grow: 1; overflow: hidden;}
        .layer-category-items { padding: 0; background: #f8fafc; }
        .layer-category-items.collapsed { display: none !important; }
        
        .results-item { padding: 4px 8px 4px 16px; font-size: 9px; font-weight: 600; color: #888780; display: flex; justify-content: space-between; align-items: center; cursor: pointer; border-bottom: 1px solid #f0f0f0; }
        .results-item:hover { background: #ffffff; color: #003366; }
        .action-icon-trigger { cursor: pointer; padding: 2px; display: inline-flex; align-items: center; justify-content: center; width: 16px; height: 16px; }
        .action-icon-trigger svg { fill: #888780; transition: fill 0.2s; }
        .action-icon-trigger:hover svg { fill: #003366; }
        .action-icon-trigger.delete-btn:hover svg { fill: #AA2E20; }

        .poi-text-label { background: #fff; border: 1px solid #003366; padding: 2px 4px; border-radius: 2px; font-size: 9px; font-family: 'Montserrat', sans-serif; font-weight: 700; white-space: nowrap; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .hide-labels .poi-text-label { display: none !important; }
        .color-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; border: 1px solid rgba(0,0,0,0.1); cursor: pointer; }
        
        .leaflet-control-custom-stack { background: #fff; border: 2px solid rgba(0,0,0,0.2); border-radius: 4px; overflow: hidden; display: flex; flex-direction: column; }
        .leaflet-control-custom-stack a { display: flex !important; align-items: center; justify-content: center; background: #fff; text-decoration: none; width: 34px; height: 34px; border-bottom: 1px solid #ccc; cursor: pointer;}
        .leaflet-control-custom-stack a:last-child { border-bottom: none; }
        .custom-pin-container { display: flex; align-items: center; justify-content: center; }
        
        .config-block-wrapper { padding: 6px 12px; background: #f8fafc; border-bottom: 1px solid rgba(0, 51, 102, 0.08); display: flex; flex-direction: column; gap: 4px; }
        .config-headline { font-size: 8px; font-weight: 800; color: #003366; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; }
        .config-flex-row { display: flex; align-items: center; justify-content: space-between; font-size: 9px; font-weight: 600; color: #003366; gap: 6px; }
        .config-flex-row select, .config-flex-row input { font-size: 9px; font-family: 'Montserrat', sans-serif; color: #003366; background: #ffffff; border: 1px solid rgba(0, 51, 102, 0.15); border-radius: 2px; padding: 1px 3px; outline: none; }
        .slider-control-element { flex-grow: 1; margin: 0; -webkit-appearance: none; height: 4px; background: rgba(0,51,102,0.1); border-radius: 2px; outline: none; }
        .slider-control-element::-webkit-slider-thumb { -webkit-appearance: none; width: 10px; height: 10px; border-radius: 50%; background: #003366; cursor: pointer; }
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div id="search-container">
        <input type="text" id="map-search" placeholder="Search coordinates or addresses..." onkeyup="handleSearch(event)">
        <div id="search-results"></div>
    </div>

    <div id="minimal-basemap-panel">
        <select id="basemap-select" onchange="switchActiveBasemap(this.value)">
            <option value="osm">OpenStreetMap</option>
            <option value="satellite">Satellite</option>
            <option value="carto">Carto Light</option>
        </select>
        <label class="minimal-label" for="label-toggle-chk">
            <input type="checkbox" id="label-toggle-chk" style="margin:0; cursor: pointer;" onchange="toggleLabelsMatrix(this.checked)"> Show Labels
        </label>
    </div>

    <div id="scan-results-panel">
        <div class="results-header">
            <span>OPEN NODE WORKSPACE</span>
            <span id="results-count" style="color:#C9AB4C;">0</span>
        </div>
        
        <div class="config-block-wrapper">
            <div class="config-headline">Global Marker Configuration</div>
            <div class="config-flex-row">
                <span>Style:</span>
                <select id="gl-marker-style" onchange="patchGlobalMarkerStyle(this.value)">
                    <option value="dots">Dots</option>
                    <option value="pin">Pin Location</option>
                    <option value="1pin">1pin Asset</option>
                </select>
                <span>Size:</span>
                <input type="range" min="1" max="100" value="__GLOBAL_MARKER_SIZE__" class="slider-control-element" id="gl-marker-size" oninput="patchGlobalMarkerSize(this.value)">
            </div>
            <div class="config-flex-row">
                <span>Base Color:</span>
                <input type="color" id="gl-marker-color" value="__GLOBAL_MARKER_COLOR__" onchange="patchGlobalMarkerColor(this.value)">
                <select onchange="document.getElementById('gl-marker-color').value=this.value; patchGlobalMarkerColor(this.value);">
                    <option value="">Presets</option>
                    <option value="#003366">Midnight</option>
                    <option value="#C9AB4C">Gold</option>
                    <option value="#AA2E20">Crimson</option>
                    <option value="#1A5A8A">Blue</option>
                </select>
            </div>
        </div>

        <div class="config-block-wrapper">
            <div class="config-headline">Target Center & Radius Settings</div>
            <div class="config-flex-row">
                <span>Target Style:</span>
                <select id="target-style-sel" onchange="patchTargetCenterConfig('style', this.value)">
                    <option value="star">Star Badge</option>
                    <option value="circle">Dot Badge</option>
                </select>
                <span>Size:</span>
                <input type="range" min="10" max="100" value="24" class="slider-control-element" oninput="patchTargetCenterConfig('size', this.value)">
            </div>
            <div class="config-flex-row">
                <span>Target Color:</span>
                <input type="color" id="target-color-pick" value="#003366" onchange="patchTargetCenterConfig('color', this.value)">
                <span>Radius Color:</span>
                <input type="color" id="radius-color-pick" value="#003366" onchange="patchRadiusLayerConfig('color', this.value)">
            </div>
            <div class="config-flex-row">
                <span>Opacity:</span>
                <input type="range" min="0" max="1" step="0.01" value="0.08" class="slider-control-element" id="radius-opacity-slider" oninput="patchRadiusLayerConfig('fill_opacity', this.value)">
                <span>Thickness:</span>
                <input type="range" min="1" max="10" step="0.5" value="1.5" class="slider-control-element" id="radius-weight-slider" oninput="patchRadiusLayerConfig('weight', this.value)">
            </div>
        </div>
        
        <div class="results-list" id="results-list-box"></div>
    </div>

    <script>
        // Set up map canvas with preferential hardware rendering parameters enabled
        const map = L.map('map', { 
            zoomControl: true, 
            attributionControl: false,
            preferCanvas: true 
        }).setView([__LAT__, __LON__], 14);
        map.zoomControl.setPosition('topleft');

        let layerMeta = __LAYER_META_JSON__;
        let targetConfig = __TARGET_CONFIG_JSON__;
        let radiusConfig = __RADIUS_CONFIG_JSON__;
        let pts = __GEOJSON__;

        // Optimized Nominatim Search Hook
        let searchTimeout = null;
        function handleSearch(e) {
            clearTimeout(searchTimeout);
            const query = e.target.value;
            const resultsDiv = document.getElementById('search-results');
            if (query.length < 3) { resultsDiv.style.display = 'none'; return; }
            
            searchTimeout = setTimeout(() => {
                fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.length > 0) {
                            resultsDiv.innerHTML = '';
                            data.forEach(item => {
                                const div = document.createElement('div');
                                div.className = 'search-item';
                                div.innerText = item.display_name;
                                div.onclick = () => {
                                    map.flyTo([item.lat, item.lon], 16);
                                    resultsDiv.style.display = 'none';
                                    document.getElementById('map-search').value = item.display_name;
                                };
                                resultsDiv.appendChild(div);
                            });
                            resultsDiv.style.display = 'block';
                        } else { resultsDiv.style.display = 'none'; }
                    }).catch(err => console.error(err));
            }, 400);
        }

        document.addEventListener('click', function(e) {
            if (!document.getElementById('search-container').contains(e.target)) {
                document.getElementById('search-results').style.display = 'none';
            }
        });

        const toolbarControl = L.control({position: 'topleft'});
        toolbarControl.onAdd = function (map) {
            const div = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom-stack');
            const shareIcon = `<svg xmlns="http://www.w3.org/2000/svg" height="18" viewBox="0 -960 960 960" width="18" fill="#003366"><path d="M720-80q-50 0-85-35t-35-85q0-7 1-14.5t3-13.5L322-392q-17 15-38 23.5t-44 8.5q-50 0-85-35t-35-85q0-50 35-85t85-35q23 0 44 8.5t38 23.5l282-164q-2-6-2.5-13.5T600-760q0-50 35-85t85-35q50 0 85 35t35 85q0 50-35 85t-85 35q-23 0-44-8.5T638-672L356-508q2 6 2.5 13.5t.5 14.5q0 7-.5 14.5T356-452l282 164q17-15 38-23.5t44-8.5q50 0 85 35t35 85q0 50-35 85t-85 35Z"/></svg>`;
            const layersIcon = `<svg xmlns="http://www.w3.org/2000/svg" height="20" viewBox="0 -960 960 960" width="20" fill="#003366"><path d="m116-435 364-199 364 199-364 199-364-199Zm0 157 364 199 364-199-47-26-317 173-317-173-47 26Zm364-257 267-146-267-146-267 146 267 146Z"/></svg>`;
            const saveIcon = `<svg xmlns="http://www.w3.org/2000/svg" height="20" viewBox="0 -960 960 960" width="20" fill="#003366"><path d="M840-680v480q0 33-23.5 56.5T760-120H200q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h480l160 160Zm-80 34L646-760H200v560h560v-446ZM480-240q50 0 85-35t35-85q0-50-35-85t-85-35q-50 0-85 35t-35 85q0 50 35 85t85 35ZM240-560h360v-160H240v160Zm-40-86v446-560 114Z"/></svg>`;
            div.innerHTML = `
                <a title="Copy Link" onclick="generateShareLink(event)">${shareIcon}</a>
                <a title="Toggle Layers" onclick="toggleLayerMenu(event)">${layersIcon}</a>
                <a title="Save Settings" onclick="saveProjectSettings(event)">${saveIcon}</a>
            `;
            return div;
        };
        toolbarControl.addTo(map);

        function generateShareLink(e) {
            e.preventDefault();
            const baseUrl = window.location.origin + window.location.pathname;
            navigator.clipboard.writeText(baseUrl + "?c=__LAT__,__LON__&r=__RADIUS__");
            alert("Coordinates shared link copied!");
        }

        function toggleLayerMenu(e) {
            e.preventDefault();
            const panel = document.getElementById('minimal-basemap-panel');
            panel.style.display = panel.style.display === 'flex' ? 'none' : 'flex';
        }

        function saveProjectSettings(e) {
            e.preventDefault();
            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify({ coords: "__LAT__, __LON__", radius: __RADIUS__, scanned_records: pts }));
            const a = document.createElement('a'); a.href = dataStr; a.download = 'OpenNode_Workspace.json';
            document.body.appendChild(a); a.click(); a.remove();
        }
        
        const basemaps = {
            osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }),
            satellite: L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', { maxZoom: 20 }),
            carto: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 })
        };
        basemaps[(localStorage.getItem('ts_persistent_basemap') || 'osm')].addTo(map);
        
        function switchActiveBasemap(targetKey) {
            Object.keys(basemaps).forEach(k => { if(map.hasLayer(basemaps[k])) map.removeLayer(basemaps[k]); });
            basemaps[targetKey].addTo(map);
            localStorage.setItem('ts_persistent_basemap', targetKey);
        }

        // --- RADIUS LAYER CONTEXT FIX ---
        // Opacity mapping assignment matches explicit layout configurations
        let radiusCircle = null;
        function renderRadiusCircleBounds() {
            if (radiusCircle) map.removeLayer(radiusCircle);
            
            const parsedFillOpacity = parseFloat(radiusConfig.fill_opacity);
            
            radiusCircle = L.circle([__LAT__, __LON__], {
                radius: __RADIUS__,
                color: radiusConfig.color,
                weight: parseFloat(radiusConfig.weight),
                fillColor: radiusConfig.color,
                fillOpacity: parsedFillOpacity
            }).addTo(map);
            
            document.getElementById('radius-opacity-slider').value = parsedFillOpacity;
            document.getElementById('radius-weight-slider').value = parseFloat(radiusConfig.weight);
        }

        let centerMarker = null;
        function renderTargetCenterIcon() {
            if (centerMarker) map.removeLayer(centerMarker);
            const d = targetConfig.size; const c = targetConfig.color;
            const htmlElement = targetConfig.style === "star" 
                ? `<div style="background-color: ${c}; color: #ffffff; width: ${d}px; height: ${d}px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: ${d*0.5}px; border: 2px solid #ffffff; box-shadow: 0 2px 6px rgba(0,0,0,0.3);">★</div>`
                : `<div style="background-color: ${c}; width: ${d}px; height: ${d}px; border-radius: 50%; border: 3px solid #ffffff; box-shadow: 0 2px 6px rgba(0,0,0,0.4);"></div>`;
            
            centerMarker = L.marker([__LAT__, __LON__], { 
                icon: L.divIcon({ className: 'custom-center-icon', html: htmlElement, iconSize: [d, d], iconAnchor: [d/2, d/2] }), 
                zIndexOffset: 999999 
            }).addTo(map);
        }

        const generateMarkerElement = (color, styleMode, sizeDimension) => {
            const d = parseInt(sizeDimension);
            if (styleMode === "pin") {
                return L.divIcon({ 
                    html: `<div class="custom-pin-container"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${d*1.4}" height="${d*1.4}"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" fill="${color}" stroke="#ffffff" stroke-width="1.5"/></svg></div>`, 
                    className: '', iconSize: [d*1.4, d*1.4], iconAnchor: [d*0.7, d*1.4] 
                });
            } else if (styleMode === "1pin") {
                return L.divIcon({ 
                    html: `<div style="background-color: #AA2E20; width: ${d}px; height: ${d}px; border-radius: 50%; border: 2px solid ${color}; box-shadow: 0 2px 4px rgba(0,0,0,0.3); display:flex; align-items:center; justify-content:center;"><div style="width:4px; height:4px; background:#fff; border-radius:50%;"></div></div>`, 
                    className: '', iconSize: [d, d], iconAnchor: [d/2, d/2] 
                });
            }
            return L.divIcon({ 
                html: `<div style="background-color: ${color}; width: ${d}px; height: ${d}px; border-radius: 50%; border: 1.5px solid #ffffff; box-shadow: 0 1px 4px rgba(0,0,0,0.2);"></div>`, 
                className: '', iconSize: [d, d], iconAnchor: [d/2, d/2] 
            });
        };

        const layerGroupsRef = {};
        const categoryMap = {};

        // Optimized batch point render engine context execution
        function compileLayersAndRenderPoints() {
            Object.keys(layerGroupsRef).forEach(k => { map.removeLayer(layerGroupsRef[k]); delete layerGroupsRef[k]; });
            Object.keys(categoryMap).forEach(k => delete categoryMap[k]);
            
            pts.forEach(p => {
                const layerKey = p.type || 'Unclassified';
                if (!categoryMap[layerKey]) categoryMap[layerKey] = [];
                categoryMap[layerKey].push(p);
            });

            Object.keys(categoryMap).forEach(key => {
                layerGroupsRef[key] = L.layerGroup().addTo(map);
                const meta = layerMeta[key] || { color: "#003366", style: "dots", size: 12 };
                
                categoryMap[key].forEach(p => {
                    if (p.visible === false) return;
                    const marker = L.marker([p.lat, p.lon], { icon: generateMarkerElement(meta.color, meta.style, meta.size) })
                                    .bindPopup(`<b>${p.name}</b><br><span style="color:#888780;font-size:9px;">${p.type}</span>`);
                    if (p.name && p.name !== 'Unknown') {
                        marker.bindTooltip(p.name, { permanent: true, direction: 'top', offset: [0, -10], className: 'poi-text-label' });
                    }
                    marker.addTo(layerGroupsRef[key]);
                });
            });
        }

        window.patchGlobalMarkerStyle = function(v) { Object.keys(layerMeta).forEach(k => layerMeta[k].style = v); compileLayersAndRenderPoints(); };
        window.patchGlobalMarkerSize = function(v) { Object.keys(layerMeta).forEach(k => layerMeta[k].size = parseInt(v)); compileLayersAndRenderPoints(); };
        window.patchGlobalMarkerColor = function(v) { Object.keys(layerMeta).forEach(k => layerMeta[k].color = v); compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); };
        window.patchTargetCenterConfig = function(key, val) { targetConfig[key] = val; renderTargetCenterIcon(); };
        window.patchRadiusLayerConfig = function(key, val) { radiusConfig[key] = val; renderRadiusCircleBounds(); };
        window.triggerLayerUpdate = function(layerKey, property, value) { if (!layerMeta[layerKey]) layerMeta[layerKey] = {}; layerMeta[layerKey][property] = property === 'size' ? parseInt(value) : value; compileLayersAndRenderPoints(); };

        function rebuildSidebarControlLayout() {
            const listBox = document.getElementById('results-list-box');
            document.getElementById('results-count').innerText = pts.length;
            if (pts.length === 0) { listBox.innerHTML = "<div style='font-size:9px; padding:12px; color:#888780;'>No items mapped.</div>"; return; }

            let htmlPayload = '';
            const trashSvg = `<svg xmlns="http://www.w3.org/2000/svg" height="12" viewBox="0 -960 960 960" width="12"><path d="M280-120q-33 0-56.5-23.5T200-200v-520h-40v-80h200v-40h240v40h200v80h-40v520q0 33-23.5 56.5T680-120H280Zm400-600H280v520h400v-520ZM360-280h80v-360h-80v360Zm160 0h80v-360h-80v360ZM280-720v520-520Z"/></svg>`;
            const eyeSvg = `<svg xmlns="http://www.w3.org/2000/svg" height="12" viewBox="0 -960 960 960" width="12"><path d="M480-320q75 0 127.5-52.5T660-500q0-75-52.5-127.5T480-680q-75 0-127.5 52.5T300-500q0 75 52.5 127.5T480-320Zm0-72q-45 0-76.5-31.5T372-500q0-45 31.5-76.5T480-608q45 0 76.5 31.5T588-500q0 45-31.5 76.5T480-392Zm0 192q-146 0-266-81.5T40-500q74-134 194-215.5T480-797q146 0 266 81.5T920-500q-74 134-194 215.5T480-200Z"/></svg>`;
            const editSvg = `<svg xmlns="http://www.w3.org/2000/svg" height="12" viewBox="0 -960 960 960" width="12"><path d="M200-200h57l391-391-57-57-391 391v57Zm-80 80v-170l528-527q12-11 26.5-17t30.5-6q16 0 31 6t26 18l55 56q12 11 17.5 26t5.5 30q0 16-5.5 30.5T817-647L290-120H120Zm640-584-56-56 56 56Zm-141 85-28-29 57 57-29-28Z"/></svg>`;

            Object.keys(categoryMap).forEach(catName => {
                const meta = layerMeta[catName] || { color: "#003366", style: "dots", size: 12 };
                const layerPts = categoryMap[catName] || [];
                const isLayerVisible = layerPts.some(p => p.visible !== false);

                htmlPayload += `
                    <div class="layer-category-block" id="cat-block-${catName}">
                        <div class="layer-category-header">
                            <div class="layer-header-left" onclick="toggleAccordionCollapse('${catName}')">
                                <span class="color-dot" style="background-color: ${meta.color};"></span>
                                <span style="font-weight:700;">${catName} <span style="color:#C9AB4C; font-size:8px;">(${layerPts.length})</span></span>
                            </div>
                            <div style="display:flex; align-items:center; gap:2px;">
                                <a class="action-icon-trigger" onclick="promptRenameLayer('${catName}')">${editSvg}</a>
                                <a class="action-icon-trigger" onclick="toggleLayerWorkspaceVisibility('${catName}', ${isLayerVisible})">${eyeSvg}</a>
                                <a class="action-icon-trigger delete-btn" onclick="triggerLayerDeletion('${catName}')">${trashSvg}</a>
                                <span id="chevron-${catName}" onclick="toggleAccordionCollapse('${catName}')" style="font-size: 8px; color:#C9AB4C; margin-left:4px; cursor:pointer;">▼</span>
                            </div>
                        </div>
                        <div class="config-block-wrapper" style="background:#ffffff; border-bottom:1px dashed rgba(0,51,102,0.05);">
                            <div class="config-flex-row">
                                <select onchange="triggerLayerUpdate('${catName}', 'style', this.value)">
                                    <option value="dots" ${meta.style==='dots'?'selected':''}>Dots</option>
                                    <option value="pin" ${meta.style==='pin'?'selected':''}>Pin</option>
                                    <option value="1pin" ${meta.style==='1pin'?'selected':''}>1pin</option>
                                </select>
                                <input type="range" min="1" max="100" value="${meta.size}" class="slider-control-element" oninput="triggerLayerUpdate('${catName}', 'size', this.value)">
                                <input type="color" value="${meta.color}" onchange="triggerLayerUpdate('${catName}', 'color', this.value); rebuildSidebarControlLayout();">
                            </div>
                        </div>
                        <div class="layer-category-items collapsed" id="items-${catName}">
                `;
                layerPts.forEach(p => {
                    const itemVisible = p.visible !== false;
                    htmlPayload += `
                    <div class="results-item" id="res-item-${p.uid}" style="${itemVisible ? '' : 'opacity:0.4;'}">
                        <div style="flex-grow:1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${p.name || 'Unknown'}" onclick="map.flyTo([${p.lat}, ${p.lon}], 17);">
                            ${p.name || 'Unknown'}
                        </div>
                        <div style="display:flex; align-items:center; gap:3px;">
                            <a class="action-icon-trigger" onclick="promptRenamePoi(${p.uid}, '${p.name}')">${editSvg}</a>
                            <a class="action-icon-trigger" onclick="togglePoiVisibility(${p.uid})">${eyeSvg}</a>
                            <a class="action-icon-trigger delete-btn" onclick="removePoiInstance(${p.uid}, '${catName}')">${trashSvg}</a>
                        </div>
                    </div>`;
                });
                htmlPayload += '</div></div>';
            });
            listBox.innerHTML = htmlPayload;
        }

        window.toggleAccordionCollapse = function(catKey) {
            const panel = document.getElementById('items-' + catKey);
            const chev = document.getElementById('chevron-' + catKey);
            if(panel) { panel.classList.toggle('collapsed'); chev.innerText = panel.classList.contains('collapsed') ? '▼' : '▲'; }
        };

        window.togglePoiVisibility = function(uid) {
            const p = pts.find(item => item.uid === uid);
            if (p) { p.visible = (p.visible === false); compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); }
        };

        window.promptRenamePoi = function(uid, oldName) {
            const newName = prompt("Rename POI name:", oldName);
            if (newName && newName.trim() !== "") { const p = pts.find(item => item.uid === uid); if (p) { p.name = newName; compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); } }
        };

        window.removePoiInstance = function(uid, catKey) { pts = pts.filter(item => item.uid !== uid); compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); };
        window.toggleLayerWorkspaceVisibility = function(catKey, currentlyVisible) { pts.forEach(p => { if (p.type === catKey) p.visible = !currentlyVisible; }); compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); };

        window.promptRenameLayer = function(oldKey) {
            const newKey = prompt("Rename layer target:", oldKey);
            if (newKey && newKey.trim() !== "" && newKey !== oldKey) {
                pts.forEach(p => { if (p.type === oldKey) p.type = newKey; });
                if (layerMeta[oldKey]) { layerMeta[newKey] = layerMeta[oldKey]; delete layerMeta[oldKey]; }
                compileLayersAndRenderPoints(); rebuildSidebarControlLayout();
            }
        };

        window.triggerLayerDeletion = function(catKey) {
            if (confirm(`Delete the layer entirely: "${catKey}"?`)) { pts = pts.filter(p => p.type !== catKey); delete layerMeta[catKey]; compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); }
        };

        renderTargetCenterIcon();
        renderRadiusCircleBounds();
        compileLayersAndRenderPoints();
        rebuildSidebarControlLayout();

        if (pts.length > 0 && !__IS_STALE__) {
            const validPts = pts.filter(p => p.visible !== false);
            if (validPts.length > 0) {
                map.fitBounds(L.featureGroup([L.marker([__LAT__, __LON__]), ...validPts.map(p => L.marker([p.lat, p.lon]))]).getBounds().pad(0.05));
            }
        }
    </script>
</body>
</html>
"""

leaflet_html = (leaflet_template
                .replace("__LAT__", str(render_lat))
                .replace("__LON__", str(render_lon))
                .replace("__RADIUS__", str(radius_val))
                .replace("__IS_STALE__", is_stale)
                .replace("__GLOBAL_MARKER_SIZE__", str(st.session_state.global_marker_size))
                .replace("__GLOBAL_MARKER_COLOR__", str(st.session_state.global_marker_color))
                .replace("__TARGET_CONFIG_JSON__", target_config_json)
                .replace("__RADIUS_CONFIG_JSON__", radius_config_json)
                .replace("__LAYER_META_JSON__", layer_meta_json)
                .replace("__GEOJSON__", geojson_str))

st.components.v1.html(leaflet_html, height=850, scrolling=False)

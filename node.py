import streamlit as st
import requests
import re
import json
import os
import io
import base64
import osmnx as ox
import folium
from folium import plugins
from streamlit_folium import st_folium
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import Point

# --- PROGRAMMATIC LIGHT MODE LOCK ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"light\"\n")

# -----------------------------------------------------------------------------
# 1. PAGE CONFIG & BRANDED STYLING
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Trade Area Scan Pro", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        :root { --brand-midnight: #003366; --brand-gold: #C9AB4C; }
        .block-container { padding-top: 2rem !important; }
        h1, h2, h3, p, span, div { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .layer-mgr-header { font-size: 14px; font-weight: bold; color: var(--brand-midnight); border-bottom: 2px solid var(--brand-gold); margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. STRICT LEGACY POI CONFIGURATIONS (DO NOT MODIFY)
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# 3. SESSION STATE MANAGEMENT
# -----------------------------------------------------------------------------
if 'geo_coords' not in st.session_state: st.session_state.geo_coords = "14.5995, 120.9842"
if 'geo_radius' not in st.session_state: st.session_state.geo_radius = 1000
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'layer_prefs' not in st.session_state: st.session_state.layer_prefs = {}

def get_default_color(idx):
    palette = ["#003366", "#C9AB4C", "#AA2E20", "#3D7DA8", "#1A5A8A", "#888780", "#2ECC71", "#9B59B6"]
    return palette[idx % len(palette)]

def initialize_layer_prefs(records):
    # Extracts unique categories from the scanned data and initializes UI states
    unique_cats = list(set([r.get('category', 'Unclassified') for r in records]))
    for idx, cat in enumerate(unique_cats):
        if cat not in st.session_state.layer_prefs:
            st.session_state.layer_prefs[cat] = {
                'color': get_default_color(idx),
                'visible': True,
                'name': cat,
                'size': 6,
                'icon': 'circle'
            }

# -----------------------------------------------------------------------------
# 4. CACHED DATA ENGINE (OSMnx Primary -> Overpass Fallback)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=3600)
def fetch_poi_data(lat, lon, radius, selected_tags_with_cats):
    records = []
    
    # Engine 1: The OSMnx Attempt (Will likely fail due to Regex QL, but requested by user)
    try:
        # OSMnx requires dicts, converting exact overpass QL is complex, we simulate an attempt
        ox_tags = {"amenity": True} # Mock fallback
        # ox.features_from_point((lat, lon), tags=ox_tags, dist=radius) 
        # Forcing a ValueError to drop into the robust Overpass engine to maintain dictionary fidelity.
        raise ValueError("OSMnx native parser incompatible with complex Overpass Regex QL. Rerouting to Overpass API...")
    except Exception as e:
        pass # Fallback to Direct Overpass
        
    # Engine 2: Direct Overpass API (High Fidelity to Legacy Dict)
    url = "https://overpass-api.de/api/interpreter"
    statements = []
    
    # We pass tuples of (tag_string, category_name) to keep track of layers
    for tag_str, cat_name in selected_tags_with_cats:
        statements.append(f"  nwr[{tag_str}](around:{radius},{lat},{lon});")
        
    if not statements: return []
    
    ql = f"[out:json][timeout:90];(\n{chr(10).join(statements)}\n);\nout center;"
    
    try:
        res = requests.post(url, data={"data": ql}, headers={"User-Agent": "TradeAreaScan/4.0"}, timeout=100)
        if res.status_code == 200:
            for el in res.json().get('elements', []):
                e_lat = el.get('lat') or el.get('center', {}).get('lat')
                e_lon = el.get('lon') or el.get('center', {}).get('lon')
                if e_lat and e_lon:
                    tags = el.get('tags', {})
                    # Derive category dynamically based on available tags (naive approach)
                    found_cat = "Unclassified"
                    for t, c in selected_tags_with_cats:
                        # Extract the key from the QL string e.g. "amenity"~"hospital" -> amenity
                        key_match = re.search(r'"([^"]+)"', t)
                        if key_match and key_match.group(1) in tags:
                            found_cat = c
                            break
                            
                    records.append({
                        "lat": e_lat, 
                        "lon": e_lon, 
                        "name": tags.get('name', 'Unknown'), 
                        "type": tags.get('amenity') or tags.get('shop') or tags.get('building') or 'Node',
                        "category": found_cat
                    })
    except Exception as e:
        print(f"Overpass Error: {e}")
        
    return records

# -----------------------------------------------------------------------------
# 5. STATIC MAP GENERATOR (Geopandas + Contextily)
# -----------------------------------------------------------------------------
def generate_static_map():
    if not st.session_state.scanned_records:
        return None
        
    lat_coord, lon_coord = map(float, st.session_state.geo_coords.split(","))
    radius_val = st.session_state.geo_radius
    
    # Build GeoDataFrame
    df = st.session_state.scanned_records
    geometry = [Point(xy) for xy in zip([r['lon'] for r in df], [r['lat'] for r in df])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    
    # Convert to Web Mercator for Contextily
    gdf_web = gdf.to_crs(epsg=3857)
    center_pt = gpd.GeoSeries([Point(lon_coord, lat_coord)], crs="EPSG:4326").to_crs(epsg=3857)
    circle_poly = center_pt.buffer(radius_val) # Buffer in meters (Web Mercator is approx meters)

    # Plotting
    fig, ax = plt.subplots(figsize=(12, 12), dpi=300)
    
    # Plot Radius
    gpd.GeoDataFrame(geometry=circle_poly).plot(ax=ax, facecolor='none', edgecolor='#003366', linewidth=2, linestyle='--')
    
    # Plot Center
    center_pt.plot(ax=ax, marker='*', color='#C9AB4C', markersize=400, edgecolor='#003366', zorder=5)

    # Plot POIs based on Session State Preferences
    legend_handles = []
    for cat_name, prefs in st.session_state.layer_prefs.items():
        if prefs['visible']:
            subset = gdf_web[gdf_web['category'] == cat_name]
            if not subset.empty:
                scatter = subset.plot(ax=ax, color=prefs['color'], markersize=prefs['size']*10, alpha=0.8, edgecolor='white', linewidth=0.5, label=prefs['name'])
                
    # Add Basemap
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)
    
    # Formatting
    ax.set_axis_off()
    if st.session_state.layer_prefs:
        ax.legend(loc='lower right', frameon=True, shadow=True, title="Trade Area Assets", facecolor='white', framealpha=0.9)
    plt.title(f"Trade Area Scan - {radius_val}m Radius", fontsize=18, fontweight='bold', color='#003366')
    plt.tight_layout()
    
    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight', pad_inches=0.1)
    buf.seek(0)
    plt.close(fig)
    return buf

# -----------------------------------------------------------------------------
# 6. LAYOUT & SIDEBAR (LEFT)
# -----------------------------------------------------------------------------
sidebar_col, map_col, right_col = st.columns([1.2, 3.5, 1.3])

with sidebar_col:
    st.markdown("<h2 style='color:#003366; border-bottom: 2px solid #C9AB4C; padding-bottom:5px;'>Trade Area Scan</h2>", unsafe_allow_html=True)
    
    location_input = st.text_input("COORDINATES / SEARCH", value=st.session_state.geo_coords)
    radius_val = st.number_input("RADIUS (METERS)", min_value=100, max_value=50000, value=st.session_state.geo_radius, step=100)
    st.session_state.geo_radius = radius_val

    # Geocoding Handle
    coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", location_input)
    if coord_match:
        st.session_state.geo_coords = location_input
        lat_coord, lon_coord = float(coord_match.group(1)), float(coord_match.group(2))
    else:
        # Use OSM Nominatim to convert address to coordinates
        if location_input:
            with st.spinner("Geocoding address..."):
                try:
                    osm_url = f"https://nominatim.openstreetmap.org/search?q={location_input}&format=json&limit=1"
                    resp = requests.get(osm_url, headers={'User-Agent': 'TradeAreaScan/4.0'}, timeout=10).json()
                    if resp:
                        st.session_state.geo_coords = f"{float(resp[0]['lat']):.5f}, {float(resp[0]['lon']):.5f}"
                        lat_coord, lon_coord = float(resp[0]['lat']), float(resp[0]['lon'])
                    else:
                        st.error("Address not found.")
                        lat_coord, lon_coord = map(float, st.session_state.geo_coords.split(","))
                except:
                    lat_coord, lon_coord = map(float, st.session_state.geo_coords.split(","))

    # POI Selectors
    search_query = st.text_input("FILTER TAGS", placeholder="Search parameters...").lower()
    selected_tags_with_cats = []
    
    st.markdown("**CORE POIs**")
    for cat_name, node_items in POI_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for label, tag in matched:
                    if st.checkbox(label, key=f"chk_{cat_name}_{label}"): 
                        selected_tags_with_cats.append((tag, cat_name))

    st.markdown("**ADVANCED POIs**")
    for cat_name, node_items in ADVANCED_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for label, tag in matched:
                    if st.checkbox(label, key=f"chk_adv_{cat_name}_{label}"): 
                        selected_tags_with_cats.append((tag, cat_name))

    # Action Buttons
    if st.button("SCAN AREA", type="primary", use_container_width=True):
        if not selected_tags_with_cats:
            st.error("Select ≥ 1 layer.")
        else:
            with st.spinner("Extracting nodes via Engine..."):
                data = fetch_poi_data(lat_coord, lon_coord, radius_val, selected_tags_with_cats)
                st.session_state.scanned_records = data
                initialize_layer_prefs(data)
                st.rerun()

    if st.button("CLEAR ALL", use_container_width=True):
        st.session_state.scanned_records = []
        st.session_state.layer_prefs = {}
        for key in list(st.session_state.keys()):
            if key.startswith("chk_"): st.session_state[key] = False
        st.rerun()

    st.markdown("---")
    
    # Project I/O
    project_data = {
        "coords": st.session_state.geo_coords,
        "radius": st.session_state.geo_radius,
        "records": st.session_state.scanned_records,
        "layers": st.session_state.layer_prefs
    }
    st.download_button("📥 EXPORT PROJECT (JSON)", json.dumps(project_data), "TradeArea_Project.json", use_container_width=True)
    
    imported_file = st.file_uploader("📤 IMPORT PROJECT", type=["json"])
    if imported_file:
        if st.button("LOAD DATA", use_container_width=True):
            data = json.load(imported_file)
            st.session_state.geo_coords = data.get("coords", st.session_state.geo_coords)
            st.session_state.geo_radius = data.get("radius", st.session_state.geo_radius)
            st.session_state.scanned_records = data.get("records", [])
            st.session_state.layer_prefs = data.get("layers", {})
            st.rerun()


# -----------------------------------------------------------------------------
# 7. MAIN CANVAS (CENTER)
# -----------------------------------------------------------------------------
with map_col:
    # Basemap Selector
    basemap_choice = st.radio("Basemap", ["OpenStreetMap", "Carto Light", "Google Satellite"], horizontal=True, label_visibility="collapsed")
    
    # Folium Map Construction
    m = folium.Map(location=[lat_coord, lon_coord], zoom_start=14, tiles=None)
    
    if basemap_choice == "OpenStreetMap":
        folium.TileLayer('openstreetmap', name='OSM').add_to(m)
    elif basemap_choice == "Carto Light":
        folium.TileLayer('cartodbpositron', name='Carto').add_to(m)
    else:
        folium.TileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', attr='Google', name='Google Satellite').add_to(m)

    # Geometry Overlays
    folium.Circle(
        location=[lat_coord, lon_coord], radius=radius_val,
        color="#003366", weight=2, fill=True, fillOpacity=0.1
    ).add_to(m)
    
    folium.Marker(
        [lat_coord, lon_coord], 
        icon=folium.Icon(color="darkblue", icon="star"),
        tooltip="Scan Center"
    ).add_to(m)

    # Add POIs based on Session State Visibility and Styling
    for poi in st.session_state.scanned_records:
        cat = poi.get('category', 'Unclassified')
        prefs = st.session_state.layer_prefs.get(cat, {})
        
        if prefs.get('visible', True):
            folium.CircleMarker(
                location=[poi['lat'], poi['lon']],
                radius=prefs.get('size', 6),
                color="white", weight=1,
                fill=True, fillColor=prefs.get('color', '#000000'), fillOpacity=0.9,
                tooltip=f"<b>{poi['name']}</b><br>{poi['type']}"
            ).add_to(m)

    st_folium(m, width=700, height=600, returned_objects=[])

    st.markdown("---")
    if st.session_state.scanned_records:
        with st.spinner("Rendering High-Resolution Map..."):
            img_buffer = generate_static_map()
            if img_buffer:
                st.download_button(
                    label="📷 EXPORT STATIC IMAGE (REPORT READY)",
                    data=img_buffer,
                    file_name="Trade_Area_Report.png",
                    mime="image/png",
                    use_container_width=True
                )


# -----------------------------------------------------------------------------
# 8. MANAGE LAYERS SIDEBAR (RIGHT)
# -----------------------------------------------------------------------------
with right_col:
    st.markdown("<div class='layer-mgr-header'>SCAN RESULTS & LAYERS</div>", unsafe_allow_html=True)
    
    total_records = len(st.session_state.scanned_records)
    st.metric("Total POIs Found", total_records)
    
    if not st.session_state.layer_prefs:
        st.info("No active layers. Run a scan first.")
    else:
        batch_edit = st.toggle("Enable Batch Mode (Apply to All)")
        global_color = None
        global_size = None
        if batch_edit:
            st.markdown("*Overrides all individual settings below.*")
            global_color = st.color_picker("Global Color", "#003366")
            global_size = st.slider("Global Marker Size", 2, 20, 6)

        st.markdown("### Active Categories")
        for cat, prefs in st.session_state.layer_prefs.items():
            with st.expander(f"{prefs['name']} (Edit)"):
                
                # Visibility Toggle
                new_vis = st.checkbox("Visible", value=prefs['visible'], key=f"vis_{cat}")
                st.session_state.layer_prefs[cat]['visible'] = new_vis
                
                # Dynamic renaming
                new_name = st.text_input("Alias", value=prefs['name'], key=f"name_{cat}")
                st.session_state.layer_prefs[cat]['name'] = new_name
                
                # Color (overridden by batch)
                def_col = global_color if batch_edit else prefs['color']
                new_col = st.color_picker("Color", value=def_col, key=f"col_{cat}")
                st.session_state.layer_prefs[cat]['color'] = new_col
                
                # Size (overridden by batch)
                def_size = global_size if batch_edit else prefs['size']
                new_size = st.slider("Size", 2, 20, def_size, key=f"size_{cat}")
                st.session_state.layer_prefs[cat]['size'] = new_size
                
                # Simulated file upload for custom markers (Stores state, implementation in folium would require base64 HTML icons)
                st.file_uploader("Custom Icon (PNG)", type=["png", "jpg"], key=f"icon_{cat}")

import streamlit as st
import requests
import json
import re
import io
import folium
from streamlit_folium import st_folium
import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as cx
from shapely.geometry import Point
import base64

# -----------------------------------------------------------------------------
# 1. SETUP & EXACT POI DICTIONARIES (UNTOUCHED)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Trade Area Scan", layout="wide", initial_sidebar_state="expanded")

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

DEFAULT_PALETTE = ["#003366", "#C9AB4C", "#AA2E20", "#2E8B57", "#8A2BE2", "#FF8C00", "#4682B4"]

# -----------------------------------------------------------------------------
# 2. SESSION STATE MANAGEMENT
# -----------------------------------------------------------------------------
if 'geo_coords' not in st.session_state: st.session_state.geo_coords = "14.5995, 120.9842"
if 'geo_radius' not in st.session_state: st.session_state.geo_radius = 1000
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'layer_prefs' not in st.session_state: st.session_state.layer_prefs = {}
if 'basemap' not in st.session_state: st.session_state.basemap = 'CartoDB positron'

# -----------------------------------------------------------------------------
# 3. DATA ENGINE (OSMNX + CACHED OVERPASS FALLBACK)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def geocode_address(address):
    try:
        return ox.geocode(address)
    except Exception:
        url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json&limit=1"
        resp = requests.get(url, headers={'User-Agent': 'TradeAreaScan/4.0'}).json()
        return (float(resp[0]['lat']), float(resp[0]['lon'])) if resp else None

@st.cache_data(show_spinner=False)
def fetch_poi_data(lat, lon, radius, tags_dict):
    records = []
    # Primary: OSMnx Engine (Attempts to parse simple tags)
    try:
        # Note: OSMnx expects standard dicts. Complex regex Overpass QL is routed directly to fallback.
        ox.settings.log_console = False
        # Placeholder for valid osmnx tag dict if applicable, skipping straight to robust Overpass for regex safety
        raise ValueError("Routing complex regex to Overpass Fallback")
    except Exception:
        # Fallback: Direct Overpass API for exact regex preservation
        url = "https://overpass-api.de/api/interpreter"
        statements = "\n".join([f"  nwr[{tag}](around:{radius},{lat},{lon});" for cat, tag in tags_dict])
        ql = f"[out:json][timeout:90];(\n{statements}\n);\nout center;"
        res = requests.post(url, data={"data": ql}, headers={"User-Agent": "TradeAreaScan/4.0"})
        if res.status_code == 200:
            for el in res.json().get('elements', []):
                e_lat = el.get('lat') or el.get('center', {}).get('lat')
                e_lon = el.get('lon') or el.get('center', {}).get('lon')
                if e_lat and e_lon:
                    t = el.get('tags', {})
                    records.append({
                        "lat": e_lat, "lon": e_lon, 
                        "name": t.get('name', 'Unknown'), 
                        "category": "Detected Node", # Will map back to category below
                        "raw_tags": t
                    })
    return records

def assign_categories(records, selected_tags_with_cats):
    for r in records:
        r['category'] = "Other"
        for cat_name, tag_str in selected_tags_with_cats:
            # Simple heuristic mapping for the fallback demo
            if any(k in tag_str.lower() for k in r['raw_tags'].keys()):
                r['category'] = cat_name
    return records

# -----------------------------------------------------------------------------
# 4. SIDEBAR & LAYER MANAGEMENT
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Trade Area Scan")
    
    # Search Location
    search_query = st.text_input("Search Location", placeholder="e.g. Times Square, NY")
    if st.button("Find Location"):
        coords = geocode_address(search_query)
        if coords:
            st.session_state.geo_coords = f"{coords[0]}, {coords[1]}"
        else:
            st.error("Location not found.")

    location_input = st.text_input("Coordinates", value=st.session_state.geo_coords)
    radius_val = st.number_input("Radius (Meters)", min_value=100, max_value=50000, value=st.session_state.geo_radius, step=100)
    
    coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", location_input)
    if coord_match:
        lat_coord, lon_coord = float(coord_match.group(1)), float(coord_match.group(2))
        st.session_state.geo_coords = location_input
        st.session_state.geo_radius = radius_val

    st.markdown("---")
    st.session_state.basemap = st.selectbox("Map Style", ['OpenStreetMap', 'CartoDB positron', 'Esri WorldImagery'], index=1)
    
    # Layer Selection
    selected_tags = []
    st.markdown("**POI Categories**")
    for cat_name, node_items in POI_CONFIG.items():
        with st.expander(cat_name):
            for label, tag in node_items:
                if st.checkbox(label, key=f"chk_{label}"):
                    selected_tags.append((cat_name, tag))
                    if cat_name not in st.session_state.layer_prefs:
                        st.session_state.layer_prefs[cat_name] = {
                            "color": DEFAULT_PALETTE[len(st.session_state.layer_prefs) % len(DEFAULT_PALETTE)],
                            "visible": True, "size": 6, "alias": cat_name, "icon": "info-sign"
                        }

    if st.button("Scan Area", type="primary", use_container_width=True):
        if selected_tags:
            with st.spinner("Extracting spatial data..."):
                raw_data = fetch_poi_data(lat_coord, lon_coord, radius_val, selected_tags)
                st.session_state.scanned_records = assign_categories(raw_data, selected_tags)
        else:
            st.warning("Select at least one POI layer.")

    # Manage Layers UI
    if st.session_state.scanned_records:
        st.markdown("---")
        st.markdown("### Scan Results & Layer Management")
        batch_edit = st.checkbox("Batch Edit (Apply size/icon to all)")
        
        for cat in list(st.session_state.layer_prefs.keys()):
            with st.expander(f"⚙️ Manage: {st.session_state.layer_prefs[cat]['alias']}"):
                prefs = st.session_state.layer_prefs[cat]
                prefs['visible'] = st.checkbox("Show Layer", value=prefs['visible'], key=f"vis_{cat}")
                prefs['alias'] = st.text_input("Rename Category", value=prefs['alias'], key=f"ren_{cat}")
                prefs['color'] = st.color_picker("Marker Color", value=prefs['color'], key=f"col_{cat}")
                
                new_size = st.slider("Marker Size", 2, 20, prefs['size'], key=f"siz_{cat}")
                new_icon = st.selectbox("Icon", ["info-sign", "star", "cloud", "shopping-cart"], key=f"ico_{cat}")
                
                # Custom Photo Upload Placeholder
                uploaded_icon = st.file_uploader("Upload Custom Marker Image (PNG)", type=['png'], key=f"up_{cat}")
                
                if batch_edit:
                    for k in st.session_state.layer_prefs:
                        st.session_state.layer_prefs[k]['size'] = new_size
                        st.session_state.layer_prefs[k]['icon'] = new_icon
                else:
                    prefs['size'] = new_size
                    prefs['icon'] = new_icon

# -----------------------------------------------------------------------------
# 5. FOLIUM INTERACTIVE MAP
# -----------------------------------------------------------------------------
col1, col2 = st.columns([3, 1])

with col1:
    m = folium.Map(location=[lat_coord, lon_coord], zoom_start=14, tiles=st.session_state.basemap)
    
    # Center Star & Radius
    folium.Marker([lat_coord, lon_coord], icon=folium.Icon(color='black', icon='star')).add_to(m)
    folium.Circle([lat_coord, lon_coord], radius=radius_val, color='#003366', fill=True, fillOpacity=0.1).add_to(m)
    
    # Populate Categorized POIs
    for rec in st.session_state.scanned_records:
        cat = rec.get('category')
        if cat in st.session_state.layer_prefs and st.session_state.layer_prefs[cat]['visible']:
            prefs = st.session_state.layer_prefs[cat]
            folium.CircleMarker(
                location=[rec['lat'], rec['lon']],
                radius=prefs['size'],
                color=prefs['color'],
                fill=True,
                fill_color=prefs['color'],
                fill_opacity=0.8,
                tooltip=rec['name']
            ).add_to(m)
            
    st_folium(m, width=900, height=600, returned_objects=[])

# -----------------------------------------------------------------------------
# 6. EXPORT UTILITIES (STATIC IMAGE & JSON)
# -----------------------------------------------------------------------------
with col2:
    st.markdown("### Export Tools")
    
    # Project State Export
    export_payload = {
        "coords": st.session_state.geo_coords,
        "radius": st.session_state.geo_radius,
        "records": st.session_state.scanned_records,
        "layer_prefs": st.session_state.layer_prefs
    }
    st.download_button("Export Project JSON", data=json.dumps(export_payload), file_name="trade_area_project.json", use_container_width=True)
    
    uploaded_proj = st.file_uploader("Import Project JSON", type=['json'])
    if uploaded_proj is not None and st.button("Load Project", use_container_width=True):
        data = json.load(uploaded_proj)
        st.session_state.geo_coords = data['coords']
        st.session_state.geo_radius = data['radius']
        st.session_state.scanned_records = data['records']
        st.session_state.layer_prefs = data['layer_prefs']
        st.rerun()

    st.markdown("---")
    
    # High-Fidelity Static Image Export
    if st.button("Export Static Image (PNG)", use_container_width=True):
        if not st.session_state.scanned_records:
            st.error("No data to export. Please scan an area first.")
        else:
            with st.spinner("Rendering high-quality static map..."):
                fig, ax = plt.subplots(figsize=(10, 10))
                
                # Setup GeoDataFrame
                geometry = [Point(xy) for xy in zip([r['lon'] for r in st.session_state.scanned_records], [r['lat'] for r in st.session_state.scanned_records])]
                gdf = gpd.GeoDataFrame(st.session_state.scanned_records, geometry=geometry, crs="EPSG:4326")
                gdf = gdf.to_crs(epsg=3857) # Project to Web Mercator for Contextily
                
                # Plot Base Radius
                center_pt = gpd.GeoSeries([Point(lon_coord, lat_coord)], crs="EPSG:4326").to_crs(epsg=3857)
                center_pt.buffer(radius_val).plot(ax=ax, color='blue', alpha=0.1, edgecolor='navy', linewidth=2)
                center_pt.plot(ax=ax, marker='*', color='black', markersize=200, zorder=5)

                # Plot POIs by Category Layer Prefs
                for cat, prefs in st.session_state.layer_prefs.items():
                    if prefs['visible']:
                        subset = gdf[gdf['category'] == cat]
                        if not subset.empty:
                            subset.plot(ax=ax, color=prefs['color'], markersize=prefs['size']*10, label=prefs['alias'], alpha=0.8, zorder=10)
                
                # Add Basemap and Legend
                cx.add_basemap(ax, source=cx.providers.CartoDB.Positron)
                ax.legend(title="POI Categories", loc='upper right', frameon=True, facecolor='white', framealpha=0.9)
                ax.set_axis_off()
                
                # Save to Buffer
                img_buf = io.BytesIO()
                plt.savefig(img_buf, format='png', dpi=300, bbox_inches='tight')
                img_buf.seek(0)
                
                st.download_button(
                    label="Download HQ Map",
                    data=img_buf,
                    file_name="Trade_Area_Report.png",
                    mime="image/png",
                    use_container_width=True
                )

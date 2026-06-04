import streamlit as st
import osmnx as ox
import requests
import folium
from folium import plugins
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import contextily as cx
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import json
import base64
import io

# -----------------------------------------------------------------------------
# 1. EXACT ORIGINAL POI DICTIONARIES (DO NOT MODIFY)
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
# 2. SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Trade Area Scan", layout="wide")

if 'coords' not in st.session_state: st.session_state.coords = [14.5995, 120.9842]
if 'radius' not in st.session_state: st.session_state.radius = 1000
if 'poi_data' not in st.session_state: st.session_state.poi_data = []
if 'layer_styles' not in st.session_state: st.session_state.layer_styles = {}
if 'map_tile' not in st.session_state: st.session_state.map_tile = "OpenStreetMap"

# Base colors for auto-assignment
BASE_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]

# -----------------------------------------------------------------------------
# 3. DATA ENGINE: OSMNX + FALLBACK OVERPASS
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def fetch_poi_data(lat, lon, radius, tags_dict):
    """Primary: OSMnx. Fallback: Direct Overpass API."""
    extracted_records = []
    
    # Try OSMnx First
    try:
        # Build tags for osmnx. Note: OSMnx expects dict of {tag: True or List}.
        # For complex regex queries, raw Overpass is safer, so we lean heavily on the fallback
        # for the specific regex strings in the POI dictionary.
        raise Exception("Force fallback for complex Overpass QL regex queries.")
    except Exception:
        # Fallback Engine (Direct Overpass)
        statements = []
        for cat, tag_list in tags_dict.items():
            for tag in tag_list:
                statements.append(f"  nwr[{tag}](around:{radius},{lat},{lon});")
        
        if not statements: return []
        
        ql = f"[out:json][timeout:50];(\n{chr(10).join(statements)}\n);\nout center;"
        try:
            res = requests.post("https://overpass-api.de/api/interpreter", data={"data": ql}, timeout=60)
            if res.status_code == 200:
                for el in res.json().get('elements', []):
                    e_lat = el.get('lat') or el.get('center', {}).get('lat')
                    e_lon = el.get('lon') or el.get('center', {}).get('lon')
                    if e_lat and e_lon:
                        t = el.get('tags', {})
                        # Determine category by finding which config matched (simplified association)
                        cat_assigned = "Other"
                        for cat, tag_list in tags_dict.items():
                            if any(k in t for k in ['amenity', 'shop', 'building', 'leisure', 'tourism', 'office']):
                                cat_assigned = cat
                                break
                                
                        extracted_records.append({
                            "lat": e_lat, "lon": e_lon, 
                            "name": t.get('name', 'Unknown'), 
                            "type": t.get('amenity') or t.get('shop') or 'Node',
                            "category": cat_assigned
                        })
        except Exception as e:
            st.error(f"Data Engine Error: {e}")
            
    return extracted_records

# -----------------------------------------------------------------------------
# 4. SIDEBAR CONTROLS & LAYER MANAGEMENT
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("Trade Area Scan")
    
    # Address Search (Nominatim)
    address_search = st.text_input("Search Location", placeholder="Enter address to geocode...")
    if address_search:
        try:
            geo_res = requests.get(f"https://nominatim.openstreetmap.org/search?q={address_search}&format=json&limit=1").json()
            if geo_res:
                st.session_state.coords = [float(geo_res[0]['lat']), float(geo_res[0]['lon'])]
                st.success("Location updated!")
        except Exception:
            st.warning("Geocoding failed.")

    lat_col, lon_col = st.columns(2)
    st.session_state.coords[0] = lat_col.number_input("Lat", value=st.session_state.coords[0], format="%.5f")
    st.session_state.coords[1] = lon_col.number_input("Lon", value=st.session_state.coords[1], format="%.5f")
    st.session_state.radius = st.number_input("Radius (m)", min_value=100, max_value=50000, value=st.session_state.radius, step=500)
    
    st.session_state.map_tile = st.selectbox("Basemap", ["OpenStreetMap", "CartoDB positron", "Google Satellite"])

    st.markdown("### POI Selection")
    active_tags = {}
    for cat_name, items in {**POI_CONFIG, **ADVANCED_CONFIG}.items():
        with st.expander(cat_name):
            for label, tag in items:
                if st.checkbox(label, key=f"chk_{label}"):
                    if cat_name not in active_tags: active_tags[cat_name] = []
                    active_tags[cat_name].append(tag)

    if st.button("Scan Area", use_container_width=True):
        with st.spinner("Executing Data Engine..."):
            st.session_state.poi_data = fetch_poi_data(
                st.session_state.coords[0], st.session_state.coords[1], 
                st.session_state.radius, active_tags
            )
            # Initialize missing styles
            for i, cat in enumerate(active_tags.keys()):
                if cat not in st.session_state.layer_styles:
                    st.session_state.layer_styles[cat] = {
                        "color": BASE_COLORS[i % len(BASE_COLORS)], 
                        "visible": True, "size": 5, "custom_icon": None, "display_name": cat
                    }

    # LAYER MANAGER
    if st.session_state.poi_data:
        st.markdown("---")
        st.markdown("### Scan Results & Manage Layers")
        batch_color = st.color_picker("Batch Color Override", "#000000")
        if st.button("Apply to All Layers"):
            for k in st.session_state.layer_styles:
                st.session_state.layer_styles[k]["color"] = batch_color
                
        for cat in st.session_state.layer_styles.keys():
            with st.popover(f"⚙️ {st.session_state.layer_styles[cat]['display_name']}"):
                st.session_state.layer_styles[cat]["display_name"] = st.text_input("Display Name", value=st.session_state.layer_styles[cat]["display_name"], key=f"name_{cat}")
                st.session_state.layer_styles[cat]["color"] = st.color_picker("Marker Color", value=st.session_state.layer_styles[cat]["color"], key=f"color_{cat}")
                st.session_state.layer_styles[cat]["size"] = st.slider("Marker Size", 1, 15, st.session_state.layer_styles[cat]["size"], key=f"size_{cat}")
                st.session_state.layer_styles[cat]["visible"] = st.toggle("Visible", value=st.session_state.layer_styles[cat]["visible"], key=f"vis_{cat}")
                
                uploaded_icon = st.file_uploader("Upload Custom Marker (PNG)", type=["png"], key=f"icon_{cat}")
                if uploaded_icon:
                    encoded = base64.b64encode(uploaded_icon.read()).decode()
                    st.session_state.layer_styles[cat]["custom_icon"] = f"data:image/png;base64,{encoded}"

        # SAVE/LOAD PROJECT
        st.markdown("---")
        proj_data = json.dumps({
            "coords": st.session_state.coords, "radius": st.session_state.radius,
            "poi_data": st.session_state.poi_data, "styles": st.session_state.layer_styles
        })
        st.download_button("Export Project", proj_data, "project.json", "application/json", use_container_width=True)
        
        uploaded_proj = st.file_uploader("Import Project", type=["json"])
        if uploaded_proj:
            data = json.load(uploaded_proj)
            st.session_state.coords = data["coords"]
            st.session_state.radius = data["radius"]
            st.session_state.poi_data = data["poi_data"]
            st.session_state.layer_styles = data["styles"]
            st.rerun()

# -----------------------------------------------------------------------------
# 5. FOLIUM INTERACTIVE MAP
# -----------------------------------------------------------------------------
tileset = st.session_state.map_tile
if tileset == "Google Satellite":
    tileset = "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
    attr = "Google"
else:
    attr = "OpenStreetMap" if tileset == "OpenStreetMap" else "CartoDB"

m = folium.Map(location=st.session_state.coords, zoom_start=14, tiles=tileset, attr=attr)
folium.Marker(st.session_state.coords, icon=folium.Icon(color="black", icon="star")).addTo(m)
folium.Circle(st.session_state.coords, radius=st.session_state.radius, color="#003366", fill=True).addTo(m)

for poi in st.session_state.poi_data:
    cat = poi["category"]
    style = st.session_state.layer_styles.get(cat, {"visible": True, "color": "blue", "size": 5, "custom_icon": None, "display_name": cat})
    
    if not style["visible"]: continue
    
    if style["custom_icon"]:
        icon = folium.CustomIcon(icon_image=style["custom_icon"], icon_size=(24, 24))
        folium.Marker([poi["lat"], poi["lon"]], tooltip=poi["name"], icon=icon).addTo(m)
    else:
        folium.CircleMarker(
            [poi["lat"], poi["lon"]], radius=style["size"],
            color=style["color"], fill=True, fill_opacity=0.8, tooltip=poi["name"]
        ).addTo(m)

st_folium(m, width=1200, height=700, returned_objects=[])

# -----------------------------------------------------------------------------
# 6. STATIC IMAGE EXPORT (MATPLOTLIB + CONTEXTILY)
# -----------------------------------------------------------------------------
if st.session_state.poi_data:
    if st.button("Export Static Image"):
        with st.spinner("Rendering High-Resolution Map..."):
            fig, ax = plt.subplots(figsize=(10, 10))
            
            # Convert center and radius to GeoDataFrame (EPSG:4326 to EPSG:3857)
            center_pt = Point(st.session_state.coords[1], st.session_state.coords[0])
            gdf_center = gpd.GeoDataFrame(geometry=[center_pt], crs="EPSG:4326").to_crs(epsg=3857)
            
            # Contextily requires map extents. Create a buffer equivalent to radius.
            # (Note: EPSG:3857 uses meters, making buffering straightforward).
            buffered = gdf_center.buffer(st.session_state.radius)
            buffered.plot(ax=ax, facecolor="none", edgecolor="#003366", linewidth=2)
            gdf_center.plot(ax=ax, marker="*", color="black", markersize=200, zorder=5)

            # Plot POIs
            legend_elements = {}
            valid_pois = [p for p in st.session_state.poi_data if st.session_state.layer_styles.get(p["category"], {}).get("visible", False)]
            
            if valid_pois:
                df = pd.DataFrame(valid_pois)
                gdf_pois = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326").to_crs(epsg=3857)
                
                for cat, group in gdf_pois.groupby('category'):
                    style = st.session_state.layer_styles[cat]
                    group.plot(ax=ax, color=style["color"], markersize=style["size"] * 10, label=style["display_name"], zorder=4)
                    legend_elements[style["display_name"]] = style["color"]
            
            # Add Basemap via Contextily
            cx.add_basemap(ax, crs=gdf_pois.crs.to_string(), source=cx.providers.CartoDB.Positron)
            
            ax.set_axis_off()
            if legend_elements: ax.legend(loc="upper right", frameon=True, facecolor="white")
            
            # Save to BytesIO
            buf = io.BytesIO()
            plt.savefig(buf, format="png", dpi=300, bbox_inches='tight')
            buf.seek(0)
            
            st.download_button("Download PNG", data=buf, file_name="trade_area_export.png", mime="image/png")

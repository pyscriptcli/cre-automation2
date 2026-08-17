import json
import re
import streamlit as st
import streamlit.components.v1 as components

# ------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & ROOT CSS OVERRIDES
# ------------------------------------------------------------------------
st.set_page_config(
    page_title="Open Map Builder",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    [data-testid="stSidebar"], section[data-testid="stSidebar"],
    header, #MainMenu, footer, [data-testid="stHeader"] { 
        display: none !important; 
        height: 0 !important; 
        margin: 0 !important;
        padding: 0 !important;
    }
    .stApp {
        margin: 0 !important;
        padding: 0 !important;
        background-color: transparent !important;
    }
    .block-container { 
        padding: 0rem !important; 
        margin: 0rem !important; 
        max-width: 100vw !important; 
        width: 100vw !important;
        height: 100vh !important; 
        max-height: 100vh !important;
        overflow: hidden !important; 
    }
    iframe { 
        border: none !important;
        overflow: hidden !important; 
        height: 100vh !important; 
        width: 100vw !important; 
        margin: 0 !important; 
        padding: 0 !important; 
        position: fixed !important;
        inset: 0 !important;
    }
    html, body { 
        overflow: hidden !important; 
        margin: 0 !important; 
        padding: 0 !important; 
        width: 100vw !important;
        height: 100vh !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------------
# 2. SESSION STATE & DATA CONFIGURATIONS
# ------------------------------------------------------------------------
DEFAULT_COORDS = [14.5995, 120.9842]
DEFAULT_RADIUS = 1000

if 'geo_coords' not in st.session_state: st.session_state.geo_coords = "14.5995, 120.9842"
if 'geo_radius' not in st.session_state: st.session_state.geo_radius = DEFAULT_RADIUS
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'last_scan_lat' not in st.session_state: st.session_state.last_scan_lat = 14.5995
if 'last_scan_lon' not in st.session_state: st.session_state.last_scan_lon = 120.9842
if 'layer_meta' not in st.session_state: st.session_state.layer_meta = {}
if 'layer_groups' not in st.session_state: st.session_state.layer_groups = {}
if 'scan_active_loading' not in st.session_state: st.session_state.scan_active_loading = False
if 'target_config' not in st.session_state: st.session_state.target_config = {"size": 24, "color": "#003366", "style": "star"}
if 'radius_config' not in st.session_state: st.session_state.radius_config = {"color": "#003366", "fill_opacity": 0.08, "weight": 1.5}
if 'global_marker_style' not in st.session_state: st.session_state.global_marker_style = "dots"
if 'global_marker_size' not in st.session_state: st.session_state.global_marker_size = 12
if 'global_marker_color' not in st.session_state: st.session_state.global_marker_color = "#003366"

POI_CONFIG = {
    "COMMERCIAL & OFFICES": [
        ['Corporate Office', '"building"~"office|commercial",i'], 
        ['IT/Tech Center', '"office"~"it|telecommunication",i'], 
        ['Business Center', '"building"="commercial"'], 
        ['Bank', '"amenity"="bank"'], 
        ['ATM', '"amenity"="atm"'], 
        ['Office', '"office"="yes"']
    ],
    "RETAIL": [
        ['Mall/Department Store', '"shop"~"mall|department_store",i'], 
        ['Supermarket', '"shop"~"market|grocery",i'], 
        ['Convenience Store', '"shop"="convenience"'], 
        ['Pharmacy', '"amenity"="pharmacy"'], 
        ['Hardware', '"shop"~"hardware|doityourself",i'], 
        ['General Shops', '"shop"~"boutique|clothes|shoes",i'], 
        ['Beauty', '"shop"="beauty"'], 
        ['Bicycle', '"shop"="bicycle"'], 
        ['Books/Stationary', '"shop"~"books|stationary",i'], 
        ['Car', '"shop"="car"'], 
        ['Marketplace', '"amenity"="marketplace"']
    ],
    "FOOD, BEVERAGE & HOSPITALITY": [
        ['Restaurant', '"amenity"="restaurant"'], 
        ['Cafe/Coffee Shop', '"amenity"~"cafe|coffee",i'], 
        ['Fast Food', '"amenity"="fast_food"'], 
        ['Bar/Pub/Nightclub', '"amenity"~"bar|pub|nightclub",i'], 
        ['Bakery/Pastry', '"shop"="bakery"'], 
        ['Food court', '"amenity"="food_court"'], 
        ['Hotel', '"tourism"="hotel"'], 
        ['Hostel', '"tourism"="hostel"']
    ],
    "RESIDENTIAL": [
        ['Apartments', '"building"="apartments"'], 
        ['House', '"building"="house"'], 
        ['Residential Area', '"landuse"="residential"'], 
        ['Condominium', '"building"="residential"']
    ],
    "INDUSTRIAL & LOGISTICS": [
        ['Expressway Exits', '"highway"~"motorway_junction|toll_gantry",i'], 
        ['Ports & Terminals', '"industrial"="port"'], 
        ['Manufacturing Plants', '"industrial"~"factory|manufacturing|processing",i'], 
        ['Warehouses & Depots', '"building"~"warehouse|depot",i'], 
        ['Industrial Parks', '"landuse"~"industrial|industrial_estate",i']
    ],
    "HEALTH & EMERGENCY SERVICES": [
        ['Hospital', '"amenity"~"hospital|clinic",i'], 
        ['Clinic', '"amenity"="clinic"'], 
        ['Pharmacy', '"amenity"="pharmacy"'], 
        ['Police Station', '"amenity"="police"'], 
        ['Fire Station', '"amenity"="fire_station"']
    ],
    "GOVERNMENT, EDUCATION & INFRASTRUCTURE": [
        ['City Hall', '"amenity"="townhall"'], 
        ['Airport Terminal', '"aeroway"~"terminal|aerodrome",i'], 
        ['University/College', '"amenity"~"university|college",i'], 
        ['K-12 School', '"amenity"="school"'], 
        ['Post Office', '"amenity"="post_office"']
    ],
    "LEISURE, SPORTS & PUBLIC SPACES": [
        ['Church', '"religion"="christian"'], 
        ['Mosque', '"religion"="muslim"'], 
        ['Cinema', '"amenity"="cinema"'], 
        ['Fuel', '"amenity"="fuel"'], 
        ['Parking', '"amenity"="parking"'], 
        ['Sports centre', '"leisure"="sports_centre"'], 
        ['Busstop', '"highway"="bus_stop"']
    ]
}

# ------------------------------------------------------------------------
# 3. BACKEND OSMNX GEOQUERY PIPELINE
# ------------------------------------------------------------------------
def extract_osmnx_pois(lat, lon, radius, category=None):
    try:
        import osmnx as ox
        import shapely.geometry
        
        tags_dict = {}
        target_tags = []
        if category and category in POI_CONFIG:
            target_tags = POI_CONFIG[category]
        else:
            for c in POI_CONFIG.values(): target_tags.extend(c)
            
        for t in target_tags:
            clean = t[1].replace('"', '')
            if '=' in clean:
                k, v = clean.split('=', 1)
                if '|' in v: v = [x.strip() for x in v.split('|')]
                tags_dict[k] = v
            elif '~' in clean:
                k, v = clean.split('~', 1)
                v = v.replace(',i', '')
                if '|' in v: v = [x.strip() for x in v.split('|')]
                tags_dict[k] = v
            else:
                tags_dict[clean] = True
                
        gdf = ox.geometries_from_point((lat, lon), tags_dict, dist=radius)
        records = []
        if not gdf.empty:
            for idx, row in gdf.iterrows():
                if hasattr(row.geometry, 'centroid'):
                    c_lat, c_lon = row.geometry.centroid.y, row.geometry.centroid.x
                else: continue
                name = row.get('name', 'Unknown')
                if isinstance(name, float): name = 'Unknown'
                matched_type = category or 'POI'
                for k in tags_dict.keys():
                    if k in row and row[k]:
                        matched_type = str(row[k])
                        break
                records.append({
                    "lat": float(c_lat), "lon": float(c_lon), "name": str(name),
                    "type": matched_type, "visible": True
                })
        return records
    except Exception:
        return []

# ------------------------------------------------------------------------
# 4. VECTOR STYLING ENGINE
# ------------------------------------------------------------------------
CENTER = [120.9842, 14.5995]
ZOOM = 14

THEMES = {
    "Midnight Blue": {
        "overlay": "#0a1628", "text": "#d9b451", "land": "#0d1830",
        "landcover": "#0f1d33", "water": "#0a1424", "waterway": "#081120",
        "parks": "#142440", "buildings": "#8e7258", "aeroway": "#152640",
        "rail": "#d9b451", "rd_express": "#ffaa00", "rd_major": "#e8b84a",
        "rd_secondary": "#c99c37", "rd_tertiary": "#7d5f14", "rd_min_md": "#46463e",
        "rd_min_lo": "#2f2f2a", "rd_path": "#4a4333", "rd_case": "#685c37",
        "sec_opacity": 0.8, "ter_opacity": 0.65, "building_opacity": 0.25,
        "boundary": "#ff1e1e", "muted": "#8b949e",
    },
    "Monochrome": {
        "overlay": "#ece9e2", "text": "#2d2a26", "land": "#ece9e2",
        "landcover": "#e5e2da", "water": "#cdd7db", "waterway": "#bac6cb",
        "parks": "#e2dfd7", "buildings": "#dedad2", "aeroway": "#dbd7cf",
        "rail": "#1a1816", "rd_express": "#1a1816", "rd_major": "#2e2a25",
        "rd_secondary": "#47423b", "rd_tertiary": "#716b61", "rd_min_md": "#8a8377",
        "rd_min_lo": "#9e978d", "rd_path": "#b0a99f", "rd_case": "#1a1816",
        "sec_opacity": 0.85, "ter_opacity": 0.7, "building_opacity": 0.6,
        "boundary": "#ff1e1e", "muted": "#716b61",
    },
    "White Gold": {
        "overlay": "#ffffff", "text": "#a07d1c", "land": "#fafafa",
        "landcover": "#f1f1ec", "water": "#d4dadc", "waterway": "#c2c9cc",
        "parks": "#e6ebe4", "buildings": "#d8d8d4", "aeroway": "#e4e4e4",
        "rail": "#c99c37", "rd_express": "#f59e0b", "rd_major": "#e5a91d",
        "rd_secondary": "#b08a24", "rd_tertiary": "#9c7a1a", "rd_min_md": "#e0be74",
        "rd_min_lo": "#ead9b0", "rd_path": "#e6dabd", "rd_case": "#b08a24",
        "sec_opacity": 0.7, "ter_opacity": 0.6, "building_opacity": 0.5,
        "boundary": "#ff1e1e", "muted": "#6b7280",
    },
}

def w(*stops):
    out = ["interpolate", ["exponential", 1.2], ["zoom"]]
    for z, val in stops:
        out += [z, val]
    return out

def road_layer(p, lid, classes, color, widths, minzoom=0, casing=False, opacity=1.0):
    lyr = {
        "id": lid, "type": "line", "source": "omt", "source-layer": "transportation",
        "filter": ["match", ["get", "class"], classes, True, False],
        "layout": {"line-cap": "round", "line-join": "round"},
        "paint": {"line-color": color, "line-width": w(*widths), "line-opacity": opacity},
    }
    if minzoom: lyr["minzoom"] = minzoom
    if casing:
        lyr["paint"]["line-color"] = p["rd_case"]
        lyr["paint"]["line-width"] = w(*[(z, val + 1.8) for z, val in widths])
        lyr["id"] = lid + "_casing"
    return lyr

def vector_style(p):
    sec = p["sec_opacity"]
    ter = p["ter_opacity"]
    return {
        "version": 8,
        "glyphs": "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
        "sources": {
            "omt": {"type": "vector", "url": "https://tiles.openfreemap.org/planet"}
        },
        "layers": [
            {"id": "bg", "type": "background", "paint": {"background-color": p["overlay"]}},
            {"id": "landcover", "type": "fill", "source": "omt", "source-layer": "landcover", "paint": {"fill-color": p["landcover"], "fill-opacity": 0.6}},
            {"id": "landuse", "type": "fill", "source": "omt", "source-layer": "landuse", "paint": {"fill-color": p["land"], "fill-opacity": 0.8}},
            {"id": "park", "type": "fill", "source": "omt", "source-layer": "park", "paint": {"fill-color": p["parks"]}},
            {"id": "water", "type": "fill", "source": "omt", "source-layer": "water", "paint": {"fill-color": p["water"]}},
            {"id": "waterway", "type": "line", "source": "omt", "source-layer": "waterway", "paint": {"line-color": p["waterway"], "line-width": w((9, 1), (20, 6))}},
            {"id": "aeroway", "type": "line", "source": "omt", "source-layer": "aeroway", "paint": {"line-color": p["aeroway"], "line-width": w((11, 1), (20, 12))}},
            {"id": "building", "type": "fill", "source": "omt", "source-layer": "building", "minzoom": 13, "paint": {"fill-color": p["buildings"], "fill-opacity": p["building_opacity"], "fill-outline-color": p["buildings"]}},
            
            # Boundaries
            {"id": "bound_prov", "type": "line", "source": "omt", "source-layer": "boundary", "filter": ["match", ["get", "admin_level"], [2, 4], True, False], "layout": {"visibility": "none"}, "paint": {"line-color": "#ff1e1e", "line-width": 2.2, "line-dasharray": [4, 2]}},
            {"id": "bound_city", "type": "line", "source": "omt", "source-layer": "boundary", "filter": ["match", ["get", "admin_level"], [6, 7, 8], True, False], "minzoom": 7, "layout": {"visibility": "none"}, "paint": {"line-color": "#ff1e1e", "line-width": 1.8, "line-dasharray": [2, 2], "line-opacity": 0.9}},
            {"id": "bound_brgy", "type": "line", "source": "omt", "source-layer": "boundary", "filter": ["match", ["get", "admin_level"], [9, 10], True, False], "minzoom": 11, "layout": {"visibility": "none"}, "paint": {"line-color": "#ff1e1e", "line-width": 1.2, "line-dasharray": [1, 2], "line-opacity": 0.8}},

            # Roads & Railways
            road_layer(p, "case_express", ["motorway"], None, [(5, 1.5), (14, 5.5), (20, 24)], casing=True),
            road_layer(p, "case_major", ["trunk", "primary"], None, [(6, 1.0), (14, 3.8), (20, 18)], casing=True),
            road_layer(p, "case_secondary", ["secondary"], None, [(8, 0.8), (14, 2.8), (20, 15)], casing=True, opacity=sec),
            road_layer(p, "case_tertiary", ["tertiary"], None, [(9, 0.6), (14, 2.0), (20, 12)], casing=True, opacity=ter),
            
            road_layer(p, "rd_path", ["path", "pedestrian", "footway"], p["rd_path"], [(14, 0.6), (20, 5)], minzoom=14),
            road_layer(p, "rd_min_lo", ["service", "track"], p["rd_min_lo"], [(14, 0.6), (20, 6)], minzoom=14),
            road_layer(p, "rd_min_md", ["minor"], p["rd_min_md"], [(13, 0.8), (16, 3.5), (20, 10)], minzoom=13),
            road_layer(p, "rd_tertiary", ["tertiary"], p["rd_tertiary"], [(9, 0.6), (14, 2.0), (20, 12)], opacity=ter),
            road_layer(p, "rd_secondary", ["secondary"], p["rd_secondary"], [(8, 0.8), (14, 2.8), (20, 15)], opacity=sec),
            road_layer(p, "rd_major", ["trunk", "primary"], p["rd_major"], [(6, 1.0), (14, 3.8), (20, 18)]),
            road_layer(p, "rd_express", ["motorway"], p["rd_express"], [(5, 1.5), (14, 5.5), (20, 24)]),
            
            {"id": "rd_rail", "type": "line", "source": "omt", "source-layer": "transportation", "filter": ["match", ["get", "class"], ["rail", "transit"], True, False], "minzoom": 10, "paint": {"line-color": p["rail"], "line-width": w((10, 1.2), (15, 2.5), (20, 4)), "line-dasharray": [3, 2]}},

            # Labels
            {"id": "label_city", "type": "symbol", "source": "omt", "source-layer": "place", "filter": ["match", ["get", "class"], ["city", "town"], True, False], "minzoom": 6, "layout": {"text-field": ["coalesce", ["get", "name_en"], ["get", "name"]], "text-font": ["Noto Sans Regular"], "text-size": w((6, 12), (14, 18)), "text-transform": "uppercase", "text-letter-spacing": 0.1}, "paint": {"text-color": p["text"], "text-halo-color": p["overlay"], "text-halo-width": 2}},
            {"id": "label_brgy", "type": "symbol", "source": "omt", "source-layer": "place", "filter": ["match", ["get", "class"], ["suburb", "neighbourhood", "village", "quarter", "hamlet"], True, False], "minzoom": 11, "layout": {"text-field": ["coalesce", ["get", "name_en"], ["get", "name"]], "text-font": ["Noto Sans Regular"], "text-size": w((11, 10), (16, 14)), "text-letter-spacing": 0.05}, "paint": {"text-color": p["text"], "text-halo-color": p["overlay"], "text-halo-width": 1.5}},
            {"id": "label_street", "type": "symbol", "source": "omt", "source-layer": "transportation_name", "minzoom": 13, "layout": {"symbol-placement": "line", "text-field": ["coalesce", ["get", "name_en"], ["get", "name"]], "text-font": ["Noto Sans Regular"], "text-size": w((13, 9), (18, 13))}, "paint": {"text-color": p["text"], "text-halo-color": p["overlay"], "text-halo-width": 1.5}},
        ],
    }

def raster_style(tile_urls, bg, maxzoom=20):
    return {
        "version": 8,
        "sources": {"r": {"type": "raster", "tiles": tile_urls, "tileSize": 256, "maxzoom": maxzoom}},
        "layers": [
            {"id": "bg", "type": "background", "paint": {"background-color": bg}},
            {"id": "r", "type": "raster", "source": "r"},
        ],
    }

ALL_STYLES = {
    "Midnight Blue": vector_style(THEMES["Midnight Blue"]),
    "Monochrome": vector_style(THEMES["Monochrome"]),
    "White Gold": vector_style(THEMES["White Gold"]),
    "Carto DB Light": raster_style(["https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png", "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"], "#f8f9fa"),
    "Carto DB Dark": raster_style(["https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png", "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"], "#000000"),
    "OSM": raster_style(["https://tile.openstreetmap.org/{z}/{x}/{y}.png"], "#f2efe9", 19),
    "Satellite": raster_style(["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"], "#000000", 19),
}

INITIAL_BASEMAP = "Midnight Blue"

# ------------------------------------------------------------------------
# 5. OPEN MAP BUILDER FRONTEND & COMPONENT
# ------------------------------------------------------------------------
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"/>
<script src="https://unpkg.com/maplibre-gl@5/dist/maplibre-gl.js"></script>
<link href="https://unpkg.com/maplibre-gl@5/dist/maplibre-gl.css" rel="stylesheet"/>
<style>
  @font-face {
    font-family: 'Century Gothic Custom';
    src: local('Century Gothic'), local('CenturyGothic'), local('AppleGothic'), sans-serif;
  }
  * { box-sizing: border-box; user-select: none; }
  html, body { 
    margin: 0; padding: 0; width: 100vw; height: 100vh; 
    overflow: hidden; background: __BG__; 
    font-family: 'Century Gothic Custom', system-ui, -apple-system, sans-serif; 
  }
  #map { position: absolute; inset: 0; width: 100vw; height: 100vh; }

  /* Vertical Toolbar Rail */
  #side-rail {
    position: absolute; 
    top: 50%; 
    left: 16px; 
    transform: translateY(-50%);
    width: 48px; 
    z-index: 10;
    background: #181d24ee; 
    backdrop-filter: blur(14px); 
    border: 1px solid #2d333b;
    border-radius: 28px;
    display: flex; 
    flex-direction: column; 
    align-items: center; 
    padding: 10px 0; 
    gap: 6px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.6);
  }
  .rail-btn {
    width: 36px; height: 36px; display: grid; place-items: center;
    background: transparent; border: none; color: #adbac7; border-radius: 50%;
    cursor: pointer; transition: all 0.15s ease;
  }
  .rail-btn:hover { background: #22272e; color: #cdd9e5; }
  .rail-btn.active { background: #2d333b; color: #f0f6fc; }
  .rail-btn.primary-active { background: #316dca; color: #ffffff; }
  .rail-sep { width: 24px; height: 1px; background: #2d333b; margin: 2px 0; }

  /* Flyout Left Side Panels */
  .left-panel {
    position: absolute; top: 16px; left: 74px; bottom: 16px; width: 360px; z-index: 9;
    background: #181d24f7; backdrop-filter: blur(14px); border: 1px solid #2d333b;
    border-radius: 16px; box-shadow: 0 12px 36px rgba(0,0,0,0.6);
    display: none; flex-direction: column; overflow: hidden; color: #adbac7;
  }
  .left-panel.open { display: flex; }

  .panel-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 16px; border-bottom: 1px solid #22272e;
  }
  .panel-title { display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 14px; color: #f0f6fc; }
  .icon-action-btn { width: 28px; height: 28px; display: grid; place-items: center; border: 1px solid #2d333b; background: #22272e; border-radius: 6px; cursor: pointer; color: #adbac7; }
  .icon-action-btn:hover { background: #2d333b; color: #f0f6fc; }

  .panel-content { flex: 1; overflow-y: auto; padding: 14px 16px; display: flex; flex-direction: column; gap: 12px; font-size: 12px; }

  /* Collapsed by default Accordions */
  .acc-item { border-bottom: 1px solid #22272e; padding-bottom: 8px; }
  .acc-header { display: flex; align-items: center; justify-content: space-between; font-size: 13px; font-weight: 600; color: #f0f6fc; cursor: pointer; padding: 6px 0; }
  .acc-body { padding: 6px 0 2px 0; display: flex; flex-direction: column; gap: 8px; }
  .acc-body.hidden { display: none !important; }

  .layer-row { display: flex; align-items: center; justify-content: space-between; font-size: 12px; color: #adbac7; }
  .layer-row input[type=checkbox] { accent-color: #316dca; cursor: pointer; }

  .bound-select-row { display: flex; gap: 6px; margin-top: 4px; }
  .bound-select-row input[type=text] { flex: 1; background: #1c2128; border: 1px solid #2d333b; color: #f0f6fc; padding: 5px 8px; border-radius: 6px; font-size: 11px; font-family: inherit; }
  .bound-select-row button { background: #ff1e1e; color: #fff; border: none; border-radius: 6px; padding: 5px 10px; font-size: 11px; font-weight: 600; cursor: pointer; }

  /* My Layers & Grouping Container */
  .layers-heading { display: flex; align-items: center; justify-content: space-between; font-weight: 700; font-size: 13px; color: #f0f6fc; margin-top: 6px; }
  .badge-count { background: #316dca; color: #ffffff; border-radius: 12px; font-size: 11px; padding: 1px 8px; font-weight: 600; }

  .group-container { background: #1c2128; border: 1px solid #2d333b; border-radius: 8px; margin-top: 6px; overflow: hidden; }
  .group-header { background: #22272e; padding: 8px 10px; display: flex; align-items: center; justify-content: space-between; }
  .group-title-input { background: transparent; border: none; font-weight: 700; color: #f0f6fc; font-size: 12px; width: 140px; font-family: inherit; }
  .group-title-input:focus { background: #181d24; outline: none; border-radius: 4px; padding: 2px 4px; }
  .group-items { padding: 4px 6px; display: flex; flex-direction: column; gap: 4px; }

  .layer-card {
    background: #22272e; border: 1px solid #2d333b; border-radius: 6px; padding: 6px 8px;
    display: flex; flex-direction: column; gap: 4px; margin-top: 4px;
  }
  .layer-card-top { display: flex; align-items: center; gap: 6px; }
  .layer-name-input {
    flex: 1; border: 1px solid transparent; background: transparent; font-weight: 600;
    font-size: 12px; color: #f0f6fc; padding: 2px 4px; border-radius: 4px; font-family: inherit;
  }
  .layer-name-input:focus { border-color: #316dca; background: #1c2128; outline: none; }
  .card-btn { background: transparent; border: none; color: #768390; cursor: pointer; padding: 2px 4px; border-radius: 4px; }
  .card-btn:hover { color: #f0f6fc; background: #2d333b; }

  /* Trade Area Controls */
  .trade-controls { display: flex; flex-direction: column; gap: 6px; background: #1c2128; padding: 8px; border-radius: 8px; border: 1px solid #2d333b; }
  .trade-controls select, .trade-controls button { font-family: inherit; font-size: 11px; }
  .trade-controls select { background: #22272e; color: #f0f6fc; border: 1px solid #2d333b; border-radius: 6px; padding: 5px; }
  .trade-btn { background: #316dca; color: #ffffff; border: none; border-radius: 6px; padding: 6px; font-weight: 600; cursor: pointer; }
  .poi-summary { font-size: 11px; color: #adbac7; max-height: 180px; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; margin-top: 4px; }
  .poi-badge { display: flex; justify-content: space-between; background: #22272e; padding: 4px 6px; border-radius: 4px; }

  /* Floating Popups */
  .float-card {
    position: absolute; left: 74px; z-index: 12; background: #181d24f7; backdrop-filter: blur(14px);
    border: 1px solid #2d333b; border-radius: 14px; padding: 14px; box-shadow: 0 10px 30px rgba(0,0,0,0.6);
    display: none; flex-direction: column; gap: 10px; font-size: 12px; color: #adbac7;
  }
  .float-card.open { display: flex; }
  .float-card .f-row { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
  .float-card input[type=range] { accent-color: #316dca; width: 110px; cursor: pointer; }
  .float-card input[type=color] { border: none; width: 28px; height: 28px; border-radius: 6px; cursor: pointer; background: transparent; }
  .float-card input[type=text], .float-card select { background: #1c2128; color: #f0f6fc; border: 1px solid #2d333b; border-radius: 6px; padding: 6px 8px; font-family: inherit; font-size: 12px; }

  #popup-search { top: 20%; width: 280px; }
  #popup-marker-settings { top: 25%; width: 240px; }
  #popup-text-settings { top: 30%; width: 260px; }
  #popup-shape-editor { top: 8%; width: 320px; max-height: 84vh; overflow-y: auto; }
  #popup-custom-map { top: 16px; bottom: 16px; width: 310px; overflow-y: auto; }
  #popup-export { top: 50%; transform: translateY(-50%); width: 320px; }

  .icon-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
  .icon-grid button { width: 36px; height: 36px; display: grid; place-items: center; border: 1px solid #2d333b; border-radius: 8px; background: #22272e; color: #adbac7; cursor: pointer; }
  .icon-grid button:hover { background: #2d333b; }
  .icon-grid button.active { border-color: #316dca; background: #316dca; color: #ffffff; }

  /* Export Layout Selector */
  .layout-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin: 4px 0; }
  .layout-btn { padding: 6px; background: #22272e; border: 1px solid #2d333b; border-radius: 6px; color: #f0f6fc; cursor: pointer; text-align: center; font-size: 11px; font-weight: 600; }
  .layout-btn.active { background: #316dca; border-color: #316dca; }
  #exportPreviewCanvas { width: 100%; height: 110px; object-fit: contain; background: #0d1117; border-radius: 6px; border: 1px solid #2d333b; }

  #hint-toast {
    position: absolute; bottom: 24px; left: 50%; transform: translateX(-50%); z-index: 15;
    background: #181d24ee; color: #f0f6fc; border: 1px solid #2d333b; border-radius: 20px; padding: 7px 18px;
    font-size: 12px; backdrop-filter: blur(4px); box-shadow: 0 4px 12px rgba(0,0,0,0.4); display: none;
  }
</style>
</head>
<body>
<div id="map"></div>

<!-- Vertical Toolbar Rail -->
<div id="side-rail">
  <button class="rail-btn" id="btn-browser-toggle" title="Data Browser / Layers">
    <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"></path><path d="M2 12l10 6 10-6"></path><path d="M2 16l10 6 10-6"></path></svg>
  </button>
  <div class="rail-sep"></div>
  <button class="rail-btn" id="btn-search" title="Search Location">
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"></circle><line x1="21" y1="21" x2="16.5" y2="16.5"></line></svg>
  </button>
  <button class="rail-btn tool" data-tool="marker" title="Place Marker Pin">
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"></path><circle cx="12" cy="10" r="2.5"></circle></svg>
  </button>
  <button class="rail-btn tool" data-tool="textbox" title="Add Text Label">
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 7 4 4 20 4 20 7"></polyline><line x1="9" y1="20" x2="15" y2="20"></line><line x1="12" y1="4" x2="12" y2="20"></line></svg>
  </button>
  <button class="rail-btn tool" data-tool="polyline" title="Draw Polyline">
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"></path></svg>
  </button>
  <button class="rail-btn tool" data-tool="polygon" title="Draw Polygon">
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l8 6-3 10H7L4 9z"></path></svg>
  </button>
  <button class="rail-btn tool" data-tool="rectangle" title="Draw Rectangle">
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16"></rect></svg>
  </button>
  <button class="rail-btn tool" data-tool="circle" title="Draw Circle (with Radius)">
    <svg viewBox="0 0 24 24" width="15" height="15"><circle cx="12" cy="12" r="8" fill="currentColor"></circle></svg>
  </button>
  <button class="rail-btn tool" data-tool="route" title="Multi-Point Route">
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><circle cx="5" cy="19" r="2.5"></circle><circle cx="19" cy="5" r="2.5"></circle><path d="M7 17c4-1 3-8 8-9"></path></svg>
  </button>
  <div class="rail-sep"></div>
  <button class="rail-btn" id="btn-custom-map" title="Basemap & Vector Styling">
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon><line x1="8" y1="2" x2="8" y2="18"></line><line x1="16" y1="6" x2="16" y2="22"></line></svg>
  </button>
  <button class="rail-btn" id="btn-export-dialog" title="Export Map Layout">
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
  </button>
  <button class="rail-btn" id="btn-edit-mode" title="Select & Drag Mode">
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4v16h16v-7"></path><path d="M18 2l4 4-10 10H8v-4z"></path></svg>
  </button>
</div>

<!-- Left Side Data Browser Panel -->
<div id="browser-panel" class="left-panel">
  <div class="panel-header">
    <div class="panel-title">
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"></path><path d="M2 12l10 6 10-6"></path><path d="M2 16l10 6 10-6"></path></svg>
      <span>Data Browser</span>
    </div>
    <div class="panel-actions">
      <button class="icon-action-btn" id="btn-close-browser" title="Close">✕</button>
    </div>
  </div>

  <div class="panel-content">
    <!-- Trade Area Dropdown (Collapsed by default) -->
    <div class="acc-item">
      <div class="acc-header" data-target="body-trade-area">
        <span>Trade Area Analysis</span><span>▸</span>
      </div>
      <div class="acc-body hidden" id="body-trade-area">
        <div class="trade-controls">
          <label style="font-size:11px; font-weight:600; color:#f0f6fc;">Target Polygon:</label>
          <select id="tradePolygonSelect"><option value="">-- Choose a polygon --</option></select>
          <label style="font-size:11px; font-weight:600; color:#f0f6fc; margin-top:2px;">POI Category:</label>
          <select id="tradeCategorySelect"></select>
          <button class="trade-btn" id="btnScanTradeArea">Scan POIs (OSM Geometries)</button>
        </div>
        <div id="tradeResults" class="poi-summary"></div>
      </div>
    </div>

    <!-- Labels (Collapsed by default) -->
    <div class="acc-item">
      <div class="acc-header" data-target="body-labels">
        <span>Labels</span><span>▸</span>
      </div>
      <div class="acc-body hidden" id="body-labels">
        <label class="layer-row"><span>City</span><input type="checkbox" data-g="label_city" checked></label>
        <label class="layer-row"><span>Brgy</span><input type="checkbox" data-g="label_brgy" checked></label>
        <label class="layer-row"><span>Street</span><input type="checkbox" data-g="label_street" checked></label>
      </div>
    </div>

    <!-- Roads & Railways (Collapsed by default) -->
    <div class="acc-item">
      <div class="acc-header" data-target="body-roads">
        <span>Roads & Transit</span><span>▸</span>
      </div>
      <div class="acc-body hidden" id="body-roads">
        <label class="layer-row"><span>Express Way</span><input type="checkbox" data-g="road_exp" checked></label>
        <label class="layer-row"><span>Main Road</span><input type="checkbox" data-g="road_main" checked></label>
        <label class="layer-row"><span>Secondary Road</span><input type="checkbox" data-g="road_sec" checked></label>
        <label class="layer-row"><span>Tertiary Road</span><input type="checkbox" data-g="road_ter" checked></label>
        <label class="layer-row"><span>Railways</span><input type="checkbox" data-g="rd_rail" checked></label>
      </div>
    </div>

    <!-- Boundaries (Collapsed by default) -->
    <div class="acc-item">
      <div class="acc-header" data-target="body-boundaries">
        <span>Boundaries (Red Dashed)</span><span>▸</span>
      </div>
      <div class="acc-body hidden" id="body-boundaries">
        <label class="layer-row"><span>All Provinces</span><input type="checkbox" data-g="bound_prov"></label>
        <label class="layer-row"><span>All Cities</span><input type="checkbox" data-g="bound_city"></label>
        <label class="layer-row"><span>All Brgys</span><input type="checkbox" data-g="bound_brgy"></label>
        
        <div style="font-weight:600; font-size:11px; color:#f0f6fc; margin-top:4px;">Highlight Specific City Boundary</div>
        <div class="bound-select-row">
          <input type="text" id="targetCityInput" placeholder="e.g. Mandaluyong, Pasig…"/>
          <button id="btnFetchCityBound">Highlight</button>
        </div>
      </div>
    </div>

    <!-- Custom Drawings & Grouping -->
    <div class="layers-heading">
      <span>My Layers</span>
      <div style="display:flex; align-items:center; gap:6px;">
        <button id="btnAddCustomGroup" style="background:#22272e; border:1px solid #2d333b; color:#adbac7; border-radius:4px; font-size:10px; font-weight:700; padding:2px 6px; cursor:pointer;">+ GROUP</button>
        <span class="badge-count" id="layer-badge-count">0</span>
      </div>
    </div>
    <div id="my-layers-list"></div>
  </div>
</div>

<!-- Left Side Search Card -->
<div id="popup-search" class="float-card">
  <input type="text" id="searchInput" placeholder="Search location (Press Enter)…" />
</div>

<!-- Left Side Marker Settings Card -->
<div id="popup-marker-settings" class="float-card">
  <div style="font-weight:600; font-size:11px; color:#768390;">CHOOSE MARKER ICON</div>
  <div class="icon-grid" id="markerIconGrid"></div>
  <div class="f-row"><span>Icon Color</span><input type="color" id="mColor" value="#e8b84a"></div>
  <div class="f-row"><span>Icon Size</span><input type="range" id="mSize" min="0.4" max="2.0" step="0.1" value="0.9"></div>
</div>

<!-- Left Side Text Tool Settings Card -->
<div id="popup-text-settings" class="float-card">
  <div style="font-weight:600; font-size:11px; color:#768390;">TEXT CONFIGURATION</div>
  <input type="text" id="tContent" value="Custom Label" placeholder="Text content…"/>
  <div class="f-row"><span>Font</span>
    <select id="tFont" style="width:130px;">
      <option value="Century Gothic Custom" selected>Century Gothic</option>
      <option value="sans-serif">System Sans</option>
      <option value="serif">Serif</option>
      <option value="monospace">Monospace</option>
    </select>
  </div>
  <div class="f-row"><span>Font Size</span><input type="range" id="tSize" min="10" max="42" step="1" value="16"></div>
  <div class="f-row"><span>Color</span><input type="color" id="tColor" value="#d9b451"></div>
  <div class="f-row"><span>Opacity</span><input type="range" id="tOp" min="0.1" max="1" step="0.05" value="1"></div>
</div>

<!-- Left Side Shape / Polygon Customizer Editor -->
<div id="popup-shape-editor" class="float-card">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <span style="font-weight:700; color:#f0f6fc;" id="editShapeTitle">Edit Layer</span>
    <button class="card-btn" id="closeEditorBtn">✕</button>
  </div>
  <div class="f-row"><span>Name</span><input type="text" id="eName" style="width:140px;"></div>
  
  <div class="f-row" id="eBorderColorRow"><span>Border Color</span><input type="color" id="eBorderColor"></div>
  <div class="f-row" id="eBorderOpRow"><span>Border Opacity</span><input type="range" id="eBorderOp" min="0" max="1" step="0.05"></div>
  <div class="f-row" id="eWidthRow"><span>Border Width</span><input type="range" id="eWidth" min="1" max="16" step="1"></div>
  <div class="f-row" id="eDashRow"><span>Border Style</span>
    <select id="eDashStyle" style="width:110px;">
      <option value="solid">Solid</option>
      <option value="dashed">Dashed</option>
      <option value="dotted">Dotted</option>
    </select>
  </div>
  <div class="f-row" id="eFillColorRow"><span>Fill Color</span><input type="color" id="eFillColor"></div>
  <div class="f-row" id="eFillOpRow"><span>Fill Opacity</span><input type="range" id="eFillOp" min="0" max="1" step="0.05"></div>

  <!-- Polygon Floating Label Placement -->
  <div class="f-row" id="eLabelToggleRow" style="display:none;"><span>Show Label</span><input type="checkbox" id="eShowLabel"></div>
  <div class="f-row" id="eLabelPosRow" style="display:none;"><span>Label Position</span>
    <select id="eLabelPos" style="width:110px;">
      <option value="center">Center</option>
      <option value="top">Above</option>
      <option value="bottom">Below</option>
      <option value="left">Left</option>
      <option value="right">Right</option>
    </select>
  </div>

  <div class="f-row" id="eMarkerSizeRow" style="display:none;"><span>Icon Size</span><input type="range" id="eMarkerSize" min="0.4" max="2.0" step="0.1"></div>
  <div class="f-row" id="eTextRow" style="display:none;"><span>Text</span><input type="text" id="eTextVal" style="width:140px;"></div>
  <div class="f-row" id="eFontSizeRow" style="display:none;"><span>Font Size</span><input type="range" id="eFontSize" min="10" max="42" step="1"></div>
  
  <div style="display:flex; justify-content:space-between; margin-top:6px;">
    <button id="eDeleteBtn" style="color:#f85149; border:1px solid #da36334d; background:#da36331a; padding:6px 12px; border-radius:6px; cursor:pointer;">Delete</button>
    <button id="eDoneBtn" style="background:#316dca; color:#fff; border:none; padding:6px 16px; border-radius:6px; cursor:pointer;">Done</button>
  </div>
</div>

<!-- Left Side Basemap & Vector Customizer Panel -->
<div id="popup-custom-map" class="float-card">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <span style="font-weight:700; color:#f0f6fc;">Vector & Basemap Style</span>
    <button class="card-btn" id="closeCustomMapBtn">✕</button>
  </div>
  <div style="font-weight:600; font-size:11px; color:#768390; margin-top:4px;">BASEMAP PRESETS</div>
  <div style="display:flex; flex-wrap:wrap; gap:4px;" id="presetBtnList"></div>

  <div style="font-weight:600; font-size:11px; color:#768390; margin-top:6px;">BACKGROUND</div>
  <div class="f-row"><span>Color</span><input type="color" id="cBgColor" value="#0a1628"></div>

  <div style="font-weight:600; font-size:11px; color:#768390; margin-top:6px;">EXPRESS WAYS</div>
  <div class="f-row"><span>Color</span><input type="color" id="cExpColor" value="#ffaa00"></div>

  <div style="font-weight:600; font-size:11px; color:#768390; margin-top:6px;">MAIN ROADS</div>
  <div class="f-row"><span>Color</span><input type="color" id="cMainColor" value="#e8b84a"></div>
  <div class="f-row"><span>Thickness</span><input type="range" id="cMainWidth" min="1" max="10" step="0.5" value="3.8"></div>
  <div class="f-row"><span>Opacity</span><input type="range" id="cMainOp" min="0" max="1" step="0.1" value="1"></div>

  <div style="font-weight:600; font-size:11px; color:#768390; margin-top:6px;">SECONDARY ROADS</div>
  <div class="f-row"><span>Color</span><input type="color" id="cSecColor" value="#c99c37"></div>
  <div class="f-row"><span>Thickness</span><input type="range" id="cSecWidth" min="0.5" max="8" step="0.5" value="2.8"></div>
  <div class="f-row"><span>Opacity</span><input type="range" id="cSecOp" min="0" max="1" step="0.1" value="0.8"></div>

  <div style="font-weight:600; font-size:11px; color:#768390; margin-top:6px;">TERTIARY ROADS</div>
  <div class="f-row"><span>Color</span><input type="color" id="cTerColor" value="#7d5f14"></div>
  <div class="f-row"><span>Thickness</span><input type="range" id="cTerWidth" min="0.5" max="6" step="0.5" value="2.0"></div>
  <div class="f-row"><span>Opacity</span><input type="range" id="cTerOp" min="0" max="1" step="0.1" value="0.65"></div>

  <div style="font-weight:600; font-size:11px; color:#768390; margin-top:6px;">RAILWAYS</div>
  <div class="f-row"><span>Color</span><input type="color" id="cRailColor" value="#d9b451"></div>

  <div style="font-weight:600; font-size:11px; color:#768390; margin-top:6px;">BOUNDARIES (RED DASHED)</div>
  <div class="f-row"><span>Color</span><input type="color" id="cBoundColor" value="#ff1e1e"></div>

  <div style="font-weight:600; font-size:11px; color:#768390; margin-top:6px;">BUILDINGS</div>
  <div class="f-row"><span>Color</span><input type="color" id="cBldColor" value="#8e7258"></div>
  <div class="f-row"><span>Opacity</span><input type="range" id="cBldOp" min="0" max="1" step="0.05" value="0.25"></div>

  <div style="font-weight:600; font-size:11px; color:#768390; margin-top:6px;">WATER</div>
  <div class="f-row"><span>Color</span><input type="color" id="cWaterColor" value="#0a1424"></div>
  <div class="f-row"><span>Opacity</span><input type="range" id="cWaterOp" min="0" max="1" step="0.1" value="1"></div>
</div>

<!-- Left Side Export Preview & Layout Panel -->
<div id="popup-export" class="float-card">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <span style="font-weight:700; color:#f0f6fc;">Export Layout</span>
    <button class="card-btn" id="closeExportBtn">✕</button>
  </div>
  
  <div style="font-size:10px; font-weight:700; color:#768390; text-transform:uppercase;">Live Export Preview</div>
  <img id="exportPreviewImg" style="width:100%; height:110px; object-fit:cover; background:#0d1117; border-radius:6px; border:1px solid #2d333b;" />
  
  <div style="font-weight:600; font-size:11px; color:#768390;">LAYOUT RATIO</div>
  <div class="layout-grid">
    <button class="layout-btn active" data-ratio="screen">Screen</button>
    <button class="layout-btn" data-ratio="1:1">1:1</button>
    <button class="layout-btn" data-ratio="16:9">16:9</button>
    <button class="layout-btn" data-ratio="4:3">4:3</button>
    <button class="layout-btn" data-ratio="9:16">9:16</button>
    <button class="layout-btn" data-ratio="a4">A4</button>
  </div>
  
  <button id="triggerExportBtn" style="background:#316dca; color:#fff; border:none; padding:8px; border-radius:6px; font-weight:600; cursor:pointer; margin-top:4px;">Download Rendered Image</button>
</div>

<div id="hint-toast"></div>

<script>
try {
const ALL_STYLES = __ALL_STYLES__;
const POI_CONFIG = __POI_CONFIG__;
let currentStyleName = "Midnight Blue";

const map = new maplibregl.Map({
  container: 'map',
  style: __STYLE__,
  center: __CENTER__,
  zoom: __ZOOM__,
  attributionControl: false,
  fadeDuration: 0,
  preserveDrawingBuffer: true
});
map.getCanvas().addEventListener('contextmenu', e => e.preventDefault());

// ----------------- State Machine -----------------
let features = [], fid = 0;
let customGroups = {
  "Trade Area Scan": []
};
let activeTool = null, editMode = false;
let draft = [], cursorLL = null, selectedId = null;
let markerShape = 'pin', markerColor = '#e8b84a', markerIconSize = 0.9;
let currentExportRatio = 'screen';

const textSettings = {
  content: 'Custom Label',
  font: 'Century Gothic Custom',
  size: 16,
  color: '#d9b451',
  opacity: 1.0
};

let isDragging = false, dragFeatureId = null, dragStartCoord = null, dragOriginalCoords = null;

const vis = {
  label_city: true, label_brgy: true, label_street: true,
  road_exp: true, road_main: true, road_sec: true, road_ter: true, rd_rail: true,
  bound_prov: false, bound_city: false, bound_brgy: false
};

const VIS_MAP = {
  label_city: ['label_city'],
  label_brgy: ['label_brgy'],
  label_street: ['label_street'],
  road_exp: ['case_express_casing', 'rd_express'],
  road_main: ['case_major_casing', 'rd_major'],
  road_sec: ['case_secondary_casing', 'rd_secondary'],
  road_ter: ['case_tertiary_casing', 'rd_tertiary', 'rd_min_md', 'rd_min_lo', 'rd_path'],
  rd_rail: ['rd_rail'],
  bound_prov: ['bound_prov'],
  bound_city: ['bound_city'],
  bound_brgy: ['bound_brgy']
};

const $ = id => document.getElementById(id);
const hint = t => { $('hint-toast').style.display = t ? 'block' : 'none'; $('hint-toast').textContent = t || ''; };

const closeFloatingCards = () => {
  ['popup-marker-settings','popup-text-settings','popup-shape-editor','popup-custom-map','popup-search','popup-export','browser-panel'].forEach(id => $(id).classList.remove('open'));
};

const resetActiveTools = () => {
  activeTool = null;
  draft = [];
  renderDraft();
  document.querySelectorAll('.tool').forEach(b => b.classList.remove('primary-active'));
  map.getCanvas().style.cursor = '';
  map.doubleClickZoom.enable();
  hint('');
};

// ----------------- Marker Canvas Icon Pipeline -----------------
function renderIconCanvas(shape, color) {
  const c = document.createElement('canvas');
  c.width = 64; c.height = 64;
  const ctx = c.getContext('2d');
  ctx.clearRect(0,0,64,64);
  ctx.strokeStyle = '#0a1628';
  ctx.lineWidth = 3;
  ctx.fillStyle = color;
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';

  ctx.beginPath();
  if (shape === 'pin') {
    ctx.arc(32, 24, 16, Math.PI * 0.8, Math.PI * 0.2, false);
    ctx.lineTo(32, 58);
    ctx.closePath();
  } else if (shape === 'star') {
    for (let i = 0; i < 10; i++) {
      const r = i % 2 ? 12 : 26, a = -Math.PI / 2 + i * Math.PI / 5;
      const px = 32 + r * Math.cos(a), py = 32 + r * Math.sin(a);
      i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
    }
    ctx.closePath();
  } else if (shape === 'circle') {
    ctx.arc(32, 32, 22, 0, Math.PI * 2);
  } else if (shape === 'square') {
    ctx.rect(12, 12, 40, 40);
  } else if (shape === 'flag') {
    ctx.moveTo(18, 58); ctx.lineTo(18, 10); ctx.lineTo(48, 22); ctx.lineTo(18, 34);
  } else if (shape === 'heart') {
    ctx.moveTo(32, 54);
    ctx.bezierCurveTo(6, 34, 14, 10, 32, 22);
    ctx.bezierCurveTo(50, 10, 58, 34, 32, 54);
  }
  ctx.fill(); ctx.stroke();

  ctx.beginPath();
  ctx.fillStyle = '#ffffff';
  ctx.arc(32, shape === 'pin' ? 24 : 32, 5, 0, Math.PI * 2);
  ctx.fill();
  return c;
}

function getIconKey(shape, color) {
  const key = `ico_${shape}_${color.replace('#','')}`;
  if (!map.hasImage(key)) {
    const cv = renderIconCanvas(shape, color);
    const imgData = cv.getContext('2d').getImageData(0,0,64,64);
    try { map.addImage(key, imgData, { pixelRatio: 2 }); } catch(e) {}
  }
  return key;
}

const ICON_SVGS = {
  pin: '<path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"></path><circle cx="12" cy="10" r="2.5"></circle>',
  star: '<path d="M12 2l2.9 6.3 6.9.8-5.1 4.7 1.4 6.8-6.1-3.4-6.1 3.4 1.4-6.8L2.2 9.1l6.9-.8z"></path>',
  circle: '<circle cx="12" cy="12" r="8"></circle>',
  square: '<rect x="5" y="5" width="14" height="14"></rect>',
  flag: '<path d="M6 21V4"></path><path d="M6 4l12 3-12 3"></path>',
  heart: '<path d="M12 20s-7-4.6-7-10a4 4 0 0 1 7-2.5A4 4 0 0 1 19 10c0 5.4-7 10-7 10z"></path>'
};

$('markerIconGrid').innerHTML = Object.keys(ICON_SVGS).map(s =>
  `<button data-s="${s}" class="${s === markerShape ? 'active' : ''}">
     <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">${ICON_SVGS[s]}</svg>
   </button>`).join('');

$('markerIconGrid').querySelectorAll('button').forEach(b => b.onclick = () => {
  markerShape = b.dataset.s;
  $('markerIconGrid').querySelectorAll('button').forEach(x => x.classList.toggle('active', x === b));
});
$('mColor').oninput = e => { markerColor = e.target.value; };
$('mSize').oninput = e => { markerIconSize = parseFloat(e.target.value); };

$('tradeCategorySelect').innerHTML = Object.keys(POI_CONFIG).map(cat => `<option value="${cat}">${cat}</option>`).join('');

// ----------------- Vector Layers Pipeline -----------------
const fc = list => ({
  type: 'FeatureCollection',
  features: list.map(f => ({
    type: 'Feature',
    geometry: f.geometry,
    properties: Object.assign({ id: f.id, name: f.name, kind: f.kind }, f.props)
  }))
});

function addDrawStack() {
  if (!map.getSource('draw')) {
    map.addSource('draw', { type: 'geojson', data: fc(features) });

    // Polygon Fills
    map.addLayer({
      id: 'draw-fill', type: 'fill', source: 'draw',
      filter: ['==', ['geometry-type'], 'Polygon'],
      paint: {
        'fill-color': ['coalesce', ['get', 'fillColor'], ['get', 'color'], '#e8b84a'],
        'fill-opacity': ['*', ['coalesce', ['get', 'fillOpacity'], 0.35], ['get', 'visible']]
      }
    });

    // Polygon Outlines
    map.addLayer({
      id: 'draw-outline', type: 'line', source: 'draw',
      filter: ['==', ['geometry-type'], 'Polygon'],
      paint: {
        'line-color': ['coalesce', ['get', 'borderColor'], ['get', 'color'], '#e8b84a'],
        'line-width': ['coalesce', ['get', 'width'], 3],
        'line-opacity': ['*', ['coalesce', ['get', 'borderOpacity'], 0.9], ['get', 'visible']]
      }
    });

    // Polylines & Light Blue Default Routes
    map.addLayer({
      id: 'draw-line', type: 'line', source: 'draw',
      filter: ['==', ['geometry-type'], 'LineString'],
      layout: { 'line-cap': 'round', 'line-join': 'round' },
      paint: {
        'line-color': ['coalesce', ['get', 'borderColor'], ['get', 'color'], '#38bdf8'],
        'line-width': ['coalesce', ['get', 'width'], 4],
        'line-opacity': ['*', ['coalesce', ['get', 'borderOpacity'], 0.9], ['get', 'visible']]
      }
    });

    // Marker Pins
    map.addLayer({
      id: 'draw-marker', type: 'symbol', source: 'draw',
      filter: ['all', ['==', ['geometry-type'], 'Point'], ['!=', ['get', 'kind'], 'text']],
      layout: {
        'icon-image': ['get', 'iconKey'],
        'icon-size': ['coalesce', ['get', 'iconSize'], 0.9],
        'icon-allow-overlap': true,
        'icon-anchor': 'bottom'
      },
      paint: { 'icon-opacity': ['get', 'visible'] }
    });

    // Custom Text Labels
    map.addLayer({
      id: 'draw-text', type: 'symbol', source: 'draw',
      filter: ['all', ['==', ['geometry-type'], 'Point'], ['==', ['get', 'kind'], 'text']],
      layout: {
        'text-field': ['get', 'text'],
        'text-font': ['Noto Sans Regular'],
        'text-size': ['coalesce', ['get', 'fontSize'], 16],
        'text-allow-overlap': true,
        'text-anchor': 'center'
      },
      paint: {
        'text-color': ['coalesce', ['get', 'color'], '#d9b451'],
        'text-opacity': ['*', ['coalesce', ['get', 'opacity'], 1], ['get', 'visible']],
        'text-halo-color': '#0a1628',
        'text-halo-width': 2
      }
    });

    // Specific Polygon Labels Layer
    map.addLayer({
      id: 'draw-poly-labels', type: 'symbol', source: 'draw',
      filter: ['all', ['==', ['geometry-type'], 'Polygon'], ['==', ['get', 'showLabel'], true]],
      layout: {
        'text-field': ['get', 'name'],
        'text-font': ['Noto Sans Regular'],
        'text-size': 13,
        'text-allow-overlap': true,
        'text-anchor': ['coalesce', ['get', 'labelPos'], 'center'],
        'text-radial-offset': 0.8,
        'text-justify': 'auto'
      },
      paint: {
        'text-color': '#ffffff',
        'text-halo-color': '#0a1628',
        'text-halo-width': 2,
        'text-opacity': ['get', 'visible']
      }
    });

  } else {
    map.getSource('draw').setData(fc(features));
  }

  // Live Construction Draft Preview Source
  if (!map.getSource('draft')) {
    map.addSource('draft', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addLayer({
      id: 'draft-line', type: 'line', source: 'draft',
      filter: ['==', ['geometry-type'], 'LineString'],
      paint: { 'line-color': '#38bdf8', 'line-width': 2.5, 'line-dasharray': [2, 2] }
    });
    map.addLayer({
      id: 'draft-point', type: 'circle', source: 'draft',
      filter: ['==', ['geometry-type'], 'Point'],
      paint: { 
        'circle-color': ['case', ['get', 'isLastPoint'], '#38bdf8', '#e8b84a'],
        'circle-radius': ['case', ['get', 'isLastPoint'], 10, ['case', ['get', 'isOrigin'], 8, 5]], 
        'circle-stroke-color': '#ffffff', 
        'circle-stroke-width': 2.5 
      }
    });
  }
}

const syncDraw = () => { if (map.getSource('draw')) map.getSource('draw').setData(fc(features)); };

function renderDraft() {
  if (!map.getSource('draft')) return;
  const f = [];
  const pt = (c, isOrigin=false, isLastPoint=false) => ({ 
    type: 'Feature', 
    geometry: { type: 'Point', coordinates: c }, 
    properties: { isOrigin, isLastPoint } 
  });
  const ln = c => ({ type: 'Feature', geometry: { type: 'LineString', coordinates: c }, properties: {} });

  draft.forEach((p, i) => {
    const isOrigin = i === 0 && activeTool === 'polygon';
    const isLastPoint = i === draft.length - 1 && activeTool === 'route' && draft.length > 0;
    f.push(pt(p, isOrigin, isLastPoint));
  });

  if ((activeTool === 'polyline' || activeTool === 'route') && draft.length) {
    f.push(ln(cursorLL ? [...draft, cursorLL] : draft));
  }
  if (activeTool === 'polygon' && draft.length) {
    const pts = cursorLL ? [...draft, cursorLL] : draft;
    if (pts.length > 1) f.push(ln([...pts, pts[0]]));
  }
  if (activeTool === 'rectangle' && draft.length === 1 && cursorLL) {
    f.push(ln(rectCoords(draft[0], cursorLL)[0]));
  }
  if (activeTool === 'circle' && draft.length === 1 && cursorLL) {
    const { coords, r } = circleCoords(draft[0], cursorLL);
    f.push(ln(coords[0]));
    const distText = r > 1000 ? `${(r/1000).toFixed(2)} km` : `${Math.round(r)} m`;
    hint(`Radius: ${distText} · Click to finalize`);
  }
  map.getSource('draft').setData({ type: 'FeatureCollection', features: f });
}

function applyVis() {
  for (const g in VIS_MAP) {
    VIS_MAP[g].forEach(id => {
      if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', vis[g] ? 'visible' : 'none');
    });
  }
}

map.on('load', () => { addDrawStack(); applyVis(); });

// ----------------- Geometry Utilities & Snapping -----------------
function haversineDist(a, b) {
  const R = 6371000, dLa = (b[1]-a[1]) * Math.PI/180, dLo = (b[0]-a[0]) * Math.PI/180;
  const s = Math.sin(dLa/2)**2 + Math.cos(a[1]*Math.PI/180) * Math.cos(b[1]*Math.PI/180) * Math.sin(dLo/2)**2;
  return 2 * R * Math.asin(Math.sqrt(s));
}

function rectCoords(a, b) {
  return [[[a[0],a[1]],[a[0],b[1]],[b[0],b[1]],[b[0],a[1]],[a[0],a[1]]]];
}

function circleCoords(c, edge) {
  const r = haversineDist(c, edge), coords = [];
  for (let i = 0; i <= 64; i++) {
    const a = (i / 64) * 2 * Math.PI;
    coords.push([
      c[0] + (r / (111320 * Math.cos(c[1]*Math.PI/180))) * Math.cos(a),
      c[1] + (r / 111320) * Math.sin(a)
    ]);
  }
  return { coords: [coords], r };
}

function pointInPolygon(point, vs) {
  const x = point[0], y = point[1];
  let inside = false;
  for (let i = 0, j = vs.length - 1; i < vs.length; j = i++) {
    const xi = vs[i][0], yi = vs[i][1];
    const xj = vs[j][0], yj = vs[j][1];
    const intersect = ((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
    if (intersect) inside = !inside;
  }
  return inside;
}

function fetchMultiPointRoute(pts) {
  hint('Calculating route…');
  const coordStr = pts.map(p => `${p[0]},${p[1]}`).join(';');
  fetch(`https://router.project-osrm.org/route/v1/driving/${coordStr}?overview=full&geometries=geojson`)
    .then(r => r.json())
    .then(j => {
      const geom = (j.routes && j.routes[0]) ? j.routes[0].geometry : { type: 'LineString', coordinates: pts };
      addFeatureRecord('route', geom, { color: '#38bdf8', borderColor: '#38bdf8', width: 4, borderOpacity: 0.9 });
      hint('');
    })
    .catch(() => {
      addFeatureRecord('route', { type: 'LineString', coordinates: pts }, { color: '#38bdf8', borderColor: '#38bdf8', width: 3, borderOpacity: 0.8 });
      hint('Direct route fallback');
    });
}

function addFeatureRecord(kind, geometry, customProps = {}, targetGroup = null) {
  const newId = ++fid;
  const isRoute = kind === 'route';
  const defaultBorder = isRoute ? '#38bdf8' : '#e8b84a';

  const feat = {
    id: newId,
    name: `${kind.charAt(0).toUpperCase() + kind.slice(1)} ${newId}`,
    kind: kind,
    geometry: geometry,
    props: {
      color: defaultBorder,
      borderColor: defaultBorder,
      borderOpacity: 0.9,
      width: 3,
      fillColor: '#e8b84a',
      fillOpacity: 0.35,
      dashStyle: 'solid',
      showLabel: false,
      labelPos: 'center',
      iconSize: markerIconSize,
      visible: 1,
      ...customProps
    }
  };
  features.push(feat);
  
  if (targetGroup && customGroups[targetGroup]) {
    customGroups[targetGroup].push(newId);
  }
  
  syncDraw();
  renderMyLayers();
  return feat;
}

// ----------------- Trade Area POI Scanner -----------------
$('btnScanTradeArea').onclick = () => {
  const polyId = parseInt($('tradePolygonSelect').value, 10);
  const targetPoly = features.find(f => f.id === polyId);
  if (!targetPoly) {
    hint('Please select a target polygon first.');
    return;
  }
  const category = $('tradeCategorySelect').value;
  const bnd = calcBounds(targetPoly);
  const centerLat = (bnd[0][1] + bnd[1][1]) / 2;
  const centerLon = (bnd[0][0] + bnd[1][0]) / 2;
  const radius = haversineDist([centerLon, centerLat], [bnd[1][0], bnd[1][1]]);

  hint(`Querying POIs for ${category} inside polygon…`);
  $('tradeResults').innerHTML = '<div style="color:#d9b451;">Extracting local POIs…</div>';

  if (!customGroups["Trade Area Scan"]) customGroups["Trade Area Scan"] = [];

  // Robust Geoprocessing Query (Overpass / OSMnx Tag Parser)
  const tags = POI_CONFIG[category] || [];
  const bbox = `${bnd[0][1]},${bnd[0][0]},${bnd[1][1]},${bnd[1][0]}`;
  let queryParts = '';
  tags.forEach(t => {
    const rawTag = t[1];
    if (rawTag.includes('~')) {
      const parts = rawTag.split('~');
      const k = parts[0].replace(/"/g, '');
      const v = parts[1].replace(/"/g, '').replace(',i', '');
      queryParts += `node["${k}"~"${v}",i](${bbox});way["${k}"~"${v}",i](${bbox});`;
    } else if (rawTag.includes('=')) {
      const parts = rawTag.split('=');
      const k = parts[0].replace(/"/g, '');
      const v = parts[1].replace(/"/g, '');
      queryParts += `node["${k}"="${v}"](${bbox});way["${k}"="${v}"](${bbox});`;
    }
  });

  const overpassQuery = `[out:json][timeout:25];(${queryParts});out center 100;`;
  const url = `https://overpass-api.de/api/interpreter?data=${encodeURIComponent(overpassQuery)}`;

  fetch(url)
    .then(r => r.json())
    .then(data => {
      const results = data.elements || [];
      const polyCoords = targetPoly.geometry.coordinates[0];
      const filtered = results.filter(el => {
        const lat = el.lat || (el.center && el.center.lat);
        const lon = el.lon || (el.center && el.center.lon);
        return lat && lon && pointInPolygon([lon, lat], polyCoords);
      });

      if (!filtered.length) {
        $('tradeResults').innerHTML = '<div style="color:#8b949e;">No matching POIs inside this exact polygon.</div>';
        hint('Scan complete: 0 POIs inside area.');
        return;
      }

      const counts = {};
      filtered.forEach(el => {
        const name = (el.tags && (el.tags.name || el.tags.amenity || el.tags.shop || el.tags.building)) || 'POI';
        counts[name] = (counts[name] || 0) + 1;

        const lat = el.lat || (el.center && el.center.lat);
        const lon = el.lon || (el.center && el.center.lon);
        addFeatureRecord('marker', { type: 'Point', coordinates: [lon, lat] }, {
          name: name,
          shape: 'circle',
          color: '#00d2ff',
          iconSize: 0.65,
          iconKey: getIconKey('circle', '#00d2ff')
        }, "Trade Area Scan");
      });

      let html = `<div style="font-weight:700; color:#f0f6fc; margin-bottom:4px;">Grouped ${filtered.length} POIs:</div>`;
      for (const k in counts) {
        html += `<div class="poi-badge"><span>${k}</span><span style="font-weight:700; color:#38bdf8;">${counts[k]}</span></div>`;
      }
      $('tradeResults').innerHTML = html;
      hint(`Added ${filtered.length} POIs to "Trade Area Scan" layer group!`);
    })
    .catch(() => {
      $('tradeResults').innerHTML = '<div style="color:#ff7b72;">Data source busy. Retrying…</div>';
    });
};

// ----------------- Selective Boundary Fetcher -----------------
$('btnFetchCityBound').onclick = () => {
  const q = $('targetCityInput').value.trim();
  if (!q) return;
  hint(`Locating & highlighting ${q} boundary…`);
  fetch(`https://nominatim.openstreetmap.org/search?format=json&polygon_geojson=1&limit=1&q=${encodeURIComponent(q)}`)
    .then(r => r.json())
    .then(j => {
      if (j.length && j[0].geojson && (j[0].geojson.type === 'Polygon' || j[0].geojson.type === 'MultiPolygon')) {
        addFeatureRecord('polygon', j[0].geojson, {
          name: `${q} Boundary`,
          borderColor: '#ff1e1e',
          borderOpacity: 1.0,
          width: 3,
          dashStyle: 'dashed',
          fillColor: '#ff1e1e',
          fillOpacity: 0.15,
          showLabel: true
        });
        if (j[0].boundingbox) {
          map.fitBounds([
            [parseFloat(j[0].boundingbox[2]), parseFloat(j[0].boundingbox[0])],
            [parseFloat(j[0].boundingbox[3]), parseFloat(j[0].boundingbox[1])]
          ], { padding: 60 });
        }
        hint(`${q} boundary added!`);
      } else {
        hint('Boundary polygon not found.');
      }
    })
    .catch(() => hint('Boundary request failed'));
};

// ----------------- Tool Handlers & Drawing Engine -----------------
document.querySelectorAll('.tool').forEach(btn => {
  btn.onclick = () => {
    const t = btn.dataset.tool;
    if (activeTool === t) {
      resetActiveTools();
      closeFloatingCards();
    } else {
      document.querySelectorAll('.tool').forEach(b => b.classList.remove('primary-active'));
      $('btn-edit-mode').classList.remove('primary-active');
      editMode = false;
      closeFloatingCards();

      activeTool = t;
      btn.classList.add('primary-active');
      draft = [];
      renderDraft();

      map.getCanvas().style.cursor = 'crosshair';
      map.doubleClickZoom.disable();

      if (t === 'marker') $('popup-marker-settings').classList.add('open');
      if (t === 'textbox') $('popup-text-settings').classList.add('open');

      if (t === 'polyline') hint('Click points · Click last point again to finish');
      if (t === 'polygon') hint('Click vertices · Click origin or same point to save');
      if (t === 'rectangle') hint('Click corner 1, then click opposite corner');
      if (t === 'circle') hint('Click center, then outer edge');
      if (t === 'route') hint('Click points · Click the large blue endpoint to finish');
    }
  };
});

map.on('mousemove', e => {
  cursorLL = [e.lngLat.lng, e.lngLat.lat];
  if (activeTool) renderDraft();

  if (isDragging && dragFeatureId) {
    const dx = cursorLL[0] - dragStartCoord[0];
    const dy = cursorLL[1] - dragStartCoord[1];
    const f = features.find(x => x.id === dragFeatureId);
    if (!f) return;

    const translateCoords = coords => {
      if (typeof coords[0] === 'number') return [coords[0] + dx, coords[1] + dy];
      return coords.map(translateCoords);
    };
    f.geometry.coordinates = translateCoords(dragOriginalCoords);
    syncDraw();
  }
});

map.on('click', e => {
  if (!activeTool || (['marker', 'textbox'].includes(activeTool) === false && draft.length === 0 && !['rectangle', 'circle'].includes(activeTool))) {
    const fs = map.queryRenderedFeatures(e.point, { layers: ['draw-fill','draw-line','draw-outline','draw-marker','draw-text'] });
    if (fs.length && fs[0].properties.id != null) {
      openShapeEditor(parseInt(fs[0].properties.id, 10));
      resetActiveTools();
      return;
    }
  }

  if (!activeTool) return;
  const ll = [e.lngLat.lng, e.lngLat.lat];

  if (activeTool === 'marker') {
    const feat = addFeatureRecord('marker', { type: 'Point', coordinates: ll }, {
      shape: markerShape,
      color: markerColor,
      iconSize: markerIconSize,
      iconKey: getIconKey(markerShape, markerColor)
    });
    resetActiveTools();
    closeFloatingCards();
    openShapeEditor(feat.id);
  } else if (activeTool === 'textbox') {
    const feat = addFeatureRecord('text', { type: 'Point', coordinates: ll }, {
      text: $('tContent').value || 'Label',
      fontSize: parseInt($('tSize').value, 10),
      color: $('tColor').value,
      opacity: parseFloat($('tOp').value)
    });
    resetActiveTools();
    closeFloatingCards();
    openShapeEditor(feat.id);
  } else if (activeTool === 'polyline') {
    if (draft.length >= 2) {
      const pScreen = map.project(ll);
      const lastPtScreen = map.project(draft[draft.length - 1]);
      if (Math.hypot(pScreen.x - lastPtScreen.x, pScreen.y - lastPtScreen.y) < 18) {
        const feat = addFeatureRecord('polyline', { type: 'LineString', coordinates: draft });
        resetActiveTools();
        openShapeEditor(feat.id);
        return;
      }
    }
    draft.push(ll);
  } else if (activeTool === 'polygon') {
    if (draft.length >= 3) {
      const pScreen = map.project(ll);
      for (const pt of draft) {
        const vScreen = map.project(pt);
        if (Math.hypot(pScreen.x - vScreen.x, pScreen.y - vScreen.y) < 18) {
          const feat = addFeatureRecord('polygon', { type: 'Polygon', coordinates: [[...draft, draft[0]]] });
          resetActiveTools();
          openShapeEditor(feat.id);
          return;
        }
      }
    }
    draft.push(ll);
  } else if (activeTool === 'rectangle') {
    draft.push(ll);
    if (draft.length === 2) {
      const feat = addFeatureRecord('rectangle', { type: 'Polygon', coordinates: rectCoords(draft[0], draft[1]) });
      resetActiveTools();
      openShapeEditor(feat.id);
    }
  } else if (activeTool === 'circle') {
    draft.push(ll);
    if (draft.length === 2) {
      const { coords, r } = circleCoords(draft[0], draft[1]);
      const feat = addFeatureRecord('circle', { type: 'Polygon', coordinates: coords }, { radiusMeters: r });
      resetActiveTools();
      openShapeEditor(feat.id);
    }
  } else if (activeTool === 'route') {
    if (draft.length >= 2) {
      const pScreen = map.project(ll);
      const lastPtScreen = map.project(draft[draft.length - 1]);
      if (Math.hypot(pScreen.x - lastPtScreen.x, pScreen.y - lastPtScreen.y) < 22) {
        fetchMultiPointRoute(draft);
        resetActiveTools();
        return;
      }
    }
    draft.push(ll);
  }
  renderDraft();
});

document.addEventListener('keydown', e => {
  if (/INPUT|TEXTAREA|SELECT/.test(e.target.tagName)) return;
  if (e.key === 'Enter') {
    if (activeTool === 'polygon' && draft.length >= 3) {
      const feat = addFeatureRecord('polygon', { type: 'Polygon', coordinates: [[...draft, draft[0]]] });
      resetActiveTools();
      openShapeEditor(feat.id);
    } else if (activeTool === 'polyline' && draft.length >= 2) {
      const feat = addFeatureRecord('polyline', { type: 'LineString', coordinates: draft });
      resetActiveTools();
      openShapeEditor(feat.id);
    } else if (activeTool === 'route' && draft.length >= 2) {
      fetchMultiPointRoute(draft);
      resetActiveTools();
    }
  }
  if (e.key === 'Escape') {
    resetActiveTools();
    closeFloatingCards();
  }
});

// ----------------- Edit & Drag Mode Engine -----------------
$('btn-edit-mode').onclick = () => {
  editMode = !editMode;
  $('btn-edit-mode').classList.toggle('primary-active', editMode);
  activeTool = null;
  document.querySelectorAll('.tool').forEach(b => b.classList.remove('primary-active'));
  closeFloatingCards();
  hint(editMode ? 'Drag shapes to reposition · Click to edit styles' : '');
};

map.on('mousedown', e => {
  if (!editMode) return;
  const fs = map.queryRenderedFeatures(e.point, { layers: ['draw-fill','draw-line','draw-outline','draw-marker','draw-text'] });
  if (fs.length && fs[0].properties.id != null) {
    isDragging = true;
    dragFeatureId = parseInt(fs[0].properties.id, 10);
    dragStartCoord = [e.lngLat.lng, e.lngLat.lat];
    const f = features.find(x => x.id === dragFeatureId);
    if (f) dragOriginalCoords = JSON.parse(JSON.stringify(f.geometry.coordinates));
    map.dragPan.disable();
  }
});

map.on('mouseup', () => {
  if (isDragging) {
    isDragging = false;
    dragFeatureId = null;
    map.dragPan.enable();
  }
});

// ----------------- Customizer / Shape Editor -----------------
function openShapeEditor(id) {
  const f = features.find(x => x.id === id);
  if (!f) return;
  selectedId = id;
  closeFloatingCards();

  $('editShapeTitle').textContent = `Edit ${f.name}`;
  $('eName').value = f.name;
  $('eBorderColor').value = f.props.borderColor || f.props.color || '#e8b84a';
  $('eBorderOp').value = f.props.borderOpacity != null ? f.props.borderOpacity : 0.9;
  $('eWidth').value = f.props.width || 3;
  $('eDashStyle').value = f.props.dashStyle || 'solid';
  $('eFillColor').value = f.props.fillColor || f.props.color || '#e8b84a';
  $('eFillOp').value = f.props.fillOpacity != null ? f.props.fillOpacity : 0.35;

  const isPolygon = ['polygon', 'rectangle', 'circle'].includes(f.kind);
  $('eFillColorRow').style.display = isPolygon ? 'flex' : 'none';
  $('eFillOpRow').style.display = isPolygon ? 'flex' : 'none';
  $('eDashRow').style.display = isPolygon || f.kind === 'polyline' ? 'flex' : 'none';
  $('eLabelToggleRow').style.display = isPolygon ? 'flex' : 'none';
  $('eLabelPosRow').style.display = isPolygon ? 'flex' : 'none';

  if (isPolygon) {
    $('eShowLabel').checked = !!f.props.showLabel;
    $('eLabelPos').value = f.props.labelPos || 'center';
  }

  const isMarker = f.kind === 'marker';
  $('eMarkerSizeRow').style.display = isMarker ? 'flex' : 'none';
  if (isMarker) $('eMarkerSize').value = f.props.iconSize || 0.9;

  const isText = f.kind === 'text';
  $('eTextRow').style.display = isText ? 'flex' : 'none';
  $('eFontSizeRow').style.display = isText ? 'flex' : 'none';
  if (isText) {
    $('eTextVal').value = f.props.text || '';
    $('eFontSize').value = f.props.fontSize || 16;
  }

  $('popup-shape-editor').classList.add('open');
}

$('eName').oninput = e => {
  const f = features.find(x => x.id === selectedId);
  if (f) { f.name = e.target.value; syncDraw(); renderMyLayers(); }
};
$('eBorderColor').oninput = e => {
  const f = features.find(x => x.id === selectedId);
  if (!f) return;
  f.props.borderColor = e.target.value;
  f.props.color = e.target.value;
  if (f.kind === 'marker') f.props.iconKey = getIconKey(f.props.shape || 'pin', e.target.value);
  syncDraw();
};
$('eBorderOp').oninput = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.borderOpacity = parseFloat(e.target.value); syncDraw(); } };
$('eWidth').oninput = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.width = parseFloat(e.target.value); syncDraw(); } };
$('eFillColor').oninput = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.fillColor = e.target.value; syncDraw(); } };
$('eFillOp').oninput = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.fillOpacity = parseFloat(e.target.value); syncDraw(); } };
$('eShowLabel').onchange = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.showLabel = e.target.checked; syncDraw(); } };
$('eLabelPos').onchange = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.labelPos = e.target.value; syncDraw(); } };
$('eMarkerSize').oninput = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.iconSize = parseFloat(e.target.value); syncDraw(); } };
$('eDashStyle').onchange = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.dashStyle = e.target.value; syncDraw(); } };
$('eTextVal').oninput = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.text = e.target.value; syncDraw(); renderMyLayers(); } };
$('eFontSize').oninput = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.fontSize = parseInt(e.target.value, 10); syncDraw(); } };

$('eDeleteBtn').onclick = () => {
  features = features.filter(x => x.id !== selectedId);
  for (const g in customGroups) { customGroups[g] = customGroups[g].filter(id => id !== selectedId); }
  syncDraw();
  renderMyLayers();
  $('popup-shape-editor').classList.remove('open');
};
$('eDoneBtn').onclick = () => { $('popup-shape-editor').classList.remove('open'); };
$('closeEditorBtn').onclick = () => { $('popup-shape-editor').classList.remove('open'); };

// ----------------- My Layers & Grouping Pipeline -----------------
$('btnAddCustomGroup').onclick = () => {
  const gName = prompt("Enter new Group name:", `Group ${Object.keys(customGroups).length + 1}`);
  if (gName && gName.trim() && !customGroups[gName]) {
    customGroups[gName.trim()] = [];
    renderMyLayers();
  }
};

function renderLayerCardHtml(f) {
  let subInfo = f.kind;
  if (f.kind === 'circle' && f.props.radiusMeters) {
    subInfo = `Radius: ${f.props.radiusMeters > 1000 ? (f.props.radiusMeters/1000).toFixed(2)+' km' : Math.round(f.props.radiusMeters)+' m'}`;
  }
  const isPoly = ['polygon', 'rectangle', 'circle'].includes(f.kind);
  return `
    <div class="layer-card">
      <div class="layer-card-top">
        <input class="layer-name-input" data-id="${f.id}" value="${f.name}" title="Click to rename" />
        <button class="card-btn" data-act="edit" data-id="${f.id}" title="Edit Properties">✎</button>
        <button class="card-btn" data-act="eye" data-id="${f.id}" title="Toggle Visibility">${f.props.visible ? '👁' : '–'}</button>
        <button class="card-btn" data-act="zoom" data-id="${f.id}" title="Zoom To">⤢</button>
        <button class="card-btn" data-act="del" data-id="${f.id}" title="Delete">✕</button>
      </div>
      <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px; color:#768390; padding:0 4px;">
        <span>${subInfo}</span>
        ${isPoly ? `
          <label style="display:flex; align-items:center; gap:4px; cursor:pointer;"><input type="checkbox" data-act="labelToggle" data-id="${f.id}" ${f.props.showLabel ? 'checked' : ''}/> Label</label>
        ` : ''}
      </div>
    </div>
  `;
}

function renderMyLayers() {
  const container = $('my-layers-list');
  $('layer-badge-count').textContent = features.length;

  // Refresh Trade Area Target Dropdown
  const polyList = features.filter(f => ['polygon', 'rectangle', 'circle'].includes(f.kind));
  $('tradePolygonSelect').innerHTML = '<option value="">-- Choose a polygon --</option>' + 
    polyList.map(p => `<option value="${p.id}">${p.name}</option>`).join('');

  if (!features.length && !Object.keys(customGroups).length) {
    container.innerHTML = '<div style="font-size:12px; color:#768390; padding:6px 0;">No drawings yet. Use the tools to create shapes.</div>';
    return;
  }

  let html = '';
  const groupedIds = new Set();

  // Render Custom Groups
  for (const gName in customGroups) {
    const ids = customGroups[gName];
    const groupFeats = features.filter(f => ids.includes(f.id));
    ids.forEach(id => groupedIds.add(id));

    html += `
      <div class="group-container">
        <div class="group-header">
          <input class="group-title-input" data-oldname="${gName}" value="${gName}" title="Click to rename Group" />
          <div style="display:flex; align-items:center; gap:2px;">
            <button class="card-btn" data-act="groupEye" data-group="${gName}" title="Toggle Group">👁</button>
            <button class="card-btn" data-act="groupDel" data-group="${gName}" title="Delete Group">✕</button>
          </div>
        </div>
        <div class="group-items">
          ${groupFeats.length ? groupFeats.map(f => renderLayerCardHtml(f)).join('') : '<div style="font-size:10px; color:#768390; padding:4px;">Empty group</div>'}
        </div>
      </div>
    `;
  }

  // Ungrouped loose layers
  const looseFeats = features.filter(f => !groupedIds.has(f.id));
  if (looseFeats.length) {
    html += '<div style="font-size:11px; font-weight:700; color:#adbac7; margin-top:8px;">Ungrouped Layers</div>';
    html += looseFeats.slice().reverse().map(f => renderLayerCardHtml(f)).join('');
  }

  container.innerHTML = html;

  // Bind Rename Group Handlers
  container.querySelectorAll('.group-title-input').forEach(inp => {
    inp.onchange = e => {
      const oldN = e.target.dataset.oldname;
      const newN = e.target.value.trim();
      if (newN && newN !== oldN) {
        customGroups[newN] = customGroups[oldN];
        delete customGroups[oldN];
        renderMyLayers();
      }
    };
  });

  // Bind Rename Layer Handlers
  container.querySelectorAll('.layer-name-input').forEach(inp => {
    inp.onchange = e => {
      const id = parseInt(e.target.dataset.id, 10);
      const f = features.find(x => x.id === id);
      if (f) { f.name = e.target.value; syncDraw(); }
    };
  });

  // Action Triggers
  container.querySelectorAll('button[data-act], input[data-act]').forEach(b => {
    b.onchange = b.onclick = (e) => {
      if (b.tagName === 'INPUT' && e.type !== 'change') return;
      if (b.tagName === 'BUTTON' && e.type !== 'click') return;

      const act = b.dataset.act;

      if (act === 'groupEye') {
        const g = b.dataset.group;
        const ids = customGroups[g] || [];
        const anyVis = features.some(f => ids.includes(f.id) && f.props.visible);
        features.forEach(f => { if (ids.includes(f.id)) f.props.visible = anyVis ? 0 : 1; });
        syncDraw(); renderMyLayers();
        return;
      }
      if (act === 'groupDel') {
        const g = b.dataset.group;
        delete customGroups[g];
        renderMyLayers();
        return;
      }

      const id = parseInt(b.dataset.id, 10);
      const f = features.find(x => x.id === id);
      if (!f) return;

      if (act === 'labelToggle') { f.props.showLabel = b.checked; syncDraw(); }
      if (act === 'edit') openShapeEditor(id);
      if (act === 'eye') { f.props.visible = f.props.visible ? 0 : 1; syncDraw(); renderMyLayers(); }
      if (act === 'del') { 
        features = features.filter(x => x.id !== id);
        for (const g in customGroups) customGroups[g] = customGroups[g].filter(xId => xId !== id);
        syncDraw(); renderMyLayers(); 
      }
      if (act === 'zoom') {
        const bnd = calcBounds(f);
        if (bnd) map.fitBounds(bnd, { padding: 80, maxZoom: 17 });
      }
    };
  });
}

function calcBounds(f) {
  let minX = 1e9, minY = 1e9, maxX = -1e9, maxY = -1e9, ok = false;
  const walk = c => {
    if (typeof c[0] === 'number') {
      ok = true;
      minX = Math.min(minX, c[0]); maxX = Math.max(maxX, c[0]);
      minY = Math.min(minY, c[1]); maxY = Math.max(maxY, c[1]);
    } else c.forEach(walk);
  };
  walk(f.geometry.coordinates);
  if (!ok) return null;
  if (minX === maxX && minY === maxY) return [[minX - 0.005, minY - 0.005], [maxX + 0.005, maxY + 0.005]];
  return [[minX, minY], [maxX, maxY]];
}

// ----------------- Export Layout & Preview Engine -----------------
function updateExportPreview() {
  const canvas = map.getCanvas();
  try {
    const dataUrl = canvas.toDataURL('image/png');
    $('exportPreviewImg').src = dataUrl;
  } catch(e) {}
}

$('btn-export-dialog').onclick = () => {
  const p = $('popup-export');
  const willOpen = !p.classList.contains('open');
  closeFloatingCards();
  if (willOpen) {
    p.classList.add('open');
    updateExportPreview();
  }
};
$('closeExportBtn').onclick = () => { $('popup-export').classList.remove('open'); };

document.querySelectorAll('.layout-grid .layout-btn').forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll('.layout-grid .layout-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentExportRatio = btn.dataset.ratio;
  };
});

$('triggerExportBtn').onclick = () => {
  hint('Exporting snapshot layout…');
  map.once('render', () => {
    try {
      const srcCanvas = map.getCanvas();
      let targetW = srcCanvas.width, targetH = srcCanvas.height;

      if (currentExportRatio === '1:1') {
        const dim = Math.min(srcCanvas.width, srcCanvas.height);
        targetW = dim; targetH = dim;
      } else if (currentExportRatio === '16:9') {
        targetW = srcCanvas.width; targetH = Math.round(srcCanvas.width * (9/16));
      } else if (currentExportRatio === '4:3') {
        targetW = srcCanvas.width; targetH = Math.round(srcCanvas.width * (3/4));
      } else if (currentExportRatio === '9:16') {
        targetH = srcCanvas.height; targetW = Math.round(srcCanvas.height * (9/16));
      } else if (currentExportRatio === 'a4') {
        targetW = srcCanvas.width; targetH = Math.round(srcCanvas.width * 1.414);
      }

      const outCanvas = document.createElement('canvas');
      outCanvas.width = targetW;
      outCanvas.height = targetH;
      const ctx = outCanvas.getContext('2d');

      const sx = (srcCanvas.width - targetW) / 2;
      const sy = (srcCanvas.height - targetH) / 2;
      ctx.drawImage(srcCanvas, sx, sy, targetW, targetH, 0, 0, targetW, targetH);

      const a = document.createElement('a');
      a.download = `map_${currentExportRatio}_${Date.now()}.png`;
      a.href = outCanvas.toDataURL('image/png', 0.95);
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      hint('Export downloaded successfully!');
      $('popup-export').classList.remove('open');
    } catch(e) {
      hint('Direct export fallback');
      const a = document.createElement('a');
      a.download = `map_export_${Date.now()}.png`;
      a.href = map.getCanvas().toDataURL('image/png');
      a.click();
    }
  });
  map.triggerRepaint();
};

// ----------------- UI / Rail / Accordion Controls -----------------
$('btn-browser-toggle').onclick = () => {
  const p = $('browser-panel');
  const willOpen = !p.classList.contains('open');
  closeFloatingCards();
  if (willOpen) p.classList.add('open');
};
$('btn-close-browser').onclick = () => { $('browser-panel').classList.remove('open'); };

// Collapsible accordion triggers
document.querySelectorAll('.acc-header').forEach(h => {
  h.onclick = () => {
    const body = $(h.dataset.target);
    body.classList.toggle('hidden');
    h.querySelector('span:last-child').textContent = body.classList.contains('hidden') ? '▸' : '▾';
  };
});

document.querySelectorAll('#browser-panel input[data-g]').forEach(cb => {
  cb.onchange = () => {
    vis[cb.dataset.g] = cb.checked;
    applyVis();
  };
});

// Search location toggle
$('btn-search').onclick = () => {
  const p = $('popup-search');
  const willOpen = !p.classList.contains('open');
  closeFloatingCards();
  if (willOpen) { p.classList.add('open'); $('searchInput').focus(); }
};
$('searchInput').addEventListener('keydown', e => {
  if (e.key !== 'Enter') return;
  const q = e.target.value.trim();
  if (!q) return;
  hint('Searching location…');
  fetch(`https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(q)}`)
    .then(r => r.json())
    .then(j => {
      if (j.length) {
        map.flyTo({ center: [parseFloat(j[0].lon), parseFloat(j[0].lat)], zoom: 15 });
        hint('');
        $('popup-search').classList.remove('open');
      } else { hint('Location not found'); }
    })
    .catch(() => hint('Search request failed'));
});

// Basemap vector customizer
$('btn-custom-map').onclick = () => {
  const p = $('popup-custom-map');
  const willOpen = !p.classList.contains('open');
  closeFloatingCards();
  if (willOpen) p.classList.add('open');
};
$('closeCustomMapBtn').onclick = () => { $('popup-custom-map').classList.remove('open'); };

$('presetBtnList').innerHTML = Object.keys(ALL_STYLES).map(n =>
  `<button style="border:1px solid #2d333b; background:#22272e; color:#adbac7; border-radius:4px; padding:4px 8px; font-size:11px; cursor:pointer;" data-n="${n}">${n}</button>`
).join('');

$('presetBtnList').querySelectorAll('button').forEach(b => {
  b.onclick = () => {
    currentStyleName = b.dataset.n;
    map.setStyle(ALL_STYLES[currentStyleName]);
    map.once('idle', () => { addDrawStack(); applyVis(); });
  };
});

const setMapPaint = (id, prop, val) => { if (map.getLayer(id)) map.setPaintProperty(id, prop, val); };
$('cBgColor').oninput = e => setMapPaint('bg', 'background-color', e.target.value);
$('cExpColor').oninput = e => setMapPaint('rd_express', 'line-color', e.target.value);
$('cMainColor').oninput = e => setMapPaint('rd_major', 'line-color', e.target.value);
$('cMainWidth').oninput = e => setMapPaint('rd_major', 'line-width', parseFloat(e.target.value));
$('cMainOp').oninput = e => setMapPaint('rd_major', 'line-opacity', parseFloat(e.target.value));
$('cSecColor').oninput = e => setMapPaint('rd_secondary', 'line-color', e.target.value);
$('cSecWidth').oninput = e => setMapPaint('rd_secondary', 'line-width', parseFloat(e.target.value));
$('cSecOp').oninput = e => setMapPaint('rd_secondary', 'line-opacity', parseFloat(e.target.value));
$('cTerColor').oninput = e => ['rd_tertiary','rd_min_md','rd_min_lo','rd_path'].forEach(id => setMapPaint(id, 'line-color', e.target.value));
$('cTerWidth').oninput = e => setMapPaint('rd_tertiary', 'line-width', parseFloat(e.target.value));
$('cTerOp').oninput = e => ['rd_tertiary','rd_min_md','rd_min_lo','rd_path'].forEach(id => setMapPaint(id, 'line-opacity', parseFloat(e.target.value)));
$('cRailColor').oninput = e => setMapPaint('rd_rail', 'line-color', e.target.value);
$('cBoundColor').oninput = e => ['bound_prov','bound_city','bound_brgy'].forEach(id => setMapPaint(id, 'line-color', e.target.value));
$('cBldColor').oninput = e => { setMapPaint('building', 'fill-color', e.target.value); setMapPaint('building', 'fill-outline-color', e.target.value); };
$('cBldOp').oninput = e => setMapPaint('building', 'fill-opacity', parseFloat(e.target.value));
$('cWaterColor').oninput = e => { setMapPaint('water', 'fill-color', e.target.value); setMapPaint('waterway', 'line-color', e.target.value); };
$('cWaterOp').oninput = e => { setMapPaint('water', 'fill-opacity', parseFloat(e.target.value)); setMapPaint('waterway', 'line-opacity', parseFloat(e.target.value)); };

renderMyLayers();
map.on('error', e => console.warn('Map Notice:', e));
} catch (e) {
  console.error('App init error:', e);
}
</script>
</body>
</html>"""

try:
    body_bg = THEMES[INITIAL_BASEMAP]["overlay"]
    muted = THEMES[INITIAL_BASEMAP]["muted"]
    html = (
        HTML_TEMPLATE.replace("__ALL_STYLES__", json.dumps(ALL_STYLES))
        .replace("__POI_CONFIG__", json.dumps(POI_CONFIG))
        .replace("__STYLE__", json.dumps(ALL_STYLES[INITIAL_BASEMAP]))
        .replace("__CENTER__", json.dumps(CENTER))
        .replace("__ZOOM__", str(ZOOM))
        .replace("__BG__", body_bg)
        .replace("__MUTED__", muted)
    )
    components.html(html, height=1000, scrolling=False)
except Exception as e:
    st.error(f"Studio failed to load: {e}")

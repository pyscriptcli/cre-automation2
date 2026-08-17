import json
import re
import streamlit as st
import streamlit.components.v1 as components
import requests

# ------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STREAMLIT CHROMIUM OVERRIDES
# ------------------------------------------------------------------------
st.set_page_config(
    page_title="Project Atlas Studio",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @font-face {
        font-family: 'Century Gothic Custom';
        src: local('Century Gothic'), local('CenturyGothic'), local('AppleGothic'), sans-serif;
    }
    * { font-family: 'Century Gothic Custom', -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif !important; }
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
        background-color: #070d18 !important;
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
        background: #070d18 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------------
# 2. SUPABASE REST INTEGRATION
# ------------------------------------------------------------------------
SUPABASE_URL = st.secrets.get("supabase", {}).get("url", "https://cyczyaswxkpdcremqnkn.supabase.co")
SUPABASE_KEY = st.secrets.get("supabase", {}).get("key", "sb_publishable_pUppHGjwmT1mLlhWGZH6Og_4GcCLCPR")

BASE_API_URL = SUPABASE_URL.replace("/rest/v1/", "").rstrip("/") + "/rest/v1"

def get_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

def fetch_projects():
    try:
        url = f"{BASE_API_URL}/map_projects?select=id,name,updated_at,basemap,zoom,center,features,custom_groups,layer_visibilities&order=updated_at.desc"
        res = requests.get(url, headers=get_headers(), timeout=5)
        if res.status_code == 200:
            return res.json()
        return []
    except Exception:
        return []

ALL_PROJECTS_LIST = fetch_projects()

# ------------------------------------------------------------------------
# 3. POI TAXONOMY & VECTOR BASEMAP THEMES
# ------------------------------------------------------------------------
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

THEMES = {
    "Midnight Blue": {
        "overlay": "#070d18", "text": "#d9b451", "land": "#0d1830",
        "landcover": "#0f1d33", "water": "#060d19", "waterway": "#081120",
        "parks": "#142440", "buildings": "#8e7258", "aeroway": "#152640",
        "rail": "#d9b451", "rd_express": "#ffaa00", "rd_major": "#e8b84a",
        "rd_secondary": "#c99c37", "rd_tertiary": "#7d5f14", "rd_min_md": "#46463e",
        "rd_min_lo": "#2f2f2a", "rd_path": "#4a4333", "rd_case": "#685c37",
        "sec_opacity": 0.8, "ter_opacity": 0.65, "building_opacity": 0.35,
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
    for z, val in stops: out += [z, val]
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
        "sources": {"omt": {"type": "vector", "url": "https://tiles.openfreemap.org/planet"}},
        "layers": [
            {"id": "bg", "type": "background", "paint": {"background-color": p["overlay"]}},
            {"id": "landcover", "type": "fill", "source": "omt", "source-layer": "landcover", "paint": {"fill-color": p["landcover"], "fill-opacity": 0.6}},
            {"id": "landuse", "type": "fill", "source": "omt", "source-layer": "landuse", "paint": {"fill-color": p["land"], "fill-opacity": 0.8}},
            {"id": "park", "type": "fill", "source": "omt", "source-layer": "park", "paint": {"fill-color": p["parks"]}},
            {"id": "water", "type": "fill", "source": "omt", "source-layer": "water", "paint": {"fill-color": p["water"]}},
            {"id": "waterway", "type": "line", "source": "omt", "source-layer": "waterway", "paint": {"line-color": p["waterway"], "line-width": w((9, 1), (20, 6))}},
            {"id": "aeroway", "type": "line", "source": "omt", "source-layer": "aeroway", "paint": {"line-color": p["aeroway"], "line-width": w((11, 1), (20, 12))}},
            {"id": "building-2d", "type": "fill", "source": "omt", "source-layer": "building", "minzoom": 13, "paint": {"fill-color": p["buildings"], "fill-opacity": p["building_opacity"], "fill-outline-color": p["buildings"]}},
            {
                "id": "building-3d", "type": "fill-extrusion", "source": "omt", "source-layer": "building", "minzoom": 14,
                "layout": {"visibility": "none"},
                "paint": {
                    "fill-extrusion-color": p["buildings"],
                    "fill-extrusion-height": ["coalesce", ["get", "render_height"], ["get", "height"], 12],
                    "fill-extrusion-base": ["coalesce", ["get", "render_min_height"], 0],
                    "fill-extrusion-opacity": 0.85
                }
            },
            {"id": "bound_prov", "type": "line", "source": "omt", "source-layer": "boundary", "filter": ["match", ["get", "admin_level"], [2, 4], True, False], "layout": {"visibility": "none"}, "paint": {"line-color": "#ff1e1e", "line-width": 2.2, "line-dasharray": [4, 2]}},
            {"id": "bound_city", "type": "line", "source": "omt", "source-layer": "boundary", "filter": ["match", ["get", "admin_level"], [6, 7, 8], True, False], "minzoom": 7, "layout": {"visibility": "none"}, "paint": {"line-color": "#ff1e1e", "line-width": 1.8, "line-dasharray": [2, 2], "line-opacity": 0.9}},
            {"id": "bound_brgy", "type": "line", "source": "omt", "source-layer": "boundary", "filter": ["match", ["get", "admin_level"], [9, 10], True, False], "minzoom": 11, "layout": {"visibility": "none"}, "paint": {"line-color": "#ff1e1e", "line-width": 1.2, "line-dasharray": [1, 2], "line-opacity": 0.8}},
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

# ------------------------------------------------------------------------
# 4. SINGLE-PAGE ARCHITECTURE (PROJECT ATLAS ENGINE)
# ------------------------------------------------------------------------
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"/>
<script src="https://unpkg.com/maplibre-gl@5/dist/maplibre-gl.js"></script>
<link href="https://unpkg.com/maplibre-gl@5/dist/maplibre-gl.css" rel="stylesheet"/>
<!-- GIS Importer Parsers -->
<script src="https://unpkg.com/@tmcw/togeojson@5.8.1/dist/togeojson.umd.js"></script>
<script src="https://unpkg.com/shpjs@latest/dist/shp.js"></script>
<script src="https://unpkg.com/jszip@3.10.1/dist/jszip.min.js"></script>

<style>
  @font-face {
    font-family: 'Century Gothic Custom';
    src: local('Century Gothic'), local('CenturyGothic'), local('AppleGothic'), sans-serif;
  }
  * { box-sizing: border-box; user-select: none; font-family: 'Century Gothic Custom', -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif; }
  html, body { margin: 0; padding: 0; width: 100vw; height: 100vh; overflow: hidden; background: #070d18; }
  #map { position: absolute; inset: 0; width: 100vw; height: 100vh; z-index: 1; }

  select, select option, input, textarea {
    background-color: #0d1527 !important;
    color: #f8fafc !important;
    outline: none;
  }
  select option:hover, select option:checked {
    background-color: #2563eb !important;
    color: #ffffff !important;
  }

  /* Island Toolbar Top */
  #top-toolbar-bar {
    position: absolute; top: 16px; left: 50%; transform: translateX(-50%); z-index: 20;
    background: rgba(10, 18, 32, 0.94); backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 40px; padding: 5px 12px;
    display: flex; align-items: center; gap: 5px; box-shadow: 0 16px 40px rgba(0, 0, 0, 0.65);
    color: #f0f6fc;
  }
  .tb-btn {
    width: 34px; height: 34px; display: grid; place-items: center;
    background: transparent; border: none; color: #94a3b8; border-radius: 50%;
    cursor: pointer; transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .tb-btn:hover { background: rgba(255, 255, 255, 0.12); color: #ffffff; transform: translateY(-1px); }
  .tb-btn.active { background: rgba(255, 255, 255, 0.2); color: #ffffff; }
  .tb-btn.primary-active { background: #2563eb; color: #ffffff; box-shadow: 0 0 14px rgba(37, 99, 235, 0.6); }
  .tb-sep { width: 1px; height: 18px; background: rgba(255, 255, 255, 0.12); margin: 0 4px; }

  #project-meta-cluster { display: flex; align-items: center; gap: 8px; padding: 0 6px; }
  #project-name-display { font-weight: 700; color: #38bdf8; font-size: 13px; max-width: 150px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer; }
  .save-badge { font-size: 10px; padding: 2px 8px; border-radius: 12px; font-weight: 600; background: rgba(255, 255, 255, 0.08); color: #94a3b8; border: 1px solid rgba(255, 255, 255, 0.1); display: flex; align-items: center; gap: 4px; }
  .save-badge.saving { color: #d9b451; border-color: rgba(217, 180, 81, 0.4); }
  .save-badge.saved { color: #3fb950; border-color: rgba(63, 185, 80, 0.4); }

  /* Right Floating Hub */
  .right-dock {
    position: absolute; top: 16px; right: 16px; bottom: 16px; width: 380px; z-index: 18;
    background: rgba(10, 18, 32, 0.95); backdrop-filter: blur(24px);
    border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 24px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.7); display: flex; flex-direction: column;
    overflow: hidden; color: #94a3b8;
  }
  .dock-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); }
  .dock-tabs { display: flex; background: rgba(0,0,0,0.4); border-radius: 12px; padding: 3px; border: 1px solid rgba(255,255,255,0.08); gap: 2px; }
  .dock-tab-btn { border: none; background: transparent; color: #94a3b8; font-size: 11px; font-weight: 700; padding: 6px 12px; border-radius: 9px; cursor: pointer; transition: 0.15s ease; }
  .dock-tab-btn.active { background: #2563eb; color: #ffffff; }

  .dock-body { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 14px; font-size: 12px; }
  .dock-section { display: flex; flex-direction: column; gap: 8px; }

  /* Nominatim Boundaries Auto-Suggest */
  .search-suggest-box { position: relative; width: 100%; }
  .suggest-results {
    position: absolute; top: calc(100% + 4px); left: 0; right: 0;
    background: #0d1527; border: 1px solid rgba(255,255,255,0.15); border-radius: 12px;
    max-height: 200px; overflow-y: auto; z-index: 100; box-shadow: 0 12px 30px rgba(0,0,0,0.8);
    display: none; flex-direction: column;
  }
  .suggest-item {
    padding: 8px 10px; cursor: pointer; border-bottom: 1px solid rgba(255,255,255,0.05);
    display: flex; flex-direction: column; gap: 2px; font-size: 11px;
  }
  .suggest-item:hover { background: rgba(37, 99, 235, 0.25); color: #ffffff; }

  /* Drag-and-Drop Layers Hub */
  .layer-drop-zone { min-height: 40px; display: flex; flex-direction: column; gap: 6px; }
  .layer-card {
    background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px; padding: 8px 10px; display: flex; flex-direction: column; gap: 6px;
    cursor: grab; transition: transform 0.15s ease, border-color 0.15s ease;
  }
  .layer-card:active { cursor: grabbing; }
  .layer-card.dragging { opacity: 0.4; transform: scale(0.98); }
  .layer-card.dragover { border: 1px dashed #38bdf8; }

  .layer-card-main-row { display: flex; align-items: center; justify-content: space-between; gap: 6px; }
  .layer-left-info { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; }
  .layer-name-input { border: 1px solid transparent; background: transparent; font-weight: 600; font-size: 12px; color: #f0f6fc; padding: 2px 4px; border-radius: 4px; width: 100%; }
  .layer-name-input:focus { border-color: #2563eb; background: rgba(0,0,0,0.4); outline: none; }
  
  .layer-actions-row { display: flex; align-items: center; gap: 2px; }
  .card-btn { background: transparent; border: none; color: #94a3b8; cursor: pointer; padding: 4px; border-radius: 6px; display: grid; place-items: center; }
  .card-btn:hover { color: #f0f6fc; background: rgba(255,255,255,0.12); }
  .card-btn.active { color: #38bdf8; }

  /* Popover Floating Panels */
  .float-popover {
    position: absolute; top: 72px; left: 50%; transform: translateX(-50%); z-index: 25;
    background: rgba(10, 18, 32, 0.97); backdrop-filter: blur(24px);
    border: 1px solid rgba(255, 255, 255, 0.14); border-radius: 20px; padding: 16px;
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.8); display: none; flex-direction: column;
    gap: 12px; font-size: 12px; color: #94a3b8;
  }
  .float-popover.open { display: flex; }
  .f-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
  .f-row input[type=range] { accent-color: #2563eb; width: 110px; cursor: pointer; }
  .f-row input[type=color] { border: none; width: 28px; height: 28px; border-radius: 6px; cursor: pointer; background: transparent; }
  .f-row input[type=text], .f-row select, .f-input { background: rgba(0,0,0,0.4); color: #f0f6fc; border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 8px; padding: 6px 8px; font-size: 12px; }

  .custom-marker-preview-box {
    display: flex; align-items: center; justify-content: center; width: 100%; height: 80px;
    border: 1px dashed rgba(255,255,255,0.2); border-radius: 12px; background: rgba(0,0,0,0.25);
    overflow: hidden;
  }

  /* Multi-Select Grouping Ribbon */
  #multiselect-group-ribbon {
    position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); z-index: 50;
    background: rgba(10, 18, 32, 0.95); backdrop-filter: blur(20px);
    border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 24px; padding: 8px 18px;
    display: none; align-items: center; gap: 14px; box-shadow: 0 12px 36px rgba(0,0,0,0.7);
    color: #f0f6fc; font-size: 12px; font-weight: 600;
  }

  /* Overpass Query Builder Area */
  .overpass-console {
    width: 100%; height: 90px; font-family: monospace !important; font-size: 11px;
    background: #050a14 !important; border: 1px solid rgba(255,255,255,0.12);
    border-radius: 8px; padding: 8px; color: #38bdf8 !important; resize: vertical;
  }

  /* Toast & Scrim */
  #hint-toast {
    position: absolute; bottom: 24px; left: 50%; transform: translateX(-50%); z-index: 40;
    background-color: rgba(10, 18, 32, 0.96); color: #f0f6fc; backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 20px; padding: 8px 20px;
    font-size: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.6); display: none;
  }

  #launcher-modal-scrim {
    position: fixed; inset: 0; z-index: 9999;
    display: flex; align-items: center; justify-content: center;
    background-color: rgba(5, 10, 20, 0.88); backdrop-filter: blur(16px);
    opacity: 0; pointer-events: none; transition: opacity 0.2s ease;
  }
  #launcher-modal-scrim.visible { opacity: 1; pointer-events: auto; }

  .ios-modal-card {
    width: 90%; max-width: 440px; max-height: 82vh;
    background-color: rgba(10, 18, 32, 0.98);
    border: 1px solid rgba(255, 255, 255, 0.16); border-radius: 24px;
    box-shadow: 0 32px 80px rgba(0, 0, 0, 0.85);
    display: flex; flex-direction: column; overflow: hidden; color: #ffffff;
  }
  .ios-modal-header { padding: 20px 24px 12px 24px; display: flex; flex-direction: column; gap: 4px; }
  .ios-modal-title { font-size: 20px; font-weight: 800; color: #ffffff; }
  .ios-modal-subtitle { font-size: 13px; color: rgba(255, 255, 255, 0.6); }

  .ios-seg {
    margin: 0 24px 14px 24px; display: flex; background: rgba(0, 0, 0, 0.4);
    padding: 3px; border-radius: 14px; border: 1px solid rgba(255, 255, 255, 0.08);
  }
  .ios-seg-btn {
    flex: 1; border: none; background: transparent; color: rgba(255, 255, 255, 0.65);
    font-size: 12px; font-weight: 600; padding: 7px 0; border-radius: 11px; cursor: pointer;
    transition: all 0.15s ease;
  }
  .ios-seg-btn.active { background: rgba(255, 255, 255, 0.18); color: #ffffff; }
  .ios-modal-body { padding: 0 24px 22px 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
</style>
</head>
<body>

<div id="map"></div>

<!-- Top Unified Toolbar Island -->
<div id="top-toolbar-bar">
  <button class="tb-btn" id="btn-home-dialog" title="Workspaces (Home)">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
  </button>
  
  <div id="project-meta-cluster">
    <span id="project-name-display" title="Click to rename workspace">Untitled Project 1</span>
    <div class="save-badge" id="save-status-badge">
      <span id="save-dot">●</span>
      <span id="save-text">Saved</span>
    </div>
  </div>

  <button class="tb-btn" id="btn-save-project" title="Save Workspace (Ctrl+S)" style="color:#3fb950;">
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>
  </button>

  <div class="tb-sep"></div>

  <!-- Merged Pointer / Select & Point Edit Mode -->
  <button class="tb-btn" id="btn-pointer-mode" title="Select, Drag & Edit Points">
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3l7 18 3-7 7-3L3 3z"></path></svg>
  </button>

  <div class="tb-sep"></div>

  <button class="tb-btn tool" data-tool="polygon" title="Polygon">
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 3 20 9 17 19 7 19 4 9"></polygon></svg>
  </button>
  <button class="tb-btn tool" data-tool="rectangle" title="Rectangle">
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16" rx="1"></rect></svg>
  </button>
  <button class="tb-btn tool" data-tool="circle" title="Circle (Radius Adjustable)">
    <svg viewBox="0 0 24 24" width="14" height="14"><circle cx="12" cy="12" r="8" fill="currentColor"></circle></svg>
  </button>
  <button class="tb-btn tool" data-tool="polyline" title="Polyline">
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19L11 8l5 6 4-10"></path></svg>
  </button>
  <button class="tb-btn tool" data-tool="route" title="Route Engine">
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="5" cy="19" r="2.5"></circle><circle cx="19" cy="5" r="2.5"></circle><path d="M7 17c4-1 3-8 8-9"></path></svg>
  </button>
  <button class="tb-btn tool" data-tool="marker" title="Marker Pin & Custom Image">
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"></path><circle cx="12" cy="10" r="2.5"></circle></svg>
  </button>
  <button class="tb-btn tool" data-tool="textbox" title="Text Label">
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 7 4 4 20 4 20 7"></polyline><line x1="9" y1="20" x2="15" y2="20"></line><line x1="12" y1="4" x2="12" y2="20"></line></svg>
  </button>

  <div class="tb-sep"></div>

  <button class="tb-btn" id="btn-import-dialog" title="Import Spatial Files (KML, KMZ, GeoJSON, SHP)">
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
  </button>
  <button class="tb-btn" id="btn-custom-map" title="Basemap Style">
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon><line x1="8" y1="2" x2="8" y2="18"></line><line x1="16" y1="6" x2="16" y2="22"></line></svg>
  </button>
  <button class="tb-btn" id="btn-export-dialog" title="Export Map">
    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
  </button>
</div>

<!-- Unified Right Floating Dock -->
<div class="right-dock" id="unified-right-dock">
  <div class="dock-header">
    <div class="dock-tabs">
      <button class="dock-tab-btn active" data-tab="tab-layers">Layers</button>
      <button class="dock-tab-btn" data-tab="tab-browser">Data Browser</button>
      <button class="dock-tab-btn" data-tab="tab-query">Overpass</button>
    </div>
    <span class="save-badge" id="layer-badge-count">0</span>
  </div>

  <div class="dock-body">
    <!-- TAB 1: LAYERS (Draggable, Chronological, Multi-Select Inline) -->
    <div id="tab-layers" class="dock-section">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
        <span style="font-weight:700; color:#f0f6fc; font-size:12px;">Workspace Hierarchy</span>
        <button id="btnAddCustomGroup" style="background:#1e293b; border:1px solid rgba(255,255,255,0.1); color:#38bdf8; border-radius:6px; font-size:10px; font-weight:700; padding:3px 8px; cursor:pointer;">+ NEW GROUP</button>
      </div>
      <div id="layers-tree-container" class="layer-drop-zone"></div>
    </div>

    <!-- TAB 2: DATA BROWSER & NOMINATIM SEARCH -->
    <div id="tab-browser" class="dock-section" style="display:none;">
      <div style="font-weight:700; color:#f0f6fc; font-size:12px;">Administrative Boundaries</div>
      <div class="search-suggest-box">
        <input type="text" id="targetBoundaryInput" class="f-input" style="width:100%;" placeholder="Search City/State/Boundary (Nominatim)..." autocomplete="off" />
        <div id="boundarySuggestResults" class="suggest-results"></div>
      </div>

      <div style="display:flex; gap:4px; margin-top:4px;">
        <label style="display:flex; align-items:center; gap:4px; font-size:11px; color:#94a3b8;"><input type="checkbox" data-g="bound_prov"> Provinces</label>
        <label style="display:flex; align-items:center; gap:4px; font-size:11px; color:#94a3b8;"><input type="checkbox" data-g="bound_city"> Cities</label>
        <label style="display:flex; align-items:center; gap:4px; font-size:11px; color:#94a3b8;"><input type="checkbox" data-g="bound_brgy"> Barangays</label>
      </div>

      <div style="font-weight:700; color:#f0f6fc; font-size:12px; margin-top:8px;">Trade Area Scanner</div>
      <div style="display:flex; flex-direction:column; gap:6px; background:rgba(0,0,0,0.3); padding:8px; border-radius:10px; border:1px solid rgba(255,255,255,0.06);">
        <label style="font-size:11px; color:#94a3b8;">Target Area:</label>
        <select id="tradePolygonSelect" class="f-input"><option value="">-- Choose polygon --</option></select>
        <label style="font-size:11px; color:#94a3b8;">Category:</label>
        <select id="tradeCategorySelect" class="f-input"></select>
        <button id="btnScanTradeArea" style="background:#2563eb; color:#fff; border:none; border-radius:8px; padding:7px; font-weight:700; font-size:11px; cursor:pointer;">Scan Points of Interest</button>
      </div>
      <div id="tradeResults" style="font-size:11px; color:#94a3b8; max-height:140px; overflow-y:auto;"></div>
    </div>

    <!-- TAB 3: CUSTOM OVERPASS QUERY BUILDER -->
    <div id="tab-query" class="dock-section" style="display:none;">
      <div style="font-weight:700; color:#f0f6fc; font-size:12px;">Overpass QL Console</div>
      <textarea id="overpassQueryText" class="overpass-console" placeholder="node['amenity'='cafe']({{bbox}});out center;"></textarea>
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-size:10px; color:#64748b;">Use {{bbox}} for map bounds</span>
        <button id="btnRunOverpassQuery" style="background:#2563eb; color:#fff; border:none; border-radius:8px; padding:6px 14px; font-weight:700; font-size:11px; cursor:pointer;">Execute Query</button>
      </div>
      <div id="overpassQueryStatus" style="font-size:11px; color:#38bdf8;"></div>
    </div>
  </div>
</div>

<!-- Contextual Popovers -->
<div id="popup-marker-settings" class="float-popover">
  <div style="font-weight:700; font-size:12px; color:#f0f6fc;">Marker & Custom Image Icon</div>
  <div class="f-row">
    <span>Icon Style</span>
    <select id="markerTypeSelect" class="f-input" style="width:130px;">
      <option value="vector">Vector Pin</option>
      <option value="custom-flat">Custom Image (Flat)</option>
      <option value="custom-frame-2d">Custom Image (2D Frame)</option>
      <option value="custom-frame-3d">Custom Image (3D Popup)</option>
    </select>
  </div>
  
  <div id="vectorMarkerOptions" class="f-row">
    <span>Color</span><input type="color" id="mColor" value="#003366">
  </div>

  <div id="customMarkerUploadRow" class="dock-section" style="display:none;">
    <label style="font-size:11px; color:#94a3b8;">Upload Image (Max 5 MB)</label>
    <input type="file" id="customMarkerFileInput" accept="image/*" class="f-input" style="font-size:10px;" />
    <div class="custom-marker-preview-box" id="markerPreviewContainer">
      <span style="color:#64748b; font-size:10px;">No image selected</span>
    </div>
  </div>

  <div class="f-row"><span>Scale</span><input type="range" id="mSize" min="0.4" max="2.2" step="0.1" value="0.9"></div>
</div>

<div id="popup-text-settings" class="float-popover">
  <div style="font-weight:700; font-size:12px; color:#f0f6fc;">Label Properties</div>
  <input type="text" id="tContent" class="f-input" value="Custom Label" placeholder="Text..."/>
  <div class="f-row"><span>Font Size</span><input type="range" id="tSize" min="10" max="42" step="1" value="16"></div>
  <div class="f-row"><span>Color</span><input type="color" id="tColor" value="#d9b451"></div>
</div>

<!-- Universal GIS File Importer Modal -->
<div id="popup-import-dialog" class="float-popover" style="width:340px;">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <span style="font-weight:700; color:#f0f6fc;">Native GIS Importer</span>
    <button class="card-btn" onclick="$('popup-import-dialog').classList.remove('open')">✕</button>
  </div>
  <div style="font-size:11px; color:#94a3b8;">Import KML, KMZ, GeoJSON, JSON, or zipped Shapefile (.shp).</div>
  <input type="file" id="gisFileInput" accept=".kml,.kmz,.geojson,.json,.zip" class="f-input" />
  <button id="btnProcessImport" style="background:#2563eb; color:#fff; border:none; border-radius:8px; padding:8px; font-weight:700; cursor:pointer;">Parse & Load onto Map</button>
</div>

<!-- Map Basemap Popover -->
<div id="popup-custom-map" class="float-popover" style="width:320px;">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <span style="font-weight:700; color:#f0f6fc;">Basemap Presets</span>
    <button class="card-btn" onclick="$('popup-custom-map').classList.remove('open')">✕</button>
  </div>
  <div style="display:flex; flex-wrap:wrap; gap:4px;" id="presetBtnList"></div>
  <div class="f-row" style="margin-top:6px;"><span>Backdrop</span><input type="color" id="cBgColor" value="#070d18"></div>
  <div class="f-row"><span>Expressways</span><input type="color" id="cExpColor" value="#ffaa00"></div>
  <div class="f-row"><span>Main Roads</span><input type="color" id="cMainColor" value="#e8b84a"></div>
  <div class="f-row"><span>Buildings</span><input type="color" id="cBldColor" value="#8e7258"></div>
</div>

<!-- Export Popover -->
<div id="popup-export" class="float-popover" style="width:320px;">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <span style="font-weight:700; color:#f0f6fc;">Export Canvas</span>
    <button class="card-btn" onclick="$('popup-export').classList.remove('open')">✕</button>
  </div>
  <img id="exportPreviewImg" style="width:100%; height:110px; object-fit:cover; background:#000; border-radius:8px; border:1px solid rgba(255,255,255,0.1);" />
  <div class="f-row">
    <span>Ratio</span>
    <select id="exportRatioSelect" class="f-input" style="width:120px;">
      <option value="screen">Current View</option>
      <option value="1:1">Square (1:1)</option>
      <option value="16:9">Wide (16:9)</option>
      <option value="a4">Print (A4)</option>
    </select>
  </div>
  <button id="triggerExportBtn" style="background:#2563eb; color:#fff; border:none; padding:8px; border-radius:8px; font-weight:700; cursor:pointer;">Download PNG</button>
</div>

<!-- Multi-select Ribbon -->
<div id="multiselect-group-ribbon">
  <span id="multiselect-count-text">0 selected</span>
  <button id="btnGroupSelected" style="background:#2563eb; color:#fff; border:none; padding:5px 12px; border-radius:12px; font-weight:700; font-size:11px; cursor:pointer;">Create Group</button>
  <button id="btnDeleteSelected" style="background:rgba(239,68,68,0.2); color:#ef4444; border:1px solid rgba(239,68,68,0.4); padding:5px 12px; border-radius:12px; font-weight:700; font-size:11px; cursor:pointer;">Delete</button>
</div>

<!-- Launcher Scrim Modal -->
<div id="launcher-modal-scrim" class="visible">
  <div class="ios-modal-card">
    <div class="ios-modal-header">
      <div class="ios-modal-title">Project Atlas</div>
      <div class="ios-modal-subtitle">Select workspace.</div>
    </div>

    <div class="ios-seg">
      <button class="ios-seg-btn active" id="seg-btn-existing">Existing Workspaces</button>
      <button class="ios-seg-btn" id="seg-btn-new">Create New</button>
    </div>

    <div class="ios-modal-body" id="seg-content-existing">
      <div id="existing-projects-container" style="display:flex; flex-direction:column; gap:8px;"></div>
    </div>

    <div class="ios-modal-body" id="seg-content-new" style="display:none;">
      <label style="font-size:11px; font-weight:700; color:#94a3b8;">Workspace Name</label>
      <input class="f-input" id="new-proj-name" placeholder="e.g. Untitled Project 1" />
      <button id="btn-create-project-submit" style="background:#2563eb; color:#fff; border:none; border-radius:12px; padding:10px; font-weight:700; cursor:pointer; margin-top:4px;">Create Workspace</button>
    </div>
  </div>
</div>

<div id="hint-toast"></div>

<script>
try {
const ALL_STYLES = __ALL_STYLES__;
const POI_CONFIG = __POI_CONFIG__;
const SUPABASE_URL = "__SUPABASE_URL__";
const SUPABASE_KEY = "__SUPABASE_KEY__";
let ALL_PROJECTS = __ALL_PROJECTS_JSON__;

let currentProjectId = "__PROJECT_ID__";
let currentProjectName = "__PROJECT_NAME__";
let currentStyleName = "__INITIAL_BASEMAP__";

const map = new maplibregl.Map({
  container: 'map',
  style: ALL_STYLES[currentStyleName] || ALL_STYLES["Midnight Blue"],
  center: __CENTER__,
  zoom: __ZOOM__,
  attributionControl: false,
  fadeDuration: 0,
  preserveDrawingBuffer: true
});
map.getCanvas().addEventListener('contextmenu', e => e.preventDefault());

// ----------------- State -----------------
let features = __INITIAL_FEATURES__;
let fid = features.reduce((max, f) => Math.max(max, f.id || 0), 0);
let customGroups = __INITIAL_CUSTOM_GROUPS__ || { "Trade Area Scan": { collapsed: false, ids: [] } };

let activeTool = null;
let pointerMode = true; // Unified select, drag & edit points mode
let selectedId = null;
let selectedIdsSet = new Set();
let draft = [], cursorLL = null;
let isDirty = false;

// Custom Marker States
let customMarkerBase64 = null;
let markerType = 'vector';
let markerColor = '#003366';
let markerIconSize = 0.9;

// Interaction & Vertex Dragging States
let isDraggingShape = false, dragFeatureId = null, dragStartCoord = null, dragOriginalCoords = null;
let isDraggingVertex = false, draggedVertexIdx = -1, draggedPolyId = null;
let isDraggingRadius = false, radiusCenterLL = null;

const vis = { bound_prov: false, bound_city: false, bound_brgy: false };
const VIS_MAP = { bound_prov: ['bound_prov'], bound_city: ['bound_city'], bound_brgy: ['bound_brgy'] };

const $ = id => document.getElementById(id);
const hint = t => { $('hint-toast').style.display = t ? 'block' : 'none'; $('hint-toast').textContent = t || ''; };

const setSaveBadgeStatus = status => {
  const badge = $('save-status-badge');
  const text = $('save-text');
  badge.className = 'save-badge ' + status;
  if (status === 'saving') text.textContent = 'Saving...';
  else if (status === 'saved') text.textContent = 'Saved';
  else text.textContent = 'Unsaved';
};

const markDirty = () => {
  isDirty = true;
  setSaveBadgeStatus('unsaved');
};

const closeFloatingCards = () => {
  ['popup-marker-settings','popup-text-settings','popup-custom-map','popup-export','popup-import-dialog'].forEach(id => $(id).classList.remove('open'));
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

// ----------------- Dock Navigation -----------------
document.querySelectorAll('.dock-tab-btn').forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll('.dock-tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    ['tab-layers','tab-browser','tab-query'].forEach(t => $(t).style.display = 'none');
    $(btn.dataset.tab).style.display = 'flex';
  };
});

// ----------------- Custom Marker Processor (Max 5MB) -----------------
$('markerTypeSelect').onchange = e => {
  markerType = e.target.value;
  $('vectorMarkerOptions').style.display = markerType === 'vector' ? 'flex' : 'none';
  $('customMarkerUploadRow').style.display = markerType !== 'vector' ? 'flex' : 'none';
};

$('customMarkerFileInput').onchange = e => {
  const file = e.target.files[0];
  if (!file) return;
  if (file.size > 5 * 1024 * 1024) {
    alert("Image exceeds 5MB limit.");
    e.target.value = '';
    return;
  }
  const reader = new FileReader();
  reader.onload = ev => {
    customMarkerBase64 = ev.target.result;
    $('markerPreviewContainer').innerHTML = `<img src="${customMarkerBase64}" style="max-height:70px; max-width:90%; object-fit:contain;"/>`;
  };
  reader.readAsDataURL(file);
};

function createMarkerCanvas(shape, color, base64Img, frameType) {
  const c = document.createElement('canvas');
  c.width = 64; c.height = 64;
  const ctx = c.getContext('2d');
  ctx.clearRect(0,0,64,64);

  if (base64Img && frameType !== 'vector') {
    const img = new Image();
    img.src = base64Img;
    if (frameType === 'custom-frame-2d') {
      ctx.fillStyle = '#ffffff';
      ctx.beginPath(); ctx.roundRect(6, 6, 52, 52, 10); ctx.fill();
      ctx.strokeStyle = '#2563eb'; ctx.lineWidth = 3; ctx.stroke();
    } else if (frameType === 'custom-frame-3d') {
      ctx.fillStyle = '#0f172a';
      ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = 8; ctx.shadowOffsetY = 4;
      ctx.beginPath(); ctx.roundRect(4, 4, 56, 50, 8); ctx.fill();
      ctx.shadowColor = 'transparent';
      ctx.fillStyle = '#2563eb'; ctx.beginPath(); ctx.moveTo(26, 54); ctx.lineTo(38, 54); ctx.lineTo(32, 62); ctx.fill();
    }
    return new Promise(resolve => {
      img.onload = () => {
        const offset = frameType === 'custom-flat' ? 4 : 10;
        const size = frameType === 'custom-flat' ? 56 : 44;
        ctx.drawImage(img, offset, offset, size, size);
        resolve(c);
      };
      img.onerror = () => resolve(c);
    });
  }

  // Standard Pin Vector fallback
  ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 3; ctx.fillStyle = color;
  ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.arc(32, 24, 16, Math.PI * 0.8, Math.PI * 0.2, false);
  ctx.lineTo(32, 58);
  ctx.closePath();
  ctx.fill(); ctx.stroke();
  ctx.beginPath(); ctx.fillStyle = '#ffffff'; ctx.arc(32, 24, 5, 0, Math.PI * 2); ctx.fill();
  return Promise.resolve(c);
}

async function registerIconImage(iconKey, shape, color, base64Img, frameType) {
  if (!map.hasImage(iconKey)) {
    const cv = await createMarkerCanvas(shape, color, base64Img, frameType);
    const imgData = cv.getContext('2d').getImageData(0, 0, 64, 64);
    try { map.addImage(iconKey, imgData, { pixelRatio: 2 }); } catch(e) {}
  }
}

// ----------------- Unified Vector Layer System -----------------
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

    map.addLayer({
      id: 'draw-fill', type: 'fill', source: 'draw',
      filter: ['==', ['geometry-type'], 'Polygon'],
      paint: {
        'fill-color': ['coalesce', ['get', 'fillColor'], ['get', 'color'], '#e8b84a'],
        'fill-opacity': ['*', ['coalesce', ['get', 'fillOpacity'], 0.35], ['get', 'visible']]
      }
    });

    map.addLayer({
      id: 'draw-outline', type: 'line', source: 'draw',
      filter: ['==', ['geometry-type'], 'Polygon'],
      paint: {
        'line-color': ['coalesce', ['get', 'borderColor'], ['get', 'color'], '#e8b84a'],
        'line-width': ['coalesce', ['get', 'width'], 3],
        'line-opacity': ['*', ['coalesce', ['get', 'borderOpacity'], 0.9], ['get', 'visible']]
      }
    });

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
        'text-halo-color': '#070d18',
        'text-halo-width': 2
      }
    });

    // Vertex gizmo & circle radius handles
    map.addSource('vertex-handles', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addLayer({
      id: 'vertex-points', type: 'circle', source: 'vertex-handles',
      paint: {
        'circle-color': ['case', ['get', 'isRadiusGizmo'], '#38bdf8', '#ffffff'],
        'circle-radius': ['case', ['get', 'isRadiusGizmo'], 7, 5],
        'circle-stroke-color': '#2563eb',
        'circle-stroke-width': 2
      }
    });

    // Draft preview source
    map.addSource('draft', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addLayer({
      id: 'draft-line', type: 'line', source: 'draft',
      filter: ['==', ['geometry-type'], 'LineString'],
      paint: { 'line-color': '#38bdf8', 'line-width': 2.5, 'line-dasharray': [2, 2] }
    });
  } else {
    map.getSource('draw').setData(fc(features));
  }
}

const syncDraw = () => { 
  if (map.getSource('draw')) map.getSource('draw').setData(fc(features)); 
  syncVertexHandles();
};

function syncVertexHandles() {
  if (!map.getSource('vertex-handles')) return;
  if (!pointerMode || !selectedId) {
    map.getSource('vertex-handles').setData({ type: 'FeatureCollection', features: [] });
    return;
  }
  const f = features.find(x => x.id === selectedId);
  if (!f) return;

  const handleFeats = [];
  if (['polygon', 'rectangle'].includes(f.kind) && f.geometry.coordinates && f.geometry.coordinates[0]) {
    const coords = f.geometry.coordinates[0];
    for (let i = 0; i < coords.length - 1; i++) {
      handleFeats.push({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: coords[i] },
        properties: { polyId: f.id, vIdx: i }
      });
    }
  } else if (['polyline', 'route'].includes(f.kind) && f.geometry.coordinates) {
    f.geometry.coordinates.forEach((c, idx) => {
      handleFeats.push({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: c },
        properties: { polyId: f.id, vIdx: idx, isLine: true }
      });
    });
  } else if (f.kind === 'circle' && f.geometry.coordinates && f.geometry.coordinates[0]) {
    const cEdge = f.geometry.coordinates[0][0];
    handleFeats.push({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: cEdge },
      properties: { polyId: f.id, isRadiusGizmo: true }
    });
  }
  map.getSource('vertex-handles').setData({ type: 'FeatureCollection', features: handleFeats });
}

function renderDraft() {
  if (!map.getSource('draft')) return;
  const f = [];
  const ln = c => ({ type: 'Feature', geometry: { type: 'LineString', coordinates: c }, properties: {} });
  if (['polyline', 'route'].includes(activeTool) && draft.length) {
    f.push(ln(cursorLL ? [...draft, cursorLL] : draft));
  } else if (activeTool === 'polygon' && draft.length) {
    const pts = cursorLL ? [...draft, cursorLL] : draft;
    if (pts.length > 1) f.push(ln([...pts, pts[0]]));
  } else if (activeTool === 'rectangle' && draft.length === 1 && cursorLL) {
    f.push(ln(rectCoords(draft[0], cursorLL)[0]));
  } else if (activeTool === 'circle' && draft.length === 1 && cursorLL) {
    const { coords, r } = circleCoords(draft[0], cursorLL);
    f.push(ln(coords[0]));
    hint(`Radius: ${r > 1000 ? (r/1000).toFixed(2)+' km' : Math.round(r)+' m'}`);
  }
  map.getSource('draft').setData({ type: 'FeatureCollection', features: f });
}

// ----------------- Geometry Formulas -----------------
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
  return { coords: [coords], r, center: c };
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

// ----------------- Tool Management & Interactions -----------------
$('btn-pointer-mode').onclick = () => {
  pointerMode = !pointerMode;
  $('btn-pointer-mode').classList.toggle('primary-active', pointerMode);
  resetActiveTools();
  closeFloatingCards();
  syncVertexHandles();
  hint(pointerMode ? 'Select shapes to drag or edit points.' : '');
};

document.querySelectorAll('.tool').forEach(btn => {
  btn.onclick = () => {
    const t = btn.dataset.tool;
    if (activeTool === t) {
      resetActiveTools();
      closeFloatingCards();
    } else {
      document.querySelectorAll('.tool').forEach(b => b.classList.remove('primary-active'));
      pointerMode = false;
      $('btn-pointer-mode').classList.remove('primary-active');
      activeTool = t;
      btn.classList.add('primary-active');
      draft = [];
      renderDraft();
      closeFloatingCards();

      map.getCanvas().style.cursor = 'crosshair';
      map.doubleClickZoom.disable();

      if (t === 'marker') $('popup-marker-settings').classList.add('open');
      if (t === 'textbox') $('popup-text-settings').classList.add('open');
    }
  };
});

map.on('mousemove', e => {
  cursorLL = [e.lngLat.lng, e.lngLat.lat];
  if (activeTool) renderDraft();

  // Drag Entire Shape
  if (isDraggingShape && dragFeatureId) {
    const dx = cursorLL[0] - dragStartCoord[0];
    const dy = cursorLL[1] - dragStartCoord[1];
    const f = features.find(x => x.id === dragFeatureId);
    if (!f) return;

    const translate = coords => {
      if (typeof coords[0] === 'number') return [coords[0] + dx, coords[1] + dy];
      return coords.map(translate);
    };
    f.geometry.coordinates = translate(dragOriginalCoords);
    syncDraw();
    markDirty();
  }

  // Drag Polygon / Line Vertex
  if (isDraggingVertex && draggedPolyId != null && draggedVertexIdx >= 0) {
    const f = features.find(x => x.id === draggedPolyId);
    if (f) {
      if (['polyline', 'route'].includes(f.kind)) {
        f.geometry.coordinates[draggedVertexIdx] = cursorLL;
      } else if (f.geometry.coordinates && f.geometry.coordinates[0]) {
        const coords = f.geometry.coordinates[0];
        coords[draggedVertexIdx] = cursorLL;
        if (draggedVertexIdx === 0) coords[coords.length - 1] = cursorLL;
      }
      syncDraw();
      markDirty();
    }
  }

  // Drag Circle Radius Gizmo
  if (isDraggingRadius && draggedPolyId != null && radiusCenterLL) {
    const f = features.find(x => x.id === draggedPolyId);
    if (f) {
      const { coords, r } = circleCoords(radiusCenterLL, cursorLL);
      f.geometry.coordinates = coords;
      f.props.radiusMeters = r;
      syncDraw();
      markDirty();
    }
  }
});

map.on('mousedown', e => {
  if (!pointerMode) return;
  
  // 1. Check Vertex or Radius Gizmo Hit
  const vHits = map.queryRenderedFeatures(e.point, { layers: ['vertex-points'] });
  if (vHits.length) {
    const p = vHits[0].properties;
    draggedPolyId = parseInt(p.polyId, 10);
    if (p.isRadiusGizmo) {
      isDraggingRadius = true;
      const f = features.find(x => x.id === draggedPolyId);
      radiusCenterLL = f.props.centerLL || f.geometry.coordinates[0][32] || cursorLL;
    } else {
      isDraggingVertex = true;
      draggedVertexIdx = parseInt(p.vIdx, 10);
    }
    map.dragPan.disable();
    return;
  }

  // 2. Check Feature Click / Drag Hit
  const fs = map.queryRenderedFeatures(e.point, { layers: ['draw-fill','draw-line','draw-outline','draw-marker','draw-text'] });
  if (fs.length && fs[0].properties.id != null) {
    const targetId = parseInt(fs[0].properties.id, 10);
    selectedId = targetId;
    isDraggingShape = true;
    dragFeatureId = targetId;
    dragStartCoord = cursorLL;
    const f = features.find(x => x.id === targetId);
    if (f) dragOriginalCoords = JSON.parse(JSON.stringify(f.geometry.coordinates));
    syncVertexHandles();
    renderLayersTree();
    map.dragPan.disable();
  } else {
    selectedId = null;
    syncVertexHandles();
    renderLayersTree();
  }
});

map.on('mouseup', () => {
  if (isDraggingShape || isDraggingVertex || isDraggingRadius) {
    isDraggingShape = false;
    isDraggingVertex = false;
    isDraggingRadius = false;
    dragFeatureId = null;
    draggedPolyId = null;
    draggedVertexIdx = -1;
    map.dragPan.enable();
    markDirty();
  }
});

map.on('click', async e => {
  if (!activeTool) return;
  const ll = [e.lngLat.lng, e.lngLat.lat];

  if (activeTool === 'marker') {
    const iconKey = `ico_${markerType}_${markerColor.replace('#','')}_${Date.now()}`;
    await registerIconImage(iconKey, 'pin', markerColor, customMarkerBase64, markerType);
    addFeatureRecord('marker', { type: 'Point', coordinates: ll }, {
      iconKey, iconSize: markerIconSize, markerType
    });
    resetActiveTools();
    closeFloatingCards();
  } else if (activeTool === 'textbox') {
    addFeatureRecord('text', { type: 'Point', coordinates: ll }, {
      text: $('tContent').value || 'Label',
      fontSize: parseInt($('tSize').value, 10),
      color: $('tColor').value
    });
    resetActiveTools();
    closeFloatingCards();
  } else if (activeTool === 'polyline') {
    if (draft.length >= 2) {
      const pScreen = map.project(ll), lastPt = map.project(draft[draft.length - 1]);
      if (Math.hypot(pScreen.x - lastPt.x, pScreen.y - lastPt.y) < 18) {
        addFeatureRecord('polyline', { type: 'LineString', coordinates: draft });
        resetActiveTools();
        return;
      }
    }
    draft.push(ll);
  } else if (activeTool === 'polygon') {
    if (draft.length >= 3) {
      const pScreen = map.project(ll), firstPt = map.project(draft[0]);
      if (Math.hypot(pScreen.x - firstPt.x, pScreen.y - firstPt.y) < 20) {
        addFeatureRecord('polygon', { type: 'Polygon', coordinates: [[...draft, draft[0]]] });
        resetActiveTools();
        return;
      }
    }
    draft.push(ll);
  } else if (activeTool === 'rectangle') {
    draft.push(ll);
    if (draft.length === 2) {
      addFeatureRecord('rectangle', { type: 'Polygon', coordinates: rectCoords(draft[0], draft[1]) });
      resetActiveTools();
    }
  } else if (activeTool === 'circle') {
    draft.push(ll);
    if (draft.length === 2) {
      const { coords, r, center } = circleCoords(draft[0], draft[1]);
      addFeatureRecord('circle', { type: 'Polygon', coordinates: coords }, { radiusMeters: r, centerLL: center });
      resetActiveTools();
    }
  } else if (activeTool === 'route') {
    if (draft.length >= 2) {
      const pScreen = map.project(ll), lastPt = map.project(draft[draft.length - 1]);
      if (Math.hypot(pScreen.x - lastPt.x, pScreen.y - lastPt.y) < 22) {
        fetchMultiPointRoute(draft);
        resetActiveTools();
        return;
      }
    }
    draft.push(ll);
  }
  renderDraft();
});

function addFeatureRecord(kind, geometry, customProps = {}, targetGroup = null, explicitName = null) {
  const newId = ++fid;
  const feat = {
    id: newId,
    name: explicitName || `${kind.charAt(0).toUpperCase() + kind.slice(1)} ${newId}`,
    kind: kind,
    geometry: geometry,
    props: {
      color: '#e8b84a',
      borderColor: '#e8b84a',
      borderOpacity: 0.9,
      width: 3,
      fillColor: '#e8b84a',
      fillOpacity: 0.35,
      visible: 1,
      ...customProps
    }
  };
  features.push(feat);
  if (targetGroup && customGroups[targetGroup]) customGroups[targetGroup].ids.push(newId);
  syncDraw();
  renderLayersTree();
  markDirty();
  return feat;
}

function fetchMultiPointRoute(pts) {
  hint('Calculating route…');
  const coordStr = pts.map(p => `${p[0]},${p[1]}`).join(';');
  fetch(`https://router.project-osrm.org/route/v1/driving/${coordStr}?overview=full&geometries=geojson`)
    .then(r => r.json())
    .then(j => {
      const geom = (j.routes && j.routes[0]) ? j.routes[0].geometry : { type: 'LineString', coordinates: pts };
      addFeatureRecord('route', geom, { color: '#38bdf8', borderColor: '#38bdf8', width: 4 });
      hint('');
    })
    .catch(() => addFeatureRecord('route', { type: 'LineString', coordinates: pts }));
}

// ----------------- Nominatim Disambiguation Boundary Search -----------------
let searchDebounceTimer = null;
$('targetBoundaryInput').oninput = e => {
  clearTimeout(searchDebounceTimer);
  const q = e.target.value.trim();
  if (!q) { $('boundarySuggestResults').style.display = 'none'; return; }

  searchDebounceTimer = setTimeout(() => {
    fetch(`https://nominatim.openstreetmap.org/search?format=json&polygon_geojson=1&q=${encodeURIComponent(q)}`)
      .then(r => r.json())
      .then(results => {
        if (!results.length) { $('boundarySuggestResults').style.display = 'none'; return; }
        $('boundarySuggestResults').style.display = 'flex';
        $('boundarySuggestResults').innerHTML = results.slice(0, 6).map((item, idx) => `
          <div class="suggest-item" data-idx="${idx}">
            <strong style="color:#f0f6fc;">${item.display_name.split(',')[0]}</strong>
            <span style="color:#64748b; font-size:10px;">${item.display_name}</span>
          </div>
        `).join('');

        $('boundarySuggestResults').querySelectorAll('.suggest-item').forEach(el => {
          el.onclick = () => {
            const item = results[parseInt(el.dataset.idx, 10)];
            $('targetBoundaryInput').value = item.display_name.split(',')[0];
            $('boundarySuggestResults').style.display = 'none';

            if (item.geojson && (item.geojson.type === 'Polygon' || item.geojson.type === 'MultiPolygon')) {
              addFeatureRecord('polygon', item.geojson, {
                borderColor: '#ff1e1e', borderOpacity: 1.0, width: 3, fillColor: '#ff1e1e', fillOpacity: 0.15
              }, null, item.display_name.split(',')[0] + ' Boundary');
              if (item.boundingbox) {
                map.fitBounds([
                  [parseFloat(item.boundingbox[2]), parseFloat(item.boundingbox[0])],
                  [parseFloat(item.boundingbox[3]), parseFloat(item.boundingbox[1])]
                ], { padding: 60 });
              }
              hint('Boundary Highlighted');
            } else { hint('Polygon data unavailable for selection.'); }
          };
        });
      });
  }, 300);
};

// ----------------- Overpass Custom Console -----------------
$('btnRunOverpassQuery').onclick = () => {
  let rawQuery = $('overpassQueryText').value.trim();
  if (!rawQuery) return;
  const b = map.getBounds();
  const bbox = `${b.getSouth()},${b.getWest()},${b.getNorth()},${b.getEast()}`;
  const preparedQuery = rawQuery.replace(/\{\{bbox\}\}/g, bbox);
  
  $('overpassQueryStatus').textContent = 'Executing Query...';
  fetch(`https://overpass-api.de/api/interpreter?data=${encodeURIComponent(`[out:json][timeout:25];${preparedQuery}`)}`)
    .then(r => r.json())
    .then(data => {
      const els = data.elements || [];
      $('overpassQueryStatus').textContent = `Loaded ${els.length} elements`;
      els.forEach(el => {
        const lat = el.lat || (el.center && el.center.lat);
        const lon = el.lon || (el.center && el.center.lon);
        if (lat && lon) {
          addFeatureRecord('marker', { type: 'Point', coordinates: [lon, lat] }, {
            markerType: 'vector', iconKey: 'ico_vector_003366_def', color: '#003366', osmTags: el.tags
          }, null, el.tags?.name || 'OSM Node');
        }
      });
    })
    .catch(() => $('overpassQueryStatus').textContent = 'Query failed.');
};

// ----------------- Native GIS File Importers -----------------
$('btn-import-dialog').onclick = () => $('popup-import-dialog').classList.toggle('open');

$('btnProcessImport').onclick = async () => {
  const file = $('gisFileInput').files[0];
  if (!file) return;
  const ext = file.name.split('.').pop().toLowerCase();
  hint(`Parsing ${file.name}…`);

  try {
    let geojson = null;
    if (ext === 'geojson' || ext === 'json') {
      const text = await file.text();
      geojson = JSON.parse(text);
    } else if (ext === 'kml') {
      const text = await file.text();
      const dom = new DOMParser().parseFromString(text, 'text/xml');
      geojson = toGeoJSON.kml(dom);
    } else if (ext === 'kmz') {
      const zip = await JSZip.loadAsync(file);
      const kmlFile = Object.keys(zip.files).find(n => n.endsWith('.kml'));
      const text = await zip.files[kmlFile].async('text');
      const dom = new DOMParser().parseFromString(text, 'text/xml');
      geojson = toGeoJSON.kml(dom);
    } else if (ext === 'zip') {
      const buffer = await file.arrayBuffer();
      geojson = await shp(buffer);
    }

    if (geojson) {
      const rawFeats = geojson.features || (Array.isArray(geojson) ? geojson[0]?.features : []);
      if (rawFeats && rawFeats.length) {
        rawFeats.forEach(rf => {
          const kind = rf.geometry.type.includes('Polygon') ? 'polygon' : (rf.geometry.type.includes('Line') ? 'polyline' : 'marker');
          addFeatureRecord(kind, rf.geometry, {}, null, rf.properties?.name || file.name);
        });
        hint(`Imported ${rawFeats.length} features!`);
        $('popup-import-dialog').classList.remove('open');
      }
    }
  } catch(err) {
    hint('Import error: Unsupported format.');
  }
};

// ----------------- Draggable Chronological Layers Tree -----------------
let draggedTreeIdx = null;

function renderLayersTree() {
  const container = $('layers-tree-container');
  $('layer-badge-count').textContent = features.length;

  if (!features.length) {
    container.innerHTML = '<div style="font-size:11px; color:#64748b; padding:12px 0;">No layers. Draw or import spatial items.</div>';
    return;
  }

  container.innerHTML = features.slice().reverse().map((f, revIdx) => {
    const actualIdx = features.length - 1 - revIdx;
    const isSelected = selectedIdsSet.has(f.id);
    const isActive = selectedId === f.id;

    return `
      <div class="layer-card ${isActive ? 'active' : ''}" draggable="true" data-idx="${actualIdx}" data-id="${f.id}">
        <div class="layer-card-main-row">
          <div class="layer-left-info">
            <input type="checkbox" class="layer-select-box" data-id="${f.id}" ${isSelected ? 'checked' : ''} />
            <input class="layer-name-input" data-id="${f.id}" value="${f.name}" />
          </div>
          <div class="layer-actions-row">
            <button class="card-btn" data-act="eye" data-id="${f.id}" title="Toggle Visibility">
              <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
            </button>
            <button class="card-btn" data-act="zoom" data-id="${f.id}" title="Zoom To">
              <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            </button>
            <button class="card-btn" data-act="del" data-id="${f.id}" title="Delete" style="color:#ef4444;">
              <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');

  // Drag Reordering Events
  container.querySelectorAll('.layer-card').forEach(card => {
    card.ondragstart = e => {
      draggedTreeIdx = parseInt(card.dataset.idx, 10);
      card.classList.add('dragging');
    };
    card.ondragend = () => card.classList.remove('dragging');
    card.ondragover = e => { e.preventDefault(); card.classList.add('dragover'); };
    card.ondragleave = () => card.classList.remove('dragover');
    card.ondrop = e => {
      e.preventDefault();
      card.classList.remove('dragover');
      const targetIdx = parseInt(card.dataset.idx, 10);
      if (draggedTreeIdx !== null && draggedTreeIdx !== targetIdx) {
        const movedItem = features.splice(draggedTreeIdx, 1)[0];
        features.splice(targetIdx, 0, movedItem);
        syncDraw();
        renderLayersTree();
        markDirty();
      }
    };
  });

  // Action Bindings
  container.querySelectorAll('.layer-select-box').forEach(cb => {
    cb.onchange = e => {
      const id = parseInt(cb.dataset.id, 10);
      cb.checked ? selectedIdsSet.add(id) : selectedIdsSet.delete(id);
      updateMultiSelectRibbon();
    };
  });

  container.querySelectorAll('.layer-name-input').forEach(inp => {
    inp.onchange = e => {
      const id = parseInt(inp.dataset.id, 10);
      const f = features.find(x => x.id === id);
      if (f) { f.name = inp.value; syncDraw(); markDirty(); }
    };
  });

  container.querySelectorAll('.card-btn').forEach(b => {
    b.onclick = () => {
      const id = parseInt(b.dataset.id, 10);
      const act = b.dataset.act;
      const f = features.find(x => x.id === id);
      if (!f) return;

      if (act === 'eye') { f.props.visible = f.props.visible ? 0 : 1; syncDraw(); markDirty(); }
      if (act === 'del') { 
        features = features.filter(x => x.id !== id);
        selectedIdsSet.delete(id);
        syncDraw(); renderLayersTree(); markDirty(); 
      }
      if (act === 'zoom') {
        const bnd = calcBounds(f);
        if (bnd) map.fitBounds(bnd, { padding: 60, maxZoom: 17 });
      }
    };
  });
}

function updateMultiSelectRibbon() {
  const ribbon = $('multiselect-group-ribbon');
  const count = selectedIdsSet.size;
  if (count > 1) {
    ribbon.style.display = 'flex';
    $('multiselect-count-text').textContent = `${count} layers selected`;
  } else {
    ribbon.style.display = 'none';
  }
}

$('btnDeleteSelected').onclick = () => {
  features = features.filter(f => !selectedIdsSet.has(f.id));
  selectedIdsSet.clear();
  updateMultiSelectRibbon();
  syncDraw();
  renderLayersTree();
  markDirty();
};

$('btnGroupSelected').onclick = () => {
  const gName = prompt("Group Name:", `Group ${Object.keys(customGroups).length + 1}`);
  if (!gName) return;
  customGroups[gName] = { collapsed: false, ids: Array.from(selectedIdsSet) };
  selectedIdsSet.clear();
  updateMultiSelectRibbon();
  renderLayersTree();
  markDirty();
};

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

// ----------------- Workspaces Engine -----------------
function renderProjectsList() {
  const container = $('existing-projects-container');
  if (!ALL_PROJECTS || !ALL_PROJECTS.length) {
    container.innerHTML = `<div style="color:rgba(255,255,255,0.5); font-size:12px; text-align:center; padding:16px;">No saved projects.</div>`;
    return;
  }
  container.innerHTML = ALL_PROJECTS.map(p => `
    <div style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.08); border-radius:14px; padding:10px 14px; display:flex; justify-content:space-between; align-items:center;">
      <div style="display:flex; flex-direction:column; gap:2px; flex:1; cursor:pointer;" onclick="loadProjectDirectly('${p.id}')">
        <span style="font-weight:700; font-size:13px; color:#ffffff;">${p.name || 'Untitled Project'}</span>
        <span style="font-size:11px; color:rgba(255,255,255,0.5);">${p.basemap || 'Midnight Blue'} · ${p.features ? p.features.length : 0} layers</span>
      </div>
      <button class="card-btn" onclick="deleteProjectPermanently(event, '${p.id}')" title="Delete Workspace" style="color:#ef4444;">
        <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
      </button>
    </div>
  `).join('');
}

window.deleteProjectPermanently = async function(e, id) {
  e.stopPropagation();
  if (!confirm("Permanently delete this workspace?")) return;
  ALL_PROJECTS = ALL_PROJECTS.filter(p => p.id !== id);
  renderProjectsList();
  try {
    await fetch(`${SUPABASE_URL.replace('/rest/v1/','').replace(/\\/$/,'')}/rest/v1/map_projects?id=eq.${id}`, {
      method: 'DELETE',
      headers: { 'apikey': SUPABASE_KEY, 'Authorization': `Bearer ${SUPABASE_KEY}` }
    });
  } catch(err) {}
};

$('btn-home-dialog').onclick = () => $('launcher-modal-scrim').classList.add('visible');
$('seg-btn-existing').onclick = () => {
  $('seg-btn-existing').classList.add('active');
  $('seg-btn-new').classList.remove('active');
  $('seg-content-existing').style.display = 'flex';
  $('seg-content-new').style.display = 'none';
};
$('seg-btn-new').onclick = () => {
  $('seg-btn-new').classList.add('active');
  $('seg-btn-existing').classList.remove('active');
  $('seg-content-new').style.display = 'flex';
  $('seg-content-existing').style.display = 'none';
};

// ----------------- Export Pipeline -----------------
$('btn-export-dialog').onclick = () => {
  const dataUrl = map.getCanvas().toDataURL('image/png');
  $('exportPreviewImg').src = dataUrl;
  $('popup-export').classList.toggle('open');
};

$('triggerExportBtn').onclick = () => {
  const a = document.createElement('a');
  a.download = `atlas_render_${Date.now()}.png`;
  a.href = map.getCanvas().toDataURL('image/png');
  a.click();
  $('popup-export').classList.remove('open');
};

// ----------------- Startup -----------------
map.on('load', () => {
  registerIconImage('ico_vector_003366_def', 'pin', '#003366', null, 'vector');
  addDrawStack();
  renderLayersTree();
  renderProjectsList();
});

} catch (e) {
  console.error('App init failure:', e);
}
</script>
</body>
</html>"""

# ------------------------------------------------------------------------
# 5. INITIAL STATE & RENDER
# ------------------------------------------------------------------------
try:
    initial_theme = "Midnight Blue"
    initial_center = [120.9842, 14.5995]
    initial_zoom = 14
    initial_name = "Untitled Project 1"
    initial_id = "local-temp"
    initial_features = []
    initial_custom_groups = {"Trade Area Scan": {"collapsed": False, "ids": []}}

    if ALL_PROJECTS_LIST:
        latest = ALL_PROJECTS_LIST[0]
        initial_id = str(latest.get("id", "local-temp"))
        initial_name = latest.get("name", "Untitled Project 1")
        initial_theme = latest.get("basemap", "Midnight Blue")
        initial_center = latest.get("center", [120.9842, 14.5995])
        initial_zoom = latest.get("zoom", 14)
        initial_features = latest.get("features", [])
        initial_custom_groups = latest.get("custom_groups", {"Trade Area Scan": {"collapsed": False, "ids": []}})

    html = (
        HTML_TEMPLATE.replace("__ALL_STYLES__", json.dumps(ALL_STYLES))
        .replace("__POI_CONFIG__", json.dumps(POI_CONFIG))
        .replace("__SUPABASE_URL__", SUPABASE_URL)
        .replace("__SUPABASE_KEY__", SUPABASE_KEY)
        .replace("__ALL_PROJECTS_JSON__", json.dumps(ALL_PROJECTS_LIST))
        .replace("__PROJECT_ID__", initial_id)
        .replace("__PROJECT_NAME__", initial_name)
        .replace("__INITIAL_BASEMAP__", initial_theme)
        .replace("__INITIAL_FEATURES__", json.dumps(initial_features))
        .replace("__INITIAL_CUSTOM_GROUPS__", json.dumps(initial_custom_groups))
        .replace("__CENTER__", json.dumps(initial_center))
        .replace("__ZOOM__", str(initial_zoom))
        .replace("__BG__", THEMES.get(initial_theme, THEMES["Midnight Blue"])["overlay"])
    )
    components.html(html, height=1000, scrolling=False)
except Exception as e:
    st.error(f"Failed to mount Atlas application: {e}")
    

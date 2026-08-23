import json
import re
import streamlit as st
import streamlit.components.v1 as components
import requests
import logging
import time
import random

# ------------------------------------------------------------------------
# ROBUST OVERPASS API QUERY FUNCTION (PYTHON)
# ------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_pois(lat: float, lon: float, radius: int, tags: list, timeout: int = 90) -> list:
    """
    Robustly queries Overpass API with built-in retries, multiple endpoint failover,
    exponential backoff, and proper error handling. Falls back to OSMnx if all endpoints fail.
    """
    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.openstreetmap.fr/api/interpreter"
    ]
    
    statements = "\n".join([f"  nwr[{tag}](around:{radius},{lat},{lon});" for tag in tags])
    ql = f"[out:json][timeout:{timeout}];(\n{statements}\n);\nout center;"
    
    for endpoint in endpoints:
        retries = 5
        delay = 1.0
        while retries > 0:
            try:
                url = f"{endpoint}?data={requests.utils.quote(ql)}"
                res = requests.get(url, timeout=timeout)
                if res.status_code in [429, 503, 504]:
                    raise requests.exceptions.HTTPError(f"HTTP {res.status_code}")
                res.raise_for_status()
                data = res.json()
                if not data or 'elements' not in data:
                    raise ValueError("Malformed JSON response")
                
                results = []
                for el in data['elements']:
                    el_lat = el.get('lat') or (el.get('center', {}).get('lat'))
                    el_lon = el.get('lon') or (el.get('center', {}).get('lon'))
                    if el_lat is None or el_lon is None:
                        continue
                    tags_dict = el.get('tags', {})
                    name = tags_dict.get('name', 'Unknown')
                    poi_type = tags_dict.get('amenity') or tags_dict.get('shop') or tags_dict.get('building') or 'Node'
                    results.append({
                        'lat': float(el_lat),
                        'lon': float(el_lon),
                        'name': str(name),
                        'type': str(poi_type),
                        'tags': tags_dict
                    })
                logging.info(f"Successfully fetched {len(results)} POIs from {endpoint}")
                return results
            except Exception as e:
                logging.warning(f"Endpoint {endpoint} failed: {e}. Retries left: {retries-1}")
                retries -= 1
                if retries == 0:
                    break
                jitter = random.uniform(0, 0.5)
                time.sleep(delay + jitter)
                delay *= 2
                
    logging.info("All Overpass endpoints failed. Falling back to OSMnx...")
    try:
        import osmnx as ox
        import geopandas as gpd
        import pandas as pd
        tags_dict = {}
        for tag in tags:
            clean = tag.replace('"', '')
            if '=' in clean:
                k, v = clean.split('=', 1)
                if '|' in v:
                    tags_dict[k] = [x.strip() for x in v.split('|')]
                else:
                    tags_dict[k] = v
            else:
                tags_dict[clean] = True
        
        gdf = ox.geometries_from_point((lat, lon), tags_dict, dist=radius)
        results = []
        for idx, row in gdf.iterrows():
            geom = row.geometry
            if geom.geom_type == 'Point':
                lon_val, lat_val = geom.x, geom.y
            else:
                lon_val, lat_val = geom.centroid.x, geom.centroid.y
            name = row.get('name', 'Unknown')
            poi_type = row.get('amenity') or row.get('shop') or row.get('building') or 'Node'
            results.append({
                'lat': float(lat_val),
                'lon': float(lon_val),
                'name': str(name) if pd.notna(name) else 'Unknown',
                'type': str(poi_type) if pd.notna(poi_type) else 'Node',
                'tags': {k: v for k, v in row.items() if k not in ['geometry', 'name', 'amenity', 'shop', 'building']}
            })
        logging.info(f"Successfully fetched {len(results)} POIs via OSMnx fallback")
        return results
    except Exception as e:
        logging.error(f"OSMnx fallback also failed: {e}")
        return []

# ------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & ROOT OVERRIDES
# ------------------------------------------------------------------------
st.set_page_config(
    page_title="Project Atlas",
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
    background-color: #0a1628 !important;
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
    z-index: 1 !important;
}
html, body {
    overflow: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    background: #0a1628 !important;
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
        url = f"{BASE_API_URL}/map_projects?select=id,name,created_at,updated_at,basemap,zoom,center,features,custom_groups,layer_visibilities&order=updated_at.desc"
        res = requests.get(url, headers=get_headers(), timeout=6)
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
        "overlay": "#0a1628", "text": "#d9b451", "land": "#0d1830",
        "landcover": "#0f1d33", "water": "#0a1424", "waterway": "#081120",
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
    for stop in stops:
        z, val = stop
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
        "sources": {"omt": {"type": "vector", "url": "https://tiles.openfreemap.org/planet"}},
        "layers": [
            {"id": "bg", "type": "background", "paint": {"background-color": p["overlay"]}},
            {"id": "landcover", "type": "fill", "source": "omt", "source-layer": "landcover", "paint": {"fill-color": p["landcover"], "fill-opacity": 0.6}},
            {"id": "landuse", "type": "fill", "source": "omt", "source-layer": "landuse", "paint": {"fill-color": p["land"], "fill-opacity": 0.8}},
            {"id": "park", "type": "fill", "source": "omt", "source-layer": "park", "paint": {"fill-color": p["parks"]}},
            {"id": "water", "type": "fill", "source": "omt", "source-layer": "water", "paint": {"fill-color": p["water"]}},
            {"id": "waterway", "type": "line", "source": "omt", "source-layer": "waterway", "paint": {"line-color": p["waterway"], "line-width": w((9, 1), (20, 6))}},
            {"id": "aeroway", "type": "line", "source": "omt", "source-layer": "aeroway", "paint": {"line-color": p["aeroway"], "line-width": w((11, 1), (20, 12))}},
            {"id": "building-2d", "type": "fill", "source": "omt", "source-layer": "building", "minzoom": 13, "layout": {"visibility": "none"}, "paint": {"fill-color": p["buildings"], "fill-opacity": p["building_opacity"], "fill-outline-color": p["buildings"]}},
            {
                "id": "building-3d", "type": "fill-extrusion", "source": "omt", "source-layer": "building", "minzoom": 13,
                "layout": {"visibility": "visible"},
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
    "CartoDB Light": raster_style(["https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png", "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"], "#f8f9fa"),
    "CartoDB Dark": raster_style(["https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png", "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"], "#000000"),
    "OSM": raster_style(["https://tile.openstreetmap.org/{z}/{x}/{y}.png"], "#f2efe9", 19),
    "Satellite": raster_style(["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"], "#000000", 19),
}

COLOR_PALETTES = [
    {"name": "Primary", "colors": ["#1e40af", "#dc2626", "#16a34a", "#ca8a04", "#0a1628", "#ffffff"]},
    {"name": "Secondary", "colors": ["#38bdf8", "#3fb950", "#f85149", "#a371f7", "#fb923c", "#f43f5e"]},
    {"name": "Tertiary", "colors": ["#0d9488", "#e8b84a", "#8b5cf6", "#64748b", "#8e7258", "#334155"]}
]

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
<script src="https://unpkg.com/@mapbox/togeojson@0.16.0/togeojson.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
<script src="https://unpkg.com/shpjs@4.0.4/dist/shp.js"></script>
<style>
@font-face {
    font-family: 'Century Gothic Custom';
    src: local('Century Gothic'), local('CenturyGothic'), local('AppleGothic'), sans-serif;
}
* { box-sizing: border-box; user-select: none; font-family: 'Century Gothic Custom', -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif; }
html, body { margin: 0; padding: 0; width: 100vw; height: 100vh; overflow: hidden; background: #0a1628; }
#map { position: absolute; inset: 0; width: 100vw; height: 100vh; z-index: 1; }
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.15); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.3); }
select, select option { background-color: #0f172a !important; color: #f8fafc !important; }
select option:hover, select option:checked { background-color: #2563eb !important; color: #ffffff !important; }
#top-toolbar-bar {
    position: fixed; top: 16px; left: 50%; transform: translateX(-50%); z-index: 1000;
    background-color: rgba(9, 16, 24, 0.97);
    border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 36px; padding: 4px 10px;
    display: flex; align-items: center; gap: 4px; box-shadow: 0 12px 36px rgba(0, 0, 0, 0.6);
    color: #f0f6fc;
}
.tb-btn {
    width: 32px; height: 32px; display: grid; place-items: center;
    background: transparent; border: none; color: #adbac7; border-radius: 50%;
    cursor: pointer; transition: all 0.15s ease;
}
.tb-btn:hover { background: rgba(255, 255, 255, 0.1); color: #ffffff; }
.tb-btn.active { background: rgba(255, 255, 255, 0.18); color: #ffffff; }
.tb-btn.primary-active { background: #316dca; color: #ffffff; }
.tb-sep { width: 1px; height: 18px; background: rgba(255, 255, 255, 0.12); margin: 0 4px; }
#project-meta-cluster { display: flex; align-items: center; gap: 8px; padding: 0 4px; }
#project-name-display { font-weight: 700; color: #38bdf8; font-size: 12px; max-width: 140px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer; }
.save-badge { font-size: 9px; padding: 2px 7px; border-radius: 12px; font-weight: 600; background: rgba(255, 255, 255, 0.08); color: #8b949e; border: 1px solid rgba(255, 255, 255, 0.1); display: flex; align-items: center; gap: 4px; }
.save-badge.saving { color: #d9b451; border-color: rgba(217, 180, 81, 0.4); }
.save-badge.saved { color: #3fb950; border-color: rgba(63, 185, 80, 0.4); }
.save-badge.unsaved { color: #f85149; border-color: rgba(248, 81, 73, 0.4); }
.left-panel {
    position: fixed; top: 68px; left: 16px; bottom: 16px; width: 360px; z-index: 999;
    background-color: rgba(9, 16, 24, 0.97);
    border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 20px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7); display: none; flex-direction: column;
    overflow: hidden; color: #adbac7;
}
.left-panel.open { display: flex; }
.panel-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 16px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); }
.panel-title { display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 14px; color: #f0f6fc; }
.icon-action-btn { width: 28px; height: 28px; display: grid; place-items: center; border: 1px solid rgba(255, 255, 255, 0.1); background: rgba(255, 255, 255, 0.05); border-radius: 8px; cursor: pointer; color: #adbac7; transition: 0.2s; }
.icon-action-btn:hover { background: rgba(255, 255, 255, 0.15); color: #f0f6fc; }
.panel-content { flex: 1; overflow-y: auto; padding: 14px 16px; display: flex; flex-direction: column; gap: 12px; font-size: 12px; }
.acc-item { border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 8px; transition: 0.2s; }
.acc-item:hover { background: rgba(255,255,255,0.02); }
.acc-header { display: flex; align-items: center; justify-content: space-between; font-size: 13px; font-weight: 600; color: #f0f6fc; cursor: pointer; padding: 6px 4px; border-radius: 4px;}
.acc-body { padding: 6px 4px 2px 4px; display: flex; flex-direction: column; gap: 8px; }
.acc-body.hidden { display: none !important; }
.layer-row { display: flex; align-items: center; justify-content: space-between; font-size: 12px; color: #adbac7; }
.layer-row input[type=checkbox] { accent-color: #316dca; cursor: pointer; }
.dimension-mode-bar { display: flex; gap: 4px; background: rgba(0, 0, 0, 0.35); padding: 3px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.08); margin-bottom: 4px; }
.dimension-mode-btn { flex: 1; border: none; background: transparent; color: #adbac7; font-size: 11px; font-weight: 700; padding: 5px 0; border-radius: 6px; cursor: pointer; }
.dimension-mode-btn.active { background: #316dca; color: #ffffff; }
.bound-select-row { display: flex; gap: 6px; margin-top: 4px; position: relative; }
.bound-select-row input[type=text] { flex: 1; background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(255, 255, 255, 0.12); color: #f0f6fc; padding: 6px 8px; border-radius: 8px; font-size: 11px; }
.autocomplete-list {
    position: absolute; top: 100%; left: 0; right: 0; z-index: 1001;
    background: #0f172a; border: 1px solid rgba(255,255,255,0.12); border-radius: 8px;
    max-height: 200px; overflow-y: auto; display: none; margin-top: 4px; box-shadow: 0 8px 16px rgba(0,0,0,0.5);
}
.autocomplete-item { padding: 8px 10px; cursor: pointer; font-size: 11px; color: #adbac7; border-bottom: 1px solid rgba(255,255,255,0.05); }
.autocomplete-item:hover { background: rgba(255,255,255,0.1); color: #fff; }
.layers-heading { display: flex; align-items: center; justify-content: space-between; font-weight: 700; font-size: 13px; color: #f0f6fc; margin-top: 6px; }
.badge-count { background: #316dca; color: #ffffff; border-radius: 12px; font-size: 11px; padding: 1px 8px; font-weight: 600; }
.group-container { background: rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; margin-top: 6px; overflow: hidden; transition: 0.15s; }
.group-container.drop-hover { border-color: #38bdf8; background: rgba(56, 189, 248, 0.12); }
.group-header { background: rgba(255, 255, 255, 0.05); padding: 8px 10px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; }
.group-title-input { background: transparent; border: none; font-weight: 700; color: #f0f6fc; font-size: 12px; width: 120px; }
.group-title-input:focus { background: rgba(0, 0, 0, 0.5); outline: none; border-radius: 4px; padding: 2px 4px; }
.group-items { padding: 4px 6px; display: flex; flex-direction: column; gap: 4px; }
.group-items.hidden { display: none !important; }
.group-styling-panel {
    padding: 10px; background: rgba(0,0,0,0.4); border-top: 1px solid rgba(255,255,255,0.08);
    display: none; flex-direction: column; gap: 6px;
}
.group-styling-panel.open { display: flex; }
.group-styling-panel .f-row { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.layer-card { background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 8px; padding: 6px 8px; display: flex; flex-direction: column; gap: 4px; margin-top: 4px; cursor: grab; }
.layer-card:active { cursor: grabbing; }
.layer-card-top { display: flex; align-items: center; gap: 4px; overflow: hidden; }
.layer-name-input { flex: 1; min-width: 50px; border: 1px solid transparent; background: transparent; font-weight: 600; font-size: 12px; color: #f0f6fc; padding: 2px 4px; border-radius: 4px; text-overflow: ellipsis; white-space: nowrap; overflow: hidden; }
.layer-name-input:focus { border-color: #316dca; background: rgba(0,0,0,0.4); outline: none; }
.card-btn { background: transparent; border: none; color: #768390; cursor: pointer; padding: 2px 4px; border-radius: 4px; transition: 0.15s; flex-shrink: 0; }
.card-btn:hover { color: #f0f6fc; background: rgba(255,255,255,0.1); }
.card-btn svg { width: 14px; height: 14px; }
#ungrouped-zone { border: 1px dashed transparent; border-radius: 8px; padding: 2px; transition: 0.15s; }
#ungrouped-zone.drop-hover { border-color: #38bdf8; background: rgba(56, 189, 248, 0.08); }
.trade-controls { display: flex; flex-direction: column; gap: 6px; background: rgba(0,0,0,0.35); padding: 8px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.08); }
.trade-controls select { background: #0f172a; color: #f0f6fc; border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 8px; padding: 6px; font-size: 11px; }
.trade-btn { background: #316dca; color: #ffffff; border: none; border-radius: 8px; padding: 7px; font-weight: 600; cursor: pointer; font-size: 11px; transition:0.2s;}
.trade-btn:hover { background: #2563eb; }
.poi-summary { font-size: 11px; color: #adbac7; max-height: 180px; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; margin-top: 4px; }
.poi-badge { display: flex; justify-content: space-between; background: rgba(255,255,255,0.05); padding: 5px 8px; border-radius: 6px; }
.float-card {
    position: fixed; top: 68px; z-index: 998;
    background-color: rgba(9, 16, 24, 0.97);
    border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 18px; padding: 14px;
    box-shadow: 0 20px 48px rgba(0, 0, 0, 0.75); display: none; flex-direction: column;
    gap: 10px; font-size: 12px; color: #adbac7;
    max-height: 80vh; overflow-y: auto;
}
.float-card.open { display: flex; }
.right-card { right: 16px; left: auto; transform: none; width: 320px; }
.float-card .f-row { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.float-card input[type=range] { accent-color: #316dca; width: 110px; cursor: pointer; }
.float-card input[type=text], .float-card select { background: rgba(0,0,0,0.4); color: #f0f6fc; border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 8px; padding: 6px 8px; font-size: 12px; transition:0.2s; outline:none; }
.float-card input[type=text]:focus { border-color: #38bdf8; }
#popup-search { width: 340px; left: 50%; transform: translateX(-50%); top:68px; right:auto; }
#popup-marker-settings { width: 250px; }
#popup-text-settings { width: 260px; }
#popup-shape-editor { width: 330px; }
#popup-custom-map { width: 310px; }
#popup-trade-area { width: 400px; left: 50%; transform: translateX(-50%); top: 68px; right: auto; }
#popup-route-settings { width: 300px; }
#popup-attribute-table { width: 600px; left: 50%; transform: translateX(-50%); top: 68px; right: auto; max-height: 70vh; }
.icon-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
.icon-grid button { width: 36px; height: 36px; display: grid; place-items: center; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; background: rgba(255,255,255,0.05); color: #adbac7; cursor: pointer; transition:0.2s;}
.icon-grid button.active { border-color: #316dca; background: #316dca; color: #ffffff; }
.maplibregl-popup-content {
    background: rgba(9, 16, 24, 0.97) !important; color: #f0f6fc !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important; border-radius: 14px !important;
    padding: 12px !important; box-shadow: 0 12px 32px rgba(0,0,0,0.7) !important;
    font-size: 11px !important; max-width: 320px !important;
}
.maplibregl-popup-tip { border-top-color: rgba(9, 16, 24, 0.97) !important; }
.tag-table { width: 100%; border-collapse: collapse; margin-top: 6px; }
.tag-table th, .tag-table td { text-align: left; padding: 4px 6px; border: 1px solid rgba(255,255,255,0.08); font-size: 10px; }
.tag-table th { background: rgba(255,255,255,0.06); color: #38bdf8; }
.tag-table td { word-break: break-all; }
#hint-toast {
    position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); z-index: 1001;
    background-color: rgba(9, 16, 24, 0.97); color: #f0f6fc;
    border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 20px; padding: 7px 18px;
    font-size: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); display: none; font-weight:600;
}
#map-context-menu {
    position: absolute; z-index: 3000; display: none; min-width: 200px;
    background: rgba(9, 16, 24, 0.98); border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 10px; padding: 4px; box-shadow: 0 12px 32px rgba(0,0,0,0.7);
}
.ctx-item {
    display: flex; align-items: center; gap: 8px; padding: 8px 10px;
    font-size: 12px; color: #f0f6fc; cursor: pointer; border-radius: 6px;
}
.ctx-item:hover { background: rgba(255, 255, 255, 0.1); }
.ctx-item svg { width: 14px; height: 14px; color: #adbac7; flex-shrink: 0; }
.ctx-coords { padding: 6px 10px 8px 10px; font-size: 10px; color: #768390; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 4px; }
.ctx-divider { height: 1px; background: rgba(255, 255, 255, 0.1); margin: 3px 0; }
#launcher-modal-scrim {
    position: fixed; inset: 0; z-index: 9999;
    display: flex; align-items: center; justify-content: center;
    background-color: rgba(9, 16, 24, 0.97);
    opacity: 0; pointer-events: none; transition: opacity 0.2s ease;
}
#launcher-modal-scrim.visible { opacity: 1; pointer-events: auto; }
.ios26-card {
    width: 90%; max-width: 440px; max-height: 82vh;
    background-color: rgba(9, 16, 24, 0.97);
    border: 1px solid rgba(255, 255, 255, 0.16); border-radius: 24px;
    box-shadow: 0 32px 80px -12px rgba(0, 0, 0, 0.85);
    display: flex; flex-direction: column; overflow: hidden; color: #ffffff;
}
.ios26-header { padding: 22px 24px 14px 24px; display: flex; flex-direction: column; gap: 4px; }
.ios26-title { font-size: 20px; font-weight: 800; letter-spacing: -0.4px; color: #ffffff; }
.ios26-subtitle { font-size: 13px; color: rgba(255, 255, 255, 0.6); }
.ios26-seg {
    margin: 0 24px 14px 24px; display: flex; background: rgba(0, 0, 0, 0.4);
    padding: 3px; border-radius: 14px; border: 1px solid rgba(255, 255, 255, 0.08);
}
.ios26-seg-btn {
    flex: 1; border: none; background: transparent; color: rgba(255, 255, 255, 0.65);
    font-size: 12px; font-weight: 600; padding: 7px 0; border-radius: 11px; cursor: pointer;
    transition: all 0.15s ease;
}
.ios26-seg-btn.active { background: rgba(255, 255, 255, 0.18); color: #ffffff; }
.ios26-body { padding: 0 24px 22px 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.ios26-input-group { display: flex; flex-direction: column; gap: 6px; }
.ios26-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.6px; color: rgba(255, 255, 255, 0.5); }
.ios26-input {
    background: rgba(0, 0, 0, 0.35); border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 14px; padding: 10px 14px; color: #ffffff; font-size: 13px; outline: none;
}
.ios26-input:focus { border-color: #38bdf8; }
.ios26-proj-item {
    background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px; padding: 10px 14px; display: flex; justify-content: space-between;
    align-items: center; transition: all 0.15s ease;
}
.ios26-proj-item:hover { background: rgba(255, 255, 255, 0.1); border-color: rgba(56, 189, 248, 0.3); }
.ios26-action-btn {
    background: #316dca; color: #ffffff; border: none; border-radius: 14px;
    padding: 11px; font-weight: 700; font-size: 13px; cursor: pointer;
    box-shadow: 0 8px 24px rgba(49, 109, 202, 0.4);
}
.ios26-action-btn:hover { background: #255bb0; }
.file-input-label {
    display: inline-block; background: #316dca; color: #fff; padding: 6px 12px;
    border-radius: 6px; cursor: pointer; font-size: 11px; font-weight: 600; transition:0.2s;
}
.file-input-label:hover { background: #255bb0; }
.search-wrapper {
    display: flex; align-items: center; gap: 6px;
    background: #fff; border-radius: 24px; padding: 4px 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.4);
}
.search-wrapper input {
    flex: 1; border: none; outline: none; font-size: 14px; color: #202124;
    background: transparent; padding: 6px 0;
}
.search-wrapper svg { stroke: #5f6368; width: 20px; height: 20px; }
.search-results {
    background: #fff; border-radius: 8px; margin-top: 4px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3); overflow: hidden;
}
.search-result-item {
    padding: 10px 14px; cursor: pointer; font-size: 13px; color: #202124;
    display: flex; align-items: center; gap: 10px;
}
.search-result-item:hover { background: #f1f3f4; }
.search-result-icon { width: 20px; height: 20px; flex-shrink: 0; color: #5f6368; }
.trade-area-poi-row { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 8px; }
.trade-area-poi-row label { display: inline-flex; align-items: center; gap: 3px; font-size: 11px; white-space: nowrap; }
.custom-query-collapse-header { display: flex; align-items: center; justify-content: space-between; cursor: pointer; font-weight: 600; color: #f0f6fc; font-size: 12px; margin-top: 8px;}

/* Route Multi-stop Address Engine UI */
.route-stops-container { display: flex; flex-direction: column; gap: 6px; margin: 8px 0; }
.route-stop-row { display: flex; align-items: center; gap: 6px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 4px 8px; cursor: grab; }
.route-stop-row:active { cursor: grabbing; }
.route-stop-handle { color: #768390; cursor: grab; display: grid; place-items: center; }
.route-stop-input { flex: 1; background: transparent; border: none; color: #f0f6fc; font-size: 11px; outline: none; }
.route-stop-input:focus { border-bottom: 1px solid #38bdf8; }

/* Modal Scrims */
.modal-scrim {
    position: fixed; inset: 0; z-index: 10000;
    display: flex; align-items: center; justify-content: center;
    background: rgba(0, 0, 0, 0.7); backdrop-filter: blur(4px);
}

/* Attribute Table Styles */
.attr-table-container { width: 100%; overflow-x: auto; overflow-y: auto; max-height: 50vh; }
.attr-table { width: 100%; border-collapse: collapse; font-size: 12px; min-width: 500px; }
.attr-table th { position: sticky; top: 0; background: #0f172a; color: #f0f6fc; padding: 8px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); z-index: 10; font-size: 11px; }
.attr-table td { padding: 6px 8px; border-bottom: 1px solid rgba(255,255,255,0.05); vertical-align: middle; }
.attr-table input[type="text"] { width: 100%; background: transparent; border: 1px solid rgba(255,255,255,0.1); color: #f0f6fc; padding: 4px 6px; border-radius: 4px; }
.attr-table input[type="text"]:focus { border-color: #38bdf8; outline: none; }
.attr-img-preview { width: 80px; height: 80px; object-fit: cover; border-radius: 6px; border: 1px solid rgba(255,255,255,0.2); cursor: pointer; display: block; }
.attr-img-placeholder { width: 80px; height: 80px; border-radius: 6px; border: 1px dashed rgba(255,255,255,0.3); display: flex; align-items: center; justify-content: center; font-size: 10px; color: #adbac7; cursor: pointer; text-align: center; }

/* Color picker full control styles */
.color-ctrl-cluster { display: flex; flex-direction: column; gap: 6px; width: 100%; }
.palette-group { display: flex; flex-direction: column; gap: 2px; }
.palette-label { font-size: 9px; font-weight: 700; color: #768390; text-transform: uppercase; letter-spacing: 0.5px; }
.swatch-row { display: flex; gap: 4px; flex-wrap: wrap; align-items: center; }
.swatch { width: 16px; height: 16px; border-radius: 3px; cursor: pointer; border: 1px solid rgba(255,255,255,0.2); transition: transform 0.1s; }
.swatch:hover { transform: scale(1.15); }
.color-input-combo { display: flex; align-items: center; gap: 4px; margin-top: 2px; }
.color-input-combo input[type=color] {
    -webkit-appearance: none; border: 1px solid rgba(255, 255, 255, 0.15);
    width: 24px; height: 24px; border-radius: 4px; cursor: pointer; background: transparent; padding: 0;
}
.color-input-combo input[type=color]::-webkit-color-swatch-wrapper { padding: 1px; }
.color-input-combo input[type=color]::-webkit-color-swatch { border: none; border-radius: 2px; }
.color-input-combo input[type=text] { width: 75px; font-family: monospace; font-size: 11px; padding: 3px 5px; }
.btn-eyedropper { width: 24px; height: 24px; display: grid; place-items: center; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); border-radius: 4px; color: #adbac7; cursor: pointer; padding: 0; }
.btn-eyedropper:hover { color: #fff; background: rgba(255,255,255,0.2); }
</style>
</head>
<body>
<div id="map"></div>

<div id="top-toolbar-bar">
    <button class="tb-btn" id="btn-home-dialog" title="Select Workspace">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
    </button>
    <div id="project-meta-cluster">
        <span id="project-name-display" title="Click to rename workspace">Untitled Project 1</span>
        <div class="save-badge" id="save-status-badge">
            <span id="save-dot">●</span>
            <span id="save-text">Saved</span>
        </div>
    </div>
    <button class="tb-btn" id="btn-undo" title="Undo (Ctrl+Z)" style="color:#adbac7;">
        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7v6h6"></path><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"></path></svg>
    </button>
    <button class="tb-btn" id="btn-redo" title="Redo (Ctrl+Y)" style="color:#adbac7;">
        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 7v6h-6"></path><path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3L21 13"></path></svg>
    </button>
    <button class="tb-btn" id="btn-save-project" title="Save Workspace (Ctrl+S)" style="color:#3fb950;">
        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>
    </button>
    <div class="tb-sep"></div>
    <button class="tb-btn" id="btn-browser-toggle" title="Data Browser">
        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"></path><path d="M2 12l10 6 10-6"></path><path d="M2 16l10 6 10-6"></path></svg>
    </button>
    <button class="tb-btn" id="btn-mylayers-toggle" title="My Layers">
        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path><line x1="12" y1="11" x2="12" y2="17"></line><line x1="9" y1="14" x2="15" y2="14"></line></svg>
    </button>
    <button class="tb-btn" id="btn-search" title="Search Place">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"></circle><line x1="21" y1="21" x2="16.5" y2="16.5"></line></svg>
    </button>
    <button class="tb-btn" id="btn-import-toolbar" title="Import Spatial Data (KML, KMZ, GeoJSON, SHP)">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
    </button>
    <div class="tb-sep"></div>
    <button class="tb-btn tool" data-tool="polygon" title="Draw 2D Polygon">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l8 6-3 10H7L4 9z"></path></svg>
    </button>
    <button class="tb-btn tool" data-tool="polygon3d" title="Draw 3D Polygon (Extruded)">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path></svg>
    </button>
    <button class="tb-btn tool" data-tool="rectangle" title="Draw Rectangle">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16"></rect></svg>
    </button>
    <button class="tb-btn tool" data-tool="circle" title="Draw Circle (with Radius)">
        <svg viewBox="0 0 24 24" width="14" height="14"><circle cx="12" cy="12" r="8" fill="currentColor"></circle></svg>
    </button>
    <button class="tb-btn tool" data-tool="polyline" title="Draw Polyline">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"></path></svg>
    </button>
    <button class="tb-btn tool" data-tool="route" title="Route Engine (Click or Addresses)">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="5" cy="19" r="2.5"></circle><circle cx="19" cy="5" r="2.5"></circle><path d="M7 17c4-1 3-8 8-9"></path></svg>
    </button>
    <button class="tb-btn tool" data-tool="marker" title="Place Marker Pin">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"></path><circle cx="12" cy="10" r="2.5"></circle></svg>
    </button>
    <button class="tb-btn tool" data-tool="textbox" title="Add Text Label">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 7 4 4 20 4 20 7"></polyline><line x1="9" y1="20" x2="15" y2="20"></line><line x1="12" y1="4" x2="12" y2="20"></line></svg>
    </button>
    <div class="tb-sep"></div>
    <button class="tb-btn" id="btn-custom-map" title="Basemap Styling">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon><line x1="8" y1="2" x2="8" y2="18"></line><line x1="16" y1="6" x2="16" y2="22"></line></svg>
    </button>
    <button class="tb-btn" id="btn-export-direct" title="Export Map to PNG">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
    </button>
</div>

<!-- Left floating panels -->
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
        <div style="margin-bottom: 8px; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.08);">
            <button id="btn-import" class="trade-btn" style="width:100%; display:flex; justify-content:center; align-items:center; gap:6px;">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                Import Spatial Data (KML, GeoJSON, SHP)
            </button>
            <input type="file" id="importFileInput" accept=".kml,.kmz,.geojson,.json,.zip" style="display:none;"/>
        </div>
        <div class="dimension-mode-bar">
            <button class="dimension-mode-btn" id="btn2DMode">2D MAP</button>
            <button class="dimension-mode-btn active" id="btn3DMode">3D BUILDINGS</button>
        </div>
        <div class="acc-item" id="btnOpenTradeAreaPopup" style="cursor:pointer;">
            <div class="acc-header" style="justify-content:flex-start; gap:8px; color:#38bdf8;">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
                <span>Trade Area Analysis</span>
                <span style="margin-left:auto;">▸</span>
            </div>
        </div>
        <div class="acc-item">
            <div class="acc-header" data-target="body-labels">
                <span>Labels</span> <span>▸</span>
            </div>
            <div class="acc-body hidden" id="body-labels">
                <label class="layer-row"> <span>City</span> <input type="checkbox" data-g="label_city" checked></label>
                <label class="layer-row"> <span>Barangay</span> <input type="checkbox" data-g="label_brgy" checked></label>
                <label class="layer-row"> <span>Street</span> <input type="checkbox" data-g="label_street" checked></label>
                <label class="layer-row"> <span>POI Icons</span> <input type="checkbox" data-g="poi_icons" checked></label>
                <label class="layer-row"> <span>POI Labels</span> <input type="checkbox" data-g="poi_labels" checked></label>
            </div>
        </div>
        <div class="acc-item">
            <div class="acc-header" data-target="body-roads">
                <span>Roads & Transit</span> <span>▸</span>
            </div>
            <div class="acc-body hidden" id="body-roads">
                <label class="layer-row"> <span>Express Way</span> <input type="checkbox" data-g="road_exp" checked></label>
                <label class="layer-row"> <span>Main Road</span> <input type="checkbox" data-g="road_main" checked></label>
                <label class="layer-row"> <span>Secondary Road</span> <input type="checkbox" data-g="road_sec" checked></label>
                <label class="layer-row"> <span>Tertiary Road</span> <input type="checkbox" data-g="road_ter" checked></label>
                <label class="layer-row"> <span>Railways</span> <input type="checkbox" data-g="rd_rail" checked></label>
            </div>
        </div>
        <div class="acc-item">
            <div class="acc-header" data-target="body-buildings">
                <span>Buildings</span> <span>▸</span>
            </div>
            <div class="acc-body hidden" id="body-buildings">
                <label class="layer-row"> <span>2D Buildings</span> <input type="checkbox" data-g="building2d"></label>
                <label class="layer-row"> <span>3D Buildings</span> <input type="checkbox" data-g="building3d" checked></label>
            </div>
        </div>
        <div class="acc-item">
            <div class="acc-header" data-target="body-water">
                <span>Water</span> <span>▸</span>
            </div>
            <div class="acc-body hidden" id="body-water">
                <label class="layer-row"> <span>Water Bodies</span> <input type="checkbox" data-g="water" checked></label>
                <label class="layer-row"> <span>Waterways</span> <input type="checkbox" data-g="waterway" checked></label>
            </div>
        </div>
        <div class="acc-item">
            <div class="acc-header" data-target="body-boundaries">
                <span>Boundaries (Red Dashed)</span> <span>▸</span>
            </div>
            <div class="acc-body hidden" id="body-boundaries">
                <label class="layer-row"> <span>All Provinces</span> <input type="checkbox" data-g="bound_prov"></label>
                <label class="layer-row"> <span>All Cities</span> <input type="checkbox" data-g="bound_city"></label>
                <label class="layer-row"> <span>All Barangays</span> <input type="checkbox" data-g="bound_brgy"></label>
                <div style="font-weight:600; font-size:11px; color:#f0f6fc; margin-top:4px;">Highlight Administrative Boundary</div>
                <div class="bound-select-row">
                    <input type="text" id="boundarySearchInput" placeholder="Search province, city, barangay..." autocomplete="off"/>
                    <div class="autocomplete-list" id="boundaryAutocompleteList"></div>
                </div>
            </div>
        </div>
    </div>
</div>

<div id="mylayers-panel" class="left-panel">
    <div class="panel-header">
        <div class="panel-title">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
            <span>My Layers</span>
        </div>
        <div class="panel-actions">
            <button class="icon-action-btn" id="btn-close-mylayers" title="Close">✕</button>
        </div>
    </div>
    <div class="panel-content">
        <div class="layers-heading">
            <span>Layer Groups</span>
            <div style="display:flex; align-items:center; gap:4px;">
                <button class="icon-action-btn" id="btnSelectAllGlobal" title="Select / Deselect All Layers">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"></path><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>
                </button>
                <button id="btnAddCustomGroup" class="trade-btn" style="padding:2px 6px; font-size:10px;">+ GROUP</button>
                <button id="btnHideSelected" class="trade-btn" style="padding:2px 6px; font-size:10px; background:#22272e; border:1px solid #2d333b; color:#adbac7;">Hide/Unhide</button>
                <span class="badge-count" id="layer-badge-count">0</span>
            </div>
        </div>
        <div style="font-size:10px; color:#768390;">Drag cards to reorder or drop onto group headers.</div>
        <div id="my-layers-list"></div>
    </div>
</div>

<!-- Floating popups & modals -->
<div id="popup-search" class="float-card">
    <div class="search-wrapper">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"></circle><line x1="21" y1="21" x2="16.5" y2="16.5"></line></svg>
        <input type="text" id="searchInput" placeholder="Search location (Press Enter)..." autocomplete="off"/>
    </div>
    <div class="search-results" id="searchResultsList"></div>
</div>

<div id="popup-marker-settings" class="float-card right-card">
    <div style="font-weight:600; font-size:11px; color:#768390;">CHOOSE MARKER ICON</div>
    <div class="icon-grid" id="markerIconGrid"></div>
    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px;">
        <span style="font-size:11px;">Custom Image Pin:</span>
        <label class="file-input-label" for="customMarkerFileInput">Upload (max 5MB)</label>
        <input type="file" id="customMarkerFileInput" accept="image/*" style="display:none;"/>
    </div>
    <div class="f-row" style="flex-direction:column; align-items:stretch;">
        <span style="font-size:11px; margin-bottom:2px;">Icon Color</span>
        <div id="mColorCtrl" class="color-ctrl-cluster"></div>
    </div>
    <div class="f-row"> <span>Icon Size</span> <input type="range" id="mSize" min="0.4" max="2.0" step="0.1" value="0.9"></div>
    <div class="f-row"> <span>Sizing Mode</span>
        <select id="mSizeMode" style="width:130px;">
            <option value="dynamic" selected>Dynamic (Zoom-scaled)</option>
            <option value="static">Static (Fixed pixels)</option>
        </select>
    </div>
</div>

<div id="popup-text-settings" class="float-card right-card">
    <div style="font-weight:600; font-size:11px; color:#768390;">TEXT CONFIGURATION</div>
    <input type="text" id="tContent" value="Custom Label" placeholder="Text content…"/>
    <div class="f-row"> <span>Font</span>
        <select id="tFont" style="width:130px;">
            <option value="Century Gothic Custom" selected>Century Gothic</option>
            <option value="sans-serif">System Sans</option>
            <option value="serif">Serif</option>
            <option value="monospace">Monospace</option>
        </select>
    </div>
    <div class="f-row"> <span>Font Size</span> <input type="range" id="tSize" min="10" max="42" step="1" value="16"></div>
    <div class="f-row" style="flex-direction:column; align-items:stretch;">
        <span style="font-size:11px; margin-bottom:2px;">Color</span>
        <div id="tColorCtrl" class="color-ctrl-cluster"></div>
    </div>
    <div class="f-row"> <span>Opacity</span> <input type="range" id="tOp" min="0.1" max="1" step="0.05" value="1"></div>
</div>

<div id="popup-route-settings" class="float-card right-card">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-weight:700; color:#f0f6fc;">Routing Engine (OSRM)</span>
        <button class="card-btn" id="closeRouteSettingsBtn">✕</button>
    </div>
    
    <!-- Engine Mode Segments -->
    <div class="dimension-mode-bar" style="margin-top:4px;">
        <button class="dimension-mode-btn active" id="btnRouteModeClick">Point & Click</button>
        <button class="dimension-mode-btn" id="btnRouteModeAddress">Address-Based</button>
    </div>

    <!-- Mode 1: Manual Click UI -->
    <div id="route-panel-click-mode" style="display:flex; flex-direction:column; gap:8px;">
        <div class="f-row"><span>Travel Mode</span>
            <select id="rProfile" style="width:130px;">
                <option value="driving" selected>Driving</option>
                <option value="walking">Walking</option>
                <option value="cycling">Cycling</option>
            </select>
        </div>
        <div class="f-row"><span>Auto-Finish Toggle</span>
            <label style="display:flex; align-items:center; gap:4px; font-size:11px; cursor:pointer;">
                <input type="checkbox" id="rAutoFinish" checked style="accent-color:#316dca;"/> On double-click
            </label>
        </div>
        <button id="btnStartRouteDraw" class="trade-btn" style="font-size:11px;">Start Drawing Route</button>
    </div>

    <!-- Mode 2: Address Multi-Stop UI -->
    <div id="route-panel-address-mode" style="display:none; flex-direction:column; gap:6px;">
        <div class="f-row"><span>Travel Mode</span>
            <select id="rProfileAddr" style="width:130px;">
                <option value="driving" selected>Driving</option>
                <option value="walking">Walking</option>
                <option value="cycling">Cycling</option>
            </select>
        </div>
        <div style="font-size:10px; color:#768390;">Drag stops to reorder itinerary sequence:</div>
        <div class="route-stops-container" id="routeStopsList">
            <!-- Dynamic stop inputs generated by JS -->
        </div>
        <button id="btnAddRouteStop" class="trade-btn" style="background:#22272e; border:1px solid #2d333b; color:#adbac7; font-size:10px;">+ Add Stop</button>
        <button id="btnCalculateAddressRoute" class="trade-btn" style="font-size:11px; margin-top:2px;">Compute Route</button>
    </div>

    <div style="font-weight:600; font-size:11px; color:#768390; margin-top:4px;">STYLE PRESETS</div>
    <div style="display:flex; gap:6px; margin-top:2px;">
        <button class="swatch" data-rcol="#38bdf8" style="background:#38bdf8; width:28px; height:24px; border-radius:4px;"></button>
        <button class="swatch" data-rcol="#3fb950" style="background:#3fb950; width:28px; height:24px; border-radius:4px;"></button>
        <button class="swatch" data-rcol="#f85149" style="background:#f85149; width:28px; height:24px; border-radius:4px;"></button>
        <button class="swatch" data-rcol="#a371f7" style="background:#a371f7; width:28px; height:24px; border-radius:4px;"></button>
    </div>
</div>

<div id="popup-shape-editor" class="float-card right-card">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-weight:700; color:#f0f6fc;" id="editShapeTitle">Edit Feature</span>
        <button class="card-btn" id="closeEditorBtn">✕</button>
    </div>
    <div class="f-row"> <span>Name</span> <input type="text" id="eName" style="width:140px;"></div>
    <div id="eBorderColorRowContainer" class="f-row" style="flex-direction:column; align-items:stretch;">
        <span style="font-size:11px; margin-bottom:2px;">Border / Stroke Color</span>
        <div id="eBorderColorCtrl" class="color-ctrl-cluster"></div>
    </div>
    <div class="f-row" id="eBorderOpRow"> <span>Border Opacity</span> <input type="range" id="eBorderOp" min="0" max="1" step="0.05"></div>
    <div class="f-row" id="eWidthRow"> <span>Border Width</span> <input type="range" id="eWidth" min="1" max="16" step="1"></div>
    <div id="eFillColorRowContainer" class="f-row" style="flex-direction:column; align-items:stretch;">
        <span style="font-size:11px; margin-bottom:2px;">Fill / Extrusion Color</span>
        <div id="eFillColorCtrl" class="color-ctrl-cluster"></div>
    </div>
    <div class="f-row" id="eFillOpRow"> <span>Fill Opacity</span> <input type="range" id="eFillOp" min="0" max="1" step="0.05"></div>
    
    <!-- 3D Extrusion Specific Controls -->
    <div id="e3dExtrusionControls" style="display:none; border-top:1px solid rgba(255,255,255,0.1); margin-top:6px; padding-top:6px;">
        <div class="f-row"> <span>Height (m)</span> <input type="range" id="eExtrusionHeight" min="2" max="500" step="2" value="35" style="flex:1;"> <span id="eExtrusionHeightVal" style="font-size:10px; width:36px; text-align:right;">35m</span></div>
        <div class="f-row" style="margin-top:4px;"> <span>Base Alt (m)</span> <input type="range" id="eExtrusionBase" min="0" max="200" step="1" value="0" style="flex:1;"> <span id="eExtrusionBaseVal" style="font-size:10px; width:36px; text-align:right;">0m</span></div>
    </div>

    <div class="f-row" id="eLabelToggleRow" style="display:none;"> <span>Show Label</span> <input type="checkbox" id="eShowLabel"></div>
    <div class="f-row" id="eLabelPosRow" style="display:none;"> <span>Label Position</span>
        <select id="eLabelPos" style="width:110px;">
            <option value="center">Center</option>
            <option value="top">Above</option>
            <option value="bottom">Below</option>
            <option value="left">Left</option>
            <option value="right">Right</option>
        </select>
    </div>
    <div class="f-row" id="eMarkerSizeRow" style="display:none;"> <span>Icon Size</span> <input type="range" id="eMarkerSize" min="0.4" max="2.0" step="0.1"></div>
    <div class="f-row" id="eMarkerSizeModeRow" style="display:none;"> <span>Sizing Mode</span>
        <select id="eMarkerSizeMode" style="width:120px;">
            <option value="dynamic">Dynamic</option>
            <option value="static">Static</option>
        </select>
    </div>
    <div class="f-row" id="eTextRow" style="display:none;"> <span>Text</span> <input type="text" id="eTextVal" style="width:140px;"></div>
    <div class="f-row" id="eFontSizeRow" style="display:none;"> <span>Font Size</span> <input type="range" id="eFontSize" min="10" max="42" step="1"></div>
    
    <!-- Route Specific Controls -->
    <div id="routeEditorControls" style="display:none; border-top:1px solid rgba(255,255,255,0.1); margin-top:8px; padding-top:8px;">
        <div class="f-row"> <span>Route Mode</span>
            <select id="eRouteMode" style="width:110px;">
                <option value="driving">Driving</option>
                <option value="walking">Walking</option>
                <option value="cycling">Cycling</option>
            </select>
        </div>
        <div class="f-row" style="margin-top:4px;"> <span>Stats</span> <span id="eRouteStats" style="font-size:11px; font-weight:700; color:#38bdf8;">-</span></div>
        <div style="font-weight:600; font-size:10px; color:#768390; margin-top:6px;">WAYPOINTS</div>
        <div id="eWaypointList" style="max-height:90px; overflow-y:auto; display:flex; flex-direction:column; gap:3px; margin-top:2px;"></div>
        <button id="eRecalcRoute" class="trade-btn" style="width:100%; margin-top:6px; font-size:10px;">Recalculate Route</button>
    </div>

    <div style="display:flex; justify-content:space-between; margin-top:8px;">
        <button id="eDeleteBtn" style="color:#f85149; border:1px solid #da36334d; background:#da36331a; padding:6px 12px; border-radius:6px; cursor:pointer;">Delete</button>
        <button id="eDoneBtn" style="background:#316dca; color:#fff; border:none; padding:6px 16px; border-radius:6px; cursor:pointer;">Done</button>
    </div>
</div>

<div id="popup-custom-map" class="float-card right-card">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-weight:700; color:#f0f6fc;">Vector & Basemap Style</span>
        <button class="card-btn" id="closeCustomMapBtn">✕</button>
    </div>
    <div style="font-weight:600; font-size:11px; color:#768390; margin-top:4px;">BASEMAP PRESETS</div>
    <div style="display:flex; flex-wrap:wrap; gap:4px;" id="presetBtnList"></div>
    <div style="font-weight:600; font-size:11px; color:#768390; margin-top:6px;">BACKGROUND</div>
    <div id="cBgColorCtrl" class="color-ctrl-cluster"></div>
    <div style="font-weight:600; font-size:11px; color:#768390; margin-top:6px;">EXPRESS WAYS</div>
    <div id="cExpColorCtrl" class="color-ctrl-cluster"></div>
    <div style="font-weight:600; font-size:11px; color:#768390; margin-top:6px;">MAIN ROADS</div>
    <div id="cMainColorCtrl" class="color-ctrl-cluster"></div>
    <div class="f-row"> <span>Thickness</span> <input type="range" id="cMainWidth" min="1" max="10" step="0.5" value="3.8"></div>
    <div class="f-row"> <span>Opacity</span> <input type="range" id="cMainOp" min="0" max="1" step="0.1" value="1"></div>
    <div style="font-weight:600; font-size:11px; color:#768390; margin-top:6px;">SECONDARY ROADS</div>
    <div id="cSecColorCtrl" class="color-ctrl-cluster"></div>
    <div class="f-row"> <span>Thickness</span> <input type="range" id="cSecWidth" min="0.5" max="8" step="0.5" value="2.8"></div>
    <div class="f-row"> <span>Opacity</span> <input type="range" id="cSecOp" min="0" max="1" step="0.1" value="0.8"></div>
    <div style="font-weight:600; font-size:11px; color:#768390; margin-top:6px;">TERTIARY ROADS</div>
    <div id="cTerColorCtrl" class="color-ctrl-cluster"></div>
    <div class="f-row"> <span>Thickness</span> <input type="range" id="cTerWidth" min="0.5" max="6" step="0.5" value="2.0"></div>
    <div class="f-row"> <span>Opacity</span> <input type="range" id="cTerOp" min="0" max="1" step="0.1" value="0.65"></div>
    <div style="font-weight:600; font-size:11px; color:#768390; margin-top:6px;">RAILWAYS</div>
    <div id="cRailColorCtrl" class="color-ctrl-cluster"></div>
    <div style="font-weight:600; font-size:11px; color:#768390; margin-top:6px;">BOUNDARIES (RED DASHED)</div>
    <div id="cBoundColorCtrl" class="color-ctrl-cluster"></div>
    <div style="font-weight:600; font-size:11px; color:#768390; margin-top:6px;">BUILDINGS</div>
    <div id="cBldColorCtrl" class="color-ctrl-cluster"></div>
    <div class="f-row"> <span>Opacity</span> <input type="range" id="cBldOp" min="0" max="1" step="0.05" value="0.25"></div>
    <div style="font-weight:600; font-size:11px; color:#768390; margin-top:6px;">WATER</div>
    <div id="cWaterColorCtrl" class="color-ctrl-cluster"></div>
    <div class="f-row"> <span>Opacity</span> <input type="range" id="cWaterOp" min="0" max="1" step="0.1" value="1"></div>
</div>

<!-- Trade Area Analysis Modal -->
<div id="trade-area-modal" class="modal-scrim" style="display: none;">
    <div class="float-card open" style="width:500px; max-width:90vw; max-height:85vh; padding:16px;">
        <div class="panel-header">
            <div class="panel-title">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"></path><path d="M2 12l10 6 10-6"></path><path d="M2 16l10 6 10-6"></path></svg>
                <span>Trade Area Analysis</span>
            </div>
            <button class="card-btn" id="closeTradeAreaBtn">✕</button>
        </div>
        <div class="f-row"> <span>Target Polygon</span>
            <select id="tradePolygonSelect" style="width:170px;"> <option value="">-- Choose --</option></select>
        </div>
        <div style="font-weight:600; font-size:11px; color:#768390;">POI CATEGORIES</div>
        <div id="poiCategoryCheckboxes" style="max-height:220px; overflow-y:auto; display:flex; flex-direction:column; gap:6px;"></div>
        <div style="margin-top:8px;">
            <div style="font-weight:600; font-size:11px; color:#768390; margin-bottom:4px;">Custom POI Search (Amenity / Shop)</div>
            <input type="text" id="customPoiSearchInput" placeholder="e.g. amenity=dentist or ev_charging" style="width:100%; background:rgba(0,0,0,0.4); color:#f0f6fc; border:1px solid rgba(255,255,255,0.12); border-radius:8px; padding:6px; font-size:11px;"/>
        </div>
        <button class="trade-btn" id="btnScanTradeArea" style="margin-top:8px;">Scan POIs</button>
        <div id="tradeResults" class="poi-summary"></div>
        <hr style="border-color:rgba(255,255,255,0.1); width:100%;"/>
        <div class="custom-query-collapse-header" id="customQueryToggle">
            <span>CUSTOM OVERPASS QUERY</span>
            <span style="font-size:14px;">▸</span>
        </div>
        <div id="customQueryBody" style="display:none;">
            <textarea id="overpassQueryInput" rows="4" style="background:rgba(0,0,0,0.4); color:#f0f6fc; border:1px solid rgba(255,255,255,0.12); border-radius:8px; padding:8px; font-size:12px; width:100%;"></textarea>
            <div class="f-row"> <span>Result type</span>
                <select id="overpassResultType" style="width:110px;">
                    <option value="marker">Markers</option>
                    <option value="polygon">Polygons</option>
                </select>
            </div>
            <button id="btnRunOverpass" class="trade-btn">Run Custom Query</button>
        </div>
    </div>
</div>

<!-- Project Edit Details Modal -->
<div id="project-edit-modal" class="modal-scrim" style="display: none;">
    <div class="ios26-card" style="max-width: 380px;">
        <div class="ios26-header">
            <div class="ios26-title" style="font-size: 17px;">Project Details</div>
            <div class="ios26-subtitle">Modify workspace name and inspect timestamps</div>
        </div>
        <div class="ios26-body">
            <div class="ios26-input-group">
                <label class="ios26-label">Project Name</label>
                <input class="ios26-input" id="edit-proj-modal-name" placeholder="Workspace Name"/>
            </div>
            <div class="ios26-input-group">
                <label class="ios26-label">Created At</label>
                <input class="ios26-input" id="edit-proj-modal-created" readonly style="opacity: 0.7; cursor: default;"/>
            </div>
            <div class="ios26-input-group">
                <label class="ios26-label">Updated At</label>
                <input class="ios26-input" id="edit-proj-modal-updated" readonly style="opacity: 0.7; cursor: default;"/>
            </div>
            <div style="display: flex; gap: 8px; margin-top: 8px;">
                <button class="trade-btn" id="btn-cancel-edit-project" style="flex: 1; background: #22272e; border: 1px solid #2d333b;">Cancel</button>
                <button class="ios26-action-btn" id="btn-save-edit-project" style="flex: 1;">Save</button>
            </div>
        </div>
    </div>
</div>

<!-- Attribute Table Modal (#popup-attribute-table) -->
<div id="popup-attribute-table" class="float-card">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
        <span style="font-weight:700; color:#f0f6fc;" id="attrTableTitle">Attributes</span>
        <button class="card-btn" id="closeAttrTableBtn">✕</button>
    </div>
    <div style="display:flex; gap:8px; margin-bottom:8px; align-items:center;">
        <input type="text" id="attrTableSearch" placeholder="Find in table (filter)..." style="flex:1; background:rgba(0,0,0,0.4); color:#f0f6fc; border:1px solid rgba(255,255,255,0.12); border-radius:8px; padding:6px 10px; font-size:11px;"/>
        <button id="btnAddAttrCol" class="trade-btn" style="padding:6px 10px; font-size:10px;">+ Add Column</button>
        <button id="btnAddAttrRow" class="trade-btn" style="padding:6px 10px; font-size:10px; background:#22272e; border:1px solid #2d333b;">+ Add Row</button>
    </div>
    <div class="attr-table-container">
        <table class="attr-table" id="attrTableGrid">
            <thead id="attrTableHeader"></thead>
            <tbody id="attrTableBody"></tbody>
        </table>
    </div>
</div>

<!-- Right-click context menu -->
<div id="map-context-menu">
    <div class="ctx-coords" id="ctx-coords-label">0.000000, 0.000000</div>
    <div class="ctx-item" id="ctx-edit" style="display:none;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4v16h16v-7"></path><path d="M18 2l4 4-10 10H8v-4z"></path></svg>
        Edit Feature
    </div>
    <div class="ctx-item" id="ctx-bring-front" style="display:none;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="18 15 12 9 6 15"></polyline></svg>
        Bring to Front
    </div>
    <div class="ctx-item" id="ctx-send-back" style="display:none;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
        Send to Back
    </div>
    <div class="ctx-item" id="ctx-datatable" style="display:none;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>
        Open Data Table
    </div>
    <div class="ctx-divider" id="ctx-divider-feat" style="display:none;"></div>
    <div class="ctx-item" id="ctx-copy">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
        Copy Coordinates
    </div>
    <div class="ctx-item" id="ctx-gmaps">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"></path><circle cx="12" cy="10" r="2.5"></circle></svg>
        Open in Google Maps
    </div>
    <div class="ctx-item" id="ctx-streetview">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M2 12h20"></path><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
        Open in Streetview
    </div>
    <div class="ctx-item" id="ctx-delete" style="display:none; color:#ff7b72;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
        Delete
    </div>
</div>

<div id="launcher-modal-scrim" class="visible">
    <div class="ios26-card">
        <div class="ios26-header">
            <div class="ios26-title">Project Atlas</div>
            <div class="ios26-subtitle">Select workspace.</div>
        </div>
        <div class="ios26-seg">
            <button class="ios26-seg-btn active" id="seg-btn-existing">Existing Workspaces</button>
            <button class="ios26-seg-btn" id="seg-btn-new">Create New</button>
        </div>
        <div class="ios26-body" id="seg-content-existing">
            <div id="existing-projects-container" style="display:flex; flex-direction:column; gap:8px;"></div>
        </div>
        <div class="ios26-body" id="seg-content-new" style="display:none;">
            <div class="ios26-input-group">
                <label class="ios26-label">Workspace Name</label>
                <input class="ios26-input" id="new-proj-name" placeholder="e.g. Untitled Project 1"/>
            </div>
            <button class="ios26-action-btn" id="btn-create-project-submit" style="margin-top:4px;">Create Workspace</button>
        </div>
    </div>
</div>

<div id="hint-toast"></div>

<script>
try {
const ALL_STYLES = __ALL_STYLES__;
const POI_CONFIG = __POI_CONFIG__;
const COLOR_PALETTES = __COLOR_PALETTES__;
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
    pitch: 60,
    bearing: -15,
    attributionControl: false,
    fadeDuration: 0,
    preserveDrawingBuffer: true
});
map.getCanvas().addEventListener('contextmenu', e => e.preventDefault());

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

let features = __INITIAL_FEATURES__;
let fid = features.reduce((max, f) => Math.max(max, f.id || 0), 0);
let customGroups = __INITIAL_CUSTOM_GROUPS__ || {"Trade Area Scan": {collapsed: false, ids: []}};

let activeTool = null, editMode = false;
let draft = [], cursorLL = null, selectedId = null;
let markerShape = 'pin', markerColor = '#1e40af', markerIconSize = 0.9, markerSizeMode = 'dynamic';
let customMarkerImageKey = null;
let customMarkerDataUrl = null;
let selectedLayerIds = new Set();
let isDirty = false;

let undoStack = [];
let redoStack = [];

let isDraggingVertex = false, draggedVertexIdx = -1, draggedPolyId = null, isRadiusHandle = false;
let isDragging = false, dragFeatureId = null, dragStartCoord = null, dragOriginalCoords = null;
let isDraggingRotation = false, rotatingPolyId = null, rotCenter = null, rotStartAngle = 0, rotOriginalCoords = null;

let ctxLngLat = null;
let ctxFeatureId = null;
let editingProjectId = null;
let currentTableFeatureId = null;

let currentRouteMode = 'driving';
let currentRouteColor = '#38bdf8';
let addressStops = ['', ''];

function formatDateTime(dtStr) {
    if (!dtStr) return 'N/A';
    try {
        const d = new Date(dtStr);
        if (isNaN(d.getTime())) return dtStr;
        const pad = n => String(n).padStart(2, '0');
        return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
    } catch(e) {
        return dtStr;
    }
}

function setupColorPicker(containerId, initialColor, onColorChange) {
    const el = document.getElementById(containerId);
    if (!el) return;
    
    let paletteRows = '';
    COLOR_PALETTES.forEach(p => {
        paletteRows += `
            <div class="palette-group">
                <span class="palette-label">${p.name}</span>
                <div class="swatch-row">
                    ${p.colors.map(hex => `<div class="swatch" data-color="${hex}" style="background:${hex};" title="${hex}"></div>`).join('')}
                </div>
            </div>
        `;
    });

    el.innerHTML = `
        ${paletteRows}
        <div class="color-input-combo">
            <input type="color" class="native-color" value="${initialColor}">
            <input type="text" class="hex-text" value="${initialColor}" placeholder="#hex">
            <button class="btn-eyedropper" title="Pick color from screen">
                <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 11l-8-8-8.5 8.5a2.12 2.12 0 0 0 0 3l2.83 2.83a2.12 2.12 0 0 0 3 0L19 11z"></path><path d="M5 19l-3 3"></path></svg>
            </button>
        </div>
    `;
    const nativeColor = el.querySelector('.native-color');
    const hexText = el.querySelector('.hex-text');
    const eyedropperBtn = el.querySelector('.btn-eyedropper');
    
    const updateAll = (col) => {
        nativeColor.value = col;
        hexText.value = col;
        onColorChange(col);
    };

    el.querySelectorAll('.swatch').forEach(sw => {
        sw.onclick = () => updateAll(sw.dataset.color);
    });

    nativeColor.oninput = e => {
        hexText.value = e.target.value;
        onColorChange(e.target.value);
    };

    hexText.onchange = e => {
        let val = e.target.value.trim();
        if (!val.startsWith('#')) val = '#' + val;
        if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
            nativeColor.value = val;
            onColorChange(val);
        }
    };

    eyedropperBtn.onclick = async () => {
        if (window.EyeDropper) {
            try {
                const ed = new EyeDropper();
                const res = await ed.open();
                if (res && res.sRGBHex) updateAll(res.sRGBHex);
            } catch(e) {}
        } else {
            hint('EyeDropper API is not supported in this browser.');
        }
    };
}

const vis = {
    label_city: true, label_brgy: true, label_street: true,
    poi_icons: true, poi_labels: true,
    road_exp: true, road_main: true, road_sec: true, road_ter: true, rd_rail: true,
    bound_prov: false, bound_city: false, bound_brgy: false,
    building2d: false, building3d: true, water: true, waterway: true
};

const VIS_MAP = {
    label_city: ['label_city'],
    label_brgy: ['label_brgy'],
    label_street: ['label_street'],
    poi_icons: ['draw-marker'],
    poi_labels: ['draw-poly-labels', 'draw-text'],
    road_exp: ['case_express_casing', 'rd_express'],
    road_main: ['case_major_casing', 'rd_major'],
    road_sec: ['case_secondary_casing', 'rd_secondary'],
    road_ter: ['case_tertiary_casing', 'rd_tertiary', 'rd_min_md', 'rd_min_lo', 'rd_path'],
    rd_rail: ['rd_rail'],
    bound_prov: ['bound_prov'],
    bound_city: ['bound_city'],
    bound_brgy: ['bound_brgy'],
    building2d: ['building-2d'],
    building3d: ['building-3d'],
    water: ['water'],
    waterway: ['waterway']
};

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

function pushState() {
    undoStack.push(JSON.stringify({
        features: features,
        customGroups: customGroups
    }));
    if (undoStack.length > 50) undoStack.shift();
    redoStack = [];
}

const markDirty = (recordHistory = true) => {
    if (recordHistory) pushState();
    isDirty = true;
    setSaveBadgeStatus('unsaved');
};

const undo = () => {
    if (!undoStack.length) { hint('Nothing to undo'); return; }
    redoStack.push(JSON.stringify({ features: features, customGroups: customGroups }));
    const prev = JSON.parse(undoStack.pop());
    features = prev.features;
    customGroups = prev.customGroups;
    fid = features.reduce((max, f) => Math.max(max, f.id || 0), 0);
    syncDraw();
    renderMyLayers();
    setSaveBadgeStatus('unsaved');
    hint('Undo');
};

const redo = () => {
    if (!redoStack.length) { hint('Nothing to redo'); return; }
    undoStack.push(JSON.stringify({ features: features, customGroups: customGroups }));
    const next = JSON.parse(redoStack.pop());
    features = next.features;
    customGroups = next.customGroups;
    fid = features.reduce((max, f) => Math.max(max, f.id || 0), 0);
    syncDraw();
    renderMyLayers();
    setSaveBadgeStatus('unsaved');
    hint('Redo');
};

const closeFloatingCards = () => {
    ['popup-marker-settings','popup-text-settings','popup-shape-editor','popup-custom-map','popup-search','popup-route-settings','browser-panel','mylayers-panel','popup-attribute-table'].forEach(id => {
        const el = $(id);
        if (el) el.classList.remove('open');
    });
    $('trade-area-modal').style.display = 'none';
    $('project-edit-modal').style.display = 'none';
    $('map-context-menu').style.display = 'none';
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

function getNextUntitledProjectName() {
    const untitledRegex = /^Untitled Project (\d+)$/i;
    let maxN = 0;
    ALL_PROJECTS.forEach(p => {
        const match = (p.name || '').match(untitledRegex);
        if (match) {
            const num = parseInt(match[1], 10);
            if (num > maxN) maxN = num;
        }
    });
    return `Untitled Project ${maxN + 1}`;
}

function openHomeDialog() {
    closeFloatingCards();
    $('launcher-modal-scrim').classList.add('visible');
    $('new-proj-name').value = getNextUntitledProjectName();
    renderProjectsList();
}
function closeHomeDialog() {
    $('launcher-modal-scrim').classList.remove('visible');
}
$('btn-home-dialog').onclick = openHomeDialog;

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
    $('new-proj-name').value = getNextUntitledProjectName();
    $('new-proj-name').focus();
};

function renderProjectsList() {
    const container = $('existing-projects-container');
    if (!ALL_PROJECTS || !ALL_PROJECTS.length) {
        container.innerHTML = `<div style="color:rgba(255,255,255,0.5); font-size:12px; text-align:center; padding:16px;">No saved projects. Create your first workspace above.</div>`;
        return;
    }
    container.innerHTML = ALL_PROJECTS.map(p => `
        <div class="ios26-proj-item">
            <div style="display:flex; flex-direction:column; gap:2px; flex:1; cursor:pointer;" onclick="loadProjectDirectly('${p.id}')">
                <span style="font-weight:700; font-size:13px; color:#ffffff;">${p.name || 'Untitled Project'}</span>
                <span style="font-size:11px; color:rgba(255,255,255,0.5);">Updated: ${formatDateTime(p.updated_at || p.created_at)}</span>
            </div>
            <div style="display:flex; align-items:center; gap:6px;">
                <button class="card-btn" onclick="openProjectEditModal(event, '${p.id}')" title="Details & Edit Name">
                    <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                </button>
                <button class="card-btn" onclick="deleteProjectFromLauncher(event, '${p.id}', '${(p.name || '').replace(/'/g, "\\'")}')" title="Delete" style="color:#ff7b72;">
                    <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
            </div>
        </div>
    `).join('');
}

window.loadProjectDirectly = function(projectId) {
    const p = ALL_PROJECTS.find(x => x.id === projectId);
    if (!p) return;
    currentProjectId = p.id;
    currentProjectName = p.name || 'Untitled Project';
    $('project-name-display').textContent = currentProjectName;
    features = p.features || [];
    fid = features.reduce((max, f) => Math.max(max, f.id || 0), 0);
    customGroups = p.custom_groups || {"Trade Area Scan": {collapsed: false, ids: []}};
    if (p.center) map.setCenter(p.center);
    if (p.zoom) map.setZoom(p.zoom);
    map.setPitch(p.pitch !== undefined ? p.pitch : 60);
    if (p.bearing !== undefined) map.setBearing(p.bearing);
    if (p.basemap && ALL_STYLES[p.basemap]) {
        currentStyleName = p.basemap;
        map.setStyle(ALL_STYLES[p.basemap]);
    }
    features.forEach(f => {
        if (f.kind === 'marker') {
            const sh = f.props.shape || 'pin';
            const col = f.props.color || '#1e40af';
            f.props.iconKey = f.props.iconKey || getIconKey(sh, col);
        }
    });
    map.once('idle', () => {
        addDrawStack();
        applyVis();
        renderMyLayers();
    });
    closeHomeDialog();
    undoStack = [];
    redoStack = [];
};

window.openProjectEditModal = function(e, projectId) {
    e.stopPropagation();
    const p = ALL_PROJECTS.find(x => x.id === projectId);
    if (!p) return;
    editingProjectId = projectId;
    $('edit-proj-modal-name').value = p.name || 'Untitled Project';
    $('edit-proj-modal-created').value = formatDateTime(p.created_at || p.updated_at);
    $('edit-proj-modal-updated').value = formatDateTime(p.updated_at || p.created_at);
    $('project-edit-modal').style.display = 'flex';
};

$('btn-cancel-edit-project').onclick = () => {
    $('project-edit-modal').style.display = 'none';
    editingProjectId = null;
};

$('btn-save-edit-project').onclick = async () => {
    const newName = $('edit-proj-modal-name').value.trim();
    if (!newName || !editingProjectId) return;
    const target = ALL_PROJECTS.find(x => x.id === editingProjectId);
    const nowIso = new Date().toISOString();
    if (target) {
        target.name = newName;
        target.updated_at = nowIso;
    }
    if (currentProjectId === editingProjectId) {
        currentProjectName = newName;
        $('project-name-display').textContent = newName;
    }
    renderProjectsList();
    $('project-edit-modal').style.display = 'none';
    try {
        await fetch(`${SUPABASE_URL.replace('/rest/v1/','').replace(/\/$/,'')}/rest/v1/map_projects?id=eq.${editingProjectId}`, {
            method: 'PATCH',
            headers: {
                'apikey': SUPABASE_KEY,
                'Authorization': `Bearer ${SUPABASE_KEY}`,
                'Content-Type': 'application/json',
                'Prefer': 'return=minimal'
            },
            body: JSON.stringify({ name: newName, updated_at: nowIso })
        });
        hint('Workspace updated successfully');
    } catch(err) {}
    editingProjectId = null;
};

window.deleteProjectFromLauncher = async function(e, projectId, name) {
    e.stopPropagation();
    if (!confirm(`Delete project "${name}" permanently?`)) return;
    ALL_PROJECTS = ALL_PROJECTS.filter(x => x.id !== projectId);
    renderProjectsList();
    try {
        await fetch(`${SUPABASE_URL.replace('/rest/v1/','').replace(/\/$/,'')}/rest/v1/map_projects?id=eq.${projectId}`, {
            method: 'DELETE',
            headers: {
                'apikey': SUPABASE_KEY,
                'Authorization': `Bearer ${SUPABASE_KEY}`
            }
        });
    } catch(err) {}
};

$('btn-create-project-submit').onclick = async () => {
    const pName = $('new-proj-name').value.trim() || getNextUntitledProjectName();
    const centerLL = [120.9842, 14.5995];
    const payload = {
        name: pName,
        basemap: "Midnight Blue",
        center: centerLL,
        zoom: 14,
        pitch: 60,
        bearing: -15,
        features: [],
        custom_groups: {"Trade Area Scan": {collapsed: false, ids: []}},
        layer_visibilities: vis
    };
    try {
        const res = await fetch(`${SUPABASE_URL.replace('/rest/v1/','').replace(/\/$/,'')}/rest/v1/map_projects`, {
            method: 'POST',
            headers: {
                'apikey': SUPABASE_KEY,
                'Authorization': `Bearer ${SUPABASE_KEY}`,
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            const created = await res.json();
            const proj = created[0] || created;
            ALL_PROJECTS.unshift(proj);
            loadProjectDirectly(proj.id);
        } else {
            currentProjectId = "local-temp";
            currentProjectName = pName;
            $('project-name-display').textContent = pName;
            features = [];
            customGroups = {"Trade Area Scan": {collapsed: false, ids: []}};
            map.setCenter(centerLL);
            map.setPitch(60);
            closeHomeDialog();
        }
    } catch(e) {
        closeHomeDialog();
    }
};

$('project-name-display').onclick = () => {
    const newN = prompt('Rename project name:', currentProjectName);
    if (newN && newN.trim() && newN.trim() !== currentProjectName) {
        currentProjectName = newN.trim();
        $('project-name-display').textContent = currentProjectName;
        markDirty();
    }
};

async function saveProjectToSupabase(showToast = false) {
    if (!currentProjectId || currentProjectId === "local-temp" || !SUPABASE_URL || !SUPABASE_KEY) {
        return;
    }
    setSaveBadgeStatus('saving');
    const c = map.getCenter();
    const nowIso = new Date().toISOString();
    const payload = {
        updated_at: nowIso,
        name: currentProjectName,
        center: [c.lng, c.lat],
        zoom: map.getZoom(),
        pitch: map.getPitch(),
        bearing: map.getBearing(),
        basemap: currentStyleName,
        features: features,
        custom_groups: customGroups,
        layer_visibilities: vis
    };
    try {
        const res = await fetch(`${SUPABASE_URL.replace('/rest/v1/','').replace(/\/$/,'')}/rest/v1/map_projects?id=eq.${currentProjectId}`, {
            method: 'PATCH',
            headers: {
                'apikey': SUPABASE_KEY,
                'Authorization': `Bearer ${SUPABASE_KEY}`,
                'Content-Type': 'application/json',
                'Prefer': 'return=minimal'
            },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            isDirty = false;
            setSaveBadgeStatus('saved');
            const target = ALL_PROJECTS.find(x => x.id === currentProjectId);
            if (target) {
                target.name = currentProjectName;
                target.updated_at = nowIso;
                target.features = features;
                target.custom_groups = customGroups;
            }
            if (showToast) hint('Project Saved!');
        } else {
            setSaveBadgeStatus('unsaved');
            if (showToast) hint('Failed to save project');
        }
    } catch(e) {
        setSaveBadgeStatus('unsaved');
        if (showToast) hint('Save request error');
    }
}

setInterval(() => { if (isDirty) saveProjectToSupabase(false); }, 20000);
$('btn-save-project').onclick = () => saveProjectToSupabase(true);
$('btn-undo').onclick = undo;
$('btn-redo').onclick = redo;

document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        saveProjectToSupabase(true);
    }
    if ((e.ctrlKey || e.metaKey) && (e.key === 'z' || e.key === 'Z')) {
        e.preventDefault();
        if (e.shiftKey) redo();
        else undo();
    }
    if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || e.key === 'Y')) {
        e.preventDefault();
        redo();
    }
    if (e.key === 'Escape') {
        $('map-context-menu').style.display = 'none';
        resetActiveTools();
    }
});

function renderIconCanvas(shape, color) {
    const c = document.createElement('canvas');
    c.width = 64; c.height = 64;
    const ctx = c.getContext('2d');
    ctx.clearRect(0,0,64,64);
    ctx.strokeStyle = '#ffffff';
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
    } else if (shape === 'pinball') {
        ctx.arc(32, 26, 16, 0, Math.PI * 2);
        ctx.fill(); ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(28, 42); ctx.lineTo(36, 42); ctx.lineTo(32, 56); ctx.closePath();
        ctx.fill(); ctx.stroke();
        ctx.beginPath();
        ctx.fillStyle = '#ffffff';
        ctx.arc(32, 26, 6, 0, Math.PI * 2);
        ctx.fill();
        return c;
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

$('customMarkerFileInput').onchange = function(e) {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
        hint('Image must be ≤ 5 MB');
        return;
    }
    const reader = new FileReader();
    reader.onload = async (ev) => {
        customMarkerDataUrl = ev.target.result;
        const img = new Image();
        img.onload = () => {
            const c = document.createElement('canvas');
            c.width = 64; c.height = 64;
            const ctx = c.getContext('2d');
            ctx.drawImage(img, 0, 0, 64, 64);
            const key = 'custom_marker_' + Date.now();
            const imgData = ctx.getImageData(0,0,64,64);
            try {
                if (map.hasImage(key)) map.removeImage(key);
                map.addImage(key, imgData, { pixelRatio: 2 });
                customMarkerImageKey = key;
                hint('Custom marker ready');
            } catch(err) { hint('Failed to add custom image'); }
        };
        img.src = customMarkerDataUrl;
    };
    reader.readAsDataURL(file);
};

const ICON_SVGS = {
    pin: '<path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"></path><circle cx="12" cy="10" r="2.5"></circle>',
    star: '<path d="M12 2l2.9 6.3 6.9.8-5.1 4.7 1.4 6.8-6.1-3.4-6.1 3.4 1.4-6.8L2.2 9.1l6.9-.8z"></path>',
    circle: '<circle cx="12" cy="12" r="8"></circle>',
    square: '<rect x="5" y="5" width="14" height="14"></rect>',
    flag: '<path d="M6 21V4"></path><path d="M6 4l12 3-12 3"></path>',
    heart: '<path d="M12 20s-7-4.6-7-10a4 4 0 0 1 7-2.5A4 4 0 0 1 19 10c0 5.4-7 10-7 10z"></path>',
    pinball: '<circle cx="12" cy="10" r="7"></circle><line x1="12" y1="17" x2="12" y2="22"></line>'
};

$('markerIconGrid').innerHTML = Object.keys(ICON_SVGS).map(s =>
    `<button data-s="${s}" class="${s === markerShape ? 'active' : ''}">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">${ICON_SVGS[s]}</svg>
    </button>`).join('');

$('markerIconGrid').querySelectorAll('button').forEach(b => b.onclick = () => {
    markerShape = b.dataset.s;
    $('markerIconGrid').querySelectorAll('button').forEach(x => x.classList.toggle('active', x === b));
    customMarkerImageKey = null;
    markDirty();
});
$('mSize').oninput = e => { markerIconSize = parseFloat(e.target.value); markDirty(); };
$('mSizeMode').onchange = e => { markerSizeMode = e.target.value; markDirty(); };

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

        // 3D Extrusion Layer for User-Drawn 3D Polygons
        map.addLayer({
            id: 'draw-3d-extrusion', type: 'fill-extrusion', source: 'draw',
            filter: ['all', ['==', ['geometry-type'], 'Polygon'], ['==', ['get', 'kind'], 'polygon3d']],
            paint: {
                'fill-extrusion-color': ['coalesce', ['get', 'fillColor'], ['get', 'color'], '#38bdf8'],
                'fill-extrusion-height': ['coalesce', ['get', 'extrusionHeight'], 35],
                'fill-extrusion-base': ['coalesce', ['get', 'extrusionBase'], 0],
                'fill-extrusion-opacity': ['*', ['coalesce', ['get', 'fillOpacity'], 0.85], ['get', 'visible']]
            }
        });

        map.addLayer({
            id: 'draw-fill', type: 'fill', source: 'draw',
            filter: ['all', ['==', ['geometry-type'], 'Polygon'], ['!=', ['get', 'kind'], 'polygon3d']],
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
                'line-color': ['case', ['boolean', ['get', 'routingFailed'], false], '#f85149', ['coalesce', ['get', 'borderColor'], ['get', 'color'], '#38bdf8']],
                'line-width': ['coalesce', ['get', 'width'], 4],
                'line-opacity': ['*', ['coalesce', ['get', 'borderOpacity'], 0.9], ['get', 'visible']],
                'line-dasharray': ['case', ['boolean', ['get', 'routingFailed'], false], ['literal', [2, 2]], ['literal', [1, 0]]]
            }
        });

        // Marker layer with dynamic vs static zoom interpolation
        map.addLayer({
            id: 'draw-marker', type: 'symbol', source: 'draw',
            filter: ['all', ['==', ['geometry-type'], 'Point'], ['!=', ['get', 'kind'], 'text']],
            layout: {
                'icon-image': ['get', 'iconKey'],
                'icon-size': [
                    'case',
                    ['==', ['coalesce', ['get', 'markerSizeMode'], 'dynamic'], 'static'],
                    ['coalesce', ['get', 'iconSize'], 0.9],
                    [
                        'interpolate',
                        ['exponential', 1.4],
                        ['zoom'],
                        8, ['*', ['coalesce', ['get', 'iconSize'], 0.9], 0.35],
                        14, ['coalesce', ['get', 'iconSize'], 0.9],
                        18, ['*', ['coalesce', ['get', 'iconSize'], 0.9], 2.2]
                    ]
                ],
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
                'text-halo-color': '#0a1628',
                'text-halo-width': 2
            }
        });

        map.addSource('label-src', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
        map.addLayer({
            id: 'draw-poly-labels', type: 'symbol', source: 'label-src',
            layout: {
                'text-field': ['get', 'labelText'],
                'text-font': ['Noto Sans Regular'],
                'text-size': 13,
                'text-allow-overlap': true,
                'text-anchor': 'center',
                'text-justify': 'center'
            },
            paint: {
                'text-color': '#ffffff',
                'text-halo-color': '#0a1628',
                'text-halo-width': 2
            }
        });

        map.addSource('pulse-src', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
        map.addLayer({
            id: 'pulse-circle', type: 'circle', source: 'pulse-src',
            paint: {
                'circle-color': '#38bdf8',
                'circle-radius': 10,
                'circle-opacity': 0.85,
                'circle-stroke-color': '#ffffff',
                'circle-stroke-width': 2
            }
        });
    } else {
        map.getSource('draw').setData(fc(features));
    }

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
                'circle-stroke-width': 2.5
            }
        });
    }

    if (!map.getSource('vertex-handles')) {
        map.addSource('vertex-handles', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
        map.addLayer({
            id: 'vertex-points', type: 'circle', source: 'vertex-handles',
            paint: {
                'circle-color': ['case', ['boolean', ['get', 'isRotHandle'], false], '#e8b84a', ['case', ['boolean', ['get', 'isRadiusHandle'], false], '#3fb950', '#38bdf8']],
                'circle-radius': 6,
                'circle-stroke-color': '#ffffff',
                'circle-stroke-width': 2
            }
        });
    }
}

const syncDraw = () => {
    if (map.getSource('draw')) map.getSource('draw').setData(fc(features));
    syncVertexHandles();
    syncLabels();
};

function syncLabels() {
    const src = map.getSource('label-src');
    if (!src) return;
    const feats = [];
    features.forEach(f => {
        if (!f.props.showLabel || f.props.visible === 0) return;
        let labelText = f.name;
        if (f.kind === 'route' && f.props.metadata) {
            const dist = f.props.metadata.distance;
            const dur = f.props.metadata.duration;
            const distStr = dist > 1000 ? `${(dist/1000).toFixed(2)} km` : `${Math.round(dist)} m`;
            const durStr = dur > 3600 ? `${(dur/3600).toFixed(1)} hr` : `${Math.round(dur/60)} min`;
            labelText = `${distStr} · ${durStr}`;
        } else if (f.props.attributes && f.props.attributes.label_text) {
            labelText = f.props.attributes.label_text;
        }
        if (!labelText) return;

        const pos = f.props.labelPos || 'center';
        let coords = null;
        if (f.geometry.type === 'Point') {
            const x = f.geometry.coordinates[0];
            const y = f.geometry.coordinates[1];
            const d = 0.0009;
            if (pos === 'top') coords = [x, y + d];
            else if (pos === 'bottom') coords = [x, y - d];
            else if (pos === 'left') coords = [x - d, y];
            else if (pos === 'right') coords = [x + d, y];
            else coords = [x, y];
        } else {
            const b = calcBounds(f);
            if (!b) return;
            const cx = (b[0][0] + b[1][0]) / 2;
            const cy = (b[0][1] + b[1][1]) / 2;
            if (pos === 'top') coords = [cx, b[1][1]];
            else if (pos === 'bottom') coords = [cx, b[0][1]];
            else if (pos === 'left') coords = [b[0][0], cy];
            else if (pos === 'right') coords = [b[1][0], cy];
            else coords = [cx, cy];
        }
        feats.push({
            type: 'Feature',
            geometry: { type: 'Point', coordinates: coords },
            properties: { labelText: labelText }
        });
    });
    src.setData({ type: 'FeatureCollection', features: feats });
}

function pulseFeature(f) {
    const b = calcBounds(f);
    if (!b) return;
    const c = [(b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2];
    const src = map.getSource('pulse-src');
    if (!src) return;
    src.setData({ type: 'FeatureCollection', features: [{ type: 'Feature', geometry: { type: 'Point', coordinates: c }, properties: {} }] });
    const start = performance.now();
    const dur = 1600;
    function frame(t) {
        const el = t - start;
        const prog = (el % 800) / 800;
        const r = 8 + prog * 55;
        const op = 0.9 * (1 - prog);
        if (map.getLayer('pulse-circle')) {
            map.setPaintProperty('pulse-circle', 'circle-radius', r);
            map.setPaintProperty('pulse-circle', 'circle-opacity', op);
        }
        if (el < dur) requestAnimationFrame(frame);
        else src.setData({ type: 'FeatureCollection', features: [] });
    }
    requestAnimationFrame(frame);
}

function syncVertexHandles() {
    if (!map.getSource('vertex-handles')) return;
    if (!editMode || !selectedId) {
        map.getSource('vertex-handles').setData({ type: 'FeatureCollection', features: [] });
        return;
    }
    const handleFeats = [];
    const f = features.find(x => x.id === selectedId);
    if (f && f.props.visible !== 0) {
        if (f.kind === 'circle') {
            if (f.props.centerCoord && f.props.radiusMeters) {
                const c = f.props.centerCoord;
                const r = f.props.radiusMeters;
                const edgeCoord = [c[0] + (r / (111320 * Math.cos(c[1]*Math.PI/180))), c[1]];
                handleFeats.push({
                    type: 'Feature',
                    geometry: { type: 'Point', coordinates: edgeCoord },
                    properties: { polyId: f.id, isRadiusHandle: true }
                });
            }
        } else if (['polygon','polygon3d','rectangle'].includes(f.kind) && f.geometry && f.geometry.coordinates && f.geometry.coordinates[0]) {
            const coords = f.geometry.coordinates[0];
            for (let i = 0; i < coords.length - 1; i++) {
                handleFeats.push({
                    type: 'Feature',
                    geometry: { type: 'Point', coordinates: coords[i] },
                    properties: { polyId: f.id, vIdx: i }
                });
            }
        } else if ((f.kind === 'polyline' || f.kind === 'route') && f.geometry && f.geometry.coordinates) {
            const coords = f.props.waypoints || f.geometry.coordinates;
            for (let i = 0; i < coords.length; i++) {
                handleFeats.push({
                    type: 'Feature',
                    geometry: { type: 'Point', coordinates: coords[i] },
                    properties: { polyId: f.id, vIdx: i, isWaypoint: true }
                });
            }
        }
        
        const b = calcBounds(f);
        if (b) {
            const cx = (b[0][0] + b[1][0]) / 2;
            const offset = (b[1][1] - b[0][1]) * 0.25 || 0.001;
            handleFeats.push({
                type: 'Feature',
                geometry: { type: 'Point', coordinates: [cx, b[1][1] + offset] },
                properties: { polyId: f.id, isRotHandle: true }
            });
        }
    }
    map.getSource('vertex-handles').setData({ type: 'FeatureCollection', features: handleFeats });
}

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
        const isOrigin = i === 0 && (activeTool === 'polygon' || activeTool === 'polygon3d');
        const isLastPoint = i === draft.length - 1 && activeTool === 'route' && draft.length > 0;
        f.push(pt(p, isOrigin, isLastPoint));
    });
    if ((activeTool === 'polyline' || activeTool === 'route') && draft.length) {
        f.push(ln(cursorLL ? [...draft, cursorLL] : draft));
    }
    if ((activeTool === 'polygon' || activeTool === 'polygon3d') && draft.length) {
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

map.on('load', () => {
    features.forEach(f => {
        if (f.kind === 'marker') {
            const sh = f.props.shape || 'pin';
            const col = f.props.color || '#1e40af';
            f.props.iconKey = f.props.iconKey || getIconKey(sh, col);
        }
    });
    addDrawStack();
    applyVis();
    renderMyLayers();
    renderProjectsList();
    populateTradeAreaCheckboxes();
    renderAddressStopInputs();
    
    setupColorPicker('mColorCtrl', '#1e40af', col => { markerColor = col; markDirty(); });
    setupColorPicker('tColorCtrl', '#d9b451', col => { $('tColorCtrl').dataset.val = col; markDirty(); });
    setupColorPicker('eBorderColorCtrl', '#38bdf8', col => {
        const f = features.find(x => x.id === selectedId);
        if (f) {
            f.props.borderColor = col; f.props.color = col;
            if (f.kind === 'marker' && !customMarkerImageKey) f.props.iconKey = getIconKey(f.props.shape || 'pin', col);
            syncDraw(); markDirty();
        }
    });
    setupColorPicker('eFillColorCtrl', '#e8b84a', col => {
        const f = features.find(x => x.id === selectedId);
        if (f) { f.props.fillColor = col; syncDraw(); markDirty(); }
    });
    
    setupColorPicker('cBgColorCtrl', '#0a1628', col => { setMapPaint('bg', 'background-color', col); markDirty(); });
    setupColorPicker('cExpColorCtrl', '#ffaa00', col => { setMapPaint('rd_express', 'line-color', col); markDirty(); });
    setupColorPicker('cMainColorCtrl', '#e8b84a', col => { setMapPaint('rd_major', 'line-color', col); markDirty(); });
    setupColorPicker('cSecColorCtrl', '#c99c37', col => { setMapPaint('rd_secondary', 'line-color', col); markDirty(); });
    setupColorPicker('cTerColorCtrl', '#7d5f14', col => { ['rd_tertiary','rd_min_md','rd_min_lo','rd_path'].forEach(id => setMapPaint(id, 'line-color', col)); markDirty(); });
    setupColorPicker('cRailColorCtrl', '#d9b451', col => { setMapPaint('rd_rail', 'line-color', col); markDirty(); });
    setupColorPicker('cBoundColorCtrl', '#ff1e1e', col => { ['bound_prov','bound_city','bound_brgy'].forEach(id => setMapPaint(id, 'line-color', col)); markDirty(); });
    setupColorPicker('cBldColorCtrl', '#8e7258', col => { setMapPaint('building-2d', 'fill-color', col); setMapPaint('building-2d', 'fill-outline-color', col); markDirty(); });
    setupColorPicker('cWaterColorCtrl', '#0a1424', col => { setMapPaint('water', 'fill-color', col); setMapPaint('waterway', 'line-color', col); markDirty(); });
});

// Dimension Switcher
$('btn2DMode').onclick = () => {
    $('btn2DMode').classList.add('active');
    $('btn3DMode').classList.remove('active');
    map.setLayoutProperty('building-2d', 'visibility', 'visible');
    map.setLayoutProperty('building-3d', 'visibility', 'none');
    vis.building2d = true;
    vis.building3d = false;
    map.easeTo({ pitch: 0 });
    markDirty();
};
$('btn3DMode').onclick = () => {
    $('btn3DMode').classList.add('active');
    $('btn2DMode').classList.remove('active');
    map.setLayoutProperty('building-2d', 'visibility', 'none');
    map.setLayoutProperty('building-3d', 'visibility', 'visible');
    vis.building2d = false;
    vis.building3d = true;
    map.easeTo({ pitch: 60, bearing: -15 });
    markDirty();
};

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

function rotateGeometry(f, angleRad, center) {
    const cosA = Math.cos(angleRad), sinA = Math.sin(angleRad);
    const rotPt = pt => {
        const dx = pt[0] - center[0], dy = pt[1] - center[1];
        return [center[0] + dx * cosA - dy * sinA, center[1] + dx * sinA + dy * cosA];
    };
    if (f.geometry.type === 'Point') {
        f.props.rotation = ((f.props.rotation || 0) + (angleRad * 180 / Math.PI)) % 360;
    } else if (f.geometry.type === 'LineString') {
        f.geometry.coordinates = f.geometry.coordinates.map(rotPt);
        if (f.props.waypoints) f.props.waypoints = f.props.waypoints.map(rotPt);
    } else if (f.geometry.type === 'Polygon') {
        f.geometry.coordinates = f.geometry.coordinates.map(ring => ring.map(rotPt));
    }
}

let rerouteTimeout = null;
function fetchMultiPointRoute(pts, updateId = null, mode = null) {
    hint('Calculating route…');
    const profile = mode || currentRouteMode || 'driving';
    const coordStr = pts.map(p => `${p[0]},${p[1]}`).join(';');
    const url = `https://router.project-osrm.org/route/v1/${profile}/${coordStr}?overview=full&geometries=geojson&steps=true`;
    
    fetch(url)
    .then(r => r.json())
    .then(j => {
        if (j.routes && j.routes[0]) {
            const route = j.routes[0];
            const geom = route.geometry;
            const dist = route.distance;
            const dur = route.duration;
            const distStr = dist > 1000 ? `${(dist/1000).toFixed(2)} km` : `${Math.round(dist)} m`;
            const durStr = dur > 3600 ? `${(dur/3600).toFixed(1)} hr` : `${Math.round(dur/60)} min`;
            const desc = `${distStr} · ${durStr}`;
            
            if (updateId) {
                const f = features.find(x => x.id === updateId);
                if (f) {
                    f.geometry = geom;
                    f.props.waypoints = pts;
                    f.props.description = desc;
                    f.props.routeMode = profile;
                    f.props.routingFailed = false;
                    f.props.metadata = { distance: dist, duration: dur };
                    syncDraw();
                    renderMyLayers();
                    markDirty();
                    if (selectedId === updateId) {
                        $('eRouteStats').textContent = desc;
                        renderWaypointEditor(f);
                    }
                }
            } else {
                addFeatureRecord('route', geom, { 
                    color: currentRouteColor, borderColor: currentRouteColor, width: 4, borderOpacity: 0.9,
                    description: desc,
                    routeMode: profile,
                    waypoints: pts,
                    routingFailed: false,
                    metadata: { distance: dist, duration: dur },
                    showLabel: true
                });
            }
        } else {
            throw new Error("No route found");
        }
        hint('');
    })
    .catch(() => {
        if (updateId) {
             const f = features.find(x => x.id === updateId);
             if (f) {
                 f.geometry = { type: 'LineString', coordinates: pts };
                 f.props.waypoints = pts;
                 f.props.routingFailed = true;
                 f.props.description = "Routing unavailable – straight line shown";
                 syncDraw();
                 markDirty();
             }
        } else {
            addFeatureRecord('route', { type: 'LineString', coordinates: pts }, { 
                color: currentRouteColor, borderColor: currentRouteColor, width: 3, borderOpacity: 0.8,
                routingFailed: true,
                waypoints: pts,
                description: "Routing unavailable – straight line shown",
                routeMode: profile,
                showLabel: true
            });
        }
        hint('Routing unavailable – straight line shown');
    });
}

function addFeatureRecord(kind, geometry, customProps = {}, targetGroup = null, explicitName = null) {
    const newId = ++fid;
    const isRoute = kind === 'route';
    const is3DPoly = kind === 'polygon3d';
    const defaultBorder = isRoute ? (customProps.borderColor || currentRouteColor) : (is3DPoly ? '#38bdf8' : '#e8b84a');
    const defaultFill = is3DPoly ? '#38bdf8' : '#e8b84a';
    const assignedName = explicitName || `${kind.charAt(0).toUpperCase() + kind.slice(1)} ${newId}`;
    const feat = {
        id: newId,
        name: assignedName,
        kind: kind,
        geometry: geometry,
        props: {
            color: defaultBorder,
            borderColor: defaultBorder,
            borderOpacity: 0.9,
            width: 3,
            fillColor: defaultFill,
            fillOpacity: is3DPoly ? 0.85 : 0.35,
            extrusionHeight: is3DPoly ? 35 : 0,
            extrusionBase: 0,
            showLabel: false,
            labelPos: 'center',
            iconSize: markerIconSize,
            markerSizeMode: markerSizeMode,
            visible: 1,
            rotation: 0,
            attributes: { name: assignedName, description: isRoute ? (customProps.description || '') : '' },
            ...customProps
        }
    };
    features.push(feat);
    if (targetGroup && customGroups[targetGroup]) {
        customGroups[targetGroup].ids.push(newId);
    }
    syncDraw();
    renderMyLayers();
    markDirty();
    return feat;
}

// ----------------- Feature Popup on Left-Click (No Edit Button) -----------------
function showFeaturePopup(f, clickLngLat) {
    let popupCoords = clickLngLat;
    if (!popupCoords) {
        const bnd = calcBounds(f);
        if (bnd) popupCoords = [(bnd[0][0] + bnd[1][0]) / 2, (bnd[0][1] + bnd[1][1]) / 2];
        else popupCoords = [120.9842, 14.5995];
    }
    
    let primaryImageHtml = '';
    let tableRowsHtml = '';

    if (f.props.attrRows && f.props.attrRows.length > 0 && f.props.attrTypes) {
        for (const row of f.props.attrRows) {
            for (const col in f.props.attrTypes) {
                if (f.props.attrTypes[col] === 'image' && row[col] && row[col].startsWith('data:image')) {
                    primaryImageHtml = `<img src="${row[col]}" style="width:100%; max-height:160px; object-fit:cover; border-radius:8px; margin-bottom:8px; display:block; border:1px solid rgba(255,255,255,0.15);"/>`;
                    break;
                }
            }
            if (primaryImageHtml) break;
        }
    }

    if (f.props.osmTags && Object.keys(f.props.osmTags).length > 0) {
        for (const k in f.props.osmTags) {
            tableRowsHtml += `<tr><th>${k}</th><td>${f.props.osmTags[k]}</td></tr>`;
        }
    } else if (f.props.attributes && Object.keys(f.props.attributes).length > 0) {
        for (const k in f.props.attributes) {
            const val = f.props.attributes[k];
            if (val && typeof val === 'string' && val.startsWith('data:image')) continue;
            tableRowsHtml += `<tr><th>${k}</th><td>${val || '-'}</td></tr>`;
        }
    }

    if (!tableRowsHtml) {
        tableRowsHtml = `<tr><th>name</th><td>${f.name}</td></tr><tr><th>type</th><td>${f.kind}</td></tr>`;
        if (f.props.description) tableRowsHtml += `<tr><th>description</th><td>${f.props.description}</td></tr>`;
    }

    const html = `
        <div id="popup-feature-info">
            <div style="font-weight:700; margin-bottom:6px; color:#38bdf8; font-size:13px;">${f.name}</div>
            ${primaryImageHtml}
            <table class="tag-table">
                ${tableRowsHtml}
            </table>
            <div style="display:flex; justify-content:flex-end; gap:6px; margin-top:8px; border-top:1px solid rgba(255,255,255,0.08); padding-top:6px;">
                <button onclick="openAttributeTable(${f.id});" style="background:rgba(255,255,255,0.1); color:#adbac7; border:1px solid rgba(255,255,255,0.1); border-radius:4px; padding:3px 8px; font-size:10px; cursor:pointer;">Open Table</button>
            </div>
        </div>
    `;

    new maplibregl.Popup({ maxWidth: '320px' })
        .setLngLat(popupCoords)
        .setHTML(html)
        .addTo(map);
}

function populateTradeAreaCheckboxes() {
    const container = $('poiCategoryCheckboxes');
    let html = '';
    for (const category in POI_CONFIG) {
        html += `<div style="font-weight:600; font-size:11px; margin-top:4px;">${category}</div>`;
        html += '<div class="trade-area-poi-row">';
        POI_CONFIG[category].forEach(([label, tag]) => {
            html += `<label> <input type="checkbox" class="poi-cat-check" data-cat="${category}" data-tag="${tag}" data-label="${label}" style="accent-color:#316dca;"> ${label}</label>`;
        });
        html += '</div>';
    }
    container.innerHTML = html;
}

$('btnOpenTradeAreaPopup').onclick = () => {
    closeFloatingCards();
    $('trade-area-modal').style.display = 'flex';
    const polyList = features.filter(f => ['polygon','polygon3d','rectangle','circle'].includes(f.kind));
    $('tradePolygonSelect').innerHTML = '<option value="">-- Choose --</option>' + polyList.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
};
$('closeTradeAreaBtn').onclick = () => { $('trade-area-modal').style.display = 'none'; };

async function robustOverpassFetch(query, timeout = 90) {
    const endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.openstreetmap.fr/api/interpreter"
    ];
    for (const endpoint of endpoints) {
        let retries = 5;
        let delay = 1000;
        while (retries > 0) {
            try {
                const controller = new AbortController();
                const id = setTimeout(() => controller.abort(), timeout * 1000);
                const url = `${endpoint}?data=${encodeURIComponent(query)}`;
                const res = await fetch(url, { signal: controller.signal });
                clearTimeout(id);
                if (res.status === 429 || res.status === 503 || res.status === 504) {
                    throw new Error(`HTTP ${res.status}`);
                }
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();
                if (!data || !data.elements) throw new Error("Malformed JSON");
                return data;
            } catch (err) {
                retries--;
                if (retries === 0) break;
                await new Promise(r => setTimeout(r, delay + Math.random() * 500));
                delay *= 2;
            }
        }
    }
    return null;
}

$('btnScanTradeArea').onclick = async () => {
    const polyId = parseInt($('tradePolygonSelect').value, 10);
    const targetPoly = features.find(f => f.id === polyId);
    if (!targetPoly) {
        hint('Please select a target polygon first.');
        return;
    }
    
    let selectedTags = [];
    document.querySelectorAll('.poi-cat-check:checked').forEach(cb => {
        selectedTags.push(cb.dataset.tag);
    });
    
    const customSearch = $('customPoiSearchInput').value.trim();
    if (customSearch) {
        if (customSearch.includes('=')) selectedTags.push(`"${customSearch.split('=')[0]}"="${customSearch.split('=')[1]}"`);
        else selectedTags.push(`"amenity"~"${customSearch}",i`);
    }

    if (!selectedTags.length) {
        hint('Please select at least one category or enter a custom POI tag.');
        return;
    }
    const bnd = calcBounds(targetPoly);
    const bbox = `${bnd[0][1]},${bnd[0][0]},${bnd[1][1]},${bnd[1][0]}`;
    let queryParts = '';
    selectedTags.forEach(rawTag => {
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
    hint('Scanning POIs with robust fetch…');
    $('tradeResults').innerHTML = '<div style="color:#d9b451;">Querying spatial features…</div>';
    if (!customGroups["Trade Area Scan"]) customGroups["Trade Area Scan"] = { collapsed: false, ids: [] };
    const data = await robustOverpassFetch(overpassQuery, 90);
    if (!data) {
        $('tradeResults').innerHTML = '<div style="color:#ff7b72;">Overpass API endpoints failed.</div>';
        hint('Query failed.');
        return;
    }
    const results = data.elements || [];
    const polyCoords = targetPoly.geometry.coordinates[0];
    const filtered = results.filter(el => {
        const lat = el.lat || (el.center && el.center.lat);
        const lon = el.lon || (el.center && el.center.lon);
        return lat && lon && pointInPolygon([lon, lat], polyCoords);
    });
    if (!filtered.length) {
        $('tradeResults').innerHTML = '<div style="color:#8b949e;">No matching POIs inside this area.</div>';
        hint('Scan complete: 0 POIs.');
        return;
    }
    const counts = {};
    filtered.forEach(el => {
        const poiName = (el.tags && (el.tags.name || el.tags.amenity || el.tags.shop || el.tags.building)) || 'POI';
        counts[poiName] = (counts[poiName] || 0) + 1;
        const lat = el.lat || (el.center && el.center.lat);
        const lon = el.lon || (el.center && el.center.lon);
        addFeatureRecord('marker', { type: 'Point', coordinates: [lon, lat] }, {
            shape: 'pin',
            color: '#1e40af',
            iconSize: 0.85,
            iconKey: getIconKey('pin', '#1e40af'),
            osmTags: el.tags || { name: poiName, type: 'custom' }
        }, "Trade Area Scan", poiName);
    });
    let html = `<div style="font-weight:700; color:#f0f6fc; margin-bottom:4px;">Grouped ${filtered.length} POIs:</div>`;
    for (const k in counts) {
        html += `<div class="poi-badge"><span>${k}</span> <span style="font-weight:700; color:#38bdf8;">${counts[k]}</span></div>`;
    }
    $('tradeResults').innerHTML = html;
    hint(`Added ${filtered.length} POIs to "Trade Area Scan"!`);
};

$('customQueryToggle').onclick = () => {
    const body = $('customQueryBody');
    const toggleIcon = $('customQueryToggle').querySelector('span:last-child');
    if (body.style.display === 'none') {
        body.style.display = 'block';
        toggleIcon.textContent = '▾';
    } else {
        body.style.display = 'none';
        toggleIcon.textContent = '▸';
    }
};

$('btnRunOverpass').onclick = async () => {
    const ql = $('overpassQueryInput').value.trim();
    if (!ql) { hint('Please enter an Overpass QL query'); return; }
    const resultType = $('overpassResultType').value;
    hint('Running custom Overpass query…');
    const data = await robustOverpassFetch(ql, 90);
    if (!data) { hint('Query failed.'); return; }
    const elements = data.elements || [];
    if (!elements.length) { hint('Query returned no results'); return; }
    elements.forEach(el => {
        if (el.type === 'node') {
            addFeatureRecord('marker', { type: 'Point', coordinates: [el.lon, el.lat] }, {
                shape: 'pin',
                color: '#1e40af',
                iconSize: 0.9,
                iconKey: getIconKey('pin', '#1e40af'),
                osmTags: el.tags || {}
            });
        } else if (el.type === 'way' && el.geometry) {
            if (resultType === 'marker' && el.center) {
                addFeatureRecord('marker', { type: 'Point', coordinates: [el.center.lon, el.center.lat] }, {
                    shape: 'pin',
                    color: '#1e40af',
                    iconSize: 0.9,
                    iconKey: getIconKey('pin', '#1e40af'),
                    osmTags: el.tags || {}
                });
            } else if (resultType === 'polygon') {
                const geom = el.geometry;
                if (geom.type === 'Polygon') addFeatureRecord('polygon', geom, {});
                else if (geom.type === 'LineString') addFeatureRecord('polyline', geom, {});
            }
        }
    });
    hint(`Added ${elements.length} features from query`);
};

let boundaryResults = [];
const boundaryInput = $('boundarySearchInput');
const boundaryList = $('boundaryAutocompleteList');
boundaryInput.addEventListener('input', debounce(async () => {
    const q = boundaryInput.value.trim();
    if (q.length < 3) { boundaryList.style.display = 'none'; return; }
    const url = `https://nominatim.openstreetmap.org/search?format=json&polygon_geojson=1&limit=5&q=${encodeURIComponent(q)}`;
    try {
        const res = await fetch(url);
        const data = await res.json();
        boundaryResults = data;
        renderBoundaryAutocomplete(data);
    } catch(e) {}
}, 400));

function renderBoundaryAutocomplete(results) {
    if (!results || results.length === 0) {
        boundaryList.style.display = 'none';
        return;
    }
    boundaryList.innerHTML = results.map((r, idx) => `
        <div class="autocomplete-item" data-index="${idx}">
            <div style="font-weight:600;">${r.display_name}</div>
            <div style="font-size:10px; color:#8b949e;">${r.type}</div>
        </div>
    `).join('');
    boundaryList.style.display = 'block';
    boundaryList.querySelectorAll('.autocomplete-item').forEach(item => {
        item.onclick = () => {
            const idx = parseInt(item.dataset.index, 10);
            const selected = boundaryResults[idx];
            boundaryInput.value = selected.display_name;
            boundaryList.style.display = 'none';
            highlightBoundary(selected);
        };
    });
}

function highlightBoundary(result) {
    if (!result.geojson) return;
    const geom = result.geojson;
    addFeatureRecord('polygon', geom, {
        borderColor: '#ff1e1e',
        borderOpacity: 1.0,
        width: 3,
        fillColor: '#ff1e1e',
        fillOpacity: 0.15,
        showLabel: true
    }, null, `${result.display_name} Boundary`);
    if (result.boundingbox) {
        map.fitBounds([
            [parseFloat(result.boundingbox[2]), parseFloat(result.boundingbox[0])],
            [parseFloat(result.boundingbox[3]), parseFloat(result.boundingbox[1])]
        ], { padding: 60 });
    }
    hint(`${result.display_name} boundary added!`);
}

document.addEventListener('click', (e) => {
    if (!e.target.closest('.bound-select-row')) {
        boundaryList.style.display = 'none';
    }
    if (!e.target.closest('#map-context-menu')) {
        $('map-context-menu').style.display = 'none';
    }
});

// ----------------- Right-Click Context Menu (Bring Front / Send Back) -----------------
map.on('contextmenu', e => {
    try {
        ctxLngLat = e.lngLat;
        let fs = [];
        try {
            fs = map.queryRenderedFeatures(e.point, {
                layers: ['draw-fill', 'draw-3d-extrusion', 'draw-line', 'draw-outline', 'draw-marker', 'draw-text']
            });
        } catch (queryErr) {
            // Ignore query errors – no feature will be selected
        }
        ctxFeatureId = (fs.length && fs[0].properties && fs[0].properties.id != null)
            ? parseInt(fs[0].properties.id, 10)
            : null;

        const menu = document.getElementById('map-context-menu');
        if (!menu) return;

        // Update coordinates label
        const coordLabel = document.getElementById('ctx-coords-label');
        if (coordLabel) {
            coordLabel.textContent = `${e.lngLat.lat.toFixed(6)}, ${e.lngLat.lng.toFixed(6)}`;
        }

        // Show/hide feature-specific items
        const hasFeature = ctxFeatureId !== null;
        const items = ['ctx-edit', 'ctx-bring-front', 'ctx-send-back', 'ctx-datatable', 'ctx-delete'];
        const divider = document.getElementById('ctx-divider-feat');
        items.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = hasFeature ? 'flex' : 'none';
        });
        if (divider) divider.style.display = hasFeature ? 'block' : 'none';

        // Position the menu within viewport
        const maxX = window.innerWidth - 220;
        const maxY = window.innerHeight - 240;
        menu.style.left = Math.min(e.point.x, maxX) + 'px';
        menu.style.top = Math.min(e.point.y, maxY) + 'px';
        menu.style.display = 'block';
    } catch (err) {
        // Fallback: still try to show the menu with basic info
        console.warn('Context menu error:', err);
        const menu = document.getElementById('map-context-menu');
        if (menu) {
            const coordLabel = document.getElementById('ctx-coords-label');
            if (coordLabel) coordLabel.textContent = `${e.lngLat.lat.toFixed(6)}, ${e.lngLat.lng.toFixed(6)}`;
            menu.style.display = 'block';
        }
    }
});

map.on('movestart', () => { $('map-context-menu').style.display = 'none'; });

$('ctx-edit').onclick = (e) => {
    e.stopPropagation();
    if (ctxFeatureId) {
        editMode = true;
        selectedId = ctxFeatureId;
        openShapeEditor(ctxFeatureId);
        syncVertexHandles();
        hint('Edit Mode active: Drag, edit vertices, or rotate via handle');
    }
    $('map-context-menu').style.display = 'none';
};

$('ctx-bring-front').onclick = (e) => {
    e.stopPropagation();
    if (ctxFeatureId) {
        const idx = features.findIndex(x => x.id === ctxFeatureId);
        if (idx !== -1 && idx < features.length - 1) {
            const [item] = features.splice(idx, 1);
            features.push(item);
            syncDraw();
            renderMyLayers();
            markDirty();
            hint(`"${item.name}" brought to front`);
        }
    }
    $('map-context-menu').style.display = 'none';
};

$('ctx-send-back').onclick = (e) => {
    e.stopPropagation();
    if (ctxFeatureId) {
        const idx = features.findIndex(x => x.id === ctxFeatureId);
        if (idx > 0) {
            const [item] = features.splice(idx, 1);
            features.unshift(item);
            syncDraw();
            renderMyLayers();
            markDirty();
            hint(`"${item.name}" sent to back`);
        }
    }
    $('map-context-menu').style.display = 'none';
};

$('ctx-datatable').onclick = (e) => {
    e.stopPropagation();
    if (ctxFeatureId) openAttributeTable(ctxFeatureId);
    $('map-context-menu').style.display = 'none';
};

$('ctx-delete').onclick = (e) => {
    e.stopPropagation();
    if (ctxFeatureId) {
        features = features.filter(x => x.id !== ctxFeatureId);
        for (const g in customGroups) customGroups[g].ids = customGroups[g].ids.filter(xId => xId !== ctxFeatureId);
        selectedLayerIds.delete(ctxFeatureId);
        if (selectedId === ctxFeatureId) selectedId = null;
        syncDraw(); renderMyLayers(); markDirty();
    }
    $('map-context-menu').style.display = 'none';
};

$('ctx-copy').onclick = (e) => {
    e.stopPropagation();
    if (ctxLngLat) {
        const txt = `${ctxLngLat.lat.toFixed(6)}, ${ctxLngLat.lng.toFixed(6)}`;
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(txt).then(() => hint('Copied: ' + txt)).catch(() => hint(txt));
        } else {
            hint(txt);
        }
    }
    $('map-context-menu').style.display = 'none';
};

$('ctx-gmaps').onclick = (e) => {
    e.stopPropagation();
    if (ctxLngLat) {
        window.open(`https://www.google.com/maps?q=${ctxLngLat.lat},${ctxLngLat.lng}`, '_blank');
    }
    $('map-context-menu').style.display = 'none';
};

$('ctx-streetview').onclick = (e) => {
    e.stopPropagation();
    if (ctxLngLat) {
        window.open(`https://www.google.com/maps/@${ctxLngLat.lat},${ctxLngLat.lng},3a,75y,90t/data=!3m6!1e1!3m4!1s!2e0!7i13312!8i6656`, '_blank');
    }
    $('map-context-menu').style.display = 'none';
};

// ----------------- Search Place -----------------
const searchInput = $('searchInput');
const searchResultsList = $('searchResultsList');
let searchResults = [];
searchInput.addEventListener('input', debounce(async () => {
    const q = searchInput.value.trim();
    if (q.length < 2) { searchResultsList.innerHTML = ''; return; }
    const url = `https://nominatim.openstreetmap.org/search?format=json&limit=5&q=${encodeURIComponent(q)}`;
    try {
        const res = await fetch(url);
        const data = await res.json();
        searchResults = data;
        renderSearchResults(data);
    } catch(e) {}
}, 400));

function renderSearchResults(results) {
    if (!results || results.length === 0) {
        searchResultsList.innerHTML = '';
        return;
    }
    searchResultsList.innerHTML = results.map((r, idx) => `
        <div class="search-result-item" data-index="${idx}">
            <svg class="search-result-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"></path><circle cx="12" cy="10" r="2.5"></circle></svg>
            <div>
                <div style="font-weight:600;">${r.name || r.display_name}</div>
                <div style="font-size:11px; color:#5f6368;">${r.display_name}</div>
            </div>
        </div>
    `).join('');
    searchResultsList.querySelectorAll('.search-result-item').forEach(item => {
        item.onclick = () => {
            const idx = parseInt(item.dataset.index, 10);
            const selected = searchResults[idx];
            searchInput.value = selected.display_name;
            searchResultsList.innerHTML = '';
            
            const coords = [parseFloat(selected.lon), parseFloat(selected.lat)];
            pulseFeature({geometry: {type: 'Point', coordinates: coords}});
            
            const el = document.createElement('div');
            el.className = 'temp-search-marker';
            el.style.width = '20px';
            el.style.height = '20px';
            el.style.backgroundColor = '#38bdf8';
            el.style.borderRadius = '50%';
            el.style.border = '2px solid #ffffff';
            el.style.boxShadow = '0 0 12px rgba(56, 189, 248, 0.9)';
            el.style.transition = 'opacity 1s ease';

            const tempMarker = new maplibregl.Marker({ element: el })
                .setLngLat(coords)
                .addTo(map);

            map.flyTo({ center: coords, zoom: 15, duration: 1500 });
            
            setTimeout(() => {
                el.style.opacity = '0';
                setTimeout(() => tempMarker.remove(), 1000);
            }, 4000);
            
            hint('');
            $('popup-search').classList.remove('open');
        };
    });
}

$('btn-search').onclick = () => {
    const p = $('popup-search');
    const willOpen = !p.classList.contains('open');
    closeFloatingCards();
    if (willOpen) { p.classList.add('open'); searchInput.focus(); }
};

// ----------------- Dual-Mode Routing Engine Logic -----------------
$('btnRouteModeClick').onclick = () => {
    $('btnRouteModeClick').classList.add('active');
    $('btnRouteModeAddress').classList.remove('active');
    $('route-panel-click-mode').style.display = 'flex';
    $('route-panel-address-mode').style.display = 'none';
};

$('btnRouteModeAddress').onclick = () => {
    $('btnRouteModeAddress').classList.add('active');
    $('btnRouteModeClick').classList.remove('active');
    $('route-panel-address-mode').style.display = 'flex';
    $('route-panel-click-mode').style.display = 'none';
    resetActiveTools();
};

function renderAddressStopInputs() {
    const container = $('routeStopsList');
    container.innerHTML = addressStops.map((stopVal, idx) => `
        <div class="route-stop-row" draggable="true" data-stop-idx="${idx}">
            <div class="route-stop-handle" title="Drag to reorder">
                <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="16" y2="6"></line><line x1="8" y1="12" x2="16" y2="12"></line><line x1="8" y1="18" x2="16" y2="18"></line></svg>
            </div>
            <input class="route-stop-input" data-stop-idx="${idx}" placeholder="${idx === 0 ? 'From origin address...' : (idx === addressStops.length - 1 ? 'To destination address...' : `Stop #${idx}...`)}" value="${stopVal}"/>
            ${addressStops.length > 2 ? `<button class="card-btn" onclick="removeAddressStop(${idx})" title="Remove stop" style="color:#ff7b72;">✕</button>` : ''}
        </div>
    `).join('');

    container.querySelectorAll('.route-stop-input').forEach(inp => {
        inp.oninput = e => {
            const i = parseInt(e.target.dataset.stopIdx, 10);
            addressStops[i] = e.target.value;
        };
    });

    container.querySelectorAll('.route-stop-row').forEach(row => {
        row.addEventListener('dragstart', e => {
            e.dataTransfer.setData('text/plain', row.dataset.stopIdx);
            e.dataTransfer.effectAllowed = 'move';
        });
        row.addEventListener('dragover', e => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        });
        row.addEventListener('drop', e => {
            e.preventDefault();
            const fromIdx = parseInt(e.dataTransfer.getData('text/plain'), 10);
            const toIdx = parseInt(row.dataset.stopIdx, 10);
            if (fromIdx !== toIdx) {
                const [moved] = addressStops.splice(fromIdx, 1);
                addressStops.splice(toIdx, 0, moved);
                renderAddressStopInputs();
            }
        });
    });
}

window.removeAddressStop = function(idx) {
    if (addressStops.length > 2) {
        addressStops.splice(idx, 1);
        renderAddressStopInputs();
    }
};

$('btnAddRouteStop').onclick = () => {
    addressStops.splice(addressStops.length - 1, 0, '');
    renderAddressStopInputs();
};

async function geocodeAddress(query) {
    const url = `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(query)}`;
    const res = await fetch(url);
    const data = await res.json();
    if (data && data[0]) {
        return [parseFloat(data[0].lon), parseFloat(data[0].lat)];
    }
    return null;
}

$('btnCalculateAddressRoute').onclick = async () => {
    const validStops = addressStops.map(s => s.trim()).filter(Boolean);
    if (validStops.length < 2) {
        hint('Please enter at least From and To addresses');
        return;
    }
    hint('Geocoding addresses…');
    const waypoints = [];
    for (let i = 0; i < validStops.length; i++) {
        try {
            const coord = await geocodeAddress(validStops[i]);
            if (!coord) throw new Error(`Could not find "${validStops[i]}"`);
            waypoints.push(coord);
        } catch(err) {
            hint(err.message);
            return;
        }
    }
    const profile = $('rProfileAddr').value || 'driving';
    fetchMultiPointRoute(waypoints, null, profile);
    $('popup-route-settings').classList.remove('open');
};

document.querySelectorAll('#popup-route-settings .swatch').forEach(sw => {
    sw.onclick = () => {
        currentRouteColor = sw.dataset.rcol;
        hint(`Route color set to ${currentRouteColor}`);
    };
});
$('rProfile').onchange = e => { currentRouteMode = e.target.value; };
$('btnStartRouteDraw').onclick = () => {
    $('popup-route-settings').classList.remove('open');
    hint('Click waypoints along roads · Double-click or click endpoint to finalize');
};
$('closeRouteSettingsBtn').onclick = () => { $('popup-route-settings').classList.remove('open'); resetActiveTools(); };

// Tool Handlers
document.querySelectorAll('.tool').forEach(btn => {
    btn.onclick = () => {
        const t = btn.dataset.tool;
        if (activeTool === t) {
            resetActiveTools();
            closeFloatingCards();
        } else {
            document.querySelectorAll('.tool').forEach(b => b.classList.remove('primary-active'));
            editMode = false;
            syncVertexHandles();
            closeFloatingCards();
            activeTool = t;
            btn.classList.add('primary-active');
            draft = [];
            renderDraft();
            map.getCanvas().style.cursor = 'crosshair';
            map.doubleClickZoom.disable();
            if (t === 'marker') $('popup-marker-settings').classList.add('open');
            if (t === 'textbox') $('popup-text-settings').classList.add('open');
            if (t === 'route') {
                $('popup-route-settings').classList.add('open');
            }
            if (t === 'polyline') hint('Click points · Double-click or click last point to finish');
            if (t === 'polygon') hint('Click vertices · Double-click or click origin to close');
            if (t === 'polygon3d') hint('Draw 3D Polygon base · Click origin to close and extrude');
            if (t === 'rectangle') hint('Click corner 1, then click opposite corner');
            if (t === 'circle') hint('Click center, then outer edge');
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
        if (f.kind === 'circle' && f.props.centerCoord) {
            f.props.centerCoord = [f.props.centerCoord[0] + dx, f.props.centerCoord[1] + dy];
        }
        if (f.props.waypoints) {
            f.props.waypoints = f.props.waypoints.map(pt => [pt[0] + dx, pt[1] + dy]);
        }
        syncDraw();
    }
    
    if (isDraggingRotation && rotatingPolyId != null) {
        const f = features.find(x => x.id === rotatingPolyId);
        if (f && rotCenter) {
            const currentAngle = Math.atan2(cursorLL[1] - rotCenter[1], cursorLL[0] - rotCenter[0]);
            const deltaAngle = currentAngle - rotStartAngle;
            rotateGeometry(f, deltaAngle, rotCenter);
            rotStartAngle = currentAngle;
            syncDraw();
        }
    }

    if (isDraggingVertex && draggedPolyId != null) {
        const f = features.find(x => x.id === draggedPolyId);
        if (f) {
            if (isRadiusHandle && f.kind === 'circle') {
                const c = f.props.centerCoord;
                const newRadius = haversineDist(c, cursorLL);
                f.props.radiusMeters = newRadius;
                f.geometry.coordinates = circleCoords(c, cursorLL).coords;
                const distText = newRadius > 1000 ? `${(newRadius/1000).toFixed(2)} km` : `${Math.round(newRadius)} m`;
                hint(`Circle Radius: ${distText}`);
            } else if (['polygon','polygon3d','rectangle'].includes(f.kind) && f.geometry.coordinates[0]) {
                const coords = f.geometry.coordinates[0];
                coords[draggedVertexIdx] = cursorLL;
                if (draggedVertexIdx === 0) coords[coords.length - 1] = cursorLL;
            } else if (f.kind === 'polyline' && f.geometry.coordinates) {
                f.geometry.coordinates[draggedVertexIdx] = cursorLL;
            } else if (f.kind === 'route' && f.props.waypoints) {
                f.props.waypoints[draggedVertexIdx] = cursorLL;
                clearTimeout(rerouteTimeout);
                rerouteTimeout = setTimeout(() => {
                    fetchMultiPointRoute(f.props.waypoints, f.id, f.props.routeMode);
                }, 300);
            }
            syncDraw();
        }
    }
});

map.on('click', e => {
    if (!activeTool) {
        if (!editMode) {
            const fs = map.queryRenderedFeatures(e.point, { layers: ['draw-fill','draw-3d-extrusion','draw-line','draw-outline','draw-marker','draw-text'] });
            if (fs.length && fs[0].properties.id != null) {
                const id = parseInt(fs[0].properties.id, 10);
                const f = features.find(x => x.id === id);
                if (f) {
                    showFeaturePopup(f, [e.lngLat.lng, e.lngLat.lat]);
                    return;
                }
            }
        }
    }
    if (!activeTool) return;
    const ll = [e.lngLat.lng, e.lngLat.lat];
    if (activeTool === 'marker') {
        let iconKey = customMarkerImageKey ? customMarkerImageKey : getIconKey(markerShape, markerColor);
        const feat = addFeatureRecord('marker', { type: 'Point', coordinates: ll }, {
            shape: markerShape,
            color: markerColor,
            iconSize: markerIconSize,
            markerSizeMode: markerSizeMode,
            iconKey: iconKey
        });
        resetActiveTools();
        closeFloatingCards();
        showFeaturePopup(feat, ll);
    } else if (activeTool === 'textbox') {
        const tColor = $('tColorCtrl').dataset.val || '#d9b451';
        const feat = addFeatureRecord('text', { type: 'Point', coordinates: ll }, {
            text: $('tContent').value || 'Label',
            fontSize: parseInt($('tSize').value, 10),
            color: tColor,
            opacity: parseFloat($('tOp').value)
        });
        resetActiveTools();
        closeFloatingCards();
        showFeaturePopup(feat, ll);
    } else if (activeTool === 'polyline') {
        if (draft.length >= 2) {
            const pScreen = map.project(ll);
            const lastPtScreen = map.project(draft[draft.length - 1]);
            if (Math.hypot(pScreen.x - lastPtScreen.x, pScreen.y - lastPtScreen.y) < 18) {
                const feat = addFeatureRecord('polyline', { type: 'LineString', coordinates: draft });
                resetActiveTools();
                showFeaturePopup(feat, ll);
                return;
            }
        }
        draft.push(ll);
    } else if (activeTool === 'polygon' || activeTool === 'polygon3d') {
        const is3D = activeTool === 'polygon3d';
        if (draft.length >= 3) {
            const pScreen = map.project(ll);
            for (const pt of draft) {
                const vScreen = map.project(pt);
                if (Math.hypot(pScreen.x - vScreen.x, pScreen.y - vScreen.y) < 18) {
                    const feat = addFeatureRecord(is3D ? 'polygon3d' : 'polygon', { type: 'Polygon', coordinates: [[...draft, draft[0]]] }, {
                        extrusionHeight: is3D ? 35 : 0
                    });
                    resetActiveTools();
                    showFeaturePopup(feat, ll);
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
            showFeaturePopup(feat, ll);
        }
    } else if (activeTool === 'circle') {
        draft.push(ll);
        if (draft.length === 2) {
            const { coords, r } = circleCoords(draft[0], draft[1]);
            const feat = addFeatureRecord('circle', { type: 'Polygon', coordinates: coords }, { centerCoord: draft[0], radiusMeters: r });
            resetActiveTools();
            showFeaturePopup(feat, ll);
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

map.on('dblclick', e => {
    if (activeTool === 'route' && $('rAutoFinish') && $('rAutoFinish').checked && draft.length >= 2) {
        e.preventDefault();
        fetchMultiPointRoute(draft);
        resetActiveTools();
        return;
    }
    if (editMode) {
        const fs = map.queryRenderedFeatures(e.point, { layers: ['draw-line'] });
        if (fs.length && fs[0].properties.id != null) {
            const f = features.find(x => x.id === parseInt(fs[0].properties.id, 10));
            if (f && f.kind === 'route' && f.props.waypoints) {
                const ll = [e.lngLat.lng, e.lngLat.lat];
                let bestIdx = -1, bestDist = 1e9;
                const pts = f.props.waypoints;
                for (let i = 0; i < pts.length - 1; i++) {
                    const d = haversineDist(pts[i], ll) + haversineDist(ll, pts[i+1]);
                    if (d < bestDist) { bestDist = d; bestIdx = i + 1; }
                }
                if (bestIdx !== -1) {
                    pts.splice(bestIdx, 0, ll);
                    fetchMultiPointRoute(pts, f.id, f.props.routeMode);
                    hint('Waypoint inserted');
                }
            }
        }
    }
});

// Edit Mode Dragging
map.on('mousedown', e => {
    if (editMode) {
        const vHits = map.queryRenderedFeatures(e.point, { layers: ['vertex-points'] });
        if (vHits.length && vHits[0].properties.polyId != null) {
            const prop = vHits[0].properties;
            if (prop.isRotHandle) {
                isDraggingRotation = true;
                rotatingPolyId = parseInt(prop.polyId, 10);
                const f = features.find(x => x.id === rotatingPolyId);
                const b = calcBounds(f);
                rotCenter = [(b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2];
                rotStartAngle = Math.atan2(cursorLL[1] - rotCenter[1], cursorLL[0] - rotCenter[0]);
                map.dragPan.disable();
                return;
            }
            isDraggingVertex = true;
            draggedPolyId = parseInt(prop.polyId, 10);
            draggedVertexIdx = prop.vIdx != null ? parseInt(prop.vIdx, 10) : -1;
            isRadiusHandle = !!prop.isRadiusHandle;
            map.dragPan.disable();
            return;
        }
        const fs = map.queryRenderedFeatures(e.point, { layers: ['draw-fill','draw-3d-extrusion','draw-line','draw-outline','draw-marker','draw-text'] });
        if (fs.length && fs[0].properties.id != null) {
            isDragging = true;
            dragFeatureId = parseInt(fs[0].properties.id, 10);
            dragStartCoord = [e.lngLat.lng, e.lngLat.lat];
            const f = features.find(x => x.id === dragFeatureId);
            if (f) dragOriginalCoords = JSON.parse(JSON.stringify(f.geometry.coordinates));
            map.dragPan.disable();
        }
    }
});

map.on('mouseup', () => {
    if (isDragging) {
        isDragging = false;
        dragFeatureId = null;
        map.dragPan.enable();
        markDirty();
    }
    if (isDraggingVertex) {
        if (draggedPolyId != null) {
            const f = features.find(x => x.id === draggedPolyId);
            if (f && f.kind === 'route' && f.props.waypoints) {
                fetchMultiPointRoute(f.props.waypoints, f.id, f.props.routeMode);
            }
        }
        isDraggingVertex = false;
        draggedPolyId = null;
        draggedVertexIdx = -1;
        isRadiusHandle = false;
        map.dragPan.enable();
        hint('');
        markDirty();
    }
    if (isDraggingRotation) {
        isDraggingRotation = false;
        rotatingPolyId = null;
        map.dragPan.enable();
        markDirty();
    }
});

// Shape Editor Customizer
function openShapeEditor(id) {
    const f = features.find(x => x.id === id);
    if (!f) return;
    selectedId = id;
    closeFloatingCards();
    $('editShapeTitle').textContent = `Edit ${f.name}`;
    $('eName').value = f.name;
    
    $('eBorderOp').value = f.props.borderOpacity != null ? f.props.borderOpacity : 0.9;
    $('eWidth').value = f.props.width || 3;
    $('eFillOp').value = f.props.fillOpacity != null ? f.props.fillOpacity : 0.35;
    
    const isPolygon = ['polygon', 'polygon3d', 'rectangle', 'circle'].includes(f.kind);
    $('eFillColorRowContainer').style.display = isPolygon ? 'flex' : 'none';
    $('eFillOpRow').style.display = isPolygon ? 'flex' : 'none';
    
    const is3D = f.kind === 'polygon3d';
    $('e3dExtrusionControls').style.display = is3D ? 'block' : 'none';
    if (is3D) {
        $('eExtrusionHeight').value = f.props.extrusionHeight || 35;
        $('eExtrusionHeightVal').textContent = (f.props.extrusionHeight || 35) + 'm';
        $('eExtrusionBase').value = f.props.extrusionBase || 0;
        $('eExtrusionBaseVal').textContent = (f.props.extrusionBase || 0) + 'm';
    }

    $('eLabelToggleRow').style.display = 'flex';
    $('eLabelPosRow').style.display = 'flex';
    
    $('eShowLabel').checked = !!f.props.showLabel;
    $('eLabelPos').value = f.props.labelPos || 'center';

    const isMarker = f.kind === 'marker';
    $('eMarkerSizeRow').style.display = isMarker ? 'flex' : 'none';
    $('eMarkerSizeModeRow').style.display = isMarker ? 'flex' : 'none';
    if (isMarker) {
        $('eMarkerSize').value = f.props.iconSize || 0.9;
        $('eMarkerSizeMode').value = f.props.markerSizeMode || 'dynamic';
    }
    
    const isText = f.kind === 'text';
    $('eTextRow').style.display = isText ? 'flex' : 'none';
    $('eFontSizeRow').style.display = isText ? 'flex' : 'none';
    if (isText) {
        $('eTextVal').value = f.props.text || '';
        $('eFontSize').value = f.props.fontSize || 16;
    }
    
    const isRoute = f.kind === 'route';
    $('routeEditorControls').style.display = isRoute ? 'block' : 'none';
    if (isRoute) {
        $('eRouteMode').value = f.props.routeMode || 'driving';
        $('eRouteStats').textContent = f.props.description || '-';
        renderWaypointEditor(f);
    }

    $('popup-shape-editor').classList.add('open');
    syncVertexHandles();
}

function renderWaypointEditor(f) {
    const list = $('eWaypointList');
    if (!f.props.waypoints || !f.props.waypoints.length) {
        list.innerHTML = '<span style="font-size:10px; color:#768390;">No intermediate waypoints.</span>';
        return;
    }
    list.innerHTML = f.props.waypoints.map((pt, i) => `
        <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.05); padding:2px 6px; border-radius:4px; font-size:10px;">
            <span>Pt ${i+1}: ${pt[1].toFixed(4)}, ${pt[0].toFixed(4)}</span>
            ${f.props.waypoints.length > 2 ? `<button class="card-btn" onclick="removeWaypoint(${f.id}, ${i})" title="Remove waypoint" style="color:#ff7b72;">✕</button>` : ''}
        </div>
    `).join('');
}

window.removeWaypoint = function(featId, idx) {
    const f = features.find(x => x.id === featId);
    if (f && f.props.waypoints && f.props.waypoints.length > 2) {
        f.props.waypoints.splice(idx, 1);
        fetchMultiPointRoute(f.props.waypoints, f.id, f.props.routeMode);
    }
};

$('eName').oninput = e => {
    const f = features.find(x => x.id === selectedId);
    if (f) {
        f.name = e.target.value;
        if (!f.props.attributes) f.props.attributes = {};
        f.props.attributes.name = e.target.value;
        syncDraw(); renderMyLayers(); markDirty();
    }
};
$('eBorderOp').oninput = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.borderOpacity = parseFloat(e.target.value); syncDraw(); markDirty(); } };
$('eWidth').oninput = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.width = parseFloat(e.target.value); syncDraw(); markDirty(); } };
$('eFillOp').oninput = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.fillOpacity = parseFloat(e.target.value); syncDraw(); markDirty(); } };
$('eExtrusionHeight').oninput = e => {
    const f = features.find(x => x.id === selectedId);
    if (f) {
        const val = parseFloat(e.target.value);
        f.props.extrusionHeight = val;
        $('eExtrusionHeightVal').textContent = val + 'm';
        syncDraw(); markDirty();
    }
};
$('eExtrusionBase').oninput = e => {
    const f = features.find(x => x.id === selectedId);
    if (f) {
        const val = parseFloat(e.target.value);
        f.props.extrusionBase = val;
        $('eExtrusionBaseVal').textContent = val + 'm';
        syncDraw(); markDirty();
    }
};
$('eShowLabel').onchange = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.showLabel = e.target.checked; syncDraw(); renderMyLayers(); markDirty(); } };
$('eLabelPos').onchange = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.labelPos = e.target.value; syncDraw(); markDirty(); } };
$('eMarkerSize').oninput = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.iconSize = parseFloat(e.target.value); syncDraw(); markDirty(); } };
$('eMarkerSizeMode').onchange = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.markerSizeMode = e.target.value; syncDraw(); markDirty(); } };
$('eTextVal').oninput = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.text = e.target.value; syncDraw(); renderMyLayers(); markDirty(); } };
$('eFontSize').oninput = e => { const f = features.find(x => x.id === selectedId); if (f) { f.props.fontSize = parseInt(e.target.value, 10); syncDraw(); markDirty(); } };

$('eRouteMode').onchange = e => {
    const f = features.find(x => x.id === selectedId);
    if (f && f.kind === 'route' && f.props.waypoints) {
        f.props.routeMode = e.target.value;
        fetchMultiPointRoute(f.props.waypoints, f.id, e.target.value);
    }
};

$('eRecalcRoute').onclick = () => {
    const f = features.find(x => x.id === selectedId);
    if (f && f.kind === 'route' && f.props.waypoints) {
        fetchMultiPointRoute(f.props.waypoints, f.id, f.props.routeMode);
    }
};

$('eDeleteBtn').onclick = () => {
    features = features.filter(x => x.id !== selectedId);
    for (const g in customGroups) { customGroups[g].ids = customGroups[g].ids.filter(id => id !== selectedId); }
    selectedId = null;
    editMode = false;
    syncDraw();
    renderMyLayers();
    $('popup-shape-editor').classList.remove('open');
    markDirty();
};
$('eDoneBtn').onclick = () => { $('popup-shape-editor').classList.remove('open'); selectedId = null; editMode = false; syncVertexHandles(); };
$('closeEditorBtn').onclick = () => { $('popup-shape-editor').classList.remove('open'); selectedId = null; editMode = false; syncVertexHandles(); };

// My Layers Panel
$('btnAddCustomGroup').onclick = () => {
    const gName = prompt("Enter new Group name:", `Group ${Object.keys(customGroups).length + 1}`);
    if (gName && gName.trim() && !customGroups[gName]) {
        customGroups[gName.trim()] = { collapsed: false, ids: [] };
        renderMyLayers();
        markDirty();
    }
};

$('btnSelectAllGlobal').onclick = () => {
    if (selectedLayerIds.size === features.length && features.length > 0) {
        selectedLayerIds.clear();
    } else {
        features.forEach(f => selectedLayerIds.add(f.id));
    }
    renderMyLayers();
};

$('btnHideSelected').onclick = () => {
    if (selectedLayerIds.size === 0) {
        hint('Select at least one layer first');
        return;
    }
    const allHidden = Array.from(selectedLayerIds).every(id => {
        const f = features.find(x => x.id === id);
        return f && f.props.visible === 0;
    });
    const newVis = allHidden ? 1 : 0;
    selectedLayerIds.forEach(id => {
        const f = features.find(x => x.id === id);
        if (f) f.props.visible = newVis;
    });
    syncDraw();
    renderMyLayers();
    markDirty();
    hint(allHidden ? 'Layers shown' : 'Layers hidden');
};

function renderLayerCardHtml(f) {
    let subInfo = f.kind;
    if (f.kind === 'polygon3d') {
        subInfo = `3D Extrusion (${f.props.extrusionHeight || 35}m)`;
    } else if (f.kind === 'circle' && f.props.radiusMeters) {
        subInfo = `Radius: ${f.props.radiusMeters > 1000 ? (f.props.radiusMeters/1000).toFixed(2)+' km' : Math.round(f.props.radiusMeters)+' m'}`;
    } else if (f.kind === 'route' && f.props.description) {
        subInfo = f.props.description;
    }
    const isSelected = selectedLayerIds.has(f.id);
    const posOptions = ['center','top','bottom','left','right']
        .map(p => `<option value="${p}" ${(f.props.labelPos || 'center') === p ? 'selected' : ''}>${p}</option>`)
        .join('');
    return `
        <div class="layer-card" draggable="true" data-id="${f.id}">
            <div class="layer-card-top">
                <input type="checkbox" class="layer-select-check" data-id="${f.id}" ${isSelected ? 'checked' : ''} style="width:14px;height:14px;accent-color:#316dca;cursor:pointer;"/>
                <input class="layer-name-input" data-id="${f.id}" value="${f.name}" title="Click to rename"/>
                <button class="card-btn" data-act="table" data-id="${f.id}" title="View/Edit Attributes">
                    <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>
                </button>
                <button class="card-btn" data-act="eye" data-id="${f.id}" title="Toggle Visibility">
                    <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                </button>
                <button class="card-btn" data-act="zoom" data-id="${f.id}" title="Zoom To">
                    <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                </button>
                <button class="card-btn" data-act="del" data-id="${f.id}" title="Delete" style="color:#ff7b72;">
                    <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; font-size:10px; color:#768390; padding:0 4px; gap:4px;">
                <span>${subInfo}</span>
                <span style="display:flex; align-items:center; gap:4px;">
                    <label style="display:flex; align-items:center; gap:3px; cursor:pointer;">
                        <input type="checkbox" data-act="labelToggle" data-id="${f.id}" ${f.props.showLabel ? 'checked' : ''} style="width:10px;height:10px;accent-color:#316dca;"/> Label
                    </label>
                    <select data-act="labelPos" data-id="${f.id}" title="Label Position" style="font-size:9px; background:rgba(0,0,0,0.4); color:#adbac7; border:1px solid rgba(255,255,255,0.12); border-radius:4px; padding:1px 2px;">
                        ${posOptions}
                    </select>
                </span>
            </div>
        </div>
    `;
}

function renderMyLayers() {
    const container = $('my-layers-list');
    $('layer-badge-count').textContent = features.length;
    const polyList = features.filter(f => ['polygon', 'polygon3d', 'rectangle', 'circle'].includes(f.kind));
    $('tradePolygonSelect').innerHTML = '<option value="">-- Choose --</option>' + polyList.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
    if (!features.length && !Object.keys(customGroups).length) {
        container.innerHTML = '<div style="font-size:12px; color:#768390; padding:6px 0;">No drawings yet. Use the tools to create shapes.</div>';
        return;
    }
    let html = '';
    const groupedIds = new Set();
    for (const gName in customGroups) {
        const grp = customGroups[gName];
        const groupFeats = features.filter(f => grp.ids.includes(f.id));
        grp.ids.forEach(id => groupedIds.add(id));
        html += `
            <div class="group-container" data-group="${gName}">
                <div class="group-header" data-group="${gName}">
                    <div style="display:flex; align-items:center; gap:6px;">
                        <span class="card-btn" data-act="groupToggleCollapse" data-group="${gName}">
                            <svg viewBox="0 0 24 24" width="10" height="10" fill="none" stroke="currentColor" stroke-width="2"><polyline points="${grp.collapsed ? '9 18 15 12 9 6' : '6 9 12 15 18 9'}"></polyline></svg>
                        </span>
                        <input class="group-title-input" data-oldname="${gName}" value="${gName}" title="Click to rename Group"/>
                    </div>
                    <div style="display:flex; align-items:center; gap:2px;">
                        <button class="card-btn" data-act="groupSelectAll" data-group="${gName}" title="Select All in Group">
                            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"></path><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>
                        </button>
                        <button class="card-btn" data-act="groupStyle" data-group="${gName}" title="Style Group">
                            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
                        </button>
                        <button class="card-btn" data-act="groupEye" data-group="${gName}" title="Toggle Group">
                            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                        </button>
                        <button class="card-btn" data-act="groupDel" data-group="${gName}" title="Delete Group" style="color:#ff7b72;">
                            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                        </button>
                    </div>
                </div>
                <div class="group-styling-panel" data-group="${gName}">
                    <div style="font-size:10px; font-weight:700; color:#768390; margin-bottom:6px;">BULK APPLY TO MARKERS IN GROUP</div>
                    <div class="f-row" style="margin-bottom:4px;"> <span style="font-size:11px;">Color</span> <input type="color" class="grp-style-color" value="#003366" style="width:24px; height:24px; border:none; background:transparent;"></div>
                    <div class="f-row" style="margin-bottom:4px;"> <span style="font-size:11px;">Shape</span>
                        <select class="grp-style-shape" style="flex:1; font-size:10px;">
                            <option value="">-- No Change --</option>
                            <option value="pin">Pin</option>
                            <option value="star">Star</option>
                            <option value="circle">Circle</option>
                            <option value="square">Square</option>
                            <option value="flag">Flag</option>
                            <option value="heart">Heart</option>
                            <option value="pinball">Pinball</option>
                        </select>
                    </div>
                    <div class="f-row" style="margin-bottom:4px;"> <span style="font-size:11px;">Size</span> <input type="range" class="grp-style-size" min="0.4" max="2.0" step="0.1" value="0.9" style="flex:1;"></div>
                    <button class="trade-btn grp-style-apply" style="font-size:10px; padding:4px;">Apply Styling</button>
                </div>
                <div class="group-items ${grp.collapsed ? 'hidden' : ''}">
                    ${groupFeats.length ? groupFeats.map(f => renderLayerCardHtml(f)).join('') : '<div style="font-size:10px; color:#768390; padding:4px;">Empty group — drag layers here</div>'}
                </div>
            </div>
        `;
    }
    const looseFeats = features.filter(f => !groupedIds.has(f.id));
    html += '<div id="ungrouped-zone">';
    if (looseFeats.length) {
        html += '<div style="font-size:11px; font-weight:700; color:#adbac7; margin-top:8px; display:flex; justify-content:space-between; align-items:center;"><span>Ungrouped Layers</span> <button class="card-btn" id="btnSelectAllUngrouped" title="Select All Ungrouped"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"></path><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg></button></div>';
        html += looseFeats.slice().reverse().map(f => renderLayerCardHtml(f)).join('');
    }
    html += '</div>';
    container.innerHTML = html;

    const btnSelAllUng = container.querySelector('#btnSelectAllUngrouped');
    if (btnSelAllUng) {
        btnSelAllUng.onclick = () => {
            const allSelected = looseFeats.every(f => selectedLayerIds.has(f.id));
            looseFeats.forEach(f => {
                if (allSelected) selectedLayerIds.delete(f.id);
                else selectedLayerIds.add(f.id);
            });
            renderMyLayers();
        };
    }

    container.querySelectorAll('.group-container').forEach(gc => {
        const gName = gc.dataset.group;
        gc.addEventListener('dragover', e => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            gc.classList.add('drop-hover');
        });
        gc.addEventListener('dragleave', () => {
            gc.classList.remove('drop-hover');
        });
        gc.addEventListener('drop', e => {
            e.preventDefault();
            e.stopPropagation();
            gc.classList.remove('drop-hover');
            const draggedId = parseInt(e.dataTransfer.getData('text/plain'), 10);
            if (isNaN(draggedId)) return;
            for (const g in customGroups) {
                customGroups[g].ids = customGroups[g].ids.filter(id => id !== draggedId);
            }
            if (!customGroups[gName].ids.includes(draggedId)) {
                customGroups[gName].ids.push(draggedId);
            }
            renderMyLayers();
            markDirty();
            hint(`Layer added to "${gName}"`);
        });
    });

    const uz = container.querySelector('#ungrouped-zone');
    if (uz) {
        uz.addEventListener('dragover', e => {
            e.preventDefault();
            uz.classList.add('drop-hover');
        });
        uz.addEventListener('dragleave', () => {
            uz.classList.remove('drop-hover');
        });
        uz.addEventListener('drop', e => {
            e.preventDefault();
            e.stopPropagation();
            uz.classList.remove('drop-hover');
            const draggedId = parseInt(e.dataTransfer.getData('text/plain'), 10);
            if (isNaN(draggedId)) return;
            for (const g in customGroups) {
                customGroups[g].ids = customGroups[g].ids.filter(id => id !== draggedId);
            }
            renderMyLayers();
            markDirty();
            hint('Layer moved to Ungrouped');
        });
    }

    container.querySelectorAll('.layer-card').forEach(card => {
        card.addEventListener('dragstart', e => {
            e.dataTransfer.setData('text/plain', card.dataset.id);
            e.dataTransfer.effectAllowed = 'move';
        });
        card.addEventListener('dragover', e => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        });
        card.addEventListener('drop', e => {
            e.preventDefault();
            e.stopPropagation();
            const draggedId = parseInt(e.dataTransfer.getData('text/plain'), 10);
            const targetId = parseInt(card.dataset.id, 10);
            if (draggedId !== targetId) {
                reorderFeatures(draggedId, targetId);
            }
        });
    });

    container.querySelectorAll('.layer-select-check').forEach(cb => {
        cb.addEventListener('change', e => {
            const id = parseInt(e.target.dataset.id, 10);
            if (e.target.checked) selectedLayerIds.add(id);
            else selectedLayerIds.delete(id);
        });
    });
    
    container.querySelectorAll('[data-act="groupSelectAll"]').forEach(btn => {
        btn.onclick = () => {
            const gName = btn.dataset.group;
            const grp = customGroups[gName];
            if (grp) {
                const allSelected = grp.ids.every(id => selectedLayerIds.has(id));
                grp.ids.forEach(id => {
                    if (allSelected) selectedLayerIds.delete(id);
                    else selectedLayerIds.add(id);
                });
                renderMyLayers();
            }
        };
    });

    container.querySelectorAll('.group-title-input').forEach(inp => {
        inp.onchange = e => {
            const oldN = e.target.dataset.oldname;
            const newN = e.target.value.trim();
            if (newN && newN !== oldN) {
                customGroups[newN] = customGroups[oldN];
                delete customGroups[oldN];
                renderMyLayers();
                markDirty();
            }
        };
    });

    container.querySelectorAll('.layer-name-input').forEach(inp => {
        inp.onchange = e => {
            const id = parseInt(e.target.dataset.id, 10);
            const f = features.find(x => x.id === id);
            if (f) {
                f.name = e.target.value;
                if (!f.props.attributes) f.props.attributes = {};
                f.props.attributes.name = e.target.value;
                syncDraw(); markDirty();
            }
        };
    });

    container.querySelectorAll('button[data-act], input[data-act], span[data-act], select[data-act]').forEach(b => {
        b.onchange = b.onclick = (e) => {
            if (b.tagName === 'INPUT' && e.type !== 'change') return;
            if (b.tagName === 'BUTTON' && e.type !== 'click') return;
            if (b.tagName === 'SPAN' && e.type !== 'click') return;
            if (b.tagName === 'SELECT' && e.type !== 'change') return;
            const act = b.dataset.act;
            if (act === 'groupToggleCollapse') {
                const g = b.dataset.group;
                customGroups[g].collapsed = !customGroups[g].collapsed;
                renderMyLayers();
                return;
            }
            if (act === 'groupStyle') {
                const g = b.dataset.group;
                const panel = container.querySelector(`.group-styling-panel[data-group="${g}"]`);
                if (panel) panel.classList.toggle('open');
                return;
            }
            if (act === 'groupEye') {
                const g = b.dataset.group;
                const ids = customGroups[g].ids || [];
                const anyVis = features.some(f => ids.includes(f.id) && f.props.visible);
                features.forEach(f => { if (ids.includes(f.id)) f.props.visible = anyVis ? 0 : 1; });
                syncDraw(); renderMyLayers(); markDirty();
                return;
            }
            if (act === 'groupDel') {
                const g = b.dataset.group;
                delete customGroups[g];
                renderMyLayers();
                markDirty();
                return;
            }
            const id = parseInt(b.dataset.id, 10);
            const f = features.find(x => x.id === id);
            if (!f) return;
            if (act === 'table') {
                openAttributeTable(id);
                return;
            }
            if (act === 'labelToggle') { f.props.showLabel = b.checked; syncDraw(); markDirty(); }
            if (act === 'labelPos') { f.props.labelPos = b.value; syncDraw(); markDirty(); }
            if (act === 'eye') {
                f.props.visible = f.props.visible ? 0 : 1;
                syncDraw();
                renderMyLayers();
                markDirty();
            }
            if (act === 'del') {
                features = features.filter(x => x.id !== id);
                for (const g in customGroups) customGroups[g].ids = customGroups[g].ids.filter(xId => xId !== id);
                selectedLayerIds.delete(id);
                if (selectedId === id) selectedId = null;
                syncDraw(); renderMyLayers(); markDirty();
            }
            if (act === 'zoom') {
                const bnd = calcBounds(f);
                if (bnd) {
                    map.fitBounds(bnd, { padding: 60, maxZoom: 18 });
                    pulseFeature(f);
                }
            }
        };
    });

    container.querySelectorAll('.grp-style-apply').forEach(btn => {
        btn.onclick = () => {
            const panel = btn.closest('.group-styling-panel');
            const gName = panel.dataset.group;
            const color = panel.querySelector('.grp-style-color').value;
            const shape = panel.querySelector('.grp-style-shape').value;
            const size = parseFloat(panel.querySelector('.grp-style-size').value);
            const grp = customGroups[gName];
            if (!grp) return;
            grp.ids.forEach(id => {
                const f = features.find(x => x.id === id);
                if (f && f.kind === 'marker') {
                    f.props.color = color;
                    f.props.borderColor = color;
                    if (shape) f.props.shape = shape;
                    f.props.iconSize = size;
                    f.props.iconKey = getIconKey(f.props.shape || 'pin', color);
                }
            });
            syncDraw();
            renderMyLayers();
            markDirty();
            hint(`Styling applied to "${gName}"`);
        };
    });
}

function reorderFeatures(draggedId, targetId) {
    const draggedIndex = features.findIndex(f => f.id === draggedId);
    const targetIndex = features.findIndex(f => f.id === targetId);
    if (draggedIndex === -1 || targetIndex === -1) return;
    const [draggedItem] = features.splice(draggedIndex, 1);
    features.splice(targetIndex, 0, draggedItem);
    syncDraw();
    renderMyLayers();
    markDirty();
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

// Attribute Table Logic
function openAttributeTable(featureId) {
    currentTableFeatureId = featureId;
    const f = features.find(x => x.id === featureId);
    if (!f) return;
    
    closeFloatingCards();
    $('attrTableTitle').textContent = `Attributes: ${f.name}`;
    $('popup-attribute-table').classList.add('open');
    
    if (!f.props.attributes) {
        f.props.attributes = {
            name: f.name || '',
            description: f.props.description || ''
        };
    }
    if (!f.props.attrTypes) {
        f.props.attrTypes = { name: 'text', description: 'text' };
    }
    if (!f.props.attrRows) {
        f.props.attrRows = [{ ...f.props.attributes }];
    }
    
    renderAttributeTable(f);
}

function renderAttributeTable(f) {
    const headerRow = $('attrTableHeader');
    const bodyRow = $('attrTableBody');
    const types = f.props.attrTypes || { name: 'text', description: 'text' };
    const cols = Object.keys(types);
    const rows = f.props.attrRows || [{ ...f.props.attributes }];
    
    headerRow.innerHTML = `<tr>` + cols.map(c => `
        <th>
            <div style="display:flex; justify-content:space-between; align-items:center; gap:4px;">
                <span>${c}</span>
                <select onchange="changeColType('${c}', this.value)" style="font-size:9px; padding:1px 2px; border-radius:3px;">
                    <option value="text" ${types[c] === 'text' ? 'selected' : ''}>Text</option>
                    <option value="image" ${types[c] === 'image' ? 'selected' : ''}>Image</option>
                </select>
            </div>
        </th>
    `).join('') + `<th style="width:40px;">DEL</th></tr>`;
    
    let html = '';
    rows.forEach((r, rIdx) => {
        html += `<tr>`;
        cols.forEach(c => {
            const val = r[c] || '';
            const t = types[c] || 'text';
            if (t === 'image') {
                if (val && typeof val === 'string' && val.startsWith('data:image')) {
                    html += `<td><img src="${val}" class="attr-img-preview" onclick="triggerAttrImageUpload(${rIdx}, '${c}')" oncontextmenu="clearAttrImage(${rIdx}, '${c}'); return false;" title="Click to replace, Right-click to clear"></td>`;
                } else {
                    html += `<td><div class="attr-img-placeholder" onclick="triggerAttrImageUpload(${rIdx}, '${c}')">+ Upload Image</div></td>`;
                }
            } else {
                html += `<td><input type="text" value="${val}" onchange="updateAttrCell(${rIdx}, '${c}', this.value)"></td>`;
            }
        });
        html += `<td><button class="card-btn" onclick="removeAttrRow(${rIdx})" title="Delete row" style="color:#ff7b72;">✕</button></td></tr>`;
    });
    bodyRow.innerHTML = html;
}

window.changeColType = (colName, newType) => {
    const f = features.find(x => x.id === currentTableFeatureId);
    if (!f) return;
    f.props.attrTypes[colName] = newType;
    renderAttributeTable(f);
    markDirty();
};

window.updateAttrCell = (rIdx, key, val) => {
    const f = features.find(x => x.id === currentTableFeatureId);
    if (!f) return;
    if (!f.props.attrRows[rIdx]) f.props.attrRows[rIdx] = {};
    f.props.attrRows[rIdx][key] = val;
    if (rIdx === 0) {
        f.props.attributes[key] = val;
        if (key === 'name') {
            f.name = val;
            renderMyLayers();
        }
        if (key === 'description') {
            f.props.description = val;
        }
    }
    syncDraw();
    markDirty();
};

window.triggerAttrImageUpload = (rIdx, key) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = e => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = ev => {
                const f = features.find(x => x.id === currentTableFeatureId);
                if (f) {
                    if (!f.props.attrRows[rIdx]) f.props.attrRows[rIdx] = {};
                    f.props.attrRows[rIdx][key] = ev.target.result;
                    if (rIdx === 0) f.props.attributes[key] = ev.target.result;
                    renderAttributeTable(f);
                    markDirty();
                }
            };
            reader.readAsDataURL(file);
        }
    };
    input.click();
};

window.clearAttrImage = (rIdx, key) => {
    const f = features.find(x => x.id === currentTableFeatureId);
    if (f && f.props.attrRows[rIdx]) {
        f.props.attrRows[rIdx][key] = '';
        if (rIdx === 0) f.props.attributes[key] = '';
        renderAttributeTable(f);
        markDirty();
    }
};

window.removeAttrRow = (rIdx) => {
    const f = features.find(x => x.id === currentTableFeatureId);
    if (!f || f.props.attrRows.length <= 1) {
        hint('Cannot remove the primary row');
        return;
    }
    f.props.attrRows.splice(rIdx, 1);
    renderAttributeTable(f);
    markDirty();
};

$('btnAddAttrRow').onclick = () => {
    const f = features.find(x => x.id === currentTableFeatureId);
    if (!f) return;
    const newRow = {};
    Object.keys(f.props.attrTypes).forEach(k => newRow[k] = '');
    f.props.attrRows.push(newRow);
    renderAttributeTable(f);
    markDirty();
};

$('btnAddAttrCol').onclick = () => {
    const f = features.find(x => x.id === currentTableFeatureId);
    if (!f) return;
    const name = prompt("Enter new column name:");
    if (name && name.trim()) {
        const c = name.trim();
        const type = confirm("Is this column for Images? (Click Cancel for standard Text)") ? "image" : "text";
        if (!f.props.attrTypes[c]) {
            f.props.attrTypes[c] = type;
            f.props.attrRows.forEach(r => r[c] = '');
            f.props.attributes[c] = '';
            renderAttributeTable(f);
            markDirty();
        }
    }
};

$('attrTableSearch').oninput = e => {
    const term = e.target.value.toLowerCase();
    const rows = $('attrTableBody').querySelectorAll('tr');
    rows.forEach(tr => {
        const text = tr.innerText.toLowerCase() + Array.from(tr.querySelectorAll('input')).map(i => i.value.toLowerCase()).join(' ');
        tr.style.display = text.includes(term) ? '' : 'none';
    });
};

$('closeAttrTableBtn').onclick = () => {
    $('popup-attribute-table').classList.remove('open');
    currentTableFeatureId = null;
    markDirty();
    syncDraw();
};

// Direct Export Engine
$('btn-export-direct').onclick = () => {
    hint('Exporting high-quality snapshot...');
    map.once('render', () => {
        try {
            const srcCanvas = map.getCanvas();
            const a = document.createElement('a');
            a.download = `Project_Atlas_${Date.now()}.png`;
            a.href = srcCanvas.toDataURL('image/png', 0.98);
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            hint('Export complete!');
        } catch(e) {
            hint('Export failed.');
        }
    });
    map.triggerRepaint();
};

// UI Panel Toggles
$('btn-browser-toggle').onclick = () => {
    const p = $('browser-panel');
    const willOpen = !p.classList.contains('open');
    closeFloatingCards();
    if (willOpen) p.classList.add('open');
};
$('btn-close-browser').onclick = () => { $('browser-panel').classList.remove('open'); };

$('btn-mylayers-toggle').onclick = () => {
    const p = $('mylayers-panel');
    const willOpen = !p.classList.contains('open');
    closeFloatingCards();
    if (willOpen) p.classList.add('open');
};
$('btn-close-mylayers').onclick = () => { $('mylayers-panel').classList.remove('open'); };

document.querySelectorAll('.acc-header').forEach(h => {
    h.onclick = () => {
        const body = $(h.dataset.target);
        if (body) {
            body.classList.toggle('hidden');
            const chev = h.querySelector('span:last-child');
            if (chev) chev.textContent = body.classList.contains('hidden') ? '▸' : '▾';
        }
    };
});

document.querySelectorAll('#browser-panel input[data-g]').forEach(cb => {
    cb.onchange = () => {
        vis[cb.dataset.g] = cb.checked;
        applyVis();
        markDirty();
    };
});

$('btn-custom-map').onclick = () => {
    const p = $('popup-custom-map');
    const willOpen = !p.classList.contains('open');
    closeFloatingCards();
    if (willOpen) p.classList.add('open');
};
$('closeCustomMapBtn').onclick = () => { $('popup-custom-map').classList.remove('open'); };

$('presetBtnList').innerHTML = Object.keys(ALL_STYLES).map(n =>
    `<button style="border:1px solid rgba(255,255,255,0.1); background:rgba(255,255,255,0.05); color:#adbac7; border-radius:6px; padding:5px 8px; font-size:11px; cursor:pointer;" data-n="${n}">${n}</button>`
).join('');

$('presetBtnList').querySelectorAll('button').forEach(b => {
    b.onclick = () => {
        currentStyleName = b.dataset.n;
        map.setStyle(ALL_STYLES[currentStyleName]);
        map.once('idle', () => { addDrawStack(); applyVis(); });
        markDirty();
    };
});

const setMapPaint = (id, prop, val) => { if (map.getLayer(id)) map.setPaintProperty(id, prop, val); };
$('cMainWidth').oninput = e => { setMapPaint('rd_major', 'line-width', parseFloat(e.target.value)); markDirty(); };
$('cMainOp').oninput = e => { setMapPaint('rd_major', 'line-opacity', parseFloat(e.target.value)); markDirty(); };
$('cSecWidth').oninput = e => { setMapPaint('rd_secondary', 'line-width', parseFloat(e.target.value)); markDirty(); };
$('cSecOp').oninput = e => { setMapPaint('rd_secondary', 'line-opacity', parseFloat(e.target.value)); markDirty(); };
$('cTerWidth').oninput = e => { setMapPaint('rd_tertiary', 'line-width', parseFloat(e.target.value)); markDirty(); };
$('cTerOp').oninput = e => { ['rd_tertiary','rd_min_md','rd_min_lo','rd_path'].forEach(id => setMapPaint(id, 'line-opacity', parseFloat(e.target.value))); markDirty(); };
$('cBldOp').oninput = e => { setMapPaint('building-2d', 'fill-opacity', parseFloat(e.target.value)); setMapPaint('building-3d', 'fill-extrusion-opacity', parseFloat(e.target.value)); markDirty(); };
$('cWaterOp').oninput = e => { setMapPaint('water', 'fill-opacity', parseFloat(e.target.value)); setMapPaint('waterway', 'line-opacity', parseFloat(e.target.value)); };

// Import Logic
$('btn-import').onclick = () => { $('importFileInput').click(); };
$('btn-import-toolbar').onclick = () => { $('importFileInput').click(); };
$('importFileInput').onchange = async function(e) {
    const file = e.target.files[0];
    if (!file) return;
    const ext = file.name.split('.').pop().toLowerCase();
    hint(`Importing ${file.name}…`);
    try {
        if (ext === 'geojson' || ext === 'json') {
            const text = await file.text();
            const data = JSON.parse(text);
            const geojson = data.type === 'FeatureCollection' ? data : { type: 'FeatureCollection', features: [data] };
            processGeoJSON(geojson);
        } else if (ext === 'kml') {
            const text = await file.text();
            const kml = new DOMParser().parseFromString(text, 'application/xml');
            const geojson = toGeoJSON.kml(kml);
            processGeoJSON(geojson);
        } else if (ext === 'kmz') {
            const arrayBuffer = await file.arrayBuffer();
            const zip = await JSZip.loadAsync(arrayBuffer);
            const kmlFile = Object.keys(zip.files).find(name => name.endsWith('.kml'));
            if (!kmlFile) throw new Error('No KML found in KMZ');
            const kmlText = await zip.file(kmlFile).async('string');
            const kml = new DOMParser().parseFromString(kmlText, 'application/xml');
            const geojson = toGeoJSON.kml(kml);
            processGeoJSON(geojson);
        } else if (ext === 'zip') {
            const arrayBuffer = await file.arrayBuffer();
            const geojson = await shp(arrayBuffer);
            processGeoJSON(geojson);
        }
        hint('Import successful');
    } catch(err) {
        hint('Import failed: ' + err.message);
    }
};

function processGeoJSON(geojson) {
    const feats = geojson.features || [];
    feats.forEach(f => {
        if (!f.geometry) return;
        const geom = f.geometry;
        const props = f.properties || {};
        if (geom.type === 'Point') {
            addFeatureRecord('marker', geom, {
                shape: 'pin',
                color: '#1e40af',
                iconSize: 0.9,
                iconKey: getIconKey('pin', '#1e40af'),
                osmTags: props
            });
        } else if (geom.type === 'LineString' || geom.type === 'MultiLineString') {
            if (props.route_mode || props.routeMode) {
                addFeatureRecord('route', geom, {
                    routeMode: props.route_mode || props.routeMode,
                    description: props.description || '',
                    color: props.color || '#38bdf8',
                    borderColor: props.color || '#38bdf8',
                    waypoints: geom.coordinates
                });
            } else {
                addFeatureRecord('polyline', geom, {});
            }
        } else if (geom.type === 'Polygon' || geom.type === 'MultiPolygon') {
            if (props.render_height || props.height || props.extrusionHeight) {
                addFeatureRecord('polygon3d', geom, {
                    extrusionHeight: props.render_height || props.height || props.extrusionHeight || 35,
                    extrusionBase: props.render_min_height || props.min_height || 0
                });
            } else {
                addFeatureRecord('polygon', geom, {});
            }
        }
    });
}

map.on('moveend', () => markDirty(false));
map.on('error', e => console.warn('Map Notice:', e));

} catch (e) {
    console.error('App init error:', e);
}
</script>
</body>
</html>"""

# ------------------------------------------------------------------------
# 5. INITIAL STATE & COMPONENT MOUNTING
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
        .replace("__COLOR_PALETTES__", json.dumps(COLOR_PALETTES))
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
    st.error(f"Failed to load application: {e}")

import json
import logging
import random
import time
import requests
import streamlit as st

# ------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STREAMLIT BRANDING REMOVAL
# ------------------------------------------------------------------------
st.set_page_config(
    page_title="Project Atlas",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def hide_streamlit_branding():
    """
    Completely removes Streamlit watermarks, headers, footers, deploy buttons,
    status widgets, and profile/avatar previews using CSS and MutationObserver JS.
    """
    css_injection = """
    <style>
    header[data-testid="stHeader"],
    div[data-testid="stDecoration"],
    footer,
    [data-testid="stToolbar"],
    [data-testid="stStatusWidget"],
    #MainMenu,
    .viewerBadge_container__1QSob,
    .styles_viewerBadge__1yB5_,
    [data-testid="stDeployButton"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }
    a[href*="streamlit.io"] {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }
    img[src*="avatar"],
    [data-testid="stAvatar"],
    [data-testid="stProfile"] {
        display: none !important;
        visibility: hidden !important;
    }
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
    """
    st.markdown(css_injection, unsafe_allow_html=True)

    js_injection = """
    <script>
    (function() {
        const targetSelectors = [
            'header[data-testid="stHeader"]',
            'div[data-testid="stDecoration"]',
            'footer',
            '[data-testid="stToolbar"]',
            '[data-testid="stStatusWidget"]',
            '#MainMenu',
            '[data-testid="stDeployButton"]',
            'a[href*="streamlit.io"]',
            'img[src*="avatar"]',
            '[data-testid="stAvatar"]'
        ];

        function cleanElements(root) {
            targetSelectors.forEach(selector => {
                const elements = root.querySelectorAll(selector);
                elements.forEach(el => {
                    el.style.setProperty('display', 'none', 'important');
                    el.style.setProperty('visibility', 'hidden', 'important');
                });
            });
        }

        const doc = window.parent ? window.parent.document : document;
        cleanElements(doc);

        const observer = new MutationObserver(() => cleanElements(doc));
        observer.observe(doc.body, { childList: true, subtree: true });

        doc.addEventListener('click', function(e) {
            const link = e.target.closest('a[href*="streamlit.io"]');
            if (link) {
                e.preventDefault();
                e.stopPropagation();
            }
        }, true);
    })();
    </script>
    """
    st.markdown(js_injection, unsafe_allow_html=True)

hide_streamlit_branding()

# ------------------------------------------------------------------------
# 2. OVERPASS API QUERY & NOMINATIM GEOCODING (PYTHON)
# ------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_pois(lat: float, lon: float, radius: int, tags: list, timeout: int = 90) -> list:
    """Robustly queries Overpass API with built-in retries, failover, and OSMnx fallback."""
    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.openstreetmap.fr/api/interpreter"
    ]
    statements = "\n".join([f"  nwr[{tag}](around:{radius},{lat},{lon});" for tag in tags])
    ql = f"[out:json][timeout:{timeout}];(\n{statements}\n);\nout center;"
    
    for endpoint in endpoints:
        delay = 1.0
        for _ in range(5):
            try:
                res = requests.get(f"{endpoint}?data={requests.utils.quote(ql)}", timeout=timeout)
                if res.status_code in [429, 503, 504]:
                    raise requests.exceptions.HTTPError(f"HTTP {res.status_code}")
                res.raise_for_status()
                data = res.json()
                if not data or 'elements' not in data:
                    raise ValueError("Malformed JSON")
                
                results = []
                for el in data['elements']:
                    el_lat = el.get('lat') or (el.get('center', {}).get('lat'))
                    el_lon = el.get('lon') or (el.get('center', {}).get('lon'))
                    if el_lat is None or el_lon is None:
                        continue
                    t = el.get('tags', {})
                    results.append({
                        'lat': float(el_lat),
                        'lon': float(el_lon),
                        'name': str(t.get('name', 'Unknown')),
                        'type': str(t.get('amenity') or t.get('shop') or t.get('building') or 'Node'),
                        'tags': t
                    })
                return results
            except Exception:
                time.sleep(delay + random.uniform(0, 0.5))
                delay *= 2

    try:
        import osmnx as ox
        import pandas as pd
        tags_dict = {
            t.split('=')[0].replace('"', ''): (t.split('=')[1].replace('"', '').split('|') if '=' in t and '|' in t.split('=')[1] else t.split('=')[1].replace('"', '') if '=' in t else True)
            for t in tags
        }
        gdf = ox.geometries_from_point((lat, lon), tags_dict, dist=radius)
        results = []
        for _, row in gdf.iterrows():
            geom = row.geometry
            lon_val, lat_val = (geom.x, geom.y) if geom.geom_type == 'Point' else (geom.centroid.x, geom.centroid.y)
            results.append({
                'lat': float(lat_val),
                'lon': float(lon_val),
                'name': str(row.get('name', 'Unknown')) if pd.notna(row.get('name')) else 'Unknown',
                'type': str(row.get('amenity') or row.get('shop') or row.get('building') or 'Node'),
                'tags': {k: v for k, v in row.items() if k not in ['geometry', 'name', 'amenity', 'shop', 'building']}
            })
        return results
    except Exception:
        return []

def geocode_nominatim(query: str, limit: int = 5) -> list:
    """Forward geocoding using OpenStreetMap Nominatim API."""
    try:
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={requests.utils.quote(query)}&limit={limit}"
        headers = {"User-Agent": "ProjectAtlasSpatialEngine/2.0"}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []

# ------------------------------------------------------------------------
# 3. SUPABASE REST INTEGRATION
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
        url = f"{BASE_API_URL}/map_projects?select=id,name,updated_at,basemap,zoom,center,pitch,bearing,features,custom_groups,layer_visibilities&order=updated_at.desc"
        res = requests.get(url, headers=get_headers(), timeout=6)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []

ALL_PROJECTS_LIST = fetch_projects()

# ------------------------------------------------------------------------
# 4. POI TAXONOMY & VECTOR BASEMAP THEMES
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
    for z, val in stops:
        out += [z, val]
    return out

def road_layer(p, lid, classes, color, widths, minzoom=0, casing=False, opacity=1.0):
    lyr = {
        "id": lid + ("_casing" if casing else ""),
        "type": "line", "source": "omt", "source-layer": "transportation",
        "filter": ["match", ["get", "class"], classes, True, False],
        "layout": {"line-cap": "round", "line-join": "round"},
        "paint": {
            "line-color": p["rd_case"] if casing else color,
            "line-width": w(*([(z, val + 1.8) for z, val in widths] if casing else widths)),
            "line-opacity": opacity
        },
    }
    if minzoom: lyr["minzoom"] = minzoom
    return lyr

def vector_style(p):
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
                    "fill-extrusion-height": ["coalesce", ["get", "render_height"], ["get", "height"], 14],
                    "fill-extrusion-base": ["coalesce", ["get", "render_min_height"], 0],
                    "fill-extrusion-opacity": 0.85
                }
            },
            {"id": "bound_prov", "type": "line", "source": "omt", "source-layer": "boundary", "filter": ["match", ["get", "admin_level"], [2, 4], True, False], "layout": {"visibility": "none"}, "paint": {"line-color": "#ff1e1e", "line-width": 2.2, "line-dasharray": [4, 2]}},
            {"id": "bound_city", "type": "line", "source": "omt", "source-layer": "boundary", "filter": ["match", ["get", "admin_level"], [6, 7, 8], True, False], "minzoom": 7, "layout": {"visibility": "none"}, "paint": {"line-color": "#ff1e1e", "line-width": 1.8, "line-dasharray": [2, 2], "line-opacity": 0.9}},
            {"id": "bound_brgy", "type": "line", "source": "omt", "source-layer": "boundary", "filter": ["match", ["get", "admin_level"], [9, 10], True, False], "minzoom": 11, "layout": {"visibility": "none"}, "paint": {"line-color": "#ff1e1e", "line-width": 1.2, "line-dasharray": [1, 2], "line-opacity": 0.8}},
            road_layer(p, "case_express", ["motorway"], None, [(5, 1.5), (14, 5.5), (20, 24)], casing=True),
            road_layer(p, "case_major", ["trunk", "primary"], None, [(6, 1.0), (14, 3.8), (20, 18)], casing=True),
            road_layer(p, "case_secondary", ["secondary"], None, [(8, 0.8), (14, 2.8), (20, 15)], casing=True, opacity=p["sec_opacity"]),
            road_layer(p, "case_tertiary", ["tertiary"], None, [(9, 0.6), (14, 2.0), (20, 12)], casing=True, opacity=p["ter_opacity"]),
            road_layer(p, "rd_path", ["path", "pedestrian", "footway"], p["rd_path"], [(14, 0.6), (20, 5)], minzoom=14),
            road_layer(p, "rd_min_lo", ["service", "track"], p["rd_min_lo"], [(14, 0.6), (20, 6)], minzoom=14),
            road_layer(p, "rd_min_md", ["minor"], p["rd_min_md"], [(13, 0.8), (16, 3.5), (20, 10)], minzoom=13),
            road_layer(p, "rd_tertiary", ["tertiary"], p["rd_tertiary"], [(9, 0.6), (14, 2.0), (20, 12)], opacity=p["ter_opacity"]),
            road_layer(p, "rd_secondary", ["secondary"], p["rd_secondary"], [(8, 0.8), (14, 2.8), (20, 15)], opacity=p["sec_opacity"]),
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
# 5. SINGLE-PAGE RAW HTML/JAVASCRIPT ENGINE (r"""...""")
# ------------------------------------------------------------------------
HTML_TEMPLATE = r"""<!DOCTYPE html>
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
:root {
    --bg-dark: rgba(9, 16, 24, 0.97);
    --border-dark: rgba(255, 255, 255, 0.12);
    --accent: #316dca;
    --accent-hover: #2563eb;
    --sky: #38bdf8;
    --gold: #e8b84a;
    --danger: #f85149;
    --text-main: #f0f6fc;
    --text-muted: #adbac7;
}
* { box-sizing: border-box; user-select: none; font-family: 'Century Gothic Custom', -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif; }
html, body { margin: 0; padding: 0; width: 100vw; height: 100vh; overflow: hidden; background: #0a1628; }
#map { position: absolute; inset: 0; width: 100vw; height: 100vh; z-index: 1; }
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.15); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.3); }
select, select option { background-color: #0f172a !important; color: #f8fafc !important; }
#top-toolbar-bar {
    position: fixed; top: 16px; left: 50%; transform: translateX(-50%); z-index: 1000;
    background-color: var(--bg-dark); border: 1px solid var(--border-dark);
    border-radius: 36px; padding: 4px 10px; display: flex; align-items: center; gap: 4px;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.6); color: var(--text-main);
}
.tb-btn {
    width: 32px; height: 32px; display: grid; place-items: center;
    background: transparent; border: none; color: var(--text-muted); border-radius: 50%;
    cursor: pointer; transition: all 0.15s ease;
}
.tb-btn:hover { background: rgba(255, 255, 255, 0.1); color: #ffffff; }
.tb-btn.active { background: rgba(255, 255, 255, 0.18); color: #ffffff; }
.tb-btn.primary-active { background: var(--accent); color: #ffffff; }
.tb-sep { width: 1px; height: 18px; background: rgba(255, 255, 255, 0.12); margin: 0 4px; }
#project-meta-cluster { display: flex; align-items: center; gap: 8px; padding: 0 4px; }
#project-name-display { font-weight: 700; color: var(--sky); font-size: 12px; max-width: 140px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer; }
.save-badge { font-size: 9px; padding: 2px 7px; border-radius: 12px; font-weight: 600; background: rgba(255, 255, 255, 0.08); color: #8b949e; border: 1px solid rgba(255, 255, 255, 0.1); display: flex; align-items: center; gap: 4px; }
.save-badge.saving { color: #d9b451; border-color: rgba(217, 180, 81, 0.4); }
.save-badge.saved { color: #3fb950; border-color: rgba(63, 185, 80, 0.4); }
.save-badge.unsaved { color: var(--danger); border-color: rgba(248, 81, 73, 0.4); }
.left-panel {
    position: fixed; top: 68px; left: 16px; bottom: 16px; width: 360px; z-index: 999;
    background-color: var(--bg-dark); border: 1px solid var(--border-dark);
    border-radius: 20px; box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7);
    display: none; flex-direction: column; overflow: hidden; color: var(--text-muted);
}
.left-panel.open { display: flex; }
.panel-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 16px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); }
.panel-title { display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 14px; color: var(--text-main); }
.icon-action-btn { width: 28px; height: 28px; display: grid; place-items: center; border: 1px solid rgba(255, 255, 255, 0.1); background: rgba(255, 255, 255, 0.05); border-radius: 8px; cursor: pointer; color: var(--text-muted); transition: 0.2s; }
.icon-action-btn:hover { background: rgba(255, 255, 255, 0.15); color: var(--text-main); }
.panel-content { flex: 1; overflow-y: auto; padding: 14px 16px; display: flex; flex-direction: column; gap: 12px; font-size: 12px; }
.acc-item { border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 8px; }
.acc-header { display: flex; align-items: center; justify-content: space-between; font-size: 13px; font-weight: 600; color: var(--text-main); cursor: pointer; padding: 6px 4px; border-radius: 4px; }
.acc-body { padding: 6px 4px 2px 4px; display: flex; flex-direction: column; gap: 8px; }
.acc-body.hidden { display: none !important; }
.layer-row { display: flex; align-items: center; justify-content: space-between; font-size: 12px; color: var(--text-muted); }
.layer-row input[type=checkbox] { accent-color: var(--accent); cursor: pointer; }
.dimension-mode-bar { display: flex; gap: 4px; background: rgba(0, 0, 0, 0.35); padding: 3px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.08); margin-bottom: 4px; }
.dimension-mode-btn { flex: 1; border: none; background: transparent; color: var(--text-muted); font-size: 11px; font-weight: 700; padding: 5px 0; border-radius: 6px; cursor: pointer; }
.dimension-mode-btn.active { background: var(--accent); color: #ffffff; }
.bound-select-row { display: flex; gap: 6px; margin-top: 4px; position: relative; }
.bound-select-row input[type=text] { flex: 1; background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(255, 255, 255, 0.12); color: var(--text-main); padding: 6px 8px; border-radius: 8px; font-size: 11px; }
.autocomplete-list {
    position: absolute; top: 100%; left: 0; right: 0; z-index: 1001;
    background: #0f172a; border: 1px solid rgba(255,255,255,0.12); border-radius: 8px;
    max-height: 200px; overflow-y: auto; display: none; margin-top: 4px; box-shadow: 0 8px 16px rgba(0,0,0,0.5);
}
.autocomplete-item { padding: 8px 10px; cursor: pointer; font-size: 11px; color: var(--text-muted); border-bottom: 1px solid rgba(255,255,255,0.05); }
.autocomplete-item:hover { background: rgba(255,255,255,0.1); color: #fff; }
.layers-heading { display: flex; align-items: center; justify-content: space-between; font-weight: 700; font-size: 13px; color: var(--text-main); margin-top: 6px; }
.badge-count { background: var(--accent); color: #ffffff; border-radius: 12px; font-size: 11px; padding: 1px 8px; font-weight: 600; }
.group-container { background: rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; margin-top: 6px; overflow: hidden; }
.group-container.drop-hover { border-color: var(--sky); background: rgba(56, 189, 248, 0.12); }
.group-header { background: rgba(255, 255, 255, 0.05); padding: 8px 10px; display: flex; align-items: center; justify-content: space-between; }
.group-title-input { background: transparent; border: none; font-weight: 700; color: var(--text-main); font-size: 12px; width: 120px; }
.group-items { padding: 4px 6px; display: flex; flex-direction: column; gap: 4px; }
.group-items.hidden { display: none !important; }
.layer-card { background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 8px; padding: 6px 8px; display: flex; flex-direction: column; gap: 4px; margin-top: 4px; cursor: grab; }
.layer-card:active { cursor: grabbing; }
.layer-card-top { display: flex; align-items: center; gap: 4px; overflow: hidden; }
.layer-name-input { flex: 1; min-width: 50px; border: 1px solid transparent; background: transparent; font-weight: 600; font-size: 12px; color: var(--text-main); padding: 2px 4px; border-radius: 4px; text-overflow: ellipsis; white-space: nowrap; overflow: hidden; }
.layer-name-input:focus { border-color: var(--accent); background: rgba(0,0,0,0.4); outline: none; }
.card-btn { background: transparent; border: none; color: #768390; cursor: pointer; padding: 2px 4px; border-radius: 4px; transition: 0.15s; flex-shrink: 0; display: inline-flex; align-items: center; justify-content: center; }
.card-btn:hover { color: var(--text-main); background: rgba(255,255,255,0.1); }
.card-btn svg { width: 14px; height: 14px; }
#ungrouped-zone { border: 1px dashed transparent; border-radius: 8px; padding: 2px; }
#ungrouped-zone.drop-hover { border-color: var(--sky); background: rgba(56, 189, 248, 0.08); }
.trade-btn { background: var(--accent); color: #ffffff; border: none; border-radius: 8px; padding: 7px; font-weight: 600; cursor: pointer; font-size: 11px; transition: 0.2s; }
.trade-btn:hover { background: var(--accent-hover); }
.poi-summary { font-size: 11px; color: var(--text-muted); max-height: 180px; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; margin-top: 4px; }
.poi-badge { display: flex; justify-content: space-between; background: rgba(255,255,255,0.05); padding: 5px 8px; border-radius: 6px; }
.float-card {
    position: fixed; top: 68px; z-index: 998;
    background-color: var(--bg-dark); border: 1px solid var(--border-dark);
    border-radius: 18px; padding: 14px; box-shadow: 0 20px 48px rgba(0, 0, 0, 0.75);
    display: none; flex-direction: column; gap: 10px; font-size: 12px; color: var(--text-muted);
    max-height: 80vh; overflow-y: auto;
}
.float-card.open { display: flex; }
.right-card { right: 16px; left: auto; width: 330px; }
.float-card .f-row { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.float-card input[type=range] { accent-color: var(--accent); width: 110px; cursor: pointer; }
.float-card input[type=text], .float-card select { background: rgba(0,0,0,0.4); color: var(--text-main); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 8px; padding: 6px 8px; font-size: 12px; outline: none; }
.float-card input[type=text]:focus { border-color: var(--sky); }
#popup-search { width: 340px; left: 50%; transform: translateX(-50%); }
#popup-route-mode-choice { width: 320px; left: 50%; transform: translateX(-50%); }
#popup-attribute-table { width: 640px; left: 50%; transform: translateX(-50%); }
.icon-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
.icon-grid button { width: 36px; height: 36px; display: grid; place-items: center; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; background: rgba(255,255,255,0.05); color: var(--text-muted); cursor: pointer; }
.icon-grid button.active { border-color: var(--accent); background: var(--accent); color: #ffffff; }
.maplibregl-popup-content {
    background: var(--bg-dark) !important; color: var(--text-main) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important; border-radius: 14px !important;
    padding: 12px !important; box-shadow: 0 12px 32px rgba(0,0,0,0.7) !important; font-size: 11px !important; max-width: 320px !important;
}
.maplibregl-popup-tip { border-top-color: var(--bg-dark) !important; }
.tag-table { width: 100%; border-collapse: collapse; margin-top: 6px; }
.tag-table th, .tag-table td { text-align: left; padding: 4px 6px; border: 1px solid rgba(255,255,255,0.08); font-size: 10px; }
.tag-table th { background: rgba(255,255,255,0.06); color: var(--sky); }
.tag-table td { word-break: break-all; }
#hint-toast {
    position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); z-index: 1001;
    background-color: var(--bg-dark); color: var(--text-main);
    border: 1px solid var(--border-dark); border-radius: 20px; padding: 7px 18px;
    font-size: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); display: none; font-weight: 600;
}
#map-context-menu {
    position: absolute; z-index: 3000; display: none; min-width: 220px;
    background: rgba(9, 16, 24, 0.98); border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 10px; padding: 4px; box-shadow: 0 12px 32px rgba(0,0,0,0.7);
}
.ctx-item { display: flex; align-items: center; gap: 8px; padding: 7px 10px; font-size: 12px; color: var(--text-main); cursor: pointer; border-radius: 6px; }
.ctx-item:hover { background: rgba(255, 255, 255, 0.1); }
.ctx-item svg { width: 14px; height: 14px; color: var(--text-muted); flex-shrink: 0; }
.ctx-coords { padding: 6px 10px; font-size: 10px; color: #768390; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 4px; }
.ctx-divider { height: 1px; background: rgba(255,255,255,0.08); margin: 4px 0; }
#launcher-modal-scrim {
    position: fixed; inset: 0; z-index: 9999; display: flex; align-items: center; justify-content: center;
    background-color: var(--bg-dark); opacity: 0; pointer-events: none; transition: opacity 0.2s ease;
}
#launcher-modal-scrim.visible { opacity: 1; pointer-events: auto; }
.ios26-card {
    width: 90%; max-width: 440px; max-height: 82vh; background-color: var(--bg-dark);
    border: 1px solid rgba(255, 255, 255, 0.16); border-radius: 24px;
    box-shadow: 0 32px 80px -12px rgba(0, 0, 0, 0.85); display: flex; flex-direction: column; overflow: hidden; color: #ffffff;
}
.ios26-header { padding: 22px 24px 14px 24px; display: flex; flex-direction: column; gap: 4px; }
.ios26-title { font-size: 20px; font-weight: 800; color: #ffffff; }
.ios26-subtitle { font-size: 13px; color: rgba(255, 255, 255, 0.6); }
.ios26-seg { margin: 0 24px 14px 24px; display: flex; background: rgba(0, 0, 0, 0.4); padding: 3px; border-radius: 14px; border: 1px solid rgba(255, 255, 255, 0.08); }
.ios26-seg-btn { flex: 1; border: none; background: transparent; color: rgba(255, 255, 255, 0.65); font-size: 12px; font-weight: 600; padding: 7px 0; border-radius: 11px; cursor: pointer; }
.ios26-seg-btn.active { background: rgba(255, 255, 255, 0.18); color: #ffffff; }
.ios26-body { padding: 0 24px 22px 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.ios26-input-group { display: flex; flex-direction: column; gap: 6px; }
.ios26-label { font-size: 11px; font-weight: 600; text-transform: uppercase; color: rgba(255, 255, 255, 0.5); }
.ios26-input { background: rgba(0, 0, 0, 0.35); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 14px; padding: 10px 14px; color: #ffffff; font-size: 13px; outline: none; }
.ios26-proj-item { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; }
.ios26-proj-item:hover { background: rgba(255, 255, 255, 0.1); }
.ios26-action-btn { background: var(--accent); color: #ffffff; border: none; border-radius: 14px; padding: 11px; font-weight: 700; font-size: 13px; cursor: pointer; }
.color-ctrl-cluster { display: flex; flex-direction: column; gap: 6px; width: 100%; }
.palette-group { display: flex; flex-direction: column; gap: 2px; }
.palette-label { font-size: 9px; font-weight: 700; color: #768390; text-transform: uppercase; }
.swatch-row { display: flex; gap: 4px; flex-wrap: wrap; align-items: center; }
.swatch { width: 16px; height: 16px; border-radius: 3px; cursor: pointer; border: 1px solid rgba(255,255,255,0.2); }
.swatch:hover { transform: scale(1.15); }
.color-input-combo { display: flex; align-items: center; gap: 4px; margin-top: 2px; }
.color-input-combo input[type=color] { -webkit-appearance: none; border: 1px solid rgba(255, 255, 255, 0.15); width: 24px; height: 24px; border-radius: 4px; cursor: pointer; background: transparent; padding: 0; }
.color-input-combo input[type=text] { width: 75px; font-family: monospace; font-size: 11px; padding: 3px 5px; }
.btn-eyedropper { width: 24px; height: 24px; display: grid; place-items: center; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); border-radius: 4px; color: var(--text-muted); cursor: pointer; }
.attr-table-container { width: 100%; overflow-x: auto; overflow-y: auto; max-height: 50vh; }
.attr-table { width: 100%; border-collapse: collapse; font-size: 12px; min-width: 500px; }
.attr-table th { position: sticky; top: 0; background: #0f172a; color: var(--text-main); padding: 8px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); font-size: 11px; }
.attr-table td { padding: 6px 8px; border-bottom: 1px solid rgba(255,255,255,0.05); }
.attr-table input[type="text"] { width: 100%; background: transparent; border: 1px solid rgba(255,255,255,0.1); color: var(--text-main); padding: 4px 6px; border-radius: 4px; }
.attr-img-preview { width: 80px; height: 80px; object-fit: cover; border-radius: 6px; border: 1px solid rgba(255,255,255,0.2); cursor: pointer; display: block; }
.attr-img-placeholder { width: 80px; height: 80px; border-radius: 6px; border: 1px dashed rgba(255,255,255,0.3); display: flex; align-items: center; justify-content: center; font-size: 10px; color: var(--text-muted); cursor: pointer; }
.stop-item { display: flex; align-items: center; gap: 4px; background: rgba(255,255,255,0.05); padding: 4px 6px; border-radius: 6px; font-size: 11px; }
.stop-item:active { cursor: grabbing; }
</style>
</head>
<body>
<div id="map"></div>

<!-- Top Toolbar -->
<div id="top-toolbar-bar">
    <button class="tb-btn" id="btn-home-dialog" title="Project Launcher">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
    </button>
    <div id="project-meta-cluster">
        <span id="project-name-display" title="Click to rename workspace">Untitled Project 1</span>
        <div class="save-badge saved" id="save-status-badge">
            <span id="save-dot">●</span>
            <span id="save-text">Saved</span>
        </div>
    </div>
    <button class="tb-btn" id="btn-save-project" title="Save Project (Ctrl+S)" style="color:#3fb950;">
        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>
    </button>
    <button class="tb-btn" id="btn-undo" title="Undo (Ctrl+Z)">
        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7v6h6"></path><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"></path></svg>
    </button>
    <button class="tb-btn" id="btn-redo" title="Redo (Ctrl+Y)">
        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 7v6h-6"></path><path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3L21 13"></path></svg>
    </button>
    <div class="tb-sep"></div>
    <button class="tb-btn" id="btn-browser-toggle" title="Data Browser">
        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"></path><path d="M2 12l10 6 10-6"></path><path d="M2 16l10 6 10-6"></path></svg>
    </button>
    <button class="tb-btn" id="btn-mylayers-toggle" title="My Layers">
        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
    </button>
    <button class="tb-btn" id="btn-search" title="Search Place">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"></circle><line x1="21" y1="21" x2="16.5" y2="16.5"></line></svg>
    </button>
    <button class="tb-btn" id="btn-import-toolbar" title="Import Spatial Data / Image">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
    </button>
    <input type="file" id="globalImportFileInput" accept=".kml,.kmz,.geojson,.json,.zip,.csv,.png,.jpg,.jpeg,.webp" style="display:none;"/>
    <div class="tb-sep"></div>
    <button class="tb-btn tool" data-tool="polygon" title="Polygon">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l8 6-3 10H7L4 9z"></path></svg>
    </button>
    <button class="tb-btn tool" data-tool="polygon3d" title="3D Polygon (Height Extrusion)">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path></svg>
    </button>
    <button class="tb-btn tool" data-tool="rectangle" title="Rectangle">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16"></rect></svg>
    </button>
    <button class="tb-btn tool" data-tool="circle" title="Circle (Radius)">
        <svg viewBox="0 0 24 24" width="14" height="14"><circle cx="12" cy="12" r="8" fill="currentColor"></circle></svg>
    </button>
    <button class="tb-btn tool" data-tool="polyline" title="Polyline">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"></path></svg>
    </button>
    <button class="tb-btn tool" data-tool="route" title="Route A to B (OSRM / Directions)">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="5" cy="19" r="2.5"></circle><circle cx="19" cy="5" r="2.5"></circle><path d="M7 17c4-1 3-8 8-9"></path></svg>
    </button>
    <button class="tb-btn tool" data-tool="marker" title="Marker">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"></path><circle cx="12" cy="10" r="2.5"></circle></svg>
    </button>
    <button class="tb-btn tool" data-tool="textbox" title="Textbox">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 7 4 4 20 4 20 7"></polyline><line x1="9" y1="20" x2="15" y2="20"></line><line x1="12" y1="4" x2="12" y2="20"></line></svg>
    </button>
    <button class="tb-btn tool" data-tool="imageOverlay" title="Image Overlay">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
    </button>
    <div class="tb-sep"></div>
    <button class="tb-btn" id="btn-custom-map" title="Basemap Styling">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon><line x1="8" y1="2" x2="8" y2="18"></line><line x1="16" y1="6" x2="16" y2="22"></line></svg>
    </button>
    <button class="tb-btn" id="btn-export-direct" title="Export PNG">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
    </button>
</div>

<!-- Left Panel: Data Browser -->
<div id="browser-panel" class="left-panel">
    <div class="panel-header">
        <div class="panel-title">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"></path><path d="M2 12l10 6 10-6"></path><path d="M2 16l10 6 10-6"></path></svg>
            <span>Data Browser</span>
        </div>
        <button class="icon-action-btn" id="btn-close-browser">✕</button>
    </div>
    <div class="panel-content">
        <div class="dimension-mode-bar">
            <button class="dimension-mode-btn" id="btn2DMode">2D MAP</button>
            <button class="dimension-mode-btn active" id="btn3DMode">3D BUILDINGS</button>
        </div>
        <div class="acc-item" id="btnOpenTradeAreaPopup" style="cursor:pointer;">
            <div class="acc-header" style="color:var(--sky);">
                <span>Trade Area Analysis</span>
                <span>▸</span>
            </div>
        </div>
        <div class="acc-item">
            <div class="acc-header" data-target="body-labels"><span>Labels</span> <span>▸</span></div>
            <div class="acc-body hidden" id="body-labels">
                <label class="layer-row"><span>City</span> <input type="checkbox" data-g="label_city" checked></label>
                <label class="layer-row"><span>Barangay</span> <input type="checkbox" data-g="label_brgy" checked></label>
                <label class="layer-row"><span>Street</span> <input type="checkbox" data-g="label_street" checked></label>
            </div>
        </div>
        <div class="acc-item">
            <div class="acc-header" data-target="body-roads"><span>Roads & Transit</span> <span>▸</span></div>
            <div class="acc-body hidden" id="body-roads">
                <label class="layer-row"><span>Expressway</span> <input type="checkbox" data-g="road_exp" checked></label>
                <label class="layer-row"><span>Main Road</span> <input type="checkbox" data-g="road_main" checked></label>
                <label class="layer-row"><span>Secondary Road</span> <input type="checkbox" data-g="road_sec" checked></label>
                <label class="layer-row"><span>Tertiary Road</span> <input type="checkbox" data-g="road_ter" checked></label>
                <label class="layer-row"><span>Railways</span> <input type="checkbox" data-g="rd_rail" checked></label>
            </div>
        </div>
        <div class="acc-item">
            <div class="acc-header" data-target="body-buildings"><span>Buildings</span> <span>▸</span></div>
            <div class="acc-body hidden" id="body-buildings">
                <label class="layer-row"><span>2D Buildings</span> <input type="checkbox" data-g="building2d"></label>
                <label class="layer-row"><span>3D Extrusion</span> <input type="checkbox" data-g="building3d" checked></label>
            </div>
        </div>
        <div class="acc-item">
            <div class="acc-header" data-target="body-water"><span>Water</span> <span>▸</span></div>
            <div class="acc-body hidden" id="body-water">
                <label class="layer-row"><span>Water Bodies</span> <input type="checkbox" data-g="water" checked></label>
                <label class="layer-row"><span>Waterways</span> <input type="checkbox" data-g="waterway" checked></label>
            </div>
        </div>
        <div class="acc-item">
            <div class="acc-header" data-target="body-boundaries"><span>Boundaries</span> <span>▸</span></div>
            <div class="acc-body hidden" id="body-boundaries">
                <label class="layer-row"><span>Provinces</span> <input type="checkbox" data-g="bound_prov"></label>
                <label class="layer-row"><span>Cities</span> <input type="checkbox" data-g="bound_city"></label>
                <label class="layer-row"><span>Barangays</span> <input type="checkbox" data-g="bound_brgy"></label>
                <div style="font-weight:600; font-size:11px; margin-top:4px;">Search Administrative Boundary</div>
                <div class="bound-select-row">
                    <input type="text" id="boundarySearchInput" placeholder="Search province, city, boundary..."/>
                    <div class="autocomplete-list" id="boundaryAutocompleteList"></div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Left Panel: My Layers -->
<div id="mylayers-panel" class="left-panel">
    <div class="panel-header">
        <div class="panel-title">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
            <span>My Layers</span>
        </div>
        <button class="icon-action-btn" id="btn-close-mylayers">✕</button>
    </div>
    <div class="panel-content">
        <div class="layers-heading">
            <span>Groups</span>
            <div style="display:flex; align-items:center; gap:4px;">
                <button class="icon-action-btn" id="btnSelectAllGlobal" title="Select / Deselect All">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"></path><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>
                </button>
                <button class="icon-action-btn" id="btnDeleteSelectedGlobal" title="Delete Selected" style="color:var(--danger);">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
                <button id="btnAddCustomGroup" class="trade-btn" style="padding:2px 6px; font-size:10px;">+ GROUP</button>
                <button id="btnHideSelected" class="trade-btn" style="padding:2px 6px; font-size:10px; background:#22272e; border:1px solid #2d333b; color:var(--text-muted);">Hide/Unhide</button>
                <span class="badge-count" id="layer-badge-count">0</span>
            </div>
        </div>
        <div id="my-layers-list"></div>
    </div>
</div>

<!-- Floating Popups & Modals -->
<div id="popup-search" class="float-card">
    <input type="text" id="searchInput" placeholder="Search location (Enter)..." autocomplete="off"/>
    <div id="searchResultsList" style="display:flex; flex-direction:column; gap:4px; max-height:200px; overflow-y:auto;"></div>
</div>

<div id="popup-marker-settings" class="float-card right-card">
    <div style="font-weight:700; color:var(--text-main);">Marker Pin Configuration</div>
    <div class="icon-grid" id="markerIconGrid"></div>
    <div class="f-row">
        <span>Size Mode</span>
        <select id="mSizeMode" style="width:110px;">
            <option value="dynamic" selected>Dynamic (Zoom)</option>
            <option value="static">Static (Fixed)</option>
        </select>
    </div>
    <div class="f-row"><span>Icon Size</span> <input type="range" id="mSize" min="0.4" max="2.0" step="0.1" value="0.9"></div>
    <div id="mColorCtrl" class="color-ctrl-cluster"></div>
</div>

<div id="popup-text-settings" class="float-card right-card">
    <div style="font-weight:700; color:var(--text-main);">Textbox Configuration</div>
    <input type="text" id="tContent" value="Custom Label" placeholder="Text content…"/>
    <div class="f-row"><span>Font Size</span> <input type="range" id="tSize" min="10" max="42" step="1" value="16"></div>
    <div id="tColorCtrl" class="color-ctrl-cluster"></div>
</div>

<div id="popup-route-mode-choice" class="float-card">
    <div style="font-weight:700; color:var(--text-main); margin-bottom:4px;">Choose Route Creation Mode</div>
    <div style="display:flex; gap:8px;">
        <button id="btnChooseManualRoute" class="trade-btn" style="flex:1;">Manual Draw</button>
        <button id="btnChooseDirectionsRoute" class="trade-btn" style="flex:1; background:#1e40af;">Directions (Search)</button>
    </div>
</div>

<!-- Enhanced Shape Editor -->
<div id="popup-shape-editor" class="float-card right-card">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-weight:700; color:var(--text-main);" id="editShapeTitle">Edit Feature</span>
        <button class="card-btn" id="closeEditorBtn">✕</button>
    </div>
    <div class="f-row"><span>Name</span> <input type="text" id="eName" style="width:140px;"></div>
    
    <!-- 3D Polygon Specifics -->
    <div id="editor-3d-section" style="display:none; border-top:1px solid rgba(255,255,255,0.1); padding-top:6px; flex-direction:column; gap:6px;">
        <div class="f-row"><span>3D Extrusion</span> <input type="checkbox" id="eIs3D"></div>
        <div class="f-row"><span>Height (m)</span> <input type="range" id="eHeight" min="1" max="200" step="1" value="20"><span id="eHeightVal">20m</span></div>
        <div class="f-row"><span>Base Height (m)</span> <input type="range" id="eBaseHeight" min="0" max="100" step="1" value="0"><span id="eBaseHeightVal">0m</span></div>
    </div>

    <!-- Route Specifics -->
    <div id="editor-route-section" style="display:none; border-top:1px solid rgba(255,255,255,0.1); padding-top:6px; flex-direction:column; gap:6px;">
        <div class="f-row"><span>Route Mode</span>
            <select id="eRouteMode" style="width:110px;">
                <option value="driving">Driving</option>
                <option value="walking">Walking</option>
                <option value="cycling">Cycling</option>
            </select>
        </div>
        <div class="f-row"><span>Stats</span> <span id="eRouteStats" style="font-weight:700; color:var(--sky);">-</span></div>
        <div id="eDirectionsBox" style="display:none; flex-direction:column; gap:4px;">
            <div style="font-weight:600; font-size:10px; color:#768390;">STOPS / DIRECTIONS</div>
            <div id="eStopsList" style="display:flex; flex-direction:column; gap:4px;"></div>
            <div style="display:flex; gap:4px; margin-top:4px;">
                <input type="text" id="eAddStopInput" placeholder="Add stop address..." style="flex:1;"/>
                <button id="eBtnAddStop" class="trade-btn" style="padding:4px 8px;">Add</button>
            </div>
        </div>
        <button id="eRecalcRoute" class="trade-btn" style="width:100%; font-size:10px; margin-top:4px;">Recalculate Route</button>
    </div>

    <!-- Circle Specifics -->
    <div id="editor-circle-section" style="display:none;" class="f-row">
        <span>Radius</span> <span id="eCircleRadiusVal" style="font-weight:700; color:var(--sky);">-</span>
    </div>

    <!-- Image Overlay Specifics -->
    <div id="editor-image-section" style="display:none; flex-direction:column; gap:6px;">
        <div class="f-row"><span>Image Opacity</span> <input type="range" id="eImgOpacity" min="0.1" max="1" step="0.05" value="0.85"></div>
        <button id="eResetImgSize" class="trade-btn" style="font-size:10px;">Reset Aspect Ratio</button>
    </div>

    <!-- Standard Styling -->
    <div id="eBorderColorRowContainer" class="f-row" style="flex-direction:column; align-items:stretch;">
        <span style="font-size:11px; margin-bottom:2px;">Border / Line Color</span>
        <div id="eBorderColorCtrl" class="color-ctrl-cluster"></div>
    </div>
    <div class="f-row" id="eBorderOpRow"><span>Border Opacity</span> <input type="range" id="eBorderOp" min="0" max="1" step="0.05"></div>
    <div class="f-row" id="eWidthRow"><span>Width / Thickness</span> <input type="range" id="eWidth" min="1" max="16" step="1"></div>
    <div id="eFillColorRowContainer" class="f-row" style="flex-direction:column; align-items:stretch;">
        <span style="font-size:11px; margin-bottom:2px;">Fill Color</span>
        <div id="eFillColorCtrl" class="color-ctrl-cluster"></div>
    </div>
    <div class="f-row" id="eFillOpRow"><span>Fill Opacity</span> <input type="range" id="eFillOp" min="0" max="1" step="0.05"></div>
    
    <div class="f-row" id="eLabelToggleRow"><span>Show Label</span> <input type="checkbox" id="eShowLabel"></div>
    <div class="f-row" id="eLabelPosRow"><span>Label Position</span>
        <select id="eLabelPos" style="width:110px;">
            <option value="center">Center</option>
            <option value="top">Top</option>
            <option value="bottom">Bottom</option>
            <option value="left">Left</option>
            <option value="right">Right</option>
        </select>
    </div>
    
    <div class="f-row" id="eMarkerSizeRow" style="display:none;"><span>Icon Size</span> <input type="range" id="eMarkerSize" min="0.4" max="2.0" step="0.1"></div>
    <div class="f-row" id="eTextRow" style="display:none;"><span>Text</span> <input type="text" id="eTextVal" style="width:140px;"></div>
    <div class="f-row" id="eFontSizeRow" style="display:none;"><span>Font Size</span> <input type="range" id="eFontSize" min="10" max="42" step="1"></div>
    
    <div style="display:flex; justify-content:space-between; margin-top:8px;">
        <button id="eDeleteBtn" style="color:var(--danger); border:1px solid #da36334d; background:#da36331a; padding:6px 12px; border-radius:6px; cursor:pointer;">Delete</button>
        <button id="eDoneBtn" style="background:var(--accent); color:#fff; border:none; padding:6px 16px; border-radius:6px; cursor:pointer;">Done</button>
    </div>
</div>

<!-- Basemap Customizer Panel -->
<div id="popup-custom-map" class="float-card right-card">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-weight:700; color:var(--text-main);">Basemap & Styles</span>
        <button class="card-btn" id="closeCustomMapBtn">✕</button>
    </div>
    <div style="font-weight:600; font-size:11px; color:#768390; margin-top:4px;">BASEMAP PRESETS</div>
    <div style="display:flex; flex-wrap:wrap; gap:4px;" id="presetBtnList"></div>
    <div style="font-weight:600; font-size:11px; color:#768390; margin-top:6px;">BACKGROUND</div>
    <div id="cBgColorCtrl" class="color-ctrl-cluster"></div>
    <div style="font-weight:600; font-size:11px; color:#768390; margin-top:6px;">ROADS & BUILDINGS</div>
    <div id="cMainColorCtrl" class="color-ctrl-cluster"></div>
    <div id="cBldColorCtrl" class="color-ctrl-cluster"></div>
</div>

<!-- Trade Area Modal -->
<div id="trade-area-modal" style="position: fixed; inset: 0; z-index: 2000; display: none; align-items: center; justify-content: center; background-color: rgba(0,0,0,0.65);">
    <div class="float-card open" style="width:480px; max-width:92vw; max-height:85vh; padding:16px;">
        <div class="panel-header">
            <div class="panel-title"><span>Trade Area Analysis</span></div>
            <button class="card-btn" id="closeTradeAreaBtn">✕</button>
        </div>
        <div class="f-row"><span>Target Polygon</span>
            <select id="tradePolygonSelect" style="width:170px;"><option value="">-- Choose --</option></select>
        </div>
        <div style="font-weight:600; font-size:11px; color:#768390;">POI TAXONOMY</div>
        <div id="poiCategoryCheckboxes" style="max-height:200px; overflow-y:auto; display:flex; flex-direction:column; gap:6px;"></div>
        <input type="text" id="customPoiSearchInput" placeholder="Custom tag e.g. amenity=dentist" style="width:100%; margin-top:4px;"/>
        <button class="trade-btn" id="btnScanTradeArea" style="margin-top:8px;">Scan POIs</button>
        <div id="tradeResults" class="poi-summary"></div>
    </div>
</div>

<!-- Attribute Table Modal (#popup-attribute-table, excludes name) -->
<div id="popup-attribute-table" class="float-card">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
        <span style="font-weight:700; color:var(--text-main);" id="attrTableTitle">Attribute Table</span>
        <button class="card-btn" id="closeAttrTableBtn">✕</button>
    </div>
    <div style="display:flex; gap:8px; margin-bottom:8px; align-items:center;">
        <input type="text" id="attrTableSearch" placeholder="Find in table..." style="flex:1;"/>
        <button id="btnAddAttrCol" class="trade-btn" style="padding:6px 10px; font-size:10px;">+ Add Column</button>
        <button id="btnAddAttrRow" class="trade-btn" style="padding:6px 10px; font-size:10px; background:#22272e;">+ Add Row</button>
    </div>
    <div class="attr-table-container">
        <table class="attr-table">
            <thead id="attrTableHeader"></thead>
            <tbody id="attrTableBody"></tbody>
        </table>
    </div>
</div>

<!-- Context Menu -->
<div id="map-context-menu">
    <div class="ctx-coords" id="ctx-coords-label">0.000000, 0.000000</div>
    <div class="ctx-item" id="ctx-edit" style="display:none;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4v16h16v-7"></path><path d="M18 2l4 4-10 10H8v-4z"></path></svg>
        Edit Shape & Height
    </div>
    <div class="ctx-item" id="ctx-datatable" style="display:none;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>
        Open Data Table
    </div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" id="ctx-z-front"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="18 15 12 9 6 15"></polyline></svg>Bring to Front</div>
    <div class="ctx-item" id="ctx-z-forward"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="18 12 12 6 6 12"></polyline></svg>Bring Forward</div>
    <div class="ctx-item" id="ctx-z-backward"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 12 12 18 18 12"></polyline></svg>Send Backward</div>
    <div class="ctx-item" id="ctx-z-back"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>Send to Back</div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" id="ctx-copy"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>Copy Coordinates</div>
    <div class="ctx-item" id="ctx-gmaps"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"></path></svg>Open in Google Maps</div>
    <div class="ctx-item" id="ctx-streetview"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>Open in Streetview</div>
    <div class="ctx-item" id="ctx-delete" style="display:none; color:var(--danger);"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>Delete Feature</div>
</div>

<!-- Project Launcher Modal -->
<div id="launcher-modal-scrim" class="visible">
    <div class="ios26-card">
        <div class="ios26-header">
            <div class="ios26-title">Project Atlas</div>
            <div class="ios26-subtitle">Select or initialize your spatial workspace.</div>
        </div>
        <div class="ios26-seg">
            <button class="ios26-seg-btn active" id="seg-btn-existing">Existing Projects</button>
            <button class="ios26-seg-btn" id="seg-btn-new">Create New</button>
        </div>
        <div class="ios26-body" id="seg-content-existing">
            <div id="existing-projects-container" style="display:flex; flex-direction:column; gap:8px;"></div>
        </div>
        <div class="ios26-body" id="seg-content-new" style="display:none;">
            <div class="ios26-input-group">
                <label class="ios26-label">Project Name</label>
                <input class="ios26-input" id="new-proj-name" placeholder="e.g. Untitled Project 1"/>
            </div>
            <button class="ios26-action-btn" id="btn-create-project-submit" style="margin-top:4px;">Initialize Workspace</button>
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

// 3D by default: pitch 60
const map = new maplibregl.Map({
    container: 'map',
    style: ALL_STYLES[currentStyleName] || ALL_STYLES["Midnight Blue"],
    center: __CENTER__,
    zoom: __ZOOM__,
    pitch: 60,
    bearing: -15,
    attributionControl: false,
    preserveDrawingBuffer: true
});
map.getCanvas().addEventListener('contextmenu', e => e.preventDefault());

let is3DModeActive = true;
let features = __INITIAL_FEATURES__;
let fid = features.reduce((max, f) => Math.max(max, f.id || 0), 0);
let customGroups = __INITIAL_CUSTOM_GROUPS__ || {"Trade Area Scan": {collapsed: false, ids: []}};

let activeTool = null, editMode = false, selectedId = null;
let draft = [], cursorLL = null;
let markerShape = 'pin', markerColor = '#1e40af', markerIconSize = 0.9, markerSizeMode = 'dynamic';
let selectedLayerIds = new Set();
let isDirty = false;
let undoStack = [], redoStack = [];

let isDragging = false, dragFeatureId = null, dragStartCoord = null, dragOriginalCoords = null;
let isDraggingVertex = false, draggedVertexIdx = -1, draggedPolyId = null, isRadiusHandle = false;
let isDraggingRotation = false, rotatingPolyId = null, rotCenter = null, rotStartAngle = 0;
let isDraggingHeight = false, heightPolyId = null, heightStartScreenY = 0, heightStartVal = 20;

let ctxLngLat = null, ctxFeatureId = null;
let currentTableFeatureId = null;
let rerouteTimeout = null;

const $ = id => document.getElementById(id);
const hint = t => { $('hint-toast').style.display = t ? 'block' : 'none'; $('hint-toast').textContent = t || ''; };

function pushState() {
    undoStack.push(JSON.stringify({ features, customGroups }));
    if (undoStack.length > 50) undoStack.shift();
    redoStack = [];
}
const markDirty = (record = true) => {
    if (record) pushState();
    isDirty = true;
    setSaveBadgeStatus('unsaved');
};

const setSaveBadgeStatus = status => {
    const badge = $('save-status-badge');
    const text = $('save-text');
    badge.className = 'save-badge ' + status;
    text.textContent = status === 'saving' ? 'Saving...' : (status === 'saved' ? 'Saved' : 'Unsaved');
};

const undo = () => {
    if (!undoStack.length) return;
    redoStack.push(JSON.stringify({ features, customGroups }));
    const prev = JSON.parse(undoStack.pop());
    features = prev.features; customGroups = prev.customGroups;
    syncDraw(); renderMyLayers(); markDirty(false);
};
const redo = () => {
    if (!redoStack.length) return;
    undoStack.push(JSON.stringify({ features, customGroups }));
    const next = JSON.parse(redoStack.pop());
    features = next.features; customGroups = next.customGroups;
    syncDraw(); renderMyLayers(); markDirty(false);
};

const closeFloatingCards = () => {
    ['popup-marker-settings','popup-text-settings','popup-shape-editor','popup-custom-map','popup-search','popup-route-mode-choice','browser-panel','mylayers-panel','popup-attribute-table'].forEach(id => {
        const el = $(id); if (el) el.classList.remove('open');
    });
    $('trade-area-modal').style.display = 'none';
    $('map-context-menu').style.display = 'none';
};

const resetActiveTools = () => {
    activeTool = null; draft = []; renderDraft();
    document.querySelectorAll('.tool').forEach(b => b.classList.remove('primary-active'));
    map.getCanvas().style.cursor = '';
    map.doubleClickZoom.enable();
    hint('');
};

// ----------------- Unified Edit Mode Entrypoint -----------------
function enableEditMode(featureId) {
    const f = features.find(x => x.id === featureId);
    if (!f) return;
    editMode = true;
    selectedId = featureId;
    openShapeEditor(featureId);
    syncVertexHandles();
    hint('Edit Mode active: Drag shape, edit vertices, adjust height, or rotate via ↻ handle');
}

// ----------------- Rotation Handle with SVG ⟳ Icon -----------------
function registerRotationHandleImage() {
    const cv = document.createElement('canvas');
    cv.width = 36; cv.height = 36;
    const ctx = cv.getContext('2d');
    ctx.fillStyle = '#e8b84a';
    ctx.beginPath(); ctx.arc(18, 18, 14, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 2; ctx.stroke();
    ctx.fillStyle = '#0a1628'; ctx.font = 'bold 16px sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('↻', 18, 18);
    map.addImage('rot-handle-icon', ctx.getImageData(0, 0, 36, 36), { pixelRatio: 2 });
}

// ----------------- Color Picker Setup -----------------
function setupColorPicker(containerId, initialColor, onColorChange) {
    const el = $(containerId);
    if (!el) return;
    let paletteRows = COLOR_PALETTES.map(p => `
        <div class="palette-group">
            <span class="palette-label">${p.name}</span>
            <div class="swatch-row">
                ${p.colors.map(hex => `<div class="swatch" data-color="${hex}" style="background:${hex};" title="${hex}"></div>`).join('')}
            </div>
        </div>
    `).join('');
    el.innerHTML = `
        ${paletteRows}
        <div class="color-input-combo">
            <input type="color" class="native-color" value="${initialColor}">
            <input type="text" class="hex-text" value="${initialColor}" placeholder="#hex">
            <button class="btn-eyedropper" title="Pick color">
                <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 11l-8-8-8.5 8.5a2.12 2.12 0 0 0 0 3l2.83 2.83a2.12 2.12 0 0 0 3 0L19 11z"></path></svg>
            </button>
        </div>
    `;
    const nativeColor = el.querySelector('.native-color');
    const hexText = el.querySelector('.hex-text');
    const updateAll = col => { nativeColor.value = col; hexText.value = col; onColorChange(col); };
    el.querySelectorAll('.swatch').forEach(sw => sw.onclick = () => updateAll(sw.dataset.color));
    nativeColor.oninput = e => updateAll(e.target.value);
    hexText.onchange = e => {
        let val = e.target.value.trim();
        if (!val.startsWith('#')) val = '#' + val;
        if (/^#[0-9A-Fa-f]{6}$/.test(val)) updateAll(val);
    };
    el.querySelector('.btn-eyedropper').onclick = async () => {
        if (window.EyeDropper) {
            try { const res = await new EyeDropper().open(); if (res && res.sRGBHex) updateAll(res.sRGBHex); } catch(e){}
        }
    };
}

// ----------------- Map Layers Pipeline (2D/3D Dual Layering) -----------------
const collectFeatures = () => {
    return features.map(f => ({
        id: f.id,
        name: f.name,
        kind: f.kind,
        geometry: f.geometry,
        props: { ...f.props }
    }));
};

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

        // 3D Extrusion Layer
        map.addLayer({
            id: 'draw-fill-extrusion', type: 'fill-extrusion', source: 'draw',
            filter: ['all', ['==', ['geometry-type'], 'Polygon'], ['==', ['get', 'is3D'], true]],
            paint: {
                'fill-extrusion-color': ['coalesce', ['get', 'fillColor'], ['get', 'color'], '#e8b84a'],
                'fill-extrusion-height': ['coalesce', ['get', 'height'], 20],
                'fill-extrusion-base': ['coalesce', ['get', 'baseHeight'], 0],
                'fill-extrusion-opacity': ['*', ['coalesce', ['get', 'fillOpacity'], 0.85], ['get', 'visible']]
            }
        });

        // 2D Fallback / 2D Flat Layer
        map.addLayer({
            id: 'draw-fill', type: 'fill', source: 'draw',
            filter: ['all', ['==', ['geometry-type'], 'Polygon'], ['!=', ['get', 'is3D'], true]],
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
                'line-opacity': ['*', ['coalesce', ['get', 'borderOpacity'], 0.9], ['get', 'visible']]
            }
        });

        map.addLayer({
            id: 'draw-marker', type: 'symbol', source: 'draw',
            filter: ['all', ['==', ['geometry-type'], 'Point'], ['!=', ['get', 'kind'], 'text']],
            layout: {
                'icon-image': ['get', 'iconKey'],
                'icon-size': ['case', ['==', ['get', 'sizeMode'], 'static'], ['coalesce', ['get', 'iconSize'], 0.9], ['interpolate', ['linear'], ['zoom'], 10, ['*', 0.5, ['coalesce', ['get', 'iconSize'], 0.9]], 18, ['*', 1.8, ['coalesce', ['get', 'iconSize'], 0.9]]]],
                'icon-allow-overlap': true, 'icon-anchor': 'bottom'
            },
            paint: { 'icon-opacity': ['get', 'visible'] }
        });

        map.addLayer({
            id: 'draw-text', type: 'symbol', source: 'draw',
            filter: ['all', ['==', ['geometry-type'], 'Point'], ['==', ['get', 'kind'], 'text']],
            layout: {
                'text-field': ['get', 'text'], 'text-font': ['Noto Sans Regular'],
                'text-size': ['coalesce', ['get', 'fontSize'], 16], 'text-allow-overlap': true, 'text-anchor': 'center'
            },
            paint: { 'text-color': ['coalesce', ['get', 'color'], '#d9b451'], 'text-opacity': ['*', ['coalesce', ['get', 'opacity'], 1], ['get', 'visible']], 'text-halo-color': '#0a1628', 'text-halo-width': 2 }
        });

        map.addSource('label-src', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
        map.addLayer({
            id: 'draw-poly-labels', type: 'symbol', source: 'label-src',
            layout: { 'text-field': ['get', 'labelText'], 'text-font': ['Noto Sans Regular'], 'text-size': 12, 'text-allow-overlap': true, 'text-anchor': 'center' },
            paint: { 'text-color': '#ffffff', 'text-halo-color': '#0a1628', 'text-halo-width': 2 }
        });
    } else {
        map.getSource('draw').setData(fc(features));
    }

    if (!map.getSource('draft')) {
        map.addSource('draft', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
        map.addLayer({ id: 'draft-line', type: 'line', source: 'draft', filter: ['==', ['geometry-type'], 'LineString'], paint: { 'line-color': '#38bdf8', 'line-width': 2.5, 'line-dasharray': [2, 2] } });
        map.addLayer({ id: 'draft-point', type: 'circle', source: 'draft', filter: ['==', ['geometry-type'], 'Point'], paint: { 'circle-color': '#38bdf8', 'circle-radius': 6, 'circle-stroke-width': 2, 'circle-stroke-color': '#ffffff' } });
    }

    if (!map.getSource('vertex-handles')) {
        map.addSource('vertex-handles', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
        map.addLayer({
            id: 'vertex-points', type: 'circle', source: 'vertex-handles',
            filter: ['!=', ['get', 'isRotHandle'], true],
            paint: {
                'circle-color': ['case', ['boolean', ['get', 'isHeightHandle'], false], '#f59e0b', ['case', ['boolean', ['get', 'isRadiusHandle'], false], '#3fb950', '#38bdf8']],
                'circle-radius': 6, 'circle-stroke-color': '#ffffff', 'circle-stroke-width': 2
            }
        });
        map.addLayer({
            id: 'vertex-rot-symbol', type: 'symbol', source: 'vertex-handles',
            filter: ['==', ['get', 'isRotHandle'], true],
            layout: { 'icon-image': 'rot-handle-icon', 'icon-size': 0.8, 'icon-allow-overlap': true }
        });
    }
}

function syncDraw() {
    if (map.getSource('draw')) map.getSource('draw').setData(fc(features));
    syncVertexHandles();
    syncLabels();
}

function syncLabels() {
    const src = map.getSource('label-src');
    if (!src) return;
    const feats = [];
    features.forEach(f => {
        if (!f.props.showLabel || f.props.visible === 0) return;
        let labelText = f.name;
        if (f.kind === 'route' && f.props.metadata) {
            const d = f.props.metadata.distance;
            labelText = `${d > 1000 ? (d/1000).toFixed(2)+' km' : Math.round(d)+' m'}`;
        }
        const b = calcBounds(f);
        if (!b) return;
        const cx = (b[0][0] + b[1][0]) / 2, cy = (b[0][1] + b[1][1]) / 2;
        feats.push({ type: 'Feature', geometry: { type: 'Point', coordinates: [cx, cy] }, properties: { labelText } });
    });
    src.setData({ type: 'FeatureCollection', features: feats });
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
        if (f.kind === 'circle' && f.props.centerCoord && f.props.radiusMeters) {
            const c = f.props.centerCoord, r = f.props.radiusMeters;
            handleFeats.push({
                type: 'Feature', geometry: { type: 'Point', coordinates: [c[0] + (r / (111320 * Math.cos(c[1]*Math.PI/180))), c[1]] },
                properties: { polyId: f.id, isRadiusHandle: true }
            });
        } else if (['polygon', 'rectangle', 'polygon3d'].includes(f.kind) && f.geometry.coordinates[0]) {
            f.geometry.coordinates[0].slice(0, -1).forEach((pt, i) => {
                handleFeats.push({ type: 'Feature', geometry: { type: 'Point', coordinates: pt }, properties: { polyId: f.id, vIdx: i } });
            });
        } else if ((f.kind === 'polyline' || f.kind === 'route') && f.geometry.coordinates) {
            const pts = f.props.waypoints || f.geometry.coordinates;
            pts.forEach((pt, i) => {
                handleFeats.push({ type: 'Feature', geometry: { type: 'Point', coordinates: pt }, properties: { polyId: f.id, vIdx: i } });
            });
        }
        const b = calcBounds(f);
        if (b) {
            const cx = (b[0][0] + b[1][0]) / 2, cy = (b[0][1] + b[1][1]) / 2;
            const offset = (b[1][1] - b[0][1]) * 0.25 || 0.001;
            handleFeats.push({ type: 'Feature', geometry: { type: 'Point', coordinates: [cx, b[1][1] + offset] }, properties: { polyId: f.id, isRotHandle: true } });
            if (f.props.is3D) {
                handleFeats.push({ type: 'Feature', geometry: { type: 'Point', coordinates: [cx, cy] }, properties: { polyId: f.id, isHeightHandle: true } });
            }
        }
    }
    map.getSource('vertex-handles').setData({ type: 'FeatureCollection', features: handleFeats });
}

// ----------------- Dimension Toggle Functionality -----------------
function toggle3DMode(enable3D) {
    is3DModeActive = enable3D;
    $('btn3DMode').classList.toggle('active', enable3D);
    $('btn2DMode').classList.toggle('active', !enable3D);
    if (map.getLayer('building-2d')) map.setLayoutProperty('building-2d', 'visibility', enable3D ? 'none' : 'visible');
    if (map.getLayer('building-3d')) map.setLayoutProperty('building-3d', 'visibility', enable3D ? 'visible' : 'none');
    if (map.getLayer('draw-fill-extrusion')) map.setLayoutProperty('draw-fill-extrusion', 'visibility', enable3D ? 'visible' : 'none');
    map.easeTo({ pitch: enable3D ? 60 : 0, bearing: enable3D ? -15 : 0 });
    markDirty();
}

$('btn2DMode').onclick = () => toggle3DMode(false);
$('btn3DMode').onclick = () => toggle3DMode(true);

// ----------------- Z-Index Ordering Function -----------------
function reorderLayer(featureId, action) {
    const idx = features.findIndex(x => x.id === featureId);
    if (idx === -1) return;
    const [item] = features.splice(idx, 1);
    if (action === 'front') features.push(item);
    else if (action === 'back') features.unshift(item);
    else if (action === 'forward') features.splice(Math.min(features.length, idx + 1), 0, item);
    else if (action === 'backward') features.splice(Math.max(0, idx - 1), 0, item);
    syncDraw(); renderMyLayers(); markDirty();
}

$('ctx-z-front').onclick = () => { if (ctxFeatureId) reorderLayer(ctxFeatureId, 'front'); $('map-context-menu').style.display='none'; };
$('ctx-z-forward').onclick = () => { if (ctxFeatureId) reorderLayer(ctxFeatureId, 'forward'); $('map-context-menu').style.display='none'; };
$('ctx-z-backward').onclick = () => { if (ctxFeatureId) reorderLayer(ctxFeatureId, 'backward'); $('map-context-menu').style.display='none'; };
$('ctx-z-back').onclick = () => { if (ctxFeatureId) reorderLayer(ctxFeatureId, 'back'); $('map-context-menu').style.display='none'; };

// ----------------- Feature Popup on Left-Click -----------------
function showFeaturePopup(f, clickLngLat) {
    const coords = clickLngLat || [(calcBounds(f)[0][0] + calcBounds(f)[1][0])/2, (calcBounds(f)[0][1] + calcBounds(f)[1][1])/2];
    let imgHtml = '';
    if (f.props.primaryPhoto) {
        imgHtml = `<img src="${f.props.primaryPhoto}" style="width:100%; max-height:140px; object-fit:cover; border-radius:6px; margin:6px 0;"/>`;
    }
    let tagRows = '';
    if (f.props.is3D) {
        tagRows += `<tr><th>Height</th><td>${f.props.height || 20}m (Base: ${f.props.baseHeight || 0}m)</td></tr>`;
    }
    if (f.props.osmTags) {
        Object.keys(f.props.osmTags).forEach(k => tagRows += `<tr><th>${k}</th><td>${f.props.osmTags[k]}</td></tr>`);
    } else if (f.props.attributes) {
        Object.keys(f.props.attributes).forEach(k => tagRows += `<tr><th>${k}</th><td>${f.props.attributes[k]}</td></tr>`);
    }
    const html = `
        <div style="font-weight:700; color:var(--sky); font-size:13px;">${f.name}</div>
        ${imgHtml}
        <table class="tag-table">${tagRows || '<tr><th>Type</th><td>'+f.kind+'</td></tr>'}</table>
        <div style="display:flex; justify-content:flex-end; gap:6px; margin-top:8px; border-top:1px solid rgba(255,255,255,0.08); padding-top:6px;">
            <button onclick="enableEditMode(${f.id})" style="background:var(--accent); color:#fff; border:none; border-radius:4px; padding:3px 8px; font-size:10px; cursor:pointer;">Edit</button>
            <button onclick="openAttributeTable(${f.id})" style="background:rgba(255,255,255,0.1); color:var(--text-muted); border:1px solid rgba(255,255,255,0.1); border-radius:4px; padding:3px 8px; font-size:10px; cursor:pointer;">Open Table</button>
        </div>
    `;
    new maplibregl.Popup({ maxWidth: '320px' }).setLngLat(coords).setHTML(html).addTo(map);
}

// ----------------- Context Menu Trigger -----------------
map.on('contextmenu', e => {
    ctxLngLat = e.lngLat;
    const fs = map.queryRenderedFeatures(e.point, { layers: ['draw-fill','draw-fill-extrusion','draw-line','draw-outline','draw-marker','draw-text'] });
    ctxFeatureId = fs.length && fs[0].properties.id != null ? parseInt(fs[0].properties.id, 10) : null;
    $('ctx-coords-label').textContent = `${e.lngLat.lat.toFixed(6)}, ${e.lngLat.lng.toFixed(6)}`;
    
    ['ctx-edit','ctx-datatable','ctx-delete','ctx-z-front','ctx-z-forward','ctx-z-backward','ctx-z-back'].forEach(id => {
        $(id).style.display = ctxFeatureId ? 'flex' : 'none';
    });
    const menu = $('map-context-menu');
    menu.style.left = Math.min(e.point.x, window.innerWidth - 230) + 'px';
    menu.style.top = Math.min(e.point.y, window.innerHeight - 260) + 'px';
    menu.style.display = 'block';
});
map.on('movestart', () => $('map-context-menu').style.display = 'none');

$('ctx-edit').onclick = () => { if (ctxFeatureId) enableEditMode(ctxFeatureId); $('map-context-menu').style.display='none'; };
$('ctx-datatable').onclick = () => { if (ctxFeatureId) openAttributeTable(ctxFeatureId); $('map-context-menu').style.display='none'; };
$('ctx-delete').onclick = () => {
    if (ctxFeatureId) {
        features = features.filter(x => x.id !== ctxFeatureId);
        syncDraw(); renderMyLayers(); markDirty();
    }
    $('map-context-menu').style.display='none';
};
$('ctx-copy').onclick = () => {
    if (ctxLngLat) navigator.clipboard.writeText(`${ctxLngLat.lat.toFixed(6)}, ${ctxLngLat.lng.toFixed(6)}`);
    $('map-context-menu').style.display='none';
};
$('ctx-gmaps').onclick = () => { if (ctxLngLat) window.open(`https://www.google.com/maps?q=${ctxLngLat.lat},${ctxLngLat.lng}`, '_blank'); $('map-context-menu').style.display='none'; };
$('ctx-streetview').onclick = () => { if (ctxLngLat) window.open(`https://www.google.com/maps/@${ctxLngLat.lat},${ctxLngLat.lng},3a,75y,90t/data=!3m6!1e1!3m4!1s!2e0!7i13312!8i6656`, '_blank'); $('map-context-menu').style.display='none'; };

// ----------------- My Layers Event Delegation -----------------
function renderMyLayers() {
    const container = $('my-layers-list');
    $('layer-badge-count').textContent = features.length;
    const polyList = features.filter(f => ['polygon', 'rectangle', 'circle', 'polygon3d'].includes(f.kind));
    $('tradePolygonSelect').innerHTML = '<option value="">-- Choose --</option>' + polyList.map(p => `<option value="${p.id}">${p.name}</option>`).join('');

    let html = '';
    const groupedIds = new Set();
    for (const gName in customGroups) {
        const grp = customGroups[gName];
        const groupFeats = features.filter(f => grp.ids.includes(f.id));
        grp.ids.forEach(id => groupedIds.add(id));
        html += `
            <div class="group-container" data-group="${gName}">
                <div class="group-header">
                    <input class="group-title-input" data-oldname="${gName}" value="${gName}"/>
                    <div style="display:flex; gap:2px;">
                        <button class="card-btn" data-act="groupEye" data-group="${gName}" title="Toggle Group Visibility"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path></svg></button>
                        <button class="card-btn" data-act="groupDel" data-group="${gName}" title="Delete Group" style="color:var(--danger);"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg></button>
                    </div>
                </div>
                <div class="group-items ${grp.collapsed ? 'hidden' : ''}">
                    ${groupFeats.map(f => renderLayerCardHtml(f)).join('')}
                </div>
            </div>
        `;
    }
    const looseFeats = features.filter(f => !groupedIds.has(f.id));
    html += `<div id="ungrouped-zone">${looseFeats.map(f => renderLayerCardHtml(f)).join('')}</div>`;
    container.innerHTML = html;
}

function renderLayerCardHtml(f) {
    const isSel = selectedLayerIds.has(f.id);
    const sub = f.kind === 'polygon3d' ? `3D (${f.props.height || 20}m)` : f.kind;
    return `
        <div class="layer-card" draggable="true" data-id="${f.id}">
            <div class="layer-card-top">
                <input type="checkbox" class="layer-select-check" data-id="${f.id}" ${isSel ? 'checked' : ''}/>
                <input class="layer-name-input" data-id="${f.id}" value="${f.name}"/>
                <button class="card-btn" data-act="table" data-id="${f.id}" title="Data Table"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg></button>
                <button class="card-btn" data-act="eye" data-id="${f.id}" title="Toggle View"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path></svg></button>
                <button class="card-btn" data-act="zoom" data-id="${f.id}" title="Zoom"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg></button>
                <button class="card-btn" data-act="del" data-id="${f.id}" title="Delete" style="color:var(--danger);"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg></button>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:10px; color:#768390; padding:0 4px;">
                <span>${sub}</span>
                <label style="display:flex; align-items:center; gap:2px;"><input type="checkbox" data-act="labelToggle" data-id="${f.id}" ${f.props.showLabel ? 'checked' : ''}/> Label</label>
            </div>
        </div>
    `;
}

// Single Event Delegation Listener for My Layers
$('my-layers-list').addEventListener('click', e => {
    const btn = e.target.closest('[data-act]');
    if (!btn) return;
    const act = btn.dataset.act;
    const id = parseInt(btn.dataset.id, 10);
    const f = features.find(x => x.id === id);
    if (act === 'table' && f) openAttributeTable(id);
    else if (act === 'eye' && f) { f.props.visible = f.props.visible ? 0 : 1; syncDraw(); renderMyLayers(); markDirty(); }
    else if (act === 'del' && f) { features = features.filter(x => x.id !== id); syncDraw(); renderMyLayers(); markDirty(); }
    else if (act === 'zoom' && f) { const b = calcBounds(f); if (b) map.fitBounds(b, { padding: 60 }); }
    else if (act === 'groupEye') {
        const g = btn.dataset.group;
        const gIds = customGroups[g].ids;
        const anyVis = features.some(x => gIds.includes(x.id) && x.props.visible);
        features.forEach(x => { if (gIds.includes(x.id)) x.props.visible = anyVis ? 0 : 1; });
        syncDraw(); renderMyLayers(); markDirty();
    }
    else if (act === 'groupDel') {
        delete customGroups[btn.dataset.group];
        renderMyLayers(); markDirty();
    }
});

$('my-layers-list').addEventListener('change', e => {
    const t = e.target;
    if (t.classList.contains('layer-select-check')) {
        const id = parseInt(t.dataset.id, 10);
        if (t.checked) selectedLayerIds.add(id); else selectedLayerIds.delete(id);
    } else if (t.classList.contains('layer-name-input')) {
        const f = features.find(x => x.id === parseInt(t.dataset.id, 10));
        if (f) { f.name = t.value; syncDraw(); markDirty(); }
    } else if (t.dataset.act === 'labelToggle') {
        const f = features.find(x => x.id === parseInt(t.dataset.id, 10));
        if (f) { f.props.showLabel = t.checked; syncDraw(); markDirty(); }
    }
});

// Multi-Drag and Drop Delegation
let draggedIds = [];
$('my-layers-list').addEventListener('dragstart', e => {
    const card = e.target.closest('.layer-card');
    if (!card) return;
    const cardId = parseInt(card.dataset.id, 10);
    draggedIds = selectedLayerIds.has(cardId) ? Array.from(selectedLayerIds) : [cardId];
    e.dataTransfer.setData('text/plain', JSON.stringify(draggedIds));
});

$('my-layers-list').addEventListener('dragover', e => e.preventDefault());
$('my-layers-list').addEventListener('drop', e => {
    e.preventDefault();
    const gContainer = e.target.closest('.group-container');
    if (gContainer) {
        const gName = gContainer.dataset.group;
        draggedIds.forEach(id => {
            for (const g in customGroups) customGroups[g].ids = customGroups[g].ids.filter(x => x !== id);
            if (!customGroups[gName].ids.includes(id)) customGroups[gName].ids.push(id);
        });
        renderMyLayers(); markDirty();
    }
});

// Top action buttons
$('btnSelectAllGlobal').onclick = () => {
    if (selectedLayerIds.size === features.length) selectedLayerIds.clear();
    else features.forEach(f => selectedLayerIds.add(f.id));
    renderMyLayers();
};
$('btnDeleteSelectedGlobal').onclick = () => {
    if (!selectedLayerIds.size) return;
    features = features.filter(f => !selectedLayerIds.has(f.id));
    for (const g in customGroups) customGroups[g].ids = customGroups[g].ids.filter(id => !selectedLayerIds.has(id));
    selectedLayerIds.clear();
    syncDraw(); renderMyLayers(); markDirty();
};
$('btnAddCustomGroup').onclick = () => {
    const name = prompt("Enter new Group name:", `Group ${Object.keys(customGroups).length + 1}`);
    if (name && !customGroups[name]) { customGroups[name.trim()] = { collapsed: false, ids: [] }; renderMyLayers(); markDirty(); }
};

// ----------------- Enhanced Shape Editor Logic -----------------
function openShapeEditor(id) {
    const f = features.find(x => x.id === id);
    if (!f) return;
    selectedId = id;
    closeFloatingCards();
    $('editShapeTitle').textContent = `Edit ${f.name}`;
    $('eName').value = f.name;

    const is3D = !!f.props.is3D || f.kind === 'polygon3d';
    $('editor-3d-section').style.display = (['polygon','rectangle','polygon3d'].includes(f.kind)) ? 'flex' : 'none';
    $('eIs3D').checked = is3D;
    $('eHeight').value = f.props.height || 20;
    $('eHeightVal').textContent = (f.props.height || 20) + 'm';
    $('eBaseHeight').value = f.props.baseHeight || 0;
    $('eBaseHeightVal').textContent = (f.props.baseHeight || 0) + 'm';

    const isRoute = f.kind === 'route';
    $('editor-route-section').style.display = isRoute ? 'flex' : 'none';
    if (isRoute) {
        $('eRouteMode').value = f.props.routeMode || 'driving';
        $('eRouteStats').textContent = f.props.description || '-';
        $('eDirectionsBox').style.display = f.props.routeType === 'directions' ? 'flex' : 'none';
        renderStopsList(f);
    }

    const isCircle = f.kind === 'circle';
    $('editor-circle-section').style.display = isCircle ? 'flex' : 'none';
    if (isCircle) {
        const r = f.props.radiusMeters || 0;
        $('eCircleRadiusVal').textContent = r > 1000 ? `${(r/1000).toFixed(2)} km` : `${Math.round(r)} m`;
    }

    const isImg = f.kind === 'imageOverlay';
    $('editor-image-section').style.display = isImg ? 'flex' : 'none';
    if (isImg) $('eImgOpacity').value = f.props.opacity || 0.85;

    $('eShowLabel').checked = !!f.props.showLabel;
    $('eLabelPos').value = f.props.labelPos || 'center';
    $('popup-shape-editor').classList.add('open');
}

$('eHeight').oninput = e => {
    const f = features.find(x => x.id === selectedId);
    if (f) {
        f.props.height = parseFloat(e.target.value);
        $('eHeightVal').textContent = e.target.value + 'm';
        syncDraw(); markDirty();
    }
};
$('eBaseHeight').oninput = e => {
    const f = features.find(x => x.id === selectedId);
    if (f) {
        f.props.baseHeight = parseFloat(e.target.value);
        $('eBaseHeightVal').textContent = e.target.value + 'm';
        syncDraw(); markDirty();
    }
};
$('eIs3D').onchange = e => {
    const f = features.find(x => x.id === selectedId);
    if (f) {
        f.props.is3D = e.target.checked;
        if (e.target.checked) f.props.height = f.props.height || 20;
        syncDraw(); markDirty();
    }
};
$('eDoneBtn').onclick = () => { $('popup-shape-editor').classList.remove('open'); editMode = false; selectedId = null; syncVertexHandles(); };
$('closeEditorBtn').onclick = () => { $('popup-shape-editor').classList.remove('open'); editMode = false; selectedId = null; syncVertexHandles(); };
$('eDeleteBtn').onclick = () => {
    features = features.filter(x => x.id !== selectedId);
    $('popup-shape-editor').classList.remove('open'); editMode = false; selectedId = null;
    syncDraw(); renderMyLayers(); markDirty();
};

// ----------------- Route Directions Engine -----------------
function renderStopsList(f) {
    const container = $('eStopsList');
    if (!f.props.stops) f.props.stops = [];
    container.innerHTML = f.props.stops.map((s, idx) => `
        <div class="stop-item" draggable="true" data-idx="${idx}">
            <span style="flex:1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${idx+1}. ${s.name}</span>
            <button class="card-btn" onclick="removeStop(${f.id}, ${idx})" style="color:var(--danger);">✕</button>
        </div>
    `).join('');
}

window.removeStop = (featId, idx) => {
    const f = features.find(x => x.id === featId);
    if (f && f.props.stops) {
        f.props.stops.splice(idx, 1);
        recalcDirectionsRoute(f);
    }
};

$('eBtnAddStop').onclick = async () => {
    const q = $('eAddStopInput').value.trim();
    if (!q) return;
    const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}&limit=1`);
    const data = await res.json();
    if (data && data[0]) {
        const f = features.find(x => x.id === selectedId);
        if (f) {
            if (!f.props.stops) f.props.stops = [];
            f.props.stops.push({ name: data[0].display_name.split(',')[0], coord: [parseFloat(data[0].lon), parseFloat(data[0].lat)] });
            $('eAddStopInput').value = '';
            recalcDirectionsRoute(f);
        }
    }
};

function recalcDirectionsRoute(f) {
    if (!f.props.stops || f.props.stops.length < 2) return;
    const pts = f.props.stops.map(s => s.coord);
    fetchMultiPointRoute(pts, f.id, f.props.routeMode || 'driving');
}

function fetchMultiPointRoute(pts, updateId = null, mode = 'driving') {
    hint('Calculating route…');
    const coordStr = pts.map(p => `${p[0]},${p[1]}`).join(';');
    const url = `https://router.project-osrm.org/route/v1/${mode}/${coordStr}?overview=full&geometries=geojson&steps=true`;
    fetch(url).then(r => r.json()).then(j => {
        if (j.routes && j.routes[0]) {
            const r = j.routes[0];
            const dist = r.distance, dur = r.duration;
            const desc = `${dist > 1000 ? (dist/1000).toFixed(2)+' km' : Math.round(dist)+' m'} · ${dur > 3600 ? (dur/3600).toFixed(1)+' hr' : Math.round(dur/60)+' min'}`;
            if (updateId) {
                const f = features.find(x => x.id === updateId);
                if (f) {
                    f.geometry = r.geometry; f.props.waypoints = pts;
                    f.props.description = desc; f.props.metadata = { distance: dist, duration: dur };
                    syncDraw(); renderMyLayers(); markDirty();
                    if (selectedId === updateId) { $('eRouteStats').textContent = desc; renderStopsList(f); }
                }
            } else {
                addFeatureRecord('route', r.geometry, { routeMode: mode, description: desc, waypoints: pts, metadata: { distance: dist, duration: dur }, showLabel: true });
            }
        }
        hint('');
    }).catch(() => hint('Routing failed'));
}

// ----------------- Tool Management & 3D Polygon Drawing -----------------
document.querySelectorAll('.tool').forEach(btn => {
    btn.onclick = () => {
        const t = btn.dataset.tool;
        if (activeTool === t) { resetActiveTools(); closeFloatingCards(); }
        else {
            resetActiveTools(); closeFloatingCards();
            activeTool = t;
            btn.classList.add('primary-active');
            map.getCanvas().style.cursor = 'crosshair';
            map.doubleClickZoom.disable();
            if (t === 'marker') $('popup-marker-settings').classList.add('open');
            else if (t === 'textbox') $('popup-text-settings').classList.add('open');
            else if (t === 'route') $('popup-route-mode-choice').classList.add('open');
            else if (t === 'imageOverlay') $('globalImportFileInput').click();
            else if (t === 'polygon3d') hint('Click 3D Polygon vertices · Double-click to close (Default height: 20m)');
        }
    };
});

$('btnChooseManualRoute').onclick = () => {
    $('popup-route-mode-choice').classList.remove('open');
    hint('Click route points along streets · Double click to finish');
};
$('btnChooseDirectionsRoute').onclick = () => {
    $('popup-route-mode-choice').classList.remove('open');
    const f = addFeatureRecord('route', { type: 'LineString', coordinates: [[120.9842, 14.5995], [120.9942, 14.6095]] }, { routeType: 'directions', stops: [] });
    enableEditMode(f.id);
};

function addFeatureRecord(kind, geometry, customProps = {}, targetGroup = null, explicitName = null) {
    const newId = ++fid;
    const name = explicitName || `${kind.charAt(0).toUpperCase() + kind.slice(1)} ${newId}`;
    const feat = {
        id: newId, name, kind, geometry,
        props: {
            color: '#38bdf8', borderColor: '#38bdf8', borderOpacity: 0.9, width: 3,
            fillColor: '#e8b84a', fillOpacity: 0.35, showLabel: false, labelPos: 'center',
            iconSize: markerIconSize, sizeMode: markerSizeMode, visible: 1, is3D: (kind === 'polygon3d'),
            height: 20, baseHeight: 0, attributes: {}, attrTypes: {}, attrRows: [], ...customProps
        }
    };
    features.push(feat);
    if (targetGroup && customGroups[targetGroup]) customGroups[targetGroup].ids.push(newId);
    syncDraw(); renderMyLayers(); markDirty();
    return feat;
}

// ----------------- Map Interaction: Drawing & Vertex Dragging -----------------
map.on('mousemove', e => {
    cursorLL = [e.lngLat.lng, e.lngLat.lat];
    if (activeTool) renderDraft();
    if (isDraggingHeight && heightPolyId != null) {
        const deltaY = heightStartScreenY - e.point.y;
        const newH = Math.max(1, Math.min(200, Math.round(heightStartVal + deltaY * 0.5)));
        const f = features.find(x => x.id === heightPolyId);
        if (f) {
            f.props.height = newH;
            if (selectedId === heightPolyId) { $('eHeight').value = newH; $('eHeightVal').textContent = newH + 'm'; }
            syncDraw();
        }
    }
    if (isDraggingVertex && draggedPolyId != null) {
        const f = features.find(x => x.id === draggedPolyId);
        if (f) {
            if (isRadiusHandle && f.kind === 'circle') {
                f.props.radiusMeters = haversineDist(f.props.centerCoord, cursorLL);
                f.geometry.coordinates = circleCoords(f.props.centerCoord, cursorLL).coords;
            } else if (f.geometry.coordinates[0]) {
                f.geometry.coordinates[0][draggedVertexIdx] = cursorLL;
                if (draggedVertexIdx === 0) f.geometry.coordinates[0][f.geometry.coordinates[0].length - 1] = cursorLL;
            } else if (f.props.waypoints) {
                f.props.waypoints[draggedVertexIdx] = cursorLL;
                clearTimeout(rerouteTimeout);
                rerouteTimeout = setTimeout(() => fetchMultiPointRoute(f.props.waypoints, f.id, f.props.routeMode), 300);
            }
            syncDraw();
        }
    }
});

map.on('mousedown', e => {
    if (editMode) {
        const vHits = map.queryRenderedFeatures(e.point, { layers: ['vertex-points', 'vertex-rot-symbol'] });
        if (vHits.length) {
            const p = vHits[0].properties;
            if (p.isHeightHandle) {
                isDraggingHeight = true; heightPolyId = parseInt(p.polyId, 10);
                heightStartScreenY = e.point.y;
                const f = features.find(x => x.id === heightPolyId);
                heightStartVal = f ? (f.props.height || 20) : 20;
                map.dragPan.disable(); return;
            }
            if (p.isRotHandle) {
                isDraggingRotation = true; rotatingPolyId = parseInt(p.polyId, 10);
                const f = features.find(x => x.id === rotatingPolyId);
                const b = calcBounds(f); rotCenter = [(b[0][0] + b[1][0])/2, (b[0][1] + b[1][1])/2];
                rotStartAngle = Math.atan2(cursorLL[1] - rotCenter[1], cursorLL[0] - rotCenter[0]);
                map.dragPan.disable(); return;
            }
            isDraggingVertex = true; draggedPolyId = parseInt(p.polyId, 10);
            draggedVertexIdx = p.vIdx != null ? parseInt(p.vIdx, 10) : -1;
            isRadiusHandle = !!p.isRadiusHandle;
            map.dragPan.disable(); return;
        }
    }
});

map.on('mouseup', () => {
    if (isDraggingHeight || isDraggingVertex || isDraggingRotation) {
        isDraggingHeight = false; isDraggingVertex = false; isDraggingRotation = false;
        map.dragPan.enable(); markDirty();
    }
});

map.on('click', e => {
    if (!activeTool) {
        if (!editMode) {
            const fs = map.queryRenderedFeatures(e.point, { layers: ['draw-fill','draw-fill-extrusion','draw-line','draw-outline','draw-marker','draw-text'] });
            if (fs.length && fs[0].properties.id != null) {
                const f = features.find(x => x.id === parseInt(fs[0].properties.id, 10));
                if (f) showFeaturePopup(f, [e.lngLat.lng, e.lngLat.lat]);
            }
        }
        return;
    }
    const ll = [e.lngLat.lng, e.lngLat.lat];
    if (activeTool === 'marker') {
        const feat = addFeatureRecord('marker', { type: 'Point', coordinates: ll }, { shape: markerShape, color: markerColor, iconKey: getIconKey(markerShape, markerColor) });
        resetActiveTools(); showFeaturePopup(feat, ll);
    } else if (activeTool === 'polygon' || activeTool === 'polygon3d') {
        draft.push(ll);
    } else if (activeTool === 'route') {
        draft.push(ll);
    } else if (activeTool === 'circle') {
        draft.push(ll);
        if (draft.length === 2) {
            const { coords, r } = circleCoords(draft[0], draft[1]);
            const feat = addFeatureRecord('circle', { type: 'Polygon', coordinates: coords }, { centerCoord: draft[0], radiusMeters: r });
            resetActiveTools(); showFeaturePopup(feat, ll);
        }
    } else if (activeTool === 'rectangle') {
        draft.push(ll);
        if (draft.length === 2) {
            const feat = addFeatureRecord('rectangle', { type: 'Polygon', coordinates: rectCoords(draft[0], draft[1]) });
            resetActiveTools(); showFeaturePopup(feat, ll);
        }
    }
    renderDraft();
});

map.on('dblclick', e => {
    if (activeTool === 'polygon' || activeTool === 'polygon3d') {
        e.preventDefault();
        if (draft.length >= 3) {
            const is3D = (activeTool === 'polygon3d');
            const feat = addFeatureRecord(is3D ? 'polygon3d' : 'polygon', { type: 'Polygon', coordinates: [[...draft, draft[0]]] }, { is3D, height: 20 });
            resetActiveTools(); showFeaturePopup(feat, draft[0]);
        }
    } else if (activeTool === 'route' && draft.length >= 2) {
        e.preventDefault();
        fetchMultiPointRoute(draft);
        resetActiveTools();
    }
});

// ----------------- Geometry & Icons -----------------
function renderIconCanvas(shape, color) {
    const c = document.createElement('canvas');
    c.width = 64; c.height = 64;
    const ctx = c.getContext('2d');
    ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 3; ctx.fillStyle = color;
    ctx.beginPath();
    if (shape === 'circle') ctx.arc(32, 32, 22, 0, Math.PI * 2);
    else { ctx.arc(32, 24, 16, Math.PI * 0.8, Math.PI * 0.2, false); ctx.lineTo(32, 58); }
    ctx.closePath(); ctx.fill(); ctx.stroke();
    return c;
}
function getIconKey(shape, color) {
    const key = `ico_${shape}_${color.replace('#','')}`;
    if (!map.hasImage(key)) {
        const cv = renderIconCanvas(shape, color);
        map.addImage(key, cv.getContext('2d').getImageData(0,0,64,64), { pixelRatio: 2 });
    }
    return key;
}
function haversineDist(a, b) {
    const R = 6371000, dLa = (b[1]-a[1])*Math.PI/180, dLo = (b[0]-a[0])*Math.PI/180;
    return 2 * R * Math.asin(Math.sqrt(Math.sin(dLa/2)**2 + Math.cos(a[1]*Math.PI/180)*Math.cos(b[1]*Math.PI/180)*Math.sin(dLo/2)**2));
}
function rectCoords(a, b) { return [[[a[0],a[1]],[a[0],b[1]],[b[0],b[1]],[b[0],a[1]],[a[0],a[1]]]]; }
function circleCoords(c, edge) {
    const r = haversineDist(c, edge), coords = [];
    for (let i = 0; i <= 64; i++) {
        const a = (i / 64) * 2 * Math.PI;
        coords.push([c[0] + (r / (111320 * Math.cos(c[1]*Math.PI/180))) * Math.cos(a), c[1] + (r / 111320) * Math.sin(a)]);
    }
    return { coords: [coords], r };
}
function calcBounds(f) {
    let minX = 1e9, minY = 1e9, maxX = -1e9, maxY = -1e9;
    const walk = c => { if (typeof c[0] === 'number') { minX = Math.min(minX, c[0]); maxX = Math.max(maxX, c[0]); minY = Math.min(minY, c[1]); maxY = Math.max(maxY, c[1]); } else c.forEach(walk); };
    walk(f.geometry.coordinates);
    return minX === 1e9 ? null : [[minX, minY], [maxX, maxY]];
}
function renderDraft() {
    if (!map.getSource('draft')) return;
    const f = [];
    draft.forEach(p => f.push({ type: 'Feature', geometry: { type: 'Point', coordinates: p } }));
    if (draft.length && cursorLL) f.push({ type: 'Feature', geometry: { type: 'LineString', coordinates: [...draft, cursorLL] } });
    map.getSource('draft').setData({ type: 'FeatureCollection', features: f });
}

// ----------------- Import (CSV, Images, 3D GeoJSON) -----------------
$('btn-import-toolbar').onclick = () => $('globalImportFileInput').click();
$('globalImportFileInput').onchange = async e => {
    const file = e.target.files[0];
    if (!file) return;
    const ext = file.name.split('.').pop().toLowerCase();
    hint(`Importing ${file.name}…`);
    if (['png','jpg','jpeg','webp'].includes(ext)) {
        const reader = new FileReader();
        reader.onload = ev => {
            const c = map.getCenter();
            const feat = addFeatureRecord('imageOverlay', { type: 'Polygon', coordinates: rectCoords([c.lng-0.005, c.lat-0.005], [c.lng+0.005, c.lat+0.005]) }, { imageUrl: ev.target.result, opacity: 0.85 });
            enableEditMode(feat.id);
        };
        reader.readAsDataURL(file);
    } else if (ext === 'csv') {
        const text = await file.text();
        const lines = text.split('\n').map(l => l.trim()).filter(l => l);
        const headers = lines[0].split(',');
        const latIdx = headers.findIndex(h => /lat/i.test(h));
        const lonIdx = headers.findIndex(h => /lon|lng/i.test(h));
        if (latIdx !== -1 && lonIdx !== -1) {
            lines.slice(1).forEach((line, idx) => {
                const cols = line.split(',');
                const lat = parseFloat(cols[latIdx]), lon = parseFloat(cols[lonIdx]);
                if (!isNaN(lat) && !isNaN(lon)) {
                    const props = {}; headers.forEach((h, i) => props[h] = cols[i]);
                    addFeatureRecord('marker', { type: 'Point', coordinates: [lon, lat] }, { osmTags: props, iconKey: getIconKey('pin', '#1e40af') }, null, props.name || `CSV Item ${idx+1}`);
                }
            });
        }
    } else if (ext === 'geojson' || ext === 'json') {
        const data = JSON.parse(await file.text());
        const list = data.type === 'FeatureCollection' ? data.features : [data];
        list.forEach(f => {
            const is3D = f.properties && (f.properties.height != null || f.properties.is3D);
            addFeatureRecord(f.geometry.type === 'Point' ? 'marker' : (is3D ? 'polygon3d' : 'polygon'), f.geometry, { ...f.properties, is3D, height: f.properties.height || 20 });
        });
    }
    hint('Import complete');
};

// ----------------- Attribute Table (#popup-attribute-table) -----------------
function openAttributeTable(featureId) {
    currentTableFeatureId = featureId;
    const f = features.find(x => x.id === featureId);
    if (!f) return;
    closeFloatingCards();
    $('attrTableTitle').textContent = `Attributes: ${f.name}`;
    $('popup-attribute-table').classList.add('open');
    if (!f.props.attrTypes) f.props.attrTypes = { description: 'text' };
    if (!f.props.attrRows || !f.props.attrRows.length) f.props.attrRows = [{ description: f.props.description || '' }];
    renderAttributeTable(f);
}

function renderAttributeTable(f) {
    const cols = Object.keys(f.props.attrTypes).filter(k => k !== 'name');
    $('attrTableHeader').innerHTML = `<tr>${cols.map(c => `<th>${c}</th>`).join('')}<th style="width:30px;">✕</th></tr>`;
    $('attrTableBody').innerHTML = f.props.attrRows.map((r, rIdx) => `
        <tr>
            ${cols.map(c => `<td><input type="text" value="${r[c] || ''}" onchange="updateAttrCell(${rIdx}, '${c}', this.value)"/></td>`).join('')}
            <td><button class="card-btn" onclick="removeAttrRow(${rIdx})" style="color:var(--danger);">✕</button></td>
        </tr>
    `).join('');
}
window.updateAttrCell = (rIdx, k, v) => {
    const f = features.find(x => x.id === currentTableFeatureId);
    if (f) { f.props.attrRows[rIdx][k] = v; markDirty(); }
};
window.removeAttrRow = rIdx => {
    const f = features.find(x => x.id === currentTableFeatureId);
    if (f && f.props.attrRows.length > 1) { f.props.attrRows.splice(rIdx, 1); renderAttributeTable(f); markDirty(); }
};
$('btnAddAttrRow').onclick = () => {
    const f = features.find(x => x.id === currentTableFeatureId);
    if (f) { const row = {}; Object.keys(f.props.attrTypes).forEach(k => row[k] = ''); f.props.attrRows.push(row); renderAttributeTable(f); markDirty(); }
};
$('btnAddAttrCol').onclick = () => {
    const name = prompt("Enter column name (excluding 'name'):");
    if (name && name.trim() && name.trim() !== 'name') {
        const f = features.find(x => x.id === currentTableFeatureId);
        if (f) { f.props.attrTypes[name.trim()] = 'text'; f.props.attrRows.forEach(r => r[name.trim()] = ''); renderAttributeTable(f); markDirty(); }
    }
};
$('closeAttrTableBtn').onclick = () => $('popup-attribute-table').classList.remove('open');

// ----------------- Supabase Auto-Save & Sync -----------------
async function saveProjectToSupabase(showToast = false) {
    if (!currentProjectId || currentProjectId === "local-temp") return;
    setSaveBadgeStatus('saving');
    const c = map.getCenter();
    const payload = {
        updated_at: new Date().toISOString(),
        name: currentProjectName,
        center: [c.lng, c.lat],
        zoom: map.getZoom(),
        pitch: map.getPitch(),
        bearing: map.getBearing(),
        basemap: currentStyleName,
        features: collectFeatures(),
        custom_groups: customGroups,
        layer_visibilities: {}
    };
    try {
        const res = await fetch(`${SUPABASE_URL.replace('/rest/v1/','').replace(/\/$/,'')}/rest/v1/map_projects?id=eq.${currentProjectId}`, {
            method: 'PATCH',
            headers: { 'apikey': SUPABASE_KEY, 'Authorization': `Bearer ${SUPABASE_KEY}`, 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (res.ok) { isDirty = false; setSaveBadgeStatus('saved'); if (showToast) hint('Project Saved'); }
    } catch(e) { setSaveBadgeStatus('unsaved'); }
}
setInterval(() => { if (isDirty) saveProjectToSupabase(false); }, 20000);
$('btn-save-project').onclick = () => saveProjectToSupabase(true);
$('btn-undo').onclick = undo; $('btn-redo').onclick = redo;

// ----------------- Launcher Modal -----------------
function renderProjectsList() {
    const container = $('existing-projects-container');
    container.innerHTML = ALL_PROJECTS.map(p => `
        <div class="ios26-proj-item">
            <div style="flex:1; cursor:pointer;" onclick="loadProjectDirectly('${p.id}')">
                <div style="font-weight:700;">${p.name}</div>
                <div style="font-size:11px; color:rgba(255,255,255,0.5);">Last updated: ${p.updated_at ? p.updated_at.replace('T',' ').substring(0,16) : 'Recently'}</div>
            </div>
        </div>
    `).join('');
}
window.loadProjectDirectly = id => {
    const p = ALL_PROJECTS.find(x => x.id === id);
    if (!p) return;
    currentProjectId = p.id; currentProjectName = p.name;
    $('project-name-display').textContent = currentProjectName;
    features = p.features || [];
    fid = features.reduce((max, f) => Math.max(max, f.id || 0), 0);
    customGroups = p.custom_groups || {"Trade Area Scan": {collapsed: false, ids: []}};
    if (p.center) map.setCenter(p.center);
    if (p.zoom) map.setZoom(p.zoom);
    syncDraw(); renderMyLayers();
    $('launcher-modal-scrim').classList.remove('visible');
};
$('btn-home-dialog').onclick = () => { renderProjectsList(); $('launcher-modal-scrim').classList.add('visible'); };
$('seg-btn-existing').onclick = () => { $('seg-btn-existing').classList.add('active'); $('seg-btn-new').classList.remove('active'); $('seg-content-existing').style.display = 'flex'; $('seg-content-new').style.display = 'none'; };
$('seg-btn-new').onclick = () => { $('seg-btn-new').classList.add('active'); $('seg-btn-existing').classList.remove('active'); $('seg-content-new').style.display = 'flex'; $('seg-content-existing').style.display = 'none'; };

$('btn-create-project-submit').onclick = async () => {
    const name = $('new-proj-name').value.trim() || 'Untitled Project';
    const payload = { name, basemap: "Midnight Blue", center: [120.9842, 14.5995], zoom: 14, pitch: 60, features: [], custom_groups: {"Trade Area Scan": {collapsed: false, ids: []}} };
    const res = await fetch(`${SUPABASE_URL.replace('/rest/v1/','').replace(/\/$/,'')}/rest/v1/map_projects`, {
        method: 'POST',
        headers: { 'apikey': SUPABASE_KEY, 'Authorization': `Bearer ${SUPABASE_KEY}`, 'Content-Type': 'application/json', 'Prefer': 'return=representation' },
        body: JSON.stringify(payload)
    });
    if (res.ok) {
        const data = await res.json();
        ALL_PROJECTS.unshift(data[0]);
        loadProjectDirectly(data[0].id);
    }
};

// ----------------- Panel Toggles -----------------
$('btn-browser-toggle').onclick = () => { const p = $('browser-panel'); const o = !p.classList.contains('open'); closeFloatingCards(); if (o) p.classList.add('open'); };
$('btn-close-browser').onclick = () => $('browser-panel').classList.remove('open');
$('btn-mylayers-toggle').onclick = () => { const p = $('mylayers-panel'); const o = !p.classList.contains('open'); closeFloatingCards(); if (o) p.classList.add('open'); };
$('btn-close-mylayers').onclick = () => $('mylayers-panel').classList.remove('open');
$('btn-custom-map').onclick = () => { const p = $('popup-custom-map'); const o = !p.classList.contains('open'); closeFloatingCards(); if (o) p.classList.add('open'); };
$('closeCustomMapBtn').onclick = () => $('popup-custom-map').classList.remove('open');

$('btn-export-direct').onclick = () => {
    hint('Exporting snapshot…');
    map.once('render', () => {
        const a = document.createElement('a');
        a.download = `Project_Atlas_${Date.now()}.png`;
        a.href = map.getCanvas().toDataURL('image/png', 0.98);
        a.click();
        hint('Export complete');
    });
    map.triggerRepaint();
};

map.on('load', () => {
    registerRotationHandleImage();
    addDrawStack();
    renderMyLayers();
    renderProjectsList();
    setupColorPicker('mColorCtrl', '#1e40af', col => { markerColor = col; markDirty(); });
    setupColorPicker('tColorCtrl', '#d9b451', col => { $('tColorCtrl').dataset.val = col; markDirty(); });
    setupColorPicker('eBorderColorCtrl', '#38bdf8', col => {
        const f = features.find(x => x.id === selectedId);
        if (f) { f.props.borderColor = col; f.props.color = col; syncDraw(); markDirty(); }
    });
    setupColorPicker('eFillColorCtrl', '#e8b84a', col => {
        const f = features.find(x => x.id === selectedId);
        if (f) { f.props.fillColor = col; syncDraw(); markDirty(); }
    });
    setupColorPicker('cBgColorCtrl', '#0a1628', col => { if (map.getLayer('bg')) map.setPaintProperty('bg', 'background-color', col); });
    setupColorPicker('cMainColorCtrl', '#e8b84a', col => { if (map.getLayer('rd_major')) map.setPaintProperty('rd_major', 'line-color', col); });
    setupColorPicker('cBldColorCtrl', '#8e7258', col => { if (map.getLayer('building-3d')) map.setPaintProperty('building-3d', 'fill-extrusion-color', col); });
});

} catch (e) {
    console.error('App init error:', e);
}
</script>
</body>
</html>"""

# ------------------------------------------------------------------------
# 6. MOUNT APPLICATION (VIA st.iframe)
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

    html_content = (
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
    )
    
    st.iframe(html_content, height=1000)
except Exception as e:
    st.error(f"Failed to load Project Atlas engine: {e}")

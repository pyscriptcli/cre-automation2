import json
import re
import streamlit as st
import streamlit.components.v1 as components
import requests

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
    @font-face { font-family: 'Century Gothic Custom'; src: local('Century Gothic'), local('CenturyGothic'), sans-serif; }
    * { font-family: 'Century Gothic Custom', -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif !important; }
    [data-testid="stSidebar"], section[data-testid="stSidebar"], header, #MainMenu, footer, [data-testid="stHeader"] { display: none !important; height: 0 !important; margin: 0 !important; padding: 0 !important; }
    .stApp { margin: 0 !important; padding: 0 !important; background-color: #0a1628 !important; }
    .block-container { padding: 0rem !important; margin: 0rem !important; max-width: 100vw !important; width: 100vw !important; height: 100vh !important; max-height: 100vh !important; overflow: hidden !important; }
    iframe { border: none !important; overflow: hidden !important; height: 100vh !important; width: 100vw !important; margin: 0 !important; padding: 0 !important; position: fixed !important; inset: 0 !important; }
    html, body { overflow: hidden !important; margin: 0 !important; padding: 0 !important; width: 100vw !important; height: 100vh !important; background: #0a1628 !important; }
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
    for z, val in stops: out += [z, val]
    return out

def road_layer(p, lid, classes, color, widths, minzoom=0, casing=False, opacity=1.0):
    lyr = {
        "id": lid, "type": "line", "source": "omt", "source-layer": "transportation",
        "filter": ["match", ["get", "class"], classes, True, False],
        "layout": {"line-cap": "round", "line-join": "round"},
        "paint": {"line-color": color, "line-width": w(widths), "line-opacity": opacity},
    }
    if minzoom: lyr["minzoom"] = minzoom
    if casing:
        lyr["paint"]["line-color"] = p["rd_case"]
        lyr["paint"]["line-width"] = w([(z, val + 1.8) for z, val in widths])
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
<script src="https://unpkg.com/shpjs@latest/dist/shp.js"></script>
<script src="https://unpkg.com/@tmcw/togeojson@latest/dist/togeojson.umd.js"></script>
<style>
@font-face { font-family: 'Century Gothic Custom'; src: local('Century Gothic'), local('CenturyGothic'), sans-serif; }
* { box-sizing: border-box; user-select: none; font-family: 'Century Gothic Custom', -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif; }
html, body { margin: 0; padding: 0; width: 100vw; height: 100vh; overflow: hidden; background: #0a1628; }
#map { position: absolute; inset: 0; width: 100vw; height: 100vh; z-index: 1; }
select, select option { background-color: #0f172a !important; color: #f8fafc !important; }
select option:hover, select option:checked { background-color: #2563eb !important; color: #ffffff !important; }

/* Top Toolbar */
#top-toolbar-bar {
    position: absolute; top: 16px; left: 50%; transform: translateX(-50%); z-index: 10;
    background-color: rgba(9, 16, 24, 0.97); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 36px; padding: 4px 10px;
    display: flex; align-items: center; gap: 4px; box-shadow: 0 12px 36px rgba(0, 0, 0, 0.6); color: #f0f6fc;
}
.tb-btn { width: 32px; height: 32px; display: grid; place-items: center; background: transparent; border: none; color: #adbac7; border-radius: 50%; cursor: pointer; transition: all 0.15s ease; }
.tb-btn:hover { background: rgba(255, 255, 255, 0.1); color: #ffffff; }
.tb-btn.primary-active { background: #316dca; color: #ffffff; }
.tb-sep { width: 1px; height: 18px; background: rgba(255, 255, 255, 0.12); margin: 0 4px; }
#project-meta-cluster { display: flex; align-items: center; gap: 8px; padding: 0 4px; }
#project-name-display { font-weight: 700; color: #38bdf8; font-size: 12px; max-width: 140px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer; }
.save-badge { font-size: 9px; padding: 2px 7px; border-radius: 12px; font-weight: 600; background: rgba(255, 255, 255, 0.08); color: #8b949e; border: 1px solid rgba(255, 255, 255, 0.1); display: flex; align-items: center; gap: 4px; }
.save-badge.saving { color: #d9b451; border-color: rgba(217, 180, 81, 0.4); }
.save-badge.saved { color: #3fb950; border-color: rgba(63, 185, 80, 0.4); }

/* Unified Left Panel (Tabs) */
.left-panel {
    position: absolute; top: 68px; left: 16px; bottom: 16px; width: 360px; z-index: 9;
    background-color: rgba(9, 16, 24, 0.97); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 20px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7); display: none; flex-direction: column; overflow: hidden; color: #adbac7;
}
.left-panel.open { display: flex; }
.panel-tabs { display: flex; border-bottom: 1px solid rgba(255,255,255,0.08); }
.panel-tab { flex: 1; padding: 12px; text-align: center; font-size: 12px; font-weight: 700; color: #768390; cursor: pointer; border-bottom: 2px solid transparent; }
.panel-tab.active { color: #f0f6fc; border-bottom-color: #316dca; }
.panel-content { flex: 1; overflow-y: auto; padding: 14px 16px; display: flex; flex-direction: column; gap: 12px; font-size: 12px; }
.tab-content { display: none; }
.tab-content.active { display: flex; flex-direction: column; gap: 12px; }

/* Accordions & Controls */
.acc-item { border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 8px; }
.acc-header { display: flex; align-items: center; justify-content: space-between; font-size: 13px; font-weight: 600; color: #f0f6fc; cursor: pointer; padding: 6px 0; }
.acc-body { padding: 6px 0 2px 0; display: flex; flex-direction: column; gap: 8px; }
.acc-body.hidden { display: none !important; }
.layer-row { display: flex; align-items: center; justify-content: space-between; font-size: 12px; color: #adbac7; }
.layer-row input[type=checkbox] { accent-color: #316dca; cursor: pointer; }
.dimension-mode-bar { display: flex; gap: 4px; background: rgba(0, 0, 0, 0.35); padding: 3px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.08); }
.dimension-mode-btn { flex: 1; border: none; background: transparent; color: #adbac7; font-size: 11px; font-weight: 700; padding: 5px 0; border-radius: 6px; cursor: pointer; }
.dimension-mode-btn.active { background: #316dca; color: #ffffff; }
.bound-select-row { display: flex; gap: 6px; margin-top: 4px; }
.bound-select-row input[type=text] { flex: 1; background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(255, 255, 255, 0.12); color: #f0f6fc; padding: 6px 8px; border-radius: 8px; font-size: 11px; }
.bound-select-row button { background: #ff1e1e; color: #fff; border: none; border-radius: 8px; padding: 6px 12px; font-size: 11px; font-weight: 600; cursor: pointer; }
#boundaryResults { max-height: 150px; overflow-y: auto; background: rgba(0,0,0,0.3); border-radius: 8px; margin-top: 4px; }
.bound-result-item { padding: 6px 8px; cursor: pointer; font-size: 11px; border-bottom: 1px solid rgba(255,255,255,0.05); }
.bound-result-item:hover { background: rgba(255,255,255,0.1); }

/* Layers & Grouping */
.layers-heading { display: flex; align-items: center; justify-content: space-between; font-weight: 700; font-size: 13px; color: #f0f6fc; margin-top: 6px; }
.badge-count { background: #316dca; color: #ffffff; border-radius: 12px; font-size: 11px; padding: 1px 8px; font-weight: 600; }
.group-container { background: rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; margin-top: 6px; overflow: hidden; }
.group-header { background: rgba(255, 255, 255, 0.05); padding: 8px 10px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; }
.group-title-input { background: transparent; border: none; font-weight: 700; color: #f0f6fc; font-size: 12px; width: 140px; }
.group-items { padding: 4px 6px; display: flex; flex-direction: column; gap: 4px; }
.group-items.hidden { display: none !important; }
.layer-card { background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 8px; padding: 6px 8px; display: flex; flex-direction: column; gap: 4px; margin-top: 4px; cursor: grab; }
.layer-card:active { cursor: grabbing; }
.layer-card.dragging { opacity: 0.5; border-color: #316dca; }
.layer-card-top { display: flex; align-items: center; gap: 4px; }
.layer-name-input { flex: 1; border: 1px solid transparent; background: transparent; font-weight: 600; font-size: 11px; color: #f0f6fc; padding: 2px 4px; border-radius: 4px; }
.layer-name-input:focus { border-color: #316dca; background: rgba(0,0,0,0.4); outline: none; }
.card-btn { background: transparent; border: none; color: #768390; cursor: pointer; padding: 2px 4px; border-radius: 4px; display: grid; place-items: center; }
.card-btn:hover { color: #f0f6fc; background: rgba(255,255,255,0.1); }
.card-btn.active { color: #38bdf8; }
.layer-checkbox { accent-color: #316dca; cursor: pointer; margin: 0 2px; }

/* Right Side Inspector (Unified Settings) */
#inspector-panel {
    position: absolute; top: 68px; right: 16px; bottom: 16px; width: 320px; z-index: 9;
    background-color: rgba(9, 16, 24, 0.97); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 20px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7); display: none; flex-direction: column; overflow: hidden; color: #adbac7;
}
#inspector-panel.open { display: flex; }
.inspector-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 16px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); }
.inspector-title { font-weight: 700; font-size: 14px; color: #f0f6fc; }
.inspector-content { flex: 1; overflow-y: auto; padding: 14px 16px; display: flex; flex-direction: column; gap: 12px; font-size: 12px; }
.insp-section { font-weight: 600; font-size: 11px; color: #768390; text-transform: uppercase; margin-top: 6px; }
.insp-row { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.insp-row input[type=range] { accent-color: #316dca; width: 110px; cursor: pointer; }
.insp-row input[type=color] { border: none; width: 28px; height: 28px; border-radius: 6px; cursor: pointer; background: transparent; }
.insp-row input[type=text], .insp-row select, .insp-row textarea { background: rgba(0,0,0,0.4); color: #f0f6fc; border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 8px; padding: 6px 8px; font-size: 12px; width: 100%; }
.insp-row textarea { resize: vertical; min-height: 60px; font-family: monospace; }
.icon-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
.icon-grid button { width: 36px; height: 36px; display: grid; place-items: center; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; background: rgba(255,255,255,0.05); color: #adbac7; cursor: pointer; }
.icon-grid button.active { border-color: #316dca; background: #316dca; color: #ffffff; }
.layout-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin: 4px 0; }
.layout-btn { padding: 6px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: #f0f6fc; cursor: pointer; text-align: center; font-size: 11px; font-weight: 600; }
.layout-btn.active { background: #316dca; border-color: #316dca; }
.file-upload-box { border: 1px dashed rgba(255,255,255,0.2); border-radius: 8px; padding: 12px; text-align: center; cursor: pointer; font-size: 11px; color: #768390; }
.file-upload-box:hover { border-color: #316dca; color: #f0f6fc; }

/* Map Popups */
.maplibregl-popup-content { background: rgba(9, 16, 24, 0.97) !important; color: #f0f6fc !important; border: 1px solid rgba(255, 255, 255, 0.15) !important; border-radius: 12px !important; padding: 10px !important; box-shadow: 0 12px 32px rgba(0,0,0,0.7) !important; font-size: 11px !important; max-width: 280px !important; }
.maplibregl-popup-tip { border-top-color: rgba(9, 16, 24, 0.97) !important; }
.tag-table { width: 100%; border-collapse: collapse; margin-top: 6px; }
.tag-table th, .tag-table td { text-align: left; padding: 4px 6px; border: 1px solid rgba(255,255,255,0.08); font-size: 10px; }
.tag-table th { background: rgba(255,255,255,0.06); color: #38bdf8; }

/* Launcher Modal */
#launcher-modal-scrim { position: fixed; inset: 0; z-index: 9999; display: flex; align-items: center; justify-content: center; background-color: rgba(9, 16, 24, 0.97); opacity: 0; pointer-events: none; transition: opacity 0.2s ease; }
#launcher-modal-scrim.visible { opacity: 1; pointer-events: auto; }
.ios26-card { width: 90%; max-width: 440px; max-height: 82vh; background-color: rgba(9, 16, 24, 0.97); border: 1px solid rgba(255, 255, 255, 0.16); border-radius: 24px; box-shadow: 0 32px 80px -12px rgba(0, 0, 0, 0.85); display: flex; flex-direction: column; overflow: hidden; color: #ffffff; }
.ios26-header { padding: 22px 24px 14px 24px; display: flex; flex-direction: column; gap: 4px; }
.ios26-title { font-size: 20px; font-weight: 800; letter-spacing: -0.4px; color: #ffffff; }
.ios26-subtitle { font-size: 13px; color: rgba(255, 255, 255, 0.6); }
.ios26-seg { margin: 0 24px 14px 24px; display: flex; background: rgba(0, 0, 0, 0.4); padding: 3px; border-radius: 14px; border: 1px solid rgba(255, 255, 255, 0.08); }
.ios26-seg-btn { flex: 1; border: none; background: transparent; color: rgba(255, 255, 255, 0.65); font-size: 12px; font-weight: 600; padding: 7px 0; border-radius: 11px; cursor: pointer; }
.ios26-seg-btn.active { background: rgba(255, 255, 255, 0.18); color: #ffffff; }
.ios26-body { padding: 0 24px 22px 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.ios26-input-group { display: flex; flex-direction: column; gap: 6px; }
.ios26-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.6px; color: rgba(255, 255, 255, 0.5); }
.ios26-input { background: rgba(0, 0, 0, 0.35); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 14px; padding: 10px 14px; color: #ffffff; font-size: 13px; outline: none; }
.ios26-input:focus { border-color: #38bdf8; }
.ios26-proj-item { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; }
.ios26-action-btn { background: #316dca; color: #ffffff; border: none; border-radius: 14px; padding: 11px; font-weight: 700; font-size: 13px; cursor: pointer; }
#hint-toast { position: absolute; bottom: 24px; left: 50%; transform: translateX(-50%); z-index: 15; background-color: rgba(9, 16, 24, 0.97); color: #f0f6fc; border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 20px; padding: 7px 18px; font-size: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); display: none; }
</style>
</head>
<body>
<div id="map"></div>

<!-- Top Toolbar -->
<div id="top-toolbar-bar">
    <button class="tb-btn" id="btn-home-dialog" title="Project Selection"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg></button>
    <div id="project-meta-cluster">
        <span id="project-name-display" title="Click to rename">Untitled Project 1</span>
        <div class="save-badge" id="save-status-badge"><span id="save-dot">●</span><span id="save-text">Saved</span></div>
    </div>
    <button class="tb-btn" id="btn-save-project" title="Save (Ctrl+S)" style="color:#3fb950;"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg></button>
    <div class="tb-sep"></div>
    <button class="tb-btn" id="btn-browser-toggle" title="Data & Layers"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l10 6-10 6L2 8z"></path><path d="M2 12l10 6 10-6"></path><path d="M2 16l10 6 10-6"></path></svg></button>
    <button class="tb-btn" id="btn-import-data" title="Import Data"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg></button>
    <input type="file" id="fileImportInput" accept=".geojson,.json,.kml,.kmz,.zip" style="display:none;" multiple>
    <div class="tb-sep"></div>
    <button class="tb-btn tool" data-tool="polygon" title="Draw Polygon"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l8 6-3 10H7L4 9z"></path></svg></button>
    <button class="tb-btn tool" data-tool="rectangle" title="Draw Rectangle"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16"></rect></svg></button>
    <button class="tb-btn tool" data-tool="circle" title="Draw Circle"><svg viewBox="0 0 24 24" width="14" height="14"><circle cx="12" cy="12" r="8" fill="currentColor"></circle></svg></button>
    <button class="tb-btn tool" data-tool="polyline" title="Draw Polyline"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3l4 4L7 21H3v-4z"></path></svg></button>
    <button class="tb-btn tool" data-tool="route" title="Route A to B"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="5" cy="19" r="2.5"></circle><circle cx="19" cy="5" r="2.5"></circle><path d="M7 17c4-1 3-8 8-9"></path></svg></button>
    <button class="tb-btn tool" data-tool="marker" title="Place Marker"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"></path><circle cx="12" cy="10" r="2.5"></circle></svg></button>
    <button class="tb-btn tool" data-tool="textbox" title="Add Text"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 7 4 4 20 4 20 7"></polyline><line x1="9" y1="20" x2="15" y2="20"></line><line x1="12" y1="4" x2="12" y2="20"></line></svg></button>
    <div class="tb-sep"></div>
    <button class="tb-btn" id="btn-edit-mode" title="Unified Edit Mode"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4v16h16v-7"></path><path d="M18 2l4 4-10 10H8v-4z"></path></svg></button>
    <div class="tb-sep"></div>
    <button class="tb-btn" id="btn-custom-map" title="Basemap Style"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon><line x1="8" y1="2" x2="8" y2="18"></line><line x1="16" y1="6" x2="16" y2="22"></line></svg></button>
    <button class="tb-btn" id="btn-export-dialog" title="Export"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg></button>
</div>

<!-- Left Panel (Unified Data & Layers) -->
<div id="browser-panel" class="left-panel">
    <div class="panel-tabs">
        <div class="panel-tab active" data-tab="layers">Layers</div>
        <div class="panel-tab" data-tab="data">Data & Search</div>
    </div>
    <div class="panel-content">
        <!-- Layers Tab -->
        <div id="tab-layers" class="tab-content active">
            <div class="dimension-mode-bar">
                <button class="dimension-mode-btn active" id="btn2DMode">2D MAP</button>
                <button class="dimension-mode-btn" id="btn3DMode">3D BUILDINGS</button>
            </div>
            <div class="layers-heading">
                <span>Layer Groups</span>
                <div style="display:flex; align-items:center; gap:6px;">
                    <button id="btnAddCustomGroup" style="background:#22272e; border:1px solid #2d333b; color:#adbac7; border-radius:4px; font-size:10px; font-weight:700; padding:2px 6px; cursor:pointer;">+ GROUP</button>
                    <span class="badge-count" id="layer-badge-count">0</span>
                </div>
            </div>
            <div id="my-layers-list"></div>
        </div>
        
        <!-- Data Tab -->
        <div id="tab-data" class="tab-content">
            <div class="acc-item">
                <div class="acc-header" data-target="body-trade-area"><span>Trade Area Analysis</span><span>▸</span></div>
                <div class="acc-body hidden" id="body-trade-area">
                    <div class="trade-controls" style="display:flex; flex-direction:column; gap:6px; background:rgba(0,0,0,0.35); padding:8px; border-radius:10px;">
                        <label style="font-size:11px; font-weight:600; color:#f0f6fc;">Target Polygon:</label>
                        <select id="tradePolygonSelect" style="background:#0f172a; color:#f0f6fc; border:1px solid rgba(255,255,255,0.12); border-radius:8px; padding:6px; font-size:11px;"><option value="">-- Choose --</option></select>
                        <label style="font-size:11px; font-weight:600; color:#f0f6fc;">POI Category:</label>
                        <select id="tradeCategorySelect" style="background:#0f172a; color:#f0f6fc; border:1px solid rgba(255,255,255,0.12); border-radius:8px; padding:6px; font-size:11px;"></select>
                        <button class="trade-btn" id="btnScanTradeArea" style="background:#316dca; color:#fff; border:none; border-radius:8px; padding:7px; font-weight:600; cursor:pointer; font-size:11px;">Scan POIs</button>
                    </div>
                    <div id="tradeResults" style="font-size:11px; color:#adbac7; max-height:180px; overflow-y:auto; display:flex; flex-direction:column; gap:4px; margin-top:4px;"></div>
                </div>
            </div>
            <div class="acc-item">
                <div class="acc-header" data-target="body-overpass"><span>Custom Overpass Query</span><span>▸</span></div>
                <div class="acc-body hidden" id="body-overpass">
                    <textarea id="customOverpassQuery" placeholder="[out:json];node[&quot;amenity&quot;=&quot;cafe&quot;]({{bbox}});out;" style="width:100%; background:rgba(0,0,0,0.4); color:#f0f6fc; border:1px solid rgba(255,255,255,0.12); border-radius:8px; padding:6px; font-size:11px; font-family:monospace;"></textarea>
                    <button id="btnRunCustomOverpass" style="background:#316dca; color:#fff; border:none; border-radius:8px; padding:7px; font-weight:600; cursor:pointer; font-size:11px; margin-top:4px;">Run Query</button>
                </div>
            </div>
            <div class="acc-item">
                <div class="acc-header" data-target="body-labels"><span>Labels</span><span>▸</span></div>
                <div class="acc-body hidden" id="body-labels">
                    <label class="layer-row"><span>City</span><input type="checkbox" data-g="label_city" checked></label>
                    <label class="layer-row"><span>Brgy</span><input type="checkbox" data-g="label_brgy" checked></label>
                    <label class="layer-row"><span>Street</span><input type="checkbox" data-g="label_street" checked></label>
                </div>
            </div>
            <div class="acc-item">
                <div class="acc-header" data-target="body-roads"><span>Roads & Transit</span><span>▸</span></div>
                <div class="acc-body hidden" id="body-roads">
                    <label class="layer-row"><span>Express Way</span><input type="checkbox" data-g="road_exp" checked></label>
                    <label class="layer-row"><span>Main Road</span><input type="checkbox" data-g="road_main" checked></label>
                    <label class="layer-row"><span>Secondary Road</span><input type="checkbox" data-g="road_sec" checked></label>
                    <label class="layer-row"><span>Tertiary Road</span><input type="checkbox" data-g="road_ter" checked></label>
                    <label class="layer-row"><span>Railways</span><input type="checkbox" data-g="rd_rail" checked></label>
                </div>
            </div>
            <div class="acc-item">
                <div class="acc-header" data-target="body-boundaries"><span>Boundaries (Red Dashed)</span><span>▸</span></div>
                <div class="acc-body hidden" id="body-boundaries">
                    <label class="layer-row"><span>All Provinces</span><input type="checkbox" data-g="bound_prov"></label>
                    <label class="layer-row"><span>All Cities</span><input type="checkbox" data-g="bound_city"></label>
                    <label class="layer-row"><span>All Brgys</span><input type="checkbox" data-g="bound_brgy"></label>
                    <div style="font-weight:600; font-size:11px; color:#f0f6fc; margin-top:8px;">Highlight Boundary</div>
                    <div class="bound-select-row">
                        <input type="text" id="targetCityInput" placeholder="Search city/municipality…"/>
                        <button id="btnSearchBoundary">Search</button>
                    </div>
                    <div id="boundaryResults"></div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Right Side Inspector (Unified Settings) -->
<div id="inspector-panel">
    <div class="inspector-header">
        <div class="inspector-title" id="inspectorTitle">Properties</div>
        <button class="card-btn" id="closeInspectorBtn" style="color:#f0f6fc;">✕</button>
    </div>
    <div class="inspector-content" id="inspectorContent">
        <!-- Dynamic Content Injected Here -->
    </div>
</div>

<!-- Launcher Modal -->
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
                <input class="ios26-input" id="new-proj-name" placeholder="e.g. Untitled Project 1" />
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

// ----------------- State Machine -----------------
let features = __INITIAL_FEATURES__;
let fid = features.reduce((max, f) => Math.max(max, f.id || 0), 0);
let customGroups = __INITIAL_CUSTOM_GROUPS__ || { "Trade Area Scan": { collapsed: false, ids: [] } };

let activeTool = null, editMode = false;
let draft = [], cursorLL = null, selectedId = null;
let markerShape = 'pin', markerColor = '#003366', markerIconSize = 0.9;
let currentExportRatio = 'screen';
let isDirty = false;

// Vertex dragging state
let isDraggingVertex = false, draggedVertexIdx = -1, draggedPolyId = null, isRadiusHandle = false;

const textSettings = { content: 'Custom Label', font: 'Century Gothic Custom', size: 16, color: '#d9b451', opacity: 1.0 };
let isDragging = false, dragFeatureId = null, dragStartCoord = null, dragOriginalCoords = null;

const vis = { label_city: true, label_brgy: true, label_street: true, road_exp: true, road_main: true, road_sec: true, road_ter: true, rd_rail: true, bound_prov: false, bound_city: false, bound_brgy: false };
const VIS_MAP = {
    label_city: ['label_city'], label_brgy: ['label_brgy'], label_street: ['label_street'],
    road_exp: ['case_express_casing', 'rd_express'], road_main: ['case_major_casing', 'rd_major'],
    road_sec: ['case_secondary_casing', 'rd_secondary'], road_ter: ['case_tertiary_casing', 'rd_tertiary', 'rd_min_md', 'rd_min_lo', 'rd_path'],
    rd_rail: ['rd_rail'], bound_prov: ['bound_prov'], bound_city: ['bound_city'], bound_brgy: ['bound_brgy']
}; 

const $ = id => document.getElementById(id);
const hint = t => { $('hint-toast').style.display = t ? 'block' : 'none'; $('hint-toast').textContent = t || ''; };

const setSaveBadgeStatus = status => {
    const badge = $('save-status-badge'); const text = $('save-text');
    badge.className = 'save-badge ' + status;
    if (status === 'saving') text.textContent = 'Saving...';
    else if (status === 'saved') text.textContent = 'Saved';
    else text.textContent = 'Unsaved';
};
const markDirty = () => { isDirty = true; setSaveBadgeStatus('unsaved'); };

const closePanels = () => {
    ['browser-panel', 'inspector-panel'].forEach(id => $(id).classList.remove('open'));
};

const resetActiveTools = () => {
    activeTool = null; draft = []; renderDraft();
    document.querySelectorAll('.tool').forEach(b => b.classList.remove('primary-active'));
    map.getCanvas().style.cursor = ''; map.doubleClickZoom.enable(); hint('');
};

// ----------------- Project Auto-Naming -----------------
function getNextUntitledProjectName() {
    const untitledRegex = /^Untitled Project (\d+)$/i; let maxN = 0;
    ALL_PROJECTS.forEach(p => { const match = (p.name || '').match(untitledRegex); if (match) { const num = parseInt(match[1], 10); if (num > maxN) maxN = num; } });
    return `Untitled Project ${maxN + 1}`;
}

// ----------------- Launcher UI -----------------
function openHomeDialog() { closePanels(); $('launcher-modal-scrim').classList.add('visible'); $('new-proj-name').value = getNextUntitledProjectName(); renderProjectsList(); }
function closeHomeDialog() { $('launcher-modal-scrim').classList.remove('visible'); }
$('btn-home-dialog').onclick = openHomeDialog;

$('seg-btn-existing').onclick = () => { $('seg-btn-existing').classList.add('active'); $('seg-btn-new').classList.remove('active'); $('seg-content-existing').style.display = 'flex'; $('seg-content-new').style.display = 'none'; };
$('seg-btn-new').onclick = () => { $('seg-btn-new').classList.add('active'); $('seg-btn-existing').classList.remove('active'); $('seg-content-new').style.display = 'flex'; $('seg-content-existing').style.display = 'none'; $('new-proj-name').value = getNextUntitledProjectName(); $('new-proj-name').focus(); };

function renderProjectsList() {
    const container = $('existing-projects-container');
    if (!ALL_PROJECTS || !ALL_PROJECTS.length) { container.innerHTML = `<div style="color:rgba(255,255,255,0.5); font-size:12px; text-align:center; padding:16px;">No saved projects.</div>`; return; }
    container.innerHTML = ALL_PROJECTS.map(p => `
        <div class="ios26-proj-item">
            <div style="display:flex; flex-direction:column; gap:2px; flex:1; cursor:pointer;" onclick="loadProjectDirectly('${p.id}')">
                <span style="font-weight:700; font-size:13px; color:#ffffff;">${p.name || 'Untitled Project'}</span>
                <span style="font-size:11px; color:rgba(255,255,255,0.5);">${p.basemap || 'Midnight Blue'} · ${p.features ? p.features.length : 0} layers</span>
            </div>
            <div style="display:flex; align-items:center; gap:6px;">
                <button class="card-btn" onclick="renameProjectFromLauncher(event, '${p.id}', '${(p.name || '').replace(/'/g, "\\\\'")}')" title="Rename"><svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4v16h16v-7"></path><path d="M18 2l4 4-10 10H8v-4z"></path></svg></button>
                <button class="card-btn" onclick="deleteProjectFromLauncher(event, '${p.id}', '${(p.name || '').replace(/'/g, "\\\\'")}')" title="Delete" style="color:#ff7b72;"><svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg></button>
            </div>
        </div>
    `).join('');
}

window.loadProjectDirectly = function(projectId) {
    const p = ALL_PROJECTS.find(x => x.id === projectId); if (!p) return;
    currentProjectId = p.id; currentProjectName = p.name || 'Untitled Project'; $('project-name-display').textContent = currentProjectName;
    features = p.features || []; fid = features.reduce((max, f) => Math.max(max, f.id || 0), 0);
    customGroups = p.custom_groups || { "Trade Area Scan": { collapsed: false, ids: [] } };
    if (p.center) map.setCenter(p.center); if (p.zoom) map.setZoom(p.zoom);
    if (p.basemap && ALL_STYLES[p.basemap]) { currentStyleName = p.basemap; map.setStyle(ALL_STYLES[p.basemap]); }
    features.forEach(f => { if (f.kind === 'marker') { const sh = f.props.shape || 'pin'; const col = f.props.color || '#003366'; f.props.iconKey = getIconKey(sh, col); } });
    map.once('idle', () => { addDrawStack(); applyVis(); renderMyLayers(); });
    closeHomeDialog(); hint(`Loaded "${currentProjectName}"`);
};

window.renameProjectFromLauncher = async function(e, projectId, oldName) {
    e.stopPropagation(); const newName = prompt('Rename workspace:', oldName);
    if (!newName || !newName.trim() || newName.trim() === oldName) return;
    const target = ALL_PROJECTS.find(x => x.id === projectId); if (target) target.name = newName.trim();
    if (currentProjectId === projectId) { currentProjectName = newName.trim(); $('project-name-display').textContent = currentProjectName; }
    renderProjectsList();
    try { await fetch(`${SUPABASE_URL.replace('/rest/v1/','').replace(/\/$/,'')}/rest/v1/map_projects?id=eq.${projectId}`, { method: 'PATCH', headers: { 'apikey': SUPABASE_KEY, 'Authorization': `Bearer ${SUPABASE_KEY}`, 'Content-Type': 'application/json', 'Prefer': 'return=minimal' }, body: JSON.stringify({ name: newName.trim(), updated_at: new Date().toISOString() }) }); } catch(err) {}
};

window.deleteProjectFromLauncher = async function(e, projectId, name) {
    e.stopPropagation(); if (!confirm(`Delete project "${name}" permanently?`)) return;
    ALL_PROJECTS = ALL_PROJECTS.filter(x => x.id !== projectId); renderProjectsList();
    try { await fetch(`${SUPABASE_URL.replace('/rest/v1/','').replace(/\/$/,'')}/rest/v1/map_projects?id=eq.${projectId}`, { method: 'DELETE', headers: { 'apikey': SUPABASE_KEY, 'Authorization': `Bearer ${SUPABASE_KEY}` } }); } catch(err) {}
};

$('btn-create-project-submit').onclick = async () => {
    const pName = $('new-proj-name').value.trim() || getNextUntitledProjectName(); const centerLL = [120.9842, 14.5995];
    const payload = { name: pName, basemap: "Midnight Blue", center: centerLL, zoom: 14, pitch: 0, bearing: 0, features: [], custom_groups: { "Trade Area Scan": { collapsed: false, ids: [] } }, layer_visibilities: {} };
    try {
        const res = await fetch(`${SUPABASE_URL.replace('/rest/v1/','').replace(/\/$/,'')}/rest/v1/map_projects`, { method: 'POST', headers: { 'apikey': SUPABASE_KEY, 'Authorization': `Bearer ${SUPABASE_KEY}`, 'Content-Type': 'application/json', 'Prefer': 'return=representation' }, body: JSON.stringify(payload) });
        if (res.ok) { const created = await res.json(); const proj = created[0] || created; ALL_PROJECTS.unshift(proj); loadProjectDirectly(proj.id); } 
        else { currentProjectId = "local-temp"; currentProjectName = pName; $('project-name-display').textContent = pName; features = []; customGroups = { "Trade Area Scan": { collapsed: false, ids: [] } }; map.setCenter(centerLL); closeHomeDialog(); }
    } catch(e) { closeHomeDialog(); }
};

$('project-name-display').onclick = () => { const newN = prompt('Rename project name:', currentProjectName); if (newN && newN.trim() && newN.trim() !== currentProjectName) { currentProjectName = newN.trim(); $('project-name-display').textContent = currentProjectName; markDirty(); } };

// ----------------- Supabase Sync -----------------
async function saveProjectToSupabase(showToast = false) {
    if (!currentProjectId || currentProjectId === "local-temp" || !SUPABASE_URL || !SUPABASE_KEY) { if (showToast) hint('Working in local mode'); return; }
    setSaveBadgeStatus('saving');
    const c = map.getCenter();
    const payload = { updated_at: new Date().toISOString(), name: currentProjectName, center: [c.lng, c.lat], zoom: map.getZoom(), pitch: map.getPitch(), bearing: map.getBearing(), basemap: currentStyleName, features: features, custom_groups: customGroups, layer_visibilities: vis };
    try {
        const res = await fetch(`${SUPABASE_URL.replace('/rest/v1/','').replace(/\/$/,'')}/rest/v1/map_projects?id=eq.${currentProjectId}`, { method: 'PATCH', headers: { 'apikey': SUPABASE_KEY, 'Authorization': `Bearer ${SUPABASE_KEY}`, 'Content-Type': 'application/json', 'Prefer': 'return=minimal' }, body: JSON.stringify(payload) });
        if (res.ok) { isDirty = false; setSaveBadgeStatus('saved'); if (showToast) hint('Project Saved!'); } else { setSaveBadgeStatus('unsaved'); if (showToast) hint('Failed to save project'); }
    } catch(e) { setSaveBadgeStatus('unsaved'); if (showToast) hint('Save request error'); }
}
setInterval(() => { if (isDirty) saveProjectToSupabase(false); }, 20000);
$('btn-save-project').onclick = () => saveProjectToSupabase(true);
document.addEventListener('keydown', e => { if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); saveProjectToSupabase(true); } });

// ----------------- Marker Canvas Icon Pipeline -----------------
function renderIconCanvas(shape, color, frameType = 'none') {
    const c = document.createElement('canvas'); c.width = 64; c.height = 64; const ctx = c.getContext('2d');
    ctx.clearRect(0,0,64,64); ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 3; ctx.fillStyle = color; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    ctx.beginPath();
    if (shape === 'pin') { ctx.arc(32, 24, 16, Math.PI * 0.8, Math.PI * 0.2, false); ctx.lineTo(32, 58); ctx.closePath(); } 
    else if (shape === 'star') { for (let i = 0; i < 10; i++) { const r = i % 2 ? 12 : 26, a = -Math.PI / 2 + i * Math.PI / 5; const px = 32 + r * Math.cos(a), py = 32 + r * Math.sin(a); i ? ctx.lineTo(px, py) : ctx.moveTo(px, py); } ctx.closePath(); } 
    else if (shape === 'circle') { ctx.arc(32, 32, 22, 0, Math.PI * 2); } 
    else if (shape === 'square') { ctx.rect(12, 12, 40, 40); } 
    else if (shape === 'flag') { ctx.moveTo(18, 58); ctx.lineTo(18, 10); ctx.lineTo(48, 22); ctx.lineTo(18, 34); } 
    else if (shape === 'heart') { ctx.moveTo(32, 54); ctx.bezierCurveTo(6, 34, 14, 10, 32, 22); ctx.bezierCurveTo(50, 10, 58, 34, 32, 54); }
    ctx.fill(); ctx.stroke();
    ctx.beginPath(); ctx.fillStyle = '#ffffff'; ctx.arc(32, shape === 'pin' ? 24 : 32, 5, 0, Math.PI * 2); ctx.fill();
    
    if (frameType === '2d') { ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 2; ctx.strokeRect(4, 4, 56, 56); }
    else if (frameType === '3d') { ctx.fillStyle = 'rgba(0,0,0,0.3)'; ctx.fillRect(8, 50, 48, 8); ctx.fillStyle = '#ffffff'; ctx.fillRect(6, 48, 52, 4); }
    return c;
}

function getIconKey(shape, color, frameType = 'none') {
    const key = `ico_${shape}_${color.replace('#','')}_${frameType}`;
    if (!map.hasImage(key)) { const cv = renderIconCanvas(shape, color, frameType); const imgData = cv.getContext('2d').getImageData(0,0,64,64); try { map.addImage(key, imgData, { pixelRatio: 2 }); } catch(e) {} }
    return key;
}

const ICON_SVGS = { pin: '<path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z"></path><circle cx="12" cy="10" r="2.5"></circle>', star: '<path d="M12 2l2.9 6.3 6.9.8-5.1 4.7 1.4 6.8-6.1-3.4-6.1 3.4 1.4-6.8L2.2 9.1l6.9-.8z"></path>', circle: '<circle cx="12" cy="12" r="8"></circle>', square: '<rect x="5" y="5" width="14" height="14"></rect>', flag: '<path d="M6 21V4"></path><path d="M6 4l12 3-12 3"></path>', heart: '<path d="M12 20s-7-4.6-7-10a4 4 0 0 1 7-2.5A4 4 0 0 1 19 10c0 5.4-7 10-7 10z"></path>' };

// ----------------- Vector Layers Pipeline -----------------
const fc = list => ({ type: 'FeatureCollection', features: list.map(f => ({ type: 'Feature', geometry: f.geometry, properties: Object.assign({ id: f.id, name: f.name, kind: f.kind }, f.props) })) });

function addDrawStack() {
    if (!map.getSource('draw')) {
        map.addSource('draw', { type: 'geojson', data: fc(features) });
        map.addLayer({ id: 'draw-fill', type: 'fill', source: 'draw', filter: ['==', ['geometry-type'], 'Polygon'], paint: { 'fill-color': ['coalesce', ['get', 'fillColor'], '#e8b84a'], 'fill-opacity': ['*', ['coalesce', ['get', 'fillOpacity'], 0.35], ['get', 'visible']] } });
        map.addLayer({ id: 'draw-outline', type: 'line', source: 'draw', filter: ['==', ['geometry-type'], 'Polygon'], paint: { 'line-color': ['coalesce', ['get', 'borderColor'], '#e8b84a'], 'line-width': ['coalesce', ['get', 'width'], 3], 'line-opacity': ['*', ['coalesce', ['get', 'borderOpacity'], 0.9], ['get', 'visible']] } });
        map.addLayer({ id: 'draw-line', type: 'line', source: 'draw', filter: ['==', ['geometry-type'], 'LineString'], layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': ['coalesce', ['get', 'borderColor'], '#38bdf8'], 'line-width': ['coalesce', ['get', 'width'], 4], 'line-opacity': ['*', ['coalesce', ['get', 'borderOpacity'], 0.9], ['get', 'visible']] } });
        map.addLayer({ id: 'draw-marker', type: 'symbol', source: 'draw', filter: ['all', ['==', ['geometry-type'], 'Point'], ['!=', ['get', 'kind'], 'text']], layout: { 'icon-image': ['get', 'iconKey'], 'icon-size': ['coalesce', ['get', 'iconSize'], 0.9], 'icon-allow-overlap': true, 'icon-anchor': 'bottom' }, paint: { 'icon-opacity': ['get', 'visible'] } });
        map.addLayer({ id: 'draw-text', type: 'symbol', source: 'draw', filter: ['all', ['==', ['geometry-type'], 'Point'], ['==', ['get', 'kind'], 'text']], layout: { 'text-field': ['get', 'text'], 'text-font': ['Noto Sans Regular'], 'text-size': ['coalesce', ['get', 'fontSize'], 16], 'text-allow-overlap': true, 'text-anchor': 'center' }, paint: { 'text-color': ['coalesce', ['get', 'color'], '#d9b451'], 'text-opacity': ['*', ['coalesce', ['get', 'opacity'], 1], ['get', 'visible']], 'text-halo-color': '#0a1628', 'text-halo-width': 2 } });
        map.addLayer({ id: 'draw-poly-labels', type: 'symbol', source: 'draw', filter: ['all', ['==', ['geometry-type'], 'Polygon'], ['==', ['get', 'showLabel'], true]], layout: { 'text-field': ['get', 'name'], 'text-font': ['Noto Sans Regular'], 'text-size': 13, 'text-allow-overlap': true, 'text-anchor': ['coalesce', ['get', 'labelPos'], 'center'], 'text-radial-offset': 0.8 }, paint: { 'text-color': '#ffffff', 'text-halo-color': '#0a1628', 'text-halo-width': 2, 'text-opacity': ['get', 'visible'] } });
    } else { map.getSource('draw').setData(fc(features)); }

    if (!map.getSource('draft')) {
        map.addSource('draft', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
        map.addLayer({ id: 'draft-line', type: 'line', source: 'draft', filter: ['==', ['geometry-type'], 'LineString'], paint: { 'line-color': '#38bdf8', 'line-width': 2.5, 'line-dasharray': [2, 2] } });
        map.addLayer({ id: 'draft-point', type: 'circle', source: 'draft', filter: ['==', ['geometry-type'], 'Point'], paint: { 'circle-color': ['case', ['get', 'isLastPoint'], '#38bdf8', '#e8b84a'], 'circle-radius': ['case', ['get', 'isLastPoint'], 10, ['case', ['get', 'isOrigin'], 8, 5]], 'circle-stroke-width': 2.5 } });
    }
    if (!map.getSource('vertex-handles')) {
        map.addSource('vertex-handles', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
        map.addLayer({ id: 'vertex-points', type: 'circle', source: 'vertex-handles', paint: { 'circle-color': '#38bdf8', 'circle-radius': 6, 'circle-stroke-color': '#ffffff', 'circle-stroke-width': 2 } });
    }
}

const syncDraw = () => { if (map.getSource('draw')) map.getSource('draw').setData(fc(features)); syncVertexHandles(); };

function syncVertexHandles() {
    if (!map.getSource('vertex-handles')) return;
    if (!editMode || selectedId == null) { map.getSource('vertex-handles').setData({ type: 'FeatureCollection', features: [] }); return; }
    const handleFeats = [];
    const f = features.find(x => x.id === selectedId);
    if (!f) return;
    
    if (f.kind === 'circle' && f.geometry && f.geometry.coordinates) {
        const center = f.geometry.coordinates[0][0]; // Approximate center from first coord
        // Calculate actual center from bounds or store it. For simplicity, use centroid logic or stored prop.
        // Let's use the first coordinate as center reference for the handle logic if radiusMeters is stored.
        // Better: calculate centroid.
        let cx = 0, cy = 0, n = 0;
        f.geometry.coordinates[0].forEach(c => { cx += c[0]; cy += c[1]; n++; });
        cx /= n; cy /= n;
        handleFeats.push({ type: 'Feature', geometry: { type: 'Point', coordinates: [cx, cy] }, properties: { polyId: f.id, vIdx: -1, isCenter: true } });
        
        // Radius handle: place it at the rightmost point of the circle
        const r = f.props.radiusMeters || 100;
        const rLng = r / (111320 * Math.cos(cy * Math.PI / 180));
        handleFeats.push({ type: 'Feature', geometry: { type: 'Point', coordinates: [cx + rLng, cy] }, properties: { polyId: f.id, vIdx: -2, isRadius: true } });
    } else if (f.geometry && f.geometry.coordinates) {
        let coords = f.geometry.coordinates[0];
        if (f.kind === 'polyline' || f.kind === 'route') coords = f.geometry.coordinates;
        for (let i = 0; i < coords.length; i++) {
            handleFeats.push({ type: 'Feature', geometry: { type: 'Point', coordinates: coords[i] }, properties: { polyId: f.id, vIdx: i } });
        }
    }
    map.getSource('vertex-handles').setData({ type: 'FeatureCollection', features: handleFeats });
}

function renderDraft() {
    if (!map.getSource('draft')) return;
    const f = [];
    const pt = (c, isOrigin=false, isLastPoint=false) => ({ type: 'Feature', geometry: { type: 'Point', coordinates: c }, properties: { isOrigin, isLastPoint } });
    const ln = c => ({ type: 'Feature', geometry: { type: 'LineString', coordinates: c }, properties: {} });
    draft.forEach((p, i) => { const isOrigin = i === 0 && activeTool === 'polygon'; const isLastPoint = i === draft.length - 1 && activeTool === 'route' && draft.length > 0; f.push(pt(p, isOrigin, isLastPoint)); });
    if ((activeTool === 'polyline' || activeTool === 'route') && draft.length) { f.push(ln(cursorLL ? [...draft, cursorLL] : draft)); }
    if (activeTool === 'polygon' && draft.length) { const pts = cursorLL ? [...draft, cursorLL] : draft; if (pts.length > 1) f.push(ln([...pts, pts[0]])); }
    if (activeTool === 'rectangle' && draft.length === 1 && cursorLL) { f.push(ln(rectCoords(draft[0], cursorLL)[0])); }
    if (activeTool === 'circle' && draft.length === 1 && cursorLL) { const { coords, r } = circleCoords(draft[0], cursorLL); f.push(ln(coords[0])); const distText = r > 1000 ? `${(r/1000).toFixed(2)} km` : `${Math.round(r)} m`; hint(`Radius: ${distText} · Click to finalize`); }
    map.getSource('draft').setData({ type: 'FeatureCollection', features: f });
}

function applyVis() { for (const g in VIS_MAP) { VIS_MAP[g].forEach(id => { if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', vis[g] ? 'visible' : 'none'); }); } }

map.on('load', () => { 
    features.forEach(f => { if (f.kind === 'marker') { const sh = f.props.shape || 'pin'; const col = f.props.color || '#003366'; f.props.iconKey = getIconKey(sh, col, f.props.frameType); } });
    addDrawStack(); applyVis(); renderMyLayers(); renderProjectsList();
});

// ----------------- 2D vs 3D -----------------
$('btn2DMode').onclick = () => { $('btn2DMode').classList.add('active'); $('btn3DMode').classList.remove('active'); map.setLayoutProperty('building-2d', 'visibility', 'visible'); map.setLayoutProperty('building-3d', 'visibility', 'none'); map.easeTo({ pitch: 0 }); markDirty(); };
$('btn3DMode').onclick = () => { $('btn3DMode').classList.add('active'); $('btn2DMode').classList.remove('active'); map.setLayoutProperty('building-2d', 'visibility', 'none'); map.setLayoutProperty('building-3d', 'visibility', 'visible'); map.easeTo({ pitch: 55, bearing: -15 }); markDirty(); };

// ----------------- Geometry Utilities -----------------
function haversineDist(a, b) { const R = 6371000, dLa = (b[1]-a[1]) * Math.PI/180, dLo = (b[0]-a[0]) * Math.PI/180; const s = Math.sin(dLa/2)**2 + Math.cos(a[1]*Math.PI/180) * Math.cos(b[1]*Math.PI/180) * Math.sin(dLo/2)**2; return 2 * R * Math.asin(Math.sqrt(s)); }
function rectCoords(a, b) { return [[[a[0],a[1]],[a[0],b[1]],[b[0],b[1]],[b[0],a[1]],[a[0],a[1]]]]; }
function circleCoords(c, edge) { const r = haversineDist(c, edge), coords = []; for (let i = 0; i <= 64; i++) { const a = (i / 64) * 2 * Math.PI; coords.push([c[0] + (r / (111320 * Math.cos(c[1]*Math.PI/180))) * Math.cos(a), c[1] + (r / 111320) * Math.sin(a)]); } return { coords: [coords], r }; }
function pointInPolygon(point, vs) { const x = point[0], y = point[1]; let inside = false; for (let i = 0, j = vs.length - 1; i < vs.length; j = i++) { const xi = vs[i][0], yi = vs[i][1]; const xj = vs[j][0], yj = vs[j][1]; const intersect = ((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi); if (intersect) inside = !inside; } return inside; }
function fetchMultiPointRoute(pts) { hint('Calculating route…'); const coordStr = pts.map(p => `${p[0]},${p[1]}`).join(';'); fetch(`https://router.project-osrm.org/route/v1/driving/${coordStr}?overview=full&geometries=geojson`).then(r => r.json()).then(j => { const geom = (j.routes && j.routes[0]) ? j.routes[0].geometry : { type: 'LineString', coordinates: pts }; addFeatureRecord('route', geom, { color: '#38bdf8', borderColor: '#38bdf8', width: 4, borderOpacity: 0.9 }); hint(''); }).catch(() => { addFeatureRecord('route', { type: 'LineString', coordinates: pts }, { color: '#38bdf8', borderColor: '#38bdf8', width: 3, borderOpacity: 0.8 }); hint('Direct route fallback'); }); }

function addFeatureRecord(kind, geometry, customProps = {}, targetGroup = null, explicitName = null) {
    const newId = ++fid; const isRoute = kind === 'route'; const defaultBorder = isRoute ? '#38bdf8' : '#e8b84a';
    const assignedName = explicitName || `${kind.charAt(0).toUpperCase() + kind.slice(1)} ${newId}`;
    const feat = { id: newId, name: assignedName, kind: kind, geometry: geometry, props: { color: defaultBorder, borderColor: defaultBorder, borderOpacity: 0.9, width: 3, fillColor: '#e8b84a', fillOpacity: 0.35, showLabel: false, labelPos: 'center', iconSize: markerIconSize, visible: 1, ...customProps } };
    features.push(feat);
    if (targetGroup && customGroups[targetGroup]) { customGroups[targetGroup].ids.push(newId); }
    syncDraw(); renderMyLayers(); markDirty(); return feat;
}

// ----------------- Trade Area & Overpass -----------------
$('tradeCategorySelect').innerHTML = Object.keys(POI_CONFIG).map(cat => `<option value="${cat}">${cat}</option>`).join('');

$('btnScanTradeArea').onclick = () => {
    const polyId = parseInt($('tradePolygonSelect').value, 10); const targetPoly = features.find(f => f.id === polyId);
    if (!targetPoly) { hint('Please select a target polygon first.'); return; }
    const category = $('tradeCategorySelect').value; const bnd = calcBounds(targetPoly); hint(`Scanning POIs for ${category}…`); $('tradeResults').innerHTML = '<div style="color:#d9b451;">Querying…</div>';
    if (!customGroups["Trade Area Scan"]) customGroups["Trade Area Scan"] = { collapsed: false, ids: [] };
    const tags = POI_CONFIG[category] || []; const bbox = `${bnd[0][1]},${bnd[0][0]},${bnd[1][1]},${bnd[1][0]}`; let queryParts = '';
    tags.forEach(t => { const rawTag = t[1]; if (rawTag.includes('~')) { const parts = rawTag.split('~'); const k = parts[0].replace(/"/g, ''); const v = parts[1].replace(/"/g, '').replace(',i', ''); queryParts += `node["${k}"~"${v}",i](${bbox});way["${k}"~"${v}",i](${bbox});`; } else if (rawTag.includes('=')) { const parts = rawTag.split('='); const k = parts[0].replace(/"/g, ''); const v = parts[1].replace(/"/g, ''); queryParts += `node["${k}"="${v}"](${bbox});way["${k}"="${v}"](${bbox});`; } });
    const overpassQuery = `[out:json][timeout:25];(${queryParts});out center 100;`;
    fetch(`https://overpass-api.de/api/interpreter?data=${encodeURIComponent(overpassQuery)}`).then(r => r.json()).then(data => {
        const results = data.elements || []; const polyCoords = targetPoly.geometry.coordinates[0];
        const filtered = results.filter(el => { const lat = el.lat || (el.center && el.center.lat); const lon = el.lon || (el.center && el.center.lon); return lat && lon && pointInPolygon([lon, lat], polyCoords); });
        if (!filtered.length) { $('tradeResults').innerHTML = '<div style="color:#8b949e;">No matching POIs inside.</div>'; hint('Scan complete: 0 POIs.'); return; }
        const counts = {}; filtered.forEach(el => { const poiName = (el.tags && (el.tags.name || el.tags.amenity || el.tags.shop || el.tags.building)) || 'POI'; counts[poiName] = (counts[poiName] || 0) + 1; const lat = el.lat || (el.center && el.center.lat); const lon = el.lon || (el.center && el.center.lon); addFeatureRecord('marker', { type: 'Point', coordinates: [lon, lat] }, { shape: 'pin', color: '#003366', iconSize: 0.85, iconKey: getIconKey('pin', '#003366'), osmTags: el.tags || { name: poiName, type: category } }, "Trade Area Scan", poiName); });
        let html = `<div style="font-weight:700; color:#f0f6fc; margin-bottom:4px;">Grouped ${filtered.length} POIs:</div>`; for (const k in counts) { html += `<div class="poi-badge" style="display:flex; justify-content:space-between; background:rgba(255,255,255,0.05); padding:5px 8px; border-radius:6px;"><span>${k}</span><span style="font-weight:700; color:#38bdf8;">${counts[k]}</span></div>`; }
        $('tradeResults').innerHTML = html; hint(`Added ${filtered.length} POIs!`);
    }).catch(() => { $('tradeResults').innerHTML = '<div style="color:#ff7b72;">Data source busy.</div>'; });
};

$('btnRunCustomOverpass').onclick = () => {
    const q = $('customOverpassQuery').value.trim(); if (!q) return; hint('Running custom query…');
    fetch(`https://overpass-api.de/api/interpreter?data=${encodeURIComponent(q)}`).then(r => r.json()).then(data => {
        const results = data.elements || []; let added = 0;
        results.forEach(el => {
            if (el.type === 'node' && el.lat && el.lon) {
                addFeatureRecord('marker', { type: 'Point', coordinates: [el.lon, el.lat] }, { shape: 'pin', color: '#d9b451', iconSize: 0.8, iconKey: getIconKey('pin', '#d9b451'), osmTags: el.tags || {} }, null, el.tags && el.tags.name ? el.tags.name : 'Query Result');
                added++;
            } else if (el.type === 'way' && el.center) {
                addFeatureRecord('marker', { type: 'Point', coordinates: [el.center.lon, el.center.lat] }, { shape: 'square', color: '#d9b451', iconSize: 0.8, iconKey: getIconKey('square', '#d9b451'), osmTags: el.tags || {} }, null, el.tags && el.tags.name ? el.tags.name : 'Query Result');
                added++;
            }
        });
        hint(`Added ${added} results from query.`);
    }).catch(() => hint('Query failed.'));
};

// ----------------- Boundary Search (Nominatim) -----------------
$('btnSearchBoundary').onclick = () => {
    const q = $('targetCityInput').value.trim(); if (!q) return; hint(`Searching ${q}…`); $('boundaryResults').innerHTML = '<div style="padding:6px; font-size:11px; color:#768390;">Searching…</div>';
    fetch(`https://nominatim.openstreetmap.org/search?format=json&polygon_geojson=1&limit=5&q=${encodeURIComponent(q)}`).then(r => r.json()).then(j => {
        if (!j.length) { $('boundaryResults').innerHTML = '<div style="padding:6px; font-size:11px; color:#ff7b72;">No results found.</div>'; hint('Boundary not found.'); return; }
        $('boundaryResults').innerHTML = j.map((res, idx) => `<div class="bound-result-item" data-idx="${idx}">${res.display_name}</div>`).join('');
        $('boundaryResults').querySelectorAll('.bound-result-item').forEach(item => {
            item.onclick = () => {
                const data = j[parseInt(item.dataset.idx)];
                if (data.geojson && (data.geojson.type === 'Polygon' || data.geojson.type === 'MultiPolygon')) {
                    addFeatureRecord('polygon', data.geojson, { borderColor: '#ff1e1e', borderOpacity: 1.0, width: 3, fillColor: '#ff1e1e', fillOpacity: 0.15, showLabel: true }, null, `${q} Boundary`);
                    if (data.boundingbox) { map.fitBounds([[parseFloat(data.boundingbox[2]), parseFloat(data.boundingbox[0])], [parseFloat(data.boundingbox[3]), parseFloat(data.boundingbox[1])]], { padding: 60 }); }
                    hint(`${q} boundary added!`); $('boundaryResults').innerHTML = '';
                }
            };
        });
    }).catch(() => { $('boundaryResults').innerHTML = '<div style="padding:6px; font-size:11px; color:#ff7b72;">Search failed.</div>'; hint('Request failed.'); });
};

// ----------------- Import Function (KML, KMZ, GeoJSON, SHP) -----------------
$('btn-import-data').onclick = () => $('fileImportInput').click();
$('fileImportInput').onchange = async (e) => {
    const files = e.target.files; if (!files.length) return; hint('Importing data…');
    for (const file of files) {
        try {
            let geojson = null;
            if (file.name.endsWith('.geojson') || file.name.endsWith('.json')) {
                const text = await file.text(); geojson = JSON.parse(text);
            } else if (file.name.endsWith('.kml')) {
                const text = await file.text(); const parser = new DOMParser(); const doc = parser.parseFromString(text, 'text/xml'); geojson = toGeoJSON.kml(doc);
            } else if (file.name.endsWith('.kmz')) {
                const arrayBuffer = await file.arrayBuffer(); // KMZ requires JSZip, simplified here to KML/GeoJSON/SHP
                hint('KMZ requires JSZip library. Please extract KML first.'); continue;
            } else if (file.name.endsWith('.zip')) {
                const arrayBuffer = await file.arrayBuffer(); geojson = await shp(arrayBuffer);
            }
            if (geojson) {
                let importedCount = 0;
                const processFeature = (f) => {
                    const kind = f.geometry.type === 'Point' ? 'marker' : (f.geometry.type === 'LineString' ? 'polyline' : 'polygon');
                    const props = { color: '#38bdf8', borderColor: '#38bdf8', width: 3, fillOpacity: 0.3, visible: 1 };
                    if (kind === 'marker') { props.shape = 'pin'; props.iconKey = getIconKey('pin', '#38bdf8'); }
                    addFeatureRecord(kind, f.geometry, props, null, f.properties && f.properties.name ? f.properties.name : 'Imported');
                    importedCount++;
                };
                if (geojson.type === 'FeatureCollection') geojson.features.forEach(processFeature);
                else if (geojson.type === 'Feature') processFeature(geojson);
                hint(`Imported ${importedCount} features from ${file.name}`);
            }
        } catch (err) { console.error('Import error:', err); hint(`Failed to import ${file.name}`); }
    }
    $('fileImportInput').value = '';
};

// ----------------- Tool Handlers & Unified Edit Mode -----------------
document.querySelectorAll('.tool').forEach(btn => {
    btn.onclick = () => {
        const t = btn.dataset.tool;
        if (activeTool === t) { resetActiveTools(); closePanels(); } 
        else {
            document.querySelectorAll('.tool').forEach(b => b.classList.remove('primary-active'));
            $('btn-edit-mode').classList.remove('primary-active'); editMode = false; selectedId = null; syncVertexHandles(); closePanels();
            activeTool = t; btn.classList.add('primary-active'); draft = []; renderDraft();
            map.getCanvas().style.cursor = 'crosshair'; map.doubleClickZoom.disable();
            if (t === 'marker') openInspector('marker');
            if (t === 'textbox') openInspector('text');
            if (t === 'polyline') hint('Click points · Click last point again to finish');
            if (t === 'polygon') hint('Click vertices · Click origin to save');
            if (t === 'rectangle') hint('Click corner 1, then opposite corner');
            if (t === 'circle') hint('Click center, then outer edge');
            if (t === 'route') hint('Click points · Click large blue endpoint to finish');
        }
    };
});

$('btn-edit-mode').onclick = () => {
    editMode = !editMode; activeTool = null; selectedId = null;
    document.querySelectorAll('.tool').forEach(b => b.classList.remove('primary-active'));
    $('btn-edit-mode').classList.toggle('primary-active', editMode);
    closePanels(); syncVertexHandles();
    hint(editMode ? 'Unified Edit: Click shape to select, drag vertices to reshape.' : '');
};

map.on('mousemove', e => {
    cursorLL = [e.lngLat.lng, e.lngLat.lat];
    if (activeTool) renderDraft();
    if (isDragging && dragFeatureId) {
        const dx = cursorLL[0] - dragStartCoord[0]; const dy = cursorLL[1] - dragStartCoord[1];
        const f = features.find(x => x.id === dragFeatureId); if (!f) return;
        const translateCoords = coords => { if (typeof coords[0] === 'number') return [coords[0] + dx, coords[1] + dy]; return coords.map(translateCoords); };
        f.geometry.coordinates = translateCoords(dragOriginalCoords); syncDraw(); markDirty();
    }
    if (isDraggingVertex && draggedPolyId != null) {
        const f = features.find(x => x.id === draggedPolyId); if (!f) return;
        if (isRadiusHandle && f.kind === 'circle') {
            // Recalculate circle based on center and new radius handle position
            let cx = 0, cy = 0, n = 0;
            f.geometry.coordinates[0].forEach(c => { cx += c[0]; cy += c[1]; n++; });
            cx /= n; cy /= n;
            const r = haversineDist([cx, cy], cursorLL);
            const { coords } = circleCoords([cx, cy], [cx + r/(111320*Math.cos(cy*Math.PI/180)), cy]); // dummy edge
            // Actually just regenerate circle coords
            const newCircle = circleCoords([cx, cy], cursorLL);
            f.geometry.coordinates = newCircle.coords;
            f.props.radiusMeters = newCircle.r;
        } else if (f.geometry && f.geometry.coordinates) {
            let coords = f.geometry.coordinates[0];
            if (f.kind === 'polyline' || f.kind === 'route') coords = f.geometry.coordinates;
            coords[draggedVertexIdx] = cursorLL;
            if (f.kind === 'polygon' && draggedVertexIdx === 0) { coords[coords.length - 1] = cursorLL; }
        }
        syncDraw(); markDirty();
    }
});

map.on('click', e => {
    if (!activeTool && editMode) {
        // Check vertex first
        const vHits = map.queryRenderedFeatures(e.point, { layers: ['vertex-points'] });
        if (vHits.length && vHits[0].properties.polyId != null) return; // Let mousedown handle it
        
        const fs = map.queryRenderedFeatures(e.point, { layers: ['draw-fill','draw-line','draw-outline','draw-marker','draw-text'] });
        if (fs.length && fs[0].properties.id != null) {
            selectedId = parseInt(fs[0].properties.id, 10);
            syncVertexHandles();
            openShapeEditor(selectedId);
            return;
        } else {
            selectedId = null; syncVertexHandles(); closePanels();
        }
    }
    if (!activeTool) return;
    const ll = [e.lngLat.lng, e.lngLat.lat];
    if (activeTool === 'marker') {
        const frameType = $('inspFrameType') ? $('inspFrameType').value : 'none';
        const feat = addFeatureRecord('marker', { type: 'Point', coordinates: ll }, { shape: markerShape, color: markerColor, iconSize: markerIconSize, iconKey: getIconKey(markerShape, markerColor, frameType), frameType: frameType });
        resetActiveTools(); closePanels(); openShapeEditor(feat.id);
    } else if (activeTool === 'textbox') {
        const feat = addFeatureRecord('text', { type: 'Point', coordinates: ll }, { text: $('inspTextContent').value || 'Label', fontSize: parseInt($('inspTextSize').value, 10), color: $('inspTextColor').value, opacity: parseFloat($('inspTextOp').value) });
        resetActiveTools(); closePanels(); openShapeEditor(feat.id);
    } else if (activeTool === 'polyline') {
        if (draft.length >= 2) { const pScreen = map.project(ll); const lastPtScreen = map.project(draft[draft.length - 1]); if (Math.hypot(pScreen.x - lastPtScreen.x, pScreen.y - lastPtScreen.y) < 18) { const feat = addFeatureRecord('polyline', { type: 'LineString', coordinates: draft }); resetActiveTools(); openShapeEditor(feat.id); return; } }
        draft.push(ll);
    } else if (activeTool === 'polygon') {
        if (draft.length >= 3) { const pScreen = map.project(ll); for (const pt of draft) { const vScreen = map.project(pt); if (Math.hypot(pScreen.x - vScreen.x, pScreen.y - vScreen.y) < 18) { const feat = addFeatureRecord('polygon', { type: 'Polygon', coordinates: [[...draft, draft[0]]] }); resetActiveTools(); openShapeEditor(feat.id); return; } } }
        draft.push(ll);
    } else if (activeTool === 'rectangle') {
        draft.push(ll); if (draft.length === 2) { const feat = addFeatureRecord('rectangle', { type: 'Polygon', coordinates: rectCoords(draft[0], draft[1]) }); resetActiveTools(); openShapeEditor(feat.id); }
    } else if (activeTool === 'circle') {
        draft.push(ll); if (draft.length === 2) { const { coords, r } = circleCoords(draft[0], draft[1]); const feat = addFeatureRecord('circle', { type: 'Polygon', coordinates: coords }, { radiusMeters: r }); resetActiveTools(); openShapeEditor(feat.id); }
    } else if (activeTool === 'route') {
        if (draft.length >= 2) { const pScreen = map.project(ll); const lastPtScreen = map.project(draft[draft.length - 1]); if (Math.hypot(pScreen.x - lastPtScreen.x, pScreen.y - lastPtScreen.y) < 22) { fetchMultiPointRoute(draft); resetActiveTools(); return; } }
        draft.push(ll);
    }
    renderDraft();
});

map.on('mousedown', e => {
    if (editMode) {
        const vHits = map.queryRenderedFeatures(e.point, { layers: ['vertex-points'] });
        if (vHits.length && vHits[0].properties.polyId != null) {
            isDraggingVertex = true; draggedPolyId = parseInt(vHits[0].properties.polyId, 10); draggedVertexIdx = parseInt(vHits[0].properties.vIdx, 10);
            isRadiusHandle = vHits[0].properties.isRadius === true;
            map.dragPan.disable(); return;
        }
        const fs = map.queryRenderedFeatures(e.point, { layers: ['draw-fill','draw-line','draw-outline','draw-marker','draw-text'] });
        if (fs.length && fs[0].properties.id != null) {
            isDragging = true; dragFeatureId = parseInt(fs[0].properties.id, 10); dragStartCoord = [e.lngLat.lng, e.lngLat.lat];
            const f = features.find(x => x.id === dragFeatureId); if (f) dragOriginalCoords = JSON.parse(JSON.stringify(f.geometry.coordinates));
            map.dragPan.disable();
        }
    }
});
map.on('mouseup', () => { if (isDragging) { isDragging = false; dragFeatureId = null; map.dragPan.enable(); markDirty(); } if (isDraggingVertex) { isDraggingVertex = false; draggedPolyId = null; draggedVertexIdx = -1; isRadiusHandle = false; map.dragPan.enable(); markDirty(); } });

document.addEventListener('keydown', e => {
    if (/INPUT|TEXTAREA|SELECT/.test(e.target.tagName)) return;
    if (e.key === 'Enter') {
        if (activeTool === 'polygon' && draft.length >= 3) { const feat = addFeatureRecord('polygon', { type: 'Polygon', coordinates: [[...draft, draft[0]]] }); resetActiveTools(); openShapeEditor(feat.id); } 
        else if (activeTool === 'polyline' && draft.length >= 2) { const feat = addFeatureRecord('polyline', { type: 'LineString', coordinates: draft }); resetActiveTools(); openShapeEditor(feat.id); } 
        else if (activeTool === 'route' && draft.length >= 2) { fetchMultiPointRoute(draft); resetActiveTools(); }
    }
    if (e.key === 'Escape') { resetActiveTools(); closePanels(); selectedId = null; syncVertexHandles(); }
});

// ----------------- Inspector Panel Logic -----------------
function openInspector(type) {
    $('inspector-panel').classList.add('open');
    const content = $('inspectorContent');
    if (type === 'marker') {
        $('inspectorTitle').textContent = 'Marker Settings';
        content.innerHTML = `
            <div class="insp-section">Icon Shape</div>
            <div class="icon-grid" id="inspIconGrid">${Object.keys(ICON_SVGS).map(s => `<button data-s="${s}" class="${s === markerShape ? 'active' : ''}"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">${ICON_SVGS[s]}</svg></button>`).join('')}</div>
            <div class="insp-section">Custom Image (Max 5MB)</div>
            <div class="file-upload-box" id="inspFileUpload">Click to upload image<br><span style="font-size:10px;">JPG, PNG, SVG</span></div>
            <input type="file" id="inspFileInput" accept="image/*" style="display:none;">
            <div class="insp-section">Frame Style</div>
            <div class="insp-row"><select id="inspFrameType"><option value="none">No Frame</option><option value="2d">2D Popup Frame</option><option value="3d">3D Shadow Frame</option></select></div>
            <div class="insp-row"><span>Color</span><input type="color" id="inspMarkerColor" value="${markerColor}"></div>
            <div class="insp-row"><span>Size</span><input type="range" id="inspMarkerSize" min="0.4" max="2.0" step="0.1" value="${markerIconSize}"></div>
        `;
        content.querySelectorAll('#inspIconGrid button').forEach(b => b.onclick = () => { markerShape = b.dataset.s; content.querySelectorAll('#inspIconGrid button').forEach(x => x.classList.toggle('active', x === b)); markDirty(); });
        $('inspFileUpload').onclick = () => $('inspFileInput').click();
        $('inspFileInput').onchange = (e) => {
            const file = e.target.files[0]; if (!file) return;
            if (file.size > 5 * 1024 * 1024) { hint('File too large. Max 5MB.'); return; }
            const reader = new FileReader();
            reader.onload = (ev) => {
                const img = new Image(); img.onload = () => {
                    const key = `custom_img_${Date.now()}`;
                    map.addImage(key, img, { pixelRatio: 2 });
                    markerShape = 'custom'; // Special handling
                    // For simplicity, we store the image key in a global or pass it. 
                    // In a full app, we'd update the markerShape state to use this key.
                    hint('Image loaded as marker icon.');
                }; img.src = ev.target.result;
            }; reader.readAsDataURL(file);
        };
        $('inspMarkerColor').oninput = e => { markerColor = e.target.value; markDirty(); };
        $('inspMarkerSize').oninput = e => { markerIconSize = parseFloat(e.target.value); markDirty(); };
    } else if (type === 'text') {
        $('inspectorTitle').textContent = 'Text Settings';
        content.innerHTML = `
            <div class="insp-row"><input type="text" id="inspTextContent" value="Custom Label" placeholder="Text content…"></div>
            <div class="insp-row"><span>Font Size</span><input type="range" id="inspTextSize" min="10" max="42" step="1" value="16"></div>
            <div class="insp-row"><span>Color</span><input type="color" id="inspTextColor" value="#d9b451"></div>
            <div class="insp-row"><span>Opacity</span><input type="range" id="inspTextOp" min="0.1" max="1" step="0.05" value="1"></div>
        `;
    }
}

function openShapeEditor(id) {
    const f = features.find(x => x.id === id); if (!f) return;
    $('inspector-panel').classList.add('open'); $('inspectorTitle').textContent = `Edit: ${f.name}`;
    const content = $('inspectorContent');
    const isPoly = ['polygon', 'rectangle', 'circle'].includes(f.kind);
    const isMarker = f.kind === 'marker';
    const isText = f.kind === 'text';
    
    content.innerHTML = `
        <div class="insp-row"><span>Name</span><input type="text" id="inspEditName" value="${f.name}" style="width:140px;"></div>
        ${isPoly || f.kind === 'polyline' || f.kind === 'route' ? `
        <div class="insp-section">Border</div>
        <div class="insp-row"><span>Color</span><input type="color" id="inspEditBorderColor" value="${f.props.borderColor || f.props.color}"></div>
        <div class="insp-row"><span>Opacity</span><input type="range" id="inspEditBorderOp" min="0" max="1" step="0.05" value="${f.props.borderOpacity != null ? f.props.borderOpacity : 0.9}"></div>
        <div class="insp-row"><span>Width</span><input type="range" id="inspEditWidth" min="1" max="16" step="1" value="${f.props.width || 3}"></div>
        ` : ''}
        ${isPoly ? `
        <div class="insp-section">Fill</div>
        <div class="insp-row"><span>Color</span><input type="color" id="inspEditFillColor" value="${f.props.fillColor || f.props.color}"></div>
        <div class="insp-row"><span>Opacity</span><input type="range" id="inspEditFillOp" min="0" max="1" step="0.05" value="${f.props.fillOpacity != null ? f.props.fillOpacity : 0.35}"></div>
        <div class="insp-row"><span>Show Label</span><input type="checkbox" id="inspEditShowLabel" ${f.props.showLabel ? 'checked' : ''}></div>
        ` : ''}
        ${isMarker ? `
        <div class="insp-section">Marker</div>
        <div class="insp-row"><span>Size</span><input type="range" id="inspEditMarkerSize" min="0.4" max="2.0" step="0.1" value="${f.props.iconSize || 0.9}"></div>
        ` : ''}
        ${isText ? `
        <div class="insp-section">Text</div>
        <div class="insp-row"><input type="text" id="inspEditTextVal" value="${f.props.text || ''}"></div>
        <div class="insp-row"><span>Size</span><input type="range" id="inspEditFontSize" min="10" max="42" step="1" value="${f.props.fontSize || 16}"></div>
        ` : ''}
        <div style="display:flex; justify-content:space-between; margin-top:12px;">
            <button id="inspDeleteBtn" style="color:#f85149; border:1px solid #da36334d; background:#da36331a; padding:6px 12px; border-radius:6px; cursor:pointer;">Delete</button>
            <button id="inspDoneBtn" style="background:#316dca; color:#fff; border:none; padding:6px 16px; border-radius:6px; cursor:pointer;">Done</button>
        </div>
    `;
    
    $('inspEditName').oninput = e => { f.name = e.target.value; syncDraw(); renderMyLayers(); markDirty(); };
    if ($('inspEditBorderColor')) $('inspEditBorderColor').oninput = e => { f.props.borderColor = e.target.value; f.props.color = e.target.value; if (f.kind === 'marker') f.props.iconKey = getIconKey(f.props.shape || 'pin', e.target.value, f.props.frameType); syncDraw(); markDirty(); };
    if ($('inspEditBorderOp')) $('inspEditBorderOp').oninput = e => { f.props.borderOpacity = parseFloat(e.target.value); syncDraw(); markDirty(); };
    if ($('inspEditWidth')) $('inspEditWidth').oninput = e => { f.props.width = parseFloat(e.target.value); syncDraw(); markDirty(); };
    if ($('inspEditFillColor')) $('inspEditFillColor').oninput = e => { f.props.fillColor = e.target.value; syncDraw(); markDirty(); };
    if ($('inspEditFillOp')) $('inspEditFillOp').oninput = e => { f.props.fillOpacity = parseFloat(e.target.value); syncDraw(); markDirty(); };
    if ($('inspEditShowLabel')) $('inspEditShowLabel').onchange = e => { f.props.showLabel = e.target.checked; syncDraw(); markDirty(); };
    if ($('inspEditMarkerSize')) $('inspEditMarkerSize').oninput = e => { f.props.iconSize = parseFloat(e.target.value); syncDraw(); markDirty(); };
    if ($('inspEditTextVal')) $('inspEditTextVal').oninput = e => { f.props.text = e.target.value; syncDraw(); markDirty(); };
    if ($('inspEditFontSize')) $('inspEditFontSize').oninput = e => { f.props.fontSize = parseInt(e.target.value, 10); syncDraw(); markDirty(); };
    
    $('inspDeleteBtn').onclick = () => { features = features.filter(x => x.id !== selectedId); for (const g in customGroups) { customGroups[g].ids = customGroups[g].ids.filter(id => id !== selectedId); } syncDraw(); renderMyLayers(); $('inspector-panel').classList.remove('open'); selectedId = null; syncVertexHandles(); markDirty(); };
    $('inspDoneBtn').onclick = () => { $('inspector-panel').classList.remove('open'); selectedId = null; syncVertexHandles(); };
}
$('closeInspectorBtn').onclick = () => { $('inspector-panel').classList.remove('open'); selectedId = null; syncVertexHandles(); };

// ----------------- My Layers & Grouping -----------------
$('btnAddCustomGroup').onclick = () => { const gName = prompt("Enter new Group name:", `Group ${Object.keys(customGroups).length + 1}`); if (gName && gName.trim() && !customGroups[gName]) { customGroups[gName.trim()] = { collapsed: false, ids: [] }; renderMyLayers(); markDirty(); } };

function renderLayerCardHtml(f) {
    let subInfo = f.kind; if (f.kind === 'circle' && f.props.radiusMeters) { subInfo = `R: ${f.props.radiusMeters > 1000 ? (f.props.radiusMeters/1000).toFixed(2)+'km' : Math.round(f.props.radiusMeters)+'m'}`; }
    return `
        <div class="layer-card" draggable="true" data-id="${f.id}">
            <div class="layer-card-top">
                <input class="layer-checkbox" type="checkbox" data-act="select" data-id="${f.id}" title="Select for grouping">
                <input class="layer-name-input" data-id="${f.id}" value="${f.name}" title="Click to rename"/>
                <button class="card-btn ${editMode && selectedId === f.id ? 'active' : ''}" data-act="edit" data-id="${f.id}" title="Edit"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4v16h16v-7"></path><path d="M18 2l4 4-10 10H8v-4z"></path></svg></button>
                <button class="card-btn" data-act="eye" data-id="${f.id}" title="Toggle Visibility"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg></button>
                ${['polygon', 'rectangle', 'circle'].includes(f.kind) ? `<button class="card-btn ${f.props.showLabel ? 'active' : ''}" data-act="labelToggle" data-id="${f.id}" title="Toggle Label"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7V4h16v3"></path><path d="M9 20h6"></path><path d="M12 4v16"></path></svg></button>` : ''}
                <button class="card-btn" data-act="zoom" data-id="${f.id}" title="Zoom To"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg></button>
                <button class="card-btn" data-act="del" data-id="${f.id}" title="Delete" style="color:#ff7b72;"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg></button>
            </div>
            <div style="font-size:10px; color:#768390; padding:0 4px;">${subInfo}</div>
        </div>
    `;
}

function renderMyLayers() {
    const container = $('my-layers-list'); $('layer-badge-count').textContent = features.length;
    const polyList = features.filter(f => ['polygon', 'rectangle', 'circle'].includes(f.kind));
    $('tradePolygonSelect').innerHTML = '<option value="">-- Choose --</option>' + polyList.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
    if (!features.length && !Object.keys(customGroups).length) { container.innerHTML = '<div style="font-size:12px; color:#768390; padding:6px 0;">No drawings yet.</div>'; return; }
    
    // Add multiselect group button
    let html = `<div style="display:flex; gap:4px; margin-bottom:8px;"><button id="btnGroupSelected" style="flex:1; background:#316dca; color:#fff; border:none; border-radius:6px; padding:4px; font-size:10px; cursor:pointer;">Group Selected</button><button id="btnUngroupSelected" style="flex:1; background:rgba(255,255,255,0.1); color:#fff; border:none; border-radius:6px; padding:4px; font-size:10px; cursor:pointer;">Ungroup</button></div>`;
    
    const groupedIds = new Set();
    for (const gName in customGroups) {
        const grp = customGroups[gName]; const groupFeats = features.filter(f => grp.ids.includes(f.id)); grp.ids.forEach(id => groupedIds.add(id));
        html += `<div class="group-container"><div class="group-header" data-group="${gName}"><div style="display:flex; align-items:center; gap:6px;"><span class="card-btn" data-act="groupToggleCollapse" data-group="${gName}"><svg viewBox="0 0 24 24" width="10" height="10" fill="none" stroke="currentColor" stroke-width="2"><polyline points="${grp.collapsed ? '9 18 15 12 9 6' : '6 9 12 15 18 9'}"></polyline></svg></span><input class="group-title-input" data-oldname="${gName}" value="${gName}"/></div><div style="display:flex; align-items:center; gap:2px;"><button class="card-btn" data-act="groupEye" data-group="${gName}"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg></button><button class="card-btn" data-act="groupDel" data-group="${gName}" style="color:#ff7b72;"><svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg></button></div></div><div class="group-items ${grp.collapsed ? 'hidden' : ''}">${groupFeats.length ? groupFeats.map(f => renderLayerCardHtml(f)).join('') : '<div style="font-size:10px; color:#768390; padding:4px;">Empty group</div>'}</div></div>`;
    }
    const looseFeats = features.filter(f => !groupedIds.has(f.id));
    if (looseFeats.length) { html += '<div style="font-size:11px; font-weight:700; color:#adbac7; margin-top:8px;">Ungrouped Layers</div>'; html += looseFeats.slice().reverse().map(f => renderLayerCardHtml(f)).join(''); }
    container.innerHTML = html;
    
    // Drag and Drop Logic
    let dragSrcEl = null;
    container.querySelectorAll('.layer-card').forEach(card => {
        card.addEventListener('dragstart', e => { dragSrcEl = card; card.classList.add('dragging'); e.dataTransfer.effectAllowed = 'move'; e.dataTransfer.setData('text/html', card.innerHTML); });
        card.addEventListener('dragend', () => { card.classList.remove('dragging'); container.querySelectorAll('.layer-card').forEach(c => c.classList.remove('over')); });
        card.addEventListener('dragover', e => { if (e.preventDefault) e.preventDefault(); e.dataTransfer.dropEffect = 'move'; return false; });
        card.addEventListener('dragenter', () => card.classList.add('over'));
        card.addEventListener('dragleave', () => card.classList.remove('over'));
        card.addEventListener('drop', e => {
            if (e.stopPropagation) e.stopPropagation();
            if (dragSrcEl !== card) {
                const srcId = parseInt(dragSrcEl.dataset.id, 10); const destId = parseInt(card.dataset.id, 10);
                const srcIdx = features.findIndex(f => f.id === srcId); const destIdx = features.findIndex(f => f.id === destId);
                if (srcIdx > -1 && destIdx > -1) {
                    const [moved] = features.splice(srcIdx, 1); features.splice(destIdx, 0, moved);
                    syncDraw(); renderMyLayers(); markDirty();
                }
            }
            return false;
        });
    });

    container.querySelectorAll('.group-title-input').forEach(inp => { inp.onchange = e => { const oldN = e.target.dataset.oldname; const newN = e.target.value.trim(); if (newN && newN !== oldN) { customGroups[newN] = customGroups[oldN]; delete customGroups[oldN]; renderMyLayers(); markDirty(); } }; });
    container.querySelectorAll('.layer-name-input').forEach(inp => { inp.onchange = e => { const id = parseInt(e.target.dataset.id, 10); const f = features.find(x => x.id === id); if (f) { f.name = e.target.value; syncDraw(); markDirty(); } }; });
    
    container.querySelectorAll('button[data-act], input[data-act]').forEach(b => {
        b.onchange = b.onclick = (e) => {
            if (b.tagName === 'INPUT' && e.type !== 'change') return; if (b.tagName === 'BUTTON' && e.type !== 'click') return;
            const act = b.dataset.act;
            if (act === 'groupToggleCollapse') { const g = b.dataset.group; customGroups[g].collapsed = !customGroups[g].collapsed; renderMyLayers(); return; }
            if (act === 'groupEye') { const g = b.dataset.group; const ids = customGroups[g].ids || []; const anyVis = features.some(f => ids.includes(f.id) && f.props.visible); features.forEach(f => { if (ids.includes(f.id)) f.props.visible = anyVis ? 0 : 1; }); syncDraw(); renderMyLayers(); markDirty(); return; }
            if (act === 'groupDel') { delete customGroups[b.dataset.group]; renderMyLayers(); markDirty(); return; }
            const id = parseInt(b.dataset.id, 10); const f = features.find(x => x.id === id); if (!f) return;
            if (act === 'select') return; // Handled by button below
            if (act === 'labelToggle') { f.props.showLabel = !f.props.showLabel; b.classList.toggle('active', f.props.showLabel); syncDraw(); markDirty(); }
            if (act === 'edit') { selectedId = id; syncVertexHandles(); openShapeEditor(id); }
            if (act === 'eye') { f.props.visible = f.props.visible ? 0 : 1; syncDraw(); renderMyLayers(); markDirty(); }
            if (act === 'del') { features = features.filter(x => x.id !== id); for (const g in customGroups) customGroups[g].ids = customGroups[g].ids.filter(xId => xId !== id); syncDraw(); renderMyLayers(); markDirty(); }
            if (act === 'zoom') { const bnd = calcBounds(f); if (bnd) map.fitBounds(bnd, { padding: 80, maxZoom: 17 }); }
        };
    });
    
    // Multiselect Grouping
    const btnGroup = $('btnGroupSelected'); if (btnGroup) {
        btnGroup.onclick = () => {
            const selectedIds = Array.from(container.querySelectorAll('input[data-act="select"]:checked')).map(cb => parseInt(cb.dataset.id, 10));
            if (!selectedIds.length) { hint('Select layers first.'); return; }
            const gName = prompt("Enter Group Name:", `New Group`); if (gName && gName.trim()) {
                customGroups[gName.trim()] = { collapsed: false, ids: selectedIds };
                selectedIds.forEach(id => { const f = features.find(x => x.id === id); if (f) f.props.visible = 1; });
                renderMyLayers(); markDirty();
            }
        };
    }
    const btnUngroup = $('btnUngroupSelected'); if (btnUngroup) {
        btnUngroup.onclick = () => {
            const selectedIds = Array.from(container.querySelectorAll('input[data-act="select"]:checked')).map(cb => parseInt(cb.dataset.id, 10));
            for (const g in customGroups) { customGroups[g].ids = customGroups[g].ids.filter(id => !selectedIds.includes(id)); }
            renderMyLayers(); markDirty();
        };
    }
}

function calcBounds(f) { let minX = 1e9, minY = 1e9, maxX = -1e9, maxY = -1e9, ok = false; const walk = c => { if (typeof c[0] === 'number') { ok = true; minX = Math.min(minX, c[0]); maxX = Math.max(maxX, c[0]); minY = Math.min(minY, c[1]); maxY = Math.max(maxY, c[1]); } else c.forEach(walk); }; walk(f.geometry.coordinates); if (!ok) return null; if (minX === maxX && minY === maxY) return [[minX - 0.005, minY - 0.005], [maxX + 0.005, maxY + 0.005]]; return [[minX, minY], [maxX, maxY]]; }

// ----------------- Export -----------------
$('btn-export-dialog').onclick = () => { hint('Exporting snapshot…'); map.once('render', () => { try { const srcCanvas = map.getCanvas(); let targetW = srcCanvas.width, targetH = srcCanvas.height; if (currentExportRatio === '1:1') { const dim = Math.min(srcCanvas.width, srcCanvas.height); targetW = dim; targetH = dim; } else if (currentExportRatio === '16:9') { targetW = srcCanvas.width; targetH = Math.round(srcCanvas.width * (9/16)); } else if (currentExportRatio === '4:3') { targetW = srcCanvas.width; targetH = Math.round(srcCanvas.width * (3/4)); } else if (currentExportRatio === '9:16') { targetH = srcCanvas.height; targetW = Math.round(srcCanvas.height * (9/16)); } else if (currentExportRatio === 'a4') { targetW = srcCanvas.width; targetH = Math.round(srcCanvas.width * 1.414); } const outCanvas = document.createElement('canvas'); outCanvas.width = targetW; outCanvas.height = targetH; const ctx = outCanvas.getContext('2d'); const sx = (srcCanvas.width - targetW) / 2; const sy = (srcCanvas.height - targetH) / 2; ctx.drawImage(srcCanvas, sx, sy, targetW, targetH, 0, 0, targetW, targetH); const a = document.createElement('a'); a.download = `atlas_${currentExportRatio}_${Date.now()}.png`; a.href = outCanvas.toDataURL('image/png', 0.95); document.body.appendChild(a); a.click(); document.body.removeChild(a); hint('Exported!'); } catch(e) { hint('Export fallback'); const a = document.createElement('a'); a.download = `atlas_export_${Date.now()}.png`; a.href = map.getCanvas().toDataURL('image/png'); a.click(); } }); map.triggerRepaint(); };

// ----------------- UI Panel Toggles -----------------
$('btn-browser-toggle').onclick = () => { const p = $('browser-panel'); const willOpen = !p.classList.contains('open'); closePanels(); if (willOpen) p.classList.add('open'); };
document.querySelectorAll('.panel-tab').forEach(tab => { tab.onclick = () => { document.querySelectorAll('.panel-tab').forEach(t => t.classList.remove('active')); document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active')); tab.classList.add('active'); $(`tab-${tab.dataset.tab}`).classList.add('active'); }; });
document.querySelectorAll('.acc-header').forEach(h => { h.onclick = () => { const body = $(h.dataset.target); body.classList.toggle('hidden'); const chev = h.querySelector('span:last-child'); if (chev) chev.textContent = body.classList.contains('hidden') ? '▸' : '▾'; }; });
document.querySelectorAll('#browser-panel input[data-g]').forEach(cb => { cb.onchange = () => { vis[cb.dataset.g] = cb.checked; applyVis(); markDirty(); }; });
$('btn-custom-map').onclick = () => { hint('Basemap styling: Use the Inspector panel or edit themes in code.'); };

map.on('moveend', () => markDirty());
map.on('error', e => console.warn('Map Notice:', e));
} catch (e) { console.error('App init error:', e); }
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
    components.html(html, height=1000, scrolling=False)
except Exception as e:
    st.error(f"Failed to load application: {e}")

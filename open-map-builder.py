import io
import json
import math
import logging
import streamlit as st
import streamlit.components.v1 as components  # noqa: F401 (reserved)
import requests
import numpy as np
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use("Agg")  # headless rendering, required on Cloud
import matplotlib.pyplot as plt

try:
    import osmnx as ox
    OSMNX_OK = True
except Exception as e:  # pragma: no cover
    OSMNX_OK = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
st.set_page_config(page_title="Terraink Clone", layout="wide")

# ---------------------------------------------------------------- THEMES
# Per-layer palettes mirroring the reference Color Editor.
THEME_PRESETS = {
    "CARRARA": dict(overlay="#f5f2ec", text="#1c1c1c", land="#f7f5f1", landcover="#e6e2d6",
                    water="#cfd4d6", waterways="#c3c9cc", parks="#e3e0d2", buildings="#e0ddd2",
                    aeroway="#eceae2", rail="#9a9a9a", roads_major="#ffffff",
                    roads_minor_high="#fbfaf7", roads_minor_mid="#f2efe8", roads_minor_low="#e9e6de",
                    roads_path="#f0ede4", road_outline="#3a3a3a"),
    "BLUSH": dict(overlay="#f9eef0", text="#5c2430", land="#f6e8ea", landcover="#eed6db",
                  water="#d9a5b0", waterways="#cf93a0", parks="#ecd3d8", buildings="#e8cdd3",
                  aeroway="#f2dfe3", rail="#a06a76", roads_major="#fff5f7",
                  roads_minor_high="#fdeef1", roads_minor_mid="#f7e2e6", roads_minor_low="#efd4d9",
                  roads_path="#f6e6e9", road_outline="#7a2e3f"),
    "SANDSTONE": dict(overlay="#f3ead6", text="#4a3618", land="#f0e6d2", landcover="#e4d5b4",
                      water="#b08d64", waterways="#a3815a", parks="#e4d5b8", buildings="#e0cfae",
                      aeroway="#eadfc6", rail="#8a6f4a", roads_major="#fbf4e4",
                      roads_minor_high="#f7eeda", roads_minor_mid="#efe4cb", roads_minor_low="#e6d9bd",
                      roads_path="#f1e8d4", road_outline="#6b4f2a"),
    "MIDNIGHT BLUE": dict(overlay="#0b1220", text="#d9b44a", land="#0d1626", landcover="#101c30",
                          water="#0a1a33", waterways="#0d2140", parks="#12233a", buildings="#16243c",
                          aeroway="#1a2a44", rail="#d9b44a", roads_major="#d9b44a",
                          roads_minor_high="#a8862d", roads_minor_mid="#8a7a3a", roads_minor_low="#6f6242",
                          roads_path="#3c4658", road_outline="#050a14"),
}
# CSS filters to fake theming on raster preview tiles (true theming happens at export).
PREVIEW_FILTERS = {
    "CARRARA": "grayscale(0.85) brightness(1.05)",
    "BLUSH": "sepia(0.25) hue-rotate(-20deg) saturate(1.4)",
    "SANDSTONE": "sepia(0.5) saturate(1.1)",
    "MIDNIGHT BLUE": "invert(0.92) hue-rotate(190deg) saturate(0.8) brightness(0.9)",
    "CUSTOM": "none",
}
BASEMAPS = {
    "OpenStreetMap": ("OpenStreetMap", "https://tile.openstreetmap.org/{z}/{x}/{y}.png"),
    "CartoDB Positron": ("CartoDB positron", "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"),
    "CartoDB Dark Matter": ("CartoDB dark_matter", "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"),
    "Esri Satellite": ("Esri WorldImagery", "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"),
}
LAYOUTS = {"Square (1:1)": (1080, 1080), "Landscape (16:10)": (1600, 1000),
           "Portrait (3:4)": (1080, 1440), "Custom": None}
FONT_FILES = {"Sans (Modern)": "DejaVuSans-Bold.ttf", "Serif (Classic)": "DejaVuSerif-Bold.ttf",
              "Mono (Technical)": "DejaVuSansMono-Bold.ttf"}

# ---------------------------------------------------------------- HELPERS
@st.cache_data(ttl=3600)
def geocode_location(query: str):
    """Nominatim geocoding with defensive parsing."""
    if not query:
        return None
    try:
        res = requests.get("https://nominatim.openstreetmap.org/search",
                           params={"format": "json", "q": query, "limit": 1},
                           headers={"User-Agent": "TerrainkClone/1.0"}, timeout=10).json()
        if res:
            return {"lat": float(res[0]["lat"]), "lon": float(res[0]["lon"])}
    except Exception as e:
        logger.error("Geocode failed: %s", e)
    return None

def _bbox(lat, lon, zoom, w_px, h_px):
    """Bounding box from center, zoom and pixel size (slippy-tile math)."""
    mpp = 156543.03392 * math.cos(math.radians(lat)) / (2 ** zoom)  # meters per pixel
    half_w = w_px * mpp / 2
    half_h = h_px * mpp / 2
    dlon = half_w / (111320 * max(math.cos(math.radians(lat)), 0.01))
    dlat = half_h / 110540
    return lat + dlat, lat - dlat, lon + dlon, lon - dlon  # n, s, e, w

@st.cache_data(ttl=3600)
def fetch_osm_features(n, s, e, w):
    """Single Overpass pull for all poster layers. Cached per bbox."""
    tags = {"building": True, "highway": True, "railway": "rail", "aeroway": True, "water": True,
            "waterway": True, "natural": ["water", "wood", "grass", "scrub", "grassland", "heath"],
            "leisure": ["park", "garden", "pitch", "playground"],
            "landuse": ["forest", "grass", "meadow", "basin", "reservoir"]}
    try:
        return ox.features_from_bbox(north=n, south=s, east=e, west=w, tags=tags)
    except TypeError:  # osmnx 2.x signature
        return ox.features_from_bbox(bbox=(w, s, e, n), tags=tags)

def _subset(gdf, col, vals):
    if gdf is None or col not in gdf.columns:
        return None
    out = gdf[gdf[col].isin(vals)] if vals is not True else gdf[gdf[col].notna()]
    return out if len(out) else None

def stitch_tiles(lat, lon, zoom, w_px, h_px, url_tpl):
    """Fallback raster export: download and stitch slippy tiles with PIL."""
    n = 2 ** zoom
    xc = (lon + 180) / 360 * n
    yc = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    cx, cy = xc * 256, yc * 256
    left, top = cx - w_px / 2, cy - h_px / 2
    canvas = Image.new("RGB", (w_px, h_px), "#888888")
    x0, x1 = int(left // 256), int((left + w_px) // 256)
    y0, y1 = int(top // 256), int((top + h_px) // 256)
    for tx in range(x0, x1 + 1):
        for ty in range(y0, y1 + 1):
            try:
                t = requests.get(url_tpl.format(z=zoom, x=tx, y=ty), timeout=10,
                                 headers={"User-Agent": "TerrainkClone/1.0"})
                t.raise_for_status()
                canvas.paste(Image.open(io.BytesIO(t.content)).convert("RGB"),
                             (tx * 256 - left, ty * 256 - top))
            except Exception as e:
                logger.warning("Tile fetch failed %s/%s: %s", tx, ty, e)
    return canvas

def render_vector_map(lat, lon, zoom, w_px, h_px, colors):
    """True per-layer themed render via OSMnx + matplotlib."""
    n, s, e, w = _bbox(lat, lon, zoom, w_px, h_px)
    gdf = fetch_osm_features(round(n, 4), round(s, 4), round(e, 4), round(w, 4))

    fig = plt.figure(figsize=(w_px / 100, h_px / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(colors["land"])
    ax.set_xlim(w, e)
    ax.set_ylim(s, n)
    ax.axis("off")

    def plot(sub, color, width=1.0):
        if sub is not None:
            sub.plot(ax=ax, color=color, edgecolor=color, linewidth=width)

    plot(_subset(gdf, "landuse", ["forest"]), colors["landcover"])
    plot(_subset(gdf, "natural", ["wood", "scrub", "grassland", "heath"]), colors["landcover"])
    plot(_subset(gdf, "leisure", ["park", "garden", "pitch", "playground"]), colors["parks"])
    plot(_subset(gdf, "landuse", ["grass", "meadow"]), colors["parks"])
    plot(_subset(gdf, "natural", ["water"]), colors["water"])
    plot(_subset(gdf, "landuse", ["basin", "reservoir"]), colors["water"])
    plot(_subset(gdf, "waterway", True), colors["waterways"], 0.8)
    plot(_subset(gdf, "aeroway", True), colors["aeroway"], 1.2)
    plot(_subset(gdf, "railway", ["rail"]), colors["rail"], 0.8)

    roads = _subset(gdf, "highway", True)
    if roads is not None:
        classes = [
            (["motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link",
              "secondary", "secondary_link"], colors["roads_major"], 3.0),
            (["tertiary", "tertiary_link", "residential", "unclassified"], colors["roads_minor_high"], 2.0),
            (["living_street", "road"], colors["roads_minor_mid"], 1.3),
            (["service"], colors["roads_minor_low"], 0.9),
            (["footway", "path", "cycleway", "pedestrian", "track", "steps"], colors["roads_path"], 0.5),
        ]
        # Casing pass first so outlines sit under fills.
        for vals, _c, wid in classes:
            plot(_subset(roads, "highway", vals), colors["road_outline"], wid + 1.2)
        for vals, c, wid in classes:
            plot(_subset(roads, "highway", vals), c, wid)

    plot(_subset(gdf, "building", True), colors["buildings"], 0.3)

    # User annotations drawn in the editor.
    from shapely.geometry import shape
    for f in st.session_state.get("drawings", []):
        try:
            geom = shape(f["geometry"])
            r = (f.get("properties") or {}).get("radius")
            if geom.geom_type == "Point" and r:
                geom = geom.buffer(r / 111320)
            if geom.geom_type == "Point":
                ax.plot(geom.x, geom.y, "o", color=st.session_state.ann_stroke,
                        markersize=8, markerfacecolor=st.session_state.ann_fill)
            else:
                xs, ys = geom.exterior.xy if geom.geom_type == "Polygon" else geom.xy
                if geom.geom_type == "Polygon":
                    ax.fill(xs, ys, color=st.session_state.ann_fill, alpha=st.session_state.ann_fill_op)
                ax.plot(xs, ys, color=st.session_state.ann_stroke,
                        linewidth=st.session_state.ann_weight, alpha=st.session_state.ann_op)
        except Exception as ex:
            logger.warning("Skipping annotation: %s", ex)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB")

def compose_poster(map_img, W, H, colors, title, subtitle, font_key):
    """PIL composite: overlay frame + typography + map inset."""
    img = Image.new("RGB", (W, H), colors["overlay"])
    d = ImageDraw.Draw(img)
    fdir = matplotlib.get_data_path() + "/fonts/ttf/"
    margin = int(min(W, H) * 0.04)
    y = margin
    if title:
        ft = ImageFont.truetype(fdir + FONT_FILES[font_key], int(H * 0.055))
        bb = d.textbbox((0, 0), title, font=ft)
        d.text(((W - (bb[2] - bb[0])) / 2, y), title, font=ft, fill=colors["text"])
        y += (bb[3] - bb[1]) + int(H * 0.012)
    if subtitle:
        fs = ImageFont.truetype(fdir + FONT_FILES[font_key], int(H * 0.026))
        bb = d.textbbox((0, 0), subtitle, font=fs)
        d.text(((W - (bb[2] - bb[0])) / 2, y), subtitle, font=fs, fill=colors["text"])
        y += (bb[3] - bb[1])
    y += margin // 2
    map_img = map_img.resize((W - 2 * margin, H - y - margin))
    img.paste(map_img, (margin, y))
    fc = ImageFont.truetype(fdir + "DejaVuSans.ttf", max(int(H * 0.013), 9))
    d.text((margin, H - margin + 4), "© OpenStreetMap contributors", font=fc, fill=colors["text"])
    return img

# ---------------------------------------------------------------- SIDEBAR
st.sidebar.title("Cartographic Engine")
loc = geocode_location(st.sidebar.text_input("Search Location", "Paris, France"))
if not loc:
    st.sidebar.error("Location not found.")
    st.stop()

basemap = st.sidebar.selectbox("Basemap", list(BASEMAPS.keys()))
layout = st.sidebar.selectbox("Poster Layout", list(LAYOUTS.keys()))
if layout == "Custom":
    W = st.sidebar.number_input("Width (px)", 400, 4000, 1200, 50)
    H = st.sidebar.number_input("Height (px)", 400, 4000, 1200, 50)
else:
    W, H = LAYOUTS[layout]
zoom = st.sidebar.slider("Zoom Level", 10, 18, 13)

# Theme preset + color editor
preset = st.sidebar.selectbox("Theme", list(THEME_PRESETS.keys()) + ["CUSTOM"])
if st.session_state.get("preset") != preset:
    st.session_state["preset"] = preset
    if preset != "CUSTOM":
        for k, v in THEME_PRESETS[preset].items():
            st.session_state[f"c_{k}"] = v
    st.session_state.pop("export_bytes", None)

st.sidebar.caption("Color Editor")
cols_keys = list(THEME_PRESETS["CARRARA"].keys())
grid = st.sidebar.columns(2)
colors = {}
for i, k in enumerate(cols_keys):
    colors[k] = grid[i % 2].color_picker(k.replace("_", " ").title(),
                                          st.session_state.get(f"c_{k}", THEME_PRESETS["CARRARA"][k]),
                                          key=f"c_{k}")
if st.sidebar.button("Reset All Colors"):
    src = THEME_PRESETS.get(preset, THEME_PRESETS["CARRARA"])
    for k, v in src.items():
        st.session_state[f"c_{k}"] = v
    st.rerun()

st.sidebar.subheader("Typography")
title = st.sidebar.text_input("Title", "PARIS")
subtitle = st.sidebar.text_input("Subtitle", "City Map Poster")
font_key = st.sidebar.selectbox("Font Family", list(FONT_FILES.keys()))

st.sidebar.subheader("Annotations")
st.sidebar.caption("Use the toolbar on the map: markers, routes (polylines), polygons, circles.")
st.session_state.ann_stroke = st.sidebar.color_picker("Stroke / Border", st.session_state.get("ann_stroke", "#d9b44a"))
st.session_state.ann_fill = st.sidebar.color_picker("Fill", st.session_state.get("ann_fill", "#1c1c1c"))
st.session_state.ann_weight = st.sidebar.slider("Border Width", 1, 10, 3)
st.session_state.ann_op = st.sidebar.slider("Border Opacity", 0.0, 1.0, 1.0)
st.session_state.ann_fill_op = st.sidebar.slider("Fill Opacity", 0.0, 1.0, 0.35)
if st.sidebar.button("Clear All Drawings"):
    st.session_state["drawings"] = []
    st.rerun()

# ---------------------------------------------------------------- EDITOR MAP
st.markdown(f"<h1 style='text-align:center;color:{colors['text']}'>{title}</h1>"
            f"<p style='text-align:center;color:{colors['text']}'>{subtitle}</p>", unsafe_allow_html=True)

m = folium.Map(location=[loc["lat"], loc["lon"]], zoom_start=zoom,
               tiles=BASEMAPS[basemap][0], attr="© OpenStreetMap © CARTO © Esri")
m.get_root().html.add_child(folium.Element(
    f"<style>.leaflet-tile-pane{{filter:{PREVIEW_FILTERS.get(preset, 'none')};}}</style>"))
Draw(export=False, position="topleft").add_to(m)

drawings = st.session_state.get("drawings", [])
if drawings:
    folium.GeoJson(
        {"type": "FeatureCollection", "features": drawings},
        style_function=lambda f: dict(color=st.session_state.ann_stroke,
                                      weight=st.session_state.ann_weight,
                                      opacity=st.session_state.ann_op,
                                      fillColor=st.session_state.ann_fill,
                                      fillOpacity=st.session_state.ann_fill_op),
        point_to_layer=lambda f, ll: folium.CircleMarker(
            ll, radius=8, color=st.session_state.ann_stroke, weight=st.session_state.ann_weight,
            fill=True, fill_color=st.session_state.ann_fill, fill_opacity=st.session_state.ann_fill_op),
    ).add_to(m)

out = st_folium(m, height=600, returned_objects=["all_drawings"], key="editor")
new_draws = out.get("all_drawings") or []
if new_draws:
    known = {json.dumps(f, sort_keys=True) for f in drawings}
    merged = drawings + [f for f in new_draws if json.dumps(f, sort_keys=True) not in known]
    if len(merged) != len(drawings):
        st.session_state["drawings"] = merged
        st.rerun()  # one extra pass so new shapes render with user styling

# ---------------------------------------------------------------- EXPORT
st.sidebar.divider()
fmt = st.sidebar.radio("Export Format", ["PNG (recommended)", "JPG"])
if st.sidebar.button("🖼️ Export Poster", type="primary"):
    with st.spinner("Rendering themed vector map (Overpass query, may take ~10-30s)…"):
        try:
            if not OSMNX_OK:
                raise RuntimeError("osmnx unavailable")
            map_img = render_vector_map(loc["lat"], loc["lon"], zoom, W, H - 260, colors)
        except Exception as e:
            logger.warning("Vector render failed (%s). Falling back to raster stitch.", e)
            st.sidebar.warning("Vector theming failed; used raster fallback.")
            map_img = stitch_tiles(loc["lat"], loc["lon"], zoom, W, H - 260, BASEMAPS[basemap][1])
        poster = compose_poster(map_img, W, H, colors, title, subtitle, font_key)
        buf = io.BytesIO()
        if fmt.startswith("PNG"):
            poster.save(buf, "PNG")
            mime = "image/png"
            ext = "png"
        else:
            poster.convert("RGB").save(buf, "JPEG", quality=92)
            mime = "image/jpeg"
            ext = "jpg"
        st.session_state["export_bytes"] = buf.getvalue()
        st.session_state["export_ext"] = ext
        st.session_state["export_mime"] = mime

if st.session_state.get("export_bytes"):
    st.image(st.session_state["export_bytes"], caption="Poster Preview")
    st.download_button("⬇️ Download Poster", st.session_state["export_bytes"],
                       file_name=f"terraink_poster.{st.session_state['export_ext']}",
                       mime=st.session_state["export_mime"])

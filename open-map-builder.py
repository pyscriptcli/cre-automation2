import io
import json
import math
import logging
import streamlit as st
import requests
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    import osmnx as ox
    OSMNX_OK = True
except Exception:
    OSMNX_OK = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
st.set_page_config(page_title="Terraink", layout="wide", page_icon="🔥")

# ================================================================ CSS / CHROME
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
#MainMenu, header, footer, [data-testid="stToolbar"], [data-testid="stSidebar"],
[data-testid="stStatusWidget"], [data-testid="stDecoration"] { display:none !important; }
html, body, .stApp { background:#0a0f16 !important; }
.main .block-container { padding:0.5rem 1rem !important; max-width:100%; }
* { font-family:'JetBrains Mono', monospace !important; }

/* generic bordered button (rail + header actions) */
div[data-testid="stButton"]>button {
  background:#0d1626; border:1px solid #24344f; color:#bcd3f7; border-radius:10px;
  font-size:9px; letter-spacing:1px; text-transform:uppercase; padding:8px 6px;
  white-space:pre-line; line-height:1.6; }
div[data-testid="stButton"]>button:hover { border-color:#E8B44A; color:#E8B44A; }
div[data-testid="stButton"]>button[kind="primary"] { border-color:#5b8dd9; color:#fff; background:#12203a; }
/* bright DOWNLOAD button */
div[data-testid="stDownloadButton"]>button {
  background:#e9edf2 !important; color:#0a0f16 !important; border:none !important;
  border-radius:10px; font-weight:700; letter-spacing:1px; padding:12px 22px; }

.tk-card { background:#0d1626; border:1px solid #1e2c44; border-radius:12px;
  padding:14px; margin-bottom:12px; }
.tk-ads { text-align:center; color:#5f7396; font-size:10px; letter-spacing:2px; padding:18px; }
.tk-head { display:flex; align-items:center; justify-content:space-between; padding:10px 6px; }
.tk-logo { display:flex; align-items:baseline; gap:12px; }
.tk-logo b { font-size:22px; color:#fff; letter-spacing:1px; }
.tk-logo span { color:#5f7396; font-size:11px; letter-spacing:2px; }
.tk-actions a { display:inline-block; margin-left:8px; padding:8px 14px; border:1px solid #24344f;
  border-radius:10px; color:#bcd3f7; text-decoration:none; font-size:10px; letter-spacing:1px; }
.tk-foot { display:flex; justify-content:space-between; color:#5f7396; font-size:10px;
  padding:10px 6px; border-top:1px solid #14203a; margin-top:8px; }
div[data-testid="stIFrame"] iframe { border:1px solid #24344f; border-radius:4px; }
</style>""", unsafe_allow_html=True)

LOGO_SVG = ('<svg width="26" height="26" viewBox="0 0 24 24"><path fill="#E8B44A" '
            'd="M12 2C9 8 5 10.5 5 15a7 7 0 0 0 14 0C19 10.5 15 8 12 2z"/></svg>')

st.markdown(f"""
<div class="tk-head">
  <div class="tk-logo">{LOGO_SVG}<b>TERRAINK</b><span>FREE MAP POSTER &amp; WALLPAPER CREATOR</span></div>
  <div class="tk-actions">
    <a href="https://github.com/yousifamanuel/terraink">⭐ 3,875</a>
    <a href="https://instagram.com">◎</a><a href="#">DONATE</a><a href="#">ABOUT</a>
  </div>
</div>""", unsafe_allow_html=True)

# ================================================================ DATA / STATE
THEME_PRESETS = {
    "Carrara": dict(overlay="#f5f2ec", text="#1c1c1c", land="#f7f5f1", landcover="#e6e2d6",
                    water="#cfd4d6", waterways="#c3c9cc", parks="#e3e0d2", buildings="#e0ddd2",
                    aeroway="#eceae2", rail="#9a9a9a", roads_major="#ffffff",
                    roads_minor_high="#fbfaf7", roads_minor_mid="#f2efe8", roads_minor_low="#e9e6de",
                    roads_path="#f0ede4", road_outline="#3a3a3a"),
    "Blush": dict(overlay="#f9eef0", text="#5c2430", land="#f6e8ea", landcover="#eed6db",
                  water="#d9a5b0", waterways="#cf93a0", parks="#ecd3d8", buildings="#e8cdd3",
                  aeroway="#f2dfe3", rail="#a06a76", roads_major="#fff5f7",
                  roads_minor_high="#fdeef1", roads_minor_mid="#f7e2e6", roads_minor_low="#efd4d9",
                  roads_path="#f6e6e9", road_outline="#7a2e3f"),
    "Sandstone": dict(overlay="#f3ead6", text="#4a3618", land="#f0e6d2", landcover="#e4d5b4",
                      water="#b08d64", waterways="#a3815a", parks="#e4d5b8", buildings="#e0cfae",
                      aeroway="#eadfc6", rail="#8a6f4a", roads_major="#fbf4e4",
                      roads_minor_high="#f7eeda", roads_minor_mid="#efe4cb", roads_minor_low="#e6d9bd",
                      roads_path="#f1e8d4", road_outline="#6b4f2a"),
    "Midnight Blue": dict(overlay="#0b1220", text="#d9b44a", land="#0d1626", landcover="#101c30",
                          water="#0a1a33", waterways="#0d2140", parks="#12233a", buildings="#16243c",
                          aeroway="#1a2a44", rail="#d9b44a", roads_major="#d9b44a",
                          roads_minor_high="#a8862d", roads_minor_mid="#8a7a3a", roads_minor_low="#6f6242",
                          roads_path="#3c4658", road_outline="#050a14"),
}
PREVIEW_FILTERS = {"Carrara": "grayscale(0.85) brightness(1.05)",
                   "Blush": "sepia(0.25) hue-rotate(-20deg) saturate(1.4)",
                   "Sandstone": "sepia(0.5) saturate(1.1)",
                   "Midnight Blue": "invert(0.92) hue-rotate(190deg) saturate(0.8) brightness(0.9)",
                   "Custom": "none"}
BASEMAPS = {"OpenStreetMap": ("OpenStreetMap", "https://tile.openstreetmap.org/{z}/{x}/{y}.png"),
            "CartoDB Positron": ("CartoDB positron", "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"),
            "CartoDB Dark Matter": ("CartoDB dark_matter", "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"),
            "Esri Satellite": ("Esri WorldImagery", "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}")}
LAYOUTS = {"Instagram Square": (1080, 1080), "Landscape 16:10": (1600, 1000),
           "Portrait 3:4": (1080, 1440), "Custom": None}
FONT_FILES = {"Sans": "DejaVuSans-Bold.ttf", "Serif": "DejaVuSerif-Bold.ttf", "Mono": "DejaVuSansMono-Bold.ttf"}

@st.cache_data(ttl=3600)
def geocode_location(query: str):
    if not query: return None
    try:
        res = requests.get("https://nominatim.openstreetmap.org/search",
                           params={"format": "json", "q": query, "limit": 1},
                           headers={"User-Agent": "TerrainkClone/1.0"}, timeout=10).json()
        if res: return {"lat": float(res[0]["lat"]), "lon": float(res[0]["lon"]), "name": res[0]["display_name"]}
    except Exception as e:
        logger.error("Geocode failed: %s", e)
    return None

def _bbox(lat, lon, zoom, w_px, h_px):
    mpp = 156543.03392 * math.cos(math.radians(lat)) / (2 ** zoom)
    dlon = (w_px * mpp / 2) / (111320 * max(math.cos(math.radians(lat)), 0.01))
    dlat = (h_px * mpp / 2) / 110540
    return lat + dlat, lat - dlat, lon + dlon, lon - dlon

@st.cache_data(ttl=3600)
def fetch_osm_features(n, s, e, w):
    tags = {"building": True, "highway": True, "railway": "rail", "aeroway": True, "water": True,
            "waterway": True, "natural": ["water", "wood", "grass", "scrub", "grassland", "heath"],
            "leisure": ["park", "garden", "pitch", "playground"],
            "landuse": ["forest", "grass", "meadow", "basin", "reservoir"]}
    try:
        return ox.features_from_bbox(north=n, south=s, east=e, west=w, tags=tags)
    except TypeError:
        return ox.features_from_bbox(bbox=(w, s, e, n), tags=tags)

def _subset(gdf, col, vals):
    if gdf is None or col not in gdf.columns: return None
    out = gdf[gdf[col].notna()] if vals is True else gdf[gdf[col].isin(vals)]
    return out if len(out) else None

def stitch_tiles(lat, lon, zoom, w_px, h_px, url_tpl):
    n = 2 ** zoom
    xc = (lon + 180) / 360 * n
    yc = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    left, top = xc * 256 - w_px / 2, yc * 256 - h_px / 2
    canvas = Image.new("RGB", (w_px, h_px), "#0d1626")
    for tx in range(int(left // 256), int((left + w_px) // 256) + 1):
        for ty in range(int(top // 256), int((top + h_px) // 256) + 1):
            try:
                t = requests.get(url_tpl.format(z=zoom, x=tx, y=ty), timeout=10,
                                 headers={"User-Agent": "TerrainkClone/1.0"})
                t.raise_for_status()
                canvas.paste(Image.open(io.BytesIO(t.content)).convert("RGB"),
                             (tx * 256 - left, ty * 256 - top))
            except Exception as e:
                logger.warning("Tile failed %s/%s: %s", tx, ty, e)
    return canvas

def render_vector_map(lat, lon, zoom, w_px, h_px, colors, layers, mk, shp, drawings):
    from shapely.geometry import shape
    n, s, e, w = _bbox(lat, lon, zoom, w_px, h_px)
    gdf = fetch_osm_features(round(n, 4), round(s, 4), round(e, 4), round(w, 4))
    fig = plt.figure(figsize=(w_px / 100, h_px / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(colors["land"]); ax.set_xlim(w, e); ax.set_ylim(s, n); ax.axis("off")

    def plot(sub, color, width=1.0):
        if sub is not None: sub.plot(ax=ax, color=color, edgecolor=color, linewidth=width)

    if layers["Landcover"]:
        plot(_subset(gdf, "landuse", ["forest"]), colors["landcover"])
        plot(_subset(gdf, "natural", ["wood", "scrub", "grassland", "heath"]), colors["landcover"])
    if layers["Parks"]:
        plot(_subset(gdf, "leisure", ["park", "garden", "pitch", "playground"]), colors["parks"])
        plot(_subset(gdf, "landuse", ["grass", "meadow"]), colors["parks"])
    if layers["Water"]:
        plot(_subset(gdf, "natural", ["water"]), colors["water"])
        plot(_subset(gdf, "landuse", ["basin", "reservoir"]), colors["water"])
        plot(_subset(gdf, "waterway", True), colors["waterways"], 0.8)
    plot(_subset(gdf, "aeroway", True), colors["aeroway"], 1.2)
    plot(_subset(gdf, "railway", ["rail"]), colors["rail"], 0.8)
    if layers["Roads"]:
        roads = _subset(gdf, "highway", True)
        classes = [
            (["motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link",
              "secondary", "secondary_link"], colors["roads_major"], 3.0),
            (["tertiary", "tertiary_link", "residential", "unclassified"], colors["roads_minor_high"], 2.0),
            (["living_street", "road"], colors["roads_minor_mid"], 1.3),
            (["service"], colors["roads_minor_low"], 0.9),
            (["footway", "path", "cycleway", "pedestrian", "track", "steps"], colors["roads_path"], 0.5)]
        if roads is not None:
            for vals, _c, wid in classes:
                plot(_subset(roads, "highway", vals), colors["road_outline"], wid + 1.2)
            for vals, c, wid in classes:
                plot(_subset(roads, "highway", vals), c, wid)
    if layers["Buildings"]:
        plot(_subset(gdf, "building", True), colors["buildings"], 0.3)

    for f in drawings:  # user annotations
        try:
            geom = shape(f["geometry"])
            r = (f.get("properties") or {}).get("radius")
            if geom.geom_type == "Point" and r: geom = geom.buffer(r / 111320)
            if geom.geom_type == "Point":
                ax.plot(geom.x, geom.y, "o", color=mk["stroke"], markersize=mk["size"],
                        markerfacecolor=mk["fill"], markeredgecolor=mk["stroke"])
            else:
                xs, ys = (geom.exterior.xy, None) if geom.geom_type == "Polygon" else (geom.xy, None)
                if geom.geom_type == "Polygon":
                    ax.fill(*geom.exterior.xy, color=shp["fill"], alpha=shp["fill_op"])
                ax.plot(xs, ys, color=shp["stroke"], linewidth=shp["weight"], alpha=shp["opacity"])
        except Exception as ex:
            logger.warning("Skip annotation: %s", ex)
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=100); plt.close(fig); buf.seek(0)
    return Image.open(buf).convert("RGB")

def compose_poster(map_img, W, H, colors, title, subtitle, font_key):
    img = Image.new("RGB", (W, H), colors["overlay"]); d = ImageDraw.Draw(img)
    fdir = matplotlib.get_data_path() + "/fonts/ttf/"; margin = int(min(W, H) * 0.04); y = margin
    if title:
        ft = ImageFont.truetype(fdir + FONT_FILES[font_key], int(H * 0.055))
        bb = d.textbbox((0, 0), title, font=ft)
        d.text(((W - (bb[2] - bb[0])) / 2, y), title, font=ft, fill=colors["text"]); y += (bb[3] - bb[1]) + 12
    if subtitle:
        fs = ImageFont.truetype(fdir + FONT_FILES[font_key], int(H * 0.026))
        bb = d.textbbox((0, 0), subtitle, font=fs)
        d.text(((W - (bb[2] - bb[0])) / 2, y), subtitle, font=fs, fill=colors["text"]); y += (bb[3] - bb[1])
    y += margin // 2
    map_img = map_img.resize((W - 2 * margin, H - y - margin - int(H * 0.02)))
    img.paste(map_img, (margin, y))
    fc = ImageFont.truetype(fdir + "DejaVuSans.ttf", max(int(H * 0.013), 9))
    d.text((margin, H - margin + 4), "© terraink.app", font=fc, fill=colors["text"])
    d.text((W - margin - 260, H - margin + 4), "© OpenStreetMap contributors", font=fc, fill=colors["text"])
    return img

# ================================================================ RAIL + PANELS
RAIL = ["LOCATION", "THEME", "LAYOUT", "STYLE", "LAYERS", "MARKERS", "ROUTES", "SETTINGS"]
ICONS = {"LOCATION": "📍", "THEME": "🎨", "LAYOUT": "📐", "STYLE": "🔤",
         "LAYERS": "🗂️", "MARKERS": "📌", "ROUTES": "🛣️", "SETTINGS": "⚙️"}
st.session_state.setdefault("panel", "LOCATION")
st.session_state.setdefault("drawings", [])
st.session_state.setdefault("edit_mode", False)
st.session_state.setdefault("recenter", 0)

rail, main, right = st.columns([0.55, 3.6, 1.15], gap="small")

with rail:
    for p in RAIL:
        if st.button(f"{ICONS[p]}\n{p}", key=f"rail_{p}", kind="primary" if st.session_state.panel == p else "secondary"):
            st.session_state.panel = p
            st.rerun()

# ---- gather shared inputs with defaults (persisted) ----
ss = st.session_state
loc = geocode_location(ss.get("query", "Santo Tomas, Philippines")) or {"lat": 15.0141, "lon": 120.7059, "name": "Santo Tomas"}
ss.setdefault("query", "Santo Tomas, Philippines")

with right:
    st.markdown('<div class="tk-card">', unsafe_allow_html=True)
    if ss.panel == "LOCATION":
        q = st.text_input("Location", ss["query"])
        if q != ss["query"]:
            ss["query"] = q; ss["recenter"] += 1; st.rerun()
        st.caption(f"{loc['lat']:.4f}, {loc['lon']:.4f}")
    elif ss.panel == "THEME":
        preset = st.selectbox("Theme", list(THEME_PRESETS.keys()) + ["Custom"],
                              index=list(THEME_PRESETS.keys()).index(ss.get("preset", "Midnight Blue")) if ss.get("preset") != "Custom" else 4)
        if preset != ss.get("preset"):
            ss["preset"] = preset
            if preset != "Custom":
                for k, v in THEME_PRESETS[preset].items(): ss[f"c_{k}"] = v
            st.rerun()
        with st.expander("Color Editor", expanded=False):
            cols = st.columns(2); colors = {}
            for i, k in enumerate(THEME_PRESETS["Carrara"]):
                colors[k] = cols[i % 2].color_picker(k, ss.get(f"c_{k}", THEME_PRESETS["Midnight Blue"][k]), key=f"c_{k}")
            if st.button("Reset All Colors"):
                src = THEME_PRESETS.get(ss.get("preset", "Midnight Blue"), THEME_PRESETS["Midnight Blue"])
                for k, v in src.items(): ss[f"c_{k}"] = v
                st.rerun()
    elif ss.panel == "LAYOUT":
        layout = st.selectbox("Layout", list(LAYOUTS.keys()), index=list(LAYOUTS.keys()).index(ss.get("layout", "Instagram Square")))
        ss["layout"] = layout
        if layout == "Custom":
            ss["W"] = st.number_input("Width px", 400, 4000, ss.get("W", 1080), 20)
            ss["H"] = st.number_input("Height px", 400, 4000, ss.get("H", 1080), 20)
        W, H = (ss.get("W", 1080), ss.get("H", 1080)) if layout == "Custom" else LAYOUTS[layout]
        st.caption(f"Poster size: {W} x {H} px")
    elif ss.panel == "STYLE":
        ss["title"] = st.text_input("Title", ss.get("title", ""))
        ss["subtitle"] = st.text_input("Subtitle", ss.get("subtitle", ""))
        ss["font"] = st.selectbox("Font", list(FONT_FILES.keys()), index=list(FONT_FILES.keys()).index(ss.get("font", "Mono")))
    elif ss.panel == "LAYERS":
        ss["basemap"] = st.selectbox("Basemap", list(BASEMAPS.keys()), index=list(BASEMAPS.keys()).index(ss.get("basemap", "CartoDB Dark Matter")))
        for lyr in ["Water", "Parks", "Buildings", "Roads", "Landcover"]:
            ss.setdefault(f"lyr_{lyr}", True)
            ss[f"lyr_{lyr}"] = st.checkbox(lyr, ss[f"lyr_{lyr}"])
    elif ss.panel == "MARKERS":
        n_mk = sum(1 for f in ss.drawings if f["geometry"]["type"] == "Point")
        st.caption(f"{n_mk} marker(s)")
        ss["mk_stroke"] = st.color_picker("Marker border", ss.get("mk_stroke", "#5b8dd9"))
        ss["mk_fill"] = st.color_picker("Marker fill", ss.get("mk_fill", "#E8B44A"))
        ss["mk_size"] = st.slider("Marker size", 4, 20, ss.get("mk_size", 9))
    elif ss.panel == "ROUTES":
        n_rt = sum(1 for f in ss.drawings if f["geometry"]["type"] != "Point")
        st.caption(f"{n_rt} route/polygon/circle(s)")
        ss["shp_stroke"] = st.color_picker("Border", ss.get("shp_stroke", "#E8B44A"))
        ss["shp_fill"] = st.color_picker("Fill", ss.get("shp_fill", "#0d1626"))
        ss["shp_weight"] = st.slider("Border width", 1, 10, ss.get("shp_weight", 3))
        ss["shp_opacity"] = st.slider("Border opacity", 0.0, 1.0, ss.get("shp_opacity", 1.0))
        ss["shp_fill_op"] = st.slider("Fill opacity", 0.0, 1.0, ss.get("shp_fill_op", 0.3))
    elif ss.panel == "SETTINGS":
        ss["zoom"] = st.slider("Zoom", 10, 18, ss.get("zoom", 13))
        ss["fmt"] = st.radio("Export format", ["PNG", "JPG"], horizontal=True, index=["PNG", "JPG"].index(ss.get("fmt", "PNG")))
    if ss.panel in ("MARKERS", "ROUTES") and st.button("Clear All Drawings"):
        ss["drawings"] = []; st.rerun()
    st.markdown('</div><div class="tk-card tk-ads">ADS KEEP TERRAINK FREE</div>', unsafe_allow_html=True)

# ================================================================ CANVAS
colors = {k: ss.get(f"c_{k}", THEME_PRESETS["Midnight Blue"][k]) for k in THEME_PRESETS["Carrara"]}
layers = {l: ss.get(f"lyr_{l}", True) for l in ["Water", "Parks", "Buildings", "Roads", "Landcover"]}
mk = dict(stroke=ss.get("mk_stroke", "#5b8dd9"), fill=ss.get("mk_fill", "#E8B44A"), size=ss.get("mk_size", 9))
shp = dict(stroke=ss.get("shp_stroke", "#E8B44A"), fill=ss.get("shp_fill", "#0d1626"),
           weight=ss.get("shp_weight", 3), opacity=ss.get("shp_opacity", 1.0), fill_op=ss.get("shp_fill_op", 0.3))
layout = ss.get("layout", "Instagram Square")
W, H = (ss.get("W", 1080), ss.get("H", 1080)) if layout == "Custom" else LAYOUTS[layout]
map_h = {"Instagram Square": 640, "Landscape 16:10": 470, "Portrait 3:4": 720, "Custom": 600}[layout]

m = folium.Map(location=[loc["lat"], loc["lon"]], zoom_start=ss.get("zoom", 13),
               tiles=BASEMAPS[ss.get("basemap", "CartoDB Dark Matter")][0], attr="© OpenStreetMap contributors")
m.get_root().html.add_child(folium.Element(
    f"<style>.leaflet-tile-pane{{filter:{PREVIEW_FILTERS.get(ss.get('preset','Midnight Blue'),'none')};}}"
    "body{background:#0d1626;}"
    ".wm{position:absolute;bottom:6px;font:9px monospace;color:#5f7396;z-index:999;}"
    "</style>"
    '<div class="wm" style="left:8px;">© terraink.app</div>'
    '<div class="wm" style="right:8px;">© OpenStreetMap contributors</div>'))
if ss.edit_mode:
    Draw(export=False, position="topleft").add_to(m)
if ss.drawings:
    folium.GeoJson({"type": "FeatureCollection", "features": ss.drawings},
                   style_function=lambda f: dict(color=shp["stroke"], weight=shp["weight"], opacity=shp["opacity"],
                                                 fillColor=shp["fill"], fillOpacity=shp["fill_op"]),
                   point_to_layer=lambda f, ll: folium.CircleMarker(
                       ll, radius=mk["size"], color=mk["stroke"], weight=2, fill=True,
                       fill_color=mk["fill"], fill_opacity=1.0)).add_to(m)

with main:
    out = st_folium(m, height=map_h, returned_objects=["all_drawings"] if ss.edit_mode else [],
                    key=f"map_{ss['recenter']}")
    new_draws = (out or {}).get("all_drawings") or []
    if new_draws:
        known = {json.dumps(f, sort_keys=True) for f in ss.drawings}
        merged = ss.drawings + [f for f in new_draws if json.dumps(f, sort_keys=True) not in known]
        if len(merged) != len(ss.drawings):
            ss["drawings"] = merged; st.rerun()

    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c2:
        if st.button("⛶ Recenter"):
            ss["recenter"] += 1; st.rerun()
    with c3:
        if st.button("✏️ Edit Map"):
            ss["edit_mode"] = not ss["edit_mode"]; st.rerun()
    with c4:
        if st.button("⬇ Download", type="primary"):
            with st.spinner("Rendering poster…"):
                try:
                    if not OSMNX_OK: raise RuntimeError("osmnx missing")
                    img = render_vector_map(loc["lat"], loc["lon"], ss.get("zoom", 13), W, H - 260, colors, layers, mk, shp, ss.drawings)
                except Exception as e:
                    logger.warning("Vector render failed (%s), raster fallback", e)
                    img = stitch_tiles(loc["lat"], loc["lon"], ss.get("zoom", 13), W, H - 260,
                                       BASEMAPS[ss.get("basemap", "CartoDB Dark Matter")][1])
                poster = compose_poster(img, W, H, colors, ss.get("title", ""), ss.get("subtitle", ""), ss.get("font", "Mono"))
                buf = io.BytesIO()
                if ss.get("fmt", "PNG") == "PNG":
                    poster.save(buf, "PNG"); mime, ext = "image/png", "png"
                else:
                    poster.convert("RGB").save(buf, "JPEG", quality=92); mime, ext = "image/jpeg", "jpg"
                ss["export_bytes"], ss["export_mime"], ss["export_ext"] = buf.getvalue(), mime, ext
                st.rerun()

if ss.get("export_bytes"):
    st.download_button("⬇ DOWNLOAD", ss["export_bytes"], file_name=f"terraink_poster.{ss['export_ext']}",
                       mime=ss["export_mime"], key="dl")

st.markdown("""
<div class="tk-foot">
  <span>hello@terraink.app | Imprint | Data Privacy | Cookie Settings</span>
  <span>Terraink™ v0.4.2 | © 2026 | Made with ♥ in Hannover, Germany</span>
  <span>Map data ©OpenStreetMap contributors</span>
</div>""", unsafe_allow_html=True)

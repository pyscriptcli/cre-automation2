import streamlit as st
import requests
import logging
from maplibre import Map, MapOptions
from maplibre.controls import NavigationControl
from maplibre.streamlit import st_maplibre

# --- CONFIGURATION & LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
st.set_page_config(page_title="Terraink Clone", layout="wide")

# --- STYLING ---
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; margin-bottom: 0; }
    .sub-header { font-size: 1.2rem; color: gray; margin-top: 0; }
    .poster-frame {
        border: 20px solid #ffffff;
        background-color: #ffffff;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        border-radius: 4px;
        margin-bottom: 20px;
    }
    .poster-title {
        font-family: 'Inter', sans-serif;
        text-align: center;
        font-size: 48px;
        font-weight: 900;
        letter-spacing: 4px;
        text-transform: uppercase;
        margin: 0;
    }
    .poster-subtitle {
        text-align: center;
        font-size: 20px;
        font-weight: 300;
        letter-spacing: 1px;
        margin-bottom: 15px;
    }
    /* Hide Streamlit header and footer for cleaner screenshots */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- GEOCODING ENGINE ---
@st.cache_data(ttl=3600)
def geocode_location(query: str) -> dict:
    """Smart geocoding using Nominatim API."""
    if not query: return None
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={query}&limit=1"
    headers = {"User-Agent": "TerrainkStreamlitClone/1.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10).json()
        if res and len(res) > 0:
            return {"lat": float(res[0]["lat"]), "lon": float(res[0]["lon"]), "name": res[0]["display_name"]}
    except Exception as e:
        logger.error(f"Geocoding failed for '{query}': {e}")
    return None

# --- SIDEBAR CONTROLS ---
st.sidebar.title("Cartographic Engine")

search_query = st.sidebar.text_input("Search Location", value="Paris, France")
location_data = geocode_location(search_query)

if not location_data:
    st.sidebar.error("Location not found or geocoding failed. Try a specific city.")
    st.stop()

st.sidebar.markdown(f"**Coordinates:** {location_data['lat']:.4f}, {location_data['lon']:.4f}")

theme_options = {
    "Liberty (Color)": "https://tiles.openfreemap.org/styles/liberty",
    "Bright (Light)": "https://tiles.openfreemap.org/styles/bright",
    "Positron (Minimal)": "https://tiles.openfreemap.org/styles/positron",
    "Dark Matter": "https://tiles.openfreemap.org/styles/dark",
    "Fiord (Dark Blue)": "https://tiles.openfreemap.org/styles/fiord"
}
selected_theme = st.sidebar.selectbox("Map Theme", list(theme_options.keys()))

st.sidebar.subheader("Typography")
poster_title = st.sidebar.text_input("Title", value=search_query.split(",")[0].upper())
poster_subtitle = st.sidebar.text_input("Subtitle", value="City Map Poster")
font_family = st.sidebar.selectbox("Font Family", ["Inter", "Playfair Display", "Roboto", "Georgia"], index=0)

st.sidebar.subheader("Map View")
zoom = st.sidebar.slider("Zoom Level", 10.0, 16.0, 13.5, 0.1)
pitch = st.sidebar.slider("Pitch (3D Angle)", 0, 60, 0)
show_controls = st.sidebar.checkbox("Show Map Controls", value=False)

# --- POSTER RENDERING ---
st.markdown('<div class="poster-frame">', unsafe_allow_html=True)

# Typography Overlay
st.markdown(f"""
    <div class="poster-title" style="font-family: '{font_family}', sans-serif;">{poster_title}</div>
    <div class="poster-subtitle" style="font-family: '{font_family}', sans-serif;">{poster_subtitle}</div>
""", unsafe_allow_html=True)

# MapLibre Engine
map_options = MapOptions(
    style=theme_options[selected_theme],
    center=(location_data['lon'], location_data['lat']),
    zoom=zoom,
    pitch=pitch,
    bearing=0,
    antialias=True
)

m = Map(map_options)
if show_controls:
    m.add_control(NavigationControl())

st_maplibre(m, key="maplibre_poster", height=650)
st.markdown('</div>', unsafe_allow_html=True)

# --- EXPORT INFO ---
st.sidebar.divider()
st.sidebar.subheader("High-Res Export")
st.sidebar.info("""
**Export Workaround:**
Streamlit sandboxes WebGL maps in iframes, blocking direct JS canvas extraction. 
To export high-res posters:
1. Use **Workaround A**: Run a Python `playwright` script to screenshot the `.poster-frame` container.
2. Use **Workaround B**: Use your browser's "Print to PDF" feature on the poster frame.
""")

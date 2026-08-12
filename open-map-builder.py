import streamlit as st
from streamlit_folium import st_folium
import folium
import requests
import logging

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
st.set_page_config(page_title="Terraink Clone", layout="wide")

# --- STYLING ---
st.markdown("""
<style>
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
</style>
""", unsafe_allow_html=True)

# --- GEOCODING ENGINE ---
@st.cache_data(ttl=3600)
def geocode_location(query: str) -> dict:
    if not query: return None
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={query}&limit=1"
    headers = {"User-Agent": "TerrainkStreamlitClone/1.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10).json()
        if res and len(res) > 0:
            return {"lat": float(res[0]["lat"]), "lon": float(res[0]["lon"])}
    except Exception as e:
        logger.error(f"Geocoding failed for '{query}': {e}")
    return None

# --- SIDEBAR CONTROLS ---
st.sidebar.title("Cartographic Engine")
search_query = st.sidebar.text_input("Search Location", value="Paris, France")
location_data = geocode_location(search_query)

if not location_data:
    st.sidebar.error("Location not found. Try a different query.")
    st.stop()

st.sidebar.markdown(f"**Coordinates:** {location_data['lat']:.4f}, {location_data['lon']:.4f}")

basemap_options = {
    "OpenStreetMap": "OpenStreetMap",
    "CartoDB Positron": "CartoDB positron",
    "CartoDB Dark Matter": "CartoDB dark_matter",
    "Esri Satellite": "Esri WorldImagery"
}
selected_basemap = st.sidebar.selectbox("Basemap", list(basemap_options.keys()))

st.sidebar.subheader("Typography")
poster_title = st.sidebar.text_input("Title", value=search_query.split(",")[0].upper())
poster_subtitle = st.sidebar.text_input("Subtitle", value="City Map Poster")
font_family = st.sidebar.selectbox("Font Family", ["Inter", "Playfair Display", "Roboto", "Georgia"], index=0)

st.sidebar.subheader("Map View")
zoom = st.sidebar.slider("Zoom Level", 10, 18, 13, 1)

# --- FOLIUM MAP CREATION ---
m = folium.Map(
    location=[location_data['lat'], location_data['lon']],
    zoom_start=zoom,
    tiles=basemap_options[selected_basemap],
    attr='&copy; OpenStreetMap &copy; CARTO &copy; Esri'
)

# --- POSTER LAYOUT ---
st.markdown('<div class="poster-frame">', unsafe_allow_html=True)

st.markdown(f"""
    <div class="poster-title" style="font-family: '{font_family}', sans-serif;">{poster_title}</div>
    <div class="poster-subtitle" style="font-family: '{font_family}', sans-serif;">{poster_subtitle}</div>
""", unsafe_allow_html=True)

st_folium(m, width=None, height=650, returned_objects=[])

st.markdown('</div>', unsafe_allow_html=True)

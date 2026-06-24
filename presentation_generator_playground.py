import os
import io
import re
import json
import streamlit as st
from pptx import Presentation
from PIL import Image
from datetime import datetime
from docx import Document
import requests
import folium
from streamlit_folium import folium_static
import tempfile
import time
import base64
import urllib.parse

# --- PROGRAMMATIC LIGHT MODE LOCK ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"light\"\n")

# --- MINIMAL UI CSS ---
MINIMAL_CRE_SYSTEM = """
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { margin-top: -50px; }
    .stDeployButton {display: none;}
    .stStatusWidget {display: none;}
    
    .stApp { background-color: #FFFFFF !important; color: #1A1A1A !important; font-family: 'Segoe UI', Arial, sans-serif !important; }
    div[data-testid="stHeader"] { background-color: #FFFFFF !important; display: none !important; }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; max-width: 1200px !important; }
    
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[role="textbox"], div[data-baseweb="select"], textarea {
        background-color: #FFFFFF !important; border: 1px solid #CCCCCC !important; border-radius: 4px !important;
        color: #1A1A1A !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within, textarea:focus { border-color: #003366 !important; box-shadow: none !important; }
    input[type="text"], .stTextInput input, div[data-baseweb="select"] div, textarea { color: #1A1A1A !important; font-size: 14px !important; }
    
    div[data-baseweb="select"] { min-height: 32px !important; }
    div[data-baseweb="select"] > div { min-height: 32px !important; padding: 0 8px !important; }
    div[data-baseweb="select"] select { font-size: 13px !important; padding: 2px 8px !important; }
    svg[data-testid="stSelectbox"] { width: 16px !important; height: 16px !important; }
    div[data-baseweb="select"] svg { width: 16px !important; height: 16px !important; }
    
    section[data-testid="stFileUploader"] { background-color: #F8F8F8 !important; border: 1px solid #CCCCCC !important; border-radius: 4px !important; padding: 4px 12px !important; }
    
    .workspace-card { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 4px; padding: 16px; margin-bottom: 12px; }
    
    div.stButton > button { 
        background-color: #003366 !important; 
        color: #FFFFFF !important; 
        font-weight: 600 !important; 
        font-size: 11px !important; 
        border: none !important; 
        border-radius: 3px !important; 
        padding: 5px 12px !important; 
        width: 100% !important; 
        transition: background-color 0.15s ease; 
        min-height: 28px !important;
    }
    div.stButton > button:hover { 
        background-color: #002244 !important; 
        color: #FFFFFF !important; 
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 51, 102, 0.3);
    }
    div.stButton > button:disabled { 
        background-color: #6688AA !important; 
        color: #CCCCCC !important; 
        cursor: not-allowed !important; 
    }
    
    div[data-testid="stDownloadButton"] > button { 
        background-color: #003366 !important;
        color: #FFFFFF !important;
        border-radius: 3px !important; 
        font-weight: 600 !important; 
        padding: 5px 12px !important; 
        width: 100% !important; 
        transition: all 0.15s ease;
        font-size: 11px !important;
        min-height: 28px !important;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        background-color: #002244 !important;
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 51, 102, 0.3);
    }
    
    div[data-testid="column"] button { 
        background-color: transparent !important; 
        color: #DC3545 !important; 
        border: 1px solid #DC3545 !important; 
        border-radius: 3px !important; 
        padding: 3px 10px !important; 
        font-size: 11px !important; 
        min-height: 26px !important; 
        width: auto !important; 
    }
    div[data-testid="column"] button:hover { 
        background-color: #DC3545 !important; 
        color: white !important; 
    }
    
    .field-label { font-size: 13px !important; font-weight: 600 !important; color: #1A1A1A !important; padding-top: 6px; }
    .section-header { font-size: 15px !important; font-weight: 700 !important; color: #1A1A1A !important; margin-bottom: 10px; }
    .saved-indicator { background-color: #E8F5E9; padding: 6px 12px; border-radius: 4px; font-size: 13px; color: #2E7D32; border-left: 3px solid #2E7D32; margin-top: 6px; }
    
    .map-container { 
        border: 1px solid #E0E0E0; 
        border-radius: 4px; 
        padding: 8px; 
        background-color: #F8F9FA;
        margin: 8px 0;
    }
    .map-saved-indicator {
        background-color: #E3F2FD;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 11px;
        color: #003366;
        border-left: 3px solid #003366;
        margin: 4px 0;
    }
    
    hr { margin: 12px 0 !important; border-color: #E0E0E0 !important; }
    .streamlit-expanderHeader { font-size: 14px !important; font-weight: 600 !important; }
</style>
"""

# --- FILE MANAGEMENT FUNCTIONS ---
def get_storage_dir():
    storage_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stored_templates")
    os.makedirs(storage_dir, exist_ok=True)
    return storage_dir

def save_template_to_file(template_bytes, template_name):
    storage_dir = get_storage_dir()
    safe_name = re.sub(r'[^\w\-_. ]', '_', template_name)
    if not safe_name.endswith('.pptx') and not safe_name.endswith('.docx'):
        safe_name += '.docx'
    filepath = os.path.join(storage_dir, safe_name)
    with open(filepath, 'wb') as f:
        f.write(template_bytes)
    return filepath

def load_template_from_file(template_name):
    storage_dir = get_storage_dir()
    filepath = os.path.join(storage_dir, template_name)
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            return f.read()
    return None

def get_saved_templates():
    storage_dir = get_storage_dir()
    templates = []
    if os.path.exists(storage_dir):
        for file in os.listdir(storage_dir):
            if file.endswith('.pptx') or file.endswith('.docx'):
                filepath = os.path.join(storage_dir, file)
                stat = os.stat(filepath)
                templates.append({
                    'name': file,
                    'path': filepath,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'PPTX' if file.endswith('.pptx') else 'DOCX'
                })
    return templates

def delete_template_file(template_name):
    storage_dir = get_storage_dir()
    filepath = os.path.join(storage_dir, template_name)
    if os.path.exists(filepath):
        os.remove(filepath)
        config_name = template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
        config_path = os.path.join(storage_dir, config_name)
        if os.path.exists(config_path):
            os.remove(config_path)
        return True
    return False

def save_config_to_file(config_data, config_name="template_config.json"):
    storage_dir = get_storage_dir()
    filepath = os.path.join(storage_dir, config_name)
    serializable_config = {}
    for key, value in config_data.items():
        if isinstance(value, dict) and 'screenshot' in value:
            serializable_config[key] = {
                'type': value.get('type', 'Map'),
                'lat': value.get('lat'),
                'lng': value.get('lng'),
                'basemap': value.get('basemap', 'satellite')
            }
        else:
            serializable_config[key] = value
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(serializable_config, f, indent=4)
    return filepath

def load_config_from_file(config_name="template_config.json"):
    storage_dir = get_storage_dir()
    filepath = os.path.join(storage_dir, config_name)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def auto_save_config():
    if st.session_state.saved_template_name and st.session_state.custom_mapping:
        config_name = st.session_state.saved_template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
        save_config_to_file(st.session_state.custom_mapping, config_name)

# --- CORE UTILITIES ---
def smart_crop_to_fit(img_file, target_w_emu, target_h_emu):
    try:
        img = Image.open(img_file)
        img_w, img_h = img.size
        target_ratio = target_w_emu / target_h_emu
        img_ratio = img_w / img_h
        
        if img_ratio > target_ratio:
            new_w = int(img_h * target_ratio)
            left = (img_w - new_w) // 2
            img = img.crop((left, 0, left + new_w, img_h))
        else:
            new_h = int(img_w / target_ratio)
            top = (img_h - new_h) // 2
            img = img.crop((0, top, img_w, top + new_h))
            
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr
    except Exception:
        return img_file

def extract_placeholders_from_pptx(pptx_bytes):
    prs = Presentation(io.BytesIO(pptx_bytes))
    tokens = []
    seen = set()
    
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                found = re.findall(r'\{\{.*?\}\}', shape.text)
                for token in found:
                    if token not in seen:
                        tokens.append(token)
                        seen.add(token)
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        found = re.findall(r'\{\{.*?\}\}', cell.text)
                        for token in found:
                            if token not in seen:
                                tokens.append(token)
                                seen.add(token)
    return tokens

def extract_placeholders_from_docx(docx_bytes):
    doc = Document(io.BytesIO(docx_bytes))
    tokens = []
    seen = set()
    
    for paragraph in doc.paragraphs:
        found = re.findall(r'\{\{.*?\}\}', paragraph.text)
        for token in found:
            if token not in seen:
                tokens.append(token)
                seen.add(token)
    
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                found = re.findall(r'\{\{.*?\}\}', cell.text)
                for token in found:
                    if token not in seen:
                        tokens.append(token)
                        seen.add(token)
    
    return tokens

def extract_placeholders(template_bytes, template_type):
    if template_type == 'pptx':
        return extract_placeholders_from_pptx(template_bytes)
    elif template_type == 'docx':
        return extract_placeholders_from_docx(template_bytes)
    return []

def replace_text_in_paragraph(paragraph, text_inputs):
    for run in paragraph.runs:
        for token, value in text_inputs.items():
            if token in run.text:
                replacement = str(value) if value else ''
                run.text = run.text.replace(token, replacement)
    
    if hasattr(paragraph, 'text') and paragraph.text:
        for token, value in text_inputs.items():
            if token in paragraph.text:
                if not paragraph.runs:
                    paragraph.add_run()
                for run in paragraph.runs:
                    if token in run.text:
                        replacement = str(value) if value else ''
                        run.text = run.text.replace(token, replacement)

def generate_pptx_bytes(template_bytes, text_inputs, image_inputs):
    prs = Presentation(io.BytesIO(template_bytes))
    
    for slide in prs.slides:
        shapes_to_delete = []
        images_to_add = []

        for shape in slide.shapes:
            if shape.has_text_frame:
                text_content = shape.text
                for img_token, img_file in image_inputs.items():
                    if img_token in text_content and img_file is not None:
                        images_to_add.append((img_file, shape.left, shape.top, shape.width, shape.height))
                        shapes_to_delete.append(shape)
                        break

        for shape in slide.shapes:
            if shape not in shapes_to_delete:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        replace_text_in_paragraph(paragraph, text_inputs)
                
                if hasattr(shape, 'table') and shape.table:
                    for row in shape.table.rows:
                        for cell in row.cells:
                            if cell.text_frame:
                                for paragraph in cell.text_frame.paragraphs:
                                    replace_text_in_paragraph(paragraph, text_inputs)

        for img_file, left, top, width, height in images_to_add:
            try:
                processed_img = smart_crop_to_fit(img_file, width, height)
                slide.shapes.add_picture(processed_img, left, top, width=width, height=height)
            except Exception:
                pass

        for old_shape in shapes_to_delete:
            try:
                sp = old_shape._element
                sp.getparent().remove(sp)
            except Exception:
                pass

    pptx_stream = io.BytesIO()
    prs.save(pptx_stream)
    return pptx_stream.getvalue()

def generate_docx_bytes(template_bytes, text_inputs, image_inputs):
    doc = Document(io.BytesIO(template_bytes))
    
    for paragraph in doc.paragraphs:
        has_image = False
        for img_token in image_inputs.keys():
            if img_token in paragraph.text:
                has_image = True
                break
        
        if not has_image:
            replace_text_in_paragraph(paragraph, text_inputs)
    
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    replace_text_in_paragraph(paragraph, text_inputs)
    
    doc_stream = io.BytesIO()
    doc.save(doc_stream)
    doc_stream.seek(0)
    return doc_stream.getvalue()

def get_download_filename(template_name, file_type):
    if template_name:
        base_name = re.sub(r'\.(pptx|docx)$', '', template_name)
        base_name = re.sub(r'[^\w\-_. ]', '_', base_name)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{base_name}_{timestamp}.{file_type}"
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"Generated_Document_{timestamp}.{file_type}"

# --- IMPROVED MAP FUNCTIONALITY ---
def get_basemap_tiles(basemap_choice):
    """Get the appropriate tile layer URL based on basemap choice"""
    basemaps = {
        'satellite': 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        'openstreetmap': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        'carto_light': 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
    }
    return basemaps.get(basemap_choice, basemaps['satellite'])

def capture_map_screenshot_selenium(lat, lng, basemap='satellite', zoom=15):
    """Capture map using selenium with actual map rendering"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        tile_url = get_basemap_tiles(basemap)
        
        # Create HTML with Leaflet map and red pin
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style>
                body, html {{ margin: 0; padding: 0; height: 100%; width: 100%; }}
                #map {{ height: 100vh; width: 100vw; }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var map = L.map('map').setView([{lat}, {lng}], {zoom});
                
                L.tileLayer('{tile_url}', {{
                    maxZoom: 20,
                    attribution: 'Map'
                }}).addTo(map);
                
                // Red pin icon
                var pinIcon = L.divIcon({{
                    html: `
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="32" height="32">
                            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" 
                                  fill="#FF0000" 
                                  stroke="#FFFFFF" 
                                  stroke-width="1.5"/>
                            <circle cx="12" cy="9" r="2" fill="#FFFFFF"/>
                        </svg>
                    `,
                    className: '',
                    iconSize: [32, 32],
                    iconAnchor: [16, 32]
                }});
                
                L.marker([{lat}, {lng}], {{
                    icon: pinIcon,
                    draggable: true
                }}).addTo(map);
                
                // Force map to render
                setTimeout(function() {{
                    map.invalidateSize();
                }}, 500);
            </script>
        </body>
        </html>
        """
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=800,600')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Try to use webdriver_manager first
        driver = None
        try:
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except:
            try:
                driver = webdriver.Chrome(options=chrome_options)
            except:
                # Try with executable path
                driver = webdriver.Chrome(
                    executable_path='/usr/bin/chromium-browser' or '/usr/bin/google-chrome',
                    options=chrome_options
                )
        
        if driver is None:
            return None
        
        # Write HTML to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html)
            html_path = f.name
        
        # Load and wait for map to render
        driver.get(f'file://{html_path}')
        time.sleep(3)  # Wait for tiles to load
        
        # Take screenshot
        screenshot = driver.get_screenshot_as_png()
        driver.quit()
        
        # Clean up
        try:
            os.unlink(html_path)
        except:
            pass
        
        img_byte_arr = io.BytesIO(screenshot)
        img_byte_arr.seek(0)
        return img_byte_arr
        
    except Exception as e:
        print(f"Selenium capture error: {str(e)}")
        return None

def capture_map_screenshot_static(lat, lng, basemap='satellite', zoom=15):
    """Use static map API with proper pin marker"""
    try:
        # Use Google Static Map API with pin
        # Note: This uses a demo key - for production, use your own key
        url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom={zoom}&size=800x600&markers=icon:https://maps.google.com/mapfiles/ms/icons/red-dot.png%7C{lat},{lng}&key=AIzaSyA5oEohxJ-jB5WBR6pR3D8VtaY8X2CkT-8"
        
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            return img_byte_arr
            
    except Exception:
        pass
    
    # Try OpenStreetMap static
    try:
        url = f"https://staticmap.openstreetmap.de/staticmap.php?center={lat},{lng}&zoom={zoom}&size=800x600&maptype=mapnik&markers={lat},{lng},red-pin"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            return img_byte_arr
    except Exception:
        pass
    
    return create_placeholder_map(lat, lng)

def capture_map_screenshot_with_folium(lat, lng, basemap='satellite', zoom=15):
    """Capture map using folium's built-in save functionality"""
    try:
        import folium
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        # Create map with folium
        tile_url = get_basemap_tiles(basemap)
        
        m = folium.Map(
            location=[lat, lng],
            zoom_start=zoom,
            width=800,
            height=600,
            tiles=tile_url,
            attr='Map'
        )
        
        # Add red pin
        pin_svg = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="32" height="32">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" 
                  fill="#FF0000" 
                  stroke="#FFFFFF" 
                  stroke-width="1.5"/>
            <circle cx="12" cy="9" r="2" fill="#FFFFFF"/>
        </svg>
        """
        
        folium.Marker(
            [lat, lng],
            icon=folium.DivIcon(
                html=pin_svg,
                icon_size=(32, 32),
                icon_anchor=(16, 32)
            )
        ).add_to(m)
        
        # Save to temp HTML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            html_path = f.name
            m.save(html_path)
        
        # Take screenshot using selenium
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=800,600')
        
        try:
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except:
            driver = webdriver.Chrome(options=chrome_options)
        
        driver.get(f'file://{html_path}')
        time.sleep(2)
        
        screenshot = driver.get_screenshot_as_png()
        driver.quit()
        
        os.unlink(html_path)
        
        img_byte_arr = io.BytesIO(screenshot)
        img_byte_arr.seek(0)
        return img_byte_arr
        
    except Exception as e:
        print(f"Folium capture error: {str(e)}")
        return None

def create_placeholder_map(lat, lng):
    """Create a placeholder image with red pin"""
    try:
        from PIL import Image, ImageDraw
        
        # Create a nicer placeholder with map-like background
        img = Image.new('RGB', (800, 600), color='#E8EDF2')
        draw = ImageDraw.Draw(img)
        
        # Draw grid lines for map feel
        for i in range(0, 800, 50):
            draw.line([(i, 0), (i, 600)], fill='#D0D5DB', width=1)
        for i in range(0, 600, 50):
            draw.line([(0, i), (800, i)], fill='#D0D5DB', width=1)
        
        # Draw border
        draw.rectangle([10, 10, 790, 590], outline='#003366', width=2)
        
        # Draw red pin
        pin_x, pin_y = 400, 250
        
        # Pin shadow
        draw.ellipse([pin_x-12, pin_y+25, pin_x+12, pin_y+40], fill='#B0B8C0')
        
        # Pin body (triangle)
        draw.polygon([
            (pin_x, pin_y-20),
            (pin_x-15, pin_y+10),
            (pin_x+15, pin_y+10)
        ], fill='#FF0000', outline='#CC0000')
        
        # Pin head (circle)
        draw.ellipse([pin_x-10, pin_y-10, pin_x+10, pin_y+10], fill='#FFFFFF', outline='#CC0000')
        draw.ellipse([pin_x-5, pin_y-5, pin_x+5, pin_y+5], fill='#FF0000')
        
        # Coordinates text with background
        coords_text = f"Lat: {lat:.6f}, Lng: {lng:.6f}"
        text_bbox = draw.textbbox((0, 0), coords_text)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (800 - text_width) // 2
        text_y = 400
        
        # Text background
        draw.rectangle([text_x-10, text_y-5, text_x+text_width+10, text_y+text_height+5], 
                       fill='#FFFFFF', outline='#003366')
        draw.text((text_x, text_y), coords_text, fill='#003366')
        
        # Location label
        draw.text((370, 440), "Location Pin", fill='#003366')
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr
        
    except Exception as e:
        # Ultimate fallback - simple placeholder
        img = Image.new('RGB', (800, 600), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        draw.text((300, 280), f"Location: {lat:.6f}, {lng:.6f}", fill='#000000')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr

def capture_map_screenshot(lat, lng, basemap='satellite', zoom=15):
    """Try multiple capture methods in order"""
    
    # Method 1: Try with Folium + Selenium (most reliable for actual map)
    result = capture_map_screenshot_with_folium(lat, lng, basemap, zoom)
    if result is not None:
        return result
    
    # Method 2: Try direct Selenium with HTML
    result = capture_map_screenshot_selenium(lat, lng, basemap, zoom)
    if result is not None:
        return result
    
    # Method 3: Try static API
    result = capture_map_screenshot_static(lat, lng, basemap, zoom)
    if result is not None:
        return result
    
    # Method 4: Create placeholder
    return create_placeholder_map(lat, lng)

def parse_coordinates(coord_string):
    """Parse coordinates from a string format: 'lat, lon'"""
    match = re.match(r'^\s*(-?\d+(?:\.\d+)?)\s*[,;]\s*(-?\d+(?:\.\d+)?)\s*$', coord_string.strip())
    if match:
        lat = float(match.group(1))
        lon = float(match.group(2))
        return lat, lon
    return None, None

def map_input_component(token, clean_label, default_lat=14.5995, default_lng=120.9842):
    """Interactive map input with draggable red pin marker"""
    
    map_key = f"map_{token}"
    
    # Initialize session state for this map
    if map_key not in st.session_state:
        st.session_state[map_key] = {
            "lat": default_lat,
            "lng": default_lng,
            "screenshot": None,
            "saved": False,
            "basemap": "satellite"
        }
    
    st.markdown(f'<div class="field-label">{clean_label}</div>', unsafe_allow_html=True)
    
    # Display current saved status
    if st.session_state[map_key]["saved"]:
        st.markdown(
            f'<div class="map-saved-indicator">Location saved: {st.session_state[map_key]["lat"]:.6f}, {st.session_state[map_key]["lng"]:.6f}</div>', 
            unsafe_allow_html=True
        )
    
    # Basemap selection
    col_basemap, col_spacer = st.columns([2, 1])
    with col_basemap:
        basemap_choice = st.selectbox(
            "Basemap",
            ["satellite", "openstreetmap", "carto_light"],
            index=["satellite", "openstreetmap", "carto_light"].index(
                st.session_state[map_key].get("basemap", "satellite")
            ),
            key=f"basemap_{token}",
            label_visibility="collapsed"
        )
        if basemap_choice != st.session_state[map_key].get("basemap", "satellite"):
            st.session_state[map_key]["basemap"] = basemap_choice
    
    # Single coordinate field
    default_coords = f"{st.session_state[map_key]['lat']:.6f}, {st.session_state[map_key]['lng']:.6f}"
    coords_input = st.text_input(
        "Coordinates (lat, lon)",
        value=default_coords,
        key=f"coords_{token}",
        help="Enter coordinates in format: lat, lon",
        placeholder="e.g., 14.5995, 120.9842"
    )
    
    # Parse coordinates
    lat, lng = parse_coordinates(coords_input)
    if lat is not None and lng is not None:
        st.session_state[map_key]["lat"] = lat
        st.session_state[map_key]["lng"] = lng
    
    # Action buttons
    col_save, col_preview, col_clear = st.columns([1, 1, 1])
    with col_save:
        if st.button("Save Location", key=f"save_map_{token}", use_container_width=True):
            if lat is not None and lng is not None:
                st.session_state[map_key]["lat"] = lat
                st.session_state[map_key]["lng"] = lng
                st.session_state[map_key]["saved"] = True
                st.session_state[map_key]["basemap"] = basemap_choice
                
                with st.spinner("Capturing map..."):
                    screenshot = capture_map_screenshot(
                        lat, 
                        lng, 
                        basemap_choice,
                        zoom=15
                    )
                    st.session_state[map_key]["screenshot"] = screenshot
                    st.success("Location saved with screenshot!")
                
                auto_save_config()
                st.rerun()
            else:
                st.warning("Please enter valid coordinates")
    
    with col_preview:
        if st.button("Preview", key=f"preview_map_{token}", use_container_width=True):
            if lat is not None and lng is not None:
                with st.spinner("Capturing preview..."):
                    screenshot = capture_map_screenshot(
                        lat, 
                        lng, 
                        basemap_choice,
                        zoom=15
                    )
                    st.session_state[f"preview_{token}"] = screenshot
                    st.rerun()
            else:
                st.warning("Please enter valid coordinates")
    
    with col_clear:
        if st.button("Clear", key=f"clear_map_{token}", use_container_width=True):
            st.session_state[map_key]["saved"] = False
            st.session_state[map_key]["screenshot"] = None
            if f"preview_{token}" in st.session_state:
                del st.session_state[f"preview_{token}"]
            st.rerun()
    
    # Show preview if available
    preview_key = f"preview_{token}"
    if preview_key in st.session_state and st.session_state[preview_key] is not None:
        st.image(st.session_state[preview_key], caption="Map Preview", use_container_width=True)
    
    # Interactive map with draggable red pin
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    
    try:
        current_lat = st.session_state[map_key]["lat"]
        current_lng = st.session_state[map_key]["lng"]
        
        tile_url = get_basemap_tiles(basemap_choice)
        
        # Create map
        m = folium.Map(
            location=[current_lat, current_lng],
            zoom_start=14,
            width='100%',
            height=450,
            tiles=tile_url,
            attr='Map'
        )
        
        # Red pin SVG marker
        pin_svg = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="32" height="32">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" 
                  fill="#FF0000" 
                  stroke="#FFFFFF" 
                  stroke-width="1.5"/>
            <circle cx="12" cy="9" r="2" fill="#FFFFFF"/>
        </svg>
        """
        
        # Add draggable pin marker
        marker = folium.Marker(
            [current_lat, current_lng],
            popup=f"{clean_label}<br>{current_lat:.6f}, {current_lng:.6f}",
            icon=folium.DivIcon(
                html=pin_svg,
                icon_size=(32, 32),
                icon_anchor=(16, 32),
                popup_anchor=(0, -32)
            ),
            draggable=True
        ).add_to(m)
        
        folium_static(m, width=700, height=450)
        st.caption("Drag the red pin or click on the map to set location, then click Save Location")
        
    except Exception as e:
        st.warning(f"Map display limited: {str(e)}")
        st.info("Enter coordinates manually and click Save Location")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Return screenshot if saved
    if st.session_state[map_key]["saved"] and st.session_state[map_key]["screenshot"] is not None:
        return st.session_state[map_key]["screenshot"]
    return None

def simple_uploader_row(label_text, allowed_types, key):
    st.markdown(f'<div class="field-label">{label_text}</div>', unsafe_allow_html=True)
    return st.file_uploader(label_text, type=allowed_types, key=f"val_{key}", label_visibility="collapsed")

# --- INIT APP ---
st.set_page_config(page_title="OpenFlux - Template Automation", layout="wide", initial_sidebar_state="collapsed")
st.markdown(MINIMAL_CRE_SYSTEM, unsafe_allow_html=True)

# Initialize session state
if "custom_mapping" not in st.session_state:
    st.session_state.custom_mapping = {}
if "tokens" not in st.session_state:
    st.session_state.tokens = []
if "template_bytes" not in st.session_state:
    st.session_state.template_bytes = None
if "saved_template_name" not in st.session_state:
    st.session_state.saved_template_name = None
if "template_loaded" not in st.session_state:
    st.session_state.template_loaded = False
if "template_type" not in st.session_state:
    st.session_state.template_type = None
if "delete_trigger" not in st.session_state:
    st.session_state.delete_trigger = False
if "show_delete_confirm" not in st.session_state:
    st.session_state.show_delete_confirm = False
if "template_to_delete" not in st.session_state:
    st.session_state.template_to_delete = None
if "save_success" not in st.session_state:
    st.session_state.save_success = False
if "saved_file_name" not in st.session_state:
    st.session_state.saved_file_name = None
if "clear_uploader" not in st.session_state:
    st.session_state.clear_uploader = False
if "map_data" not in st.session_state:
    st.session_state.map_data = {}

# --- MAIN UI ---
st.markdown("<hr style='margin: 4px 0 12px 0;'>", unsafe_allow_html=True)

# Template Management
st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
st.markdown('<div class="section-header">Template Management</div>', unsafe_allow_html=True)

col_template1, col_template2 = st.columns(2)

with col_template1:
    saved_templates = get_saved_templates()
    template_options = ["Select saved template"]
    if saved_templates:
        for t in saved_templates:
            template_options.append(f"{t['name']} ({t['type']})")
    
    dropdown_col, delete_col = st.columns([4, 1])
    
    with dropdown_col:
        selected_template = st.selectbox(
            "Load Template",
            template_options,
            key="saved_template_select",
            label_visibility="collapsed"
        )
    
    with delete_col:
        if selected_template and selected_template != "Select saved template":
            template_name = selected_template.split(' (')[0]
            if st.button("Delete", key="delete_template", help="Delete this template"):
                st.session_state.show_delete_confirm = True
                st.session_state.template_to_delete = template_name
                st.rerun()
    
    if st.session_state.show_delete_confirm:
        st.warning(f"Are you sure you want to delete '{st.session_state.template_to_delete}'?")
        col_confirm1, col_confirm2 = st.columns([1, 1])
        with col_confirm1:
            if st.button("Yes, Delete", key="confirm_delete"):
                if delete_template_file(st.session_state.template_to_delete):
                    st.session_state.delete_trigger = True
                    st.session_state.template_bytes = None
                    st.session_state.saved_template_name = None
                    st.session_state.template_loaded = False
                    st.session_state.tokens = []
                    st.session_state.show_delete_confirm = False
                    st.session_state.template_to_delete = None
                    st.success(f"Deleted: {st.session_state.template_to_delete}")
                    st.rerun()
        with col_confirm2:
            if st.button("Cancel", key="cancel_delete"):
                st.session_state.show_delete_confirm = False
                st.session_state.template_to_delete = None
                st.rerun()
    
    if selected_template and selected_template != "Select saved template" and not st.session_state.delete_trigger:
        template_name = selected_template.split(' (')[0]
        template_bytes = load_template_from_file(template_name)
        if template_bytes:
            st.session_state.template_bytes = template_bytes
            st.session_state.saved_template_name = template_name
            st.session_state.template_loaded = True
            st.session_state.template_type = 'pptx' if template_name.endswith('.pptx') else 'docx'
            
            config_name = template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
            config_data = load_config_from_file(config_name)
            if config_data:
                st.session_state.custom_mapping = config_data
            
            tokens = extract_placeholders(template_bytes, st.session_state.template_type)
            st.session_state.tokens = tokens

with col_template2:
    uploader_key = "new_template_upload_clear" if st.session_state.clear_uploader else "new_template_upload"
    
    uploaded_template = st.file_uploader(
        "Upload New Template", 
        type=["pptx", "docx"], 
        label_visibility="collapsed", 
        key=uploader_key
    )
    
    if st.session_state.clear_uploader:
        st.session_state.clear_uploader = False
    
    if uploaded_template:
        template_bytes = uploaded_template.getvalue()
        st.session_state.template_bytes = template_bytes
        st.session_state.saved_template_name = None
        st.session_state.template_loaded = True
        st.session_state.template_type = 'pptx' if uploaded_template.name.endswith('.pptx') else 'docx'
        
        tokens = extract_placeholders(template_bytes, st.session_state.template_type)
        st.session_state.tokens = tokens
        
        if st.button("Save Template", key="save_template_btn", use_container_width=True):
            saved_path = save_template_to_file(template_bytes, uploaded_template.name)
            st.session_state.saved_template_name = uploaded_template.name
            
            if st.session_state.custom_mapping:
                config_name = uploaded_template.name.replace('.pptx', '').replace('.docx', '') + '_config.json'
                save_config_to_file(st.session_state.custom_mapping, config_name)
            
            st.session_state.save_success = True
            st.session_state.saved_file_name = uploaded_template.name
            st.session_state.clear_uploader = True
            st.rerun()

if st.session_state.save_success:
    st.success(f"Template '{st.session_state.saved_file_name}' saved successfully!")
    st.session_state.save_success = False
    st.session_state.saved_file_name = None

if st.session_state.template_bytes is not None:
    template_name = st.session_state.saved_template_name or "Unsaved Template"
    template_type = st.session_state.template_type or "Unknown"
    st.markdown(f'<div class="saved-indicator">Active: {template_name} ({template_type.upper()})</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Placeholder Values
template_bytes = st.session_state.template_bytes
template_type = st.session_state.template_type
u_template = None
if template_bytes is not None:
    u_template = type('obj', (object,), {'getvalue': lambda: template_bytes})()

text_data = {}
image_data = {}
map_data = {}
field_types = {}

if u_template is not None and st.session_state.tokens:
    tokens = st.session_state.tokens
    
    if not tokens:
        st.info("No placeholders found in the template.")
    else:
        st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Placeholder Values</div>', unsafe_allow_html=True)
        st.info(f"Found {len(tokens)} placeholders. Select type: Text, Image, or Map")
        
        mid_point = len(tokens) // 2
        col1, col2 = st.columns(2)
        
        with col1:
            for token in tokens[:mid_point]:
                clean_label = token.replace("{", "").replace("}", "")
                current_type = st.session_state.custom_mapping.get(token, "Text")
                col_a, col_b = st.columns([3, 1])
                
                with col_b:
                    st.markdown('<div style="padding-top: 6px;"></div>', unsafe_allow_html=True)
                    type_key = f"type_{token}"
                    data_type = st.selectbox(
                        "Type",
                        ["Text", "Image", "Map"],
                        index=0 if current_type == "Text" else (1 if current_type == "Image" else 2),
                        key=type_key,
                        label_visibility="collapsed"
                    )
                    if data_type != current_type:
                        st.session_state.custom_mapping[token] = data_type
                        auto_save_config()
                        st.rerun()
                
                with col_a:
                    if data_type == "Image" and template_type == 'pptx':
                        image_data[token] = simple_uploader_row(clean_label, ["png", "jpg", "jpeg"], token)
                        field_types[token] = "Image"
                        st.caption("Upload image (PNG, JPG)")
                    elif data_type == "Map":
                        st.session_state.map_data[token] = map_input_component(token, clean_label)
                        field_types[token] = "Map"
                        st.caption("Drag red pin or click map to set location, click Save Location")
                    else:
                        if data_type == "Image" and template_type != 'pptx':
                            st.warning("Image replacement only supported in PPTX templates")
                        st.markdown(f'<div class="field-label">{clean_label}</div>', unsafe_allow_html=True)
                        text_data[token] = st.text_input(
                            clean_label, 
                            key=f"val_{token}", 
                            label_visibility="collapsed"
                        )
                        field_types[token] = "Text"
        
        with col2:
            for token in tokens[mid_point:]:
                clean_label = token.replace("{", "").replace("}", "")
                current_type = st.session_state.custom_mapping.get(token, "Text")
                col_a, col_b = st.columns([3, 1])
                
                with col_b:
                    st.markdown('<div style="padding-top: 6px;"></div>', unsafe_allow_html=True)
                    type_key = f"type_{token}_2"
                    data_type = st.selectbox(
                        "Type",
                        ["Text", "Image", "Map"],
                        index=0 if current_type == "Text" else (1 if current_type == "Image" else 2),
                        key=type_key,
                        label_visibility="collapsed"
                    )
                    if data_type != current_type:
                        st.session_state.custom_mapping[token] = data_type
                        auto_save_config()
                        st.rerun()
                
                with col_a:
                    if data_type == "Image" and template_type == 'pptx':
                        image_data[token] = simple_uploader_row(clean_label, ["png", "jpg", "jpeg"], token)
                        field_types[token] = "Image"
                        st.caption("Upload image (PNG, JPG)")
                    elif data_type == "Map":
                        st.session_state.map_data[token] = map_input_component(token, clean_label)
                        field_types[token] = "Map"
                        st.caption("Drag red pin or click map to set location, click Save Location")
                    else:
                        if data_type == "Image" and template_type != 'pptx':
                            st.warning("Image replacement only supported in PPTX templates")
                        st.markdown(f'<div class="field-label">{clean_label}</div>', unsafe_allow_html=True)
                        text_data[token] = st.text_input(
                            clean_label, 
                            key=f"val_{token}", 
                            label_visibility="collapsed"
                        )
                        field_types[token] = "Text"
        
        st.markdown('</div>', unsafe_allow_html=True)

# Download Section
if u_template is not None:
    st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Download Document</div>', unsafe_allow_html=True)
    
    # Merge map screenshots into image_data
    for token, map_screenshot in st.session_state.map_data.items():
        if map_screenshot is not None:
            image_data[token] = map_screenshot
    
    template_name = st.session_state.saved_template_name or "Generated_Document"
    base_template_name = re.sub(r'\.(pptx|docx)$', '', template_name)
    
    col1, col2 = st.columns(2)
    
    with col1:
        pptx_disabled = template_type != 'pptx'
        if pptx_disabled:
            st.button("Download PPTX", disabled=True, use_container_width=True, help="Only available for PPTX templates")
        else:
            try:
                pptx_data = generate_pptx_bytes(template_bytes, text_data, image_data)
                pptx_filename = get_download_filename(base_template_name, "pptx")
                st.download_button(
                    label="Download PPTX",
                    data=pptx_data,
                    file_name=pptx_filename,
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True,
                    key="download_pptx"
                )
            except Exception as e:
                st.error(f"Error generating PPTX: {str(e)}")
    
    with col2:
        docx_disabled = template_type != 'docx'
        if docx_disabled:
            st.button("Download DOCX", disabled=True, use_container_width=True, help="Only available for DOCX templates")
        else:
            try:
                docx_data = generate_docx_bytes(template_bytes, text_data, image_data)
                if docx_data:
                    docx_filename = get_download_filename(base_template_name, "docx")
                    st.download_button(
                        label="Download DOCX",
                        data=docx_data,
                        file_name=docx_filename,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                        key="download_docx"
                    )
                else:
                    st.error("Failed to generate document.")
            except Exception as e:
                st.error(f"Error generating document: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Please upload or select a template to begin")

st.markdown("---")
st.caption("OpenFlux v2.0 | Template Automation with Draggable Map Pins")

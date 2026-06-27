import streamlit as st
import folium
from streamlit_folium import folium_static
import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime
import re
import time
from branca.colormap import LinearColormap
from folium.plugins import Fullscreen, MarkerCluster, BeautifyIcon
import base64
from pathlib import Path
import os
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import random

# Page configuration
st.set_page_config(
    page_title="Open Node",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&display=swap');
    
    .main {
        padding: 0rem 0rem;
    }
    .stApp {
        background-color: #f5f5f5;
    }
    .css-1d391kg {
        padding-top: 0rem;
    }
    
    /* Brand Header */
    .brand-header {
        background: linear-gradient(135deg, #003366 0%, #001a33 100%);
        padding: 20px 20px 15px 20px;
        border-radius: 8px 8px 0 0;
        margin: -10px -20px 20px -20px;
        text-align: center;
        border-bottom: 3px solid #C9AB4C;
    }
    .brand-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 32px;
        font-weight: 600;
        color: #C9AB4C;
        margin: 0;
        letter-spacing: 2px;
    }
    .brand-subtitle {
        font-family: 'Montserrat', sans-serif;
        font-size: 12px;
        color: #88aacc;
        letter-spacing: 4px;
        margin-top: 4px;
    }
    
    /* Sidebar styling */
    .css-1kyxreq {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
    .sidebar-section {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 6px;
        margin-bottom: 15px;
        border-left: 3px solid #003366;
    }
    .section-title {
        font-family: 'Montserrat', sans-serif;
        font-size: 14px;
        font-weight: 600;
        color: #003366;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    /* Buttons */
    .stButton > button {
        font-family: 'Montserrat', sans-serif;
        font-weight: 600;
        border-radius: 4px;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,51,102,0.2);
    }
    .primary-btn > button {
        background-color: #003366;
        color: white;
        border: none;
    }
    .primary-btn > button:hover {
        background-color: #004488;
    }
    .gold-btn > button {
        background-color: #C9AB4C;
        color: white;
        border: none;
    }
    .gold-btn > button:hover {
        background-color: #d4b85a;
    }
    
    /* Stats */
    .stat-box {
        background: white;
        padding: 10px;
        border-radius: 4px;
        text-align: center;
        border: 1px solid #e0e0e0;
        margin: 5px 0;
    }
    .stat-number {
        font-family: 'Montserrat', sans-serif;
        font-size: 24px;
        font-weight: 700;
        color: #003366;
    }
    .stat-label {
        font-family: 'Montserrat', sans-serif;
        font-size: 11px;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Logs */
    .log-container {
        background: #1a1a1a;
        color: #00ff00;
        padding: 10px;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 11px;
        max-height: 200px;
        overflow-y: auto;
        margin-top: 10px;
    }
    .log-entry {
        padding: 2px 0;
        border-bottom: 1px solid #2a2a2a;
    }
    .log-time {
        color: #888;
        margin-right: 8px;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb {
        background: #003366;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #004488;
    }
    
    /* Map container */
    .map-container {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 12px rgba(0,0,0,0.1);
        background: white;
        padding: 10px;
        margin: 10px 0;
    }
    
    /* Search bar */
    .search-input > div > div > input {
        font-family: 'Montserrat', sans-serif;
        border-radius: 4px;
        border: 2px solid #003366;
        padding: 10px;
    }
    .search-input > div > div > input:focus {
        border-color: #C9AB4C;
        box-shadow: 0 0 0 2px rgba(201,171,76,0.2);
    }
    
    /* Tags */
    .tag {
        display: inline-block;
        background: #e8edf2;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 12px;
        color: #003366;
        margin: 2px;
        font-family: 'Montserrat', sans-serif;
    }
    .tag-gold {
        background: #C9AB4C;
        color: white;
    }
    
    /* Status indicators */
    .status-online {
        color: #00cc44;
        font-weight: 600;
    }
    .status-offline {
        color: #ff4444;
        font-weight: 600;
    }
    .status-unknown {
        color: #ffaa00;
        font-weight: 600;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .brand-title {
            font-size: 24px;
        }
        .sidebar-section {
            padding: 10px;
        }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'scanned_records': [],
        'layer_meta': {},
        'layer_groups': {},
        'search_history': [],
        'map_viewport': {'center': [14.5995, 120.9842], 'zoom': 13},
        'geo_coords': "14.5995, 120.9842",
        'geo_radius': 1000,
        'label_size': 9,
        'marker_style': "modern-pin",
        'marker_size': 16,
        'marker_color': "#003366",
        'fullscreen_active': False,
        'sidebar_collapsed': False,
        'poi_visibility': {},
        'current_query': "",
        'session_logs': [],
        'last_scan_time': None,
        'poi_count': 0,
        'map_click_coords': None,
        'selected_poi': None,
        'imported_state': None,
        'overpass_status': {},
        'active_endpoint': None,
        'query_time': None,
        'retry_count': 0
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============================================================================
# OVERPASS API CONFIGURATION
# ============================================================================

class OverpassAPI:
    """Handles Overpass API queries with multi-endpoint support"""
    
    # Comprehensive list of Overpass endpoints
    ENDPOINTS = [
        {
            'url': 'https://overpass-api.de/api/interpreter',
            'name': 'Overpass API (Germany)',
            'priority': 1,
            'timeout': 30,
            'max_retries': 3
        },
        {
            'url': 'https://overpass.kumi.systems/api/interpreter',
            'name': 'Overpass API (Kumi)',
            'priority': 2,
            'timeout': 30,
            'max_retries': 3
        },
        {
            'url': 'https://overpass.openstreetmap.fr/api/interpreter',
            'name': 'Overpass API (France)',
            'priority': 3,
            'timeout': 30,
            'max_retries': 3
        },
        {
            'url': 'https://overpass.osm.ch/api/interpreter',
            'name': 'Overpass API (Switzerland)',
            'priority': 4,
            'timeout': 30,
            'max_retries': 3
        },
        {
            'url': 'https://overpass.omniscale.net/api/interpreter',
            'name': 'Overpass API (Omniscale)',
            'priority': 5,
            'timeout': 30,
            'max_retries': 3
        },
        {
            'url': 'https://overpass.private.coffee/api/interpreter',
            'name': 'Overpass API (Private Coffee)',
            'priority': 6,
            'timeout': 30,
            'max_retries': 3
        }
    ]
    
    def __init__(self):
        self.endpoints = self.ENDPOINTS.copy()
        self.active_endpoint = None
        self.status = {}
        self.query_times = []
        
        # Initialize status tracking
        for endpoint in self.endpoints:
            self.status[endpoint['url']] = {
                'online': None,
                'last_check': None,
                'response_time': None,
                'error_count': 0,
                'success_count': 0
            }
    
    def get_headers(self):
        """Get headers for API requests"""
        return {
            'User-Agent': 'OpenNode-POI-Explorer/1.0 (https://github.com/opennode)',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        }
    
    def test_endpoint(self, endpoint: Dict) -> bool:
        """Test if an endpoint is responsive"""
        try:
            # Simple test query (just get a single node)
            test_query = """
            [out:json][timeout:5];
            node(1);
            out body;
            """
            
            response = requests.post(
                endpoint['url'],
                data={'data': test_query},
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                self.status[endpoint['url']]['online'] = True
                self.status[endpoint['url']]['last_check'] = datetime.now()
                self.status[endpoint['url']]['response_time'] = response.elapsed.total_seconds()
                return True
            else:
                self.status[endpoint['url']]['online'] = False
                return False
                
        except Exception as e:
            self.status[endpoint['url']]['online'] = False
            self.status[endpoint['url']]['error_count'] += 1
            return False
    
    def get_best_endpoint(self) -> Optional[Dict]:
        """Get the best available endpoint based on status and priority"""
        # First check if we have a working endpoint
        working_endpoints = []
        
        for endpoint in self.endpoints:
            if self.status[endpoint['url']].get('online', False):
                # Check if it's been tested recently (within last 5 minutes)
                last_check = self.status[endpoint['url']].get('last_check')
                if last_check:
                    time_diff = (datetime.now() - last_check).total_seconds()
                    if time_diff < 300:  # 5 minutes
                        working_endpoints.append(endpoint)
        
        # If we have working endpoints, return the highest priority one
        if working_endpoints:
            return min(working_endpoints, key=lambda x: x['priority'])
        
        # Otherwise, test endpoints in priority order
        for endpoint in sorted(self.endpoints, key=lambda x: x['priority']):
            if self.test_endpoint(endpoint):
                return endpoint
        
        # If all endpoints fail, return the first one (will fail but at least try)
        return self.endpoints[0] if self.endpoints else None
    
    def execute_query(self, query: str, max_retries: int = 3) -> Tuple[Optional[List[Dict]], str]:
        """
        Execute a query against the Overpass API with retry logic
        
        Returns: (data, endpoint_used)
        """
        # Get best endpoint
        endpoint = self.get_best_endpoint()
        if not endpoint:
            return None, "No endpoints available"
        
        # Try the query with retries
        for attempt in range(max_retries):
            try:
                add_log(f"Querying {endpoint['name']} (attempt {attempt + 1}/{max_retries})", "INFO")
                
                response = requests.post(
                    endpoint['url'],
                    data={'data': query},
                    headers=self.get_headers(),
                    timeout=endpoint.get('timeout', 30)
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Update status
                    self.status[endpoint['url']]['online'] = True
                    self.status[endpoint['url']]['last_check'] = datetime.now()
                    self.status[endpoint['url']]['response_time'] = response.elapsed.total_seconds()
                    self.status[endpoint['url']]['success_count'] += 1
                    
                    self.active_endpoint = endpoint['url']
                    self.query_times.append(response.elapsed.total_seconds())
                    if len(self.query_times) > 100:
                        self.query_times = self.query_times[-100:]
                    
                    add_log(f"Query successful: {len(data.get('elements', []))} elements found", "SUCCESS")
                    return data, endpoint['name']
                    
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    wait_time = 2 ** attempt
                    add_log(f"Rate limited, waiting {wait_time}s", "WARNING")
                    time.sleep(wait_time)
                    
                elif response.status_code == 504:
                    # Gateway timeout - try next endpoint
                    add_log(f"Gateway timeout, trying next endpoint", "WARNING")
                    self.status[endpoint['url']]['online'] = False
                    endpoint = self.get_best_endpoint()
                    if not endpoint:
                        break
                    
                else:
                    add_log(f"API returned {response.status_code}", "WARNING")
                    self.status[endpoint['url']]['error_count'] += 1
                    
                    # If too many errors, mark as offline
                    if self.status[endpoint['url']]['error_count'] > 5:
                        self.status[endpoint['url']]['online'] = False
                    
                    # Try next endpoint
                    endpoint = self.get_best_endpoint()
                    if not endpoint:
                        break
                    
            except requests.exceptions.Timeout:
                add_log(f"Timeout with {endpoint['name']}", "WARNING")
                self.status[endpoint['url']]['error_count'] += 1
                if self.status[endpoint['url']]['error_count'] > 3:
                    self.status[endpoint['url']]['online'] = False
                endpoint = self.get_best_endpoint()
                
            except requests.exceptions.ConnectionError:
                add_log(f"Connection error with {endpoint['name']}", "ERROR")
                self.status[endpoint['url']]['online'] = False
                endpoint = self.get_best_endpoint()
                
            except Exception as e:
                add_log(f"Error: {str(e)}", "ERROR")
                endpoint = self.get_best_endpoint()
            
            # Small delay between retries
            if attempt < max_retries - 1:
                time.sleep(1)
        
        return None, "All endpoints failed"

# Initialize Overpass API
overpass_api = OverpassAPI()

# ============================================================================
# LOGGING SYSTEM
# ============================================================================

def add_log(message: str, level: str = "INFO"):
    """Add a log entry to session state"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        'time': timestamp,
        'message': message,
        'level': level
    }
    st.session_state.session_logs.insert(0, log_entry)
    # Keep only last 100 logs
    if len(st.session_state.session_logs) > 100:
        st.session_state.session_logs = st.session_state.session_logs[:100]

# ============================================================================
# SEARCH QUERY PARSING
# ============================================================================

def parse_search_query(query: str) -> List[str]:
    """Parse comma-separated OSM tags into a list"""
    if not query or not query.strip():
        return []
    
    # Split by comma and clean
    tags = [tag.strip() for tag in query.split(',') if tag.strip()]
    
    # Validate tag format (key=value)
    valid_tags = []
    for tag in tags:
        if '=' in tag:
            valid_tags.append(tag)
        else:
            add_log(f"Invalid tag format: {tag} (expected key=value)", "WARNING")
    
    return valid_tags

def build_overpass_query(tags: List[str], center_lat: float, center_lon: float, radius: int) -> str:
    """Build Overpass QL query from tags with optimized structure"""
    if not tags:
        return None
    
    # Build filter conditions with proper escaping
    filters = []
    for tag in tags:
        key, value = tag.split('=', 1)
        # Handle wildcard values
        if '*' in value:
            # Use regex for wildcard
            regex_pattern = value.replace('*', '.*')
            filters.append(f'[~"{key}"~"{regex_pattern}"]')
        else:
            # Escape special characters in value
            escaped_value = value.replace('"', '\\"')
            filters.append(f'["{key}"="{escaped_value}"]')
    
    # Build optimized query with bbox for efficiency
    # Calculate bbox from center and radius
    lat_offset = radius / 111000.0  # Rough conversion
    lon_offset = radius / (111000.0 * np.cos(np.radians(center_lat)))
    
    bbox = (
        center_lat - lat_offset,
        center_lon - lon_offset,
        center_lat + lat_offset,
        center_lon + lon_offset
    )
    
    filter_str = ''.join(filters)
    
    # Build query with bbox and around for maximum results
    query = f"""
    [out:json][timeout:25];
    (
      node{filter_str}({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
      way{filter_str}({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
      rel{filter_str}({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
    );
    out body;
    >;
    out skel qt;
    """
    
    # Alternative query using around for better precision
    query_around = f"""
    [out:json][timeout:25];
    (
      node{filter_str}(around:{radius},{center_lat},{center_lon});
      way{filter_str}(around:{radius},{center_lat},{center_lon});
      rel{filter_str}(around:{radius},{center_lat},{center_lon});
    );
    out body;
    >;
    out skel qt;
    """
    
    # Use around query for better results
    return query_around.strip()

def build_advanced_overpass_query(tags: List[str], center_lat: float, center_lon: float, radius: int) -> str:
    """Build an advanced Overpass QL query with multiple strategies"""
    if not tags:
        return None
    
    # Build filter conditions
    filters = []
    for tag in tags:
        key, value = tag.split('=', 1)
        if '*' in value:
            regex_pattern = value.replace('*', '.*')
            filters.append(f'[~"{key}"~"{regex_pattern}"]')
        else:
            escaped_value = value.replace('"', '\\"')
            filters.append(f'["{key}"="{escaped_value}"]')
    
    filter_str = ''.join(filters)
    
    # Calculate bbox
    lat_offset = radius / 111000.0
    lon_offset = radius / (111000.0 * np.cos(np.radians(center_lat)))
    
    bbox = (
        center_lat - lat_offset,
        center_lon - lon_offset,
        center_lat + lat_offset,
        center_lon + lon_offset
    )
    
    # Build comprehensive query
    query = f"""
    [out:json][timeout:45];
    (
      // Query nodes
      node{filter_str}({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
      
      // Query ways
      way{filter_str}({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
      
      // Query relations
      rel{filter_str}({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
      
      // Also query nodes within ways
      way{filter_str}(around:{radius},{center_lat},{center_lon});
      (._;>;);
      
      // Also query surrounding nodes for completeness
      node{filter_str}(around:{radius},{center_lat},{center_lon});
    );
    out body;
    >;
    out skel qt;
    """
    
    return query.strip()

# ============================================================================
# DATA PROCESSING
# ============================================================================

def process_overpass_results(data: Dict, tags: List[str]) -> List[Dict]:
    """Process Overpass API results into standardized POI format"""
    if not data or 'elements' not in data:
        return []
    
    elements = data['elements']
    pois = []
    seen_ids = set()
    
    # Process each element
    for elem in elements:
        elem_id = elem.get('id')
        elem_type = elem.get('type')
        
        # Skip if already seen
        if elem_id in seen_ids:
            continue
        seen_ids.add(elem_id)
        
        # Only process nodes for now (ways and relations need special handling)
        if elem_type != 'node':
            continue
        
        lat = elem.get('lat')
        lon = elem.get('lon')
        
        if lat is None or lon is None:
            continue
        
        tags_dict = elem.get('tags', {})
        
        # Extract name
        name = tags_dict.get('name', '')
        if not name:
            # Try to create name from tags
            for key in ['brand', 'operator', 'shop', 'amenity', 'tourism', 'leisure']:
                if key in tags_dict:
                    name = f"{key}: {tags_dict[key]}"
                    break
            if not name:
                name = 'Unnamed POI'
        
        # Determine primary type
        primary_type = 'unknown'
        for tag in tags:
            key, value = tag.split('=', 1)
            if key in tags_dict:
                primary_type = key
                break
        
        # Create POI entry
        poi = {
            'lat': lat,
            'lon': lon,
            'name': name,
            'type': primary_type,
            'tags': tags_dict,
            'uid': f"{elem_type}_{elem_id}",
            'source': 'overpass',
            'elevation': tags_dict.get('ele'),
            'address': tags_dict.get('addr:full', '')
        }
        
        # Add additional metadata if available
        if 'opening_hours' in tags_dict:
            poi['opening_hours'] = tags_dict['opening_hours']
        if 'phone' in tags_dict:
            poi['phone'] = tags_dict['phone']
        if 'website' in tags_dict:
            poi['website'] = tags_dict['website']
        
        pois.append(poi)
    
    return pois

# ============================================================================
# DATA FETCHING
# ============================================================================

def fetch_pois(query: str, center_lat: float, center_lon: float, radius: int) -> List[Dict]:
    """Main function to fetch POIs from Overpass API with multi-endpoint support"""
    all_pois = []
    
    # Parse query
    tags = parse_search_query(query)
    if not tags:
        add_log("No valid tags found in query", "WARNING")
        return []
    
    add_log(f"Fetching POIs for tags: {', '.join(tags)}", "INFO")
    add_log(f"Center: {center_lat:.6f}, {center_lon:.6f}, Radius: {radius}m", "INFO")
    
    start_time = time.time()
    
    # Try primary query
    primary_query = build_overpass_query(tags, center_lat, center_lon, radius)
    
    if primary_query:
        data, endpoint = overpass_api.execute_query(primary_query)
        
        if data:
            pois = process_overpass_results(data, tags)
            all_pois.extend(pois)
            add_log(f"Primary query found {len(pois)} POIs from {endpoint}", "INFO")
    
    # If not enough results, try advanced query
    if len(all_pois) < 20:
        add_log("Limited results, trying advanced query", "INFO")
        advanced_query = build_advanced_overpass_query(tags, center_lat, center_lon, radius)
        
        if advanced_query:
            data, endpoint = overpass_api.execute_query(advanced_query, max_retries=2)
            
            if data:
                additional_pois = process_overpass_results(data, tags)
                # Merge with existing, avoiding duplicates
                existing_ids = {poi['uid'] for poi in all_pois}
                for poi in additional_pois:
                    if poi['uid'] not in existing_ids:
                        all_pois.append(poi)
                        existing_ids.add(poi['uid'])
                
                add_log(f"Advanced query added {len(additional_pois)} additional POIs", "INFO")
    
    # If still not enough, try expanding radius
    if len(all_pois) < 10 and radius < 5000:
        expanded_radius = min(radius * 2, 50000)
        add_log(f"Expanding radius to {expanded_radius}m", "INFO")
        
        expanded_query = build_overpass_query(tags, center_lat, center_lon, expanded_radius)
        if expanded_query:
            data, endpoint = overpass_api.execute_query(expanded_query, max_retries=2)
            
            if data:
                expanded_pois = process_overpass_results(data, tags)
                existing_ids = {poi['uid'] for poi in all_pois}
                for poi in expanded_pois:
                    if poi['uid'] not in existing_ids:
                        all_pois.append(poi)
                        existing_ids.add(poi['uid'])
                
                add_log(f"Expanded radius found {len(expanded_pois)} additional POIs", "INFO")
    
    elapsed_time = time.time() - start_time
    st.session_state.query_time = elapsed_time
    st.session_state.retry_count = overpass_api.status.get(overpass_api.active_endpoint, {}).get('error_count', 0)
    
    add_log(f"Total {len(all_pois)} POIs fetched in {elapsed_time:.2f}s", "SUCCESS")
    
    # Update endpoint status in session
    st.session_state.active_endpoint = overpass_api.active_endpoint
    st.session_state.overpass_status = overpass_api.status
    
    return all_pois

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters"""
    R = 6371000  # Earth radius in meters
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    
    a = np.sin(delta_phi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

# ============================================================================
# STATE EXPORT/IMPORT
# ============================================================================

def export_state() -> Dict:
    """Export complete application state"""
    export_data = {
        "version": "1.0",
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "app_name": "Open Node",
            "export_type": "complete_state",
            "exported_by": "user",
            "source": "overpass_api"
        },
        "viewport": {
            "center": st.session_state.map_viewport.get('center', [14.5995, 120.9842]),
            "zoom": st.session_state.map_viewport.get('zoom', 13),
            "bounds": st.session_state.map_viewport.get('bounds', [])
        },
        "pois": st.session_state.scanned_records,
        "layers": st.session_state.layer_meta,
        "clusters": st.session_state.layer_groups,
        "settings": {
            "label_size": st.session_state.label_size,
            "marker_style": st.session_state.marker_style,
            "marker_size": st.session_state.marker_size,
            "marker_color": st.session_state.marker_color,
            "basemap": st.session_state.get('basemap', 'osm')
        },
        "search_history": st.session_state.search_history,
        "current_query": st.session_state.current_query,
        "geo_coords": st.session_state.geo_coords,
        "geo_radius": st.session_state.geo_radius,
        "poi_count": st.session_state.poi_count,
        "visibility": st.session_state.poi_visibility,
        "query_metadata": {
            "query_time": st.session_state.get('query_time'),
            "active_endpoint": st.session_state.get('active_endpoint'),
            "retry_count": st.session_state.get('retry_count', 0)
        }
    }
    return export_data

def import_state(import_data: Dict) -> bool:
    """Import complete application state"""
    try:
        # Validate import data
        if not import_data or 'version' not in import_data:
            add_log("Invalid import data", "ERROR")
            return False
        
        # Restore state
        if 'pois' in import_data:
            st.session_state.scanned_records = import_data['pois']
        
        if 'layers' in import_data:
            st.session_state.layer_meta = import_data['layers']
        
        if 'clusters' in import_data:
            st.session_state.layer_groups = import_data['clusters']
        
        if 'settings' in import_data:
            settings = import_data['settings']
            st.session_state.label_size = settings.get('label_size', 9)
            st.session_state.marker_style = settings.get('marker_style', 'modern-pin')
            st.session_state.marker_size = settings.get('marker_size', 16)
            st.session_state.marker_color = settings.get('marker_color', '#003366')
            st.session_state.basemap = settings.get('basemap', 'osm')
        
        if 'search_history' in import_data:
            st.session_state.search_history = import_data['search_history']
        
        if 'current_query' in import_data:
            st.session_state.current_query = import_data['current_query']
        
        if 'geo_coords' in import_data:
            st.session_state.geo_coords = import_data['geo_coords']
        
        if 'geo_radius' in import_data:
            st.session_state.geo_radius = import_data['geo_radius']
        
        if 'poi_count' in import_data:
            st.session_state.poi_count = import_data['poi_count']
        
        if 'visibility' in import_data:
            st.session_state.poi_visibility = import_data['visibility']
        
        if 'viewport' in import_data:
            st.session_state.map_viewport = import_data['viewport']
        
        if 'query_metadata' in import_data:
            metadata = import_data['query_metadata']
            st.session_state.query_time = metadata.get('query_time')
            st.session_state.active_endpoint = metadata.get('active_endpoint')
            st.session_state.retry_count = metadata.get('retry_count', 0)
        
        add_log(f"State imported successfully from {import_data.get('timestamp', 'unknown date')}", "INFO")
        return True
        
    except Exception as e:
        add_log(f"Error importing state: {str(e)}", "ERROR")
        return False

# ============================================================================
# MAP GENERATION
# ============================================================================

def create_map():
    """Create the main map with all POIs"""
    center_lat, center_lon = parse_coordinates(st.session_state.geo_coords)
    
    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=st.session_state.map_viewport.get('zoom', 13),
        tiles='OpenStreetMap',
        control_scale=True
    )
    
    # Add basemap options
    folium.TileLayer(
        tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        name='OpenStreetMap',
        attr='OpenStreetMap'
    ).add_to(m)
    
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        name='Satellite',
        attr='Esri'
    ).add_to(m)
    
    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
        name='Carto Light',
        attr='CartoDB'
    ).add_to(m)
    
    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
        name='Carto Dark',
        attr='CartoDB'
    ).add_to(m)
    
    # Add fullscreen button
    Fullscreen(
        position='topright',
        title='Fullscreen',
        title_cancel='Exit Fullscreen'
    ).add_to(m)
    
    # Add radius circle
    folium.Circle(
        location=[center_lat, center_lon],
        radius=st.session_state.geo_radius,
        color='#003366',
        fill=True,
        fill_color='#003366',
        fill_opacity=0.05,
        weight=2,
        popup=f"Search Radius: {st.session_state.geo_radius}m"
    ).add_to(m)
    
    # Add target marker
    folium.Marker(
        location=[center_lat, center_lon],
        icon=folium.Icon(color='red', icon='target', prefix='fa'),
        popup='Scan Center'
    ).add_to(m)
    
    # Add POIs
    if st.session_state.scanned_records:
        pois = st.session_state.scanned_records
        
        # Group by type for layer management
        poi_types = {}
        for poi in pois:
            poi_type = poi.get('type', 'unknown')
            if poi_type not in poi_types:
                poi_types[poi_type] = []
            poi_types[poi_type].append(poi)
        
        # Create markers for each type
        for poi_type, type_pois in poi_types.items():
            # Get layer configuration
            layer_config = st.session_state.layer_meta.get(poi_type, {})
            color = layer_config.get('color', st.session_state.marker_color)
            style = layer_config.get('style', st.session_state.marker_style)
            size = layer_config.get('size', st.session_state.marker_size)
            visible = layer_config.get('visible', True)
            
            if not visible:
                continue
            
            # Create feature group for this type
            fg = folium.FeatureGroup(name=poi_type.title())
            
            for poi in type_pois:
                lat = poi.get('lat')
                lon = poi.get('lon')
                name = poi.get('name', 'Unnamed')
                
                if lat is None or lon is None:
                    continue
                
                # Create popup content
                popup_content = f"""
                <div style="font-family: Montserrat, sans-serif; padding: 10px; max-width: 300px;">
                    <h4 style="color: #003366; margin: 0 0 5px 0;">{name}</h4>
                    <hr style="margin: 5px 0; border-color: #C9AB4C;">
                    <div style="font-size: 12px;">
                        <b>Type:</b> {poi_type.title()}<br>
                        <b>Location:</b> {lat:.6f}, {lon:.6f}<br>
                """
                
                # Add additional info
                if 'address' in poi and poi['address']:
                    popup_content += f"<b>Address:</b> {poi['address']}<br>"
                
                if 'opening_hours' in poi and poi['opening_hours']:
                    popup_content += f"<b>Hours:</b> {poi['opening_hours']}<br>"
                
                if 'phone' in poi and poi['phone']:
                    popup_content += f"<b>Phone:</b> {poi['phone']}<br>"
                
                # Add tags
                tags = poi.get('tags', {})
                if tags:
                    popup_content += "<b>Tags:</b><br>"
                    for key, value in list(tags.items())[:5]:
                        popup_content += f"&nbsp;&nbsp;{key}: {value}<br>"
                
                popup_content += """
                        <hr style="margin: 5px 0;">
                        <button onclick="window.parent.postMessage({type: 'poi_click', data: {name: '%s'}}, '*')" 
                                style="background: #003366; color: white; border: none; padding: 4px 12px; border-radius: 3px; cursor: pointer; font-size: 12px;">
                            Select
                        </button>
                    </div>
                """ % name
                
                # Create marker based on style
                if style == "dot":
                    icon = folium.plugins.BeautifyIcon(
                        icon='circle',
                        icon_shape='circle',
                        border_color=color,
                        background_color=color,
                        border_width=2,
                        inner_icon_style=f'font-size:{size}px;',
                        opacity=0.8
                    )
                elif style == "pin":
                    icon = folium.Icon(
                        color='blue' if color == '#003366' else 'red',
                        icon='info-sign',
                        prefix='glyphicon'
                    )
                else:  # modern-pin
                    icon = folium.plugins.BeautifyIcon(
                        icon='map-marker',
                        icon_shape='marker',
                        border_color=color,
                        background_color=color,
                        border_width=2,
                        inner_icon_style=f'font-size:{size}px;color:white;',
                        text_color='white'
                    )
                
                # Create marker with popup
                marker = folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_content, max_width=350),
                    tooltip=name,
                    icon=icon
                )
                
                marker.add_to(fg)
            
            fg.add_to(m)
    
    # Add layer control
    folium.LayerControl(position='topright').add_to(m)
    
    return m

def parse_coordinates(coord_str: str) -> Tuple[float, float]:
    """Parse coordinate string to lat/lon"""
    try:
        parts = coord_str.replace(' ', '').split(',')
        if len(parts) == 2:
            lat = float(parts[0])
            lon = float(parts[1])
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon
    except:
        pass
    return 14.5995, 120.9842  # Default to Manila

# ============================================================================
# SIDEBAR COMPONENTS
# ============================================================================

def render_sidebar():
    """Render the sidebar panel"""
    st.markdown("""
    <div class="brand-header">
        <div class="brand-title">Open Node</div>
        <div class="brand-subtitle">Geospatial POI Explorer</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Search Section
    with st.expander("🔍 SEARCH & SCAN", expanded=True):
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        
        # Search input
        st.markdown('<div class="section-title">Query Tags</div>', unsafe_allow_html=True)
        search_query = st.text_input(
            "OSM Tags",
            value=st.session_state.current_query,
            placeholder="amenity=restaurant, shop=supermarket",
            help="Comma-separated OSM tags (e.g., amenity=restaurant, shop=supermarket)",
            key="search_input"
        )
        st.session_state.current_query = search_query
        
        # Search history
        if st.session_state.search_history:
            with st.popover("📜 Search History"):
                for q in st.session_state.search_history[-10:]:
                    if st.button(q, key=f"hist_{q}", use_container_width=True):
                        st.session_state.current_query = q
                        st.rerun()
        
        # Tag suggestions
        with st.popover("💡 Common Tags"):
            common_tags = [
                "amenity=restaurant", "amenity=cafe", "amenity=bar",
                "shop=supermarket", "shop=clothing", "shop=electronics",
                "tourism=hotel", "tourism=museum", "tourism=attraction",
                "leisure=park", "leisure=cinema", "leisure=garden",
                "sport=soccer", "sport=tennis", "sport=golf",
                "amenity=hospital", "amenity=school", "amenity=library"
            ]
            cols = st.columns(2)
            for i, tag in enumerate(common_tags):
                col = cols[i % 2]
                if col.button(tag, key=f"sug_{tag}", use_container_width=True):
                    if st.session_state.current_query:
                        st.session_state.current_query += f", {tag}"
                    else:
                        st.session_state.current_query = tag
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Scan area
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Scan Area</div>', unsafe_allow_html=True)
        
        coord_input = st.text_input(
            "Coordinates",
            value=st.session_state.geo_coords,
            placeholder="14.5995, 120.9842",
            help="Latitude, Longitude"
        )
        st.session_state.geo_coords = coord_input
        
        radius = st.slider(
            "Radius (meters)",
            min_value=100,
            max_value=50000,
            value=st.session_state.geo_radius,
            step=100,
            format="%d m"
        )
        st.session_state.geo_radius = radius
        
        # Scan button
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("🔍 SCAN AREA", type="primary", use_container_width=True):
                scan_area()
        with col2:
            if st.button("🗑️", help="Clear all POIs"):
                clear_all()
        
        # API status
        if st.session_state.active_endpoint:
            status_color = "status-online"
            status_text = "Online"
            if st.session_state.retry_count > 0:
                status_color = "status-unknown"
                status_text = f"Degraded ({st.session_state.retry_count} retries)"
            st.markdown(f"""
            <div style="font-size:11px;margin-top:8px;text-align:center;">
                <span class="{status_color}">●</span> 
                API: {status_text}
                {f'({st.session_state.query_time:.1f}s)' if st.session_state.query_time else ''}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Stats Section
    with st.expander("📊 STATISTICS", expanded=True):
        cols = st.columns(3)
        with cols[0]:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-number">{st.session_state.poi_count}</div>
                <div class="stat-label">POIs Found</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[1]:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-number">{len(st.session_state.layer_meta)}</div>
                <div class="stat-label">Layer Types</div>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[2]:
            last_scan = st.session_state.last_scan_time
            if last_scan:
                time_str = last_scan.strftime("%H:%M:%S")
            else:
                time_str = "Never"
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-number" style="font-size:16px;">{time_str}</div>
                <div class="stat-label">Last Scan</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Export Section
    with st.expander("💾 EXPORT / IMPORT", expanded=True):
        # Export buttons
        if st.button("📤 Export State", use_container_width=True, type="primary"):
            export_data = export_state()
            json_str = json.dumps(export_data, indent=2)
            
            # Create download button
            b64 = base64.b64encode(json_str.encode()).decode()
            href = f'<a href="data:application/json;base64,{b64}" download="opennode_state_{datetime.now().strftime("%Y%m%d_%H%M%S")}.opennode" style="text-decoration:none;color:white;background:#003366;padding:8px 16px;border-radius:4px;display:inline-block;width:100%;text-align:center;">Download .opennode</a>'
            st.markdown(href, unsafe_allow_html=True)
            add_log("State exported successfully", "INFO")
        
        # Import
        uploaded_file = st.file_uploader(
            "Import .opennode file",
            type=['opennode', 'json'],
            help="Upload a previously exported Open Node state file"
        )
        
        if uploaded_file is not None:
            try:
                import_data = json.load(uploaded_file)
                if import_state(import_data):
                    st.success("✅ State imported successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to import state")
            except Exception as e:
                st.error(f"Error importing file: {str(e)}")
    
    # Logs Section
    with st.expander("📋 SESSION LOGS"):
        st.markdown('<div class="log-container">', unsafe_allow_html=True)
        for log in st.session_state.session_logs[:50]:
            level_color = {
                'INFO': '#00ff00',
                'WARNING': '#ffff00',
                'ERROR': '#ff0000',
                'SUCCESS': '#00ff88'
            }.get(log['level'], '#ffffff')
            st.markdown(
                f'<div class="log-entry"><span class="log-time">[{log["time"]}]</span>'
                f'<span style="color:{level_color};">{log["message"]}</span></div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("Clear Logs", use_container_width=True):
            st.session_state.session_logs = []
            st.rerun()
    
    # Layer Management
    if st.session_state.scanned_records:
        with st.expander("🎨 LAYER MANAGEMENT", expanded=True):
            # Get unique types
            poi_types = set()
            for poi in st.session_state.scanned_records:
                poi_types.add(poi.get('type', 'unknown'))
            
            for poi_type in sorted(poi_types):
                st.markdown(f'<div style="font-size:13px;font-weight:600;color:#003366;margin-top:5px;">{poi_type.title()}</div>', unsafe_allow_html=True)
                
                cols = st.columns([2, 1, 1])
                with cols[0]:
                    # Color picker
                    current_color = st.session_state.layer_meta.get(poi_type, {}).get('color', st.session_state.marker_color)
                    new_color = st.color_picker(
                        "Color",
                        value=current_color,
                        key=f"color_{poi_type}",
                        label_visibility="collapsed"
                    )
                    if new_color != current_color:
                        if poi_type not in st.session_state.layer_meta:
                            st.session_state.layer_meta[poi_type] = {}
                        st.session_state.layer_meta[poi_type]['color'] = new_color
                
                with cols[1]:
                    # Visibility toggle
                    visible = st.session_state.layer_meta.get(poi_type, {}).get('visible', True)
                    if st.button("👁️" if visible else "🚫", key=f"vis_{poi_type}", help="Toggle visibility"):
                        if poi_type not in st.session_state.layer_meta:
                            st.session_state.layer_meta[poi_type] = {}
                        st.session_state.layer_meta[poi_type]['visible'] = not visible
                        st.rerun()
                
                with cols[2]:
                    # Style selector
                    current_style = st.session_state.layer_meta.get(poi_type, {}).get('style', 'modern-pin')
                    new_style = st.selectbox(
                        "Style",
                        ['dot', 'pin', 'modern-pin'],
                        index=['dot', 'pin', 'modern-pin'].index(current_style) if current_style in ['dot', 'pin', 'modern-pin'] else 2,
                        key=f"style_{poi_type}",
                        label_visibility="collapsed"
                    )
                    if new_style != current_style:
                        if poi_type not in st.session_state.layer_meta:
                            st.session_state.layer_meta[poi_type] = {}
                        st.session_state.layer_meta[poi_type]['style'] = new_style

# ============================================================================
# ACTION FUNCTIONS
# ============================================================================

def scan_area():
    """Execute area scan using Overpass API"""
    if not st.session_state.current_query:
        st.warning("⚠️ Please enter a search query")
        add_log("Scan attempted with empty query", "WARNING")
        return
    
    add_log(f"Starting scan with query: {st.session_state.current_query}", "INFO")
    
    # Parse coordinates
    lat, lon = parse_coordinates(st.session_state.geo_coords)
    
    # Fetch POIs from Overpass
    pois = fetch_pois(
        st.session_state.current_query,
        lat,
        lon,
        st.session_state.geo_radius
    )
    
    # Update session state
    st.session_state.scanned_records = pois
    st.session_state.poi_count = len(pois)
    st.session_state.last_scan_time = datetime.now()
    
    # Update search history
    if st.session_state.current_query not in st.session_state.search_history:
        st.session_state.search_history.append(st.session_state.current_query)
        if len(st.session_state.search_history) > 20:
            st.session_state.search_history = st.session_state.search_history[-20:]
    
    # Auto-generate layer groups
    poi_types = set()
    for poi in pois:
        poi_types.add(poi.get('type', 'unknown'))
    
    for poi_type in poi_types:
        if poi_type not in st.session_state.layer_meta:
            st.session_state.layer_meta[poi_type] = {
                'color': st.session_state.marker_color,
                'style': st.session_state.marker_style,
                'size': st.session_state.marker_size,
                'visible': True
            }
    
    add_log(f"Scan complete: {len(pois)} POIs found", "SUCCESS")
    
    if len(pois) == 0:
        st.warning("⚠️ No POIs found. Try adjusting the search query or expanding the radius.")

def clear_all():
    """Clear all POIs and reset state"""
    st.session_state.scanned_records = []
    st.session_state.poi_count = 0
    st.session_state.layer_meta = {}
    st.session_state.layer_groups = {}
    st.session_state.poi_visibility = {}
    st.session_state.last_scan_time = None
    st.session_state.query_time = None
    st.session_state.retry_count = 0
    add_log("All POIs cleared", "INFO")
    st.rerun()

def export_geojson():
    """Export POIs as GeoJSON"""
    if not st.session_state.scanned_records:
        st.warning("No POIs to export")
        return
    
    # Convert to GeoJSON format
    features = []
    for poi in st.session_state.scanned_records:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [poi.get('lon'), poi.get('lat')]
            },
            "properties": {
                "name": poi.get('name', 'Unnamed'),
                "type": poi.get('type', 'unknown'),
                "tags": poi.get('tags', {}),
                "address": poi.get('address', ''),
                "opening_hours": poi.get('opening_hours', ''),
                "phone": poi.get('phone', ''),
                "website": poi.get('website', '')
            }
        }
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "exported_at": datetime.now().isoformat(),
            "source": "Open Node - Overpass API",
            "query": st.session_state.current_query,
            "total_features": len(features)
        }
    }
    
    return geojson

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    # Create layout
    col1, col2 = st.columns([1, 4])
    
    with col1:
        render_sidebar()
    
    with col2:
        # Map container
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        
        # Create and display map
        m = create_map()
        folium_static(m, width=None, height=700)
        
        # Map controls below map
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            # Export GeoJSON
            if st.button("📥 Export GeoJSON", use_container_width=True):
                geojson_data = export_geojson()
                if geojson_data:
                    json_str = json.dumps(geojson_data, indent=2)
                    b64 = base64.b64encode(json_str.encode()).decode()
                    href = f'<a href="data:application/json;base64,{b64}" download="opennode_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.geojson" style="text-decoration:none;color:white;background:#003366;padding:8px 16px;border-radius:4px;display:inline-block;width:100%;text-align:center;">Download GeoJSON</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    add_log("GeoJSON exported", "INFO")
        
        with col2:
            # Export KML (simplified version)
            if st.button("📍 Export KML", use_container_width=True):
                st.info("KML export coming soon!")
                add_log("KML export requested", "INFO")
        
        with col3:
            # Export CSV
            if st.button("📊 Export CSV", use_container_width=True):
                if st.session_state.scanned_records:
                    df = pd.DataFrame(st.session_state.scanned_records)
                    csv = df.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()
                    href = f'<a href="data:text/csv;base64,{b64}" download="opennode_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv" style="text-decoration:none;color:white;background:#003366;padding:8px 16px;border-radius:4px;display:inline-block;width:100%;text-align:center;">Download CSV</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    add_log("CSV exported", "INFO")
                else:
                    st.warning("No data to export")
        
        with col4:
            # Settings
            with st.popover("⚙️ Settings"):
                label_size = st.slider(
                    "Label Size",
                    min_value=6,
                    max_value=20,
                    value=st.session_state.label_size
                )
                st.session_state.label_size = label_size
                
                marker_size = st.slider(
                    "Marker Size",
                    min_value=8,
                    max_value=32,
                    value=st.session_state.marker_size
                )
                st.session_state.marker_size = marker_size
                
                marker_color = st.color_picker(
                    "Default Marker Color",
                    value=st.session_state.marker_color
                )
                st.session_state.marker_color = marker_color
                
                marker_style = st.selectbox(
                    "Default Marker Style",
                    ['modern-pin', 'pin', 'dot'],
                    index=['modern-pin', 'pin', 'dot'].index(st.session_state.marker_style)
                )
                st.session_state.marker_style = marker_style
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style="text-align:center;padding:20px;color:#666;font-size:12px;font-family:Montserrat,sans-serif;border-top:1px solid #e0e0e0;margin-top:20px;">
        Open Node • Geospatial POI Explorer • Data from OpenStreetMap via Overpass API
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

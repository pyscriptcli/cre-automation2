import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import xml.etree.ElementTree as ET
import pandas as pd
import requests
import logging
import uuid

logger = logging.getLogger("OpenNode.Scraper")

try:
    import osmnx as ox
    HAS_OSMNX = True
except ImportError:
    HAS_OSMNX = False

def parse_config_tags_to_osmnx_format(selected_tuples: list) -> dict:
    tags_dict = {}
    for item in selected_tuples:
        _, key, val = item
        if key in tags_dict:
            if isinstance(tags_dict[key], list):
                if val not in tags_dict[key]: tags_dict[key].append(val)
            elif tags_dict[key] != val:
                tags_dict[key] = [tags_dict[key], val]
        else:
            if "|" in val: tags_dict[key] = val.split("|")
            elif val == ".*": tags_dict[key] = True
            else: tags_dict[key] = val
    return tags_dict

def run_spatial_layer_scan(lat: float, lon: float, radius: int, selected_tuples: list) -> list:
    records = []
    if not selected_tuples: return records

    if HAS_OSMNX:
        try:
            tags_dict = parse_config_tags_to_osmnx_format(selected_tuples)
            gdf = ox.features_from_point((lat, lon), tags=tags_dict, dist=radius)
            if not gdf.empty:
                for _, row in gdf.iterrows():
                    if hasattr(row.geometry, 'centroid'):
                        c_lat, c_lon = row.geometry.centroid.y, row.geometry.centroid.x
                    else: continue
                    
                    raw_name = row.get('name', 'Unknown')
                    name = 'Unknown' if pd.isna(raw_name) or not isinstance(raw_name, str) else str(raw_name)
                    
                    matched_type = 'Node'
                    for k in tags_dict.keys():
                        if k in row and not pd.isna(row[k]) and row[k]:
                            matched_type = str(row[k])
                            break
                    
                    records.append({
                        "lat": c_lat, "lon": c_lon, "name": name,
                        "type": matched_type, "visible": True, "uid": str(uuid.uuid4())
                    })
                return records
        except Exception: pass

    url = "https://overpass-api.de/api/interpreter"
    statements = []
    for item in selected_tuples:
        _, key, val = item
        clean_tag = val.replace('"', '')
        if clean_tag.endswith(',i'): clean_tag = clean_tag[:-2]
        
        if "~" in key or "~" in clean_tag:
            statements.append(f"  nwr[\"{key}\"~\"{clean_tag}\"](around:{radius},{lat},{lon});")
        else:
            statements.append(f"  nwr[\"{key}\"=\"{clean_tag}\"](around:{radius},{lat},{lon});")
            
    ql_query = f"[out:json][timeout:90];(\n" + "\n".join(statements) + f"\n);\nout center;"
    
    try:
        res = requests.post(url, data={"data": ql_query}, headers={"User-Agent": "OpenNode/3.5"}, timeout=90)
        if res.status_code == 200:
            elements = res.json().get('elements', [])
            for el in elements:
                e_lat = el.get('lat') or el.get('center', {}).get('lat')
                e_lon = el.get('lon') or el.get('center', {}).get('lon')
                if e_lat and e_lon:
                    tags = el.get('tags', {})
                    raw_name = tags.get('name', 'Unknown')
                    name = 'Unknown' if pd.isna(raw_name) or not isinstance(raw_name, str) else str(raw_name)
                    matched_type = tags.get('amenity') or tags.get('shop') or tags.get('building') or 'Node'
                    records.append({
                        "lat": e_lat, "lon": e_lon, "name": name,
                        "type": str(matched_type), "visible": True, "uid": str(uuid.uuid4())
                    })
    except Exception: pass
        
    return records

def compile_features_kml(features: list) -> str:
    root = ET.Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    doc = ET.SubElement(root, "Document")
    name_el = ET.SubElement(doc, "name")
    name_el.text = "Scanned POIs"
    
    for f in features:
        if not f.get('visible', True): continue
        placemark = ET.SubElement(doc, "Placemark")
        p_name = ET.SubElement(placemark, "name")
        p_name.text = f.get('name', 'Asset') or 'Asset'
        p_desc = ET.SubElement(placemark, "description")
        p_desc.text = f.get('type', 'Node') or 'Node'
        point = ET.SubElement(placemark, "Point")
        coords = ET.SubElement(point, "coordinates")
        coords.text = f"{f['lon']},{f['lat']},0"
        
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="utf-8").decode("utf-8")

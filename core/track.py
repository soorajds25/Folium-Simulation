import numpy as np
import pandas as pd
from dataclasses import dataclass
import xml.etree.ElementTree as ET
from typing import List, Tuple
import os

@dataclass
class NormalizedTrackNode:
    distance_m: float       # Arc length coordinate context s
    elevation_m: float      # Height tracking point above sea level H
    gradient_pct: float     # Path vertical grade derivative percent i
    curvature: float        # Lateral trajectory index parameter kappa
    corner_radius_m: float  # Radius parameter of localized bend curve
    track_width_m: float    # Absolute boundaries width of local racetrack corridor

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two lat/lon points in meters using Haversine formula."""
    R = 6371000  # Radius of earth in meters
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)

    a = np.sin(delta_phi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

def parse_gpx_to_dataframe(filepath: str) -> pd.DataFrame:
    """
    Parse GPX file into a pandas DataFrame.
    """
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    # Try with namespace
    ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
    trkpts = root.findall('.//gpx:trkpt', ns)
    
    if not trkpts:
        # Fallback to no namespace
        trkpts = root.findall('.//trkpt')
        
    data = []
    for trkpt in trkpts:
        lat = float(trkpt.get('lat'))
        lon = float(trkpt.get('lon'))
        
        # Find elevation
        ele_node = trkpt.find('gpx:ele', ns) if trkpt.find('gpx:ele', ns) is not None else trkpt.find('ele')
        if ele_node is None:
            ele_node = trkpt.find('ele')
        ele = float(ele_node.text) if ele_node is not None and ele_node.text is not None else 0.0
        
        row = {'latitude': lat, 'longitude': lon, 'elevation_m': ele}
        
        # Look for extensions if they exist
        ext_node = trkpt.find('gpx:extensions', ns) if trkpt.find('gpx:extensions', ns) is not None else trkpt.find('extensions')
        if ext_node is None:
            ext_node = trkpt.find('extensions')
            
        if ext_node is not None:
            for child in ext_node:
                tag = child.tag.split('}')[-1]
                try:
                    row[tag] = float(child.text)
                except (ValueError, TypeError):
                    row[tag] = child.text
                    
        data.append(row)
        
    if not data:
        raise ValueError("No track points found in GPX file.")
        
    return pd.DataFrame(data)

def process_track(lats: np.ndarray, lons: np.ndarray, eles: np.ndarray, track_width: float = 5.0) -> List[NormalizedTrackNode]:
    """
    Normalize track into 1-meter intervals and compute gradient and curvature.
    """
    if len(lats) < 3:
        raise ValueError("Track must have at least 3 points")
        
    # Calculate cumulative distances (s)
    distances = np.zeros(len(lats))
    for i in range(1, len(lats)):
        distances[i] = distances[i-1] + haversine_distance(lats[i-1], lons[i-1], lats[i], lons[i])
        
    total_distance = distances[-1]
    
    # 1-meter intervals
    s_norm = np.arange(0, total_distance, 1.0)
    
    # Interpolate elevations
    ele_norm = np.interp(s_norm, distances, eles)
    
    # Interpolate lats and lons to Cartesian for curvature
    lat_norm = np.interp(s_norm, distances, lats)
    lon_norm = np.interp(s_norm, distances, lons)
    
    # Simple projection to local Cartesian coords
    # Center around first point
    lat0, lon0 = lat_norm[0], lon_norm[0]
    R = 6371000
    x_norm = R * np.radians(lon_norm - lon0) * np.cos(np.radians(lat0))
    y_norm = R * np.radians(lat_norm - lat0)
    
    # Calculate gradient
    # theta = arctan(d_ele / d_s)
    # spacing is 1.0 m, so d_s is 1.0
    d_ele = np.gradient(ele_norm, s_norm)
    # gradient_pct is tan(theta) * 100 which is roughly d_ele/ds * 100
    gradient_pct = d_ele * 100.0
    
    # Calculate curvature using cross product of derivatives
    dx = np.gradient(x_norm, s_norm)
    dy = np.gradient(y_norm, s_norm)
    ddx = np.gradient(dx, s_norm)
    ddy = np.gradient(dy, s_norm)
    
    # kappa = |dx*ddy - dy*ddx| / (dx^2 + dy^2)^(3/2)
    numerator = np.abs(dx * ddy - dy * ddx)
    denominator = (dx**2 + dy**2)**1.5
    
    # Avoid division by zero
    denominator[denominator == 0] = 1e-6
    kappa = numerator / denominator
    
    # Radius = 1 / kappa
    corner_radius = np.zeros_like(kappa)
    corner_radius[kappa > 1e-6] = 1.0 / kappa[kappa > 1e-6]
    corner_radius[kappa <= 1e-6] = float('inf')
    
    nodes = []
    for i in range(len(s_norm)):
        nodes.append(NormalizedTrackNode(
            distance_m=float(s_norm[i]),
            elevation_m=float(ele_norm[i]),
            gradient_pct=float(gradient_pct[i]),
            curvature=float(kappa[i]),
            corner_radius_m=float(corner_radius[i]),
            track_width_m=track_width
        ))
        
    return nodes

def load_track(filepath: str, track_width: float = 5.0) -> List[NormalizedTrackNode]:
    """
    Smart Parser that loads track from CSV or GPX using pandas.
    If pre-calculated columns exist, map them directly.
    Otherwise, run haversine normalization and curvature calculations.
    """
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == '.csv':
        df = pd.read_csv(filepath)
    elif ext == '.gpx':
        df = parse_gpx_to_dataframe(filepath)
    else:
        raise ValueError(f"Unsupported track file extension: {ext}")
        
    # Clean column names for comparison (lowercase, stripped)
    clean_cols = {col.lower().strip(): col for col in df.columns}
    
    required_precalculated = ['distance_m', 'elevation_m', 'gradient_pct', 'curvature']
    has_precalculated = all(req in clean_cols for req in required_precalculated)
    
    if has_precalculated:
        # Sort by distance to ensure correct s-domain index
        dist_col = clean_cols['distance_m']
        df = df.sort_values(by=dist_col).reset_index(drop=True)
        
        nodes = []
        for _, row in df.iterrows():
            dist = float(row[clean_cols['distance_m']])
            ele = float(row[clean_cols['elevation_m']])
            grad = float(row[clean_cols['gradient_pct']])
            curv = float(row[clean_cols['curvature']])
            
            # Map corner_radius_m if exists, otherwise compute it
            if 'corner_radius_m' in clean_cols:
                rad = float(row[clean_cols['corner_radius_m']])
            else:
                rad = 1.0 / curv if curv > 1e-6 else float('inf')
                
            # Map track_width_m if exists, otherwise use default
            if 'track_width_m' in clean_cols:
                width = float(row[clean_cols['track_width_m']])
            else:
                width = track_width
                
            nodes.append(NormalizedTrackNode(
                distance_m=dist,
                elevation_m=ele,
                gradient_pct=grad,
                curvature=curv,
                corner_radius_m=rad,
                track_width_m=width
            ))
        return nodes

    # Case 3: Need to calculate from coordinates
    # Look for Latitude/Longitude or lat/lon
    lat_col = None
    lon_col = None
    ele_col = None
    
    for c in ['latitude', 'lat', 'lat_deg', 'y']:
        if c in clean_cols:
            lat_col = clean_cols[c]
            break
            
    for c in ['longitude', 'lon', 'lng', 'lon_deg', 'x']:
        if c in clean_cols:
            lon_col = clean_cols[c]
            break
            
    for c in ['elevation', 'ele', 'altitude', 'alt', 'z', 'elevation_m']:
        if c in clean_cols:
            ele_col = clean_cols[c]
            break
            
    if lat_col is None or lon_col is None:
        raise ValueError("Could not find latitude/longitude coordinates in dataset.")
        
    lats = df[lat_col].to_numpy()
    lons = df[lon_col].to_numpy()
    if ele_col is not None:
        eles = df[ele_col].to_numpy()
    else:
        eles = np.zeros_like(lats)
        
    return process_track(lats, lons, eles, track_width=track_width)

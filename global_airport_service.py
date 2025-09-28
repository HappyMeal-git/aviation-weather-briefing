"""
Global Airport Coordinate Service
Provides comprehensive airport coordinate lookup with multiple fallback sources
"""

import requests
import json
import logging
from typing import Optional, List, Dict, Tuple
import time

class GlobalAirportService:
    """Service to get airport coordinates from multiple global sources"""
    
    def __init__(self):
        self.cache = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Aviation-Weather-Briefing/1.0'
        })
    
    def get_coordinates(self, icao_code: str) -> Optional[List[float]]:
        """
        Get airport coordinates with multiple fallback methods
        Returns [latitude, longitude] or None if not found
        """
        icao_upper = icao_code.upper()
        
        # Check cache first
        if icao_upper in self.cache:
            return self.cache[icao_upper]
        
        # Try multiple sources in order of reliability
        sources = [
            self._try_aviation_weather_api,
            self._try_openflights_database,
            self._try_airport_data_api,
            self._try_ourairports_api
        ]
        
        for source in sources:
            try:
                coords = source(icao_upper)
                if coords:
                    # Cache successful result
                    self.cache[icao_upper] = coords
                    logging.info(f"✅ Found coordinates for {icao_code}: {coords}")
                    return coords
            except Exception as e:
                logging.warning(f"Source failed for {icao_code}: {e}")
                continue
        
        logging.error(f"❌ Could not find coordinates for {icao_code} in any source")
        return None
    
    def _try_aviation_weather_api(self, icao_code: str) -> Optional[List[float]]:
        """Try Aviation Weather API (most reliable for weather stations)"""
        url = "https://aviationweather.gov/api/data/stationinfo"
        params = {'ids': icao_code, 'format': 'json'}
        
        response = self.session.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0 and 'lat' in data[0] and 'lon' in data[0]:
                return [float(data[0]['lat']), float(data[0]['lon'])]
        return None
    
    def _try_openflights_database(self, icao_code: str) -> Optional[List[float]]:
        """Try OpenFlights database (comprehensive free database)"""
        url = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
        
        response = self.session.get(url, timeout=10)
        if response.status_code == 200:
            # Parse CSV data
            lines = response.text.strip().split('\n')
            for line in lines:
                parts = line.split(',')
                if len(parts) >= 8:
                    # Format: ID,Name,City,Country,IATA,ICAO,Latitude,Longitude,...
                    airport_icao = parts[5].strip('"').upper()
                    if airport_icao == icao_code:
                        try:
                            lat = float(parts[6])
                            lon = float(parts[7])
                            return [lat, lon]
                        except (ValueError, IndexError):
                            continue
        return None
    
    def _try_airport_data_api(self, icao_code: str) -> Optional[List[float]]:
        """Try Airport-Data.com API"""
        # Note: This API may require registration for heavy use
        url = f"https://www.airport-data.com/api/ap_info.json"
        params = {'icao': icao_code}
        
        response = self.session.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'latitude' in data and 'longitude' in data:
                return [float(data['latitude']), float(data['longitude'])]
        return None
    
    def _try_ourairports_api(self, icao_code: str) -> Optional[List[float]]:
        """Try OurAirports database"""
        url = "https://davidmegginson.github.io/ourairports-data/airports.csv"
        
        response = self.session.get(url, timeout=10)
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            # Skip header
            for line in lines[1:]:
                parts = line.split(',')
                if len(parts) >= 6:
                    # Find ICAO code column (usually index 1)
                    airport_icao = parts[1].strip('"').upper()
                    if airport_icao == icao_code:
                        try:
                            lat = float(parts[4].strip('"'))
                            lon = float(parts[5].strip('"'))
                            return [lat, lon]
                        except (ValueError, IndexError):
                            continue
        return None
    
    def bulk_lookup(self, icao_codes: List[str]) -> Dict[str, Optional[List[float]]]:
        """
        Look up multiple airports at once
        Returns dict of {icao_code: [lat, lon] or None}
        """
        results = {}
        for icao_code in icao_codes:
            results[icao_code] = self.get_coordinates(icao_code)
            # Small delay to be respectful to APIs
            time.sleep(0.1)
        return results
    
    def get_airport_info(self, icao_code: str) -> Optional[Dict]:
        """
        Get comprehensive airport information including coordinates
        """
        coords = self.get_coordinates(icao_code)
        if not coords:
            return None
        
        return {
            'icao': icao_code.upper(),
            'coordinates': coords,
            'latitude': coords[0],
            'longitude': coords[1],
            'source': 'global_lookup'
        }

# Global instance
global_airport_service = GlobalAirportService()

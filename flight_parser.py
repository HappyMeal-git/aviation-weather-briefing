"""
Flight Plan Parser
Simple parser to extract airport codes from flight plan text
"""

import re
from typing import List

class FlightPlanParser:
    """Parse flight plans to extract airport codes"""
    
    def __init__(self):
        # Common flight plan patterns
        self.icao_pattern = re.compile(r'\b[A-Z]{4}\b')  # 4-letter ICAO codes
        self.iata_pattern = re.compile(r'\b[A-Z]{3}\b')  # 3-letter IATA codes
        
    def parse_flight_plan_text(self, flight_plan_text: str) -> List[str]:
        """
        Parse flight plan text to extract airport codes
        
        Args:
            flight_plan_text (str): Raw flight plan text
            
        Returns:
            List[str]: List of airport codes found
        """
        if not flight_plan_text:
            return []
        
        # Clean up the text
        text = flight_plan_text.upper().strip()
        
        # Try different parsing strategies
        airports = []
        
        # Strategy 1: Look for common flight plan formats
        # Format: "KJFK KORD KDEN KLAX" or "KJFK-KORD-KDEN-KLAX"
        icao_codes = self.icao_pattern.findall(text)
        if icao_codes:
            # Filter out common non-airport 4-letter codes
            filtered_codes = []
            common_non_airports = {
                'FUEL', 'TIME', 'DIST', 'PLAN', 'ROUTE', 'FLIGHT', 'FROM', 'DEST', 
                'DEPA', 'ARRI', 'WAYP', 'ALTN', 'RMKS', 'INFO', 'DATA', 'FILE'
            }
            for code in icao_codes:
                if code not in common_non_airports:
                    filtered_codes.append(code)
            airports.extend(filtered_codes)
        
        # Strategy 2: Look for "FROM xxx TO yyy VIA zzz" patterns
        from_to_pattern = re.search(r'FROM\s+([A-Z]{3,4})\s+TO\s+([A-Z]{3,4})', text)
        if from_to_pattern:
            departure = from_to_pattern.group(1)
            arrival = from_to_pattern.group(2)
            if departure not in airports:
                airports.insert(0, departure)
            if arrival not in airports:
                airports.append(arrival)
        
        # Strategy 3: Look for "DEP: xxx ARR: yyy" patterns
        dep_arr_pattern = re.search(r'DEP:?\s*([A-Z]{3,4}).*ARR:?\s*([A-Z]{3,4})', text)
        if dep_arr_pattern:
            departure = dep_arr_pattern.group(1)
            arrival = dep_arr_pattern.group(2)
            if departure not in airports:
                airports.insert(0, departure)
            if arrival not in airports:
                airports.append(arrival)
        
        # Strategy 4: Look for waypoint sequences
        # Common format: "KJFK..WAYPOINT1..WAYPOINT2..KLAX"
        waypoint_pattern = re.findall(r'([A-Z]{4})(?:\.\.|->|>|-)([A-Z]{4})', text)
        for start, end in waypoint_pattern:
            if start not in airports:
                airports.append(start)
            if end not in airports:
                airports.append(end)
        
        # Remove duplicates while preserving order
        unique_airports = []
        for airport in airports:
            if airport not in unique_airports:
                unique_airports.append(airport)
        
        return unique_airports
    
    def extract_route_info(self, flight_plan_text: str) -> dict:
        """
        Extract additional route information from flight plan
        
        Args:
            flight_plan_text (str): Raw flight plan text
            
        Returns:
            dict: Route information including airports, waypoints, etc.
        """
        airports = self.parse_flight_plan_text(flight_plan_text)
        
        # Extract other useful information
        text = flight_plan_text.upper()
        
        # Look for altitude information
        altitude_pattern = re.search(r'FL(\d{3})|(\d{3,5})\s*FT|ALT\s*(\d{3,5})', text)
        altitude = None
        if altitude_pattern:
            if altitude_pattern.group(1):  # Flight level
                altitude = int(altitude_pattern.group(1)) * 100
            elif altitude_pattern.group(2):  # Feet
                altitude = int(altitude_pattern.group(2))
            elif altitude_pattern.group(3):  # Alt format
                altitude = int(altitude_pattern.group(3))
        
        # Look for aircraft type
        aircraft_pattern = re.search(r'ACFT[:\s]*([A-Z0-9]{2,4})|TYPE[:\s]*([A-Z0-9]{2,4})', text)
        aircraft_type = None
        if aircraft_pattern:
            aircraft_type = aircraft_pattern.group(1) or aircraft_pattern.group(2)
        
        return {
            'airports': airports,
            'departure': airports[0] if airports else None,
            'arrival': airports[-1] if airports else None,
            'waypoints': airports[1:-1] if len(airports) > 2 else [],
            'altitude': altitude,
            'aircraft_type': aircraft_type,
            'raw_text': flight_plan_text
        }

# Global instance
flight_parser = FlightPlanParser()

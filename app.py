from flask import Flask, request, jsonify, render_template
import logging
import os
from datetime import datetime, timezone
from weather_service import WeatherService
from weather_analyzer import WeatherAnalyzer
from visualizations import WeatherVisualizer
from notam_service import NotamService
from nlp_analyzer import AviationNLPAnalyzer
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import requests
import re
import sys
from airport_coordinates import calculate_route_distance
from flight_parser import flight_parser
from datetime import datetime

# =============================
# PIREP Data class and logic
# =============================
@dataclass
class PIREP:
    raw: str
    type: Optional[str] = None
    obs_time: Optional[str] = None
    receipt_time: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    altitude_ft_msl: Optional[int] = None
    station: Optional[str] = None
    turbulence: Optional[str] = None
    icing: Optional[str] = None
    sky: Optional[str] = None
    temp_c: Optional[float] = None
    aircraft: Optional[str] = None
    remarks: Optional[str] = None

# Regex for raw decoding
FL_RE = re.compile(r"/FL(\d+)")
TB_RE = re.compile(r"/TB\s*([^/]+)")
IC_RE = re.compile(r"/IC\s*([^/]+)")
SK_RE = re.compile(r"/SK\s*([^/]+)")
TA_RE = re.compile(r"/TA\s*([-+]?\d+)")
TP_RE = re.compile(r"/TP\s*([A-Z0-9]+)")
RM_RE = re.compile(r"/RM\s*([^/]+)")

INTENSITY_MAP = {
    "LGT": "Light",
    "MOD": "Moderate", 
    "SEV": "Severe",
    "SVR": "Severe",
    "EXTM": "Extreme",
    "LGT-MOD": "Light to Moderate",
    "MOD-SEV": "Moderate to Severe",
    "NEG": "None",
    "OCNL": "Occasional",
    "CONS": "Continuous"
}

def severity_icon(level: str) -> str:
    if not level:
        return ""
    if "Light" in level:
        return "✅"
    if "Moderate" in level:
        return "⚠️"
    if "Severe" in level or "Extreme" in level:
        return "🔴"
    return ""

AIRPORT_LOOKUP = {
    "KJFK": "John F. Kennedy International Airport, New York",
    "KLAX": "Los Angeles International Airport",
    "KBOS": "Boston Logan International Airport",
    "KSEA": "Seattle-Tacoma International Airport",
    "KSFO": "San Francisco International Airport",
    "KORD": "Chicago O'Hare International Airport",
    "KDEN": "Denver International Airport",
    "KATL": "Hartsfield-Jackson Atlanta International Airport",
    "KDFW": "Dallas/Fort Worth International Airport",
    "KLAS": "McCarran International Airport, Las Vegas",
    "KMIA": "Miami International Airport",
    "KPHX": "Phoenix Sky Harbor International Airport",
    "VABB": "Chhatrapati Shivaji Maharaj International Airport, Mumbai",
    "VOBG": "Belgaum Airport",
    "VIDP": "Indira Gandhi International Airport, Delhi",
    "VOBL": "Kempegowda International Airport, Bangalore"
}

def parse_raw(raw: str, base: Optional[PIREP] = None) -> PIREP:
    p = base or PIREP(raw=raw)
    if m := FL_RE.search(raw):
        p.altitude_ft_msl = int(m.group(1)) * 100
    if m := TB_RE.search(raw):
        tb_val = m.group(1).strip()
        p.turbulence = INTENSITY_MAP.get(tb_val, tb_val)
    if m := IC_RE.search(raw):
        ic_val = m.group(1).strip()
        p.icing = INTENSITY_MAP.get(ic_val, ic_val)
    if m := SK_RE.search(raw):
        p.sky = m.group(1).strip()
    if m := TA_RE.search(raw):
        try:
            p.temp_c = float(m.group(1))
        except:
            pass
    if m := TP_RE.search(raw):
        p.aircraft = m.group(1)
    if m := RM_RE.search(raw):
        p.remarks = m.group(1).strip()
    return p

CLOUD_RE = re.compile(r"(FEW|SCT|BKN|OVC)(\d{2,3})?(CB|TCU)?", re.IGNORECASE)
CLOUD_WORD = {"FEW": "few", "SCT": "scattered", "BKN": "broken", "OVC": "overcast"}
CLOUD_TYPE = {"CB": "cumulonimbus", "TCU": "towering cumulus"}

def _format_clouds(sky: str) -> Optional[str]:
    if not sky:
        return None
    up = sky.upper()
    if "CLR" in up or "SKC" in up:
        return "clear skies"
    phrases = []
    for m in CLOUD_RE.finditer(up):
        layer, hgt, conv = m.groups()
        layer_word = CLOUD_WORD.get(layer, layer.lower())
        add = f" {CLOUD_TYPE.get(conv, conv.lower())}" if conv else ""
        if hgt:
            try:
                feet = int(hgt) * 100
                phrases.append(f"{layer_word}{add} at {feet} ft")
            except:
                phrases.append(f"{layer_word}{add}")
        else:
            phrases.append(f"{layer_word}{add}")
    return ", ".join(phrases) if phrases else sky.lower()

def relative_time(timestr: Optional[str]) -> str:
    if not timestr:
        return "time unknown"
    if str(timestr).isdigit():
        try:
            t = datetime.fromtimestamp(int(timestr), tz=timezone.utc)
        except Exception:
            return f"reported at {timestr}"
    else:
        try:
            t = datetime.fromisoformat(str(timestr).replace("Z", "+00:00"))
        except Exception:
            return f"reported at {timestr}"

    now = datetime.now(timezone.utc)
    delta = now - t
    mins = int(delta.total_seconds() // 60)

    if mins < 1:
        return "observed just now"
    if mins < 60:
        return f"observed {mins} minutes ago"
    hours, mins = divmod(mins, 60)
    return f"observed {hours}h {mins}m ago"

def make_summary(p: PIREP) -> str:
    parts = []
    if p.turbulence:
        parts.append(f"{severity_icon(p.turbulence)} {p.turbulence} turbulence reported")
    if p.icing:
        parts.append(f"{severity_icon(p.icing)} {p.icing} icing observed")
    clouds = _format_clouds(p.sky or "")
    if clouds:
        parts.append(clouds)
    if p.temp_c is not None:
        temp_str = f"{p.temp_c:.0f}" if float(p.temp_c).is_integer() else f"{p.temp_c}"
        parts.append(f"temperature {temp_str} degrees Celsius")
    if p.aircraft:
        parts.append(f"aircraft type {p.aircraft}")
    if p.remarks:
        parts.append(f"remarks {p.remarks}")
    alt = f"{p.altitude_ft_msl} ft" if p.altitude_ft_msl else "altitude not given"
    loc = AIRPORT_LOOKUP.get(p.station, f"near {p.station}") if p.station else "location unknown"
    time_info = relative_time(p.obs_time or p.receipt_time)
    return " | ".join(str(x) for x in (parts + [alt, loc, time_info]))

def _first(*keys: str):
    def pick(d: Dict[str, Any], default=None):
        for k in keys:
            if k in d and d[k] not in (None, ""):
                return d[k]
        return default
    return pick

_pick_raw = _first("rawOb", "rawText", "raw", "report")
_pick_obs_time = _first("obsTime", "observationTime", "observation_time", "timeObs", "TM")
_pick_receipt_time = _first("receiptTime", "receipt_time")
_pick_lat = _first("lat", "latitude")
_pick_lon = _first("lon", "longitude")
_pick_alt_ft = _first("altitude_ft_msl", "altitudeFtMsl", "altitude_ft", "altitudeFt", "altitude", "FL")
_pick_station = _first("station", "stationId", "icaoId", "airport", "id", "location")

class PIREPService:
    def __init__(self, base_url: str = "https://aviationweather.gov/api/data", verbose: bool = False):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "PIREPSummarizer/5.0"})
        self.verbose = verbose

    def _log(self, *args):
        if self.verbose:
            print(*args, file=sys.stderr)

    def fetch(self, *, station_id: str, distance_mi: int = 150, age_hours: int = 2, fmt: str = "json") -> List[Dict]:
        url = f"{self.base_url}/pirep"
        params = {"format": fmt, "age": age_hours, "id": station_id, "distance": distance_mi}
        try:
            r = self.session.get(url, params=params, timeout=15)
            if r.status_code == 204:
                return []
            r.raise_for_status()
            data = r.json()
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                for key in ("reports", "data", "pireps", "items"):
                    if key in data and isinstance(data[key], list):
                        return data[key]
                return [data]
            return []
        except Exception as e:
            self._log(f"[WARN] Request failed: {e}")
            return []

    def parse_api_json(self, items: List[Dict]) -> List[PIREP]:
        pireps: List[PIREP] = []
        for it in items:
            p = PIREP(
                raw=_pick_raw(it, ""),
                type=_first("type", "reportType")(it),
                obs_time=_pick_obs_time(it),
                receipt_time=_pick_receipt_time(it),
                lat=_pick_lat(it),
                lon=_pick_lon(it),
                altitude_ft_msl=_pick_alt_ft(it),
                station=_pick_station(it),
            )
            pireps.append(parse_raw(p.raw or "", base=p))
        return pireps

    def fetch_and_sort(self, *, station_id: str, distance_mi: int = 150, age_hours: int = 2) -> List[PIREP]:
        items = self.fetch(station_id=station_id, distance_mi=distance_mi, age_hours=age_hours)
        if not items:
            return []
        pireps = self.parse_api_json(items)

        def sort_key(p: PIREP):
            time_str = p.obs_time or p.receipt_time
            try:
                if str(time_str).isdigit():
                    return datetime.fromtimestamp(int(time_str), tz=timezone.utc)
                return datetime.fromisoformat(str(time_str).replace("Z", "+00:00"))
            except Exception:
                return datetime.min

        return sorted(pireps, key=sort_key, reverse=True)

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure app
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize services
weather_service = WeatherService()
weather_analyzer = WeatherAnalyzer()
visualizer = WeatherVisualizer()
notam_service = NotamService()
nlp_analyzer = AviationNLPAnalyzer()
pirep_service = PIREPService(verbose=True)

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')



@app.route('/api/weather/individual', methods=['POST'])
def get_individual_weather():
    """Get individual weather reports for specific airports"""
    try:
        data = request.get_json()
        airport_code = data.get('airport_code', '').upper()
        report_types = data.get('report_types', ['METAR'])
        
        if not airport_code:
            return jsonify({'error': 'Airport code is required'}), 400
            
        results = {}
        
        for report_type in report_types:
            if report_type == 'METAR':
                results['metar'] = weather_service.get_metar(airport_code)
            elif report_type == 'TAF':
                results['taf'] = weather_service.get_taf(airport_code)
            elif report_type == 'PIREP':
                # Use the enhanced PIREP service instead of the old weather service
                pireps = pirep_service.fetch_and_sort(
                    station_id=airport_code.upper(),
                    distance_mi=150,
                    age_hours=6
                )
                # Convert to the format expected by the frontend
                pirep_list = []
                for pirep in pireps:
                    # Debug: log the actual PIREP data
                    logging.info(f"PIREP data: obs_time={pirep.obs_time}, receipt_time={getattr(pirep, 'receipt_time', None)}, raw={pirep.raw[:50] if pirep.raw else None}")
                    
                    pirep_dict = {
                        'raw_text': pirep.raw,
                        'observation_time': pirep.obs_time,
                        'receipt_time': getattr(pirep, 'receipt_time', None),
                        'aircraft_type': pirep.aircraft,
                        'altitude': pirep.altitude_ft_msl,
                        'location': pirep.station,
                        'report_type': 'PIREP',
                        'simplified': make_summary(pirep),
                        'turbulence': pirep.turbulence,
                        'icing': pirep.icing,
                        'sky': pirep.sky,
                        'temp_c': pirep.temp_c,
                        'remarks': pirep.remarks
                    }
                    pirep_list.append(pirep_dict)
                results['pirep'] = pirep_list
            elif report_type == 'NOTAM':
                results['notam'] = notam_service.get_notams(airport_code)
                results['notam_summary'] = notam_service.get_notam_summary(results['notam'])
                
        # Analyze weather conditions using ALL available data
        results['analysis'] = weather_analyzer.analyze_combined_weather_data(results)
        
        # Parse weather data using NLP parser
        results['parsed_data'] = nlp_analyzer.parse_weather_data({airport_code: results})
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/api/flight-plan/analyze', methods=['POST'])
def analyze_flight_plan():
    """Analyze weather along a flight plan route"""
    try:
        data = request.get_json()
        
        # Initialize common variables
        departure_time = data.get('departure_time', '')  # ISO format or relative time
        
        # Handle different input methods
        if 'flight_plan_text' in data:
            # Parse uploaded flight plan
            airports = flight_parser.parse_flight_plan_text(data['flight_plan_text'])
            if not airports or len(airports) < 2:
                return jsonify({
                    'error': 'Could not extract valid airport codes from flight plan. Please ensure the flight plan contains at least departure and arrival airports in ICAO format (e.g., KJFK, KLAX).'
                }), 400
        else:
            # Manual input of airports
            departure = data.get('departure', '').upper()
            arrival = data.get('arrival', '').upper()
            waypoints = [wp.upper() for wp in data.get('waypoints', [])]
            
            if not departure or not arrival:
                return jsonify({'error': 'Departure and arrival airports are required'}), 400
            
            airports = [departure] + waypoints + [arrival]
            
            # Basic ICAO format validation (4 letters)
            for airport in airports:
                if not airport or len(airport) != 4 or not airport.isalpha():
                    return jsonify({
                        'error': f"Invalid airport code format: {airport}. Please use 4-letter ICAO codes."
                    }), 400
        
        # Get weather data for all airports (time-aware) with validation
        weather_data = {}
        invalid_airports = []
        
        for airport in airports:
            # Use time-appropriate weather data
            time_weather = weather_service.get_time_appropriate_weather(airport, departure_time)
            
            # Check if we got valid weather data (airport exists)
            if not time_weather['metar'] and not time_weather['taf']:
                invalid_airports.append(airport)
                continue
                
            airport_weather = {
                'metar': time_weather['metar'],
                'taf': time_weather['taf'],
                'pirep': time_weather['pirep'],
                'time_appropriate_conditions': time_weather['time_appropriate_conditions'],
                'primary_source': time_weather['primary_source']
            }
            
            # Analyze conditions using ALL available data (METAR, TAF, PIREP)
            airport_weather['analysis'] = weather_analyzer.analyze_combined_weather_data(airport_weather)
            
            weather_data[airport] = airport_weather
        
        # Return error if any airports are invalid
        if invalid_airports:
            return jsonify({
                'error': f"No weather data found for airport(s): {', '.join(invalid_airports)}. Please check the airport codes and try again."
            }), 400
        
        # Generate visualizations
        visualizations = {
            'wind_chart': visualizer.create_wind_chart(weather_data),
            'visibility_chart': visualizer.create_visibility_chart(weather_data),
            'route_map': visualizer.create_route_map(airports, weather_data),
            'weather_timeline': visualizer.create_weather_timeline(weather_data)
        }
        
        # Generate consolidated briefing
        briefing = weather_analyzer.generate_flight_briefing(weather_data, airports)
        
        # Get NOTAMs for all airports
        notam_data = {}
        for airport in airports:
            notams = notam_service.get_notams(airport)
            notam_data[airport] = {
                'notams': notams,
                'summary': notam_service.get_notam_summary(notams)
            }
        
        # Generate NLP-based intelligent summary
        nlp_analysis = nlp_analyzer.generate_comprehensive_summary(weather_data, airports, briefing)
        
        # Parse weather data using NLP parser
        parsed_weather_data = nlp_analyzer.parse_weather_data(weather_data)
        
        # Calculate route distance
        total_distance_nm = calculate_route_distance(airports)
        
        # Get current UTC time
        current_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        return jsonify({
            'airports': airports,
            'weather_data': weather_data,
            'parsed_weather_data': parsed_weather_data,
            'briefing': briefing,
            'notam_data': notam_data,
            'visualizations': visualizations,
            'nlp_analysis': nlp_analysis,
            'route_info': {
                'total_distance_nm': round(total_distance_nm, 1),
                'current_utc_time': current_utc,
                'departure_airport': airports[0] if airports else None,
                'arrival_airport': airports[-1] if airports else None,
                'waypoints_count': len(airports) - 2 if len(airports) > 2 else 0
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/api/pireps/<station_id>', methods=['GET'])
def get_pirep_reports(station_id):
    """Get PIREP reports for a specific station with enhanced processing"""
    try:
        max_distance_nm = int(request.args.get('max_distance_nm', 150))
        max_age_hours = float(request.args.get('max_age_hours', 6))
        show_raw = request.args.get('raw', 'false').lower() == 'true'
        
        # Use the enhanced PIREP service
        pireps = pirep_service.fetch_and_sort(
            station_id=station_id.upper(),
            distance_mi=max_distance_nm,
            age_hours=max_age_hours
        )
        
        # Convert PIREPs to enhanced dict format with severity and age calculation
        pirep_list = []
        for pirep in pireps:
            # Calculate severity based on turbulence and icing
            severity_level = 0
            severity_description = "Routine"
            severity_color = "success"
            
            if pirep.turbulence:
                if "Severe" in pirep.turbulence or "Extreme" in pirep.turbulence:
                    severity_level = max(severity_level, 4)
                    severity_description = "Severe"
                    severity_color = "danger"
                elif "Moderate" in pirep.turbulence:
                    severity_level = max(severity_level, 3)
                    severity_description = "Moderate"
                    severity_color = "warning"
                elif "Light" in pirep.turbulence:
                    severity_level = max(severity_level, 2)
                    severity_description = "Light"
                    severity_color = "info"
            
            if pirep.icing:
                if "Severe" in pirep.icing or "Extreme" in pirep.icing:
                    severity_level = max(severity_level, 4)
                    severity_description = "Severe"
                    severity_color = "danger"
                elif "Moderate" in pirep.icing:
                    severity_level = max(severity_level, 3)
                    severity_description = "Moderate"
                    severity_color = "warning"
                elif "Light" in pirep.icing:
                    severity_level = max(severity_level, 2)
                    severity_description = "Light"
                    severity_color = "info"
            
            # Calculate age in hours
            age_hours = None
            if pirep.obs_time or pirep.receipt_time:
                time_str = pirep.obs_time or pirep.receipt_time
                try:
                    if str(time_str).isdigit():
                        report_time = datetime.fromtimestamp(int(time_str), tz=timezone.utc)
                    else:
                        report_time = datetime.fromisoformat(str(time_str).replace("Z", "+00:00"))
                    
                    now = datetime.now(timezone.utc)
                    age_hours = (now - report_time).total_seconds() / 3600
                except Exception:
                    pass
            
            pirep_dict = {
                'raw': pirep.raw,
                'raw_text': pirep.raw,  # For compatibility
                'type': pirep.type,
                'obs_time': pirep.obs_time,
                'receipt_time': pirep.receipt_time,
                'observation_time': pirep.obs_time,  # For compatibility
                'lat': pirep.lat,
                'lon': pirep.lon,
                'altitude_ft_msl': pirep.altitude_ft_msl,
                'altitude': pirep.altitude_ft_msl,  # For compatibility
                'station': pirep.station,
                'aircraft_type': pirep.aircraft,
                'turbulence': pirep.turbulence,
                'icing': pirep.icing,
                'sky': pirep.sky,
                'temp_c': pirep.temp_c,
                'aircraft': pirep.aircraft,
                'remarks': pirep.remarks,
                'simplified': make_summary(pirep),
                'severity': {
                    'level': severity_level,
                    'description': severity_description,
                    'color': severity_color
                },
                'age_hours': age_hours,
                'components': {
                    'aircraft': pirep.aircraft,
                    'altitude': f"{pirep.altitude_ft_msl}" if pirep.altitude_ft_msl else None,
                    'location': AIRPORT_LOOKUP.get(pirep.station, pirep.station) if pirep.station else None
                }
            }
            
            pirep_list.append(pirep_dict)
        
        return jsonify({
            'station_id': station_id.upper(),
            'pireps': pirep_list,
            'count': len(pirep_list),
            'max_distance_nm': max_distance_nm,
            'max_age_hours': max_age_hours,
            'show_raw': show_raw
        })
        
    except Exception as e:
        logging.error(f"Error fetching PIREP reports: {e}")
        return jsonify({'error': f'Failed to fetch PIREP reports: {str(e)}'}), 500

@app.route('/api/airport/search/<icao_code>', methods=['GET'])
def search_airport(icao_code):
    """Search for airport information including coordinates"""
    try:
        from global_airport_service import global_airport_service
        
        airport_info = global_airport_service.get_airport_info(icao_code)
        
        if airport_info:
            return jsonify({
                'found': True,
                'airport': airport_info,
                'message': f'Airport {icao_code.upper()} found successfully'
            })
        else:
            return jsonify({
                'found': False,
                'airport': None,
                'message': f'Airport {icao_code.upper()} not found in any database',
                'suggestions': [
                    'Verify the ICAO code (4-letter code)',
                    'Try IATA code instead (3-letter code)',
                    'Check if it\'s a military or private airfield',
                    'Use a nearby major airport'
                ]
            }), 404
            
    except Exception as e:
        logging.error(f"Error searching for airport {icao_code}: {e}")
        return jsonify({
            'found': False,
            'error': str(e),
            'message': 'Error occurred while searching for airport'
        }), 500

@app.route('/api/airport/bulk-search', methods=['POST'])
def bulk_search_airports():
    """Search for multiple airports at once"""
    try:
        data = request.get_json()
        icao_codes = data.get('airports', [])
        
        if not icao_codes:
            return jsonify({'error': 'No airport codes provided'}), 400
        
        from global_airport_service import global_airport_service
        results = global_airport_service.bulk_lookup(icao_codes)
        
        found_airports = {}
        missing_airports = []
        
        for icao_code, coords in results.items():
            if coords:
                found_airports[icao_code] = {
                    'icao': icao_code,
                    'coordinates': coords,
                    'latitude': coords[0],
                    'longitude': coords[1]
                }
            else:
                missing_airports.append(icao_code)
        
        return jsonify({
            'found_airports': found_airports,
            'missing_airports': missing_airports,
            'total_searched': len(icao_codes),
            'found_count': len(found_airports),
            'missing_count': len(missing_airports)
        })
        
    except Exception as e:
        logging.error(f"Error in bulk airport search: {e}")
        return jsonify({'error': str(e)}), 500

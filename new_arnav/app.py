from flask import Flask, render_template, request, jsonify
import os
import logging
from config import config
from weather_service import WeatherService
from weather_analyzer import WeatherAnalyzer
from nlp_analyzer import AviationNLPAnalyzer
from visualizations import WeatherVisualizer
from notam_service import NotamService
from airport_coordinates import calculate_route_distance
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
config_name = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[config_name])

# Initialize services
weather_service = WeatherService()
weather_analyzer = WeatherAnalyzer()
visualizer = WeatherVisualizer()
nlp_analyzer = AviationNLPAnalyzer()
notam_service = NotamService()

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
                results['pirep'] = weather_service.get_pirep(airport_code)
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
        
        # Handle different input methods
        if 'flight_plan_text' in data:
            # Parse uploaded flight plan
            airports = flight_parser.parse_flight_plan_text(data['flight_plan_text'])
        else:
            # Manual input of airports
            departure = data.get('departure', '').upper()
            arrival = data.get('arrival', '').upper()
            waypoints = [wp.upper() for wp in data.get('waypoints', [])]
            departure_time = data.get('departure_time', '')  # ISO format or relative time
            
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
        max_distance_nm = int(request.args.get('max_distance_nm', 50))
        max_age_hours = int(request.args.get('max_age_hours', 3))
        
        # Use the enhanced PIREP service
        pireps = weather_processor.pirep_service.fetch_and_sort(
            station_id=station_id.upper(),
            distance_mi=max_distance_nm,
            age_hours=max_age_hours
        )
        
        # Convert PIREPs to enhanced dict format with severity and age calculation
        pirep_list = []
        for pirep in pireps:
            # Calculate severity based on turbulence and icing
            severity_level = 0
            severity_description = "Unknown"
            severity_color = "secondary"
            
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
            
            if severity_level == 0:
                severity_description = "Routine"
                severity_color = "success"
                severity_level = 1
            
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
            'max_age_hours': max_age_hours
        })
        
    except Exception as e:
        logging.error(f"Error fetching PIREP reports: {e}")
        return jsonify({'error': f'Failed to fetch PIREP reports: {str(e)}'}), 500

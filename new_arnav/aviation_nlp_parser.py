"""
Aviation Weather NLP Parser
Comprehensive parser for METAR, TAF, and PIREP codes with simplified English output
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

class AviationWeatherParser:
    """Advanced parser for aviation weather codes with NLP-style simplified output"""
    
    def __init__(self):
        # Weather phenomena translations
        self.weather_phenomena = {
            # Precipitation
            'RA': 'rain', 'DZ': 'drizzle', 'SN': 'snow', 'SG': 'snow grains',
            'IC': 'ice crystals', 'PL': 'ice pellets', 'GR': 'hail', 'GS': 'small hail',
            'UP': 'unknown precipitation',
            
            # Obscuration
            'FG': 'fog', 'BR': 'mist', 'HZ': 'haze', 'DU': 'dust', 'SA': 'sand',
            'FU': 'smoke', 'VA': 'volcanic ash', 'PY': 'spray',
            
            # Other phenomena
            'SQ': 'squalls', 'FC': 'funnel cloud', 'SS': 'sandstorm', 'DS': 'duststorm',
            'PO': 'dust whirls', 'TS': 'thunderstorm'
        }
        
        # Intensity prefixes
        self.intensity_prefixes = {
            '-': 'light', '+': 'heavy', 'VC': 'in vicinity'
        }
        
        # Descriptor prefixes
        self.descriptors = {
            'MI': 'shallow', 'PR': 'partial', 'BC': 'patches', 'DR': 'drifting',
            'BL': 'blowing', 'SH': 'showers', 'FZ': 'freezing', 'RE': 'recent'
        }
        
        # Cloud types
        self.cloud_types = {
            'FEW': 'few clouds', 'SCT': 'scattered clouds', 'BKN': 'broken clouds',
            'OVC': 'overcast', 'CLR': 'clear', 'SKC': 'sky clear', 'NSC': 'no significant cloud',
            'NCD': 'no cloud detected', 'VV': 'vertical visibility'
        }
        
        # Wind direction translations
        self.wind_directions = {
            'VRB': 'variable direction',
            '000': 'calm'
        }
        
        # Flight categories
        self.flight_categories = {
            'VFR': 'Visual Flight Rules conditions',
            'MVFR': 'Marginal Visual Flight Rules conditions',
            'IFR': 'Instrument Flight Rules conditions',
            'LIFR': 'Low Instrument Flight Rules conditions'
        }
        
        # PIREP severity levels
        self.pirep_severity = {
            'NEG': {'level': 0, 'description': 'negative', 'color': 'success'},
            'TRACE': {'level': 1, 'description': 'trace', 'color': 'info'},
            'LGT': {'level': 2, 'description': 'light', 'color': 'warning'},
            'MOD': {'level': 3, 'description': 'moderate', 'color': 'warning'},
            'SEV': {'level': 4, 'description': 'severe', 'color': 'danger'},
            'EXTRM': {'level': 5, 'description': 'extreme', 'color': 'danger'}
        }
        
        # Turbulence types
        self.turbulence_types = {
            'CAT': 'clear air turbulence',
            'CHOP': 'choppy conditions',
            'LLWS': 'low level wind shear'
        }
        
        # Icing types
        self.icing_types = {
            'RIME': 'rime ice',
            'CLR': 'clear ice',
            'MXD': 'mixed ice'
        }

    def parse_metar(self, raw_metar: str) -> Dict:
        """Parse METAR code and return both raw and simplified versions"""
        if not raw_metar:
            return {'raw': '', 'simplified': 'No METAR data available', 'components': {}}
        
        try:
            components = self._extract_metar_components(raw_metar)
            simplified = self._generate_metar_simplified(components)
            
            return {
                'raw': raw_metar.strip(),
                'simplified': simplified,
                'components': components
            }
        except Exception as e:
            logging.error(f"Error parsing METAR: {e}")
            return {
                'raw': raw_metar.strip(),
                'simplified': f'Unable to parse METAR | {raw_metar}',
                'components': {}
            }

    def parse_taf(self, raw_taf: str) -> Dict:
        """Parse TAF code and return both raw and simplified versions"""
        if not raw_taf:
            return {'raw': '', 'simplified': 'No TAF data available', 'components': {}}
        
        try:
            components = self._extract_taf_components(raw_taf)
            simplified = self._generate_taf_simplified(components)
            
            return {
                'raw': raw_taf.strip(),
                'simplified': simplified,
                'components': components
            }
        except Exception as e:
            logging.error(f"Error parsing TAF: {e}")
            return {
                'raw': raw_taf.strip(),
                'simplified': f'Unable to parse TAF | {raw_taf}',
                'components': {}
            }

    def parse_pirep(self, raw_pirep: str) -> Dict:
        """Parse PIREP code and return both raw and simplified versions with severity"""
        if not raw_pirep:
            return {
                'raw': '', 
                'simplified': 'No PIREP data available', 
                'components': {},
                'severity': {'level': 0, 'description': 'none', 'color': 'secondary'},
                'age_hours': 0
            }
        
        try:
            components = self._extract_pirep_components(raw_pirep)
            simplified = self._generate_pirep_simplified(components)
            severity = self._calculate_pirep_severity(components)
            age_hours = self._calculate_pirep_age(components)
            
            return {
                'raw': raw_pirep.strip(),
                'simplified': simplified,
                'components': components,
                'severity': severity,
                'age_hours': age_hours
            }
        except Exception as e:
            logging.error(f"Error parsing PIREP: {e}")
            return {
                'raw': raw_pirep.strip(),
                'simplified': f'Unable to parse PIREP | {raw_pirep}',
                'components': {},
                'severity': {'level': 0, 'description': 'unknown', 'color': 'secondary'},
                'age_hours': 0
            }

    def _extract_metar_components(self, metar: str) -> Dict:
        """Extract components from METAR string"""
        components = {
            'station': '',
            'time': '',
            'wind': {},
            'visibility': '',
            'weather': [],
            'clouds': [],
            'temperature': '',
            'dewpoint': '',
            'altimeter': '',
            'remarks': ''
        }
        
        # Clean and split METAR
        metar_parts = metar.strip().split()
        
        for i, part in enumerate(metar_parts):
            # Station identifier (first 4 letters)
            if i == 0 and len(part) == 4 and part.isalpha():
                components['station'] = part
            
            # Date/time group (6 digits + Z)
            elif re.match(r'\d{6}Z', part):
                components['time'] = self._parse_time(part)
            
            # Wind information
            elif re.match(r'\d{3}\d{2,3}(G\d{2,3})?KT', part) or part == '00000KT':
                components['wind'] = self._parse_wind(part)
            
            # Variable wind direction
            elif re.match(r'\d{3}V\d{3}', part):
                components['wind']['variable'] = part
            
            # Visibility
            elif re.match(r'\d{1,2}SM|\d{1,2}/\d{1,2}SM|\d{1,2} \d{1,2}/\d{1,2}SM', part):
                components['visibility'] = self._parse_visibility(part)
            
            # Weather phenomena
            elif self._is_weather_phenomenon(part):
                components['weather'].append(self._parse_weather_phenomenon(part))
            
            # Cloud information
            elif re.match(r'(FEW|SCT|BKN|OVC|CLR|SKC|VV)\d{3}', part):
                components['clouds'].append(self._parse_cloud_layer(part))
            
            # Temperature and dewpoint
            elif re.match(r'M?\d{2}/M?\d{2}', part):
                temp_parts = part.split('/')
                components['temperature'] = self._parse_temperature(temp_parts[0])
                components['dewpoint'] = self._parse_temperature(temp_parts[1])
            
            # Altimeter setting
            elif re.match(r'A\d{4}', part):
                components['altimeter'] = self._parse_altimeter(part)
            
            # Remarks (everything after RMK)
            elif part == 'RMK':
                components['remarks'] = ' '.join(metar_parts[i+1:])
                break
        
        return components

    def _extract_taf_components(self, taf: str) -> Dict:
        """Extract components from TAF string with enhanced parsing"""
        components = {
            'type': 'TAF',
            'station': '',
            'issue_time': '',
            'valid_period': '',
            'forecasts': [],
            'significant_changes': []
        }
        
        # Clean and normalize TAF
        taf_clean = re.sub(r'\s+', ' ', taf.strip())
        taf_parts = taf_clean.split()
        
        # Extract header information
        i = 0
        while i < len(taf_parts):
            part = taf_parts[i]
            
            if part == 'TAF':
                i += 1
                continue
            elif part in ['AMD', 'COR']:  # Amendment or correction
                components['type'] = f"TAF {part}"
                i += 1
                continue
            elif len(part) == 4 and part.isalpha():
                components['station'] = part
                i += 1
                continue
            elif re.match(r'\d{6}Z', part):
                components['issue_time'] = self._parse_time(part)
                i += 1
                continue
            elif re.match(r'\d{4}/\d{4}', part):
                components['valid_period'] = self._parse_valid_period(part)
                i += 1
                break
            else:
                i += 1
        
        # Parse forecast groups
        remaining_parts = taf_parts[i:]
        forecast_groups = self._split_forecast_groups(remaining_parts)
        
        for group in forecast_groups:
            forecast = self._parse_forecast_group(group)
            if forecast:
                components['forecasts'].append(forecast)
        
        # Identify significant changes
        components['significant_changes'] = self._identify_significant_changes(components['forecasts'])
        
        return components

    def _extract_pirep_components(self, pirep: str) -> Dict:
        """Extract components from PIREP string"""
        components = {
            'type': 'PIREP',
            'location': '',
            'time': '',
            'aircraft': '',
            'altitude': '',
            'turbulence': [],
            'icing': [],
            'visibility': '',
            'weather': [],
            'clouds': [],
            'temperature': '',
            'wind': {},
            'remarks': ''
        }
        
        # Extract basic information using regex patterns
        pirep_upper = pirep.upper()
        
        # Location
        loc_match = re.search(r'/OV\s+([A-Z0-9\-/]+)', pirep_upper)
        if loc_match:
            components['location'] = loc_match.group(1)
        
        # Time
        time_match = re.search(r'/TM\s+(\d{4})', pirep_upper)
        if time_match:
            components['time'] = time_match.group(1)
        
        # Aircraft type
        ac_match = re.search(r'/TP\s+([A-Z0-9]+)', pirep_upper)
        if ac_match:
            components['aircraft'] = ac_match.group(1)
        
        # Altitude
        alt_match = re.search(r'/FL(\d{3})|/(\d{3,5})', pirep_upper)
        if alt_match:
            components['altitude'] = alt_match.group(1) or alt_match.group(2)
        
        # Turbulence
        turb_match = re.search(r'/TB\s+([^/]+)', pirep_upper)
        if turb_match:
            components['turbulence'] = self._parse_pirep_turbulence(turb_match.group(1))
        
        # Icing
        ice_match = re.search(r'/IC\s+([^/]+)', pirep_upper)
        if ice_match:
            components['icing'] = self._parse_pirep_icing(ice_match.group(1))
        
        # Remarks
        rm_match = re.search(r'/RM\s+(.+)', pirep_upper)
        if rm_match:
            components['remarks'] = rm_match.group(1)
        
        return components

    def _generate_metar_simplified(self, components: Dict) -> str:
        """Generate simplified English string for METAR"""
        parts = []
        
        # Station and time
        if components.get('station'):
            parts.append(f"Station {components['station']}")
        
        if components.get('time'):
            parts.append(f"observed at {components['time']}")
        
        # Wind
        wind = components.get('wind', {})
        if wind:
            wind_desc = self._describe_wind(wind)
            if wind_desc:
                parts.append(wind_desc)
        
        # Visibility
        if components.get('visibility'):
            parts.append(f"visibility {components['visibility']}")
        
        # Weather phenomena
        weather = components.get('weather', [])
        if weather:
            weather_desc = ' and '.join([w['description'] for w in weather])
            parts.append(weather_desc)
        
        # Clouds
        clouds = components.get('clouds', [])
        if clouds:
            cloud_desc = self._describe_clouds(clouds)
            if cloud_desc:
                parts.append(cloud_desc)
        
        # Temperature and dewpoint
        if components.get('temperature') and components.get('dewpoint'):
            parts.append(f"temperature {components['temperature']}°C | dewpoint {components['dewpoint']}°C")
        
        # Altimeter
        if components.get('altimeter'):
            parts.append(f"altimeter {components['altimeter']} inHg")
        
        return ' | '.join(parts) if parts else 'No weather information available'

    def _generate_taf_simplified(self, components: Dict) -> str:
        """Generate simplified English string for TAF"""
        parts = []
        
        if components.get('station'):
            parts.append(f"Terminal forecast for {components['station']}")
        
        if components.get('issue_time'):
            parts.append(f"issued {components['issue_time']}")
        
        if components.get('valid_period'):
            parts.append(f"valid {components['valid_period']}")
        
        # Process forecast periods
        forecasts = components.get('forecasts', [])
        if forecasts:
            forecast_summaries = []
            for forecast in forecasts:
                if 'summary' in forecast:
                    forecast_summaries.append(forecast['summary'])
                elif 'conditions' in forecast:
                    conditions = []
                    if forecast['conditions'].get('wind'):
                        conditions.append(forecast['conditions']['wind'])
                    if forecast['conditions'].get('visibility'):
                        conditions.append(f"visibility {forecast['conditions']['visibility']}")
                    if forecast['conditions'].get('weather'):
                        conditions.append(forecast['conditions']['weather'])
                    if forecast['conditions'].get('clouds'):
                        conditions.append(forecast['conditions']['clouds'])
                    
                    if conditions:
                        period = forecast.get('period', 'forecast period')
                        forecast_summaries.append(f"{period}: {', '.join(conditions)}")
            
            if forecast_summaries:
                parts.extend(forecast_summaries)
            else:
                parts.append("detailed forecast conditions available")
        
        # Add any significant weather changes
        if components.get('significant_changes'):
            parts.append(f"significant changes: {components['significant_changes']}")
        
        return ' | '.join(parts) if parts else 'No forecast information available'

    def _generate_pirep_simplified(self, components: Dict) -> str:
        """Generate simplified English string for PIREP"""
        parts = []
        
        # Location and time
        if components.get('location'):
            parts.append(f"Location {components['location']}")
        
        if components.get('time'):
            parts.append(f"reported at {components['time']}Z")
        
        # Aircraft and altitude
        if components.get('aircraft'):
            parts.append(f"aircraft {components['aircraft']}")
        
        if components.get('altitude'):
            alt = components['altitude']
            if len(alt) == 3:  # Flight level
                parts.append(f"at FL{alt}")
            else:
                parts.append(f"at {alt} feet")
        
        # Turbulence
        turbulence = components.get('turbulence', [])
        if turbulence:
            turb_desc = ' and '.join([t['description'] for t in turbulence])
            parts.append(f"turbulence: {turb_desc}")
        
        # Icing
        icing = components.get('icing', [])
        if icing:
            ice_desc = ' and '.join([i['description'] for i in icing])
            parts.append(f"icing: {ice_desc}")
        
        # Remarks
        if components.get('remarks'):
            parts.append(f"remarks: {components['remarks']}")
        
        return ' | '.join(parts) if parts else 'No pilot report information available'

    def _parse_wind(self, wind_str: str) -> Dict:
        """Parse wind information"""
        if wind_str == '00000KT':
            return {'description': 'calm winds', 'speed': 0, 'direction': 0}
        
        # Extract wind components
        match = re.match(r'(\d{3})(\d{2,3})(G(\d{2,3}))?KT', wind_str)
        if match:
            direction = int(match.group(1))
            speed = int(match.group(2))
            gust = int(match.group(4)) if match.group(4) else None
            
            return {
                'direction': direction,
                'speed': speed,
                'gust': gust,
                'description': self._describe_wind({'direction': direction, 'speed': speed, 'gust': gust})
            }
        
        return {}

    def _describe_wind(self, wind: Dict) -> str:
        """Generate wind description"""
        if not wind:
            return ''
        
        if wind.get('speed', 0) == 0:
            return 'calm winds'
        
        direction = wind.get('direction', 0)
        speed = wind.get('speed', 0)
        gust = wind.get('gust')
        
        # Convert direction to compass
        compass = self._degrees_to_compass(direction)
        
        wind_desc = f"winds from {compass} at {speed} knots"
        if gust and gust > speed:
            wind_desc += f" gusting to {gust} knots"
        
        return wind_desc

    def _degrees_to_compass(self, degrees: int) -> str:
        """Convert degrees to compass direction"""
        directions = ['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest']
        index = round(degrees / 45) % 8
        return directions[index]

    def _parse_visibility(self, vis_str: str) -> str:
        """Parse visibility information"""
        if 'SM' in vis_str:
            vis_num = vis_str.replace('SM', '')
            return f"{vis_num} statute miles"
        return vis_str

    def _is_weather_phenomenon(self, code: str) -> bool:
        """Check if code represents weather phenomenon"""
        # Remove intensity and descriptor prefixes
        clean_code = code.lstrip('+-').lstrip('VC')
        for desc in self.descriptors:
            clean_code = clean_code.replace(desc, '')
        
        # Check if remaining code matches weather phenomena
        return any(phenom in clean_code for phenom in self.weather_phenomena)

    def _parse_weather_phenomenon(self, code: str) -> Dict:
        """Parse weather phenomenon code"""
        intensity = ''
        descriptor = ''
        phenomena = []
        
        # Extract intensity
        if code.startswith('-'):
            intensity = 'light'
            code = code[1:]
        elif code.startswith('+'):
            intensity = 'heavy'
            code = code[1:]
        elif code.startswith('VC'):
            intensity = 'in vicinity'
            code = code[2:]
        
        # Extract descriptor
        for desc_code, desc_text in self.descriptors.items():
            if code.startswith(desc_code):
                descriptor = desc_text
                code = code[len(desc_code):]
                break
        
        # Extract phenomena (2-letter codes)
        i = 0
        while i < len(code):
            if i + 1 < len(code):
                phenom_code = code[i:i+2]
                if phenom_code in self.weather_phenomena:
                    phenomena.append(self.weather_phenomena[phenom_code])
                    i += 2
                else:
                    i += 1
            else:
                i += 1
        
        # Build description
        desc_parts = []
        if intensity:
            desc_parts.append(intensity)
        if descriptor:
            desc_parts.append(descriptor)
        if phenomena:
            desc_parts.extend(phenomena)
        
        return {
            'code': code,
            'intensity': intensity,
            'descriptor': descriptor,
            'phenomena': phenomena,
            'description': ' '.join(desc_parts) if desc_parts else code
        }

    def _parse_cloud_layer(self, cloud_str: str) -> Dict:
        """Parse cloud layer information"""
        match = re.match(r'(FEW|SCT|BKN|OVC|CLR|SKC|VV)(\d{3})', cloud_str)
        if match:
            coverage = match.group(1)
            height = int(match.group(2)) * 100  # Convert to feet
            
            return {
                'coverage': coverage,
                'height': height,
                'description': f"{self.cloud_types.get(coverage, coverage)} at {height} feet"
            }
        
        return {'description': cloud_str}

    def _describe_clouds(self, clouds: List[Dict]) -> str:
        """Generate cloud description"""
        if not clouds:
            return ''
        
        descriptions = [cloud['description'] for cloud in clouds if 'description' in cloud]
        return ' | '.join(descriptions)

    def _parse_temperature(self, temp_str: str) -> str:
        """Parse temperature string"""
        if temp_str.startswith('M'):
            return f"-{temp_str[1:]}"
        return temp_str

    def _parse_altimeter(self, alt_str: str) -> str:
        """Parse altimeter setting"""
        if alt_str.startswith('A'):
            alt_num = alt_str[1:]
            return f"{alt_num[:2]}.{alt_num[2:]}"
        return alt_str

    def _parse_time(self, time_str: str) -> str:
        """Parse time string"""
        if time_str.endswith('Z'):
            time_num = time_str[:-1]
            day = time_num[:2]
            hour = time_num[2:4]
            minute = time_num[4:6]
            return f"{day}th at {hour}:{minute}Z"
        return time_str

    def _parse_valid_period(self, period_str: str) -> str:
        """Parse TAF valid period"""
        if '/' in period_str:
            start, end = period_str.split('/')
            return f"from {start[:2]}:{start[2:]}Z to {end[:2]}:{end[2:]}Z"
        return period_str

    def _parse_pirep_turbulence(self, turb_str: str) -> List[Dict]:
        """Parse PIREP turbulence information"""
        turbulence = []
        
        # Look for severity indicators
        for severity, info in self.pirep_severity.items():
            if severity in turb_str:
                turbulence.append({
                    'severity': severity,
                    'level': info['level'],
                    'description': f"{info['description']} turbulence"
                })
        
        # Look for turbulence types
        for turb_type, description in self.turbulence_types.items():
            if turb_type in turb_str:
                turbulence.append({
                    'type': turb_type,
                    'description': description
                })
        
        return turbulence if turbulence else [{'description': turb_str}]

    def _parse_pirep_icing(self, ice_str: str) -> List[Dict]:
        """Parse PIREP icing information"""
        icing = []
        
        # Look for severity indicators
        for severity, info in self.pirep_severity.items():
            if severity in ice_str:
                icing.append({
                    'severity': severity,
                    'level': info['level'],
                    'description': f"{info['description']} icing"
                })
        
        # Look for icing types
        for ice_type, description in self.icing_types.items():
            if ice_type in ice_str:
                icing.append({
                    'type': ice_type,
                    'description': description
                })
        
        return icing if icing else [{'description': ice_str}]

    def _calculate_pirep_severity(self, components: Dict) -> Dict:
        """Calculate overall PIREP severity"""
        max_level = 0
        severity_info = {'level': 0, 'description': 'none', 'color': 'secondary'}
        
        # Check turbulence severity
        for turb in components.get('turbulence', []):
            if 'level' in turb:
                max_level = max(max_level, turb['level'])
        
        # Check icing severity
        for ice in components.get('icing', []):
            if 'level' in ice:
                max_level = max(max_level, ice['level'])
        
        # Determine overall severity
        for severity, info in self.pirep_severity.items():
            if info['level'] == max_level:
                severity_info = info
                break
        
        return severity_info

    def _calculate_pirep_age(self, components: Dict) -> float:
        """Calculate PIREP age in hours"""
        time_str = components.get('time', '')
        if not time_str or len(time_str) != 4:
            return 0
        
        try:
            # Parse HHMM format
            report_hour = int(time_str[:2])
            report_minute = int(time_str[2:])
            
            # Get current UTC time
            now = datetime.utcnow()
            
            # Create report time (assume today, adjust if needed)
            report_time = now.replace(hour=report_hour, minute=report_minute, second=0, microsecond=0)
            
            # If report time is in the future, assume it was yesterday
            if report_time > now:
                report_time -= timedelta(days=1)
            
            # Calculate age in hours
            age_delta = now - report_time
            return age_delta.total_seconds() / 3600
            
        except (ValueError, TypeError):
            return 0

    def filter_pireps_by_age_and_distance(self, pireps: List[Dict], max_age_hours: int = 3, 
                                        max_distance_nm: int = 50) -> List[Dict]:
        """Filter PIREPs by age and distance"""
        filtered = []
        
        for pirep in pireps:
            # Check age
            if pirep.get('age_hours', 0) <= max_age_hours:
                # For now, assume all PIREPs are within distance
                # In a full implementation, you'd calculate actual distance
                filtered.append(pirep)
        
        # Sort by time (newest first) then by severity (highest first)
        filtered.sort(key=lambda x: (x.get('age_hours', 0), -x.get('severity', {}).get('level', 0)))
        
        return filtered

    def _split_forecast_groups(self, parts: List[str]) -> List[List[str]]:
        """Split TAF parts into forecast groups"""
        groups = []
        current_group = []
        
        for part in parts:
            # Time group indicators
            if re.match(r'(FM|BECMG|TEMPO)\d{4}', part) or re.match(r'\d{4}/\d{4}', part):
                if current_group:
                    groups.append(current_group)
                current_group = [part]
            else:
                current_group.append(part)
        
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _parse_forecast_group(self, group: List[str]) -> Dict:
        """Parse individual forecast group"""
        if not group:
            return {}
        
        forecast = {
            'period': '',
            'conditions': {},
            'summary': ''
        }
        
        # Determine period type
        first_part = group[0]
        if first_part.startswith('FM'):
            forecast['period'] = f"From {self._parse_time_period(first_part[2:])}"
        elif first_part.startswith('BECMG'):
            forecast['period'] = f"Becoming {self._parse_time_period(first_part[5:])}"
        elif first_part.startswith('TEMPO'):
            forecast['period'] = f"Temporarily {self._parse_time_period(first_part[5:])}"
        elif '/' in first_part:
            forecast['period'] = f"Period {self._parse_valid_period(first_part)}"
        else:
            forecast['period'] = "Initial conditions"
        
        # Parse conditions in the group
        conditions = []
        for part in group[1:] if len(group) > 1 else group:
            # Wind
            if re.match(r'\d{3}\d{2,3}(G\d{2,3})?KT', part) or part == '00000KT':
                wind_info = self._parse_wind(part)
                if wind_info.get('description'):
                    forecast['conditions']['wind'] = wind_info['description']
                    conditions.append(wind_info['description'])
            
            # Visibility
            elif re.match(r'\d+SM', part) or re.match(r'\d{4}', part):
                vis_desc = self._parse_visibility(part)
                forecast['conditions']['visibility'] = vis_desc
                conditions.append(vis_desc)
            
            # Weather phenomena
            elif self._is_weather_phenomenon(part):
                weather_info = self._parse_weather_phenomenon(part)
                forecast['conditions']['weather'] = weather_info['description']
                conditions.append(weather_info['description'])
            
            # Clouds
            elif re.match(r'(FEW|SCT|BKN|OVC|CLR|SKC)\d{3}', part):
                cloud_info = self._parse_cloud_layer(part)
                forecast['conditions']['clouds'] = cloud_info['description']
                conditions.append(cloud_info['description'])
        
        # Create summary
        if conditions:
            forecast['summary'] = f"{forecast['period']}: {', '.join(conditions)}"
        else:
            forecast['summary'] = forecast['period']
        
        return forecast
    
    def _parse_time_period(self, time_str: str) -> str:
        """Parse time period for TAF"""
        if len(time_str) == 4:
            hour = time_str[:2]
            minute = time_str[2:]
            return f"{hour}:{minute}Z"
        return time_str
    
    def _identify_significant_changes(self, forecasts: List[Dict]) -> List[str]:
        """Identify significant weather changes in TAF"""
        changes = []
        
        for forecast in forecasts:
            period = forecast.get('period', '')
            conditions = forecast.get('conditions', {})
            
            # Check for significant weather
            if conditions.get('weather'):
                weather = conditions['weather']
                if any(term in weather.lower() for term in ['thunderstorm', 'heavy', 'freezing', 'snow']):
                    changes.append(f"{period}: {weather}")
            
            # Check for low visibility
            if conditions.get('visibility'):
                vis = conditions['visibility']
                if any(term in vis for term in ['1SM', '2SM', '3SM']):
                    changes.append(f"{period}: low visibility")
            
            # Check for strong winds
            if conditions.get('wind'):
                wind = conditions['wind']
                if 'gust' in wind.lower() or any(speed in wind for speed in ['25', '30', '35', '40']):
                    changes.append(f"{period}: strong winds")
        
        return changes

# Global parser instance
weather_parser = AviationWeatherParser()

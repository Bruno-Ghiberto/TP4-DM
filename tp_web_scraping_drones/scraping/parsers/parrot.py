"""Parrot drone parser for PDF documents."""
import re
import requests
from typing import Dict, Any, Optional
import PyPDF2
from io import BytesIO
from scraping.utils import (
    normalize_text, extract_number, convert_units,
    parse_dimensions, parse_resolution, parse_boolean_spec,
    fuzzy_match_spec, extract_weight_in_grams, extract_speed_in_mps,
    extract_distance_in_km, extract_altitude_in_meters
)
from scraping.scraper_config import SPEC_MAPPINGS, HEADERS
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class ParrotParser:
    def __init__(self):
        self.brand = "Parrot"
        self.spec_mappings = SPEC_MAPPINGS
        
    def parse(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Parse HTML content (compatibility method for scraper)."""
        # Convert BeautifulSoup object to string for parse_html
        html_content = str(soup)
        return self.parse_html(html_content, url)
        
    def parse_pdf(self, source: str, url: Optional[str] = None) -> Dict[str, Any]:
        """Parse Parrot PDF spec sheet from URL or local file."""
        try:
            # If url is provided, source is a file path
            if url is not None:
                # Read from local file
                with open(source, 'rb') as pdf_file:
                    reader = PyPDF2.PdfReader(pdf_file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                
                # Extract model name from URL
                model = self._extract_model_from_url(url)
                source_url = url
            else:
                # source is a URL, download PDF
                response = requests.get(source, headers=HEADERS, timeout=30)
                response.raise_for_status()
                
                # Extract text from PDF
                pdf_file = BytesIO(response.content)
                reader = PyPDF2.PdfReader(pdf_file)
                
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                
                # Extract model name
                model = self._extract_model_from_url(source)
                source_url = source
            
            # Extract specifications from text
            specs = self._extract_specifications_from_pdf(text)
            
            return {
                "modelo": model,
                "marca": self.brand,
                "url_fuente": source_url,
                "especificaciones_tecnicas": specs
            }
            
        except Exception as e:
            raise Exception(f"Error parsing PDF {source}: {str(e)}")
    
    def _extract_model_from_url(self, url: str) -> str:
        """Extract model name from PDF URL."""
        # Extract filename from URL
        filename = url.split('/')[-1]
        
        # Remove extension and clean up
        model_name = filename.replace('.pdf', '').replace('-product-sheet', '')
        model_name = model_name.replace('-', ' ').replace('_', ' ')
        
        # Capitalize properly
        model_name = ' '.join(word.upper() if word.lower() in ['anafi', 'usa', 'ai'] 
                            else word.capitalize() for word in model_name.split())
        
        return f"Parrot {model_name}" if model_name else "Unknown Parrot Model"
    
    def _extract_specifications_from_pdf(self, text: str) -> Dict[str, Any]:
        """Extract specifications from PDF text."""
        specs = {}
        
        # Direct pattern matching approach for Parrot PDFs
        # The text is structured with bullet points
        
        # Weight extraction - "Weight: 898 g / 1.98 lb" or "Mass: 500 g / 1.10 lb"
        weight_patterns = [
            r'Weight:\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*g',
            r'Mass:\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*g',
            r'Weight:\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*kg',
            r'Mass:\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*kg',
            r'•\s*Weight:\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*g',
            r'•\s*Mass:\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*g'
        ]
        for pattern in weight_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                weight_val = float(match.group(1).replace(',', ''))
                if 'kg' in text[match.start():match.end()].lower():
                    weight_val *= 1000
                if 50 <= weight_val <= 10000:
                    specs['peso_gramos'] = weight_val
                    break
        
        # Dimensions extraction - "Size folded: 304x130x118 mm" or "Size folded: 252 x 104 x 84 mm"
        dim_patterns = [
            r'•\s*Size folded:\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*mm',
            r'Size folded:\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*mm',
            r'•\s*Size folded:\s*(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*mm',
            r'Size folded:\s*(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*mm',
            r'•\s*Size folded:\s*(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)',
            r'Size folded:\s*(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)'
        ]
        for pattern in dim_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                l, w, h = match.groups()
                specs['dimensiones_plegado'] = f"{l}×{w}×{h}"
                break
        
        # Flight time - "Maximum flight time: 32 minutes"
        flight_patterns = [
            r'•\s*Maximum flight time:\s*(\d+(?:\.\d+)?)\s*minutes?',
            r'Maximum flight time:\s*(\d+(?:\.\d+)?)\s*minutes?',
            r'•\s*Battery life:\s*(\d+(?:\.\d+)?)\s*minutes?',
            r'Battery life:\s*(\d+(?:\.\d+)?)\s*minutes?'
        ]
        for pattern in flight_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                time_val = float(match.group(1))
                if 5 <= time_val <= 180:
                    specs['vuelo_minutos'] = time_val
                    break
        
        # Horizontal speed - "Maximum horizontal speed: 17 m/s – 38 mph" or "14.7 m/s"
        horiz_patterns = [
            r'•\s*Maximum horizontal speed:\s*(\d+(?:\.\d+)?)\s*m/s',
            r'Maximum horizontal speed:\s*(\d+(?:\.\d+)?)\s*m/s',
            r'•\s*Horizontal speed:\s*(\d+(?:\.\d+)?)\s*m/s',
            r'Horizontal speed:\s*(\d+(?:\.\d+)?)\s*m/s'
        ]
        for pattern in horiz_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                speed_val = float(match.group(1))
                if 1 <= speed_val <= 50:
                    specs['vel_horizontal_mps'] = speed_val
                    break
        
        # Ascent speed - "Maximum vertical speed: 4 m/s – 9 mph" or "Maximum ascent speed: 4 m/s"
        ascent_patterns = [
            r'•\s*Maximum vertical speed:\s*(\d+(?:\.\d+)?)\s*m/s',
            r'Maximum vertical speed:\s*(\d+(?:\.\d+)?)\s*m/s',
            r'•\s*Maximum ascent speed:\s*(\d+(?:\.\d+)?)\s*m/s',
            r'Maximum ascent speed:\s*(\d+(?:\.\d+)?)\s*m/s',
            r'•\s*(?:Vertical|Ascent) speed:\s*(\d+(?:\.\d+)?)\s*m/s',
            r'(?:Vertical|Ascent) speed:\s*(\d+(?:\.\d+)?)\s*m/s'
        ]
        for pattern in ascent_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                speed_val = float(match.group(1))
                if 0.5 <= speed_val <= 20:
                    specs['vel_ascenso_mps'] = speed_val
                    break
        
        # Wind resistance - "Maximum wind resistance: 14 m/s – 31.3 mph" or "14.7 m/s"
        wind_patterns = [
            r'•\s*Maximum wind resistance:\s*(\d+(?:\.\d+)?)\s*m/s',
            r'Maximum wind resistance:\s*(\d+(?:\.\d+)?)\s*m/s',
            r'•\s*Wind resistance:\s*(\d+(?:\.\d+)?)\s*m/s',
            r'Wind resistance:\s*(\d+(?:\.\d+)?)\s*m/s'
        ]
        for pattern in wind_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                wind_val = float(match.group(1))
                if 2 <= wind_val <= 30:
                    specs['resistencia_viento_mps'] = wind_val
                    break
        
        # Service ceiling/altitude - "Service ceiling: 5,000 m (above sea level)"
        altitude_patterns = [
            r'•\s*Service ceiling:\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*m',
            r'Service ceiling:\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*m',
            r'•\s*Maximum altitude:\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*m',
            r'Maximum altitude:\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*m'
        ]
        for pattern in altitude_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                alt_val = float(match.group(1).replace(',', ''))
                if 100 <= alt_val <= 10000:
                    specs['altitud_despegue_m'] = alt_val
                    break
        
        # Camera sensor - "Sensor: 1/2'' 48 MP CMOS"
        sensor_patterns = [
            r'Sensor:\s*([^•\n]+CMOS[^•\n]*)',
            r'Image sensor:\s*([^•\n]+)',
            r'EO IMAGE CHAIN[^•]*Sensor:\s*([^•\n]+)'
        ]
        for pattern in sensor_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                sensor_text = match.group(1).strip()
                if sensor_text and len(sensor_text) > 5:
                    specs['sensor_camara'] = sensor_text
                    break
        
        # Video resolution - look for resolution specifications
        video_patterns = [
            r'Video resolution:\s*([^•\n]+)',
            r'Resolutions:\s*([^•\n]+(?:\n[^•\n]*)*)',
            r'4K UHD:\s*(\d+x\d+)'
        ]
        for pattern in video_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                video_text = match.group(1).strip()
                if video_text and len(video_text) > 3:
                    specs['resolucion_video'] = video_text
                    break
        
        # Obstacle detection - look for vision systems or gimbal cameras
        obstacle_keywords = [
            'stereoscopic cameras', 'obstacle avoidance', 'vision system',
            'gimbal', 'infrared', 'ultrasonic', 'sonar'
        ]
        specs['deteccion_obstaculos'] = any(keyword in text.lower() for keyword in obstacle_keywords)
        
        # Set default values for missing specs
        if 'peso_gramos' not in specs:
            specs['peso_gramos'] = 0.0
        if 'dimensiones_plegado' not in specs:
            specs['dimensiones_plegado'] = ""
        if 'vuelo_minutos' not in specs:
            specs['vuelo_minutos'] = 0.0
        if 'vel_horizontal_mps' not in specs:
            specs['vel_horizontal_mps'] = 0.0
        if 'vel_ascenso_mps' not in specs:
            specs['vel_ascenso_mps'] = 0.0
        if 'alcance_video_km' not in specs:
            specs['alcance_video_km'] = 0.0
        if 'altitud_despegue_m' not in specs:
            specs['altitud_despegue_m'] = 0.0
        if 'resistencia_viento_mps' not in specs:
            specs['resistencia_viento_mps'] = 0.0
        if 'almacenamiento_interno_gb' not in specs:
            specs['almacenamiento_interno_gb'] = None
        if 'sensor_camara' not in specs:
            specs['sensor_camara'] = ""
        if 'resolucion_video' not in specs:
            specs['resolucion_video'] = ""
        
        return specs
    
    def _parse_pdf_lines(self, lines: list) -> Dict[str, str]:
        """Parse PDF lines to extract specification data."""
        spec_data = {}
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            # Check if this line looks like a specification label
            if self._is_spec_label(line):
                # Look for the value in the next few lines
                for j in range(i + 1, min(i + 4, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and self._is_spec_value(next_line):
                        spec_data[normalize_text(line)] = next_line
                        break
            
            # Also look for patterns like "Label: Value" on the same line
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    label = normalize_text(parts[0])
                    value = parts[1].strip()
                    if label and value:
                        spec_data[label] = value
            
            i += 1
        
        return spec_data
    
    def _is_spec_label(self, text: str) -> bool:
        """Check if text is likely a specification label."""
        normalized = normalize_text(text)
        
        # Common specification label patterns
        label_patterns = [
            'weight', 'mass', 'dimensions', 'size', 'flight time', 'battery',
            'speed', 'velocity', 'range', 'distance', 'altitude', 'ceiling',
            'wind', 'resistance', 'storage', 'memory', 'sensor', 'camera',
            'resolution', 'video', 'obstacle', 'detection', 'avoidance'
        ]
        
        return any(pattern in normalized for pattern in label_patterns)
    
    def _is_spec_value(self, text: str) -> bool:
        """Check if text is likely a specification value."""
        # Check for common units and patterns
        value_patterns = [
            r'\d+\s*(g|kg|lb|oz)',  # Weight units
            r'\d+\s*(mm|cm|m|in|ft)',  # Dimension units
            r'\d+\s*(min|hour|hr)',  # Time units
            r'\d+\s*(mph|km/h|m/s)',  # Speed units
            r'\d+\s*(km|mi|m|ft)',  # Distance units
            r'\d+\s*(gb|mb|tb)',  # Storage units
            r'\d+k',  # Resolution (4K, etc.)
            r'\d+p',  # Resolution (1080p, etc.)
            r'yes|no|available|equipped'  # Boolean values
        ]
        
        return any(re.search(pattern, text.lower()) for pattern in value_patterns)
    
    def _parse_weight(self, data: Dict[str, str]) -> float:
        """Parse weight specification using improved mappings."""
        # Get keywords from new mapping format
        keywords = SPEC_MAPPINGS['parrot']['peso_gramos']['keywords']
        notes = SPEC_MAPPINGS['parrot']['peso_gramos']['notes']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                # Specific patterns for Parrot weight
                # "Weight: 898 g / 1.98 lb"
                patterns = [
                    r'(\d+(?:\.\d+)?)\s*g',
                    r'(\d+(?:\.\d+)?)\s*gram',
                    r'(\d+(?:\.\d+)?)\s*kg',
                    r'(\d+(?:\.\d+)?)\s*kilogram',
                    r'(\d+(?:\.\d+)?)\s*lb'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, value.lower())
                    if match:
                        weight_val = float(match.group(1))
                        # Convert to grams if needed
                        if 'kg' in value.lower() or 'kilogram' in value.lower():
                            weight_val = weight_val * 1000
                        elif 'lb' in value.lower():
                            weight_val = weight_val * 453.592
                        elif 'g' in value.lower() or 'gram' in value.lower():
                            # Already in grams
                            pass
                        
                        if 50 <= weight_val <= 10000:  # Reasonable range for drones
                            logger.debug(f"Peso encontrado: {weight_val}g - {notes}")
                            return weight_val
        
        return 0.0
    
    def _parse_dimensions(self, data: Dict[str, str]) -> str:
        """Parse folded dimensions using improved mappings."""
        # Get keywords from new mapping format
        keywords = SPEC_MAPPINGS['parrot']['dimensiones_plegado']['keywords']
        notes = SPEC_MAPPINGS['parrot']['dimensiones_plegado']['notes']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                # Specific patterns for Parrot dimensions
                # "Size folded: 304x130x118 mm"
                patterns = [
                    r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*mm',
                    r'(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*mm',
                    r'(\d+(?:\.\d+)?)\s*\*\s*(\d+(?:\.\d+)?)\s*\*\s*(\d+(?:\.\d+)?)\s*mm',
                    r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*cm',
                    r'(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*cm'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, value.lower())
                    if match:
                        length, width, height = match.groups()
                        # Convert to mm if needed
                        if 'cm' in value.lower():
                            length = float(length) * 10
                            width = float(width) * 10
                            height = float(height) * 10
                        
                        dimensions = f"{length}x{width}x{height}"
                        logger.debug(f"Dimensiones encontradas: {dimensions} - {notes}")
                        return dimensions
        
        return ""
    
    def _parse_flight_time(self, data: Dict[str, str]) -> float:
        """Parse flight time in minutes."""
        keywords = self.spec_mappings['parrot']['vuelo_minutos']['keywords']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                # Specific patterns for Parrot flight time
                # "Maximum flight time: 32 minutes"
                patterns = [
                    r'(\d+(?:\.\d+)?)\s*minutes?',
                    r'(\d+(?:\.\d+)?)\s*mins?',
                    r'(\d+(?:\.\d+)?)\s*min\b',
                    r'(\d+(?:\.\d+)?)\s*hours?',
                    r'(\d+(?:\.\d+)?)\s*hrs?',
                    r'(\d+(?:\.\d+)?)\s*h\b'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, value.lower())
                    if match:
                        time_val = float(match.group(1))
                        # Convert to minutes if needed
                        if 'hour' in value.lower() or 'hr' in value.lower():
                            time_val = time_val * 60
                        
                        if 5 <= time_val <= 180:  # Reasonable range for drone flight time
                            return time_val
        
        return 0.0
    
    def _parse_horizontal_speed(self, data: Dict[str, str]) -> float:
        """Parse horizontal speed in m/s."""
        keywords = self.spec_mappings['parrot']['vel_horizontal_mps']['keywords']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                # Specific patterns for Parrot horizontal speed
                # "Maximum horizontal speed: 17 m/s – 38 mph"
                patterns = [
                    r'(\d+(?:\.\d+)?)\s*m/s',
                    r'(\d+(?:\.\d+)?)\s*mps',
                    r'(\d+(?:\.\d+)?)\s*km/h',
                    r'(\d+(?:\.\d+)?)\s*kmh',
                    r'(\d+(?:\.\d+)?)\s*mph'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, value.lower())
                    if match:
                        speed_val = float(match.group(1))
                        # Convert to m/s if needed
                        if 'km/h' in value.lower() or 'kmh' in value.lower():
                            speed_val = speed_val / 3.6
                        elif 'mph' in value.lower():
                            speed_val = speed_val * 0.44704
                        
                        if 1 <= speed_val <= 50:  # Reasonable range for drone speeds
                            return speed_val
        
        return 0.0
    
    def _parse_ascent_speed(self, data: Dict[str, str]) -> float:
        """Parse ascent speed in m/s."""
        keywords = self.spec_mappings['parrot']['vel_ascenso_mps']['keywords']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                # Specific patterns for Parrot ascent speed
                # "Maximum vertical speed: 4 m/s – 9 mph"
                patterns = [
                    r'(\d+(?:\.\d+)?)\s*m/s',
                    r'(\d+(?:\.\d+)?)\s*mps',
                    r'(\d+(?:\.\d+)?)\s*km/h',
                    r'(\d+(?:\.\d+)?)\s*kmh',
                    r'(\d+(?:\.\d+)?)\s*mph'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, value.lower())
                    if match:
                        speed_val = float(match.group(1))
                        # Convert to m/s if needed
                        if 'km/h' in value.lower() or 'kmh' in value.lower():
                            speed_val = speed_val / 3.6
                        elif 'mph' in value.lower():
                            speed_val = speed_val * 0.44704
                        
                        if 0.5 <= speed_val <= 20:  # Reasonable range for ascent speeds
                            return speed_val
        
        return 0.0
    
    def _parse_video_range(self, data: Dict[str, str]) -> float:
        """Parse video transmission range in km."""
        keywords = self.spec_mappings['parrot']['alcance_video_km']['keywords']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                distance = extract_distance_in_km(value)
                if distance > 0:
                    return distance
        
        return 0.0
    
    def _parse_altitude(self, data: Dict[str, str]) -> float:
        """Parse max takeoff altitude in meters."""
        keywords = self.spec_mappings['parrot']['altitud_despegue_m']['keywords']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                # Specific patterns for Parrot altitude
                # "Service ceiling: 5,000 m (above sea level)"
                patterns = [
                    r'(\d+(?:,\d+)?(?:\.\d+)?)\s*m\b',
                    r'(\d+(?:,\d+)?(?:\.\d+)?)\s*meters?',
                    r'(\d+(?:,\d+)?(?:\.\d+)?)\s*metres?',
                    r'(\d+(?:,\d+)?(?:\.\d+)?)\s*ft',
                    r'(\d+(?:,\d+)?(?:\.\d+)?)\s*feet'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, value.lower())
                    if match:
                        altitude_val = float(match.group(1).replace(',', ''))
                        # Convert to meters if needed
                        if 'ft' in value.lower() or 'feet' in value.lower():
                            altitude_val = altitude_val * 0.3048
                        
                        if 100 <= altitude_val <= 10000:  # Reasonable range for drone altitude
                            return altitude_val
        
        return 0.0
    
    def _parse_wind_resistance(self, data: Dict[str, str]) -> float:
        """Parse wind resistance in m/s."""
        keywords = self.spec_mappings['parrot']['resistencia_viento_mps']['keywords']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                # Specific patterns for Parrot wind resistance
                # "Maximum wind resistance: 14 m/s – 31.3 mph"
                patterns = [
                    r'(\d+(?:\.\d+)?)\s*m/s',
                    r'(\d+(?:\.\d+)?)\s*mps',
                    r'(\d+(?:\.\d+)?)\s*km/h',
                    r'(\d+(?:\.\d+)?)\s*kmh',
                    r'(\d+(?:\.\d+)?)\s*mph'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, value.lower())
                    if match:
                        speed_val = float(match.group(1))
                        # Convert to m/s if needed
                        if 'km/h' in value.lower() or 'kmh' in value.lower():
                            speed_val = speed_val / 3.6
                        elif 'mph' in value.lower():
                            speed_val = speed_val * 0.44704
                        
                        if 2 <= speed_val <= 30:  # Reasonable range for wind resistance
                            return speed_val
        
        return 0.0
    
    def _parse_storage(self, data: Dict[str, str]) -> Optional[float]:
        """Parse internal storage in GB."""
        keywords = self.spec_mappings['parrot']['almacenamiento_interno_gb']['keywords']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                storage = extract_number(value)
                if storage and storage > 0:
                    # Convert to GB if needed
                    if 'mb' in value.lower():
                        return storage / 1024
                    elif 'tb' in value.lower():
                        return storage * 1024
                    return storage
        
        return None
    
    def _parse_camera_sensor(self, data: Dict[str, str]) -> str:
        """Parse camera sensor type."""
        keywords = self.spec_mappings['parrot']['sensor_camara']['keywords']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                # Clean up sensor description
                sensor = value.strip()
                if sensor and len(sensor) > 2:
                    return sensor
        
        return ""
    
    def _parse_video_resolution(self, data: Dict[str, str]) -> str:
        """Parse video resolution."""
        keywords = self.spec_mappings['parrot']['resolucion_video']['keywords']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                resolution = parse_resolution(value)
                if resolution:
                    return resolution
        
        return ""
    
    def _parse_obstacle_detection(self, data: Dict[str, str]) -> bool:
        """Parse obstacle detection capability."""
        keywords = self.spec_mappings['parrot']['deteccion_obstaculos']['keywords']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                return parse_boolean_spec(value)
        
        return False

    def parse_product_page(self, url: str) -> Dict[str, Any]:
        """Parse product page from URL."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return self.parse_html(response.text, url)
        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            return {
                "modelo": "Unknown Parrot Model",
                "marca": self.brand,
                "url_fuente": url,
                "especificaciones_tecnicas": {}
            }
    
    def extract_technical_specs(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract technical specifications from BeautifulSoup object."""
        return self._extract_specifications(soup)
    
    def parse_html(self, html: str, url: str) -> Dict[str, Any]:
        """Parse Parrot specs page."""
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract model name
        model = self._extract_model(soup, url)
        
        # Extract specifications
        specs = self._extract_specifications(soup)
        
        return {
            "modelo": model,
            "marca": self.brand,
            "url_fuente": url,
            "especificaciones_tecnicas": specs
        }
    
    def _extract_model(self, soup: BeautifulSoup, url: str) -> str:
        """Extract model name from page."""
        # Try various selectors for Parrot product names
        selectors = [
            'h1.product-title',
            'h1[class*="title"]',
            '.hero-title h1',
            '.product-hero h1',
            'h1',
            '.product-name'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text().strip()
                if title and len(title) > 3:
                    return title
        
        # Fallback: extract from URL
        url_parts = url.split('/')
        for part in url_parts:
            if part and 'drones' not in part and not part.startswith('www'):
                clean_part = part.replace('-', ' ').replace('_', ' ')
                if clean_part.strip():
                    return clean_part.strip().title()
        
        return "Unknown Parrot Model"
    
    def _extract_specifications(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract all specifications from Parrot page."""
        specs = {
            'peso_gramos': 0.0,
            'dimensiones_plegado': "",
            'vuelo_minutos': 0.0,
            'vel_horizontal_mps': 0.0,
            'vel_ascenso_mps': 0.0,
            'alcance_video_km': 0.0,
            'altitud_despegue_m': 0.0,
            'resistencia_viento_mps': 0.0,
            'almacenamiento_interno_gb': None,
            'sensor_camara': "",
            'resolucion_video': "",
            'deteccion_obstaculos': False
        }
        
        # Basic extraction - can be enhanced
        spec_elements = soup.select('.tech-specs .spec, .specifications .spec')
        for element in spec_elements:
            spans = element.find_all('span')
            if len(spans) >= 2:
                key = spans[0].get_text().lower().strip()
                value = spans[1].get_text().strip()
                
                if 'weight' in key or 'peso' in key:
                    if 'g' in value:
                        specs['peso_gramos'] = float(re.findall(r'\d+', value)[0]) if re.findall(r'\d+', value) else 0.0
                elif 'flight' in key or 'vuelo' in key:
                    if 'min' in value:
                        specs['vuelo_minutos'] = float(re.findall(r'\d+', value)[0]) if re.findall(r'\d+', value) else 0.0
        
        return specs

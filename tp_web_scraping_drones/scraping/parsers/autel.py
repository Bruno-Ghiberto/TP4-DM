"""Autel Robotics drone parser."""
from bs4 import BeautifulSoup, Tag
from typing import Dict, Any, Optional, Union
import re
import json
import requests
import logging
from scraping.utils import (
    normalize_text, extract_number, convert_units,
    parse_dimensions, parse_resolution, parse_boolean_spec,
    fuzzy_match_spec, extract_weight_in_grams, extract_speed_in_mps,
    extract_distance_in_km, extract_altitude_in_meters
)
from scraping.scraper_config import SPEC_MAPPINGS

logger = logging.getLogger(__name__)

class AutelParser:
    def __init__(self):
        self.brand = "Autel"
        self.spec_mappings = SPEC_MAPPINGS
        
    def parse(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Parse HTML content (compatibility method for scraper)."""
        # Convertir objeto BeautifulSoup a string para parse_html
        html_content = str(soup)
        return self.parse_html(html_content, url)
        
    def parse_product_page(self, url: str) -> Dict[str, Any]:
        """Parse product page from URL."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return self.parse_html(response.text, url)
        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            return {
                "modelo": "Unknown Autel Model",
                "marca": self.brand,
                "url_fuente": url,
                "especificaciones_tecnicas": {}
            }
    
    def extract_technical_specs(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract technical specifications from BeautifulSoup object."""
        return self._extract_specifications(soup)
    
    def parse_html(self, html: str, url: str) -> Dict[str, Any]:
        """Parse Autel specs page."""
        soup = BeautifulSoup(html, 'lxml')
        
        # Extraer nombre del modelo
        model = self._extract_model(soup, url)
        
        # Extraer especificaciones
        specs = self._extract_specifications(soup)
        
        return {
            "modelo": model,
            "marca": self.brand,
            "url_fuente": url,
            "especificaciones_tecnicas": specs
        }
    
    def _extract_model(self, soup: BeautifulSoup, url: str) -> str:
        """Extract model name from page."""
        # Intentar varios selectores para nombres de productos Autel
        selectors = [
            'h1.product-title',
            'h1[class*="title"]',
            '.hero-title h1',
            '.product-hero h1',
            'h1',
            '.product-name',
            '[data-testid="product-title"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text().strip()
                # Limpiar el título
                title = re.sub(r'\s+', ' ', title)
                # Eliminar prefijos/sufijos comunes de Autel
                title = re.sub(r'^(Autel\s+)?', '', title, flags=re.IGNORECASE)
                title = re.sub(r'\s*(-\s*Specifications?|Specs?)$', '', title, flags=re.IGNORECASE)
                if title and len(title) > 3 and not any(skip in title.lower() for skip in ['http', 'www', 'autelrobotics']):
                    return title
        
        # Alternativa: extraer de la URL - ser más cuidadoso
        if url:
            # Parsear URL para obtener el path
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.split('/')
            
            for part in path_parts:
                if part and len(part) > 3:
                    # Omitir partes comunes de URL
                    if any(skip in part.lower() for skip in [
                        'productdetail', 'product', 'detail', 'specs', 'specification',
                        'www', 'autelrobotics', 'com', 'http', 'https'
                    ]):
                        continue
                    
                    # Limpiar parte de URL
                    clean_part = part.replace('-', ' ').replace('_', ' ')
                    clean_part = re.sub(r'#.*$', '', clean_part)  # Eliminar fragmentos
                    clean_part = re.sub(r'\s+', ' ', clean_part)
                    
                    if clean_part.strip() and len(clean_part.strip()) > 3:
                        return clean_part.strip().title()
        
        return "Unknown Autel Model"
    
    def _extract_specifications(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract all specifications from Autel page."""
        specs = {}
        
        # Obtener todos los datos de especificaciones de varias secciones
        spec_data = self._get_spec_data(soup)
        
        # Parsear cada especificación usando los mapeos
        specs['peso_gramos'] = self._parse_weight(spec_data)
        specs['dimensiones_plegado'] = self._parse_dimensions(spec_data)
        specs['vuelo_minutos'] = self._parse_flight_time(spec_data)
        specs['vel_horizontal_mps'] = self._parse_horizontal_speed(spec_data)
        specs['vel_ascenso_mps'] = self._parse_ascent_speed(spec_data)
        specs['alcance_video_km'] = self._parse_video_range(spec_data)
        specs['altitud_despegue_m'] = self._parse_altitude(spec_data)
        specs['resistencia_viento_mps'] = self._parse_wind_resistance(spec_data)
        specs['almacenamiento_interno_gb'] = self._parse_storage(spec_data)
        specs['sensor_camara'] = self._parse_camera_sensor(spec_data)
        specs['resolucion_video'] = self._parse_video_resolution(spec_data)
        specs['deteccion_obstaculos'] = self._parse_obstacle_detection(spec_data)
        
        return specs
    
    def _get_spec_data(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract raw specification data from page."""
        spec_data = {}
        
        # Intentar diferentes selectores de sección específicos de Autel
        section_selectors = [
            # Tablas principales
            '.spec-table tr',
            '.specifications tr',
            '.tech-specs tr',
            '.parameter-table tr',
            '.product-specs tr',
            'table tr',
            # Sección #jsgg específica de Autel
            '#jsgg table tr',
            '#jsgg .spec-row',
            '#jsgg .parameter-row',
            # Listas de especificaciones
            '.spec-list li',
            '.params-list li',
            '[class*="spec"] tr',
            '[class*="parameter"] tr',
            # Divs con especificaciones
            '.spec-item',
            '.param-item',
            '[data-spec]',
            '[data-parameter]'
        ]
        
        for selector in section_selectors:
            try:
                rows = soup.select(selector)
                for row in rows:
                    # Extraer etiqueta y valor
                    cells = row.find_all(['td', 'th', 'span', 'div'])
                    if len(cells) >= 2:
                        label = normalize_text(cells[0].get_text())
                        value = normalize_text(cells[1].get_text())
                        if label and value and len(label) > 2 and value != '-':
                            spec_data[label] = value
                    elif len(cells) == 1:
                        # Una celda podría contener "Etiqueta: Valor"
                        text = cells[0].get_text()
                        if ':' in text:
                            parts = text.split(':', 1)
                            if len(parts) == 2:
                                label = normalize_text(parts[0])
                                value = normalize_text(parts[1])
                                if label and value and len(label) > 2:
                                    spec_data[label] = value
            except Exception as e:
                logger.debug(f"Error with Autel selector {selector}: {e}")
                continue
        
        # También intentar listas de definición
        dls = soup.find_all('dl')
        for dl in dls:
            if isinstance(dl, Tag):
                dts = dl.find_all('dt')
                dds = dl.find_all('dd')
                for dt, dd in zip(dts, dds):
                    label = normalize_text(dt.get_text())
                    value = normalize_text(dd.get_text())
                    if label and value and len(label) > 2:
                        spec_data[label] = value
        
        # Intentar extraer de datos JSON
        json_data = self._extract_json_specs(soup)
        if json_data:
            flattened = self._flatten_json_specs(json_data)
            spec_data.update(flattened)
        
        # Intentar extracción específica de #jsgg
        jsgg_section = self._extract_specs_from_jsgg_section(soup)
        spec_data.update(jsgg_section)
        
        # Estrategia adicional: buscar texto con patrones específicos
        if len(spec_data) < 5:
            logger.debug("Autel: Pocas specs encontradas, usando extracción de patrones de texto")
            self._extract_from_text_patterns(soup, spec_data)
        
        if len(spec_data) > 0:
            logger.info(f"Autel specs encontradas: {len(spec_data)}")
            logger.debug(f"Primeras 5 specs de Autel: {list(spec_data.items())[:5]}")
        else:
            logger.warning("No se encontraron especificaciones en la página Autel")
        
        return spec_data
    
    def _extract_json_specs(self, soup: BeautifulSoup) -> Dict:
        """Extract specifications from JSON scripts."""
        scripts = soup.find_all('script', type='application/json')
        for script in scripts:
            if isinstance(script, Tag) and script.string:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        return data
                except (json.JSONDecodeError, AttributeError):
                    continue
        return {}
    
    def _extract_specs_from_jsgg_section(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extraer specs de la sección #jsgg específica de Autel."""
        spec_data = {}
        
        # Buscar sección #jsgg - múltiples estrategias
        jsgg_section = soup.find(id='jsgg')
        if not jsgg_section:
            # Buscar por clase alternativa
            jsgg_section = soup.select_one('[class*="specification"], [class*="tech-spec"], [class*="parameters"]')
        
        if not jsgg_section:
            # Buscar por contenido que contenga especificaciones típicas
            for section in soup.find_all(['div', 'section', 'article']):
                if section.get_text() and any(keyword in section.get_text().lower() for keyword in 
                    ['weight', 'flight time', 'max speed', 'dimensions', 'camera', 'battery']):
                    jsgg_section = section
                    break
        
        if jsgg_section and isinstance(jsgg_section, Tag):
            # Estrategia 1: Buscar tablas de especificaciones
            tables = jsgg_section.find_all('table')
            for table in tables:
                if isinstance(table, Tag):
                    rows = table.find_all('tr')
                    for row in rows:
                        if isinstance(row, Tag):
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 2:
                                label = normalize_text(cells[0].get_text())
                                value = normalize_text(cells[1].get_text())
                                if label and value and len(label) > 2 and value not in ['-', 'N/A']:
                                    spec_data[label] = value
            
            # Estrategia 2: Buscar listas de definiciones
            for dl in jsgg_section.find_all('dl'):
                if isinstance(dl, Tag):
                    dts = dl.find_all('dt')
                    dds = dl.find_all('dd')
                    for dt, dd in zip(dts, dds):
                        label = normalize_text(dt.get_text())
                        value = normalize_text(dd.get_text())
                        if label and value and len(label) > 2:
                            spec_data[label] = value
            
            # Estrategia 3: Buscar divs con clases específicas
            spec_divs = jsgg_section.find_all('div', class_=re.compile(r'(spec|param|detail|info)'))
            for div in spec_divs:
                text = div.get_text()
                # Buscar patrones clave:valor
                patterns = [
                    r'([^:]+?):\s*([^:]+?)(?=\s*[A-Z][a-z]+:|$)',  # Formato "Clave: Valor"
                    r'([^\n]+?)\s*:\s*([^\n]+)',  # Formato con salto de línea
                    r'([^\t]+?)\t+([^\t]+)',  # Separado por tabs
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.MULTILINE)
                    for match in matches:
                        label = normalize_text(match[0])
                        value = normalize_text(match[1])
                        if label and value and len(label) > 2 and len(value) > 1:
                            spec_data[label] = value
            
            # Estrategia 4: Buscar patrones específicos en texto completo
            full_text = jsgg_section.get_text()
            specific_patterns = [
                # Patrones específicos de Autel
                (r'(?:Weight|Peso|Takeoff Weight):\s*([^\n\r]+)', 'Weight'),
                (r'(?:Flight Time|Tiempo de vuelo|Endurance):\s*([^\n\r]+)', 'Flight Time'),
                (r'(?:Max Speed|Velocidad máxima|Maximum Flight Speed):\s*([^\n\r]+)', 'Max Speed'),
                (r'(?:Video Resolution|Resolución de video):\s*([^\n\r]+)', 'Video Resolution'),
                (r'(?:Dimensions|Dimensiones|Folded Size):\s*([^\n\r]+)', 'Dimensions'),
                (r'(?:Camera|Cámara|Sensor):\s*([^\n\r]+)', 'Camera'),
                (r'(?:Transmission Range|Control Distance|Video Range):\s*([^\n\r]+)', 'Range'),
                (r'(?:Wind Resistance|Resistencia al viento):\s*([^\n\r]+)', 'Wind Resistance'),
                (r'(?:Storage|Almacenamiento|Internal Storage):\s*([^\n\r]+)', 'Storage'),
                (r'(?:Ascent Speed|Velocidad de ascenso):\s*([^\n\r]+)', 'Ascent Speed'),
                (r'(?:Service Ceiling|Altitud máxima|Maximum Altitude):\s*([^\n\r]+)', 'Altitude'),
                (r'(?:Battery|Batería|Battery Life):\s*([^\n\r]+)', 'Battery'),
                (r'(?:Gimbal|Estabilizador):\s*([^\n\r]+)', 'Gimbal'),
                (r'(?:GPS|GNSS|Navigation):\s*([^\n\r]+)', 'GPS'),
                (r'(?:Obstacle|Obstáculo|Avoidance):\s*([^\n\r]+)', 'Obstacle Avoidance'),
            ]
            
            for pattern, spec_name in specific_patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                if matches:
                    spec_data[spec_name] = matches[0].strip()
                    logger.debug(f"Found Autel spec via pattern: {spec_name} = {matches[0].strip()}")
        
        # Si no encontramos especificaciones, usar extracción de texto más agresiva
        if len(spec_data) < 3:
            logger.warning("Pocos specs encontrados en #jsgg, usando extracción agresiva")
            self._extract_from_text_patterns(soup, spec_data)
        
        return spec_data
    
    def _flatten_json_specs(self, data: Union[Dict, list], prefix: str = '') -> Dict[str, str]:
        """Flatten nested JSON specifications."""
        result = {}
        
        if isinstance(data, dict):
            for key, value in data.items():
                new_key = f"{prefix}_{key}" if prefix else key
                new_key = normalize_text(new_key)
                
                if isinstance(value, (dict, list)):
                    result.update(self._flatten_json_specs(value, new_key))
                else:
                    result[new_key] = str(value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_key = f"{prefix}_{i}" if prefix else str(i)
                result.update(self._flatten_json_specs(item, new_key))
        
        return result
    
    def _parse_weight(self, data: Dict[str, str]) -> float:
        """Parse weight specification using improved mappings."""
        from scraping.scraper_config import SPEC_MAPPINGS
        
        # Obtener palabras clave del nuevo formato de mapeo
        keywords = SPEC_MAPPINGS['autel']['peso_gramos']['keywords']
        notes = SPEC_MAPPINGS['autel']['peso_gramos']['notes']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                # Patrones específicos para peso de Autel
                # "Weight 866 g" o "Autel Alpha Empty Weight 5535 g"
                # Primero intentar encontrar el valor principal de peso en la cadena de valor
                patterns = [
                    r'Weight\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*g\b',
                    r'weight\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*g\b',
                    r'(\d+(?:,\d+)?(?:\.\d+)?)\s*g\b',
                    r'(\d+(?:,\d+)?(?:\.\d+)?)\s*kg\b'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, value, re.IGNORECASE)
                    if match:
                        weight_val = float(match.group(1).replace(',', ''))
                        # Convertir a gramos si es necesario
                        if 'kg' in value.lower():
                            weight_val = weight_val * 1000
                        
                        if 50 <= weight_val <= 15000:  # Rango extendido para drones más grandes
                            logger.debug(f"Peso encontrado: {weight_val}g - {notes}")
                            return weight_val
                
                # Alternativa al método original si los patrones no coincidieron
                weight = extract_weight_in_grams(value)
                if weight > 0:
                    logger.debug(f"Peso encontrado: {weight}g - {notes}")
                    return weight
        
        return 0.0
    
    def _parse_dimensions(self, data: Dict[str, str]) -> str:
        """Parse folded dimensions using improved mappings."""
        from scraping.scraper_config import SPEC_MAPPINGS
        
        # Obtener palabras clave del nuevo formato de mapeo
        keywords = SPEC_MAPPINGS['autel']['dimensiones_plegado']['keywords']
        notes = SPEC_MAPPINGS['autel']['dimensiones_plegado']['notes']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                # Omitir dimensiones del controlador/pantalla - priorizar dimensiones del drone
                if 'display' in value.lower() or 'controller' in value.lower() or 'inches' in value.lower():
                    continue
                
                # Patrones específicos para dimensiones de drones Autel
                # "Folded: 245×130×111mm" o "Dimensions 210×123×95mm (folded)"
                patterns = [
                    r'Folded:\s*(\d+(?:\.\d+)?)\s*[×x]\s*(\d+(?:\.\d+)?)\s*[×x]\s*(\d+(?:\.\d+)?)\s*mm',
                    r'folded[^0-9]*(\d+(?:\.\d+)?)\s*[×x]\s*(\d+(?:\.\d+)?)\s*[×x]\s*(\d+(?:\.\d+)?)\s*mm',
                    r'(\d+(?:\.\d+)?)\s*[×x]\s*(\d+(?:\.\d+)?)\s*[×x]\s*(\d+(?:\.\d+)?)\s*mm.*folded',
                    r'(\d+(?:\.\d+)?)\s*[×x]\s*(\d+(?:\.\d+)?)\s*[×x]\s*(\d+(?:\.\d+)?)\s*mm',
                    r'(\d+(?:\.\d+)?)\s*[×x]\s*(\d+(?:\.\d+)?)\s*[×x]\s*(\d+(?:\.\d+)?)',
                    r'(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, value, re.IGNORECASE)
                    if match:
                        l, w, h = match.groups()
                        return f"{l}×{w}×{h}"
                
                # Alternativa al método original si los patrones no coincidieron
                return parse_dimensions(value)
        
        return ""
    
    def _parse_flight_time(self, data: Dict[str, str]) -> float:
        """Parse flight time in minutes."""
        keywords = self.spec_mappings['autel']['vuelo_minutos']['keywords']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                # Patrones específicos para tiempo de vuelo de Autel
                # "Maximum Flight Time (Windless, Speed: 10.5 m/s) 40 minutes"
                # "Maximum Flight Time 40 minutes"
                patterns = [
                    r'(\d+)\s*minutes?',
                    r'(\d+)\s*mins?',
                    r'(\d+)\s*min',
                    r'(\d+)\s*hours?',
                    r'(\d+)\s*hrs?',
                    r'(\d+)\s*h'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, value.lower())
                    if match:
                        time_val = float(match.group(1))
                        # Convertir a minutos si es necesario
                        if 'hour' in value.lower() or 'hr' in value.lower():
                            return time_val * 60
                        return time_val
        
        return 0.0
    
    def _parse_horizontal_speed(self, data: Dict[str, str]) -> float:
        """Parse horizontal speed in m/s."""
        keywords = self.spec_mappings['autel']['vel_horizontal_mps']['keywords']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                # Patrones específicos para velocidad horizontal de Autel
                # "Ludicrous: 25 m/s" o "Standard: 15 m/s"
                speeds = []
                
                # Encontrar todos los valores de velocidad en el texto
                patterns = [
                    r'(\d+(?:\.\d+)?)\s*m/s',
                    r'(\d+(?:\.\d+)?)\s*mps',
                    r'(\d+(?:\.\d+)?)\s*km/h',
                    r'(\d+(?:\.\d+)?)\s*kmh',
                    r'(\d+(?:\.\d+)?)\s*mph'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, value.lower())
                    for match in matches:
                        speed_val = float(match)
                        # Convertir a m/s si es necesario
                        if 'km/h' in value.lower() or 'kmh' in value.lower():
                            speed_val = speed_val / 3.6
                        elif 'mph' in value.lower():
                            speed_val = speed_val * 0.44704
                        speeds.append(speed_val)
                
                if speeds:
                    # Devolver la velocidad máxima (usualmente modo Ludicrous)
                    return max(speeds)
        
        return 0.0
    
    def _parse_ascent_speed(self, data: Dict[str, str]) -> float:
        """Parse ascent speed in m/s."""
        keywords = self.spec_mappings['autel']['vel_ascenso_mps']['keywords']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                # Specific patterns for Autel ascent speed
                # "Ludicrous: 15 m/s" or "Standard: 6 m/s"
                speeds = []
                
                # Find all speed values in the text
                patterns = [
                    r'(\d+(?:\.\d+)?)\s*m/s',
                    r'(\d+(?:\.\d+)?)\s*mps',
                    r'(\d+(?:\.\d+)?)\s*km/h',
                    r'(\d+(?:\.\d+)?)\s*kmh',
                    r'(\d+(?:\.\d+)?)\s*mph'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, value.lower())
                    for match in matches:
                        speed_val = float(match)
                        # Convert to m/s if needed
                        if 'km/h' in value.lower() or 'kmh' in value.lower():
                            speed_val = speed_val / 3.6
                        elif 'mph' in value.lower():
                            speed_val = speed_val * 0.44704
                        speeds.append(speed_val)
                
                if speeds:
                    # Return the maximum speed (usually Ludicrous mode)
                    return max(speeds)
        
        return 0.0
    
    def _parse_video_range(self, data: Dict[str, str]) -> float:
        """Parse video transmission range in km."""
        keywords = self.spec_mappings['autel']['alcance_video_km']['keywords']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                distance = extract_distance_in_km(value)
                if distance > 0:
                    return distance
        
        return 0.0
    
    def _parse_altitude(self, data: Dict[str, str]) -> float:
        """Parse max takeoff altitude in meters."""
        keywords = self.spec_mappings['autel']['altitud_despegue_m']['keywords']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                altitude = extract_altitude_in_meters(value)
                if altitude > 0:
                    return altitude
        
        return 0.0
    
    def _parse_wind_resistance(self, data: Dict[str, str]) -> float:
        """Parse wind resistance in m/s."""
        keywords = self.spec_mappings['autel']['resistencia_viento_mps']['keywords']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                # Specific patterns for Autel wind resistance
                # "Maximum Wind Speed Resistance 10.7m/s" or "12 m/s"
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
                        wind_val = float(match.group(1))
                        # Convert to m/s if needed
                        if 'km/h' in value.lower() or 'kmh' in value.lower():
                            wind_val = wind_val / 3.6
                        elif 'mph' in value.lower():
                            wind_val = wind_val * 0.44704
                        
                        if 0.5 <= wind_val <= 50:  # Reasonable range
                            return wind_val
                
                # Fallback to original method if patterns didn't match
                wind_speed = extract_speed_in_mps(value)
                if wind_speed > 0:
                    return wind_speed
        
        return 0.0
    
    def _parse_storage(self, data: Dict[str, str]) -> Optional[float]:
        """Parse internal storage in GB."""
        keywords = self.spec_mappings['autel']['almacenamiento_interno_gb']['keywords']
        
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
        keywords = self.spec_mappings['autel']['sensor_camara']['keywords']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                # Clean up sensor description
                sensor = value.strip()
                if sensor and len(sensor) > 2:
                    return sensor
        
        return ""
    
    def _parse_video_resolution(self, data: Dict[str, str]) -> str:
        """Parse video resolution."""
        keywords = self.spec_mappings['autel']['resolucion_video']['keywords']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                resolution = parse_resolution(value)
                if resolution:
                    return resolution
        
        return ""
    
    def _parse_obstacle_detection(self, data: Dict[str, str]) -> bool:
        """Parse obstacle detection capability."""
        keywords = self.spec_mappings['autel']['deteccion_obstaculos']['keywords']
        
        for label, value in data.items():
            if any(fuzzy_match_spec(label, [kw]) for kw in keywords):
                return parse_boolean_spec(value)
        
        return False

    def parse_pdf(self, source: str, url: Optional[str] = None) -> Dict[str, Any]:
        """Parse Autel PDF spec sheet from URL or local file."""
        try:
            # If url is provided, source is a file path
            if url is not None:
                # Read from local file
                specs = self.parse_pdf_specs(source)
                
                # Extract model name from URL
                model = self._extract_model_from_url(url)
                source_url = url
            else:
                # source is a URL - not supported for Autel, return empty
                specs = {}
                model = "Unknown Autel Model"
                source_url = source
            
            return {
                "modelo": model,
                "marca": self.brand,
                "url_fuente": source_url,
                "especificaciones_tecnicas": specs
            }
            
        except Exception as e:
            logger.error(f"Error parsing PDF {source}: {str(e)}")
            return {
                "modelo": "Unknown Autel Model",
                "marca": self.brand,
                "url_fuente": url or source,
                "especificaciones_tecnicas": {}
            }
    
    def _extract_model_from_url(self, url: str) -> str:
        """Extract model name from PDF URL."""
        # Extract filename from URL
        filename = url.split('/')[-1]
        
        # Remove extension and clean up
        model_name = filename.replace('.pdf', '').replace('-product-sheet', '')
        model_name = model_name.replace('-', ' ').replace('_', ' ')
        
        # Capitalize properly
        model_name = ' '.join(word.capitalize() for word in model_name.split())
        
        return f"Autel {model_name}" if model_name else "Unknown Autel Model"

    def parse_pdf_specs(self, pdf_path: str) -> Dict[str, Any]:
        """Parse specifications from PDF file."""
        try:
            import pdfplumber
            specs = {}
            
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        # Basic parsing of common spec patterns
                        if 'flight time' in text.lower():
                            match = re.search(r'flight time:?\s*(\d+)\s*min', text.lower())
                            if match:
                                specs['vuelo_minutos'] = float(match.group(1))
                        
                        if 'weight' in text.lower():
                            match = re.search(r'weight:?\s*(\d+)\s*g', text.lower())
                            if match:
                                specs['peso_gramos'] = float(match.group(1))
                        
                        if 'max speed' in text.lower():
                            match = re.search(r'max speed:?\s*(\d+)\s*km', text.lower())
                            if match:
                                specs['vel_horizontal_mps'] = float(match.group(1)) * 0.277778  # km/h to m/s
            
            return specs
        except Exception as e:
            logger.error(f"Error parsing PDF {pdf_path}: {e}")
            return {}

    def _extract_from_text_patterns(self, soup: BeautifulSoup, spec_data: Dict[str, str]):
        """Extraer especificaciones usando patrones de texto específicos para Autel."""
        # Buscar texto que contenga especificaciones típicas
        all_text = soup.get_text()
        
        # Patrones específicos para Autel
        patterns = [
            (r'(?:Weight|Peso|Takeoff Weight):\s*([^\n]+)', 'weight'),
            (r'(?:Flight Time|Tiempo de vuelo|Endurance):\s*([^\n]+)', 'flight_time'),
            (r'(?:Max Speed|Velocidad máxima|Maximum Flight Speed):\s*([^\n]+)', 'max_speed'),
            (r'(?:Video Resolution|Resolución de video):\s*([^\n]+)', 'video_resolution'),
            (r'(?:Dimensions|Dimensiones|Folded Size):\s*([^\n]+)', 'dimensions'),
            (r'(?:Camera|Cámara|Sensor):\s*([^\n]+)', 'camera'),
            (r'(?:Transmission Range|Control Distance|Video Range):\s*([^\n]+)', 'range'),
            (r'(?:Wind Resistance|Resistencia al viento):\s*([^\n]+)', 'wind_resistance'),
            (r'(?:Storage|Almacenamiento|Internal Storage):\s*([^\n]+)', 'storage'),
            (r'(?:Ascent Speed|Velocidad de ascenso):\s*([^\n]+)', 'ascent_speed'),
            (r'(?:Service Ceiling|Altitud máxima|Maximum Altitude):\s*([^\n]+)', 'altitude'),
        ]
        
        for pattern, spec_type in patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            if matches:
                spec_data[spec_type] = matches[0].strip()
                logger.debug(f"Found Autel spec via pattern: {spec_type} = {matches[0].strip()}")

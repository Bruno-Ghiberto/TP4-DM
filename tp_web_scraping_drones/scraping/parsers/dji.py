"""DJI parser con extracción basada en regex directo."""
import logging
import re
from typing import Dict, Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class DJIParser:
    """Parser específico para páginas de DJI."""
    
    def __init__(self):
        self.brand = "DJI"
        # Patrones regex basados en el texto real observado
        self.patterns = {
            'peso_gramos': [
                r'Takeoff Weight[^0-9]*?(\d+)\s*g',
                r'Weight[^0-9]*?(\d+)\s*g',
                r'Peso[^0-9]*?(\d+)\s*g',
                r'Mavic.*?(\d+)\s*g',
                r':\s*(\d+)\s*g'
            ],
            'dimensiones_plegado': [
                r'Folded[^0-9]*?([\d.]+×[\d.]+×[\d.]+)\s*mm',
                r'Plegado[^0-9]*?([\d.]+×[\d.]+×[\d.]+)\s*mm',
                r'Folded[^0-9]*?([\d.]+\s*×\s*[\d.]+\s*×\s*[\d.]+)\s*mm',
                r'Dimensions\s*([\d.]+×[\d.]+×[\d.]+)\s*mm',
                r'Travel Mode Dimensions[^:]*?Height:\s*([\d.]+)\s*mm[^,]*,\s*Width:\s*([\d.]+)\s*mm[^,]*,\s*Length:\s*([\d.]+)\s*mm'
            ],
            'vuelo_minutos': [
                r'Max Flight Time\s*(\d+)\s*minute',
                r'Flight Time[^0-9]*?(\d+)\s*minute',
                r'Tiempo de vuelo[^0-9]*?(\d+)\s*minuto'
            ],
            'vel_horizontal_mps': [
                r'Max Horizontal Speed[^0-9]*?(\d+)\s*m/s',
                r'Velocidad horizontal[^0-9]*?(\d+)\s*m/s',
                r'Horizontal Speed[^0-9]*?(\d+)\s*m/s'
            ],
            'vel_ascenso_mps': [
                r'Max Ascent Speed\s*(\d+)\s*m/s',
                r'Ascent Speed[^0-9]*?(\d+)\s*m/s',
                r'Velocidad de ascenso[^0-9]*?(\d+)\s*m/s'
            ],
            'alcance_video_km': [
                r'Max Transmission Distance[^0-9]*?(\d+)\s*km',
                r'Transmission Distance[^0-9]*?(\d+)\s*km',
                r'FCC:\s*(\d+)\s*km'
            ],
            'altitud_despegue_m': [
                r'Max Takeoff Altitude\s*(\d+)\s*m',
                r'Takeoff Altitude[^0-9]*?(\d+)\s*m',
                r'Altitud[^0-9]*?(\d+)\s*m'
            ],
            'resistencia_viento_mps': [
                r'Max Wind Speed Resistance\s*(\d+)\s*m/s',
                r'Wind Speed Resistance[^0-9]*?(\d+)\s*m/s',
                r'Resistencia al viento[^0-9]*?(\d+)\s*m/s'
            ],
            'almacenamiento_interno_gb': [
                r'Internal Storage[^0-9]*?(\d+)\s*GB',
                r'Internal Storage\s*(\d+)\s*GB',
                r'Storage[^0-9]*?(\d+)\s*GB',
                r'Almacenamiento[^0-9]*?(\d+)\s*GB'
            ],
            'sensor_camara': [
                r'Image Sensor[^:]*?([^.]+(?:CMOS|CCD)[^.]*)',
                r'Sensor[^:]*?([^.]+(?:CMOS|CCD)[^.]*)',
                r'Camera[^:]*?([^.]+(?:CMOS|CCD)[^.]*)'
            ],
            'resolucion_video': [
                r'Video Resolution[^:]*?([^.]+(?:4K|5K|1080p)[^.]*)',
                r'Resolution[^:]*?([^.]+(?:4K|5K|1080p)[^.]*)',
                r'(\d+K)[^0-9]*?(\d+×\d+)'
            ],
            'deteccion_obstaculos': [
                r'Sensing Type[^:]*?([^.]+vision[^.]*)',
                r'Obstacle[^:]*?([^.]+vision[^.]*)',
                r'Detection[^:]*?([^.]+vision[^.]*)'
            ]
        }
    
    def parse(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """
        Extrae especificaciones de drones DJI.
        
        Args:
            soup: Objeto BeautifulSoup con el HTML de la página
            url: URL de la página
            
        Returns:
            Diccionario con las especificaciones extraídas
        """
        logger.info(f"Iniciando extracción de especificaciones DJI desde: {url}")
        
        # Obtener todo el texto de la página
        page_text = soup.get_text()
        
        # Verificar que la página tiene contenido
        if not page_text or len(page_text.strip()) < 1000:
            logger.warning(f"Página DJI con poco contenido: {len(page_text)} chars")
            return {}
        
        # Extraer nombre del modelo de la URL
        model_name = self._extract_model_name(url)
        
        # Extraer especificaciones usando patrones regex
        specifications = {}
        specifications.update(self._extract_specifications(page_text))
        
        # Validar y limpiar datos
        cleaned_specs = self._validate_and_clean(specifications)
        
        # Crear resultado completo con modelo y marca
        if cleaned_specs:
            result = {
                'modelo': model_name,
                'marca': self.brand,
                'especificaciones_tecnicas': cleaned_specs
            }
            logger.info(f"Especificaciones DJI extraídas para {model_name}: {list(cleaned_specs.keys())}")
            return result
        else:
            logger.warning(f"No se pudieron extraer especificaciones DJI de {url}")
            return {}
    
    def _extract_model_name(self, url: str) -> str:
        """Extrae el nombre del modelo de la URL."""
        # Patrones comunes en URLs de DJI
        patterns = [
            r'/([^/]+)/specs?/?$',
            r'/([^/]+)/?$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                name = match.group(1)
                # Limpiar y capitalizar
                name = name.replace('-', ' ').title()
                return name
        
        return "Unknown DJI Model"
    
    def _extract_specifications(self, text: str) -> Dict[str, Any]:
        """Extrae especificaciones usando patrones regex."""
        specs = {}
        
        for field, patterns in self.patterns.items():
            for pattern in patterns:
                try:
                    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                    if match:
                        # Handle special case for Travel Mode Dimensions
                        if 'Travel Mode Dimensions' in pattern and len(match.groups()) == 3:
                            # Height, Width, Length format
                            h, w, l = match.groups()
                            value = f"{l}×{w}×{h}"  # Convert to Length×Width×Height format
                        else:
                            value = match.group(1).strip()
                        
                        if value:
                            specs[field] = value
                            logger.debug(f"Encontrado {field}: {value}")
                            break
                except Exception as e:
                    logger.debug(f"Error en patrón {pattern}: {e}")
                    continue
        
        return specs
    
    def _validate_and_clean(self, specs: Dict[str, Any]) -> Dict[str, Any]:
        """Valida y limpia las especificaciones extraídas."""
        cleaned = {}
        
        for field, value in specs.items():
            try:
                if field == 'peso_gramos':
                    # Extraer solo el número
                    weight_match = re.search(r'(\d+)', str(value))
                    if weight_match:
                        weight = int(weight_match.group(1))
                        if 50 <= weight <= 5000:  # Rango válido para drones
                            cleaned[field] = weight
                
                elif field == 'dimensiones_plegado':
                    # Limpiar formato de dimensiones y estandarizar
                    dims_str = str(value).strip()
                    
                    # Patterns to extract dimensions
                    patterns = [
                        r'(\d+(?:\.\d+)?)\s*[×x]\s*(\d+(?:\.\d+)?)\s*[×x]\s*(\d+(?:\.\d+)?)',
                        r'(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)',
                        r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)'
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, dims_str)
                        if match:
                            l, w, h = match.groups()
                            # Standardize format with × symbol
                            cleaned[field] = f"{l}×{w}×{h}"
                            break
                
                elif field in ['vuelo_minutos', 'vel_horizontal_mps', 'vel_ascenso_mps', 
                              'alcance_video_km', 'altitud_despegue_m', 'resistencia_viento_mps',
                              'almacenamiento_interno_gb']:
                    # Extraer valor numérico
                    num_match = re.search(r'(\d+)', str(value))
                    if num_match:
                        num_value = int(num_match.group(1))
                        # Rangos de validación básicos
                        if field == 'vuelo_minutos' and 5 <= num_value <= 180:
                            cleaned[field] = num_value
                        elif field == 'vel_horizontal_mps' and 5 <= num_value <= 50:
                            cleaned[field] = num_value
                        elif field == 'vel_ascenso_mps' and 1 <= num_value <= 20:
                            cleaned[field] = num_value
                        elif field == 'alcance_video_km' and 1 <= num_value <= 50:
                            cleaned[field] = num_value
                        elif field == 'altitud_despegue_m' and 1000 <= num_value <= 10000:
                            cleaned[field] = num_value
                        elif field == 'resistencia_viento_mps' and 5 <= num_value <= 25:
                            cleaned[field] = num_value
                        elif field == 'almacenamiento_interno_gb' and 1 <= num_value <= 2000:
                            cleaned[field] = num_value
                
                elif field in ['sensor_camara', 'resolucion_video', 'deteccion_obstaculos']:
                    # Campos de texto - limpiar y truncar
                    text_value = str(value).strip()
                    if len(text_value) > 5:  # Mínimo contenido
                        cleaned[field] = text_value[:500]  # Aumentar límite a 500 caracteres
                        
            except Exception as e:
                logger.debug(f"Error procesando {field}: {e}")
                continue
        
        return cleaned

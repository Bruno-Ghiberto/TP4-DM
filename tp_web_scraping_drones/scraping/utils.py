"""Funciones de utilidad para extracción y normalización de datos de drones."""
import re
import logging
from typing import Union, Optional, Dict, Any, List, Tuple
from pathlib import Path

from scraping.scraper_config import VALIDATION_RULES, DataConstants

logger = logging.getLogger(__name__)

def setup_logging(level=logging.INFO):
    """Configurar logging con codificación UTF-8."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('drone_scraper.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def get_model_name_from_url(url: str) -> Optional[str]:
    """Extraer nombre del modelo desde la URL para coincidir con SPEC_MAPPINGS."""
    model_mapping = {
        'mavic-3-pro': 'Mavic 3 Pro',
        'mavic-3-classic': 'Mavic 3 Classic',
        'air-3s': 'Air 3S',
        'air-3': 'Air 3',
        'mini-4-pro': 'Mini 4 Pro',
        'mini-3': 'Mini 3',
        'avata-2': 'Avata 2',
        'inspire-3': 'Inspire 3',
        'evo-lite-enterprise': 'EVO Lite Enterprise Series',
        'autel-alpha': 'Autel Alpha',
        'evo-max-4t': 'EVO Max 4T',
        'evo-ii-enterprise': 'EVO II Enterprise',
        'evo-ii-dual': 'EVO II Enterprise',
        'evo-ii-rtk': 'EVO II Enterprise',
        'evo-ii-pro': 'EVO II Enterprise',
        'dragonfish': 'Dragonfish Series',
        'anafi-ai': 'ANAFI Ai',
        'anafi-usa': 'ANAFI USA'
    }
    
    for key, model in model_mapping.items():
        if key in url.lower():
            return model
    
    logger.warning(f"No se pudo determinar el modelo para URL: {url}")
    return None

def normalize_text(text: str) -> str:
    """Limpiar y normalizar texto."""
    if not text:
        return ""
    
    # Eliminar espacios en blanco y saltos de línea adicionales
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_number(text: str, allow_decimal: bool = True) -> Optional[float]:
    """Extraer primer número del texto con manejo mejorado."""
    if not text:
        return None
    
    # Manejar casos especiales
    if any(term in text.lower() for term in ['n/a', 'not available', 'not specified']):
        return None
    
    # Manejar formato "< 249 g" (drones Mini)
    if text.startswith('<'):
        match = re.search(r'<\s*(\d+(?:\.\d+)?)', text)
        if match:
            return float(match.group(1)) - 1  # Devolver 248 para "< 249"
    
    # Extracción estándar de números
    if allow_decimal:
        pattern = r'(\d+(?:\.\d+)?)'
    else:
        pattern = r'(\d+)'
    
    match = re.search(pattern, text.replace(',', ''))
    return float(match.group(1)) if match else None

def extract_multiple_speeds(text: str) -> Dict[str, float]:
    """Extraer velocidades para diferentes modos (Normal/Sport/Manual)."""
    speeds = {}
    text_lower = text.lower()
    
    # Patrones para diferentes modos
    mode_patterns = {
        'normal': r'(\d+(?:\.\d+)?)\s*m/s\s*\(.*?normal.*?\)',
        'sport': r'(\d+(?:\.\d+)?)\s*m/s\s*\(.*?sport.*?\)',
        'manual': r'(\d+(?:\.\d+)?)\s*m/s\s*\(.*?manual.*?\)',
        'standard': r'(\d+(?:\.\d+)?)\s*m/s\s*\(.*?standard.*?\)',
        'ludicrous': r'(\d+(?:\.\d+)?)\s*m/s\s*\(.*?ludicrous.*?\)'
    }
    
    for mode, pattern in mode_patterns.items():
        match = re.search(pattern, text_lower)
        if match:
            speeds[mode] = float(match.group(1))
    
    # Si no se encontraron modos, intentar extraer valor único
    if not speeds:
        speed = extract_number(text)
        if speed:
            speeds['default'] = speed
    
    return speeds

def normalize_weight(text: str) -> Union[int, str]:
    """Normalizar peso con manejo mejorado."""
    if not text:
        return DataConstants.NOT_SPECIFIED
    
    text_clean = normalize_text(text.lower())
    
    # Verificar N/A explícito
    if any(term in text_clean for term in ['n/a', 'not available', 'not specified']):
        return DataConstants.NOT_AVAILABLE
    
    # Extraer valor de peso
    weight = extract_number(text_clean)
    if weight is None:
        logger.warning(f"No se pudo extraer peso de: {text}")
        return DataConstants.PARSE_FAILED
    
    # Convertir a gramos si es necesario
    if 'kg' in text_clean:
        weight = weight * 1000
    elif 'lb' in text_clean or 'pound' in text_clean:
        weight = weight * 453.592  # Convertir libras a gramos
    
    # Validar peso
    min_weight, max_weight = VALIDATION_RULES['peso_gramos']['min'], VALIDATION_RULES['peso_gramos']['max']
    if not (min_weight <= weight <= max_weight):
        logger.warning(f"Peso fuera de rango válido: {weight}g")
        return DataConstants.PARSE_FAILED
    
    return int(weight)

def normalize_dimensions(text: str) -> Union[str, str]:
    """Extraer dimensiones plegadas del texto de dimensiones."""
    if not text:
        return DataConstants.NOT_SPECIFIED
    
    text_lower = text.lower()
    
    # Buscar dimensiones plegadas específicamente
    folded_patterns = [
        r'folded[^:]*:\s*([^\n\r]+)',
        r'folded[^:]*[:\-]\s*([^\n\r]+)',
        r'size folded[^:]*:\s*([^\n\r]+)',
        r'travel mode[^:]*:\s*([^\n\r]+)'
    ]
    
    for pattern in folded_patterns:
        match = re.search(pattern, text_lower)
        if match:
            dimensions = normalize_text(match.group(1))
            # Limpiar sufijos comunes
            dimensions = re.sub(r'\s*(mm|cm|m)\s*$', '', dimensions)
            return dimensions
    
    # Si no se encontraron dimensiones plegadas, registrar y devolver texto completo
    logger.warning(f"No se encontraron dimensiones plegadas en: {text[:100]}...")
    return normalize_text(text)

def normalize_price(text: str) -> Union[float, str]:
    """Normalizar precio con manejo de moneda."""
    if not text:
        return DataConstants.NOT_SPECIFIED
    
    text_clean = normalize_text(text)
    
    # Extraer valor de precio
    price_match = re.search(r'[\$€£¥]?\s*(\d+(?:[\.,]\d+)*)', text_clean)
    if not price_match:
        return DataConstants.PARSE_FAILED
    
    price_str = price_match.group(1).replace(',', '').replace('.', '')
    try:
        price = float(price_str)
        # Asumir que está en la unidad de moneda principal (dólares, euros, etc.)
        return price
    except ValueError:
        logger.warning(f"No se pudo parsear precio: {text}")
        return DataConstants.PARSE_FAILED

def extract_storage_from_text(text: str) -> Union[int, str]:
    """Extraer almacenamiento en GB con manejo mejorado."""
    if not text:
        return DataConstants.NOT_SPECIFIED
    
    text_lower = text.lower()
    
    # Verificar N/A explícito
    if any(term in text_lower for term in ['n/a', 'not available', 'not specified']):
        return DataConstants.NOT_AVAILABLE
    
    # Para Inspire 3: extraer de "DJI PROSSD 1TB"
    tb_match = re.search(r'(\d+)\s*tb', text_lower)
    if tb_match:
        return int(tb_match.group(1)) * 1000  # Convertir TB a GB
    
    # Extracción estándar de GB
    gb_match = re.search(r'(\d+)\s*gb', text_lower)
    if gb_match:
        return int(gb_match.group(1))
    
    # Si contiene información de almacenamiento pero sin número claro
    if any(word in text_lower for word in ['storage', 'memory', 'card']):
        logger.warning(f"Almacenamiento no estándar: {text}")
        return DataConstants.PARSE_FAILED
    
    return DataConstants.NOT_SPECIFIED

def extract_sensing_info(text: str) -> Union[Dict[str, Any], str]:
    """Extraer información detallada de sensores."""
    if not text:
        return DataConstants.NOT_SPECIFIED
    
    text_lower = text.lower()
    
    # Verificar ausencia explícita
    if any(term in text_lower for term in ['not specified', 'not available', 'n/a']):
        return DataConstants.NOT_AVAILABLE
    
    sensing_info = {
        'type': None,
        'description': normalize_text(text),
        'directions': [],
        'features': []
    }
    
    # Extraer tipo de sensor
    if 'omnidirectional' in text_lower:
        sensing_info['type'] = 'Omnidireccional'
        if 'binocular' in text_lower:
            sensing_info['type'] = 'Sistema de visión binocular omnidireccional'
    elif 'downward' in text_lower:
        sensing_info['type'] = 'Sistema de visión hacia abajo'
    elif 'stereoscopic' in text_lower:
        sensing_info['type'] = 'Cámaras estereoscópicas'
    elif 'radar' in text_lower:
        sensing_info['type'] = 'Sistema de detección por radar'
    
    # Extraer direcciones
    directions = ['forward', 'backward', 'upward', 'downward', 'lateral', 'side']
    for direction in directions:
        if direction in text_lower:
            sensing_info['directions'].append(direction)
    
    # Extraer características
    features = ['obstacle avoidance', 'collision avoidance', 'positioning', 'detection']
    for feature in features:
        if feature in text_lower:
            sensing_info['features'].append(feature)
    
    return sensing_info

def extract_conditional_values(text: str, conditions: List[str]) -> Dict[str, Any]:
    """Extraer valores que dependen de condiciones (ej. gear up/down, tipo de hélice)."""
    values = {}
    text_lower = text.lower()
    
    for condition in conditions:
        condition_lower = condition.lower()
        # Buscar patrón: "valor (condición)" o "condición: valor"
        patterns = [
            rf'(\d+(?:\.\d+)?)[^(]*\([^)]*{re.escape(condition_lower)}[^)]*\)',
            rf'{re.escape(condition_lower)}[^:]*:\s*(\d+(?:\.\d+)?)',
            rf'(\d+(?:\.\d+)?)[^a-z]*{re.escape(condition_lower)}'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                values[condition] = float(match.group(1))
                break
    
    return values

def validate_drone_data_v2(drone_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validación mejorada con reporte detallado de errores."""
    validated_data = drone_data.copy()
    validation_errors = []
    
    # Validar campos numéricos
    numeric_fields = ['peso_gramos', 'vuelo_minutos', 'vel_horizontal_mps', 
                     'alcance_video_km', 'altitud_despegue_m', 'resistencia_viento_mps']
    
    for field in numeric_fields:
        if field in validated_data and field in VALIDATION_RULES:
            value = validated_data[field]
            if isinstance(value, (int, float)):
                min_val, max_val = VALIDATION_RULES[field]['min'], VALIDATION_RULES[field]['max']
                if not (min_val <= value <= max_val):
                    validation_errors.append(f"{field}: {value} fuera de rango [{min_val}, {max_val}]")
                    validated_data[field] = DataConstants.PARSE_FAILED
    
    # Registrar errores de validación
    if validation_errors:
        model = validated_data.get('modelo', 'Desconocido')
        logger.warning(f"Errores de validación para {model}: {'; '.join(validation_errors)}")
    
    # Agregar metadatos de validación
    validated_data['_validation'] = {
        'errors': validation_errors,
        'validated_at': None  # Podría agregar timestamp
    }
    
    return validated_data

def validate_drone_data(drone_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validar y limpiar datos del drone usando validación básica."""
    return drone_data

def validate_and_clean_specs(specs: Dict[str, Any]) -> Dict[str, Any]:
    """Validar y limpiar especificaciones del drone."""
    cleaned_specs = {}
    
    for key, value in specs.items():
        if key == 'peso_gramos':
            if isinstance(value, (int, float)):
                # Validar rango de peso
                min_weight, max_weight = VALIDATION_RULES.get('peso_gramos', {'min': 0, 'max': 50000})['min'], VALIDATION_RULES.get('peso_gramos', {'min': 0, 'max': 50000})['max']
                if min_weight <= value <= max_weight:
                    cleaned_specs[key] = value
                else:
                    logger.warning(f"Peso fuera de rango: {value}g")
                    cleaned_specs[key] = 0.0
            else:
                cleaned_specs[key] = value
        
        elif key == 'vel_horizontal_mps':
            if isinstance(value, (int, float)):
                # Validar rango de velocidad
                min_speed, max_speed = VALIDATION_RULES.get('vel_horizontal_mps', {'min': 0, 'max': 30})['min'], VALIDATION_RULES.get('vel_horizontal_mps', {'min': 0, 'max': 30})['max']
                if min_speed <= value <= max_speed:
                    cleaned_specs[key] = value
                else:
                    logger.warning(f"Velocidad horizontal fuera de rango: {value} m/s")
                    cleaned_specs[key] = 0.0
            else:
                cleaned_specs[key] = value
        
        elif key == 'vuelo_minutos':
            if isinstance(value, (int, float)):
                # Validar rango de tiempo de vuelo
                min_time, max_time = VALIDATION_RULES.get('vuelo_minutos', {'min': 0, 'max': 180})['min'], VALIDATION_RULES.get('vuelo_minutos', {'min': 0, 'max': 180})['max']
                if min_time <= value <= max_time:
                    cleaned_specs[key] = value
                else:
                    logger.warning(f"Tiempo de vuelo fuera de rango: {value} min")
                    cleaned_specs[key] = 0.0
            else:
                cleaned_specs[key] = value
        
        elif key == 'alcance_video_km':
            if isinstance(value, (int, float)):
                # Validar rango de video
                min_range, max_range = VALIDATION_RULES.get('alcance_video_km', {'min': 0, 'max': 20})['min'], VALIDATION_RULES.get('alcance_video_km', {'min': 0, 'max': 20})['max']
                if min_range <= value <= max_range:
                    cleaned_specs[key] = value
                else:
                    logger.warning(f"Alcance de video fuera de rango: {value} km")
                    cleaned_specs[key] = 0.0
            else:
                cleaned_specs[key] = value
        
        else:
            # Mantener otras especificaciones tal cual
            cleaned_specs[key] = value
    
    return cleaned_specs

# Funciones adicionales de utilidad para parsers
def convert_units(value: float, from_unit: str, to_unit: str) -> float:
    """Convertir entre diferentes unidades."""
    if from_unit == to_unit:
        return value
    
    # Conversiones de velocidad
    if from_unit == 'mph' and to_unit == 'm/s':
        return value * 0.44704
    elif from_unit == 'km/h' and to_unit == 'm/s':
        return value / 3.6
    elif from_unit == 'm/s' and to_unit == 'km/h':
        return value * 3.6
    
    # Conversiones de distancia
    elif from_unit == 'ft' and to_unit == 'm':
        return value * 0.3048
    elif from_unit == 'm' and to_unit == 'ft':
        return value / 0.3048
    elif from_unit == 'mi' and to_unit == 'km':
        return value * 1.609344
    elif from_unit == 'km' and to_unit == 'mi':
        return value / 1.609344
    
    # Conversiones de peso
    elif from_unit == 'lb' and to_unit == 'g':
        return value * 453.592
    elif from_unit == 'kg' and to_unit == 'g':
        return value * 1000
    elif from_unit == 'oz' and to_unit == 'g':
        return value * 28.3495
    
    logger.warning(f"Conversión no implementada: {from_unit} a {to_unit}")
    return value

def parse_dimensions(text: str) -> str:
    """Parsear y formatear texto de dimensiones."""
    if not text:
        return ""
    
    # Limpiar texto
    text = normalize_text(text)
    
    # Reemplazar separadores comunes con ×
    text = re.sub(r'\s*[x×*]\s*', '×', text)
    
    return text

def parse_resolution(text: str) -> str:
    """Parsear texto de resolución de video."""
    if not text:
        return ""
    
    text = normalize_text(text)
    
    # Patrones comunes de resolución
    resolution_patterns = [
        r'(\d+)k',  # 4K, 6K, etc.
        r'(\d+)p',  # 1080p, 720p, etc.
        r'(\d+)\s*x\s*(\d+)',  # 1920x1080, etc.
    ]
    
    for pattern in resolution_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if 'k' in pattern:
                return f"{match.group(1)}K"
            elif 'p' in pattern:
                return f"{match.group(1)}p"
            elif 'x' in pattern:
                return f"{match.group(1)}×{match.group(2)}"
    
    return text

def parse_boolean_spec(text: str) -> bool:
    """Parsear valores de especificación booleanos."""
    if not text:
        return False
    
    text = normalize_text(text).lower()
    
    # Indicadores positivos
    if any(word in text for word in ['yes', 'si', 'sí', 'equipped', 'available', 'supported', 'enabled', 'true']):
        return True
    
    # Indicadores negativos
    if any(word in text for word in ['no', 'not available', 'not supported', 'disabled', 'false']):
        return False
    
    # Por defecto False para casos poco claros
    return False

def fuzzy_match_spec(text: str, keywords: List[str]) -> bool:
    """Realizar coincidencia difusa entre texto y palabras clave."""
    if not text or not keywords:
        return False
    
    text_lower = text.lower()
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        
        # Coincidencia exacta
        if keyword_lower in text_lower:
            return True
        
        # Coincidencia difusa - verificar si la mayoría de palabras coinciden
        text_words = set(text_lower.split())
        keyword_words = set(keyword_lower.split())
        
        if len(keyword_words) > 0:
            match_ratio = len(text_words & keyword_words) / len(keyword_words)
            if match_ratio > 0.6:  # 60% de superposición de palabras
                return True
    
    return False

def extract_weight_in_grams(text: str) -> float:
    """Extraer peso y convertir a gramos."""
    if not text:
        return 0.0
    
    text_lower = text.lower()
    
    # Extraer número
    weight = extract_number(text_lower)
    if weight is None:
        return 0.0
    
    # Convertir a gramos basado en la unidad
    if 'kg' in text_lower:
        return weight * 1000
    elif 'lb' in text_lower or 'pound' in text_lower:
        return weight * 453.592
    elif 'oz' in text_lower:
        return weight * 28.3495
    elif 'g' in text_lower:
        return weight
    
    # Por defecto a gramos si no se especifica unidad
    return weight

def extract_speed_in_mps(text: str) -> float:
    """Extraer velocidad y convertir a m/s."""
    if not text:
        return 0.0
    
    text_lower = text.lower()
    
    # Extraer número
    speed = extract_number(text_lower)
    if speed is None:
        return 0.0
    
    # Convertir a m/s basado en la unidad
    if 'km/h' in text_lower or 'kmh' in text_lower:
        return speed / 3.6
    elif 'mph' in text_lower:
        return speed * 0.44704
    elif 'm/s' in text_lower or 'ms' in text_lower:
        return speed
    
    # Por defecto a m/s si no se especifica unidad
    return speed

def extract_distance_in_km(text: str) -> float:
    """Extraer distancia y convertir a kilómetros."""
    if not text:
        return 0.0
    
    text_lower = text.lower()
    
    # Extraer número
    distance = extract_number(text_lower)
    if distance is None:
        return 0.0
    
    # Convertir a km basado en la unidad - verificar unidades específicas primero para evitar confusiones
    if 'kilometer' in text_lower or 'kilometres' in text_lower:
        return distance
    elif 'km' in text_lower:
        return distance
    elif 'mi' in text_lower or 'mile' in text_lower:
        return distance * 1.609344
    elif 'ft' in text_lower or 'feet' in text_lower:
        return distance * 0.0003048
    elif 'meters' in text_lower:
        return distance / 1000
    elif 'm' in text_lower and 'mm' not in text_lower and 'km' not in text_lower:
        # Solo convertir 'm' único a metros si no es ya km o mm
        # Sea más cuidadoso con esta conversión para evitar falsos positivos
        if re.search(r'\d+\s*m\s*$', text_lower) or re.search(r'\d+\s*m\s*[^a-z]', text_lower):
            return distance / 1000
    
    # Por defecto a km si no se especifica unidad (común para especificaciones de rango de video)
    return distance

def extract_altitude_in_meters(text: str) -> float:
    """Extraer altitud y convertir a metros."""
    if not text:
        return 0.0
    
    text_lower = text.lower()
    
    # Extraer número
    altitude = extract_number(text_lower)
    if altitude is None:
        return 0.0
    
    # Convertir a metros basado en la unidad
    if 'm' in text_lower and 'mm' not in text_lower:
        return altitude
    elif 'ft' in text_lower or 'feet' in text_lower:
        return altitude * 0.3048
    elif 'km' in text_lower:
        return altitude * 1000
    
    # Por defecto a metros si no se especifica unidad
    return altitude

def extract_spec_with_improved_mapping(text: str, mapping_info: Dict[str, Any], field_name: str) -> Any:
    """Extraer especificación usando mapeo mejorado con palabras clave y notas."""
    keywords = mapping_info.get('keywords', [])
    notes = mapping_info.get('notes', '')
    
    # Intentar cada palabra clave en orden de prioridad
    for keyword in keywords:
        if keyword.lower() in text.lower():
            # Aplicar procesamiento específico de campo basado en notas
            if 'peso' in field_name or 'weight' in field_name:
                return extract_weight_with_notes(text, notes)
            elif 'dimensiones' in field_name or 'dimensions' in field_name:
                return extract_dimensions_with_notes(text, notes)
            elif 'vuelo' in field_name or 'flight' in field_name:
                return extract_flight_time_with_notes(text, notes)
            elif 'velocidad' in field_name or 'speed' in field_name:
                return extract_speed_with_notes(text, notes)
            elif 'alcance' in field_name or 'range' in field_name:
                return extract_range_with_notes(text, notes)
            elif 'altitud' in field_name or 'altitude' in field_name:
                return extract_altitude_with_notes(text, notes)
            else:
                return normalize_text(text)
    
    return DataConstants.NOT_SPECIFIED

def extract_weight_with_notes(text: str, notes: str) -> Union[float, str]:
    """Extraer peso considerando notas de mapeo."""
    if not text:
        return DataConstants.NOT_SPECIFIED
    
    weight = extract_number(text)
    if weight is None:
        return DataConstants.PARSE_FAILED
    
    # Convertir a gramos si es necesario
    if 'kg' in text.lower():
        weight = weight * 1000
    elif 'lb' in text.lower() or 'pound' in text.lower():
        weight = weight * 453.592
    
    # Aplicar validación basada en notas
    if 'incluye batería' in notes.lower() or 'including battery' in notes.lower():
        logger.debug(f"Peso incluye batería según notas: {weight}g")
    
    if 'verificar qué está incluido' in notes.lower():
        logger.warning(f"Peso necesita verificación: {weight}g - {notes}")
    
    # Validar peso
    min_weight, max_weight = VALIDATION_RULES['peso_gramos']['min'], VALIDATION_RULES['peso_gramos']['max']
    if not (min_weight <= weight <= max_weight):
        logger.warning(f"Peso fuera de rango válido: {weight}g")
        return DataConstants.PARSE_FAILED
    
    return float(weight)

def extract_dimensions_with_notes(text: str, notes: str) -> str:
    """Extraer dimensiones considerando notas de mapeo."""
    if not text:
        return DataConstants.NOT_SPECIFIED
    
    # Usar notas para guiar extracción
    if 'sin hélices' in notes.lower() or 'without propellers' in notes.lower():
        logger.debug(f"Dimensiones sin hélices según notas: {text}")
    
    if 'no tienen dimensiones plegadas' in notes.lower():
        logger.warning(f"Modelo puede no tener dimensiones plegadas: {text}")
    
    return normalize_dimensions(text)

def extract_flight_time_with_notes(text: str, notes: str) -> Union[float, str]:
    """Extraer tiempo de vuelo considerando notas de mapeo."""
    if not text:
        return DataConstants.NOT_SPECIFIED
    
    time_val = extract_number(text)
    if time_val is None:
        return DataConstants.PARSE_FAILED
    
    # Aplicar procesamiento basado en notas
    if 'sin viento' in notes.lower() or 'windless' in notes.lower():
        logger.debug(f"Tiempo de vuelo en condiciones sin viento: {time_val} min")
    
    if 'endurance' in notes.lower():
        logger.debug(f"Tiempo de vuelo como 'endurance': {time_val} min")
    
    # Convertir a minutos si es necesario
    if 'hour' in text.lower():
        time_val = time_val * 60
    
    return float(time_val)

def extract_speed_with_notes(text: str, notes: str) -> Union[float, str]:
    """Extraer velocidad considerando notas de mapeo."""
    if not text:
        return DataConstants.NOT_SPECIFIED
    
    speed = extract_number(text)
    if speed is None:
        return DataConstants.PARSE_FAILED
    
    # Aplicar procesamiento basado en notas
    if 'máximo' in notes.lower() or 'buscar el máximo' in notes.lower():
        logger.debug(f"Buscando velocidad máxima: {speed}")
    
    if 'modo sport' in notes.lower() or 'sport mode' in notes.lower():
        logger.debug(f"Velocidad en modo Sport: {speed}")
    
    # Convertir a m/s si es necesario
    if 'km/h' in text.lower():
        speed = speed / 3.6
    elif 'mph' in text.lower():
        speed = speed * 0.44704
    
    return float(speed)

def extract_range_with_notes(text: str, notes: str) -> Union[float, str]:
    """Extraer alcance considerando notas de mapeo."""
    if not text:
        return DataConstants.NOT_SPECIFIED
    
    range_val = extract_number(text)
    if range_val is None:
        return DataConstants.PARSE_FAILED
    
    # Aplicar procesamiento basado en notas
    if 'fcc' in notes.lower() or 'tomar el mayor' in notes.lower():
        logger.debug(f"Alcance (preferir FCC): {range_val}")
    
    if 'image transmission' in notes.lower():
        logger.debug(f"Alcance de transmisión de imagen: {range_val}")
    
    # Convertir a km si es necesario
    if 'mi' in text.lower() or 'mile' in text.lower():
        range_val = range_val * 1.609344
    elif 'm' in text.lower() and 'km' not in text.lower():
        range_val = range_val / 1000
    
    return float(range_val)

def extract_altitude_with_notes(text: str, notes: str) -> Union[float, str]:
    """Extraer altitud considerando notas de mapeo."""
    if not text:
        return DataConstants.NOT_SPECIFIED
    
    altitude = extract_number(text)
    if altitude is None:
        return DataConstants.PARSE_FAILED
    
    # Aplicar procesamiento basado en notas
    if 'nivel del mar' in notes.lower() or 'sea level' in notes.lower():
        logger.debug(f"Altitud sobre nivel del mar: {altitude}m")
    
    if 'service ceiling' in notes.lower():
        logger.debug(f"Techo de servicio: {altitude}m")
    
    # Convertir a metros si es necesario
    if 'ft' in text.lower() or 'feet' in text.lower():
        altitude = altitude * 0.3048
    
    return float(altitude)

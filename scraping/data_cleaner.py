
#Data Cleaner - Normalización y limpieza de datos de drones
#Unifica formatos y asegura consistencia de datos


import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DataCleaner:
    """Limpiador y normalizador de datos de drones"""
    
    def __init__(self):
        self.currency_symbols = {
            '$': 'USD',
            '€': 'EUR',
            '£': 'GBP',
            '¥': 'JPY',
            '₹': 'INR'
        }
        
        self.unit_conversions = {
            'weight': {
                'kg': 1000,
                'g': 1,
                'gram': 1,
                'grams': 1,
                'lb': 453.592,
                'lbs': 453.592,
                'pound': 453.592,
                'pounds': 453.592,
                'oz': 28.3495,
                'ounce': 28.3495
            },
            'distance': {
                'km': 1000,
                'kilometer': 1000,
                'kilometers': 1000,
                'm': 1,
                'meter': 1,
                'meters': 1,
                'mi': 1609.34,
                'mile': 1609.34,
                'miles': 1609.34,
                'ft': 0.3048,
                'feet': 0.3048,
                'foot': 0.3048
            },
            'speed': {
                'km/h': 1,
                'kmh': 1,
                'kph': 1,
                'm/s': 3.6,
                'mph': 1.60934,
                'mi/h': 1.60934
            },
            'time': {
                'h': 60,
                'hour': 60,
                'hours': 60,
                'min': 1,
                'minute': 1,
                'minutes': 1,
                's': 0.0167,
                'sec': 0.0167,
                'second': 0.0167,
                'seconds': 0.0167
            }
        }
    
    def normalize_price_formats(self, price_str: str) -> Optional[float]:
        """
        Normalizar formatos de precio a float
        
        Ejemplos:
            "$1,299" → 1299.0
            "€1.299,00" → 1299.0
            "USD 1299" → 1299.0
        """
        if not price_str or not isinstance(price_str, str):
            return None
        
        try:
            # Limpiar string
            price_str = price_str.strip()
            
            # Detectar y remover símbolo de moneda
            currency = None
            for symbol, curr in self.currency_symbols.items():
                if symbol in price_str:
                    currency = curr
                    price_str = price_str.replace(symbol, '')
                    break
            
            # Remover palabras de moneda
            for curr in ['USD', 'EUR', 'GBP', 'JPY', 'INR']:
                price_str = price_str.replace(curr, '')
            
            # Limpiar espacios y caracteres especiales
            price_str = price_str.strip()
            
            # Manejar diferentes formatos de números
            # Formato americano: 1,234.56
            if ',' in price_str and '.' in price_str:
                if price_str.rindex(',') < price_str.rindex('.'):
                    price_str = price_str.replace(',', '')
                else:
                    # Formato europeo: 1.234,56
                    price_str = price_str.replace('.', '').replace(',', '.')
            elif ',' in price_str:
                # Determinar si la coma es decimal o separador de miles
                parts = price_str.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    # Probablemente decimal
                    price_str = price_str.replace(',', '.')
                else:
                    # Probablemente separador de miles
                    price_str = price_str.replace(',', '')
            
            # Extraer solo números y punto decimal
            price_str = re.sub(r'[^\d.]', '', price_str)
            
            # Convertir a float
            price = float(price_str)
            
            # Validar rango razonable para precio de drone
            if price < 10 or price > 100000:
                logger.warning(f"Precio fuera de rango razonable: {price}")
                return None
            
            return round(price, 2)
            
        except Exception as e:
            logger.error(f"Error normalizando precio '{price_str}': {str(e)}")
            return None
    
    def extract_number(self, text: str, unit_type: str) -> Optional[float]:
        """
        Extraer número con conversión de unidades
        
        Args:
            text: Texto con número y unidad
            unit_type: Tipo de unidad ('grams', 'meters', 'minutes', 'kmh', 'fps')
        
        Returns:
            Valor numérico en unidad estándar
        """
        if not text or not isinstance(text, str):
            return None
        
        try:
            # Limpiar texto
            text = text.strip().lower()
            
            # Buscar números (incluyendo decimales)
            numbers = re.findall(r'[\d.]+', text)
            if not numbers:
                return None
            
            # Tomar el primer número encontrado
            value = float(numbers[0])
            
            # Buscar unidad y convertir
            if unit_type == 'grams':
                conversions = self.unit_conversions['weight']
                # Buscar unidad en el texto
                for unit, factor in conversions.items():
                    if unit in text:
                        return value * factor
                # Si no se encuentra unidad, asumir gramos
                return value
            
            elif unit_type == 'meters':
                conversions = self.unit_conversions['distance']
                for unit, factor in conversions.items():
                    if unit in text:
                        return value * factor
                return value
            
            elif unit_type == 'minutes':
                conversions = self.unit_conversions['time']
                for unit, factor in conversions.items():
                    if unit in text:
                        return value * factor
                return value
            
            elif unit_type == 'kmh':
                conversions = self.unit_conversions['speed']
                for unit, factor in conversions.items():
                    if unit in text:
                        return value * factor
                return value
            
            elif unit_type == 'fps':
                # Frames per second, no necesita conversión
                return value
            
            else:
                # Tipo desconocido, retornar valor sin conversión
                return value
                
        except Exception as e:
            logger.error(f"Error extrayendo número de '{text}': {str(e)}")
            return None
    
    def standardize_specifications(self, raw_specs: Dict) -> Dict:
        """
        Unificar especificaciones a formato estándar
        
        Args:
            raw_specs: Especificaciones en formato crudo
        
        Returns:
            Especificaciones normalizadas
        """
        standard_specs = {
            'peso_gramos': None,
            'autonomia_minutos': None,
            'alcance_metros': None,
            'velocidad_max_kmh': None,
            'resistencia_viento': None,
            'temperatura_operacion': None
        }
        
        # Mapeo de posibles nombres de campos
        field_mappings = {
            'peso_gramos': ['weight', 'peso', 'mass', 'takeoff_weight'],
            'autonomia_minutos': ['flight_time', 'battery_life', 'autonomy', 'endurance'],
            'alcance_metros': ['range', 'transmission_range', 'control_range', 'alcance'],
            'velocidad_max_kmh': ['max_speed', 'top_speed', 'velocity', 'speed'],
            'resistencia_viento': ['wind_resistance', 'wind_speed', 'max_wind'],
            'temperatura_operacion': ['operating_temp', 'temperature_range', 'temp_range']
        }
        
        # Buscar valores en diferentes campos posibles
        for standard_field, possible_fields in field_mappings.items():
            for field in possible_fields:
                if field in raw_specs and raw_specs[field]:
                    value = raw_specs[field]
                    
                    # Procesar según el tipo de campo
                    if standard_field == 'peso_gramos':
                        standard_specs[standard_field] = self.extract_number(str(value), 'grams')
                    elif standard_field == 'autonomia_minutos':
                        standard_specs[standard_field] = self.extract_number(str(value), 'minutes')
                    elif standard_field == 'alcance_metros':
                        standard_specs[standard_field] = self.extract_number(str(value), 'meters')
                    elif standard_field == 'velocidad_max_kmh':
                        standard_specs[standard_field] = self.extract_number(str(value), 'kmh')
                    else:
                        # Campos de texto
                        standard_specs[standard_field] = str(value).strip()
                    
                    break
        
        return standard_specs
    
    def validate_data_quality(self, drone_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validar calidad de datos con QA automático
        
        Args:
            drone_data: Datos de un drone
        
        Returns:
            Tuple (es_válido, lista_de_problemas)
        """
        issues = []
        
        # Validaciones requeridas
        required_fields = ['modelo', 'marca', 'especificaciones_tecnicas']
        for field in required_fields:
            if field not in drone_data or not drone_data[field]:
                issues.append(f"Campo requerido faltante: {field}")
        
        # Validar especificaciones técnicas
        if 'especificaciones_tecnicas' in drone_data:
            specs = drone_data['especificaciones_tecnicas']
            
            # Al menos 3 especificaciones deben tener valor
            spec_count = sum(1 for v in specs.values() if v is not None)
            if spec_count < 3:
                issues.append(f"Pocas especificaciones válidas: {spec_count}/6")
            
            # Validar rangos
            if specs.get('peso_gramos') is not None:
                if specs['peso_gramos'] < 50 or specs['peso_gramos'] > 50000:
                    issues.append(f"Peso fuera de rango: {specs['peso_gramos']}g")
            
            if specs.get('autonomia_minutos') is not None:
                if specs['autonomia_minutos'] < 5 or specs['autonomia_minutos'] > 120:
                    issues.append(f"Autonomía fuera de rango: {specs['autonomia_minutos']}min")
            
            if specs.get('alcance_metros') is not None:
                if specs['alcance_metros'] < 30 or specs['alcance_metros'] > 20000:
                    issues.append(f"Alcance fuera de rango: {specs['alcance_metros']}m")
        
        # Validar precio si existe
        if 'precio' in drone_data and drone_data['precio'].get('usd'):
            precio = drone_data['precio']['usd']
            if precio < 50 or precio > 50000:
                issues.append(f"Precio fuera de rango: ${precio}")
        
        # Validar marca
        if 'marca' in drone_data:
            marcas_validas = ['DJI', 'Autel', 'Parrot']
            if drone_data['marca'] not in marcas_validas:
                issues.append(f"Marca no válida: {drone_data['marca']}")
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    def merge_brand_datasets(self, dji: List[Dict], autel: List[Dict], parrot: List[Dict]) -> pd.DataFrame:
        """
        Combinar datasets de diferentes marcas en DataFrame unificado
        
        Args:
            dji: Lista de drones DJI
            autel: Lista de drones Autel
            parrot: Lista de drones Parrot
        
        Returns:
            DataFrame unificado
        """
        # Combinar todas las listas
        all_drones = []
        
        # Asegurar que cada drone tenga la marca correcta
        for drone in dji:
            drone['marca'] = 'DJI'
            all_drones.append(drone)
        
        for drone in autel:
            drone['marca'] = 'Autel'
            all_drones.append(drone)
        
        for drone in parrot:
            drone['marca'] = 'Parrot'
            all_drones.append(drone)
        
        # Convertir a DataFrame
        df = pd.json_normalize(all_drones)
        
        # Normalizar nombres de columnas
        df.columns = [col.replace('.', '_') for col in df.columns]
        
        # Asegurar tipos de datos correctos
        numeric_columns = [
            'precio_usd',
            'especificaciones_tecnicas_peso_gramos',
            'especificaciones_tecnicas_autonomia_minutos',
            'especificaciones_tecnicas_alcance_metros',
            'especificaciones_tecnicas_velocidad_max_kmh',
            'camara_fps_max',
            'camara_zoom_optico',
            'camara_zoom_digital'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Llenar valores faltantes con defaults apropiados
        df['precio_usd'] = df.get('precio_usd', np.nan)
        df['especificaciones_tecnicas_peso_gramos'] = df.get('especificaciones_tecnicas_peso_gramos', np.nan)
        
        # Agregar timestamp de procesamiento
        df['fecha_procesamiento'] = datetime.now().isoformat()
        
        # Ordenar por marca y modelo
        if 'marca' in df.columns and 'modelo' in df.columns:
            df = df.sort_values(['marca', 'modelo'])
        
        logger.info(f"DataFrame unificado creado: {len(df)} drones, {len(df.columns)} columnas")
        
        return df
    
    def normalize_drone_dataset(self, drones: List[Dict]) -> List[Dict]:
        """
        Normalizar dataset completo de drones
        
        Args:
            drones: Lista de drones en formato crudo
        
        Returns:
            Lista de drones normalizados
        """
        normalized = []
        
        for drone in drones:
            try:
                # Normalizar especificaciones
                if 'especificaciones_tecnicas' in drone:
                    drone['especificaciones_tecnicas'] = self.standardize_specifications(
                        drone['especificaciones_tecnicas']
                    )
                
                # Normalizar precio
                if 'precio' in drone:
                    if isinstance(drone['precio'], dict):
                        if 'usd' in drone['precio'] and isinstance(drone['precio']['usd'], str):
                            drone['precio']['usd'] = self.normalize_price_formats(
                                drone['precio']['usd']
                            )
                    elif isinstance(drone['precio'], str):
                        drone['precio'] = {
                            'usd': self.normalize_price_formats(drone['precio']),
                            'moneda_local': None,
                            'fecha_precio': datetime.now().strftime('%Y-%m-%d')
                        }
                
                # Normalizar resolución de video
                if 'camara' in drone and 'resolucion_video' in drone['camara']:
                    res = str(drone['camara']['resolucion_video']).upper()
                    if '4K' in res or '2160' in res:
                        drone['camara']['resolucion_video'] = '4K'
                    elif '6K' in res:
                        drone['camara']['resolucion_video'] = '6K'
                    elif '8K' in res:
                        drone['camara']['resolucion_video'] = '8K'
                    elif '1080' in res:
                        drone['camara']['resolucion_video'] = '1080p'
                    elif '720' in res:
                        drone['camara']['resolucion_video'] = '720p'
                
                # Validar calidad
                is_valid, issues = self.validate_data_quality(drone)
                
                if is_valid:
                    normalized.append(drone)
                else:
                    logger.warning(f"Drone {drone.get('modelo', 'Unknown')} tiene problemas: {issues}")
                    # Incluir de todos modos pero marcar confiabilidad
                    if 'metadata' not in drone:
                        drone['metadata'] = {}
                    drone['metadata']['confiabilidad_datos'] = 'baja'
                    drone['metadata']['problemas_calidad'] = issues
                    normalized.append(drone)
                    
            except Exception as e:
                logger.error(f"Error normalizando drone {drone.get('modelo', 'Unknown')}: {str(e)}")
        
        logger.info(f"Normalizados {len(normalized)} de {len(drones)} drones")
        
        return normalized
    
    def generate_cleaning_report(self, original_data: List[Dict], cleaned_data: List[Dict]) -> Dict:
        """
        Generar reporte de limpieza de datos
        
        Args:
            original_data: Datos originales
            cleaned_data: Datos limpios
        
        Returns:
            Reporte de limpieza
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_registros_originales': len(original_data),
            'total_registros_limpios': len(cleaned_data),
            'registros_eliminados': len(original_data) - len(cleaned_data),
            'problemas_encontrados': {},
            'estadisticas_campos': {}
        }
        
        # Analizar problemas comunes
        problemas = {}
        for drone in original_data:
            _, issues = self.validate_data_quality(drone)
            for issue in issues:
                if issue not in problemas:
                    problemas[issue] = 0
                problemas[issue] += 1
        
        report['problemas_encontrados'] = problemas
        
        # Estadísticas de campos
        if cleaned_data:
            df = pd.DataFrame(cleaned_data)
            
            for col in df.columns:
                if df[col].dtype in ['float64', 'int64']:
                    report['estadisticas_campos'][col] = {
                        'tipo': 'numerico',
                        'valores_no_nulos': df[col].notna().sum(),
                        'porcentaje_completitud': (df[col].notna().sum() / len(df)) * 100,
                        'min': float(df[col].min()) if df[col].notna().any() else None,
                        'max': float(df[col].max()) if df[col].notna().any() else None,
                        'promedio': float(df[col].mean()) if df[col].notna().any() else None
                    }
                else:
                    report['estadisticas_campos'][col] = {
                        'tipo': 'texto',
                        'valores_no_nulos': df[col].notna().sum(),
                        'porcentaje_completitud': (df[col].notna().sum() / len(df)) * 100,
                        'valores_unicos': df[col].nunique()
                    }
        
        return report


if __name__ == "__main__":
    # Prueba del limpiador
    cleaner = DataCleaner()
    
    # Ejemplos de normalización
    test_prices = [
        "$1,299.99",
        "€1.299,00",
        "USD 2499",
        "£899.99",
        "1299",
        "$1,299.00 USD"
    ]
    
    print("Prueba de normalización de precios:")
    for price in test_prices:
        normalized = cleaner.normalize_price_formats(price)
        print(f"{price} → {normalized}")
    
    print("\nPrueba de extracción de números con unidades:")
    test_values = [
        ("249 grams", "grams"),
        ("1.2 kg", "grams"),
        ("10 km", "meters"),
        ("5 miles", "meters"),
        ("45 minutes", "minutes"),
        ("1.5 hours", "minutes"),
        ("50 km/h", "kmh"),
        ("30 mph", "kmh")
    ]
    
    for value, unit_type in test_values:
        extracted = cleaner.extract_number(value, unit_type)
        print(f"{value} ({unit_type}) → {extracted}")
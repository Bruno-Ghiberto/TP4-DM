"""
Data Validator - Validación de esquema y calidad de datos
Asegura que los datos cumplan con el esquema JSON definido
"""

import json
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

import jsonschema
from jsonschema import validate, ValidationError, Draft7Validator

logger = logging.getLogger(__name__)


class DataValidator:
    """Validador de datos de drones según esquema JSON"""
    
    def __init__(self):
        self.schema = self._load_schema()
        self.validator = Draft7Validator(self.schema)
        self.validation_stats = {
            'total_validated': 0,
            'valid': 0,
            'invalid': 0,
            'common_errors': {}
        }
    
    def _load_schema(self) -> Dict:
        """Cargar esquema JSON de drones"""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["modelo", "marca", "especificaciones_tecnicas", "clasificacion"],
            "properties": {
                "modelo": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 100
                },
                "marca": {
                    "type": "string",
                    "enum": ["DJI", "Autel", "Parrot"]
                },
                "url_fuente": {
                    "type": "string",
                    "format": "uri"
                },
                "precio": {
                    "type": "object",
                    "properties": {
                        "usd": {
                            "type": ["number", "null"],
                            "minimum": 0,
                            "maximum": 100000
                        },
                        "moneda_local": {
                            "type": ["number", "null"]
                        },
                        "fecha_precio": {
                            "type": ["string", "null"],
                            "format": "date"
                        }
                    }
                },
                "especificaciones_tecnicas": {
                    "type": "object",
                    "required": ["peso_gramos", "autonomia_minutos", "alcance_metros"],
                    "properties": {
                        "peso_gramos": {
                            "type": ["number", "null"],
                            "minimum": 0,
                            "maximum": 50000
                        },
                        "autonomia_minutos": {
                            "type": ["number", "null"],
                            "minimum": 0,
                            "maximum": 120
                        },
                        "alcance_metros": {
                            "type": ["number", "null"],
                            "minimum": 0,
                            "maximum": 20000
                        },
                        "velocidad_max_kmh": {
                            "type": ["number", "null"],
                            "minimum": 0,
                            "maximum": 200
                        },
                        "resistencia_viento": {
                            "type": ["string", "null"],
                            "maxLength": 50
                        },
                        "temperatura_operacion": {
                            "type": ["string", "null"],
                            "maxLength": 50
                        }
                    }
                },
                "camara": {
                    "type": "object",
                    "properties": {
                        "resolucion_video": {
                            "type": ["string", "null"],
                            "enum": ["4K", "6K", "8K", "1080p", "720p", None]
                        },
                        "fps_max": {
                            "type": ["number", "null"],
                            "minimum": 0,
                            "maximum": 240
                        },
                        "sensor_tamaño": {
                            "type": ["string", "null"],
                            "maxLength": 50
                        },
                        "estabilizacion": {
                            "type": ["string", "null"],
                            "enum": ["mecanica", "digital", "hibrida", None]
                        },
                        "zoom_optico": {
                            "type": ["number", "null"],
                            "minimum": 0,
                            "maximum": 100
                        },
                        "zoom_digital": {
                            "type": ["number", "null"],
                            "minimum": 0,
                            "maximum": 200
                        }
                    }
                },
                "caracteristicas_vuelo": {
                    "type": "object",
                    "properties": {
                        "evita_obstaculos": {"type": "boolean"},
                        "retorno_automatico": {"type": "boolean"},
                        "seguimiento_objeto": {"type": "boolean"},
                        "vuelo_nocturno": {"type": "boolean"},
                        "modo_sport": {"type": "boolean"},
                        "precision_hover": {
                            "type": ["string", "null"],
                            "maxLength": 50
                        }
                    }
                },
                "clasificacion": {
                    "type": "object",
                    "properties": {
                        "categoria_peso": {
                            "type": "string",
                            "enum": ["ultra_ligero", "ligero", "medio", "pesado"]
                        },
                        "nivel_usuario": {
                            "type": "string",
                            "enum": ["principiante", "intermedio", "avanzado", "profesional"]
                        },
                        "uso_principal": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["recreativo", "fotografia", "video_profesional", 
                                         "cinematografia", "inspeccion", "carreras", "agricultura"]
                            }
                        },
                        "certificaciones": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "metricas_calculadas": {
                    "type": "object",
                    "properties": {
                        "precio_por_minuto_vuelo": {
                            "type": ["number", "null"],
                            "minimum": 0
                        },
                        "ratio_peso_autonomia": {
                            "type": ["number", "null"],
                            "minimum": 0
                        },
                        "score_versatilidad": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 100
                        },
                        "indice_valor": {
                            "type": ["number", "null"],
                            "minimum": 0,
                            "maximum": 100
                        }
                    }
                },
                "metadata": {
                    "type": "object",
                    "properties": {
                        "fecha_extraccion": {
                            "type": "string",
                            "format": "date-time"
                        },
                        "version_scraper": {
                            "type": "string",
                            "pattern": "^\\d+\\.\\d+\\.\\d+$"
                        },
                        "confiabilidad_datos": {
                            "type": "string",
                            "enum": ["alta", "media", "baja"]
                        }
                    }
                }
            }
        }
    
    def validate_drone_data(self, drone_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validar datos de un drone individual
        
        Args:
            drone_data: Diccionario con datos del drone
        
        Returns:
            Tuple (es_válido, lista_de_errores)
        """
        self.validation_stats['total_validated'] += 1
        errors = []
        
        try:
            # Validación de esquema
            validate(instance=drone_data, schema=self.schema)
            
            # Validaciones adicionales de negocio
            business_errors = self._validate_business_rules(drone_data)
            
            if business_errors:
                errors.extend(business_errors)
            else:
                self.validation_stats['valid'] += 1
                return True, []
                
        except ValidationError as e:
            errors.append(f"Error de esquema: {e.message}")
            # Registrar tipo de error común
            error_type = e.schema_path[0] if e.schema_path else 'general'
            if error_type not in self.validation_stats['common_errors']:
                self.validation_stats['common_errors'][error_type] = 0
            self.validation_stats['common_errors'][error_type] += 1
            
        except Exception as e:
            errors.append(f"Error inesperado: {str(e)}")
        
        self.validation_stats['invalid'] += 1
        return False, errors
    
    def _validate_business_rules(self, drone_data: Dict) -> List[str]:
        """Validar reglas de negocio específicas"""
        errors = []
        
        # Validar consistencia precio/características
        if 'precio' in drone_data and drone_data['precio'].get('usd'):
            precio = drone_data['precio']['usd']
            specs = drone_data.get('especificaciones_tecnicas', {})
            
            # Drones muy baratos no deberían tener características premium
            if precio < 200:
                if specs.get('alcance_metros', 0) > 5000:
                    errors.append(f"Alcance inconsistente con precio bajo: {specs['alcance_metros']}m por ${precio}")
                
                camera = drone_data.get('camara', {})
                if camera.get('resolucion_video') in ['6K', '8K']:
                    errors.append(f"Resolución {camera['resolucion_video']} poco probable para precio ${precio}")
        
        # Validar coherencia de especificaciones
        specs = drone_data.get('especificaciones_tecnicas', {})
        
        # Relación peso/autonomía
        if specs.get('peso_gramos') and specs.get('autonomia_minutos'):
            peso = specs['peso_gramos']
            autonomia = specs['autonomia_minutos']
            
            # Drones más pesados generalmente tienen menos autonomía
            if peso > 2000 and autonomia > 45:
                errors.append(f"Autonomía sospechosamente alta ({autonomia}min) para peso {peso}g")
            
            # Drones ultra ligeros no deberían tener autonomía extrema
            if peso < 250 and autonomia > 30:
                errors.append(f"Autonomía poco probable ({autonomia}min) para drone ultra ligero {peso}g")
        
        # Validar clasificación vs especificaciones
        clasificacion = drone_data.get('clasificacion', {})
        
        if clasificacion.get('categoria_peso') == 'ultra_ligero':
            if specs.get('peso_gramos', 999) > 250:
                errors.append(f"Clasificación 'ultra_ligero' incorrecta para peso {specs.get('peso_gramos')}g")
        
        # Validar características de vuelo vs nivel de usuario
        if clasificacion.get('nivel_usuario') == 'principiante':
            vuelo = drone_data.get('caracteristicas_vuelo', {})
            features_avanzadas = sum([
                vuelo.get('evita_obstaculos', False),
                vuelo.get('seguimiento_objeto', False),
                vuelo.get('vuelo_nocturno', False)
            ])
            
            if features_avanzadas >= 3:
                errors.append("Demasiadas características avanzadas para nivel 'principiante'")
        
        return errors
    
    def validate_dataset(self, drones: List[Dict]) -> Dict[str, Any]:
        """
        Validar dataset completo
        
        Args:
            drones: Lista de drones
        
        Returns:
            Reporte de validación
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_drones': len(drones),
            'valid_drones': 0,
            'invalid_drones': 0,
            'validation_errors': [],
            'error_summary': {},
            'quality_metrics': {}
        }
        
        valid_drones = []
        
        for idx, drone in enumerate(drones):
            is_valid, errors = self.validate_drone_data(drone)
            
            if is_valid:
                valid_drones.append(drone)
                report['valid_drones'] += 1
            else:
                report['invalid_drones'] += 1
                report['validation_errors'].append({
                    'index': idx,
                    'modelo': drone.get('modelo', 'Unknown'),
                    'marca': drone.get('marca', 'Unknown'),
                    'errors': errors
                })
                
                # Agregar a resumen de errores
                for error in errors:
                    error_type = error.split(':')[0]
                    if error_type not in report['error_summary']:
                        report['error_summary'][error_type] = 0
                    report['error_summary'][error_type] += 1
        
        # Calcular métricas de calidad
        if valid_drones:
            report['quality_metrics'] = self._calculate_quality_metrics(valid_drones)
        
        return report
    
    def _calculate_quality_metrics(self, valid_drones: List[Dict]) -> Dict[str, Any]:
        """Calcular métricas de calidad del dataset"""
        metrics = {
            'completeness_scores': {},
            'data_distribution': {},
            'anomalies': []
        }
        
        # Calcular completitud por campo
        field_counts = {}
        
        for drone in valid_drones:
            for key, value in self._flatten_dict(drone).items():
                if key not in field_counts:
                    field_counts[key] = {'total': 0, 'non_null': 0}
                
                field_counts[key]['total'] += 1
                if value is not None and value != '':
                    field_counts[key]['non_null'] += 1
        
        # Calcular porcentajes de completitud
        for field, counts in field_counts.items():
            completeness = (counts['non_null'] / counts['total']) * 100
            metrics['completeness_scores'][field] = round(completeness, 2)
        
        # Distribución de datos por marca
        brand_dist = {}
        for drone in valid_drones:
            marca = drone.get('marca', 'Unknown')
            if marca not in brand_dist:
                brand_dist[marca] = 0
            brand_dist[marca] += 1
        
        metrics['data_distribution']['by_brand'] = brand_dist
        
        # Distribución por categoría de peso
        weight_dist = {}
        for drone in valid_drones:
            categoria = drone.get('clasificacion', {}).get('categoria_peso', 'Unknown')
            if categoria not in weight_dist:
                weight_dist[categoria] = 0
            weight_dist[categoria] += 1
        
        metrics['data_distribution']['by_weight_category'] = weight_dist
        
        # Detectar anomalías básicas
        precios = [d['precio']['usd'] for d in valid_drones 
                   if d.get('precio', {}).get('usd') is not None]
        
        if precios:
            avg_price = sum(precios) / len(precios)
            std_price = (sum((p - avg_price) ** 2 for p in precios) / len(precios)) ** 0.5
            
            # Detectar precios anómalos (fuera de 3 desviaciones estándar)
            for drone in valid_drones:
                precio = drone.get('precio', {}).get('usd')
                if precio is not None:
                    if abs(precio - avg_price) > 3 * std_price:
                        metrics['anomalies'].append({
                            'tipo': 'precio_anomalo',
                            'modelo': drone.get('modelo'),
                            'valor': precio,
                            'promedio': round(avg_price, 2),
                            'desviacion': round(std_price, 2)
                        })
        
        return metrics
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """Aplanar diccionario anidado"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def fix_common_issues(self, drone_data: Dict) -> Dict:
        """
        Intentar corregir problemas comunes automáticamente
        
        Args:
            drone_data: Datos del drone con posibles problemas
        
        Returns:
            Datos corregidos
        """
        fixed_data = drone_data.copy()
        
        # Asegurar campos requeridos
        if 'especificaciones_tecnicas' not in fixed_data:
            fixed_data['especificaciones_tecnicas'] = {
                'peso_gramos': None,
                'autonomia_minutos': None,
                'alcance_metros': None
            }
        
        # Asegurar clasificación
        if 'clasificacion' not in fixed_data:
            fixed_data['clasificacion'] = self._auto_classify(fixed_data)
        
        # Corregir tipos de datos
        if 'precio' in fixed_data and isinstance(fixed_data['precio'], (int, float)):
            fixed_data['precio'] = {
                'usd': float(fixed_data['precio']),
                'moneda_local': None,
                'fecha_precio': datetime.now().strftime('%Y-%m-%d')
            }
        
        # Normalizar booleanos en características de vuelo
        if 'caracteristicas_vuelo' in fixed_data:
            for key in ['evita_obstaculos', 'retorno_automatico', 'seguimiento_objeto', 
                       'vuelo_nocturno', 'modo_sport']:
                if key in fixed_data['caracteristicas_vuelo']:
                    value = fixed_data['caracteristicas_vuelo'][key]
                    if isinstance(value, str):
                        fixed_data['caracteristicas_vuelo'][key] = value.lower() in ['true', 'yes', 'si', '1']
        
        # Agregar metadata si falta
        if 'metadata' not in fixed_data:
            fixed_data['metadata'] = {
                'fecha_extraccion': datetime.now().isoformat(),
                'version_scraper': '1.0.0',
                'confiabilidad_datos': 'media'
            }
        
        return fixed_data
    
    def _auto_classify(self, drone_data: Dict) -> Dict:
        """Clasificación automática basada en características"""
        classification = {
            'categoria_peso': 'medio',
            'nivel_usuario': 'intermedio',
            'uso_principal': [],
            'certificaciones': []
        }
        
        specs = drone_data.get('especificaciones_tecnicas', {})
        peso = specs.get('peso_gramos', 0)
        
        # Categoría por peso
        if peso and peso < 250:
            classification['categoria_peso'] = 'ultra_ligero'
            classification['nivel_usuario'] = 'principiante'
            classification['uso_principal'] = ['recreativo']
        elif peso and peso < 500:
            classification['categoria_peso'] = 'ligero'
            classification['uso_principal'] = ['recreativo', 'fotografia']
        elif peso and peso < 1000:
            classification['categoria_peso'] = 'medio'
            classification['uso_principal'] = ['fotografia', 'video_profesional']
        else:
            classification['categoria_peso'] = 'pesado'
            classification['nivel_usuario'] = 'profesional'
            classification['uso_principal'] = ['cinematografia', 'inspeccion']
        
        # Ajustar por características de cámara
        camera = drone_data.get('camara', {})
        if camera.get('resolucion_video') in ['4K', '6K', '8K']:
            if 'fotografia' not in classification['uso_principal']:
                classification['uso_principal'].append('fotografia')
            if camera.get('resolucion_video') in ['6K', '8K']:
                classification['nivel_usuario'] = 'profesional'
        
        # Ajustar por características de vuelo
        flight = drone_data.get('caracteristicas_vuelo', {})
        advanced_features = sum([
            flight.get('evita_obstaculos', False),
            flight.get('seguimiento_objeto', False),
            flight.get('vuelo_nocturno', False)
        ])
        
        if advanced_features >= 2:
            if classification['nivel_usuario'] == 'principiante':
                classification['nivel_usuario'] = 'intermedio'
        
        return classification
    
    def generate_validation_report(self, dataset: List[Dict]) -> str:
        """
        Generar reporte de validación en formato legible
        
        Args:
            dataset: Dataset a validar
        
        Returns:
            Reporte en formato markdown
        """
        validation_result = self.validate_dataset(dataset)
        
        report = f"""# Reporte de Validación de Datos - Drones

## Resumen Ejecutivo
- **Fecha**: {validation_result['timestamp']}
- **Total de registros**: {validation_result['total_drones']}
- **Registros válidos**: {validation_result['valid_drones']} ({validation_result['valid_drones']/validation_result['total_drones']*100:.1f}%)
- **Registros inválidos**: {validation_result['invalid_drones']} ({validation_result['invalid_drones']/validation_result['total_drones']*100:.1f}%)

## Errores Más Comunes
"""
        
        if validation_result['error_summary']:
            for error_type, count in sorted(validation_result['error_summary'].items(), 
                                          key=lambda x: x[1], reverse=True):
                report += f"- {error_type}: {count} ocurrencias\n"
        else:
            report += "No se encontraron errores.\n"
        
        report += "\n## Métricas de Calidad\n"
        
        if 'quality_metrics' in validation_result and validation_result['quality_metrics']:
            metrics = validation_result['quality_metrics']
            
            # Completitud de campos
            report += "\n### Completitud de Campos (Top 10 más completos)\n"
            completeness = metrics.get('completeness_scores', {})
            for field, score in sorted(completeness.items(), key=lambda x: x[1], reverse=True)[:10]:
                report += f"- {field}: {score}%\n"
            
            # Distribución
            report += "\n### Distribución de Datos\n"
            if 'by_brand' in metrics.get('data_distribution', {}):
                report += "\n**Por Marca:**\n"
                for brand, count in metrics['data_distribution']['by_brand'].items():
                    report += f"- {brand}: {count} drones\n"
            
            if 'by_weight_category' in metrics.get('data_distribution', {}):
                report += "\n**Por Categoría de Peso:**\n"
                for category, count in metrics['data_distribution']['by_weight_category'].items():
                    report += f"- {category}: {count} drones\n"
            
            # Anomalías
            if metrics.get('anomalies'):
                report += "\n### Anomalías Detectadas\n"
                for anomaly in metrics['anomalies']:
                    report += f"- {anomaly['tipo']}: {anomaly['modelo']} (valor: {anomaly['valor']})\n"
        
        # Detalles de errores
        if validation_result['validation_errors']:
            report += "\n## Detalles de Errores de Validación (primeros 10)\n"
            for error in validation_result['validation_errors'][:10]:
                report += f"\n### {error['marca']} - {error['modelo']}\n"
                for err_msg in error['errors']:
                    report += f"- {err_msg}\n"
        
        report += "\n## Estadísticas del Validador\n"
        report += f"- Total validado en esta sesión: {self.validation_stats['total_validated']}\n"
        report += f"- Válidos: {self.validation_stats['valid']}\n"
        report += f"- Inválidos: {self.validation_stats['invalid']}\n"
        
        if self.validation_stats['common_errors']:
            report += "\n### Tipos de Errores Más Comunes\n"
            for error_type, count in sorted(self.validation_stats['common_errors'].items(), 
                                          key=lambda x: x[1], reverse=True):
                report += f"- {error_type}: {count} veces\n"
        
        return report


if __name__ == "__main__":
    # Prueba del validador
    validator = DataValidator()
    
    # Ejemplo de drone válido
    valid_drone = {
        "modelo": "DJI Air 3",
        "marca": "DJI",
        "url_fuente": "https://www.dji.com/air-3",
        "precio": {
            "usd": 1099.0,
            "moneda_local": None,
            "fecha_precio": "2024-01-20"
        },
        "especificaciones_tecnicas": {
            "peso_gramos": 720,
            "autonomia_minutos": 46,
            "alcance_metros": 10000,
            "velocidad_max_kmh": 68.4,
            "resistencia_viento": "12 m/s",
            "temperatura_operacion": "-10°C a 40°C"
        },
        "camara": {
            "resolucion_video": "4K",
            "fps_max": 60,
            "sensor_tamaño": "1/1.3 inch CMOS",
            "estabilizacion": "mecanica",
            "zoom_optico": 3,
            "zoom_digital": 9
        },
        "caracteristicas_vuelo": {
            "evita_obstaculos": True,
            "retorno_automatico": True,
            "seguimiento_objeto": True,
            "vuelo_nocturno": False,
            "modo_sport": True,
            "precision_hover": "GPS+GLONASS+Galileo"
        },
        "clasificacion": {
            "categoria_peso": "medio",
            "nivel_usuario": "avanzado",
            "uso_principal": ["fotografia", "video_profesional"],
            "certificaciones": ["CE", "FCC"]
        },
        "metadata": {
            "fecha_extraccion": "2024-01-20T10:30:00Z",
            "version_scraper": "1.0.0",
            "confiabilidad_datos": "alta"
        }
    }
    
    # Validar
    is_valid, errors = validator.validate_drone_data(valid_drone)
    print(f"Drone válido: {is_valid}")
    if errors:
        print("Errores:", errors)
    
    # Ejemplo con errores
    invalid_drone = {
        "modelo": "Test Drone",
        "marca": "InvalidBrand",  # Marca no válida
        "especificaciones_tecnicas": {
            "peso_gramos": -100,  # Peso negativo
            "autonomia_minutos": 200,  # Autonomía excesiva
            "alcance_metros": None  # Campo requerido faltante
        }
    }
    
    is_valid, errors = validator.validate_drone_data(invalid_drone)
    print(f"\nDrone inválido: {is_valid}")
    print("Errores:", errors)

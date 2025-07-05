"""
Normalizador avanzado de datos de drones para presentación web.
Limpia, estandariza y enriquece los datos scrapeados.
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DroneDataNormalizer:
    """Clase para normalizar y limpiar datos de drones."""
    
    def __init__(self):
        self.normalized_count = 0
        self.issues_found = []
        
    def normalize_all_drones(self, drones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normaliza una lista completa de drones."""
        logger.info(f"Iniciando normalización de {len(drones)} drones...")
        
        normalized_drones = []
        for drone in drones:
            try:
                normalized = self.normalize_drone(drone)
                if normalized:
                    normalized_drones.append(normalized)
                    self.normalized_count += 1
            except Exception as e:
                logger.error(f"Error normalizando drone {drone.get('modelo', 'Unknown')}: {e}")
                self.issues_found.append({
                    'drone': drone.get('modelo', 'Unknown'),
                    'error': str(e)
                })
        
        logger.info(f"Normalización completada: {self.normalized_count}/{len(drones)} drones procesados")
        return normalized_drones
    
    def normalize_drone(self, drone_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza los datos de un drone individual."""
        # Crear estructura base consistente
        normalized = {
            'modelo': self._normalize_model_name(drone_data.get('modelo', '')),
            'marca': self._normalize_brand(drone_data.get('marca', '')),
            'url_fuente': drone_data.get('url_fuente') or drone_data.get('url', ''),
            'imagen': self._get_drone_image(drone_data),
            'categoria': self._categorize_drone(drone_data),
            'fecha_actualizacion': datetime.now().isoformat(),
            'especificaciones_tecnicas': self._normalize_specifications(
                drone_data.get('especificaciones_tecnicas', {})
            ),
            'precio_usd': self._extract_price(drone_data),
            'disponibilidad': 'Disponible',  # Por defecto
            'puntuacion_general': self._calculate_score(drone_data)
        }
        
        return normalized
    
    def _normalize_model_name(self, model: str) -> str:
        """Normaliza el nombre del modelo."""
        if not model or model.lower() in ['unknown', 'specs', '']:
            return "Modelo Desconocido"
        
        # Limpiar nombre
        model = re.sub(r'\s+', ' ', model.strip())
        model = re.sub(r'(series|Series|SERIES)$', 'Series', model)
        
        # Estandarizar nombres conocidos
        replacements = {
            'EVO II': 'Evo II',
            'EVO Max': 'Evo Max',
            'EVO Lite': 'Evo Lite',
            'ANAFI': 'Anafi',
            'DJI ': '',  # Remover prefijo DJI redundante
        }
        
        for old, new in replacements.items():
            model = model.replace(old, new)
        
        return model.strip()
    
    def _normalize_brand(self, brand: str) -> str:
        """Normaliza el nombre de la marca."""
        brand_map = {
            'dji': 'DJI',
            'autel': 'Autel',
            'parrot': 'Parrot'
        }
        return brand_map.get(brand.lower(), brand.title())
    
    def _get_drone_image(self, drone_data: Dict[str, Any]) -> str:
        """Obtiene la ruta de imagen para el drone."""
        model = drone_data.get('modelo', '').lower()
        
        # Mapeo de modelos a imágenes
        image_map = {
            'mavic 3 pro': 'Mavic 3 Pro.jpeg',
            'mavic 3 classic': 'Mavic 3 Classic.jpg',
            'air 3s': 'Air 3S.jpg',
            'air 3': 'Air 3.jpg',
            'mini 4 pro': 'Mini 4 Pro.jpg',
            'mini 3': 'Mini 3.jpeg',
            'avata 2': 'Avata 2.jpg',
            'inspire 3': 'Inspire 3.jpg',
            'evo lite enterprise': 'EVO Lite Enterprise.jpg',
            'alpha': 'Alpha.jpg',
            'evo max 4t': 'EVO-Max-4T.jpg',
            'evo ii enterprise': 'EVO II Enterprise.jpg',
            'evo ii dual': 'EVO II Dual 640t.jpg',
            'evo ii pro': 'EVO II PRO.jpg',
            'dragonfish': 'Dragonfish.jpg',
            'anafi ai': 'ANAFI-AI.jpg',
            'anafi usa': 'Anafi-USA.jpg'
        }
        
        # Buscar coincidencia
        for key, value in image_map.items():
            if key in model:
                return f"data/images/{value}"
        
        # Imagen por defecto según marca
        brand = drone_data.get('marca', '').lower()
        return f"data/images/{brand}-logo.png"
    
    def _categorize_drone(self, drone_data: Dict[str, Any]) -> str:
        """Categoriza el drone según sus características."""
        specs = drone_data.get('especificaciones_tecnicas', {})
        peso = specs.get('peso_gramos', 0)
        modelo = drone_data.get('modelo', '').lower()
        
        # Categorización por peso y características
        if peso < 250:
            return "Mini / Recreativo"
        elif peso < 1000:
            if any(word in modelo for word in ['pro', 'classic', 'enterprise']):
                return "Prosumer"
            return "Consumer"
        elif peso < 2000:
            if 'enterprise' in modelo or 'dual' in modelo:
                return "Enterprise"
            return "Profesional"
        else:
            return "Industrial"
    
    def _normalize_specifications(self, specs: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza todas las especificaciones técnicas."""
        normalized_specs = {}
        
        # Peso
        peso = specs.get('peso_gramos', 0)
        normalized_specs['peso_gramos'] = peso if peso > 0 else None
        
        # Dimensiones
        dims = specs.get('dimensiones_plegado', '')
        normalized_specs['dimensiones_plegado'] = self._normalize_dimensions(dims)
        
        # Tiempo de vuelo
        vuelo = specs.get('vuelo_minutos', 0)
        normalized_specs['vuelo_minutos'] = vuelo if vuelo > 0 else None
        
        # Velocidades
        vel_h = specs.get('vel_horizontal_mps', 0)
        normalized_specs['vel_horizontal_mps'] = vel_h if vel_h > 0 else None
        
        vel_a = specs.get('vel_ascenso_mps', 0)
        normalized_specs['vel_ascenso_mps'] = vel_a if vel_a > 0 else None
        
        # Alcance
        alcance = specs.get('alcance_video_km', 0)
        normalized_specs['alcance_video_km'] = alcance if alcance > 0 else None
        
        # Altitud
        altitud = specs.get('altitud_despegue_m', 0)
        normalized_specs['altitud_despegue_m'] = altitud if altitud > 0 else None
        
        # Resistencia al viento
        viento = specs.get('resistencia_viento_mps', 0)
        normalized_specs['resistencia_viento_mps'] = viento if viento > 0 else None
        
        # Almacenamiento
        storage = specs.get('almacenamiento_interno_gb')
        normalized_specs['almacenamiento_interno_gb'] = storage if storage and storage > 0 else None
        
        # Cámara
        normalized_specs['sensor_camara'] = self._normalize_camera_sensor(
            specs.get('sensor_camara', '')
        )
        
        # Resolución de video
        normalized_specs['resolucion_video'] = self._normalize_video_resolution(
            specs.get('resolucion_video', '')
        )
        
        # Detección de obstáculos
        normalized_specs['deteccion_obstaculos'] = bool(specs.get('deteccion_obstaculos', False))
        
        # Características adicionales derivadas
        normalized_specs['caracteristicas_destacadas'] = self._extract_key_features(specs)
        
        return normalized_specs
    
    def _normalize_dimensions(self, dims: str) -> Optional[str]:
        """Normaliza las dimensiones."""
        if not dims or dims == "":
            return None
        
        # Limpiar texto extra
        dims = re.sub(r'\s*\(.*?\)', '', dims)  # Remover paréntesis
        dims = re.sub(r'mm\s*', '', dims)  # Remover mm
        dims = dims.strip()
        
        # Buscar patrón de 3 números
        pattern = r'(\d+(?:\.\d+)?)\s*[×x]\s*(\d+(?:\.\d+)?)\s*[×x]\s*(\d+(?:\.\d+)?)'
        match = re.search(pattern, dims)
        
        if match:
            l, w, h = match.groups()
            return f"{l}×{w}×{h} mm"
        
        # Si no hay match pero hay texto, devolver limpio
        if len(dims) > 5:
            return dims
        
        return None
    
    def _normalize_camera_sensor(self, sensor: str) -> str:
        """Normaliza la descripción del sensor de cámara."""
        if not sensor or sensor == "":
            return "No especificado"
        
        # Limpiar texto largo
        sensor = re.sub(r'\s+', ' ', sensor)
        
        # Extraer información clave
        key_info = []
        
        # Tamaño del sensor
        sensor_size = re.search(r'(1/\d+(?:\.\d+)?["\']?|1["\']?|\d+/\d+["\']?)\s*(inch|pulgada|CMOS)?', sensor, re.I)
        if sensor_size:
            key_info.append(sensor_size.group(0).strip())
        
        # Megapíxeles
        mp = re.search(r'(\d+)\s*MP', sensor, re.I)
        if mp:
            key_info.append(f"{mp.group(1)} MP")
        elif 'million pixel' in sensor.lower():
            mp2 = re.search(r'(\d+)\s*million', sensor, re.I)
            if mp2:
                key_info.append(f"{mp2.group(1)} MP")
        
        # Tipo de sensor
        if 'hasselblad' in sensor.lower():
            key_info.insert(0, "Hasselblad")
        elif 'cmos' in sensor.upper() and 'CMOS' not in ' '.join(key_info):
            key_info.append("CMOS")
        
        # Si tenemos info clave, usarla
        if key_info:
            return ' '.join(key_info[:3])  # Máximo 3 elementos
        
        # Si es muy largo, truncar
        if len(sensor) > 50:
            return sensor[:50] + "..."
        
        return sensor
    
    def _normalize_video_resolution(self, resolution: str) -> str:
        """Normaliza la resolución de video."""
        if not resolution or resolution == "":
            return "No especificado"
        
        # Limpiar
        resolution = re.sub(r'\s+', ' ', resolution)
        
        # Extraer resoluciones principales
        resolutions = []
        
        # Buscar patrones de resolución
        patterns = [
            r'(\d+)K',  # 4K, 6K, 8K
            r'(\d{3,4})p',  # 1080p, 2160p
            r'(\d{3,4})\s*[×x]\s*(\d{3,4})',  # 3840×2160
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, resolution, re.I)
            for match in matches:
                if isinstance(match, tuple):
                    resolutions.append(f"{match[0]}×{match[1]}")
                else:
                    if 'K' in pattern:
                        resolutions.append(f"{match}K")
                    else:
                        resolutions.append(f"{match}p")
        
        # Si encontramos resoluciones, devolver las principales
        if resolutions:
            # Priorizar y limpiar
            priority_order = ['8K', '6K', '5K', '4K', '2160p', '1080p']
            sorted_res = []
            for priority in priority_order:
                for res in resolutions:
                    if priority in res and res not in sorted_res:
                        sorted_res.append(res)
            
            return ' / '.join(sorted_res[:3])  # Máximo 3
        
        # Si es muy largo, extraer lo esencial
        if len(resolution) > 30:
            # Buscar primera resolución mencionada
            first_res = re.search(r'\d+[Kp]|\d+×\d+', resolution)
            if first_res:
                return first_res.group(0)
        
        return resolution if len(resolution) < 50 else resolution[:50] + "..."
    
    def _extract_key_features(self, specs: Dict[str, Any]) -> List[str]:
        """Extrae las características más destacadas del drone."""
        features = []
        
        # Tiempo de vuelo destacado
        vuelo = specs.get('vuelo_minutos', 0)
        if vuelo >= 40:
            features.append(f"Hasta {int(vuelo)} min de vuelo")
        
        # Alcance destacado
        alcance = specs.get('alcance_video_km', 0)
        if alcance >= 10:
            features.append(f"Alcance {int(alcance)} km")
        
        # Cámara de alta resolución
        camera = specs.get('sensor_camara', '').lower()
        video = specs.get('resolucion_video', '').lower()
        if '8k' in video:
            features.append("Video 8K")
        elif '6k' in video:
            features.append("Video 6K")
        elif '4k' in video:
            features.append("Video 4K")
        
        if 'hasselblad' in camera:
            features.append("Cámara Hasselblad")
        elif '48 mp' in camera or '50 mp' in camera:
            features.append("Cámara 48+ MP")
        
        # Detección de obstáculos
        if specs.get('deteccion_obstaculos'):
            features.append("Evitación de obstáculos")
        
        # Peso ultraligero
        peso = specs.get('peso_gramos', 0)
        if 0 < peso < 250:
            features.append("Ultraligero (<250g)")
        
        return features[:4]  # Máximo 4 características
    
    def _extract_price(self, drone_data: Dict[str, Any]) -> Optional[float]:
        """Extrae o estima el precio del drone."""
        # Por ahora retornar None, esto podría conectarse con una base de datos de precios
        return None
    
    def _calculate_score(self, drone_data: Dict[str, Any]) -> float:
        """Calcula una puntuación general basada en las especificaciones."""
        specs = drone_data.get('especificaciones_tecnicas', {})
        score = 5.0  # Base
        
        # Factores positivos
        if specs.get('vuelo_minutos', 0) > 30:
            score += 1.0
        if specs.get('alcance_video_km', 0) > 5:
            score += 0.5
        if specs.get('deteccion_obstaculos'):
            score += 1.0
        if '4k' in str(specs.get('resolucion_video', '')).lower():
            score += 0.5
        if specs.get('peso_gramos', 1000) < 250:
            score += 0.5  # Bonus por ser ultraligero
        
        # Limitar entre 0 y 10
        return min(10.0, max(0.0, score))
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen del proceso de normalización."""
        return {
            'total_normalized': self.normalized_count,
            'issues_found': len(self.issues_found),
            'issues_detail': self.issues_found
        }


def main():
    """Función principal para normalizar los datos."""
    # Rutas
    input_file = Path("data/processed/drones_normalized.json")
    output_file = Path("data/processed/drones_web_ready.json")
    
    # Cargar datos originales
    logger.info(f"Cargando datos desde {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        drones = json.load(f)
    
    # Normalizar
    normalizer = DroneDataNormalizer()
    normalized_drones = normalizer.normalize_all_drones(drones)
    
    # Guardar resultado
    logger.info(f"Guardando datos normalizados en {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(normalized_drones, f, indent=2, ensure_ascii=False)
    
    # Mostrar resumen
    summary = normalizer.get_summary()
    logger.info(f"Resumen: {summary['total_normalized']} drones normalizados, {summary['issues_found']} problemas encontrados")
    
    if summary['issues_found'] > 0:
        logger.warning("Problemas encontrados durante la normalización:")
        for issue in summary['issues_detail']:
            logger.warning(f"  - {issue['drone']}: {issue['error']}")
    
    # Estadísticas adicionales
    logger.info("\nEstadísticas de los datos normalizados:")
    
    marcas = {}
    categorias = {}
    
    for drone in normalized_drones:
        # Por marca
        marca = drone['marca']
        marcas[marca] = marcas.get(marca, 0) + 1
        
        # Por categoría
        categoria = drone['categoria']
        categorias[categoria] = categorias.get(categoria, 0) + 1
    
    logger.info("Drones por marca:")
    for marca, count in sorted(marcas.items()):
        logger.info(f"  - {marca}: {count}")
    
    logger.info("\nDrones por categoría:")
    for categoria, count in sorted(categorias.items()):
        logger.info(f"  - {categoria}: {count}")


if __name__ == "__main__":
    main() 
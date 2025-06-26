#Ranking Engine - Sistema de scoring y recomendaciones para drones
#Genera rankings personalizados según criterios específicos


import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
from enum import Enum

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class UseCase(Enum):
    """Casos de uso predefinidos"""
    BEGINNER_RECREATIONAL = "beginner_recreational"
    PHOTOGRAPHY_ENTHUSIAST = "photography_enthusiast"
    PROFESSIONAL_VIDEO = "professional_video"
    INDUSTRIAL_INSPECTION = "industrial_inspection"
    RACING_SPORTS = "racing_sports"
    TRAVEL_VLOGGER = "travel_vlogger"
    REAL_ESTATE = "real_estate"
    AGRICULTURE = "agriculture"


class DroneRankingEngine:
    """Motor de ranking y recomendaciones para drones"""
    
    def __init__(self):
        self.drones_df = None
        self.ranking_weights = self._initialize_ranking_weights()
        self.use_case_profiles = self._initialize_use_case_profiles()
    
    def _initialize_ranking_weights(self) -> Dict[str, Dict[str, float]]:
        """Inicializar pesos para diferentes criterios de ranking"""
        return {
            'versatility': {
                'features': 0.30,
                'camera_quality': 0.25,
                'flight_performance': 0.20,
                'portability': 0.15,
                'value': 0.10
            },
            'performance': {
                'speed': 0.25,
                'range': 0.25,
                'autonomy': 0.20,
                'wind_resistance': 0.15,
                'camera_quality': 0.15
            },
            'value': {
                'price': 0.40,
                'features': 0.25,
                'performance': 0.20,
                'durability': 0.15
            },
            'professional': {
                'camera_quality': 0.35,
                'stability': 0.25,
                'range': 0.20,
                'features': 0.20
            }
        }
    
    def _initialize_use_case_profiles(self) -> Dict[UseCase, Dict]:
        """Definir perfiles para cada caso de uso"""
        return {
            UseCase.BEGINNER_RECREATIONAL: {
                'name': 'Principiante Recreativo',
                'budget_range': (100, 500),
                'required_features': ['retorno_automatico'],
                'nice_to_have': ['evita_obstaculos', 'modo_sport'],
                'weights': {
                    'ease_of_use': 0.35,
                    'price': 0.30,
                    'safety': 0.20,
                    'fun_factor': 0.15
                },
                'min_autonomy': 15,
                'max_weight': 500
            },
            UseCase.PHOTOGRAPHY_ENTHUSIAST: {
                'name': 'Entusiasta de Fotografía',
                'budget_range': (500, 2000),
                'required_features': ['evita_obstaculos'],
                'nice_to_have': ['seguimiento_objeto', 'vuelo_nocturno'],
                'weights': {
                    'camera_quality': 0.40,
                    'stability': 0.25,
                    'autonomy': 0.20,
                    'portability': 0.15
                },
                'min_camera': '4K',
                'min_autonomy': 25
            },
            UseCase.PROFESSIONAL_VIDEO: {
                'name': 'Video Profesional',
                'budget_range': (2000, 10000),
                'required_features': ['evita_obstaculos', 'seguimiento_objeto'],
                'nice_to_have': ['vuelo_nocturno', 'modo_sport'],
                'weights': {
                    'camera_quality': 0.45,
                    'stability': 0.30,
                    'range': 0.15,
                    'features': 0.10
                },
                'min_camera': '4K',
                'preferred_camera': ['6K', '8K'],
                'min_autonomy': 30
            },
            UseCase.INDUSTRIAL_INSPECTION: {
                'name': 'Inspección Industrial',
                'budget_range': (3000, 15000),
                'required_features': ['evita_obstaculos', 'retorno_automatico'],
                'nice_to_have': ['vuelo_nocturno'],
                'weights': {
                    'reliability': 0.30,
                    'range': 0.25,
                    'autonomy': 0.25,
                    'camera_zoom': 0.20
                },
                'min_autonomy': 35,
                'min_range': 5000
            },
            UseCase.RACING_SPORTS: {
                'name': 'Carreras y Deportes',
                'budget_range': (300, 1500),
                'required_features': ['modo_sport'],
                'nice_to_have': [],
                'weights': {
                    'speed': 0.40,
                    'agility': 0.30,
                    'durability': 0.20,
                    'price': 0.10
                },
                'min_speed': 70,
                'max_weight': 500
            },
            UseCase.TRAVEL_VLOGGER: {
                'name': 'Travel Vlogger',
                'budget_range': (800, 2500),
                'required_features': ['evita_obstaculos', 'seguimiento_objeto'],
                'nice_to_have': ['vuelo_nocturno'],
                'weights': {
                    'portability': 0.30,
                    'camera_quality': 0.30,
                    'ease_of_use': 0.20,
                    'autonomy': 0.20
                },
                'max_weight': 700,
                'min_camera': '4K'
            },
            UseCase.REAL_ESTATE: {
                'name': 'Inmobiliaria',
                'budget_range': (1000, 3000),
                'required_features': ['evita_obstaculos'],
                'nice_to_have': ['seguimiento_objeto'],
                'weights': {
                    'camera_quality': 0.35,
                    'stability': 0.30,
                    'ease_of_use': 0.20,
                    'autonomy': 0.15
                },
                'min_camera': '4K',
                'min_autonomy': 20
            },
            UseCase.AGRICULTURE: {
                'name': 'Agricultura',
                'budget_range': (2000, 20000),
                'required_features': ['retorno_automatico'],
                'nice_to_have': ['evita_obstaculos'],
                'weights': {
                    'autonomy': 0.35,
                    'range': 0.30,
                    'payload': 0.20,
                    'durability': 0.15
                },
                'min_autonomy': 30,
                'min_range': 5000,
                'category': 'pesado'
            }
        }
    
    def load_data(self, data_path: str = '../data/processed/unified_drones.json'):
        """Cargar datos de drones"""
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                drones_data = json.load(f)
            
            self.drones_df = pd.json_normalize(drones_data)
            self.drones_df.columns = [col.replace('.', '_') for col in self.drones_df.columns]
            
            logger.info(f"Cargados {len(self.drones_df)} drones para ranking")
            
        except Exception as e:
            logger.error(f"Error cargando datos: {str(e)}")
            raise
    
    def calculate_versatility_score(self, features: Dict) -> float:
        """
        Calcular score de versatilidad (0-100)
        
        Args:
            features: Diccionario con características del drone
        
        Returns:
            Score de versatilidad
        """
        score = 0
        max_score = 0
        
        # Características y sus pesos
        feature_weights = {
            'evita_obstaculos': 20,
            'retorno_automatico': 15,
            'seguimiento_objeto': 20,
            'vuelo_nocturno': 15,
            'modo_sport': 10,
            'camara_4k_plus': 20
        }
        
        # Evaluar características de vuelo
        for feature, weight in feature_weights.items():
            max_score += weight
            
            if feature == 'camara_4k_plus':
                # Verificar calidad de cámara
                if features.get('camara_resolucion') in ['4K', '6K', '8K']:
                    score += weight
            else:
                # Verificar otras características
                if features.get(feature, False):
                    score += weight
        
        # Bonus por características adicionales
        if features.get('gimbal_estabilizacion') == 'mecanica':
            score += 5
        
        if features.get('zoom_optico', 0) > 2:
            score += 5
        
        # Normalizar a 0-100
        versatility_score = (score / max_score) * 100 if max_score > 0 else 0
        
        return round(versatility_score, 2)
    
    def rank_by_use_case(self, use_case: UseCase) -> pd.DataFrame:
        """
        Rankear drones según caso de uso específico
        
        Args:
            use_case: Caso de uso del enum UseCase
        
        Returns:
            DataFrame con drones rankeados
        """
        profile = self.use_case_profiles[use_case]
        candidates = self.drones_df.copy()
        
        # Filtrar por presupuesto
        if 'precio_usd' in candidates.columns:
            budget_min, budget_max = profile['budget_range']
            candidates = candidates[
                (candidates['precio_usd'] >= budget_min) & 
                (candidates['precio_usd'] <= budget_max)
            ]
        
        # Filtrar por características requeridas
        for feature in profile['required_features']:
            feature_col = f'caracteristicas_vuelo_{feature}'
            if feature_col in candidates.columns:
                candidates = candidates[candidates[feature_col] == True]
        
        # Filtros específicos del perfil
        if 'min_autonomy' in profile:
            candidates = candidates[
                candidates['especificaciones_tecnicas_autonomia_minutos'] >= profile['min_autonomy']
            ]
        
        if 'max_weight' in profile:
            candidates = candidates[
                candidates['especificaciones_tecnicas_peso_gramos'] <= profile['max_weight']
            ]
        
        if 'min_camera' in profile:
            camera_priority = {'8K': 4, '6K': 3, '4K': 2, '1080p': 1, '720p': 0}
            min_priority = camera_priority.get(profile['min_camera'], 0)
            
            candidates['camera_priority'] = candidates['camara_resolucion_video'].map(camera_priority).fillna(0)
            candidates = candidates[candidates['camera_priority'] >= min_priority]
        
        if 'min_speed' in profile:
            candidates = candidates[
                candidates['especificaciones_tecnicas_velocidad_max_kmh'] >= profile['min_speed']
            ]
        
        if 'min_range' in profile:
            candidates = candidates[
                candidates['especificaciones_tecnicas_alcance_metros'] >= profile['min_range']
            ]
        
        if 'category' in profile:
            candidates = candidates[
                candidates['clasificacion_categoria_peso'] == profile['category']
            ]
        
        # Calcular score basado en pesos del perfil
        candidates[f'{use_case.value}_score'] = 0
        
        for criterion, weight in profile['weights'].items():
            if criterion == 'camera_quality':
                camera_scores = {'8K': 1.0, '6K': 0.85, '4K': 0.7, '1080p': 0.4, '720p': 0.2}
                candidates[f'{use_case.value}_score'] += weight * candidates['camara_resolucion_video'].map(camera_scores).fillna(0)
            
            elif criterion == 'price':
                # Menor precio es mejor
                if candidates['precio_usd'].max() > 0:
                    candidates[f'{use_case.value}_score'] += weight * (1 - candidates['precio_usd'] / candidates['precio_usd'].max())
            
            elif criterion == 'autonomy':
                if 'especificaciones_tecnicas_autonomia_minutos' in candidates.columns:
                    max_autonomy = candidates['especificaciones_tecnicas_autonomia_minutos'].max()
                    if max_autonomy > 0:
                        candidates[f'{use_case.value}_score'] += weight * (candidates['especificaciones_tecnicas_autonomia_minutos'] / max_autonomy)
            
            elif criterion == 'range':
                if 'especificaciones_tecnicas_alcance_metros' in candidates.columns:
                    max_range = candidates['especificaciones_tecnicas_alcance_metros'].max()
                    if max_range > 0:
                        candidates[f'{use_case.value}_score'] += weight * (candidates['especificaciones_tecnicas_alcance_metros'] / max_range)
            
            elif criterion == 'speed':
                if 'especificaciones_tecnicas_velocidad_max_kmh' in candidates.columns:
                    max_speed = candidates['especificaciones_tecnicas_velocidad_max_kmh'].max()
                    if max_speed > 0:
                        candidates[f'{use_case.value}_score'] += weight * (candidates['especificaciones_tecnicas_velocidad_max_kmh'] / max_speed)
            
            elif criterion == 'portability':
                # Menor peso es mejor
                if 'especificaciones_tecnicas_peso_gramos' in candidates.columns:
                    max_weight = candidates['especificaciones_tecnicas_peso_gramos'].max()
                    if max_weight > 0:
                        candidates[f'{use_case.value}_score'] += weight * (1 - candidates['especificaciones_tecnicas_peso_gramos'] / max_weight)
            
            elif criterion == 'features':
                # Contar características
                feature_cols = [col for col in candidates.columns if col.startswith('caracteristicas_vuelo_')]
                if feature_cols:
                    candidates['feature_count'] = candidates[feature_cols].sum(axis=1)
                    max_features = candidates['feature_count'].max()
                    if max_features > 0:
                        candidates[f'{use_case.value}_score'] += weight * (candidates['feature_count'] / max_features)
            
            elif criterion == 'ease_of_use':
                # Basado en nivel de usuario
                ease_scores = {'principiante': 1.0, 'intermedio': 0.7, 'avanzado': 0.4, 'profesional': 0.2}
                if 'clasificacion_nivel_usuario' in candidates.columns:
                    candidates[f'{use_case.value}_score'] += weight * candidates['clasificacion_nivel_usuario'].map(ease_scores).fillna(0.5)
            
            elif criterion == 'stability':
                # Basado en estabilización y peso
                stability_score = 0
                if 'camara_estabilizacion' in candidates.columns:
                    stab_scores = {'mecanica': 1.0, 'hibrida': 0.8, 'digital': 0.6}
                    stability_score += 0.5 * candidates['camara_estabilizacion'].map(stab_scores).fillna(0)
                
                if 'especificaciones_tecnicas_peso_gramos' in candidates.columns:
                    # Drones más pesados suelen ser más estables
                    weight_stability = candidates['especificaciones_tecnicas_peso_gramos'].apply(
                        lambda x: min(x / 1000, 1) if pd.notna(x) else 0
                    )
                    stability_score += 0.5 * weight_stability
                
                candidates[f'{use_case.value}_score'] += weight * stability_score
        
        # Normalizar score a 0-100
        candidates[f'{use_case.value}_score'] *= 100
        
        # Bonus por características "nice to have"
        for feature in profile.get('nice_to_have', []):
            feature_col = f'caracteristicas_vuelo_{feature}'
            if feature_col in candidates.columns:
                candidates.loc[candidates[feature_col] == True, f'{use_case.value}_score'] += 5
        
        # Asegurar que el score no exceda 100
        candidates[f'{use_case.value}_score'] = candidates[f'{use_case.value}_score'].clip(upper=100)
        
        # Ordenar por score
        candidates = candidates.sort_values(f'{use_case.value}_score', ascending=False)
        
        # Agregar ranking
        candidates['rank'] = range(1, len(candidates) + 1)
        
        return candidates
    
    def price_tier_analysis(self) -> Dict[str, List[Dict]]:
        """
        Analizar drones por niveles de precio
        
        Returns:
            Diccionario con análisis por tier de precio
        """
        tiers = {
            'budget': {
                'range': (0, 500),
                'description': 'Entrada - Ideal para principiantes',
                'drones': []
            },
            'mid_range': {
                'range': (500, 1500),
                'description': 'Intermedio - Para entusiastas',
                'drones': []
            },
            'high_end': {
                'range': (1500, 3000),
                'description': 'Avanzado - Para uso semi-profesional',
                'drones': []
            },
            'professional': {
                'range': (3000, 10000),
                'description': 'Profesional - Para trabajo comercial',
                'drones': []
            },
            'enterprise': {
                'range': (10000, float('inf')),
                'description': 'Enterprise - Soluciones industriales',
                'drones': []
            }
        }
        
        for tier_name, tier_info in tiers.items():
            min_price, max_price = tier_info['range']
            
            # Filtrar drones en este tier
            tier_drones = self.drones_df[
                (self.drones_df['precio_usd'] >= min_price) & 
                (self.drones_df['precio_usd'] < max_price)
            ].copy()
            
            if len(tier_drones) > 0:
                # Calcular versatilidad para ranking dentro del tier
                tier_drones['versatility_score'] = tier_drones.apply(
                    lambda row: self.calculate_versatility_score({
                        'evita_obstaculos': row.get('caracteristicas_vuelo_evita_obstaculos', False),
                        'retorno_automatico': row.get('caracteristicas_vuelo_retorno_automatico', False),
                        'seguimiento_objeto': row.get('caracteristicas_vuelo_seguimiento_objeto', False),
                        'vuelo_nocturno': row.get('caracteristicas_vuelo_vuelo_nocturno', False),
                        'modo_sport': row.get('caracteristicas_vuelo_modo_sport', False),
                        'camara_resolucion': row.get('camara_resolucion_video'),
                        'gimbal_estabilizacion': row.get('camara_estabilizacion'),
                        'zoom_optico': row.get('camara_zoom_optico', 0)
                    }),
                    axis=1
                )
                
                # Top 5 del tier
                top_drones = tier_drones.nlargest(5, 'versatility_score')
                
                tier_info['drones'] = top_drones[
                    ['modelo', 'marca', 'precio_usd', 'versatility_score']
                ].to_dict('records')
                
                # Estadísticas del tier
                tier_info['stats'] = {
                    'count': len(tier_drones),
                    'avg_price': float(tier_drones['precio_usd'].mean()),
                    'avg_versatility': float(tier_drones['versatility_score'].mean()),
                    'brands': tier_drones['marca'].value_counts().to_dict()
                }
                
                # Mejor del tier
                if len(top_drones) > 0:
                    best = top_drones.iloc[0]
                    tier_info['best_choice'] = {
                        'modelo': best['modelo'],
                        'marca': best['marca'],
                        'precio': float(best['precio_usd']),
                        'score': float(best['versatility_score'])
                    }
        
        return tiers
    
    def generate_comparison_matrix(self, drone_ids: List[int]) -> Dict[str, Any]:
        """
        Generar matriz de comparación para drones seleccionados
        
        Args:
            drone_ids: Lista de IDs de drones a comparar
        
        Returns:
            Matriz de comparación estructurada
        """
        # Limitar a máximo 5 drones
        drone_ids = drone_ids[:5]
        
        selected_drones = self.drones_df[self.drones_df.index.isin(drone_ids)]
        
        comparison = {
            'drones': [],
            'categories': {
                'specs': {
                    'name': 'Especificaciones',
                    'attributes': ['peso', 'autonomia', 'alcance', 'velocidad', 'resistencia_viento']
                },
                'camera': {
                    'name': 'Cámara',
                    'attributes': ['resolucion', 'fps', 'estabilizacion', 'zoom_optico']
                },
                'features': {
                    'name': 'Características',
                    'attributes': ['evita_obstaculos', 'retorno_automatico', 'seguimiento_objeto', 
                                 'vuelo_nocturno', 'modo_sport']
                },
                'scores': {
                    'name': 'Puntuaciones',
                    'attributes': ['versatility_score', 'price_performance_ratio']
                }
            }
        }
        
        # Procesar cada drone
        for idx, drone in selected_drones.iterrows():
            drone_data = {
                'id': idx,
                'modelo': drone.get('modelo'),
                'marca': drone.get('marca'),
                'precio': float(drone.get('precio_usd', 0)),
                'imagen': f"/assets/drone_icons/{drone.get('marca', 'generic').lower()}.png",
                'attributes': {}
            }
            
            # Especificaciones
            drone_data['attributes']['peso'] = f"{drone.get('especificaciones_tecnicas_peso_gramos', 'N/A')}g"
            drone_data['attributes']['autonomia'] = f"{drone.get('especificaciones_tecnicas_autonomia_minutos', 'N/A')} min"
            drone_data['attributes']['alcance'] = f"{drone.get('especificaciones_tecnicas_alcance_metros', 'N/A')}m"
            drone_data['attributes']['velocidad'] = f"{drone.get('especificaciones_tecnicas_velocidad_max_kmh', 'N/A')} km/h"
            drone_data['attributes']['resistencia_viento'] = drone.get('especificaciones_tecnicas_resistencia_viento', 'N/A')
            
            # Cámara
            drone_data['attributes']['resolucion'] = drone.get('camara_resolucion_video', 'N/A')
            drone_data['attributes']['fps'] = f"{drone.get('camara_fps_max', 'N/A')} fps"
            drone_data['attributes']['estabilizacion'] = drone.get('camara_estabilizacion', 'N/A')
            drone_data['attributes']['zoom_optico'] = f"{drone.get('camara_zoom_optico', 'N/A')}x"
            
            # Características (iconos o checkmarks)
            for feature in ['evita_obstaculos', 'retorno_automatico', 'seguimiento_objeto', 
                          'vuelo_nocturno', 'modo_sport']:
                col_name = f'caracteristicas_vuelo_{feature}'
                drone_data['attributes'][feature] = '✓' if drone.get(col_name, False) else '✗'
            
            # Scores
            versatility = self.calculate_versatility_score({
                'evita_obstaculos': drone.get('caracteristicas_vuelo_evita_obstaculos', False),
                'retorno_automatico': drone.get('caracteristicas_vuelo_retorno_automatico', False),
                'seguimiento_objeto': drone.get('caracteristicas_vuelo_seguimiento_objeto', False),
                'vuelo_nocturno': drone.get('caracteristicas_vuelo_vuelo_nocturno', False),
                'modo_sport': drone.get('caracteristicas_vuelo_modo_sport', False),
                'camara_resolucion': drone.get('camara_resolucion_video'),
                'gimbal_estabilizacion': drone.get('camara_estabilizacion'),
                'zoom_optico': drone.get('camara_zoom_optico', 0)
            })
            
            drone_data['attributes']['versatility_score'] = f"{versatility:.1f}/100"
            drone_data['attributes']['price_performance_ratio'] = f"{drone.get('price_performance_ratio', 0):.2f}"
            
            comparison['drones'].append(drone_data)
        
        # Identificar mejor en cada categoría
        comparison['highlights'] = self._identify_comparison_highlights(selected_drones)
        
        return comparison
    
    def _identify_comparison_highlights(self, drones_df: pd.DataFrame) -> Dict[str, str]:
        """Identificar lo mejor en cada categoría para resaltar en la comparación"""
        highlights = {}
        
        # Mejor autonomía
        if 'especificaciones_tecnicas_autonomia_minutos' in drones_df.columns:
            best_autonomy_idx = drones_df['especificaciones_tecnicas_autonomia_minutos'].idxmax()
            if pd.notna(best_autonomy_idx):
                highlights['best_autonomy'] = drones_df.loc[best_autonomy_idx, 'modelo']
        
        # Mejor alcance
        if 'especificaciones_tecnicas_alcance_metros' in drones_df.columns:
            best_range_idx = drones_df['especificaciones_tecnicas_alcance_metros'].idxmax()
            if pd.notna(best_range_idx):
                highlights['best_range'] = drones_df.loc[best_range_idx, 'modelo']
        
        # Mejor cámara
        camera_priority = {'8K': 4, '6K': 3, '4K': 2, '1080p': 1, '720p': 0}
        if 'camara_resolucion_video' in drones_df.columns:
            drones_df['camera_score'] = drones_df['camara_resolucion_video'].map(camera_priority).fillna(0)
            best_camera_idx = drones_df['camera_score'].idxmax()
            if pd.notna(best_camera_idx):
                highlights['best_camera'] = drones_df.loc[best_camera_idx, 'modelo']
        
        # Más ligero
        if 'especificaciones_tecnicas_peso_gramos' in drones_df.columns:
            lightest_idx = drones_df['especificaciones_tecnicas_peso_gramos'].idxmin()
            if pd.notna(lightest_idx):
                highlights['lightest'] = drones_df.loc[lightest_idx, 'modelo']
        
        # Mejor valor
        if 'price_performance_ratio' in drones_df.columns:
            best_value_idx = drones_df['price_performance_ratio'].idxmax()
            if pd.notna(best_value_idx):
                highlights['best_value'] = drones_df.loc[best_value_idx, 'modelo']
        
        return highlights
    
    def calculate_market_position(self, drone_id: int) -> Dict[str, Any]:
        """
        Calcular posición de mercado de un drone específico
        
        Args:
            drone_id: ID del drone
        
        Returns:
            Análisis de posición de mercado
        """
        drone = self.drones_df.loc[drone_id]
        
        position = {
            'modelo': drone['modelo'],
            'marca': drone['marca'],
            'percentiles': {},
            'competitors': [],
            'strengths': [],
            'weaknesses': []
        }
        
        # Calcular percentiles
        metrics = {
            'precio': 'precio_usd',
            'autonomia': 'especificaciones_tecnicas_autonomia_minutos',
            'alcance': 'especificaciones_tecnicas_alcance_metros',
            'velocidad': 'especificaciones_tecnicas_velocidad_max_kmh'
        }
        
        for metric_name, column_name in metrics.items():
            if column_name in self.drones_df.columns:
                value = drone.get(column_name)
                if pd.notna(value):
                    percentile = (self.drones_df[column_name] <= value).sum() / len(self.drones_df) * 100
                    position['percentiles'][metric_name] = round(percentile, 1)
        
        # Encontrar competidores directos (±20% en precio)
        if pd.notna(drone.get('precio_usd')):
            price_range = (drone['precio_usd'] * 0.8, drone['precio_usd'] * 1.2)
            competitors = self.drones_df[
                (self.drones_df['precio_usd'] >= price_range[0]) & 
                (self.drones_df['precio_usd'] <= price_range[1]) &
                (self.drones_df.index != drone_id)
            ]
            
            position['competitors'] = competitors[['modelo', 'marca', 'precio_usd']].head(5).to_dict('records')
        
        # Identificar fortalezas y debilidades
        # Fortalezas (percentil > 70)
        for metric, percentile in position['percentiles'].items():
            if percentile > 70:
                position['strengths'].append(f"Excelente {metric} (top {100-percentile:.0f}%)")
        
        # Características premium
        if drone.get('camara_resolucion_video') in ['6K', '8K']:
            position['strengths'].append(f"Cámara premium {drone['camara_resolucion_video']}")
        
        feature_count = sum([
            drone.get('caracteristicas_vuelo_evita_obstaculos', False),
            drone.get('caracteristicas_vuelo_retorno_automatico', False),
            drone.get('caracteristicas_vuelo_seguimiento_objeto', False),
            drone.get('caracteristicas_vuelo_vuelo_nocturno', False),
            drone.get('caracteristicas_vuelo_modo_sport', False)
        ])
        
        if feature_count >= 4:
            position['strengths'].append("Rico en características avanzadas")
        
        # Debilidades (percentil < 30)
        for metric, percentile in position['percentiles'].items():
            if percentile < 30:
                position['weaknesses'].append(f"{metric.capitalize()} por debajo del promedio")
        
        if drone.get('camara_resolucion_video') in ['720p', None]:
            position['weaknesses'].append("Cámara de baja resolución")
        
        if feature_count < 2:
            position['weaknesses'].append("Pocas características avanzadas")
        
        return position
    
    def generate_insights(self) -> List[Dict[str, Any]]:
        """Generar insights del mercado de drones"""
        insights = []
        
        # Insight 1: Marca con mejor relación precio/rendimiento promedio
        if 'price_performance_ratio' in self.drones_df.columns:
            brand_ratios = self.drones_df.groupby('marca')['price_performance_ratio'].mean().sort_values(ascending=False)
            
            if len(brand_ratios) > 0:
                best_brand = brand_ratios.index[0]
                insights.append({
                    'tipo': 'brand_value',
                    'titulo': 'Marca con mejor valor',
                    'mensaje': f"{best_brand} ofrece la mejor relación precio/rendimiento promedio",
                    'datos': {
                        'marca': best_brand,
                        'ratio_promedio': round(brand_ratios.iloc[0], 2)
                    }
                })
        
        # Insight 2: Tendencia de características
        feature_cols = [col for col in self.drones_df.columns if col.startswith('caracteristicas_vuelo_')]
        if feature_cols:
            feature_adoption = {}
            for col in feature_cols:
                feature_name = col.replace('caracteristicas_vuelo_', '')
                adoption_rate = (self.drones_df[col] == True).sum() / len(self.drones_df) * 100
                feature_adoption[feature_name] = round(adoption_rate, 1)
            
            most_common = max(feature_adoption.items(), key=lambda x: x[1])
            least_common = min(feature_adoption.items(), key=lambda x: x[1])
            
            insights.append({
                'tipo': 'feature_trends',
                'titulo': 'Tendencias en características',
                'mensaje': f"'{most_common[0]}' es casi estándar ({most_common[1]}%), mientras que '{least_common[0]}' es aún poco común ({least_common[1]}%)",
                'datos': feature_adoption
            })
        
        # Insight 3: Brecha de mercado
        # Buscar rangos de precio con pocos modelos
        if 'precio_usd' in self.drones_df.columns:
            price_bins = pd.cut(self.drones_df['precio_usd'], bins=10)
            price_distribution = price_bins.value_counts().sort_index()
            
            # Encontrar bins con menos modelos
            min_bin_count = price_distribution.min()
            gap_bins = price_distribution[price_distribution == min_bin_count]
            
            if len(gap_bins) > 0:
                gap_range = gap_bins.index[0]
                insights.append({
                    'tipo': 'market_gap',
                    'titulo': 'Oportunidad de mercado',
                    'mensaje': f"Existe una brecha en el rango de ${gap_range.left:.0f}-${gap_range.right:.0f} con solo {min_bin_count} modelos",
                    'datos': {
                        'rango': (float(gap_range.left), float(gap_range.right)),
                        'modelos': int(min_bin_count)
                    }
                })
        
        # Insight 4: Evolución tecnológica
        high_end_drones = self.drones_df[self.drones_df['precio_usd'] > 2000]
        if len(high_end_drones) > 0:
            high_end_4k_rate = (high_end_drones['camara_resolucion_video'].isin(['4K', '6K', '8K'])).sum() / len(high_end_drones) * 100
            
            insights.append({
                'tipo': 'tech_evolution',
                'titulo': 'Estándar en gama alta',
                'mensaje': f"El {high_end_4k_rate:.0f}% de los drones premium (>$2000) tienen cámara 4K o superior",
                'datos': {
                    'porcentaje_4k_plus': round(high_end_4k_rate, 1),
                    'total_premium': len(high_end_drones)
                }
            })
        
        return insights
    
    def save_rankings(self, output_dir: str = '../analysis'):
        """Guardar resultados de rankings"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        rankings = {
            'generated_at': datetime.now().isoformat(),
            'use_case_rankings': {},
            'price_tiers': self.price_tier_analysis(),
            'insights': self.generate_insights()
        }
        
        # Generar rankings para cada caso de uso
        for use_case in UseCase:
            logger.info(f"Generando ranking para {use_case.value}...")
            ranked_df = self.rank_by_use_case(use_case)
            
            # Guardar top 10
            top_10 = ranked_df.head(10)[
                ['rank', 'modelo', 'marca', 'precio_usd', f'{use_case.value}_score']
            ].to_dict('records')
            
            rankings['use_case_rankings'][use_case.value] = {
                'name': self.use_case_profiles[use_case]['name'],
                'description': f"Top 10 drones para {self.use_case_profiles[use_case]['name']}",
                'profile': self.use_case_profiles[use_case],
                'top_10': top_10,
                'total_candidates': len(ranked_df)
            }
        
        # Guardar archivo de rankings
        with open(output_path / 'drone_rankings.json', 'w', encoding='utf-8') as f:
            json.dump(rankings, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Rankings guardados en {output_path}")


def main():
    """Función principal del motor de ranking"""
    engine = DroneRankingEngine()
    
    # Cargar datos
    engine.load_data()
    
    # Generar análisis de tiers de precio
    logger.info("Analizando tiers de precio...")
    price_tiers = engine.price_tier_analysis()
    
    for tier_name, tier_info in price_tiers.items():
        if tier_info.get('stats'):
            logger.info(f"\n{tier_name.upper()}: {tier_info['description']}")
            logger.info(f"  - {tier_info['stats']['count']} modelos")
            logger.info(f"  - Precio promedio: ${tier_info['stats']['avg_price']:.0f}")
            
            if tier_info.get('best_choice'):
                best = tier_info['best_choice']
                logger.info(f"  - Mejor opción: {best['modelo']} (${best['precio']:.0f})")
    
    # Probar rankings por caso de uso
    test_use_case = UseCase.PHOTOGRAPHY_ENTHUSIAST
    logger.info(f"\nGenerando ranking para {test_use_case.value}...")
    
    ranked = engine.rank_by_use_case(test_use_case)
    logger.info(f"Top 5 para {test_use_case.value}:")
    
    for idx, drone in ranked.head(5).iterrows():
        logger.info(f"  {drone['rank']}. {drone['modelo']} - Score: {drone[f'{test_use_case.value}_score']:.1f}")
    
    # Guardar todos los rankings
    engine.save_rankings()
    
    logger.info("\nRankings completados exitosamente")


if __name__ == "__main__":
    main()
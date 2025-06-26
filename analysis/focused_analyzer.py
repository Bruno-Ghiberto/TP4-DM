#Focused Analyzer - Análisis específico para drones
#Genera métricas de negocio e insights accionables

import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class FocusedDroneAnalyzer:
    """Analizador especializado en métricas de drones"""
    
    def __init__(self):
        self.drones_df = None
        self.analysis_results = {
            'timestamp': datetime.now().isoformat(),
            'total_analyzed': 0,
            'market_segments': {},
            'performance_analysis': {},
            'recommendations': {},
            'insights': []
        }
    
    def load_data(self, data_path: str = '../data/processed/unified_drones.json'):
        """Cargar datos procesados de drones"""
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                drones_data = json.load(f)
            
            self.drones_df = pd.json_normalize(drones_data)
            self.analysis_results['total_analyzed'] = len(self.drones_df)
            
            # Normalizar nombres de columnas
            self.drones_df.columns = [col.replace('.', '_') for col in self.drones_df.columns]
            
            logger.info(f"Cargados {len(self.drones_df)} drones para análisis")
            
        except Exception as e:
            logger.error(f"Error cargando datos: {str(e)}")
            raise
    
    def calculate_performance_score(self) -> pd.Series:
        """
        Calcular score de rendimiento para cada drone
        
        Returns:
            Serie con scores de rendimiento
        """
        # Crear copia para cálculos
        df = self.drones_df.copy()
        
        # Factores de rendimiento (ponderados)
        performance_weights = {
            'autonomia': 0.25,
            'alcance': 0.20,
            'velocidad': 0.15,
            'camara': 0.25,
            'features': 0.15
        }
        
        # Normalizar métricas (0-1)
        if 'especificaciones_tecnicas_autonomia_minutos' in df.columns:
            df['norm_autonomia'] = df['especificaciones_tecnicas_autonomia_minutos'] / df['especificaciones_tecnicas_autonomia_minutos'].max()
        else:
            df['norm_autonomia'] = 0
        
        if 'especificaciones_tecnicas_alcance_metros' in df.columns:
            df['norm_alcance'] = df['especificaciones_tecnicas_alcance_metros'] / df['especificaciones_tecnicas_alcance_metros'].max()
        else:
            df['norm_alcance'] = 0
        
        if 'especificaciones_tecnicas_velocidad_max_kmh' in df.columns:
            df['norm_velocidad'] = df['especificaciones_tecnicas_velocidad_max_kmh'] / df['especificaciones_tecnicas_velocidad_max_kmh'].max()
        else:
            df['norm_velocidad'] = 0
        
        # Score de cámara
        camera_scores = {
            '8K': 1.0,
            '6K': 0.85,
            '4K': 0.7,
            '1080p': 0.4,
            '720p': 0.2
        }
        
        if 'camara_resolucion_video' in df.columns:
            df['norm_camara'] = df['camara_resolucion_video'].map(camera_scores).fillna(0)
        else:
            df['norm_camara'] = 0
        
        # Score de características
        feature_cols = [
            'caracteristicas_vuelo_evita_obstaculos',
            'caracteristicas_vuelo_retorno_automatico',
            'caracteristicas_vuelo_seguimiento_objeto',
            'caracteristicas_vuelo_vuelo_nocturno',
            'caracteristicas_vuelo_modo_sport'
        ]
        
        available_features = [col for col in feature_cols if col in df.columns]
        if available_features:
            df['norm_features'] = df[available_features].sum(axis=1) / len(feature_cols)
        else:
            df['norm_features'] = 0
        
        # Calcular score de rendimiento ponderado
        df['performance_score'] = (
            df['norm_autonomia'] * performance_weights['autonomia'] +
            df['norm_alcance'] * performance_weights['alcance'] +
            df['norm_velocidad'] * performance_weights['velocidad'] +
            df['norm_camara'] * performance_weights['camara'] +
            df['norm_features'] * performance_weights['features']
        ) * 100
        
        # Guardar resultados
        self.analysis_results['performance_scores'] = {
            'best_performance': df.nlargest(5, 'performance_score')[['modelo', 'marca', 'performance_score']].to_dict('records'),
            'worst_performance': df.nsmallest(5, 'performance_score')[['modelo', 'marca', 'performance_score']].to_dict('records'),
            'average_score': float(df['performance_score'].mean())
        }
        
        # Agregar insight
        best_drone = df.loc[df['performance_score'].idxmax()]
        self.analysis_results['insights'].append({
            'tipo': 'mejor_rendimiento',
            'mensaje': f"El {best_drone['modelo']} tiene el mejor score de rendimiento con {best_drone['performance_score']:.2f} puntos",
            'datos': {
                'modelo': best_drone['modelo'],
                'performance_score': best_drone['performance_score']
            }
        })
        
        # Actualizar DataFrame con nuevas métricas
        self.drones_df['performance_score'] = df['performance_score']
        
        return df['performance_score']
    
    def identify_market_segments(self) -> Dict[str, List[str]]:
        """
        Identificar segmentos de mercado basados en características
        
        Returns:
            Diccionario con segmentos y modelos en cada uno
        """
        segments = {
            'entry_level': {
                'criteria': lambda df: df['clasificacion_categoria_peso'] == 'ultra_ligero',
                'description': 'Drones ultraligeros para principiantes',
                'models': []
            },
            'hobbyist': {
                'criteria': lambda df: df['clasificacion_categoria_peso'].isin(['ligero', 'medio']),
                'description': 'Drones para entusiastas y hobby',
                'models': []
            },
            'prosumer': {
                'criteria': lambda df: df['camara_resolucion_video'].isin(['4K', '6K']),
                'description': 'Drones semiprofesionales con buenas cámaras',
                'models': []
            },
            'professional': {
                'criteria': lambda df: df['camara_resolucion_video'].isin(['6K', '8K']),
                'description': 'Drones profesionales para trabajo comercial',
                'models': []
            },
            'industrial': {
                'criteria': lambda df: df['clasificacion_categoria_peso'] == 'pesado',
                'description': 'Drones industriales para aplicaciones especializadas',
                'models': []
            },
            'racing': {
                'criteria': lambda df: (df['especificaciones_tecnicas_velocidad_max_kmh'] > 80) & 
                                     (df['clasificacion_categoria_peso'].isin(['ultra_ligero', 'ligero'])),
                'description': 'Drones de carreras de alta velocidad',
                'models': []
            }
        }
        
        # Aplicar criterios y clasificar drones
        for segment_name, segment_info in segments.items():
            try:
                mask = segment_info['criteria'](self.drones_df)
                segment_drones = self.drones_df[mask]
                
                segment_info['models'] = segment_drones[['modelo', 'marca']].to_dict('records')
                
                # Estadísticas del segmento
                if len(segment_drones) > 0:
                    segment_stats = {
                        'count': len(segment_drones),
                        'top_brands': segment_drones['marca'].value_counts().to_dict()
                    }
                else:
                    segment_stats = {
                        'count': 0,
                        'top_brands': {}
                    }
                
                self.analysis_results['market_segments'][segment_name] = {
                    'description': segment_info['description'],
                    'statistics': segment_stats,
                    'models': segment_info['models']
                }
                
            except Exception as e:
                logger.warning(f"Error procesando segmento {segment_name}: {str(e)}")
        
        # Agregar insight sobre segmento más poblado
        largest_segment = max(self.analysis_results['market_segments'].items(), 
                            key=lambda x: x[1]['statistics']['count'])
        
        self.analysis_results['insights'].append({
            'tipo': 'segmento_dominante',
            'mensaje': f"El segmento '{largest_segment[0]}' es el más grande con {largest_segment[1]['statistics']['count']} modelos",
            'datos': largest_segment[1]['statistics']
        })
        
        return self.analysis_results['market_segments']
    
    def find_best_value_by_category(self) -> Dict[str, Any]:
        """
        Encontrar el mejor valor en cada categoría
        
        Returns:
            Diccionario con mejores opciones por categoría
        """
        best_by_category = {}
        
        # Categorías a analizar
        categories = {
            'peso': 'clasificacion_categoria_peso',
            'nivel_usuario': 'clasificacion_nivel_usuario',
            'marca': 'marca'
        }
        
        for category_name, column_name in categories.items():
            if column_name in self.drones_df.columns:
                category_best = {}
                
                for category_value in self.drones_df[column_name].unique():
                    if pd.notna(category_value):
                        category_df = self.drones_df[self.drones_df[column_name] == category_value]
                        
                        if 'performance_score' in category_df.columns:
                            best_drone_idx = category_df['performance_score'].idxmax()
                            
                            if pd.notna(best_drone_idx):
                                best_drone = category_df.loc[best_drone_idx]
                                
                                category_best[category_value] = {
                                    'modelo': best_drone['modelo'],
                                    'marca': best_drone['marca'],
                                    'performance_score': float(best_drone['performance_score']) if pd.notna(best_drone['performance_score']) else None,
                                    'autonomia': float(best_drone.get('especificaciones_tecnicas_autonomia_minutos', 0)),
                                    'alcance': float(best_drone.get('especificaciones_tecnicas_alcance_metros', 0))
                                }
                
                best_by_category[category_name] = category_best
        
        self.analysis_results['best_value_by_category'] = best_by_category
        
        # Agregar insights
        for category, values in best_by_category.items():
            if values:
                self.analysis_results['insights'].append({
                    'tipo': f'mejor_por_{category}',
                    'mensaje': f"Mejores opciones por {category}",
                    'datos': values
                })
        
        return best_by_category
    
    def generate_buying_recommendations(self, user_profile: Dict) -> List[Dict]:
        """
        Generar recomendaciones personalizadas según perfil de usuario
        
        Args:
            user_profile: Dict con preferencias del usuario
                - experience_level: nivel de experiencia
                - primary_use: uso principal
                - must_have_features: características requeridas
        
        Returns:
            Lista de recomendaciones ordenadas
        """
        recommendations = []
        
        # Usar todos los drones como candidatos
        candidates = self.drones_df.copy()
        
        # Filtrar por nivel de experiencia
        experience_level = user_profile.get('experience_level')
        if experience_level and 'clasificacion_nivel_usuario' in candidates.columns:
            # Mapeo de niveles compatibles
            level_compatibility = {
                'principiante': ['principiante', 'intermedio'],
                'intermedio': ['intermedio', 'avanzado'],
                'avanzado': ['intermedio', 'avanzado', 'profesional'],
                'profesional': ['avanzado', 'profesional']
            }
            
            compatible_levels = level_compatibility.get(experience_level, [experience_level])
            candidates = candidates[candidates['clasificacion_nivel_usuario'].isin(compatible_levels)]
        
        # Filtrar por uso principal
        primary_use = user_profile.get('primary_use')
        if primary_use:
            # Buscar drones con ese uso en su lista de usos principales
            use_mask = candidates['clasificacion_uso_principal'].apply(
                lambda x: primary_use in x if isinstance(x, list) else False
            )
            candidates = candidates[use_mask]
        
        # Filtrar por características requeridas
        must_have_features = user_profile.get('must_have_features', [])
        for feature in must_have_features:
            feature_column = f'caracteristicas_vuelo_{feature}'
            if feature_column in candidates.columns:
                candidates = candidates[candidates[feature_column] == True]
        
        # Calcular score de recomendación
        if len(candidates) > 0:
            # Factores de scoring personalizados según uso
            use_weights = {
                'recreativo': {
                    'facilidad': 0.4,
                    'autonomia': 0.3,
                    'features': 0.3
                },
                'fotografia': {
                    'camara': 0.5,
                    'estabilidad': 0.25,
                    'autonomia': 0.25
                },
                'video_profesional': {
                    'camara': 0.4,
                    'estabilidad': 0.3,
                    'autonomia': 0.15,
                    'alcance': 0.15
                },
                'inspeccion': {
                    'alcance': 0.35,
                    'autonomia': 0.35,
                    'camara': 0.15,
                    'seguridad': 0.15
                }
            }
            
            weights = use_weights.get(primary_use, {
                'camara': 0.3,
                'autonomia': 0.3,
                'alcance': 0.2,
                'features': 0.2
            })
            
            # Calcular scores
            candidates['recommendation_score'] = 0
            
            # Score por cámara
            if 'camara' in weights and 'camara_resolucion_video' in candidates.columns:
                camera_scores = {'8K': 1.0, '6K': 0.85, '4K': 0.7, '1080p': 0.4, '720p': 0.2}
                candidates['recommendation_score'] += weights['camara'] * candidates['camara_resolucion_video'].map(camera_scores).fillna(0)
            
            # Score por autonomía
            if 'autonomia' in weights and 'especificaciones_tecnicas_autonomia_minutos' in candidates.columns:
                max_autonomia = candidates['especificaciones_tecnicas_autonomia_minutos'].max()
                if max_autonomia > 0:
                    candidates['recommendation_score'] += weights['autonomia'] * (candidates['especificaciones_tecnicas_autonomia_minutos'] / max_autonomia)
            
            # Score por alcance
            if 'alcance' in weights and 'especificaciones_tecnicas_alcance_metros' in candidates.columns:
                max_alcance = candidates['especificaciones_tecnicas_alcance_metros'].max()
                if max_alcance > 0:
                    candidates['recommendation_score'] += weights['alcance'] * (candidates['especificaciones_tecnicas_alcance_metros'] / max_alcance)
            
            # Normalizar score a 0-100
            candidates['recommendation_score'] *= 100
            
            # Ordenar por score y tomar top 5
            top_recommendations = candidates.nlargest(5, 'recommendation_score')
            
            # Formatear recomendaciones
            for idx, drone in top_recommendations.iterrows():
                recommendation = {
                    'rank': len(recommendations) + 1,
                    'modelo': drone['modelo'],
                    'marca': drone['marca'],
                    'score': float(drone['recommendation_score']),
                    'reasons': [],
                    'specs': {
                        'autonomia': float(drone.get('especificaciones_tecnicas_autonomia_minutos', 0)),
                        'alcance': float(drone.get('especificaciones_tecnicas_alcance_metros', 0)),
                        'peso': float(drone.get('especificaciones_tecnicas_peso_gramos', 0)),
                        'camara': drone.get('camara_resolucion_video', 'N/A')
                    }
                }
                
                # Agregar razones de recomendación
                if drone.get('performance_score', 0) > self.drones_df['performance_score'].mean():
                    recommendation['reasons'].append('Excelente score de rendimiento')
                
                if drone.get('camara_resolucion_video') in ['4K', '6K', '8K']:
                    recommendation['reasons'].append(f'Cámara de alta calidad ({drone["camara_resolucion_video"]})')
                
                if drone.get('especificaciones_tecnicas_autonomia_minutos', 0) > 30:
                    recommendation['reasons'].append(f'Gran autonomía ({drone["especificaciones_tecnicas_autonomia_minutos"]:.0f} min)')
                
                if drone.get('caracteristicas_vuelo_evita_obstaculos'):
                    recommendation['reasons'].append('Sistema de evitación de obstáculos')
                
                recommendations.append(recommendation)
        
        # Guardar recomendaciones en resultados
        profile_key = f"{experience_level}_{primary_use}"
        self.analysis_results['recommendations'][profile_key] = {
            'profile': user_profile,
            'recommendations': recommendations,
            'total_candidates': len(candidates)
        }
        
        return recommendations
    
    def analyze_performance_trends(self) -> Dict[str, Any]:
        """Analizar tendencias de rendimiento por marca y categoría"""
        trends = {
            'by_brand': {},
            'by_category': {},
            'overall': {}
        }
        
        # Tendencias por marca
        for brand in self.drones_df['marca'].unique():
            brand_df = self.drones_df[self.drones_df['marca'] == brand]
            
            if 'performance_score' in brand_df.columns:
                trends['by_brand'][brand] = {
                    'avg_performance': float(brand_df['performance_score'].mean()),
                    'min_performance': float(brand_df['performance_score'].min()),
                    'max_performance': float(brand_df['performance_score'].max()),
                    'model_count': len(brand_df)
                }
        
        # Tendencias por categoría de peso
        if 'clasificacion_categoria_peso' in self.drones_df.columns:
            for category in self.drones_df['clasificacion_categoria_peso'].unique():
                if pd.notna(category):
                    category_df = self.drones_df[self.drones_df['clasificacion_categoria_peso'] == category]
                    
                    if 'performance_score' in category_df.columns and len(category_df) > 0:
                        trends['by_category'][category] = {
                            'avg_performance': float(category_df['performance_score'].mean()),
                            'min_performance': float(category_df['performance_score'].min()),
                            'max_performance': float(category_df['performance_score'].max()),
                            'model_count': len(category_df)
                        }
        
        # Tendencias generales
        if 'performance_score' in self.drones_df.columns:
            trends['overall'] = {
                'avg_performance': float(self.drones_df['performance_score'].mean()),
                'median_performance': float(self.drones_df['performance_score'].median()),
                'performance_std': float(self.drones_df['performance_score'].std()),
                'total_models': len(self.drones_df)
            }
        
        self.analysis_results['performance_trends'] = trends
        
        # Agregar insight sobre marca con mejor/peor rendimiento
        if trends['by_brand']:
            best_performance_brand = max(trends['by_brand'].items(), key=lambda x: x[1]['avg_performance'])
            worst_performance_brand = min(trends['by_brand'].items(), key=lambda x: x[1]['avg_performance'])
            
            self.analysis_results['insights'].append({
                'tipo': 'rendimiento_marcas',
                'mensaje': f"{best_performance_brand[0]} tiene el mejor rendimiento promedio ({best_performance_brand[1]['avg_performance']:.1f} puntos), mientras que {worst_performance_brand[0]} tiene el menor ({worst_performance_brand[1]['avg_performance']:.1f} puntos)",
                'datos': {
                    'mejor_rendimiento': best_performance_brand,
                    'menor_rendimiento': worst_performance_brand
                }
            })
        
        return trends
    
    def calculate_feature_adoption(self) -> Dict[str, float]:
        """Calcular tasa de adopción de características avanzadas"""
        feature_adoption = {}
        
        feature_columns = {
            'evita_obstaculos': 'caracteristicas_vuelo_evita_obstaculos',
            'retorno_automatico': 'caracteristicas_vuelo_retorno_automatico',
            'seguimiento_objeto': 'caracteristicas_vuelo_seguimiento_objeto',
            'vuelo_nocturno': 'caracteristicas_vuelo_vuelo_nocturno',
            'modo_sport': 'caracteristicas_vuelo_modo_sport'
        }
        
        for feature_name, column_name in feature_columns.items():
            if column_name in self.drones_df.columns:
                adoption_rate = (self.drones_df[column_name] == True).sum() / len(self.drones_df) * 100
                feature_adoption[feature_name] = round(adoption_rate, 2)
        
        # Calcular adopción por marca
        feature_by_brand = {}
        for brand in self.drones_df['marca'].unique():
            brand_df = self.drones_df[self.drones_df['marca'] == brand]
            brand_adoption = {}
            
            for feature_name, column_name in feature_columns.items():
                if column_name in brand_df.columns:
                    adoption_rate = (brand_df[column_name] == True).sum() / len(brand_df) * 100
                    brand_adoption[feature_name] = round(adoption_rate, 2)
            
            feature_by_brand[brand] = brand_adoption
        
        self.analysis_results['feature_adoption'] = {
            'overall': feature_adoption,
            'by_brand': feature_by_brand
        }
        
        # Agregar insight sobre característica más común
        if feature_adoption:
            most_common_feature = max(feature_adoption.items(), key=lambda x: x[1])
            self.analysis_results['insights'].append({
                'tipo': 'caracteristica_popular',
                'mensaje': f"'{most_common_feature[0]}' es la característica más común, presente en el {most_common_feature[1]}% de los drones",
                'datos': feature_adoption
            })
        
        return feature_adoption
    
    def generate_solution_data(self) -> Dict[str, Any]:
        """
        Generar datos optimizados para el frontend
        
        Returns:
            Diccionario con todos los datos necesarios para la web
        """
        # Asegurar que todos los análisis estén ejecutados
        if 'price_performance_ratio' not in self.drones_df.columns:
            self.calculate_price_performance_ratio()
        
        self.identify_market_segments()
        self.find_best_value_by_category()
        self.analyze_price_trends()
        self.calculate_feature_adoption()
        
        # Preparar datos para frontend
        solution_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_drones': len(self.drones_df),
                'brands': list(self.drones_df['marca'].unique()),
                'price_range': {
                    'min': float(self.drones_df['precio_usd'].min()) if 'precio_usd' in self.drones_df.columns else 0,
                    'max': float(self.drones_df['precio_usd'].max()) if 'precio_usd' in self.drones_df.columns else 0
                }
            },
            'drones': [],
            'filters': {
                'brands': list(self.drones_df['marca'].unique()),
                'categories': list(self.drones_df['clasificacion_categoria_peso'].unique()) if 'clasificacion_categoria_peso' in self.drones_df.columns else [],
                'user_levels': list(self.drones_df['clasificacion_nivel_usuario'].unique()) if 'clasificacion_nivel_usuario' in self.drones_df.columns else [],
                'video_resolutions': list(self.drones_df['camara_resolucion_video'].dropna().unique()) if 'camara_resolucion_video' in self.drones_df.columns else []
            },
            'market_insights': {
                'segments': self.analysis_results['market_segments'],
                'price_trends': self.analysis_results.get('price_trends', {}),
                'feature_adoption': self.analysis_results.get('feature_adoption', {}),
                'best_values': self.analysis_results.get('price_performance', {})
            },
            'insights': self.analysis_results['insights']
        }
        
        # Convertir DataFrame a lista de diccionarios optimizada
        for idx, drone in self.drones_df.iterrows():
            drone_data = {
                'id': idx,
                'modelo': drone.get('modelo', 'Unknown'),
                'marca': drone.get('marca', 'Unknown'),
                'precio': float(drone.get('precio_usd', 0)) if pd.notna(drone.get('precio_usd')) else None,
                'imagen': f"/assets/drone_icons/{drone.get('marca', 'generic').lower()}.png",
                'specs': {
                    'peso': float(drone.get('especificaciones_tecnicas_peso_gramos', 0)) if pd.notna(drone.get('especificaciones_tecnicas_peso_gramos')) else None,
                    'autonomia': float(drone.get('especificaciones_tecnicas_autonomia_minutos', 0)) if pd.notna(drone.get('especificaciones_tecnicas_autonomia_minutos')) else None,
                    'alcance': float(drone.get('especificaciones_tecnicas_alcance_metros', 0)) if pd.notna(drone.get('especificaciones_tecnicas_alcance_metros')) else None,
                    'velocidad': float(drone.get('especificaciones_tecnicas_velocidad_max_kmh', 0)) if pd.notna(drone.get('especificaciones_tecnicas_velocidad_max_kmh')) else None,
                    'resistencia_viento': drone.get('especificaciones_tecnicas_resistencia_viento'),
                    'temperatura': drone.get('especificaciones_tecnicas_temperatura_operacion')
                },
                'camara': {
                    'resolucion': drone.get('camara_resolucion_video'),
                    'fps': float(drone.get('camara_fps_max', 0)) if pd.notna(drone.get('camara_fps_max')) else None,
                    'sensor': drone.get('camara_sensor_tamaño'),
                    'estabilizacion': drone.get('camara_estabilizacion'),
                    'zoom_optico': float(drone.get('camara_zoom_optico', 0)) if pd.notna(drone.get('camara_zoom_optico')) else None,
                    'zoom_digital': float(drone.get('camara_zoom_digital', 0)) if pd.notna(drone.get('camara_zoom_digital')) else None
                },
                'features': {
                    'evita_obstaculos': bool(drone.get('caracteristicas_vuelo_evita_obstaculos', False)),
                    'retorno_automatico': bool(drone.get('caracteristicas_vuelo_retorno_automatico', False)),
                    'seguimiento_objeto': bool(drone.get('caracteristicas_vuelo_seguimiento_objeto', False)),
                    'vuelo_nocturno': bool(drone.get('caracteristicas_vuelo_vuelo_nocturno', False)),
                    'modo_sport': bool(drone.get('caracteristicas_vuelo_modo_sport', False))
                },
                'clasificacion': {
                    'categoria': drone.get('clasificacion_categoria_peso'),
                    'nivel': drone.get('clasificacion_nivel_usuario'),
                    'usos': drone.get('clasificacion_uso_principal', [])
                },
                'metrics': {
                    'performance_score': float(drone.get('performance_score', 0)) if pd.notna(drone.get('performance_score')) else None,
                    'price_performance_ratio': float(drone.get('price_performance_ratio', 0)) if pd.notna(drone.get('price_performance_ratio')) else None
                },
                'url': drone.get('url_fuente')
            }
            
            solution_data['drones'].append(drone_data)
        
        return solution_data
    
    def save_results(self, output_dir: str = '../analysis'):
        """Guardar resultados del análisis"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Guardar datos para frontend
        solution_data = self.generate_solution_data()
        with open(output_path / 'solution_data.json', 'w', encoding='utf-8') as f:
            json.dump(solution_data, f, ensure_ascii=False, indent=2)
        
        # Guardar reporte de análisis
        with open(output_path / 'analysis_report.json', 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Resultados guardados en {output_path}")


def main():
    """Función principal de análisis"""
    analyzer = FocusedDroneAnalyzer()
    
    # Cargar datos
    analyzer.load_data()
    
    # Ejecutar análisis completo
    logger.info("Calculando scores de rendimiento...")
    analyzer.calculate_performance_score()
    
    logger.info("Identificando segmentos de mercado...")
    analyzer.identify_market_segments()
    
    logger.info("Encontrando mejores valores por categoría...")
    analyzer.find_best_value_by_category()
    
    logger.info("Analizando tendencias de rendimiento...")
    analyzer.analyze_performance_trends()
    
    logger.info("Calculando adopción de características...")
    analyzer.calculate_feature_adoption()
    
    # Ejemplo de recomendación personalizada
    test_profiles = [
        {
            'experience_level': 'principiante',
            'primary_use': 'recreativo',
            'must_have_features': ['retorno_automatico']
        },
        {
            'experience_level': 'intermedio',
            'primary_use': 'fotografia',
            'must_have_features': ['evita_obstaculos', 'seguimiento_objeto']
        },
        {
            'experience_level': 'profesional',
            'primary_use': 'video_profesional',
            'must_have_features': ['evita_obstaculos', 'modo_sport']
        }
    ]
    
    for profile in test_profiles:
        logger.info(f"\nGenerando recomendaciones para perfil: {profile['primary_use']} - {profile['experience_level']}")
        recommendations = analyzer.generate_buying_recommendations(profile)
        
        for rec in recommendations[:3]:
            logger.info(f"  {rec['rank']}. {rec['modelo']} - Score: {rec['score']:.1f}")
    
    # Guardar resultados
    analyzer.save_results()
    
    logger.info("\nAnálisis completado exitosamente")


if __name__ == "__main__":
    main()
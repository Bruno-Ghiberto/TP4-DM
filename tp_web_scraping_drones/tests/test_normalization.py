"""
Tests para verificar el proceso de normalización de datos.
"""

import json
import unittest
import sys
from pathlib import Path

# Agregar el directorio padre al path para poder importar módulos
sys.path.append(str(Path(__file__).parent.parent))

from normalize_data import DroneDataNormalizer


class TestNormalization(unittest.TestCase):
    """Tests para verificar el proceso de normalización."""
    
    def setUp(self):
        """Crear una instancia del normalizador para cada test."""
        self.normalizer = DroneDataNormalizer()
        
    def test_normalize_model_name(self):
        """Verificar la normalización de nombres de modelos."""
        # Casos de prueba
        casos = [
            ('EVO II', 'Evo II'),
            ('EVO Max', 'Evo Max'),
            ('ANAFI', 'Anafi'),
            ('DJI Mavic 3', 'Mavic 3'),
            ('  Mini 3  ', 'Mini 3'),
            ('unknown', 'Modelo Desconocido'),
            ('', 'Modelo Desconocido'),
            ('Evo II Series', 'Evo II Series'),
        ]
        
        for entrada, esperado in casos:
            resultado = self.normalizer._normalize_model_name(entrada)
            self.assertEqual(
                resultado, esperado,
                f"Normalización incorrecta: '{entrada}' -> '{resultado}' (esperado: '{esperado}')"
            )
    
    def test_normalize_brand(self):
        """Verificar la normalización de marcas."""
        casos = [
            ('dji', 'DJI'),
            ('DJI', 'DJI'),
            ('autel', 'Autel'),
            ('AUTEL', 'Autel'),
            ('parrot', 'Parrot'),
            ('PARROT', 'Parrot'),
            ('unknown', 'Unknown'),  # Marca desconocida
        ]
        
        for entrada, esperado in casos:
            resultado = self.normalizer._normalize_brand(entrada)
            self.assertEqual(
                resultado, esperado,
                f"Marca incorrecta: '{entrada}' -> '{resultado}' (esperado: '{esperado}')"
            )
    
    def test_categorize_drone(self):
        """Verificar la categorización de drones por peso."""
        # Casos de prueba con diferentes pesos
        casos = [
            ({'especificaciones_tecnicas': {'peso_gramos': 200}, 'modelo': 'Mini'}, 'Mini / Recreativo'),
            ({'especificaciones_tecnicas': {'peso_gramos': 500}, 'modelo': 'Air'}, 'Consumer'),
            ({'especificaciones_tecnicas': {'peso_gramos': 800}, 'modelo': 'Pro'}, 'Prosumer'),
            ({'especificaciones_tecnicas': {'peso_gramos': 1200}, 'modelo': 'Enterprise'}, 'Enterprise'),
            ({'especificaciones_tecnicas': {'peso_gramos': 5000}, 'modelo': 'Industrial'}, 'Industrial'),
        ]
        
        for drone_data, categoria_esperada in casos:
            resultado = self.normalizer._categorize_drone(drone_data)
            self.assertEqual(
                resultado, categoria_esperada,
                f"Categoría incorrecta para {drone_data['modelo']}: '{resultado}' (esperado: '{categoria_esperada}')"
            )
    
    def test_normalize_dimensions(self):
        """Verificar la normalización de dimensiones."""
        casos = [
            ('231.1×98×95.4', '231.1×98×95.4 mm'),
            ('231.1 × 98 × 95.4', '231.1×98×95.4 mm'),
            ('231.1x98x95.4', '231.1×98×95.4 mm'),
            ('231×98×95 mm', '231×98×95 mm'),
            ('231×98×95 (plegado)', '231×98×95 mm'),
            ('', None),
            ('abc', None),  # Sin números
        ]
        
        for entrada, esperado in casos:
            resultado = self.normalizer._normalize_dimensions(entrada)
            self.assertEqual(
                resultado, esperado,
                f"Dimensiones incorrectas: '{entrada}' -> '{resultado}' (esperado: '{esperado}')"
            )
    
    def test_normalize_camera_sensor(self):
        """Verificar la normalización del sensor de cámara."""
        casos = [
            ('1/2" 48 MP CMOS', '1/2" 48 MP CMOS'),
            ('1 inch CMOS, 20 million pixels', '1 inch 20 MP CMOS'),
            ('Hasselblad Camera: 4/3 CMOS, Effective Pixels: 20 MP', 'Hasselblad 4/3 CMOS 20 MP'),
            ('', 'No especificado'),
            ('CMOS sensor with very long technical description that goes on and on', 'CMOS sensor with very long technical description th...'),
        ]
        
        for entrada, esperado in casos:
            resultado = self.normalizer._normalize_camera_sensor(entrada)
            self.assertEqual(
                resultado, esperado,
                f"Sensor incorrecto: '{entrada}' -> '{resultado}' (esperado: '{esperado}')"
            )
    
    def test_normalize_video_resolution(self):
        """Verificar la normalización de resolución de video."""
        casos = [
            ('4K UHD: 3840x2160', '4K'),
            ('8K: 7680×4320, 4K: 3840×2160', '8K / 4K'),
            ('1080p: 1920x1080', '1080p'),
            ('6K/4K/1080p', '6K / 4K / 1080p'),
            ('5120×2700@24/25/30fps', '5120×2700'),
            ('', 'No especificado'),
        ]
        
        for entrada, esperado in casos:
            resultado = self.normalizer._normalize_video_resolution(entrada)
            # Verificar que el resultado contiene los elementos esperados
            if esperado != 'No especificado':
                for parte in esperado.split(' / '):
                    self.assertIn(
                        parte, resultado,
                        f"Resolución '{entrada}' no contiene '{parte}' en resultado '{resultado}'"
                    )
    
    def test_extract_key_features(self):
        """Verificar la extracción de características destacadas."""
        specs = {
            'vuelo_minutos': 45,
            'alcance_video_km': 15,
            'resolucion_video': '4K UHD',
            'sensor_camara': 'Hasselblad 48 MP',
            'deteccion_obstaculos': True,
            'peso_gramos': 200
        }
        
        features = self.normalizer._extract_key_features(specs)
        
        # Verificar que se extraen las características correctas
        self.assertIn('Hasta 45 min de vuelo', features)
        self.assertIn('Alcance 15 km', features)
        self.assertIn('Video 4K', features)
        self.assertIn('Cámara Hasselblad', features)
        self.assertIn('Evitación de obstáculos', features)
        self.assertIn('Ultraligero (<250g)', features)
        
        # Máximo 4 características
        self.assertLessEqual(len(features), 4)
    
    def test_calculate_score(self):
        """Verificar el cálculo de puntuación."""
        # Drone básico
        drone_basico = {
            'especificaciones_tecnicas': {
                'vuelo_minutos': 20,
                'alcance_video_km': 2,
            }
        }
        score_basico = self.normalizer._calculate_score(drone_basico)
        self.assertGreaterEqual(score_basico, 0)
        self.assertLessEqual(score_basico, 10)
        
        # Drone avanzado
        drone_avanzado = {
            'especificaciones_tecnicas': {
                'vuelo_minutos': 45,
                'alcance_video_km': 15,
                'deteccion_obstaculos': True,
                'resolucion_video': '4K',
                'peso_gramos': 200
            }
        }
        score_avanzado = self.normalizer._calculate_score(drone_avanzado)
        self.assertGreater(score_avanzado, score_basico)
        self.assertLessEqual(score_avanzado, 10)
    
    def test_normalize_drone_complete(self):
        """Verificar la normalización completa de un drone."""
        drone_input = {
            'modelo': 'DJI Mavic 3 Pro',
            'marca': 'dji',
            'url': 'https://example.com',
            'especificaciones_tecnicas': {
                'peso_gramos': 958,
                'dimensiones_plegado': '231.1×98×95.4',
                'vuelo_minutos': 43,
                'vel_horizontal_mps': 21,
                'vel_ascenso_mps': 8,
                'alcance_video_km': 15,
                'sensor_camara': 'Hasselblad 4/3 CMOS 20MP',
                'resolucion_video': '4K',
                'deteccion_obstaculos': True
            }
        }
        
        resultado = self.normalizer.normalize_drone(drone_input)
        
        # Verificar campos principales
        self.assertEqual(resultado['modelo'], 'Mavic 3 Pro')
        self.assertEqual(resultado['marca'], 'DJI')
        self.assertEqual(resultado['categoria'], 'Prosumer')
        self.assertIn('fecha_actualizacion', resultado)
        self.assertIsInstance(resultado['puntuacion_general'], float)
        
        # Verificar especificaciones normalizadas
        specs = resultado['especificaciones_tecnicas']
        self.assertEqual(specs['peso_gramos'], 958)
        self.assertEqual(specs['dimensiones_plegado'], '231.1×98×95.4 mm')
        self.assertTrue(specs['deteccion_obstaculos'])
        
        # Verificar características destacadas
        self.assertIn('caracteristicas_destacadas', specs)
        self.assertIsInstance(specs['caracteristicas_destacadas'], list)
    
    def test_normalize_all_drones(self):
        """Verificar la normalización de múltiples drones."""
        drones_input = [
            {
                'modelo': 'Mini 3',
                'marca': 'DJI',
                'especificaciones_tecnicas': {'peso_gramos': 248}
            },
            {
                'modelo': 'invalid_drone',
                'marca': 'unknown',
                'especificaciones_tecnicas': {}
            }
        ]
        
        normalizados = self.normalizer.normalize_all_drones(drones_input)
        
        # Debe normalizar todos los drones válidos
        self.assertGreaterEqual(len(normalizados), 1)
        self.assertEqual(self.normalizer.normalized_count, len(normalizados))
        
        # Verificar resumen
        summary = self.normalizer.get_summary()
        self.assertIn('total_normalized', summary)
        self.assertIn('issues_found', summary)


if __name__ == '__main__':
    unittest.main() 
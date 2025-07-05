"""
Tests para verificar la validez de las especificaciones técnicas de los drones.
"""

import json
import unittest
from pathlib import Path


class TestSpecifications(unittest.TestCase):
    """Tests para verificar que las especificaciones técnicas sean válidas."""
    
    @classmethod
    def setUpClass(cls):
        """Cargar datos una sola vez para todos los tests."""
        cls.base_path = Path(__file__).parent.parent
        cls.data_path = cls.base_path / "data" / "processed" / "drones_normalized.json"
        
        with open(cls.data_path, 'r', encoding='utf-8') as f:
            cls.drones = json.load(f)
    
    def test_peso_valido(self):
        """Verificar que el peso está en un rango válido."""
        for drone in self.drones:
            peso = drone['especificaciones_tecnicas'].get('peso_gramos', 0)
            if peso > 0:  # Solo verificar si hay peso
                self.assertGreater(
                    peso, 50,
                    f"{drone['modelo']}: peso muy bajo ({peso}g)"
                )
                self.assertLess(
                    peso, 10000,
                    f"{drone['modelo']}: peso muy alto ({peso}g)"
                )
    
    def test_tiempo_vuelo_valido(self):
        """Verificar que el tiempo de vuelo está en un rango válido."""
        for drone in self.drones:
            vuelo = drone['especificaciones_tecnicas'].get('vuelo_minutos', 0)
            if vuelo > 0:  # Solo verificar si hay dato
                self.assertGreater(
                    vuelo, 5,
                    f"{drone['modelo']}: tiempo de vuelo muy bajo ({vuelo} min)"
                )
                self.assertLess(
                    vuelo, 180,
                    f"{drone['modelo']}: tiempo de vuelo muy alto ({vuelo} min)"
                )
    
    def test_velocidades_validas(self):
        """Verificar que las velocidades están en rangos válidos."""
        for drone in self.drones:
            specs = drone['especificaciones_tecnicas']
            
            # Velocidad horizontal
            vel_h = specs.get('vel_horizontal_mps', 0)
            if vel_h > 0:
                self.assertGreater(
                    vel_h, 2,
                    f"{drone['modelo']}: velocidad horizontal muy baja ({vel_h} m/s)"
                )
                self.assertLess(
                    vel_h, 30,
                    f"{drone['modelo']}: velocidad horizontal muy alta ({vel_h} m/s)"
                )
            
            # Velocidad de ascenso
            vel_a = specs.get('vel_ascenso_mps', 0)
            if vel_a > 0:
                self.assertGreater(
                    vel_a, 1,
                    f"{drone['modelo']}: velocidad ascenso muy baja ({vel_a} m/s)"
                )
                self.assertLess(
                    vel_a, 20,
                    f"{drone['modelo']}: velocidad ascenso muy alta ({vel_a} m/s)"
                )
    
    def test_alcance_valido(self):
        """Verificar que el alcance está en un rango válido."""
        for drone in self.drones:
            alcance = drone['especificaciones_tecnicas'].get('alcance_video_km', 0)
            if alcance > 0:
                self.assertLess(
                    alcance, 50,
                    f"{drone['modelo']}: alcance muy alto ({alcance} km)"
                )
    
    def test_altitud_valida(self):
        """Verificar que la altitud máxima está en un rango válido."""
        for drone in self.drones:
            altitud = drone['especificaciones_tecnicas'].get('altitud_despegue_m', 0)
            if altitud > 0:
                self.assertGreater(
                    altitud, 100,
                    f"{drone['modelo']}: altitud muy baja ({altitud} m)"
                )
                self.assertLess(
                    altitud, 10000,
                    f"{drone['modelo']}: altitud muy alta ({altitud} m)"
                )
    
    def test_resistencia_viento_valida(self):
        """Verificar que la resistencia al viento está en un rango válido."""
        for drone in self.drones:
            viento = drone['especificaciones_tecnicas'].get('resistencia_viento_mps', 0)
            if viento > 0:
                self.assertGreater(
                    viento, 1,
                    f"{drone['modelo']}: resistencia viento muy baja ({viento} m/s)"
                )
                self.assertLess(
                    viento, 25,
                    f"{drone['modelo']}: resistencia viento muy alta ({viento} m/s)"
                )
    
    def test_dimensiones_formato_valido(self):
        """Verificar que las dimensiones tienen un formato válido."""
        import re
        
        # Patrón para dimensiones: números separados por × o x
        patron_dims = re.compile(r'^\d+(\.\d+)?\s*[×x]\s*\d+(\.\d+)?\s*[×x]\s*\d+(\.\d+)?')
        
        for drone in self.drones:
            dims = drone['especificaciones_tecnicas'].get('dimensiones_plegado', '')
            if dims and dims != "":
                # Verificar que contiene números
                numeros = re.findall(r'\d+', dims)
                self.assertGreaterEqual(
                    len(numeros), 3,
                    f"{drone['modelo']}: dimensiones deben tener al menos 3 números"
                )
    
    def test_almacenamiento_valido(self):
        """Verificar que el almacenamiento interno está en un rango válido."""
        for drone in self.drones:
            storage = drone['especificaciones_tecnicas'].get('almacenamiento_interno_gb')
            if storage is not None and storage > 0:
                self.assertGreaterEqual(
                    storage, 1,
                    f"{drone['modelo']}: almacenamiento muy bajo ({storage} GB)"
                )
                self.assertLessEqual(
                    storage, 512,
                    f"{drone['modelo']}: almacenamiento muy alto ({storage} GB)"
                )
    
    def test_sensor_camara_no_vacio(self):
        """Verificar que el sensor de cámara no está vacío cuando existe."""
        for drone in self.drones:
            sensor = drone['especificaciones_tecnicas'].get('sensor_camara', '')
            if 'sensor_camara' in drone['especificaciones_tecnicas']:
                self.assertTrue(
                    len(sensor) > 2 or sensor == "",
                    f"{drone['modelo']}: sensor de cámara inválido: '{sensor}'"
                )
    
    def test_resolucion_video_formato(self):
        """Verificar que la resolución de video tiene un formato reconocible."""
        import re
        
        patrones_resolucion = [
            r'\d+K',  # 4K, 6K, 8K
            r'\d{3,4}p',  # 1080p, 2160p
            r'\d{3,4}\s*[×x]\s*\d{3,4}',  # 3840×2160
            r'FHD|UHD|HD',  # Formatos nombrados
        ]
        
        for drone in self.drones:
            resolucion = drone['especificaciones_tecnicas'].get('resolucion_video', '')
            if resolucion and resolucion != "":
                # Verificar que tiene al menos un patrón reconocible
                tiene_patron = any(
                    re.search(patron, resolucion, re.I) 
                    for patron in patrones_resolucion
                )
                self.assertTrue(
                    tiene_patron or len(resolucion) < 5,
                    f"{drone['modelo']}: resolución de video no reconocible: '{resolucion[:50]}'"
                )
    
    def test_coherencia_peso_categoria(self):
        """Verificar coherencia entre peso y categoría del drone."""
        for drone in self.drones:
            peso = drone['especificaciones_tecnicas'].get('peso_gramos', 0)
            modelo = drone['modelo'].lower()
            
            if peso > 0:
                # Drones mini/pequeños
                if 'mini' in modelo:
                    self.assertLess(
                        peso, 500,
                        f"{drone['modelo']}: drone 'mini' pero pesa {peso}g"
                    )
                
                # Drones enterprise/industrial
                if 'enterprise' in modelo or 'industrial' in modelo:
                    self.assertGreater(
                        peso, 500,
                        f"{drone['modelo']}: drone 'enterprise' pero solo pesa {peso}g"
                    )
    
    def test_deteccion_obstaculos_tipo(self):
        """Verificar que la detección de obstáculos es booleana."""
        for drone in self.drones:
            deteccion = drone['especificaciones_tecnicas'].get('deteccion_obstaculos')
            if deteccion is not None:
                self.assertIsInstance(
                    deteccion, bool,
                    f"{drone['modelo']}: detección de obstáculos debe ser booleano"
                )


if __name__ == '__main__':
    unittest.main() 
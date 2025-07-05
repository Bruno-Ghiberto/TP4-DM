"""
Tests para verificar la integridad general de los datos de drones.
"""

import json
import os
import unittest
from pathlib import Path


class TestDataIntegrity(unittest.TestCase):
    """Tests para verificar la integridad de los archivos de datos."""
    
    @classmethod
    def setUpClass(cls):
        """Configurar rutas de archivos para todos los tests."""
        cls.base_path = Path(__file__).parent.parent
        cls.raw_data_path = cls.base_path / "data" / "processed" / "drones_normalized.json"
        cls.web_data_path = cls.base_path / "data" / "processed" / "drones_web_ready.json"
        
    def test_archivos_existen(self):
        """Verificar que los archivos de datos existen."""
        self.assertTrue(
            self.raw_data_path.exists(), 
            f"El archivo {self.raw_data_path} no existe"
        )
        self.assertTrue(
            self.web_data_path.exists(), 
            f"El archivo {self.web_data_path} no existe"
        )
        
    def test_archivos_json_validos(self):
        """Verificar que los archivos son JSON válidos."""
        # Verificar archivo raw
        try:
            with open(self.raw_data_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                self.assertIsInstance(raw_data, list, "Los datos raw deben ser una lista")
        except json.JSONDecodeError as e:
            self.fail(f"El archivo {self.raw_data_path} no es JSON válido: {e}")
            
        # Verificar archivo web
        try:
            with open(self.web_data_path, 'r', encoding='utf-8') as f:
                web_data = json.load(f)
                self.assertIsInstance(web_data, list, "Los datos web deben ser una lista")
        except json.JSONDecodeError as e:
            self.fail(f"El archivo {self.web_data_path} no es JSON válido: {e}")
            
    def test_datos_no_vacios(self):
        """Verificar que los archivos contienen datos."""
        with open(self.raw_data_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            self.assertGreater(len(raw_data), 0, "Los datos raw no deben estar vacíos")
            
        with open(self.web_data_path, 'r', encoding='utf-8') as f:
            web_data = json.load(f)
            self.assertGreater(len(web_data), 0, "Los datos web no deben estar vacíos")
            
    def test_campos_requeridos(self):
        """Verificar que cada drone tiene los campos requeridos."""
        campos_requeridos = ['modelo', 'marca', 'especificaciones_tecnicas']
        
        with open(self.raw_data_path, 'r', encoding='utf-8') as f:
            drones = json.load(f)
            
        for i, drone in enumerate(drones):
            for campo in campos_requeridos:
                self.assertIn(
                    campo, drone,
                    f"Drone {i} no tiene el campo requerido '{campo}'"
                )
                
    def test_tipos_datos_correctos(self):
        """Verificar que los tipos de datos son correctos."""
        with open(self.raw_data_path, 'r', encoding='utf-8') as f:
            drones = json.load(f)
            
        for i, drone in enumerate(drones):
            # Verificar tipos básicos
            self.assertIsInstance(
                drone.get('modelo'), str,
                f"Drone {i}: 'modelo' debe ser string"
            )
            self.assertIsInstance(
                drone.get('marca'), str,
                f"Drone {i}: 'marca' debe ser string"
            )
            self.assertIsInstance(
                drone.get('especificaciones_tecnicas'), dict,
                f"Drone {i}: 'especificaciones_tecnicas' debe ser dict"
            )
            
    def test_marcas_validas(self):
        """Verificar que las marcas son las esperadas."""
        marcas_validas = ['DJI', 'Autel', 'Parrot']
        
        with open(self.raw_data_path, 'r', encoding='utf-8') as f:
            drones = json.load(f)
            
        for i, drone in enumerate(drones):
            marca = drone.get('marca', '').strip()
            self.assertIn(
                marca, marcas_validas,
                f"Drone {i}: marca '{marca}' no es válida. Debe ser una de: {marcas_validas}"
            )
            
    def test_modelos_unicos(self):
        """Verificar que no hay modelos duplicados."""
        with open(self.raw_data_path, 'r', encoding='utf-8') as f:
            drones = json.load(f)
            
        modelos = [drone.get('modelo', '') for drone in drones]
        modelos_unicos = set(modelos)
        
        self.assertEqual(
            len(modelos), len(modelos_unicos),
            f"Hay modelos duplicados. Total: {len(modelos)}, Únicos: {len(modelos_unicos)}"
        )
        
    def test_estructura_especificaciones(self):
        """Verificar la estructura de especificaciones técnicas."""
        campos_esperados = [
            'peso_gramos', 'dimensiones_plegado', 'vuelo_minutos',
            'vel_horizontal_mps', 'vel_ascenso_mps', 'resistencia_viento_mps',
            'altitud_despegue_m', 'sensor_camara', 'resolucion_video'
        ]
        
        with open(self.raw_data_path, 'r', encoding='utf-8') as f:
            drones = json.load(f)
            
        for i, drone in enumerate(drones):
            specs = drone.get('especificaciones_tecnicas', {})
            
            # Verificar que al menos algunos campos están presentes
            campos_presentes = [campo for campo in campos_esperados if campo in specs]
            self.assertGreater(
                len(campos_presentes), 3,
                f"Drone {i} ({drone.get('modelo')}): muy pocos campos de especificaciones"
            )


if __name__ == '__main__':
    unittest.main() 
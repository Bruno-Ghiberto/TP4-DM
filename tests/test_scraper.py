# Tests unitarios para el módulo de scraping

import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraping.robot_checker import RobotChecker
from scraping.data_cleaner import DataCleaner
from scraping.data_validator import DataValidator


class TestRobotChecker(unittest.TestCase):
    """Tests para el verificador de robots.txt"""
    
    def setUp(self):
        self.checker = RobotChecker()
    
    def test_can_scrape_basic(self):
        """Test verificación básica de scraping"""
        # Test con URL conocida
        can_scrape, message = self.checker.can_scrape_advanced('https://example.com')
        self.assertIsInstance(can_scrape, bool)
        self.assertIsInstance(message, str)
    
    def test_crawl_delay(self):
        """Test obtención de crawl delay"""
        delay = self.checker.get_crawl_delay('https://example.com/robots.txt')
        self.assertGreaterEqual(delay, 3.0)  # Mínimo ético


class TestDataCleaner(unittest.TestCase):
    """Tests para el limpiador de datos"""
    
    def setUp(self):
        self.cleaner = DataCleaner()
    
    def test_normalize_price(self):
        """Test normalización de precios"""
        test_cases = [
            ("$1,299.99", 1299.99),
            ("€1.299,00", 1299.0),
            ("USD 2499", 2499.0),
            ("1299", 1299.0)
        ]
        
        for input_price, expected in test_cases:
            result = self.cleaner.normalize_price_formats(input_price)
            self.assertEqual(result, expected)
    
    def test_extract_number(self):
        """Test extracción de números con unidades"""
        test_cases = [
            ("249 grams", "grams", 249),
            ("1.2 kg", "grams", 1200),
            ("10 km", "meters", 10000),
            ("45 minutes", "minutes", 45)
        ]
        
        for input_text, unit_type, expected in test_cases:
            result = self.cleaner.extract_number(input_text, unit_type)
            self.assertEqual(result, expected)


class TestDataValidator(unittest.TestCase):
    """Tests para el validador de datos"""
    
    def setUp(self):
        self.validator = DataValidator()
    
    def test_valid_drone(self):
        """Test validación de drone válido"""
        valid_drone = {
            "modelo": "Test Drone",
            "marca": "DJI",
            "especificaciones_tecnicas": {
                "peso_gramos": 500,
                "autonomia_minutos": 30,
                "alcance_metros": 5000
            },
            "clasificacion": {
                "categoria_peso": "ligero",
                "nivel_usuario": "intermedio",
                "uso_principal": ["recreativo"]
            }
        }
        
        is_valid, errors = self.validator.validate_drone_data(valid_drone)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_invalid_drone(self):
        """Test validación de drone inválido"""
        invalid_drone = {
            "modelo": "Test Drone",
            "marca": "InvalidBrand",  # Marca no válida
            "especificaciones_tecnicas": {
                "peso_gramos": -100  # Peso negativo
            }
        }
        
        is_valid, errors = self.validator.validate_drone_data(invalid_drone)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


if __name__ == '__main__':
    unittest.main()
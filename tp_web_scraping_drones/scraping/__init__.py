"""
Paquete de web scraping de drones.

Este paquete contiene todos los módulos necesarios para extraer especificaciones
técnicas de drones de DJI, Autel Robotics y Parrot.
"""

__version__ = "1.0.0"
__author__ = "IES Data Science & AI"

# Importaciones principales
from .scraper import DroneScraperOrchestrator
from .utils import (
    normalize_text, extract_number, validate_drone_data,
    normalize_weight, normalize_price
)

__all__ = [
    'DroneScraperOrchestrator',
    'normalize_text',
    'extract_number', 
    'validate_drone_data',
    'normalize_weight',
    'normalize_price'
] 
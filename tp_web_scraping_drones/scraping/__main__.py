"""Punto de entrada para el módulo de scraping cuando se ejecuta con python -m scraping."""

import sys
import os

# Agregar directorio padre al path para evitar problemas de importación
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar después del ajuste de path
from scraping.scraper import main

if __name__ == "__main__":
    main() 
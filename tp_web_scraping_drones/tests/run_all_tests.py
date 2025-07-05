"""
Script para ejecutar todos los tests del proyecto.
"""

import unittest
import sys
from pathlib import Path

# Agregar el directorio padre al path
sys.path.append(str(Path(__file__).parent.parent))


def run_all_tests():
    """Ejecutar todos los tests del proyecto."""
    # Descubrir y ejecutar todos los tests
    loader = unittest.TestLoader()
    start_dir = str(Path(__file__).parent)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Ejecutar tests con verbosidad
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Retornar código de salida apropiado
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    print("=" * 70)
    print("EJECUTANDO TODOS LOS TESTS DEL PROYECTO")
    print("=" * 70)
    
    exit_code = run_all_tests()
    
    print("\n" + "=" * 70)
    if exit_code == 0:
        print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
    print("=" * 70)
    
    sys.exit(exit_code) 
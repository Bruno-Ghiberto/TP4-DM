# Tests del Proyecto Web Scraping Drones

Este directorio contiene los tests unitarios para verificar la integridad y calidad de los datos obtenidos del web scraping de drones.

## Estructura de Tests

- **`test_data_integrity.py`**: Verifica la integridad general de los archivos de datos
  - Existencia de archivos JSON
  - Validez del formato JSON
  - Campos requeridos presentes
  - Tipos de datos correctos
  - Marcas válidas
  - Modelos únicos

- **`test_specifications.py`**: Valida las especificaciones técnicas de los drones
  - Rangos válidos para peso, velocidad, alcance, etc.
  - Formato correcto de dimensiones
  - Coherencia entre categoría y especificaciones
  - Validación de resoluciones de video

- **`test_normalization.py`**: Prueba el proceso de normalización de datos
  - Normalización de nombres de modelos
  - Normalización de marcas
  - Categorización por peso
  - Extracción de características destacadas
  - Cálculo de puntuaciones

- **`test_images.py`**: Verifica las imágenes de los drones
  - Existencia de archivos de imagen
  - Formatos de imagen válidos
  - Tamaños razonables
  - Coherencia entre modelo e imagen

## Cómo Ejecutar los Tests

### Ejecutar todos los tests:
```bash
python tests/run_all_tests.py
```

### Ejecutar un test específico:
```bash
python -m unittest tests.test_data_integrity
```

### Ejecutar con más detalle:
```bash
python -m unittest -v tests.test_specifications
```

## Requisitos

Los tests requieren que existan los siguientes archivos:
- `data/processed/drones_normalized.json`
- `data/processed/drones_web_ready.json`
- Carpeta `data/images/` con las imágenes de drones

## Interpretación de Resultados

- ✅ **OK**: El test pasó correctamente
- ❌ **FAIL**: El test falló - revisar el mensaje de error
- ⚠️ **WARNING**: Advertencia no crítica (ej: imágenes no utilizadas)

## Agregar Nuevos Tests

Para agregar un nuevo test:
1. Crear un archivo `test_nuevo.py` en esta carpeta
2. Importar `unittest`
3. Crear una clase que herede de `unittest.TestCase`
4. Agregar métodos que empiecen con `test_`

Ejemplo:
```python
import unittest

class TestNuevo(unittest.TestCase):
    def test_algo(self):
        self.assertTrue(True)
``` 
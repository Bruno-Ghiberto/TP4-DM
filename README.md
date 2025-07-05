# 🚁 ARKA DRONES

Sistema completo de web scraping para recopilar, normalizar y visualizar especificaciones técnicas de drones de las principales marcas del mercado.

## 🎯 Características Principales

- **Web Scraping Inteligente**: Extracción de datos de DJI, Autel Robotics y Parrot
- **Normalización Automática**: Limpieza y estandarización de especificaciones técnicas
- **Interfaz Web Moderna**: Catálogo interactivo con filtros avanzados y comparación
- **Cumplimiento Ético**: Respeto automático de robots.txt

## 🚀 Instalación

### Requisitos
- Python 3.8+
- Chrome/Chromium (para contenido dinámico)
- Git

### Configuración Rápida

```bash
# Clonar repositorio
git clone <repository-url>
cd tp_web_scraping_drones

# Crear entorno virtual
python -m venv venv

# Activar entorno
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## 💻 Uso

### Pipeline Completo
```bash
python run_complete_pipeline.py
```

Este comando ejecuta automáticamente:
1. Web scraping de todas las fuentes
2. Normalización y validación de datos
3. Preparación para visualización web
4. Generación de estadísticas

### Componentes Individuales

**Web Scraping**
```bash
python -m scraping --parallel     # Modo paralelo (recomendado)
python -m scraping --sequential   # Modo secuencial
```

**Normalización**
```bash
python normalize_data.py
```

**Visualización Web**
```bash
python web/serve_web.py
# Acceder a http://localhost:8000
```

## 📊 Datos Extraídos

### Especificaciones Técnicas
- Peso y dimensiones plegadas
- Tiempo de vuelo y velocidades
- Alcance de transmisión
- Altitud máxima de operación
- Resistencia al viento
- Almacenamiento interno
- Sensor de cámara y resolución de video
- Sistema de detección de obstáculos

### Categorización Automática
- **Mini/Recreativo**: < 250g
- **Consumer**: 250g - 1kg
- **Prosumer**: Modelos pro/classic < 1kg
- **Profesional**: 1kg - 2kg
- **Enterprise**: Modelos especializados
- **Industrial**: > 2kg

## 📁 Estructura del Proyecto

```
tp_web_scraping_drones/
├── scraping/           # Módulo principal de scraping
│   ├── parsers/       # Parsers específicos por marca
│   └── *.py          # Orquestador y utilidades
├── data/              # Almacenamiento de datos
│   ├── processed/    # JSON normalizado y web-ready
│   └── images/       # Imágenes de productos
├── web/              # Interfaz de visualización
├── tests/            # Suite de pruebas
└── *.py             # Scripts principales
```

## 🔧 Configuración Avanzada

### Agregar URLs de Scraping
Editar `scraping/scraper_config.py`:
```python
URLS = {
    'dji': ['url1', 'url2', ...],
    'autel': [...],
    'parrot': [...]
}
```

### Personalizar Parsers
Cada marca tiene su parser en `scraping/parsers/`. Los parsers son extensibles para nuevos campos.

## 🐛 Solución de Problemas

| Problema | Solución |
|----------|----------|
| RuntimeWarning | Normal, no afecta funcionalidad |
| Error Selenium | Verificar instalación de Chrome |
| Datos faltantes | Valores 0.0 se convierten a null intencionalmente |
| Puerto ocupado | Cambiar puerto en serve_web.py |

## 🧪 Testing

```bash
# Ejecutar todos los tests
python tests/run_all_tests.py

# Tests específicos
python -m unittest tests.test_data_integrity
```

## 📈 Rendimiento

- **Scraping paralelo**: ~3-5x más rápido
- **Validación**: >95% precisión en datos
- **Categorización**: 100% automatizada

## 🤝 Contribuir

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/NuevaCaracteristica`)
3. Commit cambios (`git commit -m 'Agregar característica'`)
4. Push a la rama (`git push origin feature/NuevaCaracteristica`)
5. Crear Pull Request

## 📝 Licencia

Proyecto educativo. Los datos recopilados pertenecen a sus respectivos propietarios.

## 🙏 Créditos

- **Datos**: DJI, Autel Robotics, Parrot
- **Librerías**: BeautifulSoup, Selenium, Pandas
- **Visualización**: Chart.js, Particles.js

---
⭐ ¡Si este proyecto te fue útil, considera darle una estrella!

# 🎯 SISTEMA EXPERTO DE DESARROLLO WEB SCRAPING - COMPARADOR DE DRONES

## 🔰 DEFINICIÓN DE ROL Y CONTEXTO
Eres un **Senior Full-Stack Developer** especializado en:
- **Python avanzado**: Pandas (manipulación de datos), Selenium (automatización), BeautifulSoup (parsing HTML)
- **Frontend moderno**: HTML5 semántico, CSS3 (Grid/Flexbox), JavaScript ES6+ (async/await, modules)
- **Web scraping ético**: Respeto de robots.txt, rate limiting, manejo de errores
- **Análisis de datos**: Estadísticas descriptivas, métricas de negocio, insights accionables

---

## 🎯 MISIÓN ESPECÍFICA: COMPARADOR INTELIGENTE DE DRONES

**Problema real a resolver:** *"Quiero comprar un drone pero no sé cuál elegir entre las diferentes marcas y modelos según mis necesidades específicas (fotografía, recreación, trabajo profesional) y presupuesto"*

**Valor único:** Crear una herramienta que **realmente usaría alguien** antes de invertir $500-5000 USD en un drone, proporcionando comparaciones objetivas basadas en datos reales de fabricantes.

### 🎯 Fuentes de datos confirmadas:
- **DJI** (https://www.dji.com/) - Líder mundial, catálogo completo
- **Autel Robotics** (https://www.autelrobotics.com/) - Competidor premium
- **Parrot** (https://www.parrot.com/) - Innovación francesa, nicho profesional

---

## 📋 ESPECIFICACIONES TÉCNICAS DETALLADAS

### 🗃️ Estructura de datos unificada (JSON Schema):
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["modelo", "marca", "especificaciones_tecnicas", "clasificacion"],
  "properties": {
    "modelo": {"type": "string", "example": "DJI Air 3"},
    "marca": {"enum": ["DJI", "Autel", "Parrot"]},
    "url_fuente": {"type": "string", "format": "uri"},
    "precio": {
      "type": "object",
      "properties": {
        "usd": {"type": ["number", "null"]},
        "moneda_local": {"type": ["number", "null"]},
        "fecha_precio": {"type": "string", "format": "date"}
      }
    },
    "especificaciones_tecnicas": {
      "type": "object",
      "required": ["peso", "autonomia", "alcance"],
      "properties": {
        "peso_gramos": {"type": "number", "minimum": 0},
        "autonomia_minutos": {"type": "number", "minimum": 0},
        "alcance_metros": {"type": "number", "minimum": 0},
        "velocidad_max_kmh": {"type": ["number", "null"]},
        "resistencia_viento": {"type": ["string", "null"]},
        "temperatura_operacion": {"type": ["string", "null"]}
      }
    },
    "camara": {
      "type": "object",
      "properties": {
        "resolucion_video": {"enum": ["4K", "6K", "8K", "1080p", "720p", null]},
        "fps_max": {"type": ["number", "null"]},
        "sensor_tamaño": {"type": ["string", "null"]},
        "estabilizacion": {"enum": ["mecanica", "digital", "hibrida", null]},
        "zoom_optico": {"type": ["number", "null"]},
        "zoom_digital": {"type": ["number", "null"]}
      }
    },
    "caracteristicas_vuelo": {
      "type": "object",
      "properties": {
        "evita_obstaculos": {"type": "boolean"},
        "retorno_automatico": {"type": "boolean"},
        "seguimiento_objeto": {"type": "boolean"},
        "vuelo_nocturno": {"type": "boolean"},
        "modo_sport": {"type": "boolean"},
        "precision_hover": {"type": ["string", "null"]}
      }
    },
    "clasificacion": {
      "type": "object",
      "properties": {
        "categoria_peso": {"enum": ["ultra_ligero", "ligero", "medio", "pesado"]},
        "nivel_usuario": {"enum": ["principiante", "intermedio", "avanzado", "profesional"]},
        "uso_principal": {
          "type": "array",
          "items": {"enum": ["recreativo", "fotografia", "video_profesional", "cinematografia", "inspeccion", "carreras", "agricultura"]}
        },
        "certificaciones": {"type": "array", "items": {"type": "string"}}
      }
    },
    "metricas_calculadas": {
      "type": "object",
      "properties": {
        "precio_por_minuto_vuelo": {"type": ["number", "null"]},
        "ratio_peso_autonomia": {"type": ["number", "null"]},
        "score_versatilidad": {"type": "number", "minimum": 0, "maximum": 100},
        "indice_valor": {"type": ["number", "null"]}
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "fecha_extraccion": {"type": "string", "format": "date-time"},
        "version_scraper": {"type": "string"},
        "confiabilidad_datos": {"enum": ["alta", "media", "baja"]}
      }
    }
  }
}
```

---

## 🏗️ ARQUITECTURA DEL PROYECTO

```
tp_web_scraping_drones_[nombre]/
├── 📁 scraping/
│   ├── 🐍 scraper.py              # Orquestador principal con async/await
│   ├── 🤖 robot_checker.py        # Validación robots.txt + headers inteligentes
│   ├── 🧹 data_cleaner.py         # Normalización avanzada con Pandas
│   ├── 🔧 scraper_config.py       # Configuraciones por sitio (selectores, delays)
│   ├── 📊 data_validator.py       # Validación de esquema JSON
│   └── 📦 requirements.txt        # Dependencias versionadas
├── 📁 analysis/
│   ├── 🔍 focused_analyzer.py     # Métricas específicas de drones
│   ├── 🏆 ranking_engine.py       # Sistema de scoring y recomendaciones
│   ├── 📈 solution_data.json      # Dataset final optimizado para frontend
│   └── 📋 analysis_report.json    # Insights y estadísticas agregadas
├── 📁 data/
│   ├── 📁 raw/
│   │   ├── 🗂️ dji_products.json      # Datos brutos por marca
│   │   ├── 🗂️ autel_products.json
│   │   └── 🗂️ parrot_products.json
│   ├── 📁 processed/
│   │   ├── 🎯 unified_drones.json    # Datos normalizados
│   │   └── 📊 market_analysis.json   # Análisis de mercado
│   ├── 📋 metadata.json           # Información del dataset
│   └── 🔍 extraction_log.json     # Log detallado del proceso
├── 📁 web/
│   ├── 🌐 index.html              # SPA con componentes modulares
│   ├── 🎨 styles.css              # Design system para productos tech
│   ├── ⚡ script.js               # Lógica modular (ES6 modules)
│   ├── 📊 charts.js               # Visualizaciones específicas
│   ├── 🔍 filters.js              # Sistema de filtrado avanzado
│   └── 📁 assets/
│       ├── 🖼️ drone_icons/          # Iconos por marca
│       └── 📈 charts/              # Gráficos precargados
├── 📁 tests/
│   ├── 🧪 test_scraper.py         # Tests unitarios
│   └── 🎯 test_data_quality.py    # Validación de calidad de datos
├── 📜 README.md                   # Documentación completa
└── ⚙️ config.json                # Configuración global del proyecto
```

---

## 🛠️ STACK TECNOLÓGICO ESPECÍFICO

### 🐍 Backend Python (requirements.txt):
```txt
# Core scraping
requests==2.31.0
beautifulsoup4==4.12.2
selenium==4.15.0
lxml==4.9.3

# Data processing
pandas==2.1.3
numpy==1.25.2
jsonschema==4.19.2

# Utilities
python-dotenv==1.0.0
fake-useragent==1.4.0
tenacity==8.2.3  # Para reintentos inteligentes
```

### 🌐 Frontend JavaScript:
```javascript
// Core libraries (CDN)
- Chart.js 4.x: Visualizaciones interactivas
- Fuse.js: Búsqueda difusa inteligente
- Vanilla JS ES6+: Sin frameworks, máximo rendimiento
```

---

## 🎯 FUNCIONALIDADES DETALLADAS POR CAPA

### 🔄 Capa de Scraping (scraping/)

#### 1. scraper.py - Orquestador Principal
```python
# Funcionalidades requeridas:
class DroneScraperOrchestrator:
    async def scrape_all_brands(self) -> Dict[str, List[Dict]]
    def setup_selenium_driver(self) -> webdriver.Chrome  # Con user-agent rotativo
    def handle_spa_loading(self, url: str) -> BeautifulSoup  # Para JS-heavy sites
    def extract_drone_specs(self, product_page: str) -> Dict  # Parser inteligente
    def save_raw_data(self, brand: str, data: List[Dict]) -> None
```

#### 2. robot_checker.py - Validación Ética
```python
# Implementación obligatoria:
def can_scrape_advanced(url: str, user_agent: str = '*') -> Tuple[bool, str]
def get_crawl_delay(robots_url: str) -> float  # Respeto de Crawl-delay
def check_site_maps(robots_url: str) -> List[str]  # Descubrimiento de URLs
```

#### 3. data_cleaner.py - Normalización Inteligente
```python
# Funciones críticas:
def normalize_price_formats(price_str: str) -> Optional[float]  # $1,299 → 1299.0
def standardize_specifications(raw_specs: Dict) -> Dict  # Unificación de unidades
def validate_data_quality(drone_data: Dict) -> Tuple[bool, List[str]]  # QA automático
def merge_brand_datasets(dji: List, autel: List, parrot: List) -> pd.DataFrame
```

### 🔍 Capa de Análisis (analysis/)

#### 1. focused_analyzer.py - Métricas de Negocio
```python
# Análisis específicos requeridos:
def calculate_price_performance_ratio(drones_df: pd.DataFrame) -> pd.Series
def identify_market_segments(drones_df: pd.DataFrame) -> Dict[str, List[str]]
def find_best_value_by_category(drones_df: pd.DataFrame) -> Dict[str, str]
def generate_buying_recommendations(user_profile: Dict) -> List[Dict]
```

#### 2. ranking_engine.py - Sistema de Scoring
```python
# Algoritmos de recomendación:
def calculate_versatility_score(features: Dict) -> float  # 0-100
def rank_by_use_case(drones: List[Dict], use_case: str) -> List[Dict]
def price_tier_analysis(drones: List[Dict]) -> Dict[str, List[Dict]]
```

### 🌐 Capa Web (web/)

#### 1. index.html - Interfaz Principal
```html
<!-- Estructura semántica requerida: -->
<main id="drone-comparator">
  <section id="filters-panel">
    <!-- Filtros inteligentes por presupuesto, uso, nivel -->
  </section>
  <section id="results-grid">
    <!-- Cards comparativas con specs destacadas -->
  </section>
  <section id="detailed-comparison">
    <!-- Tabla side-by-side seleccionable -->
  </section>
  <section id="market-insights">
    <!-- Gráficos de tendencias y análisis -->
  </section>
</main>
```

#### 2. script.js - Lógica de Aplicación
```javascript
// Módulos JS requeridos:
class DroneComparator {
  async loadDroneData()  // Fetch de solution_data.json
  filterBySpecifications(filters)  // Filtrado reactivo
  generateComparisonTable(selectedDrones)  // Tabla dinámica
  displayMarketInsights()  // Gráficos con Chart.js
  recommendByProfile(userNeeds)  // Motor de recomendaciones
}
```

---

## 🎨 ESPECIFICACIONES DE UX/UI

### 🎯 Filtros Inteligentes Requeridos:
- **Presupuesto**: Slider con rangos predefinidos ($0-500, $500-1500, $1500+)
- **Nivel de usuario**: Radio buttons (Principiante, Intermedio, Avanzado, Profesional)
- **Uso principal**: Checkboxes múltiples (Fotografía, Video, Recreativo, Trabajo)
- **Especificaciones**: Rangos para peso, autonomía, alcance
- **Marca**: Toggle switches con logos

### 📊 Visualizaciones Obligatorias:
1. **Scatter Plot**: Precio vs Autonomía (burbujas por categoría de peso)
2. **Bar Chart**: Comparación de especificaciones técnicas
3. **Radar Chart**: Perfiles de versatilidad por modelo
4. **Heat Map**: Matriz de features por marca
5. **Timeline**: Evolución de precios (si hay datos históricos)

---

## 🔒 CONSIDERACIONES ÉTICAS CRÍTICAS

### ⚖️ Cumplimiento Legal Obligatorio:
```python
# Implementación ética mandatoria:
ETHICAL_SCRAPING_CONFIG = {
    "min_delay_seconds": 3,  # Mínimo entre requests
    "max_concurrent_requests": 1,  # Sin paralelización agresiva
    "respect_robots_txt": True,  # Verificación automática
    "user_agent": "Academic-Drone-Research-Bot/1.0 (+contact@universidad.edu)",
    "request_timeout": 15,  # Timeout generoso
    "max_retries": 2,  # Reintentos limitados
    "backoff_factor": 2.0  # Backoff exponencial
}
```

### 🚨 Validaciones por Sitio:
- **DJI**: Verificar términos específicos para uso académico
- **Autel**: Respetar rate limits (posible detección de bots)
- **Parrot**: Verificar si requiere headers específicos

### 📋 Headers Responsables:
```python
HEADERS = {
    'User-Agent': 'Academic-Drone-Research-Bot/1.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}
```

---

## 📏 CRITERIOS DE EVALUACIÓN Y CALIDAD

### 🎯 Métricas de Éxito:
1. **Utilidad Real** (30%): ¿Resuelve efectivamente el problema planteado?
2. **Calidad Técnica** (25%): Código limpio, manejo de errores, arquitectura
3. **Ética del Scraping** (20%): Respeto total de robots.txt y prácticas responsables
4. **Análisis Enfocado** (15%): Insights útiles, no análisis exhaustivo innecesario
5. **UX/UI Funcional** (10%): Interfaz intuitiva y realmente usable

### ✅ Checklist de Calidad:
- [ ] Todos los drones incluyen al menos 15 especificaciones técnicas
- [ ] Precios en USD normalizados y fechados
- [ ] Sistema de recomendaciones funcional
- [ ] Filtros responsivos sin bugs
- [ ] Gráficos interactivos con datos reales
- [ ] Manejo de errores en toda la aplicación
- [ ] Documentación completa en README.md
- [ ] Tests básicos para funciones críticas

---

## 🎯 INSTRUCCIONES DE OUTPUT

### 📋 Formato de Respuesta Estructurado:

```python
# ========================================
# 🔧 CAPA SCRAPING - ARCHIVOS PYTHON
# ========================================
# 
# Archivo: scraping/scraper.py
# Descripción: [descripción]
# 
# [código completo aquí]
#
# ----------------------------------------
# Archivo: scraping/robot_checker.py
# [continuar con todos los archivos...]
```

```html
<!-- ======================================== -->
<!-- 🌐 CAPA WEB - FRONTEND COMPLETO -->
<!-- ======================================== -->
<!-- 
Archivo: web/index.html
Descripción: [descripción]
-->

<!-- [código HTML completo aquí] -->

<!-- ---------------------------------------- -->
<!-- Archivo: web/styles.css -->
<!-- [continuar con todos los archivos...] -->
```

```markdown
<!-- ======================================== -->
<!-- 📚 DOCUMENTACIÓN Y CONFIGURACIÓN -->
<!-- ======================================== -->

# README.md

[documentación completa]

---

## config.json

[configuración del proyecto]
```

---

## 🚀 COMANDO DE EJECUCIÓN

**Desarrolla el comparador completo de drones DJI vs Autel vs Parrot siguiendo esta especificación exacta. El resultado debe ser una aplicación web funcional que permita a cualquier persona tomar una decisión informada sobre qué drone comprar según sus necesidades específicas y presupuesto.**

**Genera TODOS los archivos necesarios para que el proyecto sea ejecutable inmediatamente después de `pip install -r requirements.txt`**
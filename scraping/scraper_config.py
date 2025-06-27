#Scraper Configuration
#Configuraciones específicas para cada sitio web de drones


SCRAPER_CONFIG = {
    'dji': {
        'base_url': 'https://www.dji.com',
        'product_urls': [
            'https://www.dji.com/mavic-3-pro/specs',
            'https://www.dji.com/mavic-3-classic/specs',
            'https://www.dji.com/air-3s/specs',
            'https://www.dji.com/air-3/specs',
            'https://www.dji.com/mini-4-pro/specs',
            'https://www.dji.com/mini-3/specs',
            'https://www.dji.com/flip/specs',
            'https://www.dji.com/avata-2/specs',
            'https://www.dji.com/inspire-3/specs'
        ],
        'requires_js': True,
        'infinite_scroll': False,
        'max_products': 30,
        'delay_between_requests': 3,
        'direct_product_urls': True,
        'selectors': {
            # Selectores específicos para DJI (español) - 13 características específicas
            'product_name': 'h1.style_title__lBlWu, h1[class*="title"], .product-name h1',
            'specs_section': 'div[class*="specs"], section[class*="specification"]',
            'peso': '//div[contains(text(), "Peso al despegue") or contains(text(), "Peso") or contains(text(), "peso")]/following-sibling::div[1]',
            'dimensiones_plegado': '//div[contains(text(), "Dimensiones plegado") or contains(text(), "Tamaño plegado") or contains(text(), "dimensiones doblado")]/following-sibling::div[1]',
            'vuelo_minutos': '//div[contains(text(), "Tiempo de vuelo") or contains(text(), "Autonomía de vuelo") or contains(text(), "flight time")]/following-sibling::div[1]',
            'velocidad_horizontal': '//div[contains(text(), "Velocidad horizontal") or contains(text(), "Velocidad máxima") or contains(text(), "velocidad de vuelo")]/following-sibling::div[1]',
            'velocidad_ascenso': '//div[contains(text(), "Velocidad de ascenso") or contains(text(), "Ascenso máximo") or contains(text(), "ascent")]/following-sibling::div[1]',
            'alcance_video': '//div[contains(text(), "Alcance de transmisión") or contains(text(), "Distancia de transmisión") or contains(text(), "transmission")]/following-sibling::div[1]',
            'altitud_despegue': '//div[contains(text(), "Altitud máxima") or contains(text(), "Techo de servicio") or contains(text(), "altitude")]/following-sibling::div[1]',
            'resistencia_viento': '//div[contains(text(), "Resistencia al viento") or contains(text(), "Velocidad máxima del viento") or contains(text(), "wind")]/following-sibling::div[1]',
            'almacenamiento_interno': '//div[contains(text(), "Almacenamiento interno") or contains(text(), "Memoria interna") or contains(text(), "storage")]/following-sibling::div[1]',
            'sensor_camara': '//div[contains(text(), "Sensor de cámara") or contains(text(), "Sensor") or contains(text(), "camera sensor")]/following-sibling::div[1]',
            'resolucion_video': '//div[contains(text(), "Resolución de video") or contains(text(), "Modo de video") or contains(text(), "video resolution")]/following-sibling::div[1]',
            'deteccion_obstaculos': '//div[contains(text(), "Detección de obstáculos") or contains(text(), "Sensores de obstáculos") or contains(text(), "obstacle")]/following-sibling::div[1]',
            'specs_list': 'ul[class*="spec-list"] li, div[class*="spec-item"]'
        },
        'use_xpath': True,  # DJI requiere XPath para contenido dinámico
        'scroll_before_extract': True,
        'wait_after_scroll': 3,
        'wait_for_elements': [
            'div[class*="specs"]',
            'section[class*="specification"]'
        ]
    },
    
    'autel': {
        'base_url': 'https://www.autelrobotics.com',
        'product_urls': [

            'https://www.autelrobotics.com/productdetail/evo-lite-enterprise-series/#jsgg',
            'https://www.autelrobotics.com/productdetail/autel-alpha/#jsgg',
            'https://www.autelrobotics.com/productdetail/evo-max-4t/#jsgg',
            'https://www.autelrobotics.com/productdetail/evo-max-4n/#jsgg',
            'https://www.autelrobotics.com/productdetail/evo-ii-enterprise-drones/#jsgg',
            'https://www.autelrobotics.com/productdetail/evo-ii-dual-640t-drones/#jsgg',
            'https://www.autelrobotics.com/productdetail/evo-ii-rtk-series-drones/#jsgg',
            'https://www.autelrobotics.com/productdetail/evo-ii-pro-drones/#jsgg',
            'https://www.autelrobotics.com/productdetail/dragonfish-series-drones/#jsgg'
        ],
        'requires_js': True,
        'infinite_scroll': False,
        'max_products': 20,
        'delay_between_requests': 4,
        'direct_product_urls': True,
        'selectors': {
            # Selectores específicos para Autel (inglés) - 13 características específicas
            'product_name': 'h1.product-title, .product-name h1, h1[class*="title"]',
            'specs_section': '.product-specs, .specifications-section, div[class*="specification"]',
            'specs_table': 'table.specs-table, .product-parameters table',
            'peso': 'td:contains("Weight") + td, th:contains("Weight") + td, td:contains("Takeoff Weight") + td',
            'dimensiones_plegado': 'td:contains("Folded Dimensions") + td, td:contains("Folded Size") + td, th:contains("Dimensions Folded") + td',
            'vuelo_minutos': 'td:contains("Flight Time") + td, td:contains("Maximum Flight Time") + td, th:contains("Flight Duration") + td',
            'velocidad_horizontal': 'td:contains("Maximum Horizontal Speed") + td, td:contains("Max Speed") + td, th:contains("Top Speed") + td',
            'velocidad_ascenso': 'td:contains("Maximum Ascent Speed") + td, td:contains("Ascent Speed") + td, th:contains("Climb Rate") + td',
            'alcance_video': 'td:contains("Signal Effective Distance") + td, td:contains("Transmission Range") + td, th:contains("Control Distance") + td',
            'altitud_despegue': 'td:contains("Maximum Flight Altitude") + td, td:contains("Service Ceiling") + td, th:contains("Max Takeoff Altitude") + td',
            'resistencia_viento': 'td:contains("Wind Resistance") + td, td:contains("Maximum Wind Speed") + td, th:contains("Wind Rating") + td',
            'almacenamiento_interno': 'td:contains("Internal Storage") + td, td:contains("Built-in Storage") + td, th:contains("Memory Capacity") + td',
            'sensor_camara': 'td:contains("Camera Sensor") + td, td:contains("Image Sensor") + td, th:contains("CMOS Sensor") + td',
            'resolucion_video': 'td:contains("Video Resolution") + td, td:contains("Recording Modes") + td, th:contains("Video Recording") + td',
            'deteccion_obstaculos': 'td:contains("Obstacle Sensing") + td, td:contains("Obstacle Avoidance") + td, th:contains("Collision Avoidance") + td',
            'specs_accordion': '.accordion-item, .spec-accordion'
        },
        'wait_for_elements': [
            '.product-specs',
            '.specifications-section'
        ]
},

'parrot': {
        'base_url': 'https://www.parrot.com',
        'product_urls': [
            'https://www.parrot.com/assets/s3fs-public/2023-02/ANAFI-Ai-product-sheet.pdf',
            'https://www.parrot.com/assets/s3fs-public/2023-02/ANAFI-USA-product-sheet.pdf'
        ],
        'requires_js': False,  # Parrot usa menos JS
        'infinite_scroll': False,
        'max_products': 15,
        'delay_between_requests': 3,
        'direct_product_urls': True,  # URLs directas a productos específicos
        'has_pdf_content': True,  # Algunos productos están en PDF
        'selectors': {
            'product_list': '.product-item, .drone-item, article.product',
            'product_link': 'a[href*="/drones/"], a.product-url',
            'product_name': 'h1.product__title, h1[itemprop="name"], .product-name',
            'specs_table': '.product__specs, .technical-specs, .specifications',
            'camera_section': '.camera-specs, .imaging-system',
            'features_section': '.product__features, .key-features'
        },
        'pdf_extraction': {
            'enabled': True,
            'spec_patterns': [
                # Patrones actualizados para las 13 características específicas
                r'Weight:\s*(\d+\.?\d*)\s*(g|kg)',
                r'Folded dimensions:\s*(\d+\.?\d*)\s*×\s*(\d+\.?\d*)\s*×\s*(\d+\.?\d*)\s*(mm|cm)',
                r'Flight time:\s*(\d+)\s*(min|minutes)',
                r'Max horizontal speed:\s*(\d+\.?\d*)\s*(km/h|m/s)',
                r'Max ascent speed:\s*(\d+\.?\d*)\s*(m/s|km/h)',
                r'Transmission range:\s*(\d+\.?\d*)\s*(km|m)',
                r'Service ceiling:\s*(\d+\.?\d*)\s*(m|ft)',
                r'Wind resistance:\s*(\d+\.?\d*)\s*(m/s|km/h)',
                r'Internal storage:\s*(\d+\.?\d*)\s*(GB|MB)',
                r'Camera sensor:\s*([^,\n]+)',
                r'Video resolution:\s*([48]K|1080p|720p|UHD|FHD)',
                r'Obstacle avoidance:\s*([^,\n]+)',
                r'Dimensions folded:\s*(\d+\.?\d*)\s*×\s*(\d+\.?\d*)\s*×\s*(\d+\.?\d*)'
            ]
        },
        'locale_handling': {
            'preferred_locale': 'en-US',
            'fallback_locales': ['en', 'us']
        }
    }
}

# Configuración global de scraping ético
ETHICAL_SCRAPING_CONFIG = {
    'min_delay_seconds': 3,
    'max_concurrent_requests': 1,
    'respect_robots_txt': True,
    'user_agent': 'Academic-Drone-Research-Bot/1.0 (+contact@universidad.edu)',
    'request_timeout': 15,
    'max_retries': 2,
    'backoff_factor': 2.0,
    'verify_ssl': True,
    'follow_redirects': True,
    'max_redirects': 3
}

# Mapeo específico de características para scraping según especificaciones de cada marca
# Basado en análisis de sitios web DJI (español), Autel y Parrot (inglés)
SPEC_MAPPINGS = {
    # === 13 CARACTERÍSTICAS ESPECÍFICAS REQUERIDAS ===
    
    'modelo': {  # Nombre del modelo del drone
        'dji':   ['producto', 'nombre del producto', 'modelo', 'drone name'],
        'autel': ['product name', 'model', 'drone model', 'product title'],
        'parrot': ['product name', 'model', 'drone model', 'title']
    },
    
    'peso': {  # Peso del drone en gramos
        'dji':   ['peso al despegue', 'peso', 'peso del avión', 'peso total'],
        'autel': ['weight', 'takeoff weight', 'max takeoff weight', 'maximum takeoff weight'],
        'parrot': ['weight', 'total weight', 'drone weight', 'mass']
    },
    
    'dimensiones_plegado': {  # Dimensiones cuando está plegado
        'dji':   ['dimensiones plegado', 'tamaño plegado', 'dimensiones doblado', 'folded dimensions'],
        'autel': ['folded dimensions', 'folded size', 'dimensions folded', 'compact size'],
        'parrot': ['folded dimensions', 'compact dimensions', 'folded size', 'portable size']
    },
    
    'vuelo_minutos': {  # Tiempo de vuelo en minutos
        'dji':   ['tiempo de vuelo máximo', 'tiempo de vuelo', 'autonomía de vuelo', 'duración del vuelo'],
        'autel': ['maximum flight time', 'max flight time', 'flight time', 'flight duration'],
        'parrot': ['maximum flight time', 'max flight time', 'flight time', 'autonomy', 'battery life']
    },
    
    'velocidad_horizontal': {  # Velocidad horizontal máxima en m/s
        'dji':   ['velocidad horizontal máxima', 'velocidad máxima', 'velocidad de vuelo máxima', 'velocidad máxima de vuelo'],
        'autel': ['maximum horizontal flight speed', 'max horizontal speed', 'top speed', 'maximum speed'],
        'parrot': ['maximum horizontal speed', 'max speed', 'maximum speed', 'top speed']
    },
    
    'velocidad_ascenso': {  # Velocidad máxima de ascenso en m/s
        'dji':   ['velocidad de ascenso máxima', 'velocidad de ascenso', 'velocidad máxima de subida', 'ascenso máximo'],
        'autel': ['maximum ascent speed', 'max ascent speed', 'ascent speed', 'climb rate'],
        'parrot': ['maximum ascent speed', 'max ascent speed', 'ascent speed', 'maximum vertical speed']
    },
    
    'alcance_video': {  # Alcance de transmisión de video
        'dji':   ['alcance de transmisión máximo', 'distancia de transmisión', 'alcance de control', 'distancia máxima de transmisión'],
        'autel': ['maximum signal effective distance', 'signal effective distance', 'transmission range', 'control distance'],
        'parrot': ['range', 'transmission range', 'control range', 'video transmission range']
    },
    
    'altitud_despegue': {  # Altitud máxima de despegue en metros
        'dji':   ['altitud máxima de despegue', 'techo de servicio sobre el nivel del mar', 'altitud máxima de vuelo', 'techo de servicio máximo'],
        'autel': ['maximum flight altitude', 'max takeoff altitude', 'maximum service ceiling', 'service ceiling'],
        'parrot': ['service ceiling', 'maximum flight altitude', 'maximum altitude', 'ceiling altitude']
    },
    
    'resistencia_viento': {  # Resistencia al viento en m/s
        'dji':   ['resistencia máxima al viento', 'resistencia al viento', 'velocidad máxima del viento', 'resistencia a ráfagas'],
        'autel': ['maximum wind speed resistance', 'wind resistance', 'max wind speed', 'wind rating'],
        'parrot': ['maximum wind resistance', 'wind resistance', 'max wind speed resistance', 'wind speed resistance']
    },
    
    'almacenamiento_interno': {  # Capacidad de almacenamiento interno
        'dji':   ['almacenamiento interno', 'memoria interna', 'capacidad de almacenamiento', 'espacio de almacenamiento'],
        'autel': ['internal storage', 'built-in storage', 'memory capacity', 'internal memory'],
        'parrot': ['internal storage', 'built-in memory', 'storage capacity', 'internal memory']
    },
    
    'sensor_camara': {  # Especificaciones del sensor de la cámara
        'dji':   ['sensor de cámara', 'sensor', 'tipo de sensor', 'sensor cmos'],
        'autel': ['camera sensor', 'sensor', 'image sensor', 'cmos sensor'],
        'parrot': ['camera sensor', 'sensor', 'image sensor', 'sensor type']
    },
    
    'resolucion_video': {  # Resolución máxima de video
        'dji':   ['resolución de video', 'resolución máxima de video', 'resolución de grabación', 'modo de video'],
        'autel': ['video resolution', 'recording modes', 'video recording', 'camera resolution'],
        'parrot': ['video resolution', 'video modes', 'recording resolution', 'video recording']
    },
    
    'deteccion_obstaculos': {  # Sistema de detección de obstáculos
        'dji':   ['detección de obstáculos', 'sensores de obstáculos', 'evitación de obstáculos', 'sensores omnidireccionales'],
        'autel': ['obstacle sensing', 'obstacle avoidance', 'obstacle detection', 'collision avoidance'],
        'parrot': ['obstacle avoidance', 'obstacle detection', 'collision avoidance', 'safety sensors']
    }
}

# Patrones de extracción de datos actualizados para las 13 características específicas
EXTRACTION_PATTERNS = {
    'price': {
        'patterns': [
            r'\$[\d,]+\.?\d*',
            r'USD\s*[\d,]+\.?\d*',
            r'€[\d,]+\.?\d*',
            r'EUR\s*[\d,]+\.?\d*',
            r'£[\d,]+\.?\d*',
            r'GBP\s*[\d,]+\.?\d*'
        ],
        'cleanup': [',', ' ', 'USD', 'EUR', 'GBP', '$', '€', '£']
    },
    'peso': {
        'patterns': [
            r'(\d+\.?\d*)\s*(g|grams?|kg|kilograms?|lbs?|pounds?)',
            r'(\d+\.?\d*)\s*(gr|grammes?)'
        ]
    },
    'dimensiones_plegado': {
        'patterns': [
            r'(\d+\.?\d*)\s*×\s*(\d+\.?\d*)\s*×\s*(\d+\.?\d*)\s*(mm|cm)',
            r'(\d+\.?\d*)\s*x\s*(\d+\.?\d*)\s*x\s*(\d+\.?\d*)\s*(mm|cm)',
            r'(\d+\.?\d*)\s*\*\s*(\d+\.?\d*)\s*\*\s*(\d+\.?\d*)\s*(mm|cm)',
            r'plegado:?\s*(\d+\.?\d*)\s*×\s*(\d+\.?\d*)\s*×\s*(\d+\.?\d*)'
        ]
    },
    'vuelo_minutos': {
        'patterns': [
            r'(\d+)\s*(minutes?|mins?|min)',
            r'(\d+)\s*(hours?|hrs?|h)',
            r'up to\s*(\d+)\s*min',
            r'hasta\s*(\d+)\s*min'
        ]
    },
    'velocidad_horizontal': {
        'patterns': [
            r'(\d+\.?\d*)\s*(km/h|kmh|kph)',
            r'(\d+\.?\d*)\s*(m/s|mps)',
            r'(\d+\.?\d*)\s*(mph|mi/h)'
        ]
    },
    'velocidad_ascenso': {
        'patterns': [
            r'(\d+\.?\d*)\s*(m/s|mps)',
            r'(\d+\.?\d*)\s*(ft/s|fps)',
            r'(\d+\.?\d*)\s*(km/h|kmh)',
            r'(\d+\.?\d*)\s*(mph|mi/h)'
        ]
    },
    'alcance_video': {
        'patterns': [
            r'(\d+\.?\d*)\s*(km|kilometers?|kilometres?)',
            r'(\d+\.?\d*)\s*(mi|miles?)',
            r'(\d+\.?\d*)\s*(m|meters?|metres?)',
            r'up to\s*(\d+\.?\d*)\s*km',
            r'hasta\s*(\d+\.?\d*)\s*km'
        ]
    },
    'altitud_despegue': {
        'patterns': [
            r'(\d+\.?\d*)\s*(m|meters?|metres?)',
            r'(\d+\.?\d*)\s*(ft|feet)',
            r'(\d+\.?\d*)\s*(km|kilometers?)',
            r'up to\s*(\d+\.?\d*)\s*m',
            r'hasta\s*(\d+\.?\d*)\s*m'
        ]
    },
    'resistencia_viento': {
        'patterns': [
            r'(\d+\.?\d*)\s*(m/s|mps)',
            r'(\d+\.?\d*)\s*(km/h|kmh)',
            r'(\d+\.?\d*)\s*(mph|mi/h)',
            r'(\d+\.?\d*)\s*(kt|knots?)',
            r'level\s*(\d+)',
            r'escala\s*(\d+)'
        ]
    },
    'almacenamiento_interno': {
        'patterns': [
            r'(\d+\.?\d*)\s*(GB|gb)',
            r'(\d+\.?\d*)\s*(TB|tb)',
            r'(\d+\.?\d*)\s*(MB|mb)',
            r'(\d+)\s*(gigabytes?|terabytes?|megabytes?)'
        ]
    },
    'sensor_camara': {
        'patterns': [
            r'(\d+/\d+\.?\d*)\s*(inch|")',
            r'(\d+\.?\d*)\s*(inch|")\s*(CMOS|CCD)',
            r'(CMOS|CCD)\s*(\d+/\d+\.?\d*)',
            r'(\d+\.?\d*)\s*MP',
            r'(\d+\.?\d*)\s*megapixel'
        ]
    },
    'resolucion_video': {
        'patterns': [
            r'(4K|6K|8K|1080p|720p)',
            r'(\d{3,4})p',
            r'(\d{3,4})\s*x\s*(\d{3,4})',
            r'(UHD|FHD|HD)'
        ]
    },
    'deteccion_obstaculos': {
        'patterns': [
            r'(omnidirectional|omnidireccional)',
            r'(\d+)\s*direction',
            r'(\d+)\s*sensor',
            r'(front|rear|side|up|down)',
            r'(delantero|trasero|lateral|arriba|abajo)',
            r'(visual|infrared|lidar|ultrasonic)',
            r'(visual|infrarrojo|lidar|ultrasónico)'
        ]
    }
}

# Validación de datos actualizada para las 13 características específicas
VALIDATION_RULES = {
    'dji': {
        'min_price': 200,
        'max_price': 20000,
        'min_peso': 200,  # gramos
        'max_peso': 10000,
        'min_vuelo_minutos': 10,  # minutos
        'max_vuelo_minutos': 60,
        'min_alcance_video': 100,  # metros
        'max_alcance_video': 15000,
        'min_velocidad_horizontal': 5,  # km/h
        'max_velocidad_horizontal': 80,
        'min_velocidad_ascenso': 1,  # m/s
        'max_velocidad_ascenso': 10,
        'min_altitud_despegue': 1000,  # metros
        'max_altitud_despegue': 10000,
        'min_resistencia_viento': 5,  # m/s
        'max_resistencia_viento': 20,
        'min_almacenamiento_interno': 0,  # GB
        'max_almacenamiento_interno': 1000
    },
    'autel': {
        'min_price': 500,
        'max_price': 25000,
        'min_peso': 300,
        'max_peso': 8000,
        'min_vuelo_minutos': 15,
        'max_vuelo_minutos': 45,
        'min_alcance_video': 500,
        'max_alcance_video': 12000,
        'min_velocidad_horizontal': 5,
        'max_velocidad_horizontal': 70,
        'min_velocidad_ascenso': 1,
        'max_velocidad_ascenso': 8,
        'min_altitud_despegue': 2000,
        'max_altitud_despegue': 8000,
        'min_resistencia_viento': 5,
        'max_resistencia_viento': 18,
        'min_almacenamiento_interno': 0,
        'max_almacenamiento_interno': 512
    },
    'parrot': {
        'min_price': 100,
        'max_price': 10000,
        'min_peso': 100,
        'max_peso': 5000,
        'min_vuelo_minutos': 10,
        'max_vuelo_minutos': 35,
        'min_alcance_video': 100,
        'max_alcance_video': 5000,
        'min_velocidad_horizontal': 5,
        'max_velocidad_horizontal': 60,
        'min_velocidad_ascenso': 0.5,
        'max_velocidad_ascenso': 6,
        'min_altitud_despegue': 500,
        'max_altitud_despegue': 6000,
        'min_resistencia_viento': 3,
        'max_resistencia_viento': 15,
        'min_almacenamiento_interno': 0,
        'max_almacenamiento_interno': 256
    }
}

# Categorización de drones
DRONE_CATEGORIES = {
    'ultra_ligero': {
        'max_weight': 250,  # gramos
        'typical_use': ['recreativo', 'aprendizaje'],
        'price_range': (100, 500)
    },
    'ligero': {
        'min_weight': 250,
        'max_weight': 500,
        'typical_use': ['recreativo', 'fotografia', 'video_amateur'],
        'price_range': (300, 1500)
    },
    'medio': {
        'min_weight': 500,
        'max_weight': 1000,
        'typical_use': ['fotografia', 'video_profesional', 'inspeccion'],
        'price_range': (800, 5000)
    },
    'pesado': {
        'min_weight': 1000,
        'typical_use': ['cinematografia', 'inspeccion', 'agricultura', 'industrial'],
        'price_range': (3000, 25000)
    }
}

# Headers por defecto para requests
DEFAULT_HEADERS = {
    'User-Agent': ETHICAL_SCRAPING_CONFIG['user_agent'],
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0'
}
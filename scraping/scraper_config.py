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
            'https://www.dji.com/inspire-3/specs',
        ],
        'requires_js': True,
        'infinite_scroll': False,
        'max_products': 30,
        'delay_between_requests': 3,
        'direct_product_urls': True,
        'selectors': {
            # Selectores específicos para DJI basados en análisis del DOM
            'product_name': 'h1.style_title__lBlWu, h1[class*="title"], .product-name h1',
            'specs_section': 'div[class*="specs"], section[class*="specification"]',
            'weight': '//div[contains(text(), "Weight") or contains(text(), "weight")]/following-sibling::div[1]',
            'flight_time': '//div[contains(text(), "Flight Time") or contains(text(), "flight time")]/following-sibling::div[1]',
            'range': '//div[contains(text(), "Transmission") or contains(text(), "Range")]/following-sibling::div[1]',
            'camera': '[data-test*="camera"], div:contains("Camera") + div, div[class*="camera-specs"]',
            'specs_list': 'ul[class*="spec-list"] li, div[class*="spec-item"]',
            # === NUEVOS SELECTORES ===
            'battery_capacity': '//div[contains(text(), "Battery") or contains(text(), "Capacity")]/following-sibling::div[1]',
            'max_altitude': '//div[contains(text(), "Altitude") or contains(text(), "Service Ceiling")]/following-sibling::div[1]',
            'operating_temperature': '//div[contains(text(), "Operating Temperature") or contains(text(), "Temperature")]/following-sibling::div[1]',
            'ascent_speed': '//div[contains(text(), "Ascent") or contains(text(), "Ascent Speed")]/following-sibling::div[1]',
            'descent_speed': '//div[contains(text(), "Descent") or contains(text(), "Descent Speed")]/following-sibling::div[1]',
            'hover_time': '//div[contains(text(), "Hover") or contains(text(), "Hover Time")]/following-sibling::div[1]'
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
            'https://www.autelrobotics.com/productdetail/dragonfish-series-drones/#jsgg',
        ],
        'requires_js': True,
        'infinite_scroll': False,
        'max_products': 20,
        'delay_between_requests': 4,
        'direct_product_urls': True,
        'selectors': {
            # Selectores específicos para Autel
            'product_name': 'h1.product-title, .product-name h1, h1[class*="title"]',
            'specs_section': '.product-specs, .specifications-section, div[class*="specification"]',
            'specs_table': 'table.specs-table, .product-parameters table',
            'weight': 'td:contains("Weight") + td, th:contains("Weight") + td',
            'flight_time': 'td:contains("Flight Time") + td, th:contains("Flight Time") + td',
            'range': 'td:contains("Range") + td, th:contains("Control Distance") + td',
            'specs_accordion': '.accordion-item, .spec-accordion',
            # === NUEVOS SELECTORES ===
            'battery_capacity': 'td:contains("Battery") + td, td:contains("Capacity") + td',
            'max_altitude': 'td:contains("Altitude") + td, td:contains("Service Ceiling") + td',
            'operating_temperature': 'td:contains("Temperature") + td, td:contains("Operating Temperature") + td',
            'ascent_speed': 'td:contains("Ascent") + td, td:contains("Ascent Speed") + td',
            'descent_speed': 'td:contains("Descent") + td, td:contains("Descent Speed") + td',
            'hover_time': 'td:contains("Hover") + td, td:contains("Hover Time") + td'
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
                r'Weight:\s*(\d+\.?\d*)\s*(g|kg)',
                r'Flight time:\s*(\d+)\s*(min|minutes)',
                r'Range:\s*(\d+\.?\d*)\s*(km|m)',
                r'Video resolution:\s*([48]K|1080p|720p)',
                r'Max speed:\s*(\d+\.?\d*)\s*(km/h|m/s)',
                # === NUEVOS PATRONES ===
                r'Battery capacity:\s*(\d+)\s*(mAh|mah)',
                r'Service ceiling:\s*(\d+\.?\d*)\s*(m|ft)',
                r'Operating temperature:\s*(-?\d+\.?\d*)\s*to\s*(\d+\.?\d*)\s*°C',
                r'Max ascent speed:\s*(\d+\.?\d*)\s*(m/s|km/h)',
                r'Max descent speed:\s*(\d+\.?\d*)\s*(m/s|km/h)',
                r'Hover time:\s*(\d+)\s*(min|minutes)'
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

# Mapeo ampliado de especificaciones técnicas para scraping en DJI, Autel y Parrot
SPEC_MAPPINGS = {
    # === ESPECIFICACIONES BÁSICAS ===
    'weight': {
        'dji':   ['takeoff weight', 'weight', 'aircraft weight'],
        'autel': ['weight', 'takeoff weight', 'max takeoff weight', 'maximum takeoff weight'],
        'parrot': ['weight', 'total weight', 'drone weight', 'mass']
    },
    'flight_time': {
        'dji':   ['max flight time', 'maximum flight time', 'flight time', 'max hover time', 'hovering time'],
        'autel': ['maximum flight time', 'max flight time', 'flight time', 'maximum hover time', 'hover time'],
        'parrot': ['maximum flight time', 'max flight time', 'flight time', 'autonomy', 'battery life']
    },
    'range': {
        'dji':   ['max transmission range', 'transmission range', 'control range', 'max transmission distance', 'transmission distance'],
        'autel': ['maximum signal effective distance', 'signal effective distance', 'transmission range', 'control distance', 'max range'],
        'parrot': ['range', 'transmission range', 'control range']
    },
    'max_speed': {
        'dji':   ['max horizontal speed', 'maximum flight speed', 'max speed', 'max flight speed'],
        'autel': ['maximum horizontal flight speed', 'max speed', 'top speed', 'maximum horizontal speed'],
        'parrot': ['maximum horizontal speed', 'max speed', 'maximum speed', 'top speed']
    },
    'camera_resolution': {
        'dji':   ['video resolution', 'max video resolution', 'recording resolution', 'image resolution', 'photo resolution'],
        'autel': ['video resolution', 'recording modes', 'video recording', 'camera resolution', 'visible-light camera resolution', 'thermal imaging resolution'],
        'parrot': ['video resolution', 'video modes', 'recording resolution', 'photo resolution', 'sensor']
    },
    'wind_resistance': {
        'dji':   ['max wind speed resistance', 'wind resistance', 'max wind speed', 'wind speed resistance'],
        'autel': ['maximum wind speed resistance', 'wind resistance', 'max wind speed', 'wind rating'],
        'parrot': ['maximum wind resistance', 'wind resistance', 'max wind speed resistance', 'wind speed resistance']
    },

    'battery_capacity': {   # capacidad (mAh) de la batería
        'dji':   ['battery capacity', 'capacity', 'capacity (mah)', 'battery capacity (mah)'],
        'autel': ['battery capacity', 'capacity', 'capacity (mah)'],
        'parrot': ['battery capacity', 'capacity', 'capacity (mah)']
    },
    'max_altitude': {       # altura máxima de vuelo / techo de servicio
        'dji':   ['max takeoff altitude', 'maximum flight altitude', 'service ceiling above sea level', 'max service ceiling', 'maximum altitude'],
        'autel': ['maximum flight altitude', 'max takeoff altitude', 'maximum service ceiling', 'service ceiling', 'max service ceiling'],
        'parrot': ['service ceiling', 'maximum flight altitude', 'maximum altitude']
    },
    'operating_temperature': {  # rango de temperatura operativa
        'dji':   ['operating temperature', 'operating temperature range', 'working temperature', 'temperature range'],
        'autel': ['working temperature', 'operating temperature', 'temperature range', 'working temperature range'],
        'parrot': ['operating temperature', 'working temperature', 'temperature range']
    },
    'ascent_speed': {       # velocidad máxima de ascenso
        'dji':   ['max ascent speed', 'maximum ascent speed', 'ascent speed'],
        'autel': ['maximum ascent speed', 'max ascent speed', 'ascent speed'],
        'parrot': ['maximum ascent speed', 'max ascent speed', 'ascent speed', 'maximum vertical speed']
    },
    'descent_speed': {      # velocidad máxima de descenso
        'dji':   ['max descent speed', 'maximum descent speed', 'descent speed'],
        'autel': ['maximum descent speed', 'max descent speed', 'descent speed'],
        'parrot': ['maximum descent speed', 'max descent speed', 'descent speed', 'maximum vertical speed']
    },
    'hover_time': {         # tiempo máximo en vuelo estacionario
        'dji':   ['max hover time', 'maximum hover time', 'hover time', 'hovering time'],
        'autel': ['maximum hover time', 'hover time', 'hovering time'],
        'parrot': ['maximum hover time', 'max hover time', 'hover time', 'hovering time']
    }
}

# Patrones de extracción de datos
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
    'weight': {
        'patterns': [
            r'(\d+\.?\d*)\s*(g|grams?|kg|kilograms?|lbs?|pounds?)',
            r'(\d+\.?\d*)\s*(gr|grammes?)'
        ]
    },
    'flight_time': {
        'patterns': [
            r'(\d+)\s*(minutes?|mins?|min)',
            r'(\d+)\s*(hours?|hrs?|h)',
            r'up to\s*(\d+)\s*min'
        ]
    },
    'range': {
        'patterns': [
            r'(\d+\.?\d*)\s*(km|kilometers?|kilometres?)',
            r'(\d+\.?\d*)\s*(mi|miles?)',
            r'(\d+\.?\d*)\s*(m|meters?|metres?)',
            r'up to\s*(\d+\.?\d*)\s*km'
        ]
    },
    'speed': {
        'patterns': [
            r'(\d+\.?\d*)\s*(km/h|kmh|kph)',
            r'(\d+\.?\d*)\s*(m/s|mps)',
            r'(\d+\.?\d*)\s*(mph|mi/h)'
        ]
    },
    'resolution': {
        'patterns': [
            r'(4K|6K|8K|1080p|720p)',
            r'(\d{3,4})p',
            r'(\d{3,4})\s*x\s*(\d{3,4})'
        ]
    },
    'battery_capacity': {
        'patterns': [
            r'(\d+)\s*(mAh|mah|MAH)',
            r'(\d+\.?\d*)\s*(Ah|ah|AH)',
            r'(\d+)\s*(milliampere|milliamp)',
            r'(\d+)\s*mAh'
        ]
    },
    'altitude': {
        'patterns': [
            r'(\d+\.?\d*)\s*(m|meters?|metres?)',
            r'(\d+\.?\d*)\s*(ft|feet)',
            r'(\d+\.?\d*)\s*(km|kilometers?)',
            r'up to\s*(\d+\.?\d*)\s*m'
        ]
    },
    'temperature': {
        'patterns': [
            r'(-?\d+\.?\d*)\s*°C\s*to\s*(\d+\.?\d*)\s*°C',
            r'(-?\d+\.?\d*)\s*°F\s*to\s*(\d+\.?\d*)\s*°F',
            r'(-?\d+\.?\d*)\s*to\s*(\d+\.?\d*)\s*°C',
            r'(-?\d+\.?\d*)\s*to\s*(\d+\.?\d*)\s*°F',
            r'(-?\d+\.?\d*)\s*°C',
            r'(-?\d+\.?\d*)\s*°F'
        ]
    },
    'vertical_speed': {
        'patterns': [
            r'(\d+\.?\d*)\s*(m/s|mps)',
            r'(\d+\.?\d*)\s*(ft/s|fps)',
            r'(\d+\.?\d*)\s*(km/h|kmh)',
            r'(\d+\.?\d*)\s*(mph|mi/h)'
        ]
    },
    'hover_time': {
        'patterns': [
            r'(\d+)\s*(minutes?|mins?|min)',
            r'(\d+)\s*(hours?|hrs?|h)',
            r'up to\s*(\d+)\s*min',
            r'(\d+\.?\d*)\s*min'
        ]
    }
}

# Validación de datos por marca
VALIDATION_RULES = {
    'dji': {
        'min_price': 200,
        'max_price': 20000,
        'min_weight': 200,  # gramos
        'max_weight': 10000,
        'min_flight_time': 10,  # minutos
        'max_flight_time': 60,
        'min_range': 100,  # metros
        'max_range': 15000,
        # === NUEVAS VALIDACIONES ===
        'min_battery_capacity': 1000,  # mAh
        'max_battery_capacity': 15000,
        'min_max_altitude': 1000,  # metros
        'max_max_altitude': 10000,
        'min_operating_temp': -40,  # °C
        'max_operating_temp': 65,
        'min_ascent_speed': 1,  # m/s
        'max_ascent_speed': 10,
        'min_descent_speed': 1,  # m/s
        'max_descent_speed': 10,
        'min_hover_time': 5,  # minutos
        'max_hover_time': 50
    },
    'autel': {
        'min_price': 500,
        'max_price': 25000,
        'min_weight': 300,
        'max_weight': 8000,
        'min_flight_time': 15,
        'max_flight_time': 45,
        'min_range': 500,
        'max_range': 12000,
        # === NUEVAS VALIDACIONES ===
        'min_battery_capacity': 2000,  # mAh
        'max_battery_capacity': 20000,
        'min_max_altitude': 2000,  # metros
        'max_max_altitude': 8000,
        'min_operating_temp': -30,  # °C
        'max_operating_temp': 60,
        'min_ascent_speed': 1,  # m/s
        'max_ascent_speed': 8,
        'min_descent_speed': 1,  # m/s
        'max_descent_speed': 8,
        'min_hover_time': 10,  # minutos
        'max_hover_time': 40
    },
    'parrot': {
        'min_price': 100,
        'max_price': 10000,
        'min_weight': 100,
        'max_weight': 5000,
        'min_flight_time': 10,
        'max_flight_time': 35,
        'min_range': 100,
        'max_range': 5000,
        # === NUEVAS VALIDACIONES ===
        'min_battery_capacity': 500,  # mAh
        'max_battery_capacity': 8000,
        'min_max_altitude': 500,  # metros
        'max_max_altitude': 6000,
        'min_operating_temp': -20,  # °C
        'max_operating_temp': 50,
        'min_ascent_speed': 0.5,  # m/s
        'max_ascent_speed': 6,
        'min_descent_speed': 0.5,  # m/s
        'max_descent_speed': 6,
        'min_hover_time': 5,  # minutos
        'max_hover_time': 30
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
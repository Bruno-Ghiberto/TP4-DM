
#Scraper Configuration
#Configuraciones específicas para cada sitio web de drones


SCRAPER_CONFIG = {
    'dji': {
        'base_url': 'https://www.dji.com',
        'product_urls': [
            'https://www.dji.com/products/drones',
            'https://www.dji.com/products/camera-drones',
            'https://www.dji.com/products/handheld'
        ],
        'requires_js': True,
        'infinite_scroll': False,
        'max_products': 30,
        'delay_between_requests': 3,
        'selectors': {
            'product_list': '.product-list-item, .product-card',
            'product_link': 'a[href*="/product/"], a.product-link',
            'product_name': 'h1.product-title, h1.product-name, .product-header h1',
            'price': '.price-current, .product-price, .price',
            'specs_table': '.specs-table, .specifications-table, .product-specs',
            'camera_section': '.camera-specs, .gimbal-camera, [data-section="camera"]',
            'features_section': '.features-list, .product-features, .intelligent-features'
        },
        'api_endpoints': {
            'products': '/api/products',
            'specs': '/api/product/specs/{product_id}'
        },
        'headers': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    },
    
    'autel': {
        'base_url': 'https://www.autelrobotics.com',
        'product_urls': [
            'https://www.autelrobotics.com/productlist/drones.html',
            'https://www.autelrobotics.com/drones/',
            'https://www.autelrobotics.com/products/drones'
        ],
        'requires_js': True,
        'infinite_scroll': False,
        'max_products': 20,
        'delay_between_requests': 4,  # Más conservador con Autel
        'selectors': {
            'product_list': '.product-item, .drone-card, .product-box',
            'product_link': 'a.product-link, a[href*="/products/"]',
            'product_name': 'h1.product-name, .product-title h1, .page-title',
            'price': '.price, .product-price-value, .current-price',
            'specs_table': '.specifications, .specs-content, .product-parameters',
            'camera_section': '.camera-parameters, .payload-specs',
            'features_section': '.features, .product-highlights'
        },
        'special_handling': {
            'wait_for_element': '.product-loaded',
            'scroll_to_load': True,
            'ajax_wait': 2
        }
    },
    
    'parrot': {
        'base_url': 'https://www.parrot.com',
        'product_urls': [
            'https://www.parrot.com/en/drones',
            'https://www.parrot.com/us/drones',
            'https://www.parrot.com/en/professional-drones'
        ],
        'requires_js': False,  # Parrot usa menos JS
        'infinite_scroll': False,
        'max_products': 15,
        'delay_between_requests': 3,
        'selectors': {
            'product_list': '.product-item, .drone-item, article.product',
            'product_link': 'a[href*="/drones/"], a.product-url',
            'product_name': 'h1.product__title, h1[itemprop="name"], .product-name',
            'price': '.product__price, .price-now, [itemprop="price"]',
            'specs_table': '.product__specs, .technical-specs, .specifications',
            'camera_section': '.camera-specs, .imaging-system',
            'features_section': '.product__features, .key-features'
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

# Mapeo de especificaciones técnicas estándar
SPEC_MAPPINGS = {
    'weight': {
        'dji': ['takeoff weight', 'weight', 'aircraft weight'],
        'autel': ['weight', 'takeoff weight', 'max takeoff weight'],
        'parrot': ['weight', 'total weight', 'drone weight']
    },
    'flight_time': {
        'dji': ['max flight time', 'flight time', 'hovering time'],
        'autel': ['flight time', 'max flight time', 'endurance'],
        'parrot': ['flight time', 'autonomy', 'battery life']
    },
    'range': {
        'dji': ['max transmission range', 'control range', 'transmission distance'],
        'autel': ['transmission range', 'control distance', 'max range'],
        'parrot': ['range', 'transmission range', 'control range']
    },
    'max_speed': {
        'dji': ['max speed', 'max flight speed', 'max horizontal speed'],
        'autel': ['max speed', 'top speed', 'maximum velocity'],
        'parrot': ['max speed', 'maximum speed', 'top speed']
    },
    'camera_resolution': {
        'dji': ['video resolution', 'max video resolution', 'recording resolution'],
        'autel': ['video resolution', 'recording modes', 'video recording'],
        'parrot': ['video resolution', 'video modes', 'recording resolution']
    },
    'wind_resistance': {
        'dji': ['max wind speed resistance', 'wind resistance', 'max windspeed'],
        'autel': ['wind resistance', 'max wind speed', 'wind rating'],
        'parrot': ['wind resistance', 'maximum wind', 'wind conditions']
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
        'max_range': 15000
    },
    'autel': {
        'min_price': 500,
        'max_price': 25000,
        'min_weight': 300,
        'max_weight': 8000,
        'min_flight_time': 15,
        'max_flight_time': 45,
        'min_range': 500,
        'max_range': 12000
    },
    'parrot': {
        'min_price': 100,
        'max_price': 10000,
        'min_weight': 100,
        'max_weight': 5000,
        'min_flight_time': 10,
        'max_flight_time': 35,
        'min_range': 100,
        'max_range': 5000
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
"""Configuration for drone scraper."""

# ==================== SCRAPER_CONFIGURATION ====================
# Configuración general del scraper

# URLs de los sitios web a scrapear
URLS = {
    "dji": [
        "https://www.dji.com/mavic-3-pro/specs",
        "https://www.dji.com/mavic-3-classic/specs",
        "https://www.dji.com/air-3s/specs",
        "https://www.dji.com/air-3/specs",
        "https://www.dji.com/mini-4-pro/specs",
        "https://www.dji.com/mini-3/specs",
        "https://www.dji.com/avata-2/specs",
        "https://www.dji.com/inspire-3/specs"
    ],
    "autel": [
        "https://www.autelrobotics.com/productdetail/evo-lite-enterprise-series/#jsgg",
        "https://www.autelrobotics.com/productdetail/autel-alpha/#jsgg",
        "https://www.autelrobotics.com/productdetail/evo-max-4t/#jsgg",
        "https://www.autelrobotics.com/productdetail/evo-ii-enterprise-drones/#jsgg",
        "https://www.autelrobotics.com/productdetail/evo-ii-dual-640t-drones/#jsgg",
        "https://www.autelrobotics.com/productdetail/evo-ii-pro-drones/#jsgg",
        "https://www.autelrobotics.com/productdetail/dragonfish-series/#jsgg"
    ],
    "parrot": [
        "https://www.parrot.com/assets/s3fs-public/2023-02/ANAFI-Ai-product-sheet.pdf",
        "https://www.parrot.com/assets/s3fs-public/2023-02/ANAFI-USA-product-sheet.pdf"
    ]
}

# Configuración de delays para ser educados con los servidores
SCRAPER_DELAY = {
    "min": 1.0,  # Mínimo 1 segundo entre requests
    "max": 3.0   # Máximo 3 segundos entre requests
}

# Headers para las requests HTTP
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0'
}

# ==================== SPEC_MAPPINGS RECONFIGURADOS ====================
# Diccionario completo para extracción de especificaciones de drones
# Basado en análisis exhaustivo de archivos de texto reales de cada sitio web

SPEC_MAPPINGS = {
    # ==================== DJI ====================
    # DJI mantiene la terminología más consistente y estandarizada
    # Organiza las especificaciones en secciones: Aircraft, Camera, Gimbal, Sensing, etc.
    "dji": {
        "modelo": {
            "keywords": [
                "DJI Mavic 3 Pro",               # Título específico
                "DJI Air 3S",                    # Título específico
                "DJI Mini 4 Pro",                # Título específico
                "DJI Air 3",                     # Título específico
                "DJI Mavic 3 Classic",           # Título específico
                "Mavic 3 Pro",                   # Sin prefijo DJI
                "Air 3S",                        # Sin prefijo DJI
                "Mini 4 Pro",                    # Sin prefijo DJI
                "Air 3",                         # Sin prefijo DJI
                "Mavic 3 Classic",               # Sin prefijo DJI
            ],
            "notes": "Extraer del título de la página. Formato típico: 'DJI [Serie] [Modelo]'"
        },
        
        "peso_gramos": {
            "keywords": [
                "Takeoff Weight",                # Término estándar DJI
                "< 249 g",                       # Mini 4 Pro específico
                "249 g",                         # Peso específico
                "720 g",                         # Air 3 específico
                "724 g",                         # Air 3S específico
                "895 g",                         # Mavic 3 Classic específico
                "958 g",                         # Mavic 3 Pro específico
                "963 g",                         # Mavic 3 Pro Cine específico
            ],
            "notes": "DJI siempre usa 'Takeoff Weight'. Incluye batería, hélices y microSD"
        },
        
        "dimensiones_plegado": {
            "keywords": [
                "Folded (without propellers)",   # Formato estándar DJI
                "148×94×64 mm (L×W×H)",         # Mini 4 Pro específico
                "207×100.5×91.1 mm (L×W×H)",    # Air 3 específico
                "214.19×100.63×89.17 mm (L×W×H)", # Air 3S específico
                "221×96.3×90.3 mm (L×W×H)",     # Mavic 3 Classic específico
                "231.1×98×95.4 mm (L×W×H)",     # Mavic 3 Pro específico
            ],
            "notes": "DJI siempre especifica (L×W×H) sin hélices"
        },
        
        "vuelo_minutos": {
            "keywords": [
                "Max Flight Time",               # Término estándar DJI
                "34 minutes",                    # Mini 4 Pro específico
                "45 minutes",                    # Air 3S específico
                "46 minutes",                    # Air 3 específico
                "43 minutes",                    # Mavic 3 Pro específico
                "Measured in a controlled test environment", # Contexto de medición
            ],
            "notes": "DJI especifica condiciones de medición detalladas"
        },
        
        "vel_horizontal_mps": {
            "keywords": [
                "Max Horizontal Speed",          # Término estándar
                "at sea level, no wind",        # Condiciones estándar
                "16 m/s",                        # Mini 4 Pro específico
                "21 m/s",                        # Air 3, Air 3S, Mavic 3 específico
                "19 m/s in EU regions",         # Restricción europea
            ],
            "notes": "DJI especifica diferentes valores para regiones (EU vs resto)"
        },
        
        "vel_ascenso_mps": {
            "keywords": [
                "Max Ascent Speed",              # Término estándar
                "5 m/s",                         # Mini 4 Pro específico
                "8 m/s",                         # Mavic 3 Classic y Pro específico
                "10 m/s",                        # Air 3 y Air 3S específico
            ],
            "notes": "DJI puede especificar diferentes valores por modo (S/N/C)"
        },
        
        "alcance_video_km": {
            "keywords": [
                "Max Transmission Distance",     # Término estándar
                "unobstructed, free of interference", # Condiciones
                "FCC: 15 km",                    # Mavic 3 específico
                "CE: 8 km",                      # Europa
                "FCC: 20 km",                    # Mini 4 Pro específico
                "CE: 10 km",                     # Mini 4 Pro Europa
            ],
            "notes": "DJI especifica valores FCC/CE/SRRC/MIC por separado"
        },
        
        "altitud_despegue_m": {
            "keywords": [
                "Max Takeoff Altitude",          # Término estándar
                "4000 m",                        # Mini 4 Pro específico
                "6000 m",                        # Air 3, Air 3S, Mavic 3 específico
            ],
            "notes": "DJI especifica altitud máxima de despegue sobre nivel del mar"
        },
        
        "resistencia_viento_mps": {
            "keywords": [
                "Max Wind Speed Resistance",     # Término estándar
                "10.7 m/s",                      # Mini 4 Pro específico
                "12 m/s",                        # Air 3, Air 3S, Mavic 3 específico
            ],
            "notes": "DJI especifica resistencia al viento en m/s"
        },
        
        "almacenamiento_interno_gb": {
            "keywords": [
                "Internal Storage",              # Término estándar
                "2 GB",                          # Mini 4 Pro específico
                "8 GB",                          # Air 3, Mavic 3 Classic específico
                "42 GB",                         # Air 3S específico
                "1 TB",                          # Mavic 3 Pro Cine específico
            ],
            "notes": "No todos los modelos DJI tienen almacenamiento interno"
        },
        
        "sensor_camara": {
            "keywords": [
                "Image Sensor",                  # Término estándar
                "1/1.3-inch CMOS",              # Mini 4 Pro, Air 3 específico
                "1-inch CMOS",                   # Air 3S específico
                "4/3 CMOS",                      # Mavic 3 Pro específico
                "Effective Pixels: 48 MP",      # Resolución común
                "Effective Pixels: 50 MP",      # Air 3S específico
                "Effective Pixels: 20 MP",      # Mavic 3 Pro específico
            ],
            "notes": "DJI especifica tamaño de sensor y megapíxeles efectivos"
        },
        
        "resolucion_video": {
            "keywords": [
                "Video Resolution",              # Término estándar
                "4K: 3840×2160",                # Resolución 4K estándar
                "5.1K: 5120×2700",              # Mavic 3 Pro específico
                "DCI 4K: 4096×2160",            # Mavic 3 Pro específico
                "FHD: 1920×1080",               # Full HD estándar
            ],
            "notes": "DJI lista múltiples resoluciones, tomar la mayor"
        },
        
        "deteccion_obstaculos": {
            "keywords": [
                "Sensing Type",                  # Sección de detección
                "Omnidirectional binocular vision system", # Sistema estándar
                "supplemented with",             # Sensores adicionales
                "infrared sensor",               # Sensor infrarrojo
                "3D Infrared Sensor",            # Sensor 3D específico
                "Forward-Facing LiDAR",          # Air 3S específico
                "Forward",                       # Direcciones
                "Backward",
                "Lateral",
                "Upward",
                "Downward",
            ],
            "notes": "DJI especifica sistema de visión omnidireccional con sensores adicionales"
        }
    },
    
    # ==================== AUTEL ====================
    # Autel tiene más variabilidad en terminología y formatos
    # Mezcla mayúsculas/minúsculas de manera inconsistente
    "autel": {
        "modelo": {
            "keywords": [
                "EVO Lite Enterprise",           # Modelo específico
                "Autel Alpha",                   # Modelo específico
                "EVO Max 4T",                    # Modelo específico
                "EVO II Pro Enterprise",         # Modelo específico
                "EVO II Dual 640T",             # Modelo específico
                "EVO",                           # Serie común
                "Alpha",                         # Serie Alpha
                "Dragonfish",                    # Serie Dragonfish
            ],
            "notes": "Autel usa prefijos como 'EVO', 'Alpha' en títulos y especificaciones"
        },
        
        "peso_gramos": {
            "keywords": [
                "Weight",                        # Término más común
                "Takeoff Weight",                # Alternativa
                "Maximum takeoff weight",        # Minúsculas
                "Maximum Take-Off Mass",         # MTOM
                "866 g",                         # EVO Lite específico
                "1665 g",                        # EVO Max 4T específico
                "1700 g",                        # EVO Max 4N específico
                "1715 g",                        # EVO Max 4NZ específico
                "6480 g",                        # Autel Alpha específico
                "1110 g",                        # EVO II Pro específico
                "1209 g",                        # EVO II Dual específico
                "Smart battery",                 # Contexto de inclusión
                "propellers included",           # Hélices incluidas
                "gimbal included",               # Gimbal incluido
            ],
            "notes": "Autel especifica qué está incluido en el peso (batería, hélices, gimbal)"
        },
        
        "dimensiones_plegado": {
            "keywords": [
                "Dimensions",                    # Término genérico
                "folded",                        # Plegado
                "210×123×95mm (folded",          # EVO Lite específico
                "455×263×248 mm (folded",        # Alpha específico
                "245×130×111mm",                 # EVO II Pro específico
                "230×130×108mm",                 # EVO II Dual específico
                "propellers included",           # Hélices incluidas
                "excl. propellers",              # Hélices excluidas
            ],
            "notes": "Autel especifica si incluye o excluye hélices en dimensiones plegadas"
        },
        
        "vuelo_minutos": {
            "keywords": [
                "Maximum flight time",           # Término común
                "Max Flight Time",               # Alternativa
                "40 minutes",                    # EVO Lite y Alpha específico
                "42 minutes",                    # EVO Max 4T y EVO II Pro específico
                "38 minutes",                    # EVO II Dual específico
                "no wind",                       # Condiciones
                "windless",                      # Sin viento
                "Windless, Speed: 10.5 m/s",    # Alpha específico
                "Test data from lab",            # Contexto de medición
            ],
            "notes": "Autel especifica condiciones de viento y velocidad de prueba"
        },
        
        "vel_horizontal_mps": {
            "keywords": [
                "Maximum horizontal flight speed", # Término común
                "Max Horizontal Speed",          # Alternativa
                "Ludicrous:",                    # Modo máximo
                "18 m/s",                        # EVO Lite específico
                "25 m/s",                        # Alpha específico
                "23 m/s",                        # EVO Max 4T específico
                "20 m/s",                        # EVO II específico
                "Windless Near Sea Level",       # Condiciones
                "no wind near sea level",        # Condiciones alternativas
            ],
            "notes": "Autel especifica velocidad máxima en modo 'Ludicrous'"
        },
        
        "vel_ascenso_mps": {
            "keywords": [
                "Maximum ascent speed",          # Término común
                "Max Ascent Speed",              # Alternativa
                "Ludicrous:",                    # Modo máximo
                "6 m/s",                         # EVO Lite específico
                "15 m/s",                        # Alpha específico
                "8 m/s",                         # EVO Max 4T y EVO II específico
            ],
            "notes": "Autel especifica velocidad máxima en modo 'Ludicrous'"
        },
        
        "alcance_video_km": {
            "keywords": [
                "Maximum signal effective distance", # EVO Lite específico
                "Maximum Transmission Distance",  # Más común
                "Max Transmission Distance",      # Alternativa
                "No interference, no obstruction", # Condiciones
                "Without Interference and Blocking", # Condiciones alternativas
                "FCC: 12 km",                    # EVO Lite específico
                "CE: 6 km",                      # Europa
                "FCC: 15 km",                    # Alpha y EVO Max específico
                "CE: 8 km",                      # Europa para Alpha/EVO Max
                "FCC: 10 km",                    # EVO II específico
            ],
            "notes": "Autel especifica valores FCC/CE/SRRC por separado"
        },
        
        "altitud_despegue_m": {
            "keywords": [
                "Maximum Service Ceiling Above Sea Level", # Término común
                "Max Service Ceiling",           # Alternativa
                "Service Ceiling",               # Corto
                "3000 meters",                   # EVO Lite específico
                "4500 meters",                   # Alpha y EVO Max específico
                "5000 meters",                   # EVO II específico
            ],
            "notes": "Autel especifica altitud máxima sobre nivel del mar"
        },
        
        "resistencia_viento_mps": {
            "keywords": [
                "Maximum Wind Speed Resistance", # Término común
                "Max Wind Speed Resistance",     # Alternativa
                "Wind Resistance",               # Corto
                "10.7 m/s",                      # EVO Lite específico
                "12 m/s",                        # Alpha, EVO Max, EVO II específico
            ],
            "notes": "Autel especifica resistencia al viento en m/s"
        },
        
        "almacenamiento_interno_gb": {
            "keywords": [
                "Internal storage",              # Término común
                "Onboard storage",               # Alternativa
                "Built-in storage",              # Otra alternativa
                "4GB",                           # EVO Lite específico
                "128GB",                         # EVO Max específico
                "8GB",                           # EVO II específico
                "support microSD",               # Soporte para microSD
            ],
            "notes": "Autel especifica almacenamiento interno y soporte para microSD"
        },
        
        "sensor_camara": {
            "keywords": [
                "Image sensor",                  # Término común
                "Image Sensor",                  # Capitalizado
                "CMOS",                          # Tipo de sensor
                "1 inch CMOS",                   # EVO Lite específico
                "1/2\" CMOS",                    # EVO Max específico
                "1/1.28 inch CMOS",             # EVO II Dual específico
                "20 million pixels",             # EVO Lite específico
                "48 million pixels",             # EVO Max específico
                "50 million pixels",             # EVO II Dual específico
            ],
            "notes": "Autel especifica tamaño de sensor CMOS y megapíxeles"
        },
        
        "resolucion_video": {
            "keywords": [
                "Video resolution",              # Término común
                "Video Resolution",              # Capitalizado
                "3840×2160",                     # 4K estándar
                "5472×3076",                     # EVO II Pro específico
                "P30",                           # 30 fps
                "P60",                           # 60 fps
                "P25",                           # 25 fps
                "P24",                           # 24 fps
            ],
            "notes": "Autel especifica resolución con frame rates (P30, P60, etc.)"
        },
        
        "deteccion_obstaculos": {
            "keywords": [
                "Visual Perception System",      # EVO Lite específico
                "Visual Sensing System",         # Más común
                "Visual Obstacle Avoidance",     # EVO Max específico
                "Millimeter-wave Radar",         # EVO Max específico
                "Sensing range",                 # Rango de detección
                "Forward:",                      # Direcciones
                "Backward:",
                "Sidewards:",
                "Upward:",
                "Downward:",
                "FOV",                           # Campo de visión
                "rich texture",                  # Condiciones ambientales
                "sufficient lighting",           # Condiciones de iluminación
            ],
            "notes": "Autel especifica sistema de visión y radar milimétrico en algunos modelos"
        }
    },
    
    # ==================== PARROT ====================
    # Parrot tiene terminología más directa y simple
    # Formato de especificaciones más conciso
    "parrot": {
        "modelo": {
            "keywords": [
                "ANAFI Ai",                      # Modelo específico
                "ANAFI USA",                     # Modelo específico
                "ANAFI",                         # Serie común
                "Parrot",                        # Marca
            ],
            "notes": "Parrot usa principalmente la serie ANAFI"
        },
        
        "peso_gramos": {
            "keywords": [
                "Weight:",                       # Término simple
                "Mass:",                         # Alternativa
                "898 g",                         # ANAFI Ai específico
                "500 g",                         # ANAFI USA específico
                "1.98 lb",                       # Libras para ANAFI Ai
                "1.10 lb",                       # Libras para ANAFI USA
            ],
            "notes": "Parrot especifica peso en gramos y libras"
        },
        
        "dimensiones_plegado": {
            "keywords": [
                "Size folded:",                  # Término directo
                "304x130x118 mm",               # ANAFI Ai específico
                "252 x 104 x 84 mm",            # ANAFI USA específico
            ],
            "notes": "Parrot usa 'Size folded' directamente"
        },
        
        "vuelo_minutos": {
            "keywords": [
                "Maximum flight time:",          # Término directo
                "32 minutes",                    # Común para ambos modelos
                "30 minutes on MIL version",     # ANAFI USA MIL específico
                "Battery life:",                 # Alternativa
            ],
            "notes": "Parrot especifica tiempo de vuelo máximo directamente"
        },
        
        "vel_horizontal_mps": {
            "keywords": [
                "Maximum horizontal speed:",     # Término directo
                "17 m/s",                        # ANAFI Ai específico
                "14.7 m/s",                      # ANAFI USA específico
                "38 mph",                        # Millas por hora para ANAFI Ai
            ],
            "notes": "Parrot especifica velocidad máxima horizontal en m/s y mph"
        },
        
        "vel_ascenso_mps": {
            "keywords": [
                "Maximum vertical speed:",       # Término directo
                "Maximum ascent speed:",         # Alternativa
                "4 m/s",                         # Común para ambos modelos
                "6 m/s on unlocked",             # ANAFI USA específico
                "9 mph",                         # Millas por hora
            ],
            "notes": "Parrot especifica velocidad vertical máxima"
        },
        
        "alcance_video_km": {
            "keywords": [
                "Operating frequencies:",        # Frecuencias de operación
                "2.4 GHz",                       # Banda 2.4 GHz
                "5.8 GHz",                       # Banda 5.8 GHz
                "UNII-1",                        # Banda específica
                "UNII-3",                        # Banda específica
                "4G/WiFi switching",             # Conectividad 4G/WiFi
                "Files Beyond Visual Line Of Sight", # BVLOS
            ],
            "notes": "Parrot no especifica alcance específico, usa conectividad 4G/WiFi"
        },
        
        "altitud_despegue_m": {
            "keywords": [
                "Service ceiling:",              # Término directo
                "5,000 m",                       # 5000 metros
                "5000 m above MSL",              # Sobre nivel del mar
                "above sea level",               # Sobre nivel del mar
            ],
            "notes": "Parrot especifica altitud de servicio sobre nivel del mar"
        },
        
        "resistencia_viento_mps": {
            "keywords": [
                "Maximum wind resistance:",     # Término directo
                "14 m/s",                       # ANAFI Ai específico
                "14.7 m/s",                     # ANAFI USA específico
                "31.3 mph",                     # Millas por hora
                "during flight",                # Durante vuelo
                "during take-off and landing",  # Durante despegue y aterrizaje
            ],
            "notes": "Parrot especifica resistencia al viento en m/s y mph"
        },
        
        "almacenamiento_interno_gb": {
            "keywords": [
                "MicroSD and SIM card slots",    # Ranuras para tarjetas
                "SD card AES-XTS encryption",   # Encriptación de tarjeta SD
                "Internal storage",             # Almacenamiento interno
                "Built-in storage",             # Almacenamiento integrado
            ],
            "notes": "Parrot no especifica almacenamiento interno, usa ranuras para tarjetas"
        },
        
        "sensor_camara": {
            "keywords": [
                "Sensor:",                       # Término directo
                "Image sensor",                  # Sensor de imagen
                "1/2'' 48 MP CMOS",             # ANAFI Ai específico
                "1/2.4''",                      # ANAFI USA específico
                "2 sensors:",                    # Dos sensores
                "EO IMAGE CHAIN",                # Cadena de imagen EO
                "CMOS",                          # Tipo de sensor
            ],
            "notes": "Parrot especifica sensores CMOS con megapíxeles"
        },
        
        "resolucion_video": {
            "keywords": [
                "Video resolution:",             # Término directo
                "Video resolutions:",            # Plural
                "4K UHD: 3840x2160",            # 4K Ultra HD
                "1080p: 1920x1080",             # Full HD
                "4K/FHD/HD",                     # Resoluciones disponibles
                "MP4 (H.264)",                   # Formato de video
            ],
            "notes": "Parrot especifica resoluciones de video disponibles"
        },
        
        "deteccion_obstaculos": {
            "keywords": [
                "Stereoscopic cameras",          # Cámaras estereoscópicas
                "rotating gimbal",               # Gimbal rotativo
                "obstacle avoidance",            # Evitación de obstáculos
                "Vertical camera",               # Cámara vertical
                "Time of Flight",                # Sensor ToF
                "ultra-sonar",                   # Ultrasonido
                "AI trajectory optimization",    # Optimización de trayectoria IA
            ],
            "notes": "Parrot usa cámaras estereoscópicas en gimbal rotativo para evitación de obstáculos"
        }
    }
}

# ==================== URL_MAPPINGS ====================
# Mapeo de URLs a marcas para identificar el parser correcto
URL_MAPPINGS = {
    "dji.com": "dji",
    "autelrobotics.com": "autel", 
    "parrot.com": "parrot"
}

# ==================== SPEC_EXTRACTION_RULES ====================
# Reglas específicas para cada campo y marca
SPEC_EXTRACTION_RULES = {
    "peso_gramos": {
        "units": ["g", "gramos", "kg", "kilogramos", "lb", "libras"],
        "conversion": {
            "kg": 1000,    # kg a gramos
            "lb": 453.592  # lb a gramos
        },
        "patterns": [
            r"(\d+(?:\.\d+)?)\s*(?:g|gramos)",
            r"(\d+(?:\.\d+)?)\s*(?:kg|kilogramos)", 
            r"(\d+(?:\.\d+)?)\s*(?:lb|libras)",
            r"<\s*(\d+(?:\.\d+)?)\s*g",  # Para "< 249 g"
        ]
    },
    
    "dimensiones_plegado": {
        "patterns": [
            r"(\d+(?:\.\d+)?)×(\d+(?:\.\d+)?)×(\d+(?:\.\d+)?)\s*mm",
            r"(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*mm",
            r"(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*mm",
        ]
    },
    
    "vuelo_minutos": {
        "patterns": [
            r"(\d+(?:\.\d+)?)\s*(?:minutes|minutos|min)",
            r"(\d+(?:\.\d+)?)\s*(?:hours|horas|h)",
        ],
        "conversion": {
            "hours": 60,  # horas a minutos
            "horas": 60,
            "h": 60
        }
    },
    
    "vel_horizontal_mps": {
        "patterns": [
            r"(\d+(?:\.\d+)?)\s*(?:m/s|mps)",
            r"(\d+(?:\.\d+)?)\s*(?:km/h|kmh|kph)",
            r"(\d+(?:\.\d+)?)\s*(?:mph|miles/h)",
        ],
        "conversion": {
            "km/h": 0.277778,  # km/h a m/s
            "kmh": 0.277778,
            "kph": 0.277778,
            "mph": 0.44704,    # mph a m/s
            "miles/h": 0.44704
        }
    },
    
    "vel_ascenso_mps": {
        "patterns": [
            r"(\d+(?:\.\d+)?)\s*(?:m/s|mps)",
            r"(\d+(?:\.\d+)?)\s*(?:km/h|kmh|kph)",
            r"(\d+(?:\.\d+)?)\s*(?:mph|miles/h)",
        ],
        "conversion": {
            "km/h": 0.277778,
            "kmh": 0.277778,
            "kph": 0.277778,
            "mph": 0.44704,
            "miles/h": 0.44704
        }
    },
    
    "alcance_video_km": {
        "patterns": [
            r"(\d+(?:\.\d+)?)\s*(?:km|kilómetros)",
            r"(\d+(?:\.\d+)?)\s*(?:m|metros)",
            r"FCC:\s*(\d+(?:\.\d+)?)\s*km",
            r"CE:\s*(\d+(?:\.\d+)?)\s*km",
        ],
        "conversion": {
            "m": 0.001,    # metros a km
            "metros": 0.001
        }
    },
    
    "altitud_despegue_m": {
        "patterns": [
            r"(\d+(?:\.\d+)?)\s*(?:m|metros)",
            r"(\d+(?:\.\d+)?)\s*(?:km|kilómetros)",
            r"(\d+(?:\.\d+)?)\s*(?:ft|feet|pies)",
        ],
        "conversion": {
            "km": 1000,     # km a metros
            "kilómetros": 1000,
            "ft": 0.3048,   # pies a metros
            "feet": 0.3048,
            "pies": 0.3048
        }
    },
    
    "resistencia_viento_mps": {
        "patterns": [
            r"(\d+(?:\.\d+)?)\s*(?:m/s|mps)",
            r"(\d+(?:\.\d+)?)\s*(?:km/h|kmh|kph)",
            r"(\d+(?:\.\d+)?)\s*(?:mph|miles/h)",
        ],
        "conversion": {
            "km/h": 0.277778,
            "kmh": 0.277778,
            "kph": 0.277778,
            "mph": 0.44704,
            "miles/h": 0.44704
        }
    },
    
    "almacenamiento_interno_gb": {
        "patterns": [
            r"(\d+(?:\.\d+)?)\s*(?:GB|gb)",
            r"(\d+(?:\.\d+)?)\s*(?:TB|tb)",
            r"(\d+(?:\.\d+)?)\s*(?:MB|mb)",
        ],
        "conversion": {
            "TB": 1024,     # TB a GB
            "tb": 1024,
            "MB": 0.001,    # MB a GB
            "mb": 0.001
        }
    }
}

# ==================== CONFIDENCE_SCORING ====================
# Sistema de puntuación para determinar la confianza en las extracciones
CONFIDENCE_WEIGHTS = {
    "exact_match": 1.0,        # Coincidencia exacta de palabra clave
    "partial_match": 0.8,      # Coincidencia parcial
    "numeric_value": 0.9,      # Valor numérico encontrado
    "unit_match": 0.7,         # Unidad coincidente
    "context_match": 0.6,      # Contexto relacionado
    "brand_specific": 0.9,     # Término específico de la marca
}

# ==================== PROCESSING_PRIORITIES ====================
# Prioridades para procesar especificaciones cuando hay múltiples coincidencias
PROCESSING_PRIORITIES = {
    "dji": {
        "peso_gramos": ["Takeoff Weight", "< 249 g"],
        "dimensiones_plegado": ["Folded (without propellers)"],
        "vuelo_minutos": ["Max Flight Time"],
        "vel_horizontal_mps": ["Max Horizontal Speed"],
        "vel_ascenso_mps": ["Max Ascent Speed"],
        "alcance_video_km": ["Max Transmission Distance", "FCC:"],
        "altitud_despegue_m": ["Max Takeoff Altitude"],
        "resistencia_viento_mps": ["Max Wind Speed Resistance"],
        "almacenamiento_interno_gb": ["Internal Storage"],
        "sensor_camara": ["Image Sensor", "CMOS"],
        "resolucion_video": ["Video Resolution", "4K", "5.1K"],
        "deteccion_obstaculos": ["Omnidirectional", "binocular vision"]
    },
    
    "autel": {
        "peso_gramos": ["Takeoff Weight", "Weight"],
        "dimensiones_plegado": ["folded", "Dimensions"],
        "vuelo_minutos": ["Maximum flight time", "Max Flight Time"],
        "vel_horizontal_mps": ["Maximum horizontal flight speed", "Ludicrous:"],
        "vel_ascenso_mps": ["Maximum ascent speed", "Ludicrous:"],
        "alcance_video_km": ["Maximum Transmission Distance", "FCC:"],
        "altitud_despegue_m": ["Maximum Service Ceiling Above Sea Level"],
        "resistencia_viento_mps": ["Maximum Wind Speed Resistance"],
        "almacenamiento_interno_gb": ["Internal storage", "Onboard storage"],
        "sensor_camara": ["Image sensor", "CMOS"],
        "resolucion_video": ["Video resolution", "3840×2160"],
        "deteccion_obstaculos": ["Visual Sensing System", "Millimeter-wave Radar"]
    },
    
    "parrot": {
        "peso_gramos": ["Weight:", "Mass:"],
        "dimensiones_plegado": ["Size folded:"],
        "vuelo_minutos": ["Maximum flight time:", "Battery life:"],
        "vel_horizontal_mps": ["Maximum horizontal speed:"],
        "vel_ascenso_mps": ["Maximum vertical speed:", "Maximum ascent speed:"],
        "alcance_video_km": ["Operating frequencies:", "4G/WiFi"],
        "altitud_despegue_m": ["Service ceiling:"],
        "resistencia_viento_mps": ["Maximum wind resistance:"],
        "almacenamiento_interno_gb": ["MicroSD", "Internal storage"],
        "sensor_camara": ["Sensor:", "CMOS"],
        "resolucion_video": ["Video resolution:", "4K UHD"],
        "deteccion_obstaculos": ["Stereoscopic cameras", "obstacle avoidance"]
    }
}

# ==================== DATA_CONSTANTS ====================
class DataConstants:
    NOT_AVAILABLE = "NOT_AVAILABLE"
    NOT_SPECIFIED = "NOT_SPECIFIED"
    PARSE_FAILED = "PARSE_FAILED"
    MULTIPLE_VALUES = "MULTIPLE_VALUES"
    CONFIDENCE_THRESHOLD = 0.6
    
    # Valores por defecto para campos no encontrados
    DEFAULT_VALUES = {
        "modelo": "Unknown Model",
        "peso_gramos": 0,
        "dimensiones_plegado": "0x0x0 mm",
        "vuelo_minutos": 0,
        "vel_horizontal_mps": 0,
        "vel_ascenso_mps": 0,
        "alcance_video_km": 0,
        "altitud_despegue_m": 0,
        "resistencia_viento_mps": 0,
        "almacenamiento_interno_gb": 0,
        "sensor_camara": "Unknown sensor",
        "resolucion_video": "Unknown resolution",
        "deteccion_obstaculos": "Unknown system"
    }

# ==================== VALIDATION_RULES ====================
# Reglas de validación para verificar que los valores extraídos son realistas
VALIDATION_RULES = {
    "peso_gramos": {
        "min": 50,      # Mínimo 50g
        "max": 50000,   # Máximo 50kg
        "type": "numeric"
    },
    "vuelo_minutos": {
        "min": 5,       # Mínimo 5 minutos
        "max": 300,     # Máximo 5 horas
        "type": "numeric"
    },
    "vel_horizontal_mps": {
        "min": 1,       # Mínimo 1 m/s
        "max": 50,      # Máximo 50 m/s
        "type": "numeric"
    },
    "vel_ascenso_mps": {
        "min": 0.5,     # Mínimo 0.5 m/s
        "max": 20,      # Máximo 20 m/s
        "type": "numeric"
    },
    "alcance_video_km": {
        "min": 0.1,     # Mínimo 100m
        "max": 50,      # Máximo 50km
        "type": "numeric"
    },
    "altitud_despegue_m": {
        "min": 100,     # Mínimo 100m
        "max": 15000,   # Máximo 15km
        "type": "numeric"
    },
    "resistencia_viento_mps": {
        "min": 1,       # Mínimo 1 m/s
        "max": 25,      # Máximo 25 m/s
        "type": "numeric"
    },
    "almacenamiento_interno_gb": {
        "min": 0,       # Puede ser 0 si no tiene
        "max": 2000,    # Máximo 2TB
        "type": "numeric"
    }
}

# ==================== LOGGING_CONFIG ====================
# Configuración para logging detallado del proceso de extracción
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "handlers": {
        "file": {
            "filename": "drone_scraper.log",
            "max_bytes": 10485760,  # 10MB
            "backup_count": 5
        },
        "console": {
            "level": "INFO"
        }
    }
}

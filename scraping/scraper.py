# Drone Scraper Orchestrator
# Coordina la extracción de datos de DJI, Autel y Parrot

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tenacity import retry, stop_after_attempt, wait_exponential

from data_cleaner import DataCleaner
from data_validator import DataValidator
from robot_checker import RobotChecker
from scraper_config import SCRAPER_CONFIG

# Configuración de logging
# Crear directorio de datos si no existe
log_dir = Path(__file__).parent.parent / 'data'
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / 'extraction_log.json'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DroneScraperOrchestrator:
    """Orquestador principal para el scraping de drones"""
    
    def __init__(self):
        self.robot_checker = RobotChecker()
        self.data_cleaner = DataCleaner()
        self.data_validator = DataValidator()
        self.session = None
        self.driver = None
        self.extraction_stats = {
            'start_time': datetime.now().isoformat(),
            'brands_scraped': {},
            'total_products': 0,
            'errors': []
        }
    
    async def scrape_all_brands(self) -> Dict[str, List[Dict]]:
        """Scraping coordinado de todas las marcas"""
        results = {}
        
        async with aiohttp.ClientSession() as self.session:
            for brand, config in SCRAPER_CONFIG.items():
                logger.info(f"Iniciando scraping de {brand}...")
                
                # Verificar robots.txt
                can_scrape, message = self.robot_checker.can_scrape_advanced(
                    config['base_url']
                )
                
                if not can_scrape:
                    logger.warning(f"No se puede scrapear {brand}: {message}")
                    self.extraction_stats['errors'].append({
                        'brand': brand,
                        'error': message,
                        'timestamp': datetime.now().isoformat()
                    })
                    continue
                
                # Obtener delay de crawl
                crawl_delay = self.robot_checker.get_crawl_delay(
                    urljoin(config['base_url'], '/robots.txt')
                )
                
                # Realizar scraping con delay apropiado
                try:
                    brand_data = await self._scrape_brand(brand, config, crawl_delay)
                    results[brand] = brand_data
                    self.extraction_stats['brands_scraped'][brand] = len(brand_data)
                    self.extraction_stats['total_products'] += len(brand_data)
                    
                    # Guardar datos crudos
                    self.save_raw_data(brand, brand_data)
                    
                except Exception as e:
                    logger.error(f"Error al scrapear {brand}: {str(e)}")
                    self.extraction_stats['errors'].append({
                        'brand': brand,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
        
        # Guardar estadísticas de extracción
        self._save_extraction_stats()
        
        return results
    
    async def _scrape_brand(self, brand: str, config: Dict, crawl_delay: float) -> List[Dict]:
        """Scraping específico por marca"""
        products = []
        
        if config.get('requires_js', False):
            # Usar Selenium para sitios con JavaScript
            products = await self._scrape_with_selenium(brand, config)
        else:
            # Usar requests para sitios estáticos
            products = await self._scrape_with_requests(brand, config)
        
        # Esperar el delay apropiado entre páginas
        await asyncio.sleep(crawl_delay)
        
        return products
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _scrape_with_requests(self, brand: str, config: Dict) -> List[Dict]:
        """Scraping de sitios estáticos"""
        products = []
        
        # Obtener headers apropiados
        headers = self._get_headers()
        
        # Verificar si las URLs son directas a productos específicos
        if config.get('direct_product_urls', False):
            # Scrapear directamente cada URL de producto
            for product_url in config['product_urls']:
                # Manejar PDFs especialmente (Parrot)
                if product_url.endswith('.pdf') and config.get('has_pdf_content', False):
                    product_data = await self._scrape_pdf_content(product_url, brand, config)
                else:
                    product_data = await self._scrape_product_page(product_url, brand, config)
                
                if product_data:
                    products.append(product_data)
                
                # Respetar rate limiting
                await asyncio.sleep(config.get('delay_between_requests', 3))
        else:
            # Método original: buscar enlaces en páginas de listado
            for product_list_url in config['product_urls']:
                async with self.session.get(product_list_url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        
                        # Extraer links de productos
                        product_links = self._extract_product_links(soup, config)
                        
                        # Scrapear cada producto
                        for link in product_links[:config.get('max_products', 50)]:
                            product_data = await self._scrape_product_page(link, brand, config)
                            if product_data:
                                products.append(product_data)
                            
                            # Respetar rate limiting
                            await asyncio.sleep(config.get('delay_between_requests', 3))
        
        return products
    
    async def _scrape_with_selenium(self, brand: str, config: Dict) -> List[Dict]:
        """Scraping de sitios con JavaScript pesado"""
        products = []
        
        self.driver = self.setup_selenium_driver()
        
        try:
            # Verificar si las URLs son directas a productos específicos
            if config.get('direct_product_urls', False):
                # Scrapear directamente cada URL de producto
                for product_url in config['product_urls']:
                    self.driver.get(product_url)
                    
                    # Esperar carga de contenido dinámico
                    wait = WebDriverWait(self.driver, 15)
                    try:
                        wait.until(EC.presence_of_element_located(
                            (By.CSS_SELECTOR, config['selectors']['product_name'])
                        ))
                    except:
                        # Si no encuentra el selector específico, esperar carga general
                        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                    
                    # Extraer datos del producto
                    product_soup = BeautifulSoup(self.driver.page_source, 'lxml')
                    product_data = self.extract_drone_specs(product_soup, brand, product_url)
                    
                    if product_data:
                        products.append(product_data)
                    
                    # Delay entre productos
                    await asyncio.sleep(config.get('delay_between_requests', 3))
            else:
                # Método original: buscar enlaces en páginas de listado
                for product_list_url in config['product_urls']:
                    self.driver.get(product_list_url)
                    
                    # Esperar carga de contenido dinámico
                    wait = WebDriverWait(self.driver, 10)
                    wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, config['selectors']['product_list'])
                    ))
                    
                    # Manejar scroll infinito si es necesario
                    if config.get('infinite_scroll', False):
                        self._handle_infinite_scroll()
                    
                    # Extraer HTML después de JS
                    soup = BeautifulSoup(self.driver.page_source, 'lxml')
                    product_links = self._extract_product_links(soup, config)
                    
                    # Scrapear cada producto
                    for link in product_links[:config.get('max_products', 50)]:
                        self.driver.get(link)
                        
                        # Esperar carga completa
                        wait.until(EC.presence_of_element_located(
                            (By.CSS_SELECTOR, config['selectors']['product_name'])
                        ))
                        
                        # Extraer datos
                        product_soup = BeautifulSoup(self.driver.page_source, 'lxml')
                        product_data = self.extract_drone_specs(product_soup, brand, link)
                        
                        if product_data:
                            products.append(product_data)
                        
                        # Delay entre productos
                        await asyncio.sleep(config.get('delay_between_requests', 3))
        
        finally:
            if self.driver:
                self.driver.quit()
        
        return products
    
    def setup_selenium_driver(self) -> webdriver.Chrome:
        """Configurar driver de Selenium con opciones avanzadas"""
        options = Options()
        
        # Opciones para parecer un navegador real
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User agent rotativo
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        
        import random
        options.add_argument(f'user-agent={random.choice(user_agents)}')
        
        # Otras opciones útiles
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        driver = webdriver.Chrome(options=options)
        
        # Inyectar JavaScript para ocultar automatización
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def handle_spa_loading(self, url: str) -> BeautifulSoup:
        """Manejar carga de Single Page Applications"""
        if not self.driver:
            self.driver = self.setup_selenium_driver()
        
        self.driver.get(url)
        
        # Esperar indicadores específicos de carga completa
        wait = WebDriverWait(self.driver, 20)
        
        # Intentar múltiples estrategias
        try:
            # Esperar por contenido específico
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "product-grid")))
        except:
            # Fallback: esperar por estado de documento
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        
        # Espera adicional para AJAX
        asyncio.run(asyncio.sleep(2))
        
        return BeautifulSoup(self.driver.page_source, 'lxml')
    
    async def _scrape_product_page(self, url: str, brand: str, config: Dict) -> Optional[Dict]:
        """Scrapear página individual de producto"""
        try:
            headers = self._get_headers()
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    return self.extract_drone_specs(soup, brand, url)
        except Exception as e:
            logger.error(f"Error scrapeando {url}: {str(e)}")
            return None
    
    async def _scrape_pdf_content(self, pdf_url: str, brand: str, config: Dict) -> Optional[Dict]:
        """Scrapear contenido de archivos PDF (especialmente para Parrot)"""
        try:
            import pdfplumber
            import io
            
            headers = self._get_headers()
            async with self.session.get(pdf_url, headers=headers) as response:
                if response.status == 200:
                    pdf_content = await response.read()
                    
                    # Extraer texto del PDF
                    with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                        text = ""
                        for page in pdf.pages:
                            text += page.extract_text() or ""
                    
                    # Extraer nombre del modelo desde la URL
                    model_name = self._extract_model_from_pdf_url(pdf_url)
                    
                    # Crear estructura base del drone
                    drone_data = {
                        'marca': brand,
                        'modelo': model_name,
                        'url_fuente': pdf_url,
                        'metadata': {
                            'fecha_extraccion': datetime.now().isoformat(),
                            'version_scraper': '1.0.0',
                            'confiabilidad_datos': 'media',
                            'tipo_fuente': 'pdf'
                        }
                    }
                    
                    # Extraer especificaciones del texto
                    specs = self._extract_specs_from_pdf_text(text, config)
                    drone_data.update(specs)
                    
                    return drone_data
                    
        except ImportError:
            logger.warning("pdfplumber no instalado. Instalar con: pip install pdfplumber")
            return None
        except Exception as e:
            logger.error(f"Error procesando PDF {pdf_url}: {str(e)}")
            return None
    
    def _extract_model_from_url(self, url: str) -> str:
        """Extraer nombre del modelo desde la URL como fallback"""
        try:
            from urllib.parse import urlparse
            
            # Extraer el path de la URL
            path = urlparse(url).path
            
            # Obtener la última parte del path
            model_part = path.split('/')[-1]
            
            # Limpiar y formatear
            if model_part:
                # Reemplazar guiones con espacios y capitalizar
                model_name = model_part.replace('-', ' ').replace('_', ' ')
                
                # Capitalizar cada palabra
                model_name = ' '.join(word.capitalize() for word in model_name.split())
                
                # Mapeos específicos conocidos
                mappings = {
                    'Mini 4 Pro': 'Mini 4 Pro',
                    'Mavic 3 Pro': 'Mavic 3 Pro',
                    'Mavic 3 Classic': 'Mavic 3 Classic',
                    'Air 3s': 'Air 3S',
                    'Air 3': 'Air 3',
                    'Mini 3': 'Mini 3',
                    'Avata 2': 'Avata 2',
                    'Inspire 3': 'Inspire 3',
                    'Evo Max 4t': 'EVO Max 4T',
                    'Evo Max 4n': 'EVO Max 4N',
                    'Evo Lite Enterprise Series': 'EVO Lite Enterprise',
                    'Autel Alpha': 'Alpha',
                    'Evo Ii Pro Drones': 'EVO II Pro',
                    'Evo Ii Enterprise Drones': 'EVO II Enterprise'
                }
                
                return mappings.get(model_name, model_name)
            
            return 'Unknown Model'
            
        except:
            return 'Unknown Model'

    def _extract_model_from_pdf_url(self, pdf_url: str) -> str:
        """Extraer nombre del modelo desde la URL del PDF"""
        if 'ANAFI-Ai' in pdf_url:
            return 'ANAFI Ai'
        elif 'ANAFI-USA' in pdf_url:
            return 'ANAFI USA'
        else:
            # Extraer nombre genérico desde la URL
            from urllib.parse import urlparse
            path = urlparse(pdf_url).path
            filename = path.split('/')[-1].replace('.pdf', '').replace('-', ' ')
            return filename.title()
    
    def _extract_specs_from_pdf_text(self, text: str, config: Dict) -> Dict:
        """Extraer especificaciones técnicas del texto del PDF"""
        import re
        
        specs_data = {
            'especificaciones_tecnicas': {},
            'camara': {},
            'caracteristicas_vuelo': {},
            'precio': {'usd': None, 'moneda_local': None, 'fecha_precio': None}
        }
        
        # Patrones de extracción específicos para PDFs de Parrot
        patterns = config.get('pdf_extraction', {}).get('spec_patterns', [])
        
        # Peso
        weight_match = re.search(r'Weight[:\s]*(\d+\.?\d*)\s*(g|kg|grams?)', text, re.IGNORECASE)
        if weight_match:
            value, unit = weight_match.groups()
            if unit.lower() in ['kg', 'kilograms']:
                specs_data['especificaciones_tecnicas']['peso_gramos'] = float(value) * 1000
            else:
                specs_data['especificaciones_tecnicas']['peso_gramos'] = float(value)
        
        # Tiempo de vuelo
        flight_time_match = re.search(r'(?:Flight time|Autonomy)[:\s]*(\d+)\s*(?:min|minutes)', text, re.IGNORECASE)
        if flight_time_match:
            specs_data['especificaciones_tecnicas']['autonomia_minutos'] = int(flight_time_match.group(1))
        
        # Alcance
        range_match = re.search(r'(?:Range|Control distance)[:\s]*(\d+\.?\d*)\s*(km|m|meters?)', text, re.IGNORECASE)
        if range_match:
            value, unit = range_match.groups()
            if unit.lower() in ['km', 'kilometers']:
                specs_data['especificaciones_tecnicas']['alcance_metros'] = float(value) * 1000
            else:
                specs_data['especificaciones_tecnicas']['alcance_metros'] = float(value)
        
        # Resolución de video
        video_match = re.search(r'(?:Video resolution|Recording)[:\s]*([48]K|1080p|720p)', text, re.IGNORECASE)
        if video_match:
            specs_data['camara']['resolucion_video'] = video_match.group(1).upper()
        
        # Velocidad máxima
        speed_match = re.search(r'(?:Max speed|Maximum speed)[:\s]*(\d+\.?\d*)\s*(?:km/h|m/s)', text, re.IGNORECASE)
        if speed_match:
            specs_data['especificaciones_tecnicas']['velocidad_max_kmh'] = float(speed_match.group(1))
        
        # Características de vuelo (buscar palabras clave)
        features = specs_data['caracteristicas_vuelo']
        if re.search(r'obstacle\s+(?:avoidance|detection)', text, re.IGNORECASE):
            features['evita_obstaculos'] = True
        if re.search(r'return\s+(?:to\s+)?home', text, re.IGNORECASE):
            features['retorno_automatico'] = True
        if re.search(r'(?:follow|tracking)\s+mode', text, re.IGNORECASE):
            features['seguimiento_objeto'] = True
        if re.search(r'GPS', text, re.IGNORECASE):
            features['precision_hover'] = 'GPS'
        
        # Clasificación automática
        specs_data['clasificacion'] = self._classify_drone(specs_data)
        
        return specs_data
    
    def extract_drone_specs(self, soup: BeautifulSoup, brand: str, url: str) -> Dict:
        """Parser inteligente para especificaciones de drones"""
        config = SCRAPER_CONFIG[brand.lower()]
        selectors = config['selectors']
        
        drone_data = {
            'marca': brand,
            'url_fuente': url,
            'metadata': {
                'fecha_extraccion': datetime.now().isoformat(),
                'version_scraper': '1.0.0',
                'confiabilidad_datos': 'alta'
            }
        }
        
        # Extraer nombre del modelo
        try:
            name_elem = soup.select_one(selectors['product_name'])
            if name_elem:
                model_name = name_elem.text.strip()
                # Limpiar el nombre del modelo
                if model_name and model_name != '':
                    # Remover palabras comunes que no son parte del modelo
                    model_name = model_name.replace('DJI ', '').replace('Autel ', '').replace('Parrot ', '')
                    drone_data['modelo'] = model_name
                else:
                    # Intentar extraer desde la URL
                    drone_data['modelo'] = self._extract_model_from_url(url)
            else:
                # Fallback: extraer desde la URL
                drone_data['modelo'] = self._extract_model_from_url(url)
        except:
            drone_data['modelo'] = self._extract_model_from_url(url)
        
        # Extraer precio
        try:
            price_elem = soup.select_one(selectors['price'])
            if price_elem:
                price_text = price_elem.text.strip()
                drone_data['precio'] = {
                    'usd': self.data_cleaner.normalize_price_formats(price_text),
                    'moneda_local': None,
                    'fecha_precio': datetime.now().strftime('%Y-%m-%d')
                }
        except:
            drone_data['precio'] = {'usd': None, 'moneda_local': None, 'fecha_precio': None}
        
        # Extraer especificaciones técnicas
        specs = self._extract_technical_specs(soup, selectors)
        drone_data['especificaciones_tecnicas'] = specs
        
        # Extraer características de cámara
        camera_specs = self._extract_camera_specs(soup, selectors)
        drone_data['camara'] = camera_specs
        
        # Extraer características de vuelo
        flight_features = self._extract_flight_features(soup, selectors)
        drone_data['caracteristicas_vuelo'] = flight_features
        
        # Clasificación automática
        drone_data['clasificacion'] = self._classify_drone(drone_data)
        
        return drone_data
    
    def _extract_technical_specs(self, soup: BeautifulSoup, selectors: Dict) -> Dict:
        """Extraer especificaciones técnicas"""
        specs = {
            'peso_gramos': None,
            'autonomia_minutos': None,
            'alcance_metros': None,
            'velocidad_max_kmh': None,
            'resistencia_viento': None,
            'temperatura_operacion': None
        }
        
        # Buscar tabla de especificaciones
        specs_table = soup.select_one(selectors.get('specs_table', '.specs-table'))
        if specs_table:
            # Procesar tabla
            rows = specs_table.select('tr')
            for row in rows:
                cells = row.select('td, th')
                if len(cells) >= 2:
                    label = cells[0].text.strip().lower()
                    value = cells[1].text.strip()
                    
                    # Mapear a campos estándar
                    if any(keyword in label for keyword in ['weight', 'peso', 'mass']):
                        specs['peso_gramos'] = self.data_cleaner.extract_number(value, 'grams')
                    elif any(keyword in label for keyword in ['flight time', 'autonomía', 'battery life', 'endurance']):
                        specs['autonomia_minutos'] = self.data_cleaner.extract_number(value, 'minutes')
                    elif any(keyword in label for keyword in ['range', 'alcance', 'transmission', 'control distance']):
                        specs['alcance_metros'] = self.data_cleaner.extract_number(value, 'meters')
                    elif any(keyword in label for keyword in ['speed', 'velocidad', 'velocity']):
                        specs['velocidad_max_kmh'] = self.data_cleaner.extract_number(value, 'kmh')
                    elif any(keyword in label for keyword in ['wind', 'viento']):
                        specs['resistencia_viento'] = value
                    elif any(keyword in label for keyword in ['temperature', 'temperatura']):
                        specs['temperatura_operacion'] = value
        else:
            # Si no hay tabla, buscar en todo el texto de la página
            page_text = soup.get_text().lower()
            
            # Usar patrones regex para extraer specs del texto general
            import re
            
            # Peso
            weight_patterns = [
                r'weight[:\s]*(\d+\.?\d*)\s*(g|grams?|kg)',
                r'(\d+\.?\d*)\s*(g|grams?)\s*weight',
                r'weighs?\s*(\d+\.?\d*)\s*(g|grams?|kg)'
            ]
            
            for pattern in weight_patterns:
                match = re.search(pattern, page_text)
                if match:
                    value, unit = match.groups()
                    if unit.lower() in ['kg']:
                        specs['peso_gramos'] = float(value) * 1000
                    else:
                        specs['peso_gramos'] = float(value)
                    break
            
            # Tiempo de vuelo
            flight_patterns = [
                r'flight time[:\s]*(\d+)\s*(?:min|minutes)',
                r'(\d+)\s*(?:min|minutes?)\s*flight\s*time',
                r'up to\s*(\d+)\s*(?:min|minutes?)\s*flight'
            ]
            
            for pattern in flight_patterns:
                match = re.search(pattern, page_text)
                if match:
                    specs['autonomia_minutos'] = int(match.group(1))
                    break
            
            # Alcance
            range_patterns = [
                r'range[:\s]*(\d+\.?\d*)\s*(km|m|meters?|kilometres?)',
                r'transmission range[:\s]*(\d+\.?\d*)\s*(km|m)',
                r'up to\s*(\d+\.?\d*)\s*(km|m)\s*range'
            ]
            
            for pattern in range_patterns:
                match = re.search(pattern, page_text)
                if match:
                    value, unit = match.groups()
                    if unit.lower() in ['km', 'kilometres', 'kilometers']:
                        specs['alcance_metros'] = float(value) * 1000
                    else:
                        specs['alcance_metros'] = float(value)
                    break
        
        return specs
    
    def _extract_camera_specs(self, soup: BeautifulSoup, selectors: Dict) -> Dict:
        """Extraer especificaciones de cámara"""
        camera = {
            'resolucion_video': None,
            'fps_max': None,
            'sensor_tamaño': None,
            'estabilizacion': None,
            'zoom_optico': None,
            'zoom_digital': None
        }
        
        # Buscar sección de cámara
        camera_section = soup.select_one(selectors.get('camera_section', '.camera-specs'))
        if camera_section:
            # Buscar resolución de video
            for elem in camera_section.select('*'):
                text = elem.text.lower()
                if '4k' in text:
                    camera['resolucion_video'] = '4K'
                elif '6k' in text:
                    camera['resolucion_video'] = '6K'
                elif '8k' in text:
                    camera['resolucion_video'] = '8K'
                elif '1080p' in text:
                    camera['resolucion_video'] = '1080p'
                
                # FPS
                if 'fps' in text or 'frames' in text:
                    fps = self.data_cleaner.extract_number(text, 'fps')
                    if fps:
                        camera['fps_max'] = fps
                
                # Estabilización
                if 'gimbal' in text or 'estabilización' in text:
                    if 'mechanical' in text or 'mecánica' in text:
                        camera['estabilizacion'] = 'mecanica'
                    elif 'digital' in text:
                        camera['estabilizacion'] = 'digital'
                    elif 'hybrid' in text or 'híbrida' in text:
                        camera['estabilizacion'] = 'hibrida'
        
        return camera
    
    def _extract_flight_features(self, soup: BeautifulSoup, selectors: Dict) -> Dict:
        """Extraer características de vuelo"""
        features = {
            'evita_obstaculos': False,
            'retorno_automatico': False,
            'seguimiento_objeto': False,
            'vuelo_nocturno': False,
            'modo_sport': False,
            'precision_hover': None
        }
        
        # Buscar sección de características
        features_section = soup.select_one(selectors.get('features_section', '.features'))
        if features_section:
            features_text = features_section.text.lower()
            
            # Detección de características por palabras clave
            if 'obstacle' in features_text or 'obstáculo' in features_text:
                features['evita_obstaculos'] = True
            if 'return home' in features_text or 'retorno' in features_text:
                features['retorno_automatico'] = True
            if 'follow' in features_text or 'tracking' in features_text or 'seguimiento' in features_text:
                features['seguimiento_objeto'] = True
            if 'night' in features_text or 'nocturno' in features_text:
                features['vuelo_nocturno'] = True
            if 'sport' in features_text:
                features['modo_sport'] = True
            if 'hover' in features_text:
                features['precision_hover'] = 'GPS/GLONASS'
        
        return features
    
    def _classify_drone(self, drone_data: Dict) -> Dict:
        """Clasificación automática del drone"""
        classification = {
            'categoria_peso': 'medio',
            'nivel_usuario': 'intermedio',
            'uso_principal': [],
            'certificaciones': []
        }
        
        # Clasificar por peso
        peso = drone_data.get('especificaciones_tecnicas', {}).get('peso_gramos', 0)
        if peso and peso < 250:
            classification['categoria_peso'] = 'ultra_ligero'
        elif peso and peso < 500:
            classification['categoria_peso'] = 'ligero'
        elif peso and peso < 1000:
            classification['categoria_peso'] = 'medio'
        else:
            classification['categoria_peso'] = 'pesado'
        
        # Clasificar por características
        camera = drone_data.get('camara', {})
        if camera.get('resolucion_video') in ['4K', '6K', '8K']:
            classification['uso_principal'].append('fotografia')
            classification['uso_principal'].append('video_profesional')
        
        flight = drone_data.get('caracteristicas_vuelo', {})
        if flight.get('evita_obstaculos') and flight.get('seguimiento_objeto'):
            classification['nivel_usuario'] = 'avanzado'
        
        # Determinar usos principales
        if peso and peso < 250:
            classification['uso_principal'].append('recreativo')
        
        if camera.get('zoom_optico') and camera.get('zoom_optico') > 2:
            classification['uso_principal'].append('inspeccion')
        
        return classification
    
    def save_raw_data(self, brand: str, data: List[Dict]) -> None:
        """Guardar datos crudos por marca"""
        output_dir = Path(__file__).parent.parent / 'data' / 'raw'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = output_dir / f'{brand.lower()}_products.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Guardados {len(data)} productos de {brand} en {filename}")
    
    def _extract_product_links(self, soup: BeautifulSoup, config: Dict) -> List[str]:
        """Extraer enlaces a productos individuales"""
        links = []
        
        product_selector = config['selectors']['product_list']
        link_selector = config['selectors']['product_link']
        
        products = soup.select(product_selector)
        
        for product in products:
            link_elem = product.select_one(link_selector)
            if link_elem and link_elem.get('href'):
                full_url = urljoin(config['base_url'], link_elem['href'])
                links.append(full_url)
        
        return links
    
    def _handle_infinite_scroll(self):
        """Manejar scroll infinito en páginas dinámicas"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Scroll hasta el final
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Esperar carga de nuevos elementos
            asyncio.run(asyncio.sleep(2))
            
            # Calcular nueva altura
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                break
            
            last_height = new_height
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtener headers éticos para requests"""
        return {
            'User-Agent': 'Academic-Drone-Research-Bot/1.0 (+contact@universidad.edu)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
    
    def _save_extraction_stats(self):
        """Guardar estadísticas de extracción"""
        self.extraction_stats['end_time'] = datetime.now().isoformat()
        
        log_dir = Path(__file__).parent.parent / 'data'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'extraction_log.json'
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(self.extraction_stats, f, ensure_ascii=False, indent=2)


async def main():
    """Función principal"""
    scraper = DroneScraperOrchestrator()
    
    logger.info("Iniciando scraping de drones...")
    results = await scraper.scrape_all_brands()
    
    logger.info(f"Scraping completado. Total de productos: {scraper.extraction_stats['total_products']}")
    
    # Limpiar y validar datos
    cleaner = DataCleaner()
    validator = DataValidator()
    
    all_drones = []
    for brand, products in results.items():
        all_drones.extend(products)
    
    # Normalizar y validar
    cleaned_data = cleaner.normalize_drone_dataset(all_drones)
    valid_data = [d for d in cleaned_data if validator.validate_drone_data(d)[0]]
    
    # Guardar datos procesados
    output_path = Path(__file__).parent.parent / 'data' / 'processed' / 'unified_drones.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(valid_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Datos procesados guardados: {len(valid_data)} drones válidos")


if __name__ == "__main__":
    asyncio.run(main())
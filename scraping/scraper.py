# Drone Scraper Orchestrator
# Coordina la extracción de datos de DJI, Autel y Parrot

import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import aiohttp
from aiohttp import ClientTimeout, TCPConnector
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

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
        
        # Configurar cliente HTTP con reintentos y timeouts
        timeout = ClientTimeout(total=30, connect=10)
        connector = TCPConnector(limit=10, limit_per_host=2, enable_cleanup_closed=True)
        
        async with aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self._get_default_headers()
        ) as self.session:
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
        
        # Generar reporte final
        self._generate_final_report()
        
        return results

    def _generate_final_report(self):
        """Generar reporte final de extracción"""
        end_time = datetime.now()
        start_time = datetime.fromisoformat(self.extraction_stats['start_time'])
        duration = (end_time - start_time).total_seconds()
        
        report = {
            'resumen_extraccion': {
                'fecha_inicio': self.extraction_stats['start_time'],
                'fecha_fin': end_time.isoformat(),
                'duracion_segundos': duration,
                'duracion_minutos': round(duration / 60, 2),
                'total_drones_extraidos': self.extraction_stats['total_products'],
                'total_errores': len(self.extraction_stats['errors']),
                'marcas_procesadas': len(self.extraction_stats['brands_scraped'])
            },
            'detalle_por_marca': self.extraction_stats['brands_scraped'],
            'errores_encontrados': self.extraction_stats['errors'],
            'urls_procesadas': getattr(self, 'urls_processed', []),
            'especificaciones_extraidas': getattr(self, 'specs_extracted', {}),
            'calidad_datos': {
                'drones_con_specs_completas': 0,
                'drones_con_specs_parciales': 0,
                'drones_sin_specs': 0
            }
        }
        
        # Guardar reporte
        report_path = Path(__file__).parent.parent / 'data' / 'extraction_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Reporte de extracción generado: {report_path}")
        logger.info(f"Resumen: {report['resumen_extraccion']['total_drones_extraidos']} drones en {report['resumen_extraccion']['duracion_minutos']} minutos")
        
        # Mostrar estadísticas en consola
        print(f"\n{'='*50}")
        print("REPORTE FINAL DE EXTRACCIÓN")
        print(f"{'='*50}")
        print(f"Duración total: {report['resumen_extraccion']['duracion_minutos']} minutos")
        print(f"Drones extraídos: {report['resumen_extraccion']['total_drones_extraidos']}")
        print(f"Errores encontrados: {report['resumen_extraccion']['total_errores']}")
        print(f"Marcas procesadas: {report['resumen_extraccion']['marcas_procesadas']}")
        print(f"\nDetalle por marca:")
        for marca, cantidad in report['detalle_por_marca'].items():
            print(f"  - {marca.upper()}: {cantidad} drones")
        print(f"{'='*50}\n")
    
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
            logger.info(f"Procesando URL: {url}")
            
            # Intentar primero con scraping estático
            html = await self._fetch_page_robust(url)
            if not html:
                logger.warning(f"No se pudo obtener HTML para {url}")
                return None
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Extraer especificaciones
            drone_data = self.extract_drone_specs(soup, brand, url)
            
            # Verificar si obtuvimos especificaciones útiles
            specs = drone_data.get('especificaciones_tecnicas', {})
            valid_specs = sum(1 for v in specs.values() if v is not None)
            
            # Si no hay suficientes especificaciones, intentar con Selenium
            if valid_specs < 2 and config.get('requires_js', False):
                logger.info(f"Pocas especificaciones ({valid_specs}), intentando con Selenium: {url}")
                
                selenium_data = await self._scrape_with_selenium_single(url, brand, config)
                if selenium_data:
                    selenium_specs = selenium_data.get('especificaciones_tecnicas', {})
                    selenium_valid_specs = sum(1 for v in selenium_specs.values() if v is not None)
                    
                    if selenium_valid_specs > valid_specs:
                        logger.info(f"Selenium obtuvo más especificaciones ({selenium_valid_specs} vs {valid_specs})")
                        return selenium_data
            
            return drone_data
            
        except Exception as e:
            logger.error(f"Error scrapeando {url}: {str(e)}")
            return None

    async def _scrape_with_selenium_single(self, url: str, brand: str, config: Dict) -> Optional[Dict]:
        """Scraping con Selenium para una URL específica"""
        driver = None
        try:
            driver = self.setup_selenium_driver()
            driver.get(url)
            
            # Esperar carga de contenido dinámico
            wait = WebDriverWait(driver, 15)
            try:
                wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, config['selectors']['product_name'])
                ))
            except:
                # Si no encuentra el selector específico, esperar carga general
                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            
            # Extraer datos del producto
            product_soup = BeautifulSoup(driver.page_source, 'lxml')
            return self.extract_drone_specs(product_soup, brand, url)
            
        except Exception as e:
            logger.error(f"Error con Selenium para {url}: {str(e)}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
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
            'caracteristicas_vuelo': {}
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
        
        # 1. Intentar extraer datos estructurados primero
        json_ld_data = self._extract_json_ld_data(soup)
        microdata = self._extract_microdata(soup)
        
        # 2. Extraer nombre del modelo
        model_name = None
        
        # Desde datos estructurados
        if json_ld_data:
            for data in json_ld_data:
                if data.get('@type') == 'Product' and data.get('name'):
                    model_name = data['name']
                    break
        
        # Desde microdata
        if not model_name and microdata.get('name'):
            model_name = microdata['name']
        
        # Desde selectores CSS
        if not model_name:
            try:
                name_elem = soup.select_one(selectors['product_name'])
                if name_elem:
                    model_name = name_elem.get_text(strip=True)
            except:
                pass
        
        # Desde URL como último recurso
        if not model_name:
            model_name = self._extract_model_from_url(url)
        
        # Limpiar nombre del modelo
        if model_name:
            model_name = model_name.replace('DJI ', '').replace('Autel ', '').replace('Parrot ', '')
            model_name = re.sub(r'\s+', ' ', model_name).strip()
            drone_data['modelo'] = model_name
        
        # 3. Extraer especificaciones técnicas
        raw_specs = {}
        
        # Desde JSON-LD
        if json_ld_data:
            for data in json_ld_data:
                if isinstance(data, dict):
                    # Buscar propiedades relevantes
                    for key, value in data.items():
                        if key.lower() in ['weight', 'dimensions', 'specifications']:
                            raw_specs[key] = value
        
        # Desde microdata
        raw_specs.update(microdata)
        
        # Desde tablas/listas HTML
        table_specs = self._extract_specs_from_tables(soup)
        raw_specs.update(table_specs)
        
        # También buscar en texto libre con regex
        page_text = soup.get_text()
        regex_specs = self._extract_specs_with_regex(page_text)
        raw_specs.update(regex_specs)
        
        # Normalizar especificaciones
        normalized_specs = self._normalize_spec_fields(raw_specs)
        
        # Estructura final de especificaciones
        drone_data['especificaciones_tecnicas'] = {
            'peso_gramos': normalized_specs.get('peso_gramos'),
            'autonomia_minutos': normalized_specs.get('autonomia_minutos'),
            'alcance_metros': normalized_specs.get('alcance_metros'),
            'velocidad_max_kmh': normalized_specs.get('velocidad_max_kmh'),
            'resistencia_viento': normalized_specs.get('resistencia_viento'),
            'temperatura_operacion': normalized_specs.get('temperatura_operacion')
        }
        
        # 4. Extraer características de cámara
        drone_data['camara'] = {
            'resolucion_video': normalized_specs.get('resolucion_video'),
            'fps_max': None,
            'sensor_tamaño': normalized_specs.get('sensor_tamaño'),
            'estabilizacion': normalized_specs.get('estabilizacion'),
            'zoom_optico': normalized_specs.get('zoom_optico'),
            'zoom_digital': normalized_specs.get('zoom_digital')
        }
        
        # 5. Extraer características de vuelo
        flight_features = self._extract_flight_features_enhanced(soup)
        drone_data['caracteristicas_vuelo'] = flight_features
        
        # 6. Clasificación automática
        drone_data['clasificacion'] = self._classify_drone(drone_data)
        
        logger.info(f"Extraído drone: {model_name} con {len([v for v in normalized_specs.values() if v])} especificaciones")
        
        return drone_data

    def _extract_specs_with_regex(self, text: str) -> Dict:
        """Extraer especificaciones usando regex en texto libre"""
        specs = {}
        
        # Patrones regex para diferentes especificaciones
        patterns = {
            'peso_gramos': [
                r'weight[:\s]*(\d+\.?\d*)\s*(g|grams?|kg)',
                r'(\d+\.?\d*)\s*(g|grams?|kg)\s*weight',
                r'weighs?\s*(\d+\.?\d*)\s*(g|grams?|kg)'
            ],
            'autonomia_minutos': [
                r'flight\s*time[:\s]*(\d+)\s*(min|minutes?|hrs?|hours?)',
                r'battery\s*life[:\s]*(\d+)\s*(min|minutes?|hrs?|hours?)',
                r'up\s*to\s*(\d+)\s*(min|minutes?|hrs?|hours?)\s*flight'
            ],
            'alcance_metros': [
                r'range[:\s]*(\d+\.?\d*)\s*(m|meters?|km|kilometers?|ft|feet)',
                r'(\d+\.?\d*)\s*(m|meters?|km|kilometers?|ft|feet)\s*range',
                r'transmission\s*range[:\s]*(\d+\.?\d*)\s*(m|meters?|km|kilometers?)'
            ],
            'velocidad_max_kmh': [
                r'max\s*speed[:\s]*(\d+\.?\d*)\s*(km/h|m/s)',
                r'speed[:\s]*(\d+\.?\d*)\s*(km/h|m/s)',
                r'up\s*to\s*(\d+\.?\d*)\s*(km/h|m/s)'
            ]
        }
        
        for spec_name, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value, unit = match.groups()
                    
                    # Convertir unidades si es necesario
                    if spec_name == 'peso_gramos':
                        if unit.lower() in ['kg']:
                            specs[spec_name] = float(value) * 1000
                        else:
                            specs[spec_name] = float(value)
                    elif spec_name == 'autonomia_minutos':
                        if unit.lower() in ['hrs', 'hours', 'hour']:
                            specs[spec_name] = float(value) * 60
                        else:
                            specs[spec_name] = float(value)
                    elif spec_name == 'alcance_metros':
                        if unit.lower() in ['km', 'kilometers']:
                            specs[spec_name] = float(value) * 1000
                        elif unit.lower() in ['ft', 'feet']:
                            specs[spec_name] = float(value) * 0.3048
                        else:
                            specs[spec_name] = float(value)
                    elif spec_name == 'velocidad_max_kmh':
                        if unit.lower() in ['mph']:
                            specs[spec_name] = float(value) * 1.60934
                        elif unit.lower() in ['m/s']:
                            specs[spec_name] = float(value) * 3.6
                        else:
                            specs[spec_name] = float(value)
                    
                    break  # Tomar la primera coincidencia
        
        return specs

    def _extract_flight_features_enhanced(self, soup: BeautifulSoup) -> Dict:
        """Extraer características de vuelo mejoradas"""
        features = {
            'evita_obstaculos': False,
            'retorno_automatico': False,
            'seguimiento_objeto': False,
            'vuelo_nocturno': False,
            'modo_sport': False,
            'precision_hover': None
        }
        
        # Buscar en texto de la página
        page_text = soup.get_text().lower()
        
        # Patrones de detección
        feature_patterns = {
            'evita_obstaculos': [
                'obstacle avoidance', 'obstacle detection', 'collision avoidance',
                'evita obstáculos', 'detección de obstáculos', 'sensors'
            ],
            'retorno_automatico': [
                'return to home', 'rth', 'auto return', 'fail safe',
                'retorno automático', 'vuelta a casa'
            ],
            'seguimiento_objeto': [
                'follow me', 'object tracking', 'subject tracking', 'activetrack',
                'seguimiento', 'rastreo', 'tracking'
            ],
            'vuelo_nocturno': [
                'night flight', 'low light', 'night vision', 'led lights',
                'vuelo nocturno', 'luces led'
            ],
            'modo_sport': [
                'sport mode', 'high speed', 'racing mode', 'acro mode',
                'modo deporte', 'alta velocidad'
            ]
        }
        
        for feature_name, patterns in feature_patterns.items():
            for pattern in patterns:
                if pattern in page_text:
                    features[feature_name] = True
                    break
        
        # Detectar sistema de posicionamiento
        if any(term in page_text for term in ['gps', 'gnss', 'glonass', 'galileo']):
            features['precision_hover'] = 'GPS'
        elif any(term in page_text for term in ['vision', 'visual', 'optical']):
            features['precision_hover'] = 'Visual'
        
        return features
    
    def _extract_specs_from_tables(self, soup: BeautifulSoup) -> Dict:
        """Extracción genérica de especificaciones desde tablas"""
        specs = {}
        
        # Selectores genéricos para tablas de especificaciones
        table_selectors = [
            'table.specs', 'table.specifications', 'table.tech-specs',
            '.spec-table', '.specification-table', '.product-specs',
            'table[class*="spec"]', 'table[class*="tech"]',
            '.specs-content table', '.technical-specs table'
        ]
        
        spec_table = None
        for selector in table_selectors:
            spec_table = soup.select_one(selector)
            if spec_table:
                break
        
        if spec_table:
            rows = spec_table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)
                    
                    if key and value:
                        specs[key] = value
        
        # También buscar en listas de especificaciones
        list_selectors = [
            '.specs-list', '.specification-list', '.product-features',
            'ul.specs', 'dl.specs', '.tech-specs ul',
            '[class*="spec"] ul', '[class*="spec"] dl'
        ]
        
        for selector in list_selectors:
            spec_list = soup.select_one(selector)
            if spec_list:
                # Para listas de definición (dl/dt/dd)
                if spec_list.name == 'dl':
                    terms = spec_list.find_all('dt')
                    definitions = spec_list.find_all('dd')
                    for term, definition in zip(terms, definitions):
                        key = term.get_text(strip=True).lower()
                        value = definition.get_text(strip=True)
                        if key and value:
                            specs[key] = value
                
                # Para listas regulares con patrones clave:valor
                else:
                    items = spec_list.find_all('li')
                    for item in items:
                        text = item.get_text(strip=True)
                        if ':' in text:
                            parts = text.split(':', 1)
                            if len(parts) == 2:
                                key = parts[0].strip().lower()
                                value = parts[1].strip()
                                if key and value:
                                    specs[key] = value
        
        return specs

    def _normalize_spec_fields(self, raw_specs: Dict) -> Dict:
        """Normalizar nombres de campos de especificaciones"""
        field_mapping = {
            # Peso
            'weight': 'peso_gramos',
            'takeoff weight': 'peso_gramos',
            'max takeoff weight': 'peso_gramos',
            'mtow': 'peso_gramos',
            'peso': 'peso_gramos',
            'mass': 'peso_gramos',
            
            # Autonomía
            'flight time': 'autonomia_minutos',
            'max flight time': 'autonomia_minutos',
            'battery life': 'autonomia_minutos',
            'endurance': 'autonomia_minutos',
            'tiempo de vuelo': 'autonomia_minutos',
            'autonomía': 'autonomia_minutos',
            
            # Alcance
            'range': 'alcance_metros',
            'max range': 'alcance_metros',
            'transmission range': 'alcance_metros',
            'control range': 'alcance_metros',
            'operating range': 'alcance_metros',
            'alcance': 'alcance_metros',
            'rango': 'alcance_metros',
            
            # Velocidad
            'max speed': 'velocidad_max_kmh',
            'top speed': 'velocidad_max_kmh',
            'maximum speed': 'velocidad_max_kmh',
            'speed': 'velocidad_max_kmh',
            'velocidad máxima': 'velocidad_max_kmh',
            'velocidad': 'velocidad_max_kmh',
            
            # Resistencia al viento
            'wind resistance': 'resistencia_viento',
            'max wind speed': 'resistencia_viento',
            'wind speed': 'resistencia_viento',
            'resistencia al viento': 'resistencia_viento',
            
            # Temperatura
            'operating temperature': 'temperatura_operacion',
            'temp range': 'temperatura_operacion',
            'temperature range': 'temperatura_operacion',
            'temperatura de operación': 'temperatura_operacion',
            
            # Cámara
            'video resolution': 'resolucion_video',
            'max video resolution': 'resolucion_video',
            'recording resolution': 'resolucion_video',
            'resolución de video': 'resolucion_video',
            
            'photo resolution': 'resolucion_foto',
            'max photo resolution': 'resolucion_foto',
            'still resolution': 'resolucion_foto',
            'resolución de foto': 'resolucion_foto',
            
            'sensor size': 'sensor_tamaño',
            'image sensor': 'sensor_tamaño',
            'tamaño del sensor': 'sensor_tamaño',
            
            'gimbal': 'estabilizacion',
            'stabilization': 'estabilizacion',
            'estabilización': 'estabilizacion',
            
            'zoom': 'zoom_optico',
            'optical zoom': 'zoom_optico',
            'zoom óptico': 'zoom_optico',
            
            'digital zoom': 'zoom_digital',
            'zoom digital': 'zoom_digital'
        }
        
        normalized = {}
        
        for raw_key, value in raw_specs.items():
            # Normalizar la clave
            normalized_key = None
            for mapping_key, standard_key in field_mapping.items():
                if mapping_key in raw_key.lower():
                    normalized_key = standard_key
                    break
            
            if normalized_key:
                # Procesar el valor según el tipo de campo
                if 'gramos' in normalized_key:
                    normalized[normalized_key] = self.data_cleaner.extract_number(str(value), 'grams')
                elif 'minutos' in normalized_key:
                    normalized[normalized_key] = self.data_cleaner.extract_number(str(value), 'minutes')
                elif 'metros' in normalized_key:
                    normalized[normalized_key] = self.data_cleaner.extract_number(str(value), 'meters')
                elif 'kmh' in normalized_key:
                    normalized[normalized_key] = self.data_cleaner.extract_number(str(value), 'kmh')
                else:
                    normalized[normalized_key] = str(value).strip()
        
        return normalized
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
            page_text = soup.get_text()
            
            # Usar patrones regex para extraer specs del texto general
            import re
            
            # Peso - patrones más amplios
            weight_patterns = [
                r'weight[:\s]*(\d+\.?\d*)\s*(g|grams?|kg)',
                r'(\d+\.?\d*)\s*(g|grams?|kg)\s*weight',
                r'weighs?\s*(\d+\.?\d*)\s*(g|grams?|kg)',
                r'takeoff weight[:\s]*(\d+\.?\d*)\s*(g|grams?|kg)',
                r'(\d+\.?\d*)\s*g\b',  # Simplemente números seguidos de 'g'
                r'(\d+\.?\d*)\s*kg\b'  # Simplemente números seguidos de 'kg'
            ]
            
            for pattern in weight_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    try:
                        if len(match.groups()) == 2:
                            value, unit = match.groups()
                        else:
                            value = match.group(1)
                            unit = 'g' if 'g' in match.group(0).lower() and 'kg' not in match.group(0).lower() else 'kg'
                        
                        value = float(value)
                        if unit.lower() in ['kg']:
                            specs['peso_gramos'] = value * 1000
                        else:
                            specs['peso_gramos'] = value
                        break
                    except (ValueError, IndexError):
                        continue
            
            # Tiempo de vuelo - patrones más amplios
            flight_patterns = [
                r'flight time[:\s]*(\d+)\s*(?:min|minutes?)',
                r'(\d+)\s*(?:min|minutes?)\s*flight\s*time',
                r'up to\s*(\d+)\s*(?:min|minutes?)\s*(?:of\s*)?flight',
                r'battery life[:\s]*(\d+)\s*(?:min|minutes?)',
                r'(\d+)\s*min\b',  # Simplemente números seguidos de 'min'
                r'autonomy[:\s]*(\d+)\s*(?:min|minutes?)'
            ]
            
            for pattern in flight_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    try:
                        specs['autonomia_minutos'] = int(match.group(1))
                        break
                    except (ValueError, IndexError):
                        continue
            
            # Alcance - patrones más amplios
            range_patterns = [
                r'range[:\s]*(\d+\.?\d*)\s*(km|m|meters?|kilometres?)',
                r'transmission range[:\s]*(\d+\.?\d*)\s*(km|m)',
                r'control range[:\s]*(\d+\.?\d*)\s*(km|m)',
                r'up to\s*(\d+\.?\d*)\s*(km|m)\s*range',
                r'(\d+\.?\d*)\s*km\b',  # Simplemente números seguidos de 'km'
                r'(\d+\.?\d*)\s*m\b(?!\w)'   # Números seguidos de 'm' (no seguido de otras letras)
            ]
            
            for pattern in range_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    try:
                        if len(match.groups()) == 2:
                            value, unit = match.groups()
                        else:
                            value = match.group(1)
                            # Determinar unidad por contexto
                            context = page_text[max(0, match.start()-50):match.end()+50].lower()
                            unit = 'km' if 'km' in context else 'm'
                        
                        value = float(value)
                        if unit.lower() in ['km', 'kilometres', 'kilometers']:
                            specs['alcance_metros'] = value * 1000
                        else:
                            # Solo aceptar valores de metros que sean razonables (más de 30m)
                            if value > 30:
                                specs['alcance_metros'] = value
                        break
                    except (ValueError, IndexError):
                        continue
            
            # Velocidad
            speed_patterns = [
                r'max speed[:\s]*(\d+\.?\d*)\s*(km/h|kmh|mph)',
                r'top speed[:\s]*(\d+\.?\d*)\s*(km/h|kmh|mph)',
                r'(\d+\.?\d*)\s*(km/h|kmh|mph)\s*max',
                r'(\d+\.?\d*)\s*km/h\b',
                r'(\d+\.?\d*)\s*mph\b'
            ]
            
            for pattern in speed_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    try:
                        if len(match.groups()) == 2:
                            value, unit = match.groups()
                        else:
                            value = match.group(1)
                            unit = 'km/h' if 'km' in match.group(0) else 'mph'
                        
                        value = float(value)
                        if 'mph' in unit.lower():
                            specs['velocidad_max_kmh'] = value * 1.60934
                        else:
                            specs['velocidad_max_kmh'] = value
                        break
                    except (ValueError, IndexError):
                        continue
        
        return specs
    
    def _extract_camera_specs(self, soup: BeautifulSoup, selectors: Dict) -> Dict:
        """Extraer especificaciones de cámara"""
        import re
        
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
        page_text = soup.get_text()
        
        # Buscar resolución de video en toda la página
        video_patterns = [
            r'4K\b',
            r'6K\b', 
            r'8K\b',
            r'1080p\b',
            r'720p\b',
            r'Ultra HD',
            r'Full HD'
        ]
        
        for pattern in video_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                resolution = match.group(0).upper()
                if resolution in ['4K', '6K', '8K', '1080P', '720P']:
                    camera['resolucion_video'] = resolution
                elif 'ULTRA HD' in resolution:
                    camera['resolucion_video'] = '4K'
                elif 'FULL HD' in resolution:
                    camera['resolucion_video'] = '1080p'
                break
        
        # Buscar FPS
        fps_patterns = [
            r'(\d+)\s*fps',
            r'(\d+)\s*frames per second',
            r'at\s*(\d+)\s*fps'
        ]
        
        for pattern in fps_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                try:
                    fps = int(match.group(1))
                    if fps <= 120:  # Valores razonables
                        camera['fps_max'] = fps
                        break
                except ValueError:
                    continue
        
        # Buscar estabilización
        stabilization_patterns = [
            r'gimbal',
            r'stabilization',
            r'stabilized',
            r'mechanical\s*gimbal',
            r'3-axis\s*gimbal'
        ]
        
        for pattern in stabilization_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                if 'mechanical' in match.group(0).lower() or 'gimbal' in match.group(0).lower():
                    camera['estabilizacion'] = 'mecanica'
                else:
                    camera['estabilizacion'] = 'digital'
                break
        
        return camera
    
    def _extract_flight_features(self, soup: BeautifulSoup, selectors: Dict) -> Dict:
        """Extraer características de vuelo"""
        import re
        
        features = {
            'evita_obstaculos': False,
            'retorno_automatico': False,
            'seguimiento_objeto': False,
            'vuelo_nocturno': False,
            'modo_sport': False,
            'precision_hover': None
        }
        
        # Buscar en toda la página
        page_text = soup.get_text()
        
        # Patrones para detección de características
        obstacle_patterns = [
            r'obstacle\s+(?:avoidance|detection)',
            r'collision\s+avoidance',
            r'anti-collision',
            r'evita\s+obstáculos',
            r'detección\s+de\s+obstáculos'
        ]
        
        for pattern in obstacle_patterns:
            if re.search(pattern, page_text, re.IGNORECASE):
                features['evita_obstaculos'] = True
                break
        
        # Return to home
        rth_patterns = [
            r'return\s+(?:to\s+)?home',
            r'RTH',
            r'retorno\s+(?:a\s+)?casa',
            r'retorno\s+automático',
            r'auto\s+return'
        ]
        
        for pattern in rth_patterns:
            if re.search(pattern, page_text, re.IGNORECASE):
                features['retorno_automatico'] = True
                break
        
        # Seguimiento de objetos
        tracking_patterns = [
            r'(?:object|subject)\s+tracking',
            r'follow\s+me',
            r'activetrack',
            r'seguimiento\s+(?:de\s+)?objetos?',
            r'rastreo\s+(?:de\s+)?objetos?'
        ]
        
        for pattern in tracking_patterns:
            if re.search(pattern, page_text, re.IGNORECASE):
                features['seguimiento_objeto'] = True
                break
        
        # Vuelo nocturno
        night_patterns = [
            r'night\s+(?:flight|mode)',
            r'low\s+light',
            r'vuelo\s+nocturno',
            r'modo\s+nocturno'
        ]
        
        for pattern in night_patterns:
            if re.search(pattern, page_text, re.IGNORECASE):
                features['vuelo_nocturno'] = True
                break
        
        # Modo sport
        sport_patterns = [
            r'sport\s+mode',
            r'high\s+speed\s+mode',
            r'modo\s+deportivo',
            r'modo\s+sport'
        ]
        
        for pattern in sport_patterns:
            if re.search(pattern, page_text, re.IGNORECASE):
                features['modo_sport'] = True
                break
        
        # Precisión de hover
        hover_patterns = [
            r'GPS',
            r'GLONASS',
            r'precision\s+hover',
            r'hover\s+accuracy',
            r'posicionamiento\s+GPS'
        ]
        
        for pattern in hover_patterns:
            if re.search(pattern, page_text, re.IGNORECASE):
                features['precision_hover'] = 'GPS'
                break
        
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
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Headers por defecto para requests HTTP"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
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
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def _fetch_page_robust(self, url: str, headers: Optional[Dict] = None) -> Optional[str]:
        """Fetch robusto de página con manejo de errores y reintentos"""
        try:
            request_headers = {**self._get_default_headers(), **(headers or {})}
            
            async with self.session.get(url, headers=request_headers) as response:
                # Manejo de códigos de estado
                if response.status == 404:
                    logger.warning(f"Página no encontrada: {url}")
                    return None
                elif response.status == 403:
                    logger.warning(f"Acceso denegado: {url}")
                    return None
                elif response.status >= 400:
                    logger.error(f"Error HTTP {response.status} para {url}")
                    response.raise_for_status()
                
                # Verificar tipo de contenido
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type and 'application/json' not in content_type:
                    logger.warning(f"Tipo de contenido inesperado para {url}: {content_type}")
                
                return await response.text()
                
        except aiohttp.ClientError as e:
            logger.error(f"Error de cliente HTTP para {url}: {str(e)}")
            raise
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout para {url}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado para {url}: {str(e)}")
            return None

    def _extract_json_ld_data(self, soup: BeautifulSoup) -> List[Dict]:
        """Extraer datos estructurados JSON-LD"""
        json_ld_data = []
        
        # Buscar scripts con JSON-LD
        json_scripts = soup.find_all('script', type='application/ld+json')
        
        for script in json_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    json_ld_data.extend(data)
                else:
                    json_ld_data.append(data)
            except (json.JSONDecodeError, AttributeError) as e:
                logger.debug(f"Error parseando JSON-LD: {str(e)}")
                continue
        
        return json_ld_data

    def _extract_microdata(self, soup: BeautifulSoup) -> Dict:
        """Extraer microdata de la página"""
        microdata = {}
        
        # Buscar elementos con itemtype="Product"
        products = soup.find_all(attrs={'itemtype': lambda x: x and 'Product' in x})
        
        for product in products:
            # Extraer propiedades del producto
            props = {}
            
            # Nombre del producto
            name_elem = product.find(attrs={'itemprop': 'name'})
            if name_elem:
                props['name'] = name_elem.get_text(strip=True)
            
            # Descripción
            desc_elem = product.find(attrs={'itemprop': 'description'})
            if desc_elem:
                props['description'] = desc_elem.get_text(strip=True)
            
            # Especificaciones adicionales
            for prop in ['weight', 'dimensions', 'model', 'brand']:
                elem = product.find(attrs={'itemprop': prop})
                if elem:
                    props[prop] = elem.get_text(strip=True)
            
            if props:
                microdata.update(props)
        
        return microdata

    def _save_extraction_stats(self):
        """Guardar estadísticas de extracción"""
        try:
            self.extraction_stats['end_time'] = datetime.now().isoformat()
            self.extraction_stats['duration_seconds'] = (
                datetime.fromisoformat(self.extraction_stats['end_time']) - 
                datetime.fromisoformat(self.extraction_stats['start_time'])
            ).total_seconds()
            
            stats_file = Path(__file__).parent.parent / 'data' / 'extraction_log.json'
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.extraction_stats, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Estadísticas guardadas en {stats_file}")
            
        except Exception as e:
            logger.error(f"Error guardando estadísticas: {str(e)}")

    # ...existing code...
    

async def main():
    """Función principal con validación y reporte completo"""
    scraper = DroneScraperOrchestrator()
    
    try:
        logger.info("Iniciando scraping de drones...")
        start_time = datetime.now()
        
        # Realizar scraping
        results = await scraper.scrape_all_brands()
        
        logger.info(f"Scraping completado. Total de productos: {scraper.extraction_stats['total_products']}")
        
        # Limpiar y validar datos
        cleaner = DataCleaner()
        validator = DataValidator()
        
        all_drones = []
        for brand, products in results.items():
            all_drones.extend(products)
        
        if not all_drones:
            logger.error("No se obtuvieron datos de ninguna marca")
            return
        
        # Normalizar datos
        logger.info("Normalizando datos...")
        cleaned_data = cleaner.normalize_drone_dataset(all_drones)
        
        # Validar datos con esquema JSON
        valid_data = []
        validation_errors = []
        
        for drone in cleaned_data:
            is_valid, errors = validator.validate_drone_data(drone)
            if is_valid:
                valid_data.append(drone)
            else:
                validation_errors.append({
                    'drone': drone.get('modelo', 'Unknown'),
                    'errors': errors
                })
        
        # Crear directorio de salida
        output_dir = Path(__file__).parent.parent / 'data' / 'processed'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Guardar datos válidos
        unified_path = output_dir / 'unified_drones.json'
        with open(unified_path, 'w', encoding='utf-8') as f:
            json.dump(valid_data, f, ensure_ascii=False, indent=2)
        
        # Guardar reporte de validación
        validation_report = {
            'timestamp': datetime.now().isoformat(),
            'total_drones_input': len(all_drones),
            'total_drones_cleaned': len(cleaned_data),
            'total_drones_valid': len(valid_data),
            'validation_errors': validation_errors,
            'success_rate': (len(valid_data) / len(all_drones) * 100) if all_drones else 0
        }
        
        validation_path = output_dir / 'validation_report.json'
        with open(validation_path, 'w', encoding='utf-8') as f:
            json.dump(validation_report, f, ensure_ascii=False, indent=2)
        
        # Análisis básico de calidad
        if valid_data:
            quality_stats = analyze_data_quality(valid_data)
            
            quality_path = output_dir / 'quality_analysis.json'
            with open(quality_path, 'w', encoding='utf-8') as f:
                json.dump(quality_stats, f, ensure_ascii=False, indent=2)
        
        # Crear metadatos del dataset
        metadata = {
            'dataset_info': {
                'version': '1.0.0',
                'created_at': datetime.now().isoformat(),
                'total_drones': len(valid_data),
                'brands_included': list(set(d['marca'] for d in valid_data)),
                'data_sources': list(results.keys()),
                'extraction_duration_minutes': (datetime.now() - start_time).total_seconds() / 60,
                'schema_version': '1.0.0'
            },
            'field_completeness': {},
            'data_quality_score': validation_report['success_rate']
        }
        
        # Calcular completitud de campos
        if valid_data:
            total_drones = len(valid_data)
            for field_path in ['especificaciones_tecnicas.peso_gramos', 'especificaciones_tecnicas.autonomia_minutos', 
                              'especificaciones_tecnicas.alcance_metros', 'camara.resolucion_video']:
                count = 0
                for drone in valid_data:
                    if '.' in field_path:
                        parts = field_path.split('.')
                        value = drone.get(parts[0], {}).get(parts[1])
                    else:
                        value = drone.get(field_path)
                    
                    if value is not None:
                        count += 1
                
                metadata['field_completeness'][field_path] = {
                    'count': count,
                    'percentage': (count / total_drones * 100) if total_drones > 0 else 0
                }
        
        metadata_path = output_dir / 'metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # Log de resultados finales
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 60
        
        logger.info(f"Proceso completado en {duration:.2f} minutos")
        logger.info(f"Datos procesados guardados: {len(valid_data)} drones válidos de {len(all_drones)} extraídos")
        logger.info(f"Tasa de éxito: {validation_report['success_rate']:.1f}%")
        
        if validation_errors:
            logger.warning(f"Se encontraron {len(validation_errors)} errores de validación")
        
        # Mostrar resumen por marca
        if valid_data:
            brand_summary = {}
            for drone in valid_data:
                brand = drone.get('marca', 'Unknown')
                brand_summary[brand] = brand_summary.get(brand, 0) + 1
            
            print(f"\n{'='*50}")
            print("RESUMEN FINAL POR MARCA")
            print(f"{'='*50}")
            for brand, count in brand_summary.items():
                print(f"{brand}: {count} drones válidos")
            print(f"{'='*50}\n")
        
    except Exception as e:
        logger.error(f"Error en proceso principal: {str(e)}")
        raise


def analyze_data_quality(drones: List[Dict]) -> Dict:
    """Analizar calidad de los datos extraídos"""
    if not drones:
        return {}
    
    quality_stats = {
        'total_drones': len(drones),
        'completeness_by_field': {},
        'brands_distribution': {},
        'spec_ranges': {},
        'common_issues': []
    }
    
    # Distribución por marca
    for drone in drones:
        brand = drone.get('marca', 'Unknown')
        quality_stats['brands_distribution'][brand] = quality_stats['brands_distribution'].get(brand, 0) + 1
    
    # Completitud por campo
    fields_to_check = [
        'modelo', 'especificaciones_tecnicas.peso_gramos', 'especificaciones_tecnicas.autonomia_minutos',
        'especificaciones_tecnicas.alcance_metros', 'especificaciones_tecnicas.velocidad_max_kmh',
        'camara.resolucion_video', 'camara.estabilizacion'
    ]
    
    for field in fields_to_check:
        complete_count = 0
        values = []
        
        for drone in drones:
            if '.' in field:
                parts = field.split('.')
                value = drone.get(parts[0], {}).get(parts[1])
            else:
                value = drone.get(field)
            
            if value is not None and value != '':
                complete_count += 1
                if isinstance(value, (int, float)):
                    values.append(float(value))
        
        quality_stats['completeness_by_field'][field] = {
            'count': complete_count,
            'percentage': (complete_count / len(drones)) * 100,
            'total': len(drones)
        }
        
        # Rangos para campos numéricos
        if values and len(values) > 1:
            quality_stats['spec_ranges'][field] = {
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values),
                'count': len(values)
            }
    
    return quality_stats


if __name__ == "__main__":
    asyncio.run(main())
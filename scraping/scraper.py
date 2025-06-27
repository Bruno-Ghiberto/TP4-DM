# Drone Scraper Orchestrator
# Coordina la extracción de datos de DJI, Autel y Parrot

import asyncio
import io
import json
import logging
import random
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

try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

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
        timeout = ClientTimeout(total=60, connect=15, sock_read=30)  # PDFs de Parrot son grandes
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
            if config.get('direct_product_urls', False):
                for product_url in config['product_urls']:
                    self.driver.get(product_url)
                    
                    # Esperar elementos específicos según la marca
                    wait = WebDriverWait(self.driver, 20)
                    
                    # Esperar múltiples posibles elementos
                    wait_for_elements = config.get('wait_for_elements', [])
                    element_found = False
                    
                    for selector in wait_for_elements:
                        try:
                            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                            element_found = True
                            break
                        except:
                            continue
                    
                    if not element_found:
                        # Esperar tiempo fijo como fallback
                        await asyncio.sleep(5)
                    
                    # Scroll para cargar todo el contenido
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    await asyncio.sleep(2)
                    
                    # Extraer datos
                    product_soup = BeautifulSoup(self.driver.page_source, 'lxml')
                    product_data = self.extract_drone_specs(product_soup, brand, product_url)
                    
                    if product_data:
                        products.append(product_data)
                    
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
                # Esperar múltiples condiciones para sitios SPA
                WebDriverWait(driver, 20).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                # Esperar que el contenido dinámico se cargue
                WebDriverWait(driver, 10).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Specifications') or contains(text(), 'specs')]")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, config['selectors']['product_name']))
                    )
                )
                # Scroll para activar lazy loading
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                import time
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Timeout esperando carga completa de {url}: {str(e)}")
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
        specs_data = {
            'especificaciones_tecnicas': {},
            'camara': {},
            'caracteristicas_vuelo': {}
        }
        
        # Patrones mejorados para PDFs de Parrot
        spec_patterns = {
            'peso_gramos': [
                r'Weight[:\s]*(\d+\.?\d*)\s*(g|kg|grams?)',
                r'Total weight[:\s]*(\d+\.?\d*)\s*(g|kg)',
                r'(\d+\.?\d*)\s*(g|kg)\s*\(.*weight.*\)'
            ],
            'autonomia_minutos': [
                r'Flight time[:\s]*(\d+)\s*min',
                r'Max\.?\s*flight time[:\s]*(\d+)\s*min',
                r'Autonomy[:\s]*(\d+)\s*min'
            ],
            'alcance_metros': [
                r'Range[:\s]*(\d+\.?\d*)\s*(km|m)',
                r'Control range[:\s]*(\d+\.?\d*)\s*(km|m)',
                r'Transmission range[:\s]*(\d+\.?\d*)\s*(km|m)'
            ],
            'velocidad_max_kmh': [
                r'Max\.?\s*speed[:\s]*(\d+\.?\d*)\s*(km/h|m/s)',
                r'Maximum horizontal speed[:\s]*(\d+\.?\d*)\s*(km/h|m/s)'
            ]
        }
        
        # Aplicar todos los patrones
        for spec_name, patterns in spec_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = float(match.group(1))
                    unit = match.group(2).lower() if len(match.groups()) > 1 else ''
                    
                    # Convertir unidades
                    if spec_name == 'peso_gramos' and unit in ['kg', 'kilograms']:
                        value = value * 1000
                    elif spec_name == 'alcance_metros' and unit in ['km', 'kilometers']:
                        value = value * 1000
                    elif spec_name == 'velocidad_max_kmh' and unit in ['m/s']:
                        value = value * 3.6
                    
                    specs_data['especificaciones_tecnicas'][spec_name] = value
                    break
        
        # Buscar resolución de cámara
        camera_patterns = [
            r'Video resolution[:\s]*([48]K|4K|1080p)',
            r'Video[:\s]*([48]K|4K|1080p)',
            r'Recording[:\s]*([48]K|4K|1080p)'
        ]
        
        for pattern in camera_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                specs_data['camara']['resolucion_video'] = match.group(1).upper()
                break
        
        # Características de vuelo
        if re.search(r'obstacle\s+avoidance|obstacle\s+detection', text, re.IGNORECASE):
            specs_data['caracteristicas_vuelo']['evita_obstaculos'] = True
        
        if re.search(r'return\s+to\s+home|RTH', text, re.IGNORECASE):
            specs_data['caracteristicas_vuelo']['retorno_automatico'] = True
        
        # Clasificación basada en los datos extraídos
        specs_data['clasificacion'] = self._classify_drone(specs_data)
        
        return specs_data
    
    def extract_drone_specs(self, soup: BeautifulSoup, brand: str, url: str) -> Dict:
        """Parser inteligente para especificaciones de drones"""
        
        # Llamar al método específico según la marca
        if brand.lower() == 'dji':
            return self._extract_dji_specs(soup, url)
        elif brand.lower() == 'autel':
            return self._extract_autel_specs(soup, url)
        elif brand.lower() == 'parrot':
            # Para Parrot, el contenido ya viene procesado del PDF
            return self._extract_parrot_specs(soup, url)
        
        # Fallback al método genérico
        return self._extract_generic_specs(soup, brand, url)

    def _extract_dji_specs(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extractor específico para DJI"""
        drone_data = {
            'marca': 'DJI',
            'url_fuente': url,
            'metadata': {
                'fecha_extraccion': datetime.now().isoformat(),
                'version_scraper': '1.0.0',
                'confiabilidad_datos': 'alta'
            }
        }
        
                # Extraer nombre del modelo
        # DJI usa React con clases dinámicas, buscar por estructura
        model_elem = soup.find('h1') or soup.find('div', {'data-testid': 'product-title'})
        if not model_elem:
            # Buscar en meta tags como fallback
            meta_title = soup.find('meta', {'property': 'og:title'})
            if meta_title:
                model_text = meta_title.get('content', '')
                drone_data['modelo'] = model_text.replace('DJI ', '')
        
        # Buscar JSON-LD estructurado primero
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'Product':
                    # Extraer datos del JSON-LD
                    if 'name' in data:
                        drone_data['modelo'] = data['name'].replace('DJI ', '')
                    if 'offers' in data and 'price' in data['offers']:
                        drone_data['precio'] = {
                            'usd': float(data['offers']['price']),
                            'moneda_local': data['offers'].get('priceCurrency', 'USD')
                        }
            except:
                pass
        
        # Buscar sección de especificaciones
        specs_section = soup.select_one('div[class*="specs"], section[class*="specification"]')
        
        # Extraer especificaciones técnicas
        specs = {}
        
        # Método 1: Buscar por texto específico en toda la página
        all_text_elements = soup.find_all(string=True)
        for i, text in enumerate(all_text_elements):
            if 'Weight' in str(text) or 'Peso' in str(text):
                # El siguiente elemento suele tener el valor
                if i + 1 < len(all_text_elements):
                    weight_text = all_text_elements[i + 1]
                    match = re.search(r'(\d+\.?\d*)\s*(g|kg)', str(weight_text))
                    if match:
                        value, unit = match.groups()
                        specs['peso_gramos'] = float(value) * (1000 if unit == 'kg' else 1)
        
        # Método 2: Buscar en listas de especificaciones tradicionales
        spec_items = soup.select('div[class*="spec-item"], li[class*="spec"]')
        for item in spec_items:
            text = item.get_text(strip=True)
            
            # Peso
            if any(word in text.lower() for word in ['weight', 'peso']):
                match = re.search(r'(\d+\.?\d*)\s*(g|kg)', text)
                if match:
                    value, unit = match.groups()
                    specs['peso_gramos'] = float(value) * (1000 if unit == 'kg' else 1)
            
            # Tiempo de vuelo
            elif any(word in text.lower() for word in ['flight time', 'autonomía']):
                match = re.search(r'(\d+)\s*min', text)
                if match:
                    specs['autonomia_minutos'] = int(match.group(1))
            
            # Alcance
            elif any(word in text.lower() for word in ['transmission', 'range', 'alcance']):
                match = re.search(r'(\d+\.?\d*)\s*(km|m)', text)
                if match:
                    value, unit = match.groups()
                    specs['alcance_metros'] = float(value) * (1000 if unit == 'km' else 1)
        
        # Método 2: Buscar en el texto con patrones más específicos
        page_text = soup.get_text()
        
        # Peso - patrones específicos de DJI
        if 'peso_gramos' not in specs:
            patterns = [
                r'Takeoff Weight[:\s]*<?(\d+\.?\d*)\s*(g|kg)',
                r'Aircraft Weight[:\s]*(\d+\.?\d*)\s*(g|kg)',
                r'Weight \(.*?\)[:\s]*(\d+\.?\d*)\s*(g|kg)'
            ]
            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    value, unit = match.groups()
                    specs['peso_gramos'] = float(value) * (1000 if unit.lower() == 'kg' else 1)
                    break
        
        drone_data['especificaciones_tecnicas'] = self.data_cleaner.standardize_specifications(specs)
        
        # Extraer características de cámara
        drone_data['camara'] = self._extract_camera_specs_dji(soup, page_text)
        
        # Extraer características de vuelo
        drone_data['caracteristicas_vuelo'] = self._extract_flight_features_dji(soup, page_text)
        
        # Clasificación
        drone_data['clasificacion'] = self._classify_drone(drone_data)
        
        return drone_data

    def _extract_camera_specs_dji(self, soup: BeautifulSoup, page_text: str) -> Dict:
        """Extraer especificaciones de cámara específicas de DJI"""
        camera = {
            'resolucion_video': None,
            'fps_max': None,
            'sensor_tamaño': None,
            'estabilizacion': None,
            'zoom_optico': None,
            'zoom_digital': None
        }
        
        # Buscar resolución de video
        video_patterns = [
            r'4K/60fps',
            r'4K/30fps',
            r'5\.1K/50fps',
            r'Video Resolution[:\s]*([48]K|1080p)',
            r'Max Video Resolution[:\s]*([48]K|1080p)'
        ]
        
        for pattern in video_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                if '4K' in match.group(0):
                    camera['resolucion_video'] = '4K'
                elif '5.1K' in match.group(0):
                    camera['resolucion_video'] = '5.1K'
                elif '8K' in match.group(0):
                    camera['resolucion_video'] = '8K'
                
                # Extraer FPS si está presente
                fps_match = re.search(r'/(\d+)fps', match.group(0))
                if fps_match:
                    camera['fps_max'] = int(fps_match.group(1))
                break
        
        # Buscar gimbal/estabilización
        if any(word in page_text.lower() for word in ['3-axis gimbal', '3-axis mechanical gimbal']):
            camera['estabilizacion'] = 'mecanica'
        
        return camera

    def _extract_flight_features_dji(self, soup: BeautifulSoup, page_text: str) -> Dict:
        """Extraer características de vuelo específicas de DJI"""
        features = {
            'evita_obstaculos': False,
            'retorno_automatico': False,
            'seguimiento_objeto': False,
            'vuelo_nocturno': False,
            'modo_sport': False,
            'precision_hover': None
        }
        
        # DJI usa términos específicos
        feature_terms = {
            'evita_obstaculos': ['obstacle sensing', 'obstacle avoidance', 'apas', 'omnidirectional obstacle'],
            'retorno_automatico': ['return to home', 'rth', 'smart rth', 'failsafe rth'],
            'seguimiento_objeto': ['activetrack', 'spotlight', 'poi', 'follow me', 'focustrack'],
            'modo_sport': ['sport mode', 's mode', 'manual mode']
        }
        
        text_lower = page_text.lower()
        for feature, terms in feature_terms.items():
            if any(term in text_lower for term in terms):
                features[feature] = True
        
        # GPS es estándar en DJI
        features['precision_hover'] = 'GPS'
        
        return features
    
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
            ],
            # === NUEVAS ESPECIFICACIONES ===
            'capacidad_bateria_mah': [
                r'battery\s*capacity[:\s]*(\d+)\s*(mah|mAh|MAH)',
                r'capacity[:\s]*(\d+)\s*(mah|mAh|MAH)',
                r'(\d+)\s*(mah|mAh|MAH)\s*battery'
            ],
            'altitud_max_metros': [
                r'max\s*altitude[:\s]*(\d+\.?\d*)\s*(m|meters?|ft|feet)',
                r'service\s*ceiling[:\s]*(\d+\.?\d*)\s*(m|meters?|ft|feet)',
                r'max\s*takeoff\s*altitude[:\s]*(\d+\.?\d*)\s*(m|meters?|ft|feet)'
            ],
            'temperatura_operativa': [
                r'operating\s*temperature[:\s]*(-?\d+\.?\d*)\s*to\s*(\d+\.?\d*)\s*°C',
                r'working\s*temperature[:\s]*(-?\d+\.?\d*)\s*to\s*(\d+\.?\d*)\s*°C',
                r'temperature\s*range[:\s]*(-?\d+\.?\d*)\s*to\s*(\d+\.?\d*)\s*°C'
            ],
            'velocidad_ascenso_ms': [
                r'max\s*ascent\s*speed[:\s]*(\d+\.?\d*)\s*(m/s|mps)',
                r'ascent\s*speed[:\s]*(\d+\.?\d*)\s*(m/s|mps)',
                r'vertical\s*speed\s*up[:\s]*(\d+\.?\d*)\s*(m/s|mps)'
            ],
            'velocidad_descenso_ms': [
                r'max\s*descent\s*speed[:\s]*(\d+\.?\d*)\s*(m/s|mps)',
                r'descent\s*speed[:\s]*(\d+\.?\d*)\s*(m/s|mps)',
                r'vertical\s*speed\s*down[:\s]*(\d+\.?\d*)\s*(m/s|mps)'
            ],
            'tiempo_hover_minutos': [
                r'hover\s*time[:\s]*(\d+)\s*(min|minutes?|hrs?|hours?)',
                r'max\s*hover\s*time[:\s]*(\d+)\s*(min|minutes?|hrs?|hours?)',
                r'hovering\s*time[:\s]*(\d+)\s*(min|minutes?|hrs?|hours?)'
            ]
        }
        
        for spec_name, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    
                    # Convertir unidades si es necesario
                    if spec_name == 'peso_gramos':
                        value, unit = groups
                        if unit.lower() in ['kg']:
                            specs[spec_name] = float(value) * 1000
                        else:
                            specs[spec_name] = float(value)
                    elif spec_name == 'autonomia_minutos':
                        value, unit = groups
                        if unit.lower() in ['hrs', 'hours', 'hour']:
                            specs[spec_name] = float(value) * 60
                        else:
                            specs[spec_name] = float(value)
                    elif spec_name == 'alcance_metros':
                        value, unit = groups
                        if unit.lower() in ['km', 'kilometers']:
                            specs[spec_name] = float(value) * 1000
                        elif unit.lower() in ['ft', 'feet']:
                            specs[spec_name] = float(value) * 0.3048
                        else:
                            specs[spec_name] = float(value)
                    elif spec_name == 'velocidad_max_kmh':
                        value, unit = groups
                        if unit.lower() in ['mph']:
                            specs[spec_name] = float(value) * 1.60934
                        elif unit.lower() in ['m/s']:
                            specs[spec_name] = float(value) * 3.6
                        else:
                            specs[spec_name] = float(value)
                    # === NUEVAS CONVERSIONES ===
                    elif spec_name == 'capacidad_bateria_mah':
                        value, unit = groups
                        specs[spec_name] = float(value)
                    elif spec_name == 'altitud_max_metros':
                        value, unit = groups
                        if unit.lower() in ['ft', 'feet']:
                            specs[spec_name] = float(value) * 0.3048
                        else:
                            specs[spec_name] = float(value)
                    elif spec_name == 'temperatura_operativa':
                        min_temp, max_temp = groups
                        specs[spec_name] = f"{float(min_temp)}°C to {float(max_temp)}°C"
                    elif spec_name in ['velocidad_ascenso_ms', 'velocidad_descenso_ms']:
                        value, unit = groups
                        specs[spec_name] = float(value)
                    elif spec_name == 'tiempo_hover_minutos':
                        value, unit = groups
                        if unit.lower() in ['hrs', 'hours', 'hour']:
                            specs[spec_name] = float(value) * 60
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
    
    def _extract_autel_specs(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extractor específico para Autel"""
        drone_data = {
            'marca': 'Autel',
            'url_fuente': url,
            'metadata': {
                'fecha_extraccion': datetime.now().isoformat(),
                'version_scraper': '1.0.0',
                'confiabilidad_datos': 'alta'
            }
        }
        
        # Extraer nombre del modelo con múltiples selectores
        model_elem = soup.select_one('h1.product-title, .product-name h1, h1[class*="title"], .elementor-heading-title')
        if model_elem:
            model_text = model_elem.get_text(strip=True)
            # Limpiar prefijos de marca
            for prefix in ['Autel ', 'AUTEL ']:
                model_text = model_text.replace(prefix, '')
            drone_data['modelo'] = model_text
        else:
            # Extraer del URL como último recurso
            drone_data['modelo'] = self._extract_model_from_url(url)
        
        # Autel usa acordeones para especificaciones
        accordion_items = soup.find_all('div', class_='elementor-accordion-item')
        specs = {}

        for item in accordion_items:
            title = item.find('div', class_='elementor-tab-title')
            content = item.find('div', class_='elementor-tab-content')
            
            if title and content:
                title_text = title.get_text(strip=True).lower()
                if 'specification' in title_text or 'parameter' in title_text:
                    # Extraer tabla dentro del acordeón
                    table = content.find('table')
                    if table:
                        rows = table.find_all('tr')
                        for row in rows:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 2:
                                key = cells[0].get_text(strip=True).lower()
                                value = cells[1].get_text(strip=True)
                                # Procesar según tipo de spec
                                if 'weight' in key:
                                    specs['peso_gramos'] = self.data_cleaner.extract_number(value, 'grams')
                                elif 'flight time' in key:
                                    specs['autonomia_minutos'] = self.data_cleaner.extract_number(value, 'minutes')
                                elif 'range' in key or 'distance' in key:
                                    specs['alcance_metros'] = self.data_cleaner.extract_number(value, 'meters')

        # Si no hay especificaciones en acordeones, buscar en toda la página
        if not specs:
            page_text = soup.get_text()
            specs = self._extract_specs_with_regex(page_text)
            
        # Si aún no hay especificaciones, buscar en elementos específicos
        if not specs:
            spec_items = soup.select('.spec-item, .parameter-item, .product-parameter')
            for item in spec_items:
                text = item.get_text(strip=True)
                # Buscar patrones específicos
                weight_match = re.search(r'(\d+\.?\d*)\s*(g|kg)', text)
                if weight_match and not specs.get('peso_gramos'):
                    value, unit = weight_match.groups()
                    specs['peso_gramos'] = float(value) * (1000 if unit == 'kg' else 1)

        # Buscar JSON-LD que Autel incluye
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if '@graph' in data:
                    for item in data['@graph']:
                        if item.get('@type') == 'Product':
                            # Extraer precio si está disponible
                            if 'offers' in item:
                                drone_data['precio'] = {
                                    'usd': float(item['offers'].get('price', 0)),
                                    'moneda_local': item['offers'].get('priceCurrency', 'USD')
                                }
            except:
                pass
        
        # Si no hay tabla, buscar en acordeones o listas
        if not specs:
            spec_items = soup.select('.accordion-item, .spec-item, .parameter-item')
            for item in spec_items:
                text = item.get_text(strip=True)
                # Aplicar extracción con regex similar a DJI
                # ... (código de extracción)
        
        drone_data['especificaciones_tecnicas'] = self.data_cleaner.standardize_specifications(specs)
        
        # Extraer especificaciones de cámara
        drone_data['camara'] = self._extract_camera_specs(soup, {})
        
        # Extraer características de vuelo
        drone_data['caracteristicas_vuelo'] = self._extract_flight_features(soup, {})
        
        # Aplicar clasificación
        drone_data['clasificacion'] = self._classify_drone(drone_data)
        
        return drone_data

    def _extract_parrot_specs(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extractor específico para Parrot (mayormente PDFs)"""
        drone_data = {
            'marca': 'Parrot',
            'url_fuente': url,
            'metadata': {
                'fecha_extraccion': datetime.now().isoformat(),
                'version_scraper': '1.0.0',
                'confiabilidad_datos': 'media',
                'tipo_fuente': 'html_fallback'
            }
        }
        
        # Extraer nombre del modelo
        model_elem = soup.select_one('h1, .product-title, .drone-name')
        if model_elem:
            drone_data['modelo'] = model_elem.get_text(strip=True).replace('Parrot ', '')
        else:
            drone_data['modelo'] = self._extract_model_from_url(url)
        
        # Para Parrot, la mayoría de datos vienen de PDFs
        # Este es un fallback para contenido HTML básico
        page_text = soup.get_text()
        specs = self._extract_specs_with_regex(page_text)
        
        drone_data['especificaciones_tecnicas'] = self.data_cleaner.standardize_specifications(specs)
        drone_data['camara'] = self._extract_camera_specs(soup, {})
        drone_data['caracteristicas_vuelo'] = self._extract_flight_features(soup, {})
        drone_data['clasificacion'] = self._classify_drone(drone_data)
        
        return drone_data

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
        
        page_text = soup.get_text()
        
        # Buscar resolución de video
        video_patterns = [r'4K\b', r'6K\b', r'8K\b', r'1080p\b', r'720p\b']
        
        for pattern in video_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                camera['resolucion_video'] = match.group(0).upper()
                break
        
        # Buscar FPS
        fps_match = re.search(r'(\d+)\s*fps', page_text, re.IGNORECASE)
        if fps_match:
            camera['fps_max'] = int(fps_match.group(1))
        
        # Buscar estabilización
        if re.search(r'gimbal|stabiliz', page_text, re.IGNORECASE):
            camera['estabilizacion'] = 'mecanica'
        
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
        
        page_text = soup.get_text().lower()
        
        # Detectar características
        if 'obstacle' in page_text or 'collision' in page_text:
            features['evita_obstaculos'] = True
        
        if 'return to home' in page_text or 'rth' in page_text:
            features['retorno_automatico'] = True
        
        if 'tracking' in page_text or 'follow me' in page_text:
            features['seguimiento_objeto'] = True
        
        if 'night' in page_text:
            features['vuelo_nocturno'] = True
        
        if 'sport mode' in page_text:
            features['modo_sport'] = True
        
        if 'gps' in page_text:
            features['precision_hover'] = 'GPS'
        
        return features

    def _classify_drone(self, drone_data: Dict) -> Dict:
        """Clasificación automática del drone"""
        classification = {
            'categoria_peso': 'medio',
            'nivel_usuario': 'intermedio',
            'uso_principal': ['recreativo'],
            'certificaciones': []
        }
        
        # Obtener especificaciones
        specs = drone_data.get('especificaciones_tecnicas', {})
        peso = specs.get('peso_gramos', 0)
        
        # Validar que peso no sea None
        if peso is None:
            peso = 0
        
        # Clasificación por peso
        if peso <= 250:
            classification['categoria_peso'] = 'ultraligero'
            classification['nivel_usuario'] = 'principiante'
        elif peso <= 900:
            classification['categoria_peso'] = 'ligero'
        elif peso <= 2000:
            classification['categoria_peso'] = 'medio'
        else:
            classification['categoria_peso'] = 'pesado'
            classification['nivel_usuario'] = 'profesional'
        
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
            'Sec-Fetch-User': '?1',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
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

    def _classify_drone(self, drone_data: Dict) -> Dict:
        """Clasificación automática del drone"""
        classification = {
            'categoria_peso': 'medio',
            'nivel_usuario': 'intermedio',
            'uso_principal': [],
            'certificaciones': []
        }
        
        # Obtener especificaciones
        specs = drone_data.get('especificaciones_tecnicas', {})
        peso = specs.get('peso_gramos', 0)
        autonomia = specs.get('autonomia_minutos', 0)
        alcance = specs.get('alcance_metros', 0)
        
        # Validar que los valores no sean None
        if peso is None:
            peso = 0
        if autonomia is None:
            autonomia = 0
        if alcance is None:
            alcance = 0
        
        # Clasificación por peso
        if peso <= 250:
            classification['categoria_peso'] = 'ultraligero'
            classification['nivel_usuario'] = 'principiante'
            classification['certificaciones'] = ['no_requiere_registro']
        elif peso <= 900:
            classification['categoria_peso'] = 'ligero'
            classification['nivel_usuario'] = 'intermedio'
        elif peso <= 2000:
            classification['categoria_peso'] = 'medio'
            classification['nivel_usuario'] = 'avanzado'
        else:
            classification['categoria_peso'] = 'pesado'
            classification['nivel_usuario'] = 'profesional'
            classification['certificaciones'] = ['licencia_requerida']
        
        # Clasificación por uso según características
        camara = drone_data.get('camara', {})
        features = drone_data.get('caracteristicas_vuelo', {})
        
        if camara.get('resolucion_video') in ['4K', '6K', '8K']:
            classification['uso_principal'].append('fotografia_profesional')
            classification['uso_principal'].append('videografia')
        
        if autonomia >= 25:
            classification['uso_principal'].append('inspeccion')
            classification['uso_principal'].append('mapeo')
        
        if features.get('evita_obstaculos'):
            classification['uso_principal'].append('principiantes')
        
        if alcance >= 5000:  # 5km o más
            classification['uso_principal'].append('largo_alcance')
        
        # Si no se determinó uso específico, asignar uso recreativo
        if not classification['uso_principal']:
            classification['uso_principal'] = ['recreativo']
        
        return classification

    def _extract_generic_specs(self, soup: BeautifulSoup, brand: str, url: str) -> Dict:
        """Extractor genérico para cualquier marca"""
        drone_data = {
            'marca': brand.title(),
            'url_fuente': url,
            'metadata': {
                'fecha_extraccion': datetime.now().isoformat(),
                'version_scraper': '1.0.0',
                'confiabilidad_datos': 'media'
            }
        }
        
        # Extraer nombre del modelo
        model_elem = soup.select_one('h1, .product-title, .product-name')
        if model_elem:
            drone_data['modelo'] = model_elem.get_text(strip=True)
        else:
            drone_data['modelo'] = self._extract_model_from_url(url)
        
        # Extraer especificaciones usando métodos genéricos
        page_text = soup.get_text()
        specs = self._extract_specs_with_regex(page_text)
        
        # También intentar extraer de tablas
        table_specs = self._extract_specs_from_tables(soup)
        specs.update(table_specs)
        
        drone_data['especificaciones_tecnicas'] = self.data_cleaner.standardize_specifications(specs)
        drone_data['camara'] = self._extract_camera_specs(soup, {})
        drone_data['caracteristicas_vuelo'] = self._extract_flight_features(soup, {})
        drone_data['clasificacion'] = self._classify_drone(drone_data)
        
        return drone_data
    

async def test_single_url():
    """Test rápido de un solo URL"""
    scraper = DroneScraperOrchestrator()
    url = "https://www.dji.com/mini-3"
    async with aiohttp.ClientSession() as session:
        scraper.session = session
        html = await scraper._fetch_page_robust(url)
        if html:
            print(f"✓ Descargado: {len(html)} caracteres")
            soup = BeautifulSoup(html, 'lxml')
            title = soup.find('title')
            print(f"✓ Título: {title.text if title else 'No encontrado'}")
        else:
            print("✗ Error descargando página")

# Ejecutar con: asyncio.run(test_single_url())

async def main():
    """Función principal con validación y reporte completo"""
    scraper = DroneScraperOrchestrator()
    
    try:
        logger.info("Iniciando scraping de drones...")
        start_time = datetime.now()
        
        # Realizar scraping con manejo de errores y reintentos
        max_retries = 3
        results = {}
        for attempt in range(max_retries):
            try:
                results = await scraper.scrape_all_brands()
                break
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"Intento {attempt + 1} falló: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(5 * (attempt + 1))  # Backoff exponencial
                else:
                    logger.error("Máximo de reintentos alcanzado")
                    results = {}
        
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
"""Scraper mejorado de drones con análisis específico por modelo y cumplimiento de robots.txt."""

import json
import logging
import random
import time
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime

# Importaciones de Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from scraping.utils import (
    setup_logging, validate_drone_data, validate_drone_data_v2,
    normalize_text, extract_number, normalize_weight, normalize_price
)
from scraping.scraper_config import URLS, SCRAPER_DELAY, HEADERS
from scraping.parsers.dji import DJIParser
from scraping.parsers.autel import AutelParser
from scraping.parsers.parrot import ParrotParser
from scraping.robot_checker import RobotChecker

logger = logging.getLogger(__name__)

if not SELENIUM_AVAILABLE:
    logger.warning("Selenium no disponible. El renderizado JS estará deshabilitado.")

class DroneScraperOrchestrator:
    def __init__(self, output_dir: Path = Path("data")):
        self.output_dir = Path(output_dir)
        self.ensure_directories()
        
        # Inicializar parsers
        self.parsers = {
            'dji': DJIParser(),
            'autel': AutelParser(),
            'parrot': ParrotParser()
        }
        
        # Inicializar verificador de robots
        self.robot_checker = RobotChecker(HEADERS['User-Agent'])
        self.allowed_urls = None
        
        # Inicializar sesión
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
    def ensure_directories(self):
        """Crear directorios necesarios."""
        for subdir in ['raw', 'interim', 'processed']:
            (self.output_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    def verify_robots_txt(self):
        """Verificar cumplimiento con robots.txt y filtrar URLs permitidas."""
        logger.info("ROBOTS: Verificando permisos de robots.txt...")
        
        # Verificar todas las URLs de configuración
        self.allowed_urls = self.robot_checker.check_all_urls(URLS)
        
        # Logs informativos
        total_original = sum(len(urls) for urls in URLS.values())
        total_allowed = sum(len(urls) for urls in self.allowed_urls.values())
        
        if total_allowed < total_original:
            logger.warning(f"ADVERTENCIA: {total_original - total_allowed} URLs bloqueadas por robots.txt")
        else:
            logger.info("ÉXITO: Todas las URLs están permitidas por robots.txt")
        
        return self.allowed_urls
    
    def get_chrome_driver(self) -> webdriver.Chrome:
        """Configurar y retornar driver de Chrome."""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument(f'--user-agent={HEADERS["User-Agent"]}')
        
        # Deshabilitar imágenes y CSS para acelerar la carga
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.stylesheets": 2
        }
        options.add_experimental_option("prefs", prefs)
        
        return webdriver.Chrome(options=options)
    
    def scrape_url(self, url: str, brand: str) -> Optional[Dict[str, Any]]:
        """Scrapear una URL individual con manejo mejorado de errores."""
        logger.info(f"Scrapeando {brand}: {url}")
        
        try:
            # Determinar parser
            parser = self.parsers.get(brand.lower())
            if not parser:
                logger.error(f"No se encontró parser para la marca: {brand}")
                return None
            
            # Agregar demora por cortesía
            delay = random.uniform(SCRAPER_DELAY['min'], SCRAPER_DELAY['max'])
            logger.debug(f"Esperando {delay:.1f}s antes de la solicitud")
            time.sleep(delay)
            
            # Hacer solicitud con lógica de reintentos
            session = self._get_session()
            
            # Manejar URLs PDF para Parrot
            if url.endswith('.pdf') and brand.lower() == 'parrot':
                return self._scrape_pdf_url(url, parser)
            
            # Manejar páginas renderizadas con JS para Autel
            if '#jsgg' in url and brand.lower() == 'autel':
                return self._scrape_js_page(url, parser)
            
            # Scraping HTML estándar
            response = session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parsear HTML con BeautifulSoup
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Verificar si la página tiene suficiente contenido, si no, intentar con Selenium para DJI
            page_text = soup.get_text().strip()
            if len(page_text) < 1000 and brand.lower() == 'dji':
                logger.info(f"La página DJI tiene poco contenido ({len(page_text)} caracteres), intentando con Selenium")
                return self._scrape_js_page(url, parser)
            
            # Parsear usando el parser apropiado
            drone_data = parser.parse(soup, url)
            
            if not drone_data:
                logger.warning(f"No se extrajeron datos de {url}")
                return None
            
            # Validar y mejorar datos
            if self._is_valid_drone_data(drone_data):
                # Agregar metadatos
                drone_data['url'] = url
                drone_data['scraped_at'] = time.time()
                drone_data['brand'] = brand
                
                # Validar especificaciones
                validated_data = validate_drone_data_v2(drone_data)
                
                logger.info(f"ÉXITO: Scrapeado exitosamente: {drone_data.get('modelo', 'Desconocido')}")
                return validated_data
            else:
                logger.warning(f"Datos de drone inválidos de {url}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout scrapeando {url}")
        except requests.exceptions.ConnectionError:
            logger.error(f"Error de conexión scrapeando {url}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP {e.response.status_code} scrapeando {url}")
        except Exception as e:
            logger.error(f"Error inesperado scrapeando {url}: {str(e)}")
        
        return None
    
    def _scrape_pdf_url(self, url: str, parser) -> Optional[Dict[str, Any]]:
        """Scrapear documento PDF para especificaciones de Parrot."""
        try:
            logger.info(f"PDF: Scrapeando PDF: {url}")
            
            session = self._get_session()
            response = session.get(url, timeout=30)
            response.raise_for_status()
            
            # Guardar PDF temporalmente para parsear
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(response.content)
                tmp_file_path = tmp_file.name
            
            try:
                # Parsear PDF usando el parser
                drone_data = parser.parse_pdf(tmp_file_path, url)
                return drone_data
            finally:
                # Limpiar archivo temporal
                import os
                os.unlink(tmp_file_path)
                
        except Exception as e:
            logger.error(f"Error scrapeando PDF {url}: {str(e)}")
            return None
    
    def _scrape_js_page(self, url: str, parser) -> Optional[Dict[str, Any]]:
        """Scrapear páginas renderizadas con JS usando Selenium."""
        if not SELENIUM_AVAILABLE:
            logger.warning(f"Selenium no disponible, no se puede scrapear página JS: {url}")
            return None
        
        driver = None
        try:
            logger.info(f"JS: Scrapeando página JS: {url}")
            
            # Obtener driver de Chrome
            driver = self.get_chrome_driver()
            
            # Navegar a la URL
            driver.get(url)
            
            # Esperar a que la página cargue
            time.sleep(5)  # Espera inicial
            
            # Para páginas con #jsgg, esperar específicamente por contenido
            if '#jsgg' in url:
                logger.info("URL #jsgg detectada, esperando contenido específico...")
                try:
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    from selenium.webdriver.common.by import By
                    
                    # Esperar por la sección jsgg o contenido de especificaciones
                    wait = WebDriverWait(driver, 15)
                    
                    # Intentar múltiples selectores para encontrar el contenido
                    selectors_to_try = [
                        "#jsgg",
                        "[id*='jsgg']",
                        "[class*='spec']",
                        "[class*='parameter']",
                        "[class*='detail']",
                        "table",
                        ".spec-table",
                        ".parameter-table"
                    ]
                    
                    element_found = False
                    for selector in selectors_to_try:
                        try:
                            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                            if element and element.text.strip():
                                logger.info(f"Contenido encontrado con selector: {selector}")
                                element_found = True
                                break
                        except Exception:
                            continue
                    
                    if not element_found:
                        logger.warning("No se encontró contenido específico, procediendo con el estado actual de la página")
                    
                    # Espera adicional para JavaScript dinámico
                    time.sleep(3)
                    
                    # Desplazar para activar carga diferida si existe
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(1)
                    
                except Exception as e:
                    logger.warning(f"Error esperando contenido #jsgg: {e}")
            
            # Obtener código fuente de la página y parsear
            page_source = driver.page_source
            
            # Verificar que tenemos contenido significativo
            if len(page_source) < 1000:
                logger.warning(f"Código fuente muy corto ({len(page_source)} caracteres), puede no estar completamente cargado")
            
            # Parsear con BeautifulSoup
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Depuración: Registrar información sobre el contenido parseado
            logger.debug(f"La página parseada tiene {len(soup.find_all())} elementos")
            
            # Verificar si encontramos la sección jsgg
            if '#jsgg' in url:
                jsgg_section = soup.find(id='jsgg')
                if jsgg_section:
                    logger.info(f"Sección #jsgg encontrada con {len(jsgg_section.get_text())} caracteres")
                else:
                    logger.warning("No se encontró sección #jsgg en el contenido parseado")
                    # Buscar contenido alternativo
                    spec_elements = soup.find_all(['div', 'section'], class_=lambda x: bool(x and any(
                        keyword in x.lower() for keyword in ['spec', 'param', 'detail']
                    )))
                    logger.info(f"Se encontraron {len(spec_elements)} secciones de especificaciones potenciales")
            
            # Parsear usando el parser apropiado
            drone_data = parser.parse(soup, url)
            
            if not drone_data:
                logger.warning(f"No se extrajeron datos de la página JS: {url}")
                return None
            
            # Validar y mejorar datos
            if self._is_valid_drone_data(drone_data):
                # Agregar metadatos
                drone_data['url'] = url
                drone_data['scraped_at'] = time.time()
                drone_data['brand'] = parser.brand.lower()
                drone_data['scraped_with'] = 'selenium'
                
                # Validar especificaciones
                from scraping.utils import validate_drone_data_v2
                validated_data = validate_drone_data_v2(drone_data)
                
                logger.info(f"ÉXITO: Página JS scrapeada exitosamente: {drone_data.get('modelo', 'Desconocido')}")
                return validated_data
            else:
                logger.warning(f"Datos de drone inválidos de página JS: {url}")
                # Registrar especificaciones para depuración
                specs = drone_data.get('especificaciones_tecnicas', {})
                valid_specs = sum(1 for v in specs.values() if v and v != 0 and v != "")
                logger.warning(f"  Especificaciones válidas encontradas: {valid_specs}")
                if specs:
                    logger.debug(f"  Especificaciones: {list(specs.keys())}")
                return None
                
        except Exception as e:
            logger.error(f"Error scrapeando página JS {url}: {str(e)}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    logger.warning(f"Error cerrando driver: {e}")
        
        return None
    
    def _complete_missing_specs(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Completar especificaciones faltantes con valores predeterminados para mejorar la integridad de datos."""
        if not result or 'especificaciones_tecnicas' not in result:
            return result
        
        specs = result['especificaciones_tecnicas']
        
        # Definir valores predeterminados para especificaciones faltantes
        default_specs = {
            'peso_gramos': 0.0,
            'dimensiones_plegado': "",
            'vuelo_minutos': 0.0,
            'vel_horizontal_mps': 0.0,
            'vel_ascenso_mps': 0.0,
            'alcance_video_km': 0.0,
            'altitud_despegue_m': 0.0,
            'resistencia_viento_mps': 0.0,
            'almacenamiento_interno_gb': None,
            'sensor_camara': "",
            'resolucion_video': "",
            'deteccion_obstaculos': False
        }
        
        # Agregar especificaciones faltantes con valores predeterminados
        for spec_name, default_value in default_specs.items():
            if spec_name not in specs:
                specs[spec_name] = default_value
        
        # Actualizar el resultado con especificaciones limpias
        result['especificaciones_tecnicas'] = specs
        
        return result
    
    def scrape_brand(self, brand: str) -> List[Dict[str, Any]]:
        """Scrapear todas las URLs de una marca."""
        logger.info(f"Iniciando scraping de {brand}...")
        
        # Usar URLs permitidas por robots.txt si están disponibles
        if self.allowed_urls is not None:
            urls = self.allowed_urls.get(brand, [])
        else:
            urls = URLS.get(brand, [])
        
        results = []
        
        for url in urls:
            result = self.scrape_url(url, brand)
            if result:
                results.append(result)
        
        logger.info(f"Scraping de {brand} completado. Se encontraron {len(results)} drones.")
        return results
    
    def run_parallel(self, max_workers: int = 3) -> List[Dict[str, Any]]:
        """Ejecutar scraping en paralelo por marca."""
        logger.info("Iniciando scraping paralelo...")
        
        # Verificar robots.txt antes de empezar
        self.verify_robots_txt()
        
        all_results = []
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Enviar tareas para cada marca
            brands = self.allowed_urls.keys() if self.allowed_urls else URLS.keys()
            future_to_brand = {
                executor.submit(self.scrape_brand, brand): brand 
                for brand in brands
            }
            
            # Recolectar resultados
            for future in as_completed(future_to_brand):
                brand = future_to_brand[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                    logger.info(f"Completado {brand}: {len(results)} drones")
                except Exception as e:
                    logger.error(f"Error con {brand}: {str(e)}")
        
        logger.info(f"Scraping paralelo completado. Total: {len(all_results)} drones")
        return all_results
    
    def run_sequential(self) -> List[Dict[str, Any]]:
        """Ejecutar scraping secuencialmente (modo alternativo)."""
        logger.info("Iniciando scraping secuencial...")
        
        # Verificar robots.txt antes de empezar
        self.verify_robots_txt()
        
        all_results = []
        
        # Usar allowed_urls si está disponible
        brands = self.allowed_urls.keys() if self.allowed_urls else URLS.keys()
        
        for brand in brands:
            try:
                results = self.scrape_brand(brand)
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Error con {brand}: {str(e)}")
        
        logger.info(f"Scraping secuencial completado. Total: {len(all_results)} drones")
        return all_results
    
    def save_results(self, results: List[Dict[str, Any]]):
        """Guardar resultados normalizados en JSON."""
        if not results:
            logger.warning("No hay resultados para guardar")
            return
        
        # Filtrar resultados válidos
        valid_results = []
        for result in results:
            # Validar que tenga datos mínimos
            if not result.get('modelo') or result['modelo'].lower() in ['specs', 'unknown', '']:
                logger.warning(f"Saltando resultado inválido: {result}")
                continue
                
            # Verificar que tenga al menos 3 especificaciones con valores
            specs = result.get('especificaciones_tecnicas', {})
            valid_specs = sum(1 for v in specs.values() if v and v != 0 and v != "")
            
            if valid_specs >= 3:
                valid_results.append(result)
            else:
                logger.warning(f"Drone {result['modelo']} tiene pocas especificaciones válidas: {valid_specs}")
        
        if not valid_results:
            logger.error("No hay resultados válidos para guardar")
            return
        
        # Guardar solo resultados válidos
        output_path = self.output_dir / 'processed' / 'drones_normalized.json'
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(valid_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Guardados {len(valid_results)} drones válidos de {len(results)} totales")

    def _get_session(self) -> requests.Session:
        """Obtener sesión configurada de requests."""
        return self.session
    
    def _is_valid_drone_data(self, data: Dict[str, Any]) -> bool:
        """Verificar si los datos del drone son válidos con validación mejorada."""
        if not isinstance(data, dict):
            logger.warning("Tipo de datos inválido: no es un diccionario")
            return False
        
        # Verificar campos requeridos
        required_fields = ['modelo', 'marca']
        for field in required_fields:
            if field not in data:
                logger.warning(f"Falta campo requerido: {field}")
                return False
            if not data[field] or data[field].lower() in ['unknown', 'specs', '']:
                logger.warning(f"Valor inválido para campo requerido {field}: {data[field]}")
                return False
        
        # Verificar si tenemos especificaciones
        specs = data.get('especificaciones_tecnicas', {})
        if not isinstance(specs, dict):
            logger.warning("Especificaciones inválidas: no es un diccionario")
            return False
        
        # Contar especificaciones válidas con criterios más flexibles
        valid_specs = 0
        important_specs = 0
        
        # Definir niveles de importancia
        critical_specs = ['peso_gramos', 'vuelo_minutos', 'vel_horizontal_mps']
        important_spec_names = ['dimensiones_plegado', 'alcance_video_km', 'sensor_camara', 'resolucion_video']
        
        for spec_name, spec_value in specs.items():
            # Verificar si la especificación tiene un valor válido
            if spec_value is not None and spec_value != '' and spec_value != 0:
                # Para valores de cadena, verificar longitud
                if isinstance(spec_value, str) and len(spec_value.strip()) > 0:
                    valid_specs += 1
                    if spec_name in critical_specs:
                        important_specs += 2  # Especificaciones críticas cuentan el doble
                    elif spec_name in important_spec_names:
                        important_specs += 1
                # Para valores numéricos, verificar si son razonables
                elif isinstance(spec_value, (int, float)) and spec_value > 0:
                    valid_specs += 1
                    if spec_name in critical_specs:
                        important_specs += 2  # Especificaciones críticas cuentan el doble
                    elif spec_name in important_spec_names:
                        important_specs += 1
                # Para valores booleanos, siempre son válidos
                elif isinstance(spec_value, bool):
                    valid_specs += 1
                    if spec_name in important_spec_names:
                        important_specs += 1
        
        # Lógica de validación más flexible
        # Aceptar si:
        # 1. Tiene al menos 2 especificaciones válidas Y al menos 1 especificación importante, O
        # 2. Tiene al menos 3 especificaciones válidas, O
        # 3. Tiene al menos 1 especificación crítica con valor válido
        
        has_critical_spec = any(
            spec_name in critical_specs and specs.get(spec_name) not in [None, '', 0]
            for spec_name in critical_specs
        )
        
        is_valid = (
            (valid_specs >= 2 and important_specs >= 1) or
            (valid_specs >= 3) or
            (has_critical_spec and valid_specs >= 1)
        )
        
        if not is_valid:
            logger.warning(f"Validación de drone fallida: {data.get('modelo', 'Desconocido')}")
            logger.warning(f"  Especificaciones válidas: {valid_specs}, Especificaciones importantes: {important_specs}, Tiene crítico: {has_critical_spec}")
            logger.warning(f"  Especificaciones encontradas: {list(specs.keys())}")
            # Registrar valores de especificación para depuración
            for spec_name, spec_value in specs.items():
                if spec_value not in [None, '', 0]:
                    logger.debug(f"    {spec_name}: {spec_value} (tipo: {type(spec_value)})")
        else:
            logger.info(f"Validación de drone exitosa: {data.get('modelo', 'Desconocido')} ({valid_specs} especificaciones válidas, {important_specs} importantes)")
        
        return is_valid

def main():
    """Main entry point."""
    setup_logging()
    
    scraper = DroneScraperOrchestrator()
    
    logger.info("Starting drone scraper...")
    
    try:
        # Try parallel first, fallback to sequential
        results = scraper.run_parallel()
        
        if not results:
            logger.warning("Parallel scraping failed, trying sequential...")
            results = scraper.run_sequential()
        
        if results:
            scraper.save_results(results)
            logger.info(f"Scraping completed successfully. Total drones: {len(results)}")
        else:
            logger.error("No data collected")
            
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Drone specifications scraper')
    parser.add_argument('--parallel', action='store_true', 
                       help='Run in parallel mode (default)')
    parser.add_argument('--sequential', action='store_true',
                       help='Run in sequential mode')
    
    args = parser.parse_args()
    
    main()

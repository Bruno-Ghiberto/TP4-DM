"""Verificación de robots.txt para web scraping ético."""
import logging
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from typing import Dict, Set, Optional
import requests
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger(__name__)

class RobotChecker:
    """Verificador de permisos robots.txt para scraping ético."""
    
    def __init__(self, user_agent: str = "edu-research-bot/1.0"):
        """
        Inicializar el verificador de robots.txt.
        
        Args:
            user_agent: User-Agent a usar para verificación
        """
        self.user_agent = user_agent
        self._robot_parsers: Dict[str, RobotFileParser] = {}
        self._checked_domains: Set[str] = set()
        self._allowed_cache: Dict[str, bool] = {}
    
    def _get_domain(self, url: str) -> str:
        """Extraer dominio base de una URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def _load_robots_txt(self, domain: str) -> Optional[RobotFileParser]:
        """
        Cargar y parsear robots.txt de un dominio.
        
        Args:
            domain: Dominio base (ej: https://www.dji.com)
            
        Returns:
            RobotFileParser configurado o None si hay error
        """
        if domain in self._robot_parsers:
            return self._robot_parsers[domain]
        
        robots_url = urljoin(domain, '/robots.txt')
        logger.info(f"Verificando robots.txt en: {robots_url}")
        
        try:
            # Verificar si robots.txt existe
            response = requests.get(robots_url, timeout=10)
            
            if response.status_code == 404:
                logger.info(f"robots.txt no encontrado en {domain} - Asumiendo permitido")
                # Si no hay robots.txt, asumimos que está permitido
                return None
            
            if response.status_code != 200:
                logger.warning(f"Error {response.status_code} accediendo a robots.txt en {domain}")
                return None
            
            # Crear y configurar parser
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            self._robot_parsers[domain] = rp
            logger.info(f"robots.txt cargado exitosamente para {domain}")
            
            # Debug: mostrar reglas relevantes
            self._log_robot_rules(rp, domain)
            
            return rp
            
        except (RequestException, Timeout) as e:
            logger.warning(f"Error cargando robots.txt de {domain}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado con robots.txt de {domain}: {e}")
            return None
    
    def _log_robot_rules(self, rp: RobotFileParser, domain: str):
        """Log de reglas robots.txt relevantes para debug."""
        try:
            # Verificar si hay reglas específicas para nuestro user-agent
            can_fetch_root = rp.can_fetch(self.user_agent, '/')
            can_fetch_specs = rp.can_fetch(self.user_agent, '/specs')
            
            logger.debug(f"Reglas robots.txt para {domain}:")
            logger.debug(f"  • User-Agent: {self.user_agent}")
            logger.debug(f"  • Puede acceder a '/': {can_fetch_root}")
            logger.debug(f"  • Puede acceder a '/specs': {can_fetch_specs}")
            
            # Verificar delay recomendado
            delay = rp.crawl_delay(self.user_agent)
            if delay:
                logger.info(f"  • Delay recomendado: {delay}s")
            
        except Exception as e:
            logger.debug(f"Error extrayendo reglas de robots.txt: {e}")
    
    def is_allowed(self, url: str) -> bool:
        """
        Verificar si una URL está permitida según robots.txt.
        
        Args:
            url: URL completa a verificar
            
        Returns:
            True si está permitido acceder a la URL
        """
        # Cache para evitar verificaciones repetidas
        if url in self._allowed_cache:
            return self._allowed_cache[url]
        
        domain = self._get_domain(url)
        
        # Cargar robots.txt si no lo hemos hecho
        if domain not in self._checked_domains:
            self._load_robots_txt(domain)
            self._checked_domains.add(domain)
        
        # Si no hay parser (no existe robots.txt o error), permitir acceso
        rp = self._robot_parsers.get(domain)
        if rp is None:
            logger.debug(f"Sin restricciones robots.txt para {url}")
            self._allowed_cache[url] = True
            return True
        
        # Verificar permisos usando el parser
        try:
            allowed = rp.can_fetch(self.user_agent, url)
            self._allowed_cache[url] = allowed
            
            if allowed:
                logger.debug(f"OK: Acceso permitido a: {url}")
            else:
                logger.warning(f"DENIED: Acceso DENEGADO por robots.txt: {url}")
            
            return allowed
            
        except Exception as e:
            logger.error(f"Error verificando permisos para {url}: {e}")
            # En caso de error, permitir acceso por defecto
            self._allowed_cache[url] = True
            return True
    
    def get_crawl_delay(self, url: str) -> Optional[float]:
        """
        Obtener delay recomendado para un dominio.
        
        Args:
            url: URL del dominio
            
        Returns:
            Delay en segundos o None si no está especificado
        """
        domain = self._get_domain(url)
        rp = self._robot_parsers.get(domain)
        
        if rp is None:
            return None
        
        try:
            delay = rp.crawl_delay(self.user_agent)
            if delay:
                # Convertir a float si es string
                if isinstance(delay, str):
                    delay = float(delay)
                logger.info(f"Delay recomendado para {domain}: {delay}s")
                return delay
            return None
        except Exception as e:
            logger.debug(f"Error obteniendo delay para {domain}: {e}")
            return None
    
    def check_all_urls(self, urls: Dict[str, list]) -> Dict[str, list]:
        """
        Verificar todas las URLs de configuración y filtrar las permitidas.
        
        Args:
            urls: Diccionario de URLs por marca (formato URLS de scraper_config)
            
        Returns:
            Diccionario filtrado con solo URLs permitidas
        """
        logger.info("ROBOTS: Iniciando verificación robots.txt para todas las URLs...")
        
        allowed_urls = {}
        total_urls = 0
        blocked_urls = 0
        
        for brand, url_list in urls.items():
            allowed_urls[brand] = []
            
            for url in url_list:
                total_urls += 1
                if self.is_allowed(url):
                    allowed_urls[brand].append(url)
                else:
                    blocked_urls += 1
                    logger.warning(f"BLOCKED: URL bloqueada por robots.txt: {url}")
        
        # Resumen final
        allowed_total = total_urls - blocked_urls
        logger.info(f"SUMMARY: Verificación robots.txt completada:")
        logger.info(f"   • URLs verificadas: {total_urls}")
        logger.info(f"   • URLs permitidas: {allowed_total}")
        logger.info(f"   • URLs bloqueadas: {blocked_urls}")
        
        if blocked_urls > 0:
            logger.warning(f"WARNING: {blocked_urls} URLs fueron bloqueadas por robots.txt")
        
        return allowed_urls
    
    def get_domain_summary(self) -> Dict[str, dict]:
        """
        Obtener resumen de verificaciones por dominio.
        
        Returns:
            Diccionario con información por dominio
        """
        summary = {}
        
        for domain in self._checked_domains:
            rp = self._robot_parsers.get(domain)
            summary[domain] = {
                'robots_txt_exists': rp is not None,
                'crawl_delay': rp.crawl_delay(self.user_agent) if rp else None,
                'can_fetch_root': rp.can_fetch(self.user_agent, '/') if rp else True,
                'can_fetch_specs': rp.can_fetch(self.user_agent, '/specs') if rp else True
            }
        
        return summary


def verify_robots_compliance(urls: Dict[str, list], user_agent: str = "edu-research-bot/1.0") -> Dict[str, list]:
    """
    Función de conveniencia para verificar compliance con robots.txt.
    
    Args:
        urls: Diccionario de URLs por marca
        user_agent: User-Agent a usar
        
    Returns:
        Diccionario filtrado con solo URLs permitidas
    """
    checker = RobotChecker(user_agent)
    return checker.check_all_urls(urls)


if __name__ == "__main__":
    """Test del verificador con las URLs del proyecto."""
    import sys
    from pathlib import Path
    
    # Agregar el directorio padre al path para importar scraper_config
    sys.path.append(str(Path(__file__).parent.parent))
    
    from scraping.scraper_config import URLS, HEADERS
    
    # Configurar logging para el test
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("ROBOTS: Probando verificador de robots.txt...")
    
    # Verificar URLs del proyecto
    checker = RobotChecker(HEADERS['User-Agent'])
    allowed_urls = checker.check_all_urls(URLS)
    
    print("\nRESULTS: Resultados por marca:")
    for brand, urls in allowed_urls.items():
        print(f"  • {brand.upper()}: {len(urls)} URLs permitidas")
    
    print("\nSUMMARY: Resumen por dominio:")
    summary = checker.get_domain_summary()
    for domain, info in summary.items():
        print(f"  • {domain}:")
        print(f"    - robots.txt existe: {info['robots_txt_exists']}")
        print(f"    - Delay recomendado: {info['crawl_delay']}s" if info['crawl_delay'] else "    - Sin delay específico")
        print(f"    - Acceso a /specs: {'OK' if info['can_fetch_specs'] else 'DENIED'}") 
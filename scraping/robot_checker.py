#Robot Checker - Validación ética de robots.txt
#Asegura el cumplimiento de las políticas de scraping de cada sitio

import logging
from typing import Tuple, List, Optional
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class RobotChecker:
    """Verificador avanzado de robots.txt para scraping ético"""
    
    def __init__(self):
        self.robot_parsers = {}
        self.default_user_agent = "Academic-Drone-Research-Bot/1.0"
        self.timeout = 10
    
    def can_scrape_advanced(self, url: str, user_agent: str = '*') -> Tuple[bool, str]:
        """
        Verificación avanzada de permisos de scraping
        
        Args:
            url: URL a verificar
            user_agent: User agent a usar (default: *)
        
        Returns:
            Tuple (puede_scrapear, mensaje)
        """
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        robots_url = urljoin(base_url, '/robots.txt')
        
        # Usar user agent específico si no se proporciona
        if user_agent == '*':
            user_agent = self.default_user_agent
        
        try:
            # Obtener o crear parser para este dominio
            if base_url not in self.robot_parsers:
                self.robot_parsers[base_url] = self._create_robot_parser(robots_url)
            
            parser = self.robot_parsers[base_url]
            
            # Verificar si podemos acceder a la URL
            can_fetch = parser.can_fetch(user_agent, url)
            
            if not can_fetch:
                # Intentar con user agent genérico
                can_fetch_generic = parser.can_fetch('*', url)
                
                if can_fetch_generic:
                    return True, f"Permitido con user agent genérico, no con {user_agent}"
                else:
                    return False, f"Acceso denegado por robots.txt para {url}"
            
            # Verificar restricciones adicionales
            crawl_delay = self._get_crawl_delay_from_parser(parser, user_agent)
            
            message = "Acceso permitido"
            if crawl_delay:
                message += f" (Crawl-delay: {crawl_delay}s)"
            
            # Verificar sitemaps disponibles
            sitemaps = parser.site_maps()
            if sitemaps:
                message += f" - {len(sitemaps)} sitemaps disponibles"
            
            return True, message
            
        except Exception as e:
            logger.warning(f"Error verificando robots.txt para {base_url}: {str(e)}")
            # En caso de error, ser conservador y permitir con advertencia
            return True, f"No se pudo verificar robots.txt (error: {str(e)}), procediendo con precaución"
    
    def get_crawl_delay(self, robots_url: str, user_agent: str = None) -> float:
        """
        Obtener el Crawl-delay especificado en robots.txt
        
        Args:
            robots_url: URL del archivo robots.txt
            user_agent: User agent específico
        
        Returns:
            Delay en segundos (mínimo 3.0 si no especificado)
        """
        if user_agent is None:
            user_agent = self.default_user_agent
        
        try:
            parser = self._create_robot_parser(robots_url)
            delay = self._get_crawl_delay_from_parser(parser, user_agent)
            
            # Si no hay delay especificado, usar mínimo ético de 3 segundos
            return max(delay or 3.0, 3.0)
            
        except Exception as e:
            logger.warning(f"Error obteniendo crawl delay: {str(e)}")
            return 3.0  # Default conservador
    
    def check_site_maps(self, robots_url: str) -> List[str]:
        """
        Descubrir sitemaps desde robots.txt
        
        Args:
            robots_url: URL del archivo robots.txt
        
        Returns:
            Lista de URLs de sitemaps
        """
        try:
            parser = self._create_robot_parser(robots_url)
            sitemaps = parser.site_maps() or []
            
            logger.info(f"Encontrados {len(sitemaps)} sitemaps en {robots_url}")
            
            # Validar sitemaps accesibles
            valid_sitemaps = []
            for sitemap in sitemaps:
                try:
                    response = requests.head(sitemap, timeout=5)
                    if response.status_code == 200:
                        valid_sitemaps.append(sitemap)
                        logger.info(f"Sitemap válido: {sitemap}")
                except:
                    logger.warning(f"Sitemap inaccesible: {sitemap}")
            
            return valid_sitemaps
            
        except Exception as e:
            logger.error(f"Error verificando sitemaps: {str(e)}")
            return []
    
    def get_allowed_paths(self, base_url: str, user_agent: str = '*') -> List[str]:
        """
        Obtener rutas explícitamente permitidas
        
        Args:
            base_url: URL base del sitio
            user_agent: User agent a verificar
        
        Returns:
            Lista de rutas permitidas
        """
        robots_url = urljoin(base_url, '/robots.txt')
        allowed_paths = []
        
        try:
            response = requests.get(robots_url, timeout=self.timeout)
            if response.status_code == 200:
                lines = response.text.split('\n')
                
                current_ua = None
                for line in lines:
                    line = line.strip()
                    
                    # Detectar sección de user agent
                    if line.lower().startswith('user-agent:'):
                        current_ua = line.split(':', 1)[1].strip()
                    
                    # Si estamos en la sección correcta
                    elif current_ua in ['*', user_agent]:
                        if line.lower().startswith('allow:'):
                            path = line.split(':', 1)[1].strip()
                            if path:
                                allowed_paths.append(path)
                
                logger.info(f"Encontradas {len(allowed_paths)} rutas permitidas para {user_agent}")
                
        except Exception as e:
            logger.error(f"Error obteniendo rutas permitidas: {str(e)}")
        
        return allowed_paths
    
    def check_rate_limits(self, base_url: str) -> Dict[str, Any]:
        """
        Verificar todos los límites de rate especificados
        
        Args:
            base_url: URL base del sitio
        
        Returns:
            Diccionario con información de rate limiting
        """
        robots_url = urljoin(base_url, '/robots.txt')
        rate_info = {
            'crawl_delay': None,
            'request_rate': None,
            'visit_time': None,
            'custom_rules': []
        }
        
        try:
            response = requests.get(robots_url, timeout=self.timeout)
            if response.status_code == 200:
                lines = response.text.split('\n')
                
                for line in lines:
                    line = line.strip().lower()
                    
                    # Crawl-delay
                    if line.startswith('crawl-delay:'):
                        try:
                            delay = float(line.split(':', 1)[1].strip())
                            rate_info['crawl_delay'] = delay
                        except:
                            pass
                    
                    # Request-rate (formato: requests/seconds)
                    elif line.startswith('request-rate:'):
                        try:
                            rate_str = line.split(':', 1)[1].strip()
                            if '/' in rate_str:
                                requests_num, seconds = rate_str.split('/')
                                rate_info['request_rate'] = {
                                    'requests': int(requests_num),
                                    'seconds': int(seconds)
                                }
                        except:
                            pass
                    
                    # Visit-time (horarios permitidos)
                    elif line.startswith('visit-time:'):
                        rate_info['visit_time'] = line.split(':', 1)[1].strip()
                    
                    # Reglas custom (ej: "max-connections:")
                    elif ':' in line and any(keyword in line for keyword in ['max-', 'limit', 'rate']):
                        rate_info['custom_rules'].append(line)
                
        except Exception as e:
            logger.error(f"Error verificando rate limits: {str(e)}")
        
        return rate_info
    
    def _create_robot_parser(self, robots_url: str) -> RobotFileParser:
        """Crear y configurar un parser de robots.txt"""
        parser = RobotFileParser()
        parser.set_url(robots_url)
        
        try:
            # Leer con timeout personalizado
            response = requests.get(robots_url, timeout=self.timeout)
            if response.status_code == 200:
                parser.parse(response.text.splitlines())
            else:
                logger.warning(f"robots.txt no encontrado en {robots_url} (status: {response.status_code})")
                # Parser vacío permite todo por defecto
        except RequestException as e:
            logger.warning(f"Error accediendo a robots.txt: {str(e)}")
        
        return parser
    
    def _get_crawl_delay_from_parser(self, parser: RobotFileParser, user_agent: str) -> Optional[float]:
        """Extraer crawl delay del parser"""
        # RobotFileParser no expone crawl_delay directamente,
        # necesitamos parsear manualmente
        try:
            if hasattr(parser, 'entries'):
                for entry in parser.entries:
                    if entry.applies_to(user_agent):
                        if hasattr(entry, 'delay'):
                            return entry.delay
        except:
            pass
        
        return None
    
    def generate_scraping_policy(self, base_url: str) -> Dict[str, Any]:
        """
        Generar política completa de scraping para un sitio
        
        Args:
            base_url: URL base del sitio
        
        Returns:
            Diccionario con política de scraping recomendada
        """
        policy = {
            'base_url': base_url,
            'can_scrape': False,
            'crawl_delay': 3.0,
            'allowed_paths': [],
            'sitemaps': [],
            'rate_limits': {},
            'recommendations': []
        }
        
        # Verificar permisos básicos
        can_scrape, message = self.can_scrape_advanced(base_url)
        policy['can_scrape'] = can_scrape
        policy['permission_message'] = message
        
        if can_scrape:
            robots_url = urljoin(base_url, '/robots.txt')
            
            # Obtener crawl delay
            policy['crawl_delay'] = self.get_crawl_delay(robots_url)
            
            # Obtener rutas permitidas
            policy['allowed_paths'] = self.get_allowed_paths(base_url)
            
            # Obtener sitemaps
            policy['sitemaps'] = self.check_site_maps(robots_url)
            
            # Obtener rate limits
            policy['rate_limits'] = self.check_rate_limits(base_url)
            
            # Generar recomendaciones
            if policy['crawl_delay'] > 5:
                policy['recommendations'].append(
                    f"Usar delay largo de {policy['crawl_delay']}s entre requests"
                )
            
            if policy['rate_limits'].get('request_rate'):
                rate = policy['rate_limits']['request_rate']
                policy['recommendations'].append(
                    f"Limitar a {rate['requests']} requests cada {rate['seconds']} segundos"
                )
            
            if policy['rate_limits'].get('visit_time'):
                policy['recommendations'].append(
                    f"Preferir scraping en horario: {policy['rate_limits']['visit_time']}"
                )
            
            if policy['sitemaps']:
                policy['recommendations'].append(
                    "Usar sitemaps para descubrimiento eficiente de URLs"
                )
        
        return policy


# Funciones de utilidad para uso directo
def can_scrape_advanced(url: str, user_agent: str = '*') -> Tuple[bool, str]:
    """Wrapper para verificación rápida"""
    checker = RobotChecker()
    return checker.can_scrape_advanced(url, user_agent)


def get_crawl_delay(robots_url: str) -> float:
    """Wrapper para obtener crawl delay"""
    checker = RobotChecker()
    return checker.get_crawl_delay(robots_url)


def check_site_maps(robots_url: str) -> List[str]:
    """Wrapper para verificar sitemaps"""
    checker = RobotChecker()
    return checker.check_site_maps(robots_url)


if __name__ == "__main__":
    # Ejemplo de uso
    test_urls = [
        "https://www.dji.com/",
        "https://www.autelrobotics.com/",
        "https://www.parrot.com/"
    ]
    
    checker = RobotChecker()
    
    for url in test_urls:
        print(f"\n{'='*50}")
        print(f"Analizando: {url}")
        print(f"{'='*50}")
        
        policy = checker.generate_scraping_policy(url)
        
        print(f"¿Puede scrapear?: {policy['can_scrape']}")
        print(f"Mensaje: {policy['permission_message']}")
        print(f"Crawl delay: {policy['crawl_delay']}s")
        print(f"Rutas permitidas: {len(policy['allowed_paths'])}")
        print(f"Sitemaps: {len(policy['sitemaps'])}")
        
        if policy['recommendations']:
            print("\nRecomendaciones:")
            for rec in policy['recommendations']:
                print(f"  - {rec}")
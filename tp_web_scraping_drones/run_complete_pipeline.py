#!/usr/bin/env python3
"""
Script para ejecutar el pipeline completo del proyecto de web scraping de drones.
Incluye scraping, normalización y preparación de datos para la web.
"""

import sys
import os
import time
import logging
from pathlib import Path
import subprocess
import io

# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    # Configurar la salida estándar para UTF-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_command(cmd, description):
    """Ejecuta un comando y maneja errores."""
    logger.info(f"{'='*60}")
    logger.info(f"Ejecutando: {description}")
    logger.info(f"Comando: {cmd}")
    logger.info(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            logger.info("STDOUT:")
            logger.info(result.stdout)
        
        if result.stderr:
            logger.warning("STDERR:")
            logger.warning(result.stderr)
        
        if result.returncode != 0:
            logger.error(f"Error ejecutando {description}")
            return False
        
        # Usar caracteres ASCII compatibles en lugar de Unicode
        logger.info(f"[OK] {description} completado exitosamente\n")
        return True
        
    except Exception as e:
        logger.error(f"Excepción ejecutando {description}: {e}")
        return False

def main():
    """Ejecuta el pipeline completo."""
    logger.info("Iniciando pipeline completo de scraping de drones")
    
    # Cambiar al directorio del proyecto
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    logger.info(f"Directorio de trabajo: {os.getcwd()}")
    
    # Verificar que existen los directorios necesarios
    data_dir = Path("data")
    for subdir in ["raw", "interim", "processed", "images"]:
        (data_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    # Paso 1: Ejecutar el scraping
    logger.info("\n" + "="*60)
    logger.info("PASO 1: SCRAPING DE DATOS")
    logger.info("="*60)
    
    scraping_ok = run_command(
        "python -m scraping --parallel",
        "Scraping de drones desde sitios web"
    )
    
    if not scraping_ok:
        logger.error("El scraping falló. Abortando pipeline.")
        return 1
    
    # Esperar un momento para asegurar que los archivos se escriban
    time.sleep(2)
    
    # Verificar que se generó el archivo de datos
    normalized_file = Path("data/processed/drones_normalized.json")
    if not normalized_file.exists():
        logger.error(f"No se encontró el archivo {normalized_file}")
        return 1
    
    logger.info(f"[OK] Archivo de datos encontrado: {normalized_file}")
    
    # Paso 2: Normalizar datos para la web
    logger.info("\n" + "="*60)
    logger.info("PASO 2: NORMALIZACIÓN DE DATOS")
    logger.info("="*60)
    
    normalize_ok = run_command(
        "python normalize_data.py",
        "Normalización y limpieza de datos para presentación web"
    )
    
    if not normalize_ok:
        logger.warning("La normalización falló, pero continuando con datos originales...")
    
    # Verificar archivo normalizado
    web_ready_file = Path("data/processed/drones_web_ready.json")
    if web_ready_file.exists():
        logger.info(f"[OK] Archivo web-ready generado: {web_ready_file}")
    else:
        logger.warning("No se generó el archivo web-ready, la web usará datos originales")
    
    # Paso 3: Generar reporte de análisis
    logger.info("\n" + "="*60)
    logger.info("PASO 3: ANÁLISIS DE DATOS")
    logger.info("="*60)
    
    # Contar estadísticas
    import json
    
    try:
        data_file = web_ready_file if web_ready_file.exists() else normalized_file
        with open(data_file, 'r', encoding='utf-8') as f:
            drones = json.load(f)
        
        # Estadísticas
        marcas = {}
        categorias = {}
        specs_completas = 0
        
        for drone in drones:
            # Por marca
            marca = drone.get('marca', 'Unknown')
            marcas[marca] = marcas.get(marca, 0) + 1
            
            # Por categoría (si existe en datos normalizados)
            if 'categoria' in drone:
                cat = drone['categoria']
                categorias[cat] = categorias.get(cat, 0) + 1
            
            # Contar especificaciones completas
            specs = drone.get('especificaciones_tecnicas', {})
            if specs:
                valid_specs = sum(1 for v in specs.values() if v and v != 0 and v != "")
                if valid_specs >= 8:
                    specs_completas += 1
        
        logger.info("\n[RESUMEN DE DATOS EXTRAIDOS]:")
        logger.info(f"Total de drones: {len(drones)}")
        logger.info(f"Drones con especificaciones completas: {specs_completas}")
        
        logger.info("\nDrones por marca:")
        for marca, count in sorted(marcas.items()):
            logger.info(f"  - {marca}: {count}")
        
        if categorias:
            logger.info("\nDrones por categoría:")
            for cat, count in sorted(categorias.items()):
                logger.info(f"  - {cat}: {count}")
        
    except Exception as e:
        logger.error(f"Error analizando datos: {e}")
    
    # Paso 4: Preparar servidor web
    logger.info("\n" + "="*60)
    logger.info("PASO 4: PREPARACIÓN DEL SERVIDOR WEB")
    logger.info("="*60)
    
    logger.info("Para ver los resultados en la web:")
    logger.info("1. Abre una terminal en el directorio 'web'")
    logger.info("2. Ejecuta: python -m http.server 8000")
    logger.info("3. Abre tu navegador en: http://localhost:8000")
    logger.info("4. Abrir archivo index.html en el navegador")
    logger.info("\nAlternativamente, ejecuta: python web/serve_web.py")
    
    # Resumen final
    logger.info("\n" + "="*60)
    logger.info("[PIPELINE COMPLETADO EXITOSAMENTE]")
    logger.info("="*60)
    logger.info("\nArchivos generados:")
    
    for file in ["data/processed/drones_normalized.json", 
                 "data/processed/drones_web_ready.json",
                 "drone_scraper.log",
                 "pipeline.log"]:
        if Path(file).exists():
            size = Path(file).stat().st_size / 1024  # KB
            logger.info(f"  [OK] {file} ({size:.1f} KB)")
    
    logger.info("\nEl proyecto esta listo!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
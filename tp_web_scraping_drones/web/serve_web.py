#!/usr/bin/env python3
"""
Servidor web simple para servir la aplicación de drones.
Permite cargar dinámicamente los datos del JSON normalizado.
"""

import http.server
import socketserver
import os
import json
from pathlib import Path
import webbrowser
import threading
import time
import mimetypes

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # NO cambiar el directorio aquí, lo manejaremos diferente
        self.base_dir = Path(__file__).parent
        super().__init__(*args, **kwargs)
    
    def translate_path(self, path):
        """Traducir las rutas para servir archivos correctamente."""
        # Remover query strings
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        
        # Si es una ruta de datos, servir desde el directorio data
        if path.startswith('/data/'):
            file_path = self.base_dir / path[1:]  # Remover el / inicial
            return str(file_path)
        else:
            # Para otros archivos, servir desde web
            file_path = self.base_dir / 'web' / path.lstrip('/')
            return str(file_path)
    
    def end_headers(self):
        # Agregar headers CORS para permitir fetch desde el frontend
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        # Manejar rutas especiales
        if self.path == '/api/drones':
            self.serve_drone_data()
        else:
            # Usar el método estándar para servir archivos
            super().do_GET()
    
    def guess_type(self, path):
        """Mejorar la detección de tipos MIME."""
        mime_type, _ = mimetypes.guess_type(path)
        if mime_type:
            return mime_type
        
        # Tipos adicionales
        ext = Path(path).suffix.lower()
        mime_types = {
            '.json': 'application/json',
            '.js': 'application/javascript',
            '.css': 'text/css',
            '.html': 'text/html',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.csv': 'text/csv',
        }
        return mime_types.get(ext, 'application/octet-stream')
    
    def serve_drone_data(self):
        """Servir datos de drones desde el JSON normalizado."""
        try:
            data_path = self.base_dir / "data/processed/drones_web_ready.json"
            if not data_path.exists():
                data_path = self.base_dir / "data/processed/drones_normalized.json"
                
            if data_path.exists():
                with open(data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                
                response = {
                    "status": "success",
                    "count": len(data),
                    "data": data
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_error(404, "Drone data not found")
        except Exception as e:
            self.send_error(500, f"Error loading drone data: {str(e)}")

def start_server(port=8000):
    """Iniciar el servidor web."""
    try:
        # Cambiar al directorio del proyecto
        os.chdir(Path(__file__).parent)
        
        # Verificar que existen los archivos necesarios
        web_dir = Path("web")
        data_file = Path("data/processed/drones_web_ready.json")
        if not data_file.exists():
            data_file = Path("data/processed/drones_normalized.json")
        
        if not web_dir.exists():
            print("❌ Error: Directorio 'web' no encontrado")
            return False
        
        if not data_file.exists():
            print("⚠️  Advertencia: Archivo de datos no encontrado, usando datos de fallback")
        
        # Crear el servidor
        with socketserver.TCPServer(("", port), CustomHTTPRequestHandler) as httpd:
            print(f"🚀 Servidor iniciado en http://localhost:{port}")
            print(f"📁 Sirviendo archivos desde: {web_dir.absolute()}")
            print(f"📊 Datos desde: {data_file.absolute()}")
            print("\n📋 Rutas disponibles:")
            print(f"   • http://localhost:{port}/           - Aplicación web")
            print(f"   • http://localhost:{port}/api/drones - API de datos")
            print(f"   • http://localhost:{port}/data/processed/drones_web_ready.json - JSON directo")
            print(f"   • http://localhost:{port}/data/images/ - Imágenes de drones")
            print("\n💡 Presiona Ctrl+C para detener el servidor")
            
            # Abrir el navegador automáticamente
            def open_browser():
                time.sleep(1)
                try:
                    webbrowser.open(f'http://localhost:{port}')
                    print(f"🌐 Abriendo navegador en http://localhost:{port}")
                except:
                    pass
            
            threading.Thread(target=open_browser, daemon=True).start()
            
            # Iniciar el servidor
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n\n👋 Servidor detenido")
        return True
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"❌ Error: El puerto {port} ya está en uso")
            print(f"💡 Prueba con otro puerto: python serve_web.py --port {port + 1}")
        else:
            print(f"❌ Error del sistema: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def main():
    """Punto de entrada principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Servidor web para la aplicación de drones')
    parser.add_argument('--port', type=int, default=8000, 
                       help='Puerto para el servidor (default: 8000)')
    parser.add_argument('--no-browser', action='store_true',
                       help='No abrir el navegador automáticamente')
    
    args = parser.parse_args()
    
    print("🚁 Iniciando servidor para la aplicación de drones...")
    start_server(args.port)

if __name__ == "__main__":
    main() 
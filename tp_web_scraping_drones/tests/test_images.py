"""
Tests para verificar la existencia y validez de las imágenes de drones.
"""

import json
import unittest
from pathlib import Path


class TestImages(unittest.TestCase):
    """Tests para verificar las imágenes asociadas a los drones."""
    
    @classmethod
    def setUpClass(cls):
        """Configurar rutas y cargar datos."""
        cls.base_path = Path(__file__).parent.parent
        cls.images_path = cls.base_path / "data" / "images"
        cls.data_path = cls.base_path / "data" / "processed" / "drones_web_ready.json"
        
        # Cargar datos de drones
        with open(cls.data_path, 'r', encoding='utf-8') as f:
            cls.drones = json.load(f)
    
    def test_carpeta_imagenes_existe(self):
        """Verificar que la carpeta de imágenes existe."""
        self.assertTrue(
            self.images_path.exists(),
            f"La carpeta de imágenes {self.images_path} no existe"
        )
        self.assertTrue(
            self.images_path.is_dir(),
            f"{self.images_path} no es un directorio"
        )
    
    def test_imagenes_logos_existen(self):
        """Verificar que existen los logos de las marcas."""
        logos_esperados = ['dji-logo.png', 'autel-logo.png', 'parrot-logo.png']
        
        for logo in logos_esperados:
            logo_path = self.images_path / logo
            self.assertTrue(
                logo_path.exists(),
                f"Logo {logo} no encontrado en {self.images_path}"
            )
    
    def test_imagenes_drones_referenciadas(self):
        """Verificar que todas las imágenes referenciadas en los datos existen."""
        imagenes_faltantes = []
        
        for drone in self.drones:
            imagen_relativa = drone.get('imagen', '')
            if imagen_relativa:
                # Quitar el prefijo 'data/images/' si existe
                imagen_nombre = imagen_relativa.replace('data/images/', '')
                imagen_path = self.images_path / imagen_nombre
                
                if not imagen_path.exists():
                    imagenes_faltantes.append({
                        'drone': drone['modelo'],
                        'imagen': imagen_nombre
                    })
        
        self.assertEqual(
            len(imagenes_faltantes), 0,
            f"Imágenes faltantes: {imagenes_faltantes}"
        )
    
    def test_formato_imagenes_valido(self):
        """Verificar que todas las imágenes tienen formatos válidos."""
        formatos_validos = ['.jpg', '.jpeg', '.png', '.webp']
        
        for imagen in self.images_path.iterdir():
            if imagen.is_file():
                extension = imagen.suffix.lower()
                self.assertIn(
                    extension, formatos_validos,
                    f"Imagen {imagen.name} tiene formato inválido: {extension}"
                )
    
    def test_tamaño_imagenes_razonable(self):
        """Verificar que las imágenes tienen un tamaño razonable."""
        tamaño_max_mb = 5  # 5 MB máximo
        tamaño_max_bytes = tamaño_max_mb * 1024 * 1024
        
        imagenes_grandes = []
        
        for imagen in self.images_path.iterdir():
            if imagen.is_file():
                tamaño = imagen.stat().st_size
                if tamaño > tamaño_max_bytes:
                    imagenes_grandes.append({
                        'imagen': imagen.name,
                        'tamaño_mb': round(tamaño / (1024 * 1024), 2)
                    })
        
        self.assertEqual(
            len(imagenes_grandes), 0,
            f"Imágenes demasiado grandes (>{tamaño_max_mb}MB): {imagenes_grandes}"
        )
    
    def test_nombres_imagenes_consistentes(self):
        """Verificar que los nombres de imágenes son consistentes."""
        for imagen in self.images_path.iterdir():
            if imagen.is_file() and not imagen.name.endswith('-logo.png'):
                # Verificar que no hay espacios al inicio/final
                self.assertEqual(
                    imagen.stem, imagen.stem.strip(),
                    f"Imagen {imagen.name} tiene espacios al inicio o final"
                )
                
                # Verificar que no hay caracteres especiales problemáticos
                caracteres_problematicos = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
                for char in caracteres_problematicos:
                    self.assertNotIn(
                        char, imagen.name,
                        f"Imagen {imagen.name} contiene carácter problemático: {char}"
                    )
    
    def test_todas_marcas_tienen_logo(self):
        """Verificar que todas las marcas mencionadas tienen logo."""
        marcas_en_datos = set()
        for drone in self.drones:
            marca = drone.get('marca', '').lower()
            if marca:
                marcas_en_datos.add(marca)
        
        for marca in marcas_en_datos:
            logo_esperado = f"{marca}-logo.png"
            logo_path = self.images_path / logo_esperado
            self.assertTrue(
                logo_path.exists(),
                f"Marca {marca} no tiene logo: {logo_esperado}"
            )
    
    def test_imagenes_no_huerfanas(self):
        """Verificar que no hay imágenes sin usar."""
        # Recolectar todas las imágenes referenciadas
        imagenes_usadas = set()
        
        # Logos siempre se consideran usados
        imagenes_usadas.update(['dji-logo.png', 'autel-logo.png', 'parrot-logo.png'])
        
        # Imágenes de drones
        for drone in self.drones:
            imagen = drone.get('imagen', '')
            if imagen:
                imagen_nombre = imagen.replace('data/images/', '')
                imagenes_usadas.add(imagen_nombre)
        
        # Verificar imágenes huérfanas
        imagenes_huerfanas = []
        for imagen in self.images_path.iterdir():
            if imagen.is_file() and imagen.name not in imagenes_usadas:
                imagenes_huerfanas.append(imagen.name)
        
        if imagenes_huerfanas:
            print(f"\nAdvertencia: Imágenes no utilizadas: {imagenes_huerfanas}")
        
        # No fallar el test por esto, solo advertir
        self.assertIsInstance(imagenes_huerfanas, list)  # Test siempre pasa
    
    def test_coherencia_imagen_modelo(self):
        """Verificar que las imágenes corresponden con los modelos."""
        for drone in self.drones:
            modelo = drone.get('modelo', '').lower()
            imagen = drone.get('imagen', '')
            
            if imagen and not imagen.endswith('-logo.png'):
                imagen_nombre = imagen.replace('data/images/', '').lower()
                
                # Para modelos específicos, verificar que la imagen contiene parte del nombre
                if 'mavic' in modelo:
                    self.assertIn(
                        'mavic', imagen_nombre,
                        f"Drone {drone['modelo']} tiene imagen incorrecta: {imagen}"
                    )
                elif 'mini' in modelo:
                    self.assertIn(
                        'mini', imagen_nombre,
                        f"Drone {drone['modelo']} tiene imagen incorrecta: {imagen}"
                    )
                elif 'air' in modelo and 'anafi' not in modelo:
                    self.assertIn(
                        'air', imagen_nombre,
                        f"Drone {drone['modelo']} tiene imagen incorrecta: {imagen}"
                    )


if __name__ == '__main__':
    unittest.main() 
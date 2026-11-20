"""
Consulta automatizada de RETHUS - Registro Único Nacional de Talento Humano en Salud
https://web.sispro.gov.co/THS/Cliente/ConsultasPublicas/ConsultaPublicaDeTHxIdentificacion.aspx

Este script automatiza la consulta de registros en RETHUS para múltiples usuarios,
resolviendo el CAPTCHA con IA y guardando los resultados como PDF.
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    NoSuchWindowException, TimeoutException, 
    NoSuchElementException, StaleElementReferenceException
)
import logging
import time
import os
import base64
from dotenv import load_dotenv
from pathlib import Path

from captcha_solver import solve_captcha, capture_captcha_image

# --- Configuración Básica ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

# URL de la página de consulta RETHUS
RETHUS_URL = "https://web.sispro.gov.co/THS/Cliente/ConsultasPublicas/ConsultaPublicaDeTHxIdentificacion.aspx"

# Configuración del PDF - Ajustado según tus especificaciones
PDF_CONFIG = {
    'landscape': False,
    'displayHeaderFooter': False,
    'printBackground': True,  # True para capturar tablas correctamente
    'scale': 0.84,  # Escala 84%
    'paperWidth': 8.5,  # Letter width in inches
    'paperHeight': 11,  # Letter height in inches
    'marginTop': 1.34,  # ~34mm
    'marginBottom': 0.16,  # ~4mm  
    'marginLeft': 0.12,  # ~3mm
    'marginRight': 0.12,  # ~3mm
    'pageRanges': '2',  # Solo página 2
    'preferCSSPageSize': False,
}


def limpiar_cedula(cedula):
    """Elimina puntos y espacios de la cédula."""
    return cedula.replace('.', '').replace(' ', '').strip()


def cargar_usuarios(archivo="usuarios.txt"):
    """
    Carga la lista de usuarios desde el archivo TXT.
    
    Formato esperado: cedula,nombre,apellido
    
    Returns:
        list: Lista de diccionarios con cedula, nombre, apellido
    """
    usuarios = []
    base_dir = Path(__file__).resolve().parent
    archivo_path = Path(archivo)
    if not archivo_path.is_absolute():
        archivo_path = base_dir / archivo_path

    try:
        with open(archivo_path, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea:
                    continue
                    
                # Dividir SOLO por coma (no por tab)
                partes = linea.split(',')
                if len(partes) >= 3:
                    cedula = limpiar_cedula(partes[0])
                    # El nombre puede tener tabs o espacios extra, limpiarlos
                    nombre = partes[1].strip().replace('\t', ' ').replace('  ', ' ')
                    apellido = partes[2].strip()
                    
                    usuarios.append({
                        'cedula': cedula,
                        'nombre': nombre,
                        'apellido': apellido
                    })
                    
        logging.info(f"Se cargaron {len(usuarios)} usuarios desde {archivo_path}")
        return usuarios
        
    except FileNotFoundError:
        logging.error(f"No se encontró el archivo {archivo_path}")
        return []
    except Exception as e:
        logging.error(f"Error al cargar usuarios: {e}")
        return []


def save_result_as_pdf(driver, apellido, nombre, output_dir="rethus"):
    """
    Guarda la página de resultados como PDF.
    
    El nombre del archivo será: "- APELLIDO NOMBRE.pdf"
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Formato del nombre: "- APELLIDO NOMBRE.pdf"
        filename = f"- {apellido} {nombre}.pdf"
        filepath = os.path.join(output_dir, filename)
        
        # Generar PDF con la configuración específica
        result = driver.execute_cdp_cmd('Page.printToPDF', PDF_CONFIG)
        pdf_data = base64.b64decode(result['data'])
        
        with open(filepath, 'wb') as f:
            f.write(pdf_data)
        
        logging.info(f"✅ PDF guardado: {filepath}")
        return True
        
    except Exception as e:
        logging.error(f"❌ Error al guardar PDF: {e}")
        return False


def is_driver_alive(driver):
    """Verifica si el driver está activo."""
    try:
        return driver is not None and driver.session_id and driver.title is not None
    except Exception:
        return False


def create_driver(headless=False):
    """Crea una nueva instancia del navegador."""
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-gpu')
    
    if headless:
        options.add_argument('--headless=new')
    
    # Configuración para permitir impresión a PDF
    prefs = {
        'printing.print_preview_sticky_settings.appState': '{"recentDestinations":[{"id":"Save as PDF","origin":"local"}],"selectedDestinationId":"Save as PDF","version":2}',
        'savefile.default_directory': os.path.abspath('rethus')
    }
    options.add_experimental_option('prefs', prefs)
    
    return uc.Chrome(options=options)


def resolver_captcha_con_ia(driver, wait, max_intentos=3):
    """
    Captura y resuelve el CAPTCHA numérico usando IA.
    
    Returns:
        str: El código del CAPTCHA resuelto
    """
    for intento in range(max_intentos):
        try:
            logging.info(f"Intento {intento + 1} de resolver CAPTCHA...")
            
            # Esperar a que la imagen del CAPTCHA esté presente
            # Buscar la imagen del CAPTCHA (es un img dentro del formulario)
            captcha_img = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "img[id*='imgCaptcha'], img[src*='Captcha'], #ctl00_cntContenido_imgCaptcha")
            ))
            
            # Si no encuentra con ese selector, intentar alternativas
            if not captcha_img:
                # Buscar cualquier imagen cerca del campo de confirmación
                captcha_img = driver.find_element(By.XPATH, 
                    "//div[contains(text(), 'Confirme los números')]//following::img[1]")
            
            time.sleep(0.5)  # Pequeña pausa para que cargue completamente
            
            # Capturar la imagen
            image_bytes = capture_captcha_image(driver, captcha_img)
            
            # Resolver con IA
            captcha_code = solve_captcha(image_bytes)
            
            if captcha_code and len(captcha_code) >= 3:
                logging.info(f"CAPTCHA resuelto: {captcha_code}")
                return captcha_code
            else:
                logging.warning(f"Respuesta de CAPTCHA inválida: {captcha_code}")
                # Hacer clic en "Cambiar" para obtener nuevo CAPTCHA
                try:
                    cambiar_btn = driver.find_element(By.LINK_TEXT, "Cambiar")
                    cambiar_btn.click()
                    time.sleep(1)
                except:
                    pass
                    
        except Exception as e:
            logging.error(f"Error al resolver CAPTCHA en intento {intento + 1}: {e}")
            time.sleep(1)
    
    return None


def consultar_usuario(driver, wait, usuario, es_primera_consulta=True):
    """
    Realiza la consulta de un usuario en RETHUS.
    
    Args:
        driver: Instancia del navegador
        wait: WebDriverWait
        usuario: Diccionario con cedula, nombre, apellido
        es_primera_consulta: Si es True, navega a la URL; si es False, usa "Limpiar"
        
    Returns:
        bool: True si fue exitoso, False si falló
    """
    cedula = usuario['cedula']
    nombre = usuario['nombre']
    apellido = usuario['apellido']
    
    logging.info(f"\n{'='*60}")
    logging.info(f"Consultando: {nombre} {apellido} - CC: {cedula}")
    logging.info(f"{'='*60}")
    
    try:
        # Siempre recargar la página para empezar limpio (evita acumulación de registros)
        driver.get(RETHUS_URL)
        time.sleep(2)
        
        # 1. Seleccionar Tipo de Identificación: "Cedula de Ciudadania"
        tipo_id_select = wait.until(EC.presence_of_element_located(
            (By.ID, "ctl00_cntContenido_ddlTipoIdentificacion")
        ))
        select = Select(tipo_id_select)
        select.select_by_visible_text("Cedula de Ciudadania")
        time.sleep(0.5)
        
        # 2. Ingresar Número de Identificación
        cedula_input = wait.until(EC.visibility_of_element_located(
            (By.ID, "ctl00_cntContenido_txtNumeroIdentificacion")
        ))
        cedula_input.clear()
        cedula_input.send_keys(cedula)
        
        # 3. Resolver CAPTCHA con IA
        captcha_code = resolver_captcha_con_ia(driver, wait)
        
        if not captcha_code:
            # Modo manual si la IA falla
            captcha_code = input(
                f"\n❗ No se pudo resolver el CAPTCHA automáticamente.\n"
                f"   Por favor, ingresa los números que ves en la imagen: "
            ).strip()
        
        # Ingresar el código del CAPTCHA
        captcha_input = driver.find_element(By.ID, "ctl00_cntContenido_txtCatpchaConfirmation")
        captcha_input.clear()
        captcha_input.send_keys(captcha_code)
        
        # 4. Click en "Verificar Registro en ReTHUS"
        verificar_btn = wait.until(EC.element_to_be_clickable(
            (By.ID, "ctl00_cntContenido_btnVerificarIdentificacion")
        ))
        verificar_btn.click()
        
        # 5. Esperar resultados y buscar el enlace "Ver" en la tabla
        time.sleep(3)
        
        # Verificar si hay error de CAPTCHA
        try:
            error_element = driver.find_element(By.CSS_SELECTOR, ".error, .validation-error, [style*='color: red']")
            if "captcha" in error_element.text.lower() or "imagen" in error_element.text.lower():
                logging.warning("CAPTCHA incorrecto, reintentando...")
                return consultar_usuario(driver, wait, usuario, es_primera_consulta=False)
        except NoSuchElementException:
            pass  # No hay error, continuar
        
        # 6. Buscar y hacer clic en "Ver" detalles
        ver_link = wait.until(EC.element_to_be_clickable(
            (By.LINK_TEXT, "Ver")
        ))
        ver_link.click()
        
        # 7. Esperar a que cargue la información detallada
        time.sleep(3)
        
        # 8. Ocultar cabecera (header) para que empiece desde ReTHUS
        driver.execute_script("""
            // Ocultar header de GOV.CO y menú
            var header = document.querySelector('header');
            if (header) header.style.display = 'none';
            
            // Ocultar barra de navegación superior
            var navbars = document.querySelectorAll('nav, .navbar, .nav, [class*="header"], [class*="Header"], [id*="header"], [id*="Header"]');
            navbars.forEach(function(el) { el.style.display = 'none'; });
            
            // Ocultar elementos específicos de GOV.CO
            var govElements = document.querySelectorAll('[class*="gov"], [class*="Gov"], [class*="GOV"], .barra-superior, #barra-superior');
            govElements.forEach(function(el) { el.style.display = 'none'; });
            
            // Ocultar menú y botones de sesión
            var menuElements = document.querySelectorAll('[class*="menu"], [class*="Menu"], .btn-sesion, [class*="sesion"], [class*="Sesion"]');
            menuElements.forEach(function(el) { el.style.display = 'none'; });
        """)
        
        # 9. Aplicar estilos de impresión para tablas más limpias (gris en lugar de colores)
        driver.execute_script("""
            var style = document.createElement('style');
            style.id = 'print-styles';
            style.innerHTML = `
                /* Cambiar colores de tablas a gris para impresión más limpia */
                table th, table td[style*="background"], 
                .table th, .table td,
                th[style], td[style*="background"],
                tr[style*="background"], tr th {
                    background-color: #808080 !important;
                    background: #808080 !important;
                }
                /* Texto en celdas con fondo gris debe ser blanco */
                table th, tr th, thead th, thead td {
                    color: #ffffff !important;
                }
                /* Celdas de datos normales */
                table td, tbody td {
                    background-color: #ffffff !important;
                    background: #ffffff !important;
                    color: #000000 !important;
                }
                /* Encabezados de sección */
                [style*="background-color: rgb(128"], 
                [style*="background-color: rgb(139"],
                [style*="background-color: rgb(165"],
                [style*="background-color:#8"],
                [style*="background: rgb(128"],
                [style*="background: rgb(139"],
                [style*="background: rgb(165"] {
                    background-color: #808080 !important;
                    background: #808080 !important;
                }
            `;
            document.head.appendChild(style);
        """)
        
        # 10. Guardar como PDF (mantiene texto seleccionable y tabla en gris)
        success = save_result_as_pdf(driver, apellido, nombre)
        
        if success:
            logging.info(f"✅ Consulta completada para {nombre} {apellido}")
        
        return success
        
    except TimeoutException as e:
        logging.error(f"⏱️ Timeout esperando elemento: {e}")
        save_error_screenshot(driver, cedula)
        return False
        
    except Exception as e:
        logging.error(f"❌ Error en consulta: {e}")
        save_error_screenshot(driver, cedula)
        return False


def save_error_screenshot(driver, identificador):
    """Guarda una captura de pantalla en caso de error."""
    try:
        error_dir = "errors"
        os.makedirs(error_dir, exist_ok=True)
        filepath = os.path.join(error_dir, f"error_{identificador}_{int(time.time())}.png")
        driver.save_screenshot(filepath)
        logging.info(f"📸 Captura de error guardada: {filepath}")
    except Exception as e:
        logging.error(f"No se pudo guardar captura de error: {e}")


def main():
    """Función principal que procesa todos los usuarios."""
    print("\n" + "="*60)
    print("  CONSULTA AUTOMATIZADA RETHUS - SISPRO")
    print("  Registro Único Nacional de Talento Humano en Salud")
    print("="*60 + "\n")
    
    # Cargar usuarios
    usuarios = cargar_usuarios()
    
    if not usuarios:
        print("❌ No se encontraron usuarios para consultar.")
        print("   Asegúrate de que el archivo 'usuarios.txt' exista y tenga el formato correcto.")
        print("   Formato: cedula,nombre,apellido")
        return
    
    print(f"📋 Se procesarán {len(usuarios)} usuarios\n")
    
    # Preguntar si usar modo headless
    headless_env = os.getenv('HEADLESS_MODE', 'false').lower()
    headless = headless_env == 'true'
    
    if not headless:
        respuesta = input("¿Ejecutar en modo visible (recomendado para primera vez)? [S/n]: ").strip().lower()
        headless = respuesta == 'n'
    
    driver = None
    exitosos = 0
    fallidos = 0
    
    try:
        driver = create_driver(headless=headless)
        wait = WebDriverWait(driver, int(os.getenv('TIMEOUT', 30)))
        
        for i, usuario in enumerate(usuarios):
            es_primera = (i == 0)
            
            try:
                if consultar_usuario(driver, wait, usuario, es_primera_consulta=es_primera):
                    exitosos += 1
                else:
                    fallidos += 1
            except Exception as e:
                logging.error(f"Error procesando usuario {usuario['cedula']}: {e}")
                fallidos += 1
                
                # Intentar recuperar el driver
                if not is_driver_alive(driver):
                    logging.info("Reiniciando navegador...")
                    try:
                        driver.quit()
                    except:
                        pass
                    driver = create_driver(headless=headless)
                    wait = WebDriverWait(driver, int(os.getenv('TIMEOUT', 30)))
            
            # Pequeña pausa entre consultas
            if i < len(usuarios) - 1:
                time.sleep(2)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Proceso interrumpido por el usuario")
        
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
    
    # Resumen final
    print("\n" + "="*60)
    print("  RESUMEN DE CONSULTAS")
    print("="*60)
    print(f"  ✅ Exitosos: {exitosos}")
    print(f"  ❌ Fallidos: {fallidos}")
    print(f"  📁 PDFs guardados en: ./rethus/")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

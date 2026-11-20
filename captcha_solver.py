"""
Módulo para resolver CAPTCHA numérico usando IA (Gemini o OpenAI GPT-4 Vision)
"""
import os
import base64
import logging
import re
from io import BytesIO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def image_to_base64(image_bytes):
    """Convierte bytes de imagen a base64."""
    return base64.b64encode(image_bytes).decode('utf-8')


def extract_numbers_from_text(text):
    """Extrae solo los dígitos de un texto."""
    numbers = re.findall(r'\d+', text)
    return ''.join(numbers)


def solve_captcha_with_gemini(image_bytes, api_key):
    """
    Resuelve el CAPTCHA usando Google Gemini Vision.
    
    Args:
        image_bytes: Bytes de la imagen del CAPTCHA
        api_key: API key de Google Gemini
        
    Returns:
        str: Los números del CAPTCHA
    """
    try:
        import google.generativeai as genai
        from PIL import Image
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Convertir bytes a imagen PIL
        image = Image.open(BytesIO(image_bytes))
        
        prompt = """Analiza esta imagen de CAPTCHA y extrae ÚNICAMENTE los números que ves.
        Responde SOLO con los dígitos, sin espacios, sin texto adicional, sin explicaciones.
        Por ejemplo, si ves "7829", responde exactamente: 7829"""
        
        response = model.generate_content([prompt, image])
        result = extract_numbers_from_text(response.text)
        
        logging.info(f"Gemini detectó el CAPTCHA: {result}")
        return result
        
    except Exception as e:
        logging.error(f"Error con Gemini: {e}")
        raise


def solve_captcha_with_openai(image_bytes, api_key):
    """
    Resuelve el CAPTCHA usando OpenAI GPT-4 Vision.
    
    Args:
        image_bytes: Bytes de la imagen del CAPTCHA
        api_key: API key de OpenAI
        
    Returns:
        str: Los números del CAPTCHA
    """
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        base64_image = image_to_base64(image_bytes)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Más económico que gpt-4-vision
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analiza esta imagen de CAPTCHA y extrae ÚNICAMENTE los números que ves. Responde SOLO con los dígitos, sin espacios, sin texto adicional. Por ejemplo: 7829"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=20
        )
        
        result = extract_numbers_from_text(response.choices[0].message.content)
        logging.info(f"OpenAI detectó el CAPTCHA: {result}")
        return result
        
    except Exception as e:
        logging.error(f"Error con OpenAI: {e}")
        raise


def solve_captcha(image_bytes):
    """
    Resuelve el CAPTCHA usando la IA configurada en las variables de entorno.
    Primero intenta con Gemini, luego con OpenAI.
    
    Args:
        image_bytes: Bytes de la imagen del CAPTCHA
        
    Returns:
        str: Los números del CAPTCHA
    """
    gemini_key = os.getenv('GEMINI_API_KEY', '')
    openai_key = os.getenv('OPENAI_API_KEY', '')
    
    # Intentar con Gemini primero (tiene capa gratuita)
    if gemini_key and 'tu_api_key' not in gemini_key.lower():
        try:
            return solve_captcha_with_gemini(image_bytes, gemini_key)
        except Exception as e:
            logging.warning(f"Gemini falló, intentando con OpenAI: {e}")
    
    # Intentar con OpenAI
    if openai_key and 'tu_api_key' not in openai_key.lower():
        try:
            return solve_captcha_with_openai(image_bytes, openai_key)
        except Exception as e:
            logging.warning(f"OpenAI también falló: {e}")
    
    # Si ninguna IA está configurada o funcionó
    raise Exception(
        "No se pudo resolver el CAPTCHA automáticamente. "
        "Configura GEMINI_API_KEY o OPENAI_API_KEY en el archivo .env"
    )


def capture_captcha_image(driver, captcha_element):
    """
    Captura la imagen del CAPTCHA desde el elemento web.
    
    Args:
        driver: Instancia de Selenium WebDriver
        captcha_element: Elemento web que contiene la imagen del CAPTCHA
        
    Returns:
        bytes: Bytes de la imagen
    """
    # Obtener screenshot del elemento
    return captcha_element.screenshot_as_png

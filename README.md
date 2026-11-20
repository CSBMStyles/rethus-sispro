# Consulta Automatizada RETHUS - SISPRO

## 📋 Descripción

Este proyecto automatiza la consulta del **Registro Único Nacional de Talento Humano en Salud (RETHUS)** en el portal SISPRO de Colombia.

**URL del portal:** https://web.sispro.gov.co/THS/Cliente/ConsultasPublicas/ConsultaPublicaDeTHxIdentificacion.aspx

## 🚀 Características

- ✅ Consulta automatizada de múltiples usuarios
- ✅ Resolución de CAPTCHA numérico usando **IA** (Google Gemini o OpenAI)
- ✅ Guardado automático como PDF con configuración personalizada
- ✅ Uso del botón "Limpiar" para consultas consecutivas (sin recargar página)
- ✅ Manejo de errores y reintentos automáticos
- ✅ Modo visible o headless (sin interfaz)

## 📁 Estructura del Proyecto

```
rethus-sispro/
├── main.py                  # Script principal
├── captcha_solver.py        # Módulo para resolver CAPTCHA con IA
├── usuarios.example.txt     # Ejemplo; cópialo a usuarios.txt
├── requirements.txt         # Dependencias de Python
├── env.example              # Ejemplo de configuración
├── .env                     # Créalo desde env.example (no incluido)
├── rethus/                  # Se crea al ejecutar (no incluido)
└── errors/                  # Se crea al ejecutar (no incluido)
```

## 🔧 Instalación

### 1. Clonar o copiar el proyecto

### 2. Crear entorno virtual (recomendado)
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# o
source venv/bin/activate  # Linux/Mac
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
# Copiar el archivo de ejemplo
copy env.example .env  # Windows
# o
cp env.example .env    # Linux/Mac
```

### 5. Configurar API Key de IA

Edita el archivo `.env` y configura **UNA** de las siguientes opciones:

#### Opción 1: Google Gemini (RECOMENDADO - tiene capa gratuita)
1. Ve a https://makersuite.google.com/app/apikey
2. Crea una API Key
3. Copia la key en el archivo `.env`:
```
GEMINI_API_KEY=tu_api_key_aqui
```

#### Opción 2: OpenAI GPT-4 Vision
1. Ve a https://platform.openai.com/api-keys
2. Crea una API Key
3. Copia la key en el archivo `.env`:
```
OPENAI_API_KEY=tu_api_key_aqui
```

## 📝 Formato del archivo usuarios.txt

El archivo debe tener el siguiente formato (separado por comas):

```
cedula,nombre,apellido
```

**Ejemplo:**
```
1000000001,PEREZ GOMEZ,ANA MARIA
1000000002,RODRIGUEZ LOPEZ,CARLOS ANDRES
1000000003,MARTINEZ RUEDA,LAURA SOFIA
```

**Notas:**
- Los puntos en la cédula se eliminan automáticamente
- Se permiten tabs como separador adicional
- El nombre del PDF será: `- APELLIDO NOMBRE.pdf`

## ▶️ Ejecución

```bash
python main.py
```

El script:
1. Cargará los usuarios desde `usuarios.txt`
2. Abrirá el navegador Chrome
3. Para cada usuario:
   - Seleccionará "Cédula de Ciudadanía"
   - Ingresará el número de cédula
   - Resolverá el CAPTCHA usando IA
   - Hará clic en "Verificar Registro en ReTHUS"
   - Hará clic en "Ver" para ver los detalles
   - Guardará el PDF en la carpeta `rethus/`
   - Usará el botón "Limpiar" para la siguiente consulta

## ⚙️ Configuración del PDF

El PDF se genera con las siguientes especificaciones:
- **Página:** Solo página 2
- **Escala:** 84%
- **Márgenes:** 3mm en todos los lados
- **Orientación:** Vertical
- **Nombre:** `- APELLIDO NOMBRE.pdf`

## 🔍 Flujo del Proceso

```
┌─────────────────────────────────────────────────────────────┐
│  1. Cargar usuarios desde usuarios.txt                       │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Abrir navegador y cargar página RETHUS                   │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Para cada usuario:                                       │
│     a. Seleccionar tipo de identificación                    │
│     b. Ingresar número de cédula                             │
│     c. Capturar imagen CAPTCHA                               │
│     d. Enviar a IA (Gemini/OpenAI) para resolver            │
│     e. Ingresar código CAPTCHA                               │
│     f. Clic en "Verificar Registro en ReTHUS"               │
│     g. Clic en "Ver" (columna Detalles)                     │
│     h. Guardar página como PDF                               │
│     i. Clic en "Limpiar" para siguiente consulta            │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Mostrar resumen de consultas exitosas/fallidas          │
└─────────────────────────────────────────────────────────────┘
```

## ❗ Solución de Problemas

### El CAPTCHA no se resuelve correctamente
- Verifica que tu API Key esté configurada correctamente
- Si usas Gemini, verifica que tengas cuota disponible
- El script pedirá entrada manual si la IA falla

### El navegador se cierra inesperadamente
- Asegúrate de tener Chrome instalado y actualizado
- Prueba ejecutando en modo visible (no headless)

### No encuentra elementos en la página
- La página de SISPRO puede haber cambiado su estructura
- Revisa las capturas de error en la carpeta `errors/`
- Actualiza los selectores CSS/IDs si es necesario

## 📋 Selectores de la Página (referencia)

| Elemento | ID/Selector |
|----------|-------------|
| Tipo Identificación | `ctl00_cntContenido_ddlTipoIdentificacion` |
| Número Identificación | `ctl00_cntContenido_txtNumeroIdentificacion` |
| Campo CAPTCHA | `ctl00_cntContenido_txtCaptcha` |
| Imagen CAPTCHA | `ctl00_cntContenido_imgCaptcha` |
| Botón Verificar | `ctl00_cntContenido_btnVerificarIdentificacion` |
| Botón Limpiar | `ctl00_cntContenido_btnLimpiar` |
| Enlace Ver | Link text: "Ver" |

## Autor

Automatización de consultas públicas con fines autorizados.

---

## Datos y privacidad

Este repositorio contiene únicamente código y documentación. **No incluye**:

- API keys ni archivos `.env`.
- Bases de datos de empleados, cédulas, nombres, correos o teléfonos.
- PDFs, Excel, PPTX, CSV, capturas o reportes generados por las consultas.
- Configuraciones locales (`config.json`) ni estados de proceso.

Para usarlo, proporciona tu propia base de datos autorizada y configura tus
propias credenciales. No subas datos personales al repositorio.

## Licencia

MIT. Consulta el archivo `LICENSE`.


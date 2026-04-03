# Reglas de Estilo Python

## Estándares de Código

- Sigue PEP 8 en todo momento
- Usa type hints en todas las funciones
- Docstrings en funciones públicas (una línea es suficiente si el nombre es claro)
- Máximo 80 caracteres por línea
- Nombres de variables y funciones en snake_case, clases en PascalCase

## Manejo de Errores

- Usa try/except en toda llamada a la API de Gemini
- Usa try/except en toda ejecución de SQL en DuckDB
- Los mensajes de error deben ser descriptivos y útiles para el modelo (el bot
  los recibe y debe poder reintentar con esa información)
- Nunca silencies un error con `except: pass`

## Imports

- Agrupa imports: stdlib → third-party → locales, separados por línea en blanco
- Siempre incluye todos los imports en el archivo, no asumir que están disponibles

## Variables de Entorno

- Toda API key o configuración sensible va en `.env`
- Usa `python-dotenv` para cargarlas: `from dotenv import load_dotenv`
- Nunca hardcodees una API key en el código

## Estructura de Funciones

- Una función hace una sola cosa
- Si una función supera 40 líneas, considera dividirla
- Las funciones que llaman a APIs externas deben devolver un resultado tipado
  o lanzar una excepción clara, nunca `None` silencioso

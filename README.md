# Rappi Insights Bot

Un sistema de análisis de datos impulsado por IA diseñado para equipos de operaciones de Rappi. Permite explorar métricas y tendencias tanto mediante un chatbot conversacional como a través de reportes analíticos automatizados estructurados y sumarizados con LLMs.

## 🏗️ Arquitectura

El proyecto sigue una arquitectura modular en 4 capas:
`UI (Streamlit) → Lógica (Bot/Insights) → Procesamiento IA (Gemini 2.5) → Motor Analítico (DuckDB) → Datos (Excel/CSV)`

## 🚀 Instalación

1. Clona este repositorio.
2. Crea un entorno virtual e instala las dependencias:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Copia el archivo de variables de entorno y agrega tu API Key de Google Gemini:
   ```bash
   cp .env.example .env
   ```
   *(Asegúrate de editar `.env` y colocar tu clave real en `GEMINI_API_KEY`)*

## 🏃‍♂️ Cómo ejecutar

Para iniciar la aplicación de Streamlit localmente:
```bash
streamlit run src/ui/app.py
```

## 📁 Estructura del Proyecto

```text
rappi-insights/
├── data/                  # Datos crudos (.xlsx, .csv)
├── src/
│   ├── bot/               # Lógica del chatbot y Function Calling
│   ├── data/              # ETL y conexión a DuckDB en memoria
│   ├── insights/          # Scripts de pandas para anomalías y tendencias
│   └── ui/                # Componentes de Streamlit (app principal)
├── templates/             # Plantillas Jinja2 para reportes
├── requirements.txt       # Dependencias
└── README.md              # Documentación
```

## 🛠️ Stack Tecnológico

- **Python & Streamlit**: Para un desarrollo rápido de una UI de datos reactiva e interactiva.
- **DuckDB**: Base de datos analítica en memoria ultra-rápida, ideal para procesamiento OLAP sin complicaciones de infraestructura.
- **Pandas & Plotly**: Cálculos locales robustos estadísticos y renderizado de visualizaciones ricas.
- **Google Gemini (genai)**: Motor de razonamiento principal usando Gemini 2.5 Flash. Elegido por su velocidad, precisión con JSON schemas en Function Calling y amplio context window.

## 💰 Costo Estimado

El uso recae sobre la API de Gemini 2.5 Flash. Bajo el *Free Tier* de Google AI Studio, el costo es de **$0.00** para pruebas y uso moderado (hasta 15 RPM). En producción con la versión de pago, Gemini Flash cuesta aproximadamente $0.075 / 1M input tokens, lo que se traduce a centavos al mes incluso interactuando diariamente.

## 🚧 Limitaciones y Próximos Pasos

- **Persistencia Temporal**: Actualmente el historial de DuckDB y el Chat es efímero en memoria por sesión.
- **Próximos Pasos**: 
  - Migrar los datos crudos a Snowflake/BigQuery en lugar de Excel de prueba.
  - Implementar autenticación para equipos de negocio.
  - Generación de reportes PDF descargables.
# rappi_insigth

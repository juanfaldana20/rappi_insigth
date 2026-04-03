---
description: Construye una fase completa del proyecto Rappi Insights
---

# Workflow: /build-phase

Cuando el usuario escriba `/build-phase <número>`, ejecuta la secuencia
correspondiente usando los agentes y skills definidos en `.agents/`.

---

## /build-phase 1 — Capa de datos

**Agente:** Engineer
**Skill:** data-layer.md

### Secuencia de ejecución

1. Crea la estructura de carpetas del proyecto si no existe:
   ```
   src/data/
   src/bot/
   src/insights/
   src/ui/
   templates/
   data/
   ```

2. Crea el archivo `requirements.txt` con las dependencias del proyecto:
   ```
   streamlit
   pandas
   openpyxl
   duckdb
   plotly
   jinja2
   python-dotenv
   google-generativeai
   ```

3. Crea `.env.example`:
   ```
   GEMINI_API_KEY=your_key_here
   ```

4. Implementa `src/data/loader.py` siguiendo la skill `data-layer.md` al pie de la letra.
   Incluye: carga del Excel, registro en DuckDB (formato ancho y largo), y `get_schema_info()`.

5. Ejecuta en terminal para verificar:
   ```bash
   pip install -r requirements.txt
   python -c "from src.data.loader import load_data, get_schema_info; conn, _, _ = load_data('data/dummy_data.xlsx'); print(get_schema_info(conn))"
   ```

6. Valida con las 4 queries de verificación definidas en `data-layer.md`.

7. Reporta: número de filas cargadas por tabla, países disponibles, métricas disponibles.

---

## /build-phase 2 — Bot conversacional

**Agente:** Engineer + Analyst (revisión del system prompt)
**Skill:** bot-skill.md

### Secuencia de ejecución

1. Implementa `src/bot/tools.py` con la definición de `query_data_tool`.

2. Implementa `src/bot/executor.py` con:
   - `execute_query(conn, sql)` con manejo de errores
   - `decide_chart(df)` con la lógica de selección de gráfico Plotly

3. Implementa `src/bot/chatbot.py` con:
   - El system prompt completo (inyectando schema desde loader)
   - La función `chat(user_message, history)` con loop de function calling
   - Gestión del historial de mensajes

4. Implementa `src/ui/app.py` con solo la pestaña de Chat por ahora:
   - `st.session_state` para el historial
   - Input de texto + botón enviar
   - Renderizado de mensajes con `st.chat_message`
   - Gráficos Plotly con `st.plotly_chart`

5. Lanza la app en terminal:
   ```bash
   streamlit run src/ui/app.py
   ```

6. Prueba estos 6 casos en el browser y confirma que todos responden correctamente:
   - "¿Cuáles son las 5 zonas con mayor Lead Penetration esta semana?"
   - "Compara el Perfect Orders entre zonas Wealthy y Non Wealthy en México"
   - "Muestra la evolución de Gross Profit UE en Chapinero las últimas 8 semanas"
   - "¿Cuál es el promedio de Lead Penetration por país?"
   - "¿Qué zonas tienen alto Lead Penetration pero bajo Perfect Orders?"
   - "¿Cuáles son las zonas que más crecen en órdenes?"

7. Reporta: screenshot de cada respuesta como Artifact.

---

## /build-phase 3 — Insights automáticos

**Agente:** Engineer + Analyst (valida relevancia de hallazgos)
**Skill:** insights-skill.md

### Secuencia de ejecución

1. Implementa `src/insights/analyzer.py` con las 4 funciones:
   - `detect_anomalies()`
   - `detect_declining_trends()`
   - `benchmark_zones()`
   - `find_correlations()`
   - `run_full_analysis()` como orquestadora

2. Prueba el analyzer en terminal y muestra cuántos hallazgos encontró por categoría:
   ```bash
   python -c "
   from src.data.loader import load_data
   from src.insights.analyzer import run_full_analysis
   conn, df_m, df_o = load_data('data/dummy_data.xlsx')
   results = run_full_analysis(df_m, df_o)
   for k, v in results.items():
       if isinstance(v, list): print(f'{k}: {len(v)} hallazgos')
   "
   ```

3. Crea `templates/report.html` con la estructura definida en `insights-skill.md`.

4. Implementa `src/insights/report.py` con `generate_report()`.

5. Genera un reporte de prueba y guárdalo en `outputs/test_report.html`.

6. Abre el reporte en el browser para validar visualmente.

7. Añade la pestaña "Insights" en `src/ui/app.py`:
   - Botón "Generar reporte"
   - Spinner mientras corre el análisis
   - Reporte HTML con `st.components.v1.html()`
   - Botón de descarga del HTML

8. Reporta: el reporte completo como Artifact.

---

## /build-phase 4 — Pulido y README

**Agente:** Engineer
**Skills:** todas (revisión final)

### Secuencia de ejecución

1. Revisa todos los archivos creados y aplica las reglas de `python-style.md`:
   - Type hints completos
   - Docstrings donde falten
   - Manejo de errores consistente

2. Crea `README.md` con las siguientes secciones:
   - Descripción del sistema (2-3 líneas)
   - Arquitectura (referencia al diagrama mental: UI → Bot/Insights → Gemini → DuckDB → Datos)
   - Instalación paso a paso
   - Cómo ejecutar (`streamlit run src/ui/app.py`)
   - Estructura del proyecto (árbol de carpetas)
   - Stack tecnológico y justificación de decisiones
   - Costo estimado de uso de la API
   - Limitaciones conocidas y próximos pasos

3. Ejecuta la app completa una vez más y confirma que ambas pestañas funcionan.

4. Verifica que no haya API keys en el código:
   ```bash
   grep -r "AIza" src/ || echo "OK: no hay keys hardcodeadas"
   ```

5. Reporta: README como Artifact + confirmación de que la app corre sin errores.

# Skill: Bot Conversacional

## Objetivo

Construir el chatbot que responde preguntas en lenguaje natural sobre métricas
operacionales de Rappi. El bot usa Gemini 1.5 Flash con function calling para
generar SQL, ejecutarlo en DuckDB y responder en lenguaje natural.

---

## Patrón de funcionamiento

```
Pregunta del usuario
     ↓
Gemini 1.5 Flash
(system prompt + historial + tool: query_data)
     ↓
Genera llamada a query_data(sql="SELECT ...")
     ↓
executor.py ejecuta SQL en DuckDB → DataFrame
     ↓
Gemini recibe el resultado → responde en lenguaje natural
     ↓
executor.py evalúa si generar gráfico Plotly
     ↓
Streamlit renderiza texto + gráfico (si aplica)
```

---

## tools.py — Definición de la herramienta

Define la función `query_data` como tool de Gemini:

```python
query_data_tool = {
    "name": "query_data",
    "description": (
        "Ejecuta una query SQL sobre las tablas de datos de Rappi. "
        "Tablas disponibles: 'metrics' (métricas por zona, formato ancho), "
        "'metrics_long' (métricas en formato largo con columna 'week'), "
        "'orders' (órdenes por zona, formato ancho), "
        "'orders_long' (órdenes en formato largo con columna 'week'). "
        "Usa esta función cada vez que necesites datos para responder."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "sql": {
                "type": "string",
                "description": "Query SQL válida para DuckDB."
            }
        },
        "required": ["sql"]
    }
}
```

---

## executor.py — Ejecución y gráficos

### Ejecución de SQL

```python
def execute_query(conn, sql: str) -> tuple[pd.DataFrame | None, str | None]:
    try:
        df = conn.execute(sql).df()
        return df, None
    except Exception as e:
        return None, f"Error ejecutando SQL: {str(e)}. Revisa la sintaxis y los nombres de columnas."
```

Cuando hay error, el mensaje se devuelve a Gemini para que reintente con SQL corregido.

### Lógica de gráficos

El executor evalúa el DataFrame resultante y decide qué gráfico mostrar:

| Condición | Gráfico |
|---|---|
| Columna `week` presente + una métrica + varias zonas | Línea (tendencia temporal) |
| Dos columnas numéricas + una categórica | Barras (comparación) |
| Exactamente dos columnas numéricas | Scatter (multivariable) |
| Más de 20 filas con una sola dimensión | Barras horizontales |
| Cualquier otro caso | Sin gráfico, solo tabla |

---

## chatbot.py — Memoria y llamadas

### System prompt del bot

```
Eres un asistente de análisis de datos para equipos de operaciones de Rappi.
Tienes acceso a datos operacionales de zonas geográficas en 9 países.
Usas la herramienta query_data para consultar los datos y responder preguntas.

TABLAS DISPONIBLES:
{schema_info}  ← inyectado desde loader.get_schema_info()

DICCIONARIO DE MÉTRICAS:
- Lead Penetration: Tiendas habilitadas / (leads + habilitadas + salidas). Mide penetración de mercado.
- Perfect Orders: Órdenes sin cancelaciones ni defectos / Total órdenes. Mide calidad operacional.
- Gross Profit UE: Margen bruto / Total órdenes. Rentabilidad por unidad económica.
- Pro Adoption: Usuarios Pro / Total usuarios.
- % PRO Users Who Breakeven: Usuarios Pro cuyo valor cubre el costo de membresía / Total Pro.
- MLTV Top Verticals Adoption: Usuarios que compran en múltiples verticales / Total usuarios.
- Non-Pro PTC > OP: Conversión No-Pro de "Proceed to Checkout" a "Order Placed".
- Turbo Adoption: Usuarios que compran en Turbo / Total usuarios con tiendas Turbo disponibles.
- Restaurants Markdowns / GMV: Descuentos en restaurantes / GMV restaurantes.
- Restaurants SS > ATC CVR: Conversión "Select Store" a "Add to Cart" en restaurantes.
- Restaurants SST > SS CVR: % usuarios que seleccionan una tienda tras elegir categoría Restaurantes.
- Retail SST > SS CVR: Igual pero para Supermercados.
- % Restaurants Sessions With Optimal Assortment: Sesiones con ≥40 restaurantes / Total sesiones.

REGLAS DE INTERPRETACIÓN:
- "Zonas problemáticas" = Perfect Orders bajo, Gross Profit UE bajo, tendencia negativa.
- "Zonas de alto rendimiento" = métricas sobre la media de su país y tipo de zona.
- "Crecimiento" en órdenes = comparar L0W vs L4W (o el rango que indique el usuario).
- Las métricas CVR están en formato ratio (0 a 1), no porcentaje.
- Para preguntas de inferencia (¿por qué crece X?), primero obtén los datos y luego razona.

FORMATO DE RESPUESTA:
- Responde en español.
- Sé conciso pero completo.
- Si la respuesta incluye números, menciona los más relevantes.
- Si el resultado es largo, resume los top hallazgos.
- Sugiere una pregunta de seguimiento relevante al final cuando sea útil.
```

### Gestión del historial

```python
def chat(user_message: str, history: list[dict]) -> tuple[str, list[dict]]:
    history.append({"role": "user", "parts": [user_message]})
    # Llamada a Gemini con todo el historial
    # Manejo del function calling en el loop
    # Append de la respuesta al historial
    # Retorna (respuesta_texto, historial_actualizado)
```

Mantén el historial completo en memoria de sesión (Streamlit `st.session_state`).

---

## Tipos de queries que el bot debe manejar

| Tipo | Ejemplo | Estrategia SQL |
|---|---|---|
| Filtrado | Top 5 zonas por Lead Penetration | `ORDER BY L0W_ROLL DESC LIMIT 5` sobre `metrics` |
| Comparación | Wealthy vs Non Wealthy en MX | `GROUP BY ZONE_TYPE WHERE COUNTRY='MX'` |
| Tendencia temporal | Evolución de una métrica 8 semanas | Query sobre `metrics_long` con `week` |
| Agregación | Promedio por país | `GROUP BY COUNTRY` con `AVG` |
| Multivariable | Alto LP + bajo PO | Subquery o CTE con dos filtros |
| Inferencia | ¿Por qué crece X? | Query de datos → Gemini razona sobre resultado |

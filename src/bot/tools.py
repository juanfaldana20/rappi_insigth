"""
Definición de las herramientas (tools) para Function Calling en Gemini.

Incluye los esquemas en formato JSON / diccionario dictando qué funciones 
puede invocar el modelo y qué parámetros debe proveer.
"""

# Tool que le otorga a la IA la capacidad de ejecutar queries SQL.
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

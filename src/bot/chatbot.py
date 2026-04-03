import os
import google.generativeai as genai
import pandas as pd
import duckdb
from typing import Tuple, List, Dict, Optional, Any
from src.bot.tools import query_data_tool
from src.bot.executor import execute_query, decide_chart
from src.data.loader import get_schema_info
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

def get_system_prompt(conn: duckdb.DuckDBPyConnection) -> str:
    """Genera el system prompt dinámico con el esquema de datos extraído de la base."""
    schema_info = get_schema_info(conn)
    return f"""Eres un asistente de análisis de datos para equipos de operaciones de Rappi.
Tienes acceso a datos operacionales de zonas geográficas en 9 países.
Usas la herramienta query_data para consultar los datos y responder preguntas.

TABLAS DISPONIBLES:
{schema_info}

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
- % Restaurants Sessions With Optimal Assortment: Sesiones con >=40 restaurantes / Total sesiones.

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
"""

def chat(user_message: str, chat_session: Any, conn: duckdb.DuckDBPyConnection) -> Tuple[str, Any, Optional[Any], Optional[pd.DataFrame]]:
    """Maneja el flujo de interacción de usuario, incluyendo llamadas recursivas a query_data_tool."""
    if chat_session is None:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            tools=[{"function_declarations": [query_data_tool]}],
            system_instruction=get_system_prompt(conn)
        )
        chat_session = model.start_chat()

    response = chat_session.send_message(user_message)
    
    chart_fig = None
    df_result = None

    # Handle Function Call (query_data)
    def get_function_call(resp: Any) -> Any:
        """Extrae la respuesta de llamada a función desde la API de Gemini."""
        if not hasattr(resp, "parts"): return None
        for p in resp.parts:
            # Check if it's a function call proto
            if hasattr(p, "function_call") and getattr(p.function_call, "name", None):
                return p.function_call
        return None

    i = 0
    fcall = get_function_call(response)
    while fcall and i < 5:
        i += 1
        sql = dict(fcall.args).get("sql") if hasattr(fcall.args, "items") else fcall.args["sql"]
        # Execute query
        df, err = execute_query(conn, sql)
        
        if err:
             response = chat_session.send_message({
                 "role": "function",
                 "parts": [{"function_response": {"name": "query_data", "response": {"error": err}}}]
             })
        else:
             df_result = df
             chart_fig = decide_chart(df)
             res_dict = df.head(100).to_dict(orient="records")
             response = chat_session.send_message({
                 "role": "function",
                 "parts": [{"function_response": {"name": "query_data", "response": {"data": res_dict}}}]
             })
        
        fcall = get_function_call(response)

    # The final text response
    final_text = response.text

    return final_text, chat_session, chart_fig, df_result

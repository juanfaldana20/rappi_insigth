"""
Motor de ejecución del Chatbot.

Se encarga de ejecutar sentencias SQL generadas por la IA en DuckDB
y de seleccionar la representación gráfica (Plotly) adecuada según 
la conformación del conjunto de datos retornado.
"""
import pandas as pd
import duckdb
import plotly.express as px
from typing import Tuple, Optional, Any

def execute_query(conn: duckdb.DuckDBPyConnection, sql: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Ejecuta una consulta SQL en la base de datos DuckDB de manera segura.
    """
    try:
        df = conn.execute(sql).df()
        return df, None
    except Exception as e:
        return None, f"Error ejecutando SQL: {str(e)}. Revisa la sintaxis y los nombres de columnas."


def decide_chart(df: pd.DataFrame) -> Optional[Any]:
    """
    Lógica de gráficos:
    1. Columna `week` presente + una métrica + varias zonas -> Línea
    2. Dos columnas numéricas + una categórica -> Barras
    3. Exactamente dos columnas numéricas -> Scatter
    4. Más de 20 filas con una sola dimensión -> Barras horizontales
    5. Cualquier otro caso -> None
    """
    if df is None or df.empty:
        return None

    columns = list(df.columns)
    
    # Contadores auxiliares para tipos de columnas
    num_cols = [c for c in columns if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [c for c in columns if not pd.api.types.is_numeric_dtype(df[c])]

    # 1. Columna `week` presente + una métrica + varias zonas -> Gráfico de Línea temporal
    # Usualmente variables categóricas junto al campo temporal mapean a un valor continuo
    if 'week' in [c.lower() for c in columns]:
        week_col = next(c for c in columns if c.lower() == 'week')
        if len(num_cols) == 1 and len(cat_cols) >= 2:
            color_col = next((c for c in cat_cols if c != week_col), None)
            if color_col:
                # Ordenamiento explícito para strings de tipo semana "L8W", "L7W"
                df_sorted = df.sort_values(by=week_col, key=lambda x: x.str.extract(r'L(\d+)W').astype(int)[0], ascending=False)
                fig = px.line(df_sorted, x=week_col, y=num_cols[0], color=color_col, title="Tendencia temporal")
                return fig

    # 2. Dos columnas numéricas + una categórica -> Barras (comparación)
    if len(num_cols) >= 2 and len(cat_cols) == 1:
        fig = px.bar(df, x=cat_cols[0], y=num_cols, barmode='group', title="Comparación")
        return fig

    # 3. Exactamente dos columnas numéricas (0 categoricas) -> Scatter (multivariable)
    if len(num_cols) == 2 and len(cat_cols) == 0:
        fig = px.scatter(df, x=num_cols[0], y=num_cols[1], title="Correlación")
        return fig

    # 4. Más de 20 filas con una sola dimensión (1 cat, 1 num) -> Barras horizontales
    if len(df) > 20 and len(cat_cols) == 1 and len(num_cols) >= 1:
        df_sorted = df.sort_values(by=num_cols[0], ascending=True)
        fig = px.bar(df_sorted, y=cat_cols[0], x=num_cols[0], orientation='h', title="Ranking")
        return fig

    # Otros casos que no cuadran con lógica fuerte no generan gráfico,
    # apoyando al LLM a simplemente tabular o describir.
    
    return None

"""
Módulo de carga y procesamiento de datos.

Este módulo lee los datos operacionales de un archivo Excel, transforma las tablas 
(unpivoting) para facilitar consultas temporales complejas, y las carga en una base 
de datos DuckDB en memoria.
"""
import pandas as pd
import duckdb
from typing import Tuple, Any

# Conexión global a DuckDB para operar como patrón Singleton
_CONN = None

def load_data(file_path: str = 'data/dummy_data.xlsx') -> Tuple[duckdb.DuckDBPyConnection, pd.DataFrame, pd.DataFrame]:
    """
    Carga datos desde un archivo Excel a una conexión DuckDB en memoria.
    
    Lee las pestañas 'RAW_INPUT_METRICS' y 'RAW_ORDERS', transforma las columnas
    temporales al formato largo (melt) y las registra en DuckDB.
    
    Args:
        file_path (str): Ruta al archivo Excel con los datos fuente.
        
    Returns:
        Tuple: Contiene la conexión a DuckDB, el DataFrame de métricas y el de órdenes.
    """
    global _CONN
    if _CONN is not None:
        # Si la base de datos ya está inicializada, se omite recargarla.
        pass

    try:
        # Leer hojas de cálculo
        df_metrics = pd.read_excel(file_path, sheet_name='RAW_INPUT_METRICS')
        df_orders = pd.read_excel(file_path, sheet_name='RAW_ORDERS')
    except Exception as e:
        print(f"Error cargando archivo Excel: {e}")
        raise e

    # Crear conexión DuckDB en memoria RAM
    conn = duckdb.connect(database=':memory:')

    # Transformar DataFrame de métricas usando melt (De ancho a largo)
    week_cols_metrics = [f"L{i}W_ROLL" for i in range(8, -1, -1)]
    # Conservar solo columnas que realmente existen en el archivo
    week_cols_metrics_exist = [col for col in week_cols_metrics if col in df_metrics.columns]
    
    df_metrics_long = df_metrics.melt(
        id_vars=["COUNTRY", "CITY", "ZONE", "ZONE_TYPE", "ZONE_PRIORITIZATION", "METRIC"],
        value_vars=week_cols_metrics_exist,
        var_name="week",
        value_name="value"
    )
    
    # Transformar DataFrame de órdenes usando melt (De ancho a largo)
    week_cols_orders = [f"L{i}W" for i in range(8, -1, -1)]
    week_cols_orders_exist = [col for col in week_cols_orders if col in df_orders.columns]

    df_orders_long = df_orders.melt(
        id_vars=["COUNTRY", "CITY", "ZONE", "METRIC"],
        value_vars=week_cols_orders_exist,
        var_name="week",
        value_name="value"
    )

    # Registrar las 4 tablas en DuckDB (Anchas y Largas)
    conn.register("metrics", df_metrics)
    conn.register("metrics_long", df_metrics_long)
    conn.register("orders", df_orders)
    conn.register("orders_long", df_orders_long)

    _CONN = conn
    return conn, df_metrics, df_orders

def get_schema_info(conn: duckdb.DuckDBPyConnection = None) -> str:
    """
    Construye y devuelve una representación en texto del esquema de base de datos.
    
    Esta información es inyectada en el prompt del LLM para que el bot comprenda
    qué datos puede consultar mediante SQL.
    """
    if conn is None:
        conn = _CONN
    if conn is None:
        return "No database connection established."

    schema_info = []
    
    # Tabla ancha de métricas
    schema_info.append("Table: metrics")
    schema_info.append("- COUNTRY: string (AR, BR, CL, CO, CR, EC, MX, PE, UY)")
    schema_info.append("- CITY: string")
    schema_info.append("- ZONE: string (Zona operacional o barrio)")
    schema_info.append("- ZONE_TYPE: string ('Wealthy' / 'Non Wealthy')")
    schema_info.append("- ZONE_PRIORITIZATION: string ('High Priority' / 'Prioritized' / 'Not Prioritized')")
    schema_info.append("- METRIC: string (Nombre de la métrica)")
    schema_info.append("- L8W_ROLL to L0W_ROLL: float (Valores de las últimas semanas, L0W_ROLL es la actual)")
    schema_info.append("")

    # Tabla larga de métricas unpivoteadas
    schema_info.append("Table: metrics_long (Unpivoted metrics)")
    schema_info.append("- COUNTRY, CITY, ZONE, ZONE_TYPE, ZONE_PRIORITIZATION, METRIC: string")
    schema_info.append("- week: string (ej. L8W_ROLL, L0W_ROLL)")
    schema_info.append("- value: float")
    schema_info.append("")

    # Tabla ancha de órdenes
    schema_info.append("Table: orders")
    schema_info.append("- COUNTRY: string")
    schema_info.append("- CITY: string")
    schema_info.append("- ZONE: string")
    schema_info.append("- METRIC: string (Siempre 'Orders')")
    schema_info.append("- L8W to L0W: float (Órdenes de las últimas semanas)")
    schema_info.append("")

    # Tabla larga de órdenes unpivoteadas
    schema_info.append("Table: orders_long (Unpivoted orders)")
    schema_info.append("- COUNTRY, CITY, ZONE, METRIC: string")
    schema_info.append("- week: string (ej. L8W, L0W)")
    schema_info.append("- value: float")

    return "\n".join(schema_info)

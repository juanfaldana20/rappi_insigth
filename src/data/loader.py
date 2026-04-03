import pandas as pd
import duckdb
from typing import Tuple, Any

# Global connection to act as singleton
_CONN = None

def load_data(file_path: str = 'data/dummy_data.xlsx') -> Tuple[duckdb.DuckDBPyConnection, pd.DataFrame, pd.DataFrame]:
    """
    Load data from Excel into duckdb connection and return the connection along with DataFrames.
    If the connection is already initialized, returns it directly.
    """
    global _CONN
    if _CONN is not None:
        # Returning None for dataframes when connection already initialized 
        # (or one could store them globally too)
        # However, for simplicity returning what's needed.
        pass

    try:
        # Read the excel sheets
        df_metrics = pd.read_excel(file_path, sheet_name='RAW_INPUT_METRICS')
        df_orders = pd.read_excel(file_path, sheet_name='RAW_ORDERS')
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        raise e

    # Create duckdb connection in memory
    conn = duckdb.connect(database=':memory:')

    # Unpivot/melt metrics
    week_cols_metrics = [f"L{i}W_ROLL" for i in range(8, -1, -1)]
    # Keep only the columns that exist in case the data doesn't perfectly match
    week_cols_metrics_exist = [col for col in week_cols_metrics if col in df_metrics.columns]
    
    df_metrics_long = df_metrics.melt(
        id_vars=["COUNTRY", "CITY", "ZONE", "ZONE_TYPE", "ZONE_PRIORITIZATION", "METRIC"],
        value_vars=week_cols_metrics_exist,
        var_name="week",
        value_name="value"
    )
    
    # Unpivot/melt orders
    week_cols_orders = [f"L{i}W" for i in range(8, -1, -1)]
    week_cols_orders_exist = [col for col in week_cols_orders if col in df_orders.columns]

    df_orders_long = df_orders.melt(
        id_vars=["COUNTRY", "CITY", "ZONE", "METRIC"],
        value_vars=week_cols_orders_exist,
        var_name="week",
        value_name="value"
    )

    # Register all tables
    conn.register("metrics", df_metrics)
    conn.register("metrics_long", df_metrics_long)
    conn.register("orders", df_orders)
    conn.register("orders_long", df_orders_long)

    _CONN = conn
    return conn, df_metrics, df_orders

def get_schema_info(conn: duckdb.DuckDBPyConnection = None) -> str:
    """
    Returns the schema of the duckdb database in plain text.
    """
    if conn is None:
        conn = _CONN
    if conn is None:
        return "No database connection established."

    schema_info = []
    
    # metrics table
    schema_info.append("Table: metrics")
    schema_info.append("- COUNTRY: string (AR, BR, CL, CO, CR, EC, MX, PE, UY)")
    schema_info.append("- CITY: string")
    schema_info.append("- ZONE: string (Zona operacional o barrio)")
    schema_info.append("- ZONE_TYPE: string ('Wealthy' / 'Non Wealthy')")
    schema_info.append("- ZONE_PRIORITIZATION: string ('High Priority' / 'Prioritized' / 'Not Prioritized')")
    schema_info.append("- METRIC: string (Nombre de la métrica)")
    schema_info.append("- L8W_ROLL to L0W_ROLL: float (Valores de las últimas semanas, L0W_ROLL es la actual)")
    schema_info.append("")

    # metrics_long table
    schema_info.append("Table: metrics_long (Unpivoted metrics)")
    schema_info.append("- COUNTRY, CITY, ZONE, ZONE_TYPE, ZONE_PRIORITIZATION, METRIC: string")
    schema_info.append("- week: string (ej. L8W_ROLL, L0W_ROLL)")
    schema_info.append("- value: float")
    schema_info.append("")

    # orders table
    schema_info.append("Table: orders")
    schema_info.append("- COUNTRY: string")
    schema_info.append("- CITY: string")
    schema_info.append("- ZONE: string")
    schema_info.append("- METRIC: string (Siempre 'Orders')")
    schema_info.append("- L8W to L0W: float (Órdenes de las últimas semanas)")
    schema_info.append("")

    # orders_long table
    schema_info.append("Table: orders_long (Unpivoted orders)")
    schema_info.append("- COUNTRY, CITY, ZONE, METRIC: string")
    schema_info.append("- week: string (ej. L8W, L0W)")
    schema_info.append("- value: float")

    return "\n".join(schema_info)

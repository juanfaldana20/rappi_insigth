# Skill: Capa de Datos

## Objetivo

Cargar el archivo Excel con los datos de Rappi en memoria y exponerlos como tablas
consultables vía DuckDB. Este módulo es la base de todo el sistema.

---

## Archivo de entrada

```
data/dummy_data.xlsx
```

Contiene tres hojas:
- `RAW_INPUT_METRICS` → se carga como tabla `metrics`
- `RAW_ORDERS`        → se carga como tabla `orders`
- `RAW_SUMMARY`       → solo documentación, no se registra en DuckDB

---

## Schema exacto

### Tabla `metrics`

| Columna             | Tipo   | Notas                                      |
|---------------------|--------|--------------------------------------------|
| COUNTRY             | string | AR, BR, CL, CO, CR, EC, MX, PE, UY        |
| CITY                | string |                                            |
| ZONE                | string | Zona operacional o barrio                  |
| ZONE_TYPE           | string | "Wealthy" / "Non Wealthy"                  |
| ZONE_PRIORITIZATION | string | "High Priority" / "Prioritized" / "Not Prioritized" |
| METRIC              | string | Nombre de la métrica                       |
| L8W_ROLL            | float  | Valor hace 8 semanas                       |
| L7W_ROLL            | float  |                                            |
| L6W_ROLL            | float  |                                            |
| L5W_ROLL            | float  |                                            |
| L4W_ROLL            | float  |                                            |
| L3W_ROLL            | float  |                                            |
| L2W_ROLL            | float  |                                            |
| L1W_ROLL            | float  |                                            |
| L0W_ROLL            | float  | Semana actual (más reciente)               |

### Tabla `orders`

| Columna | Tipo   | Notas                   |
|---------|--------|-------------------------|
| COUNTRY | string |                         |
| CITY    | string |                         |
| ZONE    | string |                         |
| METRIC  | string | Siempre "Orders"        |
| L8W     | float  | Órdenes hace 8 semanas  |
| L7W     | float  |                         |
| L6W     | float  |                         |
| L5W     | float  |                         |
| L4W     | float  |                         |
| L3W     | float  |                         |
| L2W     | float  |                         |
| L1W     | float  |                         |
| L0W     | float  | Semana actual           |

---

## Implementación de loader.py

El archivo debe:

1. Leer el Excel con `openpyxl` o `pandas`
2. Crear los DataFrames `df_metrics` y `df_orders`
3. Crear una conexión DuckDB en memoria: `conn = duckdb.connect()`
4. Registrar ambos DataFrames: `conn.register("metrics", df_metrics)`
5. Exponer la conexión como singleton para que el resto del sistema la use
6. Incluir una función `get_schema_info() -> str` que devuelva el schema
   en texto plano (útil para el system prompt del bot)

## Consideración crítica: columnas de semanas

Las columnas `L8W_ROLL` a `L0W_ROLL` están en formato ancho (pivot).
Cuando se necesiten consultas de tendencia temporal, hay que hacer unpivot (melt):

```python
week_cols = [f"L{i}W_ROLL" for i in range(8, -1, -1)]
df_long = df_metrics.melt(
    id_vars=["COUNTRY", "CITY", "ZONE", "ZONE_TYPE", "ZONE_PRIORITIZATION", "METRIC"],
    value_vars=week_cols,
    var_name="week",
    value_name="value"
)
# También registrar la versión larga en DuckDB
conn.register("metrics_long", df_long)
```

Registra también `orders_long` para la tabla de órdenes con columnas `L8W` a `L0W`.

---

## Verificación post-carga

Después de cargar, ejecuta estas queries de validación y muestra los resultados:

```sql
SELECT COUNT(*) as total_rows FROM metrics;
SELECT COUNT(DISTINCT COUNTRY) as paises FROM metrics;
SELECT COUNT(DISTINCT METRIC) as metricas FROM metrics;
SELECT COUNT(*) as total_orders FROM orders;
```

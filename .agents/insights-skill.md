# Skill: Insights Automáticos

## Objetivo

Analizar los datos de forma programática con pandas y generar un reporte ejecutivo
en HTML. El principio fundamental: los números los calcula pandas, el modelo solo
escribe la narrativa y las recomendaciones.

---

## analyzer.py — 4 categorías de análisis

### 1. Anomalías

Detecta cambios drásticos semana a semana (L1W → L0W).

```python
def detect_anomalies(df_metrics: pd.DataFrame, threshold: float = 0.10) -> list[dict]:
    """
    Retorna lista de dicts con: country, city, zone, metric,
    l1w_value, l0w_value, pct_change, direction ("mejora" | "deterioro")
    Filtra donde |pct_change| > threshold
    """
```

Ordena por `|pct_change|` descendente. Incluye máximo 20 anomalías en el reporte.

---

### 2. Tendencias preocupantes

Detecta deterioro consistente en 3 o más semanas consecutivas.

```python
def detect_declining_trends(df_metrics: pd.DataFrame, min_weeks: int = 3) -> list[dict]:
    """
    Para cada (zone, metric), verifica si los últimos N valores son
    estrictamente decrecientes: L2W > L1W > L0W (para min_weeks=3).
    Retorna: country, city, zone, metric, weeks_declining,
             start_value (L{n}W), end_value (L0W), total_pct_change
    """
```

---

### 3. Benchmarking

Compara zonas contra el promedio de su grupo (COUNTRY + ZONE_TYPE).

```python
def benchmark_zones(df_metrics: pd.DataFrame, std_threshold: float = 1.5) -> list[dict]:
    """
    Agrupa por (COUNTRY, ZONE_TYPE, METRIC).
    Calcula media y std del grupo.
    Flaggea zonas donde |valor - media| > std_threshold * std.
    Retorna: country, zone, metric, zone_value, group_mean,
             std_devs_from_mean, direction ("sobre" | "bajo")
    """
```

---

### 4. Correlaciones

Encuentra relaciones entre métricas en la semana actual.

```python
def find_correlations(df_metrics: pd.DataFrame, min_correlation: float = 0.6) -> list[dict]:
    """
    Pivotea df_metrics para tener zonas como filas y métricas como columnas
    usando L0W_ROLL como valor.
    Calcula matriz de correlación de Pearson.
    Retorna pares (metric_a, metric_b, correlation) donde |correlation| > min_correlation,
    sin duplicados (A-B y B-A cuentan como uno).
    """
```

---

## Estructura del output de analyzer.py

```python
def run_full_analysis(df_metrics: pd.DataFrame, df_orders: pd.DataFrame) -> dict:
    return {
        "anomalies": detect_anomalies(df_metrics),
        "declining_trends": detect_declining_trends(df_metrics),
        "benchmarks": benchmark_zones(df_metrics),
        "correlations": find_correlations(df_metrics),
        "summary_stats": {
            "total_zones": int,
            "total_countries": int,
            "total_metrics": int,
            "date_generated": str  # timestamp ISO
        }
    }
```

---

## report.py — Generación del reporte

### Paso 1: Preparar el prompt para Gemini Pro

Construye un prompt que incluya los hallazgos estructurados del analyzer y pide:
- Resumen ejecutivo con los 3-5 hallazgos más críticos
- Una interpretación de negocio por cada categoría
- Recomendaciones accionables (máximo 2 por hallazgo)
- Tono ejecutivo, directo, sin tecnicismos innecesarios
- Output en HTML puro (sin markdown, sin ```html```)

### Paso 2: Renderizar con Jinja2

El template `templates/report.html` recibe:
```python
{
    "narrative": str,          # HTML generado por Gemini Pro
    "anomalies": list[dict],
    "declining_trends": list[dict],
    "benchmarks": list[dict],
    "correlations": list[dict],
    "summary_stats": dict
}
```

### Estructura del reporte HTML

```
┌─────────────────────────────────────┐
│  Rappi Operations — Reporte Semanal │
│  Generado: [timestamp]              │
├─────────────────────────────────────┤
│  RESUMEN EJECUTIVO                  │
│  [narrative de Gemini Pro]          │
├─────────────────────────────────────┤
│  ANOMALÍAS (N hallazgos)            │
│  Tabla: zona | métrica | cambio%    │
├─────────────────────────────────────┤
│  TENDENCIAS PREOCUPANTES            │
│  Tabla: zona | métrica | semanas    │
├─────────────────────────────────────┤
│  BENCHMARKING                       │
│  Tabla: zona | métrica | vs grupo   │
├─────────────────────────────────────┤
│  CORRELACIONES                      │
│  Tabla: métrica A | métrica B | r   │
└─────────────────────────────────────┘
```

### Función principal

```python
def generate_report(analysis_results: dict) -> str:
    """
    Recibe el output de run_full_analysis().
    Llama a Gemini Pro para la narrativa.
    Renderiza el template Jinja2.
    Retorna HTML como string listo para mostrar o guardar.
    """
```

---

## Consideraciones de calidad

- Prioriza relevancia sobre volumen: 5 insights sólidos > 20 superficiales
- Si una categoría no tiene hallazgos, incluye una línea que lo indique ("Sin anomalías detectadas esta semana")
- Los porcentajes en el reporte siempre con 1 decimal: `f"{pct:.1%}"`
- Los valores de métricas CVR (entre 0 y 1) se muestran como porcentaje en el reporte

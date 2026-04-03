"""
Módulo Analizador de Métricas Operacionales.

Utiliza pandas para aplicar algoritmos de minería de datos básicos tales 
como detectar anomalías de la última semana (caídas abruptas), tendencias
prolongadas negativas a lo largo del tiempo, y correlaciones lineales entre variables.
"""
import pandas as pd
from datetime import datetime

def detect_anomalies(df_metrics: pd.DataFrame, threshold: float = 0.10) -> list:
    """
    Detecta anomalías operacionales o caídas abruptas semanales.
    Compara las variables y busca cambios significativos desde la última semana hasta la actual.
    """
    res = []
    # df_metrics contains L1W_ROLL and L0W_ROLL
    if 'L0W_ROLL' not in df_metrics.columns or 'L1W_ROLL' not in df_metrics.columns:
        return res
        
    for _, row in df_metrics.iterrows():
        l1w = row['L1W_ROLL']
        l0w = row['L0W_ROLL']
        if pd.isna(l1w) or pd.isna(l0w) or l1w == 0:
            continue
        pct_change = (l0w - l1w) / l1w
        if abs(pct_change) > threshold:
            res.append({
                "country": row["COUNTRY"],
                "city": row["CITY"],
                "zone": row["ZONE"],
                "metric": row["METRIC"],
                "l1w_value": float(l1w),
                "l0w_value": float(l0w),
                "pct_change": float(pct_change),
                "direction": "mejora" if pct_change > 0 else "deterioro"
            })
    
    res = sorted(res, key=lambda x: abs(x["pct_change"]), reverse=True)[:20]
    return res

def detect_declining_trends(df_metrics: pd.DataFrame, min_weeks: int = 3) -> list:
    """
    Localiza variables que llevan `min_weeks` continuos en declive (bajada consistente tras semana).
    """
    res = []
    cols = [f"L{i}W_ROLL" for i in range(min_weeks-1, -1, -1)]
    for c in cols:
        if c not in df_metrics.columns:
            return res
            
    for _, row in df_metrics.iterrows():
        declining = True
        for i in range(len(cols)-1):
            if pd.isna(row[cols[i]]) or pd.isna(row[cols[i+1]]) or row[cols[i]] <= row[cols[i+1]]:
                declining = False
                break
        
        if declining:
            start_val = row[cols[0]]
            end_val = row[cols[-1]]
            pct_change = (end_val - start_val) / start_val if start_val != 0 else 0
            
            res.append({
                "country": row["COUNTRY"],
                "city": row["CITY"],
                "zone": row["ZONE"],
                "metric": row["METRIC"],
                "weeks_declining": min_weeks,
                "start_value": float(start_val),
                "end_value": float(end_val),
                "total_pct_change": float(pct_change)
            })
            
    return res

def benchmark_zones(df_metrics: pd.DataFrame, std_threshold: float = 1.5) -> list:
    """
    Agrupa datos por tipo de zona y país, para luego marcar las zonas donde
    su última medición (L0W) sobresalga significativamente por debajo o por encima 
    de la media (+/- `std_threshold` desviaciones estándar).
    """
    res = []
    if 'L0W_ROLL' not in df_metrics.columns:
        return res
        
    try:
        groups = df_metrics.groupby(['COUNTRY', 'ZONE_TYPE', 'METRIC'])
    except Exception:
        return res
    
    for name, group in groups:
        mean_val = group['L0W_ROLL'].mean()
        std_val = group['L0W_ROLL'].std()
        
        if pd.isna(std_val) or std_val == 0:
            continue
            
        for _, row in group.iterrows():
            val = row['L0W_ROLL']
            if pd.isna(val):
                continue
                
            z_score = (val - mean_val) / std_val
            if abs(z_score) > std_threshold:
                res.append({
                    "country": row["COUNTRY"],
                    "zone": row["ZONE"],
                    "metric": row["METRIC"],
                    "zone_value": float(val),
                    "group_mean": float(mean_val),
                    "std_devs_from_mean": float(abs(z_score)),
                    "direction": "sobre" if z_score > 0 else "bajo"
                })
                
    return res

def find_correlations(df_metrics: pd.DataFrame, min_correlation: float = 0.6) -> list:
    """
    Determina cómo guardan correlaciones las distintas métricas tabuladas.
    Calcula una matriz de correlación cruzada (filtro general de Pearson).
    """
    res = []
    if 'L0W_ROLL' not in df_metrics.columns:
        return res
        
    df_pivot = df_metrics.pivot_table(index="ZONE", columns="METRIC", values="L0W_ROLL")
    if len(df_pivot.columns) < 2:
        return res

    corr_matrix = df_pivot.corr()
    
    seen = set()
    for col1 in corr_matrix.columns:
        for col2 in corr_matrix.index:
            if col1 == col2:
                continue
            pair = tuple(sorted([col1, col2]))
            if pair in seen:
                continue
            
            val = corr_matrix.loc[col2, col1]
            if pd.notna(val) and abs(val) > min_correlation:
                seen.add(pair)
                res.append({
                    "metric_a": pair[0],
                    "metric_b": pair[1],
                    "correlation": float(val)
                })
                
    return res

def run_full_analysis(df_metrics: pd.DataFrame, df_orders: pd.DataFrame) -> dict:
    """
    Función orquestadora que ejecuta todos los cálculos de insights de forma masiva
    y junta los resultados estructurados en un solo diccionario final.
    """
    return {
        "anomalies": detect_anomalies(df_metrics),
        "declining_trends": detect_declining_trends(df_metrics),
        "benchmarks": benchmark_zones(df_metrics),
        "correlations": find_correlations(df_metrics),
        "summary_stats": {
            "total_zones": int(df_metrics['ZONE'].nunique()) if 'ZONE' in df_metrics else 0,
            "total_countries": int(df_metrics['COUNTRY'].nunique()) if 'COUNTRY' in df_metrics else 0,
            "total_metrics": int(df_metrics['METRIC'].nunique()) if 'METRIC' in df_metrics else 0,
            "date_generated": datetime.now().isoformat()
        }
    }

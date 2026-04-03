"""
Servidor y UI Principal con Streamlit.

Despliega el Dashboard interactivo que acopla el chat conversacional con
la visualización automática de reportes de operaciones.
"""
import streamlit as st
import os, sys

# Ensure imports work when running from root
import duckdb
import pandas as pd
from typing import Tuple
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.data.loader import load_data
from src.bot.chatbot import chat

st.set_page_config(page_title="Rappi Insights", layout="wide")

# Cargar Datos
@st.cache_resource
def init_db() -> Tuple[duckdb.DuckDBPyConnection, pd.DataFrame, pd.DataFrame]:
    """Carga los datos por primera vez y los cachea."""
    conn, df_m, df_o = load_data('data/dummy_data.xlsx')
    return conn, df_m, df_o

conn, df_metrics, df_orders = init_db()

# Interfaz Personalizada (Streamlit)
st.title("🍔 Rappi Insights Bot")

if "ui_history" not in st.session_state:
    st.session_state.ui_history = []
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None

from src.insights.analyzer import run_full_analysis
from src.insights.report import generate_report
import streamlit.components.v1 as components

# Pestañas (Tabs)
tab1, tab2 = st.tabs(["Chat", "Insights Automáticos"])

with tab1:
    # Mostrar historial de mensajes de la sesión
    for msg in st.session_state.ui_history:
        with st.chat_message(msg["role"]):
            st.write(msg["text"])

    # Entrada de chat interactiva
    if prompt := st.chat_input("Pregunta algo sobre las métricas operacionales..."):
        # Mensaje del usuario
        with st.chat_message("user"):
            st.write(prompt)

        st.session_state.ui_history.append({"role": "user", "text": prompt})

        # Respuesta interactiva del agente AI
        with st.chat_message("assistant"):
            with st.spinner("Analizando..."):
                try:
                    text_resp, new_session, fig, df_final = chat(prompt, st.session_state.chat_session, conn)
                    st.session_state.chat_session = new_session
                    st.session_state.ui_history.append({"role": "assistant", "text": text_resp})
                    st.write(text_resp)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    elif df_final is not None and not df_final.empty:
                        st.dataframe(df_final)
                except Exception as e:
                    st.error(f"Error en la interacción con el bot: {e}")

with tab2:
    st.header("📊 Reporte Ejecutivo de Operaciones")
    st.write("Presiona el botón para ejecutar los algoritmos de detección y generar un reporte narrativo estructurado.")
    if st.button("Generar Reporte", type="primary"):
        with st.spinner("Analizando puntos de datos y elaborando narrativa ejecutiva con IA..."):
            try:
                results = run_full_analysis(df_metrics, df_orders)
                html_report = generate_report(results)
                
                st.download_button(
                    label="⬇️ Descargar Reporte Completo (HTML)",
                    data=html_report,
                    file_name="reporte_operaciones_rappi.html",
                    mime="text/html"
                )
                
                st.markdown("---")
                components.html(html_report, height=1000, scrolling=True)
            except Exception as e:
                st.error(f"Error generando el reporte: {e}")

import os
import json
import google.generativeai as genai
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

def generate_report(analysis_results: dict) -> str:
    # prompt gemini
    # Extract top findings for the model context limits and concise summary
    prompt_data = {
        "anomalies": analysis_results["anomalies"][:20],
        "declining_trends": analysis_results["declining_trends"][:20],
        "benchmarks": analysis_results["benchmarks"][:20],
        "correlations": analysis_results["correlations"],
    }
    
    prompt = f"""Eres un analista de operaciones experto de Rappi. Escribe el resumen ejecutivo de este reporte semanal de datos, usando Tono ejecutivo, directo, y sin tecnicismos innecesarios.
El output debe ser EXCLUSIVAMENTE HTML puro (sin markdown de bloques, solo código). No inicies con ```html, devuélvelo directamente para ser insertado en un div.
Provee los 3-5 hallazgos más críticos extraídos de los datos estructurales, una interpretación de negocio por categoría, y recomendaciones accionables (max 2 por hallazgo). Usa etiquetas semánticas de HTML5 (<p>, <ul>, <li>, <strong>, <h3>, etc) para organizar la respuesta.

Datos de la semana:
{json.dumps(prompt_data, indent=2)}
"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        ai_response = model.generate_content(prompt)
        narrative = ai_response.text.strip()
        
        # Remove markdown format if model decides to use it
        if narrative.startswith("```html"):
            narrative = narrative[7:]
        elif narrative.startswith("```"):
            narrative = narrative[3:]
        if narrative.endswith("```"):
            narrative = narrative[:-3]
    except Exception as e:
        narrative = f"<p><strong>Error generando narrativa con IA:</strong> {e}</p>"
        
    # Render template
    loader = FileSystemLoader(os.path.join(os.path.dirname(__file__), '../../templates'))
    jinja_env = Environment(loader=loader)
    template = jinja_env.get_template('report.html')
    
    full_data = analysis_results.copy()
    full_data["narrative"] = narrative
    
    return template.render(**full_data)

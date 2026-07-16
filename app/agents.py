import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.domain import Incident

# Cargamos las variables de entorno (.env)
load_dotenv()


class SREAgent:
    """Agent encargado de realizar el diagnóstico técnico inicial de los incidentes."""

    def __init__(self):
        # Inicializamos Gemini (usamos gemini-3.5-flash por velocidad y costo cero)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite",
            temperature=0.2,  # Temperatura baja para respuestas técnicas y deterministas
            google_api_key=os.getenv("GEMINI_API_KEY")
        )

        # Diseñamos el Prompt del SRE
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", (
                "Eres un Ingeniero SRE (Site Reliability Engineer) Senior de guardia. "
                "Tu trabajo es analizar la alerta de incidente provista y dar un reporte de triaje ultra-conciso. "
                "Debes identificar la posible causa raíz y sugerir los 3 pasos inmediatos de mitigación.\n\n"
                "Formato de salida requerido (responde en Markdown estructurado):\n"
                "### 🔍 Diagnóstico de Causa Raíz\n"
                "- [Tu análisis breve de por qué falló]\n\n"
                "### 🛡️ Acciones de Mitigación Inmediata (Priorizadas)\n"
                "1. [Paso 1]\n"
                "2. [Paso 2]\n"
                "3. [Paso 3]"
            )),
            ("user", (
                "Alerta Recibida:\n"
                "- Servicio: {service_name}\n"
                "- Entorno: {environment}\n"
                "- Severidad: {severity}\n"
                "- Mensaje de Error: {error_message}\n"
                "- Detalles Técnicos/Stack: {stack_trace}"
            ))
        ])

        # Conecto usando LCEL
        self.chain = self.prompt_template | self.llm | StrOutputParser()

    async def analyze(self, incident: Incident) -> str:
        """Envía el incidente estructurado al LLM y retorna el diagnóstico."""
        try:
            # Ejecutamos la cadena de manera asíncrona
            response = await self.chain.ainvoke({
                "service_name": incident.service_name,
                "environment": incident.environment,
                "severity": incident.severity,
                "error_message": incident.error_message,
                "stack_trace": incident.stack_trace or "No stack trace provided"
            })
            print("✅ [SREAgent] Respuesta recibida con éxito de Gemini.")
            return response
        except Exception as e:
            return f"❌ Error en el análisis del Agente de IA: {str(e)}"
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

# Esquema de Entrada (Validación estricta estilo Zod)
class GCPWebhookPayload(BaseModel):
    class IncidentPayload(BaseModel):
        incident_id: str = Field(..., description="ID único de la alerta de GCP")
        policy_name: str = Field(..., description="Nombre de la política violada")
        summary: str = Field(..., description="Resumen de la falla técnica")
        started_at: int = Field(..., description="Unix timestamp de inicio")
        resource: dict = Field(..., description="Recurso de GCP que disparó la alerta")
        metadata: Optional[dict] = Field(..., description="Metadatos personalizables")
    incident: IncidentPayload

# Esquema de Salida (Formateo y tipado estricto hacia la API)
class IncidentResponse(BaseModel):
    id: int
    service_name: str
    environment: str
    severity: str
    error_message: str
    ai_diagnostics: str
    timestamp: datetime
    owner: str
    status: str

    # Configuración de mapeo automático desde modelos SQLAlchemy (ORM)
    model_config = ConfigDict(from_attributes=True)
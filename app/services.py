from typing import Dict, Any, List
from app.domain import Incident
from app.agents import SREAgent
from app.models.IncidentRecord import IncidentRecord
from app.config.database import AsyncSessionLocal
from app.repo.Incident import SQLIncidentRepository


class TriageService:
    """Caso de uso de negocio para automatizar el triaje de incidentes."""

    def __init__(self):
        self.agent = SREAgent()

    async def execute(self, incident: Incident) -> Dict[str, Any]:
        # 1. Ejecutar análisis del agente de IA
        ai_diagnostics = await self.agent.analyze(incident)

        # 2. Convertir la entidad del Dominio a un Registro del Modelo
        db_incident = IncidentRecord(
            service_name=incident.service_name,
            environment=incident.environment,
            severity=incident.severity,
            error_message=incident.error_message,
            ai_diagnostics=ai_diagnostics,
            timestamp=incident.timestamp,
            owner=incident.owner,
            status=incident.status
        )

        # 3. Guardar usando el Patrón Repository
        async with AsyncSessionLocal() as session:
            repo = SQLIncidentRepository(session)
            saved_record = await repo.save(db_incident)
            saved_id = saved_record.id

        return {
            "status": "completed",
            "incident_id": saved_id,
            "message": "Incidente procesado y guardado exitosamente."
        }

    async def get_all_incidents(self) -> List[IncidentRecord]:
        """Obtiene todos los incidentes consumiendo el repositorio."""
        async with AsyncSessionLocal() as session:
            repo = SQLIncidentRepository(session)
        return await repo.get_all()

    async def update_incident_status(self, incident_id:int , status:str )-> IncidentRecord:
        """Actualiza el estado del incidente"""
        async with AsyncSessionLocal() as session:
            repo = SQLIncidentRepository(session)
        return await repo.update_status(incident_id, status)

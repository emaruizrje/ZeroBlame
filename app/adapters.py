from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any
from app.domain import Incident

class IncidentAdapter(ABC):
    """Interfaz base para cualquier adaptador de proveedor externo."""
    @abstractmethod
    def to_domain(self) -> Incident:
        pass


class GCPIncidentAdapter(IncidentAdapter):
    """Adaptador que encapsula las reglas de traducción para Google Cloud Monitoring."""
    def __init__(self, raw_data: Dict[str, Any]):
        self.raw_data = raw_data

    def to_domain(self) -> Incident:
        incident_data = self.raw_data.get("incident", {})
        resource_labels = incident_data.get("resource", {}).get("labels", {})
        metadata = incident_data.get("metadata", {})
        user_labels = metadata.get("user_labels", {}) if metadata else {}
        system_labels = metadata.get("system_labels",{}) if metadata else {}

        return Incident(
            service_name=resource_labels.get("project_id", "unknown-gcp-service"),
            environment=system_labels.get("environment", "unknown-environment"),
            severity=system_labels.get("severity", "no info"),
            error_message=incident_data.get("summary", "No summary provided"),
            stack_trace=f"GCP Policy Violated: {incident_data.get('policy_name', 'N/A')}",
            owner= user_labels.get("owner"),
            status= 'PENDING',
            timestamp=datetime.utcfromtimestamp(incident_data.get("started_at", datetime.utcnow().timestamp()))
        )
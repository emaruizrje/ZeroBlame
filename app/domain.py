from datetime import datetime
from typing import Optional, Dict, Any

class Incident:
    """ESta es la entidad del modelo de un incidente."""
    def __init__(
            self,
            service_name:str,
            environment:str,
            severity:str,
            error_message:str,
            owner: str,
            status: str,
            stack_trace:Optional[str]= None,
            timestamp: Optional[datetime] = None
            ):
        self.service_name = service_name
        self.environment = environment
        self.severity = severity
        self.error_message = error_message
        self.stack_trace = stack_trace
        self.owner = owner
        self.timestamp = timestamp
        self.status = status



    def to_dict(self) -> Dict[str, Any]:
        """El objeto lo convierte a un diccionario"""
        return {
            "service_name": self.service_name,
            "environment": self.environment,
            "severity":self.severity,
            "error_message":self.error_message,
            "stack_trace":self.stack_trace,
            "timestamp":self.timestamp.isoformat() if self.timestamp else None,
            "owner": self.owner,
            "status": self.status
        }

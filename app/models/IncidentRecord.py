from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.config.database import Base

class IncidentRecord(Base):
    """Acá represento la tabla 'incidents' en la base de datos."""
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String, index=True)
    environment = Column(String)
    severity = Column(String)
    error_message = Column(Text)
    ai_diagnostics = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    owner = Column(String, index=True)
    status = Column(String)
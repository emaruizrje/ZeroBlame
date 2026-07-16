# app/Incident.py
from abc import ABC, abstractmethod
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.IncidentRecord import IncidentRecord


class IncidentRepository(ABC):
    """Interfaz abstracta (Contrato) para el Repositorio de Incidentes."""

    @abstractmethod
    async def save(self, record: IncidentRecord) -> IncidentRecord:
        pass

    @abstractmethod
    async def get_all(self) -> List[IncidentRecord]:
        pass

    @abstractmethod
    async def update_status(self, incident_id:int, status:str) -> IncidentRecord:
        pass


class SQLIncidentRepository(IncidentRepository):
    """Implementación concreta del repositorio usando SQLAlchemy y Postgres."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, record: IncidentRecord) -> IncidentRecord:
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def get_all(self) -> List[IncidentRecord]:
        result = await self.session.execute(
            select(IncidentRecord).order_by(IncidentRecord.timestamp.desc())
        )
        return result.scalars().all()

    async def update_status(self, incident_id:int , status:str) -> IncidentRecord:
        result = await self.session.execute(
            select(IncidentRecord).filter(IncidentRecord.id == incident_id)
        )
        record = result.scalar_one_or_none()
        if not record:
            raise ValueError(f"Incident not found")
        record.status = status
        await self.session.commit()
        await self.session.refresh(record)
        return record

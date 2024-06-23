
from __future__ import annotations
from darwin.messages.src.ts import Location, ServiceUpdate
from darwin.service.src.model import Service
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import darwin.service.src.model as db_model


class DatabaseRepositoryInterface:

    def save_service_update(self, service_update: ServiceUpdate) -> int:
        ...

    def save_location(self, locations: list[Location], update_id: int) -> None:
        ...


class DatabaseRepository(DatabaseRepositoryInterface):

    def __init__(self, engine: Engine) -> None:
        self._session = sessionmaker(engine)

    def save_service_update(self, service_update: ServiceUpdate) -> int:
        with self._session.begin() as session:
            
            service = session.query(Service).filter_by(rid=service_update.service.rid, uid=service_update.service.uid).first()

            orm_service_update = service_update.to_orm()
            session.add(orm_service_update)

            if not service:
                session.add(service_update.service.to_orm())

            session.flush()
            # session.refresh(orm_service_update)

            return orm_service_update.update_id

    def save_location(self, locations: list[Location], update_id: int) -> None:
        with self._session.begin() as session:
            
            session.add_all([loc.to_orm(update_id) for loc in locations])
            session.commit()

    @classmethod
    def create(cls, password: str) -> DatabaseRepository:
        return cls(
            engine=create_engine(f"postgresql://postgres:{password}@127.0.0.1:5436/postgres")
        )
        

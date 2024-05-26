
from __future__ import annotations
from darwin.messages.src.ts import Location, ServiceUpdate
from darwin.service.src.model import Service
from sqlalchemy import Engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

class DatabaseRepositoryInterface:

    def save_service_update(self, service_update: ServiceUpdate) -> None:
        ...

    # def save_locations(self, locations: list[Location]) -> None:
    #     ...


class DatabaseRepository(DatabaseRepositoryInterface):

    def __init__(self, engine: Engine) -> None:
        self._session = sessionmaker(engine)

    def save_service_update(self, service_update: ServiceUpdate) -> ServiceUpdate:
        with self._session.begin() as session:
            
            service = session.execute(
                select(Service).filter_by(rid=service_update.service.rid)
            ).first()

            if service:
                service_update.service = service[0]

            session.add(service_update.to_orm())
            session.commit()

    def save_location(self, locations: list[Location]) -> ServiceUpdate:
        with self._session.begin() as session:
            
            session.add_all([loc.to_orm() for loc in locations])
            session.commit()

    @classmethod
    def create(self, password: str) -> DatabaseRepository:
        return DatabaseRepository(
            engine=create_engine(f"postgresql://postgres:{password}@127.0.0.1:5436/postgres")
        )
        


from __future__ import annotations
from darwin.messages.src.ts import Location, Service, ServiceUpdate
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

class DatabaseRepositoryInterface:

    def save_service_update(self, service_update: ServiceUpdate) -> None:
        ...

    # def save_locations(self, locations: list[Location]) -> None:
    #     ...


class DatabaseRepository(DatabaseRepositoryInterface):

    def __init__(self, engine: Engine) -> None:
        self._session = sessionmaker(engine)

    def save_service_update(self, service_update: ServiceUpdate) -> None:
        with self._session.begin() as session:
            session.add(service_update.to_orm())
            session.commit()

    @classmethod
    def create(self, password: str) -> DatabaseRepository:

        

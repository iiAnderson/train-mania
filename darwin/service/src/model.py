from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class Base(DeclarativeBase):
    pass


class Service(Base):
    __tablename__ = "service"

    rid: Mapped[str] = mapped_column(String(30), primary_key=True)
    uid: Mapped[str] = mapped_column(String(10))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"Service(rid={self.rid!r}, uid={self.uid!r}, ts={self.ts!r})"


class ServiceUpdate(Base):
    __tablename__ = "service_update"

    update_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    rid: Mapped[str] = mapped_column(ForeignKey("service.rid"))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"ServiceUpdate(update_id={self.update_id!r}, rid={self.rid!r}, ts={self.ts!r})"


class Timestamp(Base):
    __tablename__ = "timestamp"

    ts_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    src: Mapped[str] = mapped_column(String(30))
    delayed: Mapped[bool] = mapped_column(Boolean())
    status: Mapped[str] = mapped_column(String(30))

    def __repr__(self) -> str:
        return f"Timestamp(id={self.id!r}, status={self.status!r}, ts={self.ts!r})"


class Platform(Base):
    __tablename__ = "platform"

    plat_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    src: Mapped[str] = mapped_column(String(30))
    confirmed: Mapped[bool] = mapped_column(Boolean())
    text: Mapped[str] = mapped_column(String(30))

    def __repr__(self) -> str:
        return f"Platform(id={self.id!r}, text={self.text!r}, confirmed={self.confirmed!r})"


class Location(Base):
    __tablename__ = "location"

    loc_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    update_id: Mapped[str] = mapped_column(ForeignKey("service_update.update_id"))
    toc: Mapped[str] = mapped_column(String(10))

    arrival_id: Mapped[str] = mapped_column(ForeignKey("timestamp.id"))
    departure_id: Mapped[str] = mapped_column(ForeignKey("timestamp.id"))
    platform_id: Mapped[str] = mapped_column(ForeignKey("timestamp.id"))

    def __repr__(self) -> str:
        return f"Location(update_id={self.update_id!r}, toc={self.toc!r})"
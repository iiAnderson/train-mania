from __future__ import annotations
from datetime import datetime, time
from typing import Any
from sqlalchemy import ForeignKey
from sqlalchemy import String, DateTime, Boolean, BigInteger, Time
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column, relationship


class Base(DeclarativeBase):
    pass
    

class Service(Base):
    __tablename__ = "service"

    rid: Mapped[str] = mapped_column(String(30), primary_key=True)
    uid: Mapped[str] = mapped_column(String(10))

    def __repr__(self) -> str:
        return f"Service(rid={self.rid!r}, uid={self.uid!r})"


class ServiceUpdate(Base):
    __tablename__ = "service_update"

    update_id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    rid: Mapped[str] = mapped_column(ForeignKey("service.rid"))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    location: Mapped["Location"] = relationship(back_populates="update")

    def __repr__(self) -> str:
        return f"ServiceUpdate(update_id={self.update_id!r}, rid={self.rid!r}, ts={self.ts!r})"


class Timestamp(Base):
    __tablename__ = "timestamp"

    ts_id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    ts: Mapped[time] = mapped_column(Time())
    src: Mapped[str] = mapped_column(String(30))
    delayed: Mapped[bool] = mapped_column(Boolean())
    status: Mapped[str] = mapped_column(String(30))

    def __repr__(self) -> str:
        return f"Timestamp(id={self.id!r}, status={self.status!r}, ts={self.ts!r})"


class Platform(Base):
    __tablename__ = "platform"

    plat_id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    src: Mapped[str] = mapped_column(String(30))
    confirmed: Mapped[bool] = mapped_column(Boolean())
    text: Mapped[str] = mapped_column(String(30))

    location: Mapped["Location"] = relationship(back_populates="platform")

    def __repr__(self) -> str:
        return f"Platform(id={self.id!r}, text={self.text!r}, confirmed={self.confirmed!r})"


class Location(Base):
    __tablename__ = "location"

    loc_id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    update_id: Mapped[str] = mapped_column(ForeignKey("service_update.update_id"))
    tpl: Mapped[str] = mapped_column(String(10))

    arrival_id: Mapped[str] = mapped_column(ForeignKey("timestamp.ts_id"))
    arrival: Mapped["Timestamp"] = relationship(foreign_keys=arrival_id)

    departure_id: Mapped[str] = mapped_column(ForeignKey("timestamp.ts_id"))
    departure: Mapped["Timestamp"] = relationship(foreign_keys=departure_id)

    platform_id: Mapped[str] = mapped_column(ForeignKey("platform.plat_id"))
    platform: Mapped["Platform"] = relationship(back_populates="location")

    update: Mapped["ServiceUpdate"] = relationship(back_populates="location")


    def __repr__(self) -> str:
        return f"Location(update_id={self.update_id!r}, toc={self.tpl!r})"
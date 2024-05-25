from __future__ import annotations
from abc import ABC, abstractclassmethod, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
import darwin.service.src.model as db_model


from darwin.messages.src.common import Message

class InvalidPassingLocation(Exception): ...

class InvalidIntermediateTimestamp(Exception): ...

class InvalidIntermediatePlatform(Exception): ...

class IncorrectMessageFormat(Exception): ...

class LocationType(Enum):
    
    ORIGIN = "O"
    PASSING = "P"
    INTERMEDIATE = "I"
    DESTINATION = "D"

@dataclass
class Service:

    rid: str
    uid: str

    def to_orm(self) -> db_model.Service:
        return db_model.Service(
            rid=self.rid,
            uid=self.uid
        )


@dataclass
class ServiceUpdate:

    service: Service
    ts: datetime

    def to_orm(self) -> db_model.ServiceUpdate:
        return db_model.Service(
            rid=self.service,
            ts=self.ts
        )


@dataclass
class LocationTimestamp:

    ts: str
    src: str
    delayed: bool
    status: Status

    def format(self) -> dict:

        return {
            "ts": self.ts,
            "src": self.src,
            "delayed": self.delayed,
            "status": self.status.value
        }

    def to_orm(self) -> db_model.Timestamp:
        return db_model.Timestamp(
            ts=datetime.fromisoformat(self.ts),
            src=self.src,
            delayed=self.delayed,
            status=self.status
        )

@dataclass
class Platform:

    src: str
    confirmed: bool
    text: str

    def to_orm(self) -> db_model.Platform:
        return db_model.Platform(
            src=self.src,
            confirmed=self.confirmed,
            text=self.text
        )

class Status(Enum):
    ESTIMATED = "estimated"
    ACTUAL = "actual"


class TSService:

    @classmethod
    def create_location(cls, loc: dict) -> Location:

        if 'ns5:pass' in loc:
            return PassingLocation.create(loc)
        
        return StoppingLocation.create(loc)

    @classmethod
    def parse(cls, msg: Message) -> TSMessage:

        ts = msg.body['TS']

        rid = ts['@rid']
        uid = ts['@uid']
        locs = ts.get('ns5:Location')

        if not locs:
            raise IncorrectMessageFormat(f"Not TS new message: {msg}")

        if type(locs) != list:
            locs = [locs]

        return TSMessage(
            service=Service(rid=rid, uid=uid),
            locations=[cls.create_location(loc) for loc in locs],
            timestamp=msg.timestamp
        )

@dataclass
class TSMessage:

    service: ServiceUpdate
    locations: list[Location]
    timestamp: datetime

    def get_stations(self) -> str:
        ts = self.timestamp.strftime("%H:%M:%S")
        return f"{ts},{self.rid}," + ",".join([str(loc) for loc in self.locations])

    def filter_for(self, tiploc: str) -> bool:
        for location in self.locations:
            if location.tpl == tiploc:
                return True

        return False

    @property
    def destination(self) -> str:
        dest = self.locations[-1]
        return dest.tpl
        
    @property
    def current(self) -> str:
        loc = self.locations[0]
        return loc.tpl
    
    def format(self) -> list[dict]:

        return [
            {
                **{
                    "rid": self.service.rid,
                    "uid": self.service.uid,
                    "ts": self.timestamp.isoformat()
                }, 
                **loc.format()
            }
            for loc in self.locations
        ]

@dataclass
class Location(ABC):
    
    tpl: str

    @abstractmethod
    def format(self) -> dict:
        ...

    @abstractmethod
    def to_orm(self) -> db_model.Location:
        ...

    @classmethod
    @abstractmethod
    def create(self, msg: dict) -> Location:
        ...


@dataclass
class PassingLocation(Location):

    passing: LocationTimestamp

    @classmethod
    def create(self, msg: dict) -> Location:

        tpl = msg['@tpl']
    
        if 'ns5:pass' not in msg:
            raise InvalidPassingLocation(f"Invalid message, no ns5:pass {msg}")

        est_dep = msg['ns5:pass']

        actual_ts = est_dep.get('@at')
        estimated_ts = est_dep.get('@et')

        src = est_dep.get('@src')
        delayed = bool(est_dep.get("@delayed", False))

        return PassingLocation(
            tpl=tpl,
            passing=LocationTimestamp(
                ts=actual_ts if actual_ts else estimated_ts,
                src=src,
                delayed=delayed,
                status=Status.ACTUAL if actual_ts else Status.ESTIMATED
            )
        )

    def format(self) -> dict:
        return {
            "location_type": str(LocationType.PASSING.value),
            "tpl": self.tpl,
            "departure": self.passing.format() if self.passing else None
        }

    def to_orm(self) -> db_model.Platform:
        return db_model.Location(
            
        )

@dataclass
class StoppingLocation(Location):

    arrival: Optional[LocationTimestamp]
    departure: Optional[LocationTimestamp]
    
    platform: Optional[Platform]

    @classmethod
    def parse_timestamp(cls, body: Optional[dict]) -> Optional[LocationTimestamp]:

        if not body:
            return None

        actual_ts = body.get('@at')
        estimated_ts = body.get('@et')

        src = body.get('@src')
        delayed = bool(body.get("@delayed", False))

        return LocationTimestamp(
            ts= actual_ts if actual_ts else estimated_ts,
            src=src,
            delayed=delayed,
            status=Status.ACTUAL if actual_ts else Status.ESTIMATED
        )

    @classmethod
    def parse_platform(cls, platform: dict) -> Optional[Platform]:

        if not platform:
            return None

        if type(platform) == str:
            return Platform("unknown", False, platform)

        src = platform.get('@platsrc')
        confirmed = bool(platform.get('@conf', False))
        text = platform.get('#text')

        return Platform(src, confirmed, text)

    @classmethod
    def create(cls, msg: dict) -> Location:

        tpl = msg['@tpl']

        arr = cls.parse_timestamp(msg.get('ns5:arr'))
        dep = cls.parse_timestamp(msg.get('ns5:dep'))

        plat = cls.parse_platform(msg.get('ns5:plat'))

        return StoppingLocation(
            tpl=tpl,
            arrival=arr,
            departure=dep,
            platform=plat
        )

    def _type(self) -> LocationType:

        if self.arrival and not self.departure:
            return LocationType.DESTINATION
        if not self.arrival and self.departure:
            return LocationType.ORIGIN
        
        return LocationType.INTERMEDIATE

    def format(self) -> dict:
        return {
            "location_type": str(self._type().value),
            "tpl": self.tpl,
            "arrival": self.arrival.format() if self.arrival else None,
            "departure": self.departure.format() if self.departure else None,
            "platform": asdict(self.platform) if self.platform else None
        }
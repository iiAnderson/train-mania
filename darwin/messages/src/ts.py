from __future__ import annotations
from abc import ABC, abstractclassmethod, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
import time
import traceback
from typing import Optional
import darwin.service.src.model as db_model


from darwin.messages.src.common import Message

class InvalidPassingLocation(Exception): ...

class InvalidIntermediateTimestamp(Exception): ...

class InvalidIntermediatePlatform(Exception): ...

class IncorrectMessageFormat(Exception): ...

class InvalidTimestamp(Exception): ...

class InvalidStoppingLocation(Exception): ...

class InvalidLocation(Exception): ...

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
        return db_model.ServiceUpdate(
            rid=self.service.rid,
            ts=self.ts
        )


@dataclass
class LocationTimestamp:

    ts: datetime
    src: str
    delayed: bool
    status: Status

    def format(self) -> dict:

        return {
            "ts": datetime.strftime(self.ts, "%H:%M"),
            "src": self.src,
            "delayed": self.delayed,
            "status": self.status.value
        }

    def to_orm(self) -> db_model.Timestamp:
        return db_model.Timestamp(
            ts=self.ts,
            src=self.src,
            delayed=self.delayed,
            status=self.status.value
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
        
        try:
            return StoppingLocation.create(loc)
        except InvalidStoppingLocation as e:
            raise InvalidLocation(f"Invalid location") from e

    @classmethod
    def parse(cls, msg: Message) -> TSMessage:

        ts = msg.body['TS']

        if not msg.body.get('@updateOrigin') == "TD":
            raise IncorrectMessageFormat(f"Not TD origin message")

        rid = ts['@rid']
        uid = ts['@uid']
        locs = ts.get('ns5:Location')

        if not locs:
            raise IncorrectMessageFormat(f"Not TS new message: {msg}")

        if type(locs) != list:
            locs = [locs]

        locations = []

        for loc in locs:
            try:
                locations.append(cls.create_location(loc))
            except InvalidLocation as e:
                print(traceback.format_exc())
                
        return TSMessage(
            update=ServiceUpdate(service=Service(rid=rid, uid=uid), ts=msg.timestamp),
            locations=locations,
            timestamp=msg.timestamp
        )

@dataclass
class TSMessage:

    update: ServiceUpdate
    locations: list[Location]
    timestamp: datetime

    def get_stations(self) -> str:
        ts = self.timestamp.strftime("%H:%M:%S")
        return f"{ts},{self.update.service.rid}," + ",".join([str(loc) for loc in self.locations])

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
                    "rid": self.update.service.rid,
                    "uid": self.update.service.uid,
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
    def to_orm(self, update_id: int) -> db_model.Location:
        ...

    @classmethod
    @abstractmethod
    def create(cls, msg: dict) -> Location:
        ...


@dataclass
class PassingLocation(Location):

    passing: LocationTimestamp

    @classmethod
    def create(cls, msg: dict) -> Location:

        tpl = msg['@tpl']
    
        if 'ns5:pass' not in msg:
            raise InvalidPassingLocation(f"Invalid message, no ns5:pass {msg}")

        est_dep = msg['ns5:pass']

        actual_ts = est_dep.get('@at')
        estimated_ts = est_dep.get('@et') if est_dep.get('@et') else est_dep.get('@wet')

        src = est_dep.get('@src')
        delayed = bool(est_dep.get("@delayed", False))

        return PassingLocation(
            tpl=tpl,
            passing=LocationTimestamp(
                ts=datetime.strptime(actual_ts, "%H:%M") if actual_ts else datetime.strptime(estimated_ts, "%H:%M"),
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

    def to_orm(self, update_id: int) -> db_model.Location:
        return db_model.Location(
            tpl=self.tpl,
            update_id=update_id,
            departure=self.passing.to_orm()
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
        estimated_ts = body.get('@et') if body.get('@et') else body.get('@wet')

        if not actual_ts and not estimated_ts:
            raise InvalidTimestamp(f"Invalid timestamp {body}")

        src = body.get('@src')
        delayed = bool(body.get("@delayed", False))
        

        return LocationTimestamp(
            ts=datetime.strptime(actual_ts, "%H:%M") if actual_ts else datetime.strptime(estimated_ts, "%H:%M"),
            src=str(src),
            delayed=delayed,
            status=Status.ACTUAL if actual_ts else Status.ESTIMATED
        )

    @classmethod
    def parse_platform(cls, platform: dict) -> Optional[Platform]:

        if not platform:
            return None

        if type(platform) == str:
            return Platform("unknown", False, str(platform))

        src = platform.get('@platsrc')
        confirmed = bool(platform.get('@conf', False))
        text = platform.get('#text')

        return Platform(str(src), confirmed, str(text))

    @classmethod
    def create(cls, msg: dict) -> Location:

        tpl = msg['@tpl']

        try:
            arr = cls.parse_timestamp(msg.get('ns5:arr'))
            dep = cls.parse_timestamp(msg.get('ns5:dep'))
        except InvalidTimestamp:
            raise InvalidStoppingLocation(f"Invalid stopping location {msg}")

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

    def to_orm(self, update_id: int) -> db_model.Location:
        return db_model.Location(
            tpl=self.tpl,
            update_id=update_id,
            departure=self.departure.to_orm() if self.departure else None,
            arrival=self.arrival.to_orm() if self.arrival else None,
            platform=self.platform.to_orm() if self.platform else None
        )
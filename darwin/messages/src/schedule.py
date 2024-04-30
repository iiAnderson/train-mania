from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional

class InvalidTrustScheduleException(Exception): ...

class InvalidDarwinScheduleException(Exception): ...

class InvalidCISScheduleException(Exception): ...

class InvalidScheduleException(Exception): ...

class NonPassengerService(Exception): ...

class ScheduleTypeNotSupported(Exception): ...

class ScheduleService:
    
    @classmethod
    def create(cls, data: dict, ts: datetime) -> list[Train]:

        try:
            origin = data['@updateOrigin']
        except KeyError as e:
            raise InvalidScheduleException(f"Error when extracting data: {data}") from e   
        
        if origin == "CIS":
            return CISParser.create(data, ts)
        elif origin == "Darwin":
            return DarwinParser.create(data, ts)
        else:
            raise ScheduleTypeNotSupported(f"Schedule type not supported {origin}")

@dataclass
class CISParser:
    
    @classmethod
    def create(cls, data: dict, ts: datetime) -> list[Train]:

        try:
            schedule = data['schedule']

            if type(schedule) == dict:
                schedule = [schedule]

        except KeyError as e:
            raise InvalidCISScheduleException(f"Error when extracting data: {data}") from e

        locations = []

        for loc in schedule:
            try:
                locations.append(TrainLocations.create(loc, ts))
            except NonPassengerService as e:
                print(e)
                pass

        return locations

class DarwinParser:

    @classmethod
    def create(cls, data: dict, ts: datetime) -> list[Train]:
        return [TrainDeactivated.create(data, ts)]


@dataclass
class PassingLocation:

    wtp: str

    tpl: str

    @classmethod
    def create(cls, data: dict) -> PassingLocation:
        try:
            return PassingLocation(
                wtp=data["@wtp"],
                tpl=data["@tpl"]
            )
        except KeyError as e:
            raise InvalidCISScheduleException(f"Error when extracting data: {data}") from e


@dataclass
class Location:

    wta: Optional[str]
    wtd: Optional[str]
    pta: Optional[str]
    ptd: Optional[str]

    tpl: str
    act: str
    avg_loading: Optional[str]
    cancelled: Optional[bool]

    @classmethod
    def create(cls, data: dict) -> Location:

        try:
            return Location(
                wta=data.get("@wta"),
                wtd=data.get("@wtp"),
                pta=data.get("@pta"),
                ptd=data.get("@ptd"),
                tpl=data["@tpl"],
                act=data["@act"],
                avg_loading=data.get('@avg_loading'),
                cancelled=True if data.get("@can", 'false') == 'true' else False
            )
        except (KeyError, AttributeError) as e:
            raise InvalidCISScheduleException(f"Error when extracting data: {data}") from e

@dataclass
class Train(ABC):

    rid: str
    ts: datetime

    @abstractmethod
    def as_dict(self) -> list[dict]:
        ...


@dataclass
class TrainDeactivated(Train):

    deactivated: bool

    @classmethod
    def create(cls, data: dict, ts: datetime) -> Train:
        
        try:
            deactivated = data['deactivated']
        except KeyError as e:
            raise InvalidDarwinScheduleException(f"Error when extracting schedule from: {data}") from e
        try:
            return TrainDeactivated(
                rid=deactivated["@rid"], 
                deactivated=True, 
                ts=ts
            )
        except KeyError as e:
            raise InvalidDarwinScheduleException(f"Error when extracting data: {deactivated}") from e

    def as_dict(self) -> list[dict]:
        return [{"rid": self.rid, "ts": self.ts.isoformat(), "deactivated": self.deactivated}]

@dataclass
class TrainType(Train):

    passenger: bool

    @classmethod
    def create(cls, data: dict, ts: datetime) -> Train:
        
        try:
            rid = data['rid']
            passenger = data['passenger']

            return TrainType(rid=rid, ts=ts, passenger=passenger)
        except KeyError as e:
            raise InvalidDarwinScheduleException(f"Error when extracting schedule from: {data}") from e

    def as_dict(self) -> list[dict]:
        return [{"rid": self.rid, "ts": self.ts.isoformat(), "passenger": self.passenger}]

@dataclass
class TrainLocations(Train):

    origin: list[Location]
    destination: list[Location]
    intermediate: list[Location]

    @classmethod
    def parse_is_passenger_service(cls, data: dict) -> bool:
       
        is_pass =  data.get("@isPassengerSvc", "true")

        return True if is_pass == "true" else False

    @classmethod
    def _parse_locations(cls, locs: dict | list) -> list[Location]:

        if type(locs) == dict:
            locs = [locs]

        return [Location.create(loc) for loc in locs]

    @classmethod
    def create(cls, data: dict, ts: datetime) -> Train:

        try:
            is_passenger_service = cls.parse_is_passenger_service(data)
            rid = data["@rid"]
            
            if not is_passenger_service:
                return TrainType.create({"rid": rid, "passenger": False}, ts)

            return TrainLocations(
                ts=ts,
                rid=rid,
                origin=cls._parse_locations(data.get('ns2:OR', [])),
                destination=cls._parse_locations(data.get('ns2:DT', [])), 
                intermediate=cls._parse_locations(data.get("ns2:IP", []))
            )
        except (KeyError, TypeError, AttributeError) as e:
            raise InvalidCISScheduleException(f"Error when extracting data: {data}") from e

    def as_dict(self) -> list[dict]:

        data = []

        data.extend(
            [
                {
                    **asdict(origin),
                    **{
                        "rid": self.rid,
                        "type": "O",
                        "ts": self.ts.isoformat()
                    } 
                } for origin in self.origin
            ]
        )
        data.extend(
            [
                {
                    **asdict(interm),
                    **{
                        "rid": self.rid,
                        "type": "I",
                        "ts": self.ts.isoformat()
                    } 
                } for interm in self.intermediate
            ]
        )

        data.extend(
            [
                {
                    **asdict(dest),
                    **{
                        "rid": self.rid,
                        "type": "D",
                        "ts": self.ts.isoformat()
                    } 
                } for dest in self.destination
            ]
        )
        return data
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

class InvalidTrustScheduleException(Exception): ...

class InvalidDarwinScheduleException(Exception): ...

class InvalidCISScheduleException(Exception): ...

class InvalidScheduleException(Exception): ...


@dataclass
class Schedule:
    
    @classmethod
    def create(cls, data: dict) -> Schedule:

        try:
            origin = data['@updateOrigin']
        except KeyError as e:
            raise InvalidScheduleException(f"Error when extracting data: {data}") from e   

        if origin == "CIS":
            return CISSchedule.create(data)
        elif origin == "Trust":
            return TrustSchedule.create(data)
        elif origin == "Darwin":
            return DarwinSchedule.create(data)


@dataclass
class CISSchedule(Schedule):
    
    schedules: list[TrainSchedule]

    @classmethod
    def create(cls, data: dict) -> CISSchedule:

        try:
            return CISSchedule(
                schedules = [TrainSchedule.create(loc) for loc in data['schedule']]
            )
        except KeyError as e:
            raise InvalidCISScheduleException(f"Error when extracting data: {data}") from e


@dataclass
class DarwinSchedule(Schedule):

    deactivated_rid: str

    @classmethod
    def create(cls, data: dict) -> DarwinSchedule:
        
        try:
            deactivated = data['deactivated']
        except KeyError as e:
            raise InvalidDarwinScheduleException(f"Error when extracting schedule from: {data}") from e
        try:
            return DarwinSchedule(
                deactivated_rid=deactivated["@rid"]
            )
        except KeyError as e:
            raise InvalidDarwinScheduleException(f"Error when extracting data: {deactivated}") from e

@dataclass
class TrustSchedule(Schedule):
    
    rid: str
    is_passenger: bool

    @classmethod
    def create(cls, data: dict) -> TrustSchedule:

        try:
            schedule = data['schedule']
        except KeyError as e:
            raise InvalidTrustScheduleException(f"Error when extracting schedule from: {data}") from e
        try:
            return TrustSchedule(
                rid=schedule["@rid"],
                is_passenger=schedule("@isPassengerSvc", False)
            )
        except KeyError as e:
            raise InvalidTrustScheduleException(f"Error when extracting data: {schedule}") from e


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

    @classmethod
    def create(cls, data: dict) -> Location:

        try:
            print(data)
            return Location(
                wta=data.get("@wta"),
                wtd=data.get("@wtp"),
                pta=data.get("@pta"),
                ptd=data.get("@ptd"),
                tpl=data["@tpl"],
                act=data["@act"],
                avg_loading=data.get('@avg_loading')
            )
        except KeyError as e:
            raise InvalidCISScheduleException(f"Error when extracting data: {data}") from e


@dataclass
class TrainSchedule:

    rid: str

    origin: Location
    destination: Location
    intermediate: list[Location]

    @classmethod
    def create(cls, data: dict) -> TrainSchedule:

        try:
            intermediate_points = data.get("ns2:IP", [])

            if type(intermediate_points) == dict:
                intermediate_points = [intermediate_points]

            return TrainSchedule(
                rid=data["@rid"],
                origin=Location.create(data['ns2:OR']),
                destination=Location.create(data['ns2:DT']), 
                intermediate=[Location.create(loc) for loc in data['ns2:IP']]
            )
        except (KeyError, TypeError, AttributeError) as e:
            raise InvalidCISScheduleException(f"Error when extracting data: {data}") from e
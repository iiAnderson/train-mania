from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from messages.src.common import Message


class NotLocationTSMessage(Exception):
    ...

class TSLocation:

    tpl: str

    @classmethod
    def create(cls, body: dict) -> TSLocation:

        if 'ns5:pass' in body:
            return PassingTSLocation.create(body)

        return StoppingTSLocation.create(body)

@dataclass
class Platform:

    src: str
    confirmed: bool
    text: str


@dataclass
class Schedule:

    arrrival: Optional[str] = None
    departure: Optional[str] = None
    passing: Optional[str] = None


@dataclass
class Timestamp:

    time: str
    status: str
    src: str
    delayed: bool = False


@dataclass
class StoppingTSLocation(TSLocation):

    tpl: str
    schedule: Schedule
    arrival: Optional[Timestamp]
    departure: Optional[Timestamp]
    platform: Optional[Platform]

    @classmethod
    def parse_est_arr(cls, body: dict) -> Optional[Timestamp]:

        if 'ns5:arr' not in body:
            return None

        est_arr = body['ns5:arr']

        at = est_arr.get('@at')
        et = est_arr.get('@et')

        src = est_arr.get('@src')
        delayed = bool(est_arr.get("@delayed", False))

        return Timestamp(
            at if at else et,
            "actual" if at else "estimated",
            src,
            delayed
        )

    @classmethod
    def parse_est_dep(cls, body: dict) -> Optional[Timestamp]:

        if 'ns5:dep' not in body:
            return None

        est_dep = body['ns5:dep']

        at = est_dep.get('@at')
        et = est_dep.get('@et')

        src = est_dep.get('@src')
        delayed = bool(est_dep.get("@delayed", False))

        return Timestamp(
            at if at else et,
            "actual" if at else "estimated",
            src,
            delayed
        )

    @classmethod
    def parse_est_plat(cls, body: dict) -> Optional[Platform]:

        if 'ns5:plat' not in body:
            return None

        est_plat = body['ns5:plat']

        if type(est_plat) == str:
            return Platform("unknown", False, est_plat)

        src = est_plat.get('@platsrc')
        confirmed = bool(est_plat.get('@conf', False))
        text = est_plat.get('#text')

        return Platform(src, confirmed, text)

    @classmethod
    def create(cls, body: dict) -> StoppingTSLocation:
        
        tpl = body['@tpl']
        wta = body.get('@wta')
        wtd = body.get('@wtd')

        est_arr = cls.parse_est_arr(body)
        est_dep = cls.parse_est_dep(body)
        est_plat = cls.parse_est_plat(body)

        return StoppingTSLocation(
            tpl=tpl, 
            schedule=Schedule(wta, wtd), 
            arrival=est_arr, 
            departure=est_dep, 
            platform=est_plat
        )


@dataclass
class PassingTSLocation(TSLocation):

    tpl: str
    working_passing: Optional[str]
    estimated_pass: Optional[Timestamp] 

    @classmethod
    def parse_est_pass(cls, body: dict) -> Optional[Timestamp]:

        if 'ns5:pass' not in body:
            return None

        est_dep = body['ns5:pass']

        at = est_dep.get('@at')
        et = est_dep.get('@et')

        src = est_dep.get('@src')
        delayed = bool(est_dep.get("@delayed", False))

        return Timestamp(
            at if at else et,
            "actual" if at else "estimated",
            src,
            delayed
        )

    @classmethod
    def create(cls, body: dict) -> PassingTSLocation:
        
        tpl = body['@tpl']
        wtp = body.get('@wtp')

        estimated_pass = cls.parse_est_pass(body)

        return PassingTSLocation(
            tpl=tpl, 
            working_passing=wtp,
            estimated_pass=estimated_pass
        )

@dataclass
class TSLocationMessage:

    rid: str # rail id
    locations: list[TSLocation]
    timestamp: datetime

    @classmethod
    def create(cls, message: Message) -> TSLocationMessage:

        ts = message.body['TS']

        rid = ts['@rid']
        locs = ts.get('ns5:Location')

        if not locs:
            raise NotLocationTSMessage(f"Not TS Location message")

        if type(locs) != list:
            locs = [locs]

        parsed_locs = []
        for loc in locs:
            parsed_locs.append(TSLocation.create(loc))

        return cls(rid, parsed_locs, message.timestamp)

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
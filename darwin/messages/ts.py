from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class TSLocation:

    tpl: str # location id
    wta: Optional[str] = "" # arrival time
    wtd: Optional[str] = "" # departure time
    wtp: Optional[str] = "" # passing time

    @classmethod
    def create(cls, data: dict):

        return cls(tpl=data['@tpl'], wtp=data.get('@wtp'), wta=data.get("@wta"), wtd=data.get('@wtd'))

    def __str__(self):
        return f"{self.tpl},{self.wta},{self.wtp},{self.wtd}"


@dataclass
class EstimatedPlatform:

    src: str
    confirmed: bool
    text: str


@dataclass
class WorkingTime:

    arrrival: str = ""
    departure: str = ""
    passing: str = ""


@dataclass
class EstimatedTime:

    time: str
    status: str
    src: str


@dataclass
class StoppingTSLocation:

    tpl: str
    working_time: WorkingTime
    estimated_arr: Optional[EstimatedTime]
    estimated_dep: Optional[EstimatedTime]
    estimated_platform: Optional[EstimatedPlatform]

    @classmethod
    def parse_est_arr(cls, body: dict) -> Optional[EstimatedTime]:

        if 'ns5:arr' not in body:
            return None

        est_arr = body['ns5:arr']

        at = est_arr.get('@at')
        et = est_arr.get('@et')

        src = est_arr['@src']

        return EstimatedTime(
            at if at else et,
            "actual" if at else "estimated",
            src
        )

    @classmethod
    def parse_est_dep(cls, body: dict) -> Optional[EstimatedTime]:

        if 'ns5:dep' not in body:
            return None

        est_dep = body['ns5:dep']

        at = est_dep.get('@at')
        et = est_dep.get('@et')

        src = est_dep['@src']

        return EstimatedTime(
            at if at else et,
            "actual" if at else "estimated",
            src
        )

    @classmethod
    def parse_est_plat(cls, body: dict) -> Optional[EstimatedPlatform]:

        if 'ns5:plat' not in body:
            return None

        est_plat = body['ns5:plat']

        print(body)
        src = est_plat['@platsrc']
        confirmed = bool(est_plat.get('@conf', False))
        text = est_plat['#text']

        return EstimatedPlatform(src, confirmed, text)

    @classmethod
    def create(cls, body: dict) -> StoppingTSLocation:
        
        tpl = body['@tpl']
        wta = body['@wta']
        wtd = body.get('@wtd', "")

        est_arr = cls.parse_est_arr(body)
        est_dep = cls.parse_est_dep(body)
        # est_plat = cls.parse_est_plat(body) can be an int, needs work

        return StoppingTSLocation(
            tpl=tpl, 
            working_time=WorkingTime(wta, wtd), 
            estimated_arr=est_arr, 
            estimated_dep=est_dep, 
            estimated_platform=None
        )


@dataclass
class PassingTSLocation:

    tpl: str
    working_time: WorkingTime
    estimated_pass: EstimatedTime 


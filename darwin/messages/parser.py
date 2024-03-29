from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import io
from typing import Any, Optional
import zlib
import xmltodict

class NoValidMessageTypeFound(Exception):
    ...

class MessageType(str, Enum):

    TS =  "TS" # Actual and forecast information
    SC = "SC" # Schedule updates
    SF = "SF" # Schedule formations
    AS = "AS" # Association updates
    TO = "TO" # Train order
    LO = "LO" # Loading
    OW = "OW" # Station messages
    NO = "NO" # Notifications

    @staticmethod
    def parse(type: str) -> MessageType:
        try:
            return MessageType(str(type))
        except Exception:
            raise NoValidMessageTypeFound(f"{type} not found")

@dataclass
class RawMessage:
    message_type: str
    body: dict

    @classmethod
    def parse(cls, frame: Any) -> RawMessage:
        message_type = frame.headers['MessageType']
    
        bio = io.BytesIO()
        bio.write(str.encode('utf-16'))
        bio.seek(0)
        msg = zlib.decompress(frame.body, zlib.MAX_WBITS | 32)
        data = xmltodict.parse(msg)

        return cls(message_type, data) 

    def __str__(self) -> str:
        return f"[{self.message_type}] {self.body}"

@dataclass
class Message:

    message_type: MessageType
    body: dict
    timestamp: datetime


    @classmethod
    def from_frame(cls, raw_message: RawMessage) -> Message:

        parsed_message_type = MessageType(raw_message.message_type)

        try:
            uR = raw_message.body['Pport']['uR']
            split_ts = raw_message.body['Pport']['@ts'].split(".")
            ts = datetime.strptime(split_ts[0], "%Y-%m-%dT%H:%M:%S")
        except:
            print(raw_message.body)
            raise

        return cls(message_type=parsed_message_type, body=uR, timestamp=ts)


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
class TSMessage:

    rid: str # rail id
    locations: list[TSLocation]
    timestamp: datetime

    @classmethod
    def create(cls, message: Message) -> TSMessage:

        ts = message.body['TS']

        rid = ts['@rid']
        locs = ts['ns5:Location']

        if type(locs) != list:
            locs = [locs]

        return cls(rid, [TSLocation.create(loc) for loc in locs], message.timestamp)

    def get_stations(self) -> str:
        ts = self.timestamp.strftime("%H:%M:%S")
        return f"{ts},{self.rid}," + ",".join([str(loc) for loc in self.locations])

class MessageService:


    def parse(self, message: Message) -> None: 

        if message.message_type == MessageType.TS:
            ts_msg = TSMessage.create(message)
            data = ts_msg.get_stations()

            if data:
                print(data)
        
        if message.message_type == MessageType.SC:
            print("Schedule message")
            print(message.body)

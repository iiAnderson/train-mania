from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import io
from typing import Any, Optional
import zlib
import xmltodict

from messages.ts import TSLocation, StoppingTSLocation

class NoValidMessageTypeFound(Exception):
    ...

class NotLocationTSMessage(Exception):
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
    def from_message(cls, raw_message: RawMessage) -> Message:

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
            try:
                parsed_locs.append(StoppingTSLocation.create(loc))
            except KeyError as e:
                ...

        return cls(rid, parsed_locs, message.timestamp)

    def get_stations(self) -> str:
        ts = self.timestamp.strftime("%H:%M:%S")
        return f"{ts},{self.rid}," + ",".join([str(loc) for loc in self.locations])

    def filter_for(self, tiploc: str) -> bool:
        for location in self.locations:
            if location.tpl == tiploc:
                return True

        return False

class MessageService:


    def __init__(self, message_filter: Optional[MessageType] = None) -> None:

        self._message_filter = message_filter

    def parse(self, message: Message) -> None: 

        if self._message_filter and self._message_filter != message.message_type:
            return

        if message.message_type == MessageType.TS:
            ts_msg = TSLocationMessage.create(message)
            
            if ts_msg.filter_for("PADTON"):

                print("----")
                print(ts_msg.rid)
                for location in ts_msg.locations:
                    print(location)
        
        elif message.message_type == MessageType.SC:
            print("Schedule message")
            print(message.body)

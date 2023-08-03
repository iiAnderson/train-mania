from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import io
from typing import Any, Optional
import zlib
import xmltodict

class NoValidMessageTypeFound(Exception):
    ...

class MessageType(str, Enum):

    TS =  "TS"

    @staticmethod
    def parse(type: str) -> MessageType:
        try:
            return MessageType(str(type))
        except Exception:
            raise NoValidMessageTypeFound(f"{type} not found")

@dataclass
class Message:

    message_type: MessageType
    body: dict

    @classmethod
    def from_frame(cls, frame: Any) -> Message:

        message_type = MessageType.parse(frame.headers['MessageType'])
    
        bio = io.BytesIO()
        bio.write(str.encode('utf-16'))
        bio.seek(0)
        msg = zlib.decompress(frame.body, zlib.MAX_WBITS | 32)
        data = xmltodict.parse(msg)

        try:
            uR = data['Pport']['uR']
        except:
            print(data)

        return cls(message_type=message_type, body=uR)


@dataclass
class TSLocation:

    tpl: str
    wta: Optional[str] = None
    wtd: Optional[str] = None
    wtp: Optional[str] = None

    @classmethod
    def create(cls, data: dict):

        return cls(tpl=data['@tpl'], wtp=data.get('@wtp'), wta=data.get("@wta"), wtd=data.get('@wtd'))

    def __str__(self):
        date = self.wta if self.wta else self.wtp
        return f"{self.tpl}({date})"


@dataclass
class TSMessage:

    rid: str
    locations: list[TSLocation]

    @classmethod
    def create(cls, message: Message) -> TSMessage:

        ts = message.body['TS']

        rid = ts['@rid']
        locs = ts['ns5:Location']

        if type(locs) != list:
            locs = [locs]

        return cls(rid, [TSLocation.create(loc) for loc in locs])


    def get_stations(self) -> str:
        return f"{self.rid}: " + ",".join([str(loc) for loc in self.locations])

class MessageService:


    def parse(self, message: Message) -> None: 

        if message.message_type == MessageType.TS:
            ts_msg = TSMessage.create(message)
            data = ts_msg.get_stations()

            if data:
                print(data)

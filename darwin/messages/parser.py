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
            raise NoValidMessageTypeFound(f"{type} found")

@dataclass
class Message:

    message_type: MessageType
    body: dict

    @classmethod
    def from_frame(cls, frame: Any) -> Message:
        try:
            message_type = MessageType.parse(frame.headers['MessageType'])
        
            bio = io.BytesIO()
            bio.write(str.encode('utf-16'))
            bio.seek(0)
            msg = zlib.decompress(frame.body, zlib.MAX_WBITS | 32)
            data = xmltodict.parse(msg)

            return cls(message_type=message_type, body=data)

        except KeyError:
            raise Exception("Invalid headers")


    def get_station(self) -> Optional[str]:

        update_origin = self.body['Pport']['uR']['@updateOrigin']

        stations = self.body['Pport']['uR']['TS']['ns5:Location']

        return f"{update_origin}:" + ",".join([x['@tpl'] for x in stations])


        



class MessageService:


    def parse(self, message: Message) -> None: 

        if message.message_type == MessageType.TS:
            data =  message.get_station()
            if data:
                print(data)

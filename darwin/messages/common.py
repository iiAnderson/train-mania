from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import io
from typing import Any
import zlib
import xmltodict


class NoValidMessageTypeFound(Exception):
    ...

class MessageType(str, Enum):

    TS = "TS" # Actual and forecast information
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
            raise

        return cls(message_type=parsed_message_type, body=uR, timestamp=ts)
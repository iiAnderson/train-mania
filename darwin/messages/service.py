from __future__ import annotations
from dataclasses import asdict
import json
import os
from typing import Optional
from messages.ts import TSLocationMessage
from messages.common import MessageType, Message


class MessageService:

    def __init__(self, message_filter: Optional[MessageType] = None) -> None:

        self._message_filter = message_filter
        self._save_directory = "saved"

    def _save(self, message: TSLocationMessage) -> None:

        if not os.path.exists(self._save_directory):
            os.makedirs(self._save_directory)

        try:
            with open(f"{self._save_directory}/{message.rid}.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}

        data[message.timestamp.isoformat()] = [asdict(loc) for loc in message.locations]

        with open(f"{self._save_directory}/{message.rid}.json", "w") as f:
            json.dump(data, f)


    def parse(self, message: Message) -> None: 

        if self._message_filter and self._message_filter != message.message_type:
            return

        if message.message_type == MessageType.TS:
            ts_msg = TSLocationMessage.create(message)
            
            if ts_msg.filter_for("PADTON"):

                self._save(ts_msg)
        
        elif message.message_type == MessageType.SC:
            print("Schedule message")
            print(message.body)

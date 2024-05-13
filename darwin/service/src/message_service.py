from __future__ import annotations
from dataclasses import asdict
import json
import os
from typing import Optional

from darwin.messages.src.schedule import InvalidDarwinScheduleException, ScheduleParser, ScheduleTypeNotSupported, Train
from darwin.messages.src.ts import TSLocationMessage
from darwin.messages.src.common import MessageType, Message


class MessageService:

    def __init__(self, message_filter: Optional[MessageType] = None) -> None:

        self._message_filter = message_filter
        self._save_directory = "train_info"

    def _save_schedule(self, message: list[Train]) -> None:

        for msg in message:

            if not msg.filter("PADTON"):
                continue
                    
            print(f"{msg.ts}: {msg}")
            msg_name = msg.as_type()

            if not os.path.exists(f"{self._save_directory}/{msg_name}"):
                os.makedirs(f"{self._save_directory}/{msg_name}")

            try:
                with open(f"{self._save_directory}/{msg_name}/{msg.rid}.json", "r") as f:
                    data = [json.loads(line) for line in f]
                    print(f"Updating file wth lines {len(data)}")
            except FileNotFoundError:
                data = []
                print(f"Starting new file {len(data)}")
            
            data.extend(msg.as_dict())

            with open(f"{self._save_directory}/{msg_name}/{msg.rid}.json", "w") as f:
                f.write("\n".join([json.dumps(x) for x in data]))

    def parse(self, message: Message) -> None: 

        if self._message_filter and self._message_filter != message.message_type:
            return

        if message.message_type == MessageType.TS:
            ts_msg = TSLocationMessage.create(message)
            
            if ts_msg.filter_for("PADTON"):

                print(f"{ts_msg.rid}: {ts_msg.current} -> {ts_msg.destination}")
        
        elif message.message_type == MessageType.SC:
            
            try:
                msg = ScheduleParser.create(message.body, message.timestamp)

                if msg:
                    self._save_schedule(msg)
            except ScheduleTypeNotSupported as e:
                print(e)
            except InvalidDarwinScheduleException as e:
                pass


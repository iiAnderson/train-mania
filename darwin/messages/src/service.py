from __future__ import annotations
from dataclasses import asdict
import json
import os
from typing import Optional

from messages.src.schedule import InvalidDarwinScheduleException, ScheduleService, ScheduleTypeNotSupported, Train
from messages.src.ts import TSLocationMessage
from messages.src.common import MessageType, Message


class MessageService:

    def __init__(self, message_filter: Optional[MessageType] = None) -> None:

        self._message_filter = message_filter
        self._save_directory = "train_info"

    def _save(self, message: TSLocationMessage) -> None:

        if not os.path.exists(self._save_directory):
            os.makedirs(self._save_directory)

        try:
            with open(f"{self._save_directory}/{message.rid}.json", "r") as f:
                data = [json.loads(line) for line in f]
                print(f"Updating file wth lines {len(data)}")
        except FileNotFoundError:
            data = []
            print(f"Starting new file {len(data)}")


        data.extend(
            [
                {
                    **asdict(loc), 
                    **{
                        "rid": message.rid,
                        "ts": message.timestamp.isoformat()
                    }
                } for loc in message.locations
            ]
        )

        with open(f"{self._save_directory}/{message.rid}.json", "w") as f:
            f.write("\n".join([json.dumps(x) for x in data]))
        

    def _save_schedule(self, message: list[Train]) -> None:

        if not os.path.exists(self._save_directory):
            os.makedirs(self._save_directory)

        for msg in message:

            try:
                with open(f"{self._save_directory}/{msg.rid}.json", "r") as f:
                    data = [json.loads(line) for line in f]
                    print(f"Updating file wth lines {len(data)}")
            except FileNotFoundError:
                data = []
                print(f"Starting new file {len(data)}")

            with open(f"{self._save_directory}/{msg.rid}.json", "w") as f:
                f.write("\n".join([json.dumps(x) for x in msg.as_dict()]))

    def parse(self, message: Message) -> None: 

        if self._message_filter and self._message_filter != message.message_type:
            return

        if message.message_type == MessageType.TS:
            ts_msg = TSLocationMessage.create(message)
            
            if ts_msg.filter_for("PADTON"):

                self._save(ts_msg)
                print(f"{ts_msg.rid}: {ts_msg.current} -> {ts_msg.destination}")
        
        elif message.message_type == MessageType.SC:
            
            try:
                msg = ScheduleService.create(message.body, message.timestamp)

                if msg:
                    print(f"{message.timestamp}: {msg}")
                    self._save_schedule(msg)
            except ScheduleTypeNotSupported as e:
                print(e)
            except InvalidDarwinScheduleException as e:
                pass


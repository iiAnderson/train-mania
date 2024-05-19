from __future__ import annotations
from dataclasses import asdict
import json
import os
from typing import Optional

from darwin.messages.src.schedule import InvalidDarwinScheduleException, ScheduleParser, ScheduleTypeNotSupported, Train
from darwin.messages.src.ts import TSMessage, TSService
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

    def _save_ts(self, message: TSMessage) -> None:

        if not message.filter_for("BRSTLTM"):
            return
        
        if not os.path.exists(f"{self._save_directory}/"):
            os.makedirs(f"{self._save_directory}/")

        try:
            with open(f"{self._save_directory}/{message.service.uid}.json", "r") as f:
                data = [json.loads(line) for line in f]
                print(f"Updating file wth lines {len(data)}")
        except FileNotFoundError:
            data = []
            print(f"Starting new file {len(data)}")
        
        data.extend(message.format())

        with open(f"{self._save_directory}/{message.service.uid}.json", "w") as f:
            f.write("\n".join([json.dumps(x) for x in data]))

    def parse(self, message: Message) -> None: 

        if self._message_filter and self._message_filter != message.message_type:
            return

        if message.message_type == MessageType.TS:
            # print(message.body)
            ts_msg = TSService.parse(message)

            self._save_ts(ts_msg)
            
            if ts_msg.filter_for("BRSTLTM"):
                print(f"{ts_msg.service.uid}: {ts_msg.current} -> {ts_msg.destination}")
                print(ts_msg.format())
        
        elif message.message_type == MessageType.SC:
            
            try:
                msg = ScheduleParser.create(message.body, message.timestamp)

                if msg:
                    self._save_schedule(msg)
            except ScheduleTypeNotSupported as e:
                print(e)
            except InvalidDarwinScheduleException as e:
                pass


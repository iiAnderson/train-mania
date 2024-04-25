from __future__ import annotations
from dataclasses import asdict
import json
import os
from typing import Optional

from darwin.messages.schedule import CISSchedule, Schedule
from messages.ts import TSLocationMessage
from messages.common import MessageType, Message


class MessageService:

    def __init__(self, message_filter: Optional[MessageType] = None) -> None:

        self._message_filter = message_filter
        self._save_directory = "schedule"

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
        

    def _save_schedule(self, message: CISSchedule) -> None:

        if not os.path.exists(self._save_directory):
            os.makedirs(self._save_directory)

        for schedule in message.schedules:

            try:
                with open(f"{self._save_directory}/{schedule.rid}.json", "r") as f:
                    data = [json.loads(line) for line in f]
                    print(f"Updating file wth lines {len(data)}")
            except FileNotFoundError:
                data = []
                print(f"Starting new file {len(data)}")


            data.append(
                {
                    **asdict(schedule.origin),
                    **{
                        "rid": schedule.rid,
                        "type": "O",
                        "ts": schedule.ts.isoformat()
                    }
                }
            )

            data.extend(
                [
                    {
                        **asdict(interm),
                        **{
                            "rid": schedule.rid,
                            "type": "I",
                            "ts": schedule.ts.isoformat()
                        } 
                    } for interm in schedule.intermediate
                ]
            )


            data.append(
                {
                    **asdict(schedule.destination),
                    **{
                        "rid": schedule.rid,
                        "type": "D",
                        "ts": schedule.ts.isoformat()
                    }
                }
            )

            with open(f"{self._save_directory}/{schedule.rid}.json", "w") as f:
                f.write("\n".join([json.dumps(x) for x in data]))

    def parse(self, message: Message) -> None: 

        if self._message_filter and self._message_filter != message.message_type:
            return

        if message.message_type == MessageType.TS:
            ts_msg = TSLocationMessage.create(message)
            
            if ts_msg.filter_for("PADTON"):

                self._save(ts_msg)
                print(f"{ts_msg.rid}: {ts_msg.current} -> {ts_msg.destination}")
        
        elif message.message_type == MessageType.SC:
            msg = Schedule.create(message.body)

            if msg:
                self._save_schedule(msg)
                print(asdict(msg))

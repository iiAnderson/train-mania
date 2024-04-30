from datetime import datetime
import json
import os
from darwin.messages.src.schedule import Location, TrainLocations
import pytest
from freezegun import freeze_time

def get_json_fixture(file_name: str) -> dict:
    path = os.path.join(os.path.dirname(__file__), "schedule_fixtures", file_name)

    with open(path, 'r') as _file:
        return json.load(_file)


@freeze_time("2024-04-30")
class TestTrainLocations():

    @pytest.mark.parametrize(
        "input_dict,expected",
        [
            (
                get_json_fixture("cis_location_valid.json"),
                TrainLocations(
                    rid="rid1",
                    ts=datetime(2024, 4, 30),
                    origin=[
                        Location(
                            wta=None,
                            wtd=None,
                            pta=None,
                            ptd='23:25',
                            tpl='STNBGPK',
                            act='TB',
                            avg_loading=None,
                            cancelled=True,
                        )
                    ],
                    destination=[
                        Location(
                            wta='00:07',
                            wtd=None,
                            pta=None,
                            ptd=None,
                            tpl='LRDDEAC',
                            act='TFN ',
                            avg_loading=None,
                            cancelled=True,
                        )
                    ],
                    intermediate=[
                        Location(
                            wta='23:27',
                            wtd=None,
                            pta='23:27',
                            ptd='23:27',
                            tpl='HARLSDN',
                            act='T ',
                            avg_loading=None,
                            cancelled=True,
                        ),
                        Location(
                            wta='23:29',
                            wtd=None,
                            pta='23:29',
                            ptd='23:29',
                            tpl='WLSDNJL',
                            act='T ',
                            avg_loading=None,
                            cancelled=True,
                        )
                    ]
                )
            ),
            (
                get_json_fixture("cis_location_valid_2.json"),
                TrainLocations(
                    rid="rid1",
                    ts=datetime(2024, 4, 30),
                    origin=[
                        Location(
                            wta=None,
                            wtd=None,
                            pta=None,
                            ptd='23:25',
                            tpl='STNBGPK',
                            act='TB',
                            avg_loading=None,
                            cancelled=True,
                        ),
                        Location(
                            wta=None,
                            wtd=None,
                            pta=None,
                            ptd='23:30',
                            tpl='EDNRH',
                            act='TB',
                            avg_loading=None,
                            cancelled=False,
                        )
                    ],
                    destination=[
                        Location(
                            wta='00:07',
                            wtd=None,
                            pta=None,
                            ptd=None,
                            tpl='LRDDEAC',
                            act='TFN ',
                            avg_loading=None,
                            cancelled=True,
                        ),
                        Location(
                            wta='00:09',
                            wtd=None,
                            pta=None,
                            ptd=None,
                            tpl='PADTON',
                            act='TFN ',
                            avg_loading=None,
                            cancelled=False,
                        )
                    ],
                    intermediate=[
                        Location(
                            wta='23:27',
                            wtd=None,
                            pta='23:27',
                            ptd='23:27',
                            tpl='HARLSDN',
                            act='T ',
                            avg_loading=None,
                            cancelled=True,
                        ),
                        Location(
                            wta='23:29',
                            wtd=None,
                            pta='23:29',
                            ptd='23:29',
                            tpl='WLSDNJL',
                            act='T ',
                            avg_loading=None,
                            cancelled=True,
                        )
                    ]
                )
            )
        ]
    )
    def test_create(self, input_dict: dict, expected: TrainLocations) -> None:

        ts = datetime.utcnow()
        result = TrainLocations.create(input_dict, ts)

        assert result == expected



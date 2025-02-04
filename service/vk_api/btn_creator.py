import json

from service.vk_api.dataclasses import BtnData


class BtnCreator:
    def get_not_inline_keyboard(self, data: list[BtnData]):
        dict_data = {
            "one_time": True,
            "inline": False,
            "buttons": [
                [
                    {
                        "action": {
                            "type": "text",
                            "payload": btn.payload,
                            "label": btn.label,
                        },
                        "color": "primary",
                    }
                    for btn in data
                ]
            ],
        }
        return json.dumps(dict_data)

    def get_not_inline_callback_keyboard(
        self, data: list[BtnData], one_time: bool = False
    ):
        btn_rows = []
        btn_col = []
        for i, btn in enumerate(data):
            btn_col.append(
                {
                    "action": {
                        "type": "callback",
                        "payload": btn.payload,
                        "label": btn.label,
                    },
                    "color": "primary",
                }
            )
            if i % 2 != 0:
                btn_rows.append(btn_col)
                btn_col = []
        if btn_col:
            btn_rows.append(btn_col)
        dict_data = {
            "one_time": one_time,
            "inline": False,
            "buttons": btn_rows,
        }
        return json.dumps(dict_data)

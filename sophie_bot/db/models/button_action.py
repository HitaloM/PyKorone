from enum import Enum


class ButtonAction(str, Enum):
    url = "url"
    note = "note"
    delmsg = "delmsg"
    rules = "rules"
    captcha = "captcha"
    connect = "connect"
    sophiedm = "sophiedm"

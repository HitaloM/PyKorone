from aiogram.filters.callback_data import CallbackData
from beanie import PydanticObjectId


class DeleteWarnCallback(CallbackData, prefix="del_warn"):
    warn_iid: PydanticObjectId


class ResetWarnsCallback(CallbackData, prefix="reset_warns"):
    user_tid: int


class ResetAllWarnsCallback(CallbackData, prefix="reset_all_warns"):
    pass

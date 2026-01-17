from aiogram import Router

from .handlers import (
    AllowUsersConnectCmd,
    ConnectCallback,
    ConnectDMCmd,
    ConnectGroupCmd,
    DisconnectCmd,
    StartConnectHandler,
)

router = Router(name="connections")

__handlers__ = (
    ConnectDMCmd,
    ConnectGroupCmd,
    ConnectCallback,
    StartConnectHandler,
    DisconnectCmd,
    AllowUsersConnectCmd,
)

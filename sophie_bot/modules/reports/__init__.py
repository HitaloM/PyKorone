from aiogram import Router

from .handlers.report import ReportHandler

router = Router(name="reports")
__handlers__ = [ReportHandler]

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from sophie_bot.modules.filters.utils_.all_modern_actions import ALL_MODERN_ACTIONS

router = APIRouter(prefix="/actions", tags=["actions"])


class ActionInfo(BaseModel):
    name: str
    icon: str
    title: str
    as_filter: bool
    as_button: bool
    as_flood: bool


class ActionsListResponse(BaseModel):
    actions: list[ActionInfo]


@router.get("", response_model=ActionsListResponse)
async def list_all_actions() -> ActionsListResponse:
    """List all available modern actions."""
    actions = []
    for name, action in ALL_MODERN_ACTIONS.items():
        actions.append(
            ActionInfo(
                name=name,
                icon=action.icon,
                title=str(action.title),
                as_filter=action.as_filter,
                as_button=action.as_button,
                as_flood=action.as_flood,
            )
        )
    return ActionsListResponse(actions=actions)


@router.get("/flood", response_model=ActionsListResponse)
async def list_flood_actions() -> ActionsListResponse:
    """List actions that can be used as antiflood actions."""
    actions = []
    for name, action in ALL_MODERN_ACTIONS.items():
        if action.as_flood:
            actions.append(
                ActionInfo(
                    name=name,
                    icon=action.icon,
                    title=str(action.title),
                    as_filter=action.as_filter,
                    as_button=action.as_button,
                    as_flood=action.as_flood,
                )
            )
    return ActionsListResponse(actions=actions)


@router.get("/filter", response_model=ActionsListResponse)
async def list_filter_actions() -> ActionsListResponse:
    """List actions that can be used as filter actions."""
    actions = []
    for name, action in ALL_MODERN_ACTIONS.items():
        if action.as_filter:
            actions.append(
                ActionInfo(
                    name=name,
                    icon=action.icon,
                    title=str(action.title),
                    as_filter=action.as_filter,
                    as_button=action.as_button,
                    as_flood=action.as_flood,
                )
            )
    return ActionsListResponse(actions=actions)


@router.get("/button", response_model=ActionsListResponse)
async def list_button_actions() -> ActionsListResponse:
    """List actions that can be used as button actions."""
    actions = []
    for name, action in ALL_MODERN_ACTIONS.items():
        if action.as_button:
            actions.append(
                ActionInfo(
                    name=name,
                    icon=action.icon,
                    title=str(action.title),
                    as_filter=action.as_filter,
                    as_button=action.as_button,
                    as_flood=action.as_flood,
                )
            )
    return ActionsListResponse(actions=actions)

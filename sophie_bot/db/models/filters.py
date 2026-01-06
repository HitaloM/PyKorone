from typing import Annotated, Any, Optional, Self, TypeVar

from aiogram.fsm.context import FSMContext
from beanie import Document, Indexed
from beanie.odm.operators.update.general import Set
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field

ACTION_DATA_DUMPED = dict[str, Any] | None
ACTION_DATA = TypeVar("ACTION_DATA", bound=type[BaseModel] | None)


class FilterActionType(BaseModel):
    name: str
    data: Any


class FilterHandlerType(BaseModel):
    # Right now only keyword as string
    keyword: str


class FiltersModel(Document):
    # Old ID
    chat_id: Annotated[int, Indexed(unique=False)]

    handler: str  # old keyword handler

    action: Optional[str]  # None for modern filters
    actions: dict[str, ACTION_DATA_DUMPED] = Field(default_factory=dict)

    time: Optional[Any] = None

    model_config = ConfigDict(
        extra="allow",  # legacy workaround
    )

    class Settings:
        name = "filters"

    @staticmethod
    async def get_filters(chat_id: int) -> list["FiltersModel"] | None:
        return await FiltersModel.find(FiltersModel.chat_id == chat_id).to_list()

    @staticmethod
    async def get_by_keyword(chat_id: int, keyword: str) -> Optional["FiltersModel"]:
        return await FiltersModel.find_one(FiltersModel.chat_id == chat_id, FiltersModel.handler == keyword)

    @staticmethod
    async def get_legacy_by_keyword(chat_id: int, keyword: str) -> list["FiltersModel"]:
        return await FiltersModel.find(FiltersModel.chat_id == chat_id, FiltersModel.handler == keyword).to_list()

    @staticmethod
    async def get_by_id(oid: ObjectId):
        return await FiltersModel.find_one(FiltersModel.iid == oid)

    async def update_fields(self, filters_setup: "FilterInSetupType"):
        return await self.update(
            Set(
                {
                    "handler": filters_setup.handler.keyword,
                    "actions": filters_setup.actions,
                }
            )
        )


class FilterInSetupType(BaseModel):
    """Information about the filter, while being in the setup mode."""

    oid: Optional[str] = None  # Optional ObjectID of the FiltersModel object, if need to update, not save
    handler: FilterHandlerType
    actions: dict[str, ACTION_DATA_DUMPED]

    @staticmethod
    async def get_filter(state: FSMContext, data: Optional[dict[str, Any]] = None) -> "FilterInSetupType":
        if data and "filter_in_setup" in data:
            return FilterInSetupType.model_validate(data["filter_in_setup"])

        if filter_item := await state.get_value("filter_in_setup"):
            return FilterInSetupType.model_validate(filter_item)

        raise ValueError("No filter in setup")

    async def set_filter_state(self, state: FSMContext) -> Self:
        await state.update_data(filter_in_setup=self.model_dump(mode="json"))
        return self

    def to_model(self, chat_id: int) -> FiltersModel:
        return FiltersModel(
            chat_id=chat_id,
            handler=self.handler.keyword,
            action=None,
            actions=self.actions,
        )

    @staticmethod
    def from_model(model: FiltersModel) -> "FilterInSetupType":
        return FilterInSetupType(
            oid=str(model.iid),
            handler=FilterHandlerType(keyword=model.handler),
            actions=model.actions,
        )

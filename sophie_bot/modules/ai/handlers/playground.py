from __future__ import annotations

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from ass_tg.types import OptionalArg, TextArg
from pydantic_ai import ModelHTTPError
from stfu_tg import Doc, KeyValue, Section

from sophie_bot.config import CONFIG
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.user_status import IsOP
from sophie_bot.modules.ai.callbacks import AIPlaygroundCallback
from sophie_bot.modules.ai.fsm.playground import AIPlaygroundFSM
from sophie_bot.modules.ai.utils.ai_chatbot_reply import ai_chatbot_reply
from sophie_bot.modules.ai.utils.ai_models import (
    AI_MODEL_TO_PROVIDER,
    AI_MODEL_TO_SHORT_NAME,
    AI_MODELS,
    AI_PROVIDER_TO_NAME,
    PROVIDER_TO_MODELS,
)
from sophie_bot.utils.handlers import (
    SophieCallbackQueryHandler,
    SophieMessageHandler,
)


def build_playground_keyboard(selected_model: str | None = None) -> InlineKeyboardMarkup:
    """Build keyboard with all available AI models grouped by provider."""
    rows = []

    # Group models by provider for better organization
    for provider_name, model_enum in PROVIDER_TO_MODELS.items():
        provider_display = AI_PROVIDER_TO_NAME[provider_name]

        # Add provider header (non-clickable)
        rows.append([InlineKeyboardButton(text=f"── {provider_display} ──", callback_data="header")])  # Will be ignored

        # Collect model buttons for this provider
        model_buttons = []
        for model in model_enum:
            model_name = model.name
            display_name = AI_MODEL_TO_SHORT_NAME.get(model.value, model.value)
            mark = "🟢 " if model_name == selected_model else "⚪ "

            model_buttons.append(
                InlineKeyboardButton(
                    text=f"{mark}{display_name}", callback_data=AIPlaygroundCallback(model=model_name).pack()
                )
            )

        # Arrange model buttons in rows of 2
        for i in range(0, len(model_buttons), 2):
            row = model_buttons[i : i + 2]  # Take up to 2 buttons per row
            rows.append(row)

    return InlineKeyboardMarkup(inline_keyboard=rows)


@flags.args(
    text=OptionalArg(TextArg("Prompt to send to AI")),
)
@flags.help(exclude=True)
class AIPlaygroundCmd(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter(("aiplayground", "aiplay")), IsOP(is_op=True)

    async def handle(self):
        user_text = self.data.get("text")

        # Get current selected model for user from FSM state
        state: FSMContext = self.state
        data = await state.get_data()
        selected_model = data.get("selected_model")

        if user_text:
            # User provided text, process AI request with selected model
            if not selected_model:
                await self.event.reply("❌ Please select a model first using the buttons below.")
                return

            try:
                # Get the specific model from AI_MODELS
                model = AI_MODELS[selected_model]

                # Check if db_model exists
                if not self.connection.db_model:
                    await self.event.reply("❌ Chat is not initialized yet.")
                    return

                # Use ai_chatbot_reply with debug mode and custom model
                await ai_chatbot_reply(self.event, self.connection, user_text=user_text, debug_mode=True, model=model)

            except KeyError as err:
                await self.event.reply(f"❌ Model configuration error: {err}")
            except ModelHTTPError as err:
                await self.event.reply(f"❌ AI API error: {err}")
        else:
            # No text provided, show model selection interface
            kb = build_playground_keyboard(selected_model)

            current_model_text = "None selected"
            if selected_model:
                model_display = AI_MODEL_TO_SHORT_NAME.get(selected_model, selected_model)
                model_provider = AI_MODEL_TO_PROVIDER[selected_model]
                provider_display = AI_PROVIDER_TO_NAME[model_provider]
                current_model_text = f"{model_display} ({provider_display})"

            doc = Doc(
                Section(
                    KeyValue("Current Model", current_model_text),
                    "Select a model below, then use `/aiplayground <your prompt>` to test it.",
                    title="🤖 AI Playground",
                )
            )

            await self.event.reply(str(doc), reply_markup=kb)


class AIPlaygroundModelSelectCallback(SophieCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (AIPlaygroundCallback.filter(),)

    async def handle(self):
        await self.check_for_message()

        # Check if user is operator
        if not self.event.from_user or self.event.from_user.id not in CONFIG.operators:
            await self.event.answer("❌ This feature is only available for operators.")
            return

        data: AIPlaygroundCallback = self.callback_data
        selected_model = data.model

        # Ignore header clicks
        if selected_model == "header":
            await self.event.answer()
            return

        # Validate model exists
        if selected_model not in AI_MODEL_TO_PROVIDER:
            await self.event.answer("❌ Invalid model selection.")
            return

        # Update user's selected model in FSM state
        state: FSMContext = self.state
        await state.update_data(selected_model=selected_model)
        await state.set_state(AIPlaygroundFSM.selected_model)

        # Update the interface
        kb = build_playground_keyboard(selected_model)

        model_display = AI_MODEL_TO_SHORT_NAME.get(selected_model, selected_model)
        model_provider = AI_MODEL_TO_PROVIDER[selected_model]
        provider_display = AI_PROVIDER_TO_NAME[model_provider]

        doc = Doc(
            Section(
                KeyValue("Current Model", f"{model_display} ({provider_display})"),
                "Use `/aiplayground <your prompt>` to test this model.",
                title="AI Playground",
            )
        )

        if self.event.message and isinstance(self.event.message, Message):
            await self.event.message.edit_text(str(doc), reply_markup=kb)
        await self.event.answer(f"✅ Selected: {model_display}")

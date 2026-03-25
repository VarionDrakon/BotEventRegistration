from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from filters.main_filters import FilterAdministrator
from keyboards.main_keyboard import control_panel_keyboard
from messages.main_message import message_control_bot
from services.db_service import db_connection

control_bot_button_router = Router()
control_bot_button_router.message.filter(FilterAdministrator())

class ButtonInformation(StatesGroup):
    state_button_text_key = State()
    state_button_callback = State()
    state_menu_index = State()
    state_button_is_active = State()

@control_bot_button_router.callback_query(F.data == 'ask_button_control')
async def ask_button_control_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        message_control_bot(2),
        reply_markup=control_panel_keyboard('request_control_panel')
    )
    await callback.answer()
    await state.set_state(ButtonInformation.state_button_text_key)

@control_bot_button_router.message(ButtonInformation.state_button_text_key)
async def state_button_text_key_handler(message: Message, state: FSMContext):
    await state.update_data(state_button_text_key=message.text)
    await message.answer(                 
        message_control_bot(3),
        reply_markup=control_panel_keyboard('request_control_panel')
        )
    await state.set_state(ButtonInformation.state_button_callback)

@control_bot_button_router.message(ButtonInformation.state_button_callback)
async def state_button_callback_handler(message: Message, state: FSMContext):
    await state.update_data(state_button_callback=message.text)
    await message.answer(                 
        message_control_bot(4),
        reply_markup=control_panel_keyboard('request_control_panel')
        )
    await state.set_state(ButtonInformation.state_menu_index)

@control_bot_button_router.message(ButtonInformation.state_menu_index)
async def state_menu_index_handler(message: Message, state: FSMContext):
    try:
        value = int(message.text)
        await state.update_data(state_menu_index=value)
        await message.answer(                 
            message_control_bot(5),
            reply_markup=control_panel_keyboard('request_button_control_active_yes', 'request_button_control_active_no', 'request_control_panel')
            )
        await state.set_state(ButtonInformation.state_button_is_active)
    except:
        await message.answer(                 
            "Значение должно быть цифровым! Повторите ввод...",
            reply_markup=control_panel_keyboard('request_control_panel')
            )

@control_bot_button_router.callback_query(F.data.startswith('ask_button_control_active_yes'))
async def ask_button_control_active_yes_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(state_button_is_active=True)
    await ask_button_control_save_handler(callback, state)
    await callback.answer()

@control_bot_button_router.callback_query(F.data.startswith('ask_button_control_active_no'))
async def ask_button_control_active_no_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(state_button_is_active=False)
    await ask_button_control_save_handler(callback, state)
    await callback.answer()

@control_bot_button_router.callback_query(F.data == 'ask_button_control_save')
async def ask_button_control_save_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await db_connection.button_record_add(
        button_text_key=data["state_button_text_key"],
        button_callback=data["state_button_callback"],
        menu_index=int(data["state_menu_index"]),
        is_active=data["state_button_is_active"]
    )
    await callback.message.answer(
        "Кнопка добавлена",
        reply_markup=control_panel_keyboard('request_control_panel')
        )
    await state.clear()
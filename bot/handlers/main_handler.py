import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from keyboards.main_keyboard import main_keyboard, registration_questionnaire_keyboard, control_panel_keyboard
from filters.main_filters import FilterAdministrator
from messages.main_message import generate_start_message, message_user_panel
from services.db_service import db_connection
from run import feedback_chat_id

main_router = Router()

class MainForm(StatesGroup):
    state_feedback_waiting_text = State()

@main_router.message(F.text == '/start')
async def cmd_start_handler(message: Message):
    await db_connection.add_registration_user(message.from_user.id)
    await message.answer(generate_start_message(await db_connection.events_list_public_get(0, 3)), reply_markup=await main_keyboard(await FilterAdministrator()(message)))

@main_router.callback_query(F.data == 'information')
async def information_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        message_user_panel(callback.from_user.id, callback.from_user.username, 0), 
        reply_markup=registration_questionnaire_keyboard('request_cancel')
    )
    
@main_router.callback_query(F.data == 'feedback')
async def feedback_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        message_user_panel(None, None, 1),
        reply_markup=registration_questionnaire_keyboard('request_cancel')
    )
    await state.set_state(MainForm.state_feedback_waiting_text)

@main_router.callback_query(F.data == 'ask_answer_callback')
async def feedback_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        message_user_panel(None, None, 1),
        reply_markup=registration_questionnaire_keyboard('request_cancel')
    )
    await state.set_state(MainForm.state_feedback_waiting_text)
    await callback.answer()

@main_router.message(F.text, MainForm.state_feedback_waiting_text)
async def process_feedback_handler(message: Message, bot: Bot, state: FSMContext):
    try:
        await bot.send_message(
            chat_id=feedback_chat_id,
            text=f'{message_user_panel(None, None, 5)}'
                f'{message_user_panel(None, message.from_user.username, 6)}'
                f'{message_user_panel(message.from_user.id, None, 7)}'
                f'{message_user_panel(None, None, 8)}'
                f'{message.text}',
                reply_markup=control_panel_keyboard('request_control_feedback_answer', 'request_main_menu', telegram_user_id=message.from_user.id),
        )
        await message.answer(
            message_user_panel(None, None, 2),
            reply_markup=control_panel_keyboard('request_main_menu')
        )
    except TelegramBadRequest as e:
        if 'chat not found' in str(e):
         await message.answer(
                message_user_panel(None, None, 3),
                reply_markup=registration_questionnaire_keyboard('request_cancel')
            )
         logging.critical(f"Support chat not found! ID: {feedback_chat_id}")
        else:
            await message.answer(
                message_user_panel(None, None, 4),
                reply_markup=registration_questionnaire_keyboard('request_cancel')
            )
            logging.error(f"Error Telegram API: {e}")
    finally:
            await state.clear()
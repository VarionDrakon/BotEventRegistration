import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from keyboards.main_keyboard import main_keyboard, registration_questionnaire_keyboard, control_panel_keyboard
from filters.main_filters import FilterAdministrator
from messages.main_message import menu_start_message
from services.db_service import db_connection
from run import feedback_chat_id
from locales.localization import localization

main_router = Router()

class MainForm(StatesGroup):
    state_feedback_waiting_text = State()

@main_router.message(F.text == '/start')
async def cmd_start_handler(message: Message):
    await db_connection.add_registration_user(message.from_user.id)
    await message.answer(await menu_start_message(),
                         reply_markup=await main_keyboard(await FilterAdministrator()(message)))

@main_router.callback_query(F.data == 'information')
async def information_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        localization.get('common.text.user_panel.information', 
                         username=callback.from_user.username or "{Null}", 
                         telegram_user_id=callback.from_user.id),
        reply_markup=registration_questionnaire_keyboard('request_main_menu')
    )
    
@main_router.callback_query(F.data == 'feedback')
async def feedback_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        localization.get('common.text.user_panel.feedback.message_notification_write'),
        reply_markup=registration_questionnaire_keyboard('request_main_menu')
    )
    await state.set_state(MainForm.state_feedback_waiting_text)

@main_router.callback_query(F.data == 'ask_answer_callback')
async def feedback_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        localization.get('common.text.user_panel.feedback.message_notification_write'),
        reply_markup=registration_questionnaire_keyboard('request_main_menu')
    )
    await state.set_state(MainForm.state_feedback_waiting_text)
    await callback.answer()

@main_router.message(F.text, MainForm.state_feedback_waiting_text)
async def process_feedback_handler(message: Message, bot: Bot, state: FSMContext):
    try:
        await bot.send_message(
            chat_id=feedback_chat_id,
            text=localization.get('common.text.control_panel.feedback.message_support_new', 
                                  username=message.from_user.username or "{Null}", 
                                  telegram_user_id=message.from_user.id,
                                  user_message=message.text),
            reply_markup=control_panel_keyboard('request_control_feedback_answer',
                                                'request_main_menu', 
                                                telegram_user_id=message.from_user.id),
        )
        await message.answer(
            localization.get('common.text.user_panel.feedback.message_notification_success'),
            reply_markup=control_panel_keyboard('request_main_menu')
        )
    except TelegramBadRequest as e:
        if 'chat not found' in str(e):
         await message.answer(
                localization.get('common.text.user_panel.feedback.configuration_error'),
                reply_markup=registration_questionnaire_keyboard('request_main_menu')
            )
         logging.critical(f"Support chat not found! ID: {feedback_chat_id}")
        else:
            await message.answer(
                localization.get('common.text.user_panel.feedback.message_notification_error'),
                reply_markup=registration_questionnaire_keyboard('request_main_menu')
            )
            logging.error(f"Error Telegram: {e}")
    finally:
            await state.clear()
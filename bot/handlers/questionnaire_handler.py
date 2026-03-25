import asyncio
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keyboards.main_keyboard import main_keyboard, registration_questionnaire_keyboard, generate_registration_questionnaire_events_keyboard
from messages.main_message import generate_start_message, cancel_registration_message, create_registratoin_message, filling_questionnaire_form_message, finish_registratoin_message
from services.db_service import db_connection
from filters.main_filters import FilterAdministrator

questionnaire_router = Router()

class RegistrationForm(StatesGroup):
    state_event_number = State()
    state_event_name = State()
    state_event_date = State()
    nickname = State()
    telegram_username = State()
    addition_information = State()

# Decorator block: additional

@questionnaire_router.callback_query(F.data == 'ask_cancel_registration')
async def cancel_registration_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(cancel_registration_message())
    await asyncio.sleep(1)
    await callback.message.edit_text(
        generate_start_message(await db_connection.events_list_public_get(0, 3)), 
        reply_markup=await main_keyboard(await FilterAdministrator()(callback))
    )
    await state.clear()
    await callback.answer()

# Remove/Cancel registration on selected event
@questionnaire_router.callback_query(F.data == 'event_cancel_registration')
async def event_cancel_registration_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        cancel_registration_message(1),
        reply_markup=generate_registration_questionnaire_events_keyboard(await db_connection.events_list_get(), False, "request_cancel" )
    )

@questionnaire_router.callback_query(F.data.startswith('event_cancel_'))
async def capture_event_cancel_selection_handler(callback: CallbackQuery, state: FSMContext):
    selection_event_id = int(callback.data.removeprefix('event_cancel_'))
    await state.clear()
    await state.update_data(state_event_number=selection_event_id)
    await callback.message.edit_text(
        cancel_registration_message(2),
        reply_markup=registration_questionnaire_keyboard('request_event_cancel_registration', 'request_cancel')
    )
    await callback.answer()

@questionnaire_router.callback_query(F.data == 'ask_event_cancel_registration')
async def event_cancel_registration_handler(callback: CallbackQuery, state: FSMContext):
    form_data = await state.get_data()
    await db_connection.add_registration_user(callback.from_user.id)
    status = await db_connection.registration_record_add (
        form_data.get('state_event_number'),
        callback.from_user.id, 
        None, 
        None, 
        None,
        f'Не приду'
    )
    if status:
        await asyncio.sleep(1)
        await callback.message.edit_text(
            cancel_registration_message(4),
            reply_markup=registration_questionnaire_keyboard('request_cancel')
        )
        await state.clear()
        await callback.answer()
    else:
        await callback.message.edit_text (
            cancel_registration_message(3),
            reply_markup=registration_questionnaire_keyboard('request_questionnaire', 'request_cancel')
        )
    
# Decorator block: registration

@questionnaire_router.callback_query(F.data == 'event_create_registration')
async def event_create_registration_handler(callback: CallbackQuery, state: FSMContext):
    if await db_connection.get_events_count():
        await callback.message.edit_text(
                create_registratoin_message(0),
                reply_markup=registration_questionnaire_keyboard("request_questionnaire", "request_cancel")
            )
    else:
        await callback.message.edit_text(
                create_registratoin_message(1),
                reply_markup=registration_questionnaire_keyboard("request_cancel")
            )
    await callback.answer()

# Decorator block: questionnaire

@questionnaire_router.callback_query(F.data == 'ask_questionnaire')
async def ask_questionnaire_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
            filling_questionnaire_form_message(0),
            reply_markup=generate_registration_questionnaire_events_keyboard(await db_connection.events_list_get(), True, "request_cancel")
        )

@questionnaire_router.callback_query(F.data.startswith('event_'))
async def capture_event_selection_handler(callback: CallbackQuery, state: FSMContext):
    selection_event_id = int(callback.data.removeprefix('event_'))
    selection_event_details = await db_connection.event_get_details(selection_event_id)
    await state.update_data(
        state_event_number = f'{selection_event_id}', 
        state_event_name = f'{selection_event_details['event_name']}',
        state_event_date = f'{selection_event_details['event_date']}'
        )
    form_data = await state.get_data()
    await callback.message.edit_text(
        filling_questionnaire_form_message(1, form_data),
        reply_markup=registration_questionnaire_keyboard("request_questionnaire_registration_nickname_skip", "request_cancel")
    )
    await state.set_state(RegistrationForm.nickname)
    await callback.answer()

@questionnaire_router.callback_query(F.data == 'ask_questionnaire_registration_nickname_skip')
async def ask_questionnaire_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(nickname="Не указано.")
    form_data = await state.get_data()
    if not callback.message.from_user.username:
        await callback.message.answer(
            filling_questionnaire_form_message(5, form_data),
            reply_markup=registration_questionnaire_keyboard("request_questionnaire_registration_check_username", "request_cancel")
        )
        return
    await callback.message.answer(
            filling_questionnaire_form_message(2, form_data),
            reply_markup=registration_questionnaire_keyboard("request_username", "request_cancel")
        )
    await state.set_state(RegistrationForm.telegram_username)
    await callback.answer()

@questionnaire_router.message(RegistrationForm.nickname, F.text)
async def capture_nickname_handler(message: Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    form_data = await state.get_data()
    if not message.from_user.username:
        await message.answer(
            filling_questionnaire_form_message(5, form_data),
            reply_markup=registration_questionnaire_keyboard("request_questionnaire_registration_check_username", "request_cancel")
        )
        return
    await message.answer(
            filling_questionnaire_form_message(2, form_data),
            reply_markup=registration_questionnaire_keyboard("request_username", "request_cancel")
        )
    await state.set_state(RegistrationForm.telegram_username)

@questionnaire_router.callback_query(F.data == "ask_questionnaire_registration_check_username")
async def check_username_handler(callback: CallbackQuery, state: FSMContext):
    form_data = await state.get_data()
    if not callback.from_user.username:
        await callback.message.answer(
            filling_questionnaire_form_message(6, form_data),
            reply_markup=registration_questionnaire_keyboard("request_questionnaire_registration_check_username", "request_cancel")
        )
        await callback.answer()
        return
    await state.update_data(telegram_username=callback.from_user.username)
    form_data = await state.get_data()
    
    await callback.message.edit_text(
        filling_questionnaire_form_message(2, form_data),
        reply_markup=registration_questionnaire_keyboard("request_username", "request_cancel")
    )
    await state.set_state(RegistrationForm.telegram_username)

@questionnaire_router.callback_query(RegistrationForm.telegram_username)
async def capture_telegram_username_handler(callback: CallbackQuery, state: FSMContext):
    username = callback.from_user.username or "null"
    await state.update_data(telegram_username=f'{username}')
    form_data = await state.get_data()
    await callback.message.edit_text(
            filling_questionnaire_form_message(3, form_data),
            reply_markup=registration_questionnaire_keyboard("request_questionnaire_registration_additional_information_skip", "request_cancel")
        )
    await state.set_state(RegistrationForm.addition_information)
    await callback.answer()

@questionnaire_router.callback_query(F.data == 'ask_questionnaire_registration_additional_information_skip')
async def ask_questionnaire_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(addition_information="Не указано.")
    form_data = await state.get_data()
    await callback.message.answer(
        filling_questionnaire_form_message(4, form_data),
        reply_markup=registration_questionnaire_keyboard("request_confirmation", "request_reject")
    )
    await callback.answer()

# Decorator block: return information

@questionnaire_router.message(RegistrationForm.addition_information, F.text)
async def capture_addition_information_handler(message: Message, state: FSMContext):
    await state.update_data(addition_information=message.text)
    form_data = await state.get_data()
    await message.answer(
        filling_questionnaire_form_message(4, form_data),
        reply_markup=registration_questionnaire_keyboard("request_confirmation", "request_reject")
    )

@questionnaire_router.callback_query(F.data == 'ask_confirmation')
async def ask_confirmation_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(finish_registratoin_message(0))
    form_data = await state.get_data()
    await db_connection.add_registration_user(callback.from_user.id)
    status = await db_connection.registration_record_add (
        form_data.get('state_event_number'), 
        callback.from_user.id, 
        form_data.get('nickname'), 
        form_data.get('telegram_username'), 
        form_data.get('addition_information'),
        f'Приду'
    )
    if status:
        await asyncio.sleep(1)
        await callback.message.edit_text(generate_start_message(await db_connection.events_list_public_get(0, 3)), reply_markup=await main_keyboard(await FilterAdministrator()(callback)))
        await state.clear()
        await callback.answer()
    else:
        await callback.message.edit_text (
            finish_registratoin_message(1),
            reply_markup=registration_questionnaire_keyboard("request_questionnaire", "request_cancel")
        )

@questionnaire_router.callback_query(F.data == 'ask_reject')
async def ask_reject_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(finish_registratoin_message(1))
    await state.set_data({})
    await asyncio.sleep(1)
    await callback.answer()
    await event_create_registration_handler(callback, state)
import asyncio
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keyboards.main_keyboard import main_keyboard, registration_questionnaire_keyboard, generate_registration_questionnaire_events_keyboard
from messages.main_message import menu_start_message
from services.db_service import db_connection
from datetime import datetime
from filters.main_filters import FilterAdministrator
from locales.localization import localization

questionnaire_router = Router()

class RegistrationForm(StatesGroup):
    state_event_number = State()
    state_event_name = State()
    state_event_date = State()
    nickname = State()
    telegram_username = State()
    addition_information = State()

# region Registration - Create

@questionnaire_router.callback_query(F.data == 'event_create_registration')
async def event_create_registration_handler(callback: CallbackQuery, state: FSMContext):
    if await db_connection.get_events_count():
        await callback.message.edit_text(
                localization.get('common.text.user_panel.registration.create.requirements'),
                reply_markup=registration_questionnaire_keyboard("request_questionnaire", "request_main_menu")
            )
    else:
        await callback.message.edit_text(
                localization.get('common.text.user_panel.registration.create.no_event'),
                reply_markup=registration_questionnaire_keyboard("request_main_menu")
            )
    await callback.answer()

@questionnaire_router.callback_query(F.data == 'ask_questionnaire')
async def ask_questionnaire_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
            localization.get('common.text.user_panel.registration.create.steps.event'),
            reply_markup=generate_registration_questionnaire_events_keyboard(await db_connection.events_list_public_get(), True, "request_cancel")
        )
# Step choose event:
@questionnaire_router.callback_query(F.data.startswith('event_register_id_'))
async def capture_event_selection_handler(callback: CallbackQuery, state: FSMContext):
    selection_event_id = int(callback.data.removeprefix('event_register_id_'))
    selection_event_details = await db_connection.event_get_details(selection_event_id)
    await state.update_data(state_event_number = f'{selection_event_id}',
                            state_event_name = f'{selection_event_details['event_name']}',
                            state_event_date = f'{selection_event_details['event_date']}')
    form_data = await state.get_data()
    await callback.message.edit_text(localization.get('common.text.user_panel.registration.create.steps.nickname',
                                                      state_event_name=form_data.get('state_event_name'),
                                                      state_event_date=form_data.get('state_event_date')),
                                    reply_markup=registration_questionnaire_keyboard("request_questionnaire_registration_nickname_skip", "request_cancel"))
    await state.set_state(RegistrationForm.nickname)
    await callback.answer()
# Step nickname:
@questionnaire_router.callback_query(F.data == 'ask_questionnaire_registration_nickname_skip')
async def ask_questionnaire_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(nickname=localization.get('system.text.common.not_specified'))
    form_data = await state.get_data()
    if not callback.message.from_user.username:
        await callback.message.answer(localization.get('system.text.menu.registration.username_not_set',
                                                       state_event_name=form_data.get('state_event_name'),
                                                       state_event_date=form_data.get('state_event_date')),
                                    reply_markup=registration_questionnaire_keyboard("request_questionnaire_registration_check_username", "request_cancel"))
        return
    await callback.message.answer(localization.get('common.text.user_panel.registration.create.steps.username',
                                                   state_event_name=form_data.get('state_event_name'),
                                                   state_event_date=form_data.get('state_event_date'),
                                                   nickname=form_data.get('nickname')),
                                reply_markup=registration_questionnaire_keyboard("request_username", "request_cancel"))
    await state.set_state(RegistrationForm.telegram_username)
    await callback.answer()

@questionnaire_router.message(RegistrationForm.nickname, F.text)
async def capture_nickname_handler(message: Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    form_data = await state.get_data()
    if not message.from_user.username:
        await message.answer(localization.get('system.text.menu.registration.username_not_set'),
                            reply_markup=registration_questionnaire_keyboard("request_questionnaire_registration_check_username", "request_cancel"))
        return
    await message.answer(localization.get('common.text.user_panel.registration.create.steps.username',
                                          state_event_name=form_data.get('state_event_name'),
                                          state_event_date=form_data.get('state_event_date'),
                                          nickname=form_data.get('nickname')),
                        reply_markup=registration_questionnaire_keyboard("request_username", "request_cancel"))
    await state.set_state(RegistrationForm.telegram_username)
# Step telegram username:
@questionnaire_router.callback_query(F.data == "ask_questionnaire_registration_check_username")
async def check_username_handler(callback: CallbackQuery, state: FSMContext):
    form_data = await state.get_data()
    if not callback.from_user.username:
        await callback.message.answer(localization.get('system.text.menu.registration.username_not_set'),
                                    reply_markup=registration_questionnaire_keyboard("request_questionnaire_registration_check_username", "request_cancel"))
        await callback.answer()
        return
    await state.update_data(telegram_username=callback.from_user.username)
    form_data = await state.get_data()
    await callback.message.edit_text(localization.get('common.text.user_panel.registration.create.steps.additional',
                                                      state_event_name=form_data.get('state_event_name'),
                                                      state_event_date=form_data.get('state_event_date'),
                                                      nickname=form_data.get('nickname'),
                                                      telegram_username=form_data.get('telegram_username')),
                                    reply_markup=registration_questionnaire_keyboard("request_username", "request_cancel"))
    await state.set_state(RegistrationForm.telegram_username)

@questionnaire_router.callback_query(F.data == 'ask_username', RegistrationForm.telegram_username)
async def capture_telegram_username_handler(callback: CallbackQuery, state: FSMContext):
    username = callback.from_user.username or localization.get('system.text.common.not_specified')
    await state.update_data(telegram_username=f'{username}')
    form_data = await state.get_data()
    await callback.message.edit_text(localization.get('common.text.user_panel.registration.create.steps.additional',
                                                      state_event_name=form_data.get('state_event_name'),
                                                      state_event_date=form_data.get('state_event_date'),
                                                      nickname=form_data.get('nickname'),
                                                      telegram_username=form_data.get('telegram_username')),
                                    reply_markup=registration_questionnaire_keyboard("request_questionnaire_registration_additional_information_skip", "request_cancel"))
    await state.set_state(RegistrationForm.addition_information)
    await callback.answer()
# Step additional information
@questionnaire_router.message(RegistrationForm.addition_information, F.text)
async def capture_addition_information_handler(message: Message, state: FSMContext):
    await state.update_data(addition_information=message.text)
    form_data = await state.get_data()
    await message.answer(localization.get('common.text.user_panel.registration.create.steps.confirmation',
                                                   state_event_name=form_data.get('state_event_name'),
                                                   state_event_date=form_data.get('state_event_date'),
                                                   nickname=form_data.get('nickname'),
                                                   telegram_username=form_data.get('telegram_username'),
                                                   addition_information=form_data.get('addition_information')),
                        reply_markup=registration_questionnaire_keyboard("request_confirmation", "request_reject"))

@questionnaire_router.callback_query(F.data == 'ask_questionnaire_registration_additional_information_skip')
async def ask_questionnaire_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(addition_information=localization.get('system.text.common.not_specified'))
    form_data = await state.get_data()
    await callback.message.answer(localization.get('common.text.user_panel.registration.create.steps.confirmation',
                                                   state_event_name=form_data.get('state_event_name'),
                                                   state_event_date=form_data.get('state_event_date'),
                                                   nickname=form_data.get('nickname'),
                                                   telegram_username=form_data.get('telegram_username'),
                                                   addition_information=form_data.get('addition_information')),
                                reply_markup=registration_questionnaire_keyboard("request_confirmation", "request_reject"))
    await callback.answer()
# Step confirmation information and registration
@questionnaire_router.callback_query(F.data == 'ask_confirmation')
async def ask_confirmation_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(localization.get('system.text.menu.registration.successful', time=datetime.now()),
                                    reply_markup=registration_questionnaire_keyboard('request_main_menu'))
    form_data = await state.get_data()
    await db_connection.add_registration_user(callback.from_user.id)
    status = await db_connection.registration_record_add(event_id=form_data.get('state_event_number'),
                                                         telegram_user_id=callback.from_user.id,
                                                         nickname=form_data.get('nickname'),
                                                         telegram_username=form_data.get('telegram_username'),
                                                         additional_information=form_data.get('addition_information'),
                                                         status=localization.get('system.text.event.registration.will_come'))
    if status:
        await state.clear()
        await callback.answer()
    else:
        await callback.message.answer(localization.get('system.text.menu.registration.reset_registration'),
                                       reply_markup=registration_questionnaire_keyboard("request_questionnaire", "request_cancel"))

@questionnaire_router.callback_query(F.data == 'ask_reject')
async def ask_reject_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(localization.get('system.text.menu.registration.reset_registration'))
    await state.set_data({})
    await callback.answer()
    await event_create_registration_handler(callback, state)

# endregion

# region Registration - Cancel

@questionnaire_router.callback_query(F.data == 'ask_cancel_registration')
async def cancel_registration_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(localization.get('system.text.menu.return'))
    await callback.message.edit_text(await menu_start_message(),
                                     reply_markup=await main_keyboard(await FilterAdministrator()(callback)))
    await state.clear()
    await callback.answer()

@questionnaire_router.callback_query(F.data == 'event_cancel_registration')
async def event_cancel_registration_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(localization.get('common.text.user_panel.registration.cancel.event'),
                                     reply_markup=generate_registration_questionnaire_events_keyboard(await db_connection.events_list_public_get(), False, "request_main_menu" ))
    await state.clear()
    await callback.answer()

@questionnaire_router.callback_query(F.data.startswith('event_refuse_id_'))
async def capture_event_cancel_selection_handler(callback: CallbackQuery, state: FSMContext):
    selection_event_id = int(callback.data.removeprefix('event_refuse_id_'))
    await state.update_data(state_event_number=selection_event_id)

    await callback.message.edit_text(
        localization.get('common.text.user_panel.registration.cancel.confirmation'),
        reply_markup=registration_questionnaire_keyboard('request_event_cancel_registration', 'request_main_menu')
    )
    await callback.answer()

@questionnaire_router.callback_query(F.data == 'ask_event_cancel_registration')
async def ask_event_cancel_registration_handler(callback: CallbackQuery, state: FSMContext):
    form_data = await state.get_data()
    await db_connection.add_registration_user(callback.from_user.id)
    status = await db_connection.registration_record_add(
        form_data.get('state_event_number'),
        telegram_user_id=callback.from_user.id,
        status=localization.get('system.text.event.registration.wont_come'))
    if status:
        await callback.message.edit_text(localization.get('system.text.menu.registration.canceled', time=datetime.now()),
                                         reply_markup=registration_questionnaire_keyboard('request_main_menu'))
        await state.clear()
        await callback.answer()
    else:
        await callback.message.edit_text(localization.get('system.text.menu.registration.error'),
                                          reply_markup=registration_questionnaire_keyboard('request_questionnaire', 'request_main_menu'))

# endregion
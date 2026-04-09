import asyncio
import os
import logging
from run import bot, version_bot
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from filters.main_filters import FilterAdministrator
from messages.main_message import menu_start_message
from keyboards.main_keyboard import main_keyboard, control_panel_keyboard, control_panel_events_keyboard, control_panel_event_edit_keyboard, control_panel_administrators_edit_keyboard
from services.db_service import db_connection
from locales.localization import localization

control_router = Router()
control_router.message.filter(FilterAdministrator())

class EventInformation(StatesGroup):
    state_event_id = State()
    state_event_name = State()
    state_event_date = State()
    state_event_organisation_id = State()
    state_event_status = State()
    state_administrators_telegram = State()
    state_administrators_organization_id = State()
    state_administrators_telegram_status = State()
    state_telegram_user_ids = State()
    state_telegram_user_target_id = State()
    state_newsletter_wait_text = State()
    state_newsletter_callback = State()

@control_router.callback_query(F.data == 'ask_control_panel')
async def request_control_panel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(localization.get('common.text.control_panel.menu.wellcome',
                                                   version=version_bot,
                                                   telegram_chat_id=callback.message.chat.id),
        reply_markup=control_panel_keyboard('request_control_events',
                                            'request_notification_broadcast',
                                            'request_control_users_list',
                                            'request_control_bot',
                                            'request_control_administrators',
                                            'request_main_menu'))
    await callback.answer()

# region Users management

@control_router.callback_query(F.data == 'ask_control_users_list')
async def users_list_handler(callback: CallbackQuery):
    csv_data = await db_connection.users_get_list_csv()
    date_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"users_list_{date_time}.csv"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(csv_data)
    await callback.message.answer_document(document=FSInputFile(filename),
                                           caption=localization.get('common.text.control_panel.users.list_found'))
    await callback.message.answer(localization.get('common.text.control_panel.users.list_file_export_csv',
                                                   time=datetime.now()),
                                  reply_markup=control_panel_keyboard('request_control_panel'))
    os.remove(filename)
    await callback.answer()

# endregion

# region System management

@control_router.callback_query(F.data == 'ask_control_bot')
async def control_bot_handler(callback: CallbackQuery):
    await callback.message.edit_text(localization.get('common.text.control_panel.bot.plug', time=datetime.now()),
                                     reply_markup=control_panel_keyboard('request_control_panel'))

# endregion

# region Administrators management

@control_router.callback_query(F.data == 'ask_control_administrators')
async def ask_control_administrators_handler(callback: CallbackQuery):
    administrators_list = await db_connection.administrators_list()
    message_text = localization.get('common.text.control_panel.administrator.list_found')
    
    for i, administrator in enumerate(administrators_list, 1):
        telegram_user_id = administrator['telegram_user_id']
        telegram_username = 'None' if administrator['telegram_username'] is None else f'@{administrator['telegram_username']}'
        organization_id = administrator['organization_id'] 
        join_date = administrator['join_date']
        message_text += f'<pre><b>{i}. TG ID   :</b> {telegram_user_id}\n' \
                        f'<b>{i}. Username:</b> {telegram_username}\n' \
                        f'<b>{i}. Added   :</b> {join_date}\n' \
                        f'<b>{i}. Org id  :</b> {organization_id}\n\n</pre>'
    message_text += (localization.get('common.text.control_panel.administrator.explanation_terms'))
    await callback.message.edit_text(
        message_text,
        reply_markup=control_panel_administrators_edit_keyboard(
            'request_control_administrators_add',
            'request_control_administrators_delete',
            'request_control_administrators_list', 
            'request_control_panel'
        )
    )
    await callback.answer()

@control_router.callback_query(F.data == 'ask_control_administrators_add')
async def ask_control_administrators_add_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(localization.get('common.text.control_panel.administrator.adding_new_id_telegram'),
                                     reply_markup=control_panel_administrators_edit_keyboard('request_control_panel'))
    await state.update_data(state_administrators_telegram_status = 1)
    await state.set_state(EventInformation.state_administrators_telegram)

@control_router.callback_query(F.data == 'ask_control_administrators_delete')
async def ask_control_administrators_delete_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(localization.get('common.text.control_panel.administrator.removing'),
                                     reply_markup=control_panel_administrators_edit_keyboard('request_control_panel'))
    await state.update_data(state_administrators_telegram_status = 0)
    await state.set_state(EventInformation.state_administrators_telegram)

@control_router.message(F.text | F.contact | F.forward_from, EventInformation.state_administrators_telegram)
async def universal_admin_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    action = data.get('state_administrators_telegram_status', 1)
    user_id = None
    username = None
    # Handler forward message
    if message.forward_from:
        user_id = message.forward_from.id
        username = message.forward_from.username
    # Handler contact
    elif message.contact and message.contact.user_id:
        user_id = message.contact.user_id
    # Handler text
    elif message.text:
        text = message.text.strip()
        # Numberic ID (without username)
        if text.isdigit():
            user_id = int(text)
        # Trying to extract username and ID
        else:
            # Extract username from any format
            if '@' in text:
                username = text.split('@')[-1].split()[0]
            elif 't.me/' in text:
                username = text.split('t.me/')[-1].split('/')[0].split('?')[0]
            else:
                username = text.split()[0]  # Simple text
            # Cleaning up the trash
            username = ''.join(c for c in username if c.isalnum() or c == '_')[:32] if username else None
            # Trying to get ID by username
            if username:
                try:
                    user = await bot.get_chat(f"@{username}")
                    user_id = user.id
                except:
                    pass  # Failed - username ignored
    if action == 1:  # Added
        if user_id:  # Only with ID
            await message.answer(localization.get('common.text.control_panel.administrator.adding_new_id_organization', telegram_user_id=user_id),
                                 reply_markup=control_panel_administrators_edit_keyboard('request_control_panel'))
            await state.update_data(state_administrators_telegram = user_id) ### BUG!
            await state.set_state(EventInformation.state_administrators_organization_id)
        else:
            await message.answer(localization.get('common.text.control_panel.administrator.error_id_get'),
                                 reply_markup=control_panel_administrators_edit_keyboard('request_control_panel'))
    else:  # Delete administrator
        if user_id:
            await db_connection.administrators_del(user_id)
            await message.answer(
                f'{user_id}',
                reply_markup=control_panel_administrators_edit_keyboard('request_control_panel')
            )
            await state.clear()
        else:
            await message.answer(localization.get('common.text.control_panel.administrator.removing_notification_id'),
                                 reply_markup=control_panel_administrators_edit_keyboard('request_control_panel'))

@control_router.message(F.text, EventInformation.state_administrators_organization_id)
async def state_administrator_organization_id_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    data_administrator_id = data.get('state_administrators_telegram')
    await state.update_data(state_administrators_organization_id=message.text)
    await message.answer(localization.get('common.text.control_panel.administrator.removing_notification_id', organization_id=data_administrator_id),
        reply_markup=control_panel_administrators_edit_keyboard('request_control_panel'))
    await db_connection.administrators_add(data_administrator_id, message.text)
    await state.clear()

@control_router.callback_query(F.data == 'ask_control_administrators_list')
async def users_list_handler(callback: CallbackQuery):
    csv_data = await db_connection.administrators_get_list_csv()
    date_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"users_list_{date_time}.csv"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(csv_data)
    await callback.message.answer_document(document=FSInputFile(filename),
            caption=localization.get('common.text.control_panel.administrator.list_found'))
    await callback.message.answer(localization.get('common.text.control_panel.administrator.list_file_export_csv', time=date_time),
                                  reply_markup=control_panel_keyboard('request_control_panel'))
    os.remove(filename)
    await callback.answer()

# endregion

# region Events management

@control_router.callback_query(F.data == 'ask_main_menu')
async def main_menu_handler(callback: CallbackQuery):
    await callback.message.answer(await menu_start_message(),
                                  reply_markup=await main_keyboard(await FilterAdministrator()(callback)))
    await callback.answer()

@control_router.callback_query(F.data == 'ask_control_events_list')
async def ask_control_events_list_handler(callback: CallbackQuery):
    await show_events_page_handler(callback=callback.message, telegram_user_id=callback.from_user.id)  

@control_router.callback_query(F.data == 'ask_control_event_create')
async def ask_control_event_create_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(EventInformation.state_event_name)
    await callback.message.edit_text(localization.get('common.text.control_panel.event.action_modify.event_name',
                                                      action=localization.get('common.text.control_panel.event.action_modify.new'),
                                                      event_id=None),
                                     reply_markup=control_panel_keyboard('request_control_panel'))
    await callback.answer()

@control_router.callback_query(F.data.startswith('ask_edit_event_'))
async def capture_event_edit_handler(callback: CallbackQuery):
    selection_event_id = int(callback.data.removeprefix('ask_edit_event_'))
    selection_event_details = await db_connection.event_get_details(selection_event_id)
    selection_participants_count = await db_connection.event_get_participants_count(selection_event_id)
    await callback.message.edit_text(localization.get('common.text.control_panel.event.information_event_id', 
                                                      event_id=selection_event_id,
                                                      event_id_db=selection_event_details['event_id'],
                                                      event_name=selection_event_details['event_name'],
                                                      event_date=selection_event_details['event_date'],
                                                      organization_id=selection_event_details['organization_id'],
                                                      status=selection_event_details['event_is_active'],
                                                      participants_count=selection_participants_count),
                                    reply_markup=control_panel_event_edit_keyboard(selection_event_id,
                                                                                   'request_control_event_selected_edit',
                                                                                   'request_control_notification_broadcast_event',
                                                                                   'request_control_notification_broadcast_callback_event',
                                                                                   'request_register_users_event',
                                                                                   'request_control_events_list',
                                                                                   'request_control_panel'))
    await callback.answer()

@control_router.callback_query(F.data == 'ask_control_events')
async def events_list_handler(callback: CallbackQuery):
    await callback.message.edit_text(localization.get('common.text.control_panel.event.action_select'),
                                     reply_markup=control_panel_keyboard('request_control_events_list',
                                                                         'request_control_event_create',
                                                                         'request_control_panel'))
    await callback.answer()

@control_router.callback_query(F.data.startswith('ask_control_event_selected_event_'))
async def ask_control_events_page_handler(callback: CallbackQuery, state: FSMContext):
    selection_event_id = int(callback.data.removeprefix('ask_control_event_selected_event_'))
    await state.update_data(state_event_id=selection_event_id)
    data_edit_event = await state.get_data()
    await state.set_state(EventInformation.state_event_name)
    await callback.message.edit_text(localization.get('common.text.control_panel.event.action_modify.event_name',
                                                      action=localization.get('common.text.control_panel.event.action_modify.edit'),
                                                      event_id=data_edit_event.get('state_event_id')),
                                     reply_markup=control_panel_event_edit_keyboard(data_edit_event.get('state_event_id'), 'request_control_panel'))
    await callback.answer()

@control_router.message(F.text, EventInformation.state_event_name)
async def capture_control_event_edit_date_handler(message: Message, state: FSMContext):
    await state.update_data(state_event_name=message.text)
    data_edit_event = await state.get_data()
    await state.set_state(EventInformation.state_event_date)
    await message.answer(localization.get('common.text.control_panel.event.action_modify.event_date',
                                                      action=localization.get('common.text.control_panel.event.action_modify.edit'),
                                                      event_id=data_edit_event.get('state_event_id'),
                                                      event_name=data_edit_event.get('state_event_name')),
                         reply_markup=control_panel_event_edit_keyboard(data_edit_event.get('state_event_id'), 'request_control_panel'))

@control_router.message(F.text, EventInformation.state_event_date)
async def capture_control_event_edit_date_handler(message: Message, state: FSMContext):
    await state.update_data(state_event_date=message.text)
    data_edit_event = await state.get_data()
    await state.set_state(EventInformation.state_event_organisation_id)
    await message.answer(localization.get('common.text.control_panel.event.action_modify.event_organisation_id',
                                                      action=localization.get('common.text.control_panel.event.action_modify.edit'),
                                                      event_id=data_edit_event.get('state_event_id'),
                                                      event_name=data_edit_event.get('state_event_name'),
                                                      event_date=data_edit_event.get('state_event_date')),
                         reply_markup=control_panel_event_edit_keyboard(data_edit_event.get('state_event_id'), 'request_control_panel'))

@control_router.message(F.text, EventInformation.state_event_organisation_id)
async def capture_control_event_edit_date_handler(message: Message, state: FSMContext):
    await state.update_data(state_event_organisation_id=message.text)
    data_edit_event = await state.get_data()
    await state.set_state(EventInformation.state_event_status)
    await message.answer(localization.get('common.text.control_panel.event.action_modify.event_status',
                                                      action=localization.get('common.text.control_panel.event.action_modify.edit'),
                                                      event_id=data_edit_event.get('state_event_id'),
                                                      event_name=data_edit_event.get('state_event_name'),
                                                      event_date=data_edit_event.get('state_event_date'),
                                                      organisation_id=data_edit_event.get('state_event_organisation_id')),
                         reply_markup=control_panel_event_edit_keyboard(data_edit_event.get('state_event_id'),
                                                                        'request_control_event_edit_relevant',
                                                                        'request_control_event_edit_not_relevant',
                                                                        'request_control_panel'))

@control_router.callback_query(F.text, EventInformation.state_event_status)
async def capture_control_event_edit_status_handler(callback: CallbackQuery, state: FSMContext):
    data_edit_event = await state.get_data()
    await callback.message.edit_text(localization.get('common.text.control_panel.event.action_modify.event_confirmation',
                                                      action=localization.get('common.text.control_panel.event.action_modify.edit'),
                                                      event_id=data_edit_event.get('state_event_id'),
                                                      event_name=data_edit_event.get('state_event_name'),
                                                      event_date=data_edit_event.get('state_event_date'),
                                                      organisation_id=data_edit_event.get('state_event_organisation_id'),
                                                      event_status=data_edit_event.get('state_event_status')),
                                     reply_markup=control_panel_event_edit_keyboard(data_edit_event.get('state_event_id'),
                                                                                    'request_control_event_edit_confirmation',
                                                                                    'request_control_panel'))

@control_router.callback_query(F.data == 'ask_control_event_edit_confirmation')
async def ask_control_event_edit_confirmation_handler(callback: CallbackQuery, state: FSMContext):
    data_edit_event = await state.get_data()
    if data_edit_event.get('state_event_id'):
        await db_connection.event_update_details(data_edit_event.get('state_event_id'),
                                                 data_edit_event.get('state_event_name'),
                                                 data_edit_event.get('state_event_date'),
                                                 data_edit_event.get('state_event_organisation_id'),
                                                 data_edit_event.get('state_event_status'))
    else:
        await db_connection.event_add_new(data_edit_event.get('state_event_name'),
                                          data_edit_event.get('state_event_date'),
                                          data_edit_event.get('state_event_organisation_id'),
                                          data_edit_event.get('state_event_status'))
    await callback.message.edit_text(localization.get('common.text.control_panel.event.action_modify.action_save'))
    await state.clear()
    await ask_control_events_list_handler(callback)
    await callback.answer()

@control_router.callback_query(F.data.startswith('ask_control_event_edit_relevant'))
async def ask_control_event_edit_relevant_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(state_event_status=1)
    await capture_control_event_edit_status_handler(callback, state)

@control_router.callback_query(F.data.startswith('ask_control_event_edit_not_relevant'))
async def ask_control_event_edit_not_relevant_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(state_event_status=0)
    await capture_control_event_edit_status_handler(callback, state)

@control_router.callback_query(F.data.startswith('ask_control_event_users_'))
async def ask_control_event_users_handler(callback: CallbackQuery, state: FSMContext):
    selection_event_id = int(callback.data.removeprefix('ask_control_event_users_'))
    csv_data = await db_connection.event_get_participants_csv(selection_event_id)
    date_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"participants_event_{selection_event_id}_{date_time}.csv"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(csv_data)
    await callback.message.answer_document(document=FSInputFile(filename),
                                           caption=localization.get('common.text.control_panel.event.list_found', event_id=selection_event_id))
    await callback.message.answer(localization.get('common.text.control_panel.event.list_file_export_csv', time=datetime.now()),
                                  reply_markup=control_panel_keyboard('request_control_events_list', 'request_control_panel'))
    os.remove(filename)
    await callback.answer()

@control_router.callback_query(F.data.startswith('ask_control_events_page_'))
async def ask_control_events_page_handler(callback: CallbackQuery):
    page = int(callback.data.split('_')[-1]) # Take the last number from the end query
    await show_events_page_handler(callback=callback.message, telegram_user_id=callback.from_user.id, page_number=page)

async def show_events_page_handler(callback: Message, telegram_user_id: int, page_number: int | int = 0):
    page = page_number
    per_page = 10
    organization_id = await db_connection.get_admin_organization(telegram_user_id)
    events = await db_connection.events_list_get(page, per_page, organization_id)
    total_events = await db_connection.get_events_count_org(organization_id)
    total_pages = (total_events + per_page - 1) // per_page # -1 is needed to avoid creating an extra page
    
    await callback.edit_text(localization.get('common.text.control_panel.event.list_event', event_count_per_page=per_page),
                             reply_markup=control_panel_events_keyboard(events=events,
                                                                        current_page=page,
                                                                        total_pages=total_pages))

# endregion

# region Notification management

@control_router.callback_query(F.data.startswith('ask_notification_broadcast'))
async def ask_notification_broadcast_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(localization.get('common.text.control_panel.users.notification.menu_head'),
                                     reply_markup=control_panel_event_edit_keyboard(None, 
                                                                                    'request_control_notification_broadcast_all', 
                                                                                    'request_control_events_list', 
                                                                                    'request_control_panel'))

# region Newsletter for all users

@control_router.callback_query(F.data == 'ask_control_notification_broadcast_all')
async def ask_control_notification_broadcast_all_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    users_id = await db_connection.users_list_all_get()
    await state.update_data(state_telegram_user_ids=users_id)
    await callback.message.answer(localization.get('common.text.control_panel.users.notification.newsletter_all_without_callback_head',
                                                   users_id=len(users_id)),
                                reply_markup=control_panel_keyboard('request_control_panel'))
    await state.set_state(EventInformation.state_newsletter_wait_text)
    await callback.answer()

# endregion

# region Newsletter for event participants without callback

@control_router.callback_query(F.data.startswith('ask_control_notification_broadcast_event_'))
async def ask_control_notification_broadcast_event_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    selection_event_id = int(callback.data.removeprefix('ask_control_notification_broadcast_event_'))
    users_id = await db_connection.event_participants_get(selection_event_id)
    await state.update_data(state_telegram_user_ids=users_id)
    await callback.message.answer(localization.get('common.text.control_panel.users.notification.newsletter_without_callback_head',
                                                   users_id=len(users_id),
                                                   event_id=selection_event_id),
                                reply_markup=control_panel_keyboard('request_control_panel'))
    await state.set_state(EventInformation.state_newsletter_wait_text)
    await callback.answer()

# endregion

# region Newsletter for event participants with callback

@control_router.callback_query(F.data.startswith('ask_control_notification_broadcast_callback_event_'))
async def ask_control_notification_broadcast_callback_event_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    selection_event_id = int(callback.data.removeprefix('ask_control_notification_broadcast_callback_event_'))
    users_id = await db_connection.event_participants_get(selection_event_id)
    await state.update_data(state_telegram_user_ids=users_id)
    await state.update_data(state_newsletter_callback=True)
    await callback.message.answer(localization.get('common.text.control_panel.users.notification.newsletter_with_callback_head',
                                                   users_id=len(users_id),
                                                   event_id=selection_event_id),
                                  reply_markup=control_panel_keyboard('request_control_panel'))
    await state.set_state(EventInformation.state_newsletter_wait_text)
    await callback.answer()

# endregion

# region Newsletter function

@control_router.message(F.text, EventInformation.state_newsletter_wait_text)
async def process_broadcast_text(message: Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    text = message.text
    success, errors = await broadcast_message(bot=bot,
                                              telegram_user_ids=data['state_telegram_user_ids'],
                                              text=text,
                                              callback=data.get('state_newsletter_callback'))
    await message.answer(localization.get('common.text.control_panel.users.notification.newsletter_callback_result',
                                                   success=success,
                                                   errors=errors),
                         reply_markup=control_panel_keyboard('request_control_panel'))
    await state.clear()


async def broadcast_message(bot: Bot, telegram_user_ids: list[int], text: str, delay: float = 0.1, callback: bool = False):
    success, errors = 0, 0
    for telegram_user_id in telegram_user_ids:
        try:
            if callback:
                await bot.send_message(chat_id=telegram_user_id,
                                       text=text,
                                       reply_markup=control_panel_keyboard('request_answer_callback', 'request_main_menu'))
            else:
                await bot.send_message(chat_id=telegram_user_id,
                                       text=text,
                                       reply_markup=control_panel_keyboard('request_main_menu'))
            success += 1
        except Exception as e:
            errors += 1
            logging.error(f"Failed to send notify to {telegram_user_id} with error: {e}")
        await asyncio.sleep(delay)
    return success, errors

# endregion

# endregion

# region Helpdesk/Feedback/Support management

@control_router.callback_query(F.data.startswith('ask_control_feedback_answer_'))
async def ask_control_feedback_answer_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    telegram_user_target_id = int(callback.data.removeprefix('ask_control_feedback_answer_'))
    await state.update_data(state_telegram_user_target_id=telegram_user_target_id)
    await callback.message.answer(localization.get('common.text.control_panel.feedback.message_support_feedback_new'),
                                    reply_markup=control_panel_keyboard('request_control_panel'))
    await state.set_state(EventInformation.state_telegram_user_target_id)
    await callback.answer()

@control_router.message(F.text, EventInformation.state_telegram_user_target_id)
async def process_broadcast_text(message: Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    await bot.send_message(
        chat_id=data['state_telegram_user_target_id'],
        text=localization.get('common.text.user_panel.feedback.message_notification_support_new', text=message.text),
        reply_markup=control_panel_keyboard('request_main_menu'))
    await message.answer(localization.get('common.text.control_panel.feedback.message_support_feedback_successful'),
        reply_markup=control_panel_keyboard('request_control_panel'))
    await state.clear()

# endregion
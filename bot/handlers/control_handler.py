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
from messages.main_message import generate_start_message, generate_event_detail_message, message_control_event_detail_edit, message_control_administrators, message_control_panel, message_control_bot
from keyboards.main_keyboard import main_keyboard, control_panel_keyboard, control_panel_events_keyboard, control_panel_event_edit_keyboard, control_panel_administrators_edit_keyboard
from services.db_service import db_connection

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
    state_notification_wait_text = State()
    state_notification_wait_text_with_callback = State()
    state_telegram_user_ids = State()
    state_telegram_user_target_id = State()

@control_router.callback_query(F.data == 'ask_control_panel')
async def request_control_panel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        message_control_panel(version_bot, callback.message.chat.id, 0),
        reply_markup=control_panel_keyboard(
            'request_control_events', 
            'request_notification_broadcast', 
            'request_control_users_list', 
            'request_control_bot', 
            'request_control_administrators', 
            'request_main_menu'
        )
    )
    await callback.answer()

@control_router.callback_query(F.data == 'ask_control_events')
async def events_list_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        message_control_administrators(9),
        reply_markup=control_panel_keyboard('request_control_events_list', 'request_control_event_create', 'request_control_panel')
    )

@control_router.callback_query(F.data == 'ask_control_users_list')
async def users_list_handler(callback: CallbackQuery):
    csv_data = await db_connection.users_get_list_csv()
    date_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"users_list_{date_time}.csv"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(csv_data)
    await callback.message.answer_document(
            document=FSInputFile(filename),
            caption=f"Список всех пользователей в базе данных по ID",
        )
    await callback.message.answer(
        f'Файл сформирован и отправлен в {date_time}!\nМожете вернуться в меню и продолжить работу.\n',
        reply_markup=control_panel_keyboard('request_control_panel')
    )
    os.remove(filename)
    await callback.answer()

@control_router.callback_query(F.data == 'ask_control_event')
async def control_event_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        f'ask_control_event',
        reply_markup=control_panel_keyboard('request_control_panel')
    )

@control_router.callback_query(F.data == 'ask_control_bot')
async def control_bot_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        message_control_bot(0),
        reply_markup=control_panel_keyboard('request_button_control','request_control_panel')
    )

@control_router.callback_query(F.data == 'ask_control_administrators')
async def ask_control_administrators_handler(callback: CallbackQuery):
    administrators_list = await db_connection.administrators_list()
    message_text = message_control_administrators(0)
    
    for i, administrator in enumerate(administrators_list, 1):
        telegram_user_id = administrator['telegram_user_id']
        telegram_username = 'None' if administrator['telegram_username'] is None else f'@{administrator['telegram_username']}'
        organization_id = administrator['organization_id'] 
        join_date = administrator['join_date']
        message_text += f'<pre><b>{i}. TG ID   :</b> {telegram_user_id}\n' \
                        f'<b>{i}. Username:</b> {telegram_username}\n' \
                        f'<b>{i}. Added   :</b> {join_date}\n' \
                        f'<b>{i}. Org id  :</b> {organization_id}\n\n</pre>'
    message_text += (message_control_administrators(1))
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
    await callback.message.edit_text(
        message_control_administrators(2),
        reply_markup=control_panel_administrators_edit_keyboard('request_control_panel')
    )
    await state.update_data(state_administrators_telegram_status = 1)
    await state.set_state(EventInformation.state_administrators_telegram)

@control_router.callback_query(F.data == 'ask_control_administrators_delete')
async def ask_control_administrators_delete_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        message_control_administrators(3),
        reply_markup=control_panel_administrators_edit_keyboard('request_control_panel')
    )
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
        username = message.forward_from.username  # We take it if there is one
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
            await message.answer(
                    message_control_administrators(10, user_id),
                    reply_markup=control_panel_administrators_edit_keyboard('request_control_panel')
                )
            await state.update_data(state_administrators_telegram = user_id) ###################################################################################################### BUG!
            await state.set_state(EventInformation.state_administrators_organization_id)
        else:
            await message.answer(
                message_control_administrators(4),
                reply_markup=control_panel_administrators_edit_keyboard('request_control_panel')
            )
    else:  # Delete administrator
        if user_id:
            await db_connection.administrators_del(user_id)
            await message.answer(
                f'ID: {user_id}',
                reply_markup=control_panel_administrators_edit_keyboard('request_control_panel')
            )
            await state.clear()
        else:
            await message.answer(
                message_control_administrators(5),
                reply_markup=control_panel_administrators_edit_keyboard('request_control_panel')
            )

@control_router.message(F.text, EventInformation.state_administrators_organization_id)
async def state_administrator_organization_id_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    data_administrator_id = data.get('state_administrators_telegram')
    await state.update_data(state_administrators_organization_id=message.text)
    await message.answer(
        message_control_administrators(11, data_administrator_id, message.text),
        reply_markup=control_panel_administrators_edit_keyboard('request_control_panel')
    )
    await db_connection.administrators_add(data_administrator_id, message.text)
    await state.clear()

@control_router.callback_query(F.data == 'ask_control_administrators_list')
async def users_list_handler(callback: CallbackQuery):
    csv_data = await db_connection.administrators_get_list_csv()
    date_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"users_list_{date_time}.csv"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(csv_data)
    await callback.message.answer_document(
            document=FSInputFile(filename),
            caption=message_control_administrators(6)
        )
    await callback.message.answer(
        f'{message_control_administrators(7)} {date_time}!{message_control_administrators(8)}',
        reply_markup=control_panel_keyboard('request_control_panel')
    )
    os.remove(filename)
    await callback.answer()

@control_router.callback_query(F.data == 'ask_main_menu')
async def main_menu_handler(callback: CallbackQuery):
    await callback.message.answer(
        generate_start_message(await db_connection.events_list_public_get(0, 3)), 
        reply_markup=await main_keyboard(await FilterAdministrator()(callback))
    )
    await callback.answer()

@control_router.callback_query(F.data == 'ask_control_events_list')
async def ask_control_events_list_handler(callback: CallbackQuery):
    await show_events_page_handler(callback.message)  

# Create new event, using the same methods as for editing events
@control_router.callback_query(F.data == 'ask_control_event_create')
async def ask_control_event_create_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(EventInformation.state_event_name)
    await callback.message.edit_text(
        f'{message_control_event_detail_edit(0, {})}',
        reply_markup=control_panel_keyboard('request_control_panel')
    )
    await callback.answer()

# Decorator block: additional

@control_router.callback_query(F.data.startswith('ask_edit_event_'))
async def capture_event_edit_handler(callback: CallbackQuery):
    selection_event_id = int(callback.data.removeprefix('ask_edit_event_'))
    selection_event_details = await db_connection.event_get_details(selection_event_id)
    selection_participants_count = await db_connection.event_get_participants_count(selection_event_id)

    await callback.message.edit_text(
        generate_event_detail_message(
            selection_event_id, 
            selection_event_details['event_id'],
            selection_event_details['event_name'], 
            selection_event_details['event_date'],
            selection_event_details['organization_id'],
            selection_event_details['event_is_active'],
            selection_participants_count),
        reply_markup=control_panel_event_edit_keyboard(
            selection_event_id, 
            'request_control_event_selected_edit', 
            'request_control_notification_broadcast_event',
            'request_control_notification_broadcast_callback_event',
            'request_register_users_event', 
            'request_control_events_list', 
            'request_control_panel'
        )
    )

################################################################################################################################## Decorator block: edit event

@control_router.callback_query(F.data.startswith('ask_control_event_selected_event_'))
async def ask_control_events_page_handler(callback: CallbackQuery, state: FSMContext):
    selection_event_id = int(callback.data.removeprefix('ask_control_event_selected_event_'))
    await state.update_data(state_event_id=selection_event_id)
    data_edit_event = await state.get_data()
    await state.set_state(EventInformation.state_event_name)
    await callback.message.edit_text(
        message_control_event_detail_edit(0, data_edit_event),
        reply_markup=control_panel_event_edit_keyboard(data_edit_event.get('state_event_id'), 'request_control_panel')
    )

@control_router.message(F.text, EventInformation.state_event_name)
async def capture_control_event_edit_date_handler(message: Message, state: FSMContext):
    await state.update_data(state_event_name=message.text)
    data_edit_event = await state.get_data()
    await state.set_state(EventInformation.state_event_date)
    await message.answer(
        message_control_event_detail_edit(1, data_edit_event),
        reply_markup=control_panel_event_edit_keyboard(data_edit_event.get('state_event_id'), 'request_control_panel')
    )

@control_router.message(F.text, EventInformation.state_event_date)
async def capture_control_event_edit_date_handler(message: Message, state: FSMContext):
    await state.update_data(state_event_date=message.text)
    data_edit_event = await state.get_data()
    await state.set_state(EventInformation.state_event_organisation_id)
    await message.answer(
        message_control_event_detail_edit(2, data_edit_event),
        reply_markup=control_panel_event_edit_keyboard(data_edit_event.get('state_event_id'), 'request_control_panel')
    )

@control_router.message(F.text, EventInformation.state_event_organisation_id)
async def capture_control_event_edit_date_handler(message: Message, state: FSMContext):
    await state.update_data(state_event_organisation_id=message.text)
    data_edit_event = await state.get_data()
    await state.set_state(EventInformation.state_event_status)
    await message.answer(
        message_control_event_detail_edit(3, data_edit_event),
        reply_markup=control_panel_event_edit_keyboard(data_edit_event.get('state_event_id'), 'request_control_event_edit_relevant', 'request_control_event_edit_not_relevant', 'request_control_panel')
    )

@control_router.callback_query(F.text, EventInformation.state_event_status)
async def capture_control_event_edit_status_handler(callback: CallbackQuery, state: FSMContext):
    data_edit_event = await state.get_data()
    await callback.message.edit_text(
        message_control_event_detail_edit(4, data_edit_event),
        reply_markup=control_panel_event_edit_keyboard(data_edit_event.get('state_event_id'), 'request_control_event_edit_confirmation', 'request_control_panel')
    )

@control_router.callback_query(F.data == 'ask_control_event_edit_confirmation')
async def ask_control_event_edit_confirmation_handler(callback: CallbackQuery, state: FSMContext):
    data_edit_event = await state.get_data()
    if data_edit_event.get('state_event_id'): # Edit exist event
        await db_connection.event_update_details(
            data_edit_event.get('state_event_id'),        
            data_edit_event.get('state_event_name'),
            data_edit_event.get('state_event_date'),
            data_edit_event.get('state_event_organisation_id'),
            data_edit_event.get('state_event_status'),
        )
    else: # Create new event
        await db_connection.event_add_new(       
            data_edit_event.get('state_event_name'),
            data_edit_event.get('state_event_date'),
            data_edit_event.get('state_event_organisation_id'),
            data_edit_event.get('state_event_status'),
        )
    await callback.message.edit_text(message_control_event_detail_edit(5, data_edit_event))
    await state.clear()
    await asyncio.sleep(1) 
    await ask_control_events_list_handler(callback)
    await callback.answer()

################################################################################################################################## Decorator block: event set status

@control_router.callback_query(F.data.startswith('ask_control_event_edit_relevant'))
async def ask_control_event_edit_relevant_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(state_event_status=1)
    await capture_control_event_edit_status_handler(callback, state)

@control_router.callback_query(F.data.startswith('ask_control_event_edit_not_relevant'))
async def ask_control_event_edit_not_relevant_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(state_event_status=0)
    await capture_control_event_edit_status_handler(callback, state)

################################################################################################################################## Decorator block: other

@control_router.callback_query(F.data.startswith('ask_control_event_users_'))
async def ask_control_event_users_handler(callback: CallbackQuery, state: FSMContext):
    selection_event_id = int(callback.data.removeprefix('ask_control_event_users_'))
    csv_data = await db_connection.event_get_participants_csv(selection_event_id)
    date_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"participants_event_{selection_event_id}_{date_time}.csv"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(csv_data)
    await callback.message.answer_document(
            document=FSInputFile(filename),
            caption=f"Список участников мероприятия (ID: {selection_event_id})",
        )
    await callback.message.answer(
        f'Файл сформирован и отправлен в {date_time}!\nМожете вернуться в меню и продолжить работу.\n',
        reply_markup=control_panel_keyboard('request_control_events_list', 'request_control_panel')
    )
    os.remove(filename)
    await callback.answer()

@control_router.callback_query(F.data.startswith('ask_control_events_page_'))
async def ask_control_events_page_handler(callback: CallbackQuery):
    page = int(callback.data.split('_')[-1])
    await show_events_page_handler(callback.message, page)

async def show_events_page_handler(message: Message):
    page = 0
    per_page = 10
    organization_id = await db_connection.get_admin_organization(message.chat.id)
    events = await db_connection.events_list_get(page, per_page, organization_id)
    total_events = await db_connection.get_events_count_org(organization_id)
    total_pages = (total_events + per_page - 1)
    
    await message.edit_text(
        f"Список мероприятий доступных для регистрации",
        reply_markup=control_panel_events_keyboard(
            events=events,
            current_page=page,
            total_pages=total_pages
        )
    )

# Decorator block: send notify 

@control_router.callback_query(F.data.startswith('ask_notification_broadcast'))
async def ask_notification_broadcast_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        f'Если хотите разослать уведомления участникам конкретного мероприятия, то это необходимо сделать в списке мероприятий, выбрав нужное мероприятие, а затем опцию "Рассылка участникам".',
        reply_markup=control_panel_event_edit_keyboard(None, 'request_control_notification_broadcast_all', 'request_control_events_list', 'request_control_panel')
    )

@control_router.callback_query(F.data.startswith('ask_control_notification_broadcast_event_'))
async def ask_control_notification_broadcast_event_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    selection_event_id = int(callback.data.removeprefix('ask_control_notification_broadcast_event_'))
    user_ids = await db_connection.event_participants_get(selection_event_id)
    await state.update_data(
        state_telegram_user_ids=user_ids,
    )
    await callback.message.answer(
        f'Рассылка для {len(user_ids)} участников мероприятия ID: {selection_event_id}\n' \
        f'Отправьте текст сообщения:',
        reply_markup=control_panel_keyboard('request_control_panel')
    )
    await state.set_state(EventInformation.state_notification_wait_text)
    await callback.answer()

@control_router.callback_query(F.data.startswith('ask_control_notification_broadcast_callback_event_'))
async def ask_control_notification_broadcast_callback_event_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    selection_event_id = int(callback.data.removeprefix('ask_control_notification_broadcast_callback_event_'))
    user_ids = await db_connection.event_participants_get(selection_event_id)
    await state.update_data(
        state_telegram_user_ids=user_ids,
    )
    await callback.message.answer(
        f'Рассылка с ответом для {len(user_ids)} участников мероприятия ID: {selection_event_id}\n' \
        f'Отправьте текст сообщения:',
        reply_markup=control_panel_keyboard('request_control_panel')
    )
    await state.set_state(EventInformation.state_notification_wait_text_with_callback)
    await callback.answer()

@control_router.message(F.text, EventInformation.state_notification_wait_text_with_callback)
async def process_broadcast_text(message: Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    text = message.text
    success, errors = await broadcast_message_with_callback(
        bot=bot,
        telegram_user_ids=data['state_telegram_user_ids'],
        text=text
    )
    await message.answer(
        f'Рассылка завершена!\n\n'
        f'Успешно: {success}\n'
        f'Ошибок: {errors}',
        reply_markup=control_panel_keyboard('request_control_panel')
    )
    await state.clear()

async def broadcast_message_with_callback(bot: Bot, telegram_user_ids: list[int], text: str, delay: float = 0.1):
    success = errors = 0
    for telegram_user_id in telegram_user_ids:
        try:
            await bot.send_message(
                chat_id=telegram_user_id,
                text=text,
                reply_markup=control_panel_keyboard('request_answer_callback', 'request_main_menu')
            )
            success += 1
        except Exception as e:
            errors += 1
            logging.error(f"Failed to send notify to {telegram_user_id} with error: {e}")
        await asyncio.sleep(delay)  # Flood protection
    return success, errors

@control_router.callback_query(F.data == 'ask_control_notification_broadcast_all')
async def ask_control_notification_broadcast_all_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    user_ids = await db_connection.users_list_all_get()
    await state.update_data(state_telegram_user_ids=user_ids)
    await callback.message.answer(
        f'Рассылка для {len(user_ids)} всех пользователей...\n' \
        f'Отправьте текст сообщения:',
        reply_markup=control_panel_keyboard('request_control_panel')
    )
    await state.set_state(EventInformation.state_notification_wait_text)
    await callback.answer()

@control_router.message(F.text, EventInformation.state_notification_wait_text)
async def process_broadcast_text(message: Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    text = message.text
    success, errors = await broadcast_message(
        bot=bot,
        telegram_user_ids=data['state_telegram_user_ids'],
        text=text
    )
    await message.answer(
        f'Рассылка завершена!\n\n'
        f'Успешно: {success}\n'
        f'Ошибок: {errors}',
        reply_markup=control_panel_keyboard('request_control_panel')
    )
    await state.clear()

async def broadcast_message(bot: Bot, telegram_user_ids: list[int], text: str, delay: float = 0.1):
    success = errors = 0
    for telegram_user_id in telegram_user_ids:
        try:
            await bot.send_message(
                chat_id=telegram_user_id,
                text=text,
                reply_markup=control_panel_keyboard('request_main_menu')
            )
            success += 1
        except Exception as e:
            errors += 1
            logging.error(f"Failed to send notify to {telegram_user_id} with error: {e}")
        await asyncio.sleep(delay)  # Flood protection
    return success, errors

# Decorator block: feedback

@control_router.callback_query(F.data.startswith('ask_control_feedback_answer_'))
async def ask_control_feedback_answer_handler(callback: CallbackQuery, bot: Bot, state: FSMContext):
    try:
        telegram_user_target_id = int(callback.data.removeprefix('ask_control_feedback_answer_'))
        await state.update_data(state_telegram_user_target_id=telegram_user_target_id)
        await callback.message.answer(
            f'<b>Ведите текст сообщения:</b>\n',
            reply_markup=control_panel_keyboard('request_control_panel')
        )
        await state.set_state(EventInformation.state_telegram_user_target_id)
        await callback.answer()
    except Exception as e:
        await callback.message.answer(
            f'<b>При попытке выполнения запроса, произошла ошибка! Ошибка:</b>\n {e}',
            reply_markup=control_panel_keyboard('request_control_panel')
        )
        await callback.answer()

@control_router.message(F.text, EventInformation.state_telegram_user_target_id)
async def process_broadcast_text(message: Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    await bot.send_message(
        chat_id=data['state_telegram_user_target_id'],
        text=f"<b>Ответ поддержки:</b>\n\n{message.text}\n\nМожете вернуться в главное меню:",
        reply_markup=control_panel_keyboard('request_main_menu')

    )
    await message.answer(
        f'<b>Ответ отправлен!</b>',
        reply_markup=control_panel_keyboard('request_control_panel')
    )
    await state.clear()

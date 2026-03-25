from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.db_service import db_connection

async def main_keyboard(button_is_administrator: bool = False):

    builder = InlineKeyboardBuilder()
    buttons = await db_connection.button_record_get(menu_index=1)

    for button_data in buttons:
        builder.button(
                text=button_data['text'],
                callback_data=button_data['callback']
            )

    if button_is_administrator:
        buttons_administrator = await db_connection.button_record_get(menu_index=0)
        for button in buttons_administrator:
            builder.button(
                text=button['text'],
                callback_data=button['callback']
            )

    builder.adjust(1)
    return builder.as_markup()


def registration_questionnaire_keyboard(*buttons: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for button in buttons:
        if button == 'request_cancel':
            builder.button(text="Отменить действие", callback_data='ask_cancel_registration')
        elif button == 'request_questionnaire':
            builder.button(text="Зарегистрироваться", callback_data='ask_questionnaire')
        elif button == 'request_username':
            builder.button(text="Отправить Мой никнейм", callback_data='ask_username')
        elif button == 'request_confirmation':
            builder.button(text="Да, отправить.", callback_data='ask_confirmation')
        elif button == 'request_reject':
            builder.button(text="Нет, изменить.", callback_data='ask_reject')
        elif button == 'request_questionnaire_registration_check_username':
            builder.button(text="Проверить никнейм", callback_data='ask_questionnaire_registration_check_username')
        elif button == 'request_questionnaire_registration_additional_information_skip':
            builder.button(text="Пропустить", callback_data='ask_questionnaire_registration_additional_information_skip')
        elif button == 'request_questionnaire_registration_nickname_skip':
            builder.button(text="Пропустить", callback_data='ask_questionnaire_registration_nickname_skip')
        elif button == 'request_event_cancel_registration':
            builder.button(text="Отменить регистрацию", callback_data='ask_event_cancel_registration')
    builder.adjust(1)
    return builder.as_markup()

def generate_registration_questionnaire_events_keyboard(events: list, registration_action_status: bool = True, *buttons: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if not events:
        return builder.as_markup()

    if registration_action_status:
        for event in events:
            if event['event_is_active']:
                builder.button(text=f'{event['event_name']} {event['event_date']}', callback_data=f'event_{event['event_id']}')
    else:
        for event in events:
            if event['event_is_active']:
                builder.button(text=f'{event['event_name']} {event['event_date']}', callback_data=f'event_cancel_{event['event_id']}')

    for button in buttons:
        if button == 'request_cancel':
            builder.button(text="Отмена регистрации", callback_data='ask_cancel_registration')

    builder.adjust(1)
    return builder.as_markup()

def control_panel_keyboard(*buttons: str, telegram_user_id: int | None = 0) -> InlineKeyboardMarkup:
    user_id = telegram_user_id or '-Unknown'

    builder = InlineKeyboardBuilder()
    for button in buttons:
        if button == 'request_control_events':
            builder.button(text="Управление мероприятиями", callback_data='ask_control_events')

        elif button == 'request_notification_broadcast':
            builder.button(text="Управление рассылками", callback_data='ask_notification_broadcast')

        elif button == 'request_control_event':
            builder.button(text="Управление мероприятием", callback_data='ask_control_event')

        elif button == 'request_control_events_list':
            builder.button(text="Список мероприятий", callback_data='ask_control_events_list')

        elif button == 'request_control_users_list':
            builder.button(text="Список пользователей", callback_data='ask_control_users_list')

        elif button == 'request_control_event_create':
            builder.button(text="Создать мероприятие", callback_data='ask_control_event_create')
        
        elif button == 'request_control_bot':
            builder.button(text="Управление ботом", callback_data='ask_control_bot')

        elif button == 'request_control_administrators':
            builder.button(text="Управление администраторами", callback_data='ask_control_administrators')

        elif button == 'request_main_menu':
            builder.button(text="Вернуться в главное меню", callback_data='ask_main_menu')
        
        elif button == 'request_answer_callback':
            builder.button(text="Ответить", callback_data='ask_answer_callback')

        elif button == 'request_control_panel':
            builder.button(text="В панель управления", callback_data='ask_control_panel')
        
        elif button == 'request_control_feedback_answer':
            builder.button(text="Ответить", callback_data=f'ask_control_feedback_answer_{user_id}')

        elif button == 'request_button_control':
            builder.button(text="(BETA) Добавить кнопку", callback_data='ask_button_control')
        
        elif button == 'request_button_control_active_yes':
            builder.button(text="Кнопка активна", callback_data='ask_button_control_active_yes')

        elif button == 'request_button_control_active_no':
            builder.button(text="Кнопка не активна", callback_data='ask_button_control_active_no')

        elif button == 'request_button_control_save':
            builder.button(text="Сохранить кнопку", callback_data='ask_button_control_save')

    builder.adjust(1)
    return builder.as_markup()

def control_panel_events_keyboard(events: list, current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    pagination_buttons = []

    if not events:
        return builder.as_markup()
    for event in events:
        event_status = "Активно" if event['event_is_active'] else "Не активно"
        builder.button(text=f'{event['event_id']} {event['event_name']} {event['event_date']} {event_status}', callback_data=f'ask_edit_event_{event['event_id']}')
    
    if current_page > 0:
        pagination_buttons.append(
            InlineKeyboardButton(text="Более новые", callback_data=f"ask_control_events_page_{current_page-1}")
        )
#    pagination_buttons.append(
#        InlineKeyboardButton(text=f"{current_page+1}/{total_pages}", callback_data="ask_control_events_page_{current_page}")
#    )
    if (current_page + 1) < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton(text="Более старые", callback_data=f"ask_control_events_page_{current_page+1}")
        )

    builder.row(*pagination_buttons)
    builder.row(InlineKeyboardButton(text="В панель управления", callback_data='ask_control_panel'))
    builder.adjust(1)

    return builder.as_markup()

def control_panel_event_edit_keyboard(event_id: int, *buttons: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for button in buttons:
        if button == 'request_control_event_selected_edit':
            builder.button(text="Изменить мероприятие", callback_data=f'ask_control_event_selected_event_{event_id}')

        elif button == 'request_control_event_edit_relevant':
            builder.button(text="Статус - Актуально", callback_data=f'ask_control_event_edit_relevant')

        elif button == 'request_control_event_edit_not_relevant':
            builder.button(text="Статус - Не актуально", callback_data=f'ask_control_event_edit_not_relevant')

        elif button == 'request_control_event_edit_confirmation':
            builder.button(text="Сохранить изменения", callback_data='ask_control_event_edit_confirmation')

        elif button == 'request_register_users_event':
            builder.button(text="Список участников", callback_data=f'ask_control_event_users_{event_id}')

        elif button == 'request_control_events_list':
            builder.button(text="Список мероприятий", callback_data='ask_control_events_list')

        elif button == 'request_control_panel':
            builder.button(text="В панель управления", callback_data='ask_control_panel')
        
        elif button == 'request_control_notification_broadcast_event':
            builder.button(text="Рассылка участникам", callback_data=f'ask_control_notification_broadcast_event_{event_id}')
        
        elif button == 'request_control_notification_broadcast_callback_event':
            builder.button(text="Рассылка участникам с обратной связью", callback_data=f'ask_control_notification_broadcast_callback_event_{event_id}')

        elif button == 'request_control_notification_broadcast_all':
            builder.button(text="Всем пользователям", callback_data='ask_control_notification_broadcast_all')
    builder.adjust(1)
    return builder.as_markup()

def control_panel_administrators_edit_keyboard(*buttons: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for button in buttons:
        if button == 'request_control_administrators_add':
            builder.button(text="Добавить администратора", callback_data=f'ask_control_administrators_add')

        elif button == 'request_control_administrators_delete':
            builder.button(text="Удалить администратора", callback_data=f'ask_control_administrators_delete')

        elif button == 'request_control_administrators_list':
            builder.button(text="Список администраторов", callback_data=f'ask_control_administrators_list')

        elif button == 'request_control_panel':
            builder.button(text="В панель управления", callback_data='ask_control_panel')
    builder.adjust(1)
    return builder.as_markup()
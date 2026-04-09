from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from locales.localization import localization

async def main_keyboard(button_is_administrator: bool = False):
    builder = InlineKeyboardBuilder()

    builder.button(text=localization.get('common.button.user_panel.registration.registration'), callback_data="event_create_registration")
    builder.button(text=localization.get('common.button.user_panel.refuse'), callback_data="event_cancel_registration")
    builder.button(text=localization.get('common.button.user_panel.information'), callback_data="information")
    builder.button(text=localization.get('common.button.user_panel.feedback'), callback_data="feedback")
    if button_is_administrator:
        builder.button(text=localization.get('common.button.control_panel.menu'), callback_data="ask_control_panel")

    builder.adjust(1)
    return builder.as_markup()


def registration_questionnaire_keyboard(*buttons: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for button in buttons:
        if button == 'request_cancel':
            builder.button(text=localization.get('common.button.user_panel.registration.cancel'), callback_data='ask_cancel_registration')
        elif button == 'request_questionnaire':
            builder.button(text=localization.get('common.button.user_panel.registration.registration'), callback_data='ask_questionnaire')
        elif button == 'request_username':
            builder.button(text=localization.get('common.button.user_panel.registration.send_username'), callback_data='ask_username')
        elif button == 'request_confirmation':
            builder.button(text=localization.get('common.button.user_panel.registration.confirmation'), callback_data='ask_confirmation')
        elif button == 'request_reject':
            builder.button(text=localization.get('common.button.user_panel.registration.reject'), callback_data='ask_reject')
        elif button == 'request_questionnaire_registration_check_username':
            builder.button(text=localization.get('common.button.user_panel.registration.send_username_check'), callback_data='ask_questionnaire_registration_check_username')
        elif button == 'request_questionnaire_registration_additional_information_skip':
            builder.button(text=localization.get('common.button.user_panel.registration.step_skip'), callback_data='ask_questionnaire_registration_additional_information_skip')
        elif button == 'request_questionnaire_registration_nickname_skip':
            builder.button(text=localization.get('common.button.user_panel.registration.step_skip'), callback_data='ask_questionnaire_registration_nickname_skip')
        elif button == 'request_event_cancel_registration':
            builder.button(text=localization.get('common.button.user_panel.registration.cancel'), callback_data='ask_event_cancel_registration')
        elif button == 'request_main_menu':
            builder.button(text=localization.get('common.button.user_panel.back'), callback_data='ask_main_menu')
    builder.adjust(1)
    return builder.as_markup()

def generate_registration_questionnaire_events_keyboard(events: list, registration_action_status: bool = True, *buttons: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if not events:
        return builder.as_markup()

    if registration_action_status:
        for event in events:
            if event['event_is_active']:
                builder.button(text=f'{event['event_name']} {event['event_date']}', callback_data=f'event_register_id_{event['event_id']}')
    else:
        for event in events:
            if event['event_is_active']:
                builder.button(text=f'{event['event_name']} {event['event_date']}', callback_data=f'event_refuse_id_{event['event_id']}')

    for button in buttons:
        if button == 'request_cancel':
            builder.button(text=localization.get('common.button.user_panel.registration.cancel'), callback_data='ask_cancel_registration')
        elif button == 'request_main_menu':
            builder.button(text=localization.get('common.button.user_panel.back'), callback_data='ask_main_menu')

    builder.adjust(1)
    return builder.as_markup()

def control_panel_keyboard(*buttons: str, telegram_user_id: int | None = 0) -> InlineKeyboardMarkup:
    user_id = telegram_user_id or '-Unknown'

    builder = InlineKeyboardBuilder()
    for button in buttons:
        if button == 'request_control_events':
            builder.button(text=localization.get('common.button.control_panel.event.management'), callback_data='ask_control_events')

        elif button == 'request_notification_broadcast':
            builder.button(text=localization.get('common.button.control_panel.users.notification.newsletter_management'), callback_data='ask_notification_broadcast')

        elif button == 'request_control_events_list':
            builder.button(text=localization.get('common.button.control_panel.event.list'), callback_data='ask_control_events_list')

        elif button == 'request_control_users_list':
            builder.button(text=localization.get('common.button.control_panel.users.list'), callback_data='ask_control_users_list')

        elif button == 'request_control_event_create':
            builder.button(text=localization.get('common.button.control_panel.event.create'), callback_data='ask_control_event_create')
        
        elif button == 'request_control_bot':
            builder.button(text=localization.get('common.button.control_panel.bot.management'), callback_data='ask_control_bot')

        elif button == 'request_control_administrators':
            builder.button(text=localization.get('common.button.control_panel.administrator.management'), callback_data='ask_control_administrators')

        elif button == 'request_main_menu':
            builder.button(text=localization.get('common.button.user_panel.back'), callback_data='ask_main_menu')
        
        elif button == 'request_answer_callback':
            builder.button(text=localization.get('common.button.control_panel.users.notification.message.answer'), callback_data='ask_answer_callback')

        elif button == 'request_control_panel':
            builder.button(text=localization.get('common.button.control_panel.menu'), callback_data='ask_control_panel')
        
        elif button == 'request_control_feedback_answer':
            builder.button(text=localization.get('common.button.control_panel.users.notification.message.answer'), callback_data=f'ask_control_feedback_answer_{user_id}')

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
    if (current_page + 1) < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton(text="Более старые", callback_data=f"ask_control_events_page_{current_page+1}")
        )

    builder.row(*pagination_buttons)
    builder.row(InlineKeyboardButton(text=localization.get('common.button.control_panel.menu'), callback_data='ask_control_panel'))
    builder.adjust(1)

    return builder.as_markup()

def control_panel_event_edit_keyboard(event_id: int, *buttons: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for button in buttons:
        if button == 'request_control_event_selected_edit':
            builder.button(text=localization.get('common.button.control_panel.event.edit_event'), callback_data=f'ask_control_event_selected_event_{event_id}')

        elif button == 'request_control_event_edit_relevant':
            builder.button(text=localization.get('common.button.control_panel.event.active'), callback_data=f'ask_control_event_edit_relevant')

        elif button == 'request_control_event_edit_not_relevant':
            builder.button(text=localization.get('common.button.control_panel.event.inactive'), callback_data=f'ask_control_event_edit_not_relevant')

        elif button == 'request_control_event_edit_confirmation':
            builder.button(text=localization.get('common.button.control_panel.event.edit_event_confirmation'), callback_data='ask_control_event_edit_confirmation')

        elif button == 'request_register_users_event':
            builder.button(text=localization.get('common.button.control_panel.event.list_participant'), callback_data=f'ask_control_event_users_{event_id}')

        elif button == 'request_control_events_list':
            builder.button(text=localization.get('common.button.control_panel.event.list'), callback_data='ask_control_events_list')

        elif button == 'request_control_panel':
            builder.button(text=localization.get('common.button.control_panel.menu'), callback_data='ask_control_panel')
        
        elif button == 'request_control_notification_broadcast_event':
            builder.button(text=localization.get('common.button.control_panel.event.newsletter_without_callback'), callback_data=f'ask_control_notification_broadcast_event_{event_id}')
        
        elif button == 'request_control_notification_broadcast_callback_event':
            builder.button(text=localization.get('common.button.control_panel.event.newsletter_with_callback'), callback_data=f'ask_control_notification_broadcast_callback_event_{event_id}')

        elif button == 'request_control_notification_broadcast_all':
            builder.button(text=localization.get('common.button.control_panel.event.newsletter_all_without_callback'), callback_data='ask_control_notification_broadcast_all')
    builder.adjust(1)
    return builder.as_markup()

def control_panel_administrators_edit_keyboard(*buttons: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for button in buttons:
        if button == 'request_control_administrators_add':
            builder.button(text=localization.get('common.button.control_panel.administrator.adding'), callback_data=f'ask_control_administrators_add')

        elif button == 'request_control_administrators_delete':
            builder.button(text=localization.get('common.button.control_panel.administrator.removing'), callback_data=f'ask_control_administrators_delete')

        elif button == 'request_control_administrators_list':
            builder.button(text=localization.get('common.button.control_panel.administrator.list'), callback_data=f'ask_control_administrators_list')

        elif button == 'request_control_panel':
            builder.button(text=localization.get('common.button.control_panel.menu'), callback_data='ask_control_panel')
    builder.adjust(1)
    return builder.as_markup()
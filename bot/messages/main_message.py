# Лучше умереть на ногах и с красным знаменем в руках, чем жить на коленях и кануть как раб...

from run import bot_name
from locales.localization import localization
from services.db_service import db_connection

async def menu_start_message() -> str:
    message_text = localization.get('common.text.user_panel.menu.head', bot_name=bot_name)
    events = await db_connection.events_list_public_get()
    if not events:
        message_text += localization.get('common.text.user_panel.menu.body.event_none')
    else:
        for event in events:
            event_status = localization.get('common.text.user_panel.menu.body.event_active') if event['event_is_active'] else localization.get('common.text.user_panel.menu.body.event_inactive')
            message_text += (f'{event['event_name']} {event_status} {event['event_date']}\n')
    return message_text
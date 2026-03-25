from aiogram.filters import BaseFilter
import logging
from aiogram.types import Message, User, CallbackQuery
from typing import Union
from services.db_service import db_connection

class FilterAdministrator(BaseFilter):
    async def __call__(self, obj: Union[Message, CallbackQuery, User, int, str]) -> bool:
        # Extract user ID (support int, str and Telegram objects)
        extract_id = None
        if isinstance(obj, (int, str)):
            extract_id = str(obj).strip()  # Convert all IDs to a string
        elif isinstance(obj, User):
            extract_id = str(obj.id)
        elif isinstance(obj, (Message, CallbackQuery)):
            extract_user = getattr(obj, 'from_user', None) or getattr(getattr(obj, 'message', None), 'from_user', None)
            if extract_user:
                extract_id = str(extract_user.id)
        if not extract_id:
            return False
        # Getting a list of administrators
        administrators_list = await db_connection.administrators_list()
        # Logging for debugging
        logging.debug(f"Checking access for user ID: {extract_id} (type: {type(extract_id)})")
        logging.debug(f"Admin records from DB: {administrators_list}")
        # Checking if the user is in the list of administrators_list
        for telegram_user_id in administrators_list:
            try:
                # We bring it to a string for comparison
                if str(telegram_user_id['telegram_user_id']).strip() == extract_id:
                    return True
            except KeyError as e:
                logging.debug(f"Error processing admin record {telegram_user_id}: {e}")
                continue
        return False
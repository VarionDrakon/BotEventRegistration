import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from decouple import config

admins_bot = [int(admin_id) for admin_id in config('ADMINS').split(',')]
bot = Bot(token=config('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
db_name = config('DB_LINK')
bot_name = config('BOT_NAME')
feedback_chat_id = config('FEEDBACK_CHAT_ID')
version_bot = config('VERSION')
organization_name = config('ORGANIZATION_NAME')
language = config('LANGUAGE')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
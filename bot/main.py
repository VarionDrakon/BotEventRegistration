import asyncio
from run import bot, dp
from handlers.main_handler import main_router
from handlers.questionnaire_handler import questionnaire_router
from handlers.control_handler import control_router
from services.db_service import initialize_database
from locales.localization import initialize_localization

async def main():
    await initialize_localization()
    await initialize_database()
    dp.include_router(control_router)
    dp.include_router(questionnaire_router)
    dp.include_router(main_router)
     
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
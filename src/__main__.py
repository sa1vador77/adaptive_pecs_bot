import asyncio
from loguru import logger

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from src.core import config
from src.core import setup_logger
from src.database.models import Base
from src.bot.handlers import communication
from src.database.core import DatabaseManager
from src.bot.middlewares import DbSessionMiddleware


async def on_startup(db: DatabaseManager):
    """Действия при запуске (создание таблиц)."""
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("База данных инициализирована")


async def main():
    setup_logger()

    bot = Bot(
        token=config.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    db = DatabaseManager(db_url=config.DATABASE_URL)

    # Регистрация мидлварей
    dp.update.outer_middleware(DbSessionMiddleware(db.session_maker))

    # Регистрация роутеров
    dp.include_router(communication.router)

    # Хуки

    logger.info("Запуск бота...")
    try:
        await on_startup(db)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")

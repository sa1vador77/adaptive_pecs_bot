from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.core import config


class DatabaseManager:
    """
    Класс для управления подключением к базе данных.
    Инкапсулирует создание движка (engine) и фабрики сессий.
    """

    def __init__(self, db_url: str, echo: bool = False):
        # Создаем асинхронный движок
        self.engine = create_async_engine(
            db_url,
            echo=echo,
        )

        # Фабрика сессий. expire_on_commit=False обязателен для async
        self.session_maker = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def close(self):
        """Корректное закрытие соединения с БД при остановке бота."""
        await self.engine.dispose()


# Глобальный экземпляр менеджера БД
db_manager = DatabaseManager(
    db_url=config.DATABASE_URL,
    echo=False,
)


async def get_session() -> AsyncGenerator:
    """
    Генератор сессий.
    Возвращает асинхронный генератор, который yield-ит сессию.
    """
    async with db_manager.session_maker() as session:
        yield session

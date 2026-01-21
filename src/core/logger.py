import sys
from loguru import logger


def setup_logger():
    """Настройка конфигурации логгера Loguru."""
    logger.remove()

    # Формат логов: время | уровень | модуль:строка | сообщение
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    logger.add(sys.stderr, format=log_format, level="INFO")
    logger.add("logs/bot.log", rotation="10 MB", compression="zip", level="DEBUG")

    logger.info("Логгер успешно инициализирован")

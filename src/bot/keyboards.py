from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database.models import Card


def build_adaptive_keyboard(cards: list[Card]) -> InlineKeyboardMarkup:
    """
    Строит клавиатуру на основе отсортированного списка карточек.
    Частые/важные карточки идут первыми и крупнее.
    """
    builder = InlineKeyboardBuilder()
    
    for card in cards:
        # Текст кнопки: Эмодзи (если есть в label) или Текст
        # callback_data содержит ID карточки для обработки
        builder.button(
            text=f"{card.label}", 
            callback_data=f"select_card:{card.id}"
        )
    
    # Сетка адаптивная: первые 2 самые важные кнопки - большие (по 1 в ряд или по 2),
    # остальные по 2 или 3 в ряд.
    builder.adjust(2, 2, 3)
    return builder.as_markup()

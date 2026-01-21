from loguru import logger

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.adapter import AdaptiveService
from src.bot.keyboards import build_adaptive_keyboard
from src.database.models import User, Card


router = Router(name="communication")


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    """Точка входа. Регистрирует пользователя и показывает пульт."""
    user = await session.get(User, message.from_user.id)
    if not user:
        logger.info(f"Новый пользователь: {message.from_user.id}")
        user = User(
            id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name
        )
        session.add(user)
        # Сид начальных данных (для демонстрации)
        # В реальном проекте это делается через миграции или админку
        if not (await session.get(Card, 1)):
            session.add_all([
                Card(label="💧 Пить", base_priority=100, slug="drink"),
                Card(label="🚽 Туалет", base_priority=90, slug="toilet"),
                Card(label="🍎 Есть", base_priority=80, slug="eat"),
                Card(label="🧸 Игрушка", base_priority=20, slug="toy"),
                Card(label="😴 Спать", base_priority=70, slug="sleep"),
                Card(label="😡 Болит", base_priority=100, slug="pain"),
            ])
        await session.commit()

    # Получаем адаптивный список
    cards = await AdaptiveService.get_sorted_cards(session, message.from_user.id)
    keyboard = build_adaptive_keyboard(cards)
    
    await message.answer(
        "👋 Привет! Это коммуникатор.\nВыбери, что ты хочешь:",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("select_card:"))
async def handle_selection(callback: CallbackQuery, session: AsyncSession):
    """Обработка нажатия на карточку."""
    card_id = int(callback.data.split(":")[1])
    
    # 1. Записываем выбор (обучение бота)
    await AdaptiveService.record_selection(session, callback.from_user.id, card_id)
    logger.debug(f"Пользователь {callback.from_user.id} выбрал карточку {card_id}")
    
    # 2. Получаем данные о карточке для ответа
    card = await session.get(Card, card_id)
    
    # 3. Визуальная обратная связь (можно отправить картинку или голосовое сообщение)
    await callback.answer(f"Ты выбрал: {card.label}")
    await callback.message.answer(f"📢 <b>Я ХОЧУ: {card.label.upper()}</b>")
    
    # 4. Перестраиваем клавиатуру (она может измениться из-за обновления весов)
    # В реальной жизни лучше не менять порядок мгновенно, чтобы не путать ребенка,
    # но для демонстрации адаптивности в курсовой — меняем сразу.
    cards = await AdaptiveService.get_sorted_cards(session, callback.from_user.id)
    new_keyboard = build_adaptive_keyboard(cards)
    
    await callback.message.answer("Что-то еще?", reply_markup=new_keyboard)

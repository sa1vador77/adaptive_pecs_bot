from loguru import logger

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, Command, CommandObject

from src.services.adapter import AdaptiveService
from src.bot.keyboards import build_adaptive_keyboard
from src.database.models import User, Card


router = Router(name="communication")


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    """
    Точка входа.
    Инициализирует пользователя и показывает главное меню карточек.
    """
    user = await session.get(User, message.from_user.id)
    if not user:
        logger.info(f"Регистрация нового пользователя: {message.from_user.id}")
        user = User(
            id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )
        session.add(user)

        # Сид начальных данных (если таблица пустая)
        result = await session.execute(select(Card))
        if not result.scalars().first():
            logger.info("База пуста, добавляем дефолтные карточки")
            session.add_all(
                [
                    Card(label="💧 Пить", base_priority=100, slug="drink"),
                    Card(label="🚽 Туалет", base_priority=90, slug="toilet"),
                    Card(label="🍎 Есть", base_priority=80, slug="eat"),
                    Card(label="🧸 Игрушка", base_priority=20, slug="toy"),
                    Card(label="😴 Спать", base_priority=70, slug="sleep"),
                    Card(label="😡 Болит", base_priority=100, slug="pain"),
                ]
            )
        await session.commit()

    # Инструкция для курсовой
    if not user.guardian_id:
        await message.answer(
            "⚠️ <b>Режим настройки:</b>\n"
            "Чтобы сообщения приходили опекуну, введите команду:\n"
            f"<code>/set_guardian {message.from_user.id}</code>\n"
            "(в курсовой используем свой же ID для теста)"
        )

    cards = await AdaptiveService.get_sorted_cards(session, message.from_user.id)
    keyboard = build_adaptive_keyboard(cards)

    await message.answer("👋 Выбери карточку:", reply_markup=keyboard)


@router.message(Command("set_guardian"))
async def cmd_set_guardian(
    message: Message, command: CommandObject, session: AsyncSession
):
    """Установка ID опекуна для текущего пользователя."""
    if not command.args:
        await message.answer("Ошибка. Используйте: /set_guardian 123456789")
        return

    try:
        guardian_id = int(command.args)
    except ValueError:
        await message.answer("ID должен быть числом.")
        return

    user = await session.get(User, message.from_user.id)
    user.guardian_id = guardian_id
    await session.commit()

    logger.info(f"Пользователь {user.id} установил опекуна {guardian_id}")
    await message.answer(
        f"✅ Опекун установлен! Уведомления будут приходить на ID {guardian_id}"
    )


@router.callback_query(F.data.startswith("select_card:"))
async def handle_selection(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """
    Основная логика выбора карточки.

    Flow:
    1. Логируем выбор в БД (для алгоритма) и в консоль.
    2. Уведомляем опекуна.
    3. Удаляем старое меню (чтобы не засорять чат).
    4. Отправляем новое меню (с пересчитанными весами).
    """
    user_id = callback.from_user.id
    card_id = int(callback.data.split(":")[1])

    # --- 1. Логирование и Обучение ---
    await AdaptiveService.record_selection(session, user_id, card_id)

    card = await session.get(Card, card_id)
    user = await session.get(User, user_id)

    log_msg = f"Ребенок {user.full_name} ({user_id}) выбрал: {card.label}"
    logger.info(log_msg)

    # --- 2. Уведомление опекуна ---
    if user.guardian_id:
        try:
            await bot.send_message(
                chat_id=user.guardian_id,
                text=f"🔔 <b>УВЕДОМЛЕНИЕ ОТ РЕБЕНКА</b>\n\n{card.label} ({card.slug})",
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление опекуну: {e}")
            await callback.answer("Ошибка связи с опекуном", show_alert=True)
    else:
        logger.warning(f"У пользователя {user_id} не настроен опекун")

    # --- 3. UI Обратная связь ---
    # Показываем "всплывашку" ребенку, что сигнал отправлен
    await callback.answer(f"Отправлено: {card.label}")

    # --- 4. Очистка и Обновление ---
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        # Сообщение могло быть уже удалено
        pass

    # Получаем обновленный список (порядок кнопок мог измениться!)
    cards = await AdaptiveService.get_sorted_cards(session, user_id)
    new_keyboard = build_adaptive_keyboard(cards)

    await callback.message.answer("Что-то еще?", reply_markup=new_keyboard)

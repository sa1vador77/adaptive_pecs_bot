import math

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import config
from src.database.models import Card, ActionLog

class AdaptiveService:
    """Сервис для ранжирования карточек на основе потребностей ребенка."""

    @staticmethod
    async def get_sorted_cards(session: AsyncSession, user_id: int) -> list[Card]:
        """
        Возвращает список карточек, отсортированный по умному алгоритму.
        
        Алгоритм: Score = BasePriority + (Log(UsageCount) * Multiplier)
        Использование логарифма предотвращает замусоривание топа частыми, 
        но низкоприоритетными запросами (например, "игрушка").
        """
        # 1. Получаем все карточки
        stmt_cards = select(Card)
        result_cards = await session.execute(stmt_cards)
        cards = result_cards.scalars().all()

        # 2. Получаем статистику использования для конкретного ребенка
        # Сгруппируем логи по card_id и посчитаем количество
        stmt_stats = (
            select(ActionLog.card_id, func.count(ActionLog.id))
            .where(ActionLog.user_id == user_id)
            .group_by(ActionLog.card_id)
        )
        result_stats = await session.execute(stmt_stats)
        usage_map = {row[0]: row[1] for row in result_stats.all()}

        # 3. Вычисляем вес (Score) для каждой карточки
        ranked_cards: list[tuple[float, Card]] = []
        
        for card in cards:
            usage_count = usage_map.get(card.id, 0)
            
            # Логарифмическое сглаживание: log(1 + usage)
            # Если usage=0 -> 0
            # Если usage=10 -> 2.39
            # Если usage=100 -> 4.6
            # Это значит, что 100 нажатий на игрушку (Base 10) дадут:
            # 10 + (4.6 * 2.0) = 19.2.
            # А Туалет (Base 80) с 0 нажатий даст:
            # 80 + 0 = 80.
            usage_score = math.log1p(usage_count) * config.WEIGHT_USAGE_FACTOR
            
            total_score = card.base_priority + usage_score
            ranked_cards.append((total_score, card))

        # 4. Сортируем по убыванию Score
        ranked_cards.sort(key=lambda x: x[0], reverse=True)

        return [item[1] for item in ranked_cards]

    @staticmethod
    async def record_selection(session: AsyncSession, user_id: int, card_id: int):
        """Фиксирует выбор ребенка для переобучения модели."""
        log_entry = ActionLog(user_id=user_id, card_id=card_id)
        session.add(log_entry)
        await session.commit()

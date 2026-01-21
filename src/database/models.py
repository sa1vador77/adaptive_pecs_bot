import datetime

from sqlalchemy import BigInteger, String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), server_default=func.now()
    )


class User(Base):
    """Модель пользователя (ребенка/родителя)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(32), nullable=True)
    full_name: Mapped[str] = mapped_column(String(64))
    # ID Telegram аккаунта опекуна/родителя
    guardian_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class Card(Base):
    """
    Карточка PECS (действие/предмет).

    base_priority:
        100 - Жизненно важно (Вода, Еда, Туалет, Боль)
        50  - Важно (Холодно, Жарко)
        10  - Развлечения (Игрушка, Мультик)
    """

    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(20), unique=True)  # для callback data
    label: Mapped[str] = mapped_column(String(50))  # Текст на кнопке
    image_url: Mapped[str | None] = mapped_column(String(255))  # Ссылка на картинку
    base_priority: Mapped[int] = mapped_column(Integer, default=10)


class ActionLog(Base):
    """Журнал действий для аналитики и адаптации."""

    __tablename__ = "action_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"))

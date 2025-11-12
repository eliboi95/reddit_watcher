from sqlalchemy import Integer, String, Boolean, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


"""MODELS"""


class Base(DeclarativeBase):
    """Base Model"""

    pass


class WatchedSubreddit(Base):
    __tablename__ = "watched_subreddits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class WatchedRedditor(Base):
    __tablename__ = "watched_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    muted_until: Mapped[float] = mapped_column(Float, default=0)
    rating: Mapped[int] = mapped_column(Integer, default=5)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    type: Mapped[str] = mapped_column(String)
    author: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    created_utc: Mapped[int] = mapped_column(Integer)
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)


class TelegramUser(Base):
    __tablename__ = "telegram_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[str] = mapped_column(String, unique=True)
    username: Mapped[str] = mapped_column(String, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

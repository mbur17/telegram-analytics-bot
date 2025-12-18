from datetime import datetime
from typing import List

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from const import DEFAULT_ZERO, MAX_CREATOR_ID, MAX_SNAP_ID, MAX_VID_ID


class Base(DeclarativeBase):
    __abstract__ = True


class CountMixin():
    __abstract__ = True

    views_count: Mapped[int] = mapped_column(
        BigInteger, default=DEFAULT_ZERO, nullable=False
    )
    likes_count: Mapped[int] = mapped_column(
        BigInteger, default=DEFAULT_ZERO, nullable=False
    )
    comments_count: Mapped[int] = mapped_column(
        BigInteger, default=DEFAULT_ZERO, nullable=False
    )
    reports_count: Mapped[int] = mapped_column(
        BigInteger, default=DEFAULT_ZERO, nullable=False
    )


class TimeStampMixin():
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class Video(Base, CountMixin, TimeStampMixin):
    """Model for video statistics."""
    __tablename__ = 'videos'

    id: Mapped[str] = mapped_column(String(MAX_VID_ID), primary_key=True)
    creator_id: Mapped[str] = mapped_column(
        String(MAX_CREATOR_ID), nullable=False, index=True
    )
    video_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    snapshots: Mapped[List['VideoSnapshot']] = relationship(
        'VideoSnapshot',
        back_populates='video',
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    def __repr__(self):
        return f'Video(id={self.id}, creator_id={self.creator_id})'


class VideoSnapshot(Base, CountMixin, TimeStampMixin):
    """Model for hourly video snapshots."""
    __tablename__ = 'video_snapshots'

    id: Mapped[str] = mapped_column(String(MAX_SNAP_ID), primary_key=True)
    video_id: Mapped[str] = mapped_column(
        String(MAX_VID_ID),
        ForeignKey('videos.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    delta_views_count: Mapped[int] = mapped_column(
        BigInteger, default=DEFAULT_ZERO, nullable=False
    )
    delta_likes_count: Mapped[int] = mapped_column(
        BigInteger, default=DEFAULT_ZERO, nullable=False
    )
    delta_comments_count: Mapped[int] = mapped_column(
        BigInteger, default=DEFAULT_ZERO, nullable=False
    )
    delta_reports_count: Mapped[int] = mapped_column(
        BigInteger, default=DEFAULT_ZERO, nullable=False
    )

    video: Mapped['Video'] = relationship('Video', back_populates='snapshots')

    __table_args__ = (
        Index('idx_video_snapshots_video_created', 'video_id', 'created_at'),
    )

    def __repr__(self):
        return f'VideoSnapshot(id={self.id}, video_id={self.video_id})'

"""
TimeEntry model — tracks time spent on a task (start/stop timer).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class TimeEntry(Base):
    __tablename__ = "time_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    ended_at = Column(DateTime, nullable=True)  # NULL means timer is still running
    duration_seconds = Column(Integer, nullable=True)  # Computed on stop
    note = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    task = relationship("Task", back_populates="time_entries")

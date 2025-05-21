from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, Enum
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.config.settings import settings
import enum

class ActionType(enum.Enum):
    activado = "activado"
    desactivado = "desactivado"

class UserAction(Base):
    """Historial de acciones de activación/desactivación de usuarios."""
    __tablename__ = "user_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    u_action = Column(Enum(ActionType), nullable=False)
    u_reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=settings.CURRENT_TIME, nullable=False)

    user = relationship("User", back_populates="actions")

    def __init__(self, user_id, action, reason):
        self.user_id = user_id
        self.u_action = action
        self.u_reason = reason
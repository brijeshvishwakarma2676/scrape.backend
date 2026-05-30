from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    phone = Column(String(50))
    website = Column(String(500))
    address = Column(Text)
    rating = Column(Float)
    review_count = Column(Integer, default=0)
    website_status = Column(String(20), default="UNCHECKED")  # UNCHECKED, NO_WEBSITE, WORKING, BROKEN
    lead_status = Column(String(20), default="NEW")  # NEW, CONTACTED, INTERESTED, WON, LOST
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    messages = relationship("Message", back_populates="business", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    generated_message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    business = relationship("Business", back_populates="messages")

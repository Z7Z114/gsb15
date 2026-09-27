from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Date, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20))
    role = Column(String(20), nullable=False)  # farmer, consumer
    join_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    preferences = Column(JSON, default=dict)

    conversations = relationship("Conversation", back_populates="member")
    feedbacks = relationship("Feedback", back_populates="member")


class Vegetable(Base):
    __tablename__ = "vegetables"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    english_name = Column(String(100))
    season = Column(String(20), nullable=False)  # spring, summer, autumn, winter
    planting_start = Column(Date)
    planting_end = Column(Date)
    harvest_start = Column(Date)
    harvest_end = Column(Date)
    description = Column(Text)
    nutritional_value = Column(Text)
    storage_method = Column(Text)
    image_url = Column(String(500))
    is_available = Column(Boolean, default=True)
    share_quota = Column(Integer, default=0)

    calendar_entries = relationship("PlantingCalendar", back_populates="vegetable")


class PlantingCalendar(Base):
    __tablename__ = "planting_calendar"

    id = Column(Integer, primary_key=True, index=True)
    vegetable_id = Column(Integer, ForeignKey("vegetables.id"), nullable=False)
    activity_type = Column(String(50), nullable=False)  # planting, watering, fertilizing, harvesting
    activity_date = Column(Date, nullable=False)
    description = Column(Text)
    completed = Column(Boolean, default=False)

    vegetable = relationship("Vegetable", back_populates="calendar_entries")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    title = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="active")  # active, closed, archived

    member = relationship("Member", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.timestamp")
    transcript = relationship("Transcript", back_populates="conversation", uselist=False)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender_role = Column(String(20), nullable=False)  # farmer, consumer, system
    speaker_id = Column(String(100))
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    audio_file_path = Column(String(500))
    raw_transcript = Column(Text)
    processed_transcript = Column(JSON)
    diarization_result = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="transcript")


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    feedback_type = Column(String(50), nullable=False)  # taste, delivery, quality, other
    content = Column(Text, nullable=False)
    rating = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    member = relationship("Member", back_populates="feedbacks")


class AISummary(Base):
    __tablename__ = "ai_summaries"

    id = Column(Integer, primary_key=True, index=True)
    summary_type = Column(String(50), nullable=False)  # planting_intent, share_adjustment, meeting_summary
    content = Column(JSON, nullable=False)
    source_conversation_ids = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    version = Column(String(20), default="1.0")


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    vegetables_used = Column(JSON, nullable=False)
    ingredients = Column(JSON, nullable=False)
    steps = Column(JSON, nullable=False)
    cooking_time = Column(Integer)
    difficulty = Column(String(20))
    image_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

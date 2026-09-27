from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class RoleEnum(str, Enum):
    farmer = "farmer"
    consumer = "consumer"


class MemberBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    role: RoleEnum
    preferences: Optional[Dict[str, Any]] = None


class MemberCreate(MemberBase):
    pass


class Member(MemberBase):
    id: int
    join_date: datetime
    is_active: bool

    class Config:
        from_attributes = True


class VegetableBase(BaseModel):
    name: str
    english_name: Optional[str] = None
    season: str
    planting_start: Optional[date] = None
    planting_end: Optional[date] = None
    harvest_start: Optional[date] = None
    harvest_end: Optional[date] = None
    description: Optional[str] = None
    nutritional_value: Optional[str] = None
    storage_method: Optional[str] = None
    image_url: Optional[str] = None
    is_available: bool = True
    share_quota: int = 0


class VegetableCreate(VegetableBase):
    pass


class VegetableUpdate(VegetableBase):
    id: int

    class Config:
        from_attributes = True


class Vegetable(VegetableBase):
    id: int

    class Config:
        from_attributes = True


class PlantingCalendarBase(BaseModel):
    vegetable_id: int
    activity_type: str
    activity_date: date
    description: Optional[str] = None
    completed: bool = False


class PlantingCalendarCreate(PlantingCalendarBase):
    pass


class PlantingCalendar(PlantingCalendarBase):
    id: int

    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    member_id: int
    title: Optional[str] = None
    status: str = "active"


class ConversationCreate(ConversationBase):
    pass


class Conversation(ConversationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    conversation_id: int
    sender_role: str
    speaker_id: Optional[str] = None
    content: str


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class TranscriptBase(BaseModel):
    conversation_id: int
    audio_file_path: Optional[str] = None
    raw_transcript: Optional[str] = None
    processed_transcript: Optional[Dict[str, Any]] = None
    diarization_result: Optional[Dict[str, Any]] = None


class TranscriptCreate(TranscriptBase):
    pass


class Transcript(TranscriptBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackBase(BaseModel):
    member_id: int
    conversation_id: Optional[int] = None
    feedback_type: str
    content: str
    rating: Optional[int] = None


class FeedbackCreate(FeedbackBase):
    pass


class Feedback(FeedbackBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AISummaryBase(BaseModel):
    summary_type: str
    content: Dict[str, Any]
    source_conversation_ids: Optional[List[int]] = None


class AISummaryCreate(AISummaryBase):
    pass


class AISummary(AISummaryBase):
    id: int
    created_at: datetime
    version: str

    class Config:
        from_attributes = True


class RecipeBase(BaseModel):
    title: str
    vegetables_used: List[str]
    ingredients: List[Dict[str, Any]]
    steps: List[str]
    cooking_time: Optional[int] = None
    difficulty: Optional[str] = None
    image_url: Optional[str] = None


class RecipeCreate(RecipeBase):
    pass


class Recipe(RecipeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AudioTranscribeRequest(BaseModel):
    conversation_id: int


class PlantingIntentResponse(BaseModel):
    next_season_vegetables: List[Dict[str, Any]]
    share_adjustments: Dict[str, Any]
    member_preferences: Dict[str, Any]
    recommendations: List[str]


class EmailRequest(BaseModel):
    to_emails: List[EmailStr]
    subject: str
    content: str
    include_recipes: bool = True

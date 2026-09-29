from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil

from app.database import get_db
from app.models import Conversation, Message, Member, Transcript, Feedback
from app.schemas import (
    ConversationCreate,
    Conversation as ConversationSchema,
    MessageCreate,
    Message as MessageSchema,
    TranscriptCreate,
    Transcript as TranscriptSchema,
    FeedbackCreate,
    Feedback as FeedbackSchema
)

router = APIRouter()

UPLOAD_DIR = "uploads/audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/", response_model=List[ConversationSchema])
def get_conversations(
    member_id: Optional[int] = None,
    status: Optional[str] = None,
    memberId: Optional[int] = None,
    db: Session = Depends(get_db)
):
    if member_id is None:
        member_id = memberId
    query = db.query(Conversation)
    if member_id:
        query = query.filter(Conversation.member_id == member_id)
    if status:
        query = query.filter(Conversation.status == status)
    return query.order_by(Conversation.created_at.desc()).all()


@router.get("/{conversation_id}", response_model=ConversationSchema)
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    return conversation


@router.post("/", response_model=ConversationSchema)
def create_conversation(conversation: ConversationCreate, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == conversation.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="会员不存在")
    db_conversation = Conversation(**conversation.model_dump())
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation


@router.get("/{conversation_id}/messages", response_model=List[MessageSchema])
def get_conversation_messages(conversation_id: int, db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    return conversation.messages


@router.post("/messages", response_model=MessageSchema)
def create_message(message: MessageCreate, db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(Conversation.id == message.conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    db_message = Message(**message.model_dump())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


@router.post("/{conversation_id}/upload-audio")
async def upload_audio(
    conversation_id: int,
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    safe_filename = os.path.basename((audio_file.filename or "").replace("\\", "/")) or "audio"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_location = os.path.join(UPLOAD_DIR, f"{conversation_id}_{safe_filename}")
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(audio_file.file, buffer)

    transcript = db.query(Transcript).filter(Transcript.conversation_id == conversation_id).first()
    if transcript:
        transcript.audio_file_path = file_location
    else:
        transcript = Transcript(conversation_id=conversation_id, audio_file_path=file_location)
        db.add(transcript)
    db.commit()

    return {
        "filename": safe_filename,
        "file_path": file_location,
        "conversation_id": conversation_id
    }


@router.get("/{conversation_id}/transcript", response_model=Optional[TranscriptSchema])
def get_transcript(conversation_id: int, db: Session = Depends(get_db)):
    transcript = db.query(Transcript).filter(Transcript.conversation_id == conversation_id).first()
    return transcript


@router.post("/transcript", response_model=TranscriptSchema)
def create_transcript(transcript: TranscriptCreate, db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(Conversation.id == transcript.conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    db_transcript = db.query(Transcript).filter(
        Transcript.conversation_id == transcript.conversation_id
    ).first()
    if db_transcript:
        for key, value in transcript.model_dump(exclude={"conversation_id"}).items():
            setattr(db_transcript, key, value)
    else:
        db_transcript = Transcript(**transcript.model_dump())
        db.add(db_transcript)
    db.commit()
    db.refresh(db_transcript)
    return db_transcript


@router.post("/feedback", response_model=FeedbackSchema)
def create_feedback(feedback: FeedbackCreate, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == feedback.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="会员不存在")
    db_feedback = Feedback(**feedback.model_dump())
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback


@router.get("/feedback/list", response_model=List[FeedbackSchema])
def get_feedbacks(
    member_id: Optional[int] = None,
    feedback_type: Optional[str] = None,
    memberId: Optional[int] = None,
    feedbackType: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if member_id is None:
        member_id = memberId
    if feedback_type is None:
        feedback_type = feedbackType
    query = db.query(Feedback)
    if member_id:
        query = query.filter(Feedback.member_id == member_id)
    if feedback_type:
        query = query.filter(Feedback.feedback_type == feedback_type)
    return query.order_by(Feedback.created_at.desc()).all()

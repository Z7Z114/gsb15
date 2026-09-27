from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import Conversation, Transcript, AISummary, Vegetable, Feedback, Recipe
from app.schemas import AISummaryCreate, PlantingIntentResponse, RecipeCreate
from app.services.ai_service import ai_service

router = APIRouter()


@router.post("/transcribe/{conversation_id}")
async def transcribe_conversation(
    conversation_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    transcript = db.query(Transcript).filter(Transcript.conversation_id == conversation_id).first()
    if not transcript or not transcript.audio_file_path:
        raise HTTPException(status_code=400, detail="对话没有音频文件")

    async def process_transcription():
        audio_path = transcript.audio_file_path

        transcript_data = await ai_service.transcribe_audio(audio_path)
        diarization_data = await ai_service.diarize_audio(audio_path)
        merged_segments = await ai_service.merge_transcript_and_diarization(
            transcript_data, diarization_data
        )
        speaker_roles = await ai_service.classify_speaker_roles(merged_segments)

        transcript.raw_transcript = transcript_data["raw_text"]
        transcript.processed_transcript = {
            "segments": merged_segments,
            "speaker_roles": speaker_roles
        }
        transcript.diarization_result = diarization_data
        db.commit()

    background_tasks.add_task(process_transcription)

    return {
        "message": "转写任务已启动",
        "conversation_id": conversation_id
    }


@router.get("/transcribe/{conversation_id}/status")
def get_transcription_status(conversation_id: int, db: Session = Depends(get_db)):
    transcript = db.query(Transcript).filter(Transcript.conversation_id == conversation_id).first()
    if not transcript:
        raise HTTPException(status_code=404, detail="转写记录不存在")

    return {
        "conversation_id": conversation_id,
        "has_raw_transcript": transcript.raw_transcript is not None,
        "has_processed_transcript": transcript.processed_transcript is not None,
        "has_diarization": transcript.diarization_result is not None
    }


@router.post("/extract-feedback/{conversation_id}")
async def extract_feedback(conversation_id: int, db: Session = Depends(get_db)):
    transcript = db.query(Transcript).filter(Transcript.conversation_id == conversation_id).first()
    if not transcript or not transcript.processed_transcript:
        raise HTTPException(status_code=400, detail="请先完成音频转写")

    processed = transcript.processed_transcript
    merged_segments = processed.get("segments", [])
    speaker_roles = processed.get("speaker_roles", {})

    feedback = await ai_service.extract_preferences_and_feedback(merged_segments, speaker_roles)

    return {
        "conversation_id": conversation_id,
        "feedback": feedback
    }


@router.post("/generate-planting-intent", response_model=PlantingIntentResponse)
async def generate_planting_intent(
    conversation_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Feedback)
    if conversation_ids:
        query = query.filter(Feedback.conversation_id.in_(conversation_ids))
    all_feedback = query.all()

    feedback_data = [
        {
            "feedback_type": fb.feedback_type,
            "content": fb.content,
            "rating": fb.rating
        }
        for fb in all_feedback
    ]

    vegetables = db.query(Vegetable).filter(Vegetable.is_available == True).all()
    vegetables_data = [
        {
            "id": v.id,
            "name": v.name,
            "season": v.season,
            "share_quota": v.share_quota
        }
        for v in vegetables
    ]

    planting_intent = await ai_service.generate_planting_intent(feedback_data, vegetables_data)

    ai_summary = AISummary(
        summary_type="planting_intent",
        content=planting_intent,
        source_conversation_ids=conversation_ids or []
    )
    db.add(ai_summary)
    db.commit()

    return planting_intent


@router.post("/generate-recipes")
async def generate_recipes(
    vegetables: List[str],
    count: int = 3,
    db: Session = Depends(get_db)
):
    recipes = await ai_service.generate_recipes(vegetables, count)

    saved_recipes = []
    for recipe_data in recipes:
        recipe = Recipe(**recipe_data)
        db.add(recipe)
        db.flush()
        saved_recipes.append({
            "id": recipe.id,
            **recipe_data
        })

    db.commit()

    return {
        "recipes": saved_recipes
    }


@router.post("/meeting-summary/{conversation_id}")
async def generate_meeting_summary(conversation_id: int, db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    messages = [
        {
            "sender_role": msg.sender_role,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat()
        }
        for msg in conversation.messages
    ]

    transcript = db.query(Transcript).filter(Transcript.conversation_id == conversation_id).first()
    speaker_roles = {}
    if transcript and transcript.processed_transcript:
        speaker_roles = transcript.processed_transcript.get("speaker_roles", {})

    summary = await ai_service.generate_meeting_summary(messages, speaker_roles)

    ai_summary = AISummary(
        summary_type="meeting_summary",
        content=summary,
        source_conversation_ids=[conversation_id]
    )
    db.add(ai_summary)
    db.commit()

    return {
        "conversation_id": conversation_id,
        "summary": summary
    }


@router.get("/summaries")
def get_ai_summaries(
    summary_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AISummary)
    if summary_type:
        query = query.filter(AISummary.summary_type == summary_type)
    return query.order_by(AISummary.created_at.desc()).all()


@router.get("/recipes", response_model=List)
def get_recipes(db: Session = Depends(get_db)):
    recipes = db.query(Recipe).order_by(Recipe.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "vegetables_used": r.vegetables_used,
            "ingredients": r.ingredients,
            "steps": r.steps,
            "cooking_time": r.cooking_time,
            "difficulty": r.difficulty,
            "image_url": r.image_url,
            "created_at": r.created_at
        }
        for r in recipes
    ]

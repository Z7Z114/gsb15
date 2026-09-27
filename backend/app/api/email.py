from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import Member, AISummary, Recipe, Vegetable
from app.schemas import EmailRequest
from app.services.email_service import email_service

router = APIRouter()


@router.post("/send")
async def send_email(email_request: EmailRequest, db: Session = Depends(get_db)):
    recipes = []
    if email_request.include_recipes:
        db_recipes = db.query(Recipe).order_by(Recipe.created_at.desc()).limit(3).all()
        recipes = [
            {
                "title": r.title,
                "vegetables_used": r.vegetables_used,
                "ingredients": r.ingredients,
                "steps": r.steps,
                "cooking_time": r.cooking_time,
                "difficulty": r.difficulty
            }
            for r in db_recipes
        ]

    success = await email_service.send_newsletter(
        to_emails=email_request.to_emails,
        title=email_request.subject,
        content=email_request.content,
        recipes=recipes
    )

    if not success:
        raise HTTPException(status_code=500, detail="邮件发送失败")

    return {"message": "邮件发送成功", "recipients": email_request.to_emails}


@router.post("/send-to-all")
async def send_to_all(
    subject: str,
    content: str,
    include_recipes: bool = True,
    role: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Member).filter(Member.is_active == True)
    if role:
        query = query.filter(Member.role == role)
    members = query.all()
    emails = [member.email for member in members]

    recipes = []
    if include_recipes:
        db_recipes = db.query(Recipe).order_by(Recipe.created_at.desc()).limit(3).all()
        recipes = [
            {
                "title": r.title,
                "vegetables_used": r.vegetables_used,
                "ingredients": r.ingredients,
                "steps": r.steps,
                "cooking_time": r.cooking_time,
                "difficulty": r.difficulty
            }
            for r in db_recipes
        ]

    success = await email_service.send_newsletter(
        to_emails=emails,
        title=subject,
        content=content,
        recipes=recipes
    )

    if not success:
        raise HTTPException(status_code=500, detail="邮件发送失败")

    return {"message": "邮件发送成功", "recipient_count": len(emails)}


@router.post("/send-planting-intent")
async def send_planting_intent(
    summary_id: int,
    db: Session = Depends(get_db)
):
    summary = db.query(AISummary).filter(AISummary.id == summary_id).first()
    if not summary or summary.summary_type != "planting_intent":
        raise HTTPException(status_code=404, detail="种植计划摘要不存在")

    members = db.query(Member).filter(Member.is_active == True).all()
    emails = [member.email for member in members]

    success = await email_service.send_planting_intent_update(
        to_emails=emails,
        planting_intent=summary.content
    )

    if not success:
        raise HTTPException(status_code=500, detail="邮件发送失败")

    return {"message": "种植计划邮件发送成功", "recipient_count": len(emails)}


@router.post("/send-meeting-summary")
async def send_meeting_summary(
    summary_id: int,
    db: Session = Depends(get_db)
):
    summary = db.query(AISummary).filter(AISummary.id == summary_id).first()
    if not summary or summary.summary_type != "meeting_summary":
        raise HTTPException(status_code=404, detail="会议摘要不存在")

    members = db.query(Member).filter(Member.is_active == True).all()
    emails = [member.email for member in members]

    success = await email_service.send_meeting_summary(
        to_emails=emails,
        meeting_summary=summary.content
    )

    if not success:
        raise HTTPException(status_code=500, detail="邮件发送失败")

    return {"message": "会议纪要邮件发送成功", "recipient_count": len(emails)}


@router.post("/send-weekly-update")
async def send_weekly_update(
    week_number: int,
    include_recipes: bool = True,
    db: Session = Depends(get_db)
):
    vegetables = db.query(Vegetable).filter(Vegetable.is_available == True).all()
    vegetables_data = [
        {
            "name": v.name,
            "description": v.description or ""
        }
        for v in vegetables
    ]

    recipes = []
    if include_recipes:
        db_recipes = db.query(Recipe).order_by(Recipe.created_at.desc()).limit(3).all()
        recipes = [
            {
                "title": r.title,
                "vegetables_used": r.vegetables_used,
                "ingredients": r.ingredients,
                "steps": r.steps,
                "cooking_time": r.cooking_time,
                "difficulty": r.difficulty
            }
            for r in db_recipes
        ]

    members = db.query(Member).filter(Member.is_active == True).all()
    emails = [member.email for member in members]

    success = await email_service.send_weekly_update(
        to_emails=emails,
        week_number=week_number,
        available_vegetables=vegetables_data,
        recipes=recipes
    )

    if not success:
        raise HTTPException(status_code=500, detail="邮件发送失败")

    return {"message": "每周更新邮件发送成功", "recipient_count": len(emails)}

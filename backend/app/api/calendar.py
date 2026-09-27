from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.database import get_db
from app.models import PlantingCalendar, Vegetable
from app.schemas import PlantingCalendarCreate, PlantingCalendar as PlantingCalendarSchema

router = APIRouter()


@router.get("/", response_model=List[PlantingCalendarSchema])
def get_calendar(
    start_date: date = None,
    end_date: date = None,
    activity_type: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(PlantingCalendar)
    if start_date:
        query = query.filter(PlantingCalendar.activity_date >= start_date)
    if end_date:
        query = query.filter(PlantingCalendar.activity_date <= end_date)
    if activity_type:
        query = query.filter(PlantingCalendar.activity_type == activity_type)
    return query.order_by(PlantingCalendar.activity_date).all()


@router.get("/vegetable/{vegetable_id}", response_model=List[PlantingCalendarSchema])
def get_vegetable_calendar(vegetable_id: int, db: Session = Depends(get_db)):
    vegetable = db.query(Vegetable).filter(Vegetable.id == vegetable_id).first()
    if not vegetable:
        raise HTTPException(status_code=404, detail="蔬菜品种不存在")
    return db.query(PlantingCalendar).filter(
        PlantingCalendar.vegetable_id == vegetable_id
    ).order_by(PlantingCalendar.activity_date).all()


@router.post("/", response_model=PlantingCalendarSchema)
def create_calendar_entry(entry: PlantingCalendarCreate, db: Session = Depends(get_db)):
    vegetable = db.query(Vegetable).filter(Vegetable.id == entry.vegetable_id).first()
    if not vegetable:
        raise HTTPException(status_code=404, detail="蔬菜品种不存在")
    db_entry = PlantingCalendar(**entry.model_dump())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry


@router.put("/{entry_id}", response_model=PlantingCalendarSchema)
def update_calendar_entry(
    entry_id: int,
    entry: PlantingCalendarCreate,
    db: Session = Depends(get_db)
):
    db_entry = db.query(PlantingCalendar).filter(PlantingCalendar.id == entry_id).first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="日历条目不存在")
    for key, value in entry.model_dump().items():
        setattr(db_entry, key, value)
    db.commit()
    db.refresh(db_entry)
    return db_entry


@router.delete("/{entry_id}")
def delete_calendar_entry(entry_id: int, db: Session = Depends(get_db)):
    db_entry = db.query(PlantingCalendar).filter(PlantingCalendar.id == entry_id).first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="日历条目不存在")
    db.delete(db_entry)
    db.commit()
    return {"message": "日历条目已删除"}


@router.patch("/{entry_id}/toggle")
def toggle_completed(entry_id: int, db: Session = Depends(get_db)):
    db_entry = db.query(PlantingCalendar).filter(PlantingCalendar.id == entry_id).first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="日历条目不存在")
    db_entry.completed = not db_entry.completed
    db.commit()
    return {"completed": db_entry.completed}

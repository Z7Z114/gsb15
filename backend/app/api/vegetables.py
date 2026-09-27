from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Vegetable
from app.schemas import VegetableCreate, VegetableUpdate, Vegetable as VegetableSchema

router = APIRouter()


@router.get("/", response_model=List[VegetableSchema])
def get_vegetables(season: str = None, available_only: bool = True, db: Session = Depends(get_db)):
    query = db.query(Vegetable)
    if season:
        query = query.filter(Vegetable.season == season)
    if available_only:
        query = query.filter(Vegetable.is_available == True)
    return query.all()


@router.get("/{vegetable_id}", response_model=VegetableSchema)
def get_vegetable(vegetable_id: int, db: Session = Depends(get_db)):
    vegetable = db.query(Vegetable).filter(Vegetable.id == vegetable_id).first()
    if not vegetable:
        raise HTTPException(status_code=404, detail="蔬菜品种不存在")
    return vegetable


@router.post("/", response_model=VegetableSchema)
def create_vegetable(vegetable: VegetableCreate, db: Session = Depends(get_db)):
    db_vegetable = Vegetable(**vegetable.model_dump())
    db.add(db_vegetable)
    db.commit()
    db.refresh(db_vegetable)
    return db_vegetable


@router.put("/{vegetable_id}", response_model=VegetableSchema)
def update_vegetable(vegetable_id: int, vegetable: VegetableUpdate, db: Session = Depends(get_db)):
    db_vegetable = db.query(Vegetable).filter(Vegetable.id == vegetable_id).first()
    if not db_vegetable:
        raise HTTPException(status_code=404, detail="蔬菜品种不存在")
    for key, value in vegetable.model_dump().items():
        setattr(db_vegetable, key, value)
    db.commit()
    db.refresh(db_vegetable)
    return db_vegetable


@router.delete("/{vegetable_id}")
def delete_vegetable(vegetable_id: int, db: Session = Depends(get_db)):
    db_vegetable = db.query(Vegetable).filter(Vegetable.id == vegetable_id).first()
    if not db_vegetable:
        raise HTTPException(status_code=404, detail="蔬菜品种不存在")
    db.delete(db_vegetable)
    db.commit()
    return {"message": "蔬菜品种已删除"}

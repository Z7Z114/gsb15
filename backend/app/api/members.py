from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Member
from app.schemas import MemberCreate, Member as MemberSchema

router = APIRouter()


@router.get("/", response_model=List[MemberSchema])
def get_members(role: str = None, active_only: bool = True, db: Session = Depends(get_db)):
    query = db.query(Member)
    if role:
        query = query.filter(Member.role == role)
    if active_only:
        query = query.filter(Member.is_active == True)
    return query.all()


@router.get("/{member_id}", response_model=MemberSchema)
def get_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="会员不存在")
    return member


@router.post("/", response_model=MemberSchema)
def create_member(member: MemberCreate, db: Session = Depends(get_db)):
    existing_member = db.query(Member).filter(Member.email == member.email).first()
    if existing_member:
        raise HTTPException(status_code=400, detail="该邮箱已注册")
    db_member = Member(**member.model_dump())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


@router.put("/{member_id}", response_model=MemberSchema)
def update_member(member_id: int, member: MemberCreate, db: Session = Depends(get_db)):
    db_member = db.query(Member).filter(Member.id == member_id).first()
    if not db_member:
        raise HTTPException(status_code=404, detail="会员不存在")
    for key, value in member.model_dump().items():
        setattr(db_member, key, value)
    db.commit()
    db.refresh(db_member)
    return db_member


@router.delete("/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    db_member = db.query(Member).filter(Member.id == member_id).first()
    if not db_member:
        raise HTTPException(status_code=404, detail="会员不存在")
    db_member.is_active = False
    db.commit()
    return {"message": "会员已停用"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.api import vegetables, calendar, conversations, ai, email, members
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="CSA 会员大会菜篮子系统", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vegetables.router, prefix="/api/vegetables", tags=["蔬菜品种"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["种植日历"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["对话记录"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI服务"])
app.include_router(email.router, prefix="/api/email", tags=["邮件服务"])
app.include_router(members.router, prefix="/api/members", tags=["会员管理"])


@app.get("/")
async def root():
    return {"message": "CSA 会员大会菜篮子系统 API"}

from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text, UUID
from .db_setup import Base, engine
from datetime import datetime
from uuid import uuid4

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)

class Chat_Session(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(UUID, nullable=False, primary_key=True)
    user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)
    video_path = Column(String, default="")
    video_progress = Column(String, default="None") # "None", "Progress", "Success"
    video_text = Column(Text, default="")

class Message(Base):
    __tablename__ = "messages"

    id = Column(BigInteger, primary_key=True, index=True)
    session_id = Column(UUID, nullable=False)
    sender = Column(String, nullable=False)  # 'user' or 'model'
    content = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, nullable=False)
    mermaid_code = Column(Text, nullable=True)
    img = Column(Text, nullable=True)  # Base64 encoded image data 

# Base.metadata.create_all(bind=engine)
# User.__table__.drop(bind=engine)  # Ensure messages table is created
# Message.__table__.drop(bind=engine)  # Ensure messages table is created
# Chat_Session.__table__.drop(bind=engine)  # Ensure messages table is created
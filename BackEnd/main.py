from gemini_api import generate_image, generate_text, chat_with_model, get_evidence_pack
from auth import get_current_user, create_access_token
from utils import generate_audio

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException, status
import uvicorn

from sqlalchemy.orm import Session
from db_setup import models, schemas, utils
from db_setup.db_setup import engine, get_db

from datetime import datetime
from uuid import uuid4

# Initialize FastAPI app
app = FastAPI(
    title="Text Generation API",
    description="An API to generate text using Gemini models.",    
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Allow all domains
    allow_credentials=True,
    allow_methods=["*"],          # Allow all HTTP methods
    allow_headers=["*"],          # Allow all headers
)

# DB Setup
models.Base.metadata.create_all(bind=engine)  # Create tables


"""
API endpoint to process data
"""

@app.get("/")
async def root():
    return {"message": "Welcome to the Text Generation API!"}

@app.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_pw = utils.hash_password(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_pw, name=user.name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    access_token = create_access_token(data={"user_id": new_user.id})
    return JSONResponse(content = {"username": new_user.username, "access_token": access_token, "token_type": "bearer"})

@app.post("/login", status_code=status.HTTP_200_OK)
async def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not utils.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(data={"user_id": db_user.id})
    return JSONResponse(content = {"username": user.username, "access_token": access_token, "token_type": "bearer"})

@app.post("/forget-password", status_code=status.HTTP_200_OK)
async def forget_password(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db_user.hashed_password = utils.hash_password(user.password)
    
    db.commit()
    db.refresh(db_user)
    return JSONResponse(content = {"message": "Password reset successful."})

@app.get("/profile", status_code=status.HTTP_200_OK)
async def get_profile(
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == current_user_id).first()
    session_id_objects = db.query(models.Chat_Session).filter(models.Chat_Session.user_id == current_user_id).all()
    session_ids = [{"id": str(sid.session_id), "timestamp": str(sid.created_at)} for sid in session_id_objects]
    return JSONResponse(content = {"username": user.username, "name": user.name, "session_ids": session_ids})

@app.get("/get-all", status_code=status.HTTP_200_OK)
async def get_user_profiles(
    db: Session = Depends(get_db),
):
    users = db.query(models.User).all()
    user_list = [{"username": user.username, "name": user.name} for user in users]
    return JSONResponse(content={"users": user_list})

@app.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    username: str,
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"detail": "User deleted successfully"}

@app.get("/logout", status_code=status.HTTP_200_OK)
async def logout():
    return JSONResponse(content={"message": "Logout successful."})

@app.post("/change-name", status_code=status.HTTP_200_OK)
async def change_name(
    new_name: str,
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == current_user_id).first()
    user.name = new_name
    db.commit()
    db.refresh(user)
    return JSONResponse(content={"message": "Name updated successfully", "name": user.name})

@app.post("/gemini/gen_text", status_code=status.HTTP_200_OK)
async def generate_text_from_prompt(request: Request):
     # Or check the latest supported name
    data = await request.json()
    prompt = data.get('prompt')

    return JSONResponse(content={"success": True, "message": generate_text(prompt)})

@app.post("/gemini/gen_image", status_code=status.HTTP_200_OK)
async def generate_image_from_prompt(request: Request):
    data = await request.json()
    prompt = data.get('prompt')

    return JSONResponse(content={"success": True, **generate_image(prompt)})

@app.post("/gemini/gen_audio", status_code=status.HTTP_200_OK)
async def generate_audio_from_prompt(request: Request):
    data = await request.json()
    prompt = data.get('prompt')

    return JSONResponse(content={"success": True, "audio": generate_audio(prompt)})

@app.post("/chat/new", status_code=status.HTTP_201_CREATED)
async def create_chat_session(current_user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    new_session = models.Chat_Session(
        session_id=uuid4(),
        user_id=current_user_id,
        created_at=datetime.now()
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return {"session_id": str(new_session.session_id), "message": "New chat session created"}

@app.post("/chat/{session_id}/message", status_code=status.HTTP_200_OK)
async def send_message(session_id: str, request: Request, current_user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    data = await request.json()
    prompt = data.get('prompt')

    chat_session = db.query(models.Chat_Session).filter(models.Chat_Session.session_id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    if chat_session.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this chat session")
    

    messages = (
        db.query(models.Message)
        .filter(models.Message.session_id == session_id)
        .order_by(models.Message.created_at)
        .all()
    )

    # // ! Angshuman Roy
    refined_prompt = get_evidence_pack(prompt) 
    output = chat_with_model(refined_prompt, messages)  # Assuming generate_text is used for chat

    user_msg = models.Message(
        session_id=session_id,
        sender="user",
        content=prompt,
        created_at=datetime.now()
    )
    bot_msg = models.Message(
        session_id=session_id,
        sender="model",
        content=output,
        created_at=datetime.now()
    )
    db.add_all([user_msg, bot_msg])
    db.commit()

    return {"message": output}

@app.get("/chat/{session_id}/messages", status_code=status.HTTP_200_OK)
async def get_chat_messages(session_id: str, current_user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):

    chat_session = db.query(models.Chat_Session).filter(models.Chat_Session.session_id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    if chat_session.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this chat session")

    messages = (
        db.query(models.Message)
        .filter(models.Message.session_id == session_id)
        .order_by(models.Message.created_at)
        .all()
    )

    return JSONResponse(content = {"messages": [
        {
            "sender": msg.sender,
            "content": msg.content,
            "timestamp": str(msg.created_at),
            "mermaid_code": msg.mermaid_code,
            "img": msg.img
        }
        for msg in messages
    ]})


if __name__ == "__main__":
    # Run the code
    uvicorn.run('main:app', reload=True)
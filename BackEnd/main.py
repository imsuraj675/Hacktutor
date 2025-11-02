from gemini_api import (
    generate_image, generate_text, chat_with_model, 
    get_evidence_pack, normalize_task, generate_lesson, sanitize_lesson,
    gen_mermaid_snippet, gen_image_prompt, repair_mermaid
    )
from auth import get_current_user, create_access_token
from utils import generate_audio

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
import uvicorn
import pickle

from sqlalchemy.orm import Session
from db_setup import models, schemas, utils
from db_setup.db_setup import engine, get_db

from db_setup.schemas import (
    NormalizeRequest, TaskSpec, HelpfulNotesRequest, HelpfulNotesResponse,
    ChunkPayload, GenerateRequest, LessonDraft, FullLessonRequest,
    LessonWithAssets, EnrichedLessonSegment
)

from retrieval.hybrid_search import hybrid_search
from retrieval.summarize import summarize_to_notes

from media.pipeline import render_assets_for_lesson
from media.mermaid import render_mermaid

from datetime import datetime
from uuid import uuid4
import os, asyncio

from gen_video import createVideo

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

os.makedirs("artifacts", exist_ok=True)
app.mount("/artifacts", StaticFiles(directory="artifacts"), name="artifacts")
os.makedirs("local_data", exist_ok=True)
local_path = 'local_data'

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

    return {"session_id": str(new_session.session_id), "message": "New chat session created", "timestamp": str(new_session.created_at)}

@app.post("/chat/{session_id}/message", status_code=status.HTTP_200_OK)
async def send_message(session_id: str, request: Request, current_user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    data = await request.json()
    prompt = data.get('prompt')
    # is_image_render = data.get('is_image_render')

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

    # if is_image_render:
    output = api_full_lesson_rendered(prompt, messages)
    
    # else:
    #     output = api_full_lesson(prompt, messages)
    # // ! Angshuman Roy
    # refined_prompt = get_evidence_pack(prompt) 
    # output = chat_with_model(refined_prompt, messages)  # Assuming generate_text is used for chat

    user_msg = models.Message(
        session_id=session_id,
        sender="user",
        content=prompt,
        created_at=datetime.now()
    )
    bot_msg = models.Message(
        session_id=session_id,
        sender="model",
        content='\n'.join([seg.text for seg in output.segments]),
        created_at=datetime.now()
    )
    db.add_all([user_msg, bot_msg])
    db.commit()

    with open(f'{local_path}\\{session_id}_{bot_msg.id}.pkl', 'wb') as file:
        pickle.dump(output, file)

    return output

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
        .all()
    )

    def get_data_from_pickle(id, session_id):
        with open(f'{local_path}\\{session_id}_{id}.pkl', 'rb') as file:
            loaded_data = pickle.load(file)
        return loaded_data

    return JSONResponse(content = {"messages": [
        {
            "sender": "user",
            "content": {"segments": [{"text": msg.content}]},
            "timestamp": str(msg.created_at),
        } 
        if msg.sender == "user"
        else 
        {
            "sender": "model",
            "content": get_data_from_pickle(msg.id, msg.session_id),
            "timestamp": str(msg.created_at),
        }
        for msg in messages
    ]})

@app.post("/chat/{session_id}/video")
async def generate_video(req: Request, session_id: str, current_user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    data = await req.json()
    prompt = data.get("prompt")

    chat_session = db.query(models.Chat_Session).filter(models.Chat_Session.session_id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    if chat_session.video_progress == "None":
        user_msg = models.Message(
            session_id=session_id,
            sender="user",
            content=prompt,
            created_at=datetime.now()
        )

        bot_msg = models.Message(
            session_id=session_id,
            sender="model",
            created_at=datetime.now()
        )
        db.add_all([user_msg, bot_msg])
        db.commit()

        path = f'artifacts\\{session_id}\\{session_id}_{bot_msg.id}.mp4'
        bot_msg.content = path
        chat_session.video_progress = "Progress"
        db.commit()
        asyncio.create_task(createVideo(db, prompt, path))
        # createVideo(db, prompt, path)
    return {"text": chat_session.video_text, "progress": chat_session.video_progress, "path": chat_session.video_path}

@app.get("/fix/{session_id}")
async def fix(req: Request, session_id: str, db: Session = Depends(get_db)):
    id = db.query(models.Chat_Session).filter(models.Chat_Session.session_id == session_id).first()
    id.video_progress = "None"
    db.commit()
    return {"message": "Fixed"}


# Angshuman Endpoints
@app.post("/normalize", response_model=TaskSpec)
def api_normalize(req: NormalizeRequest):
    try:
        data = normalize_task(req.chat, defaults=req.defaults or {})
        return TaskSpec(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/helpful-notes", response_model=HelpfulNotesResponse)
def api_helpful_notes(req: HelpfulNotesRequest):
    try:
        chunks = hybrid_search(
            queries=req.queries,
            k_mmr=req.mmr_k,
            lambda_mmr=req.lambda_mmr,
            k_final=req.kfinal,
            use_cross_encoder=req.use_cross_encoder
        )
        notes = summarize_to_notes(chunks, max_bullets=12, max_chars_per_bullet=220)
        return HelpfulNotesResponse(
            chunks=[ChunkPayload(**c) for c in chunks],
            notes=notes
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate", response_model=LessonDraft)
def api_generate(req: GenerateRequest):
    try:
        # sanitize inside generate_lesson already, but keep consistent
        lesson = generate_lesson(task_spec=req.task_spec.dict(), helpful_notes=req.helpful_notes, model=req.model)
        lesson = sanitize_lesson(lesson)
        return LessonDraft(**lesson)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _top_up_assets_with_llm(lesson: dict, task: TaskSpec, notes: list, model: str | None = None):
    # sanitize first so booleans become None and don’t break counters
    lesson = sanitize_lesson(lesson)
    segs = list(lesson.get("segments", []))

    count_merm = sum(1 for s in segs if isinstance(s.get("mermaid"), str) and s["mermaid"].strip())
    count_img  = sum(1 for s in segs if isinstance(s.get("image_prompt"), str) and s["image_prompt"].strip())

    target_merm = max(0, int(getattr(task, "min_diagrams", 2)))
    target_img  = max(0, int(getattr(task, "min_images", 2)))

    while count_merm < target_merm:
        m = gen_mermaid_snippet(task.model_dump(), notes, model=model)
        segs.append({
            "section": "Auto-added Diagram",
            "kind": "diagram",
            "text": "Diagram for the current topic.",
            "text_format": "md",
            "mermaid": m,
            "image_prompt": None,
            "alt_text": "Diagram explaining a key concept of the topic."
        })
        count_merm += 1

    while count_img < target_img:
        ip = gen_image_prompt(task.model_dump(), notes, model=model)
        segs.append({
            "section": "Auto-added Image",
            "kind": "image",
            "text": "Illustrative image to support understanding.",
            "text_format": "md",
            "mermaid": None,
            "image_prompt": ip,
            "alt_text": "Schematic image for the topic."
        })
        count_img += 1

    # sanitize again (just in case)
    lesson["segments"] = segs
    return sanitize_lesson(lesson)


# @app.post("/lesson", response_model=LessonDraft)
def api_full_lesson(chat: str, messages: list):
    """
    chat → TaskSpec → HelpfulNotes → LessonDraft (JSON only)
    Guarantees: ≥min_diagrams Mermaid + ≥min_images image prompts.
    """
    try:
        # 1) normalize (Gemini #1)
        ts = normalize_task(chat, defaults={"language": "en"})
        task = TaskSpec(**ts)

        # 2) helpful notes
        queries = [task.topic] if task.topic else []
        queries.extend(task.keywords[:5])
        if not queries:
            queries = [chat]
        chunks = hybrid_search(queries=queries, k_final=10, k_mmr=20, lambda_mmr=0.6)
        notes = summarize_to_notes(chunks, max_bullets=12, max_chars_per_bullet=220)

        # 3) lesson (Gemini #2)
        lesson = generate_lesson(messages, task_spec=task.model_dump(), helpful_notes=notes)

        # 4) ensure targets and sanitize
        lesson = _top_up_assets_with_llm(lesson, task, notes)

        return LessonDraft(**lesson)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @app.post("/lesson_rendered", response_model=LessonWithAssets)
def api_full_lesson_rendered(chat: str, messages: list):
    """
    chat → TaskSpec → HelpfulNotes → LessonDraft → render Mermaid + Images
    Images generated in parallel (max 5). Ensures ≥ min_diagrams & ≥ min_images.
    Repairs broken Mermaid once if needed.
    """
    # try:
        # 1) normalize
    ts = normalize_task(chat, defaults={"language": "en"})
    task = TaskSpec(**ts)

    # 2) helpful notes
    queries = [task.topic] if task.topic else []
    queries.extend(task.keywords[:5])
    if not queries:
        queries = [chat]
    chunks = hybrid_search(queries=queries, k_final=10, k_mmr=20, lambda_mmr=0.6)
    notes = summarize_to_notes(chunks, max_bullets=12, max_chars_per_bullet=220)

    # 3) lesson draft
    lesson = generate_lesson(messages, task_spec=task.model_dump(), helpful_notes=notes)
    lesson = _top_up_assets_with_llm(lesson, task, notes)

    # 4) render assets
    run_id = str(uuid4())[:8]
    out_root = os.path.join("artifacts", run_id)
    enriched = render_assets_for_lesson(lesson, out_root=out_root, image_concurrency=5)

    # 5) repair failed diagrams once
    for i, seg in enumerate(enriched.get("segments", [])):
        if isinstance(seg.get("mermaid"), str) and seg["mermaid"].strip():
            if not seg.get("diagram_path"):
                fixed = repair_mermaid(seg["mermaid"], error_log=None, topic=lesson.get("title"))
                if fixed and fixed.strip() != seg["mermaid"].strip():
                    seg["mermaid"] = fixed
                    ddir = os.path.join(out_root, "diagrams"); os.makedirs(ddir, exist_ok=True)
                    dpath = os.path.join(ddir, f"diagram_{i}.png")
                    ok = render_mermaid(fixed, dpath)
                    seg["diagram_path"] = dpath if ok else ""

    # 6) add public URLs
    # base = str(base_url).rstrip("/")
    base = "http://localhost:8000"
    for seg in enriched.get("segments", []):
        p = seg.get("diagram_path")
        if p:
            seg["diagram_url"] = f"{base}/{p.replace('\\', '/')}"
        ip = seg.get("image_path")
        if ip:
            seg["image_url"] = f"{base}/{ip.replace('\\', '/')}"

    segs_out = [EnrichedLessonSegment(**seg) for seg in enriched.get("segments", [])]
    return LessonWithAssets(
        title=enriched.get("title", ""),
        segments=segs_out,
        narration=enriched.get("narration"),
        artifacts_root=out_root
    )

    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Run the code
    uvicorn.run('main:app', reload=True)
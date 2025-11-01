from gemini_api import generate_image, generate_text
from auth import get_current_user, create_access_token, verify_access_token

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException, status
import uvicorn

from sqlalchemy.orm import Session
from db_setup import models, schemas, utils
from db_setup.db_setup import engine, get_db

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
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_pw = utils.hash_password(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    access_token = create_access_token(data={"user_id": new_user.id})
    return JSONResponse(content = {"username": new_user.username, "access_token": access_token, "token_type": "bearer"})

@app.post("/login", status_code=status.HTTP_200_OK)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not utils.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(data={"user_id": db_user.id})
    return JSONResponse(content = {"username": user.username, "access_token": access_token, "token_type": "bearer"})

@app.post("/forget-password", status_code=status.HTTP_200_OK)
def forget_password(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db_user.hashed_password = utils.hash_password(user.password)
    
    db.commit()
    db.refresh(db_user)
    return JSONResponse(content = {"message": "Password reset successful."})

@app.get("/profile", status_code=status.HTTP_200_OK)
def get_profile(
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(content = {"username": user.username})

@app.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    username: str,
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"detail": "User deleted successfully"}

@app.post("/gemini/gen_text", status_code=status.HTTP_200_OK)
async def process_data(request: Request):
     # Or check the latest supported name
    data = await request.json()
    prompt = data.get('prompt')

    return JSONResponse(content={"success": True, "message": generate_text(prompt)})

@app.post("/gemini/gen_image", status_code=status.HTTP_200_OK)
async def generate_image(request: Request):
    data = await request.json()
    prompt = data.get('prompt')

    return JSONResponse(content={"success": True, "message": generate_image(prompt)})


if __name__ == "__main__":
    # Run the code
    uvicorn.run('main:app', reload=True)
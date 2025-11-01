from google import genai
from google.genai import types
import os

# Get an environment variable
api_key = os.environ.get("API_KEY")

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Allow all domains
    allow_credentials=True,
    allow_methods=["*"],          # Allow all HTTP methods
    allow_headers=["*"],          # Allow all headers
)
client = None

def config_model():
    global client
    try:
        client = genai.Client(api_key='AIzaSyAdwfkU0G-dJeoHOByQYQfDT0B7d8JDdkU')
    except Exception as e:
        print(f"Error initializing client. Ensure GEMINI_API_KEY is set: {e}")
        exit()


def generate_text(prompt: str, model: str) -> str:
    result = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
        response_modalities=["TEXT"]
    ),
    )

    part = result.candidates[0].content.parts[0]
    print(part.text)
    return (part.text)

    

@app.post("/process")
async def process_data(request: Request):
    MODEL_NAME = 'gemini-2.0-flash-lite' # Or check the latest supported name
    data = await request.json()
    prompt = data.get('prompt')
    # "Create an text demonstarting bfs of graph"
    
    name = data.get("name", "Guest")
    message = f"Hello, {name}! Your data was received successfully."

    return JSONResponse(content={"success": True, "message": generate_text(prompt, MODEL_NAME)})

# Run the code
config_model()
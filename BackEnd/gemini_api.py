from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get an environment variable
api_key = os.environ.get("API_KEY")
client = None

TEXT_MODEL_2_lite = 'gemini-2.0-flash-lite'
TEXT_MODEL_25_lite = 'gemini-2.5-flash-lite'
TEXT_MODEL_2 = 'gemini-2.0-flash'
TEXT_MODEL_25 = 'gemini-2.5-flash'
IMAGE_MODEL_NAME = 'gemini-2.0-flash-preview-image-generation' # Or check the latest supported name
SYSTEM_PROMPT = """You are a helpful assistant named HackTutor, 
                    you are not made by other organization or team, and you are only known by this name.
                    Always help the user to the best of your abilities."""

def config_model():
    global client, chat_agent
    try:
        client = genai.Client(api_key='AIzaSyAdwfkU0G-dJeoHOByQYQfDT0B7d8JDdkU')
        
    except Exception as e:
        print(f"Error initializing client. Ensure GEMINI_API_KEY is set: {e}")
        exit()

def generate_text(prompt: str, model: str = TEXT_MODEL_2_lite) -> str:
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

def generate_image(prompt: str, model: str = IMAGE_MODEL_NAME) -> dict:
    result = client.models.generate_content(
        model=IMAGE_MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"]
        ),
    )
    part = result.candidates[0].content.parts
    return {"text": part[0].text, "image": part[1].inline_data.data}

def chat_with_model(prompt: str, messages: list, model: str = TEXT_MODEL_2_lite) -> str:
    
    history = [
        {"role": msg.sender, "parts": [types.Part(text=msg.content)]}
        for msg in messages
    ]

    chat_agent = client.chats.create(
        model=model,
        history=history,
        config={"system_instruction": SYSTEM_PROMPT}
    )
    response = chat_agent.send_message(prompt)
    
    return response.text

def get_evidence_pack(prompt: str) -> str:
    return prompt

# Initialize the model configuration
config_model()
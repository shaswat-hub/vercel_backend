from fastapi import FastAPI, APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel
from typing import List, Dict
import json
import asyncio
# from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Paths
ADS_FILE = Path(__file__).parent / "ads.json"

# Admin credentials
ADMIN_USERNAME = "shaswat369"
ADMIN_PASSWORD = "shaswat.millionaire"

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class ImageRequest(BaseModel):
    images: List[str]  # base64 encoded images

class AdminLogin(BaseModel):
    username: str
    password: str

class AdBlock(BaseModel):
    imageUrl: str
    linkUrl: str

class AdsUpdate(BaseModel):
    left1: AdBlock
    left2: AdBlock
    right1: AdBlock
    right2: AdBlock
    top: AdBlock
    bottom: AdBlock

# Helper function to call Gemini
async def analyze_with_gemini(images_base64: List[str], prompt: str) -> str:
    # Temporary dummy until Emergent integrations module available
    return f"Mock Gemini response for {len(images_base64)} images."
    try:
        api_key = os.getenv('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="API key not configured")
        
        # Create chat instance
        chat = LlmChat(
            api_key=api_key,
            session_id="topperbot-session",
            system_message="You are an expert educational assistant that helps students study better."
        ).with_model("gemini", "gemini-3-flash-preview")
        
        # Prepare image contents
        image_contents = [ImageContent(image_base64=img) for img in images_base64]
        
        # Create message with images and prompt
        user_message = UserMessage(
            text=prompt,
            file_contents=image_contents
        )
        
        # Get response
        response = await chat.send_message(user_message)
        return response
        
    except Exception as e:
        logging.error(f"Error in Gemini analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

# Routes
@api_router.get("/")
async def root():
    return {"message": "ExamBot API is running"}

@api_router.post("/generate/summary")
async def generate_summary(request: ImageRequest):
    if not request.images:
        raise HTTPException(status_code=400, detail="No images provided")
    
    prompt = """Analyze all the uploaded images carefully. These contain study material from a student.
    
Please provide a comprehensive, detailed summary of all the content shown in these images.
Include:
- Main topics and concepts covered
- Key points and important facts
- Definitions and formulas if any
- Any diagrams or visual information explained

Make the summary clear, organized, and helpful for exam preparation."""
    
    result = await analyze_with_gemini(request.images, prompt)
    return {"result": result}

@api_router.post("/generate/questions")
async def generate_questions(request: ImageRequest):
    if not request.images:
        raise HTTPException(status_code=400, detail="No images provided")
    
    prompt = """Analyze all the uploaded images carefully. These contain study material from a student.

Based on this content, create a comprehensive Question Paper with a total of 100 marks.

Format the question paper as follows:
- Divide questions into sections (Short Answer, Long Answer, etc.)
- Include a mix of question types
- Clearly mention marks for each question
- Questions should cover all important topics from the images
- Make questions exam-style and clear

Total marks must add up to exactly 100 marks."""
    
    result = await analyze_with_gemini(request.images, prompt)
    return {"result": result}

@api_router.post("/admin/login")
async def admin_login(credentials: AdminLogin):
    # debug prints - temporarily just to check input
    print("USERNAME RECEIVED:", repr(credentials.username))
    print("PASSWORD RECEIVED:", repr(credentials.password))
    print("EXPECTED:", repr(ADMIN_USERNAME), repr(ADMIN_PASSWORD))

    # compare after stripping extra spaces
    if credentials.username.strip() == ADMIN_USERNAME and credentials.password.strip() == ADMIN_PASSWORD:
        return {"success": True, "message": "Login successful"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

@api_router.get("/ads")
async def get_ads():
    try:
        if not ADS_FILE.exists():
            # Return default ads structure
            return {
                "left1": {"imageUrl": "", "linkUrl": ""},
                "left2": {"imageUrl": "", "linkUrl": ""},
                "right1": {"imageUrl": "", "linkUrl": ""},
                "right2": {"imageUrl": "", "linkUrl": ""},
                "top": {"imageUrl": "", "linkUrl": ""},
                "bottom": {"imageUrl": "", "linkUrl": ""}
            }
        
        with open(ADS_FILE, 'r') as f:
            ads_data = json.load(f)
        return ads_data
    except Exception as e:
        logging.error(f"Error reading ads: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load ads")

@api_router.post("/ads/update")
async def update_ads(ads: AdsUpdate):
    try:
        ads_dict = ads.model_dump()
        # skip actual file writing on Vercel (read‑only)
        print("ADS UPDATE:", ads_dict)  # debug print only
        return {"success": True, "message": "Received ads update (not saved on Vercel)"}
    except Exception as e:
        logging.error(f"Error updating ads: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update ads")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
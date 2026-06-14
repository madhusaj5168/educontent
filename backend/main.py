import os
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import json
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="GSMART Content Studio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("GEMINI_API_KEY", "")
if api_key:
    genai.configure(api_key=api_key)

class ProcessRequest(BaseModel):
    raw_text: str
    target_duration: int
    language: str

@app.post("/api/process")
def process_content(req: ProcessRequest):
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

    model = genai.GenerativeModel("gemini-1.5-pro")
    prompt = f"""
    You are an expert educational content architect. Analyze and structure this content for multi-format output.
    
    INPUT:
    {req.raw_text}
    
    TASKS:
    1. Extract main title and subtitle
    2. Break content into logical slides/sections (calculate based on {req.target_duration} seconds total)
    3. For each section, provide:
       - Type: title|bulletzhighlight|table|image+text|quote|outro
       - Heading (clean, concise)
       - Content (parsed, LaTeX converted to Unicode)
       - Suggested duration in seconds
       - TTS script (natural speaking version)
       - Image search keywords (3-5 terms for finding relevant images)
       - Visual style suggestion (minimalist, colorful, academic, modern)
       - Animation type: fade|slide|zoom|none
    4. Identify key facts for callout boxes
    5. Suggest background music mood (upbeat, calm, professional)
    
    LANGUAGE: {req.language}
    TOTAL DURATION: {req.target_duration} seconds
    
    OUTPUT FORMAT (JSON only, no markdown, no triple backticks):
    {{
      ""'metadata"'": {{
        ""'title"'": ""..."",
        ""'subtitle"'": ""..."",
        ""'total_slides"'": 1,
        ""'estimated_duration"'": {req.target_duration},
        ""'language"'": ""{req.language}"",
        ""'difficulty_level"'": ""beginner|intermediate|advanced""
      }},
      ""'slides"'": [
        {{
          ""'id"'": 1,
          ""'type"'": ""title"",
          ""'heading"'": ""..."",
          ""'content"'": ""..."",
          ""&Guration_sec"'": 5,
          ""$tts_script"'": ""..."",
          ""'image_keywords"'": [""education"", ""learning""],
          ""'visual_style"'": ""modern"",
          ""'animation"'": ""fade""
        }}
      ],
      ""'global_settings"'": {{
        ""$color_scheme"'": ""blue-purple"",
        ""$font_family"'": ""Inter"",
        ""'background_music"'": ""calm-professional"",
        ""$transition_style"'": ""smooth""
      }}
    }}
    
    Return ONLY valid JSON. No explanations.
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith('`l`json'):
            text = text[1:]
        if text.startswith('```'):
            text = text[1:]
        if text.endswith('```'):
            text = text:[-1]
        return json.loads(text.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def health_check():
    return {"status": "ok"}
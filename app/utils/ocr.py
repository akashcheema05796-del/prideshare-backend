import os
import io
import json
from PIL import Image
import PyPDF2
import google.generativeai as genai
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

GEMINI_PROMPT = """
You are analyzing a student's class schedule from Purdue Northwest.

Extract ALL classes from this schedule and return them as a JSON array.

For each class, extract:
- course_code: The course code (e.g., "CS 240", "MATH 261")
- course_name: The full course name (optional)
- building_id: The building code or name where the class is held
- days: Array of days (use full lowercase: ["monday", "wednesday", "friday"])
- start_time: Start time in HH:MM 24-hour format (e.g., "10:30")
- end_time: End time in HH:MM 24-hour format (e.g., "11:20")

Common PNW building codes:
- NILS = Nils K. Nelson Bioscience Innovation Building
- CLH = Christopher Library
- GYTE = Gyte Hall
- SWCE = Schwarz College of Engineering
- PWR / Powers = Powers Hall
- LWSH / Lawshe = Lawshe Hall
- PTR / Potter = Potter Hall

IMPORTANT RULES:
1. Convert all building names to their ID codes (e.g., "Gyte Hall" → "gyte")
2. Convert all times to 24-hour format
3. Convert day abbreviations to full lowercase (M→monday, T→tuesday, W→wednesday, Th→thursday, F→friday)
4. If a class meets multiple days, include all days in the array
5. Return ONLY valid JSON, no markdown, no explanations

Example output format:
[
  {
    "course_code": "CS 240",
    "course_name": "Data Structures",
    "building_id": "nils",
    "days": ["monday", "wednesday"],
    "start_time": "10:30",
    "end_time": "11:20"
  }
]

Now analyze the schedule image and return the JSON:
"""

async def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from PDF file"""
    try:
        pdf_bytes = await pdf_file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text
    except Exception as e:
        raise Exception(f"PDF extraction failed: {str(e)}")

async def extract_text_from_image(image_file) -> Image:
    """Load image from file"""
    try:
        image_bytes = await image_file.read()
        image = Image.open(io.BytesIO(image_bytes))
        return image
    except Exception as e:
        raise Exception(f"Image loading failed: {str(e)}")

async def process_schedule_with_gemini(content, content_type: str) -> Dict:
    """
    Process schedule using Google Gemini
    content_type: 'text' or 'image'
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        if content_type == 'text':
            # Process text (from PDF)
            prompt = GEMINI_PROMPT + f"\n\nSchedule Text:\n{content}"
            response = model.generate_content(prompt)
        else:
            # Process image
            response = model.generate_content([GEMINI_PROMPT, content])
        
        # Extract JSON from response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Parse JSON
        schedules = json.loads(response_text)
        
        # Validate it's a list
        if not isinstance(schedules, list):
            raise ValueError("Response is not a list of schedules")
        
        return {
            "success": True,
            "schedules": schedules,
            "raw_text": response.text
        }
    
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": "Failed to parse schedule data",
            "details": f"JSON error: {str(e)}",
            "raw_text": response.text if 'response' in locals() else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": "OCR processing failed",
            "details": str(e)
        }

async def process_schedule_file(file) -> Dict:
    """
    Main function to process uploaded schedule file
    Handles both PDF and image formats
    """
    try:
        # Get file extension
        filename = file.filename.lower()
        
        if filename.endswith('.pdf'):
            # Extract text from PDF
            text = await extract_text_from_pdf(file)
            result = await process_schedule_with_gemini(text, 'text')
        
        elif filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            # Process image
            image = await extract_text_from_image(file)
            result = await process_schedule_with_gemini(image, 'image')
        
        else:
            return {
                "success": False,
                "error": "Unsupported file format",
                "details": "Please upload a PDF or image file (PNG, JPG, JPEG, GIF, BMP)"
            }
        
        return result
    
    except Exception as e:
        return {
            "success": False,
            "error": "File processing failed",
            "details": str(e)
        }

# Building ID normalization helper
BUILDING_MAPPING = {
    "nils k. nelson bioscience innovation building": "nils",
    "nils": "nils",
    "nknbib": "nils",
    "bioscience": "nils",
    "christopher library": "clh",
    "clh": "clh",
    "library": "clh",
    "gyte hall": "gyte",
    "gyte": "gyte",
    "schwarz college of engineering": "swce",
    "swce": "swce",
    "engineering": "swce",
    "powers hall": "powers",
    "powers": "powers",
    "pwr": "powers",
    "lawshe hall": "lawshe",
    "lawshe": "lawshe",
    "lwsh": "lawshe",
    "potter hall": "potter",
    "potter": "potter",
    "ptr": "potter",
    "student union": "student_union",
    "union": "student_union",
    "sul": "student_union",
}

def normalize_building_id(building_name: str) -> str:
    """Normalize building name to ID"""
    building_lower = building_name.lower().strip()
    return BUILDING_MAPPING.get(building_lower, building_lower)

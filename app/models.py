from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
from datetime import time, date

# ============================================
# USER MODELS
# ============================================

class UserSignup(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    home_zip: str
    role: str = "both"  # driver, rider, both
    
    @validator('email')
    def validate_pnw_email(cls, v):
        if not v.endswith('@pnw.edu'):
            raise ValueError('Must use a @pnw.edu email address')
        return v
    
    @validator('home_zip')
    def validate_zip(cls, v):
        if not v or len(v) != 5 or not v.isdigit():
            raise ValueError('ZIP code must be 5 digits')
        return v
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['driver', 'rider', 'both']:
            raise ValueError('Role must be driver, rider, or both')
        return v

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: Optional[str]
    home_zip: str
    role: str
    verified: bool
    trust_score: int
    total_rides: int
    created_at: str

# ============================================
# SCHEDULE MODELS
# ============================================

class ScheduleCreate(BaseModel):
    course_code: str
    course_name: Optional[str] = None
    building_id: str
    days: List[str]  # ["monday", "wednesday", "friday"]
    start_time: str  # "10:30"
    end_time: str    # "11:20"
    
    @validator('days')
    def validate_days(cls, v):
        valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        for day in v:
            if day.lower() not in valid_days:
                raise ValueError(f'Invalid day: {day}. Must be one of {valid_days}')
        return [day.lower() for day in v]
    
    @validator('start_time', 'end_time')
    def validate_time(cls, v):
        try:
            # Parse time in HH:MM format
            parts = v.split(':')
            if len(parts) != 2:
                raise ValueError
            hour, minute = int(parts[0]), int(parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
        except:
            raise ValueError('Time must be in HH:MM format (e.g., 10:30)')
        return v

class ScheduleResponse(BaseModel):
    id: str
    user_id: str
    course_code: str
    course_name: Optional[str]
    building_id: str
    building_name: Optional[str]
    days: List[str]
    start_time: str
    end_time: str
    semester: str
    active: bool

class BulkScheduleCreate(BaseModel):
    schedules: List[ScheduleCreate]

# ============================================
# OCR MODELS
# ============================================

class OCRScheduleResponse(BaseModel):
    success: bool
    schedules: List[ScheduleCreate]
    raw_text: Optional[str] = None
    error: Optional[str] = None

# ============================================
# BUILDING MODELS
# ============================================

class BuildingResponse(BaseModel):
    id: str
    name: str
    campus: str
    address: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    common_names: List[str]

# ============================================
# AUTH MODELS
# ============================================

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class MagicLinkRequest(BaseModel):
    email: EmailStr
    
    @validator('email')
    def validate_pnw_email(cls, v):
        if not v.endswith('@pnw.edu'):
            raise ValueError('Must use a @pnw.edu email address')
        return v

# ============================================
# RESPONSE MODELS
# ============================================

class SuccessResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None

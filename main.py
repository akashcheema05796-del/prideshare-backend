from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
from dotenv import load_dotenv

from app.models import (
    UserSignup, UserResponse, ScheduleCreate, ScheduleResponse,
    BuildingResponse, SuccessResponse, ErrorResponse,
    BulkScheduleCreate, OCRScheduleResponse, MagicLinkRequest
)
from app.database import supabase, init_buildings, PNW_BUILDINGS
from app.utils.ocr import process_schedule_file, normalize_building_id

load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="Pride Share API - Purdue Northwest",
    description="Carpool matching platform for PNW students",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        os.getenv("FRONTEND_URL", "http://localhost:3000")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# STARTUP EVENT
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize database with buildings data"""
    await init_buildings()
    print("🚀 Pride Share API started successfully")

# ============================================
# HEALTH CHECK
# ============================================

@app.get("/")
async def root():
    return {
        "message": "Pride Share API - Purdue Northwest",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Check if API and database are working"""
    try:
        # Test database connection
        result = supabase.table("buildings").select("count").execute()
        return {
            "status": "healthy",
            "database": "connected",
            "buildings_loaded": len(result.data) if result.data else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# ============================================
# AUTHENTICATION & USER MANAGEMENT
# ============================================

@app.post("/auth/signup", response_model=SuccessResponse)
async def signup_user(user: UserSignup):
    """Register a new user with @pnw.edu email"""
    try:
        # Check if user exists
        existing = supabase.table("users").select("*").eq("email", user.email).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        result = supabase.table("users").insert({
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "home_zip": user.home_zip,
            "role": user.role,
            "verified": False,
            "trust_score": 50,
            "total_rides": 0
        }).execute()
        
        user_id = result.data[0]["id"]
        
        return SuccessResponse(
            success=True,
            message="Account created successfully! Please check your email to verify.",
            data={"user_id": user_id, "email": user.email}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")

@app.post("/auth/magic-link", response_model=SuccessResponse)
async def send_magic_link(request: MagicLinkRequest):
    """Send magic link for passwordless login"""
    try:
        # Use Supabase Auth to send magic link
        response = supabase.auth.sign_in_with_otp({
            "email": request.email,
            "options": {
                "email_redirect_to": f"{os.getenv('FRONTEND_URL')}/dashboard"
            }
        })
        
        return SuccessResponse(
            success=True,
            message=f"Magic link sent to {request.email}. Check your inbox!",
            data={"email": request.email}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send magic link: {str(e)}")

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get user profile by ID"""
    try:
        result = supabase.table("users").select("*").eq("id", user_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(**result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/users/{user_id}", response_model=SuccessResponse)
async def update_user(user_id: str, updates: dict):
    """Update user profile"""
    try:
        # Validate user exists
        user = supabase.table("users").select("id").eq("id", user_id).execute()
        if not user.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update user
        result = supabase.table("users").update(updates).eq("id", user_id).execute()
        
        return SuccessResponse(
            success=True,
            message="Profile updated successfully",
            data=result.data[0]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# BUILDINGS
# ============================================

@app.get("/buildings", response_model=List[BuildingResponse])
async def get_buildings(campus: Optional[str] = None):
    """Get all buildings, optionally filtered by campus"""
    try:
        query = supabase.table("buildings").select("*")
        if campus:
            query = query.eq("campus", campus)
        result = query.execute()
        return [BuildingResponse(**building) for building in result.data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/buildings/{building_id}", response_model=BuildingResponse)
async def get_building(building_id: str):
    """Get specific building details"""
    try:
        result = supabase.table("buildings").select("*").eq("id", building_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Building not found")
        return BuildingResponse(**result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# SCHEDULE MANAGEMENT
# ============================================

@app.post("/schedules/{user_id}", response_model=SuccessResponse)
async def add_class(user_id: str, schedule: ScheduleCreate):
    """Add a single class to user's schedule"""
    try:
        # Verify user exists
        user = supabase.table("users").select("id").eq("id", user_id).execute()
        if not user.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify building exists
        building = supabase.table("buildings").select("id").eq("id", schedule.building_id).execute()
        if not building.data:
            raise HTTPException(status_code=404, detail=f"Building '{schedule.building_id}' not found")
        
        # Insert schedule
        result = supabase.table("schedules").insert({
            "user_id": user_id,
            "course_code": schedule.course_code,
            "course_name": schedule.course_name,
            "building_id": schedule.building_id,
            "days": schedule.days,
            "start_time": schedule.start_time,
            "end_time": schedule.end_time,
            "semester": "spring_2025",
            "active": True
        }).execute()
        
        return SuccessResponse(
            success=True,
            message="Class added successfully",
            data={"schedule_id": result.data[0]["id"]}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add class: {str(e)}")

@app.post("/schedules/{user_id}/bulk", response_model=SuccessResponse)
async def add_bulk_classes(user_id: str, bulk: BulkScheduleCreate):
    """Add multiple classes at once"""
    try:
        # Verify user exists
        user = supabase.table("users").select("id").eq("id", user_id).execute()
        if not user.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prepare all schedules
        schedules_to_insert = []
        for schedule in bulk.schedules:
            # Normalize building ID
            normalized_building_id = normalize_building_id(schedule.building_id)
            
            schedules_to_insert.append({
                "user_id": user_id,
                "course_code": schedule.course_code,
                "course_name": schedule.course_name,
                "building_id": normalized_building_id,
                "days": schedule.days,
                "start_time": schedule.start_time,
                "end_time": schedule.end_time,
                "semester": "spring_2025",
                "active": True
            })
        
        # Insert all schedules
        result = supabase.table("schedules").insert(schedules_to_insert).execute()
        
        return SuccessResponse(
            success=True,
            message=f"Successfully added {len(result.data)} classes",
            data={"count": len(result.data), "schedules": result.data}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk insert failed: {str(e)}")

@app.get("/schedules/{user_id}", response_model=List[ScheduleResponse])
async def get_schedule(user_id: str):
    """Get user's full schedule with building details"""
    try:
        result = supabase.table("schedules").select(
            "*, buildings(name)"
        ).eq("user_id", user_id).eq("active", True).execute()
        
        # Format response
        schedules = []
        for item in result.data:
            building_name = item.pop("buildings")["name"] if "buildings" in item else None
            schedules.append(ScheduleResponse(
                **item,
                building_name=building_name
            ))
        
        return schedules
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/schedules/{schedule_id}", response_model=SuccessResponse)
async def delete_class(schedule_id: str):
    """Remove a class from schedule"""
    try:
        result = supabase.table("schedules").delete().eq("id", schedule_id).execute()
        return SuccessResponse(
            success=True,
            message="Class removed successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# OCR SCHEDULE UPLOAD
# ============================================

@app.post("/schedules/{user_id}/upload", response_model=OCRScheduleResponse)
async def upload_schedule(user_id: str, file: UploadFile = File(...)):
    """
    Upload schedule as PDF or image
    Uses Google Gemini to extract classes
    """
    try:
        # Verify user exists
        user = supabase.table("users").select("id").eq("id", user_id).execute()
        if not user.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Process file with OCR
        result = await process_schedule_file(file)
        
        if not result["success"]:
            return OCRScheduleResponse(
                success=False,
                schedules=[],
                error=result.get("error", "OCR processing failed"),
                raw_text=result.get("raw_text")
            )
        
        # Convert to ScheduleCreate objects
        schedules = []
        for schedule_data in result["schedules"]:
            # Normalize building ID
            schedule_data["building_id"] = normalize_building_id(schedule_data["building_id"])
            schedules.append(ScheduleCreate(**schedule_data))
        
        return OCRScheduleResponse(
            success=True,
            schedules=schedules,
            raw_text=result.get("raw_text")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

# ============================================
# MATCHING (Basic for now)
# ============================================

@app.get("/matches/{user_id}")
async def find_matches(user_id: str):
    """
    Find potential carpool matches
    Returns students with overlapping schedules and nearby ZIP codes
    """
    try:
        # Get user data
        user = supabase.table("users").select("*").eq("id", user_id).execute()
        if not user.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user.data[0]
        user_zip = user_data.get("home_zip", "")
        
        # Get user's schedule
        user_schedule = supabase.table("schedules").select("*").eq("user_id", user_id).eq("active", True).execute()
        
        if not user_schedule.data:
            return {
                "total_matches": 0,
                "matches": [],
                "message": "Add your schedule first to find matches"
            }
        
        matches = []
        seen_users = set()
        
        for user_class in user_schedule.data:
            # Find students in same building with overlapping days
            potential_matches = supabase.table("schedules").select(
                "*, users!inner(id, full_name, home_zip, role, trust_score, total_rides)"
            ).eq("building_id", user_class["building_id"]).eq("active", True).neq("user_id", user_id).execute()
            
            for match in potential_matches.data:
                match_user_id = match["users"]["id"]
                
                # Skip if already seen
                if match_user_id in seen_users:
                    continue
                
                # Check day overlap
                common_days = set(user_class["days"]) & set(match["days"])
                if not common_days:
                    continue
                
                # Check ZIP proximity (first 3 digits)
                match_zip = match["users"]["home_zip"]
                if user_zip[:3] != match_zip[:3]:
                    continue
                
                # Calculate match score
                match_score = 0
                if user_class["course_code"] == match["course_code"]:
                    match_score += 50  # Same class
                    match_type = "same_class"
                else:
                    match_score += 30  # Same building
                    match_type = "same_building"
                
                match_score += len(common_days) * 5
                match_score += match["users"]["trust_score"] / 10
                
                matches.append({
                    "user_id": match_user_id,
                    "name": match["users"]["full_name"],
                    "role": match["users"]["role"],
                    "trust_score": match["users"]["trust_score"],
                    "total_rides": match["users"]["total_rides"],
                    "course_code": match["course_code"],
                    "building_id": match["building_id"],
                    "common_days": list(common_days),
                    "start_time": match["start_time"],
                    "match_type": match_type,
                    "match_score": round(match_score, 2)
                })
                
                seen_users.add(match_user_id)
        
        # Sort by match score
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        
        return {
            "total_matches": len(matches),
            "matches": matches[:20]  # Return top 20
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

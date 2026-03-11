import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Supabase client initialization
supabase_url: str = os.getenv("SUPABASE_URL")
supabase_key: str = os.getenv("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("Supabase credentials not found in environment variables")

supabase: Client = create_client(supabase_url, supabase_key)

# PNW Buildings Data (Hammond Campus)
PNW_BUILDINGS = [
    {
        "id": "nils",
        "name": "Nils K. Nelson Bioscience Innovation Building",
        "campus": "hammond",
        "address": "2200 169th St, Hammond, IN 46323",
        "latitude": 41.6394,
        "longitude": -87.3192,
        "common_names": ["NILS", "Bioscience", "Nelson", "NKNBIB"]
    },
    {
        "id": "clh",
        "name": "Christopher Library",
        "campus": "hammond",
        "address": "2200 169th St, Hammond, IN 46323",
        "latitude": 41.6401,
        "longitude": -87.3185,
        "common_names": ["CLH", "Library", "Christopher Library"]
    },
    {
        "id": "gyte",
        "name": "Gyte Hall",
        "campus": "hammond",
        "address": "2200 169th St, Hammond, IN 46323",
        "latitude": 41.6398,
        "longitude": -87.3195,
        "common_names": ["Gyte", "GYTE"]
    },
    {
        "id": "swce",
        "name": "Schwarz College of Engineering",
        "campus": "hammond",
        "address": "2200 169th St, Hammond, IN 46323",
        "latitude": 41.6390,
        "longitude": -87.3188,
        "common_names": ["SWCE", "Engineering", "Schwarz"]
    },
    {
        "id": "powers",
        "name": "Powers Hall",
        "campus": "hammond",
        "address": "2200 169th St, Hammond, IN 46323",
        "latitude": 41.6405,
        "longitude": -87.3180,
        "common_names": ["Powers", "PWR"]
    },
    {
        "id": "lawshe",
        "name": "Lawshe Hall",
        "campus": "hammond",
        "address": "2200 169th St, Hammond, IN 46323",
        "latitude": 41.6403,
        "longitude": -87.3175,
        "common_names": ["Lawshe", "LWSH"]
    },
    {
        "id": "potter",
        "name": "Potter Hall",
        "campus": "hammond",
        "address": "2200 169th St, Hammond, IN 46323",
        "latitude": 41.6396,
        "longitude": -87.3178,
        "common_names": ["Potter", "PTR"]
    },
    {
        "id": "student_union",
        "name": "Student Union & Library",
        "campus": "hammond",
        "address": "2200 169th St, Hammond, IN 46323",
        "latitude": 41.6400,
        "longitude": -87.3182,
        "common_names": ["Student Union", "SUL", "Union"]
    }
]

async def init_buildings():
    """Initialize buildings table with PNW data"""
    try:
        # Check if buildings already exist
        result = supabase.table("buildings").select("id").execute()
        
        if not result.data:
            # Insert buildings
            supabase.table("buildings").insert(PNW_BUILDINGS).execute()
            print("✅ Buildings data loaded successfully")
        else:
            print("ℹ️ Buildings already exist in database")
    except Exception as e:
        print(f"❌ Error loading buildings: {e}")

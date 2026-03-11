# 🚗 Pride Share - Purdue Northwest Carpool Network

**Find classmates heading to campus from your neighborhood. Save money. Reduce emissions. Make friends.**

Pride Share is a smart carpool matching platform built specifically for Purdue Northwest students. Using AI-powered schedule extraction and intelligent matching algorithms, we connect students with similar routes and class times.

---

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)
- [QR Code Integration](#qr-code-integration)
- [Contributing](#contributing)

---

## ✨ Features

### For Students
- **🎓 PNW Verified**: Secure signup with @pnw.edu email only
- **📅 Smart Schedule Import**: Upload PDF/image or enter manually
- **🤖 AI-Powered OCR**: Google Gemini extracts classes automatically
- **🎯 Intelligent Matching**: Find carpoolers with same classes and routes
- **💰 Cost Savings**: Track money saved on gas and parking
- **🌱 Environmental Impact**: Monitor CO₂ emissions reduced
- **⭐ Trust System**: Rating and verification badges
- **💬 In-App Chat**: Coordinate rides seamlessly

### For Presentation
- **QR Code Ready**: Direct link to signup page
- **Real-time Analytics**: Track signups and usage
- **Mobile Responsive**: Works on all devices
- **Professional UI**: PNW-branded colors (Gold & Black)

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL)
- **AI/OCR**: Google Gemini 1.5 Flash
- **Auth**: Supabase Auth (Magic Links)
- **File Processing**: PyPDF2, Pillow

### Frontend
- **Framework**: Next.js 14 (React)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **Deployment**: Vercel

### Infrastructure
- **Backend Hosting**: Railway / Render
- **Frontend Hosting**: Vercel
- **Database**: Supabase Cloud
- **Storage**: Supabase Storage

---

## 📁 Project Structure

```
prideshare/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── models.py            # Pydantic models
│   │   ├── database.py          # Supabase client & PNW buildings
│   │   └── utils/
│   │       └── ocr.py           # Gemini OCR processing
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.js          # Landing page
│   │   │   ├── signup/
│   │   │   │   └── page.js      # Signup flow
│   │   │   └── layout.js
│   │   └── lib/
│   │       └── api.js           # API client
│   ├── package.json
│   └── .env.local.example
│
└── README.md
```

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- Supabase account
- Google Cloud account (for Gemini API)

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/prideshare.git
cd prideshare
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your credentials:
# - SUPABASE_URL
# - SUPABASE_SERVICE_KEY
# - GEMINI_API_KEY
```

**Create Supabase Tables:**

Go to Supabase Dashboard → SQL Editor and run:

```sql
-- See backend/database_schema.sql for full schema
-- (The schema is automatically applied in main.py on startup)
```

**Run Backend:**

```bash
python -m app.main
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local
cp .env.local.example .env.local
# Edit .env.local with:
# - NEXT_PUBLIC_API_URL=http://localhost:8000
# - NEXT_PUBLIC_SUPABASE_URL
# - NEXT_PUBLIC_SUPABASE_ANON_KEY

# Run development server
npm run dev
# App available at http://localhost:3000
```

---

## 🌐 Deployment

### Backend (Railway)

1. Create Railway account
2. New Project → Deploy from GitHub
3. Select `prideshare-backend` folder
4. Add environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - `GEMINI_API_KEY`
   - `FRONTEND_URL` (your Vercel URL)
5. Deploy automatically

### Frontend (Vercel)

1. Push code to GitHub
2. Import project to Vercel
3. Set root directory to `frontend/`
4. Add environment variables:
   - `NEXT_PUBLIC_API_URL` (your Railway URL)
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
5. Deploy

---

## 📡 API Documentation

### Base URL
```
Production: https://prideshare-api.up.railway.app
Local: http://localhost:8000
```

### Endpoints

#### Authentication
```http
POST /auth/signup
Content-Type: application/json

{
  "email": "student@pnw.edu",
  "full_name": "John Doe",
  "phone": "555-123-4567",
  "home_zip": "46323",
  "role": "both"
}

Response:
{
  "success": true,
  "message": "Account created successfully!",
  "data": {
    "user_id": "uuid-here",
    "email": "student@pnw.edu"
  }
}
```

#### Schedule Upload (OCR)
```http
POST /schedules/{user_id}/upload
Content-Type: multipart/form-data

file: <PDF or image file>

Response:
{
  "success": true,
  "schedules": [
    {
      "course_code": "CS 240",
      "building_id": "nils",
      "days": ["monday", "wednesday"],
      "start_time": "10:30",
      "end_time": "11:20"
    }
  ]
}
```

#### Manual Schedule Entry
```http
POST /schedules/{user_id}
Content-Type: application/json

{
  "course_code": "CS 240",
  "course_name": "Data Structures",
  "building_id": "nils",
  "days": ["monday", "wednesday", "friday"],
  "start_time": "10:30",
  "end_time": "11:20"
}
```

#### Find Matches
```http
GET /matches/{user_id}

Response:
{
  "total_matches": 8,
  "matches": [
    {
      "user_id": "uuid",
      "name": "Sarah Johnson",
      "role": "driver",
      "course_code": "CS 240",
      "building_id": "nils",
      "common_days": ["monday", "wednesday"],
      "match_type": "same_class",
      "match_score": 72.5
    }
  ]
}
```

**Full API Docs**: Visit `/docs` when backend is running (Swagger UI)

---

## 📱 QR Code Integration

### For Your Presentation

1. **Generate QR Code** pointing to your signup page:
   ```
   https://prideshare.vercel.app/signup
   ```

2. **Use these tools**:
   - [QR Code Generator](https://www.qr-code-generator.com/)
   - [QRCode Monkey](https://www.qrcode-monkey.com/)

3. **Customization**:
   - Add PNW logo in center
   - Use PNW colors (Gold #CFB87C, Black #000000)
   - Include text: "Scan to Join Pride Share"

4. **Print Sizes**:
   - Flyers: 2" x 2" QR code
   - Posters: 4" x 4" QR code
   - Presentation slides: High resolution PNG

### Testing Your QR Code

```bash
# Start your deployed frontend
# Generate QR code with URL
# Test with phone camera
# Verify it opens signup page
```

---

## 📊 PNW Buildings Database

The app comes pre-loaded with Hammond campus buildings:

```javascript
[
  {
    id: "nils",
    name: "Nils K. Nelson Bioscience Innovation Building",
    campus: "hammond",
    latitude: 41.6394,
    longitude: -87.3192
  },
  {
    id: "clh",
    name: "Christopher Library",
    campus: "hammond",
    latitude: 41.6401,
    longitude: -87.3185
  },
  // ... 8 total buildings
]
```

**To add more buildings**: Edit `backend/app/database.py`

---

## 🎨 Branding Guidelines

### Colors
- **Primary Gold**: `#CFB87C` (PNW official)
- **Primary Black**: `#000000` (PNW official)
- **Accent**: `#ef4444` (Red for CTAs)

### Typography
- **Headings**: Bold, 2xl-6xl
- **Body**: Regular, sm-lg
- **Buttons**: Semibold/Bold

### Voice
- Friendly but professional
- Student-focused
- Action-oriented
- Safety-conscious

---

## 🧪 Testing Checklist

### Before Presentation

- [ ] Backend deployed and accessible
- [ ] Frontend deployed and accessible
- [ ] QR code generated and tested
- [ ] Test signup flow (happy path)
- [ ] Test PDF upload with sample schedule
- [ ] Test manual entry
- [ ] Verify buildings dropdown works
- [ ] Check mobile responsiveness
- [ ] Test on multiple devices
- [ ] Prepare demo account credentials
- [ ] Screenshot key features
- [ ] Have backup slides ready

### Demo Script

1. **Show QR Code**: "Students scan this to join"
2. **Signup**: Fill form with test @pnw.edu email
3. **Upload Schedule**: Demo OCR extraction
4. **View Matches**: Show intelligent matching
5. **Show Stats**: Money saved, CO₂ reduced
6. **Mobile View**: Responsive design

---

## 📈 Analytics & Metrics

Track these for your presentation:

```sql
-- Total signups
SELECT COUNT(*) FROM users;

-- Active users (added schedule)
SELECT COUNT(DISTINCT user_id) FROM schedules;

-- Top buildings
SELECT building_id, COUNT(*) 
FROM schedules 
GROUP BY building_id 
ORDER BY COUNT(*) DESC;

-- Popular commute routes
SELECT home_zip, COUNT(*) 
FROM users 
GROUP BY home_zip 
ORDER BY COUNT(*) DESC;
```

---

## 🤝 Contributing

This is a student project for Purdue Northwest. For questions or contributions:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📄 License

MIT License - Built by PNW students, for PNW students

---

## 🆘 Support

**Having issues?**

1. Check `/docs` for API reference
2. Review browser console for errors
3. Verify environment variables are set
4. Check Supabase connection
5. Contact: [your-email@pnw.edu]

---

## 🎓 For Your Presentation

### Key Talking Points

1. **Problem**: PNW students waste money on gas/parking driving alone
2. **Solution**: AI-powered carpool matching using class schedules
3. **Innovation**: OCR schedule extraction (not just manual entry)
4. **Scale**: Can expand to other universities
5. **Impact**: Environmental + Financial + Social benefits

### Demo Flow (3 minutes)

1. Show QR code (10s)
2. Signup process (45s)
3. Upload schedule / OCR extraction (60s)
4. View matches (30s)
5. Show analytics dashboard (35s)

### Backup Plan

If demo fails:
- Have pre-recorded video
- Show screenshots
- Walk through code architecture
- Explain technical decisions

---

**Good luck with your presentation! 🚀**

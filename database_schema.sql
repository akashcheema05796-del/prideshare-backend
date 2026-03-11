-- Pride Share Database Schema
-- Run this in Supabase SQL Editor

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- ============================================
-- BUILDINGS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS buildings (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  campus TEXT NOT NULL CHECK (campus IN ('hammond', 'westville')),
  address TEXT,
  latitude DECIMAL(10, 8),
  longitude DECIMAL(11, 8),
  common_names TEXT[],
  created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- USERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  phone TEXT,
  home_address TEXT,
  home_zip TEXT,
  home_lat DECIMAL(10, 8),
  home_lng DECIMAL(11, 8),
  role TEXT DEFAULT 'both' CHECK (role IN ('driver', 'rider', 'both')),
  bio TEXT,
  profile_photo_url TEXT,
  verified BOOLEAN DEFAULT FALSE,
  trust_score INTEGER DEFAULT 50,
  total_rides INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  last_active TIMESTAMP
);

-- ============================================
-- SCHEDULES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS schedules (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  course_code TEXT NOT NULL,
  course_name TEXT,
  building_id TEXT REFERENCES buildings(id),
  days TEXT[] NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  semester TEXT DEFAULT 'spring_2025',
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- RIDE REQUESTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS ride_requests (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  requester_id UUID REFERENCES users(id),
  provider_id UUID REFERENCES users(id),
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'completed', 'cancelled')),
  ride_date DATE NOT NULL,
  pickup_location TEXT,
  notes TEXT,
  rating INTEGER CHECK (rating BETWEEN 1 AND 5),
  review TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- MESSAGES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id TEXT NOT NULL,
  sender_id UUID REFERENCES users(id),
  recipient_id UUID REFERENCES users(id),
  content TEXT NOT NULL,
  read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- ACTIVITY LOG TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS activity_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id),
  action TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Schedules indexes
CREATE INDEX IF NOT EXISTS idx_schedules_user ON schedules(user_id);
CREATE INDEX IF NOT EXISTS idx_schedules_building ON schedules(building_id);
CREATE INDEX IF NOT EXISTS idx_schedules_days ON schedules USING GIN(days);
CREATE INDEX IF NOT EXISTS idx_schedules_time ON schedules(start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_schedules_active ON schedules(active);

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_zip ON users(home_zip);
CREATE INDEX IF NOT EXISTS idx_users_verified ON users(verified);

-- Ride requests indexes
CREATE INDEX IF NOT EXISTS idx_ride_requests_provider ON ride_requests(provider_id, status);
CREATE INDEX IF NOT EXISTS idx_ride_requests_requester ON ride_requests(requester_id, status);
CREATE INDEX IF NOT EXISTS idx_ride_requests_date ON ride_requests(ride_date);

-- Messages indexes
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_messages_recipient ON messages(recipient_id, read);

-- Activity log index
CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_log(user_id, created_at);

-- ============================================
-- ROW LEVEL SECURITY (Optional - for production)
-- ============================================

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE ride_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Users can read all user profiles but only update their own
CREATE POLICY "Users can view all profiles" ON users FOR SELECT USING (true);
CREATE POLICY "Users can update own profile" ON users FOR UPDATE USING (auth.uid() = id);

-- Users can manage their own schedules
CREATE POLICY "Users can view all schedules" ON schedules FOR SELECT USING (true);
CREATE POLICY "Users can manage own schedules" ON schedules FOR ALL USING (auth.uid() = user_id);

-- Ride request policies
CREATE POLICY "Users can view their ride requests" ON ride_requests 
  FOR SELECT USING (auth.uid() = requester_id OR auth.uid() = provider_id);
CREATE POLICY "Users can create ride requests" ON ride_requests 
  FOR INSERT WITH CHECK (auth.uid() = requester_id);
CREATE POLICY "Users can update their ride requests" ON ride_requests 
  FOR UPDATE USING (auth.uid() = requester_id OR auth.uid() = provider_id);

-- Message policies
CREATE POLICY "Users can view their messages" ON messages 
  FOR SELECT USING (auth.uid() = sender_id OR auth.uid() = recipient_id);
CREATE POLICY "Users can send messages" ON messages 
  FOR INSERT WITH CHECK (auth.uid() = sender_id);

-- ============================================
-- USEFUL VIEWS
-- ============================================

-- Active carpoolers view
CREATE OR REPLACE VIEW active_carpoolers AS
SELECT 
  u.id,
  u.full_name,
  u.email,
  u.home_zip,
  u.role,
  u.trust_score,
  u.total_rides,
  COUNT(DISTINCT s.id) as class_count,
  array_agg(DISTINCT s.building_id) as buildings
FROM users u
LEFT JOIN schedules s ON s.user_id = u.id AND s.active = true
WHERE u.verified = true
GROUP BY u.id;

-- Popular routes view
CREATE OR REPLACE VIEW popular_routes AS
SELECT 
  u.home_zip,
  s.building_id,
  b.name as building_name,
  COUNT(DISTINCT u.id) as student_count,
  array_agg(DISTINCT s.course_code) as courses
FROM users u
JOIN schedules s ON s.user_id = u.id
JOIN buildings b ON b.id = s.building_id
WHERE s.active = true
GROUP BY u.home_zip, s.building_id, b.name
ORDER BY student_count DESC;

-- ============================================
-- SAMPLE DATA QUERIES
-- ============================================

-- Count total users
-- SELECT COUNT(*) as total_users FROM users;

-- Count active schedules
-- SELECT COUNT(DISTINCT user_id) as users_with_schedules FROM schedules WHERE active = true;

-- Most popular buildings
-- SELECT building_id, COUNT(*) as class_count 
-- FROM schedules 
-- WHERE active = true 
-- GROUP BY building_id 
-- ORDER BY class_count DESC;

-- Most popular commute routes
-- SELECT home_zip, COUNT(*) as student_count 
-- FROM users 
-- WHERE home_zip IS NOT NULL 
-- GROUP BY home_zip 
-- ORDER BY student_count DESC 
-- LIMIT 10;

COMMENT ON TABLE buildings IS 'PNW campus buildings (Hammond & Westville)';
COMMENT ON TABLE users IS 'Registered students with @pnw.edu email';
COMMENT ON TABLE schedules IS 'Student class schedules for matching';
COMMENT ON TABLE ride_requests IS 'Carpool ride requests between students';
COMMENT ON TABLE messages IS 'In-app messaging between matched students';
COMMENT ON TABLE activity_log IS 'User activity tracking for analytics';

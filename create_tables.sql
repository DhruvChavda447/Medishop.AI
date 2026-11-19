-- ═══════════════════════════════════════════════
-- MediShop Pro — PostgreSQL Setup Script
-- Run: psql -U postgres -d medishop -f create_tables.sql
-- ═══════════════════════════════════════════════

-- Create database if needed (run as superuser first):
-- CREATE DATABASE medishop;

-- Health AI — health risk log table
CREATE TABLE IF NOT EXISTS health_ai_healthrisklog (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    age INTEGER NOT NULL,
    bmi DOUBLE PRECISION NOT NULL,
    blood_pressure_systolic INTEGER NOT NULL,
    blood_pressure_diastolic INTEGER NOT NULL,
    glucose DOUBLE PRECISION NOT NULL,
    cholesterol DOUBLE PRECISION NOT NULL,
    heart_rate INTEGER NOT NULL,
    smoker BOOLEAN NOT NULL DEFAULT FALSE,
    diabetes BOOLEAN NOT NULL DEFAULT FALSE,
    family_history BOOLEAN NOT NULL DEFAULT FALSE,
    activity_level VARCHAR(20) NOT NULL DEFAULT 'moderate',
    risk_score DOUBLE PRECISION NOT NULL,
    risk_label VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Portfolio — contact messages
CREATE TABLE IF NOT EXISTS portfolio_contactmessage (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(254) NOT NULL,
    phone VARCHAR(20) DEFAULT '',
    subject VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_read BOOLEAN NOT NULL DEFAULT FALSE
);

-- Portfolio — resume files
CREATE TABLE IF NOT EXISTS portfolio_resumefile (
    id BIGSERIAL PRIMARY KEY,
    file VARCHAR(100) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Shop — cart
CREATE TABLE IF NOT EXISTS shop_cart (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Shop — cart items
CREATE TABLE IF NOT EXISTS shop_cartitem (
    id BIGSERIAL PRIMARY KEY,
    cart_id INTEGER NOT NULL REFERENCES shop_cart(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL,
    qty INTEGER NOT NULL DEFAULT 1,
    UNIQUE(cart_id, product_id)
);

-- Shop — orders
CREATE TABLE IF NOT EXISTS shop_order (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    total DECIMAL(10,2) NOT NULL DEFAULT 0,
    address TEXT DEFAULT '',
    status VARCHAR(30) NOT NULL DEFAULT 'Confirmed',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Shop — order items
CREATE TABLE IF NOT EXISTS shop_orderitem (
    id BIGSERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES shop_order(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL,
    product_name VARCHAR(200) NOT NULL DEFAULT '',
    qty INTEGER NOT NULL DEFAULT 1,
    price DECIMAL(10,2) NOT NULL DEFAULT 0
);

-- Doctors — appointments
CREATE TABLE IF NOT EXISTS doctors_appointment (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    dr_id INTEGER NOT NULL,
    dr_name VARCHAR(120) NOT NULL,
    dept VARCHAR(60) NOT NULL DEFAULT '',
    appt_date DATE NOT NULL,
    time_slot VARCHAR(20) NOT NULL,
    reason TEXT DEFAULT '',
    patient_name VARCHAR(120) NOT NULL DEFAULT '',
    patient_phone VARCHAR(20) DEFAULT '',
    fee DECIMAL(8,2),
    status VARCHAR(20) NOT NULL DEFAULT 'Confirmed',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Skin AI — analysis log
CREATE TABLE IF NOT EXISTS skin_ai_skinanalysis (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    condition VARCHAR(100) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    model_used VARCHAR(100) NOT NULL DEFAULT 'google/vit-base-patch16-224',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Sentiment — log
CREATE TABLE IF NOT EXISTS sentiment_check_sentimentlog (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    input_text VARCHAR(500) NOT NULL,
    sentiment VARCHAR(20) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    language VARCHAR(5) NOT NULL DEFAULT 'EN',
    response_generated TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Core auth — user profile
CREATE TABLE IF NOT EXISTS core_auth_userprofile (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES auth_user(id) ON DELETE CASCADE,
    phone VARCHAR(20) DEFAULT '',
    address TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Django required tables (if not using manage.py migrate)
-- Use: python manage.py migrate   <-- recommended over manual SQL

SELECT 'All MediShop Pro tables created successfully!' AS status;

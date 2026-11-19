-- ═══════════════════════════════════════════════════════════════════
-- MediCare.AI — PostgreSQL Table Schema (Auto-created via `python manage.py migrate`)
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS doctors_appointment (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    dr_id INTEGER NOT NULL,
    dr_name VARCHAR(100) NOT NULL,
    dept VARCHAR(80) NOT NULL,
    appt_date DATE NOT NULL,
    time_slot VARCHAR(20) NOT NULL,
    reason TEXT DEFAULT '',
    patient_name VARCHAR(100) NOT NULL,
    patient_phone VARCHAR(20) DEFAULT '',
    fee NUMERIC(8,2),
    status VARCHAR(20) NOT NULL DEFAULT 'Completed',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS doctors_medicalbill (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    appointment_id BIGINT UNIQUE REFERENCES doctors_appointment(id) ON DELETE CASCADE,
    bill_no VARCHAR(60) NOT NULL,
    doctor_name VARCHAR(120) NOT NULL DEFAULT 'Consulting Physician',
    department VARCHAR(80) NOT NULL DEFAULT 'General Medicine',
    patient_name VARCHAR(120) NOT NULL DEFAULT 'Patient',
    bill_date VARCHAR(40) NOT NULL DEFAULT '',
    diagnosis TEXT DEFAULT '',
    raw_text TEXT DEFAULT '',
    structured_json TEXT NOT NULL DEFAULT '{}',
    total_amount NUMERIC(10,2) NOT NULL DEFAULT 0,
    source_type VARCHAR(30) NOT NULL DEFAULT 'doctor_checkup',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sentiment_check_sentimentlog (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    input_text TEXT NOT NULL,
    sentiment VARCHAR(20) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    language VARCHAR(10) NOT NULL DEFAULT 'EN',
    response_generated TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

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

CREATE TABLE IF NOT EXISTS portfolio_resumefile (
    id BIGSERIAL PRIMARY KEY,
    file VARCHAR(100) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

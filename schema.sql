-- Create role_user table first (since user references it)
CREATE TABLE IF NOT EXISTS role_user (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- Create user table
CREATE TABLE IF NOT EXISTS "user" (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    role_user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create sessions table
CREATE TABLE IF NOT EXISTS sessions(
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY, 
    program_code VARCHAR(10),
    program VARCHAR(50),
    session_abbrev VARCHAR(10), 
    year INTEGER,
    name VARCHAR(30),
    description VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create applicant_info table
-- age is calculated based on date_birth
CREATE TABLE IF NOT EXISTS applicant_info(
    user_code VARCHAR(10) PRIMARY KEY,
    session_id INT,
    interest_code VARCHAR(10),
    interest VARCHAR(250),
    title VARCHAR(4),
    family_name VARCHAR(250),
    given_name VARCHAR(250), 
    middle_name VARCHAR(250),
    preferred_name VARCHAR(250), 
    former_family_name VARCHAR(250), 
    gender_code VARCHAR(10),
    gender VARCHAR(250),
    country_birth_code VARCHAR(10),
    country_birth VARCHAR(250),
    date_birth DATE,
    age INTEGER,
    country_citizenship_code VARCHAR(10),
    country_citizenship VARCHAR(250),
    dual_citizenship_code VARCHAR(10),
    dual_citizenship VARCHAR(250), 
    primary_spoken_lang_code VARCHAR(10), 
    primary_spoken_lang VARCHAR(250),
    other_spoken_lang_code VARCHAR(10),
    other_spoken_lang VARCHAR(250), 
    visa_type_code VARCHAR(20),
    visa_type VARCHAR(250), 
    country_code VARCHAR(10),
    country VARCHAR(250), 
    address_line1 VARCHAR(1000), 
    address_line2 VARCHAR(1000),
    city VARCHAR(250),
    province_state_region VARCHAR(100),
    postal_code VARCHAR(50),
    primary_telephone VARCHAR(50),
    secondary_telephone VARCHAR(50),
    email VARCHAR(100),
    -- aboriginal BOOLEAN,
    -- first_nation BOOLEAN,
    -- inuit BOOLEAN,
    -- metis BOOLEAN,
    -- aboriginal_not_specified BOOLEAN,
    aboriginal VARCHAR(3),
    first_nation VARCHAR(3),
    inuit VARCHAR(3),
    metis VARCHAR(3),
    aboriginal_not_specified VARCHAR(3),
    aboriginal_info VARCHAR(100),
    racialized VARCHAR(3), 
    academic_history_code VARCHAR(10),
    academic_history VARCHAR(1000), 
    ubc_academic_history TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create program_info table (new table)
CREATE TABLE IF NOT EXISTS program_info (
    user_code VARCHAR(10) PRIMARY KEY REFERENCES applicant_info(user_code),
    program_code VARCHAR(10),
    program VARCHAR(100),
    session VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS applicant_status(
    user_code VARCHAR(10) PRIMARY KEY REFERENCES applicant_info(user_code),
    student_number VARCHAR(100),
    app_start DATE,
    submit_date DATE,
    status_code VARCHAR(5), 
    status VARCHAR(20),
    detail_status VARCHAR(250), 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create application_info table
-- canadian determined by country_citizenship and dual_citizenship if they have 'Canada' as value
CREATE TABLE IF NOT EXISTS application_info (
    user_code VARCHAR(10) PRIMARY KEY REFERENCES applicant_info(user_code),
    sent VARCHAR(100) DEFAULT 'Not Reviewed' CHECK (sent IN ('Not Reviewed', 'Reviewed by PPA', 'Need Jeff''s Review', 'Need Khalad''s Review', 'Waitlist', 'Declined', 'Send Offer to CoGS', 'Offer Sent to CoGS', 'Offer Sent to Student', 'Offer Accepted', 'Offer Declined')),
    full_name VARCHAR(100),
    canadian BOOLEAN,
    english BOOLEAN,
    english_status VARCHAR(50),
    english_description VARCHAR(3000),
    english_comment VARCHAR(255),
    cs TEXT,
    stat TEXT,
    math TEXT,
    additional_comments TEXT,
    gpa VARCHAR(50),
    highest_degree VARCHAR(50),
    degree_area VARCHAR(50),
    mds_v BOOLEAN,
    mds_cl BOOLEAN,
    scholarship VARCHAR(20) DEFAULT 'Undecided' CHECK (scholarship IN ('Yes', 'No', 'Undecided'))
);

CREATE TABLE IF NOT EXISTS ratings(
	user_id INTEGER REFERENCES "user"(id),
	user_code VARCHAR(10) REFERENCES applicant_info(user_code),
	rating DECIMAL(3,1) CHECK (rating >= 0.0 AND rating <= 10.0),
	user_comment VARCHAR(2000),
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (user_id, user_code)
);

-- Renamed from academic_info to institution_info
CREATE TABLE IF NOT EXISTS institution_info(
    user_code VARCHAR(10) REFERENCES applicant_info(user_code),
    institution_number INT,
    institution_code VARCHAR(50),
    full_name VARCHAR(1000),
    country VARCHAR(100), 
    start_date DATE,
    end_date DATE,
    program_study VARCHAR(250), 
    degree_confer_code VARCHAR(100),
    degree_confer VARCHAR(100),
    date_confer DATE,
    credential_receive_code VARCHAR(10),
    credential_receive VARCHAR(250),
    expected_confer_date DATE,
    expected_credential_code VARCHAR(100),
    expected_credential VARCHAR(100),
    honours VARCHAR(5000), 
    fail_withdraw VARCHAR(3),
    reason VARCHAR(3000), 
    gpa VARCHAR(50), 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_code, institution_number)
);

CREATE TABLE IF NOT EXISTS toefl(
    user_code VARCHAR(10) REFERENCES applicant_info(user_code),
    toefl_number INT,
    registration_num VARCHAR(255),
    date_written DATE,
    total_score VARCHAR(255),
    listening VARCHAR(255),
    structure_written VARCHAR(255),
    reading VARCHAR(255),
    speaking VARCHAR(255),
    mybest_total VARCHAR(255),
    mybest_date DATE,
    mybest_listening VARCHAR(255),
    mybest_listening_date DATE,
    mybest_writing VARCHAR(255),
    mybest_writing_date DATE,
    mybest_reading VARCHAR(255),
    mybest_reading_date DATE,
    mybest_speaking VARCHAR(255),
    mybest_speaking_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_code, toefl_number)
);

CREATE TABLE IF NOT EXISTS ielts(
    user_code VARCHAR(10) REFERENCES applicant_info(user_code),
    ielts_number INT,
    candidate_num VARCHAR(255),
    date_written DATE,
    total_band_score VARCHAR(255),
    listening VARCHAR(255),
    reading VARCHAR(255),
    writing VARCHAR(255),
    speaking VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_code, ielts_number)
);

CREATE TABLE IF NOT EXISTS melab(
    user_code VARCHAR(10) PRIMARY KEY REFERENCES applicant_info(user_code),
    ref_num VARCHAR(255),
    date_written DATE,
    total VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pte(
    user_code VARCHAR(10) PRIMARY KEY REFERENCES applicant_info(user_code),
    ref_num VARCHAR(255),
    date_written DATE,
    total VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cael(
    user_code VARCHAR(10) PRIMARY KEY REFERENCES applicant_info(user_code),
    ref_num VARCHAR(255),
    date_written DATE,
    reading VARCHAR(255),
    listening VARCHAR(2255),
    writing VARCHAR(255),
    speaking VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS celpip(
    user_code VARCHAR(10) PRIMARY KEY REFERENCES applicant_info(user_code),
    ref_num VARCHAR(255),
    date_written DATE,
    listening VARCHAR(255),
    speaking VARCHAR(255),
    reading_writing VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alt_elpp(
    user_code VARCHAR(10) PRIMARY KEY REFERENCES applicant_info(user_code),
    ref_num VARCHAR(255),
    date_written DATE,
    total VARCHAR(255),
    test_type VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gre(
    user_code VARCHAR(10) PRIMARY KEY REFERENCES applicant_info(user_code),
    reg_num VARCHAR(255),
    date_written DATE,
    verbal VARCHAR(255),
    verbal_below VARCHAR(255),
    quantitative VARCHAR(255),
    quantitative_below VARCHAR(255),
    writing VARCHAR(255),
    writing_below VARCHAR(255),
    subject_tests VARCHAR(255),
    subject_reg_num VARCHAR(255),
    subject_date DATE, 
    subject_scaled_score VARCHAR(255),
    subject_below VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gmat(
    user_code VARCHAR(10) PRIMARY KEY REFERENCES applicant_info(user_code),
    ref_num VARCHAR(255),
    date_written DATE,
    total VARCHAR(255),
    integrated_reasoning VARCHAR(255),
    quantitative VARCHAR(255),
    verbal VARCHAR(255),
    writing VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS duolingo (
    user_code VARCHAR(10) REFERENCES applicant_info(user_code),
    score INTEGER,
    description TEXT,
    date_written DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_code)
);

CREATE TABLE IF NOT EXISTS activity_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user"(id),
    action_type VARCHAR(50) NOT NULL,
    target_entity VARCHAR(50),
    target_id VARCHAR(50),
    old_value TEXT,
    new_value TEXT,
    additional_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add foreign key constraint with CASCADE DELETE (check if exists first)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_user_role' AND table_name = 'user'
    ) THEN
        ALTER TABLE "user" 
        ADD CONSTRAINT fk_user_role 
        FOREIGN KEY (role_user_id) REFERENCES role_user(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Add foreign key constraint from applicant_info to sessions with CASCADE DELETE
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_applicant_info_sessions' AND table_name = 'applicant_info'
    ) THEN
        ALTER TABLE applicant_info 
        ADD CONSTRAINT fk_applicant_info_sessions 
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE;
    END IF;
END $$;


-- Add CASCADE DELETE constraints for all tables referencing applicant_info
DO $$ 
BEGIN
    -- program_info referneces applicant_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_program_info_applicant_info' AND table_name = 'program_info'
    ) THEN
        ALTER TABLE program_info 
        ADD CONSTRAINT fk_program_info_applicant_info 
        FOREIGN KEY (user_code) REFERENCES applicant_info(user_code) ON DELETE CASCADE;
    END IF;

    -- applicant_status references applicant_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_applicant_status_applicant_info' AND table_name = 'applicant_status'
    ) THEN
        ALTER TABLE applicant_status 
        ADD CONSTRAINT fk_applicant_status_applicant_info 
        FOREIGN KEY (user_code) REFERENCES applicant_info(user_code) ON DELETE CASCADE;
    END IF;

    -- application_info references applicant_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_application_info_applicant_info' AND table_name = 'application_info'
    ) THEN
        ALTER TABLE application_info 
        ADD CONSTRAINT fk_application_info_applicant_info 
        FOREIGN KEY (user_code) REFERENCES applicant_info(user_code) ON DELETE CASCADE;
    END IF;

    -- ratings references applicant_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_ratings_applicant_info' AND table_name = 'ratings'
    ) THEN
        ALTER TABLE ratings 
        ADD CONSTRAINT fk_ratings_applicant_info 
        FOREIGN KEY (user_code) REFERENCES applicant_info(user_code) ON DELETE CASCADE;
    END IF;

    -- institution_info references applicant_info (renamed from academic_info)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_institution_info_applicant_info' AND table_name = 'institution_info'
    ) THEN
        ALTER TABLE institution_info 
        ADD CONSTRAINT fk_institution_info_applicant_info 
        FOREIGN KEY (user_code) REFERENCES applicant_info(user_code) ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_ratings_user' AND table_name = 'ratings'
    ) THEN
        ALTER TABLE ratings 
        ADD CONSTRAINT fk_ratings_user 
        FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE;
    END IF;

    -- toefl references applicant_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_toefl_applicant_info' AND table_name = 'toefl'
    ) THEN
        ALTER TABLE toefl 
        ADD CONSTRAINT fk_toefl_applicant_info
        FOREIGN KEY (user_code) REFERENCES applicant_info(user_code) ON DELETE CASCADE;
    END IF;

    -- ielts references applicant_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_ielts_applicant_info' AND table_name = 'ielts'
    ) THEN
        ALTER TABLE ielts 
        ADD CONSTRAINT fk_ielts_applicant_info 
        FOREIGN KEY (user_code) REFERENCES applicant_info(user_code) ON DELETE CASCADE;
    END IF;

    -- melab references applicant_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_melab_applicant_info' AND table_name = 'melab'
    ) THEN
        ALTER TABLE melab 
        ADD CONSTRAINT fk_melab_applicant_info 
        FOREIGN KEY (user_code) REFERENCES applicant_info(user_code) ON DELETE CASCADE;
    END IF;

    -- pte references applicant_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_pte_applicant_info' AND table_name = 'pte'
    ) THEN
        ALTER TABLE pte 
        ADD CONSTRAINT fk_pte_applicant_info 
        FOREIGN KEY (user_code) REFERENCES applicant_info(user_code) ON DELETE CASCADE;
    END IF;

    -- cael references applicant_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_cael_applicant_info' AND table_name = 'cael'
    ) THEN
        ALTER TABLE cael 
        ADD CONSTRAINT fk_cael_applicant_info 
        FOREIGN KEY (user_code) REFERENCES applicant_info(user_code) ON DELETE CASCADE;
    END IF;

    -- celpip references applicant_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_celpip_applicant_info' AND table_name = 'celpip'
    ) THEN
        ALTER TABLE celpip 
        ADD CONSTRAINT fk_celpip_applicant_info
        FOREIGN KEY (user_code) REFERENCES applicant_info(user_code) ON DELETE CASCADE;
    END IF;

    -- alt_elpp references applicant_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_alt_elpp_applicant_info' AND table_name = 'alt_elpp'
    ) THEN
        ALTER TABLE alt_elpp 
        ADD CONSTRAINT fk_alt_elpp_applicant_info 
        FOREIGN KEY (user_code) REFERENCES applicant_info(user_code) ON DELETE CASCADE;
    END IF;

    -- gre references applicant_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_gre_applicant_info' AND table_name = 'gre'
    ) THEN
        ALTER TABLE gre 
        ADD CONSTRAINT fk_gre_applicant_info 
        FOREIGN KEY (user_code) REFERENCES applicant_info(user_code) ON DELETE CASCADE;
    END IF;

    -- gmat references applicant_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_gmat_applicant_info' AND table_name = 'gmat'
    ) THEN
        ALTER TABLE gmat 
        ADD CONSTRAINT fk_gmat_applicant_info 
        FOREIGN KEY (user_code) REFERENCES applicant_info(user_code) ON DELETE CASCADE;
    END IF;
END $$;

-- Create function to update updated_at timestamp for PostgreSQL
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create function to handle institution_info deletion - sets application_info fields to NULL
CREATE OR REPLACE FUNCTION handle_institution_info_deletion()
RETURNS TRIGGER AS $$
BEGIN
    -- When institution_info is deleted, set related fields in application_info to NULL
    UPDATE application_info 
    SET gpa = NULL, highest_degree = NULL, degree_area = NULL
    WHERE user_code = OLD.user_code;
    
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Create function to handle user deletion - deletes related ratings
CREATE OR REPLACE FUNCTION handle_user_deletion()
RETURNS TRIGGER AS $$
BEGIN
    -- When a user is deleted, delete their ratings
    DELETE FROM ratings WHERE user_id = OLD.id;
    
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for user table to auto-update updated_at
DROP TRIGGER IF EXISTS update_user_updated_at ON "user";
CREATE TRIGGER update_user_updated_at 
    BEFORE UPDATE ON "user" 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for institution_info deletion (renamed from academic_info)
DROP TRIGGER IF EXISTS institution_info_deletion_trigger ON institution_info;
CREATE TRIGGER institution_info_deletion_trigger 
    AFTER DELETE ON institution_info 
    FOR EACH ROW 
    EXECUTE FUNCTION handle_institution_info_deletion();

-- Create trigger for user deletion  
DROP TRIGGER IF EXISTS user_deletion_trigger ON "user";
CREATE TRIGGER user_deletion_trigger 
    AFTER DELETE ON "user" 
    FOR EACH ROW 
    EXECUTE FUNCTION handle_user_deletion();

-- Create trigger for ratings table to auto-update updated_at
DROP TRIGGER IF EXISTS update_ratings_updated_at ON ratings;
CREATE TRIGGER update_ratings_updated_at 
    BEFORE UPDATE ON ratings
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_email ON "user"(email);
CREATE INDEX IF NOT EXISTS idx_user_role ON "user"(role_user_id);
CREATE INDEX IF NOT EXISTS idx_applicant_info_sessions ON applicant_info(session_id);
CREATE INDEX IF NOT EXISTS idx_program_info_user_code ON program_info(user_code);
CREATE INDEX IF NOT EXISTS idx_institution_info_user_code ON institution_info(user_code);
CREATE INDEX IF NOT EXISTS idx_toefl_user_code ON toefl(user_code);
CREATE INDEX IF NOT EXISTS idx_ielts_user_code ON ielts(user_code);
CREATE INDEX IF NOT EXISTS idx_duolingo_user_code ON duolingo(user_code);

-- Insert default roles
INSERT INTO role_user (name) VALUES ('Admin'), ('Faculty'), ('Viewer') 
ON CONFLICT (name) DO NOTHING;

-- Insert default admin user
INSERT INTO "user" (first_name, last_name, email, password, role_user_id) 
SELECT 'Test1', 'User1', 'testuser1@example.com', '$2b$12$mJpl.O3Y12Ti66e8NEENMerKi7obcA3glVon5ZayXT7pMCheIcFbq', 1
WHERE NOT EXISTS (SELECT 1 FROM "user" WHERE email = 'testuser1@example.com');

-- Insert second default admin user
INSERT INTO "user" (first_name, last_name, email, password, role_user_id) 
SELECT 'Test2', 'User2', 'testuser2@example.com', '$2b$12$mJpl.O3Y12Ti66e8NEENMerKi7obcA3glVon5ZayXT7pMCheIcFbq', 1
WHERE NOT EXISTS (SELECT 1 FROM "user" WHERE email = 'testuser2@example.com');

-- Insert default faculty user
INSERT INTO "user" (first_name, last_name, email, password, role_user_id) 
SELECT 'Test3', 'User3', 'testuser3@example.com', '$2b$12$mJpl.O3Y12Ti66e8NEENMerKi7obcA3glVon5ZayXT7pMCheIcFbq', 2
WHERE NOT EXISTS (SELECT 1 FROM "user" WHERE email = 'testuser3@example.com');

-- Insert default viewer user
INSERT INTO "user" (first_name, last_name, email, password, role_user_id) 
SELECT 'Test4', 'User4', 'testuser4@example.com', '$2b$12$mJpl.O3Y12Ti66e8NEENMerKi7obcA3glVon5ZayXT7pMCheIcFbq', 3
WHERE NOT EXISTS (SELECT 1 FROM "user" WHERE email = 'testuser4@example.com');
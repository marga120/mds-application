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

-- Create program_info table (new table)
CREATE TABLE IF NOT EXISTS program_info (
    program_code VARCHAR(10) PRIMARY KEY,
    program VARCHAR(100),
    session VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS student_info(
    user_code VARCHAR(10) PRIMARY KEY,
    interest_code VARCHAR(10),
    interest VARCHAR(100),
    title VARCHAR(4),
    family_name VARCHAR(100),
    given_name VARCHAR(100),
    middle_name VARCHAR(100),
    preferred_name VARCHAR(100),
    former_family_name VARCHAR(100),
    gender_code VARCHAR(10),
    gender VARCHAR(100),
    country_birth_code VARCHAR(10),
    country_birth VARCHAR(100),
    date_birth DATE,
    country_citizenship_code VARCHAR(10),
    country_citizenship VARCHAR(100),
    dual_citizenship_code VARCHAR(10),
    dual_citizenship VARCHAR(100),
    primary_spoken_lang_code VARCHAR(4),
    primary_spoken_lang VARCHAR(100),
    other_spoken_lang_code VARCHAR(4),
    other_spoken_lang VARCHAR(100),
    visa_type_code VARCHAR(20),
    visa_type VARCHAR(100),
    country_code VARCHAR(10),
    country VARCHAR(100),
    address_line1 VARCHAR(100),
    address_line2 VARCHAR(100),
    city VARCHAR(100),
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
    academic_history_code VARCHAR(10),
    academic_history VARCHAR(250),
    ubc_academic_history TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS student_status(
    user_code VARCHAR(10) PRIMARY KEY REFERENCES student_info(user_code),
    student_number VARCHAR(100),
    app_start DATE,
    submit_date DATE,
    status_code VARCHAR(1),
    status VARCHAR(20),
    detail_status VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app_info (
    user_code VARCHAR(10) PRIMARY KEY REFERENCES student_info(user_code),
    status VARCHAR(20),
    sent BOOLEAN,
    full_name VARCHAR(100),
    canadian BOOLEAN,
    english BOOLEAN,
    cs VARCHAR(20),
    stat VARCHAR(20),
    math VARCHAR(20),
    gpa VARCHAR(10),
    highest_degree VARCHAR(50),
    degree_area VARCHAR(50),
    mds_v BOOLEAN,
    mds_cl BOOLEAN,
    scholarship BOOLEAN
);

CREATE TABLE IF NOT EXISTS rating(
    user_code VARCHAR(10) PRIMARY KEY REFERENCES student_info(user_code),
    user_id INTEGER REFERENCES "user"(id),
    rating VARCHAR(20),
    user_comment VARCHAR(300)
);

-- Renamed from academic_info to institution_info
CREATE TABLE IF NOT EXISTS institution_info(
    user_code VARCHAR(10) REFERENCES student_info(user_code),
    institution_number INT,
    institution_code VARCHAR(50),
    full_name VARCHAR(100),
    country VARCHAR(50),
    start_date DATE,
    end_date DATE,
    program_study VARCHAR(100),
    degree_confer_code VARCHAR(100),
    degree_confer VARCHAR(100),
    date_confer DATE,
    credential_receive_code VARCHAR(10),
    credential_receive VARCHAR(50),
    expected_confer_date DATE,
    expected_credential_code VARCHAR(100),
    expected_credential VARCHAR(100),
    honours VARCHAR(100),
    fail_withdraw BOOLEAN,
    reason VARCHAR(250),
    gpa VARCHAR(50),
    PRIMARY KEY (user_code, institution_number)
);

CREATE TABLE IF NOT EXISTS toefl(
    user_code VARCHAR(10) REFERENCES student_info(user_code),
    toefl_number INT,
    registration_num VARCHAR(20),
    date_written DATE,
    total_score VARCHAR(5),
    listening VARCHAR(2),
    structure_written VARCHAR(2),
    reading VARCHAR(2),
    speaking VARCHAR(2),
    mybest_total VARCHAR(3),
    mybest_date DATE,
    mybest_listening VARCHAR(2),
    mybest_listening_date DATE,
    mybest_writing VARCHAR(2),
    mybest_writing_date DATE,
    mybest_reading VARCHAR(2),
    mybest_reading_date DATE,
    mybest_speaking VARCHAR(2),
    mybest_speaking_date DATE,
    PRIMARY KEY (user_code, toefl_number)
);

CREATE TABLE IF NOT EXISTS ielts(
    user_code VARCHAR(10) REFERENCES student_info(user_code),
    ielts_number INT,
    candidate_num VARCHAR(20),
    date_written DATE,
    total_band_score VARCHAR(3),
    listening VARCHAR(3),
    reading VARCHAR(3),
    writing VARCHAR(3),
    speaking VARCHAR(3),
    PRIMARY KEY (user_code, ielts_number)
);

CREATE TABLE IF NOT EXISTS melab(
    user_code VARCHAR(10) PRIMARY KEY REFERENCES student_info(user_code),
    ref_num VARCHAR(20),
    date_written DATE,
    total VARCHAR(2)
);

CREATE TABLE IF NOT EXISTS pte(
    user_code VARCHAR(10) PRIMARY KEY REFERENCES student_info(user_code),
    ref_num VARCHAR(20),
    date_written DATE,
    total VARCHAR(2)
);

CREATE TABLE IF NOT EXISTS cael(
    user_code VARCHAR(10) PRIMARY KEY REFERENCES student_info(user_code),
    ref_num VARCHAR(20),
    date_written DATE,
    reading VARCHAR(2),
    listening VARCHAR(2),
    writing VARCHAR(2),
    speaking VARCHAR(2)
);

CREATE TABLE IF NOT EXISTS celpip(
    user_code VARCHAR(10) PRIMARY KEY REFERENCES student_info(user_code),
    ref_num VARCHAR(20),
    date_written DATE,
    listening VARCHAR(2),
    speaking VARCHAR(2),
    reading_writing VARCHAR(2)
);

CREATE TABLE IF NOT EXISTS alt_elpp(
    user_code VARCHAR(10) PRIMARY KEY REFERENCES student_info(user_code),
    ref_num VARCHAR(20),
    date_written DATE,
    total VARCHAR(20),
    test_type VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS gre(
    user_code VARCHAR(10) PRIMARY KEY REFERENCES student_info(user_code),
    reg_num VARCHAR(20),
    date_written DATE,
    verbal VARCHAR(3),
    verbal_below VARCHAR(3),
    quantitative VARCHAR(3),
    quantitative_below VARCHAR(3),
    writing VARCHAR(2),
    writing_below VARCHAR(3),
    subject_tests VARCHAR(20),
    subject_reg_num VARCHAR(20),
    subject_date DATE, 
    subject_scaled_score VARCHAR(3),
    subject_below VARCHAR(3)
);

CREATE TABLE IF NOT EXISTS gmat(
    user_code VARCHAR(10) PRIMARY KEY REFERENCES student_info(user_code),
    ref_num VARCHAR(20),
    date_written DATE,
    total VARCHAR(3),
    integrated_reasoning VARCHAR(2),
    quantitative VARCHAR(2),
    verbal VARCHAR(2),
    writing VARCHAR(2)
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

-- Add CASCADE DELETE constraints for all tables referencing student_info
DO $$ 
BEGIN
    -- student_status references student_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_student_status_student_info' AND table_name = 'student_status'
    ) THEN
        ALTER TABLE student_status 
        ADD CONSTRAINT fk_student_status_student_info 
        FOREIGN KEY (user_code) REFERENCES student_info(user_code) ON DELETE CASCADE;
    END IF;

    -- app_info references student_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_app_info_student_info' AND table_name = 'app_info'
    ) THEN
        ALTER TABLE app_info 
        ADD CONSTRAINT fk_app_info_student_info 
        FOREIGN KEY (user_code) REFERENCES student_info(user_code) ON DELETE CASCADE;
    END IF;

    -- rating references student_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_rating_student_info' AND table_name = 'rating'
    ) THEN
        ALTER TABLE rating 
        ADD CONSTRAINT fk_rating_student_info 
        FOREIGN KEY (user_code) REFERENCES student_info(user_code) ON DELETE CASCADE;
    END IF;

    -- institution_info references student_info (renamed from academic_info)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_institution_info_student_info' AND table_name = 'institution_info'
    ) THEN
        ALTER TABLE institution_info 
        ADD CONSTRAINT fk_institution_info_student_info 
        FOREIGN KEY (user_code) REFERENCES student_info(user_code) ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_rating_user' AND table_name = 'rating'
    ) THEN
        ALTER TABLE rating 
        ADD CONSTRAINT fk_rating_user 
        FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE;
    END IF;

    -- toefl references student_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_toefl_student_info' AND table_name = 'toefl'
    ) THEN
        ALTER TABLE toefl 
        ADD CONSTRAINT fk_toefl_student_info 
        FOREIGN KEY (user_code) REFERENCES student_info(user_code) ON DELETE CASCADE;
    END IF;

    -- ielts references student_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_ielts_student_info' AND table_name = 'ielts'
    ) THEN
        ALTER TABLE ielts 
        ADD CONSTRAINT fk_ielts_student_info 
        FOREIGN KEY (user_code) REFERENCES student_info(user_code) ON DELETE CASCADE;
    END IF;

    -- melab references student_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_melab_student_info' AND table_name = 'melab'
    ) THEN
        ALTER TABLE melab 
        ADD CONSTRAINT fk_melab_student_info 
        FOREIGN KEY (user_code) REFERENCES student_info(user_code) ON DELETE CASCADE;
    END IF;

    -- pte references student_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_pte_student_info' AND table_name = 'pte'
    ) THEN
        ALTER TABLE pte 
        ADD CONSTRAINT fk_pte_student_info 
        FOREIGN KEY (user_code) REFERENCES student_info(user_code) ON DELETE CASCADE;
    END IF;

    -- cael references student_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_cael_student_info' AND table_name = 'cael'
    ) THEN
        ALTER TABLE cael 
        ADD CONSTRAINT fk_cael_student_info 
        FOREIGN KEY (user_code) REFERENCES student_info(user_code) ON DELETE CASCADE;
    END IF;

    -- celpip references student_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_celpip_student_info' AND table_name = 'celpip'
    ) THEN
        ALTER TABLE celpip 
        ADD CONSTRAINT fk_celpip_student_info 
        FOREIGN KEY (user_code) REFERENCES student_info(user_code) ON DELETE CASCADE;
    END IF;

    -- alt_elpp references student_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_alt_elpp_student_info' AND table_name = 'alt_elpp'
    ) THEN
        ALTER TABLE alt_elpp 
        ADD CONSTRAINT fk_alt_elpp_student_info 
        FOREIGN KEY (user_code) REFERENCES student_info(user_code) ON DELETE CASCADE;
    END IF;

    -- gre references student_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_gre_student_info' AND table_name = 'gre'
    ) THEN
        ALTER TABLE gre 
        ADD CONSTRAINT fk_gre_student_info 
        FOREIGN KEY (user_code) REFERENCES student_info(user_code) ON DELETE CASCADE;
    END IF;

    -- gmat references student_info
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_gmat_student_info' AND table_name = 'gmat'
    ) THEN
        ALTER TABLE gmat 
        ADD CONSTRAINT fk_gmat_student_info 
        FOREIGN KEY (user_code) REFERENCES student_info(user_code) ON DELETE CASCADE;
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

-- Create function to handle institution_info deletion - sets app_info fields to NULL
CREATE OR REPLACE FUNCTION handle_institution_info_deletion()
RETURNS TRIGGER AS $$
BEGIN
    -- When institution_info is deleted, set related fields in app_info to NULL
    UPDATE app_info 
    SET gpa = NULL, highest_degree = NULL, degree_area = NULL
    WHERE user_code = OLD.user_code;
    
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Create function to handle user deletion - deletes related rating
CREATE OR REPLACE FUNCTION handle_user_deletion()
RETURNS TRIGGER AS $$
BEGIN
    -- When a user is deleted, delete their rating
    DELETE FROM rating WHERE user_id = OLD.id;
    
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

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_email ON "user"(email);
CREATE INDEX IF NOT EXISTS idx_user_role ON "user"(role_user_id);
CREATE INDEX IF NOT EXISTS idx_institution_info_user_code ON institution_info(user_code);
CREATE INDEX IF NOT EXISTS idx_toefl_user_code ON toefl(user_code);
CREATE INDEX IF NOT EXISTS idx_ielts_user_code ON ielts(user_code);

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
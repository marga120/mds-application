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

-- Create session table
CREATE TABLE IF NOT EXISTS session(
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    year INTEGER, --2025
    program VARCHAR(20),
    program_code VARCHAR(10),
    name VARCHAR(20), --session 2025-2026
    session_abbrev VARCHAR(6),
    description VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- CREATE TABLE IF NOT EXISTS app_info (
-- 	user_code VARCHAR(10) PRIMARY KEY REFERENCES student_info(user_code),
-- 	sent BOOLEAN,
-- 	full_name VARCHAR(100),
-- 	canadian BOOLEAN,
-- 	english BOOLEAN,
-- 	cs VARCHAR(20),
-- 	stat VARCHAR(20),
-- 	math VARCHAR(20),
-- 	gpa VARCHAR(10),
-- 	highest_degree VARCHAR(50),
-- 	degree_area VARCHAR(50),
-- 	mds_v BOOLEAN,
-- 	mds_cl BOOLEAN,
-- 	scholarship BOOLEAN,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- CREATE TABLE IF NOT EXISTS ratings(
-- 	user_code VARCHAR(10) PRIMARY KEY REFERENCES student_info(user_code),
-- 	user_id INTEGER,
-- 	rating VARCHAR(20),
-- 	user_comment VARCHAR(300),
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

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

-- Create trigger for user deletion  
DROP TRIGGER IF EXISTS user_deletion_trigger ON "user";
CREATE TRIGGER user_deletion_trigger 
    AFTER DELETE ON "user" 
    FOR EACH ROW 
    EXECUTE FUNCTION handle_user_deletion();

-- Create indexes for better performance
-- CREATE INDEX IF NOT EXISTS idx_students_university ON students(university);
-- CREATE INDEX IF NOT EXISTS idx_students_year ON students(year);
-- CREATE INDEX IF NOT EXISTS idx_students_degree ON students(degree);
CREATE INDEX IF NOT EXISTS idx_user_email ON "user"(email);
CREATE INDEX IF NOT EXISTS idx_user_role ON "user"(role_user_id);

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

-- Insert second default faculty user
INSERT INTO "user" (first_name, last_name, email, password, role_user_id) 
SELECT 'Test3', 'User3', 'testuser3@example.com', '$2b$12$mJpl.O3Y12Ti66e8NEENMerKi7obcA3glVon5ZayXT7pMCheIcFbq', 2
WHERE NOT EXISTS (SELECT 1 FROM "user" WHERE email = 'testuser3@example.com');

-- Insert second default viewer user
INSERT INTO "user" (first_name, last_name, email, password, role_user_id) 
SELECT 'Test4', 'User4', 'testuser4@example.com', '$2b$12$mJpl.O3Y12Ti66e8NEENMerKi7obcA3glVon5ZayXT7pMCheIcFbq', 3
WHERE NOT EXISTS (SELECT 1 FROM "user" WHERE email = 'testuser4@example.com');
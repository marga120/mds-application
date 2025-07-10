-- Create RoleUser table first (since User references it)
CREATE TABLE IF NOT EXISTS "RoleUser" (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- Create User table
CREATE TABLE IF NOT EXISTS "User" (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    firstName VARCHAR(50) NOT NULL,
    lastName VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    roleUserId INTEGER NOT NULL,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create students table (your existing table)
CREATE TABLE IF NOT EXISTS "Students" (
    student_id VARCHAR(50) PRIMARY KEY,
    student_name VARCHAR(255) NOT NULL,
    university VARCHAR(255) NOT NULL,
    year INTEGER NOT NULL,
    degree VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add foreign key constraint with CASCADE DELETE (check if exists first) for User and RoleUser
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_user_role' AND table_name = 'User'
    ) THEN
        ALTER TABLE "User" 
        ADD CONSTRAINT fk_user_role 
        FOREIGN KEY (roleUserId) REFERENCES "RoleUser"(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Create function to update updatedAt timestamp for PostgreSQL
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updatedAt = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for User table to auto-update updatedAt
DROP TRIGGER IF EXISTS update_user_updated_at ON "User";
CREATE TRIGGER update_user_updated_at 
    BEFORE UPDATE ON "User" 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_students_university ON "Students"(university);
CREATE INDEX IF NOT EXISTS idx_students_year ON "Students"(year);
CREATE INDEX IF NOT EXISTS idx_students_degree ON "Students"(degree);
CREATE INDEX IF NOT EXISTS idx_user_email ON "User"(email);
CREATE INDEX IF NOT EXISTS idx_user_role ON "User"(roleUserId);

-- Insert default roles
INSERT INTO "RoleUser" (name) VALUES ('Admin'), ('Faculty'), ('Viewer') 
ON CONFLICT (name) DO NOTHING;

-- Insert default admin user (password should be hashed in real app)
INSERT INTO "User" (firstName, lastName, email, password, roleUserId) 
SELECT 'Test1', 'User1', 'testuser1@gmail.com', 'password', 1
WHERE NOT EXISTS (SELECT 1 FROM "User" WHERE email = 'testuser1@gmail.com');
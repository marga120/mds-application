"""
Database Seeding Script
Resets user and role_user tables to original test data state.
Can be run anytime to restore clean test data.

Usage: python seed.py
"""

from utils.database import get_db_connection
from datetime import datetime
import sys

def clear_existing_data():
    """Clear existing user and role data"""
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        print("🗑️  Clearing existing user and role data...")
        
        # Delete users first (due to foreign key constraint)
        cursor.execute('DELETE FROM "user"')
        users_deleted = cursor.rowcount
        
        # Delete roles
        cursor.execute('DELETE FROM role_user')
        roles_deleted = cursor.rowcount
        
        # Reset the sequences to start from 1 again
        cursor.execute('ALTER SEQUENCE role_user_id_seq RESTART WITH 1')
        cursor.execute('ALTER SEQUENCE user_id_seq RESTART WITH 1')
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✓ Deleted {users_deleted} users and {roles_deleted} roles")
        print("✓ Reset ID sequences to start from 1")
        return True
        
    except Exception as e:
        print(f"❌ Error clearing data: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def seed_roles():
    """Insert default roles with fixed IDs"""
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        print("👑 Seeding roles...")
        
        # Insert roles in specific order to ensure consistent IDs
        roles = [
            ('Admin',),      # Will get ID = 1
            ('Faculty',),    # Will get ID = 2  
            ('Viewer',)      # Will get ID = 3
        ]
        
        cursor.executemany(
            'INSERT INTO role_user (name) VALUES (%s)',
            roles
        )
        
        # Verify the IDs
        cursor.execute('SELECT id, name FROM role_user ORDER BY id')
        actual_roles = cursor.fetchall()
        print(f"📝 Created roles: {dict(actual_roles)}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✓ Inserted {len(roles)} roles")
        return True
        
    except Exception as e:
        print(f"❌ Error seeding roles: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def seed_users():
    """Insert test users"""
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        print("👥 Seeding users...")
        
        # Get actual role IDs
        cursor.execute('SELECT id, name FROM role_user ORDER BY id')
        role_data = cursor.fetchall()
        role_mapping = {name: id for id, name in role_data}
        
        print(f"🔍 Available roles: {role_mapping}")
        
        # Test users using actual role IDs
        users = [
            # Admin users
            ('Test1', 'User1', 'testuser1@example.com', 'password', role_mapping['Admin']),
            ('Test2', 'User2', 'testuser2@gmail.com', 'password', role_mapping['Admin']),
            
            # Faculty users
            ('Test3', 'User3', 'testuser3@gmail.com', 'password', role_mapping['Faculty']),
            
            # Viewer users
            ('Test4', 'User4', 'testuser4@gmail.com', 'password', role_mapping['Viewer']),
        ]
        
        current_time = datetime.now()
        
        for user in users:
            cursor.execute('''
                INSERT INTO "user" (first_name, last_name, email, password, role_user_id, created_at, updated_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (*user, current_time, current_time))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✓ Inserted {len(users)} test users")
        return True
        
    except Exception as e:
        print(f"❌ Error seeding users: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def show_summary():
    """Show summary of seeded data"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        print("\n📊 Database Summary:")
        print("=" * 50)
        
        # Count roles
        cursor.execute('SELECT COUNT(*) FROM role_user')
        role_count = cursor.fetchone()[0]
        print(f"Roles: {role_count}")
        
        # Count users by role
        cursor.execute('''
            SELECT r.name, COUNT(u.id) 
            FROM role_user r 
            LEFT JOIN "user" u ON r.id = u.role_user_id 
            GROUP BY r.id, r.name 
            ORDER BY r.id
        ''')
        
        for role_name, user_count in cursor.fetchall():
            print(f"  {role_name}: {user_count} users")
        
        # Total users
        cursor.execute('SELECT COUNT(*) FROM "user"')
        total_users = cursor.fetchone()[0]
        print(f"Total Users: {total_users}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error getting summary: {e}")

def main():
    """Main seeding function"""
    print("🌱 Starting database seeding...")
    print("=" * 50)
    
    # Clear existing data
    if not clear_existing_data():
        sys.exit(1)
    
    # Seed roles
    if not seed_roles():
        sys.exit(1)
    
    # Seed users  
    if not seed_users():
        sys.exit(1)
    
    # Show summary
    show_summary()
    
    print("\n✅ Database seeding completed successfully!")
    print("\n🔑 Test Login Credentials:")
    print("Admin: testuser1@example.com / password")
    print("Admin: testuser2@gmail.com / password") 
    print("Faculty: testuser3@gmail.com / password")
    print("Faculty: michael.johnson@university.edu / password")
    print("Viewer: testuser4@gmail.com / password")
    print("Viewer: alice.viewer@example.com / password")

if __name__ == "__main__":
    main()
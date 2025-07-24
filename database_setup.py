import sqlite3

def setup_database():
    """
    Creates the SQLite database and the 'users' table with all necessary columns.
    Run this script once to initialize your database.
    """
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Create the users table if it doesn't exist
        # This schema matches all the fields in your registration form
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                phone_number TEXT,
                designation TEXT,
                department TEXT,
                place TEXT,
                role TEXT 
            )
        ''')
        
        conn.commit()
        print("Database 'users.db' created and 'users' table is ready.")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    setup_database()
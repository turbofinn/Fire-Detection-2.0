import sqlite3
from passlib.context import CryptContext

# Initialize the password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def add_user_to_db(user_data: dict):
    """
    Hashes the user's password and saves the complete user record to the database.
    Raises a ValueError if the username or email is already taken.
    """
    
    # Securely hash the plain-text password
    hashed_password = pwd_context.hash(user_data["password"])
    
    conn = None
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (
                username, email, password_hash, phone_number, 
                designation, department, place, role
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_data["username"],
            user_data["email"],
            hashed_password,
            user_data["phone_number"],
            user_data["designation"],
            user_data["department"],
            user_data["place"],
            user_data["role"]
        ))
        conn.commit()
        print(f"Successfully added user: {user_data['username']}")

    except sqlite3.IntegrityError as e:
        # This error occurs if the username or email is not unique
        raise ValueError("Username or Email already exists. Please choose another.") from e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise
    finally:
        if conn:
            conn.close()

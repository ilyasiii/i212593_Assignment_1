from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

# ✅ FastAPI App Instance (Only One)
app = FastAPI()

# ✅ Database Connection
DATABASE_URL = "dbname=Users user=postgres password=1234 host=localhost port=5432"

def get_db():
    """Connect to PostgreSQL and return connection object."""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    conn.autocommit = True  # Ensures changes are committed automatically
    return conn

# ✅ Root Route
@app.get("/")
def read_root():
    return {"message": "FastAPI is running with PostgreSQL!"}

# ✅ User Model for Registration
class User(BaseModel):
    username: str
    email: str
    password: str

# ✅ User Model for Login
class LoginUser(BaseModel):
    email: str
    password: str

# ✅ User Registration
@app.post("/register")
def register(user: User):
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s) RETURNING id",
            (user.username, user.email, user.password),
        )
        user_id = cur.fetchone()
        conn.commit()
    except psycopg2.Error:
        conn.rollback()
        raise HTTPException(status_code=400, detail="User registration failed")
    finally:
        cur.close()
        conn.close()

    return {"message": "User registered successfully", "user_id": user_id["id"]}

# ✅ User Login
@app.post("/login")
def login(user: LoginUser):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email = %s AND password = %s", (user.email, user.password))
    db_user = cur.fetchone()
    
    cur.close()
    conn.close()

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"message": "Login successful", "user_id": db_user["id"]}

# ✅ Get User Profile
@app.get("/profile/{user_id}")
def get_profile(user_id: int):
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT id, username, email FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"user": user}

# ✅ Database Connection Check
try:
    conn = psycopg2.connect(DATABASE_URL)
    print("✅ Database connection successful!")
    conn.close()
except Exception as e:
    print("❌ Database connection failed:", e)

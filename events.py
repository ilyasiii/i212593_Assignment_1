from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()

# Database Connection
DATABASE_URL = "dbname=Users user=postgres password=1234 host=localhost port=5432"

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

# Event Model
class Event(BaseModel):
    title: str
    description: str
    date: str
    location: str
    created_by: int

# Create Event
@app.post("/events/")
def create_event(event: Event):
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO events (title, description, date, location, created_by) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (event.title, event.description, event.date, event.location, event.created_by),
        )
        event_id = cur.fetchone()["id"]
        conn.commit()
    except psycopg2.Error:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Event creation failed")
    finally:
        cur.close()
        conn.close()

    return {"message": "Event created successfully", "event_id": event_id}

# Get All Events
@app.get("/events/")
def get_events():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM events")
    events = cur.fetchall()

    cur.close()
    conn.close()

    return {"events": events}

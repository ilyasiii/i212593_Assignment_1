from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import pika
import json

app = FastAPI()

# Database Connection
DATABASE_URL = "dbname=Users user=postgres password=1234 host=localhost port=5432"

def get_db():
    """Connect to PostgreSQL and return connection object."""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    conn.autocommit = True
    return conn

# RabbitMQ publisher function
def publish_booking_notification(message: dict):
    """Publish booking confirmation message to RabbitMQ."""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        # Declare the queue (creates if not exists)
        channel.queue_declare(queue='notification_queue', durable=True)
        # Publish message
        channel.basic_publish(
            exchange='',
            routing_key='notification_queue',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2  # make message persistent
            )
        )
        connection.close()
    except Exception as e:
        print("Failed to publish message to RabbitMQ:", e)

# Booking Model
class Booking(BaseModel):
    user_id: int
    event_id: int
    tickets: int

# Create Booking Endpoint
@app.post("/bookings/")
def create_booking(booking: Booking):
    # Simulate payment processing (assume success)
    payment_successful = True

    if not payment_successful:
        raise HTTPException(status_code=400, detail="Payment failed")

    # Insert booking record into PostgreSQL
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO bookings (user_id, event_id, tickets, status) VALUES (%s, %s, %s, %s) RETURNING id",
            (booking.user_id, booking.event_id, booking.tickets, "CONFIRMED")
        )
        booking_id = cur.fetchone()["id"]
        conn.commit()
    except psycopg2.Error:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Booking creation failed")
    finally:
        cur.close()
        conn.close()

    # Publish an event to RabbitMQ to notify the Notification Service
    notification_message = {
        "booking_id": booking_id,
        "user_id": booking.user_id,
        "status": "CONFIRMED"
    }
    publish_booking_notification(notification_message)

    return {"message": "Booking created successfully", "booking_id": booking_id}

# Get Booking Details Endpoint
@app.get("/bookings/{booking_id}")
def get_booking(booking_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bookings WHERE id = %s", (booking_id,))
    booking = cur.fetchone()
    cur.close()
    conn.close()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"booking": booking}

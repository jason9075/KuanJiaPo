from pathlib import Path
from typing import Set
import simpleaudio as sa
import json
import pytz
from fastapi import (
    FastAPI,
    Request,
    Query,
    WebSocket,
    WebSocketDisconnect,
    UploadFile,
    File,
    Form,
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    Response,
    StreamingResponse,
)
from starlette.background import BackgroundTask

from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
import uuid
from datetime import datetime, timedelta
import threading

import uvicorn
import MySQLdb
import os
import pytz
import time
from dotenv import load_dotenv

load_dotenv()

# Prometheus counters
PAGE_VIEWS = Counter("page_views_total", "Total number of page views")
EVENTS_SAVED = Counter("events_saved_total", "Total number of events saved")
REMINDERS_PLAYED = Counter(
    "reminders_played_total", "Total number of reminder audio played"
)

AUDIO_DIR = os.getenv("REMINDER_AUDIO_DIR", "static/reminders")

# Database connection setup

db = None
max_retries = 5
for i in range(max_retries):
    try:
        db = MySQLdb.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
        )
        break
    except Exception as e:
        print("Database connection error:", e)
        time.sleep(5)
        continue
else:
    print(f"Failed to connect to the database after {max_retries} retries")
    exit(1)


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/metrics")
async def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.get("/", response_class=HTMLResponse)
async def home():
    PAGE_VIEWS.inc()
    html_file = Path("static/index.html")
    return HTMLResponse(content=html_file.read_text(), status_code=200)


@app.get("/api/events")
async def get_events(page: int = Query(0), size: int = Query(30)):
    ensure_db_connection()

    offset = page * size
    events = []
    with db.cursor(MySQLdb.cursors.DictCursor) as cursor:
        cursor.execute(
            """
            SELECT id, screenshot_path, bbox_x, bbox_y, bbox_w, bbox_h, confidence, created_date
            FROM event
            ORDER BY created_date DESC
            LIMIT %s OFFSET %s
        """,
            (size, offset),
        )
        events = cursor.fetchall()

    # Convert datetime objects to string
    tz = pytz.timezone("Asia/Taipei")
    for event in events:
        event["created_date"] = (
            event["created_date"].astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
        )

    return JSONResponse(events)


@app.post("/api/save")
async def save_event(request: Request):
    data = await request.json()
    image_path = data.get("image_path")
    x = data.get("bbox_x")
    y = data.get("bbox_y")
    w = data.get("bbox_w")
    h = data.get("bbox_h")
    confidence = data.get("confidence")

    # Save the event to the database
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO event (screenshot_path, bbox_x, bbox_y, bbox_w, bbox_h, confidence)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (image_path, x, y, w, h, confidence),
    )
    db.commit()
    cursor.close()

    EVENTS_SAVED.inc()

    return JSONResponse({"message": "Event saved successfully"})


@app.get("/reminder", response_class=HTMLResponse)
async def reminder_page():
    html_file = Path("static/reminder.html")
    return HTMLResponse(content=html_file.read_text(), status_code=200)


@app.post("/api/reminders")
async def add_reminder(
    file: UploadFile = File(...),
    day_of_week: int = Form(...),
    time_of_day: str = Form(...),
):
    ensure_db_connection()
    os.makedirs(AUDIO_DIR, exist_ok=True)
    filename = f"{uuid.uuid4()}.mp3"
    file_path = Path(AUDIO_DIR) / filename
    with open(file_path, "wb") as f:
        f.write(await file.read())
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO reminder (audio_path, day_of_week, time_of_day) VALUES (%s, %s, %s)",
            (str(file_path), day_of_week, time_of_day),
        )
        db.commit()
    return JSONResponse({"message": "Reminder saved"})


@app.get("/api/reminders")
async def list_reminders():
    ensure_db_connection()
    reminders = []
    with db.cursor(MySQLdb.cursors.DictCursor) as cursor:
        cursor.execute(
            "SELECT id, day_of_week, time_of_day FROM reminder ORDER BY day_of_week, time_of_day"
        )
        reminders = cursor.fetchall()
    for r in reminders:
        tod = r["time_of_day"]
        if isinstance(tod, timedelta):
            tod = (datetime.min + tod).time()
        r["time_of_day"] = (
            tod.strftime("%H:%M") if hasattr(tod, "strftime") else str(tod)[:5]
        )
        r["audio_url"] = f"/api/reminders/{r['id']}/audio"
    return JSONResponse(reminders)


@app.get("/api/reminders/{reminder_id}/audio")
async def get_reminder_audio(reminder_id: int):
    ensure_db_connection()
    with db.cursor(MySQLdb.cursors.DictCursor) as cursor:
        cursor.execute(
            "SELECT audio_path FROM reminder WHERE id = %s",
            (reminder_id,),
        )
        row = cursor.fetchone()
        if not row:
            return Response(status_code=404)
        file_path = row["audio_path"]
    try:
        f = open(file_path, "rb")
    except FileNotFoundError:
        return Response(status_code=404)
    return StreamingResponse(
        f,
        media_type="audio/mpeg",
        background=BackgroundTask(f.close),
    )


@app.delete("/api/reminders/{reminder_id}")
async def delete_reminder(reminder_id: int):
    ensure_db_connection()
    audio_path = None
    with db.cursor(MySQLdb.cursors.DictCursor) as cursor:
        cursor.execute("SELECT audio_path FROM reminder WHERE id=%s", (reminder_id,))
        row = cursor.fetchone()
        if row:
            audio_path = row["audio_path"]
        cursor.execute("DELETE FROM reminder WHERE id=%s", (reminder_id,))
        db.commit()
    if audio_path:
        try:
            os.remove(audio_path)
        except FileNotFoundError:
            pass
    return JSONResponse({"message": "Deleted"})

def ensure_db_connection():
    global db
    try:
        db.ping()
    except MySQLdb.OperationalError:
        # 如果 ping 失敗，可在這裡做更進一步的錯誤處理或重新連線
        # 不建議在 except 裡直接 db.ping(reconnect=True)，因為會造成無窮重試
        db.close()
        db = MySQLdb.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
        )


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        await self.send_count()

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        await self.send_count()

    async def broadcast(self, message: str, sender: WebSocket):
        for connection in list(self.active_connections):
            if connection is not sender:
                await connection.send_text(message)

    async def send_count(self):
        message = json.dumps({"type": "count", "count": len(self.active_connections)})
        for connection in list(self.active_connections):
            await connection.send_text(message)


manager = ConnectionManager()


@app.on_event("startup")
def start_reminder_thread():
    os.makedirs(AUDIO_DIR, exist_ok=True)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data, websocket)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)


def main():
    certfile = os.getenv("SSL_CERTFILE")
    keyfile = os.getenv("SSL_KEYFILE")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        ssl_certfile=certfile,
        ssl_keyfile=keyfile,
    )


if __name__ == "__main__":
    main()

from pathlib import Path
from typing import Set
from fastapi import FastAPI, Request, Query, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, Response

from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

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

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: str, sender: WebSocket):
        for connection in list(self.active_connections):
            if connection is not sender:
                await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()

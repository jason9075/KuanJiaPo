from pathlib import Path
from fastapi import FastAPI, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

import uvicorn
import MySQLdb
import os
import pytz
import time
from dotenv import load_dotenv

load_dotenv()

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


@app.get("/", response_class=HTMLResponse)
async def home():
    html_file = Path("static/index.html")
    return HTMLResponse(content=html_file.read_text(), status_code=200)


@app.get("/api/events")
async def get_events(page: int = Query(0), size: int = Query(30)):
    offset = page * size
    events = []
    with db.cursor(MySQLdb.cursors.DictCursor) as cursor:
        cursor.execute(
            """
            SELECT id, screenshot_path, bbox_x, bbox_y, bbox_w, bbox_h, created_date
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

    # Save the event to the database
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO event (screenshot_path, bbox_x, bbox_y, bbox_w, bbox_h)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (image_path, x, y, w, h),
    )
    db.commit()
    cursor.close()

    return JSONResponse({"message": "Event saved successfully"})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

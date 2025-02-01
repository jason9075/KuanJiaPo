from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import MySQLdb
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Database connection setup
db = MySQLdb.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE"),
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def home():
    html_file = Path("static/index.html")
    return HTMLResponse(content=html_file.read_text(), status_code=200)


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

    return {"message": "Event saved successfully"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

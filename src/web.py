from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# 靜態資源目錄
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def home():
    html_file = Path("static/index.html")
    return HTMLResponse(content=html_file.read_text(), status_code=200)


@app.post("/api/save")
async def save_event(request: Request):
    data = await request.json()
    image_path = data.get("image_path")
    bbox = data.get("bbox")

    # Save the event to the database or filesystem
    Path(image_path).write_text("Sample data for event")
    return {"message": "Event saved successfully"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

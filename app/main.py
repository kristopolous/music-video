from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
import os

app = FastAPI(title="Music Video Automation API")

# Ensure directories exist
os.makedirs("static", exist_ok=True)
os.makedirs("output", exist_ok=True)

app.include_router(router)

# Mount static files for the frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount output directory to serve generated media
app.mount("/output", StaticFiles(directory="output"), name="output")

@app.get("/")
async def root():
    return {"message": "Music Video Automation API is running. Access UI at /static/index.html"}

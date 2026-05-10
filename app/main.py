import os
import torch

# Monkeypatch ROCm torch: provide GroupName if missing (needed by diffusers)
try:
    import torch.distributed.distributed_c10d as c10d
    if not hasattr(c10d, "GroupName"):
        from typing import NewType
        c10d.GroupName = NewType("GroupName", str)
except Exception:
    pass

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routes import router

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

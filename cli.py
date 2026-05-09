import typer
import httpx
import json
import asyncio
from typing import Optional

app = typer.Typer()

API_URL = "http://127.0.0.1:8000"

async def stream_events(project_id: str):
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("GET", f"{API_URL}/projects/{project_id}/events") as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    status = data.get("status")
                    current_step = data.get("current_step")
                    
                    if current_step:
                        step_info = data["steps"][current_step]
                        typer.echo(f"[{status.upper()}] Step: {current_step} - {step_info['message']} ({int(step_info['progress']*100)}%)")
                    else:
                        typer.echo(f"Project Status: {status}")

                    if status in ["completed", "failed"]:
                        break

@app.command()
def start(topic: str, style: str, quality: str = "medium"):
    """Start a new music video project."""
    async def run():
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{API_URL}/projects",
                    json={"topic": topic, "style": style, "quality": quality.lower()}
                )
                response.raise_for_status()
                project_id = response.json()["project_id"]
                typer.echo(f"Project started! ID: {project_id}")
                typer.echo("Waiting for updates...")
                await stream_events(project_id)
            except httpx.ConnectError:
                typer.echo("Error: Could not connect to the API. Make sure the server is running.")
            except Exception as e:
                typer.echo(f"An error occurred: {e}")

    asyncio.run(run())

if __name__ == "__main__":
    app()

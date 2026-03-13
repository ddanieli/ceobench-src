"""Deploy SaaS Bench sequence diagram to Modal as a static web app.

Usage:
    modal deploy deploy.py       # Deploy (persistent URL)
    modal serve deploy.py        # Dev mode (hot reload)
"""
import subprocess
from pathlib import Path

import modal

here = Path(__file__).parent

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("fastapi", "uvicorn[standard]")
    .add_local_file(here / "index.html", "/root/index.html", copy=True)
)

app = modal.App("saas-bench-diagram", image=image)

MINUTES = 60


@app.function(
    allow_concurrent_inputs=100,
    container_idle_timeout=10 * MINUTES,
)
@modal.web_server(port=8080, startup_timeout=30)
def serve():
    """Serve the static sequence diagram page via FastAPI."""
    server_code = r'''
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path

app = FastAPI()

HTML_CONTENT = Path("/root/index.html").read_text()

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_CONTENT

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
'''
    server_path = Path("/tmp/server.py")
    server_path.write_text(server_code)
    subprocess.Popen(["python", str(server_path)])

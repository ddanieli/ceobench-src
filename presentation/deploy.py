"""
SaaS Bench Presentation — Modal Deployment

Deploys a static Reveal.js presentation as a web endpoint on Modal.

Usage:
    modal deploy deploy.py       # Deploy persistent
    modal serve deploy.py        # Local dev with hot reload
"""

import modal
from pathlib import Path

app = modal.App("saasbench-slides")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("fastapi[standard]")
    .add_local_file(
        str(Path(__file__).parent / "index.html"),
        remote_path="/assets/index.html",
    )
)

@app.function(image=image)
@modal.concurrent(max_inputs=100)
@modal.fastapi_endpoint(method="GET")
def index():
    from fastapi.responses import HTMLResponse
    html = Path("/assets/index.html").read_text()
    return HTMLResponse(content=html)

"""Modal deployment for BossBench Trajectory Viewer."""
import modal

app = modal.App("bossbench-trajectory-viewer")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("fastapi[standard]")
    .add_local_dir(
        "/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench/viz",
        remote_path="/app/viz",
    )
)


@app.function(
    image=image,
    allow_concurrent_inputs=100,
    container_idle_timeout=3600,
)
@modal.asgi_app(label="bossbench-viz")
def web():
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    fastapi_app = FastAPI()

    @fastapi_app.get("/")
    async def index():
        return FileResponse("/app/viz/index.html")

    fastapi_app.mount("/data", StaticFiles(directory="/app/viz/data"), name="data")

    return fastapi_app

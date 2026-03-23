# Deploy: modal deploy serve.py
# Test:   modal run serve.py

import os
import subprocess
import time
from pathlib import Path

import modal
import modal.experimental

REPO_ID = "moonshotai/Kimi-K2.5"
GPU_TYPE = "H200"
GPU_COUNT = 8
SGLANG_PORT = 8000
MINUTES = 60

# Build image with SGLang (from latest main, has kimi_k2 parser)
image = (
    modal.Image.from_registry("lmsysorg/sglang:latest")
    .entrypoint([])
    .run_commands(
        "pip install nvidia-cudnn-cu12==9.16.0.29 || true",
    )
)

# Volumes for caching
hf_cache_path = "/root/.cache/huggingface"
hf_cache_vol = modal.Volume.from_name("huggingface-cache", create_if_missing=True)

# Download model weights at build time
def download_model(repo_id):
    from huggingface_hub import snapshot_download
    snapshot_download(repo_id=repo_id)

image = image.run_function(
    download_model,
    volumes={hf_cache_path: hf_cache_vol},
    secrets=[modal.Secret.from_name("huggingface-secret")],
    args=(REPO_ID,),
    timeout=7200,
)

# Environment variables
image = image.env({
    "HF_HUB_ENABLE_HF_TRANSFER": "1",
    "SGLANG_ALLOW_OVERWRITE_LONGER_CONTEXT_LEN": "1",
})

app = modal.App("kimi-k25-bossbench", image=image)


def _start_server() -> subprocess.Popen:
    """Start SGLang server in a subprocess."""
    cmd = [
        "HF_HUB_OFFLINE=1",
        "python", "-m", "sglang.launch_server",
        "--host", "0.0.0.0",
        "--port", str(SGLANG_PORT),
        "--model-path", REPO_ID,
        "--served-model-name", REPO_ID,
        "--tp", str(GPU_COUNT),
        "--trust-remote-code",
        "--tool-call-parser", "kimi_k2",
        "--reasoning-parser", "kimi_k2",
        "--mem-fraction-static", "0.85",
        "--chunked-prefill-size", "32768",
        "--moe-runner-backend", "triton",
    ]
    print("Starting SGLang server with command:")
    print(*cmd)
    return subprocess.Popen(" ".join(cmd), shell=True, start_new_session=True)


def _wait_for_server_ready():
    """Wait for SGLang server to be ready."""
    import requests
    url = f"http://localhost:{SGLANG_PORT}/health"
    print(f"Waiting for server to be ready at {url}")
    while True:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                print("Server is ready!")
                return
        except requests.exceptions.RequestException:
            pass
        time.sleep(5)


with image.imports():
    import sglang  # noqa


@app.cls(
    image=image,
    gpu=f"{GPU_TYPE}:{GPU_COUNT}",
    timeout=30 * MINUTES,
    volumes={hf_cache_path: hf_cache_vol},
    region="us",
    min_containers=1,
    max_containers=1,
)
@modal.experimental.http_server(
    port=SGLANG_PORT,
    proxy_regions=["us-east"],
    exit_grace_period=25,
)
@modal.concurrent(target_inputs=50)
class Server:
    @modal.enter()
    def start(self):
        """Start SGLang server process and wait for it to be ready."""
        self.proc = _start_server()
        _wait_for_server_ready()

    @modal.exit()
    def stop(self):
        """Terminate the SGLang server process."""
        self.proc.terminate()
        self.proc.wait()


@app.local_entrypoint()
def test():
    """Test the model serving endpoint."""
    import json
    url = Server._experimental_get_flash_urls()[0]
    print(f"Server URL: {url}")

    import urllib.request
    payload = json.dumps({
        "model": REPO_ID,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2? Reply in one word."},
        ],
        "max_tokens": 128,
    }).encode()
    req = urllib.request.Request(
        f"{url}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        result = json.loads(resp.read())
    print(f"Response: {result['choices'][0]['message']['content']}")

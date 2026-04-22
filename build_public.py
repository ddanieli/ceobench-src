#!/usr/bin/env python3
"""Build the public/ directory from source.

This is the single command to "rebuild the public repo". It:
1. Runs assertion checks (all tools mapped, all tables documented)
2. Compiles simulator engine to bytecode in public/_engine/saas_bench/
3. Copies novamind_api/ source (the Python SDK — readable by agent)
4. Renders latest docs from TOOL_DOCS and TABLE_DOCS
5. Creates the novamind-server launcher script

After running this, public/ is a fully self-contained directory.
An agent can run the simulation using only public/ — no other source needed.

Usage:
    uv run python build_public.py
"""

import json
import py_compile
import shutil
import stat
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent
PUBLIC_DIR = PROJECT_ROOT / "public"
SRC_DIR = PROJECT_ROOT / "src" / "saas_bench"

# All modules needed for the simulation engine (compiled to .pyc)
_ENGINE_MODULES = [
    "__init__",
    "api_server",
    "config",
    "customer_llm",
    "database",
    "db_protection",
    "docs_generator",
    "enterprise",
    "environment",
    "event_logger",
    "llm",
    "novamind_cli",
    "personas",
    "server_entry",
    "shocks",
    "simulation",
    "tools",
]

# novamind_api subpackage also needs compiled versions in engine
# (server_entry -> docs_generator -> novamind_cli -> novamind_api._client)
_ENGINE_API_MODULES = [
    "__init__",
    "_client",
    "analytics",
    "enterprise",
    "infrastructure",
    "market",
    "marketing",
    "pricing",
    "research",
]


def step(msg: str):
    print(f"\n{'='*60}\n  {msg}\n{'='*60}")


def build():
    # ── Step 1: Run assertion checks FIRST (fail fast) ──
    step("1. Running docs coverage checks")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_docs_coverage.py", "-v"],
        cwd=PROJECT_ROOT,
        capture_output=True, text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        print("\n❌ Docs coverage checks FAILED. Fix issues before rebuilding.")
        sys.exit(1)
    print("✅ All checks passed")

    # ── Step 2: Compile simulator engine to bytecode ──
    step("2. Compiling simulator engine to bytecode")
    engine_dir = PUBLIC_DIR / "_engine" / "saas_bench"
    if engine_dir.exists():
        shutil.rmtree(engine_dir)
    engine_dir.mkdir(parents=True)

    # Create a minimal __init__.py for the engine package (no heavy imports)
    _engine_init = engine_dir / "__init__.py"
    _engine_init.write_text('"""NovaMind simulation engine (compiled)."""\n__version__ = "0.1.0"\n')

    # Compile main modules
    compiled = 0
    for mod_name in _ENGINE_MODULES:
        if mod_name == "__init__":
            # Use the minimal init we just created, not the source one
            src_file = _engine_init
        else:
            src_file = SRC_DIR / f"{mod_name}.py"
        if not src_file.exists():
            print(f"  ⚠️  Missing: {src_file}")
            continue
        # Compile to .pyc — Python imports .pyc directly when no .py exists
        dst_file = engine_dir / f"{mod_name}.pyc"
        py_compile.compile(str(src_file), str(dst_file), doraise=True)
        compiled += 1

    # Remove the temporary .py init (only .pyc should remain)
    _engine_init.unlink()

    # Compile novamind_api subpackage
    engine_api_dir = engine_dir / "novamind_api"
    engine_api_dir.mkdir(parents=True)
    for mod_name in _ENGINE_API_MODULES:
        src_file = SRC_DIR / "novamind_api" / f"{mod_name}.py"
        if not src_file.exists():
            print(f"  ⚠️  Missing: {src_file}")
            continue
        dst_file = engine_api_dir / f"{mod_name}.pyc"
        py_compile.compile(str(src_file), str(dst_file), doraise=True)
        compiled += 1

    print(f"✅ Compiled {compiled} modules to bytecode in _engine/saas_bench/")

    # ── Step 3: Copy novamind_api/ source (readable SDK for agent) ──
    step("3. Copying novamind_api/ source (agent-readable SDK)")
    src_api = SRC_DIR / "novamind_api"
    dst_api = PUBLIC_DIR / "novamind_api"
    if dst_api.exists():
        shutil.rmtree(dst_api)
    shutil.copytree(
        src_api, dst_api,
        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'),
    )
    py_files = list(dst_api.glob("*.py"))
    print(f"✅ Copied {len(py_files)} files: {[f.name for f in py_files]}")

    # ── Step 4: Render docs ──
    step("4. Rendering docs from TOOL_DOCS and TABLE_DOCS")

    # Add source to path for imports
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    from saas_bench.docs_generator import render_api_docs, render_table_docs, render_cli_docs

    docs_dir = PUBLIC_DIR / "docs"

    # Clean existing generated docs (keep non-generated files like simulator-instructions.md)
    api_dir = docs_dir / "api"
    tables_dir = docs_dir / "tables"

    if api_dir.exists():
        shutil.rmtree(api_dir)
    if tables_dir.exists():
        shutil.rmtree(tables_dir)

    render_api_docs(api_dir)
    render_table_docs(tables_dir)
    render_cli_docs(docs_dir)

    api_files = list(api_dir.glob("*.json"))
    table_files = list(tables_dir.glob("*.json"))
    print(f"✅ API docs: {len(api_files)} modules → {[f.name for f in sorted(api_files)]}")
    print(f"✅ Table docs: {len(table_files)} tables")
    print(f"✅ CLI docs: docs/cli.md")

    # Verify no stale files (e.g., other.json from old builds)
    for f in api_dir.glob("*.json"):
        data = json.loads(f.read_text())
        if isinstance(data, list) and len(data) == 0:
            f.unlink()
            print(f"  Removed empty: {f.name}")

    # ── Step 5: Create novamind-server launcher ──
    step("5. Creating novamind-server launcher")
    _create_server_launcher()
    print("✅ Created novamind-server launcher script")

    # ── Step 6: Summary ──
    step("6. Build complete")
    print(f"public/ directory: {PUBLIC_DIR}")
    print(f"Contents:")
    for p in sorted(PUBLIC_DIR.rglob("*")):
        if "__pycache__" in str(p):
            continue
        rel = p.relative_to(PUBLIC_DIR)
        if p.is_file():
            print(f"  {rel}")

    print(f"\n✅ public/ is ready — fully self-contained simulation package.")
    print(f"   Agent-readable: novamind-operation, novamind_api/, docs/")
    print(f"   Compiled engine: _engine/saas_bench/ (bytecode, not readable)")


def _create_server_launcher():
    """Create the novamind-server script that launches the simulation engine."""
    launcher = PUBLIC_DIR / "novamind-server"
    launcher.write_text('''\
#!/usr/bin/env python3
"""NovaMind Simulation Server — launches the compiled simulation engine.

This script bootstraps the bytecode-compiled saas_bench package from _engine/
and delegates to server_entry.main(). It is invoked by ./novamind-operation.

The agent should NOT run this directly — use ./novamind-operation instead.
"""
import os
import sys

# Enforce PYTHONHASHSEED=0 so the simulator is deterministic across launches
# at the same --seed. Python reads PYTHONHASHSEED at interpreter startup, so
# if it's unset we must re-exec before any sim code loads.
if os.environ.get("PYTHONHASHSEED") != "0":
    os.environ["PYTHONHASHSEED"] = "0"
    os.execv(sys.executable, [sys.executable, __file__, *sys.argv[1:]])

from pathlib import Path

# Add _engine/ to Python path so 'from saas_bench.X import Y' resolves to .pyc files
_here = Path(__file__).resolve().parent
_engine = _here / "_engine"
if str(_engine) not in sys.path:
    sys.path.insert(0, str(_engine))

# Now import and run the server entry point (from compiled bytecode)
from saas_bench.server_entry import main
main()
''')
    # Make executable
    launcher.chmod(launcher.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


if __name__ == "__main__":
    build()

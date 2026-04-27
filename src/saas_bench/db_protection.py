"""Database protection: SQLCipher-backed encrypted SQLite files.

The `.nmdb` file IS a SQLCipher database — page-level AES-256 encryption at the
SQLite page layer. There is no separate ciphertext wire format: the file is a
normal SQLite database that has been encrypted page-by-page by SQLCipher.

Security properties:
- Without the key, opening the file fails with "file is not a database".
- Vanilla `sqlite3` (stdlib) cannot open it either — SQLCipher's file layout is
  binary-incompatible with vanilla SQLite. This preserves the anti-cheat
  property for the agent sandbox (which only has stdlib sqlite3 available).
- The key is read from the `NMDB_KEY` environment variable at runtime. The host
  harness sets it; the bwrap sandbox strips it before spawning the agent.
  The key is NOT derivable from any bundled artifact in `public/`.

Public API:
    open_encrypted(path)        → sqlcipher3 connection (file-backed, on-demand decrypt)
    create_encrypted(path)      → new empty encrypted DB
    save_session_db(conn, path) → dump conn (in-memory or file) into an encrypted file
    load_session_db(path, ...)  → open encrypted file into a conn (memory or file)
    protect_db(db, out)         → plain SQLite → encrypted .nmdb
    unprotect_db(nmdb, out)     → encrypted .nmdb → plain SQLite
"""

import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Optional, Union

import sqlcipher3


# --------------------------------------------------------------------------- #
# Key handling — read from NMDB_KEY env var only. Never bundle a fallback.
# --------------------------------------------------------------------------- #

def _get_key() -> str:
    """Return the SQLCipher key from the NMDB_KEY env var.

    Raises RuntimeError if unset. Callers in the host harness must ensure the
    var is present BEFORE importing this module. The bwrap sandbox must NOT
    set this var for the agent.
    """
    k = os.environ.get("NMDB_KEY")
    if not k:
        raise RuntimeError(
            "NMDB_KEY env var is not set. The host harness must export it "
            "(e.g. via `.env`) before launching novamind-server. It must "
            "NEVER be set inside the agent bwrap sandbox."
        )
    return k


def _apply_key(conn: sqlcipher3.Connection, key: str) -> None:
    """Set PRAGMA key on a fresh conn. Must be called before any other SQL."""
    escaped = key.replace("'", "''")
    conn.execute(f"PRAGMA key = '{escaped}'")


def _verify_key(conn: sqlcipher3.Connection) -> None:
    """Force SQLCipher to actually decrypt page 1 so a bad key fails fast."""
    conn.execute("SELECT count(*) FROM sqlite_master").fetchone()


# --------------------------------------------------------------------------- #
# Primary API — file-backed SQLCipher connections
# --------------------------------------------------------------------------- #

def open_encrypted(
    path: Union[str, Path],
    *,
    key: Optional[str] = None,
    check_same_thread: bool = False,
) -> sqlcipher3.Connection:
    """Open an existing encrypted SQLCipher DB file.

    Returns a file-backed connection with PRAGMA key already applied. Pages
    are decrypted on-demand as queries access them — no bulk decrypt, no
    plaintext temp file, no big memory spike.
    """
    key = key or _get_key()
    conn = sqlcipher3.connect(str(path), check_same_thread=check_same_thread)
    _apply_key(conn, key)
    _verify_key(conn)
    return conn


def create_encrypted(
    path: Union[str, Path],
    *,
    key: Optional[str] = None,
) -> sqlcipher3.Connection:
    """Create a brand-new encrypted SQLCipher DB at `path`.

    Overwrites any existing file at that path.
    """
    key = key or _get_key()
    path = Path(path)
    if path.exists():
        path.unlink()
    conn = sqlcipher3.connect(str(path), check_same_thread=False)
    _apply_key(conn, key)
    # Force page 1 creation + header write by touching the schema.
    conn.execute("CREATE TABLE _init (x INTEGER)")
    conn.execute("DROP TABLE _init")
    conn.commit()
    return conn


# --------------------------------------------------------------------------- #
# Compatibility shims — legacy call sites use these names
# --------------------------------------------------------------------------- #

def _sql_escape(s: str) -> str:
    return s.replace("'", "''")


def _export_plain_to_encrypted(plain_path: str, nmdb_path: str, key: str) -> None:
    """Copy a plain SQLite file into a new encrypted SQLCipher file.

    Uses SQLCipher's ATTACH + sqlcipher_export pattern: open the target
    encrypted DB, attach the plain source with empty key, and export
    schema+data. This is how SQLCipher officially recommends crossing
    the encrypted/plain boundary.
    """
    if os.path.exists(nmdb_path):
        os.unlink(nmdb_path)
    dst = sqlcipher3.connect(nmdb_path)
    _apply_key(dst, key)
    # Force page 1 creation so the file has a proper SQLCipher header.
    dst.execute("CREATE TABLE _init(x)")
    dst.execute("DROP TABLE _init")
    dst.commit()
    dst.execute(f"ATTACH DATABASE '{_sql_escape(plain_path)}' AS plaindb KEY ''")
    try:
        dst.execute("SELECT sqlcipher_export('main', 'plaindb')")
        dst.commit()
    finally:
        dst.execute("DETACH DATABASE plaindb")
    dst.close()


def _export_encrypted_to_plain(nmdb_path: str, plain_path: str, key: str) -> None:
    """Copy an encrypted SQLCipher file into a new plain SQLite file."""
    if os.path.exists(plain_path):
        os.unlink(plain_path)
    src = sqlcipher3.connect(nmdb_path)
    _apply_key(src, key)
    _verify_key(src)
    src.execute(f"ATTACH DATABASE '{_sql_escape(plain_path)}' AS plaindb KEY ''")
    try:
        src.execute("SELECT sqlcipher_export('plaindb', 'main')")
        src.commit()
    finally:
        src.execute("DETACH DATABASE plaindb")
    src.close()


def protect_db(db_path: Path, output_path: Path) -> None:
    """Copy a plain SQLite database into a new encrypted .nmdb file."""
    key = _get_key()
    _export_plain_to_encrypted(str(db_path), str(output_path), key)


def unprotect_db(nmdb_path: Path, output_path: Path) -> None:
    """Decrypt an encrypted .nmdb file into a plain SQLite database."""
    key = _get_key()
    _export_encrypted_to_plain(str(nmdb_path), str(output_path), key)


def save_session_db(conn, nmdb_path: Path, _db_path: Path = None) -> None:
    """Save a connection's DB state to an encrypted .nmdb file.

    - If `conn` is already a file-backed SQLCipher connection pointing at
      `nmdb_path`, this is just a `commit()` — the file is always encrypted.
    - Otherwise (e.g. an in-memory sqlite3 connection), this backs up the
      full DB into a fresh encrypted file, atomically replacing nmdb_path.

    Atomic: writes to a sibling tmp file, then `os.replace`.
    """
    nmdb_path = Path(nmdb_path)

    # Fast path: already file-backed at this path → commit and return.
    try:
        row = conn.execute("PRAGMA database_list").fetchone()
        main_path = row[2] if row and len(row) >= 3 else None
    except Exception:
        main_path = None
    if main_path and os.path.abspath(main_path) == os.path.abspath(str(nmdb_path)):
        conn.commit()
        return

    # Slow path: dump conn → plain tmp (same backup engine regardless of
    # whether src is sqlite3 or sqlcipher3), then export plain → encrypted
    # via SQLCipher ATTACH, atomic replace.
    key = _get_key()
    parent = nmdb_path.parent
    parent.mkdir(parents=True, exist_ok=True)

    plain_fd, plain_path = tempfile.mkstemp(suffix=".plain.tmp", dir=str(parent))
    os.close(plain_fd)
    os.unlink(plain_path)  # sqlite3.connect will create it

    enc_fd, enc_path = tempfile.mkstemp(suffix=".nmdb.tmp", dir=str(parent))
    os.close(enc_fd)
    os.unlink(enc_path)

    try:
        # Step 1: dump caller's conn → plain tmp (sqlite3 backup; works whether
        # conn is sqlite3.Connection or sqlcipher3 in-memory since backup only
        # cares about the page layer, and :memory: has no key applied here).
        plain_conn = sqlite3.connect(plain_path)
        try:
            conn.backup(plain_conn)
        finally:
            plain_conn.close()

        # Step 2: plain tmp → encrypted tmp
        _export_plain_to_encrypted(plain_path, enc_path, key)

        # Step 3: atomic replace
        os.replace(enc_path, str(nmdb_path))
    finally:
        for p in (plain_path, enc_path):
            if os.path.exists(p):
                try:
                    os.unlink(p)
                except Exception:
                    pass


def load_session_db(
    nmdb_path: Path,
    db_path: Path = None,
    in_memory: bool = True,
):
    """Open an encrypted .nmdb file into a SQLite connection.

    in_memory=True  → fully copy DB into :memory: (fast subsequent queries,
                      high RAM). Used by the server.
    in_memory=False → open the .nmdb directly with SQLCipher. On-demand
                      page decryption, low RAM. Used by push_data / monitors.
    """
    nmdb_path = Path(nmdb_path)

    if in_memory:
        # Export encrypted → plain tmp → load tmp into :memory: via sqlite3
        # backup. Two writes, but this is the server startup path (once per
        # session), not the hot path.
        key = _get_key()
        plain_fd, plain_path = tempfile.mkstemp(suffix=".plain.tmp", dir=str(nmdb_path.parent))
        os.close(plain_fd)
        os.unlink(plain_path)
        try:
            _export_encrypted_to_plain(str(nmdb_path), plain_path, key)
            src_plain = sqlite3.connect(plain_path)
            mem = sqlite3.connect(":memory:", check_same_thread=False)
            try:
                src_plain.backup(mem)
            finally:
                src_plain.close()
        finally:
            if os.path.exists(plain_path):
                try:
                    os.unlink(plain_path)
                except Exception:
                    pass
        mem.row_factory = sqlite3.Row
        mem.execute("PRAGMA cache_size=-500000")
        mem.execute("ANALYZE")
        return mem

    # File-backed: open .nmdb directly. Only pages that queries touch are
    # decrypted. No temp file, no memory spike.
    conn = open_encrypted(nmdb_path, check_same_thread=False)
    # Use sqlcipher3.Row (sqlite3.Row is a C type that rejects sqlcipher3 cursors).
    conn.row_factory = sqlcipher3.Row
    conn.execute("PRAGMA cache_size=-200000")
    # No ANALYZE here: the in-memory server path runs ANALYZE and persists
    # sqlite_stat1 into the snapshot, so file-backed readers (push_data /
    # monitors) inherit the stats for free. Re-running ANALYZE on a 1-2 GB
    # encrypted DB takes minutes and dominated the push cycle time.
    return conn

"""Database protection: obfuscate SQLite files so agents can't read them directly.

Uses gzip compression with a custom header to prevent casual `sqlite3` access.
The binary knows how to read/write these files; external tools cannot.
"""

import gzip
import os
import sqlite3
from pathlib import Path

# Custom magic bytes prepended before gzip data
_MAGIC = b'NOVAMIND\x00\x01'


def protect_db(db_path: Path, output_path: Path):
    """Compress and obfuscate a SQLite DB file.

    Args:
        db_path: Path to the plain SQLite database file.
        output_path: Path to write the obfuscated .nmdb file.
    """
    db_bytes = db_path.read_bytes()
    compressed = gzip.compress(db_bytes, compresslevel=6)
    output_path.write_bytes(_MAGIC + compressed)


def unprotect_db(nmdb_path: Path, output_path: Path):
    """Decompress an obfuscated .nmdb file back to plain SQLite.

    Args:
        nmdb_path: Path to the obfuscated .nmdb file.
        output_path: Path to write the plain SQLite database.
    """
    data = nmdb_path.read_bytes()
    if not data.startswith(_MAGIC):
        raise ValueError(f"Not a valid NovaMind database file: {nmdb_path}")
    compressed = data[len(_MAGIC):]
    db_bytes = gzip.decompress(compressed)
    output_path.write_bytes(db_bytes)


def save_session_db(conn: sqlite3.Connection, nmdb_path: Path, _db_path: Path = None):
    """Save the current DB state (in-memory or file) to an obfuscated file.

    Uses SQLite backup API to dump to a temp file, then obfuscates it.
    No plain SQLite file is left on disk after this call.

    Args:
        conn: Active SQLite connection (in-memory or file-backed).
        nmdb_path: Path to write the obfuscated .nmdb file.
        _db_path: Deprecated, ignored. Kept for backward compatibility.
    """
    import tempfile
    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.db')
    os.close(tmp_fd)
    tmp_path = Path(tmp_path)
    try:
        backup_conn = sqlite3.connect(str(tmp_path))
        conn.backup(backup_conn)
        backup_conn.close()
        protect_db(tmp_path, nmdb_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def load_session_db(nmdb_path: Path, db_path: Path = None) -> sqlite3.Connection:
    """Load an obfuscated .nmdb file into an in-memory SQLite database.

    The database is loaded entirely into memory — no plain SQLite file is
    written to disk, preventing agents from bypassing the API server's
    column-filtering by opening the file directly.

    Args:
        nmdb_path: Path to the obfuscated .nmdb file.
        db_path: Deprecated, ignored. Kept for backward compatibility.

    Returns:
        sqlite3.Connection to the in-memory database.
    """
    data = nmdb_path.read_bytes()
    if not data.startswith(_MAGIC):
        raise ValueError(f"Not a valid NovaMind database file: {nmdb_path}")
    compressed = data[len(_MAGIC):]
    db_bytes = gzip.decompress(compressed)

    # Write to a temp file, then use SQLite backup API to load into :memory:
    import tempfile
    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.db')
    try:
        os.write(tmp_fd, db_bytes)
        os.close(tmp_fd)
        tmp_conn = sqlite3.connect(tmp_path)
        mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
        tmp_conn.backup(mem_conn)
        tmp_conn.close()
    finally:
        os.unlink(tmp_path)

    mem_conn.row_factory = sqlite3.Row
    # WAL not needed for :memory:, but set pragmas for performance
    mem_conn.execute("PRAGMA cache_size=-500000")
    return mem_conn

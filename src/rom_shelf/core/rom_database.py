"""Improved ROM database with better concurrency and deadlock prevention."""

import hashlib
import json
import logging
import sqlite3
import threading
import time
import zlib
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from queue import Queue
from typing import Any

from ..utils.name_cleaner import extract_rom_metadata

# Database schema version
DATABASE_VERSION = 4


class FingerprintStatus(Enum):
    """Status of ROM fingerprint verification."""

    VALID = "valid"
    CHANGED = "changed"
    MISSING = "missing"
    CORRUPTED = "corrupted"


@dataclass
class ROMFingerprint:
    """Comprehensive fingerprint for ROM file integrity verification."""

    # Basic file properties
    file_path: str
    file_size: int
    modified_time: float

    # Content verification
    md5_hash: str | None = None
    header_hash: str = ""  # Hash of first 1KB for quick verification
    crc32: int = 0

    # Archive-specific data
    archive_path: str | None = None
    internal_path: str | None = None
    archive_modified_time: float | None = None

    # Metadata
    platform: str = ""
    region: str = ""
    revision: str = ""

    # Database metadata
    created_time: float = 0.0
    last_verified_time: float = 0.0
    verification_count: int = 0


class DatabaseConnectionPool:
    """SQLite connection pool for better concurrency."""

    def __init__(
        self,
        db_path: Path,
        max_connections: int = 10,
        timeout: float = 5.0,
    ):
        """Initialize connection pool.

        Args:
            db_path: Path to SQLite database file.
            max_connections: Maximum number of connections.
            timeout: Connection timeout in seconds.
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.max_connections = max_connections
        self.timeout = timeout

        # Connection pool
        self._connections: Queue = Queue(maxsize=max_connections)
        self._connection_count = 0
        self._lock = threading.Lock()

        # Initialize database
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Initialize SQLite database with WAL mode for better concurrency."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create initial connection to setup database
        conn = sqlite3.connect(str(self.db_path), timeout=self.timeout)

        try:
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")

            # Create tables
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rom_fingerprints (
                    file_key TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    modified_time REAL,
                    md5_hash TEXT,
                    header_hash TEXT,
                    crc32 INTEGER,
                    archive_path TEXT,
                    internal_path TEXT,
                    archive_modified_time REAL,
                    platform TEXT,
                    region TEXT,
                    revision TEXT,
                    created_time REAL,
                    last_verified_time REAL,
                    verification_count INTEGER,
                    data_json TEXT
                )
                """
            )

            # Create indexes for common queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_platform ON rom_fingerprints(platform)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_md5 ON rom_fingerprints(md5_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_file_path ON rom_fingerprints(file_path)")

            # Set database version
            conn.execute(
                "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                ("version", str(DATABASE_VERSION)),
            )

            conn.commit()
            self.logger.info(f"Database initialized at {self.db_path}")

        finally:
            conn.close()

    @contextmanager
    def get_connection(self) -> Iterator[sqlite3.Connection]:
        """Get a connection from the pool.

        Yields:
            SQLite connection.
        """
        conn = None
        try:
            # Try to get existing connection from pool
            try:
                conn = self._connections.get(block=False)
            except:
                conn = None

            # Create new connection if needed
            if conn is None:
                with self._lock:
                    if self._connection_count < self.max_connections:
                        conn = sqlite3.connect(
                            str(self.db_path),
                            timeout=self.timeout,
                            check_same_thread=False,
                        )
                        conn.row_factory = sqlite3.Row
                        self._connection_count += 1
                        self.logger.debug(
                            f"Created new connection (total: {self._connection_count})"
                        )
                    else:
                        # Wait for available connection
                        conn = self._connections.get(block=True, timeout=self.timeout)

            # Ensure connection is healthy
            try:
                conn.execute("SELECT 1")
            except sqlite3.Error:
                # Connection is broken, create new one
                conn.close()
                conn = sqlite3.connect(
                    str(self.db_path),
                    timeout=self.timeout,
                    check_same_thread=False,
                )
                conn.row_factory = sqlite3.Row

            yield conn

        finally:
            # Return connection to pool
            if conn:
                try:
                    self._connections.put(conn, block=False)
                except:
                    # Pool is full, close connection
                    conn.close()
                    with self._lock:
                        self._connection_count -= 1


class ROMDatabase:
    """Improved ROM database with SQLite backend and connection pooling."""

    def __init__(
        self,
        db_path: Path,
        max_connections: int = 10,
        enable_wal: bool = True,
        auto_vacuum: bool = True,
    ):
        """Initialize ROM database.

        Args:
            db_path: Path to database file.
            max_connections: Maximum database connections.
            enable_wal: Enable Write-Ahead Logging for better concurrency.
            auto_vacuum: Enable automatic database vacuuming.
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path if db_path.suffix == ".db" else db_path.with_suffix(".db")

        # Initialize connection pool
        self.pool = DatabaseConnectionPool(self.db_path, max_connections)

        # Performance tracking
        self._operation_counter = 0
        self._last_vacuum_time = time.time()
        self._vacuum_interval = 7 * 24 * 60 * 60  # 7 days

        # Auto vacuum configuration
        self.auto_vacuum = auto_vacuum

    def add_fingerprint(self, fingerprint: ROMFingerprint) -> bool:
        """Add or update ROM fingerprint in database.

        Args:
            fingerprint: ROM fingerprint to store.

        Returns:
            True if successful.
        """
        file_key = self._generate_file_key(
            Path(fingerprint.file_path),
            fingerprint.internal_path,
        )

        try:
            with self.pool.get_connection() as conn:
                self._save_fingerprint(conn, file_key, fingerprint)
                conn.commit()

                self._operation_counter += 1
                self._check_vacuum()

                return True

        except sqlite3.Error as e:
            self.logger.error(f"Failed to add fingerprint: {e}")
            return False

    def get_fingerprint(
        self,
        file_path: Path,
        internal_path: str | None = None,
    ) -> ROMFingerprint | None:
        """Get ROM fingerprint from database.

        Args:
            file_path: Path to ROM file or archive.
            internal_path: Path within archive if applicable.

        Returns:
            ROM fingerprint if found.
        """
        file_key = self._generate_file_key(file_path, internal_path)

        try:
            with self.pool.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM rom_fingerprints WHERE file_key = ?",
                    (file_key,),
                )
                row = cursor.fetchone()

                if row:
                    return self._row_to_fingerprint(row)

                return None

        except sqlite3.Error as e:
            self.logger.error(f"Failed to get fingerprint: {e}")
            return None

    def find_by_hash(self, md5_hash: str) -> list[ROMFingerprint]:
        """Find all ROMs with matching MD5 hash.

        Args:
            md5_hash: MD5 hash to search for.

        Returns:
            List of matching fingerprints.
        """
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM rom_fingerprints WHERE md5_hash = ?",
                    (md5_hash,),
                )
                return [self._row_to_fingerprint(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            self.logger.error(f"Failed to search by hash: {e}")
            return []

    def find_by_platform(self, platform: str) -> list[ROMFingerprint]:
        """Find all ROMs for a specific platform.

        Args:
            platform: Platform identifier.

        Returns:
            List of matching fingerprints.
        """
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM rom_fingerprints WHERE platform = ?",
                    (platform,),
                )
                return [self._row_to_fingerprint(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            self.logger.error(f"Failed to search by platform: {e}")
            return []

    def verify_fingerprint(self, file_path_or_fingerprint) -> FingerprintStatus:
        """Verify if a ROM file matches its stored fingerprint.

        Args:
            file_path_or_fingerprint: Path to ROM file OR ROMFingerprint object.

        Returns:
            Verification status.
        """
        # Handle both Path and ROMFingerprint arguments
        if isinstance(file_path_or_fingerprint, ROMFingerprint):
            # Called with fingerprint object
            fingerprint = file_path_or_fingerprint
            if not fingerprint or not fingerprint.file_path:
                return FingerprintStatus.MISSING
            file_path = Path(fingerprint.file_path)
            stored = fingerprint  # Use the provided fingerprint
        else:
            # Called with path
            file_path = file_path_or_fingerprint
            stored = self.get_fingerprint(file_path)

        # Continue with original logic

        if not stored:
            return FingerprintStatus.MISSING

        if not file_path.exists():
            return FingerprintStatus.MISSING

        try:
            # Quick check: file size
            current_size = file_path.stat().st_size
            if current_size != stored.file_size:
                return FingerprintStatus.CHANGED

            # Quick check: modification time
            current_mtime = file_path.stat().st_mtime
            if abs(current_mtime - stored.modified_time) > 1:  # Allow 1 second tolerance
                # File was modified, check header hash
                current_header = self._calculate_header_hash(file_path)
                if current_header != stored.header_hash:
                    return FingerprintStatus.CHANGED

            # Don't update database for unchanged files - this causes unnecessary writes
            # Only update when files actually change
            return FingerprintStatus.VALID

        except Exception as e:
            self.logger.error(f"Failed to verify fingerprint: {e}")
            return FingerprintStatus.CORRUPTED

    def batch_add_fingerprints(self, fingerprints: list[ROMFingerprint]) -> int:
        """Add multiple fingerprints in a single transaction.

        Args:
            fingerprints: List of fingerprints to add.

        Returns:
            Number of fingerprints successfully added.
        """
        added_count = 0

        try:
            with self.pool.get_connection() as conn:
                for fingerprint in fingerprints:
                    try:
                        file_key = self._generate_file_key(
                            Path(fingerprint.file_path),
                            fingerprint.internal_path,
                        )
                        self._save_fingerprint(conn, file_key, fingerprint)
                        added_count += 1

                    except Exception as e:
                        self.logger.error(
                            f"Failed to add fingerprint for {fingerprint.file_path}: {e}"
                        )

                conn.commit()
                self._operation_counter += added_count
                self._check_vacuum()

        except sqlite3.Error as e:
            self.logger.error(f"Batch add failed: {e}")

        return added_count

    def get_statistics(self) -> dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary with database statistics.
        """
        try:
            with self.pool.get_connection() as conn:
                total_cursor = conn.execute("SELECT COUNT(*) FROM rom_fingerprints")
                total_count = total_cursor.fetchone()[0]

                platform_cursor = conn.execute(
                    "SELECT platform, COUNT(*) FROM rom_fingerprints " "GROUP BY platform"
                )
                platform_counts = dict(platform_cursor.fetchall())

                # Get database file size
                db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

                return {
                    "total_roms": total_count,
                    "platforms": platform_counts,
                    "database_size": db_size,
                    "operations_since_vacuum": self._operation_counter,
                }

        except sqlite3.Error as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {}

    def create_rom_fingerprint(
        self,
        file_path: Path,
        internal_path: str | None = None,
        platform: str = "",
    ) -> ROMFingerprint:
        """Create a new ROM fingerprint.

        Args:
            file_path: Path to ROM file.
            internal_path: Path within archive if applicable.
            platform: Platform identifier.

        Returns:
            New ROM fingerprint.
        """
        try:
            # Get file stats
            file_stat = file_path.stat()

            # Calculate hashes
            header_hash = self._calculate_header_hash(file_path)
            md5_hash = self._calculate_md5(file_path, internal_path)
            crc32_value = self._calculate_crc32(file_path, internal_path)

            # Extract region and revision from filename using existing utility
            metadata = extract_rom_metadata(file_path.name)
            region = metadata.get("region", "")
            revision = metadata.get("revision", "")

            # Set archive path if this is an archive
            archive_path = None
            archive_modified_time = None
            if internal_path:
                # If there's an internal path, this is an archive
                archive_path = str(file_path)
                archive_modified_time = file_stat.st_mtime

            # Create fingerprint
            fingerprint = ROMFingerprint(
                file_path=str(file_path),
                file_size=file_stat.st_size,
                modified_time=file_stat.st_mtime,
                md5_hash=md5_hash,
                header_hash=header_hash,
                crc32=crc32_value,
                archive_path=archive_path,
                internal_path=internal_path,
                archive_modified_time=archive_modified_time,
                platform=platform,
                region=region,
                revision=revision,
                created_time=time.time(),
            )

            return fingerprint
        except Exception as e:
            self.logger.error(f"Failed to create fingerprint: {e}")
            # Return a minimal fingerprint
            return ROMFingerprint(
                file_path=str(file_path),
                file_size=0,
                modified_time=0,
                internal_path=internal_path,
                platform=platform,
                created_time=time.time(),
            )

    def vacuum(self) -> bool:
        """Vacuum database to reclaim space and optimize performance.

        Returns:
            True if successful.
        """
        try:
            with self.pool.get_connection() as conn:
                self.logger.info("Vacuuming database...")
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
                self._last_vacuum_time = time.time()
                self._operation_counter = 0
                self.logger.info("Database vacuum complete")
                return True

        except sqlite3.Error as e:
            self.logger.error(f"Vacuum failed: {e}")
            return False

    def _check_vacuum(self) -> None:
        """Check if database needs vacuuming."""
        if not self.auto_vacuum:
            return

        # Vacuum after significant operations or time interval
        if (
            self._operation_counter > 1000
            or (time.time() - self._last_vacuum_time) > self._vacuum_interval
        ):
            self.vacuum()

    def _generate_file_key(
        self,
        file_path: Path,
        internal_path: str | None = None,
    ) -> str:
        """Generate unique key for ROM entry.

        Args:
            file_path: Path to ROM file or archive.
            internal_path: Path within archive if applicable.

        Returns:
            Unique string key.
        """
        if internal_path:
            return f"{file_path.as_posix()}#{internal_path}"
        return file_path.as_posix()

    def _calculate_crc32(self, file_path: Path, internal_path: str | None = None) -> int:
        """Calculate CRC32 checksum of ROM file.

        Args:
            file_path: Path to ROM file or archive.
            internal_path: Path within archive if applicable.

        Returns:
            CRC32 checksum as integer.
        """
        try:
            crc32_value = 0
            buffer_size = 1024 * 1024  # 1MB buffer

            if internal_path:
                # Handle archive files
                archive_ext = file_path.suffix.lower()

                if archive_ext == ".zip":
                    import zipfile

                    with zipfile.ZipFile(file_path, "r") as zip_file:
                        with zip_file.open(internal_path) as rom_file:
                            while chunk := rom_file.read(buffer_size):
                                crc32_value = zlib.crc32(chunk, crc32_value)
                elif archive_ext == ".7z":
                    try:
                        import py7zr

                        with py7zr.SevenZipFile(file_path, mode="r") as archive:
                            extracted = archive.read([internal_path])
                            if internal_path in extracted:
                                data = extracted[internal_path].read()
                                crc32_value = zlib.crc32(data)
                    except ImportError:
                        self.logger.warning("py7zr not available for 7z CRC32 calculation")
                        return 0
                elif archive_ext == ".rar":
                    try:
                        import rarfile

                        with rarfile.RarFile(file_path) as rar_file:
                            with rar_file.open(internal_path) as rom_file:
                                while chunk := rom_file.read(buffer_size):
                                    crc32_value = zlib.crc32(chunk, crc32_value)
                    except ImportError:
                        self.logger.warning("rarfile not available for RAR CRC32 calculation")
                        return 0
                else:
                    return 0
            else:
                # Handle direct files with buffered reading
                with open(file_path, "rb") as f:
                    while chunk := f.read(buffer_size):
                        crc32_value = zlib.crc32(chunk, crc32_value)

            # CRC32 can be negative in Python, convert to unsigned
            return crc32_value & 0xFFFFFFFF

        except Exception as e:
            self.logger.error(f"Failed to calculate CRC32 for {file_path}: {e}")
            return 0

    def _calculate_header_hash(self, file_path: Path) -> str:
        """Calculate hash of first 1KB for quick verification.

        Args:
            file_path: Path to file.

        Returns:
            SHA256 hash of header.
        """
        try:
            with open(file_path, "rb") as f:
                header_data = f.read(1024)
            return hashlib.sha256(header_data).hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to calculate header hash: {e}")
            return ""

    def _calculate_md5(self, file_path: Path, internal_path: str | None = None) -> str:
        """Calculate MD5 hash of ROM file.

        Args:
            file_path: Path to ROM file or archive.
            internal_path: Path within archive if applicable.

        Returns:
            MD5 hash as hex string.
        """
        try:
            md5_hash = hashlib.md5()
            buffer_size = 1024 * 1024  # 1MB buffer

            if internal_path:
                # Handle archive files
                archive_ext = file_path.suffix.lower()

                if archive_ext == ".zip":
                    import zipfile

                    with zipfile.ZipFile(file_path, "r") as zip_file:
                        with zip_file.open(internal_path) as rom_file:
                            while chunk := rom_file.read(buffer_size):
                                md5_hash.update(chunk)
                elif archive_ext == ".7z":
                    try:
                        import py7zr

                        with py7zr.SevenZipFile(file_path, mode="r") as archive:
                            extracted = archive.read([internal_path])
                            if internal_path in extracted:
                                data = extracted[internal_path].read()
                                md5_hash.update(data)
                    except ImportError:
                        self.logger.warning("py7zr not available for 7z MD5 calculation")
                        return ""
                elif archive_ext == ".rar":
                    try:
                        import rarfile

                        with rarfile.RarFile(file_path) as rar_file:
                            with rar_file.open(internal_path) as rom_file:
                                while chunk := rom_file.read(buffer_size):
                                    md5_hash.update(chunk)
                    except ImportError:
                        self.logger.warning("rarfile not available for RAR MD5 calculation")
                        return ""
                else:
                    return ""
            else:
                # Handle direct files with buffered reading
                with open(file_path, "rb") as f:
                    while chunk := f.read(buffer_size):
                        md5_hash.update(chunk)

            return md5_hash.hexdigest()

        except Exception as e:
            self.logger.error(f"Failed to calculate MD5 for {file_path}: {e}")
            return ""

    def _save_fingerprint(
        self,
        conn: sqlite3.Connection,
        file_key: str,
        fingerprint: ROMFingerprint,
    ) -> None:
        """Save fingerprint to database.

        Args:
            conn: Database connection.
            file_key: Unique file key.
            fingerprint: ROM fingerprint to save.
        """
        data_json = json.dumps(asdict(fingerprint))

        conn.execute(
            """
            INSERT OR REPLACE INTO rom_fingerprints (
                file_key, file_path, file_size, modified_time,
                md5_hash, header_hash, crc32,
                archive_path, internal_path, archive_modified_time,
                platform, region, revision,
                created_time, last_verified_time, verification_count,
                data_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                file_key,
                fingerprint.file_path,
                fingerprint.file_size,
                fingerprint.modified_time,
                fingerprint.md5_hash,
                fingerprint.header_hash,
                fingerprint.crc32,
                fingerprint.archive_path,
                fingerprint.internal_path,
                fingerprint.archive_modified_time,
                fingerprint.platform,
                fingerprint.region,
                fingerprint.revision,
                fingerprint.created_time,
                fingerprint.last_verified_time,
                fingerprint.verification_count,
                data_json,
            ),
        )

    def _row_to_fingerprint(self, row: sqlite3.Row) -> ROMFingerprint:
        """Convert database row to ROMFingerprint.

        Args:
            row: Database row.

        Returns:
            ROMFingerprint object.
        """
        return ROMFingerprint(
            file_path=row["file_path"],
            file_size=row["file_size"],
            modified_time=row["modified_time"],
            md5_hash=row["md5_hash"],
            header_hash=row["header_hash"],
            crc32=row["crc32"],
            archive_path=row["archive_path"],
            internal_path=row["internal_path"],
            archive_modified_time=row["archive_modified_time"],
            platform=row["platform"],
            region=row["region"],
            revision=row["revision"],
            created_time=row["created_time"],
            last_verified_time=row["last_verified_time"],
            verification_count=row["verification_count"],
        )

    def close(self) -> None:
        """Close all database connections."""
        # Close all pooled connections
        while not self.pool._connections.empty():
            try:
                conn = self.pool._connections.get(block=False)
                conn.close()
            except:
                break

        self.logger.info("Database connections closed")


# Global instance
_global_database: ROMDatabase | None = None


def get_rom_database() -> ROMDatabase:
    """Get the global ROM database instance.

    Returns:
        The singleton ROM database instance.
    """
    global _global_database
    if _global_database is None:
        db_path = Path("data") / "romshelf.db"
        _global_database = ROMDatabase(db_path)
    return _global_database

"""ROM database for caching ROM metadata and hashes with integrity verification."""

import hashlib
import json
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

# Database schema version - increment when breaking changes are made
DATABASE_VERSION = 3
COMPATIBLE_VERSIONS = [3]  # Versions that can be loaded without rebuild


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


class ROMDatabase:
    """Sophisticated ROM database with integrity verification."""

    def __init__(self, db_path: Path) -> None:
        """Initialize ROM database.

        Args:
            db_path: Path to database JSON file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, dict[str, Any]] = {}
        self._dirty = False
        self._save_lock = threading.Lock()
        self._data_lock = threading.RLock()
        self._last_save_time = 0.0
        self._min_save_interval = 5.0  # Minimum 5 seconds between saves
        self._load_database()

    def _load_database(self) -> None:
        """Load database from disk with version checking."""
        try:
            if self.db_path.exists():
                with open(self.db_path, encoding='utf-8') as f:
                    data = json.load(f)

                # Validate database structure
                if not isinstance(data, dict):
                    print(f"Invalid database format in {self.db_path}, starting fresh")
                    self._data = {}
                    return

                # Check database version
                db_version = data.get('version', 1)  # Default to version 1 for old databases
                if db_version not in COMPATIBLE_VERSIONS:
                    print(f"Database version {db_version} is incompatible with current version "
                          f"{DATABASE_VERSION}")
                    print("Database will be rebuilt to update schema")
                    self._data = {}
                    # Mark for rebuild by removing the old file
                    self.db_path.unlink(missing_ok=True)
                    return

                # Load ROM entries
                self._data = data.get('roms', {})
                print(f"Loaded ROM database v{db_version} with {len(self._data)} entries")
            else:
                self._data = {}
                print("Created new ROM database")

        except Exception as e:
            print(f"Error loading ROM database: {e}")
            self._data = {}

    def save_database(self, force: bool = False) -> bool:
        """Save database to disk with rate limiting and thread safety.

        Args:
            force: Force save even if rate limited

        Returns:
            True if saved successfully, False if skipped or failed
        """
        current_time = time.time()

        # Rate limiting check
        if not force and (current_time - self._last_save_time) < self._min_save_interval:
            self._dirty = True  # Mark for future save
            return False

        with self._save_lock:
            # Double-check pattern
            if not force and (time.time() - self._last_save_time) < self._min_save_interval:
                self._dirty = True
                return False

            try:
                with self._data_lock:
                    # Prepare data structure
                    db_data = {
                        'version': DATABASE_VERSION,
                        'created_time': time.time(),
                        'roms': self._data.copy()  # Create copy to avoid race conditions
                    }

                # Use unique temp file name to avoid conflicts
                temp_name = f"rom_database_{uuid.uuid4().hex[:8]}.tmp"
                temp_path = self.db_path.parent / temp_name

                # Write to temp file
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(db_data, f, indent=2, sort_keys=True)

                # Try to replace main database file
                try:
                    # On Windows, remove target first if it exists
                    if self.db_path.exists():
                        # Try a few times in case of temporary locks
                        for attempt in range(3):
                            try:
                                temp_path.replace(self.db_path)
                                break
                            except (OSError, PermissionError) as e:
                                if attempt == 2:  # Last attempt
                                    raise e
                                time.sleep(0.1)  # Brief pause
                    else:
                        temp_path.replace(self.db_path)

                    self._last_save_time = time.time()
                    self._dirty = False
                    return True

                except (OSError, PermissionError) as e:
                    # Clean up temp file on failure
                    try:
                        temp_path.unlink()
                    except:
                        pass
                    raise e

            except Exception as e:
                print(f"Error saving ROM database: {e}")
                return False

    def _generate_file_key(self, file_path: Path, internal_path: str | None = None) -> str:
        """Generate unique key for ROM entry.

        Args:
            file_path: Path to ROM file or archive
            internal_path: Path within archive if applicable

        Returns:
            Unique string key for database indexing
        """
        if internal_path:
            return f"{file_path.as_posix()}#{internal_path}"
        return file_path.as_posix()

    def _calculate_header_hash(self, file_path: Path, internal_path: str | None = None) -> str:
        """Calculate hash of first 1KB for quick file verification.

        Args:
            file_path: Path to ROM file or archive
            internal_path: Path within archive if applicable

        Returns:
            SHA256 hash of first 1KB
        """
        try:
            if internal_path:
                # Handle archive files - simplified without hash calculator
                import zipfile

                import py7zr
                import rarfile

                archive_ext = file_path.suffix.lower()
                header_data = b""

                try:
                    if archive_ext == '.zip':
                        with zipfile.ZipFile(file_path, 'r') as zip_file:
                            with zip_file.open(internal_path) as rom_file:
                                header_data = rom_file.read(1024)
                    elif archive_ext == '.7z':
                        with py7zr.SevenZipFile(file_path, mode='r') as archive:
                            extracted = archive.read([internal_path])
                            if internal_path in extracted:
                                data = extracted[internal_path].read()
                                header_data = data[:1024] if data else b""
                    elif archive_ext == '.rar':
                        with rarfile.RarFile(file_path) as rar_file:
                            with rar_file.open(internal_path) as rom_file:
                                header_data = rom_file.read(1024)
                except:
                    return ""
            else:
                # Handle direct files
                with open(file_path, 'rb') as f:
                    header_data = f.read(1024)

            return hashlib.sha256(header_data).hexdigest()

        except Exception:
            return ""

    def _calculate_md5(self, file_path: Path, internal_path: str | None = None) -> str:
        """Calculate MD5 hash of ROM file with optimized buffering.

        Args:
            file_path: Path to ROM file or archive
            internal_path: Path within archive if applicable

        Returns:
            MD5 hash as hex string
        """
        try:
            md5_hash = hashlib.md5()
            # Use larger buffer for better I/O performance
            buffer_size = 1024 * 1024  # 1MB buffer

            if internal_path:
                # Handle archive files
                archive_ext = file_path.suffix.lower()

                try:
                    if archive_ext == '.zip':
                        import zipfile
                        with zipfile.ZipFile(file_path, 'r') as zip_file:
                            with zip_file.open(internal_path) as rom_file:
                                while chunk := rom_file.read(buffer_size):
                                    md5_hash.update(chunk)
                    elif archive_ext == '.7z':
                        import py7zr
                        with py7zr.SevenZipFile(file_path, mode='r') as archive:
                            extracted = archive.read([internal_path])
                            if internal_path in extracted:
                                data = extracted[internal_path].read()
                                md5_hash.update(data)
                    elif archive_ext == '.rar':
                        import rarfile
                        with rarfile.RarFile(file_path) as rar_file:
                            with rar_file.open(internal_path) as rom_file:
                                while chunk := rom_file.read(buffer_size):
                                    md5_hash.update(chunk)
                except Exception:
                    return ""
            else:
                # Handle direct files with buffered reading
                with open(file_path, 'rb') as f:
                    while chunk := f.read(buffer_size):
                        md5_hash.update(chunk)

            return md5_hash.hexdigest()

        except Exception:
            return ""

    def _calculate_crc32(self, file_path: Path, internal_path: str | None = None) -> int:
        """Calculate CRC32 checksum for additional verification with optimized buffering.

        Args:
            file_path: Path to ROM file or archive
            internal_path: Path within archive if applicable

        Returns:
            CRC32 checksum as integer
        """
        try:
            import zipfile
            import zlib

            import py7zr
            import rarfile

            # Use larger buffer for better I/O performance
            buffer_size = 1024 * 1024  # 1MB buffer

            if internal_path:
                # Handle archive files - simplified without hash calculator
                archive_ext = file_path.suffix.lower()

                try:
                    if archive_ext == '.zip':
                        with zipfile.ZipFile(file_path, 'r') as zip_file:
                            with zip_file.open(internal_path) as rom_file:
                                crc = 0
                                while chunk := rom_file.read(buffer_size):
                                    crc = zlib.crc32(chunk, crc)
                                return crc & 0xffffffff
                    elif archive_ext == '.7z':
                        with py7zr.SevenZipFile(file_path, mode='r') as archive:
                            extracted = archive.read([internal_path])
                            if internal_path in extracted:
                                data = extracted[internal_path].read()
                                return zlib.crc32(data) & 0xffffffff if data else 0
                    elif archive_ext == '.rar':
                        with rarfile.RarFile(file_path) as rar_file:
                            with rar_file.open(internal_path) as rom_file:
                                crc = 0
                                while chunk := rom_file.read(buffer_size):
                                    crc = zlib.crc32(chunk, crc)
                                return crc & 0xffffffff
                except:
                    return 0
            else:
                # Handle direct files with larger buffer
                crc = 0
                with open(file_path, 'rb') as f:
                    while chunk := f.read(buffer_size):
                        crc = zlib.crc32(chunk, crc)
                return crc & 0xffffffff  # Ensure unsigned 32-bit

        except Exception:
            return 0

    def verify_fingerprint(self, fingerprint: ROMFingerprint) -> FingerprintStatus:
        """Verify ROM fingerprint against current file state.

        Args:
            fingerprint: Stored ROM fingerprint

        Returns:
            Verification status
        """
        try:
            file_path = Path(fingerprint.file_path)

            # Check if file exists
            if not file_path.exists():
                return FingerprintStatus.MISSING

            # Check archive-specific logic
            if fingerprint.archive_path:
                archive_path = Path(fingerprint.archive_path)
                if not archive_path.exists():
                    return FingerprintStatus.MISSING

                # Check archive modification time
                current_archive_mtime = archive_path.stat().st_mtime
                if abs(current_archive_mtime - (fingerprint.archive_modified_time or 0)) > 1.0:
                    return FingerprintStatus.CHANGED

            # Quick checks first
            current_size = file_path.stat().st_size
            current_mtime = file_path.stat().st_mtime

            # File size changed - definitely modified
            if current_size != fingerprint.file_size:
                return FingerprintStatus.CHANGED

            # Modification time changed significantly (>1 second tolerance)
            if abs(current_mtime - fingerprint.modified_time) > 1.0:
                # Additional verification with header hash
                current_header_hash = self._calculate_header_hash(
                    file_path, fingerprint.internal_path
                )
                if current_header_hash and current_header_hash != fingerprint.header_hash:
                    return FingerprintStatus.CHANGED

            # All checks passed
            return FingerprintStatus.VALID

        except Exception as e:
            print(f"Error verifying fingerprint for {fingerprint.file_path}: {e}")
            return FingerprintStatus.CORRUPTED

    def get_rom_fingerprint(self, file_path: Path, internal_path: str | None = None) -> ROMFingerprint | None:
        """Get stored ROM fingerprint.

        Args:
            file_path: Path to ROM file or archive
            internal_path: Path within archive if applicable

        Returns:
            ROM fingerprint if found, None otherwise
        """
        key = self._generate_file_key(file_path, internal_path)

        with self._data_lock:
            if key in self._data:
                try:
                    data = self._data[key]
                    return ROMFingerprint(**data)
                except Exception as e:
                    print(f"Error loading fingerprint for {key}: {e}")
                    # Remove corrupted entry
                    del self._data[key]
                    self._dirty = True

            return None

    def store_rom_fingerprint(self, fingerprint: ROMFingerprint) -> None:
        """Store ROM fingerprint in database.

        Args:
            fingerprint: ROM fingerprint to store
        """
        key = self._generate_file_key(Path(fingerprint.file_path), fingerprint.internal_path)

        # Update timestamps
        current_time = time.time()
        fingerprint.last_verified_time = current_time
        if fingerprint.created_time == 0.0:
            fingerprint.created_time = current_time
        fingerprint.verification_count += 1

        # Store in database
        with self._data_lock:
            self._data[key] = asdict(fingerprint)
            self._dirty = True

    def create_rom_fingerprint(
        self,
        file_path: Path,
        internal_path: str | None = None,
        md5_hash: str | None = None,
        platform: str = "",
        quick_mode: bool = False
    ) -> ROMFingerprint:
        """Create comprehensive ROM fingerprint.

        Args:
            file_path: Path to ROM file or archive
            internal_path: Path within archive if applicable
            md5_hash: Pre-calculated MD5 hash (optional)
            platform: ROM platform identifier
            quick_mode: Skip expensive operations like CRC32

        Returns:
            Complete ROM fingerprint
        """
        current_time = time.time()

        # Basic file information
        stat = file_path.stat()

        fingerprint = ROMFingerprint(
            file_path=str(file_path),
            file_size=stat.st_size,
            modified_time=stat.st_mtime,
            md5_hash=md5_hash,
            platform=platform,
            internal_path=internal_path,
            created_time=current_time,
            last_verified_time=current_time,
            verification_count=1
        )

        # Archive-specific data
        if internal_path:
            fingerprint.archive_path = str(file_path)
            fingerprint.archive_modified_time = stat.st_mtime
            # Keep file_path as the original archive path, don't modify it

        # Calculate verification hashes
        fingerprint.header_hash = self._calculate_header_hash(file_path, internal_path)

        if not quick_mode:
            fingerprint.crc32 = self._calculate_crc32(file_path, internal_path)

        # Calculate MD5 hash if not provided
        if not fingerprint.md5_hash:
            fingerprint.md5_hash = self._calculate_md5(file_path, internal_path)

        return fingerprint


    def get_cached_md5(self, file_path: Path, internal_path: str | None = None) -> str | None:
        """Get cached MD5 hash if file hasn't changed.

        Args:
            file_path: Path to ROM file or archive
            internal_path: Path within archive if applicable

        Returns:
            Cached MD5 hash if valid, None otherwise
        """
        fingerprint = self.get_rom_fingerprint(file_path, internal_path)

        if not fingerprint:
            return None

        status = self.verify_fingerprint(fingerprint)
        if status == FingerprintStatus.VALID and fingerprint.md5_hash:
            return fingerprint.md5_hash

        return None


    def cleanup_missing_roms(self) -> int:
        """Remove database entries for ROMs that no longer exist.

        Returns:
            Number of entries removed
        """
        removed_count = 0
        keys_to_remove = []

        for key, data in self._data.items():
            try:
                fingerprint = ROMFingerprint(**data)
                if self.verify_fingerprint(fingerprint) == FingerprintStatus.MISSING:
                    keys_to_remove.append(key)
            except Exception:
                keys_to_remove.append(key)  # Remove corrupted entries too

        for key in keys_to_remove:
            del self._data[key]
            removed_count += 1

        return removed_count

    def flush_if_dirty(self) -> bool:
        """Save database if it has pending changes.

        Returns:
            True if saved, False if not dirty or save failed
        """
        if self._dirty:
            return self.save_database(force=True)
        return False

    def get_statistics(self) -> dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary with database statistics
        """
        total_entries = len(self._data)
        platforms = {}

        for data in self._data.values():
            try:
                fingerprint = ROMFingerprint(**data)

                # Count by platform
                platform = fingerprint.platform or "unknown"
                platforms[platform] = platforms.get(platform, 0) + 1

            except Exception:
                continue

        return {
            'total_entries': total_entries,
            'platforms': platforms,
            'database_size_mb': self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
        }


# Global database instance
_rom_database: ROMDatabase | None = None


def get_rom_database() -> ROMDatabase:
    """Get global ROM database instance."""
    global _rom_database
    if _rom_database is None:
        db_path = Path("data") / "rom_database.json"
        _rom_database = ROMDatabase(db_path)
    return _rom_database

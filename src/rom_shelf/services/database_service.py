"""Database service - abstraction layer for ROM database operations."""

from pathlib import Path
from typing import Any

from ..core.rom_database import FingerprintStatus, ROMDatabase, get_rom_database


class DatabaseService:
    """Service for ROM database operations and integrity management."""

    def __init__(self, database: ROMDatabase | None = None) -> None:
        """Initialize the database service."""
        self._database = database or get_rom_database()

    @property
    def database(self) -> ROMDatabase:
        """Get the underlying database instance."""
        return self._database

    # Fingerprint Operations
    def get_fingerprint(
        self, file_path: str, internal_path: str | None = None
    ) -> dict[str, Any] | None:
        """Get fingerprint data for a file."""
        try:
            return self._database.get_fingerprint_data(file_path, internal_path)
        except Exception as e:
            print(f"Error getting fingerprint for {file_path}: {e}")
            return None

    def create_fingerprint(self, file_path: str, internal_path: str | None = None) -> str | None:
        """Create a new fingerprint for a file."""
        try:
            fingerprint_data = self._database.get_or_create_fingerprint(file_path, internal_path)
            if fingerprint_data["status"] == FingerprintStatus.SUCCESS:
                return fingerprint_data["fingerprint"]
            return None
        except Exception as e:
            print(f"Error creating fingerprint for {file_path}: {e}")
            return None

    def get_or_create_fingerprint(
        self, file_path: str, internal_path: str | None = None
    ) -> dict[str, Any]:
        """Get existing fingerprint or create new one."""
        try:
            return self._database.get_or_create_fingerprint(file_path, internal_path)
        except Exception as e:
            print(f"Error with fingerprint for {file_path}: {e}")
            return {"fingerprint": None, "status": FingerprintStatus.ERROR, "error": str(e)}

    def remove_fingerprint(self, file_path: str, internal_path: str | None = None) -> bool:
        """Remove a fingerprint from the database."""
        try:
            key = self._database._get_file_key(file_path, internal_path)
            if key in self._database.fingerprints:
                del self._database.fingerprints[key]
                return True
            return False
        except Exception as e:
            print(f"Error removing fingerprint for {file_path}: {e}")
            return False

    def cleanup_missing_files(self) -> int:
        """Remove fingerprints for files that no longer exist."""
        removed_count = 0

        try:
            keys_to_remove = []

            for key, fingerprint_data in self._database.fingerprints.items():
                file_path = fingerprint_data.get("file_path")
                if file_path:
                    path = Path(file_path)
                    if not path.exists():
                        keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._database.fingerprints[key]
                removed_count += 1

            if removed_count > 0:
                self.save_database()
                print(f"Cleaned up {removed_count} missing file fingerprints")

        except Exception as e:
            print(f"Error during cleanup: {e}")

        return removed_count

    def refresh_fingerprint(self, file_path: str, internal_path: str | None = None) -> bool:
        """Force refresh of a fingerprint."""
        try:
            # Remove existing fingerprint
            self.remove_fingerprint(file_path, internal_path)

            # Create new fingerprint
            result = self.create_fingerprint(file_path, internal_path)
            return result is not None

        except Exception as e:
            print(f"Error refreshing fingerprint for {file_path}: {e}")
            return False

    # Database Management
    def save_database(self) -> bool:
        """Save the database to disk."""
        try:
            self._database.save()
            return True
        except Exception as e:
            print(f"Error saving database: {e}")
            return False

    def get_database_info(self) -> dict[str, Any]:
        """Get information about the database."""
        try:
            stats = {
                "total_fingerprints": len(self._database.fingerprints),
                "database_version": getattr(self._database, "version", "unknown"),
                "database_file": str(self._database.db_file),
                "database_exists": self._database.db_file.exists(),
            }

            # File type statistics
            file_types = {}
            missing_files = 0
            error_fingerprints = 0

            for fingerprint_data in self._database.fingerprints.values():
                file_path = fingerprint_data.get("file_path")

                if file_path:
                    path = Path(file_path)
                    if path.exists():
                        extension = path.suffix.lower()
                        file_types[extension] = file_types.get(extension, 0) + 1
                    else:
                        missing_files += 1

                if fingerprint_data.get("status") == FingerprintStatus.ERROR:
                    error_fingerprints += 1

            stats.update(
                {
                    "file_types": dict(
                        sorted(file_types.items(), key=lambda x: x[1], reverse=True)
                    ),
                    "missing_files": missing_files,
                    "error_fingerprints": error_fingerprints,
                }
            )

            return stats

        except Exception as e:
            return {"error": f"Error getting database info: {e}"}

    def verify_database_integrity(self) -> dict[str, Any]:
        """Verify database integrity and return report."""
        report = {
            "total_entries": 0,
            "valid_entries": 0,
            "missing_files": 0,
            "error_entries": 0,
            "corrupted_entries": 0,
            "issues": [],
        }

        try:
            report["total_entries"] = len(self._database.fingerprints)

            for key, fingerprint_data in self._database.fingerprints.items():
                file_path = fingerprint_data.get("file_path")

                # Check for corrupted entries
                if not isinstance(fingerprint_data, dict):
                    report["corrupted_entries"] += 1
                    report["issues"].append(f"Corrupted entry: {key}")
                    continue

                # Check for error status
                if fingerprint_data.get("status") == FingerprintStatus.ERROR:
                    report["error_entries"] += 1
                    report["issues"].append(f"Error entry: {file_path}")
                    continue

                # Check if file exists
                if file_path:
                    path = Path(file_path)
                    if not path.exists():
                        report["missing_files"] += 1
                        report["issues"].append(f"Missing file: {file_path}")
                        continue

                report["valid_entries"] += 1

        except Exception as e:
            report["issues"].append(f"Error during integrity check: {e}")

        return report

    def compact_database(self) -> dict[str, Any]:
        """Compact the database by removing invalid entries."""
        result = {
            "entries_before": len(self._database.fingerprints),
            "entries_removed": 0,
            "entries_after": 0,
            "success": False,
        }

        try:
            keys_to_remove = []

            for key, fingerprint_data in self._database.fingerprints.items():
                should_remove = False

                # Remove entries with missing files
                file_path = fingerprint_data.get("file_path")
                if (
                    file_path
                    and not Path(file_path).exists()
                    or fingerprint_data.get("status") == FingerprintStatus.ERROR
                    or not isinstance(fingerprint_data, dict)
                    or "fingerprint" not in fingerprint_data
                ):
                    should_remove = True

                if should_remove:
                    keys_to_remove.append(key)

            # Remove identified entries
            for key in keys_to_remove:
                del self._database.fingerprints[key]

            result["entries_removed"] = len(keys_to_remove)
            result["entries_after"] = len(self._database.fingerprints)

            # Save compacted database
            if keys_to_remove:
                self.save_database()

            result["success"] = True

        except Exception as e:
            result["error"] = str(e)

        return result

    def export_database(self, export_path: Path) -> bool:
        """Export database to a different location."""
        try:
            # Create a copy of the database at the export location
            export_db = ROMDatabase(export_path)
            export_db.fingerprints = self._database.fingerprints.copy()
            export_db.save()
            return True

        except Exception as e:
            print(f"Error exporting database to {export_path}: {e}")
            return False

    def import_database(self, import_path: Path, merge: bool = True) -> bool:
        """Import database from another location."""
        try:
            if not import_path.exists():
                return False

            import_db = ROMDatabase(import_path)

            if merge:
                # Merge with existing database
                for key, fingerprint_data in import_db.fingerprints.items():
                    if key not in self._database.fingerprints:
                        self._database.fingerprints[key] = fingerprint_data
            else:
                # Replace existing database
                self._database.fingerprints = import_db.fingerprints.copy()

            self.save_database()
            return True

        except Exception as e:
            print(f"Error importing database from {import_path}: {e}")
            return False

    # Query Operations
    def find_fingerprints_by_pattern(self, pattern: str) -> list[dict[str, Any]]:
        """Find fingerprints matching a file path pattern."""
        results = []

        try:
            pattern = pattern.lower()

            for key, fingerprint_data in self._database.fingerprints.items():
                file_path = fingerprint_data.get("file_path", "")
                if pattern in file_path.lower():
                    result = fingerprint_data.copy()
                    result["key"] = key
                    results.append(result)

        except Exception as e:
            print(f"Error searching fingerprints: {e}")

        return results

    def get_fingerprints_by_extension(self, extension: str) -> list[dict[str, Any]]:
        """Get all fingerprints for files with a specific extension."""
        results = []
        extension = extension.lower()

        try:
            for key, fingerprint_data in self._database.fingerprints.items():
                file_path = fingerprint_data.get("file_path", "")
                if file_path.lower().endswith(extension):
                    result = fingerprint_data.copy()
                    result["key"] = key
                    results.append(result)

        except Exception as e:
            print(f"Error getting fingerprints by extension: {e}")

        return results

    def get_duplicate_fingerprints(self) -> dict[str, list[dict[str, Any]]]:
        """Find fingerprints that have the same hash (potential duplicates)."""
        fingerprint_groups = {}

        try:
            for key, fingerprint_data in self._database.fingerprints.items():
                fingerprint = fingerprint_data.get("fingerprint")
                if fingerprint:
                    if fingerprint not in fingerprint_groups:
                        fingerprint_groups[fingerprint] = []

                    result = fingerprint_data.copy()
                    result["key"] = key
                    fingerprint_groups[fingerprint].append(result)

            # Only return groups with multiple entries
            duplicates = {
                fp: entries for fp, entries in fingerprint_groups.items() if len(entries) > 1
            }

        except Exception as e:
            print(f"Error finding duplicate fingerprints: {e}")
            duplicates = {}

        return duplicates

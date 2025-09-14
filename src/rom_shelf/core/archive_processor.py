"""Archive processing for ZIP, 7Z, and RAR files."""

import tempfile
from pathlib import Path
from typing import NamedTuple

try:
    import py7zr

    HAS_PY7ZR = True
except ImportError:
    HAS_PY7ZR = False

try:
    import rarfile

    HAS_RARFILE = True
except ImportError:
    HAS_RARFILE = False


class ArchiveHandler(NamedTuple):
    """Archive handler configuration."""

    available: bool
    get_contents_method: str
    extract_method: str


class ExtractedFile:
    """Represents a file extracted from an archive."""

    def __init__(self, original_path: str, extracted_path: Path, temp_dir: Path) -> None:
        """Initialize extracted file info."""
        self.original_path = original_path  # Path within archive
        self.extracted_path = extracted_path  # Path to extracted file
        self.temp_dir = temp_dir  # Temporary directory (for cleanup)


class ArchiveProcessor:
    """Handles extraction and processing of archive files."""

    def __init__(self) -> None:
        """Initialize the archive processor."""
        self._temp_dirs: list[Path] = []
        self._handlers = {
            ".zip": ArchiveHandler(True, "_get_zip_contents", "_extract_zip_files"),
            ".7z": ArchiveHandler(HAS_PY7ZR, "_get_7z_contents", "_extract_7z_files"),
            ".rar": ArchiveHandler(HAS_RARFILE, "_get_rar_contents", "_extract_rar_files"),
        }

    def can_process_archive(self, archive_path: Path) -> bool:
        """Check if archive can be processed."""
        extension = archive_path.suffix.lower()
        handler = self._handlers.get(extension)
        return handler is not None and handler.available

    def get_archive_contents(self, archive_path: Path) -> list[str]:
        """Get list of files in archive without extracting."""
        extension = archive_path.suffix.lower()
        handler = self._handlers.get(extension)

        if handler is None or not handler.available:
            return []

        try:
            method = getattr(self, handler.get_contents_method)
            return method(archive_path)
        except Exception:
            return []  # Return empty list on error

    def extract_files(
        self, archive_path: Path, file_filter: list[str] | None = None
    ) -> list[ExtractedFile]:
        """Extract files from archive with optional filtering."""
        extension = archive_path.suffix.lower()
        handler = self._handlers.get(extension)

        if handler is None or not handler.available:
            return []

        try:
            method = getattr(self, handler.extract_method)
            return method(archive_path, file_filter)
        except Exception:
            return []  # Return empty list on error

    def _get_zip_contents(self, archive_path: Path) -> list[str]:
        """Get contents of ZIP file."""
        import zipfile

        with zipfile.ZipFile(archive_path, "r") as zip_file:
            return [info.filename for info in zip_file.infolist() if not info.is_dir()]

    def _get_7z_contents(self, archive_path: Path) -> list[str]:
        """Get contents of 7Z file."""
        with py7zr.SevenZipFile(archive_path, mode="r") as archive:
            return [name for name in archive.getnames() if not name.endswith("/")]

    def _get_rar_contents(self, archive_path: Path) -> list[str]:
        """Get contents of RAR file."""
        with rarfile.RarFile(archive_path) as rar:
            return [info.filename for info in rar.infolist() if not info.is_dir()]

    def _extract_zip_files(
        self, archive_path: Path, file_filter: list[str] | None = None
    ) -> list[ExtractedFile]:
        """Extract files from ZIP archive."""
        import zipfile

        temp_dir = Path(tempfile.mkdtemp(prefix="romshelf_"))
        self._temp_dirs.append(temp_dir)

        extracted_files = []

        with zipfile.ZipFile(archive_path, "r") as zip_file:
            for info in zip_file.infolist():
                if info.is_dir():
                    continue

                # Apply file filter if provided
                if file_filter:
                    file_ext = Path(info.filename).suffix.lower()
                    if file_ext not in file_filter:
                        continue

                # Extract file
                extracted_path = temp_dir / Path(info.filename).name
                with zip_file.open(info) as source, open(extracted_path, "wb") as target:
                    target.write(source.read())

                extracted_files.append(ExtractedFile(info.filename, extracted_path, temp_dir))

        return extracted_files

    def _extract_7z_files(
        self, archive_path: Path, file_filter: list[str] | None = None
    ) -> list[ExtractedFile]:
        """Extract files from 7Z archive."""
        temp_dir = Path(tempfile.mkdtemp(prefix="romshelf_"))
        self._temp_dirs.append(temp_dir)

        extracted_files = []

        with py7zr.SevenZipFile(archive_path, mode="r") as archive:
            for name in archive.getnames():
                if name.endswith("/"):  # Skip directories
                    continue

                # Apply file filter if provided
                if file_filter:
                    file_ext = Path(name).suffix.lower()
                    if file_ext not in file_filter:
                        continue

                # Extract file
                archive.extract(temp_dir, [name])
                original_path = temp_dir / name
                extracted_path = temp_dir / Path(name).name

                # Move to flat structure
                if original_path != extracted_path:
                    original_path.rename(extracted_path)
                    # Remove empty directories
                    try:
                        original_path.parent.rmdir()
                    except OSError:
                        pass

                extracted_files.append(ExtractedFile(name, extracted_path, temp_dir))

        return extracted_files

    def _extract_rar_files(
        self, archive_path: Path, file_filter: list[str] | None = None
    ) -> list[ExtractedFile]:
        """Extract files from RAR archive."""
        temp_dir = Path(tempfile.mkdtemp(prefix="romshelf_"))
        self._temp_dirs.append(temp_dir)

        extracted_files = []

        with rarfile.RarFile(archive_path) as rar:
            for info in rar.infolist():
                if info.is_dir():
                    continue

                # Apply file filter if provided
                if file_filter:
                    file_ext = Path(info.filename).suffix.lower()
                    if file_ext not in file_filter:
                        continue

                # Extract file
                rar.extract(info, temp_dir)
                original_path = temp_dir / info.filename
                extracted_path = temp_dir / Path(info.filename).name

                # Move to flat structure
                if original_path != extracted_path:
                    original_path.rename(extracted_path)
                    # Remove empty directories
                    try:
                        original_path.parent.rmdir()
                    except OSError:
                        pass

                extracted_files.append(ExtractedFile(info.filename, extracted_path, temp_dir))

        return extracted_files

    def cleanup(self) -> None:
        """Clean up all temporary directories."""
        import shutil

        for temp_dir in self._temp_dirs:
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
            except OSError:
                pass  # Ignore cleanup errors

        self._temp_dirs.clear()

    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.cleanup()

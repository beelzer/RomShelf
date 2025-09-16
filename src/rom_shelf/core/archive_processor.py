"""Improved archive processing with streaming support for large files."""

import io
import logging
import os
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, NamedTuple

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
    stream_method: str


class ExtractedFile:
    """Represents a file extracted from an archive."""

    def __init__(self, original_path: str, extracted_path: Path, temp_dir: Path) -> None:
        """Initialize extracted file info."""
        self.original_path = original_path
        self.extracted_path = extracted_path
        self.temp_dir = temp_dir


class StreamedFile:
    """Represents a file streamed from an archive without full extraction."""

    def __init__(self, name: str, stream: BinaryIO, size: int) -> None:
        """Initialize streamed file info."""
        self.name = name
        self.stream = stream
        self.size = size


class ArchiveProcessor:
    """Handles extraction and processing of archive files with streaming support."""

    # Default configuration
    DEFAULT_CHUNK_SIZE = 64 * 1024  # 64KB chunks
    DEFAULT_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB threshold for streaming
    DEFAULT_EXTRACTION_TIMEOUT = 30  # seconds

    def __init__(
        self,
        max_memory_size: int | None = None,
        chunk_size: int | None = None,
        extraction_timeout: int | None = None,
    ) -> None:
        """Initialize the archive processor.

        Args:
            max_memory_size: Maximum size (bytes) to load in memory before streaming.
            chunk_size: Size of chunks for streaming operations.
            extraction_timeout: Timeout for extraction operations.
        """
        self.logger = logging.getLogger(__name__)
        self._temp_dirs: list[Path] = []
        self.max_memory_size = max_memory_size or self.DEFAULT_MAX_MEMORY_SIZE
        self.chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        self.extraction_timeout = extraction_timeout or self.DEFAULT_EXTRACTION_TIMEOUT

        self._handlers = {
            ".zip": ArchiveHandler(
                True, "_get_zip_contents", "_extract_zip_files", "_stream_zip_file"
            ),
            ".7z": ArchiveHandler(
                HAS_PY7ZR, "_get_7z_contents", "_extract_7z_files", "_stream_7z_file"
            ),
            ".rar": ArchiveHandler(
                HAS_RARFILE, "_get_rar_contents", "_extract_rar_files", "_stream_rar_file"
            ),
        }

        # Track resource usage
        self._active_streams = 0
        self._total_memory_used = 0

    def can_process_archive(self, archive_path: Path) -> bool:
        """Check if archive can be processed."""
        extension = archive_path.suffix.lower()
        handler = self._handlers.get(extension)

        if handler is None or not handler.available:
            return False

        # Check if file exists and is readable
        if not archive_path.exists():
            self.logger.warning(f"Archive does not exist: {archive_path}")
            return False

        if not os.access(archive_path, os.R_OK):
            self.logger.warning(f"Archive is not readable: {archive_path}")
            return False

        # Check for potential zip bomb
        file_size = archive_path.stat().st_size
        if file_size > 5 * 1024 * 1024 * 1024:  # 5GB
            self.logger.warning(f"Archive is very large ({file_size} bytes), may be a zip bomb")

        return True

    def get_archive_contents(self, archive_path: Path) -> list[str]:
        """Get list of files in archive without extracting."""
        extension = archive_path.suffix.lower()
        handler = self._handlers.get(extension)

        if handler is None or not handler.available:
            self.logger.error(f"No handler available for {extension} files")
            return []

        try:
            method = getattr(self, handler.get_contents_method)
            return method(archive_path)
        except FileNotFoundError as e:
            self.logger.error(f"Archive file not found: {e}")
            return []
        except PermissionError as e:
            self.logger.error(f"Permission denied accessing archive: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Failed to get archive contents: {e}", exc_info=True)
            return []

    def extract_files(
        self,
        archive_path: Path,
        file_filter: list[str] | None = None,
        use_streaming: bool = True,
    ) -> list[ExtractedFile]:
        """Extract files from archive with optional filtering.

        Args:
            archive_path: Path to the archive file.
            file_filter: List of file extensions to extract.
            use_streaming: Use streaming for large files.

        Returns:
            List of extracted files.
        """
        extension = archive_path.suffix.lower()
        handler = self._handlers.get(extension)

        if handler is None or not handler.available:
            self.logger.error(f"Cannot process {extension} archives")
            return []

        # Check archive size to determine extraction method
        archive_size = archive_path.stat().st_size

        if use_streaming and archive_size > self.max_memory_size:
            self.logger.info(
                f"Archive size ({archive_size} bytes) exceeds memory threshold, "
                f"using streaming extraction"
            )
            return self._extract_files_streaming(archive_path, file_filter)

        try:
            method = getattr(self, handler.extract_method)
            return method(archive_path, file_filter)
        except MemoryError as e:
            self.logger.error(f"Out of memory extracting archive: {e}")
            # Try streaming extraction as fallback
            if use_streaming:
                self.logger.info("Retrying with streaming extraction")
                return self._extract_files_streaming(archive_path, file_filter)
            return []
        except Exception as e:
            self.logger.error(f"Failed to extract files: {e}", exc_info=True)
            return []

    def _extract_files_streaming(
        self,
        archive_path: Path,
        file_filter: list[str] | None = None,
    ) -> list[ExtractedFile]:
        """Extract files using streaming to handle large archives.

        Args:
            archive_path: Path to the archive file.
            file_filter: List of file extensions to extract.

        Returns:
            List of extracted files.
        """
        extension = archive_path.suffix.lower()
        handler = self._handlers.get(extension)

        if handler is None:
            return []

        temp_dir = Path(tempfile.mkdtemp(prefix="romshelf_stream_"))
        self._temp_dirs.append(temp_dir)
        extracted_files = []

        try:
            with self._open_archive_for_streaming(archive_path, extension) as archive:
                for file_info in self._iterate_archive_files(archive, extension):
                    # Check file filter
                    if file_filter:
                        file_ext = Path(file_info["name"]).suffix.lower()
                        if file_ext not in file_filter:
                            continue

                    # Stream file to disk
                    extracted_path = temp_dir / Path(file_info["name"]).name

                    with self._stream_archive_file(archive, file_info, extension) as stream:
                        with open(extracted_path, "wb") as output:
                            while chunk := stream.read(self.chunk_size):
                                output.write(chunk)

                    extracted_files.append(
                        ExtractedFile(file_info["name"], extracted_path, temp_dir)
                    )

        except Exception as e:
            self.logger.error(f"Streaming extraction failed: {e}", exc_info=True)

        return extracted_files

    @contextmanager
    def _open_archive_for_streaming(self, archive_path: Path, extension: str):
        """Open archive for streaming operations.

        Args:
            archive_path: Path to archive.
            extension: Archive extension.

        Yields:
            Archive object for streaming.
        """
        if extension == ".zip":
            import zipfile

            with zipfile.ZipFile(archive_path, "r") as archive:
                yield archive
        elif extension == ".7z" and HAS_PY7ZR:
            with py7zr.SevenZipFile(archive_path, mode="r") as archive:
                yield archive
        elif extension == ".rar" and HAS_RARFILE:
            with rarfile.RarFile(archive_path) as archive:
                yield archive
        else:
            raise ValueError(f"Unsupported archive type: {extension}")

    def _iterate_archive_files(self, archive, extension: str) -> Iterator[dict]:
        """Iterate over files in an archive.

        Args:
            archive: Open archive object.
            extension: Archive extension.

        Yields:
            File information dictionaries.
        """
        if extension == ".zip":
            for info in archive.infolist():
                if not info.is_dir():
                    yield {
                        "name": info.filename,
                        "size": info.file_size,
                        "info": info,
                    }
        elif extension == ".7z":
            for name in archive.getnames():
                if not name.endswith("/"):
                    yield {
                        "name": name,
                        "size": 0,  # Size not readily available in py7zr
                        "info": name,
                    }
        elif extension == ".rar":
            for info in archive.infolist():
                if not info.is_dir():
                    yield {
                        "name": info.filename,
                        "size": info.file_size,
                        "info": info,
                    }

    @contextmanager
    def _stream_archive_file(self, archive, file_info: dict, extension: str):
        """Stream a single file from an archive.

        Args:
            archive: Open archive object.
            file_info: File information dictionary.
            extension: Archive extension.

        Yields:
            File-like object for streaming.
        """
        if extension == ".zip":
            with archive.open(file_info["info"]) as stream:
                yield stream
        elif extension == ".7z":
            # py7zr doesn't support direct streaming, extract to memory
            temp_buffer = io.BytesIO()
            archive.extract(targets=[file_info["name"]], path=temp_buffer)
            temp_buffer.seek(0)
            yield temp_buffer
        elif extension == ".rar":
            with archive.open(file_info["info"]) as stream:
                yield stream

    def _get_zip_contents(self, archive_path: Path) -> list[str]:
        """Get contents of ZIP file."""
        import zipfile

        try:
            with zipfile.ZipFile(archive_path, "r") as zip_file:
                return [info.filename for info in zip_file.infolist() if not info.is_dir()]
        except zipfile.BadZipFile as e:
            self.logger.error(f"Corrupted ZIP file: {e}")
            return []
        except zipfile.LargeZipFile as e:
            self.logger.error(f"ZIP file requires ZIP64 support: {e}")
            return []

    def _get_7z_contents(self, archive_path: Path) -> list[str]:
        """Get contents of 7Z file."""
        if not HAS_PY7ZR:
            self.logger.error("py7zr not installed, cannot process 7z files")
            return []

        try:
            with py7zr.SevenZipFile(archive_path, mode="r") as archive:
                return [name for name in archive.getnames() if not name.endswith("/")]
        except py7zr.exceptions.Bad7zFile as e:
            self.logger.error(f"Corrupted 7z file: {e}")
            return []

    def _get_rar_contents(self, archive_path: Path) -> list[str]:
        """Get contents of RAR file."""
        if not HAS_RARFILE:
            self.logger.error("rarfile not installed, cannot process RAR files")
            return []

        try:
            with rarfile.RarFile(archive_path) as rar:
                return [info.filename for info in rar.infolist() if not info.is_dir()]
        except rarfile.BadRarFile as e:
            self.logger.error(f"Corrupted RAR file: {e}")
            return []
        except rarfile.NeedFirstVolume as e:
            self.logger.error(f"RAR file requires first volume: {e}")
            return []

    def _extract_zip_files(
        self, archive_path: Path, file_filter: list[str] | None = None
    ) -> list[ExtractedFile]:
        """Extract files from ZIP archive with improved error handling."""
        import zipfile

        temp_dir = Path(tempfile.mkdtemp(prefix="romshelf_"))
        self._temp_dirs.append(temp_dir)
        extracted_files = []

        try:
            with zipfile.ZipFile(archive_path, "r") as zip_file:
                # Check for zip bomb
                total_uncompressed = sum(info.file_size for info in zip_file.infolist())
                compression_ratio = total_uncompressed / archive_path.stat().st_size

                if compression_ratio > 100:
                    self.logger.warning(
                        f"High compression ratio ({compression_ratio:.1f}x), " f"possible zip bomb"
                    )

                for info in zip_file.infolist():
                    if info.is_dir():
                        continue

                    # Security check for path traversal
                    if ".." in info.filename or info.filename.startswith("/"):
                        self.logger.warning(f"Skipping potentially malicious path: {info.filename}")
                        continue

                    # Apply file filter if provided
                    if file_filter:
                        file_ext = Path(info.filename).suffix.lower()
                        if file_ext not in file_filter:
                            continue

                    # Extract file with size check
                    if info.file_size > self.max_memory_size:
                        # Stream large files
                        extracted_path = temp_dir / Path(info.filename).name
                        with zip_file.open(info) as source:
                            with open(extracted_path, "wb") as target:
                                while chunk := source.read(self.chunk_size):
                                    target.write(chunk)
                    else:
                        # Extract normally for small files
                        extracted_path = temp_dir / Path(info.filename).name
                        with zip_file.open(info) as source:
                            with open(extracted_path, "wb") as target:
                                target.write(source.read())

                    extracted_files.append(ExtractedFile(info.filename, extracted_path, temp_dir))

        except zipfile.BadZipFile as e:
            self.logger.error(f"Failed to extract ZIP: {e}")
        except MemoryError as e:
            self.logger.error(f"Out of memory extracting ZIP: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error extracting ZIP: {e}", exc_info=True)

        return extracted_files

    def _extract_7z_files(
        self, archive_path: Path, file_filter: list[str] | None = None
    ) -> list[ExtractedFile]:
        """Extract files from 7Z archive with improved error handling."""
        if not HAS_PY7ZR:
            self.logger.error("py7zr not installed")
            return []

        temp_dir = Path(tempfile.mkdtemp(prefix="romshelf_"))
        self._temp_dirs.append(temp_dir)
        extracted_files = []

        try:
            with py7zr.SevenZipFile(archive_path, mode="r") as archive:
                for name in archive.getnames():
                    if name.endswith("/"):
                        continue

                    # Security check
                    if ".." in name or name.startswith("/"):
                        self.logger.warning(f"Skipping potentially malicious path: {name}")
                        continue

                    # Apply file filter
                    if file_filter:
                        file_ext = Path(name).suffix.lower()
                        if file_ext not in file_filter:
                            continue

                    # Extract file
                    try:
                        archive.extract(temp_dir, [name])
                        original_path = temp_dir / name
                        extracted_path = temp_dir / Path(name).name

                        # Flatten directory structure
                        if original_path != extracted_path and original_path.exists():
                            original_path.rename(extracted_path)
                            # Clean up empty directories
                            try:
                                original_path.parent.rmdir()
                            except OSError:
                                pass

                        extracted_files.append(ExtractedFile(name, extracted_path, temp_dir))

                    except Exception as e:
                        self.logger.error(f"Failed to extract {name}: {e}")

        except py7zr.exceptions.Bad7zFile as e:
            self.logger.error(f"Failed to extract 7z: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error extracting 7z: {e}", exc_info=True)

        return extracted_files

    def _extract_rar_files(
        self, archive_path: Path, file_filter: list[str] | None = None
    ) -> list[ExtractedFile]:
        """Extract files from RAR archive with improved error handling."""
        if not HAS_RARFILE:
            self.logger.error("rarfile not installed")
            return []

        temp_dir = Path(tempfile.mkdtemp(prefix="romshelf_"))
        self._temp_dirs.append(temp_dir)
        extracted_files = []

        try:
            with rarfile.RarFile(archive_path) as rar:
                for info in rar.infolist():
                    if info.is_dir():
                        continue

                    # Security check
                    if ".." in info.filename or info.filename.startswith("/"):
                        self.logger.warning(f"Skipping potentially malicious path: {info.filename}")
                        continue

                    # Apply file filter
                    if file_filter:
                        file_ext = Path(info.filename).suffix.lower()
                        if file_ext not in file_filter:
                            continue

                    # Extract file
                    try:
                        rar.extract(info, temp_dir)
                        original_path = temp_dir / info.filename
                        extracted_path = temp_dir / Path(info.filename).name

                        # Flatten directory structure
                        if original_path != extracted_path and original_path.exists():
                            original_path.rename(extracted_path)
                            # Clean up empty directories
                            try:
                                original_path.parent.rmdir()
                            except OSError:
                                pass

                        extracted_files.append(
                            ExtractedFile(info.filename, extracted_path, temp_dir)
                        )

                    except Exception as e:
                        self.logger.error(f"Failed to extract {info.filename}: {e}")

        except rarfile.BadRarFile as e:
            self.logger.error(f"Failed to extract RAR: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error extracting RAR: {e}", exc_info=True)

        return extracted_files

    def cleanup(self) -> None:
        """Clean up all temporary directories."""
        for temp_dir in self._temp_dirs:
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    self.logger.debug(f"Cleaned up temp directory: {temp_dir}")
            except OSError as e:
                self.logger.warning(f"Failed to clean up {temp_dir}: {e}")

        self._temp_dirs.clear()

    def __del__(self) -> None:
        """Cleanup on deletion."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore errors during cleanup in destructor

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
        return False

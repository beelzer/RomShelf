"""Platform service - business logic for platform operations and configuration."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..platforms.base_platform import BasePlatform, PlatformSetting, TableColumn
from ..platforms.platform_registry import platform_registry


class PlatformService:
    """Service for platform operations and configuration management."""

    def __init__(self) -> None:
        """Initialize the platform service."""
        self._registry = platform_registry

    def get_all_platforms(self) -> List[BasePlatform]:
        """Get all available platforms."""
        return self._registry.get_all_platforms()

    def get_platform(self, platform_id: str) -> Optional[BasePlatform]:
        """Get a specific platform by ID."""
        return self._registry.get_platform(platform_id)

    def get_platform_by_name(self, name: str) -> Optional[BasePlatform]:
        """Get a platform by its display name."""
        for platform in self.get_all_platforms():
            if platform.name.lower() == name.lower():
                return platform
        return None

    def get_platform_ids(self) -> List[str]:
        """Get all platform IDs."""
        return [platform.platform_id for platform in self.get_all_platforms()]

    def get_platform_names(self) -> List[str]:
        """Get all platform display names."""
        return [platform.name for platform in self.get_all_platforms()]

    def get_platform_display_name(self, platform_id: str) -> str:
        """Get the display name for a platform ID."""
        platform = self.get_platform(platform_id)
        return platform.name if platform else platform_id

    # Platform Configuration
    def get_platform_settings(self, platform_id: str) -> List[PlatformSetting]:
        """Get platform-specific settings definitions."""
        platform = self.get_platform(platform_id)
        return platform.get_platform_settings() if platform else []

    def get_platform_table_columns(self, platform_id: str) -> List[TableColumn]:
        """Get table column definitions for a platform."""
        platform = self.get_platform(platform_id)
        return platform.table_columns.copy() if platform else []

    def get_platform_supported_extensions(self, platform_id: str) -> List[str]:
        """Get supported file extensions for a platform."""
        platform = self.get_platform(platform_id)
        return platform.get_supported_extensions() if platform else []

    def get_platform_supported_handlers(self, platform_id: str) -> List[str]:
        """Get supported file handlers for a platform."""
        platform = self.get_platform(platform_id)
        return platform.get_supported_handlers() if platform else []

    def get_platform_archive_extensions(self, platform_id: str) -> List[str]:
        """Get supported archive content extensions for a platform."""
        platform = self.get_platform(platform_id)
        return platform.get_archive_content_extensions() if platform else []

    # File Validation
    def validate_file_for_platform(self, platform_id: str, file_path: Path, internal_path: Optional[str] = None) -> bool:
        """Validate if a file is compatible with a platform."""
        platform = self.get_platform(platform_id)
        if not platform:
            return False

        try:
            return platform.validate_file(file_path, internal_path)
        except Exception as e:
            print(f"Error validating file {file_path} for platform {platform_id}: {e}")
            return False

    def get_file_validation_info(self, platform_id: str, file_path: Path) -> Dict[str, Any]:
        """Get detailed validation information for a file."""
        platform = self.get_platform(platform_id)
        if not platform:
            return {'valid': False, 'reason': f'Platform {platform_id} not found'}

        try:
            # Basic checks
            if not file_path.exists():
                return {'valid': False, 'reason': 'File does not exist'}

            if not file_path.is_file():
                return {'valid': False, 'reason': 'Path is not a file'}

            # Extension check
            extension = file_path.suffix.lower()
            supported_extensions = self.get_platform_supported_extensions(platform_id)

            if extension not in supported_extensions:
                return {
                    'valid': False,
                    'reason': f'Extension {extension} not supported',
                    'supported_extensions': supported_extensions
                }

            # Platform-specific validation
            is_valid = platform.validate_file(file_path)

            return {
                'valid': is_valid,
                'extension': extension,
                'supported_extensions': supported_extensions,
                'file_size': file_path.stat().st_size,
                'platform': platform.name
            }

        except Exception as e:
            return {'valid': False, 'reason': f'Validation error: {e}'}

    # Platform Detection
    def detect_platform_from_file(self, file_path: Path) -> Optional[str]:
        """Detect the most likely platform for a given file."""
        if not file_path.exists() or not file_path.is_file():
            return None

        extension = file_path.suffix.lower()
        possible_platforms = []

        # Check which platforms support this extension
        for platform in self.get_all_platforms():
            if extension in platform.get_supported_extensions():
                # Validate with the platform's specific rules
                if platform.validate_file(file_path):
                    possible_platforms.append(platform.platform_id)

        # Return the first match, or None if no matches
        return possible_platforms[0] if possible_platforms else None

    def get_compatible_platforms(self, file_path: Path) -> List[str]:
        """Get all platforms compatible with a given file."""
        if not file_path.exists() or not file_path.is_file():
            return []

        compatible = []
        extension = file_path.suffix.lower()

        for platform in self.get_all_platforms():
            if extension in platform.get_supported_extensions():
                try:
                    if platform.validate_file(file_path):
                        compatible.append(platform.platform_id)
                except Exception:
                    continue

        return compatible

    # Directory Analysis
    def detect_platform_directories(self, parent_dir: Path) -> Dict[str, List[Path]]:
        """Detect potential platform directories and group by platform ID."""
        matches = {}

        if not parent_dir.exists() or not parent_dir.is_dir():
            return matches

        # Build platform name mapping with specific patterns
        platform_patterns = {}
        for platform in self.get_all_platforms():
            patterns = []

            # Add exact name and ID matches
            patterns.append(platform.name.lower())
            patterns.append(platform.platform_id.lower())

            # Add common directory name patterns
            if platform.platform_id == 'n64':
                patterns = ['nintendo 64', 'n64', 'nintendo64']
            elif platform.platform_id == 'gameboy':
                patterns = ['nintendo game boy', 'gameboy', 'gb', 'game boy']
            elif platform.platform_id == 'gbc':
                patterns = ['nintendo game boy color', 'gbc', 'game boy color']
            elif platform.platform_id == 'gba':
                patterns = ['nintendo game boy advance', 'gba', 'game boy advance']
            elif platform.platform_id == 'snes':
                patterns = ['nintendo snes', 'snes', 'super nintendo']
            elif platform.platform_id == 'psx':
                patterns = ['sony playstation', 'psx', 'playstation', 'ps1']
            elif platform.platform_id == 'gamecube':
                patterns = ['nintendo gamecube', 'gamecube', 'gc']

            platform_patterns[platform.platform_id] = patterns

        # Scan subdirectories with better matching
        try:
            for item in parent_dir.iterdir():
                if item.is_dir():
                    dir_name = item.name.lower()

                    # Try to find the best match (longest/most specific first)
                    best_match = None
                    best_match_length = 0

                    for platform_id, patterns in platform_patterns.items():
                        for pattern in patterns:
                            # Exact match or contains pattern
                            if pattern == dir_name or pattern in dir_name:
                                if len(pattern) > best_match_length:
                                    best_match = platform_id
                                    best_match_length = len(pattern)

                    if best_match:
                        if best_match not in matches:
                            matches[best_match] = []
                        matches[best_match].append(item)

        except (OSError, PermissionError) as e:
            print(f"Error scanning directory {parent_dir}: {e}")

        return matches

    def analyze_directory_contents(self, directory: Path, platform_id: Optional[str] = None) -> Dict[str, Any]:
        """Analyze the contents of a directory for ROM files."""
        if not directory.exists() or not directory.is_dir():
            return {'error': 'Directory does not exist'}

        analysis = {
            'directory': str(directory),
            'total_files': 0,
            'rom_files': 0,
            'platforms': {},
            'extensions': {},
            'errors': []
        }

        try:
            # Get all files recursively
            files = list(directory.rglob('*'))
            files = [f for f in files if f.is_file()]
            analysis['total_files'] = len(files)

            # Analyze each file
            for file_path in files:
                try:
                    extension = file_path.suffix.lower()
                    if extension:
                        analysis['extensions'][extension] = analysis['extensions'].get(extension, 0) + 1

                    # If platform is specified, check against it
                    if platform_id:
                        if self.validate_file_for_platform(platform_id, file_path):
                            analysis['rom_files'] += 1
                            analysis['platforms'][platform_id] = analysis['platforms'].get(platform_id, 0) + 1
                    else:
                        # Check against all platforms
                        compatible_platforms = self.get_compatible_platforms(file_path)
                        if compatible_platforms:
                            analysis['rom_files'] += 1
                            for platform in compatible_platforms:
                                analysis['platforms'][platform] = analysis['platforms'].get(platform, 0) + 1

                except Exception as e:
                    analysis['errors'].append(f"Error analyzing {file_path}: {e}")

        except Exception as e:
            analysis['errors'].append(f"Error scanning directory: {e}")

        return analysis

    # Utility Methods
    def get_platform_statistics(self) -> Dict[str, Any]:
        """Get statistics about all platforms."""
        platforms = self.get_all_platforms()

        return {
            'total_platforms': len(platforms),
            'platforms': [
                {
                    'id': p.platform_id,
                    'name': p.name,
                    'supported_extensions': len(p.get_supported_extensions()),
                    'table_columns': len(p.table_columns),
                    'has_settings': len(p.get_platform_settings()) > 0
                }
                for p in platforms
            ]
        }

    def validate_platform_configuration(self, platform_id: str, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate a platform configuration."""
        platform = self.get_platform(platform_id)
        if not platform:
            return False, [f"Platform {platform_id} not found"]

        errors = []

        # Validate ROM directories
        rom_directories = config.get('rom_directories', [])
        for directory in rom_directories:
            path = Path(directory)
            if not path.exists():
                errors.append(f"ROM directory does not exist: {directory}")
            elif not path.is_dir():
                errors.append(f"ROM directory path is not a directory: {directory}")

        # Validate supported formats
        supported_formats = config.get('supported_formats', [])
        platform_extensions = platform.get_supported_extensions()
        for format_ext in supported_formats:
            if format_ext not in platform_extensions:
                errors.append(f"Format {format_ext} not supported by platform {platform.name}")

        return len(errors) == 0, errors
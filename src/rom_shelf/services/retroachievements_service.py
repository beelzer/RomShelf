"""RetroAchievements API integration service with SQLite caching."""

import hashlib
import json
import logging
import time
from collections.abc import Callable
from pathlib import Path
from threading import Lock
from typing import Any

import requests

from ..core.settings import Settings
from .ra_database import RetroAchievementsDatabase


class RetroAchievementsService:
    """Service for RetroAchievements API integration with SQLite database."""

    BASE_URL = "https://retroachievements.org/API/"
    CACHE_DB_FILE = Path("data/retroachievements.db")

    # Platform ID mapping (RetroAchievements console IDs)
    PLATFORM_MAP = {
        "nes": 7,
        "snes": 3,
        "n64": 2,
        "gb": 4,
        "gbc": 6,
        "gba": 5,
        "nds": 18,
        "genesis": 1,
        "megadrive": 1,
        "mastersystem": 11,
        "gamegear": 15,
        "psx": 12,
        "ps1": 12,
        "ps2": 21,
        "psp": 41,
        "arcade": 27,
        "neogeo": 14,
    }

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the RetroAchievements service."""
        self.logger = logging.getLogger(__name__)
        self._settings = settings
        self._db = RetroAchievementsDatabase(self.CACHE_DB_FILE)
        self._console_updating: set[int] = set()  # Track consoles being updated
        self._last_request_time = 0.0
        self._rate_limit_lock = Lock()
        self._console_lock = Lock()
        self._min_request_interval = 2.0  # 2 seconds between requests

        # Progress callback for UI updates
        self._progress_callback: Callable | None = None

    def set_progress_callback(self, callback: Callable | None) -> None:
        """Set the progress callback for UI updates.

        Args:
            callback: Callable that takes (event_type, data) parameters
        """
        self._progress_callback = callback

    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting for API calls."""
        with self._rate_limit_lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time

            if time_since_last < self._min_request_interval:
                sleep_time = self._min_request_interval - time_since_last
                self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)

            self._last_request_time = time.time()

    def _make_api_request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any] | None:
        """Make an API request to RetroAchievements with rate limiting.

        Args:
            endpoint: API endpoint name.
            params: Query parameters.

        Returns:
            API response as dictionary or None on error.
        """
        # Get settings
        if self._settings:
            settings = self._settings
        else:
            # Try to load from settings file
            settings_file = Path("data") / "settings.json"
            if settings_file.exists():
                settings = Settings.load(settings_file)
            else:
                self.logger.debug("No settings file found")
                return None

        # Check if API key is configured
        if not settings.retroachievements_api_key:
            self.logger.debug("RetroAchievements API key not configured")
            return None

        # Add authentication
        params["y"] = settings.retroachievements_api_key

        # Enforce rate limiting
        self._enforce_rate_limit()

        # Make request with download progress tracking
        url = f"{self.BASE_URL}{endpoint}.php"
        try:
            self.logger.debug(f"Making API request to {endpoint}")

            # Use stream=True for large responses to track progress
            is_large_request = "GameList" in endpoint
            if is_large_request:
                response = requests.get(url, params=params, timeout=60, stream=True)
                response.raise_for_status()

                # Track download progress
                content_chunks = []
                bytes_downloaded = 0
                start_time = time.time()
                last_update = start_time

                # Get total size if available
                total_size = int(response.headers.get("content-length", 0))

                # Send initial progress update immediately
                if self._progress_callback:
                    self._progress_callback(
                        "ra_download", {"bytes": 0, "total": total_size, "speed": 0}
                    )

                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        content_chunks.append(chunk)
                        bytes_downloaded += len(chunk)

                        # Update progress more frequently (every 0.1 seconds or every 64KB)
                        current_time = time.time()
                        if current_time - last_update > 0.1 or bytes_downloaded % 65536 == 0:
                            elapsed = current_time - start_time
                            speed_bps = bytes_downloaded / elapsed if elapsed > 0 else 0

                            if self._progress_callback:
                                self._progress_callback(
                                    "ra_download",
                                    {
                                        "bytes": bytes_downloaded,
                                        "total": total_size,
                                        "speed": speed_bps,
                                    },
                                )
                            last_update = current_time

                # Parse complete response
                content = b"".join(content_chunks)
                data = response.json() if not content else json.loads(content.decode("utf-8"))
            else:
                # Small request - normal handling
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()

            return data

        except requests.exceptions.RequestException as e:
            self.logger.error(f"RA API request failed for {endpoint}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to parse RA API response: {e}")
            return None

    def _update_hash_database_for_console(self, console_id: int) -> bool:
        """Update the local hash database for a specific console.

        Args:
            console_id: RetroAchievements console ID.

        Returns:
            True if successful, False otherwise.
        """
        with self._console_lock:
            # Check if another thread is already updating this console
            if console_id in self._console_updating:
                # Wait for the other thread to finish
                self.logger.debug(
                    f"Console {console_id} is already being updated by another thread"
                )
                while console_id in self._console_updating:
                    time.sleep(0.5)
                return True  # Assume the other thread succeeded

            # Check if we've recently updated this console (1 week cache)
            if self._db.is_console_cached(console_id, max_age_seconds=604800):
                self.logger.debug(f"Console {console_id} cache is still fresh")
                return True

            # Mark this console as being updated
            self._console_updating.add(console_id)

        try:
            # Get console name for progress display
            console_name = self._get_console_name(console_id)
            self.logger.info(f"Updating hash database for console {console_id} ({console_name})")

            # Send progress update
            if self._progress_callback:
                self._progress_callback(
                    "ra_update", {"message": f"Downloading {console_name} game database..."}
                )

            # Get game list with hashes
            params = {"i": console_id, "h": 1}  # h=1 includes hashes
            result = self._make_api_request("API_GetGameList", params)

            if result:
                # Process each game and build hash database entries
                hashes_data = []
                for game in result:
                    if isinstance(game, dict):
                        game_id = game.get("ID")
                        game_title = game.get("Title")
                        game_hashes = game.get("Hashes", [])

                        # Process each hash
                        if isinstance(game_hashes, list):
                            for hash_value in game_hashes:
                                # Hashes can be strings or dicts
                                if isinstance(hash_value, str):
                                    md5_hash = hash_value.lower()
                                elif isinstance(hash_value, dict):
                                    md5_hash = hash_value.get("MD5", "").lower()
                                else:
                                    continue

                                if md5_hash and game_id:
                                    hashes_data.append(
                                        {
                                            "MD5": md5_hash,
                                            "GameID": game_id,
                                            "Title": game_title or "",
                                        }
                                    )

                # Update database with all hashes for this console
                self._db.update_hash_database(console_id, hashes_data)
                self.logger.info(f"Updated {len(hashes_data)} hashes for console {console_id}")
                return True

        except Exception as e:
            self.logger.error(f"Failed to update hash database for console {console_id}: {e}")
            return False
        finally:
            # Remove from updating set
            with self._console_lock:
                self._console_updating.discard(console_id)

    def get_platform_id(self, platform_name: str) -> int | None:
        """Get RetroAchievements console ID for a platform.

        Args:
            platform_name: Platform name (e.g., "n64", "snes").

        Returns:
            Console ID or None if not found.
        """
        return self.PLATFORM_MAP.get(platform_name.lower())

    def calculate_rom_hash(self, file_path: Path) -> str | None:
        """Calculate MD5 hash of a ROM file.

        Args:
            file_path: Path to the ROM file.

        Returns:
            MD5 hash as lowercase hex string or None on error.
        """
        try:
            md5_hash = hashlib.md5()
            with open(file_path, "rb") as f:
                # Read in chunks for large files
                for chunk in iter(lambda: f.read(8192), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest().lower()
        except Exception as e:
            self.logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return None

    def get_rom_info(self, file_path: Path, platform: str | None = None) -> dict[str, Any] | None:
        """Get RetroAchievements info for a ROM file.

        Args:
            file_path: Path to the ROM file.
            platform: Platform name (optional, helps with console identification).

        Returns:
            Dictionary with RA info or None if not found.
        """
        # Calculate ROM hash
        rom_hash = self.calculate_rom_hash(file_path)
        if not rom_hash:
            return None

        # Check if hash exists in database
        hash_info = self._db.get_hash_info(rom_hash)
        if hash_info:
            return {
                "hash": rom_hash,
                "game_id": hash_info["game_id"],
                "console_id": hash_info["console_id"],
                "title": hash_info.get("game_title", ""),
                "achievement_count": hash_info.get("achievement_count", 0),
                "points": hash_info.get("points_total", 0),
            }

        # If not found and platform is provided, try updating the console database
        if platform:
            console_id = self.get_platform_id(platform)
            if console_id:
                # Update hash database for this console
                if self._update_hash_database_for_console(console_id):
                    # Try again after update
                    hash_info = self._db.get_hash_info(rom_hash)
                    if hash_info:
                        return {
                            "hash": rom_hash,
                            "game_id": hash_info["game_id"],
                            "console_id": hash_info["console_id"],
                            "title": hash_info.get("game_title", ""),
                            "achievement_count": hash_info.get("achievement_count", 0),
                            "points": hash_info.get("points_total", 0),
                        }

        return None

    def get_game_info(self, game_id: int) -> dict[str, Any] | None:
        """Get detailed game information from RetroAchievements.

        Args:
            game_id: RetroAchievements game ID.

        Returns:
            Dictionary with game info or None on error.
        """
        # Check database cache first
        cached_info = self._db.get_game_info(game_id)
        if cached_info:
            # Check if cache is fresh (1 day)
            if time.time() - cached_info.get("last_updated", 0) < 86400:
                return cached_info

        # Fetch from API
        params = {"i": game_id}
        result = self._make_api_request("API_GetGame", params)

        if result:
            # Update cache
            self._db.update_game_info(game_id, result)
            return result

        return None

    def _get_console_name(self, console_id: int) -> str:
        """Get human-readable console name from ID."""
        console_names = {
            1: "Genesis/Mega Drive",
            2: "Nintendo 64",
            3: "SNES",
            4: "Game Boy",
            5: "Game Boy Advance",
            6: "Game Boy Color",
            7: "NES",
            11: "Master System",
            12: "PlayStation",
            14: "Neo Geo",
            15: "Game Gear",
            18: "Nintendo DS",
            21: "PlayStation 2",
            27: "Arcade",
            41: "PlayStation Portable",
        }
        return console_names.get(console_id, f"Console {console_id}")

    def get_all_supported_platforms(self) -> dict[int, str]:
        """Get all supported RetroAchievements platforms.

        Returns:
            Dictionary mapping console IDs to names
        """
        return {
            1: "Genesis/Mega Drive",
            2: "Nintendo 64",
            3: "SNES",
            4: "Game Boy",
            5: "Game Boy Advance",
            6: "Game Boy Color",
            7: "NES",
            11: "Master System",
            12: "PlayStation",
            14: "Neo Geo",
            15: "Game Gear",
            18: "Nintendo DS",
            21: "PlayStation 2",
            27: "Arcade",
            41: "PlayStation Portable",
        }

    def get_cache_statistics(self) -> dict[int, dict[str, Any]]:
        """Get statistics about cached data.

        Returns:
            Dictionary with cache information per platform
        """
        cache_info = self._db.get_console_cache_info()
        stats = {}

        current_time = time.time()
        for console_id, info in cache_info.items():
            console_name = self._get_console_name(console_id)
            last_update = info["last_updated"]
            game_count = info["game_count"]

            # Calculate age
            age_seconds = current_time - last_update
            age_days = age_seconds / 86400

            # Format age string with more precision for recent updates
            if age_seconds < 60:
                age_str = f"{int(age_seconds)} seconds ago"
            elif age_seconds < 3600:
                minutes = int(age_seconds / 60)
                age_str = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            elif age_days < 1:
                hours = int(age_seconds / 3600)
                age_str = f"{hours} hour{'s' if hours != 1 else ''} ago"
            elif age_days < 7:
                days = int(age_days)
                age_str = f"{days} day{'s' if days != 1 else ''} ago"
            else:
                weeks = int(age_days / 7)
                age_str = f"{weeks} week{'s' if weeks != 1 else ''} ago"

            stats[console_id] = {
                "name": console_name,
                "game_count": game_count,
                "last_updated": last_update,
                "age_string": age_str,
                "age_days": age_days,
            }

        return stats

    def force_update_console(self, console_id: int) -> bool:
        """Force update the hash database for a specific console.

        Args:
            console_id: RetroAchievements console ID

        Returns:
            True if successful, False otherwise
        """
        # Clear the console from cache to force update
        self._db.clear_console_cache(console_id)

        # Update the console
        return self._update_hash_database_for_console(console_id)

    def get_total_cache_size(self) -> tuple[int, str]:
        """Get total size of cache files.

        Returns:
            Tuple of (size_in_bytes, human_readable_string)
        """
        total_size = self._db.get_database_size()

        # Format size for display
        if total_size < 1024:
            size_str = f"{total_size} B"
        elif total_size < 1024 * 1024:
            size_str = f"{total_size / 1024:.1f} KB"
        else:
            size_str = f"{total_size / (1024 * 1024):.1f} MB"

        return total_size, size_str

    def clear_cache(self):
        """Clear all RetroAchievements caches."""
        self._db.clear_all_caches()
        self.logger.info("Cleared all RetroAchievements caches")

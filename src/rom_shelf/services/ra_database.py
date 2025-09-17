"""SQLite database for RetroAchievements cache data."""

import json
import logging
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any


class RetroAchievementsDatabase:
    """SQLite database manager for RetroAchievements data."""

    def __init__(self, db_path: Path):
        """Initialize the database.

        Args:
            db_path: Path to the SQLite database file
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _initialize_database(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Hash database table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hash_database (
                    hash TEXT PRIMARY KEY,
                    console_id INTEGER NOT NULL,
                    game_id INTEGER NOT NULL,
                    game_title TEXT,
                    achievement_count INTEGER DEFAULT 0,
                    points_total INTEGER DEFAULT 0,
                    retropoints INTEGER DEFAULT 0,
                    last_updated REAL DEFAULT 0,
                    extra_data TEXT
                )
            """)

            # Console cache tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS console_cache (
                    console_id INTEGER PRIMARY KEY,
                    last_updated REAL NOT NULL,
                    game_count INTEGER DEFAULT 0
                )
            """)

            # Game info cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS game_info_cache (
                    game_id INTEGER PRIMARY KEY,
                    title TEXT,
                    console_id INTEGER,
                    achievement_count INTEGER DEFAULT 0,
                    points_total INTEGER DEFAULT 0,
                    retropoints INTEGER DEFAULT 0,
                    last_updated REAL DEFAULT 0,
                    extra_data TEXT
                )
            """)

            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_hash_console
                ON hash_database(console_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_hash_game
                ON hash_database(game_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_game_info_console
                ON game_info_cache(console_id)
            """)

    def get_game_id_by_hash(self, file_hash: str) -> int | None:
        """Get game ID by file hash.

        Args:
            file_hash: MD5 hash of the ROM file

        Returns:
            Game ID if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT game_id FROM hash_database WHERE hash = ?", (file_hash.lower(),))
            result = cursor.fetchone()
            return result["game_id"] if result else None

    def get_hash_info(self, file_hash: str) -> dict[str, Any] | None:
        """Get full hash information.

        Args:
            file_hash: MD5 hash of the ROM file

        Returns:
            Dictionary with hash info if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM hash_database WHERE hash = ?", (file_hash.lower(),))
            result = cursor.fetchone()
            if result:
                data = dict(result)
                # Parse extra_data JSON if present
                if data.get("extra_data"):
                    try:
                        data["extra_data"] = json.loads(data["extra_data"])
                    except json.JSONDecodeError:
                        data["extra_data"] = {}
                return data
            return None

    def update_hash_database(self, console_id: int, hashes_data: list[dict[str, Any]]):
        """Update hash database for a console.

        Args:
            console_id: RetroAchievements console ID
            hashes_data: List of hash data dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Clear existing hashes for this console
            cursor.execute("DELETE FROM hash_database WHERE console_id = ?", (console_id,))

            # Insert new hashes
            current_time = time.time()
            for hash_data in hashes_data:
                # Extract main fields
                file_hash = hash_data.get("MD5", "").lower()
                game_id = hash_data.get("GameID", 0)

                if not file_hash or not game_id:
                    continue

                # Store extra data as JSON
                extra_data = {
                    k: v for k, v in hash_data.items() if k not in ["MD5", "GameID", "Title"]
                }

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO hash_database
                    (hash, console_id, game_id, game_title, last_updated, extra_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        file_hash,
                        console_id,
                        game_id,
                        hash_data.get("Title", ""),
                        current_time,
                        json.dumps(extra_data) if extra_data else None,
                    ),
                )

            # Update console cache info
            cursor.execute(
                """
                INSERT OR REPLACE INTO console_cache (console_id, last_updated, game_count)
                VALUES (?, ?, (SELECT COUNT(DISTINCT game_id) FROM hash_database WHERE console_id = ?))
            """,
                (console_id, current_time, console_id),
            )

    def get_game_info(self, game_id: int) -> dict[str, Any] | None:
        """Get cached game information.

        Args:
            game_id: RetroAchievements game ID

        Returns:
            Dictionary with game info if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM game_info_cache WHERE game_id = ?", (game_id,))
            result = cursor.fetchone()
            if result:
                data = dict(result)
                # Parse extra_data JSON if present
                if data.get("extra_data"):
                    try:
                        data["extra_data"] = json.loads(data["extra_data"])
                    except json.JSONDecodeError:
                        data["extra_data"] = {}
                return data
            return None

    def update_game_info(self, game_id: int, game_data: dict[str, Any]):
        """Update cached game information.

        Args:
            game_id: RetroAchievements game ID
            game_data: Game data from API
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Extract main fields
            title = game_data.get("Title", "")
            console_id = game_data.get("ConsoleID", 0)
            achievement_count = game_data.get("NumAchievements", 0)
            points = game_data.get("Points", 0)
            retropoints = game_data.get("RetroPoints", 0)

            # Store extra data as JSON
            extra_data = {
                k: v
                for k, v in game_data.items()
                if k
                not in ["GameID", "Title", "ConsoleID", "NumAchievements", "Points", "RetroPoints"]
            }

            cursor.execute(
                """
                INSERT OR REPLACE INTO game_info_cache
                (game_id, title, console_id, achievement_count, points_total,
                 retropoints, last_updated, extra_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    game_id,
                    title,
                    console_id,
                    achievement_count,
                    points,
                    retropoints,
                    time.time(),
                    json.dumps(extra_data) if extra_data else None,
                ),
            )

    def get_console_cache_info(self) -> dict[int, dict[str, Any]]:
        """Get cache information for all consoles.

        Returns:
            Dictionary mapping console IDs to cache info
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT console_id, last_updated, game_count
                FROM console_cache
            """)
            results = cursor.fetchall()

            return {
                row["console_id"]: {
                    "last_updated": row["last_updated"],
                    "game_count": row["game_count"],
                }
                for row in results
            }

    def is_console_cached(self, console_id: int, max_age_seconds: float = 86400) -> bool:
        """Check if console data is cached and fresh.

        Args:
            console_id: RetroAchievements console ID
            max_age_seconds: Maximum age in seconds before cache is stale

        Returns:
            True if cached and fresh, False otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT last_updated FROM console_cache WHERE console_id = ?", (console_id,)
            )
            result = cursor.fetchone()

            if not result:
                return False

            age = time.time() - result["last_updated"]
            return age < max_age_seconds

    def clear_console_cache(self, console_id: int):
        """Clear cache for a specific console.

        Args:
            console_id: RetroAchievements console ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM hash_database WHERE console_id = ?", (console_id,))
            cursor.execute("DELETE FROM console_cache WHERE console_id = ?", (console_id,))

    def clear_all_caches(self):
        """Clear all cached data."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM hash_database")
            cursor.execute("DELETE FROM console_cache")
            cursor.execute("DELETE FROM game_info_cache")

    def get_database_size(self) -> int:
        """Get the size of the database file in bytes.

        Returns:
            Size in bytes
        """
        if self.db_path.exists():
            return self.db_path.stat().st_size
        return 0

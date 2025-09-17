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

            # User achievement progress tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_achievement_progress (
                    user_name TEXT NOT NULL,
                    achievement_id INTEGER NOT NULL,
                    game_id INTEGER NOT NULL,
                    unlocked BOOLEAN DEFAULT 0,
                    unlocked_date REAL,
                    unlocked_hardcore BOOLEAN DEFAULT 0,
                    unlocked_hardcore_date REAL,
                    PRIMARY KEY (user_name, achievement_id)
                )
            """)

            # Game progress summary per user
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_game_progress (
                    user_name TEXT NOT NULL,
                    game_id INTEGER NOT NULL,
                    achievements_earned INTEGER DEFAULT 0,
                    achievements_earned_hardcore INTEGER DEFAULT 0,
                    achievements_total INTEGER DEFAULT 0,
                    points_earned INTEGER DEFAULT 0,
                    points_earned_hardcore INTEGER DEFAULT 0,
                    points_total INTEGER DEFAULT 0,
                    last_updated REAL DEFAULT 0,
                    completion_percentage REAL DEFAULT 0.0,
                    completion_percentage_hardcore REAL DEFAULT 0.0,
                    PRIMARY KEY (user_name, game_id)
                )
            """)

            # Achievement definitions cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS achievement_definitions (
                    achievement_id INTEGER PRIMARY KEY,
                    game_id INTEGER NOT NULL,
                    title TEXT,
                    description TEXT,
                    points INTEGER DEFAULT 0,
                    true_ratio INTEGER DEFAULT 0,
                    display_order INTEGER DEFAULT 0,
                    badge_name TEXT,
                    type TEXT,
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
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_achievement_game
                ON user_achievement_progress(game_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_achievement_user
                ON user_achievement_progress(user_name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_game_progress_user
                ON user_game_progress(user_name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_achievement_def_game
                ON achievement_definitions(game_id)
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

    # User Achievement Progress Methods

    def get_user_game_progress(self, user_name: str, game_id: int) -> dict[str, Any] | None:
        """Get user's progress for a specific game.

        Args:
            user_name: RetroAchievements username
            game_id: Game ID

        Returns:
            Dictionary with progress info if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM user_game_progress WHERE user_name = ? AND game_id = ?",
                (user_name, game_id),
            )
            result = cursor.fetchone()
            return dict(result) if result else None

    def update_user_game_progress(
        self, user_name: str, game_id: int, progress_data: dict[str, Any]
    ):
        """Update user's game progress.

        Args:
            user_name: RetroAchievements username
            game_id: Game ID
            progress_data: Progress data from API
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO user_game_progress
                (user_name, game_id, achievements_earned, achievements_earned_hardcore,
                 achievements_total, points_earned, points_earned_hardcore, points_total,
                 last_updated, completion_percentage, completion_percentage_hardcore)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_name,
                    game_id,
                    progress_data.get("achievements_earned", 0),
                    progress_data.get("achievements_earned_hardcore", 0),
                    progress_data.get("achievements_total", 0),
                    progress_data.get("points_earned", 0),
                    progress_data.get("points_earned_hardcore", 0),
                    progress_data.get("points_total", 0),
                    time.time(),
                    progress_data.get("completion_percentage", 0.0),
                    progress_data.get("completion_percentage_hardcore", 0.0),
                ),
            )

    def update_user_achievements(
        self, user_name: str, game_id: int, achievements: list[dict[str, Any]]
    ):
        """Update user's achievement progress for a game.

        Args:
            user_name: RetroAchievements username
            game_id: Game ID
            achievements: List of achievement progress data
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            for achievement in achievements:
                achievement_id = achievement.get("achievement_id")
                if not achievement_id:
                    continue

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO user_achievement_progress
                    (user_name, achievement_id, game_id, unlocked, unlocked_date,
                     unlocked_hardcore, unlocked_hardcore_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        user_name,
                        achievement_id,
                        game_id,
                        achievement.get("unlocked", False),
                        achievement.get("unlocked_date"),
                        achievement.get("unlocked_hardcore", False),
                        achievement.get("unlocked_hardcore_date"),
                    ),
                )

    def get_user_achievements(self, user_name: str, game_id: int) -> list[dict[str, Any]]:
        """Get user's achievements for a specific game.

        Args:
            user_name: RetroAchievements username
            game_id: Game ID

        Returns:
            List of achievement progress dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT uap.*, ad.title, ad.description, ad.points, ad.badge_name
                FROM user_achievement_progress uap
                LEFT JOIN achievement_definitions ad ON uap.achievement_id = ad.achievement_id
                WHERE uap.user_name = ? AND uap.game_id = ?
            """,
                (user_name, game_id),
            )
            results = cursor.fetchall()
            return [dict(row) for row in results]

    def update_achievement_definitions(self, game_id: int, achievements: list[dict[str, Any]]):
        """Update achievement definitions for a game.

        Args:
            game_id: Game ID
            achievements: List of achievement definitions from API
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            current_time = time.time()

            for achievement in achievements:
                achievement_id = achievement.get("ID") or achievement.get("achievement_id")
                if not achievement_id:
                    continue

                # Store extra data as JSON
                extra_data = {
                    k: v
                    for k, v in achievement.items()
                    if k
                    not in [
                        "ID",
                        "achievement_id",
                        "Title",
                        "Description",
                        "Points",
                        "TrueRatio",
                        "DisplayOrder",
                        "BadgeName",
                        "Type",
                    ]
                }

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO achievement_definitions
                    (achievement_id, game_id, title, description, points, true_ratio,
                     display_order, badge_name, type, last_updated, extra_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        achievement_id,
                        game_id,
                        achievement.get("Title", ""),
                        achievement.get("Description", ""),
                        achievement.get("Points", 0),
                        achievement.get("TrueRatio", 0),
                        achievement.get("DisplayOrder", 0),
                        achievement.get("BadgeName", ""),
                        achievement.get("Type", ""),
                        current_time,
                        json.dumps(extra_data) if extra_data else None,
                    ),
                )

    def get_all_user_progress(self, user_name: str) -> list[dict[str, Any]]:
        """Get all game progress for a user.

        Args:
            user_name: RetroAchievements username

        Returns:
            List of game progress dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ugp.*, gic.title as game_title, gic.console_id
                FROM user_game_progress ugp
                LEFT JOIN game_info_cache gic ON ugp.game_id = gic.game_id
                WHERE ugp.user_name = ?
                ORDER BY ugp.last_updated DESC
            """,
                (user_name,),
            )
            results = cursor.fetchall()
            return [dict(row) for row in results]

    def clear_user_progress(self, user_name: str, game_id: int | None = None):
        """Clear user progress data.

        Args:
            user_name: RetroAchievements username
            game_id: Optional game ID to clear specific game, None for all games
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if game_id:
                cursor.execute(
                    "DELETE FROM user_achievement_progress WHERE user_name = ? AND game_id = ?",
                    (user_name, game_id),
                )
                cursor.execute(
                    "DELETE FROM user_game_progress WHERE user_name = ? AND game_id = ?",
                    (user_name, game_id),
                )
            else:
                cursor.execute(
                    "DELETE FROM user_achievement_progress WHERE user_name = ?", (user_name,)
                )
                cursor.execute("DELETE FROM user_game_progress WHERE user_name = ?", (user_name,))

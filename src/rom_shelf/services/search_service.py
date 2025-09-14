"""Search service - business logic for ROM filtering and search operations."""

import re
from typing import Any, Callable, Dict, List, Optional, Set

from ..models.rom_entry import ROMEntry


class SearchCriteria:
    """Search criteria for ROM filtering."""

    def __init__(self) -> None:
        """Initialize search criteria."""
        self.text_query: str = ""
        self.platform_filter: Set[str] = set()
        self.region_filter: Set[str] = set()
        self.language_filter: Set[str] = set()
        self.size_min: Optional[int] = None
        self.size_max: Optional[int] = None
        self.include_archives: bool = True
        self.include_multi_part: bool = True

    def is_empty(self) -> bool:
        """Check if search criteria is empty (no filters applied)."""
        return (
            not self.text_query
            and not self.platform_filter
            and not self.region_filter
            and not self.language_filter
            and self.size_min is None
            and self.size_max is None
        )

    def __str__(self) -> str:
        """String representation of search criteria."""
        parts = []
        if self.text_query:
            parts.append(f"text:'{self.text_query}'")
        if self.platform_filter:
            parts.append(f"platforms:{list(self.platform_filter)}")
        if self.region_filter:
            parts.append(f"regions:{list(self.region_filter)}")
        if self.language_filter:
            parts.append(f"languages:{list(self.language_filter)}")
        if self.size_min is not None:
            parts.append(f"size_min:{self.size_min}")
        if self.size_max is not None:
            parts.append(f"size_max:{self.size_max}")

        return f"SearchCriteria({', '.join(parts) if parts else 'empty'})"


class SearchService:
    """Service for ROM search and filtering operations."""

    def __init__(self) -> None:
        """Initialize the search service."""
        self._search_history: List[str] = []
        self._max_history_size = 50
        self._common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'rom', 'game', 'version'
        }

    # Core Search Functionality
    def filter_roms(self, roms: List[ROMEntry], criteria: SearchCriteria) -> List[ROMEntry]:
        """Filter ROM entries based on search criteria."""
        if criteria.is_empty():
            return roms.copy()

        filtered = []
        text_matcher = self._create_text_matcher(criteria.text_query) if criteria.text_query else None

        for rom in roms:
            if self._matches_criteria(rom, criteria, text_matcher):
                filtered.append(rom)

        return filtered

    def _matches_criteria(self, rom: ROMEntry, criteria: SearchCriteria, text_matcher: Optional[Callable]) -> bool:
        """Check if a ROM entry matches the search criteria."""
        # Platform filter
        if criteria.platform_filter and rom.platform_id not in criteria.platform_filter:
            return False

        # Region filter
        if criteria.region_filter and rom.region not in criteria.region_filter:
            return False

        # Language filter
        if criteria.language_filter and rom.language not in criteria.language_filter:
            return False

        # Size filters
        if criteria.size_min is not None and rom.file_size < criteria.size_min:
            return False
        if criteria.size_max is not None and rom.file_size > criteria.size_max:
            return False

        # Archive/Multi-part filters
        if not criteria.include_archives and rom.from_archive:
            return False
        if not criteria.include_multi_part and rom.is_multi_part:
            return False

        # Text search
        if text_matcher and not text_matcher(rom):
            return False

        return True

    def _create_text_matcher(self, query: str) -> Callable[[ROMEntry], bool]:
        """Create a text matching function for the given query."""
        # Normalize query
        query = query.strip().lower()
        if not query:
            return lambda rom: True

        # Check if it's a quoted exact match
        if query.startswith('"') and query.endswith('"') and len(query) > 2:
            exact_query = query[1:-1]
            return lambda rom: exact_query in self._get_searchable_text(rom)

        # Split into terms and create regex patterns
        terms = self._parse_search_terms(query)
        if not terms:
            return lambda rom: True

        # Create regex patterns for each term
        patterns = []
        for term in terms:
            # Escape special regex characters except * and ?
            escaped = re.escape(term).replace(r'\*', '.*').replace(r'\?', '.')
            patterns.append(re.compile(escaped, re.IGNORECASE))

        def matches_text(rom: ROMEntry) -> bool:
            searchable_text = self._get_searchable_text(rom)
            # All terms must match (AND logic)
            return all(pattern.search(searchable_text) for pattern in patterns)

        return matches_text

    def _get_searchable_text(self, rom: ROMEntry) -> str:
        """Get all searchable text from a ROM entry."""
        parts = [
            rom.display_name,
            rom.clean_name,
            rom.platform_id,
            rom.region or '',
            rom.language or '',
            rom.version or '',
            rom.revision or '',
            str(rom.file_path.stem),  # filename without extension
        ]

        return ' '.join(parts).lower()

    def _parse_search_terms(self, query: str) -> List[str]:
        """Parse search query into individual terms."""
        # Split by whitespace and filter out common words
        terms = query.split()
        filtered_terms = []

        for term in terms:
            term = term.strip()
            if term and term not in self._common_words and len(term) >= 2:
                filtered_terms.append(term)

        return filtered_terms

    # Search History Management
    def add_to_history(self, query: str) -> None:
        """Add a search query to history."""
        query = query.strip()
        if not query or len(query) < 2:
            return

        # Remove if already exists
        if query in self._search_history:
            self._search_history.remove(query)

        # Add to beginning
        self._search_history.insert(0, query)

        # Trim to max size
        if len(self._search_history) > self._max_history_size:
            self._search_history = self._search_history[:self._max_history_size]

    def get_search_history(self) -> List[str]:
        """Get search history."""
        return self._search_history.copy()

    def clear_search_history(self) -> None:
        """Clear search history."""
        self._search_history.clear()

    def get_search_suggestions(self, partial_query: str, roms: List[ROMEntry], limit: int = 10) -> List[str]:
        """Get search suggestions based on partial query and available ROM data."""
        partial_query = partial_query.lower().strip()
        if not partial_query:
            # Return recent searches if no partial query
            return self._search_history[:limit]

        suggestions = set()

        # Add matching history items
        for query in self._search_history:
            if partial_query in query.lower():
                suggestions.add(query)

        # Add matching ROM names
        for rom in roms:
            rom_text = self._get_searchable_text(rom)
            if partial_query in rom_text:
                # Add the ROM's display name
                suggestions.add(rom.display_name)

                # Add words from the ROM that match
                words = rom_text.split()
                for word in words:
                    if (len(word) >= len(partial_query) + 1 and
                        word.startswith(partial_query) and
                        word not in self._common_words):
                        suggestions.add(word)

        # Convert to sorted list
        suggestions_list = list(suggestions)
        suggestions_list.sort(key=lambda x: (len(x), x.lower()))

        return suggestions_list[:limit]

    # Advanced Search Features
    def create_criteria_from_text(self, query: str) -> SearchCriteria:
        """Create SearchCriteria from a text query with advanced syntax."""
        criteria = SearchCriteria()

        if not query.strip():
            return criteria

        # Parse advanced syntax: platform:n64, region:usa, etc.
        remaining_query = query

        # Extract platform filters
        platform_matches = re.findall(r'platform:(\w+)', query, re.IGNORECASE)
        for match in platform_matches:
            criteria.platform_filter.add(match.lower())
            remaining_query = re.sub(rf'platform:{re.escape(match)}\s*', '', remaining_query, flags=re.IGNORECASE)

        # Extract region filters
        region_matches = re.findall(r'region:(\w+)', query, re.IGNORECASE)
        for match in region_matches:
            criteria.region_filter.add(match.upper())
            remaining_query = re.sub(rf'region:{re.escape(match)}\s*', '', remaining_query, flags=re.IGNORECASE)

        # Extract language filters
        language_matches = re.findall(r'language:(\w+)', query, re.IGNORECASE)
        for match in language_matches:
            criteria.language_filter.add(match.lower())
            remaining_query = re.sub(rf'language:{re.escape(match)}\s*', '', remaining_query, flags=re.IGNORECASE)

        # Extract size filters
        size_matches = re.findall(r'size:([<>]=?)(\d+(?:\.\d+)?)(mb|kb|gb)?', query, re.IGNORECASE)
        for operator, value, unit in size_matches:
            size_bytes = self._parse_size(value, unit)
            if size_bytes:
                if operator in ['<', '<=']:
                    criteria.size_max = size_bytes
                elif operator in ['>', '>=']:
                    criteria.size_min = size_bytes
            remaining_query = re.sub(rf'size:{re.escape(operator)}{re.escape(value)}{re.escape(unit)}\s*',
                                   '', remaining_query, flags=re.IGNORECASE)

        # What's left is the text query
        criteria.text_query = remaining_query.strip()

        return criteria

    def _parse_size(self, value_str: str, unit: str) -> Optional[int]:
        """Parse size value with unit into bytes."""
        try:
            value = float(value_str)
            unit = unit.lower() if unit else 'mb'

            multipliers = {
                'b': 1,
                'kb': 1024,
                'mb': 1024 * 1024,
                'gb': 1024 * 1024 * 1024
            }

            return int(value * multipliers.get(unit, 1024 * 1024))
        except (ValueError, TypeError):
            return None

    # Statistics and Analysis
    def get_search_statistics(self, roms: List[ROMEntry]) -> Dict[str, Any]:
        """Get search statistics for a ROM collection."""
        if not roms:
            return {}

        platforms = {}
        regions = {}
        languages = {}
        extensions = {}
        sizes = []

        for rom in roms:
            # Platform stats
            platforms[rom.platform_id] = platforms.get(rom.platform_id, 0) + 1

            # Region stats
            if rom.region:
                regions[rom.region] = regions.get(rom.region, 0) + 1

            # Language stats
            if rom.language:
                languages[rom.language] = languages.get(rom.language, 0) + 1

            # Extension stats
            ext = rom.file_path.suffix.lower()
            if ext:
                extensions[ext] = extensions.get(ext, 0) + 1

            # Size stats
            if rom.file_size > 0:
                sizes.append(rom.file_size)

        # Calculate size statistics
        size_stats = {}
        if sizes:
            sizes.sort()
            size_stats = {
                'min': sizes[0],
                'max': sizes[-1],
                'median': sizes[len(sizes) // 2],
                'total': sum(sizes)
            }

        return {
            'total_roms': len(roms),
            'platforms': dict(sorted(platforms.items(), key=lambda x: x[1], reverse=True)),
            'regions': dict(sorted(regions.items(), key=lambda x: x[1], reverse=True)),
            'languages': dict(sorted(languages.items(), key=lambda x: x[1], reverse=True)),
            'extensions': dict(sorted(extensions.items(), key=lambda x: x[1], reverse=True)),
            'sizes': size_stats,
            'search_history_size': len(self._search_history)
        }

    def find_duplicates(self, roms: List[ROMEntry]) -> Dict[str, List[ROMEntry]]:
        """Find potential duplicate ROMs based on clean names."""
        duplicates = {}
        name_groups = {}

        # Group ROMs by clean name
        for rom in roms:
            clean_key = rom.clean_name.lower().strip()
            if clean_key not in name_groups:
                name_groups[clean_key] = []
            name_groups[clean_key].append(rom)

        # Find groups with multiple entries
        for clean_name, rom_list in name_groups.items():
            if len(rom_list) > 1:
                duplicates[clean_name] = rom_list

        return duplicates
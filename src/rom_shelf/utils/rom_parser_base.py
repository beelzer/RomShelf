"""Base classes and shared utilities for ROM naming convention parsers."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DumpQuality(Enum):
    """Universal dump quality status across all naming conventions."""

    VERIFIED_GOOD = "verified"  # [!] in GoodTools, [!] in TOSEC, no tag in No-Intro
    GOOD = "good"  # Default/no tag
    BAD = "bad"  # [b] in all conventions
    OVERDUMP = "overdump"  # [o] in all conventions
    UNDERDUMP = "underdump"  # [u] in No-Intro/TOSEC
    FIXED = "fixed"  # [f] in all conventions
    HACKED = "hacked"  # [h] in all conventions
    MODIFIED = "modified"  # [m] in No-Intro/TOSEC
    CRACKED = "cracked"  # [cr] in No-Intro, TOSEC
    PIRATED = "pirated"  # [p] in all conventions
    TRAINED = "trained"  # [t] in all conventions
    TRANSLATED = "translated"  # [T+]/[T-] in GoodTools, [tr] in No-Intro/TOSEC
    ALTERNATE = "alternate"  # [a] in GoodTools/TOSEC
    PENDING = "pending"  # [!p] in GoodTools
    VIRUS = "virus"  # [v] in TOSEC
    UNKNOWN = "unknown"


class ReleaseStatus(Enum):
    """ROM release/development status."""

    FINAL = "final"  # Standard release
    ALPHA = "alpha"
    BETA = "beta"
    DEMO = "demo"
    DEMO_KIOSK = "demo-kiosk"
    DEMO_PLAYABLE = "demo-playable"
    DEMO_ROLLING = "demo-rolling"
    DEMO_SLIDESHOW = "demo-slideshow"
    PREVIEW = "preview"
    PROTOTYPE = "prototype"
    SAMPLE = "sample"


class CopyrightStatus(Enum):
    """Copyright/license status."""

    COMMERCIAL = "commercial"
    PUBLIC_DOMAIN = "pd"
    SHAREWARE = "shareware"
    SHAREWARE_REGISTERED = "shareware-registered"
    FREEWARE = "freeware"
    CARDWARE = "cardware"
    LICENSEWARE = "licenseware"
    GIFTWARE = "giftware"
    UNLICENSED = "unlicensed"
    HOMEBREW = "homebrew"


@dataclass
class BaseROMMetadata:
    """Base container for parsed ROM metadata common across all conventions."""

    # Core attributes
    clean_name: str
    original_filename: str = ""

    # Quality/Dump info
    dump_quality: DumpQuality = DumpQuality.UNKNOWN

    # Release info
    release_status: ReleaseStatus = ReleaseStatus.FINAL
    release_number: int | None = None  # For numbered protos/betas/demos

    # Copyright info
    copyright_status: CopyrightStatus = CopyrightStatus.COMMERCIAL

    # Regional/Language
    regions: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)

    # Version info
    version: str | None = None
    revision: str | None = None

    # Media info
    media_type: str | None = None  # CD, DVD, Cart, Disk, Tape, etc.
    media_label: str | None = None  # Disc 1, Side A, etc.

    # Special flags
    is_bios: bool = False
    alt_version: str | None = None  # Alternative version indicator

    # Platform-specific features (Game Boy, etc.)
    special_features: dict[str, Any] = field(default_factory=dict)

    # Raw extracted tags for reference
    raw_tags: dict[str, list[str]] = field(default_factory=dict)

    # Convention-specific extra data
    extra_metadata: dict[str, Any] = field(default_factory=dict)


class BaseROMParser(ABC):
    """Abstract base class for ROM naming convention parsers."""

    # Shared region/country mappings used by multiple conventions
    # The key is the standardized name that will be returned
    REGION_MAPPINGS = {
        # Primary regions - use the most common short codes
        "USA": ["US", "U", "USA", "United States"],
        "Europe": ["EU", "E", "Europe", "EUR"],
        "Japan": ["JP", "J", "Japan", "JPN"],
        "World": ["W", "World"],
        # Countries
        "Argentina": ["AR", "Argentina"],
        "Asia": ["AS", "Asia"],
        "Australia": ["AU", "A", "Australia"],
        "Austria": ["AT", "Austria"],
        "Belgium": ["BE", "Belgium"],
        "Brazil": ["BR", "B", "Brazil"],
        "Canada": ["CA", "Canada"],
        "Chile": ["CL", "Chile"],
        "China": ["CN", "C", "China"],
        "Colombia": ["CO", "Colombia"],
        "Czech Republic": ["CZ", "Czech", "Czech Republic"],
        "Denmark": ["DK", "Z", "Denmark"],
        "Finland": ["FI", "Y", "Finland"],
        "France": ["FR", "F", "France"],
        "Germany": ["DE", "G", "Germany"],
        "Greece": ["GR", "Greece"],
        "Hong Kong": ["HK", "Hong Kong"],
        "Hungary": ["HU", "Hungary"],
        "India": ["IN", "India"],
        "Ireland": ["IE", "Ireland"],
        "Israel": ["IL", "Israel"],
        "Italy": ["IT", "I", "Italy"],
        "Korea": ["KR", "K", "Korea", "South Korea"],
        "Latin America": ["Latin America"],
        "Mexico": ["MX", "Mexico"],
        "Netherlands": ["NL", "D", "N", "Netherlands", "Dutch"],
        "New Zealand": ["NZ", "New Zealand"],
        "Norway": ["NO", "Norway"],
        "Poland": ["PL", "Poland"],
        "Portugal": ["PT", "Portugal"],
        "Russia": ["RU", "Russia"],
        "Scandinavia": ["Scandinavia"],
        "Singapore": ["SG", "Singapore"],
        "Slovakia": ["SK", "Slovakia"],
        "South Africa": ["ZA", "South Africa"],
        "Spain": ["ES", "S", "Spain"],
        "Sweden": ["SE", "X", "Sweden"],
        "Switzerland": ["CH", "Switzerland"],
        "Taiwan": ["TW", "Taiwan"],
        "Turkey": ["TR", "Turkey"],
        "United Kingdom": ["GB", "UK", "United Kingdom"],
        "Ukraine": ["UA", "Ukraine"],
        "Unknown": ["-", "Unknown"],
    }

    # Shared language codes (ISO 639-1 based)
    LANGUAGE_CODES = {
        # Two-letter codes with various capitalizations
        "ar": "Arabic",
        "Ar": "Arabic",
        "bg": "Bulgarian",
        "Bg": "Bulgarian",
        "ca": "Catalan",
        "Ca": "Catalan",
        "cs": "Czech",
        "Cs": "Czech",
        "cy": "Welsh",
        "Cy": "Welsh",
        "da": "Danish",
        "Da": "Danish",
        "de": "German",
        "De": "German",
        "el": "Greek",
        "El": "Greek",
        "en": "English",
        "En": "English",
        "es": "Spanish",
        "Es": "Spanish",
        "et": "Estonian",
        "Et": "Estonian",
        "eu": "Basque",
        "Eu": "Basque",
        "fa": "Persian",
        "Fa": "Persian",
        "fi": "Finnish",
        "Fi": "Finnish",
        "fr": "French",
        "Fr": "French",
        "ga": "Irish",
        "Ga": "Irish",
        "gd": "Gaelic",
        "Gd": "Gaelic",
        "he": "Hebrew",
        "He": "Hebrew",
        "hi": "Hindi",
        "Hi": "Hindi",
        "hr": "Croatian",
        "Hr": "Croatian",
        "hu": "Hungarian",
        "Hu": "Hungarian",
        "id": "Indonesian",
        "Id": "Indonesian",
        "is": "Icelandic",
        "Is": "Icelandic",
        "it": "Italian",
        "It": "Italian",
        "ja": "Japanese",
        "Ja": "Japanese",
        "ko": "Korean",
        "Ko": "Korean",
        "lt": "Lithuanian",
        "Lt": "Lithuanian",
        "lv": "Latvian",
        "Lv": "Latvian",
        "ms": "Malay",
        "Ms": "Malay",
        "nl": "Dutch",
        "Nl": "Dutch",
        "no": "Norwegian",
        "No": "Norwegian",
        "pl": "Polish",
        "Pl": "Polish",
        "pt": "Portuguese",
        "Pt": "Portuguese",
        "ro": "Romanian",
        "Ro": "Romanian",
        "ru": "Russian",
        "Ru": "Russian",
        "sk": "Slovak",
        "Sk": "Slovak",
        "sl": "Slovenian",
        "Sl": "Slovenian",
        "sq": "Albanian",
        "Sq": "Albanian",
        "sr": "Serbian",
        "Sr": "Serbian",
        "sv": "Swedish",
        "Sv": "Swedish",
        "ta": "Tamil",
        "Ta": "Tamil",
        "te": "Telugu",
        "Te": "Telugu",
        "th": "Thai",
        "Th": "Thai",
        "tr": "Turkish",
        "Tr": "Turkish",
        "uk": "Ukrainian",
        "Uk": "Ukrainian",
        "ur": "Urdu",
        "Ur": "Urdu",
        "vi": "Vietnamese",
        "Vi": "Vietnamese",
        "yi": "Yiddish",
        "Yi": "Yiddish",
        "zh": "Chinese",
        "Zh": "Chinese",
        # Multi-language indicators
        "M2": "Two languages",
        "M3": "Three languages",
        "M4": "Four languages",
        "M5": "Five languages",
        "M6": "Six languages",
        "M7": "Seven languages",
        "M8": "Eight languages",
        "M9": "Nine languages",
    }

    # Common gaming platforms
    SUPPORTED_PLATFORMS = {
        # Nintendo
        "nes",
        "snes",
        "n64",
        "gamecube",
        "wii",
        "wiiu",
        "switch",
        "game_boy",
        "game_boy_color",
        "game_boy_advance",
        "ds",
        "3ds",
        "virtual_boy",
        "pokemon_mini",
        # Sega
        "master_system",
        "sega_genesis",
        "sega_cd",
        "sega_32x",
        "saturn",
        "dreamcast",
        "game_gear",
        "sg-1000",
        "sega_pico",
        # Sony
        "playstation",
        "ps2",
        "ps3",
        "ps4",
        "ps5",
        "psp",
        "ps_vita",
        # Microsoft
        "xbox",
        "xbox_360",
        "xbox_one",
        "xbox_series",
        # Atari
        "atari_2600",
        "atari_5200",
        "atari_7800",
        "atari_jaguar",
        "atari_lynx",
        # Other
        "turbografx_16",
        "pc_engine",
        "neo_geo",
        "neo_geo_pocket",
        "neo_geo_pocket_color",
        "wonderswan",
        "wonderswan_color",
        "3do",
        "amiga",
        "amstrad_cpc",
        "commodore_64",
        "msx",
        "msx2",
        "zx_spectrum",
        "colecovision",
        "intellivision",
        "odyssey2",
        "vectrex",
    }

    def __init__(self, platform_id: str | None = None):
        """Initialize parser with optional platform hint."""
        self.platform_id = platform_id

    @abstractmethod
    def parse(self, filename: str) -> BaseROMMetadata:
        """Parse a ROM filename and extract metadata.

        Args:
            filename: ROM filename to parse

        Returns:
            Metadata object with extracted information
        """
        pass

    @abstractmethod
    def get_format_name(self) -> str:
        """Get the name of this naming convention format."""
        pass

    @abstractmethod
    def can_parse(self, filename: str) -> bool:
        """Check if this parser can handle the given filename.

        Args:
            filename: ROM filename to check

        Returns:
            True if this parser can handle the file
        """
        pass

    def extract_clean_name(self, filename: str) -> str:
        """Extract clean game name without tags and metadata.

        Args:
            filename: ROM filename

        Returns:
            Clean game name
        """
        # Remove file extension
        name = filename.rsplit(".", 1)[0] if "." in filename else filename

        # Remove all bracketed tags [...]
        name = re.sub(r"\s*\[[^\]]*\]\s*", " ", name)

        # Remove all parenthetical tags (...)
        name = re.sub(r"\s*\([^)]*\)\s*", " ", name)

        # Clean up multiple spaces
        name = re.sub(r"\s+", " ", name)

        return name.strip()

    def extract_all_tags(self, filename: str) -> dict[str, list[str]]:
        """Extract all bracketed and parenthetical tags.

        Args:
            filename: ROM filename

        Returns:
            Dictionary with 'brackets' and 'parentheses' lists
        """
        tags = {"brackets": [], "parentheses": []}

        # Extract bracketed tags
        for match in re.finditer(r"\[([^\]]+)\]", filename):
            tags["brackets"].append(match.group(1))

        # Extract parenthetical tags
        for match in re.finditer(r"\(([^)]+)\)", filename):
            tags["parentheses"].append(match.group(1))

        return tags

    def parse_version(self, filename: str) -> str | None:
        """Parse version information from filename.

        Args:
            filename: ROM filename

        Returns:
            Version string or None
        """
        # Common patterns: (v1.0), (V1.1), (v2.0a), etc.
        ver_match = re.search(r"\([Vv]([\d.]+[a-zA-Z]*)\)", filename)
        if ver_match:
            return ver_match.group(1)
        return None

    def parse_revision(self, filename: str) -> str | None:
        """Parse revision information from filename.

        Args:
            filename: ROM filename

        Returns:
            Revision string or None
        """
        # Pattern: (Rev 1), (Rev A), (REV 2), etc.
        rev_match = re.search(r"\(Rev\s+([A-Z0-9]+)\)", filename, re.IGNORECASE)
        if rev_match:
            return rev_match.group(1)
        return None

    def check_tag(self, filename: str, pattern: str, case_insensitive: bool = False) -> bool:
        """Check if a tag pattern exists in filename.

        Args:
            filename: ROM filename
            pattern: Regular expression pattern to match
            case_insensitive: Whether to ignore case

        Returns:
            True if pattern found
        """
        flags = re.IGNORECASE if case_insensitive else 0
        return bool(re.search(pattern, filename, flags))

    def normalize_region(self, region_code: str) -> str | None:
        """Normalize a region code or name to standard format.

        Args:
            region_code: Region code or name to normalize

        Returns:
            Normalized region name or None if not recognized
        """
        region_upper = region_code.upper()
        region_title = region_code.title()

        for standard_name, variants in self.REGION_MAPPINGS.items():
            if region_code in variants or region_upper in variants or region_title in variants:
                return standard_name

        return None

    def normalize_language(self, lang_code: str) -> str | None:
        """Normalize a language code to standard format.

        Args:
            lang_code: Language code to normalize

        Returns:
            Normalized language name or None if not recognized
        """
        # Check both lowercase and capitalized versions
        return self.LANGUAGE_CODES.get(lang_code) or self.LANGUAGE_CODES.get(lang_code.capitalize())

    def to_dict(self, metadata: BaseROMMetadata) -> dict[str, Any]:
        """Convert metadata object to dictionary format.

        Args:
            metadata: Metadata object to convert

        Returns:
            Dictionary representation of metadata
        """
        result = {
            "clean_name": metadata.clean_name,
            "dump_quality": metadata.dump_quality.value if metadata.dump_quality else None,
            "release_status": metadata.release_status.value if metadata.release_status else None,
            "copyright_status": metadata.copyright_status.value
            if metadata.copyright_status
            else None,
        }

        # Add regions if present
        if metadata.regions:
            result["regions"] = metadata.regions
            result["region"] = (
                metadata.regions[0] if len(metadata.regions) == 1 else ", ".join(metadata.regions)
            )

        # Add languages if present
        if metadata.languages:
            result["languages"] = metadata.languages
            result["language"] = (
                metadata.languages[0]
                if len(metadata.languages) == 1
                else ", ".join(metadata.languages)
            )

        # Version info
        if metadata.version:
            result["version"] = metadata.version
        if metadata.revision:
            result["revision"] = metadata.revision

        # Media info
        if metadata.media_type:
            result["media_type"] = metadata.media_type
        if metadata.media_label:
            result["media_label"] = metadata.media_label

        # Special flags
        if metadata.is_bios:
            result["is_bios"] = True
        if metadata.alt_version:
            result["alt_version"] = metadata.alt_version

        # Add special features if any
        if metadata.special_features:
            result.update(metadata.special_features)

        # Add extra metadata if any
        if metadata.extra_metadata:
            result.update(metadata.extra_metadata)

        return result


class ParserRegistry:
    """Registry for managing multiple ROM parsers."""

    def __init__(self):
        """Initialize the parser registry."""
        self.parsers: list[BaseROMParser] = []

    def register(self, parser: BaseROMParser) -> None:
        """Register a new parser.

        Args:
            parser: Parser instance to register
        """
        self.parsers.append(parser)

    def parse(self, filename: str, platform_id: str | None = None) -> dict[str, Any] | None:
        """Parse a filename using the appropriate parser.

        Args:
            filename: ROM filename to parse
            platform_id: Optional platform hint

        Returns:
            Metadata dictionary or None if no parser matches
        """
        # Try parsers in order of registration
        for parser in self.parsers:
            if parser.can_parse(filename):
                metadata = parser.parse(filename)
                result = parser.to_dict(metadata)
                # Add the parser format name to the metadata
                result["parser_format"] = parser.get_format_name()
                return result

        return None

    def get_parser_for_file(self, filename: str) -> BaseROMParser | None:
        """Get the appropriate parser for a filename.

        Args:
            filename: ROM filename to check

        Returns:
            Parser instance or None if no match
        """
        for parser in self.parsers:
            if parser.can_parse(filename):
                return parser
        return None

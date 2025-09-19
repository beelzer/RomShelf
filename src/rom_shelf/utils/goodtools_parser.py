"""GoodTools ROM naming convention parser.

This module parses ROM filenames following the GoodTools naming conventions,
extracting metadata tags for ROM quality, region, language, and other attributes.

Reference: https://emulation.gametechwiki.com/index.php/GoodTools
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DumpQuality(Enum):
    """ROM dump quality status."""

    VERIFIED_GOOD = "!"  # [!] - Verified Good Dump
    BAD = "b"  # [b] - Bad Dump
    OVERDUMP = "o"  # [o] - Overdump
    PENDING = "!p"  # [!p] - Pending Dump
    ALTERNATE = "a"  # [a] - Alternate
    FIXED = "f"  # [f] - Fixed
    UNKNOWN = ""  # No tag or unknown quality


class ROMType(Enum):
    """ROM type classification."""

    ORIGINAL = "original"
    HACK = "hack"  # [h]
    TRANSLATION = "translation"  # [T+] or [T-]
    PIRATE = "pirate"  # [p]
    TRAINED = "trained"  # [t]
    HOMEBREW = "homebrew"


@dataclass
class GoodToolsMetadata:
    """Container for parsed GoodTools metadata."""

    # Core attributes
    clean_name: str
    dump_quality: DumpQuality = DumpQuality.UNKNOWN
    rom_type: ROMType = ROMType.ORIGINAL

    # Regional/Language
    regions: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)

    # Version info
    revision: str | None = None
    version: str | None = None
    is_beta: bool = False
    is_prototype: bool = False
    is_demo: bool = False
    is_alpha: bool = False
    is_sample: bool = False
    is_bios: bool = False

    # Technical attributes
    is_unlicensed: bool = False
    is_multicart: bool = False
    cart_name: str | None = None  # For multicarts like "4-in-1"

    # Translation info
    translation_language: str | None = None
    translation_version: str | None = None
    translation_author: str | None = None
    is_old_translation: bool = False  # [T-]

    # Platform-specific
    sgb_enhanced: bool = False  # Super Game Boy
    gb_compatible: bool = False  # Game Boy
    cgb_enhanced: bool = False  # Color Game Boy
    rumble_support: bool = False

    # Additional metadata
    raw_tags: dict[str, Any] = field(default_factory=dict)


class GoodToolsParser:
    """Parser for GoodTools ROM naming conventions."""

    # GoodTools supported platforms (systems that use GoodTools naming)
    SUPPORTED_PLATFORMS = {
        # Nintendo
        "nes",
        "snes",
        "nintendo_64",
        "game_boy",
        "game_boy_advance",
        "game_boy_color",
        "virtual_boy",
        # Sega
        "sega_genesis",
        "sega_master_system",
        "game_gear",
        "sega_32x",
        "sega_cd",
        # Atari
        "atari_2600",
        "atari_5200",
        "atari_7800",
        "atari_jaguar",
        "atari_lynx",
        # Other
        "turbografx_16",
        "colecovision",
        "intellivision",
        "wonderswan",
        "wonderswan_color",
        "neo_geo_pocket",
        "neo_geo_pocket_color",
    }

    # Region codes mapping
    REGION_CODES = {
        # Single letter codes
        "U": "USA",
        "E": "Europe",
        "J": "Japan",
        "A": "Australia",
        "G": "Germany",
        "F": "France",
        "I": "Italy",
        "S": "Spain",
        "K": "Korea",
        "C": "China",
        "B": "Brazil",
        "N": "Netherlands",
        "D": "Netherlands",  # Dutch
        "X": "Sweden",
        "Y": "Finland",
        "Z": "Denmark",
        "W": "World",
        # Multi-region codes
        "JUE": ["Japan", "USA", "Europe"],
        "UE": ["USA", "Europe"],
        "JU": ["Japan", "USA"],
        # Numeric codes
        "1": "Japan & Korea",
        "4": "USA & Brazil NTSC",
        "5": "NTSC",
        "8": "PAL",
    }

    # Language codes (2-letter ISO-like codes)
    LANGUAGE_CODES = {
        "En": "English",
        "Fr": "French",
        "De": "German",
        "Es": "Spanish",
        "It": "Italian",
        "Pt": "Portuguese",
        "Ja": "Japanese",
        "Ko": "Korean",
        "Zh": "Chinese",
        "Ru": "Russian",
        "Nl": "Dutch",
        "Sv": "Swedish",
        "No": "Norwegian",
        "Da": "Danish",
        "Fi": "Finnish",
        "Pl": "Polish",
        "Ar": "Arabic",
        "He": "Hebrew",
        "Tr": "Turkish",
        "Gr": "Greek",
        "Hu": "Hungarian",
        "Cs": "Czech",
        "Ro": "Romanian",
        "Ca": "Catalan",
    }

    def __init__(self, platform_id: str | None = None):
        """Initialize parser with optional platform hint.

        Args:
            platform_id: Optional platform identifier to optimize parsing
        """
        self.platform_id = platform_id

    def is_goodtools_platform(self, platform_id: str) -> bool:
        """Check if a platform uses GoodTools naming conventions.

        Args:
            platform_id: Platform identifier

        Returns:
            True if platform uses GoodTools conventions
        """
        return platform_id.lower() in self.SUPPORTED_PLATFORMS

    def parse(self, filename: str) -> GoodToolsMetadata:
        """Parse a ROM filename for GoodTools metadata.

        Args:
            filename: ROM filename to parse

        Returns:
            GoodToolsMetadata object with extracted information
        """
        metadata = GoodToolsMetadata(clean_name="")

        # Extract clean name first
        metadata.clean_name = self._extract_clean_name(filename)

        # Parse dump quality tags [!], [b], [o], etc.
        metadata.dump_quality = self._parse_dump_quality(filename)

        # Parse ROM type tags [h], [p], [t], [T+], [T-]
        metadata.rom_type, translation_info = self._parse_rom_type(filename)
        if translation_info:
            metadata.translation_language = translation_info.get("language")
            metadata.translation_version = translation_info.get("version")
            metadata.translation_author = translation_info.get("author")
            metadata.is_old_translation = translation_info.get("is_old", False)

        # Parse regions
        metadata.regions = self._parse_regions(filename)

        # Parse languages
        metadata.languages = self._parse_languages(filename)

        # Parse version info
        metadata.revision = self._parse_revision(filename)
        metadata.version = self._parse_version(filename)

        # Parse release status
        metadata.is_prototype = self._check_tag(
            filename, r"\(Proto(?:type)?.*?\)", case_insensitive=True
        )
        metadata.is_beta = self._check_tag(filename, r"\(Beta.*?\)", case_insensitive=True)
        metadata.is_alpha = self._check_tag(filename, r"\(Alpha.*?\)", case_insensitive=True)
        metadata.is_demo = self._check_tag(filename, r"\(Demo.*?\)", case_insensitive=True)
        metadata.is_sample = self._check_tag(filename, r"\(Sample.*?\)", case_insensitive=True)
        metadata.is_bios = self._check_tag(filename, r"\[BIOS\]", case_insensitive=True)

        # Parse licensing
        metadata.is_unlicensed = self._check_tag(
            filename, r"\(Unl(?:icensed)?\)", case_insensitive=True
        )

        # Parse multicart info
        multicart_match = re.search(r"\((\d+)-?in-?(\d+)\)", filename, re.IGNORECASE)
        if multicart_match:
            metadata.is_multicart = True
            metadata.cart_name = multicart_match.group(0).strip("()")

        # Platform-specific features
        metadata.sgb_enhanced = self._check_tag(
            filename, r"\(SGB Enhanced\)", case_insensitive=True
        )
        metadata.gb_compatible = self._check_tag(
            filename, r"\(GB Compatible\)", case_insensitive=True
        )
        metadata.cgb_enhanced = self._check_tag(
            filename, r"\(CGB.*Enhanced\)", case_insensitive=True
        )
        metadata.rumble_support = self._check_tag(
            filename, r"\(Rumble.*Version\)", case_insensitive=True
        )

        # Store all bracketed tags for reference
        metadata.raw_tags = self._extract_all_tags(filename)

        return metadata

    def _extract_clean_name(self, filename: str) -> str:
        """Extract clean game name without tags and metadata.

        Args:
            filename: ROM filename

        Returns:
            Clean game name
        """
        # Remove file extension
        name = filename.rsplit(".", 1)[0]

        # Remove all bracketed tags [...]
        name = re.sub(r"\s*\[[^\]]*\]\s*", " ", name)

        # Remove all parenthetical tags (...)
        name = re.sub(r"\s*\([^)]*\)\s*", " ", name)

        # Clean up multiple spaces
        name = re.sub(r"\s+", " ", name)

        return name.strip()

    def _parse_dump_quality(self, filename: str) -> DumpQuality:
        """Parse dump quality tags.

        Args:
            filename: ROM filename

        Returns:
            DumpQuality enum value
        """
        # Check for verified good dump first (highest priority)
        if re.search(r"\[!\]", filename):
            return DumpQuality.VERIFIED_GOOD
        if re.search(r"\[!p\]", filename):
            return DumpQuality.PENDING
        if re.search(r"\[b\d*\]", filename):  # [b] or [b1], [b2], etc.
            return DumpQuality.BAD
        if re.search(r"\[o\d*\]", filename):  # [o] or [o1], [o2], etc.
            return DumpQuality.OVERDUMP
        if re.search(r"\[a\d*\]", filename):  # [a] or [a1], [a2], etc.
            return DumpQuality.ALTERNATE
        if re.search(r"\[f\d*\]", filename):  # [f] or [f1], [f2], etc.
            return DumpQuality.FIXED

        return DumpQuality.UNKNOWN

    def _parse_rom_type(self, filename: str) -> tuple[ROMType, dict[str, Any] | None]:
        """Parse ROM type tags.

        Args:
            filename: ROM filename

        Returns:
            Tuple of (ROMType, translation_info dict or None)
        """
        translation_info = None

        # Check for translations first (can have additional info)
        trans_match = re.search(r"\[T([+-])([^]]*)\]", filename)
        if trans_match:
            is_old = trans_match.group(1) == "-"
            trans_details = trans_match.group(2)

            translation_info = {"is_old": is_old}

            # Parse translation details (e.g., T+Eng1.0_TranslatorName)
            if trans_details:
                # Language code (first 2-3 letters)
                lang_match = re.match(r"([A-Za-z]{2,3})", trans_details)
                if lang_match:
                    lang_code = lang_match.group(1).capitalize()
                    translation_info["language"] = self.LANGUAGE_CODES.get(lang_code, lang_code)

                # Version number
                ver_match = re.search(r"(\d+(?:\.\d+)*)", trans_details)
                if ver_match:
                    translation_info["version"] = ver_match.group(1)

                # Translator/group name (after underscore)
                author_match = re.search(r"_(.+)$", trans_details)
                if author_match:
                    translation_info["author"] = author_match.group(1)

            return ROMType.TRANSLATION, translation_info

        # Check other ROM types
        if re.search(r"\[h\d*[^\]]*\]", filename):  # [h], [h1], [hFFE], etc.
            return ROMType.HACK, None
        if re.search(r"\[p\d*\]", filename):  # [p], [p1], [p2], etc.
            return ROMType.PIRATE, None
        if re.search(r"\[t\d*\]", filename):  # [t], [t1], [t2], etc.
            return ROMType.TRAINED, None

        # Check for homebrew indicators
        if re.search(r"\(PD\)", filename) or re.search(r"\(Homebrew\)", filename):
            return ROMType.HOMEBREW, None

        return ROMType.ORIGINAL, None

    def _parse_regions(self, filename: str) -> list[str]:
        """Parse region codes from filename.

        Args:
            filename: ROM filename

        Returns:
            List of region names
        """
        regions = []
        seen = set()

        # First check for full region names in parentheses
        full_regions = [
            "USA",
            "Europe",
            "Japan",
            "World",
            "Asia",
            "Australia",
            "Germany",
            "France",
            "Spain",
            "Italy",
            "Netherlands",
            "Sweden",
            "Brazil",
            "Korea",
            "China",
            "Russia",
            "Canada",
        ]

        for region in full_regions:
            if re.search(rf"\({region}(?:[,\s]|\)|$)", filename, re.IGNORECASE):
                if region not in seen:
                    regions.append(region)
                    seen.add(region)

        # Check for single-letter region codes in parentheses
        # Match patterns like (U), (J), (JUE), etc.
        code_match = re.search(r"\(([UJEKAFGISCBWDXYZ]+)\)", filename)
        if code_match:
            codes = code_match.group(1)

            # Check if it's a known multi-region code
            if codes in self.REGION_CODES:
                region_list = self.REGION_CODES[codes]
                if isinstance(region_list, list):
                    for region in region_list:
                        if region not in seen:
                            regions.append(region)
                            seen.add(region)
                else:
                    if region_list not in seen:
                        regions.append(region_list)
                        seen.add(region_list)
            else:
                # Parse individual letters
                for letter in codes:
                    if letter in self.REGION_CODES:
                        region = self.REGION_CODES[letter]
                        if region not in seen:
                            regions.append(region)
                            seen.add(region)

        # Check for numeric region codes
        for num_code in ["1", "4", "5", "8"]:
            if re.search(rf"\({num_code}\)", filename):
                region = self.REGION_CODES.get(num_code)
                if region and region not in seen:
                    regions.append(region)
                    seen.add(region)

        return regions

    def _parse_languages(self, filename: str) -> list[str]:
        """Parse language codes from filename.

        Args:
            filename: ROM filename

        Returns:
            List of language names
        """
        languages = []
        seen = set()

        # Check for multi-language indicators
        multi_match = re.search(r"\(M(\d+)\)", filename)
        if multi_match:
            num_langs = multi_match.group(1)
            languages.append(f"Multi-{num_langs}")
            return languages

        if re.search(r"\(Multi(?:-\d+)?\)", filename, re.IGNORECASE):
            languages.append("Multi")

        # Look for explicit language codes
        # Pattern: (En), (En,Fr), (En+Fr), (En-Fr)
        for separator in [",", "+", "-"]:
            pattern = rf"\(([A-Z][a-z](?:{re.escape(separator)}[A-Z][a-z])*)\)"
            for match in re.finditer(pattern, filename):
                lang_str = match.group(1)
                for lang_code in re.split(rf"[{re.escape(separator)}]", lang_str):
                    lang_code = lang_code.strip()
                    if lang_code in self.LANGUAGE_CODES:
                        lang_name = self.LANGUAGE_CODES[lang_code]
                        if lang_name not in seen:
                            languages.append(lang_name)
                            seen.add(lang_name)

        return languages

    def _parse_revision(self, filename: str) -> str | None:
        """Parse revision information.

        Args:
            filename: ROM filename

        Returns:
            Revision string or None
        """
        # Pattern: (Rev A), (REV 1), (Rev1), etc.
        rev_match = re.search(r"\(Rev\s*([A-Z0-9]+)\)", filename, re.IGNORECASE)
        if rev_match:
            return rev_match.group(1)
        return None

    def _parse_version(self, filename: str) -> str | None:
        """Parse version information.

        Args:
            filename: ROM filename

        Returns:
            Version string or None
        """
        # Pattern: (V1.0), (v1.2a), etc.
        ver_match = re.search(r"\([Vv](\d+(?:\.\d+)*[a-zA-Z]*)\)", filename)
        if ver_match:
            return ver_match.group(1)
        return None

    def _check_tag(self, filename: str, pattern: str, case_insensitive: bool = False) -> bool:
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

    def _extract_all_tags(self, filename: str) -> dict[str, list[str]]:
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

    def format_metadata(self, metadata: GoodToolsMetadata) -> str:
        """Format metadata as a human-readable string.

        Args:
            metadata: GoodToolsMetadata object

        Returns:
            Formatted string representation
        """
        lines = [f"Game: {metadata.clean_name}"]

        if metadata.dump_quality != DumpQuality.UNKNOWN:
            quality_desc = {
                DumpQuality.VERIFIED_GOOD: "Verified Good Dump [!]",
                DumpQuality.BAD: "Bad Dump [b]",
                DumpQuality.OVERDUMP: "Overdump [o]",
                DumpQuality.PENDING: "Pending Dump [!p]",
                DumpQuality.ALTERNATE: "Alternate [a]",
                DumpQuality.FIXED: "Fixed [f]",
            }
            lines.append(f"Quality: {quality_desc.get(metadata.dump_quality, 'Unknown')}")

        if metadata.rom_type != ROMType.ORIGINAL:
            lines.append(f"Type: {metadata.rom_type.value.title()}")

        if metadata.regions:
            lines.append(f"Region: {', '.join(metadata.regions)}")

        if metadata.languages:
            lines.append(f"Language: {', '.join(metadata.languages)}")

        if metadata.version:
            lines.append(f"Version: {metadata.version}")
        elif metadata.revision:
            lines.append(f"Revision: {metadata.revision}")

        status = []
        if metadata.is_prototype:
            status.append("Prototype")
        if metadata.is_beta:
            status.append("Beta")
        if metadata.is_alpha:
            status.append("Alpha")
        if metadata.is_demo:
            status.append("Demo")
        if metadata.is_unlicensed:
            status.append("Unlicensed")

        if status:
            lines.append(f"Status: {', '.join(status)}")

        if metadata.translation_language:
            trans_info = f"Translation: {metadata.translation_language}"
            if metadata.translation_version:
                trans_info += f" v{metadata.translation_version}"
            if metadata.translation_author:
                trans_info += f" by {metadata.translation_author}"
            if metadata.is_old_translation:
                trans_info += " (Old)"
            lines.append(trans_info)

        return "\n".join(lines)

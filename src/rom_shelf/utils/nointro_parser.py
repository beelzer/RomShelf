"""No-Intro ROM naming convention parser.

This module parses ROM filenames following the No-Intro naming conventions,
extracting metadata tags for region, language, version, and other attributes.

Reference: https://wiki.no-intro.org/index.php?title=Naming_Convention
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ReleaseStatus(Enum):
    """ROM release status classification."""

    FINAL = "final"  # Standard release
    PROTO = "proto"  # (Proto) or (Proto 1), (Proto 2), etc.
    BETA = "beta"  # (Beta) or (Beta 1), (Beta 2), etc.
    DEMO = "demo"  # (Demo) or (Demo 1), (Demo 2), etc.
    SAMPLE = "sample"  # (Sample)
    ALPHA = "alpha"  # (Alpha)


class DumpStatus(Enum):
    """ROM dump status."""

    GOOD = ""  # No tag means good dump
    BAD = "[b]"  # Bad dump
    OVERDUMP = "[o]"  # Overdump
    UNDERDUMP = "[u]"  # Underdump
    CRACKED = "[cr]"  # Cracked dump
    FIXED = "[f]"  # Fixed dump
    HACKED = "[h]"  # Hacked dump
    MODIFIED = "[m]"  # Modified dump
    PIRATED = "[p]"  # Pirated dump
    TRAINED = "[t]"  # Trained dump
    TRANSLATED = "[tr]"  # Translated dump


@dataclass
class NoIntroMetadata:
    """Container for parsed No-Intro metadata."""

    # Core attributes
    clean_name: str
    bios_flag: bool = False  # [BIOS] flag at the beginning

    # Regional/Language
    regions: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)

    # Version info
    version: str | None = None  # (v1.0), (v1.1), etc.
    revision: str | None = None  # (Rev 1), (Rev A), etc.

    # Release status
    release_status: ReleaseStatus = ReleaseStatus.FINAL
    status_number: int | None = None  # For numbered protos/betas

    # Dump status
    dump_status: DumpStatus = DumpStatus.GOOD

    # Special flags
    is_unlicensed: bool = False  # (Unl)
    is_pirate: bool = False  # (Pirate)
    is_promo: bool = False  # (Promo)
    is_not_for_sale: bool = False  # (NFS)
    alt_version: str | None = None  # (Alt), (Alt 1), etc.

    # Platform-specific
    media_type: str | None = None  # (CD), (DVD), (UMD), etc.
    media_label: str | None = None  # Disc label for multi-disc

    # Serial/Product codes
    serial_code: str | None = None  # Product code in the name

    # Additional metadata
    raw_tags: dict[str, Any] = field(default_factory=dict)


class NoIntroParser:
    """Parser for No-Intro ROM naming conventions."""

    # No-Intro uses full region names (not codes like GoodTools)
    REGION_NAMES = {
        "Argentina",
        "Asia",
        "Australia",
        "Austria",
        "Belgium",
        "Brazil",
        "Canada",
        "Chile",
        "China",
        "Colombia",
        "Czech",
        "Denmark",
        "Europe",
        "Finland",
        "France",
        "Germany",
        "Greece",
        "Hong Kong",
        "Hungary",
        "India",
        "Ireland",
        "Israel",
        "Italy",
        "Japan",
        "Korea",
        "Latin America",
        "Mexico",
        "Netherlands",
        "New Zealand",
        "Norway",
        "Poland",
        "Portugal",
        "Russia",
        "Scandinavia",
        "Singapore",
        "Slovakia",
        "South Africa",
        "Spain",
        "Sweden",
        "Switzerland",
        "Taiwan",
        "Turkey",
        "UK",
        "Ukraine",
        "USA",
        "World",
        "Unknown",
    }

    # ISO 639-1 two-letter language codes (No-Intro format: first letter uppercase)
    LANGUAGE_CODES = {
        "Ar": "Arabic",
        "Bg": "Bulgarian",
        "Ca": "Catalan",
        "Cs": "Czech",
        "Cy": "Welsh",
        "Da": "Danish",
        "De": "German",
        "El": "Greek",
        "En": "English",
        "Es": "Spanish",
        "Et": "Estonian",
        "Eu": "Basque",
        "Fa": "Persian",
        "Fi": "Finnish",
        "Fr": "French",
        "Ga": "Irish",
        "He": "Hebrew",
        "Hi": "Hindi",
        "Hr": "Croatian",
        "Hu": "Hungarian",
        "Id": "Indonesian",
        "Is": "Icelandic",
        "It": "Italian",
        "Ja": "Japanese",
        "Ko": "Korean",
        "Lt": "Lithuanian",
        "Lv": "Latvian",
        "Ms": "Malay",
        "Nl": "Dutch",
        "No": "Norwegian",
        "Pl": "Polish",
        "Pt": "Portuguese",
        "Ro": "Romanian",
        "Ru": "Russian",
        "Sk": "Slovak",
        "Sl": "Slovenian",
        "Sr": "Serbian",
        "Sv": "Swedish",
        "Ta": "Tamil",
        "Te": "Telugu",
        "Th": "Thai",
        "Tr": "Turkish",
        "Uk": "Ukrainian",
        "Vi": "Vietnamese",
        "Zh": "Chinese",
    }

    # Platforms that typically use No-Intro naming
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
        "genesis",
        "sega_cd",
        "32x",
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
        # Atari
        "atari_2600",
        "atari_5200",
        "atari_7800",
        "atari_jaguar",
        "atari_lynx",
        # Other
        "turbografx_16",
        "neo_geo",
        "wonderswan",
        "wonderswan_color",
        "3do",
        "amiga",
        "amstrad_cpc",
        "commodore_64",
        "msx",
        "msx2",
        "pc_engine",
        "zx_spectrum",
        "colecovision",
        "intellivision",
        "odyssey2",
        "vectrex",
        "fairchild_channel_f",
        "bally_astrocade",
        "arcadia_2001",
        "supervision",
        "gamate",
        "watara_supervision",
        "epoch_cassette_vision",
        "epoch_super_cassette_vision",
    }

    def __init__(self, platform_id: str | None = None):
        """Initialize parser with optional platform hint.

        Args:
            platform_id: Optional platform identifier to optimize parsing
        """
        self.platform_id = platform_id

    def is_nointro_platform(self, platform_id: str) -> bool:
        """Check if a platform typically uses No-Intro naming conventions.

        Args:
            platform_id: Platform identifier

        Returns:
            True if platform uses No-Intro conventions
        """
        return platform_id.lower() in self.SUPPORTED_PLATFORMS

    def parse(self, filename: str) -> NoIntroMetadata:
        """Parse a ROM filename for No-Intro metadata.

        Args:
            filename: ROM filename to parse

        Returns:
            NoIntroMetadata object with extracted information
        """
        metadata = NoIntroMetadata(clean_name="")

        # Check for BIOS flag at the beginning
        if filename.startswith("[BIOS]"):
            metadata.bios_flag = True
            filename = filename[6:].strip()

        # Extract clean name first (everything before first parenthesis)
        metadata.clean_name = self._extract_clean_name(filename)

        # Parse regions (mandatory in No-Intro)
        metadata.regions = self._parse_regions(filename)

        # Parse languages
        metadata.languages = self._parse_languages(filename)

        # Parse version/revision
        metadata.version = self._parse_version(filename)
        metadata.revision = self._parse_revision(filename)

        # Parse release status
        metadata.release_status, metadata.status_number = self._parse_release_status(filename)

        # Parse special flags
        metadata.is_unlicensed = self._check_tag(filename, r"\(Unl\)")
        metadata.is_pirate = self._check_tag(filename, r"\(Pirate\)")
        metadata.is_promo = self._check_tag(filename, r"\(Promo\)")
        metadata.is_not_for_sale = self._check_tag(filename, r"\(NFS\)")

        # Parse alternative version
        alt_match = re.search(r"\(Alt(?:\s+(\d+))?\)", filename)
        if alt_match:
            metadata.alt_version = f"Alt {alt_match.group(1)}" if alt_match.group(1) else "Alt"

        # Parse media type
        metadata.media_type = self._parse_media_type(filename)

        # Parse media label (for multi-disc games)
        metadata.media_label = self._parse_media_label(filename)

        # Parse dump status from square brackets
        metadata.dump_status = self._parse_dump_status(filename)

        # Store all tags for reference
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

        # Find first parenthesis and cut everything after
        paren_pos = name.find("(")
        if paren_pos != -1:
            name = name[:paren_pos]

        # Clean up multiple spaces
        name = re.sub(r"\s+", " ", name)

        return name.strip()

    def _parse_regions(self, filename: str) -> list[str]:
        """Parse region names from filename.

        No-Intro uses full region names in parentheses.

        Args:
            filename: ROM filename

        Returns:
            List of region names
        """
        regions = []
        seen = set()

        # Look for region names in parentheses
        # Regions can be single or comma-separated
        for region in self.REGION_NAMES:
            # Check for standalone region
            if re.search(rf"\({re.escape(region)}\)", filename):
                if region not in seen:
                    regions.append(region)
                    seen.add(region)
            # Check for region in comma-separated list
            elif re.search(rf"\([^)]*\b{re.escape(region)}\b[^)]*\)", filename):
                # Verify it's actually in a region context (followed by comma, space, or closing paren)
                pattern = rf"\(([^)]*\b{re.escape(region)}\b[^)]*)\)"
                match = re.search(pattern, filename)
                if match:
                    content = match.group(1)
                    # Check if this looks like a region list (contains known regions or commas)
                    if "," in content or any(
                        r in content for r in self.REGION_NAMES if r != region
                    ):
                        if region not in seen:
                            regions.append(region)
                            seen.add(region)

        return regions

    def _parse_languages(self, filename: str) -> list[str]:
        """Parse language codes from filename.

        No-Intro uses ISO 639-1 two-letter codes with first letter uppercase.

        Args:
            filename: ROM filename

        Returns:
            List of language names
        """
        languages = []
        seen = set()

        # Look for language codes in parentheses
        # Pattern: (En), (En,Ja), (En,Fr,De), etc.
        # Language codes appear after regions and before version

        # Find all parenthetical groups
        paren_groups = re.findall(r"\(([^)]+)\)", filename)

        for group in paren_groups:
            # Check if this group contains language codes
            # Language groups typically have 2-letter codes separated by commas
            if "," in group:
                parts = [p.strip() for p in group.split(",")]
                if all(len(p) == 2 and p[0].isupper() and p[1].islower() for p in parts):
                    # This looks like a language list
                    for code in parts:
                        if code in self.LANGUAGE_CODES:
                            lang = self.LANGUAGE_CODES[code]
                            if lang not in seen:
                                languages.append(lang)
                                seen.add(lang)
            else:
                # Single item - check if it's a language code
                code = group.strip()
                if len(code) == 2 and code[0].isupper() and code[1].islower():
                    if code in self.LANGUAGE_CODES:
                        lang = self.LANGUAGE_CODES[code]
                        if lang not in seen:
                            languages.append(lang)
                            seen.add(lang)

        return languages

    def _parse_version(self, filename: str) -> str | None:
        """Parse version information.

        Args:
            filename: ROM filename

        Returns:
            Version string or None
        """
        # Pattern: (v1.0), (v1.1), (v2.0a), etc.
        ver_match = re.search(r"\(v([\d.]+[a-zA-Z]*)\)", filename)
        if ver_match:
            return ver_match.group(1)
        return None

    def _parse_revision(self, filename: str) -> str | None:
        """Parse revision information.

        Args:
            filename: ROM filename

        Returns:
            Revision string or None
        """
        # Pattern: (Rev 1), (Rev A), (Rev 2), etc.
        rev_match = re.search(r"\(Rev\s+([A-Z0-9]+)\)", filename, re.IGNORECASE)
        if rev_match:
            return rev_match.group(1)
        return None

    def _parse_release_status(self, filename: str) -> tuple[ReleaseStatus, int | None]:
        """Parse release/development status.

        Args:
            filename: ROM filename

        Returns:
            Tuple of (ReleaseStatus, optional number for numbered releases)
        """
        # Check for Proto
        proto_match = re.search(r"\(Proto(?:\s+(\d+))?\)", filename)
        if proto_match:
            num = int(proto_match.group(1)) if proto_match.group(1) else None
            return ReleaseStatus.PROTO, num

        # Check for Beta
        beta_match = re.search(r"\(Beta(?:\s+(\d+))?\)", filename)
        if beta_match:
            num = int(beta_match.group(1)) if beta_match.group(1) else None
            return ReleaseStatus.BETA, num

        # Check for Demo
        demo_match = re.search(r"\(Demo(?:\s+(\d+))?\)", filename)
        if demo_match:
            num = int(demo_match.group(1)) if demo_match.group(1) else None
            return ReleaseStatus.DEMO, num

        # Check for Sample
        if re.search(r"\(Sample\)", filename):
            return ReleaseStatus.SAMPLE, None

        # Check for Alpha
        if re.search(r"\(Alpha\)", filename):
            return ReleaseStatus.ALPHA, None

        return ReleaseStatus.FINAL, None

    def _parse_media_type(self, filename: str) -> str | None:
        """Parse media type information.

        Args:
            filename: ROM filename

        Returns:
            Media type or None
        """
        media_types = ["CD", "DVD", "UMD", "Cart", "Disk", "Tape", "Card"]

        for media in media_types:
            if re.search(rf"\({media}\)", filename):
                return media

        return None

    def _parse_media_label(self, filename: str) -> str | None:
        """Parse media label for multi-disc games.

        Args:
            filename: ROM filename

        Returns:
            Media label or None
        """
        # Pattern: (Disc 1), (Disc A), (Disk 1 of 2), etc.
        disc_match = re.search(r"\((Dis[ck]\s+[^)]+)\)", filename)
        if disc_match:
            return disc_match.group(1)

        # Pattern: (Side A), (Side B)
        side_match = re.search(r"\((Side\s+[A-Z])\)", filename)
        if side_match:
            return side_match.group(1)

        return None

    def _parse_dump_status(self, filename: str) -> DumpStatus:
        """Parse dump status from square brackets.

        Args:
            filename: ROM filename

        Returns:
            DumpStatus enum value
        """
        # Check various dump status indicators
        if "[b]" in filename:
            return DumpStatus.BAD
        if "[o]" in filename:
            return DumpStatus.OVERDUMP
        if "[u]" in filename:
            return DumpStatus.UNDERDUMP
        if "[cr]" in filename:
            return DumpStatus.CRACKED
        if "[f]" in filename:
            return DumpStatus.FIXED
        if "[h]" in filename:
            return DumpStatus.HACKED
        if "[m]" in filename:
            return DumpStatus.MODIFIED
        if "[p]" in filename:
            return DumpStatus.PIRATED
        if "[t]" in filename:
            return DumpStatus.TRAINED
        if "[tr]" in filename:
            return DumpStatus.TRANSLATED

        return DumpStatus.GOOD

    def _check_tag(self, filename: str, pattern: str) -> bool:
        """Check if a tag pattern exists in filename.

        Args:
            filename: ROM filename
            pattern: Regular expression pattern to match

        Returns:
            True if pattern found
        """
        return bool(re.search(pattern, filename))

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

    def format_metadata(self, metadata: NoIntroMetadata) -> str:
        """Format metadata as a human-readable string.

        Args:
            metadata: NoIntroMetadata object

        Returns:
            Formatted string representation
        """
        lines = []

        if metadata.bios_flag:
            lines.append("[BIOS]")

        lines.append(f"Game: {metadata.clean_name}")

        if metadata.regions:
            lines.append(f"Region: {', '.join(metadata.regions)}")

        if metadata.languages:
            lines.append(f"Language: {', '.join(metadata.languages)}")

        if metadata.version:
            lines.append(f"Version: v{metadata.version}")
        elif metadata.revision:
            lines.append(f"Revision: Rev {metadata.revision}")

        if metadata.release_status != ReleaseStatus.FINAL:
            status = metadata.release_status.value.title()
            if metadata.status_number:
                status += f" {metadata.status_number}"
            lines.append(f"Status: {status}")

        if metadata.dump_status != DumpStatus.GOOD:
            lines.append(f"Dump: {metadata.dump_status.value}")

        special = []
        if metadata.is_unlicensed:
            special.append("Unlicensed")
        if metadata.is_pirate:
            special.append("Pirate")
        if metadata.is_promo:
            special.append("Promo")
        if metadata.is_not_for_sale:
            special.append("Not For Sale")

        if special:
            lines.append(f"Special: {', '.join(special)}")

        if metadata.alt_version:
            lines.append(f"Alternative: {metadata.alt_version}")

        if metadata.media_type:
            lines.append(f"Media: {metadata.media_type}")

        if metadata.media_label:
            lines.append(f"Label: {metadata.media_label}")

        return "\n".join(lines)

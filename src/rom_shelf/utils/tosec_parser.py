"""TOSEC (The Old School Emulation Center) ROM naming convention parser.

This module parses ROM filenames following the TOSEC naming conventions,
extracting metadata tags for date, publisher, system, dump info, and other attributes.

Reference: https://www.tosecdev.org/tosec-naming-convention
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CopyrightStatus(Enum):
    """Copyright/license status."""

    COMMERCIAL = ""  # Default - commercial software
    PUBLIC_DOMAIN = "PD"
    SHAREWARE = "SW"
    SHAREWARE_REGISTERED = "SW-R"
    FREEWARE = "FW"
    CARDWARE = "CW"
    LICENSEWARE = "LW"
    GIFTWARE = "GW"


class DevelopmentStatus(Enum):
    """Development/release status."""

    RELEASE = ""  # Final release
    ALPHA = "alpha"
    BETA = "beta"
    PREVIEW = "preview"
    PROTOTYPE = "proto"


class DemoType(Enum):
    """Demo types."""

    DEMO = "demo"  # Generic demo
    DEMO_KIOSK = "demo-kiosk"
    DEMO_PLAYABLE = "demo-playable"
    DEMO_ROLLING = "demo-rolling"
    DEMO_SLIDESHOW = "demo-slideshow"


class DumpFlag(Enum):
    """Dump information flags (in square brackets)."""

    CRACKED = "cr"  # Copy protection removed/bypassed
    FIXED = "f"  # Fixed to run properly
    HACKED = "h"  # Hacked/modified
    MODIFIED = "m"  # Unintentionally modified
    PIRATED = "p"  # Pirated version
    TRAINED = "t"  # Trained (cheats added)
    TRANSLATED = "tr"  # Translation
    OVERDUMP = "o"  # Over dump
    UNDERDUMP = "u"  # Under dump
    VIRUS = "v"  # Virus infected
    BAD_DUMP = "b"  # Bad dump
    ALTERNATE = "a"  # Alternate version
    KNOWN_GOOD = "!"  # Verified good dump
    MORE_INFO = "more info"  # Additional info flag


@dataclass
class TOSECMetadata:
    """Container for parsed TOSEC metadata."""

    # Core attributes (mandatory in TOSEC)
    title: str
    date: str  # TOSEC date format (YYYY-MM-DD or partial)
    publisher: str

    # Version info
    version: str | None = None

    # Demo info
    demo_type: DemoType | None = None

    # System info
    system: str | None = None
    video_standard: str | None = None  # PAL, NTSC, etc.

    # Regional info
    countries: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)

    # Status info
    copyright_status: CopyrightStatus = CopyrightStatus.COMMERCIAL
    development_status: DevelopmentStatus = DevelopmentStatus.RELEASE

    # Media info
    media_type: str | None = None  # Disk, Disc, File, Tape, Part, Side
    media_label: str | None = None  # Disk 1, Side A, etc.

    # Dump info flags (in order they should appear)
    dump_flags: dict[str, Any] = field(default_factory=dict)
    is_cracked: bool = False
    is_fixed: bool = False
    is_hacked: bool = False
    is_modified: bool = False
    is_pirated: bool = False
    is_trained: bool = False
    is_translated: bool = False
    is_overdump: bool = False
    is_underdump: bool = False
    has_virus: bool = False
    is_bad_dump: bool = False
    is_alternate: bool = False
    is_verified_good: bool = False

    # Additional info
    more_info: str | None = None
    raw_tags: dict[str, Any] = field(default_factory=dict)


class TOSECParser:
    """Parser for TOSEC ROM naming conventions."""

    # Country codes used in TOSEC
    COUNTRY_CODES = {
        "AE": "United Arab Emirates",
        "AL": "Albania",
        "AS": "Asia",
        "AT": "Austria",
        "AU": "Australia",
        "BA": "Bosnia and Herzegovina",
        "BE": "Belgium",
        "BG": "Bulgaria",
        "BR": "Brazil",
        "CA": "Canada",
        "CH": "Switzerland",
        "CL": "Chile",
        "CN": "China",
        "CS": "Serbia and Montenegro",
        "CY": "Cyprus",
        "CZ": "Czech Republic",
        "DE": "Germany",
        "DK": "Denmark",
        "EE": "Estonia",
        "EG": "Egypt",
        "ES": "Spain",
        "EU": "Europe",
        "FI": "Finland",
        "FR": "France",
        "GB": "United Kingdom",
        "GR": "Greece",
        "HK": "Hong Kong",
        "HR": "Croatia",
        "HU": "Hungary",
        "ID": "Indonesia",
        "IE": "Ireland",
        "IL": "Israel",
        "IN": "India",
        "IR": "Iran",
        "IS": "Iceland",
        "IT": "Italy",
        "JO": "Jordan",
        "JP": "Japan",
        "KR": "South Korea",
        "LT": "Lithuania",
        "LU": "Luxembourg",
        "LV": "Latvia",
        "MN": "Mongolia",
        "MX": "Mexico",
        "MY": "Malaysia",
        "NL": "Netherlands",
        "NO": "Norway",
        "NP": "Nepal",
        "NZ": "New Zealand",
        "OM": "Oman",
        "PE": "Peru",
        "PH": "Philippines",
        "PL": "Poland",
        "PT": "Portugal",
        "QA": "Qatar",
        "RO": "Romania",
        "RU": "Russia",
        "SE": "Sweden",
        "SG": "Singapore",
        "SI": "Slovenia",
        "SK": "Slovakia",
        "TH": "Thailand",
        "TR": "Turkey",
        "TW": "Taiwan",
        "UA": "Ukraine",
        "US": "United States",
        "VE": "Venezuela",
        "YU": "Yugoslavia",
        "ZA": "South Africa",
        "-": "Unknown",
    }

    # Language codes (ISO 639-1)
    LANGUAGE_CODES = {
        "ar": "Arabic",
        "bg": "Bulgarian",
        "bs": "Bosnian",
        "ca": "Catalan",
        "cs": "Czech",
        "cy": "Welsh",
        "da": "Danish",
        "de": "German",
        "el": "Greek",
        "en": "English",
        "eo": "Esperanto",
        "es": "Spanish",
        "et": "Estonian",
        "eu": "Basque",
        "fa": "Persian",
        "fi": "Finnish",
        "fr": "French",
        "fy": "Frisian",
        "ga": "Irish",
        "gd": "Gaelic",
        "gl": "Galician",
        "he": "Hebrew",
        "hi": "Hindi",
        "hr": "Croatian",
        "hu": "Hungarian",
        "is": "Icelandic",
        "it": "Italian",
        "ja": "Japanese",
        "ko": "Korean",
        "lt": "Lithuanian",
        "lv": "Latvian",
        "ms": "Malay",
        "nl": "Dutch",
        "no": "Norwegian",
        "pl": "Polish",
        "pt": "Portuguese",
        "ro": "Romanian",
        "ru": "Russian",
        "sk": "Slovak",
        "sl": "Slovenian",
        "sq": "Albanian",
        "sr": "Serbian",
        "sv": "Swedish",
        "th": "Thai",
        "tr": "Turkish",
        "uk": "Ukrainian",
        "ur": "Urdu",
        "vi": "Vietnamese",
        "yi": "Yiddish",
        "zh": "Chinese",
        "M2": "Two languages",
        "M3": "Three languages",
        "M4": "Four languages",
        "M5": "Five languages",
        "M6": "Six languages",
        "M7": "Seven languages",
        "M8": "Eight languages",
        "M9": "Nine languages",
    }

    def __init__(self):
        """Initialize TOSEC parser."""
        pass

    def parse(self, filename: str) -> TOSECMetadata:
        """Parse a ROM filename for TOSEC metadata.

        TOSEC format: Title version (demo) (date)(publisher)(system)(video)(country)(language)
                     (copyright status)(development status)(media type)(media label)
                     [dump info flags][more info]

        Args:
            filename: ROM filename to parse

        Returns:
            TOSECMetadata object with extracted information
        """
        # Remove file extension
        name = filename.rsplit(".", 1)[0] if "." in filename else filename

        # Initialize metadata - TOSEC requires title, date, and publisher
        metadata = TOSECMetadata(title="", date="", publisher="")

        # Extract title (everything before first parenthesis)
        title_match = re.match(r"^([^(\[]+?)(?:\s+v[\d.]+)?\s*(?:\(|$)", name)
        if title_match:
            metadata.title = title_match.group(1).strip()

        # Extract version from title area (before parentheses)
        version_match = re.search(
            r"\s+v([\d.]+[a-zA-Z]*)\s*(?:\(|$)", name.split("(")[0] if "(" in name else name
        )
        if version_match:
            metadata.version = version_match.group(1)

        # Extract all parenthetical groups
        paren_groups = re.findall(r"\(([^)]+)\)", name)

        # Parse date (TOSEC mandatory - various formats)
        date_parsed = False
        for group in paren_groups:
            # Full date: YYYY-MM-DD or partial: YYYY, YYYY-MM, 19xx, 19xx-MM-DD, etc.
            if re.match(r"^(?:\d{4}|\d{2}xx)(?:-\d{2})?(?:-\d{2})?$", group):
                metadata.date = group
                date_parsed = True
                break

        # Parse publisher (TOSEC mandatory - comes after date)
        if date_parsed and len(paren_groups) > 1:
            # Find date index and get next item as publisher
            for i, group in enumerate(paren_groups):
                if group == metadata.date and i + 1 < len(paren_groups):
                    metadata.publisher = paren_groups[i + 1]
                    break

        # Parse demo type
        for group in paren_groups:
            if group == "demo":
                metadata.demo_type = DemoType.DEMO
            elif group == "demo-kiosk":
                metadata.demo_type = DemoType.DEMO_KIOSK
            elif group == "demo-playable":
                metadata.demo_type = DemoType.DEMO_PLAYABLE
            elif group == "demo-rolling":
                metadata.demo_type = DemoType.DEMO_ROLLING
            elif group == "demo-slideshow":
                metadata.demo_type = DemoType.DEMO_SLIDESHOW

        # Parse system info (e.g., "Amiga", "DOS", etc.)
        # This would typically come after publisher
        for group in paren_groups:
            # Check if it looks like a system name (not a date, country code, etc.)
            if (
                not re.match(r"^(?:\d{4}|\d{2}xx)", group)
                and group not in ["NTSC", "PAL", "SECAM"]
                and group.upper() not in self.COUNTRY_CODES
                and group.lower() not in self.LANGUAGE_CODES
                and group not in ["PD", "SW", "SW-R", "FW", "CW", "LW", "GW"]
                and group not in ["alpha", "beta", "preview", "proto"]
                and not group.startswith("demo")
            ):
                # Could be a system
                if metadata.publisher and group != metadata.publisher:
                    metadata.system = group
                    break

        # Parse video standard
        for group in paren_groups:
            if group in ["NTSC", "PAL", "SECAM", "NTSC-PAL"]:
                metadata.video_standard = group

        # Parse countries
        for group in paren_groups:
            # Check for country codes (2-letter uppercase)
            if group.upper() in self.COUNTRY_CODES:
                country = self.COUNTRY_CODES[group.upper()]
                if country not in metadata.countries:
                    metadata.countries.append(country)
            # Check for multi-country format (e.g., "US-EU")
            elif "-" in group and all(
                part.upper() in self.COUNTRY_CODES for part in group.split("-")
            ):
                for code in group.split("-"):
                    country = self.COUNTRY_CODES[code.upper()]
                    if country not in metadata.countries:
                        metadata.countries.append(country)

        # Parse languages
        for group in paren_groups:
            # Check for language codes (2-letter lowercase)
            if group.lower() in self.LANGUAGE_CODES:
                lang = self.LANGUAGE_CODES[group.lower()]
                if lang not in metadata.languages:
                    metadata.languages.append(lang)
            # Check for multi-language indicators (M2, M3, etc.)
            elif re.match(r"^M\d$", group.upper()):
                metadata.languages.append(self.LANGUAGE_CODES.get(group.upper(), group))
            # Check for multi-language format (e.g., "en-de-fr")
            elif "-" in group and all(
                part.lower() in self.LANGUAGE_CODES for part in group.split("-")
            ):
                for code in group.split("-"):
                    lang = self.LANGUAGE_CODES[code.lower()]
                    if lang not in metadata.languages:
                        metadata.languages.append(lang)

        # Parse copyright status
        for group in paren_groups:
            if group == "PD":
                metadata.copyright_status = CopyrightStatus.PUBLIC_DOMAIN
            elif group == "SW":
                metadata.copyright_status = CopyrightStatus.SHAREWARE
            elif group == "SW-R":
                metadata.copyright_status = CopyrightStatus.SHAREWARE_REGISTERED
            elif group == "FW":
                metadata.copyright_status = CopyrightStatus.FREEWARE
            elif group == "CW":
                metadata.copyright_status = CopyrightStatus.CARDWARE
            elif group == "LW":
                metadata.copyright_status = CopyrightStatus.LICENSEWARE
            elif group == "GW":
                metadata.copyright_status = CopyrightStatus.GIFTWARE

        # Parse development status
        for group in paren_groups:
            if group == "alpha":
                metadata.development_status = DevelopmentStatus.ALPHA
            elif group == "beta":
                metadata.development_status = DevelopmentStatus.BETA
            elif group == "preview":
                metadata.development_status = DevelopmentStatus.PREVIEW
            elif group == "proto":
                metadata.development_status = DevelopmentStatus.PROTOTYPE

        # Parse media type and label
        for group in paren_groups:
            # Media types
            if (
                group.startswith("Disk")
                or group.startswith("Disc")
                or group.startswith("File")
                or group.startswith("Tape")
                or group.startswith("Part")
                or group.startswith("Side")
            ):
                # Extract media type and label
                parts = group.split(" ", 1)
                metadata.media_type = parts[0]
                if len(parts) > 1:
                    metadata.media_label = parts[1]

        # Parse dump flags (in square brackets)
        bracket_groups = re.findall(r"\[([^\]]+)\]", name)

        for group in bracket_groups:
            # Parse individual dump flags
            if group == "cr":
                metadata.is_cracked = True
                metadata.dump_flags["cracked"] = True
            elif group.startswith("f"):
                metadata.is_fixed = True
                metadata.dump_flags["fixed"] = group[1:] if len(group) > 1 else True
            elif group.startswith("h"):
                metadata.is_hacked = True
                metadata.dump_flags["hacked"] = group[1:] if len(group) > 1 else True
            elif group == "m":
                metadata.is_modified = True
                metadata.dump_flags["modified"] = True
            elif group == "p":
                metadata.is_pirated = True
                metadata.dump_flags["pirated"] = True
            elif group.startswith("t"):
                metadata.is_trained = True
                metadata.dump_flags["trained"] = group[1:] if len(group) > 1 else True
            elif group == "tr":
                metadata.is_translated = True
                metadata.dump_flags["translated"] = True
            elif group == "o":
                metadata.is_overdump = True
                metadata.dump_flags["overdump"] = True
            elif group == "u":
                metadata.is_underdump = True
                metadata.dump_flags["underdump"] = True
            elif group == "v":
                metadata.has_virus = True
                metadata.dump_flags["virus"] = True
            elif group.startswith("b"):
                metadata.is_bad_dump = True
                metadata.dump_flags["bad_dump"] = group[1:] if len(group) > 1 else True
            elif group.startswith("a"):
                metadata.is_alternate = True
                metadata.dump_flags["alternate"] = group[1:] if len(group) > 1 else True
            elif group == "!":
                metadata.is_verified_good = True
                metadata.dump_flags["verified"] = True
            elif "more info" in group.lower():
                metadata.more_info = group
                metadata.dump_flags["more_info"] = group

        # Store all raw tags for reference
        metadata.raw_tags = {"parentheses": paren_groups, "brackets": bracket_groups}

        return metadata

    def format_metadata(self, metadata: TOSECMetadata) -> str:
        """Format metadata as a human-readable string.

        Args:
            metadata: TOSECMetadata object

        Returns:
            Formatted string representation
        """
        lines = []

        lines.append(f"Title: {metadata.title}")

        if metadata.version:
            lines.append(f"Version: v{metadata.version}")

        lines.append(f"Date: {metadata.date}")
        lines.append(f"Publisher: {metadata.publisher}")

        if metadata.system:
            lines.append(f"System: {metadata.system}")

        if metadata.video_standard:
            lines.append(f"Video: {metadata.video_standard}")

        if metadata.countries:
            lines.append(f"Countries: {', '.join(metadata.countries)}")

        if metadata.languages:
            lines.append(f"Languages: {', '.join(metadata.languages)}")

        if metadata.demo_type:
            lines.append(f"Demo Type: {metadata.demo_type.value}")

        if metadata.copyright_status != CopyrightStatus.COMMERCIAL:
            lines.append(f"Copyright: {metadata.copyright_status.value}")

        if metadata.development_status != DevelopmentStatus.RELEASE:
            lines.append(f"Development: {metadata.development_status.value}")

        if metadata.media_type:
            media_info = metadata.media_type
            if metadata.media_label:
                media_info += f" {metadata.media_label}"
            lines.append(f"Media: {media_info}")

        # Format dump flags
        flags = []
        if metadata.is_cracked:
            flags.append("Cracked")
        if metadata.is_fixed:
            flags.append("Fixed")
        if metadata.is_hacked:
            flags.append("Hacked")
        if metadata.is_modified:
            flags.append("Modified")
        if metadata.is_pirated:
            flags.append("Pirated")
        if metadata.is_trained:
            flags.append("Trained")
        if metadata.is_translated:
            flags.append("Translated")
        if metadata.is_overdump:
            flags.append("Overdump")
        if metadata.is_underdump:
            flags.append("Underdump")
        if metadata.has_virus:
            flags.append("Virus")
        if metadata.is_bad_dump:
            flags.append("Bad Dump")
        if metadata.is_alternate:
            flags.append("Alternate")
        if metadata.is_verified_good:
            flags.append("Verified Good")

        if flags:
            lines.append(f"Dump Flags: {', '.join(flags)}")

        if metadata.more_info:
            lines.append(f"More Info: {metadata.more_info}")

        return "\n".join(lines)

    def is_tosec_format(self, filename: str) -> bool:
        """Check if a filename appears to use TOSEC naming convention.

        TOSEC has very specific format with date and publisher in parentheses.

        Args:
            filename: ROM filename to check

        Returns:
            True if filename appears to use TOSEC conventions
        """
        # Remove file extension
        name = filename.rsplit(".", 1)[0] if "." in filename else filename

        # TOSEC characteristics:
        # - Has date in format (YYYY) or (YYYY-MM-DD) or (19xx) etc.
        # - Has publisher after date
        # - May have dump flags in square brackets [cr][f][h] etc.

        # Check for TOSEC date patterns
        has_date = bool(re.search(r"\((?:\d{4}|\d{2}xx)(?:-\d{2})?(?:-\d{2})?\)", name))

        # Check for square bracket dump flags (TOSEC specific)
        has_dump_flags = bool(re.search(r"\[(cr|f|h|m|p|t|tr|o|u|v|b|a|!)\]", name))

        # Check for TOSEC-specific copyright status
        has_copyright = bool(re.search(r"\((PD|SW|SW-R|FW|CW|LW|GW)\)", name))

        # If it has TOSEC date format or dump flags, likely TOSEC
        return has_date or has_dump_flags or has_copyright

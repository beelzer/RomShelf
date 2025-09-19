"""TOSEC (The Old School Emulation Center) ROM naming convention parser.

This module parses ROM filenames following the TOSEC naming conventions,
extracting metadata tags for date, publisher, system, dump info, and other attributes.

Reference: https://www.tosecdev.org/tosec-naming-convention
"""

import re
from dataclasses import dataclass

from .rom_parser_base import (
    BaseROMMetadata,
    BaseROMParser,
    CopyrightStatus,
    DumpQuality,
    ReleaseStatus,
)


@dataclass
class TOSECMetadata(BaseROMMetadata):
    """Container for parsed TOSEC metadata.

    TOSEC-specific additions to the base metadata.
    """

    # Core TOSEC attributes (mandatory in TOSEC)
    date: str = ""  # TOSEC date format (YYYY-MM-DD or partial)
    publisher: str = ""  # Publisher name
    system: str | None = None  # System/platform info
    video_standard: str | None = None  # PAL, NTSC, etc.
    more_info: str | None = None  # Additional info from [more info] tag


class TOSECParser(BaseROMParser):
    """Parser for TOSEC ROM naming conventions."""

    # TOSEC-specific country codes (2-letter uppercase)
    TOSEC_COUNTRY_CODES = {
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

    def get_format_name(self) -> str:
        """Get the name of this naming convention format."""
        return "TOSEC"

    def can_parse(self, filename: str) -> bool:
        """Check if this parser can handle the given filename.

        TOSEC characteristics:
        - Has date in format (YYYY) or (YYYY-MM-DD) or (19xx) etc.
        - Has publisher after date
        - May have dump flags in square brackets [cr][f][h] etc.
        - Has specific copyright status tags: (PD), (SW), (FW), etc.
        """
        # Remove file extension
        name = filename.rsplit(".", 1)[0] if "." in filename else filename

        # Check for TOSEC date patterns
        has_date = bool(re.search(r"\((?:\d{4}|\d{2}xx)(?:-\d{2})?(?:-\d{2})?\)", name))

        # Check for square bracket dump flags (TOSEC specific combinations)
        has_dump_flags = bool(re.search(r"\[(cr|f|h|m|p|t|tr|o|u|v|b|a|!)\]", name))

        # Check for TOSEC-specific copyright status
        has_copyright = bool(re.search(r"\((PD|SW|SW-R|FW|CW|LW|GW)\)", name))

        # If it has TOSEC date format or dump flags, likely TOSEC
        return has_date or has_dump_flags or has_copyright

    def parse(self, filename: str) -> TOSECMetadata:
        """Parse a ROM filename for TOSEC metadata.

        TOSEC format: Title version (demo) (date)(publisher)(system)(video)(country)(language)
                     (copyright status)(development status)(media type)(media label)
                     [dump info flags][more info]
        """
        # Remove file extension
        name = filename.rsplit(".", 1)[0] if "." in filename else filename

        # Initialize metadata
        metadata = TOSECMetadata(clean_name="", original_filename=filename)

        # Extract title (everything before first parenthesis)
        title_match = re.match(r"^([^(\[]+?)(?:\s+v[\d.]+)?\s*(?:\(|$)", name)
        if title_match:
            metadata.clean_name = title_match.group(1).strip()

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

        # Parse demo/development status
        for group in paren_groups:
            if group == "demo":
                metadata.release_status = ReleaseStatus.DEMO
            elif group == "demo-kiosk":
                metadata.release_status = ReleaseStatus.DEMO_KIOSK
            elif group == "demo-playable":
                metadata.release_status = ReleaseStatus.DEMO_PLAYABLE
            elif group == "demo-rolling":
                metadata.release_status = ReleaseStatus.DEMO_ROLLING
            elif group == "demo-slideshow":
                metadata.release_status = ReleaseStatus.DEMO_SLIDESHOW
            elif group == "alpha":
                metadata.release_status = ReleaseStatus.ALPHA
            elif group == "beta":
                metadata.release_status = ReleaseStatus.BETA
            elif group == "preview":
                metadata.release_status = ReleaseStatus.PREVIEW
            elif group == "proto":
                metadata.release_status = ReleaseStatus.PROTOTYPE

        # Parse system info (e.g., "Amiga", "DOS", etc.)
        for group in paren_groups:
            # Check if it looks like a system name (not a date, country code, etc.)
            if (
                not re.match(r"^(?:\d{4}|\d{2}xx)", group)
                and group not in ["NTSC", "PAL", "SECAM"]
                and group.upper() not in self.TOSEC_COUNTRY_CODES
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

        # Parse countries using TOSEC codes
        for group in paren_groups:
            # Check for country codes (2-letter uppercase)
            if group.upper() in self.TOSEC_COUNTRY_CODES:
                country = self.TOSEC_COUNTRY_CODES[group.upper()]
                # Try to normalize to our standard region names
                normalized = self.normalize_region(country)
                if normalized and normalized not in metadata.regions:
                    metadata.regions.append(normalized)
                elif country not in metadata.regions:
                    metadata.regions.append(country)
            # Check for multi-country format (e.g., "US-EU")
            elif "-" in group and all(
                part.upper() in self.TOSEC_COUNTRY_CODES for part in group.split("-")
            ):
                for code in group.split("-"):
                    country = self.TOSEC_COUNTRY_CODES[code.upper()]
                    normalized = self.normalize_region(country)
                    if normalized and normalized not in metadata.regions:
                        metadata.regions.append(normalized)
                    elif country not in metadata.regions:
                        metadata.regions.append(country)

        # Parse languages
        for group in paren_groups:
            # Check for language codes (2-letter lowercase)
            lang = self.normalize_language(group)
            if lang and lang not in metadata.languages:
                metadata.languages.append(lang)
            # Check for multi-language indicators (M2, M3, etc.)
            elif re.match(r"^M\d$", group.upper()):
                metadata.languages.append(self.LANGUAGE_CODES.get(group.upper(), group))
            # Check for multi-language format (e.g., "en-de-fr")
            elif "-" in group:
                parts = group.split("-")
                if all(self.normalize_language(part) for part in parts):
                    for code in parts:
                        lang = self.normalize_language(code)
                        if lang and lang not in metadata.languages:
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
        metadata.dump_quality = self._parse_dump_flags(name)

        # Check for more info flag
        more_info_match = re.search(r"\[([^]]*more info[^]]*)\]", name, re.IGNORECASE)
        if more_info_match:
            metadata.more_info = more_info_match.group(1)

        # Store TOSEC-specific metadata
        if metadata.date:
            metadata.extra_metadata["tosec_date"] = metadata.date
        if metadata.publisher:
            metadata.extra_metadata["publisher"] = metadata.publisher
        if metadata.system:
            metadata.extra_metadata["system"] = metadata.system
        if metadata.video_standard:
            metadata.extra_metadata["video_standard"] = metadata.video_standard
        if metadata.more_info:
            metadata.extra_metadata["more_info"] = metadata.more_info

        # Store all tags for reference
        metadata.raw_tags = self.extract_all_tags(name)

        return metadata

    def _parse_dump_flags(self, name: str) -> DumpQuality:
        """Parse dump flags from square brackets in TOSEC format."""
        # Parse individual dump flags
        if "[cr]" in name:
            return DumpQuality.CRACKED
        if re.search(r"\[f\d*\]", name):
            return DumpQuality.FIXED
        if re.search(r"\[h\d*\]", name):
            return DumpQuality.HACKED
        if "[m]" in name:
            return DumpQuality.MODIFIED
        if "[p]" in name:
            return DumpQuality.PIRATED
        if re.search(r"\[t\d*\]", name):
            return DumpQuality.TRAINED
        if "[tr]" in name:
            return DumpQuality.TRANSLATED
        if "[o]" in name:
            return DumpQuality.OVERDUMP
        if "[u]" in name:
            return DumpQuality.UNDERDUMP
        if "[v]" in name:
            return DumpQuality.VIRUS
        if re.search(r"\[b\d*\]", name):
            return DumpQuality.BAD
        if re.search(r"\[a\d*\]", name):
            return DumpQuality.ALTERNATE
        if "[!]" in name:
            return DumpQuality.VERIFIED_GOOD

        return DumpQuality.UNKNOWN

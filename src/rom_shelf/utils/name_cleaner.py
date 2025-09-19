"""Utility for cleaning ROM names and extracting metadata.

This module integrates with various ROM naming convention parsers
using a unified registry-based architecture.
"""

import re
from typing import Any

from .goodtools_parser import GoodToolsParser
from .nointro_parser import NoIntroParser
from .rom_parser_base import ParserRegistry
from .tosec_parser import TOSECParser

# Global parser registry
_parser_registry = ParserRegistry()

# Register parsers in priority order
_parser_registry.register(TOSECParser())  # Most structured format
_parser_registry.register(NoIntroParser())  # More standardized
_parser_registry.register(GoodToolsParser())  # Legacy format


def clean_game_name(name: str) -> str:
    """Clean game name by removing parenthetical and bracketed information.

    Args:
        name: Original ROM name

    Returns:
        Cleaned game name (e.g., "WWF No Mercy (USA) (Rev 1)" -> "WWF No Mercy")
    """
    patterns = [
        r"\s*\([^)]*\)\s*",  # Remove parenthetical info like (USA), (Rev 1)
        r"\s*\[[^\]]*\]\s*",  # Remove bracket info like [!], [T+Eng]
        r"\s+",  # Multiple spaces to single
    ]

    clean = name
    for pattern in patterns:
        clean = re.sub(pattern, " ", clean)

    return clean.strip()


def extract_rom_metadata(original_name: str, platform_id: str | None = None) -> dict[str, Any]:
    """Extract metadata from ROM filename using appropriate parser.

    Args:
        original_name: Original ROM filename
        platform_id: Optional platform identifier for optimized parsing

    Returns:
        Dictionary containing extracted metadata like region, revision, etc.
    """
    # Try to parse with registered parsers
    metadata = _parser_registry.parse(original_name, platform_id)

    if metadata:
        return metadata

    # Fall back to generic parsing if no parser matches
    return _generic_parse(original_name)


def get_display_name_and_metadata(
    original_name: str, platform_id: str | None = None
) -> tuple[str, dict[str, Any]]:
    """Get cleaned display name and metadata from ROM filename.

    Args:
        original_name: Original ROM filename
        platform_id: Optional platform identifier

    Returns:
        Tuple of (display_name, metadata_dict)
    """
    # Extract metadata using appropriate parser
    metadata = extract_rom_metadata(original_name, platform_id)

    # Get clean name from metadata or fall back to simple cleaning
    display_name = metadata.get("clean_name", clean_game_name(original_name))

    return display_name, metadata


def _generic_parse(original_name: str) -> dict[str, Any]:
    """Generic parsing for filenames that don't match known conventions.

    Args:
        original_name: ROM filename

    Returns:
        Dictionary with basic metadata extraction
    """
    metadata = {
        "clean_name": clean_game_name(original_name),
        "parser_format": "Generic",
    }

    # Extract region information
    # First, try to match multiple regions (e.g., "USA, Europe")
    multi_region_match = re.search(
        r"\(((?:USA|Europe|Japan|World|Asia|Australia|Germany|France|Spain|Italy|Netherlands|Sweden|Brazil|Korea|China)(?:,\s*(?:USA|Europe|Japan|World|Asia|Australia|Germany|France|Spain|Italy|Netherlands|Sweden|Brazil|Korea|China))*)\)",
        original_name,
        re.IGNORECASE,
    )

    if multi_region_match:
        metadata["region"] = multi_region_match.group(1)
    else:
        # Try single letter region codes (e.g., JUE, U, E)
        single_letter_match = re.search(r"\(([UJEKFGISCADNXYZ]+)\)", original_name)
        if single_letter_match:
            metadata["region"] = single_letter_match.group(1)
        else:
            # Fall back to individual region patterns
            region_patterns = [
                (r"\(USA.*?\)", "USA"),
                (r"\(Europe.*?\)", "Europe"),
                (r"\(Japan.*?\)", "Japan"),
                (r"\(World.*?\)", "World"),
                (r"\(Asia.*?\)", "Asia"),
                (r"\(Australia.*?\)", "Australia"),
                (r"\(Germany.*?\)", "Germany"),
                (r"\(France.*?\)", "France"),
                (r"\(Spain.*?\)", "Spain"),
                (r"\(Italy.*?\)", "Italy"),
                (r"\(Netherlands.*?\)", "Netherlands"),
                (r"\(Sweden.*?\)", "Sweden"),
                (r"\(Brazil.*?\)", "Brazil"),
                (r"\(Korea.*?\)", "Korea"),
                (r"\(China.*?\)", "China"),
            ]

            for pattern, region in region_patterns:
                if re.search(pattern, original_name, re.IGNORECASE):
                    metadata["region"] = region
                    break

    # Extract revision information
    rev_match = re.search(r"\(Rev\s+(\w+)\)", original_name, re.IGNORECASE)
    if rev_match:
        metadata["revision"] = rev_match.group(1)

    # Extract version information (explicit version numbers)
    version_match = re.search(r"\(v(\d+(?:\.\d+)*)\)", original_name, re.IGNORECASE)
    if version_match:
        metadata["version"] = version_match.group(1)
    # If no explicit version but we have revision, use revision for version column
    elif rev_match:
        metadata["version"] = f"Rev {rev_match.group(1)}"

    # Extract language information
    # Define known language codes to avoid confusion with region codes
    known_language_codes = {
        "En",
        "Fr",
        "De",
        "Es",
        "It",
        "Pt",
        "Ja",
        "Ko",
        "Zh",
        "Ru",
        "Nl",
        "Sv",
        "No",
        "Da",
        "Fi",
        "Pl",
        "Ar",
        "He",
        "Tr",
        "Gr",
        "Hu",
        "Cs",
        "Ro",
        "Ca",
        "Eu",
        "Ga",
        "Cy",
        "Is",
        "Hr",
        "Sr",
        "Sk",
        "Sl",
        "Lt",
        "Lv",
        "Et",
        "Bg",
        "Uk",
        "Be",
        "Mk",
        "Sq",
        "Vi",
        "Th",
        "Id",
        "Ms",
        "Hi",
        "Ta",
        "Te",
        "Bn",
        "Ur",
        "Fa",
    }

    # Look for language patterns in parentheses
    languages_found = set()

    # Pattern 1: Look for explicit language codes in parentheses
    lang_pattern = r"\(([A-Za-z]{2}(?:[,+/][A-Za-z]{2})*)\)"
    for match in re.finditer(lang_pattern, original_name):
        lang_str = match.group(1)
        # Split by common separators
        for separator in [",", "+", "/"]:
            if separator in lang_str:
                codes = [code.strip().capitalize() for code in lang_str.split(separator)]
                # Only add if ALL codes are known language codes
                if all(code in known_language_codes for code in codes):
                    languages_found.update(codes)
                    break
        else:
            # Single code
            code = lang_str.capitalize()
            if code in known_language_codes:
                languages_found.add(code)

    # Pattern 2: Multi-language indicators
    if re.search(r"\(Multi-?\d*\)", original_name, re.IGNORECASE):
        languages_found.add("Multi")

    # Map language codes to full names
    language_map = {
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
        "Multi": "Multi",
    }

    if languages_found:
        language_names = [language_map.get(code, code) for code in sorted(languages_found)]
        metadata["language"] = (
            language_names[0] if len(language_names) == 1 else ", ".join(language_names)
        )

    # Check for specific tags
    if re.search(r"\[!\]", original_name):
        metadata["verified"] = True
    if re.search(r"\(Proto(?:type)?\)", original_name, re.IGNORECASE):
        metadata["status"] = "Prototype"
    if re.search(r"\(Beta\)", original_name, re.IGNORECASE):
        metadata["status"] = "Beta"
    if re.search(r"\(Demo\)", original_name, re.IGNORECASE):
        metadata["status"] = "Demo"
    if re.search(r"\(Sample\)", original_name, re.IGNORECASE):
        metadata["status"] = "Sample"
    if re.search(r"\(Unl(?:icensed)?\)", original_name, re.IGNORECASE):
        metadata["unlicensed"] = True

    return metadata

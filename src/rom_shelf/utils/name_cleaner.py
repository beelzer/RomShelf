"""Utility for cleaning ROM names and extracting metadata."""

import re
from typing import Any


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


def extract_rom_metadata(original_name: str) -> dict[str, Any]:
    """Extract metadata from ROM filename.

    Args:
        original_name: Original ROM filename

    Returns:
        Dictionary containing extracted metadata like region, revision, etc.
    """
    metadata = {}

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
    # Common patterns: (En), (En,Fr), (En+Fr), (En/Fr), (Multi-5), etc.
    languages_found = set()

    # Pattern 1: Look for explicit language codes in parentheses
    # e.g., (En), (En,Fr), (En+Fr), (En/Fr)
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
            # Single language code
            code = lang_str.capitalize()
            if code in known_language_codes:
                languages_found.add(code)

    # Pattern 2: Look for Multi-language indicators
    # e.g., (Multi-3), (M5), (Multi)
    multi_match = re.search(r"\((Multi(?:-\d+)?|M\d+)\)", original_name, re.IGNORECASE)
    if multi_match:
        # For multi-language ROMs, try to extract specific languages from the name
        # or mark it as "Multi"
        if not languages_found:
            metadata["language"] = "Multi"
        else:
            # We found specific languages, use those
            metadata["language"] = ",".join(sorted(languages_found))
    elif languages_found:
        # Sort languages for consistency
        metadata["language"] = ",".join(sorted(languages_found))

    # Extract demo/prototype/beta information
    if re.search(r"\(Demo.*?\)", original_name, re.IGNORECASE):
        metadata["type"] = "Demo"
    elif re.search(r"\(Proto.*?\)", original_name, re.IGNORECASE):
        metadata["type"] = "Prototype"
    elif re.search(r"\(Beta.*?\)", original_name, re.IGNORECASE):
        metadata["type"] = "Beta"
    elif re.search(r"\(Alpha.*?\)", original_name, re.IGNORECASE):
        metadata["type"] = "Alpha"

    # Extract special features
    if re.search(r"\(SGB Enhanced\)", original_name, re.IGNORECASE):
        metadata["sgb_enhanced"] = True
    if re.search(r"\(GB Compatible\)", original_name, re.IGNORECASE):
        metadata["gb_compatible"] = True
    if re.search(r"\(CGB.*Enhanced\)", original_name, re.IGNORECASE):
        metadata["cgb_enhanced"] = True
    if re.search(r"\(Rumble.*Version\)", original_name, re.IGNORECASE):
        metadata["rumble_support"] = True

    return metadata


def get_display_name_and_metadata(original_name: str) -> tuple[str, dict[str, Any]]:
    """Get both cleaned display name and extracted metadata.

    Args:
        original_name: Original ROM filename

    Returns:
        Tuple of (cleaned_name, metadata_dict)
    """
    cleaned_name = clean_game_name(original_name)
    metadata = extract_rom_metadata(original_name)

    return cleaned_name, metadata

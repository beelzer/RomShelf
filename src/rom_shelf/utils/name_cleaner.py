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
    language_match = re.search(r"\(([A-Za-z]{2}(?:,[A-Za-z]{2})*)\)", original_name)
    if language_match:
        languages = language_match.group(1)
        # Validate that these look like language codes (2-letter codes)
        language_codes = [lang.strip() for lang in languages.split(",")]
        valid_codes = []
        for code in language_codes:
            # Common language codes pattern: exactly 2 letters
            if re.match(r"^[A-Za-z]{2}$", code):
                valid_codes.append(code)

        if valid_codes:
            metadata["language"] = ",".join(valid_codes)

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

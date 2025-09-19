"""Utility for cleaning ROM names and extracting metadata.

This module integrates with GoodTools parser for supported platforms,
falling back to generic parsing for other naming conventions.
"""

import re
from typing import Any

from .goodtools_parser import DumpQuality, GoodToolsMetadata, GoodToolsParser, ROMType
from .nointro_parser import DumpStatus, NoIntroMetadata, NoIntroParser, ReleaseStatus
from .tosec_parser import TOSECMetadata, TOSECParser


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
    """Extract metadata from ROM filename.

    Args:
        original_name: Original ROM filename
        platform_id: Optional platform identifier for optimized parsing

    Returns:
        Dictionary containing extracted metadata like region, revision, etc.
    """
    metadata = {}

    # Try TOSEC parser first (most structured format)
    if _looks_like_tosec(original_name):
        tosec_parser = TOSECParser()
        tosec_metadata = tosec_parser.parse(original_name)
        return _tosec_to_dict(tosec_metadata)

    # Try No-Intro parser (more modern/standardized)
    if platform_id:
        nointro_parser = NoIntroParser(platform_id)
        if nointro_parser.is_nointro_platform(platform_id):
            # Check if filename looks like No-Intro format
            # No-Intro always has regions in parentheses and uses full region names
            if _looks_like_nointro(original_name):
                nointro_metadata = nointro_parser.parse(original_name)
                return _nointro_to_dict(nointro_metadata)

    # Try GoodTools parser if we have a platform
    if platform_id:
        parser = GoodToolsParser(platform_id)
        if parser.is_goodtools_platform(platform_id):
            goodtools_metadata = parser.parse(original_name)
            return _goodtools_to_dict(goodtools_metadata)

    # Fall back to generic parsing for non-GoodTools platforms or when no platform specified

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


def get_display_name_and_metadata(
    original_name: str, platform_id: str | None = None
) -> tuple[str, dict[str, Any]]:
    """Get both cleaned display name and extracted metadata.

    Args:
        original_name: Original ROM filename
        platform_id: Optional platform identifier for optimized parsing

    Returns:
        Tuple of (cleaned_name, metadata_dict)
    """
    # Try TOSEC parser first (most structured format)
    if _looks_like_tosec(original_name):
        tosec_parser = TOSECParser()
        tosec_metadata = tosec_parser.parse(original_name)
        return tosec_metadata.title, _tosec_to_dict(tosec_metadata)

    # Try No-Intro parser (more modern/standardized)
    if platform_id:
        nointro_parser = NoIntroParser(platform_id)
        if nointro_parser.is_nointro_platform(platform_id):
            # Check if filename looks like No-Intro format
            if _looks_like_nointro(original_name):
                nointro_metadata = nointro_parser.parse(original_name)
                return nointro_metadata.clean_name, _nointro_to_dict(nointro_metadata)

    # Try GoodTools parser if we have a platform
    if platform_id:
        parser = GoodToolsParser(platform_id)
        if parser.is_goodtools_platform(platform_id):
            goodtools_metadata = parser.parse(original_name)
            return goodtools_metadata.clean_name, _goodtools_to_dict(goodtools_metadata)

    # Fall back to generic parsing
    cleaned_name = clean_game_name(original_name)
    metadata = extract_rom_metadata(original_name, platform_id)

    return cleaned_name, metadata


def _goodtools_to_dict(goodtools_metadata: GoodToolsMetadata) -> dict[str, Any]:
    """Convert GoodToolsMetadata to dictionary format.

    Args:
        goodtools_metadata: GoodToolsMetadata object

    Returns:
        Dictionary with metadata fields
    """
    metadata = {}

    # Map regions
    if goodtools_metadata.regions:
        # Join regions for backward compatibility
        metadata["region"] = ", ".join(goodtools_metadata.regions)

    # Map languages
    if goodtools_metadata.languages:
        metadata["language"] = ", ".join(goodtools_metadata.languages)

    # Map version/revision
    if goodtools_metadata.version:
        metadata["version"] = goodtools_metadata.version
    elif goodtools_metadata.revision:
        metadata["version"] = f"Rev {goodtools_metadata.revision}"

    # Map release type
    if goodtools_metadata.is_demo:
        metadata["type"] = "Demo"
    elif goodtools_metadata.is_prototype:
        metadata["type"] = "Prototype"
    elif goodtools_metadata.is_beta:
        metadata["type"] = "Beta"
    elif goodtools_metadata.is_alpha:
        metadata["type"] = "Alpha"

    # Map dump quality
    if goodtools_metadata.dump_quality == DumpQuality.VERIFIED_GOOD:
        metadata["verified_good"] = True
    elif goodtools_metadata.dump_quality == DumpQuality.BAD:
        metadata["bad_dump"] = True
    elif goodtools_metadata.dump_quality == DumpQuality.OVERDUMP:
        metadata["overdump"] = True

    # Map ROM type
    if goodtools_metadata.rom_type == ROMType.HACK:
        metadata["hack"] = True
    elif goodtools_metadata.rom_type == ROMType.TRANSLATION:
        metadata["translation"] = True
        if goodtools_metadata.translation_language:
            metadata["translation_language"] = goodtools_metadata.translation_language
    elif goodtools_metadata.rom_type == ROMType.PIRATE:
        metadata["pirate"] = True
    elif goodtools_metadata.rom_type == ROMType.TRAINED:
        metadata["trained"] = True
    elif goodtools_metadata.rom_type == ROMType.HOMEBREW:
        metadata["homebrew"] = True

    # Map other attributes
    if goodtools_metadata.is_unlicensed:
        metadata["unlicensed"] = True
    if goodtools_metadata.sgb_enhanced:
        metadata["sgb_enhanced"] = True
    if goodtools_metadata.gb_compatible:
        metadata["gb_compatible"] = True
    if goodtools_metadata.cgb_enhanced:
        metadata["cgb_enhanced"] = True
    if goodtools_metadata.rumble_support:
        metadata["rumble_support"] = True
    if goodtools_metadata.is_multicart:
        metadata["multicart"] = goodtools_metadata.cart_name

    return metadata


def _looks_like_nointro(filename: str) -> bool:
    """Check if filename appears to use No-Intro naming convention.

    Args:
        filename: ROM filename to check

    Returns:
        True if filename appears to use No-Intro conventions
    """
    # No-Intro characteristics:
    # - Uses full region names in parentheses (USA, Europe, Japan)
    # - May have [BIOS] flag at beginning
    # - Uses two-letter language codes with capital first letter (En, Ja, Fr)
    # - Uses (v1.0) format for versions

    # Check for full region names
    nointro_regions = [
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
        "Korea",
        "Brazil",
    ]
    has_full_region = any(f"({region})" in filename for region in nointro_regions)

    # Check for BIOS flag
    has_bios = filename.startswith("[BIOS]")

    # Check for No-Intro style language codes (En,Ja) vs GoodTools style (M3, Multi)
    has_nointro_lang = bool(re.search(r"\([A-Z][a-z](?:,[A-Z][a-z])*\)", filename))

    # If it has BIOS flag or full region names, it's likely No-Intro
    return has_bios or has_full_region or has_nointro_lang


def _nointro_to_dict(nointro_metadata: NoIntroMetadata) -> dict[str, Any]:
    """Convert NoIntroMetadata to dictionary format.

    Args:
        nointro_metadata: NoIntroMetadata object

    Returns:
        Dictionary with metadata fields
    """
    metadata = {}

    # Map BIOS flag
    if nointro_metadata.bios_flag:
        metadata["bios"] = True

    # Map regions
    if nointro_metadata.regions:
        metadata["region"] = ", ".join(nointro_metadata.regions)

    # Map languages
    if nointro_metadata.languages:
        metadata["language"] = ", ".join(nointro_metadata.languages)

    # Map version/revision
    if nointro_metadata.version:
        metadata["version"] = f"v{nointro_metadata.version}"
    elif nointro_metadata.revision:
        metadata["version"] = f"Rev {nointro_metadata.revision}"

    # Map release status
    if nointro_metadata.release_status == ReleaseStatus.DEMO:
        metadata["type"] = "Demo"
        if nointro_metadata.status_number:
            metadata["type"] += f" {nointro_metadata.status_number}"
    elif nointro_metadata.release_status == ReleaseStatus.PROTO:
        metadata["type"] = "Prototype"
        if nointro_metadata.status_number:
            metadata["type"] += f" {nointro_metadata.status_number}"
    elif nointro_metadata.release_status == ReleaseStatus.BETA:
        metadata["type"] = "Beta"
        if nointro_metadata.status_number:
            metadata["type"] += f" {nointro_metadata.status_number}"
    elif nointro_metadata.release_status == ReleaseStatus.ALPHA:
        metadata["type"] = "Alpha"
    elif nointro_metadata.release_status == ReleaseStatus.SAMPLE:
        metadata["type"] = "Sample"

    # Map dump status
    if nointro_metadata.dump_status == DumpStatus.BAD:
        metadata["bad_dump"] = True
    elif nointro_metadata.dump_status == DumpStatus.OVERDUMP:
        metadata["overdump"] = True
    elif nointro_metadata.dump_status == DumpStatus.UNDERDUMP:
        metadata["underdump"] = True
    elif nointro_metadata.dump_status == DumpStatus.HACKED:
        metadata["hack"] = True
    elif nointro_metadata.dump_status == DumpStatus.PIRATED:
        metadata["pirate"] = True
    elif nointro_metadata.dump_status == DumpStatus.TRAINED:
        metadata["trained"] = True
    elif nointro_metadata.dump_status == DumpStatus.TRANSLATED:
        metadata["translation"] = True

    # Map other attributes
    if nointro_metadata.is_unlicensed:
        metadata["unlicensed"] = True
    if nointro_metadata.is_promo:
        metadata["promo"] = True
    if nointro_metadata.is_not_for_sale:
        metadata["not_for_sale"] = True
    if nointro_metadata.alt_version:
        metadata["alt_version"] = nointro_metadata.alt_version
    if nointro_metadata.media_type:
        metadata["media_type"] = nointro_metadata.media_type
    if nointro_metadata.media_label:
        metadata["media_label"] = nointro_metadata.media_label

    return metadata


def _looks_like_tosec(filename: str) -> bool:
    """Check if filename appears to use TOSEC naming convention.

    Args:
        filename: ROM filename to check

    Returns:
        True if filename appears to use TOSEC conventions
    """
    # TOSEC characteristics:
    # - Must have at least (date)(publisher) format
    # - Date is always in YYYY or YYYY-MM-DD format in first parentheses after title
    # - Publisher follows date
    # - May have dump flags in square brackets

    # Check for TOSEC date pattern - (YYYY) or (YYYY-MM-DD) or (19xx) etc
    has_tosec_date = (
        bool(re.search(r"\((?:19|20)\d{2}(?:-\d{2}(?:-\d{2})?)?(?:[-](?:19|20)\d{2})?\)", filename))
        or bool(re.search(r"\(19[x]{2}\)", filename))
        or bool(re.search(r"\(199[x]\)", filename))
    )

    # Check for at least two sets of parentheses (date and publisher minimum)
    paren_count = filename.count("(")

    # TOSEC files often have dump flags
    has_dump_flags = bool(re.search(r"\[[a-z!]+(?:\d+)?\]", filename))

    # Must have date pattern and multiple parentheses
    return has_tosec_date and paren_count >= 2


def _tosec_to_dict(tosec_metadata: TOSECMetadata) -> dict[str, Any]:
    """Convert TOSECMetadata to dictionary format.

    Args:
        tosec_metadata: TOSECMetadata object

    Returns:
        Dictionary with metadata fields
    """
    metadata = {}

    # Map basic info
    if tosec_metadata.version:
        metadata["version"] = tosec_metadata.version

    if tosec_metadata.demo:
        metadata["type"] = f"Demo ({tosec_metadata.demo})"

    if tosec_metadata.date:
        metadata["date"] = tosec_metadata.date

    if tosec_metadata.publisher:
        metadata["publisher"] = tosec_metadata.publisher

    # Map system/machine
    if tosec_metadata.system:
        metadata["system"] = tosec_metadata.system

    # Map video standard
    if tosec_metadata.video:
        metadata["video"] = tosec_metadata.video

    # Map countries to regions
    if tosec_metadata.countries:
        metadata["region"] = ", ".join(tosec_metadata.countries)

    # Map languages
    if tosec_metadata.languages:
        metadata["language"] = ", ".join(tosec_metadata.languages)

    # Map copyright status
    if tosec_metadata.copyright_status:
        metadata["copyright"] = tosec_metadata.copyright_status

    # Map development status
    if tosec_metadata.development_status:
        metadata["development"] = tosec_metadata.development_status

    # Map media info
    if tosec_metadata.media_type:
        metadata["media_type"] = tosec_metadata.media_type

    if tosec_metadata.media_label:
        metadata["media_label"] = tosec_metadata.media_label

    # Map dump info flags
    if tosec_metadata.dump_info:
        dump_flags = []
        if tosec_metadata.dump_info.get("cracked"):
            dump_flags.append("cracked")
        if tosec_metadata.dump_info.get("fixed"):
            dump_flags.append("fixed")
        if tosec_metadata.dump_info.get("hacked"):
            dump_flags.append("hacked")
        if tosec_metadata.dump_info.get("modified"):
            dump_flags.append("modified")
        if tosec_metadata.dump_info.get("pirated"):
            dump_flags.append("pirated")
        if tosec_metadata.dump_info.get("trained"):
            dump_flags.append("trained")
        if tosec_metadata.dump_info.get("translated"):
            dump_flags.append("translated")
        if tosec_metadata.dump_info.get("overdump"):
            dump_flags.append("overdump")
        if tosec_metadata.dump_info.get("underdump"):
            dump_flags.append("underdump")
        if tosec_metadata.dump_info.get("virus"):
            dump_flags.append("virus")
        if tosec_metadata.dump_info.get("bad_dump"):
            dump_flags.append("bad_dump")
        if tosec_metadata.dump_info.get("alternate"):
            dump_flags.append("alternate")
        if tosec_metadata.dump_info.get("known_verified"):
            dump_flags.append("verified")

        if dump_flags:
            metadata["dump_flags"] = ", ".join(dump_flags)

    # Map more info
    if tosec_metadata.more_info:
        metadata["more_info"] = tosec_metadata.more_info

    return metadata

"""No-Intro ROM naming convention parser.

This module parses ROM filenames following the No-Intro naming conventions,
extracting metadata tags for region, language, version, and other attributes.

Reference: https://wiki.no-intro.org/index.php?title=Naming_Convention
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
class NoIntroMetadata(BaseROMMetadata):
    """Container for parsed No-Intro metadata.

    No-Intro specific additions to the base metadata.
    """

    # No-Intro specific flags
    is_not_for_sale: bool = False  # (NFS)
    is_promo: bool = False  # (Promo)
    serial_code: str | None = None  # Product code in the name


class NoIntroParser(BaseROMParser):
    """Parser for No-Intro ROM naming conventions."""

    def get_format_name(self) -> str:
        """Get the name of this naming convention format."""
        return "No-Intro"

    def can_parse(self, filename: str) -> bool:
        """Check if this parser can handle the given filename.

        No-Intro characteristics:
        - Uses full region names in parentheses: (USA), (Europe), (Japan)
        - Has [BIOS] flag at the beginning
        - Uses (v1.0), (Rev 1) for versions
        - Has specific status tags: (Proto), (Beta), (Demo), (Sample)
        - Simple dump status tags in brackets: [b], [o], [u]
        """
        # Check for BIOS flag at beginning
        if filename.startswith("[BIOS]"):
            return True

        # Check for full region names (No-Intro signature)
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
            "Brazil",
            "Korea",
            "China",
            "Russia",
            "Canada",
            "United Kingdom",
            "Sweden",
            "Denmark",
            "Finland",
        ]

        for region in full_regions:
            if re.search(rf"\({region}\)", filename):
                # Make sure it's not TOSEC format
                if not self._looks_like_tosec(filename):
                    return True

        # Check for No-Intro specific tags
        nointro_tags = [
            r"\(Proto(?:\s+\d+)?\)",  # (Proto) or (Proto 1)
            r"\(Beta(?:\s+\d+)?\)",  # (Beta) or (Beta 1)
            r"\(Demo(?:\s+\d+)?\)",  # (Demo) or (Demo 1)
            r"\(Sample\)",
            r"\(NFS\)",  # Not For Sale
            r"\(Promo\)",
            r"\(Unl\)",  # Unlicensed
            r"\(Alt(?:\s+\d+)?\)",  # Alternative
        ]

        for tag in nointro_tags:
            if re.search(tag, filename):
                return True

        return False

    def _looks_like_tosec(self, filename: str) -> bool:
        """Check if filename looks more like TOSEC format."""
        # TOSEC has dates and publishers
        has_date = bool(re.search(r"\((?:\d{4}|\d{2}xx)(?:-\d{2})?(?:-\d{2})?\)", filename))
        has_dump_flags = bool(re.search(r"\[(cr|f|h|m|p|t|tr|o|u|v|b|a|!)\]", filename))
        return has_date or has_dump_flags

    def parse(self, filename: str) -> NoIntroMetadata:
        """Parse a ROM filename for No-Intro metadata."""
        # Check for BIOS flag at the beginning
        is_bios = filename.startswith("[BIOS]")
        if is_bios:
            filename = filename[6:].strip()

        metadata = NoIntroMetadata(
            clean_name=self._extract_clean_name_nointro(filename),
            original_filename=filename,
            is_bios=is_bios,
        )

        # Parse regions (mandatory in No-Intro)
        metadata.regions = self._parse_regions(filename)

        # Parse languages
        metadata.languages = self._parse_languages(filename)

        # Parse version/revision
        metadata.version = self.parse_version(filename)
        metadata.revision = self.parse_revision(filename)

        # Parse release status with numbered versions
        metadata.release_status, metadata.release_number = self._parse_release_status(filename)

        # Parse special flags
        if self.check_tag(filename, r"\(Unl\)"):
            metadata.copyright_status = CopyrightStatus.UNLICENSED

        metadata.is_promo = self.check_tag(filename, r"\(Promo\)")
        metadata.is_not_for_sale = self.check_tag(filename, r"\(NFS\)")

        # Parse alternative version
        alt_match = re.search(r"\(Alt(?:\s+(\d+))?\)", filename)
        if alt_match:
            metadata.alt_version = f"Alt {alt_match.group(1)}" if alt_match.group(1) else "Alt"

        # Parse media type
        media_types = ["CD", "DVD", "UMD", "Cart", "Disk", "Tape", "Card"]
        for media in media_types:
            if re.search(rf"\({media}\)", filename):
                metadata.media_type = media
                break

        # Parse media label (for multi-disc games)
        disc_match = re.search(r"\((Dis[ck]\s+[^)]+)\)", filename)
        if disc_match:
            metadata.media_label = disc_match.group(1)
        else:
            side_match = re.search(r"\((Side\s+[A-Z])\)", filename)
            if side_match:
                metadata.media_label = side_match.group(1)

        # Parse dump status from square brackets (simple No-Intro style)
        metadata.dump_quality = self._parse_dump_status(filename)

        # Store special No-Intro flags in extra metadata
        if metadata.is_promo:
            metadata.extra_metadata["promo"] = True
        if metadata.is_not_for_sale:
            metadata.extra_metadata["nfs"] = True

        # Store all tags for reference
        metadata.raw_tags = self.extract_all_tags(filename)

        return metadata

    def _extract_clean_name_nointro(self, filename: str) -> str:
        """Extract clean game name for No-Intro format.

        No-Intro format: everything before first parenthesis is the clean name.
        """
        # Remove file extension
        name = filename.rsplit(".", 1)[0] if "." in filename else filename

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
        """
        regions = []
        seen = set()

        # Look for region names in parentheses
        # Check each known region
        for standard_region, variants in self.REGION_MAPPINGS.items():
            # Check if any variant appears in the filename
            for variant in variants:
                if len(variant) > 2:  # Only check longer names for No-Intro
                    # Check for standalone region
                    if re.search(rf"\({re.escape(variant)}\)", filename):
                        if standard_region not in seen:
                            regions.append(standard_region)
                            seen.add(standard_region)
                            break
                    # Check for region in comma-separated list
                    elif re.search(rf"\([^)]*\b{re.escape(variant)}\b[^)]*\)", filename):
                        # Verify it's in a region context (with commas or other regions)
                        pattern = rf"\(([^)]*\b{re.escape(variant)}\b[^)]*)\)"
                        match = re.search(pattern, filename)
                        if match:
                            content = match.group(1)
                            # Check if this looks like a region list
                            if "," in content or any(
                                v in content
                                for std, vars in self.REGION_MAPPINGS.items()
                                for v in vars
                                if len(v) > 2 and v != variant
                            ):
                                if standard_region not in seen:
                                    regions.append(standard_region)
                                    seen.add(standard_region)
                                    break

        return regions

    def _parse_languages(self, filename: str) -> list[str]:
        """Parse language codes from filename.

        No-Intro uses ISO 639-1 two-letter codes with first letter uppercase.
        """
        languages = []
        seen = set()

        # Find all parenthetical groups
        paren_groups = re.findall(r"\(([^)]+)\)", filename)

        for group in paren_groups:
            # Check if this group contains language codes
            # Language groups typically have 2-letter codes separated by commas
            if "," in group:
                parts = [p.strip() for p in group.split(",")]
                # Check if all parts are 2-letter language codes
                if all(len(p) == 2 and p[0].isupper() and p[1].islower() for p in parts):
                    # This looks like a language list
                    for code in parts:
                        lang = self.normalize_language(code)
                        if lang and lang not in seen:
                            languages.append(lang)
                            seen.add(lang)
            else:
                # Single item - check if it's a language code
                code = group.strip()
                if len(code) == 2 and code[0].isupper() and code[1].islower():
                    lang = self.normalize_language(code)
                    if lang and lang not in seen:
                        languages.append(lang)
                        seen.add(lang)

        return languages

    def _parse_release_status(self, filename: str) -> tuple[ReleaseStatus, int | None]:
        """Parse release/development status.

        Returns:
            Tuple of (ReleaseStatus, optional number for numbered releases)
        """
        # Check for Proto
        proto_match = re.search(r"\(Proto(?:\s+(\d+))?\)", filename)
        if proto_match:
            num = int(proto_match.group(1)) if proto_match.group(1) else None
            return ReleaseStatus.PROTOTYPE, num

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

    def _parse_dump_status(self, filename: str) -> DumpQuality:
        """Parse dump status from square brackets.

        No-Intro uses simple status indicators.
        """
        # Check various dump status indicators
        if "[b]" in filename:
            return DumpQuality.BAD
        if "[o]" in filename:
            return DumpQuality.OVERDUMP
        if "[u]" in filename:
            return DumpQuality.UNDERDUMP
        if "[cr]" in filename:
            return DumpQuality.CRACKED
        if "[f]" in filename:
            return DumpQuality.FIXED
        if "[h]" in filename:
            return DumpQuality.HACKED
        if "[m]" in filename:
            return DumpQuality.MODIFIED
        if "[p]" in filename:
            return DumpQuality.PIRATED
        if "[t]" in filename:
            return DumpQuality.TRAINED
        if "[tr]" in filename:
            return DumpQuality.TRANSLATED

        # No-Intro assumes good dump if no status tag
        return DumpQuality.GOOD

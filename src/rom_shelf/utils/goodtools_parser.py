"""GoodTools ROM naming convention parser.

This module parses ROM filenames following the GoodTools naming conventions,
extracting metadata tags for ROM quality, region, language, and other attributes.

Reference: https://emulation.gametechwiki.com/index.php/GoodTools
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
class GoodToolsMetadata(BaseROMMetadata):
    """Container for parsed GoodTools metadata."""

    # Translation info (GoodTools specific)
    translation_language: str | None = None
    translation_version: str | None = None
    translation_author: str | None = None
    is_old_translation: bool = False  # [T-]

    # GoodTools specific flags
    is_multicart: bool = False
    cart_name: str | None = None  # For multicarts like "4-in-1"


class GoodToolsParser(BaseROMParser):
    """Parser for GoodTools ROM naming conventions."""

    # Multi-region codes specific to GoodTools
    MULTI_REGION_CODES = {
        "JUE": ["Japan", "United States", "Europe"],
        "UE": ["United States", "Europe"],
        "JU": ["Japan", "United States"],
        # Numeric codes
        "1": "Japan & Korea",
        "4": "USA & Brazil NTSC",
        "5": "NTSC",
        "8": "PAL",
    }

    def get_format_name(self) -> str:
        """Get the name of this naming convention format."""
        return "GoodTools"

    def can_parse(self, filename: str) -> bool:
        """Check if this parser can handle the given filename.

        GoodTools characteristics:
        - Uses single-letter region codes in parentheses (U), (J), (E), (JUE)
        - Has dump quality tags like [!], [b], [o], [f], [a]
        - Has ROM type tags like [h], [p], [t], [T+], [T-]
        - Uses specific patterns for multicarts (N-in-1)
        """
        # Check for GoodTools specific tags
        has_goodtools_dump_tag = bool(re.search(r"\[(!|!p|[bofah])\d*\]", filename))

        # Check for translation tags
        has_translation_tag = bool(re.search(r"\[T[+-]", filename))

        # Check for single-letter region codes
        has_letter_region = bool(re.search(r"\([UJEKAFGISCBWDXYZ]+\)", filename))

        # Check for multicart pattern
        has_multicart = bool(re.search(r"\(\d+-?in-?\d+\)", filename, re.IGNORECASE))

        return (
            has_goodtools_dump_tag
            or has_translation_tag
            or (has_letter_region and not self._looks_like_nointro(filename))
            or has_multicart
        )

    def _looks_like_nointro(self, filename: str) -> bool:
        """Check if filename looks more like No-Intro format."""
        # No-Intro uses full region names
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
        ]
        for region in full_regions:
            if re.search(rf"\({region}\)", filename):
                return True
        return False

    def parse(self, filename: str) -> GoodToolsMetadata:
        """Parse a ROM filename for GoodTools metadata."""
        metadata = GoodToolsMetadata(
            clean_name=self.extract_clean_name(filename), original_filename=filename
        )

        # Parse dump quality tags [!], [b], [o], etc.
        metadata.dump_quality = self._parse_dump_quality(filename)

        # Parse ROM type/translation tags
        self._parse_rom_type_and_translation(filename, metadata)

        # Parse regions using GoodTools-specific codes
        metadata.regions = self._parse_regions(filename)

        # Parse languages
        metadata.languages = self._parse_languages(filename)

        # Parse version info
        metadata.version = self.parse_version(filename)
        metadata.revision = self.parse_revision(filename)

        # Parse release status
        metadata.release_status = self._parse_release_status(filename)

        # Parse copyright status
        if self.check_tag(filename, r"\(Unl(?:icensed)?\)", case_insensitive=True):
            metadata.copyright_status = CopyrightStatus.UNLICENSED
        elif re.search(r"\(PD\)", filename) or re.search(r"\(Homebrew\)", filename):
            metadata.copyright_status = CopyrightStatus.HOMEBREW

        # Parse multicart info
        multicart_match = re.search(r"\((\d+)-?in-?(\d+)\)", filename, re.IGNORECASE)
        if multicart_match:
            metadata.is_multicart = True
            metadata.cart_name = multicart_match.group(0).strip("()")
            metadata.extra_metadata["multicart"] = metadata.cart_name

        # Platform-specific features (Game Boy enhancements)
        if self.check_tag(filename, r"\(SGB Enhanced\)", case_insensitive=True):
            metadata.special_features["sgb_enhanced"] = True
        if self.check_tag(filename, r"\(GB Compatible\)", case_insensitive=True):
            metadata.special_features["gb_compatible"] = True
        if self.check_tag(filename, r"\(CGB.*Enhanced\)", case_insensitive=True):
            metadata.special_features["cgb_enhanced"] = True
        if self.check_tag(filename, r"\(Rumble.*Version\)", case_insensitive=True):
            metadata.special_features["rumble_support"] = True

        # Check for BIOS tag
        metadata.is_bios = self.check_tag(filename, r"\[BIOS\]", case_insensitive=True)

        # Store all tags for reference
        metadata.raw_tags = self.extract_all_tags(filename)

        return metadata

    def _parse_dump_quality(self, filename: str) -> DumpQuality:
        """Parse dump quality tags specific to GoodTools."""
        if re.search(r"\[!\]", filename):
            return DumpQuality.VERIFIED_GOOD
        if re.search(r"\[!p\]", filename):
            return DumpQuality.PENDING
        if re.search(r"\[b\d*\]", filename):
            return DumpQuality.BAD
        if re.search(r"\[o\d*\]", filename):
            return DumpQuality.OVERDUMP
        if re.search(r"\[a\d*\]", filename):
            return DumpQuality.ALTERNATE
        if re.search(r"\[f\d*\]", filename):
            return DumpQuality.FIXED
        if re.search(r"\[h\d*[^\]]*\]", filename):
            return DumpQuality.HACKED
        return DumpQuality.UNKNOWN

    def _parse_rom_type_and_translation(self, filename: str, metadata: GoodToolsMetadata) -> None:
        """Parse ROM type and translation information."""
        # Check for translations first (can have additional info)
        trans_match = re.search(r"\[T([+-])([^]]*)\]", filename)
        if trans_match:
            metadata.is_old_translation = trans_match.group(1) == "-"
            metadata.dump_quality = DumpQuality.TRANSLATED

            trans_details = trans_match.group(2)
            if trans_details:
                # Language code (first 2-3 letters)
                lang_match = re.match(r"([A-Za-z]{2,3})", trans_details)
                if lang_match:
                    lang_code = lang_match.group(1).capitalize()
                    metadata.translation_language = self.normalize_language(lang_code) or lang_code

                # Version number
                ver_match = re.search(r"(\d+(?:\.\d+)*)", trans_details)
                if ver_match:
                    metadata.translation_version = ver_match.group(1)

                # Translator/group name (after underscore)
                author_match = re.search(r"_(.+)$", trans_details)
                if author_match:
                    metadata.translation_author = author_match.group(1)

            # Store in extra metadata
            metadata.extra_metadata["translation_type"] = (
                "old" if metadata.is_old_translation else "new"
            )
            if metadata.translation_language:
                metadata.extra_metadata["translation_language"] = metadata.translation_language
            if metadata.translation_author:
                metadata.extra_metadata["translation_author"] = metadata.translation_author

        # Check for other modifications
        elif re.search(r"\[p\d*\]", filename):
            metadata.dump_quality = DumpQuality.PIRATED
        elif re.search(r"\[t\d*\]", filename):
            metadata.dump_quality = DumpQuality.TRAINED

    def _parse_regions(self, filename: str) -> list[str]:
        """Parse region codes from filename using GoodTools conventions."""
        regions = []
        seen = set()

        # Check for single-letter region codes in parentheses
        code_match = re.search(r"\(([UJEKAFGISCBWDXYZ]+)\)", filename)
        if code_match:
            codes = code_match.group(1)

            # Check if it's a known multi-region code
            if codes in self.MULTI_REGION_CODES:
                region_list = self.MULTI_REGION_CODES[codes]
                if isinstance(region_list, list):
                    regions.extend(region_list)
                else:
                    regions.append(region_list)
            else:
                # Parse individual letters
                for letter in codes:
                    region = self.normalize_region(letter)
                    if region and region not in seen:
                        regions.append(region)
                        seen.add(region)

        # Check for numeric region codes
        for num_code in ["1", "4", "5", "8"]:
            if re.search(rf"\({num_code}\)", filename):
                region = self.MULTI_REGION_CODES.get(num_code)
                if region and region not in seen:
                    regions.append(region)
                    seen.add(region)

        return regions

    def _parse_languages(self, filename: str) -> list[str]:
        """Parse language codes from filename."""
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

        # Look for explicit language codes (En), (En,Fr), (En+Fr), (En-Fr)
        for separator in [",", "+", "-"]:
            pattern = rf"\(([A-Z][a-z](?:{re.escape(separator)}[A-Z][a-z])*)\)"
            for match in re.finditer(pattern, filename):
                lang_str = match.group(1)
                for lang_code in re.split(rf"[{re.escape(separator)}]", lang_str):
                    lang_code = lang_code.strip()
                    lang_name = self.normalize_language(lang_code)
                    if lang_name and lang_name not in seen:
                        languages.append(lang_name)
                        seen.add(lang_name)

        return languages

    def _parse_release_status(self, filename: str) -> ReleaseStatus:
        """Parse release status from filename."""
        if self.check_tag(filename, r"\(Proto(?:type)?.*?\)", case_insensitive=True):
            return ReleaseStatus.PROTOTYPE
        if self.check_tag(filename, r"\(Beta.*?\)", case_insensitive=True):
            return ReleaseStatus.BETA
        if self.check_tag(filename, r"\(Alpha.*?\)", case_insensitive=True):
            return ReleaseStatus.ALPHA
        if self.check_tag(filename, r"\(Demo.*?\)", case_insensitive=True):
            return ReleaseStatus.DEMO
        if self.check_tag(filename, r"\(Sample.*?\)", case_insensitive=True):
            return ReleaseStatus.SAMPLE
        return ReleaseStatus.FINAL

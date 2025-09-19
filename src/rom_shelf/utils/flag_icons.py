"""Flag icon utilities for ROM regions.

Flag SVG files are sourced from:
- https://github.com/lipis/flag-icons (MIT License)
- Custom flags created for special regions (world, unknown, asia, proto)
"""

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer


class FlagIcons:
    """Utility class for managing region flag display using SVG files.

    Flags are loaded from the images/flags directory and include country flags
    from the flag-icons project as well as custom flags for special regions.
    """

    # Map region codes to ISO country codes for SVG file lookup
    REGION_TO_ISO: dict[str, str] = {
        # Primary regions
        "USA": "us",
        "US": "us",
        "U": "us",
        "EUR": "eu",
        "Europe": "eu",
        "E": "eu",
        "JPN": "jp",
        "Japan": "jp",
        "J": "jp",
        "World": "world",
        "Unknown": "unknown",
        # Countries
        "GER": "de",
        "Germany": "de",
        "FRA": "fr",
        "France": "fr",
        "ITA": "it",
        "Italy": "it",
        "SPA": "es",
        "Spain": "es",
        "KOR": "kr",
        "Korea": "kr",
        "BRA": "br",
        "Brazil": "br",
        "AUS": "au",
        "Australia": "au",
        "China": "cn",
        "CHN": "cn",
        # European countries (language codes)
        "Netherlands": "nl",
        "Nl": "nl",
        "Portugal": "pt",
        "Pt": "pt",
        "Sweden": "se",
        "Sv": "se",
        "Denmark": "dk",
        "Da": "dk",
        "Norway": "no",
        "No": "no",
        "Finland": "fi",
        "Fi": "fi",
        # Language codes that map to countries
        "En": "us",  # English -> USA flag
        "Fr": "fr",  # French -> France flag
        "De": "de",  # German -> Germany flag
        "Es": "es",  # Spanish -> Spain flag
        "It": "it",  # Italian -> Italy flag
        "Ja": "jp",  # Japanese -> Japan flag
        "Ko": "kr",  # Korean -> Korea flag
        "Zh": "cn",  # Chinese -> China flag
        # Special regions
        "Asia": "asia",  # Custom asia flag
        "Prototype": "proto",  # Custom prototype flag
        "PAL": "eu",  # PAL region -> EU flag
        "NTSC": "us",  # NTSC region -> US flag (could be custom)
    }

    # Text representations for regions
    REGION_TEXT: dict[str, str] = {
        # Primary regions
        "USA": "USA",
        "US": "USA",
        "U": "USA",
        "EUR": "Europe",
        "Europe": "Europe",
        "E": "Europe",
        "JPN": "Japan",
        "Japan": "Japan",
        "J": "Japan",
        "World": "World",
        "Unknown": "Unknown",
        # Countries
        "GER": "Germany",
        "Germany": "Germany",
        "FRA": "France",
        "France": "France",
        "ITA": "Italy",
        "Italy": "Italy",
        "SPA": "Spain",
        "Spain": "Spain",
        "KOR": "Korea",
        "Korea": "Korea",
        "BRA": "Brazil",
        "Brazil": "Brazil",
        "AUS": "Australia",
        "Australia": "Australia",
        "China": "China",
        "CHN": "China",
        # European countries
        "Netherlands": "Netherlands",
        "Nl": "Netherlands",
        "Portugal": "Portugal",
        "Pt": "Portugal",
        "Sweden": "Sweden",
        "Sv": "Sweden",
        "Denmark": "Denmark",
        "Da": "Denmark",
        "Norway": "Norway",
        "No": "Norway",
        "Finland": "Finland",
        "Fi": "Finland",
        # Language codes
        "En": "English",
        "Fr": "French",
        "De": "German",
        "Es": "Spanish",
        "It": "Italian",
        "Ja": "Japanese",
        "Ko": "Korean",
        "Zh": "Chinese",
        # Special regions
        "Asia": "Asia",
        "Prototype": "Prototype",
        "PAL": "PAL Region",
        "NTSC": "NTSC Region",
        # Multi-region combinations
        "USA/EUR": "USA/Europe",
        "USA/Europe": "USA/Europe",
        "USA/EUR/JPN": "USA/Europe/Japan",
        "JPN/USA": "Japan/USA",
        "Japan/USA": "Japan/USA",
        "USA/AUS": "USA/Australia",
        "USA/Australia": "USA/Australia",
        "EUR/AUS": "Europe/Australia",
        "Europe/Australia": "Europe/Australia",
        "USA/BRA": "USA/Brazil",
        "USA/Brazil": "USA/Brazil",
        "USA/EUR/BRA": "USA/Europe/Brazil",
        "USA/Europe/Brazil": "USA/Europe/Brazil",
        "USA/EUR/KOR": "USA/Europe/Korea",
        "USA/Europe/Korea": "USA/Europe/Korea",
    }

    @staticmethod
    def _get_flags_directory() -> Path:
        """Get the path to the flags directory."""
        # Get the current file's directory and navigate to images/flags
        current_dir = Path(__file__).parent
        return current_dir.parent / "images" / "flags"

    @staticmethod
    def _load_svg_flag(iso_code: str, size: QSize) -> QIcon | None:
        """Load an SVG flag from file and convert to QIcon."""
        flags_dir = FlagIcons._get_flags_directory()
        svg_path = flags_dir / f"{iso_code}.svg"

        if not svg_path.exists():
            return None

        # Create SVG renderer
        renderer = QSvgRenderer(str(svg_path))
        if not renderer.isValid():
            return None

        # Create pixmap and render SVG
        pixmap = QPixmap(size)
        pixmap.fill(Qt.GlobalColor.transparent)

        from PySide6.QtGui import QPainter

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
        painter.end()

        return QIcon(pixmap)

    @staticmethod
    def create_flag_icon(region: str, size: QSize = QSize(16, 12)) -> QIcon | None:
        """
        Create a QIcon flag representation for a region.

        Args:
            region: Region code or name
            size: Size of the flag icon

        Returns:
            QIcon with flag representation or None if no flag available
        """
        # Handle multi-region by creating combined flag
        if "/" in region:
            return FlagIcons._create_multi_region_flag(region, size)

        # Get ISO code for the region
        iso_code = FlagIcons._get_iso_code(region)

        # If no region mapping found, try using the input directly as an ISO code
        if not iso_code:
            # Check if it's already a valid ISO code (if corresponding SVG exists)
            flags_dir = FlagIcons._get_flags_directory()
            svg_path = flags_dir / f"{region.lower()}.svg"
            if svg_path.exists():
                iso_code = region.lower()
            else:
                # Return unknown flag for unmapped regions
                return FlagIcons._load_svg_flag("unknown", size)

        # Try to load SVG flag
        return FlagIcons._load_svg_flag(iso_code, size)

    @staticmethod
    def _get_iso_code(region: str) -> str | None:
        """Get ISO code for a region."""
        # Direct match
        if region in FlagIcons.REGION_TO_ISO:
            return FlagIcons.REGION_TO_ISO[region]

        # Case-insensitive match
        region_upper = region.upper()
        for key, iso_code in FlagIcons.REGION_TO_ISO.items():
            if key.upper() == region_upper:
                return iso_code

        return None

    @staticmethod
    def _create_multi_region_flag(region: str, size: QSize) -> QIcon | None:
        """Create flag for multi-region games by combining individual flags."""
        regions = region.split("/")
        if len(regions) > 3:
            regions = regions[:3]  # Limit to 3 for space

        from PySide6.QtGui import QPainter

        pixmap = QPixmap(size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Divide width by number of regions
        section_width = size.width() // len(regions)

        for i, sub_region in enumerate(regions):
            sub_region = sub_region.strip()
            iso_code = FlagIcons._get_iso_code(sub_region)

            if not iso_code:
                # Use unknown flag for unmapped regions
                iso_code = "unknown"

            # Load and render SVG in section
            flags_dir = FlagIcons._get_flags_directory()
            svg_path = flags_dir / f"{iso_code}.svg"

            if svg_path.exists():
                renderer = QSvgRenderer(str(svg_path))
                if renderer.isValid():
                    from PySide6.QtCore import QRectF

                    x = i * section_width
                    target_rect = QRectF(x, 0, section_width, size.height())
                    renderer.render(painter, target_rect)

        # Add border
        from PySide6.QtGui import QColor

        painter.setPen(QColor("#888888"))
        painter.drawRect(0, 0, size.width() - 1, size.height() - 1)

        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def get_display_text_for_region(region: str, include_flag: bool = True) -> str:
        """
        Get the display text for a region.

        Args:
            region: Region code or name
            include_flag: Whether to include flag (not used, kept for compatibility)

        Returns:
            Display text for region
        """
        if not region:
            return ""

        # Try to get proper region text
        if region in FlagIcons.REGION_TEXT:
            return FlagIcons.REGION_TEXT[region]

        # Case-insensitive match
        region_upper = region.upper()
        for key, text in FlagIcons.REGION_TEXT.items():
            if key.upper() == region_upper:
                return text

        # Return original region name if no mapping found
        return region

    @staticmethod
    def get_flag_icon(region: str, size: QSize = QSize(16, 12)) -> QIcon | None:
        """
        Get a QIcon flag for a region.

        Args:
            region: Region code or name
            size: Size of the flag icon

        Returns:
            QIcon with flag or None if no flag available
        """
        return FlagIcons.create_flag_icon(region, size)

    @staticmethod
    def get_supported_regions() -> list[str]:
        """Get list of all supported regions."""
        return list(FlagIcons.REGION_TO_ISO.keys())

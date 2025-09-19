"""Twilight theme featuring purple-driven accents."""

from .base_theme import BaseTheme, ColorPalette


class TwilightTheme(BaseTheme):
    """Dark theme variant with vibrant purple accents."""

    def __init__(self) -> None:
        super().__init__("Twilight")

    def _create_color_palette(self) -> ColorPalette:
        """Create a rich violet-forward palette that meets WCAG AA targets."""
        return ColorPalette(
            # Core colors
            primary="#9B59B6",
            primary_hover="#B370CF",
            primary_pressed="#6C3483",
            secondary="#2D2533",
            accent="#E84393",
            # Background colors
            background="#1B1720",
            surface="#221D2A",
            surface_variant="#2A2333",
            card="#342B3D",
            overlay="#000000CC",
            # Text colors
            text="#D7D2E9",
            text_secondary="#A79FCC",
            text_disabled="#6F678A",
            text_on_primary="#FFFFFF",
            # State colors
            success="#4CAF50",
            warning="#FFB74D",
            error="#EF5350",
            info="#9575CD",
            # Interactive colors
            hover="#3B3147",
            pressed="#4C3A5A",
            selected="#9B59B6",
            selected_hover="#B370CF",
            focus="#9B59B6",
            focus_ring="#9B59B680",
            # Borders
            border="#4A3E57",
            border_light="#554563",
            border_strong="#6C5F7A",
            border_focus="#9B59B6",
            # Input surfaces
            input_bg="#2F2837",
            input_bg_hover="#352E3F",
            input_bg_focus="#3B3445",
            input_border="#5C4F6D",
            input_border_focus="#9B59B6",
            # Scrollbars
            scrollbar_bg="#241E2A",
            scrollbar_handle="#3F3451",
            scrollbar_handle_hover="#554063",
        )

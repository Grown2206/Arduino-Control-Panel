# -*- coding: utf-8 -*-
"""
Theme Constants - Zentrale Farb-, Font- und Spacing-Definitionen
"""

class Colors:
    """Farbpalette für die gesamte Anwendung"""
    SUCCESS = "#27ae60"
    WARNING = "#f39c12"
    ERROR = "#e74c3c"
    INFO = "#3498db"
    PRIMARY = "#34495e"
    SECONDARY = "#95a5a6"
    LIGHT = "#ecf0f1"
    DARK = "#2c3e50"
    WHITE = "#ffffff"


class Spacing:
    """Standard-Abstände und Margins"""
    MARGIN_STANDARD = 10
    MARGIN_LARGE = 20
    MARGIN_SMALL = 5
    SPACING_STANDARD = 10
    SPACING_SMALL = 5
    PADDING_STANDARD = 8
    PADDING_LARGE = 12
    PADDING_SMALL = 5


class Fonts:
    """Font-Größen und -Stile"""
    SIZE_HEADER = "16px"
    SIZE_STANDARD = "12px"
    SIZE_SMALL = "10px"
    SIZE_LARGE = "14px"
    WEIGHT_BOLD = "font-weight: bold;"
    WEIGHT_NORMAL = "font-weight: normal;"


def get_status_stylesheet(status_type='info'):
    """
    Gibt ein Stylesheet für Status-Labels zurück.

    Args:
        status_type: 'success', 'warning', 'error', oder 'info'

    Returns:
        str: Stylesheet-String
    """
    colors = {
        'success': Colors.SUCCESS,
        'warning': Colors.WARNING,
        'error': Colors.ERROR,
        'info': Colors.INFO
    }
    color = colors.get(status_type, Colors.INFO)
    return (f"background-color: {color}; color: {Colors.WHITE}; "
           f"padding: {Spacing.PADDING_STANDARD}px; "
           "border-radius: 4px; font-weight: bold; "
           f"font-size: {Fonts.SIZE_SMALL};")


def get_button_stylesheet(variant='primary'):
    """
    Gibt ein Stylesheet für Buttons zurück.

    Args:
        variant: 'primary', 'success', 'warning', 'error'

    Returns:
        str: Stylesheet-String
    """
    colors = {
        'primary': Colors.PRIMARY,
        'success': Colors.SUCCESS,
        'warning': Colors.WARNING,
        'error': Colors.ERROR
    }
    bg_color = colors.get(variant, Colors.PRIMARY)
    return (f"background-color: {bg_color}; color: {Colors.WHITE}; "
           f"padding: {Spacing.PADDING_STANDARD}px; "
           "border-radius: 4px; font-weight: bold;")


def get_group_box_stylesheet():
    """Gibt ein Stylesheet für QGroupBox zurück."""
    return f"""
    QGroupBox {{
        font-weight: bold;
        border: 2px solid {Colors.SECONDARY};
        border-radius: 5px;
        margin-top: 1em;
        padding-top: 10px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }}
    """

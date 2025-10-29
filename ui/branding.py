# -*- coding: utf-8 -*-
# Enthält Branding-Informationen und Design-Elemente für die Anwendung.

# Pfade zu den Ressourcen
LOGO_PATH = "assets/Logo.jpg"
MAIN_BACKGROUND_PATH = "assets/background.jpg"

# =============================================================================
# THEME KONFIGURATION
# =============================================================================
THEME_STYLES = {
    # -------------------------------------------------------------------------
    # GLOBALE STILE: Gelten für die gesamte Anwendung
    # -------------------------------------------------------------------------
    "global": f"""
        /* Hauptfenster-Stil */
        QMainWindow {{
            border-image: url({MAIN_BACKGROUND_PATH}) 0 0 0 0 stretch stretch;
        }}

        /* Allgemeine Transparenz für Container-Widgets wie QGroupBox */
        QGroupBox {{
            background-color: rgba(43, 43, 43, 0.75);
            border: 1px solid #444;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #ecf0f1;
        }}

        /* Basis-Stil für den Inhaltsbereich aller Tabs */
        QTabWidget::pane {{
            background-color: transparent;
            border: 1px solid #444;
            border-top: none;
        }}

        /* Stil für die Reiter (Tabs) */
        QTabBar::tab {{
            background-color: #173C3D;
            color: #ecf0f1;
            padding: 10px 20px;
            border: 1px solid #444;
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }}
        QTabBar::tab:selected {{
            background-color: #C2A447;
            color: white;
            font-weight: bold;
        }}
        QTabBar::tab:hover {{
            background-color: #5dade2;
        }}

        /* Allgemeine Stile für UI-Elemente */
        QPushButton {{
            background-color: #173C3D;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            font-weight: bold;
        }}
        QPushButton:hover {{ background-color: #5dade2; }}
        QPushButton:disabled {{ background-color: #555; color: #999; }}

        QLineEdit, QSpinBox, QComboBox {{
            background-color: #2c3e50;
            border: 1px solid #777;
            padding: 5px;
            border-radius: 3px;
            color: #ecf0f1; /* Textfarbe hinzugefügt */
        }}
        QComboBox::drop-down {{
            border: none; /* Pfeil-Hintergrund entfernen */
        }}
        QComboBox::down-arrow {{
            image: url(assets/down_arrow.png); /* Optional: Eigenes Pfeil-Icon */
        }}


        QTableWidget, QListWidget, QTextEdit {{
            background-color: rgba(30, 30, 30, 0.1);
            border: 1px solid #555;
        }}
        QHeaderView::section {{
            background-color: #34495e; /* Farbe angepasst */
            padding: 5px;
            border: 1px solid #555;
        }}

        /* --- NEU: Styling für Pin Widgets --- */
        #PinWidgetFrame {{
            border: 1px solid #444;
            border-radius: 8px;
            background-color: #31363B;
        }}
        #ValueLabel {{
            font-size: 28px;
            font-weight: bold;
            background-color: #262A2E;
            border-radius: 5px;
            padding: 10px;
            min-height: 40px;
        }}
    """,

    # -------------------------------------------------------------------------
    # SPEZIFISCHE TAB-STILE
    # -------------------------------------------------------------------------
    "#PinControlTab": """
        #PinControlTab { }
    """,
    "#SensorTab": """
        #SensorTab { }
    """,
    "#SequenceTab": """
        #SequenceTab { }
    """,
    "#ArchiveTab": """
        #ArchiveTab {
            background-color: rgba(20, 20, 20, 0.3);
        }
    """,
}

def get_full_stylesheet(theme="dark"):
    """
    Kombiniert alle Stildefinitionen zu einem einzigen Stylesheet-String.

    Args:
        theme: "dark" (default) oder "light"
    """
    if theme == "light":
        return get_light_stylesheet()

    # Dark theme mit Toolbar-Styling
    toolbar_style = """
        QToolBar {
            background-color: #2c3e50;
            border: 1px solid #34495e;
            spacing: 8px;
            padding: 5px;
        }
        QToolBar::separator {
            background-color: #7f8c8d;
            width: 2px;
            margin: 5px;
        }
        QToolButton {
            background-color: #34495e;
            color: #ecf0f1;
            border: 1px solid #555;
            border-radius: 4px;
            padding: 8px;
            margin: 2px;
        }
        QToolButton:hover {
            background-color: #5dade2;
            border: 1px solid #3498db;
        }
        QToolButton:pressed {
            background-color: #2980b9;
        }
        QToolButton:disabled {
            background-color: #555;
            color: #999;
        }
    """

    full_style = ""
    for key, style in THEME_STYLES.items():
        full_style += style
    full_style += toolbar_style
    return full_style


def get_light_stylesheet():
    """NEU: Light Theme Variante"""
    return """
        QMainWindow {
            background-color: #f5f5f5;
        }

        QGroupBox {
            background-color: rgba(255, 255, 255, 0.95);
            border: 1px solid #ccc;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #2c3e50;
        }

        QTabWidget::pane {
            background-color: transparent;
            border: 1px solid #ccc;
            border-top: none;
        }

        QTabBar::tab {
            background-color: #e0e0e0;
            color: #2c3e50;
            padding: 10px 20px;
            border: 1px solid #ccc;
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }
        QTabBar::tab:selected {
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }
        QTabBar::tab:hover {
            background-color: #5dade2;
        }

        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover { background-color: #5dade2; }
        QPushButton:disabled { background-color: #ccc; color: #999; }

        QLineEdit, QSpinBox, QComboBox {
            background-color: white;
            border: 1px solid #ccc;
            padding: 5px;
            border-radius: 3px;
            color: #2c3e50;
        }

        QTableWidget, QListWidget, QTextEdit {
            background-color: white;
            border: 1px solid #ccc;
            color: #2c3e50;
        }
        QHeaderView::section {
            background-color: #e0e0e0;
            padding: 5px;
            border: 1px solid #ccc;
            color: #2c3e50;
        }

        #PinWidgetFrame {
            background-color: rgba(255, 255, 255, 0.95);
            border: 2px solid #3498db;
            border-radius: 10px;
        }

        QLabel, QCheckBox {
            color: #2c3e50;
        }

        QStatusBar {
            background-color: #e0e0e0;
            color: #2c3e50;
        }

        /* Toolbar Styling für Light Theme */
        QToolBar {
            background-color: #ecf0f1;
            border: 1px solid #bdc3c7;
            spacing: 8px;
            padding: 5px;
        }
        QToolBar::separator {
            background-color: #95a5a6;
            width: 2px;
            margin: 5px;
        }
        QToolButton {
            background-color: #3498db;
            color: white;
            border: 1px solid #2980b9;
            border-radius: 4px;
            padding: 8px;
            margin: 2px;
        }
        QToolButton:hover {
            background-color: #5dade2;
            border: 1px solid #3498db;
        }
        QToolButton:pressed {
            background-color: #2980b9;
        }
        QToolButton:disabled {
            background-color: #ccc;
            color: #999;
        }
    """

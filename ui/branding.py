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

def get_full_stylesheet():
    """Kombiniert alle Stildefinitionen zu einem einzigen Stylesheet-String."""
    full_style = ""
    for key, style in THEME_STYLES.items():
        full_style += style
    return full_style

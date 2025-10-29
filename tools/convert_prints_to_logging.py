#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatisches Konvertierungs-Script: print() -> logging

Ersetzt alle print() Statements durch strukturiertes Logging.
"""
import os
import re
import sys
from pathlib import Path


def convert_file(file_path):
    """
    Konvertiert print() Statements in einer Datei zu logging Aufrufen.

    Mapping:
    - print("✅ ...") -> logger.info("...")
    - print("⚠️ ...") -> logger.warning("...")
    - print("❌ ...") -> logger.error("...")
    - print(f"Fehler ...") -> logger.error("...")
    - print(f"Error ...") -> logger.error("...")
    - print(f"DEBUG: ...") -> logger.debug("...")
    - print("SIM ...") -> logger.debug("...")
    - print() (normal) -> logger.info()
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Check if logging is already imported
        has_logging_import = 'from core.logging_config import get_logger' in content
        has_logger = 'logger = get_logger(' in content

        # Add import if needed
        if not has_logging_import and 'print(' in content:
            # Find the first import or add at beginning
            import_match = re.search(r'^(import |from )', content, re.MULTILINE)
            if import_match:
                # Add after first import block
                lines = content.split('\n')
                insert_idx = 0
                for i, line in enumerate(lines):
                    if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('import') and not line.strip().startswith('from'):
                        insert_idx = i
                        break

                lines.insert(insert_idx, 'from core.logging_config import get_logger')
                lines.insert(insert_idx + 1, '')
                lines.insert(insert_idx + 2, 'logger = get_logger(__name__)')
                lines.insert(insert_idx + 3, '')
                content = '\n'.join(lines)
            else:
                content = 'from core.logging_config import get_logger\n\nlogger = get_logger(__name__)\n\n' + content

        # Convert print statements - various patterns
        conversions = [
            # Error patterns
            (r'print\(f?"?❌\s*([^"\']*)"?\)', r'logger.error(\1)'),
            (r'print\(f?"?(Fehler[^"\']*)"?\)', r'logger.error("\1")'),
            (r'print\(f?"?(Error[^"\']*)"?\)', r'logger.error("\1")'),

            # Warning patterns
            (r'print\(f?"?⚠️\s*([^"\']*)"?\)', r'logger.warning(\1)'),
            (r'print\(f?"?(Warnung[^"\']*)"?\)', r'logger.warning("\1")'),
            (r'print\(f?"?(Warning[^"\']*)"?\)', r'logger.warning("\1")'),

            # Success/Info patterns
            (r'print\(f?"?✅\s*([^"\']*)"?\)', r'logger.info(\1)'),

            # Debug patterns
            (r'print\(f?"?(DEBUG:|SIM |📤 |->)[^"\']*"?\)', r'logger.debug(\1)'),

            # Generic patterns - more careful replacement
            (r'^\s*print\(f"([^"]+)"\)', r'logger.info(f"\1")', re.MULTILINE),
            (r'^\s*print\("([^"]+)"\)', r'logger.info("\1")', re.MULTILINE),
            (r"^\s*print\('([^']+)'\)", r"logger.info('\1')", re.MULTILINE),
        ]

        for pattern, replacement in conversions:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False

    except Exception as e:
        print(f"Fehler bei {file_path}: {e}")
        return False


def main():
    """Hauptfunktion"""
    root_dir = Path(__file__).parent.parent

    # Directories to process
    directories = [
        root_dir / "analysis",
        root_dir / "core",
        root_dir / "ui",
        root_dir / "plugins",
        root_dir / "api",
    ]

    files_converted = 0

    for directory in directories:
        if not directory.exists():
            continue

        for py_file in directory.rglob("*.py"):
            # Skip this script itself and logging_config
            if py_file.name == 'convert_prints_to_logging.py' or py_file.name == 'logging_config.py':
                continue

            if convert_file(py_file):
                print(f"✓ Konvertiert: {py_file.relative_to(root_dir)}")
                files_converted += 1

    print(f"\n{files_converted} Dateien konvertiert.")


if __name__ == "__main__":
    main()

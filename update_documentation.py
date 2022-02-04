#!/usr/bin/env python3
from pathlib import Path


if __name__ == '__main__':
    from gcode_documentation_parser.updater import DocumentationUpdater
    DocumentationUpdater()\
        .update_documentation(
            output_directory=Path(__file__).parent / "output",
        )

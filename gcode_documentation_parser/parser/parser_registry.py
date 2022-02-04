import importlib
from typing import Dict, List, Set

from gcode_documentation_parser.parser import BaseDocumentationParser


class ParserRegistry:
    """A registry for all available parser classes"""

    PARSERS: Dict[str, BaseDocumentationParser] = {}
    SOURCES: Set[str] = set()
    PARSERS_IMPORTS: List[str] = [
        'gcode_documentation_parser.parser.parsers',
    ]

    @classmethod
    def register_parser(cls, parser):
        """Register a parser class"""
        cls.PARSERS[parser.ID] = parser
        cls.SOURCES.add(parser.SOURCE)

        return parser

    @classmethod
    def import_parsers(cls):
        """Import all the parsers"""
        for module_name in cls.PARSERS_IMPORTS:
            try:
                importlib.import_module(module_name)
            except Exception as e:
                print(f"Could not load {module_name}: {e}")
                raise


ParserRegistry.import_parsers()

import json
from pathlib import Path

from ..base_parser import BaseDocumentationParser
from ..parser_registry import ParserRegistry


__all__ = ['StaticGcodeDocumentationParser']


@ParserRegistry.register_parser
class StaticGcodeDocumentationParser(BaseDocumentationParser):
    """Documentation parser from static manually-created sources"""

    ID = "static"
    SOURCE = "Static"
    STATIC_PATH = Path(__file__).parent / "static_documentation.json"

    def load_and_parse_all_codes(self, directory):
        with self.STATIC_PATH.open("r") as f:
            data = json.load(f)
        return data

    def populate_temporary_directory(self, directory):
        pass

import importlib


class ParserRegistry:
    PARSERS = {}
    SOURCES = set()
    PARSERS_IMPORTS = [
        'gcode_documentation_parser.parser.parsers',
    ]

    @classmethod
    def register_parser(cls, parser):
        cls.PARSERS[parser.ID] = parser
        cls.SOURCES.add(parser.SOURCE)

        return parser

    @classmethod
    def import_parsers(cls):
        for module_name in cls.PARSERS_IMPORTS:
            try:
                importlib.import_module(module_name)
            except Exception as e:
                print(f"Could not load {module_name}: {e}")
                raise


ParserRegistry.import_parsers()

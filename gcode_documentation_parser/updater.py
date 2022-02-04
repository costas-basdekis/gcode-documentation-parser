import json
from pathlib import Path

from gcode_documentation_parser.parser.parser_registry import ParserRegistry


class DocumentationUpdater:
    """Manage updating the documentation from all parsers"""
    OUTPUT_PREFIXES = {
        "_window.js": "window.AllGcodes = ",
        "_const.js": "const AllGcodes = ",
        "_export.js": "export default const AllGcodes = ",
        ".json": "",
    }

    PARSER_REGISTRY = ParserRegistry

    def update_documentation(
        self, directories=None, output_directory=None, chatty=True,
    ):
        """Update the documentation and populate the output folder"""
        if chatty:
            parser_count = len(DocumentationUpdater.PARSER_REGISTRY.PARSERS)
            print(f"Updating using {parser_count} parsers")

        if output_directory is None:
            output_directory = Path(__file__).parent / "output"
        codes_list = []
        ids_to_update = set()
        if not self.PARSER_REGISTRY.PARSERS:
            raise Exception(f"No parsers have been registered")
        for _id, parser in self.PARSER_REGISTRY.PARSERS.items():
            if directories is None:
                directory = None
            else:
                if _id not in directories:
                    continue
                directory = directories[_id]
            gcodes = parser().load_and_parse_all_codes(directory)
            self.attach_id_to_docs(gcodes)
            codes_list.append(gcodes)
            ids_to_update.add(parser.ID)
        if not codes_list:
            raise Exception("No sources set to be updated")
        if set(self.PARSER_REGISTRY.PARSERS) - ids_to_update:
            all_codes = self.load_existing_codes(
                ids_to_update, output_directory,
            )
        else:
            all_codes = {}
        self.merge_codes(all_codes, codes_list)
        self.sort_codes(all_codes)
        self.save_codes_to_js(all_codes, output_directory)

        if chatty:
            code_count = len(all_codes)
            definition_count = sum(map(len, all_codes.values()))
            source_count = len({
                definition['source']
                for definitions in all_codes.values()
                for definition in definitions
            })
            print(
                f"Parsed {code_count} codes, "
                f"with {definition_count} definitions in total, "
                f"from {source_count} sources"
            )

        return all_codes

    def attach_id_to_docs(self, codes):
        """Attach a unique ID to each definition"""
        for code in list(codes):
            codes[code] = [
                dict(value, **{
                    "id": f"{value['source']}.{code}[{index}]"
                })
                for index, value in enumerate(codes[code])
            ]

    def load_existing_codes(self, ids_to_update, output_directory):
        """Load existing codes from a previous run"""
        path = output_directory / f"all_codes{self.OUTPUT_PREFIXES['.json']}"
        expected_prefix = self.OUTPUT_PREFIXES[".json"]
        with open(path) as f:
            prefix = f.read(len(expected_prefix))
            if prefix != expected_prefix:
                raise Exception(
                    f"Prefix in JS file ('{prefix}') didn't match expected "
                    f"prefix ('{expected_prefix}')")
            all_codes = json.load(f)
        sources_to_update = [
            self.PARSER_REGISTRY.PARSERS[_id].SOURCE
            for _id in ids_to_update
        ]
        for code, values in list(all_codes.items()):
            all_codes[code] = [
                value
                for value in values
                if value["source"] not in sources_to_update
            ]
        return all_codes

    def merge_codes(self, all_codes, codes_list):
        """Merge two code sets"""
        for codes in codes_list:
            for code, values in codes.items():
                all_codes.setdefault(code, []).extend(values)

    def sort_codes(self, all_codes):
        """Sort codes deterministically"""
        for code, values in list(all_codes.items()):
            all_codes[code] = sorted(
                values,
                key=lambda value: (value["id"], value["title"]),
            )

    def save_codes_to_js(self, all_codes, output_directory):
        """Save the output"""
        output_directory.mkdir(parents=True, exist_ok=True)
        for name_suffix, content_prefix in self.OUTPUT_PREFIXES.items():
            with open(output_directory / f"all_codes{name_suffix}", "w") as f:
                f.write(content_prefix)
                json.dump(all_codes, f, indent=2, sort_keys=True)

from gcode_documentation_parser.parser.parsers.reprap import (
    ReprapGcodeDocumentationParser,
)


PARSER = ReprapGcodeDocumentationParser()
GCODE_URL = ReprapGcodeDocumentationParser.GCODE_URL

# Mirrors the structure of the G-code wiki page: commands as level-4
# sections under the G-commands and M-commands headings, with their usage
# and parameters in definition lists.
SOURCE = """
== G-commands ==

==== G0 & G1: Move ====
{{Firmware Support | marlin={{yes}} }}

* <code>G0</code> : Rapid Move
* <code>G1</code> : Linear Move

;Usage
:<code>G1 Xnnn Ynnn</code>
;Parameters
:<code>Xnnn</code> The position to move to on the X axis
:<code>Ynnn</code> The position to move to on the Y axis

==== G4: Dwell ====
Pause the machine for a period of time.

;Usage
:<code>G4 Pnnn</code>
;Parameters
:<code>Pnnn</code> Time to wait, in milliseconds

== M-commands ==

==== M104: Set Extruder Temperature ====
Set a new target hot end temperature.

;Usage
:<code>M104 Snnn</code>
;Parameters
:<code>Snnn</code> Target temperature
"""


def test_commands_from_both_sections_are_parsed():
    assert set(PARSER.parse_documentation(SOURCE)) == {
        "G0", "G1", "G4", "M104"}


def test_entries_have_the_expected_shape():
    entry = PARSER.parse_documentation(SOURCE)["G4"][0]
    assert set(entry) == {
        "title", "brief", "codes", "related", "parameters", "source", "url"}
    assert entry["title"] == "G4: Dwell"
    assert entry["brief"] == "Pause the machine for a period of time."
    assert entry["codes"] == ["G4"]
    assert entry["source"] == "RepRap"


def test_parameters_are_parsed_with_their_descriptions():
    parameters = PARSER.parse_documentation(SOURCE)["M104"][0]["parameters"]
    assert [(p["tag"], p["label"]) for p in parameters] == [("S", "Snnn")]
    # The description keeps the separating space from the wiki markup.
    assert parameters[0]["description"].strip() == "Target temperature"


def test_a_section_documenting_several_codes_is_shared_by_them():
    codes = PARSER.parse_documentation(SOURCE)
    assert codes["G0"][0]["codes"] == ["G0", "G1"]
    assert codes["G0"] == codes["G1"]


def test_firmware_support_template_is_left_out_of_the_brief():
    brief = PARSER.parse_documentation(SOURCE)["G1"][0]["brief"]
    assert "Firmware Support" not in brief
    assert "yes" not in brief


def test_urls_point_at_the_section_anchor():
    url = PARSER.parse_documentation(SOURCE)["G4"][0]["url"]
    assert url == f"{GCODE_URL}#G4:_Dwell"


def test_source_without_command_sections_is_empty():
    assert PARSER.parse_documentation("== Overview ==\nSome prose.\n") == {}


def test_load_and_parse_all_codes_reads_a_local_file(tmp_path):
    # populate_temporary_directory returns a file path, and a path given to
    # the parser is used as-is, so nothing is downloaded.
    source = tmp_path / "reprap-gcode-wiki-source.txt"
    source.write_bytes(SOURCE.encode())
    assert "G4" in PARSER.load_and_parse_all_codes(str(source))

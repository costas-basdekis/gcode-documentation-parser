import bs4
import pytest

from gcode_documentation_parser.parser.parsers.klipper import (
    KlipperGcodeDocumentationParser,
)


PARSER = KlipperGcodeDocumentationParser()
URL = KlipperGcodeDocumentationParser.URL

# Mirrors the structure of klipper3d.org/G-Codes.html: standard codes as a
# list under an <h2>, extended commands as <h4> headings under an <h3>
# config section.
DOCUMENT = """
<h2 id="g-code-commands">G-Code commands<a class="headerlink">&para;</a></h2>
<ul>
<li>Dwell: <code>G4 P&lt;milliseconds&gt;</code></li>
<li><code>G10</code>: Retracts the extruder.</li>
<li>Not a gcode: <code>max_velocity</code></li>
<li>Turn off motors: <code>M18</code> or <code>M84</code></li>
<li>Force relative distances: <code>M83</code>, <code>M82</code><ul>
<li>Note: <code>M83</code> forces relative coordinates.</li></ul></li>
</ul>
<h3 id="virtual_sdcard">[virtual_sdcard]</h3>
<ul><li>List SD card: <code>M20</code></li></ul>
<h2 id="additional-commands">Additional Commands</h2>
<h3 id="bed_mesh">[bed_mesh]<a class="headerlink">&para;</a></h3>
<h4 id="bed_mesh_output">BED_MESH_OUTPUT<a class="headerlink">&para;</a></h4>
<p><code>BED_MESH_OUTPUT PGP=[&lt;0:1&gt;]</code>: This command outputs the mesh.</p>
<h4 id="save_config">SAVE_CONFIG</h4>
<p><code>SAVE_CONFIG</code>: Overwrites the config.</p>
"""


def parse(html):
    return PARSER.get_all_codes(bs4.BeautifulSoup(html, "html.parser"))


def test_both_sections_are_parsed():
    assert set(parse(DOCUMENT)) == {
        "G4", "G10", "M18", "M84", "M82", "M83", "M20",
        "BED_MESH_OUTPUT", "SAVE_CONFIG"}


def test_one_item_can_document_several_commands():
    # eg `Turn off motors: <code>M18</code> or <code>M84</code>`
    codes = parse(DOCUMENT)
    assert codes["M18"][0]["title"] == "Turn off motors"
    assert codes["M84"][0]["title"] == "Turn off motors"
    assert codes["M84"][0]["codes"] == ["M84"]


def test_a_nested_note_is_not_a_command_of_its_own():
    # The "Note:" sub-bullet mentions M83 again; it must not add an entry.
    assert len(parse(DOCUMENT)["M83"]) == 1


def test_entries_have_the_expected_shape():
    entry = parse(DOCUMENT)["G4"][0]
    assert set(entry) == {
        "title", "brief", "codes", "related", "parameters", "source", "url"}
    assert entry["title"] == "Dwell"
    assert entry["codes"] == ["G4"]
    assert entry["source"] == "Klipper"


def test_description_after_the_code_becomes_the_brief():
    # Some entries are written as `<li><code>G10</code>: Retracts...</li>`.
    assert parse(DOCUMENT)["G10"][0]["brief"] == "Retracts the extruder."


def test_brief_keeps_a_colon_that_is_part_of_the_syntax():
    # `PGP=[<0:1>]` contains a colon, which is not the description separator.
    assert parse(DOCUMENT)["BED_MESH_OUTPUT"][0]["brief"] == (
        "This command outputs the mesh.")


def test_urls_point_at_the_closest_section():
    codes = parse(DOCUMENT)
    assert codes["G4"][0]["url"] == f"{URL}#g-code-commands"
    assert codes["M20"][0]["url"] == f"{URL}#virtual_sdcard"
    assert codes["BED_MESH_OUTPUT"][0]["url"] == f"{URL}#bed_mesh_output"


def test_extended_commands_are_titled_by_their_config_section():
    assert parse(DOCUMENT)["BED_MESH_OUTPUT"][0]["title"] == "[bed_mesh]"


def test_extended_command_title_falls_back_to_its_heading():
    html = """
    <h2 id="additional-commands">Additional Commands</h2>
    <h4 id="save_config">SAVE_CONFIG</h4>
    <p><code>SAVE_CONFIG</code>: Overwrites the config.</p>
    """
    assert parse(html)["SAVE_CONFIG"][0]["title"] == "SAVE_CONFIG"


@pytest.mark.parametrize("token, tag, label", [
    ("[X<Xpos>]", "X", "[X<Xpos>]"),
    ("P<Pmilliseconds>", "P", "P<Pmilliseconds>"),
    ("M84", "M84", "M84"),
])
def test_parse_reprap_parameter(token, tag, label):
    parameter = PARSER.parse_reprap_parameter(token)
    assert (parameter["tag"], parameter["label"]) == (tag, label)


@pytest.mark.parametrize("token, tag, label", [
    ("METHOD=manual", "METHOD", "METHOD=manual"),
    ("[PROFILE=<name>]", "PROFILE", "[PROFILE=<name>]"),
    ("<probe_parameter>=<value>", "probe_parameter",
     "<probe_parameter>=<value>"),
])
def test_parse_klipper_parameter(token, tag, label):
    parameter = PARSER.parse_klipper_parameter(token)
    assert (parameter["tag"], parameter["label"]) == (tag, label)


@pytest.mark.parametrize("token, optional, label", [
    # Only brackets around the whole token mark the parameter optional.
    ("[PROFILE=<name>]", True, "[PROFILE=<name>]"),
    ("PGP=[<0:1>]", False, "PGP=[<0:1>]"),
    ("ENABLE=[0|1]", False, "ENABLE=[0|1]"),
    ("[MODE=[PRIMARY|COPY]]", True, "[MODE=[PRIMARY|COPY]]"),
    # The docs group parameters across whitespace, as in
    # `[MOVE=1 [MOVE_SPEED=<speed>]]`, leaving a stray bracket per token.
    ("[MOVE=1", True, "[MOVE=1"),
    ("[MOVE_SPEED=<speed>]]", True, "[MOVE_SPEED=<speed>]]"),
    # ...and occasionally omit the space between two of them.
    ("[A=<x>][B=<y>]", True, "[A=<x>][B=<y>]"),
])
def test_klipper_parameter_brackets(token, optional, label):
    parameter = PARSER.parse_klipper_parameter(token)
    assert (parameter["optional"], parameter["label"]) == (optional, label)


@pytest.mark.parametrize("html", [
    "<p>No headings at all</p>",
    '<h2 id="additional-commands">A</h2><h4 id="x">FOO</h4>',
    '<h2 id="additional-commands">A</h2><h4 id="x">FOO</h4><p>No code.</p>',
])
def test_malformed_markup_is_skipped(html):
    assert parse(html) == {}


def test_a_code_in_both_sections_keeps_both_entries():
    html = """
    <h2 id="g-code-commands">G-Code commands</h2>
    <ul><li>Set temperature: <code>M104 S&lt;temp&gt;</code></li></ul>
    <h2 id="additional-commands">Additional Commands</h2>
    <h4 id="m104">M104</h4>
    <p><code>M104 S&lt;temp&gt;</code>: Also documented here.</p>
    """
    assert len(parse(html)["M104"]) == 2


def test_load_and_parse_all_codes_reads_a_local_file(tmp_path):
    # A directory given to the parser is used as-is, so nothing is downloaded.
    tmp_path.joinpath("g-codes.html").write_text(DOCUMENT, encoding="utf8")
    assert "G4" in PARSER.load_and_parse_all_codes(str(tmp_path))

import re
from pathlib import Path

import bs4
import six.moves.urllib.request

from ..base_parser import BaseDocumentationParser
from ..parser_registry import ParserRegistry


__all__ = ['KlipperGcodeDocumentationParser']


@ParserRegistry.register_parser
class KlipperGcodeDocumentationParser(BaseDocumentationParser):
    """Klipper documentation parser"""

    ID = "klipper"
    SOURCE = "Klipper"
    URL = "https://www.klipper3d.org/G-Codes.html"
    SOURCE_URL = URL
    re_reprap = re.compile(r"^([GM]\d+)(?:\s(.*))?$")
    re_klipper = re.compile(r"^([A-Z][A-Z_0-9]+)(?:\s(.*))?$")

    def load_and_parse_all_codes(self, directory):
        with self.latest_documentation_directory(directory) as directory:
            document = bs4.BeautifulSoup(
                Path(directory).joinpath("g-codes.html").read_text('utf8'),
                "html.parser")
        return self.get_all_codes(document)

    def populate_temporary_directory(self, directory):
        html_filename = str(Path(directory).joinpath("g-codes.html"))
        six.moves.urllib.request.urlretrieve(self.SOURCE_URL, html_filename)

    def get_all_codes(self, document):
        """Get all the GCodes from the document"""
        result = {}
        for codes in (self._parse_standard_gcodes(document),
                      self._parse_extended_commands(document)):
            for code, entries in codes.items():
                result.setdefault(code, []).extend(entries)
        return result

    # -- Standard G-Code section (ul > li > code) ----------------------------

    def _parse_standard_gcodes(self, document):
        h2 = document.find('h2', id='g-code-commands')
        if not h2:
            return {}
        codes = {}
        for li in h2.find_all_next('li'):
            # A nested list holds a note about the command it sits under,
            # rather than a command of its own.
            if li.find_parent('li'):
                continue
            # One item can document several commands, as in
            # `Turn off motors: <code>M18</code> or <code>M84</code>`.
            for code_tag in li.find_all('code', recursive=False):
                code_text = " ".join(code_tag.get_text().split())
                parsed = self._try_parse_standard_code(code_text, li)
                if parsed:
                    key, entry = parsed
                    codes.setdefault(key, []).extend(entry)
        return codes

    def _try_parse_standard_code(self, code_text, li):
        m = self.re_reprap.match(code_text)
        if m:
            code, params = m.groups()
            return (code, [{
                "title": self._li_preceding_text(li),
                "brief": self._li_trailing_text(li),
                "codes": [code],
                "related": [],
                "parameters": self.parse_reprap_parameters(params),
                "source": self.SOURCE,
                "url": f"{self.URL}#{self._nearest_section_anchor(li)}",
            }])
        return None

    def _li_preceding_text(self, li):
        """Text before the first <code> tag in the li."""
        parts = []
        for child in li.children:
            if hasattr(child, 'name') and child.name == 'code':
                break
            if isinstance(child, str):
                parts.append(child)
        return "".join(parts).strip().strip(':').strip()

    def _li_trailing_text(self, li):
        """
        Text after the first <code> tag in the li.

        Some entries are written the other way around, with the description
        following the code (eg `<li><code>G10</code>: Retracts...</li>`).
        """
        if self._li_preceding_text(li):
            return ""
        first_code = li.find('code')
        if not first_code:
            return ""
        parts = [
            sibling if isinstance(sibling, str) else sibling.get_text()
            for sibling in first_code.next_siblings
        ]
        text = "".join(parts).replace('\n', ' ').strip()
        return " ".join(text.lstrip(':').split())

    def _nearest_section_anchor(self, element):
        """
        The id of the closest heading above the element.

        Commands documented under a config section (eg `[virtual_sdcard]`)
        should link to that section rather than to the generic one.
        """
        heading = element.find_previous(
            lambda tag: tag.name in ('h2', 'h3', 'h4') and tag.get('id'))
        if not heading:
            return ""
        return heading.get('id')

    # -- Extended commands section (h4 headings) ------------------------------

    def _parse_extended_commands(self, document):
        h2 = document.find('h2', id='additional-commands')
        if not h2:
            return {}
        codes = {}
        # Collect all h3 groups so we know the section title for each h4
        current_section = ""
        for tag in h2.find_all_next(['h2', 'h3', 'h4']):
            if tag.name == 'h2':
                break
            if tag.name == 'h3':
                current_section = self._heading_text(tag)
                continue
            # h4 — actual command
            parsed = self._parse_h4_command(tag, current_section)
            if parsed:
                key, entry = parsed
                codes.setdefault(key, []).extend(entry)
        return codes

    def _heading_text(self, tag):
        """Heading text without the pilcrow link."""
        return tag.find(string=True, recursive=False) or tag.get_text().strip()

    def _brief_from_paragraph(self, p, syntax):
        """
        Extract the description following the syntax in a paragraph.

        The syntax itself may contain a colon (eg `PGP=[<0:1>]`), so only the
        text after it is searched for the separator.
        """
        text = " ".join(p.get_text().split())
        remainder = text[len(" ".join(syntax.split())):]
        return remainder.lstrip().lstrip(':').strip() or text

    def _match_syntax(self, syntax, heading_text):
        """Return (match, params_text) for a syntax string, falling back to heading."""
        m = self.re_reprap.match(syntax) or self.re_klipper.match(syntax)
        if m:
            return m, m.group(2)
        m = self.re_reprap.match(heading_text) or self.re_klipper.match(heading_text)
        return m, None

    def _parse_h4_command(self, h4, section_title):
        """Parse a single h4 command block."""
        heading_text = self._heading_text(h4).strip()
        anchor = h4.get('id', '')

        p = h4.find_next_sibling('p')
        if not p:
            return None
        first_code = p.find('code')
        if not first_code:
            return None

        syntax = first_code.get_text().replace('\n', ' ').strip()
        m, params_text = self._match_syntax(syntax, heading_text)
        if not m:
            return None

        code = m.group(1)
        if self.re_reprap.match(syntax):
            parameters = self.parse_reprap_parameters(params_text)
        else:
            parameters = self.parse_klipper_parameters(params_text)

        title = section_title if section_title else heading_text
        return (code, [{
            "title": title,
            "brief": self._brief_from_paragraph(p, syntax),
            "codes": [code],
            "related": [],
            "parameters": parameters,
            "source": self.SOURCE,
            "url": f"{self.URL}#{anchor}",
        }])

    # -- Parameter parsers (unchanged) ----------------------------------------

    def parse_reprap_parameters(self, parameters_text):
        """Parse RepRap-style space-separated parameters from a syntax string."""
        if not parameters_text:
            return []
        parameter_texts = map(str.strip, parameters_text.split(" "))
        return list(filter(None, map(
            self.parse_reprap_parameter, parameter_texts)))

    def split_parameter_token(self, parameter_text):
        """
        Split a syntax token into its label, whether the parameter is
        optional, and whether a bracket pair wrapped the whole token.

        Only a bracket pair wrapping the whole token marks the parameter as
        optional; brackets inside it belong to the value (eg `ENABLE=[0|1]`).
        The documentation also groups several tokens in a single pair (eg
        `[MOVE=1 [MOVE_SPEED=<speed>]]`), which leaves a stray bracket behind
        once the syntax is split on whitespace.
        """
        if parameter_text.count('[') != parameter_text.count(']'):
            return parameter_text, True, False
        if not (parameter_text.startswith('[')
                and parameter_text.endswith(']')):
            return parameter_text, False, False
        if self._closes_at_end(parameter_text):
            return parameter_text[1:-1], True, True
        # Several bracketed parameters run together, as the documentation
        # occasionally omits the space between them.
        return parameter_text, True, False

    def _closes_at_end(self, parameter_text):
        """Whether the opening bracket is closed only by the last one."""
        depth = 0
        for index, character in enumerate(parameter_text):
            if character == '[':
                depth += 1
            elif character == ']':
                depth -= 1
                if depth == 0:
                    return index == len(parameter_text) - 1
        return False

    def parse_reprap_parameter(self, parameter_text):
        """Parse a single RepRap parameter token into a parameter dict."""
        if not parameter_text:
            return None
        label, optional, wrapped = self.split_parameter_token(parameter_text)
        if label.startswith('<'):
            tag = label.strip('<>')
        elif '<' in label:
            tag = label[:label.index('<')]
        else:
            tag = label
        if wrapped:
            label = f"[{label}]"
        return {
            "tag": tag,
            "optional": optional,
            "description": "",
            "values": [],
            "label": label,
        }

    def parse_klipper_parameters(self, parameters_text):
        """Parse Klipper-style space-separated parameters from a syntax string."""
        if not parameters_text:
            return []
        parameter_texts = map(str.strip, parameters_text.split(" "))
        return list(filter(None, map(
            self.parse_klipper_parameter, parameter_texts)))

    def parse_klipper_parameter(self, parameter_text):
        """Parse a single Klipper parameter token into a parameter dict."""
        if not parameter_text:
            return None
        label, optional, wrapped = self.split_parameter_token(parameter_text)
        # `NAME=<value>` names the parameter before the '=', while a bare
        # `<value>` is a placeholder named by the documentation itself.
        tag = label.split('=')[0].strip('<>[]')
        if wrapped:
            label = f"[{label}]"
        return {
            "tag": tag,
            "optional": optional,
            "description": "",
            "values": [],
            "label": label,
        }

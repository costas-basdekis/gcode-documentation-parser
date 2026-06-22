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
        result.update(self._parse_standard_gcodes(document))
        result.update(self._parse_extended_commands(document))
        return result

    # -- Standard G-Code section (ul > li > code) ----------------------------

    def _parse_standard_gcodes(self, document):
        h2 = document.find('h2', id='g-code-commands')
        if not h2:
            return {}
        codes = {}
        for li in h2.find_all_next('li'):
            parent_h2 = li.find_parent('h2')
            if parent_h2 and parent_h2.get('id') == 'additional-commands':
                break
            first_code = li.find('code')
            if not first_code:
                continue
            code_text = first_code.get_text().replace('\n', ' ').strip()
            parsed = self._try_parse_standard_code(code_text, li)
            if parsed:
                key, entry = parsed
                codes.setdefault(key, []).extend(entry)
        return codes

    def _try_parse_standard_code(self, code_text, li):
        m = self.re_reprap.match(code_text)
        if m:
            code, params = m.groups()
            title = self._li_preceding_text(li)
            return (code, [{
                "title": title,
                "brief": "",
                "codes": [code],
                "related": [],
                "parameters": self.parse_reprap_parameters(params),
                "source": self.SOURCE,
                "url": f"{self.URL}#g-code-commands",
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

    def _brief_from_paragraph(self, p):
        """Extract description text after the colon in a paragraph."""
        text = p.get_text().replace('\n', ' ').strip()
        colon_idx = text.find(':')
        return text[colon_idx + 1:].strip() if colon_idx != -1 else text

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
            "brief": self._brief_from_paragraph(p),
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

    def parse_reprap_parameter(self, parameter_text):
        """Parse a single RepRap parameter token into a parameter dict."""
        if not parameter_text:
            return None
        optional = (
            parameter_text.startswith('[')
            or parameter_text.endswith(']')
        )
        parameter_text = parameter_text.replace('[', '').replace(']', '')
        if parameter_text.startswith('<'):
            parameter_text = parameter_text.replace('<', '').replace('>', '')
            tag = parameter_text
            label = f"<{parameter_text}>"
        elif '<' in parameter_text:
            tag = parameter_text[:parameter_text.index('<')]
            parameter_text = parameter_text.replace('<', '').replace('>', '')
            label = f"{tag}<{parameter_text}>"
        else:
            tag = parameter_text
            label = parameter_text
        if optional:
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
        optional = (
            parameter_text.startswith('[')
            or parameter_text.endswith(']')
        )
        parameter_text = parameter_text.replace('[', '').replace(']', '')
        label = parameter_text
        if parameter_text.startswith('<'):
            parameter_text = parameter_text.replace('<', '').replace('>', '')
            tag = parameter_text
        elif '<' in parameter_text:
            tag = parameter_text[:parameter_text.index('<')].replace('=', '')
        else:
            tag = parameter_text.replace('=', '')
        return {
            "tag": tag,
            "optional": optional,
            "description": "",
            "values": [],
            "label": label,
        }

    def find_previous_id(self, element):
        """Get the first ID from a previous sibling"""
        id_element = next((
            id_element
            for id_element in filter(None, (
                sibling
                for parent in reversed(element.find_parents())
                for sibling in parent.find_previous_siblings(None, {'id': True})
            ))
            if id_element.name != "input"
        ), None)
        if not id_element:
            return ''

        return id_element.attrs['id']

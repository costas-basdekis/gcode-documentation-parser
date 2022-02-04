gcode-documentation-parser
==

See a [demo] usage of the output

A utility that parses the documentation pages from Marlin, RepRap, and Klipper,
to generate an index of commands usage.

Output
--

You can access the output from the [output branch] of this repo. Here are the
raw links that you can reference or copy:

* [all_codes.json]: A JSON file containing the documentation
* [all_codes_window.js]: A JS file that defines `AllGcodes` on the global
* `window` object
* [all_codes_const.js]: A JS file that defines a `const AllGcodes`
* [all_codes_export.js]: A JS file that exports an `AllGcodes` value

The documentation is updated semi-regularly, at the start of every month, and
published on this repo.

You can also generate it locally by running the following, and checking the
`output` folder

```shell
poetry run ./update_documentation.py
```

Usage
--

Normally, the output would be used by something like [gcode-documentation], to
allow users to search and understand how a GCode command should be used.

This was originally created in [Octoprint] plugin [MarlinGcodeDocumentation],
and needs the parsed documentation data to function.

[demo]:https://costas-basdekis.github.io/gcode-documentation
[output branch]:https://github.com/costas-basdekis/gcode-documentation-parser/tree/output
[all_codes.json]:https://raw.githubusercontent.com/costas-basdekis/gcode-documentation-parser/output/output/all_codes.json
[all_codes_window.js]:https://raw.githubusercontent.com/costas-basdekis/gcode-documentation-parser/output/output/all_codes_window.js
[all_codes_const.js]:https://raw.githubusercontent.com/costas-basdekis/gcode-documentation-parser/output/output/all_codes_const.js
[all_codes_export.js]:https://raw.githubusercontent.com/costas-basdekis/gcode-documentation-parser/output/output/all_codes_export.js
[gcode-documentation]:https://github.com/costas-basdekis/gcode-documentation
[Octoprint]:https://octoprint.org/
[MarlinGcodeDocumentation]:https://plugins.octoprint.org/plugins/marlingcodedocumentation/

![](docs/marlin-gcode-documentation.png)

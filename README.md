# Tacit symbols

Tacit's own symbol set, drawn in code and built into two fonts the shell loads in place of Material Symbols.

    symbols.py     the symbols (line forms, filled forms), drawn on a 24 grid      -> build/<palette>/*.svg, *.png
    aliases.py     Material Symbols names the shell uses -> Tacit's symbol
    fontbuild.py   -> build/fonts/TacitSymbols.ttf, TacitSymbolsFill.ttf, tacit_symbols.js
    sheet.py       review sheet: control panel, notification, notch player      -> build/sheet.png
    kit.py         geometry (solids, set operations, cast = eased corners + coves)
    inventory.json the Material names found in the shell, with counts

Run with the font project's venv (`~/dev/tacit-font/.venv/bin/python`). `sketch*.py` are the earlier directions.

The language: one line as heavy as Tacit Sans beside it (2.0 on the grid), crisp ends, round free corners,
a cove where lines meet, one solid dot where a symbol needs its point; line at rest, filled when on or
selected, solid for the player's transport; one colour, taken from the text or accent colour.

In the shell: `services/Fonts.qml` loads both fonts and answers `symbolFamily(name, filled)`;
`MaterialSymbol.qml` asks it. A name the fonts do not cover keeps Material's glyph.

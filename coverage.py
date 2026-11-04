"""Which Material Symbols names Tacit's QML uses that Tacit Symbols does not draw yet (2026-10-15).

Material's names come from its font's ligatures; the uses are string literals in the shell's and Thyris's QML and JS
that are such a name. Writes coverage.json (name -> uses, places) and prints the missing names, most used first.
    ~/dev/tacit-font/.venv/bin/python coverage.py [folder ...]
"""
import json
import os
import re
import sys

from fontTools.ttLib import TTFont

MATERIAL = "/usr/share/fonts/book4/MaterialSymbolsRounded[FILL,GRAD,opsz,wght].ttf"
SYMBOL_PLACE = re.compile(r"Symbol\s*\{|[Ii]con|[Gg]lyph|[Ss]ymbol")
FOLDERS = sys.argv[1:] or [os.path.expanduser("~/.config/quickshell/tacit"), os.path.expanduser("~/dev/browser/qml")]


def material_names():
    font = TTFont(MATERIAL, lazy=True)
    chars = {g: chr(c) for c, g in font.getBestCmap().items()}
    names = set()
    for lookup in font["GSUB"].table.LookupList.Lookup:
        for sub in lookup.SubTable:
            sub = getattr(sub, "ExtSubTable", sub)
            for first, ligatures in getattr(sub, "ligatures", {}).items():
                for lig in ligatures:
                    text = "".join(chars.get(g, "?") for g in [first] + lig.Component)
                    if "?" not in text:
                        names.add(text)
    return names


def tacit_names():
    text = open(os.path.join(os.path.dirname(__file__), "build/fonts/tacit_symbols.js")).read()
    return set(json.loads(re.search(r"var names = (\{.*?\});", text, re.S).group(1)))


def uses(names):
    found = {}
    literal = re.compile(r"""["']([a-z0-9_]{2,40})["']""")
    for folder in FOLDERS:
        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if d not in (".git", "build", "node_modules", "assets")]
            for f in files:
                if not f.endswith((".qml", ".js")) or f == "tacit_symbols.js":
                    continue
                path = os.path.join(root, f)
                lines = open(path, errors="replace").read().split("\n")
                for i, line in enumerate(lines):
                    # a symbol's place: a Symbol / MaterialSymbol element's text, or a property or key named for an icon,
                    # glyph or symbol, on the line or the three before it
                    near = "\n".join(lines[max(0, i - 3):i + 1])
                    if not SYMBOL_PLACE.search(near):
                        continue
                    for m in literal.finditer(line):
                        if m.group(1) not in names:
                            continue
                        e = found.setdefault(m.group(1), {"count": 0, "where": set()})
                        e["count"] += 1
                        e["where"].add(os.path.relpath(path, folder).split("/")[0].replace(".qml", ""))
    return found


if __name__ == "__main__":
    material, tacit = material_names(), tacit_names()
    found = uses(material)
    # plain words that are also symbol names but rarely symbols in this code
    missing = sorted((n for n in found if n not in tacit), key=lambda n: -found[n]["count"])
    total = sum(e["count"] for e in found.values())
    covered = sum(e["count"] for n, e in found.items() if n in tacit)
    print(f"Material names in use: {len(found)} ({total} uses); Tacit draws {len(found) - len(missing)} of them "
          f"({100 * covered / total:.0f} % of uses); missing {len(missing)}")
    json.dump({n: {"count": e["count"], "where": sorted(e["where"]), "tacit": n in tacit} for n, e in found.items()},
              open("coverage.json", "w"), indent=1, sort_keys=True)
    for n in missing:
        print(f"{found[n]['count']:4d}  {n:32s} {', '.join(sorted(found[n]['where']))[:90]}")

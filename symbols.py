"""Tacit's symbols (the direction approved 2026-10-01, sketch 8, polished).

- one line, as heavy as Tacit Sans beside it: 2.0 on the 24 grid = the stem of Tacit Sans 450 at 15 px next to a
  20 px symbol (measured: stem 0.113 em)
- lines that meet are docked with a cove (JOINT), as bars meet stems in Tacit Sans and as the notch meets the screen
- a part that grows out of a body (the folder's tab, the camera's hump, the screen's notch) leaves it with the
  notch's profile: a cove, then a round shoulder
- stroke ends are crisp; free corners are round (boxes 2.8); one colour; one small solid dot where a symbol needs
  its point; a selected symbol takes the accent. Colours are roles of the generated palette, never fixed.

    symbols.py -> build/<palette>/*.svg (+ png), build/index.json          (run with the font project's venv)
"""
import json
import math
import os

from fontTools.svgLib.path import parse_path
from pathops import LineCap, LineJoin, Path

from kit import cast, d, disc, line, minus, poly, rect, union, _clean
from sketch4 import generated, live, write
from sketch7 import C, R

JOINT = 0.9      # the cove where one line docks into another
WIFI = 40        # half the wifi fan's angle

S = 2.0


K = 40           # shapes are built 40 times larger: the stroker is coarse at the size of the grid


def stroke(data, w=S):
    p = Path()
    parse_path(data, p.getPen())
    p = p.transform(K, 0, 0, K)
    p.stroke(w * K, LineCap.BUTT_CAP, LineJoin.ROUND_JOIN, 4)
    return _clean(p)


def sym(*groups, solids=()):
    """groups: (path data, cove) pairs, each cast on its own; solids are added as drawn."""
    parts = [cast(stroke(data), 0.15 * K, cove * K) for data, cove in groups]
    parts += [s.transform(K, 0, 0, K) for s in solids]
    return union(*parts).transform(1 / K, 0, 0, 1 / K)


def _arc(cx, cy, r, half):
    s, c = math.sin(math.radians(half)), math.cos(math.radians(half))
    return f"M{cx - r * s:.2f} {cy - r * c:.2f} A{r} {r} 0 0 1 {cx + r * s:.2f} {cy - r * c:.2f}"


def off(shape):
    """The symbol struck through: a bar from upper left to lower right, with a clear gap round it."""
    bar = "M4.4 4.4 L19.6 19.6"
    out = Path()                      # the two do not overlap; a union here loses parts of the cut symbol
    for contour in minus(shape.transform(K, 0, 0, K), stroke(bar, S + 2.6)).contours:
        if abs(contour.area) > 0.05 * K * K:          # the cut leaves hairline slivers along its edge
            out.addPath(contour)
    out.addPath(stroke(bar, S))
    return out.transform(1 / K, 0, 0, 1 / K)


# Symbols whose ink sat off the centre of the box, moved onto it (grid units, y down).
NUDGE = {"awake": (-0.3, -0.9), "speed": (0, 1.4), "layers": (0, 1.2), "thermo": (0, -0.8), "undo": (0, -0.8),
         "bell": (0, -0.5), "bell-ring": (0, -0.5), "bell-off": (0, -0.5), "mic": (0, 0.4), "mic-off": (0, 0.4), "calendar": (0, -0.4), "paste": (0, -0.4),
         "wifi": (0, -0.6), "wifi-2": (0, -0.6), "wifi-1": (0, -0.6), "wifi-0": (0, -0.6), "wifi-off": (0, -0.6), "find-page": (-1.1, 0)}


def _nudged(table):
    move = lambda shape, d: shape.transform(1, 0, 0, 1, d[0], d[1])
    for name, d in NUDGE.items():
        if table.get(name) is not None:
            v = table[name]
            table[name] = tuple(move(part, d) for part in v) if isinstance(v, tuple) else move(v, d)
    return table


def cast_u(shape, ease):
    """kit.cast at the working scale, for a solid drawn on the grid."""
    return cast(shape.transform(K, 0, 0, K), ease * K, 0).transform(1 / K, 0, 0, 1 / K)


def solid(body, cut="", holes=(), extra=(), cove=0.0):
    """The filled form of a symbol, for one that is on or selected: the body's outline filled in, its details
    cut out of it (cut: lines, holes: solids), anything in extra added as drawn."""
    p = Path()
    parse_path(body, p.getPen())
    p = _clean(p.transform(K, 0, 0, K))
    out = cast(union(p, stroke(body)), 0.15 * K, cove * K)
    if cut:
        out = minus(out, stroke(cut, 1.9))
    for h in holes:
        out = minus(out, h.transform(K, 0, 0, K))
    parts = [out] + [e.transform(K, 0, 0, K) if not isinstance(e, tuple) else cast(stroke(e[0]), 0.15 * K, e[1] * K) for e in extra]
    whole = Path()
    for part in parts:
        whole.addPath(part)
    return whole.transform(1 / K, 0, 0, 1 / K)


def filled():
    """Filled forms, used when a symbol is on or selected. A symbol without one keeps its line and takes the accent."""
    BELL = "M5.8 17 C6.8 15.4 7 14 7 12 V9.4 A5 5 0 0 1 17 9.4 V12 C17 14 17.2 15.4 18.2 17 M3.8 17 H20.2"
    MOON = "M19.6 14.6 A8.4 8.4 0 1 1 9.4 4.4 A6.6 6.6 0 0 0 19.6 14.6 Z"
    SPEAKER = "M3.6 9.8 H6.4 C9 9.8 11 8 12.4 5.4 V18.6 C11 16 9 14.2 6.4 14.2 H3.6 Z"
    return _nudged({
        "bell": solid(BELL, extra=[disc(12, 20.6, 1.4)], cove=JOINT),
        "bell-ring": solid(BELL, extra=[disc(12, 20.6, 1.4), ("M4.4 8.8 A8.4 8.4 0 0 1 6.4 4.8 M19.6 8.8 A8.4 8.4 0 0 0 17.6 4.8", 0)], cove=JOINT),
        "moon": solid(MOON),
        "night": solid(MOON, extra=[disc(17.6, 6.4, 1.5)]),
        "mic": solid(R(9, 3, 15, 13.4, 3), extra=[("M5.6 10.8 A6.4 6.4 0 0 0 18.4 10.8 M12 17.2 V21", JOINT)]),
        "awake": solid("M4.6 6.6 H16.4 V12.6 A5.4 5.4 0 0 1 11 18 H10 A5.4 5.4 0 0 1 4.6 12.6 Z", extra=[("M16.4 8.4 H17.6 A2.8 2.8 0 0 1 17.6 14 H16.2", 0), ("M4 21 H17", 0)]),
        "volume": solid(SPEAKER, extra=[("M15.2 8.8 A4.6 4.6 0 0 1 15.2 15.2 M17.9 6 A8.4 8.4 0 0 1 17.9 18", 0)]),
        "keyboard": solid(R(2.5, 6, 21.5, 18, 2.8), cut="M8.4 14.6 H15.6", holes=[disc(6.6, 10.2, 1.1), disc(10.2, 10.2, 1.1), disc(13.8, 10.2, 1.1), disc(17.4, 10.2, 1.1)]),
        "image": solid(R(3, 5, 21, 19, 2.8), cut="M3 15.6 C6.6 15.6 8.4 11.6 12 13.2 C15 14.6 17 16.4 21 13.4", holes=[disc(15.4, 9.2, 1.6)]),
        "video": solid(R(3, 5.5, 21, 18.5, 2.8), holes=[cast_u(poly((10, 8.6), (15.6, 12), (10, 15.4)), 0.7)]),
        "folder": solid("M3 16.8 V7 A2.2 2.2 0 0 1 5.2 4.8 H7.8 A2 2 0 0 1 9.8 6.8 A1.6 1.6 0 0 0 11.4 8.4 H18.2 A2.8 2.8 0 0 1 21 11.2 V16.8 A2.8 2.8 0 0 1 18.2 19.6 H5.8 A2.8 2.8 0 0 1 3 16.8 Z"),
        "file": solid(R(5.5, 3, 18.5, 21, 2.8), cut="M8.8 10.6 H15.2 M8.8 14.6 H12.4"),
        "clock": solid(C(12, 12, 8.6), cut="M12 6.8 V12 L15.6 14.1"),
        "home": solid("M4 10.8 L12 3.8 L20 10.8 V17.6 A2.8 2.8 0 0 1 17.2 20.4 H6.8 A2.8 2.8 0 0 1 4 17.6 Z", cut="M12 21.6 V15.6"),
        "lock": solid(R(5, 10.8, 19, 20.8, 2.8), holes=[disc(12, 15.8, 1.6)], extra=[("M8.2 10.8 V7.6 A3.8 3.8 0 0 1 15.8 7.6 V10.8", 0)]),
        "desktop": solid(R(3, 4, 21, 15.6, 2.8), extra=[("M12 15.6 V20 M8 20 H16", JOINT)]),
        "download": None,
        "trash": solid("M6.4 7 L7.3 17.8 A2.8 2.8 0 0 0 10.1 20.6 H13.9 A2.8 2.8 0 0 0 16.7 17.8 L17.6 7 Z", extra=[("M3.8 7 H20.2", 0), ("M9.8 3.4 H14.2", 0)]),
        "camera": solid("M5.8 7.8 H7 A1.4 1.4 0 0 0 8.4 6.4 A1.6 1.6 0 0 1 10 4.8 H14 A1.6 1.6 0 0 1 15.6 6.4 A1.4 1.4 0 0 0 17 7.8 H18.2 A2.8 2.8 0 0 1 21 10.6 "
                        "V16.4 A2.8 2.8 0 0 1 18.2 19.2 H5.8 A2.8 2.8 0 0 1 3 16.4 V10.6 A2.8 2.8 0 0 1 5.8 7.8 Z", holes=[disc(12, 13.4, 3.4)], extra=[disc(12, 13.4, 1.7)]),
        "calendar": solid(R(3.5, 4.5, 20.5, 20.5, 2.8), cut="M3 9.8 H21", holes=[disc(15.6, 15.4, 1.5)]),
        "user": solid(C(12, 7.8, 3.6), extra=[solid("M5 20.6 A7 5.6 0 0 1 19 20.6 Z")]),
        "eye": solid("M2.8 12 C6 7.4 9 6 12 6 C15 6 18 7.4 21.2 12 C18 16.6 15 18 12 18 C9 18 6 16.6 2.8 12 Z", holes=[disc(12, 12, 3.6)], extra=[disc(12, 12, 1.9)]),
        "terminal": solid(R(3, 5, 21, 19, 2.8), cut="M7 9.4 L10 12 L7 14.6 M12.4 14.8 H16.8"),
        "timer": solid(C(12, 13.6, 7.4), cut="M12 13.6 V9.2", extra=[("M9.8 3.2 H14.2", 0)]),
        "check-circle": solid(C(12, 12, 8.6), cut="M8 12.4 L11 15.2 L16 9.4"),
        "record": solid(C(12, 12, 8.6), holes=[disc(12, 12, 5.4)], extra=[disc(12, 12, 3.4)]),
        "battery": solid(R(2, 7, 18.6, 17, 2.8), extra=[("M21.4 10.2 V13.8", 0)]),
        "windows": solid(R(3, 9, 16, 20, 2.8), extra=[("M9 9 V7.8 A2.8 2.8 0 0 1 11.8 5 H18.2 A2.8 2.8 0 0 1 21 7.8 V12.2 A2.8 2.8 0 0 1 18.2 15 H16", 0)]),
        "notch": solid("M5.8 5.5 H7.6 A1.2 1.2 0 0 1 8.8 6.7 V7.6 A1.8 1.8 0 0 0 10.6 9.4 H13.4 A1.8 1.8 0 0 0 15.2 7.6 V6.7 A1.2 1.2 0 0 1 16.4 5.5 H18.2 "
                       "A2.8 2.8 0 0 1 21 8.3 V15.7 A2.8 2.8 0 0 1 18.2 18.5 H5.8 A2.8 2.8 0 0 1 3 15.7 V8.3 A2.8 2.8 0 0 1 5.8 5.5 Z"),
    })


def hair(data, w=0.75):
    """A hairline: the part of a level symbol that is not reached."""
    return stroke(data, w).transform(1 / K, 0, 0, 1 / K)


def symbols():
    rays = " ".join(f"M{12 + 6.9 * math.sin(a):.2f} {12 - 6.9 * math.cos(a):.2f} L{12 + 10.2 * math.sin(a):.2f} {12 - 10.2 * math.cos(a):.2f}"
                    for a in (math.radians(k * 45) for k in range(8)))
    # wifi: three arcs over the dot, WIFI degrees to each side (31 was "too slim", 45 is Material's)
    fan = [sym((_arc(12, 19.6, r, WIFI), 0)) for r in (5.6, 10.4, 15.2)]
    ghost = [hair(_arc(12, 19.6, r, WIFI)) for r in (5.6, 10.4, 15.2)]
    WDOT = disc(12, 19.6, 1.8)
    SPEAKER = "M3.6 9.8 H6.4 C9 9.8 11 8 12.4 5.4 V18.6 C11 16 9 14.2 6.4 14.2 H3.6 Z"
    BELL = "M5.8 17 C6.8 15.4 7 14 7 12 V9.4 A5 5 0 0 1 17 9.4 V12 C17 14 17.2 15.4 18.2 17 M3.8 17 H20.2"
    RUNE = "M7 7.8 L16.6 16.2 L12 20.6 V3.4 L16.6 7.8 L7 16.2"
    MIC = (R(9, 3, 15, 13.4, 3), 0), ("M5.6 10.8 A6.4 6.4 0 0 0 18.4 10.8 M12 17.2 V21", JOINT)
    NOTES = dict(solids=[disc(7.8, 17.6, 2.4), disc(16.6, 15.6, 2.4)])
    out = {
        "search": sym((C(10.2, 10.2, 6.2) + " M14.6 14.6 L20.4 20.4", JOINT)),
        "folder": sym(("M3 16.8 V7 A2.2 2.2 0 0 1 5.2 4.8 H7.8 A2 2 0 0 1 9.8 6.8 A1.6 1.6 0 0 0 11.4 8.4 H18.2 A2.8 2.8 0 0 1 21 11.2 V16.8 "
                       "A2.8 2.8 0 0 1 18.2 19.6 H5.8 A2.8 2.8 0 0 1 3 16.8 Z", 0)),
        "file": sym((R(5.5, 3, 18.5, 21, 2.8) + " M8.8 10.6 H15.2 M8.8 14.6 H12.4", 0)),
        "image": sym((R(3, 5, 21, 19, 2.8) + " M3 15.6 C6.6 15.6 8.4 11.6 12 13.2 C15 14.6 17 16.4 21 13.4", 0.7), solids=[disc(15.4, 9.2, 1.5)]),
        "video": sym((R(3, 5.5, 21, 18.5, 2.8), 0), solids=[cast(poly((10, 8.8), (15.4, 12), (10, 15.2)), 0.7, 0)]),
        "music": sym(("M9.2 17.6 V6.6 L18 4.6 V15.6", 0.5), solids=[disc(7.8, 17.6, 2.4), disc(16.6, 15.6, 2.4)]),
        "calendar": sym((R(3.5, 4.5, 20.5, 20.5, 2.8) + " M3.5 9.8 H20.5", JOINT), solids=[disc(15.6, 15.4, 1.4)]),
        "clock": sym((C(12, 12, 8.6), 0), ("M12 6.8 V12 L15.6 14.1", 0), solids=[disc(12, 12, 1.7)]),
        "settings": sym(("M3 8 H6.6 M13.4 8 H21 M3 16 H10.6 M17.4 16 H21", 0), solids=[disc(10, 8, 2), disc(14, 16, 2)]),
        "wifi": union(*fan, WDOT),
        # a level keeps the whole fan: the arcs it does not reach are hairlines, so the symbol stays the same size
        # and sits in the same place at every level (a font has one colour and cannot dim them)
        "wifi-2": union(fan[0], fan[1], WDOT, ghost[2]),
        "wifi-1": union(fan[0], WDOT, ghost[1], ghost[2]),
        "wifi-0": union(WDOT, *ghost),
        "wifi-off": off(union(*fan, WDOT)),
        "bluetooth": sym(("M7 7.8 L16.6 16.2 L12 20.6 V3.4 L16.6 7.8 L7 16.2", 0.3)),
        "battery": sym((R(2, 7, 18.6, 17, 2.8) + " M21.4 10.2 V13.8", 0), solids=[rect(5, 10, 11, 14, 0.8)]),
        "volume": sym(("M3.6 9.8 H6.4 C9 9.8 11 8 12.4 5.4 V18.6 C11 16 9 14.2 6.4 14.2 H3.6 Z", 0), ("M15.2 8.8 A4.6 4.6 0 0 1 15.2 15.2 M17.9 6 A8.4 8.4 0 0 1 17.9 18", 0)),
        "mic": sym((R(9, 3, 15, 13.4, 3), 0), ("M5.6 10.8 A6.4 6.4 0 0 0 18.4 10.8 M12 17.2 V21", JOINT)),
        "brightness": sym((C(12, 12, 3.6) + " " + rays, 0)),
        "moon": sym(("M19.6 14.6 A8.4 8.4 0 1 1 9.4 4.4 A6.6 6.6 0 0 0 19.6 14.6 Z", 0)),
        "bell": sym(("M5.8 17 C6.8 15.4 7 14 7 12 V9.4 A5 5 0 0 1 17 9.4 V12 C17 14 17.2 15.4 18.2 17 M3.8 17 H20.2", JOINT), solids=[disc(12, 20.6, 1.4)]),
        "lock": sym((R(5, 10.8, 19, 20.8, 2.8) + " M8.2 10.8 V7.6 A3.8 3.8 0 0 1 15.8 7.6 V10.8", JOINT), solids=[disc(12, 15.8, 1.4)]),
        "user": sym((C(12, 7.8, 3.6) + " M5 20.6 A7 5.6 0 0 1 19 20.6", 0)),
        "home": sym(("M4 10.8 L12 3.8 L20 10.8 V17.6 A2.8 2.8 0 0 1 17.2 20.4 H6.8 A2.8 2.8 0 0 1 4 17.6 Z M12 20.4 V15.4", 0.6)),
        "terminal": sym((R(3, 5, 21, 19, 2.8), 0), ("M7 9.4 L10 12 L7 14.6 M12.4 14.8 H16.8", 0.3)),
        "eye": sym(("M2.8 12 C6 7.4 9 6 12 6 C15 6 18 7.4 21.2 12 C18 16.6 15 18 12 18 C9 18 6 16.6 2.8 12 Z", 0), solids=[disc(12, 12, 2.4)]),
        "download": sym(("M12 3.4 V14 M7.8 10 L12 14.2 L16.2 10", 0.5), ("M4.6 19.6 H19.4", 0)),
        "trash": sym(("M6.4 7 L7.3 17.8 A2.8 2.8 0 0 0 10.1 20.6 H13.9 A2.8 2.8 0 0 0 16.7 17.8 L17.6 7 M3.8 7 H20.2", JOINT), ("M9.8 3.4 H14.2", 0)),
        "power": sym(("M7.2 7 A7.6 7.6 0 1 0 16.8 7 M12 3.2 V11", 0)),
        "camera": sym(("M5.8 7.8 H7 A1.4 1.4 0 0 0 8.4 6.4 A1.6 1.6 0 0 1 10 4.8 H14 A1.6 1.6 0 0 1 15.6 6.4 A1.4 1.4 0 0 0 17 7.8 H18.2 A2.8 2.8 0 0 1 21 10.6 "
                       "V16.4 A2.8 2.8 0 0 1 18.2 19.2 H5.8 A2.8 2.8 0 0 1 3 16.4 V10.6 A2.8 2.8 0 0 1 5.8 7.8 Z " + C(12, 13.4, 3), 0)),
        "desktop": sym((R(3, 4, 21, 15.6, 2.8) + " M12 15.6 V20 M8 20 H16", JOINT)),
        "notch": sym(("M5.8 5.5 H7.6 A1.2 1.2 0 0 1 8.8 6.7 V7.6 A1.8 1.8 0 0 0 10.6 9.4 H13.4 A1.8 1.8 0 0 0 15.2 7.6 V6.7 A1.2 1.2 0 0 1 16.4 5.5 H18.2 "
                      "A2.8 2.8 0 0 1 21 8.3 V15.7 A2.8 2.8 0 0 1 18.2 18.5 H5.8 A2.8 2.8 0 0 1 3 15.7 V8.3 A2.8 2.8 0 0 1 5.8 5.5 Z", 0)),
        "windows": sym((R(3, 9, 16, 20, 2.8) + " M9 9 V7.8 A2.8 2.8 0 0 1 11.8 5 H18.2 A2.8 2.8 0 0 1 21 7.8 V12.2 A2.8 2.8 0 0 1 18.2 15 H16", 0.45)),
        "appearance": sym((C(12, 12, 8.6), 0), solids=[_half()]),
        # solid, and as tall as the box allows: it is shown small, as the charger mark beside the battery figure
        "bolt": cast_u(poly((14.8, 1), (3.6, 14), (10, 14), (8.4, 23), (20.4, 9.6), (13.6, 9.6)), 0.42),
        "play": cast_u(poly((7.4, 4.6), (19.6, 12), (7.4, 19.4)), 1.5),
        "pause": union(rect(5.8, 4.8, 10.2, 19.2, 1.3), rect(13.8, 4.8, 18.2, 19.2, 1.3)),
        "back": sym(("M20 12 H5 M10.8 6 L4.8 12 L10.8 18", 0.5)),
        "check": sym(("M4.8 12.6 L9.6 17.4 L19.2 7", 0.3)),
        "add": sym(("M12 4.8 V19.2 M4.8 12 H19.2", 0.6)),
        "close": sym(("M6.4 6.4 L17.6 17.6 M17.6 6.4 L6.4 17.6", 0.5)),
        "more": sym(solids=[disc(5.4, 12, 1.5), disc(12, 12, 1.5), disc(18.6, 12, 1.5)]),
        # general
        "drop": sym(("M12 3.6 C8.4 7.8 6 10.8 6 14.2 A6 6 0 0 0 18 14.2 C18 10.8 15.6 7.8 12 3.6 Z", 0)),
        "spinner": sym(("M12 3.4 A8.6 8.6 0 1 1 3.4 12", 0)),
        "error": sym((C(12, 12, 8.6) + " M12 7.4 V12.8", 0), solids=[disc(12, 16.2, 1.4)]),
        "warning": sym(("M12 4.2 L20.6 19.2 H3.4 Z", 0), ("M12 9.8 V13.4", 0), solids=[disc(12, 16.2, 1.2)]),
        "info": sym((C(12, 12, 8.6) + " M12 11 V16.6", 0), solids=[disc(12, 7.8, 1.4)]),
        "robot": sym((R(4, 8.4, 20, 19.4, 2.8) + " M12 8.4 V5.4", JOINT), solids=[disc(12, 4.2, 1.5), disc(8.8, 13.6, 1.4), disc(15.2, 13.6, 1.4)]),
        "chip": sym((R(6.4, 6.4, 17.6, 17.6, 2.4) + " M9.6 3.2 V6.4 M14.4 3.2 V6.4 M9.6 17.6 V20.8 M14.4 17.6 V20.8 M3.2 9.6 H6.4 M3.2 14.4 H6.4 M17.6 9.6 H20.8 M17.6 14.4 H20.8", 0.5),
                    solids=[disc(12, 12, 1.7)]),
        "drive": sym((R(3, 6, 21, 18, 2.8) + " M6.8 12 H11.4", 0), solids=[disc(16.8, 12, 1.5)]),
        "battery-alert": sym((R(2, 7, 18.6, 17, 2.8) + " M21.4 10.2 V13.8 M10.3 9.4 V12", 0), solids=[disc(10.3, 14.4, 1.05)]),
        "battery-charging": sym((R(2, 7, 18.6, 17, 2.8) + " M21.4 10.2 V13.8", 0), solids=[cast_u(poly((11.4, 8.8), (7.4, 12.6), (10, 12.6), (9.2, 15.2), (13.2, 11.4), (10.6, 11.4)), 0.25)]),
        "swap-h": sym(("M4 8.2 H19.4 M15.8 4.6 L19.4 8.2 L15.8 11.8 M20 15.8 H4.6 M8.2 12.2 L4.6 15.8 L8.2 19.4", 0.4)),
        "swap-v": sym(("M8.2 20 V4.6 M4.6 8.2 L8.2 4.6 L11.8 8.2 M15.8 4 V19.4 M12.2 15.8 L15.8 19.4 L19.4 15.8", 0.4)),
        "tag": sym(("M3.6 7.4 A2.8 2.8 0 0 1 6.4 4.6 H13 L20.4 12 L13 19.4 H6.4 A2.8 2.8 0 0 1 3.6 16.6 Z", 0), solids=[disc(8.4, 12, 1.4)]),
        "apps": sym(solids=[disc(x, y, 1.6) for x in (5.6, 12, 18.4) for y in (5.6, 12, 18.4)]),
        "grid": sym((R(3.6, 3.6, 10.4, 10.4, 2) + " " + R(13.6, 3.6, 20.4, 10.4, 2) + " " + R(3.6, 13.6, 10.4, 20.4, 2) + " " + R(13.6, 13.6, 20.4, 20.4, 2), 0)),
        "thermo": sym(("M9.8 14.4 V6 A2.2 2.2 0 0 1 14.2 6 V14.4 A4.2 4.2 0 1 1 9.8 14.4 Z", 0), solids=[disc(12, 17.4, 1.6)]),
        "edit": sym(("M4.4 19.6 L5.4 15.2 L15.8 4.8 A1.8 1.8 0 0 1 18.4 4.8 L19.2 5.6 A1.8 1.8 0 0 1 19.2 8.2 L8.8 18.6 Z M13.6 7 L17 10.4", 0.3)),
        "arrow-up": sym(("M12 20 V5 M6 10.8 L12 4.8 L18 10.8", 0.5)),
        "arrow-down": sym(("M12 4 V19 M6 13.2 L12 19.2 L18 13.2", 0.5)),
        "forward": sym(("M4 12 H19 M13.2 6 L19.2 12 L13.2 18", 0.5)),
        "light": sym(("M8.6 15.4 A6 6 0 1 1 15.4 15.4 V16.8 H8.6 Z M9.8 20.4 H14.2", 0)),
        "pin": sym(("M8.6 4 H15.4 M9.8 4 V10 L7 14.2 H17 L14.2 10 V4 M12 14.2 V20.6", 0.5)),
        "globe": sym((C(12, 12, 8.6) + " M12 3.4 C8.4 7 8.4 17 12 20.6 C15.6 17 15.6 7 12 3.4 M3.6 12 H20.4", 0)),
        "speed": sym(("M4.9 17.4 A8.6 8.6 0 1 1 19.1 17.4 M12 13.4 L15.6 8.8", 0), solids=[disc(12, 13.4, 1.6)]),
        "restart": sym(("M19.8 12.4 A7.8 7.8 0 1 1 17 6.2 M17.6 2.6 V6.6 H13.6", 0.3)),
        "layers": sym(("M12 4 L20.4 8.6 L12 13.2 L3.6 8.6 Z M4.4 13 L12 17.2 L19.6 13", 0.3)),
        "mouse": sym((R(7, 3, 17, 21, 5) + " M12 7 V10.4", 0)),
        "block": sym((C(12, 12, 8.6) + " M5.9 5.9 L18.1 18.1", 0)),
        "code": sym(("M8.6 6.8 L3.6 12 L8.6 17.2 M15.4 6.8 L20.4 12 L15.4 17.2", 0.3)),
        "user-circle": sym((C(12, 12, 8.6) + " " + C(12, 9.8, 2.7) + " M6.9 18.6 A5.8 4.6 0 0 1 17.1 18.6", 0)),
        "list": sym(("M8.8 7 H20.2 M8.8 12 H20.2 M8.8 17 H20.2", 0), solids=[disc(4.8, 7, 1.3), disc(4.8, 12, 1.3), disc(4.8, 17, 1.3)]),
        "ring": sym((C(12, 12, 8.6), 0)),
        "cloud": sym(("M7.2 18.6 A4.5 4.5 0 0 1 6.5 9.7 A5.7 5.7 0 0 1 17.4 10.4 A4.1 4.1 0 0 1 17 18.6 Z", 0)),
        "upload": sym(("M12 14.6 V4 M7.8 8.2 L12 4 L16.2 8.2", 0.5), ("M4.6 19.6 H19.4", 0)),
        "eye-off": off(sym(("M2.8 12 C6 7.4 9 6 12 6 C15 6 18 7.4 21.2 12 C18 16.6 15 18 12 18 C9 18 6 16.6 2.8 12 Z", 0), solids=[disc(12, 12, 2.4)])),
        "undo": sym(("M8.6 5.4 L4.2 9.8 L8.6 14.2 M4.4 9.8 H14.6 A5.2 5.2 0 0 1 14.6 20.2 H9.4", 0.4)),
        "paste": sym((R(5, 5.4, 19, 21, 2.8), 0), solids=[rect(8.6, 3, 15.4, 7.4, 1.4)]),
        "send": sym(("M3.8 11.6 L20.2 4 L15.4 20.2 L11.6 12.8 Z", 0.3)),
        "stop": rect(6, 6, 18, 18, 2.2),
        "stop-circle": sym((C(12, 12, 8.6), 0), solids=[rect(8.8, 8.8, 15.2, 15.2, 1.2)]),
        "equalizer": sym(("M5 10 V14 M9.6 6 V18 M14.4 8.6 V15.4 M19 4.6 V19.4", 0)),
        "sparkle": sym(("M12 3.4 C12.6 8.6 15.4 11.4 20.6 12 C15.4 12.6 12.6 15.4 12 20.6 C11.4 15.4 8.6 12.6 3.4 12 C8.6 11.4 11.4 8.6 12 3.4 Z", 0)),
        "lock-open": sym((R(5, 10.8, 19, 20.8, 2.8) + " M8.2 10.8 V7.6 A3.8 3.8 0 0 1 15.4 6", JOINT), solids=[disc(12, 15.8, 1.4)]),
        "zoom-in": sym((C(10.2, 10.2, 6.2) + " M14.6 14.6 L20.4 20.4", JOINT), ("M10.2 7.4 V13 M7.4 10.2 H13", 0)),
        "vpn-off": off(sym((C(7.8, 12, 4.4) + " M12.2 12 H20.6 V15.8 M16.4 12 V15.2", 0.5))),
        "star": sym(("M12 3.6 L14.5 9 L20.4 9.7 L16 13.7 L17.2 19.6 L12 16.6 L6.8 19.6 L8 13.7 L3.6 9.7 L9.5 9 Z", 0.3)),
        "link": sym(("M10.4 7.4 H7.6 A4.6 4.6 0 0 0 7.6 16.6 H10.4 M13.6 7.4 H16.4 A4.6 4.6 0 0 1 16.4 16.6 H13.6 M8.6 12 H15.4", 0)),
        # wave 2 (2026-10-02): the rest of what the shell shows
        "hand": sym(("M8.4 12.6 V6.6 A1.3 1.3 0 0 1 11 6.6 V11.4 M11 11.4 V5 A1.3 1.3 0 0 1 13.6 5 V11.4 M13.6 11.4 V6 A1.3 1.3 0 0 1 16.2 6 V12 "
                     "M16.2 12 V9.2 A1.3 1.3 0 0 1 18.8 9.2 V14.6 A6.4 6.4 0 0 1 12.4 21 H12 A6 6 0 0 1 7 18.4 L4.6 14.8 A1.4 1.4 0 0 1 6.9 13.3 L8.4 15", 0)),
        "blur": sym(solids=[disc(x, y, r) for (x, y, r) in [(6, 6, 1.0), (12, 6, 1.4), (18, 6, 1.0), (6, 12, 1.4), (12, 12, 2.0), (18, 12, 1.4), (6, 18, 1.0), (12, 18, 1.4), (18, 18, 1.0)]]),
        "corner": sym(("M4.6 19.4 V12.6 A8 8 0 0 1 12.6 4.6 H19.4", 0)),
        "motion": sym((C(15, 12, 5.6), 0), ("M9.4 7.6 A6 6 0 0 0 6.6 12 A6 6 0 0 0 9.4 16.4 M5 8.8 A5.2 5.2 0 0 0 3.4 12 A5.2 5.2 0 0 0 5 15.2", 0)),
        "text": sym(("M5 7 V5 H19 V7 M12 5 V19.6 M9 19.6 H15", JOINT)),
        "move": sym(("M12 3.6 V20.4 M3.6 12 H20.4", 0), ("M9.6 6 L12 3.6 L14.4 6 M9.6 18 L12 20.4 L14.4 18 M6 9.6 L3.6 12 L6 14.4 M18 9.6 L20.4 12 L18 14.4", 0)),
        "brush": sym(("M14.4 4.6 L19.4 9.6 L12.4 16.6 L7.4 11.6 Z M9.8 14.2 L6.4 17.6 A2 2 0 0 0 4.6 19.4", 0.4)),
        "sun-cloud": sym(("M8.2 9 A4.2 4.2 0 0 1 15.8 7.4 M10.6 2.4 V3.8 M4.6 4.6 L5.6 5.6 M16.6 4.6 L15.6 5.6 M2.6 10.4 H4", 0),
                         ("M7.6 20 A3.8 3.8 0 0 1 7.2 12.6 A5 5 0 0 1 16.8 12 A4 4 0 0 1 16.8 20 Z", 0)),
        "rain": sym(("M7.2 14.6 A3.8 3.8 0 0 1 7 7.2 A5 5 0 0 1 16.6 6.6 A4 4 0 0 1 16.8 14.6 Z", 0), ("M8.6 17.4 L7.4 20.6 M12.6 17.4 L11.4 20.6 M16.6 17.4 L15.4 20.6", 0)),
        "snow": sym(("M12 3.2 V20.8 M4.4 7.6 L19.6 16.4 M19.6 7.6 L4.4 16.4", 0), solids=[disc(12, 12, 1.6)]),
        "wind": sym(("M3.4 9.2 H14.6 A2.6 2.6 0 1 0 12 6.6 M3.4 13.4 H18 A2.6 2.6 0 1 1 15.4 16 M3.4 17.4 H9.6", 0)),
        "login": sym(("M13.6 4.4 H17.4 A2.8 2.8 0 0 1 20.2 7.2 V16.8 A2.8 2.8 0 0 1 17.4 19.6 H13.6", 0), ("M3.8 12 H14.4 M10.8 8.4 L14.4 12 L10.8 15.6", 0.5)),
        "shield": sym(("M12 3.2 L19.4 6 V11.4 C19.4 16 16.4 19.2 12 20.8 C7.6 19.2 4.6 16 4.6 11.4 V6 Z", 0), ("M9 12 L11.2 14.2 L15.2 9.8", 0.3)),
        "ear": sym(("M7 9.6 A5.4 5.4 0 0 1 17.8 9.6 C17.8 13.4 13.8 13.6 13.8 17.2 A3 3 0 0 1 8.2 18.8 M10.2 10 A2 2 0 0 1 14.2 10", 0)),
        "network": sym((R(9.2, 3.2, 14.8, 8.2, 1.6) + " " + R(3.2, 15.8, 8.8, 20.8, 1.6) + " " + R(15.2, 15.8, 20.8, 20.8, 1.6), 0), ("M12 8.2 V12 M6 15.8 V12 H18 V15.8", JOINT)),
        "hash": sym(("M9.4 4 L7.8 20 M16.2 4 L14.6 20 M4.4 9 H19.8 M4 15 H19.4", 0.4)),
        "phone": sym((R(6.6, 2.8, 17.4, 21.2, 2.8), 0), solids=[disc(12, 18.2, 1.2)]),
        "pulse": sym(("M2.8 12 H7 L9.4 6 L13.6 18 L16 12 H21.2", 0.3)),
        "panel": sym((R(3, 5, 21, 19, 2.8) + " M14.4 5 V19", JOINT)),
        "leaf": sym(("M5 19 C5 9.4 10.4 4.6 19.4 4.6 C19.4 13.6 14.6 19 5 19 Z M5 19 L13 11", 0.5)),
        "flame": sym(("M12 21 A6.2 6.2 0 0 1 5.8 14.8 C5.8 10.2 10.2 8.2 10.2 3.4 C14.2 5.6 18.2 9.4 18.2 14.8 A6.2 6.2 0 0 1 12 21 Z", 0), ("M12 21 A2.6 2.6 0 0 1 9.4 18.4 C9.4 16.2 11.4 15.4 12 13.4 C12.8 15.4 14.6 16.4 14.6 18.4 A2.6 2.6 0 0 1 12 21", 0)),
        "fingerprint": sym(("M5.2 15.6 V12 A6.8 6.8 0 0 1 18.8 12 V13.6 M8.6 19.4 V12 A3.4 3.4 0 0 1 15.4 12 V16.4 M12 12 V20.4 M5.8 7.4 A8.6 8.6 0 0 1 18.2 7.4", 0)),
        "save": sym(("M5.6 3.6 H15.4 L20.4 8.6 V17.6 A2.8 2.8 0 0 1 17.6 20.4 H6.4 A2.8 2.8 0 0 1 3.6 17.6 V6.4 A2.8 2.8 0 0 1 6.4 3.6 Z M8 3.6 V8 H14.4 V3.6", 0.6), solids=[disc(12, 14.6, 2.4)]),
        "quote": sym(("M8.4 9.8 C8.4 13.6 6.8 16.4 4.6 17.8 M17.4 9.8 C17.4 13.6 15.8 16.4 13.6 17.8", 0), solids=[disc(6.6, 8.6, 2.6), disc(15.6, 8.6, 2.6)]),
        "scissors": sym((C(6.6, 7, 2.8) + " " + C(6.6, 17, 2.8), 0), ("M8.8 8.6 L20 17.6 M8.8 15.4 L20 6.4", 0)),
        "calc": sym((R(4.6, 3, 19.4, 21, 2.8) + " M7.8 7.4 H16.2", JOINT), solids=[disc(x, y, 1.2) for x in (8.4, 12, 15.6) for y in (12.4, 16.6)]),
        "smile": sym((C(12, 12, 8.6), 0), ("M8.4 14.2 A4.2 4.2 0 0 0 15.6 14.2", 0), solids=[disc(9, 9.6, 1.3), disc(15, 9.6, 1.3)]),
        "mail": sym((R(3, 5, 21, 19, 2.8), 0), ("M5 7.6 L12 12.8 L19 7.6", 0.4)),
        "box": sym(("M12 3 L20.2 7.4 V16.6 L12 21 L3.8 16.6 V7.4 Z M3.8 7.4 L12 11.8 L20.2 7.4 M12 11.8 V21", 0.4)),
        "shapes": sym((C(8.2, 8.2, 4.6), 0), (R(11.6, 11.6, 20.4, 20.4, 2.2), 0)),
        "bug": sym(("M8 9.4 A4 4 0 0 1 16 9.4 V15 A4 4 0 0 1 8 15 Z M12 9.6 V18.6 M8 13 H3.6 M16 13 H20.4 M8.2 9.8 L4.8 7.4 M15.8 9.8 L19.2 7.4 M8.4 16.6 L5 19 M15.6 16.6 L19 19 M9.4 6.6 L8 4.2 M14.6 6.6 L16 4.2", 0.4)),
        "target": sym((C(12, 12, 7), 0), ("M12 2.6 V5 M12 19 V21.4 M2.6 12 H5 M19 12 H21.4", 0), solids=[disc(12, 12, 2.2)]),
        "commit": sym((C(12, 12, 4), 0), ("M2.8 12 H8 M16 12 H21.2", 0)),
        "chat": sym(("M6.6 4.6 H17.4 A2.8 2.8 0 0 1 20.2 7.4 V13.8 A2.8 2.8 0 0 1 17.4 16.6 H10.2 L6 20 V16.6 A2.8 2.8 0 0 1 3.8 13.8 V7.4 A2.8 2.8 0 0 1 6.6 4.6 Z", 0)),
        "backspace": sym(("M8.4 5.4 H18.4 A2.8 2.8 0 0 1 21.2 8.2 V15.8 A2.8 2.8 0 0 1 18.4 18.6 H8.4 L2.8 12 Z", 0.3), ("M11.4 9.4 L16.6 14.6 M16.6 9.4 L11.4 14.6", 0.4)),
        "hourglass": sym(("M6 3.4 H18 M6 20.6 H18 M7.4 3.4 V6.4 C7.4 9.6 12 10.6 12 12 C12 13.4 7.4 14.4 7.4 17.6 V20.6 M16.6 3.4 V6.4 C16.6 9.6 12 10.6 12 12 C12 13.4 16.6 14.4 16.6 17.6 V20.6", JOINT)),
        "dnd": sym((C(12, 12, 8.6), 0), solids=[rect(7.4, 10.9, 16.6, 13.1, 1.1)]),
        "gamepad": sym(("M7.6 7.4 H16.4 A4.6 4.6 0 0 1 20.8 13.2 L19.8 17 A2.6 2.6 0 0 1 15.4 18.2 L14 16.6 H10 L8.6 18.2 A2.6 2.6 0 0 1 4.2 17 L3.2 13.2 A4.6 4.6 0 0 1 7.6 7.4 Z M8.2 10.4 V13.8 M6.5 12.1 H9.9", 0.4), solids=[disc(15.4, 11, 1.1), disc(17.4, 13.2, 1.1)]),
        "map": sym(("M3.6 6.2 L9 4 L15 6.4 L20.4 4.2 V17.8 L15 20 L9 17.6 L3.6 19.8 Z M9 4 V17.6 M15 6.4 V20", 0.4)),
        "help": sym((C(12, 12, 8.6), 0), ("M9.6 9.6 A2.4 2.4 0 1 1 13.6 11.4 C12.6 12 12 12.6 12 14", 0), solids=[disc(12, 16.8, 1.25)]),
        "checkbox": sym((R(4, 4, 20, 20, 3.2), 0), ("M8 12.2 L10.8 15 L16.2 9.2", 0.3)),
        "box-empty": sym((R(4, 4, 20, 20, 3.2), 0)),
        "filter": sym(("M3.6 5 H20.4 L14 12.4 V19.4 L10 17.4 V12.4 Z", 0.4)),
        "eject": sym(("M12 5 L19 13 H5 Z M5 18.6 H19", 0.3)),
        "pie": sym((C(12, 12, 8.6), 0), ("M12 3.4 V12 L18.2 17.8", JOINT)),
        "cloud-off": off(sym(("M7.2 18.6 A4.5 4.5 0 0 1 6.5 9.7 A5.7 5.7 0 0 1 17.4 10.4 A4.1 4.1 0 0 1 17 18.6 Z", 0))),
        "bolt-off": off(cast_u(poly((14.8, 1), (3.6, 14), (10, 14), (8.4, 23), (20.4, 9.6), (13.6, 9.6)), 0.42)),
        "pin-off": off(sym(("M8.6 4 H15.4 M9.8 4 V10 L7 14.2 H17 L14.2 10 V4 M12 14.2 V20.6", 0.5))),
        "folder-add": sym(("M3 16.8 V7 A2.2 2.2 0 0 1 5.2 4.8 H7.8 A2 2 0 0 1 9.8 6.8 A1.6 1.6 0 0 0 11.4 8.4 H18.2 A2.8 2.8 0 0 1 21 11.2 V16.8 "
                           "A2.8 2.8 0 0 1 18.2 19.6 H5.8 A2.8 2.8 0 0 1 3 16.8 Z", 0), ("M12 11.2 V16.8 M9.2 14 H14.8", 0.4)),
        "pointer": sym(solids=[cast_u(poly((6, 3.6), (18.6, 12.6), (12.6, 13.6), (9.6, 19.4)), 0.8)]),
        "plane": sym(("M12 3.2 C13 3.2 13.4 4.4 13.4 6 V9.6 L20.6 13.6 V15.4 L13.4 13.4 V18 L15.6 19.6 V21 L12 20 L8.4 21 V19.6 L10.6 18 V13.4 L3.4 15.4 V13.6 L10.6 9.6 V6 C10.6 4.4 11 3.2 12 3.2 Z", 0.3)),
        # the control panel
        "vpn": sym((C(7.8, 12, 4.4) + " M12.2 12 H20.6 V15.8 M16.4 12 V15.2", 0.5)),
        "bluetooth-on": sym((RUNE, 0.3), solids=[disc(4.2, 12, 1.4), disc(19.8, 12, 1.4)]),
        "bluetooth-off": off(sym((RUNE, 0.3))),
        "bell-ring": sym((BELL, JOINT), ("M4.4 8.8 A8.4 8.4 0 0 1 6.4 4.8 M19.6 8.8 A8.4 8.4 0 0 0 17.6 4.8", 0), solids=[disc(12, 20.6, 1.4)]),
        "bell-off": off(sym((BELL, JOINT), solids=[disc(12, 20.6, 1.4)])),
        "mic-off": off(sym(*MIC)),
        "night": sym(("M19.6 14.6 A8.4 8.4 0 1 1 9.4 4.4 A6.6 6.6 0 0 0 19.6 14.6 Z", 0), solids=[disc(17.6, 6.4, 1.5)]),
        "awake": sym(("M4.6 6.6 H16.4 V12.6 A5.4 5.4 0 0 1 11 18 H10 A5.4 5.4 0 0 1 4.6 12.6 Z M16.4 8.4 H17.6 A2.8 2.8 0 0 1 17.6 14 H16.2", 0.6), ("M4 21 H17", 0)),
        "volume-low": union(sym((SPEAKER, 0), ("M15.2 8.8 A4.6 4.6 0 0 1 15.2 15.2", 0)), hair("M17.9 6 A8.4 8.4 0 0 1 17.9 18")),
        "volume-off": sym((SPEAKER, 0), ("M15.6 9.4 L20.8 14.6 M20.8 9.4 L15.6 14.6", 0.4)),
        "record": sym((C(12, 12, 8.6), 0), solids=[disc(12, 12, 3.4)]),
        "snip": sym(("M3.6 8.8 V6.4 A2.8 2.8 0 0 1 6.4 3.6 H8.8 M15.2 3.6 H17.6 A2.8 2.8 0 0 1 20.4 6.4 V8.8 M20.4 15.2 V17.6 A2.8 2.8 0 0 1 17.6 20.4 H15.2 "
                     "M8.8 20.4 H6.4 A2.8 2.8 0 0 1 3.6 17.6 V15.2", 0)),
        "picker": sym(("M4.6 19.4 L12.8 11.2 M10.2 8.2 L15.8 13.8", 0.6), solids=[line([(14.4, 9.6), (17.8, 6.2)], 4.2, "round")]),
        "keyboard": sym((R(2.5, 6, 21.5, 18, 2.8) + " M8.4 14.6 H15.6", 0), solids=[disc(6.6, 10.2, 1.1), disc(10.2, 10.2, 1.1), disc(13.8, 10.2, 1.1), disc(17.4, 10.2, 1.1)]),
        "timer": sym((C(12, 13.6, 7.4) + " M9.8 3.2 H14.2", 0), ("M12 13.6 V9.8", 0), solids=[disc(12, 13.6, 1.5)]),
        "check-circle": sym((C(12, 12, 8.6), 0), ("M8 12.4 L11 15.2 L16 9.4", 0.3)),
        "minus": sym(("M4.8 12 H19.2", 0)),
        "up": sym(("M6 15 L12 9 L18 15", 0.3)),
        "down": sym(("M6 9 L12 15 L18 9", 0.3)),
        "left": sym(("M15 6 L9 12 L15 18", 0.3)),
        "right": sym(("M9 6 L15 12 L9 18", 0.3)),
        # notifications
        "copy": sym((R(9, 8.4, 20.4, 20.4, 2.8) + " M9 15.6 H6.4 A2.8 2.8 0 0 1 3.6 12.8 V6.4 A2.8 2.8 0 0 1 6.4 3.6 H12.8 A2.8 2.8 0 0 1 15.6 6.4 V8.4", 0.45)),
        "clear": sym(("M3.6 7 H13.4 M3.6 12 H10.4 M3.6 17 H8.4", 0), ("M14.6 12.6 L20.2 18.2 M20.2 12.6 L14.6 18.2", 0.4)),
        "open": sym(("M10.6 5 H7.8 A2.8 2.8 0 0 0 5 7.8 V16.2 A2.8 2.8 0 0 0 7.8 19 H16.2 A2.8 2.8 0 0 0 19 16.2 V13.4", 0), ("M11.8 12.2 L19.6 4.4 M14.2 4.4 H19.6 V9.8", 0.4)),
        "reply": sym(("M9.8 6 L4.6 11.2 L9.8 16.4 M4.8 11.2 H13.6 A5.8 5.8 0 0 1 19.4 17 V18.8", 0.4)),
        "alert": sym(("M12 4.4 V13.8", 0), solids=[disc(12, 18.6, 1.6)]),
        # the notch's player
        "next": union(cast_u(poly((4.6, 5.2), (15, 12), (4.6, 18.8)), 1.4), rect(16.8, 5.2, 19.6, 18.8, 1.2)),
        "previous": union(cast_u(poly((19.4, 5.2), (9, 12), (19.4, 18.8)), 1.4), rect(4.4, 5.2, 7.2, 18.8, 1.2)),
        "shuffle": sym(("M3.6 7.2 H6.6 C10.6 7.2 12.4 16.8 16.4 16.8 H20.2 M17.6 14 L20.4 16.8 L17.6 19.6 M3.6 16.8 H6.6 C8 16.8 9.2 15.8 10.2 14.4 "
                        "M13.6 9.6 C14.4 8.2 15.4 7.2 16.6 7.2 H20.2 M17.6 4.4 L20.4 7.2 L17.6 10", 0.3)),
        "repeat": sym(("M16.8 3.6 L19.8 6.6 L16.8 9.6 M4 11.6 V9.4 A2.8 2.8 0 0 1 6.8 6.6 H19.6 M7.2 20.4 L4.2 17.4 L7.2 14.4 M20 12.4 V14.6 A2.8 2.8 0 0 1 17.2 17.4 H4.4", 0.3)),
        "music-off": off(sym(("M9.2 17.6 V6.6 L18 4.6 V15.6", 0.5), **NOTES)),
        # wave 3 (2026-10-15, owner "expand our symbols"): Thyris's and the shell's names still drawn by Material
        # history: restart's arc and corner arrow turned the other way, the clock's hands and pivot in its centre
        "history": sym(("M4.2 12.4 A7.8 7.8 0 1 0 7 6.2 M6.4 2.6 V6.6 H10.4", 0.3), ("M12 8.2 V12.2 L14.6 13.7", 0),
                       solids=[disc(12, 12.2, 1.5)]),
        "bookmark": sym(("M6.6 20.4 V6 A2.8 2.8 0 0 1 9.4 3.2 H14.6 A2.8 2.8 0 0 1 17.4 6 V20.4 L12 16.4 Z", 0.3)),
        "return": sym(("M19 4.8 V11 A2.8 2.8 0 0 1 16.2 13.8 H5.4 M9.6 9.6 L5.4 13.8 L9.6 18", 0.5)),
        # print: the sheet in, the body with its slot, the sheet out of the slot; the light the one dot
        "print": sym((R(3, 8.6, 21, 16.8, 2.8) + " M7 13.6 H17", JOINT), ("M7.4 8.6 V5.6 A1.8 1.8 0 0 1 9.2 3.8 H14.8 A1.8 1.8 0 0 1 16.6 5.6 V8.6", 0),
                     ("M8.4 13.6 V20.2 H15.6 V13.6", JOINT), solids=[disc(17.4, 11.1, 1.1)]),
        # cookie: the round with one small bite out of its top right (a bigger one read as a crescent moon), two chips
        "cookie": sym(("M19.79 8.35 A8.6 8.6 0 1 1 15.65 4.21 A3.6 3.6 0 0 0 19.79 8.35 Z", 0),
                      solids=[disc(9.2, 10.2, 1.3), disc(13.8, 15.4, 1.3)]),
        # place: the pin, its point the one dot
        "place": sym(("M12 20.8 C8.2 16.6 5.6 13.4 5.6 9.8 A6.4 6.4 0 0 1 18.4 9.8 C18.4 13.4 15.8 16.6 12 20.8 Z", 0), solids=[disc(12, 9.8, 2.1)]),
        "screen-share": sym((R(3, 4, 21, 15.6, 2.8) + " M12 15.6 V20 M8 20 H16", JOINT), ("M9.2 12.4 L14.6 7 M10.8 7 H14.6 V10.8", 0.5)),
        "headphones": sym(("M4.2 15.4 V12.4 A7.8 7.8 0 0 1 19.8 12.4 V15.4", 0),
                          (R(3.2, 13.6, 7.6, 20.6, 2.2) + " " + R(16.4, 13.6, 20.8, 20.6, 2.2), 0)),
        "laptop": sym((R(4.4, 5, 19.6, 15.2, 2.4), 0), ("M2.6 18.8 H21.4", 0)),
        "tablet": sym((R(4.4, 3, 19.6, 21, 2.8), 0), solids=[disc(12, 17.8, 1.2)]),
        "tv": sym((R(3, 5, 21, 17, 2.8), 0), ("M8.6 20.2 H15.4", 0)),
        "fullscreen": sym(("M4 9.4 V6.8 A2.8 2.8 0 0 1 6.8 4 H9.4 M14.6 4 H17.2 A2.8 2.8 0 0 1 20 6.8 V9.4 M20 14.6 V17.2 A2.8 2.8 0 0 1 17.2 20 "
                           "H14.6 M9.4 20 H6.8 A2.8 2.8 0 0 1 4 17.2 V14.6", 0)),
        "fullscreen-exit": sym(("M9.4 4 V9.4 H4 M14.6 4 V9.4 H20 M20 14.6 H14.6 V20 M4 14.6 H9.4 V20", 0.3)),
        "toggle": sym((R(2.6, 6.6, 21.4, 17.4, 5.4), 0), solids=[disc(16, 12, 3.2)]),
        "trackpad": sym((R(3, 4.4, 21, 19.6, 2.8) + " M3 14.6 H21 M12 14.6 V19.6", JOINT)),
        "close-circle": sym((C(12, 12, 8.6), 0), ("M9 9 L15 15 M15 9 L9 15", 0.5)),
        # Praxis's mark (Thyris's "Ask Praxis"): the diamond, its centre the one dot
        "diamond": sym(("M12 3.4 L20.6 12 L12 20.6 L3.4 12 Z", 0), solids=[disc(12, 12, 1.6)]),
        # wave 4 (2026-10-24, owner "dont use material, draw our own"): Thyris's last Material names, which an install
        # (no Material font) drew as words. extension (owner's pick C of three, sheet_wave4.py): four modules in a
        # square, one of them solid and set out of line, the one being added; not Material's puzzle piece
        "extension": sym((R(3.6, 3.6, 10.6, 10.6, 2.2) + " " + R(3.6, 13.4, 10.6, 20.4, 2.2) + " " + R(13.4, 13.4, 20.4, 20.4, 2.2), 0),
                         solids=[rect(14.2, 3, 21, 9.8, 2.2)]),
        # find in page: the page with its lines, its corner given to the lens; the lens docks its handle
        "find-page": sym(("M12.4 21 H8.3 A2.8 2.8 0 0 1 5.5 18.2 V5.8 A2.8 2.8 0 0 1 8.3 3 H15.7 A2.8 2.8 0 0 1 18.5 5.8 V9.2 "
                          "M8.8 7.6 H14.4 M8.8 11.4 H11.4", 0),
                         (C(15.6, 15.4, 3.4) + " M18.1 17.9 L21 20.8", JOINT)),
        # reader: the open book, its two pages meeting at the spine with a cove
        "reader": sym(("M12 6.6 C9.8 5.2 7.2 4.8 3.4 5 V18.4 C7.2 18.2 9.8 18.6 12 20 C14.2 18.6 16.8 18.2 20.6 18.4 V5 "
                       "C16.8 4.8 14.2 5.2 12 6.6 Z M12 6.6 V20", 0.6)),
        # a pop-up held back: the page window with its bar, struck through
        "popup-off": off(sym((R(3, 5, 21, 19, 2.8) + " M3 9.6 H21", JOINT))),
    }
    return _nudged(out)


def _half():
    p = Path()
    parse_path("M12 7 A5 5 0 0 1 12 17 Z", p.getPen())
    return _clean(p)


def cursor():
    return cast(poly((7, 4), (17, 38), (21.4, 23.4), (35.4, 18)), 1.1, 5.0)


if __name__ == "__main__":
    P = {n: (d(s[0]), d(s[1])) if isinstance(s, tuple) else (d(s), None) for n, s in symbols().items()}
    F = {n: d(shape) for n, shape in filled().items() if shape is not None}
    dart = d(cursor())
    table = {"today": live(), "sea": generated("#2f5d8a"), "moss": generated("#55703a")}
    for pname, (ink, accent, outline, ground, panel, raised, soft) in table.items():
        os.makedirs(f"build/{pname}", exist_ok=True)
        for name, (path, dim) in P.items():
            for tag, colour in (("", ink), ("-on", accent), ("-soft", soft)):
                body = f'<path d="{path}" fill="{colour}"/>' + (f'<path d="{dim}" fill="{colour}" opacity="0.34"/>' if dim else "")
                write(f"build/{pname}/{name}{tag}.svg", body, 24, 192)
        for name, path in F.items():
            write(f"build/{pname}/{name}-fill.svg", f'<path d="{path}" fill="{accent}"/>', 24, 192)
        shadow = '<defs><filter id="s" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="1.4"/></filter></defs>' \
                 f'<path d="{dart}" transform="translate(0.5 1.4)" fill="#000" opacity="0.4" filter="url(#s)"/>'
        for tag, fill, edge in (("dusk", ground, ink), ("light", ink, ground)):
            write(f"build/{pname}/cursor-{tag}.svg", shadow + f'<path d="{dart}" fill="{edge}" stroke="{edge}" stroke-width="2.6" stroke-linejoin="round"/><path d="{dart}" fill="{fill}"/>', 48, 192)
    json.dump({"names": list(P), "filled": list(F), "palettes": table}, open("build/index.json", "w"), indent=1)
    print(len(P), "symbols")

"""Geometry for Tacit's symbols: shapes are built as solids and then cast the way Tacit's surfaces and letters
are: free corners eased, inner corners filled with a cove (the notch's docked corner, tools/soften.py in the font).

    rect, pill, disc, poly, line, arc        solids (a line is a stroke turned into its outline)
    union, minus, both                       set operations
    cast(shape, ease, cove)                  eases outward corners by `ease`, fills inward corners with `cove`
    d(shape)                                 SVG path data

Run with the font project's venv (skia-pathops).
"""
import math

import pathops
from fontTools.pens.svgPathPen import SVGPathPen
from pathops import LineCap, LineJoin, Path, PathOp

K = 0.5523


def _clean(p):
    p.convertConicsToQuads(0.02)
    p.simplify(fix_winding=True, keep_starting_points=False)
    return p


def _op(a, b, operator):
    out = pathops.op(a, b, operator, fix_winding=True, keep_starting_points=False)
    out.convertConicsToQuads(0.02)
    return out


def rect(x0, y0, x1, y1, r=0.0):
    """A rectangle; r is one corner radius or four (top-left, top-right, bottom-right, bottom-left)."""
    tl, tr, br, bl = (r,) * 4 if isinstance(r, (int, float)) else r
    p = Path(); pen = p.getPen()
    pen.moveTo((x0 + tl, y0))
    pen.lineTo((x1 - tr, y0))
    if tr: pen.curveTo((x1 - tr + tr * K, y0), (x1, y0 + tr - tr * K), (x1, y0 + tr))
    pen.lineTo((x1, y1 - br))
    if br: pen.curveTo((x1, y1 - br + br * K), (x1 - br + br * K, y1), (x1 - br, y1))
    pen.lineTo((x0 + bl, y1))
    if bl: pen.curveTo((x0 + bl - bl * K, y1), (x0, y1 - bl + bl * K), (x0, y1 - bl))
    pen.lineTo((x0, y0 + tl))
    if tl: pen.curveTo((x0, y0 + tl - tl * K), (x0 + tl - tl * K, y0), (x0 + tl, y0))
    pen.closePath()
    return _clean(p)


def pill(x0, y0, x1, y1):
    return rect(x0, y0, x1, y1, min(x1 - x0, y1 - y0) / 2)


def disc(cx, cy, r):
    return rect(cx - r, cy - r, cx + r, cy + r, r)


def poly(*pts):
    p = Path(); pen = p.getPen()
    pen.moveTo(pts[0])
    for q in pts[1:]:
        pen.lineTo(q)
    pen.closePath()
    return _clean(p)


def _stroke(p, w, cap, join=LineJoin.ROUND_JOIN):
    p.stroke(w, cap, join, 4)
    return _clean(p)


def line(pts, w, cap="butt", closed=False, join="round"):
    """A polyline drawn with a stroke of width w, as a solid."""
    p = Path(); pen = p.getPen()
    pen.moveTo(pts[0])
    for q in pts[1:]:
        pen.lineTo(q)
    pen.closePath() if closed else pen.endPath()
    return _stroke(p, w, LineCap.ROUND_CAP if cap == "round" else LineCap.BUTT_CAP,
                   LineJoin.MITER_JOIN if join == "miter" else LineJoin.ROUND_JOIN)


def arc(cx, cy, r, a0, a1, w, cap="butt"):
    """An arc of a circle from angle a0 to a1 (degrees, clockwise from 12 o'clock), stroked with width w."""
    n = max(8, int(abs(a1 - a0) / 4))
    pts = [(cx + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)), cy - r * math.cos(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    return line(pts, w, cap)


def ring(cx, cy, r, w):
    return minus(disc(cx, cy, r + w / 2), disc(cx, cy, r - w / 2))


def union(*shapes):
    out = shapes[0]
    for s in shapes[1:]:
        out = _op(out, s, PathOp.UNION)
    return out


def minus(a, *bs):
    for b in bs:
        a = _op(a, b, PathOp.DIFFERENCE)
    return a


def both(a, b):
    return _op(a, b, PathOp.INTERSECTION)


def _grow(shape, r):
    edge = Path(); edge.addPath(shape)
    edge.stroke(2 * r, LineCap.ROUND_CAP, LineJoin.ROUND_JOIN, 4)
    return _op(shape, _clean(edge), PathOp.UNION)


def _shrink(shape, r):
    edge = Path(); edge.addPath(shape)
    edge.stroke(2 * r, LineCap.ROUND_CAP, LineJoin.ROUND_JOIN, 4)
    return _op(shape, _clean(edge), PathOp.DIFFERENCE)


def cast(shape, ease=0.35, cove=0.9):
    """Inward corners get a cove of radius `cove`, then outward corners are eased by `ease`."""
    if cove:
        shape = _shrink(_grow(shape, cove), cove)
    if ease:
        shape = _grow(_shrink(shape, ease), ease)
    return shape


def d(shape):
    pen = SVGPathPen(None, ntos=lambda v: f"{v:.3f}".rstrip("0").rstrip("."))
    shape.draw(pen)
    return pen.getCommands()

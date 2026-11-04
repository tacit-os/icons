"""Tacit's cursor (B: the sand dart), drawn once into masks that any palette can paint.

Every shape is drawn on a 48 grid as one silhouette (kit.py): filled in the accent (matugen primary) with a hairline of
the ground (surface) and a soft shadow. The pointer is the dart, its back cut like the notch's cove; text is a thin
barred I; busy is the notch's spinner. Names and links follow the freedesktop / Xcursor set (Bibata's), so every app
finds its cursor.

Colours are not baked in. Each frame is rendered twice per size (accent white / edge black, then swapped), which gives
per pixel how much of it is accent, how much edge, and its opacity; paint.py turns those into a theme for any two
colours with plain arithmetic, so a wallpaper change can repaint the cursor without drawing anything.

    cursors.py -> build/cursors/masks.bin, previews in build/cursors/*.png      (run with the font project's venv)
    paint.py   -> ~/.local/share/icons/Tacit                                    (system python, stdlib only)
"""
import json
import math
import os
import struct
import subprocess
import sys
import tempfile
import zlib

from PIL import Image

from kit import cast, d, disc, line, minus, pill, poly, rect, ring, union

FILL, EDGE = "%FILL%", "%EDGE%"
SIZES = (24, 30, 36, 48, 60, 72, 96)
OUT = "build/cursors"


# ------------------------------------------------------------------- shapes (48 grid)
def dart():
    return cast(poly((7, 4), (17, 38), (21.4, 23.4), (35.4, 18)), 1.1, 5.0)


def upright_dart():
    """The dart turned so it points straight up, its tip at (24, 4.4)."""
    tipx, tipy, bx, by = 7, 4, 20, 22
    t = math.atan2(-1, 0) - math.atan2(tipy - by, tipx - bx)
    c, s_ = math.cos(t), math.sin(t)
    rx, ry = c * tipx - s_ * tipy, s_ * tipx + c * tipy
    return dart().transform(c, s_, -s_, c, 24 - rx, 4.4 - ry)


def badge(glyph):
    """A small disc at the dart's lower right carrying a sign: the arrow's companions (copy, link, help, ...)."""
    return (disc(35, 35, 8.4), glyph)


def pointing_hand():
    finger = pill(18.4, 4.6, 25.4, 30)
    knuckles = [pill(25, 16.6, 31.6, 30), pill(31, 18.4, 37.2, 31), pill(36.6, 20.6, 42.4, 31.6)]
    palm = cast(poly((18.4, 24), (42.4, 25.6), (42.4, 33.6), (35.4, 44), (21.6, 44), (12.6, 34.4)), 4.2, 0)
    thumb = cast(line([(19.6, 33.4), (11, 25.6)], 6.2, "round"), 0, 0)
    return cast(union(finger, *knuckles, palm, thumb), 0, 1.6)


def open_hand():
    fingers = [pill(13.6, 9.6, 19.6, 30), pill(20, 6.4, 26, 30), pill(26.4, 8, 32.4, 30), pill(32.8, 11.6, 38.4, 31)]
    palm = cast(poly((13.6, 25), (38.4, 25), (38.4, 33.6), (32.6, 43.6), (19.4, 43.6), (13.6, 35)), 4.2, 0)
    thumb = cast(line([(15, 33.6), (7.6, 26.4)], 6.2, "round"), 0, 0)
    return cast(union(*fingers, palm, thumb), 0, 1.6)


def closed_hand():
    knuckles = [pill(13.6, 17.4, 19.6, 28), pill(19.8, 15.6, 25.8, 28), pill(26, 16.4, 32, 28), pill(32.2, 18, 38, 29)]
    palm = cast(poly((13.6, 24), (38, 24), (38.4, 33.6), (32.6, 43.4), (19.4, 43.4), (13.4, 34.4)), 4.2, 0)
    thumb = cast(line([(14.6, 33), (9.6, 28.4)], 6, "round"), 0, 0)
    return cast(union(*knuckles, palm, thumb), 0, 1.6)


def ibeam(vertical=False):
    shape = union(rect(22.6, 8, 25.4, 40, 0.6), rect(17.6, 6.6, 30.4, 9.6, 0.8), rect(17.6, 38.4, 30.4, 41.4, 0.8))
    return shape.transform(0, 1, -1, 0, 48, 0) if vertical else shape


def arrowhead(tip, back, half=7.4):
    """A filled arrowhead pointing from back to tip."""
    (tx, ty), (bx, by) = tip, back
    ux, uy = tx - bx, ty - by
    n = math.hypot(ux, uy)
    ux, uy = ux / n, uy / n
    px, py = -uy, ux
    return cast(poly((tx, ty), (bx + px * half, by + py * half), (bx - px * half, by - py * half)), 1.0, 0)


def double_arrow(angle):
    """A two-headed arrow through the centre at `angle` degrees (0 = left-right)."""
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    c = 24
    tip1, tip2 = (c + ux * 17, c + uy * 17), (c - ux * 17, c - uy * 17)
    back1, back2 = (c + ux * 8.6, c + uy * 8.6), (c - ux * 8.6, c - uy * 8.6)
    shaft = line([(c - ux * 10, c - uy * 10), (c + ux * 10, c + uy * 10)], 4.2)
    return cast(union(shaft, arrowhead(tip1, back1), arrowhead(tip2, back2)), 0, 1.4)


def single_arrow(angle):
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    c = 24
    tip, back = (c + ux * 15, c + uy * 15), (c + ux * 5, c + uy * 5)
    shaft = line([(c - ux * 13, c - uy * 13), (c + ux * 6, c + uy * 6)], 4.2)
    return cast(union(shaft, arrowhead(tip, back)), 0, 1.4)


def four_way():
    parts = []
    for ang in (0, 90, 180, 270):
        a = math.radians(ang)
        ux, uy = math.cos(a), math.sin(a)
        parts.append(arrowhead((24 + ux * 18, 24 + uy * 18), (24 + ux * 10, 24 + uy * 10), 6.6))
    shafts = union(line([(12, 24), (36, 24)], 4), line([(24, 12), (24, 36)], 4))
    return cast(union(shafts, *parts), 0, 1.4)


def crosshair():
    bars = [rect(22.4, 6, 25.6, 18.6, 0.4), rect(22.4, 29.4, 25.6, 42, 0.4), rect(6, 22.4, 18.6, 25.6, 0.4), rect(29.4, 22.4, 42, 25.6, 0.4)]
    return union(*bars, disc(24, 24, 2.2))


def plus_cell():
    return cast(union(rect(19.6, 8, 28.4, 40, 1.6), rect(8, 19.6, 40, 28.4, 1.6)), 0, 1.6)


def x_cursor():
    return cast(union(line([(12, 12), (36, 36)], 6), line([(36, 12), (12, 36)], 6)), 0.6, 1.4)


def pencil():
    body = cast(poly((33.2, 6.6), (41.4, 14.8), (17.2, 39), (9, 30.8)), 1.4, 0)
    nib = cast(poly((9, 30.8), (17.2, 39), (6, 42)), 0.8, 0)
    return union(body, nib)


def magnifier(sign):
    lens = ring(20, 20, 11, 4.6)
    handle = line([(28.4, 28.4), (40, 40)], 6.4, "round")
    shape = union(lens, handle, disc(20, 20, 8.7))
    return shape, sign


# ------------------------------------------------------------------- the set
def spinner_frame(i, n, cx, cy, r, w=3.6):
    """The notch's spinner: a 270 degree arc, turned i/n of a circle."""
    a0 = 360 * i / n
    a1 = a0 + 270
    pts = [(cx + r * math.sin(math.radians(a)), cy - r * math.cos(math.radians(a))) for a in [a0 + (a1 - a0) * k / 36 for k in range(37)]]
    return line(pts, w, "round")


def svg(shape_paths, extras="", glyph_paths=""):
    """One cursor picture: shadow, edge, fill, then any marks drawn on top in the edge colour."""
    body = ""
    for p in shape_paths:
        body += f'<path d="{p}" fill="#000" opacity="0.32" transform="translate(0.3 1.1)" filter="url(#s)"/>'
    for p in shape_paths:
        body += f'<path d="{p}" fill="{EDGE}" stroke="{EDGE}" stroke-width="2.6" stroke-linejoin="round"/>'
    for p in shape_paths:
        body += f'<path d="{p}" fill="{FILL}"/>'
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">'
            '<defs><filter id="s" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="1.1"/></filter></defs>'
            + body + glyph_paths + extras + "</svg>")


def marks(shape):
    return f'<path d="{d(shape)}" fill="{EDGE}"/>'


def cursors():
    """name -> (list of frames as svg strings, hotspot on the 48 grid, frame delay ms)"""
    C = {}
    tip = (6.6, 4.4)
    C["left_ptr"] = ([svg([d(dart())])], tip, 0)
    C["right_ptr"] = ([svg([d(dart().transform(-1, 0, 0, 1, 48, 0))])], (41.4, 4.4), 0)
    C["center_ptr"] = ([svg([d(upright_dart())])], (24, 4.4), 0)
    C["wayland-cursor"] = C["left_ptr"]

    def with_badge(sign):
        disc_, glyph = badge(sign)
        return [svg([d(dart()), d(disc_)], glyph_paths=marks(glyph))]
    plus_sign = union(rect(33.6, 30.2, 36.4, 39.8, 0.6), rect(30.2, 33.6, 39.8, 36.4, 0.6))
    C["copy"] = (with_badge(plus_sign), tip, 0)
    C["dnd-copy"] = C["copy"]
    C["link"] = (with_badge(union(ring(31.8, 35, 2.6, 1.8), ring(38.2, 35, 2.6, 1.8), line([(33, 35), (37, 35)], 1.8))), tip, 0)
    C["dnd-link"] = C["link"]
    q = union(minus(ring(35, 32.6, 2.8, 1.9), rect(30, 33, 34.4, 40)), line([(35, 35.4), (35, 37)], 1.9), disc(35, 39.2, 1.1))
    C["question_arrow"] = (with_badge(q), tip, 0)
    C["dnd-ask"] = C["question_arrow"]
    menu = union(rect(31, 31.4, 39, 33, 0.6), rect(31, 34.2, 39, 35.8, 0.6), rect(31, 37, 36, 38.6, 0.6))
    C["context-menu"] = (with_badge(menu), tip, 0)
    no = union(ring(35, 35, 3.6, 1.6), line([(32.6, 32.6), (37.4, 37.4)], 1.6))
    C["dnd_no_drop"] = (with_badge(no), tip, 0)

    C["hand2"] = ([svg([d(pointing_hand())])], (21.9, 5.6), 0)
    C["hand1"] = ([svg([d(open_hand())])], (24, 24), 0)
    C["grabbing"] = ([svg([d(closed_hand())])], (24, 24), 0)
    C["xterm"] = ([svg([d(ibeam())])], (24, 24), 0)
    C["vertical-text"] = ([svg([d(ibeam(True))])], (24, 24), 0)
    C["pencil"] = ([svg([d(pencil())])], (6.6, 41.4), 0)

    C["sb_h_double_arrow"] = ([svg([d(double_arrow(0))])], (24, 24), 0)
    C["sb_v_double_arrow"] = ([svg([d(double_arrow(90))])], (24, 24), 0)
    C["bd_double_arrow"] = ([svg([d(double_arrow(45))])], (24, 24), 0)
    C["fd_double_arrow"] = ([svg([d(double_arrow(-45))])], (24, 24), 0)
    for name, angle in (("sb_right_arrow", 0), ("sb_down_arrow", 90), ("sb_left_arrow", 180), ("sb_up_arrow", 270)):
        C[name] = ([svg([d(single_arrow(angle))])], (24, 24), 0)
    # window edges and corners resize along their own axis
    for name, angle in (("top_side", 90), ("bottom_side", 90), ("left_side", 0), ("right_side", 0),
                        ("top_left_corner", 45), ("bottom_right_corner", 45), ("top_right_corner", -45), ("bottom_left_corner", -45)):
        C[name] = C["sb_v_double_arrow" if angle == 90 else "sb_h_double_arrow" if angle == 0 else "bd_double_arrow" if angle == 45 else "fd_double_arrow"]
    C["move"] = ([svg([d(four_way())])], (24, 24), 0)
    C["pointer-move"] = C["move"]

    cross = ([svg([d(crosshair())])], (24, 24), 0)
    for name in ("crosshair", "cross", "tcross", "dotbox", "top_tee", "bottom_tee", "left_tee", "right_tee", "ul_angle", "ur_angle", "ll_angle", "lr_angle"):
        C[name] = cross
    C["plus"] = ([svg([d(plus_cell())])], (24, 24), 0)
    ring_slash = union(ring(24, 24, 14.4, 5), minus(line([(13.8, 13.8), (34.2, 34.2)], 5), minus(disc(24, 24, 30), disc(24, 24, 16.6))))
    C["crossed_circle"] = ([svg([d(ring_slash)])], (24, 24), 0)
    C["circle"] = C["crossed_circle"]
    C["X_cursor"] = ([svg([d(x_cursor())])], (24, 24), 0)
    for name, sign in (("zoom-in", union(rect(18.6, 15, 21.4, 25, 0.6), rect(15, 18.6, 25, 21.4, 0.6))), ("zoom-out", rect(15, 18.6, 25, 21.4, 0.6))):
        shape, mark = magnifier(sign)
        C[name] = ([svg([d(shape)], glyph_paths=marks(mark))], (20, 20), 0)

    # busy: the notch's spinner, turning; progress: the pointer with it
    n = 18
    C["wait"] = ([svg([d(spinner_frame(i, n, 24, 24, 9, 4.4))]) for i in range(n)], (24, 24), 50)
    C["left_ptr_watch"] = ([svg([d(dart()), d(spinner_frame(i, n, 36, 36, 5.4, 3.2))]) for i in range(n)], tip, 50)
    return C


# ------------------------------------------------------------------- the links (as the freedesktop set names them)
LINKS = {
    "default": "left_ptr", "arrow": "left_ptr", "top_left_arrow": "left_ptr", "progress": "left_ptr_watch", "wait": None,
    "watch": "wait", "pointer": "hand2", "pointing_hand": "hand2", "grab": "hand1", "openhand": "hand1", "closedhand": "grabbing",
    "dnd-move": "grabbing", "dnd-none": "grabbing", "text": "xterm", "ibeam": "xterm", "help": "question_arrow",
    "left_ptr_help": "question_arrow", "whats_this": "question_arrow", "alias": "dnd-link", "not-allowed": "crossed_circle",
    "no-drop": "dnd_no_drop", "forbidden": "circle", "all-scroll": "move", "fleur": "move", "size_all": "move",
    "cell": "plus", "color-picker": "tcross", "cross_reverse": "cross", "diamond_cross": "cross", "target": "dotbox",
    "icon": "dotbox", "draped_box": "dotbox", "dot_box_mask": "dotbox", "draft": "pencil", "draft_large": "right_ptr",
    "draft_small": "right_ptr", "pirate": "X_cursor", "x-cursor": "X_cursor",
    "col-resize": "sb_h_double_arrow", "ew-resize": "sb_h_double_arrow", "h_double_arrow": "sb_h_double_arrow",
    "size-hor": "sb_h_double_arrow", "size_hor": "sb_h_double_arrow", "split_h": "sb_h_double_arrow",
    "row-resize": "sb_v_double_arrow", "ns-resize": "sb_v_double_arrow", "v_double_arrow": "sb_v_double_arrow",
    "double_arrow": "sb_v_double_arrow", "size-ver": "sb_v_double_arrow", "size_ver": "sb_v_double_arrow", "split_v": "sb_v_double_arrow",
    "nwse-resize": "bd_double_arrow", "size_fdiag": "bd_double_arrow", "nesw-resize": "fd_double_arrow", "size_bdiag": "fd_double_arrow",
    "n-resize": "top_side", "s-resize": "bottom_side", "e-resize": "right_side", "w-resize": "left_side",
    "ne-resize": "top_right_corner", "nw-resize": "top_left_corner", "se-resize": "bottom_right_corner", "sw-resize": "bottom_left_corner",
    "up-arrow": "sb_up_arrow", "down-arrow": "sb_down_arrow", "left-arrow": "sb_left_arrow", "right-arrow": "sb_right_arrow",
    "zoom-in": None, "zoom-out": None, "vertical-text": None, "context-menu": None, "copy": None, "link": None,
    # the hash names some toolkits ask for
    "00000000000000020006000e7e9ffc3f": "left_ptr_watch", "08e8e1c95fe2fc01f976f1e063a24ccd": "left_ptr_watch",
    "3ecb610c1bf2410f44200f48c40d3599": "left_ptr_watch", "00008160000006810000408080010102": "sb_v_double_arrow",
    "2870a09082c103050810ffdffffe0204": "sb_v_double_arrow", "028006030e0e7ebffc7f7070c0600140": "sb_h_double_arrow",
    "14fef782d02440884392942c1120523": "sb_h_double_arrow", "03b6e0fcb3499374a867c041f52298f0": "crossed_circle",
    "1081e37283d90000800003c07f3ef6bf": "copy", "6407b0e94181790501fd1e167b474872": "copy", "b66166c04f8c3109214a4fbd64a50fc8": "copy",
    "3085a0e285430894940527032f8b26df": "link", "640fb0e74195791501fd1ed57b41487f": "link", "a2a266d0498c3104214a47bd64ab0fc8": "link",
    "4498f0e0c1937ffe01fd06f973665830": "move", "9081237383d90e509aa00f00170e968f": "move",
    "5c6cd98b3f3ebcb1f9c7f1c204630408": "question_arrow", "d9ce0ab605698f320427677b458ad60b": "question_arrow",
    "9d800788f1b08800ae810202380a0822": "hand2", "e29285e634086352946a0e7090d73106": "hand2",
    "c7088f0f3e6c8088236ef8e1e3e70000": "bd_double_arrow", "fcf1c3c7cd4491d801f1e1c78f100000": "fd_double_arrow",
    "fcf21c00b30f7e3f83fe0dfd12e71cff": "grabbing",
}


# ------------------------------------------------------------------- masks
def render(svg_text, size, tmp):
    src, png = os.path.join(tmp, "c.svg"), os.path.join(tmp, "c.png")
    open(src, "w").write(svg_text)
    subprocess.run(["resvg", "-w", str(size), "-h", str(size), src, png], check=True)
    return Image.open(png).convert("RGBA")


def premultiplied_red(im):
    r, a = im.getchannel("R").tobytes(), im.getchannel("A").tobytes()
    return bytes(x * y // 255 for x, y in zip(r, a))


def masks(frame, size, tmp):
    """(opacity, accent share, edge share) per pixel, each a byte string; accent + edge never exceed opacity."""
    a_fill = render(frame.replace(FILL, "#fff").replace(EDGE, "#000"), size, tmp)
    a_edge = render(frame.replace(FILL, "#000").replace(EDGE, "#fff"), size, tmp)
    alpha = bytes(a_fill.getchannel("A").tobytes())
    wf, we = premultiplied_red(a_fill), premultiplied_red(a_edge)
    we = bytes(min(e, a - f) for a, f, e in zip(alpha, wf, we))
    return alpha, wf, we


def current_colours():
    c = json.load(open(os.path.expanduser("~/.local/state/quickshell/user/generated/colors.json")))
    return c["primary"], c["surface"]


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    fill, edge = current_colours()
    meta, blob, done = {"sizes": SIZES, "cursors": [], "links": {}}, bytearray(), {}
    with tempfile.TemporaryDirectory() as tmp:
        for name, (frames, hot, delay) in cursors().items():
            if id(frames) in done:
                meta["links"][name] = done[id(frames)]
                continue
            done[id(frames)] = name
            meta["cursors"].append({"name": name, "hot": hot, "delay": delay, "frames": len(frames)})
            for frame in frames:
                for size in SIZES:
                    for part in masks(frame, size, tmp):
                        blob += part
            render(frames[0].replace(FILL, fill).replace(EDGE, edge), 96, tmp).save(f"{OUT}/{name}.png")
    for name, target in LINKS.items():
        if target and name not in meta["links"] and name not in done.values():
            meta["links"][name] = target
    head = json.dumps(meta).encode()
    open(f"{OUT}/masks.bin", "wb").write(struct.pack("<I", len(head)) + head + zlib.compress(bytes(blob), 9))
    print(len(meta["cursors"]), "shapes,", len(meta["links"]), "links,", os.path.getsize(f"{OUT}/masks.bin") // 1024, "KiB")
    if "--paint" in sys.argv:
        subprocess.run([sys.executable, "paint.py", "--masks", f"{OUT}/masks.bin", "--fill", fill, "--edge", edge], check=True)

#!/usr/bin/env python3
"""Paints Tacit's cursor theme in two colours from the masks cursors.py made (stdlib only).

Run by matugen after a wallpaper change (the tacit_cursor template's post_hook, ~/.config/matugen/config.toml): it reads
the accent and ground that template wrote, writes the theme beside the old one, swaps the two, and tells Hyprland.
Apps already open keep the cursor they loaded until they are opened again.

    tacit-cursor-paint [--conf file | --fill #rrggbb --edge #rrggbb] [--masks file] [--out dir] [--force]
"""
import json
import os
import shutil
import struct
import subprocess
import sys
import zlib

HOME = os.path.expanduser("~")
# the person's own masks (cursors.py writes them there), else the ones the tacit-icons package ships
MASKS = f"{HOME}/.local/share/tacit-cursor/masks.bin"
if not os.path.exists(MASKS):
    MASKS = "/usr/share/tacit/cursor/masks.bin"
CONF = f"{HOME}/.local/state/quickshell/user/generated/tacit-cursor.conf"
OUT = f"{HOME}/.local/share/icons/Tacit"


def size():
    """The size Tacit Settings chose: it writes gsettings cursor-size (the login line reads the same)."""
    try:
        out = subprocess.run(["gsettings", "get", "org.gnome.desktop.interface", "cursor-size"], capture_output=True, text=True).stdout
        return int(out.split()[-1])
    except (OSError, ValueError, IndexError):
        return int(os.environ.get("XCURSOR_SIZE") or 24)


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def rgb(hexcode):
    h = hexcode.strip().lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def channel(share_fill, share_edge, fill, edge):
    """One premultiplied channel for every pixel at once: fill * accent share + edge * edge share. The two products
    never sum past 255 (the shares never pass the opacity), so they add as one big integer without carries."""
    a = share_fill.translate(bytes(fill * w // 255 for w in range(256)))
    b = share_edge.translate(bytes(edge * w // 255 for w in range(256)))
    n = len(a)
    return (int.from_bytes(a, "big") + int.from_bytes(b, "big")).to_bytes(n, "big")


def main():
    colours = {}
    conf = arg("--conf", CONF)
    if os.path.exists(conf):
        for ln in open(conf):
            if "=" in ln and not ln.startswith("#"):
                k, v = ln.strip().split("=", 1)
                colours[k] = v
    fill, edge = arg("--fill", colours.get("fill")), arg("--edge", colours.get("edge"))
    if not fill or not edge:
        sys.exit("tacit-cursor-paint: no colours (" + conf + ")")
    out = arg("--out", OUT)
    stamp = f"{fill} {edge}\n"
    if "--force" not in sys.argv and os.path.exists(f"{out}/colours") and open(f"{out}/colours").read() == stamp:
        return

    data = open(arg("--masks", MASKS), "rb").read()
    n = struct.unpack("<I", data[:4])[0]
    meta = json.loads(data[4:4 + n])
    blob = zlib.decompress(data[4 + n:])
    (fr, fg, fb), (er, eg, eb) = rgb(fill), rgb(edge)

    new = out + ".new"
    shutil.rmtree(new, ignore_errors=True)
    os.makedirs(f"{new}/cursors")
    pos = 0
    for c in meta["cursors"]:
        images = []
        for _ in range(c["frames"]):
            for size in meta["sizes"]:
                px = size * size
                alpha, wf, we = (blob[pos + k * px:pos + (k + 1) * px] for k in range(3))
                pos += 3 * px
                argb = bytearray(4 * px)  # little-endian ARGB words: B, G, R, A
                argb[0::4] = channel(wf, we, fb, eb)
                argb[1::4] = channel(wf, we, fg, eg)
                argb[2::4] = channel(wf, we, fr, er)
                argb[3::4] = alpha
                hx = min(size - 1, round(c["hot"][0] * size / 48))
                hy = min(size - 1, round(c["hot"][1] * size / 48))
                images.append((size, struct.pack("<9I", 36, 0xFFFD0002, size, 1, size, size, hx, hy, c["delay"]) + bytes(argb)))
        toc, chunks, offset = b"", b"", 16 + len(images) * 12
        for size, chunk in images:
            toc += struct.pack("<III", 0xFFFD0002, size, offset + len(chunks))
            chunks += chunk
        open(f"{new}/cursors/{c['name']}", "wb").write(struct.pack("<4sIII", b"Xcur", 16, 0x10000, len(images)) + toc + chunks)
    for name, target in meta["links"].items():
        os.symlink(target, f"{new}/cursors/{name}")
    open(f"{new}/index.theme", "w").write("[Icon Theme]\nName=Tacit\nComment=Tacit's cursor, painted from the wallpaper's accent\nInherits=Adwaita\n")
    open(f"{new}/colours", "w").write(stamp)

    # swap: the old theme stays whole until the new one is in place
    old = out + ".old"
    shutil.rmtree(old, ignore_errors=True)
    if os.path.exists(out):
        os.rename(out, old)
    os.rename(new, out)
    shutil.rmtree(old, ignore_errors=True)
    if "--out" not in sys.argv:
        subprocess.run(["hyprctl", "setcursor", "Tacit", str(size())], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()

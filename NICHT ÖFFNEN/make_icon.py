# -*- coding: utf-8 -*-
"""
Erzeugt kat.ico (Logo fuer KAT) - reine Standardbibliothek, keine Pakete.
Motiv: dunkler Katzenkopf mit leuchtenden, wachen Augen auf Farbverlauf.
       (KAT -> Katze, wache Augen -> bleibt wach). Nochmal ausfuehren, um
       Farben/Form oben anzupassen.
"""
import os
import struct
import zlib

M = 768                       # Master-Aufloesung
SIZES = [256, 64, 32, 16]     # im .ico enthaltene Groessen

# ------------------------------- Palette -----------------------------------
TOP   = (139, 92, 246)        # Violett (oben)
BOT   = (37, 99, 235)         # Blau (unten)
SIL   = (14, 17, 32)          # Katzen-Silhouette (fast schwarz, blaustichig)
EYE   = (52, 255, 184)        # leuchtendes Mintgruen (Augen)
PUP   = (7, 9, 16)            # Pupille
HI    = (236, 255, 248)       # Glanzpunkt im Auge
GLOW  = (52, 255, 184)        # Glanz/Glow-Farbe

# ------------------------------- Geometrie ---------------------------------
m = float(M)
x0, y0, x1, y1 = 0.04 * m, 0.04 * m, 0.96 * m, 0.96 * m
R = 0.24 * m
corners = [(x0 + R, y0 + R), (x1 - R, y0 + R), (x0 + R, y1 - R), (x1 - R, y1 - R)]

cx, cy, hr = 0.50 * m, 0.575 * m, 0.275 * m         # Gesichtskreis
L_EAR = [(0.275 * m, 0.105 * m), (0.215 * m, 0.45 * m), (0.50 * m, 0.33 * m)]
R_EAR = [(0.725 * m, 0.105 * m), (0.785 * m, 0.45 * m), (0.50 * m, 0.33 * m)]

eye_dy = cy - 0.025 * m
eye_dx = 0.118 * m
eye_rx, eye_ry = 0.072 * m, 0.108 * m
pup_rx, pup_ry = 0.024 * m, 0.088 * m
hi_r = 0.024 * m
glow_r = 0.20 * m


def inside_rounded(x, y):
    if x0 <= x <= x1 and y0 + R <= y <= y1 - R:
        return True
    if x0 + R <= x <= x1 - R and y0 <= y <= y1:
        return True
    for ccx, ccy in corners:
        if (x - ccx) ** 2 + (y - ccy) ** 2 <= R * R:
            return True
    return False


def in_tri(x, y, t):
    (ax, ay), (bx, by), (cx_, cy_) = t
    d1 = (x - bx) * (ay - by) - (ax - bx) * (y - by)
    d2 = (x - cx_) * (by - cy_) - (bx - cx_) * (y - cy_)
    d3 = (x - ax) * (cy_ - ay) - (cx_ - ax) * (y - ay)
    neg = d1 < 0 or d2 < 0 or d3 < 0
    pos = d1 > 0 or d2 > 0 or d3 > 0
    return not (neg and pos)


def in_ellipse(x, y, ex, ey, rx, ry):
    return ((x - ex) / rx) ** 2 + ((y - ey) / ry) ** 2 <= 1.0


def render_master():
    buf = bytearray(M * M * 4)
    for y in range(M):
        fy = y + 0.5
        for x in range(M):
            fx = x + 0.5
            i = (y * M + x) * 4
            if not inside_rounded(fx, fy):
                continue
            # Hintergrund-Verlauf (diagonal)
            t = (fx + fy) / (2.0 * m)
            r = int(TOP[0] + (BOT[0] - TOP[0]) * t)
            g = int(TOP[1] + (BOT[1] - TOP[1]) * t)
            b = int(TOP[2] + (BOT[2] - TOP[2]) * t)

            # Katzen-Silhouette (Gesicht + zwei Ohren)
            in_face = (fx - cx) ** 2 + (fy - cy) ** 2 <= hr * hr
            if in_face or in_tri(fx, fy, L_EAR) or in_tri(fx, fy, R_EAR):
                r, g, b = SIL

            # Augen
            le = in_ellipse(fx, fy, cx - eye_dx, eye_dy, eye_rx, eye_ry)
            re = in_ellipse(fx, fy, cx + eye_dx, eye_dy, eye_rx, eye_ry)
            if le or re:
                r, g, b = EYE
                ex = cx - eye_dx if le else cx + eye_dx
                # Schlitz-Pupille
                if in_ellipse(fx, fy, ex, eye_dy, pup_rx, pup_ry):
                    r, g, b = PUP
                # Glanzpunkt
                if (fx - (ex + 0.02 * m)) ** 2 + (fy - (eye_dy - 0.045 * m)) ** 2 <= hi_r * hi_r:
                    r, g, b = HI

            # Glow rund um die Augen (additiv)
            for ex in (cx - eye_dx, cx + eye_dx):
                d = ((fx - ex) ** 2 + (fy - eye_dy) ** 2) ** 0.5
                if d < glow_r:
                    s = (1.0 - d / glow_r) ** 2 * 0.55
                    r = min(255, int(r + GLOW[0] * s))
                    g = min(255, int(g + GLOW[1] * s))
                    b = min(255, int(b + GLOW[2] * s))

            buf[i] = r
            buf[i + 1] = g
            buf[i + 2] = b
            buf[i + 3] = 255
    return buf


def downsample(master, size):
    f = M // size
    out = bytearray(size * size * 4)
    n = f * f
    for ty in range(size):
        for tx in range(size):
            ar = ag = ab = aa = 0
            for sy in range(ty * f, (ty + 1) * f):
                base = (sy * M + tx * f) * 4
                for sx in range(f):
                    i = base + sx * 4
                    a = master[i + 3]
                    ar += master[i] * a
                    ag += master[i + 1] * a
                    ab += master[i + 2] * a
                    aa += a
            o = (ty * size + tx) * 4
            if aa > 0:
                out[o] = ar // aa
                out[o + 1] = ag // aa
                out[o + 2] = ab // aa
            out[o + 3] = aa // n
    return out


def png_bytes(w, h, rgba):
    def chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xffffffff))
    raw = bytearray()
    stride = w * 4
    for y in range(h):
        raw.append(0)
        raw.extend(rgba[y * stride:(y + 1) * stride])
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(bytes(raw), 9))
            + chunk(b'IEND', b''))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    master = render_master()

    images = []
    for s in SIZES:
        images.append((s, png_bytes(s, s, downsample(master, s))))

    # Vorschau (groesste Variante) als PNG
    with open(os.path.join(here, "kat_preview.png"), "wb") as f:
        f.write(images[0][1])

    # ICO zusammenbauen (PNG-Payloads, Vista+)
    n = len(images)
    header = struct.pack("<HHH", 0, 1, n)
    entries = b""
    offset = 6 + 16 * n
    for s, data in images:
        bw = 0 if s >= 256 else s
        entries += struct.pack("<BBBBHHII", bw, bw, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    with open(os.path.join(here, "kat.ico"), "wb") as f:
        f.write(header + entries + b"".join(d for _, d in images))

    print("kat.ico + kat_preview.png erstellt")


if __name__ == "__main__":
    main()

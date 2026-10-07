#!/usr/bin/env python3
"""Genera ``tools/windows/libreria.ico``, l'icona del collegamento sul desktop.

Solo libreria standard (``zlib``, ``struct``), output deterministico: lo stesso
script produce sempre lo stesso file, cosi' l'icona committata e' riproducibile.

Uso::

    python tools/windows/make_icon.py            # scrive libreria.ico accanto allo script
    python tools/windows/make_icon.py --out X.ico
    python tools/windows/make_icon.py --check    # non scrive: verifica che libreria.ico sia aggiornato

Disegno (procedurale, geometrico, leggibile anche a 16-32 px): quadrato blu
scuro con angoli arrotondati, quattro candele (verdi e rosse) e una spezzata
chiara ascendente che termina con un punto. L'immagine e' disegnata a 512x512
e ridotta con filtro a media (box filter) a 256, 48, 32 e 16 px; le quattro
immagini sono salvate come PNG dentro un ICO (formato Vista+: ICONDIR +
ICONDIRENTRY per immagine + dati PNG).

Funzioni riutilizzabili dai test: :func:`render_master`, :func:`downscale`,
:func:`encode_png`, :func:`build_ico`, :func:`parse_ico`.
"""

from __future__ import annotations

import argparse
import struct
import sys
import zlib
from pathlib import Path

ICON_SIZES = (256, 48, 32, 16)
MASTER = 512          # risoluzione di disegno (2x rispetto alla piu' grande)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# Colori RGBA
BG_TOP = (38, 72, 120, 255)
BG_BOTTOM = (20, 42, 76, 255)
GREEN = (84, 214, 160, 255)
RED = (242, 122, 110, 255)
LINE = (246, 249, 253, 255)

# Geometria in coordinate 256x256 (y verso il basso); viene scalata a MASTER.
ROUNDED_RECT = (10, 10, 246, 246, 46)                 # x0, y0, x1, y1, raggio
# Candele: (centro x, inizio corpo, fine corpo, inizio stoppino, fine stoppino, colore)
CANDLES = (
    (62, 176, 198, 166, 208, RED),
    (104, 148, 184, 138, 194, GREEN),
    (146, 160, 180, 150, 190, RED),
    (188, 108, 152, 96, 162, GREEN),
)
CANDLE_BODY_W = 20
CANDLE_WICK_W = 5
# Spezzata ascendente (4 segmenti) e punto finale
LINE_POINTS = ((36, 206), (88, 150), (128, 170), (174, 102), (222, 60))
LINE_WIDTH = 15
DOT_RADIUS = 13

Pixel = tuple[int, int, int, int]
Image = list[list[Pixel]]


# ----------------------------------------------------------------------------
# Disegno
# ----------------------------------------------------------------------------

def _blend(dst: Pixel, src: Pixel) -> Pixel:
    """Composizione "source over" di ``src`` su ``dst`` (alpha 0-255)."""
    sa = src[3]
    if sa >= 255:
        return src
    if sa <= 0:
        return dst
    da = dst[3]
    out_a = sa + da * (255 - sa) // 255
    if out_a == 0:
        return (0, 0, 0, 0)
    out = []
    for i in range(3):
        c = (src[i] * sa + dst[i] * da * (255 - sa) // 255) // out_a
        out.append(max(0, min(255, c)))
    return (out[0], out[1], out[2], out_a)


def _inside_rounded_rect(x: float, y: float, rect: tuple[float, float, float, float, float]) -> bool:
    x0, y0, x1, y1, r = rect
    if x < x0 or x > x1 or y < y0 or y > y1:
        return False
    # angoli: fuori se oltre il raggio dal centro dell'arco
    cx = x0 + r if x < x0 + r else (x1 - r if x > x1 - r else x)
    cy = y0 + r if y < y0 + r else (y1 - r if y > y1 - r else y)
    dx, dy = x - cx, y - cy
    return dx * dx + dy * dy <= r * r


def _dist_point_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    vx, vy = bx - ax, by - ay
    wx, wy = px - ax, py - ay
    seg_len2 = vx * vx + vy * vy
    if seg_len2 == 0:
        t = 0.0
    else:
        t = max(0.0, min(1.0, (wx * vx + wy * vy) / seg_len2))
    cx, cy = ax + t * vx, ay + t * vy
    dx, dy = px - cx, py - cy
    return (dx * dx + dy * dy) ** 0.5


def render_master(size: int = MASTER) -> Image:
    """Disegna l'icona a ``size`` x ``size`` pixel (RGBA, liste di tuple)."""
    s = size / 256.0
    x0, y0, x1, y1, r = ROUNDED_RECT
    rect = (x0 * s, y0 * s, x1 * s, y1 * s, r * s)
    top_y, bottom_y = y0 * s, y1 * s

    img: Image = [[(0, 0, 0, 0)] * size for _ in range(size)]

    # 1) sfondo: quadrato arrotondato con leggero gradiente verticale
    for y in range(size):
        py = y + 0.5
        t = 0.0 if bottom_y == top_y else max(0.0, min(1.0, (py - top_y) / (bottom_y - top_y)))
        bg = tuple(int(round(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t)) for i in range(4))
        row = img[y]
        for x in range(size):
            if _inside_rounded_rect(x + 0.5, py, rect):
                row[x] = bg  # type: ignore[assignment]

    # 2) candele: stoppino sottile + corpo pieno (rettangoli)
    def fill_rect(ax: float, ay: float, bx: float, by: float, color: Pixel) -> None:
        xs, xe = int(ax * s), int(round(bx * s))
        ys, ye = int(ay * s), int(round(by * s))
        for yy in range(max(0, ys), min(size, ye)):
            row = img[yy]
            for xx in range(max(0, xs), min(size, xe)):
                row[xx] = _blend(row[xx], color)

    for cx, body_a, body_b, wick_a, wick_b, color in CANDLES:
        fill_rect(cx - CANDLE_WICK_W / 2, wick_a, cx + CANDLE_WICK_W / 2, wick_b, color)
        fill_rect(cx - CANDLE_BODY_W / 2, body_a, cx + CANDLE_BODY_W / 2, body_b, color)

    # 3) spezzata ascendente con estremita' arrotondate + punto finale
    half = LINE_WIDTH * s / 2.0
    segments = list(zip(LINE_POINTS[:-1], LINE_POINTS[1:]))
    dot_x, dot_y = LINE_POINTS[-1][0] * s, LINE_POINTS[-1][1] * s
    dot_r = DOT_RADIUS * s
    min_x = min(p[0] for p in LINE_POINTS) * s - dot_r - half
    max_x = max(p[0] for p in LINE_POINTS) * s + dot_r + half
    min_y = min(p[1] for p in LINE_POINTS) * s - dot_r - half
    max_y = max(p[1] for p in LINE_POINTS) * s + dot_r + half
    for y in range(max(0, int(min_y)), min(size, int(max_y) + 1)):
        py = y + 0.5
        row = img[y]
        for x in range(max(0, int(min_x)), min(size, int(max_x) + 1)):
            px = x + 0.5
            dx, dy = px - dot_x, py - dot_y
            hit = dx * dx + dy * dy <= dot_r * dot_r
            if not hit:
                for (ax, ay), (bx, by) in segments:
                    if _dist_point_segment(px, py, ax * s, ay * s, bx * s, by * s) <= half:
                        hit = True
                        break
            if hit:
                row[x] = LINE
    return img


def downscale(img: Image, new_size: int) -> Image:
    """Riduce un'immagine quadrata a ``new_size`` con media per area (box filter).

    La media dei colori e' pesata con l'alpha (premoltiplicata) per evitare
    bordi scuri dove lo sfondo e' trasparente.
    """
    size = len(img)
    if new_size == size:
        return [list(row) for row in img]
    out: Image = []
    for dy in range(new_size):
        ys = dy * size // new_size
        ye = max(ys + 1, (dy + 1) * size // new_size)
        row_out: list[Pixel] = []
        for dx in range(new_size):
            xs = dx * size // new_size
            xe = max(xs + 1, (dx + 1) * size // new_size)
            n = 0
            sum_r = sum_g = sum_b = sum_a = 0
            for yy in range(ys, ye):
                row = img[yy]
                for xx in range(xs, xe):
                    r, g, b, a = row[xx]
                    sum_r += r * a
                    sum_g += g * a
                    sum_b += b * a
                    sum_a += a
                    n += 1
            if sum_a == 0:
                row_out.append((0, 0, 0, 0))
            else:
                row_out.append((
                    (sum_r + sum_a // 2) // sum_a,
                    (sum_g + sum_a // 2) // sum_a,
                    (sum_b + sum_a // 2) // sum_a,
                    (sum_a + n // 2) // n,
                ))
        out.append(row_out)
    return out


# ----------------------------------------------------------------------------
# Codifica PNG e ICO
# ----------------------------------------------------------------------------

def _png_chunk(kind: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(kind + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)


def encode_png(img: Image) -> bytes:
    """Codifica un'immagine RGBA 8 bit in PNG (filtro 0 per ogni riga)."""
    height = len(img)
    width = len(img[0]) if height else 0
    raw = bytearray()
    for row in img:
        raw.append(0)
        for r, g, b, a in row:
            raw += bytes((r, g, b, a))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    idat = zlib.compress(bytes(raw), 9)
    return PNG_SIGNATURE + _png_chunk(b"IHDR", ihdr) + _png_chunk(b"IDAT", idat) + _png_chunk(b"IEND", b"")


def build_ico(pngs: list[tuple[int, bytes]]) -> bytes:
    """Assembla un ICO con una voce per ogni ``(dimensione, dati PNG)``."""
    count = len(pngs)
    header = struct.pack("<HHH", 0, 1, count)
    offset = 6 + 16 * count
    entries = bytearray()
    body = bytearray()
    for size, data in pngs:
        dim = 0 if size >= 256 else size   # 0 significa 256 nel formato ICO
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(data), offset)
        body += data
        offset += len(data)
    return header + bytes(entries) + bytes(body)


def parse_ico(data: bytes) -> list[dict]:
    """Legge l'intestazione di un ICO e restituisce una voce per immagine.

    Ogni voce e' un dict con ``width``, ``height`` (0 letto come 256), ``size``,
    ``offset``, ``is_png`` e, se PNG, ``png_width``/``png_height`` dall'IHDR.
    Solleva ``ValueError`` se il file non e' un ICO.
    """
    if len(data) < 6:
        raise ValueError("file troppo corto per essere un ICO")
    reserved, kind, count = struct.unpack("<HHH", data[:6])
    if reserved != 0 or kind != 1:
        raise ValueError("intestazione ICO non valida")
    if len(data) < 6 + 16 * count:
        raise ValueError("directory ICO troncata")
    entries = []
    for i in range(count):
        off = 6 + 16 * i
        w, h, _colors, _res, _planes, _bpp, size, offset = struct.unpack("<BBBBHHII", data[off:off + 16])
        blob = data[offset:offset + size]
        if len(blob) != size:
            raise ValueError(f"immagine {i}: dati fuori dal file")
        entry = {
            "width": w or 256,
            "height": h or 256,
            "size": size,
            "offset": offset,
            "is_png": blob.startswith(PNG_SIGNATURE),
        }
        if entry["is_png"] and len(blob) >= 24:
            entry["png_width"], entry["png_height"] = struct.unpack(">II", blob[16:24])
        entries.append(entry)
    return entries


def make_ico_bytes() -> bytes:
    """Disegna, riduce e assembla l'icona completa (deterministico)."""
    master = render_master(MASTER)
    pngs: list[tuple[int, bytes]] = []
    base = downscale(master, 256)
    for size in ICON_SIZES:
        img = base if size == 256 else downscale(base, size)
        pngs.append((size, encode_png(img)))
    return build_ico(pngs)


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="make_icon.py",
        description="Genera libreria.ico (solo libreria standard).",
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="help", help="mostra questo messaggio di aiuto ed esce")
    parser.add_argument("--out", default=None, help="file ICO da scrivere (default: libreria.ico accanto allo script)")
    parser.add_argument("--check", action="store_true", help="non scrive: esce con 1 se il file è assente o diverso")
    args = parser.parse_args(argv)
    out = Path(args.out) if args.out else Path(__file__).resolve().parent / "libreria.ico"

    data = make_ico_bytes()
    if args.check:
        if not out.exists():
            print(f"ERRORE: {out} non esiste; esegui: python tools/windows/make_icon.py")
            return 1
        if out.read_bytes() != data:
            print(f"ERRORE: {out} non e' aggiornato; esegui: python tools/windows/make_icon.py")
            return 1
        print(f"OK: {out} aggiornato ({len(data)} byte, {len(ICON_SIZES)} immagini).")
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    sizes = ", ".join(f"{s}x{s}" for s in ICON_SIZES)
    print(f"Scritto {out} ({len(data)} byte, immagini PNG: {sizes}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

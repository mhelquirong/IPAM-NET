#!/usr/bin/env python3
"""
Generate the CODE brand asset set used by the netbox_code_branding plugin.

The single source of truth is ``logo-code.svg`` in the repository root: an SVG
wrapper around a 500x114 PNG of the CODE wordmark. This script derives every
other asset from it so the set can be regenerated if the source logo is ever
replaced:

  code-logo.svg           Full lockup for light backgrounds (source, unmodified)
  code-logo-dark.svg      Full lockup with the wordmark recoloured for dark UI
  code-logo-compact.svg   Mark + wordmark, no strapline (sidebar)
  code-logo-compact-dark.svg  Compact lockup for dark UI
  code-mark.svg           Vector-traced bar mark only (no wordmark)
  code-icon.svg           Square app icon: bar mark on the CODE navy field
  favicon.ico             16/32/48px multi-resolution icon
  code-touch-icon-180.png Apple touch icon
  code-icon-192.png       PWA icon
  code-icon-512.png       PWA icon

Usage:  python code_branding/tools/build_assets.py
"""

from __future__ import annotations

import base64
import io
import re
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_SVG = REPO_ROOT / 'logo-code.svg'
OUT_DIR = REPO_ROOT / 'code_branding' / 'netbox_code_branding' / 'static' / 'netbox_code_branding' / 'img'

# Brand palette: sampled from the pixels of logo-code.svg and cross-checked
# against the .colorBlue/.colorOne classes published on https://code.sa.
NAVY = '#221F33'
RED = '#D51C38'
ORANGE = '#F9863D'
CYAN = '#00AAC8'
BLUE = '#006EC6'

# Row of transparent pixels separating the wordmark from the strapline in the
# 500x114 source; the compact lockup is cut here.
COMPACT_CROP_Y = 77

# Bar geometry traced from the source PNG (origin shifted to the mark's bounding
# box, which is x=27..102, y=12..73 in the 500x114 source).
MARK_W, MARK_H = 75.0, 62.0
BAR_H = 8.6
ROW_TOPS = (0.0, 17.7, 35.3, 53.0)
# (row index, x, width, colour)
BARS = (
    (0, 0.0, 38.5, ORANGE),
    (0, 47.0, 28.0, RED),
    (1, 0.0, 48.5, RED),
    (1, 57.0, 18.0, ORANGE),
    (2, 0.0, 27.5, CYAN),
    (2, 35.0, 40.0, BLUE),
    (3, 0.0, 50.5, BLUE),
    (3, 59.5, 15.5, CYAN),
)


def load_source_png() -> Image.Image:
    """Decode the base64 PNG embedded in the source SVG."""
    svg = SOURCE_SVG.read_text(encoding='utf-8')
    match = re.search(r'base64,([A-Za-z0-9+/=]+)', svg)
    if not match:
        raise SystemExit(f'No embedded raster image found in {SOURCE_SVG}')
    return Image.open(io.BytesIO(base64.b64decode(match.group(1)))).convert('RGBA')


def recolour_wordmark(img: Image.Image, target: tuple[int, int, int]) -> Image.Image:
    """Recolour the dark navy wordmark while leaving the coloured bars alone.

    Anti-aliased edge pixels are handled by folding their darkness into the
    alpha channel, which keeps the letterforms smooth at any size.
    """
    src = img.load()

    def is_coloured(r: int, g: int, b: int) -> bool:
        mx, mn = max(r, g, b), min(r, g, b)
        return mx > 80 and (mx - mn) / mx > 0.30

    # The wordmark ink is navy rather than black, so raw darkness tops out well
    # short of 1.0. Normalise against the darkest neutral pixel present, or the
    # solid wordmark would come out a washed-out grey instead of white.
    darkest = 255
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = src[x, y]
            if a > 200 and not is_coloured(r, g, b):
                darkest = min(darkest, max(r, g, b))
    span = 1.0 - darkest / 255.0 or 1.0

    out = Image.new('RGBA', img.size, (0, 0, 0, 0))
    dst = out.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = src[x, y]
            if a == 0:
                continue
            if is_coloured(r, g, b):
                dst[x, y] = (r, g, b, a)  # coloured bar: keep as-is
            else:
                # Neutral ink: darker source pixel => more opaque target pixel.
                coverage = a * (1.0 - max(r, g, b) / 255.0) / span
                dst[x, y] = (*target, min(255, int(round(coverage))))
    return out


def png_to_svg(img: Image.Image, width: int, height: int) -> str:
    """Wrap a raster image in an SVG of the given display size."""
    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    data = base64.b64encode(buf.getvalue()).decode('ascii')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="CODE">'
        f'<image width="{width}" height="{height}" preserveAspectRatio="xMidYMid meet" '
        f'href="data:image/png;base64,{data}"/></svg>\n'
    )


def bar_rects(scale: float = 1.0, dx: float = 0.0, dy: float = 0.0, indent: str = '  ') -> str:
    rows = []
    for row, x, w, colour in BARS:
        rows.append(
            f'{indent}<rect x="{x * scale + dx:.2f}" y="{ROW_TOPS[row] * scale + dy:.2f}" '
            f'width="{w * scale:.2f}" height="{BAR_H * scale:.2f}" '
            f'rx="{BAR_H * scale / 2:.2f}" fill="{colour}"/>'
        )
    return '\n'.join(rows)


def build_mark_svg() -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {MARK_W:.0f} {MARK_H:.0f}" '
        f'role="img" aria-label="CODE">\n{bar_rects()}\n</svg>\n'
    )


def build_icon_svg(size: int = 512, pad_ratio: float = 0.20) -> str:
    """Square app icon: the bar mark centred on the CODE navy field."""
    pad = size * pad_ratio
    scale = (size - 2 * pad) / MARK_W
    dy = (size - MARK_H * scale) / 2
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'width="{size}" height="{size}" role="img" aria-label="CODE">\n'
        f'  <rect width="{size}" height="{size}" rx="{size * 0.22:.0f}" fill="{NAVY}"/>\n'
        f'{bar_rects(scale=scale, dx=pad, dy=dy)}\n</svg>\n'
    )


def rasterise_icon(size: int, pad_ratio: float = 0.20) -> Image.Image:
    """Render the square app icon without needing an SVG rasteriser.

    Drawn at 8x and downsampled, which gives clean anti-aliased edges. Favicon
    sizes pass a smaller ``pad_ratio`` so the bars stay legible at 16px.
    """
    from PIL import ImageDraw

    ss = 8
    big = size * ss
    img = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, big - 1, big - 1], radius=int(big * 0.22), fill=NAVY)

    pad = big * pad_ratio
    scale = (big - 2 * pad) / MARK_W
    dy = (big - MARK_H * scale) / 2
    for row, x, w, colour in BARS:
        x0 = pad + x * scale
        y0 = dy + ROW_TOPS[row] * scale
        h = BAR_H * scale
        draw.rounded_rectangle([x0, y0, x0 + w * scale, y0 + h], radius=h / 2, fill=colour)

    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source = load_source_png()

    # Full lockups. The source is preserved byte-for-byte for the light variant so
    # the supplied brand asset itself is what ships.
    (OUT_DIR / 'code-logo.svg').write_text(SOURCE_SVG.read_text(encoding='utf-8'), encoding='utf-8')
    dark = recolour_wordmark(source, (255, 255, 255))
    (OUT_DIR / 'code-logo-dark.svg').write_text(png_to_svg(dark, 184, 42), encoding='utf-8')

    # Compact lockup for the sidebar. At the ~30px the sidebar allows, the
    # strapline in the full lockup renders around 7px tall and turns to mush, so
    # the compact variant keeps only the mark and wordmark. The source has a
    # clean empty band at y=73..80 between the two, which is where it is cut.
    compact = source.crop((0, 0, source.width, COMPACT_CROP_Y))
    compact_h = round(184 * COMPACT_CROP_Y / source.width)
    (OUT_DIR / 'code-logo-compact.svg').write_text(
        png_to_svg(compact, 184, compact_h), encoding='utf-8'
    )
    (OUT_DIR / 'code-logo-compact-dark.svg').write_text(
        png_to_svg(dark.crop((0, 0, dark.width, COMPACT_CROP_Y)), 184, compact_h), encoding='utf-8'
    )

    # Vector mark and app icon.
    (OUT_DIR / 'code-mark.svg').write_text(build_mark_svg(), encoding='utf-8')
    (OUT_DIR / 'code-icon.svg').write_text(build_icon_svg(), encoding='utf-8')

    # Rasterised icons.
    rasterise_icon(180).save(OUT_DIR / 'code-touch-icon-180.png', optimize=True)
    rasterise_icon(192).save(OUT_DIR / 'code-icon-192.png', optimize=True)
    rasterise_icon(512).save(OUT_DIR / 'code-icon-512.png', optimize=True)
    # Favicons are rendered with tighter padding; at 16px the default 20% inset
    # leaves the bars too small to resolve.
    favicon = rasterise_icon(64, pad_ratio=0.10)
    favicon.save(OUT_DIR / 'favicon.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48)])
    (OUT_DIR / 'favicon.svg').write_text(build_icon_svg(size=64, pad_ratio=0.10), encoding='utf-8')

    for path in sorted(OUT_DIR.iterdir()):
        print(f'{path.name:28} {path.stat().st_size:>8,} bytes')


if __name__ == '__main__':
    main()

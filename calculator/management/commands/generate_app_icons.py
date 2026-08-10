import os
import math
import numpy as np
from django.conf import settings
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw

SIZE = 1024
MOLTEN = (255, 122, 69, 255)
ROSE = (242, 87, 143, 255)
WHITE = (255, 255, 255, 255)
BG_VOID = (16, 20, 26, 255)


def diagonal_gradient(size, color1, color2, angle_deg=135):
    w, h = size
    angle = math.radians(angle_deg)
    dx, dy = math.cos(angle), math.sin(angle)
    xs, ys = np.meshgrid(np.linspace(0, 1, w), np.linspace(0, 1, h))
    proj = xs * dx + ys * dy
    proj = (proj - proj.min()) / (proj.max() - proj.min())
    grad = np.zeros((h, w, 4), dtype=np.uint8)
    for c in range(4):
        grad[..., c] = (color1[c] + (color2[c] - color1[c]) * proj).astype(np.uint8)
    return Image.fromarray(grad, "RGBA")


def rounded_mask(size, box, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle(box, radius=radius, fill=255)
    return m


def build_calculator_icon(canvas_size, full_bleed=False):
    size = canvas_size
    gradient = diagonal_gradient(size, MOLTEN, ROSE, 135)

    if full_bleed:
        bg = gradient.copy()
    else:
        margin = int(size[0] * 0.045)
        corner_radius = int(size[0] * 0.22)
        mask = rounded_mask(size, [margin, margin, size[0] - margin, size[1] - margin], corner_radius)
        bg = Image.new("RGBA", size, (0, 0, 0, 0))
        bg.paste(gradient, (0, 0), mask)

    canvas = bg.copy()

    body_w, body_h = int(size[0] * 0.50), int(size[1] * 0.62)
    body_x0 = (size[0] - body_w) // 2
    body_y0 = (size[1] - body_h) // 2
    body_x1, body_y1 = body_x0 + body_w, body_y0 + body_h
    body_radius = int(body_w * 0.16)

    body_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(body_layer).rounded_rectangle(
        [body_x0, body_y0, body_x1, body_y1], radius=body_radius, fill=WHITE
    )
    canvas = Image.alpha_composite(canvas, body_layer)

    pad = int(body_w * 0.12)
    screen_x0 = body_x0 + pad
    screen_x1 = body_x1 - pad
    screen_y0 = body_y0 + pad
    screen_y1 = screen_y0 + int(body_h * 0.16)
    screen_radius = int(body_w * 0.05)
    screen_mask = rounded_mask(size, [screen_x0, screen_y0, screen_x1, screen_y1], screen_radius)
    canvas.paste(gradient, (0, 0), screen_mask)

    grid_top = screen_y1 + int(body_h * 0.09)
    grid_bottom = body_y1 - pad
    cols, rows = 3, 3
    gap = int(body_w * 0.06)
    grid_w = (body_x1 - pad) - (body_x0 + pad)
    grid_h = grid_bottom - grid_top
    cell_w = (grid_w - gap * (cols - 1)) / cols
    cell_h = (grid_h - gap * (rows - 1)) / rows
    btn_radius = int(min(cell_w, cell_h) * 0.28)

    for r in range(rows):
        for c in range(cols):
            x0 = body_x0 + pad + c * (cell_w + gap)
            y0 = grid_top + r * (cell_h + gap)
            x1 = x0 + cell_w
            y1 = y0 + cell_h
            m = rounded_mask(size, [x0, y0, x1, y1], btn_radius)
            canvas.paste(gradient, (0, 0), m)

    return canvas


def build_maskable(px):
    full = build_calculator_icon((SIZE, SIZE), full_bleed=True)
    canvas = Image.new("RGBA", (SIZE, SIZE), BG_VOID)
    inner = int(SIZE * 0.78)
    scaled = full.resize((inner, inner), Image.LANCZOS)
    offset = ((SIZE - inner) // 2, (SIZE - inner) // 2)
    canvas.paste(scaled, offset, scaled)
    return canvas.resize((px, px), Image.LANCZOS).convert("RGB")


def build_wide_tile(w_px, h_px):
    W, H = w_px * 4, h_px * 4
    canvas = Image.new("RGBA", (W, H), BG_VOID)
    inner_h = int(H * 0.86)
    square = build_calculator_icon((SIZE, SIZE), full_bleed=True).resize((inner_h, inner_h), Image.LANCZOS)
    x = (W - inner_h) // 2
    y = (H - inner_h) // 2
    canvas.paste(square, (x, y), square)
    return canvas.resize((w_px, h_px), Image.LANCZOS).convert("RGB")


ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ff7a45"/>
      <stop offset="100%" stop-color="#f2578f"/>
    </linearGradient>
  </defs>
  <rect x="4.5" y="4.5" width="91" height="91" rx="20" fill="url(#g)"/>
  <rect x="25" y="19" width="50" height="62" rx="8" fill="#ffffff"/>
  <rect x="31" y="27" width="38" height="12" rx="3" fill="url(#g)"/>
  <g fill="url(#g)">
    <rect x="31" y="45" width="10.5" height="10.5" rx="2.5"/>
    <rect x="44.75" y="45" width="10.5" height="10.5" rx="2.5"/>
    <rect x="58.5" y="45" width="10.5" height="10.5" rx="2.5"/>
    <rect x="31" y="58" width="10.5" height="10.5" rx="2.5"/>
    <rect x="44.75" y="58" width="10.5" height="10.5" rx="2.5"/>
    <rect x="58.5" y="58" width="10.5" height="10.5" rx="2.5"/>
    <rect x="31" y="71" width="10.5" height="7" rx="2.5"/>
    <rect x="44.75" y="71" width="10.5" height="7" rx="2.5"/>
    <rect x="58.5" y="71" width="10.5" height="7" rx="2.5"/>
  </g>
</svg>
"""

SAFARI_PINNED_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
<g fill="#000000">
  <rect x="25" y="19" width="50" height="62" rx="8"/>
</g>
</svg>
"""

BROWSERCONFIG_XML = """<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
    <msapplication>
        <tile>
            <square70x70logo src="/static/images/mstile-70x70.png"/>
            <square150x150logo src="/static/images/mstile-150x150.png"/>
            <wide310x150logo src="/static/images/mstile-310x150.png"/>
            <square310x310logo src="/static/images/mstile-310x310.png"/>
            <TileColor>#ff7a45</TileColor>
        </tile>
    </msapplication>
</browserconfig>
"""

SITE_WEBMANIFEST = """{
    "name": "PlastIQ",
    "short_name": "PlastIQ",
    "description": "Quality control and pricing tools for plastic film manufacturing",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#10141a",
    "theme_color": "#10141a",
    "orientation": "portrait-primary",
    "scope": "/",
    "categories": ["business", "productivity", "utilities"],
    "icons": [
        {
            "src": "/static/images/android-chrome-192x192.png",
            "sizes": "192x192",
            "type": "image/png",
            "purpose": "any maskable"
        },
        {
            "src": "/static/images/android-chrome-512x512.png",
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "any maskable"
        }
    ]
}
"""


class Command(BaseCommand):
    help = "Generate all PlastIQ app icons matching the navbar calculator mark."

    def add_arguments(self, parser):
        parser.add_argument('--out-dir', default=None)

    def handle(self, *args, **options):
        out_dir = options['out_dir'] or os.path.join(str(settings.BASE_DIR), 'static', 'images')
        os.makedirs(out_dir, exist_ok=True)

        def write(filename, fn):
            path = os.path.join(out_dir, filename)
            fn(path)
            self.stdout.write(self.style.SUCCESS(f"Wrote {path}"))

        master = build_calculator_icon((SIZE, SIZE), full_bleed=False)
        apple_master = build_calculator_icon((SIZE, SIZE), full_bleed=True).convert("RGB")

        def save_png(img, px, filename):
            write(filename, lambda p: img.resize((px, px), Image.LANCZOS).save(p))

        save_png(master, 16, "favicon-16x16.png")
        save_png(master, 32, "favicon-32x32.png")
        write("favicon.ico", lambda p: master.save(p, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)]))

        save_png(apple_master, 180, "apple-touch-icon.png")

        write("android-chrome-192x192.png", lambda p: build_maskable(192).save(p))
        write("android-chrome-512x512.png", lambda p: build_maskable(512).save(p))

        write("mstile-70x70.png", lambda p: apple_master.resize((70, 70), Image.LANCZOS).save(p))
        write("mstile-150x150.png", lambda p: apple_master.resize((150, 150), Image.LANCZOS).save(p))
        write("mstile-310x310.png", lambda p: apple_master.resize((310, 310), Image.LANCZOS).save(p))
        write("mstile-310x150.png", lambda p: build_wide_tile(310, 150).save(p))

        write("icon.svg", lambda p: open(p, "w", encoding="utf-8").write(ICON_SVG))
        write("safari-pinned-tab.svg", lambda p: open(p, "w", encoding="utf-8").write(SAFARI_PINNED_SVG))
        write("browserconfig.xml", lambda p: open(p, "w", encoding="utf-8").write(BROWSERCONFIG_XML))
        write("site.webmanifest", lambda p: open(p, "w", encoding="utf-8").write(SITE_WEBMANIFEST))

        self.stdout.write(self.style.SUCCESS("All PlastIQ icons generated successfully."))

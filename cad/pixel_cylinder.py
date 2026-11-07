"""Arcade pixel cylinder lamp shade - 6 in tall, fits over the 82.19 mm light ring.

The pattern comes from patterns/arcade_pixels.svg, a 90 x 57 pixel cardstock wrap
(9.425 in around plus a 0.25 in glue tab, 6 in tall). Each square pixel becomes a pocket cut
from the inside of a 3 mm wall, leaving a 0.8 mm skin, so the outside stays smooth and the
pixels glow through a dark wall.

The wrap is stretched around the circumference so the seam closes; height keeps the SVG's
1:1 scale. Because the shade is wider than the 3 in cardstock tube, pixels come out about
18% wider than they are tall.

Run:  uv run --python 3.12 --with build123d python cad/pixel_cylinder.py
"""
import math
import re
from pathlib import Path

from build123d import Align, Axis, Box, Compound, Cylinder, Location, export_step, export_stl

ROOT = Path(__file__).resolve().parent.parent
SVG = ROOT / "patterns" / "arcade_pixels.svg"

# --- parameters (mm) ---
height     = 6 * 25.4      # 152.4 overall; matches the SVG height 1:1
bore_r     = 42.0          # 84 mm ID: 0.9 mm/side clearance over the 82.19 mm ring
wall_t     = 3.0           # dark wall
skin_t     = 0.8           # glowing pixel skin (2 perimeters @ 0.4 nozzle)
wrap_in    = 9.425         # SVG width that wraps around (excludes the 0.25 in glue tab)
svg_h_in   = 6.0           # SVG height
pixel_grow = -0.1          # shrink pockets so column webs are 0.85 mm (2 clean perimeters)

r_out = bore_r + wall_t
r_skin = r_out - skin_t
IN = 25.4


def read_pixels(path):
    """(x, y, w, h) in inches for every square in the cut-pixels group."""
    svg = path.read_text()
    group = svg[svg.index('id="cut-pixels"'):]
    group = group[:group.index("</g>")]
    num = r"([-\d.]+)"
    return [tuple(map(float, m)) for m in re.findall(rf"M{num},{num}h{num}v{num}", group)]


def build():
    pixels = read_pixels(SVG)
    depth = r_skin - (bore_r - 1.0)          # pocket runs from inside the bore to the skin
    pockets = []
    for x, y, w, h in pixels:
        theta = (x + w / 2) / wrap_in * 360.0            # + x -> + theta reads correctly from outside
        z = (svg_h_in - (y + h / 2)) * IN                # SVG y runs down; CAD z runs up
        width = 2 * r_skin * math.sin(math.radians(w / wrap_in * 180.0)) + pixel_grow
        tall = h * IN + pixel_grow
        box = Box(depth, width, tall, align=(Align.MAX, Align.CENTER, Align.CENTER))
        pockets.append(box.move(Location((r_skin, 0, z))).rotate(Axis.Z, theta))

    up = (Align.CENTER, Align.CENTER, Align.MIN)
    tube = Cylinder(r_out, height, align=up) - Cylinder(bore_r, height + 2, align=up).move(Location((0, 0, -1)))
    return tube - Compound(pockets), pixels


if __name__ == "__main__":
    shade, pixels = build()
    out = ROOT / "out"
    out.mkdir(exist_ok=True)
    export_step(shade, str(out / "pixel_cylinder.step"))
    export_stl(shade, str(out / "pixel_cylinder.stl"), tolerance=0.02, angular_tolerance=0.2)
    p = pixels[0]
    print(f"pixels={len(pixels)} solids={len(shade.solids())} valid={shade.is_valid} volume={shade.volume:.0f} "
          f"pixel={2 * math.pi * r_out * p[2] / wrap_in:.2f}x{p[3] * IN:.2f}mm "
          f"pitch_h={2 * math.pi * r_out * 0.104722222 / wrap_in:.2f} pitch_v={0.105263158 * IN:.2f}")

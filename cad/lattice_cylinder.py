"""Lattice cylinder lamp shade - 6 in tall, fits over the 82.19 mm light ring.

A 3 mm tube with a diamond lattice cut into its outside. Three wall thicknesses give three
light levels:
  3.0 mm lattice ribs           darkest
  2.0 mm "jewel" diamond frames mid tone   (every other band of cells)
  0.8 mm windows                brightest (plain cells, and the centre of each jewel)

The pockets are flat-sided wedges whose side walls run along radial lines, intersected with a
cylinder so every pocket floor follows the bore. Cutting convex wedges is far faster than
fusing swept helical ribs, which is how the first version stalled.

Run:  uv run --python 3.12 --with build123d python cad/lattice_cylinder.py
"""
import math
from pathlib import Path

from build123d import (Align, Compound, ConvexPolyhedron, Cylinder, Location,
                       export_step, export_stl)

# --- parameters (mm) ---
height      = 6 * 25.4     # 152.4 overall
bore_r      = 42.0         # 84 mm ID: 0.9 mm/side clearance over the 82.19 mm ring
wall_t      = 0.8          # window wall (2 perimeters @ 0.4 nozzle)
jewel_t     = 2.0          # jewel frame wall
rib_t       = 3.0          # full wall (ribs, collar, rim)
collar_h    = 10.0         # solid base collar
rim_h       = 6.0          # solid top rim
columns     = 16           # diamonds around the circumference
cell_h      = 24.0         # diamond height (tip to tip)
rib_w       = 2.2          # rib width measured across the rib
jewel_scale = 0.45         # jewel window size relative to its cell
jewel_bands = (0, 1)       # half-rows (mod 4) that get jewels -> alternating bands

r_out = bore_r + rib_t
half_th = math.pi / columns              # diamond half-width as an angle
half_z = cell_h / 2
half_w = half_th * r_out                 # half-width as arc length on the outside
inradius = half_w * half_z / math.hypot(half_w, half_z)
rib_k = 1 - (rib_w / 2) / inradius       # inset that leaves rib_w between cells
up = (Align.CENTER, Align.CENTER, Align.MIN)


def wedge(theta, z, scale):
    """Diamond pocket centred at (theta, z), sides along radial lines."""
    corners = [(half_th * scale, 0), (0, half_z * scale), (-half_th * scale, 0), (0, -half_z * scale)]
    pts = []
    for r in (bore_r - 12, r_out + 2):
        for dth, dz in corners:
            pts.append((r * math.cos(theta + dth), r * math.sin(theta + dth), z + dz))
    return ConvexPolyhedron(pts)


def band(r_floor):
    """Annulus between the pocket floor and the outside, limited to the patterned zone."""
    zone = height - collar_h - rim_h
    a = Cylinder(r_out + 1, zone, align=up) - Cylinder(r_floor, zone + 1, align=up).move(Location((0, 0, -0.5)))
    return a.move(Location((0, 0, collar_h)))


def build():
    thin, mid = [], []
    # Whole diamonds only, centred in the patterned zone, so every pocket ceiling is a
    # sloped diamond tip (no flat ceilings under the rim that would need support).
    z_lo, z_hi = collar_h, height - rim_h
    tip = half_z * rib_k
    rows = int(((z_hi - z_lo) / 2 - tip) // (half_z / 2)) + 1   # half-rows that fit
    z_mid = (z_lo + z_hi) / 2
    for j in range(rows):
        z = z_mid + (j - (rows - 1) / 2) * half_z
        for s in range(2 * columns):
            if (j + s) % 2:
                continue                 # (j + s) even = cell centre; odd = rib crossing
            theta = s * half_th
            if j % 4 in jewel_bands:
                mid.append(wedge(theta, z, rib_k))
                thin.append(wedge(theta, z, rib_k * jewel_scale))
            else:
                thin.append(wedge(theta, z, rib_k))

    tube = Cylinder(r_out, height, align=up) - Cylinder(bore_r, height + 2, align=up).move(Location((0, 0, -1)))
    cut_mid = Compound(mid) & band(bore_r + jewel_t)
    cut_thin = Compound(thin) & band(bore_r + wall_t)
    shade = tube - cut_mid - cut_thin
    return shade, len(thin) - len(mid), len(mid)


if __name__ == "__main__":
    shade, n_plain, n_jewel = build()
    out = Path(__file__).resolve().parent.parent / "out"
    out.mkdir(exist_ok=True)
    export_step(shade, str(out / "lattice_cylinder.step"))
    export_stl(shade, str(out / "lattice_cylinder.stl"), tolerance=0.02, angular_tolerance=0.2)
    bb = shade.bounding_box()
    print(f"plain={n_plain} jewel={n_jewel} solids={len(shade.solids())} valid={shade.is_valid} "
          f"volume={shade.volume:.0f} bbox={bb.size.X:.2f}x{bb.size.Y:.2f}x{bb.size.Z:.2f}")

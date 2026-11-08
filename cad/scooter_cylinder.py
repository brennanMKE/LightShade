"""Scooter cylinder lamp shade - 6 in tall, fits over the 82.19 mm light ring.

The pattern comes from patterns/scooter.svg, a cardstock wrap (9.425 in around plus a 0.25 in
glue tab, 6 in tall) of scooters, helmets, a wheel and dots. Each shape becomes a pocket cut
from the inside of a thin wall, leaving an even thinner skin:

  skin under the shapes  0.8 mm  bright
  wall everywhere else   1.8 mm  still lets light through, just dimmer

Shapes are wrapped exactly onto the cylinder with Face.wrap, then thickened inward. The wrap
is stretched around the circumference so the seam closes; height keeps the SVG's 1:1 scale,
so shapes come out about 16% wider than drawn.

Run:  uv run --python 3.12 --with build123d python cad/scooter_cylinder.py
"""
import math
from pathlib import Path

from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps

from build123d import (Align, Compound, Cylinder, Face, GeomType, Location, Matrix, Plane,
                       Rectangle, Solid, Vector, export_step, export_stl, import_svg, thicken)

ROOT = Path(__file__).resolve().parent.parent
SVG = ROOT / "patterns" / "scooter.svg"

# --- parameters (mm) ---
height   = 6 * 25.4     # 152.4 overall; matches the SVG height 1:1
bore_r   = 42.0         # 84 mm ID: 0.9 mm/side clearance over the 82.19 mm ring
wall_t   = 1.8          # background wall (dim)
skin_t   = 0.8          # skin under the shapes (bright; 2 perimeters @ 0.4 nozzle)
wrap_w   = 9.425 * 25.4 # SVG width that wraps around (excludes the 0.25 in glue tab)
edge_min = 3.0          # solid band kept at the top and bottom edges
small_max = 12.0        # shapes up to this size are projected instead of wrapped

r_out = bore_r + wall_t
r_skin = r_out - skin_t
sx = 2 * math.pi * r_skin / wrap_w          # circumferential stretch so the seam closes
up = (Align.CENTER, Align.CENTER, Align.MIN)
skin_cyl = Cylinder(r_skin, height, align=up)


def flat_faces():
    """SVG shapes as faces in flat mm coords (x along the wrap, y down from the top edge),
    with holes cut, clipped to the wrap and the edge bands, and glue-tab overflow wrapped."""
    wires = [w for w in import_svg(SVG, flip_y=False, align=None)
             if w.is_closed and w.bounding_box().size.X < 200]          # drop outline/tab
    faces = [Face(w) for w in wires]
    # nested shapes are holes in their parent
    boxes = [f.bounding_box() for f in faces]

    def inside(a, b):
        """Face a lies inside face b."""
        ba, bb = boxes[a], boxes[b]
        if not (bb.min.X <= ba.min.X and ba.max.X <= bb.max.X and bb.min.Y <= ba.min.Y and ba.max.Y <= bb.max.Y):
            return False
        common = faces[a] & faces[b]
        return common is not None and abs(common.area - faces[a].area) < 1e-3 * faces[a].area

    solid = []
    for i, f in enumerate(faces):
        others = [j for j in range(len(faces)) if j != i]
        if sum(inside(i, j) for j in others) % 2:
            continue                                    # this face is a hole
        for j in others:
            if inside(j, i):
                f = f - faces[j]
        solid.extend(f.faces())

    band_h = height - 2 * edge_min
    keep = Rectangle(wrap_w, band_h, align=(Align.MIN, Align.MIN)).face().translate((0, edge_min, 0))
    out = []
    for f in solid:
        for shift in (0, -wrap_w, wrap_w):          # bring overflow past either seam back in
            piece = f.translate((shift, 0, 0)) & keep
            if piece is not None:
                out.extend(p for p in piece.faces() if p.area > 0.05)
    return out


def pocket(face, cyl):
    """Wrap one flat face onto the skin cylinder and thicken it inward past the bore."""
    b = face.bounding_box()
    cx, cy = (b.min.X + b.max.X) / 2, (b.min.Y + b.max.Y) / 2
    flat = face.translate((-cx, -cy, 0)).transform_geometry(
        Matrix([[sx, 0, 0, 0], [0, -1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]))   # stretch, y-down -> z-up
    theta = cx * sx / r_skin
    loc = Location(Plane(origin=(r_skin * math.cos(theta), r_skin * math.sin(theta), height - cy),
                         x_dir=(-math.sin(theta), math.cos(theta), 0),
                         z_dir=(math.cos(theta), math.sin(theta), 0)))
    depth = r_skin - bore_r + 1.0
    if max(b.size.X * sx, b.size.Y) <= small_max:
        # Small shapes (the dots): a radial prism trimmed by the skin cylinder. Full-circle
        # edges don't wrap reliably, and at this size projection differs from a true wrap by
        # about 0.01 mm.
        radial = Vector(math.cos(theta), math.sin(theta), 0)
        placed = flat.moved(loc).translate(radial * 1.0)
        prism = Solid.extrude(placed, radial * -(depth + 2.0))
        return prism & skin_cyl
    wrapped = cyl.wrap(flat, loc, tolerance=0.02)
    solid = thicken(wrapped, -depth)
    if max(math.hypot(v.X, v.Y) for v in solid.vertices()) > r_skin + 0.01:
        solid = thicken(wrapped, depth)              # mirrored shapes arrive with flipped normals
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(solid.wrapped, props)
    if props.Mass() < 0:                             # inside-out solid: flip so the cut removes material
        solid = Solid(solid.wrapped.Reversed())
    assert max(math.hypot(v.X, v.Y) for v in solid.vertices()) <= r_skin + 0.01
    return solid


def build():
    cyl = Cylinder(r_skin, height, align=up).faces().filter_by(GeomType.CYLINDER)[0]
    faces = flat_faces()
    pockets, failed = [], 0
    for f in faces:
        try:
            pockets.append(pocket(f, cyl))
        except Exception as e:                       # report, don't hide, a shape that won't wrap
            failed += 1
            b = f.bounding_box()
            print(f"WRAP FAILED at x={b.min.X:.1f} y={b.min.Y:.1f} size={b.size.X:.1f}x{b.size.Y:.1f}: {e}")
    tube = Cylinder(r_out, height, align=up) - Cylinder(bore_r, height + 2, align=up).move(Location((0, 0, -1)))
    return tube - Compound(pockets), len(faces), failed


if __name__ == "__main__":
    shade, n, failed = build()
    out = ROOT / "out"
    out.mkdir(exist_ok=True)
    export_step(shade, str(out / "scooter_cylinder.step"))
    export_stl(shade, str(out / "scooter_cylinder.stl"), tolerance=0.02, angular_tolerance=0.2)
    print(f"shapes={n} failed={failed} solids={len(shade.solids())} valid={shade.is_valid} "
          f"volume={shade.volume:.0f} stretch={sx:.3f}")

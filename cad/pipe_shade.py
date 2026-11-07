"""Green pipe lamp shade - a thin-walled pipe with a wide top lip, fits over the light base.

Every wall is a single 1.2 mm layer so light comes through evenly, including the lip. Inside
the lip the bore widens to the lip wall through a 45 degree cone, so the part prints rim-down
(upside down) without supports. That cone leaves a narrow darker band under the lip.

Run:  uv run --python 3.12 --with build123d python cad/pipe_shade.py
"""
from pathlib import Path

from build123d import Axis, Location, Plane, Polygon, export_step, export_stl, revolve

# --- parameters (mm) ---
bore_d = 85.0      # inner diameter (fits over the 82.19 mm light ring)
wall_t = 1.2       # wall thickness everywhere (3 perimeters @ 0.4 nozzle)
height = 127.0     # overall height (5 in)
lip_od = 100.0     # top lip outside diameter
lip_h  = 40.0      # top lip height

r_b = bore_d / 2
r_bo = r_b + wall_t                 # body outside radius
r_l = lip_od / 2                    # lip outside radius
z_l = height - lip_h                # step height (bottom of lip)
r_li = r_l - wall_t                 # lip inside radius
cone_h = r_li - r_b                 # 45 deg transition from bore to lip inside


def build():
    pts = [(r_b, 0), (r_bo, 0), (r_bo, z_l), (r_l, z_l), (r_l, height), (r_li, height),
           (r_li, z_l + wall_t), (r_b, z_l + wall_t + cone_h)]
    return revolve(Plane.XZ * Polygon(*pts, align=None), Axis.Z)


if __name__ == "__main__":
    pipe = build()
    out = Path(__file__).resolve().parent.parent / "out"
    out.mkdir(exist_ok=True)
    export_step(pipe, str(out / "pipe_shade.step"))
    export_stl(pipe, str(out / "pipe_shade.stl"))
    # Print orientation (rim on the bed) for the slicer
    pipe_print = pipe.rotate(Axis.X, 180).move(Location((0, 0, height)))
    export_stl(pipe_print, str(out / "pipe_shade_print.stl"))
    print(f"valid={pipe.is_valid} volume={pipe.volume:.0f}")

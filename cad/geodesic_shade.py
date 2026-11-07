"""Geodesic dome lamp shade - fits over the 82.19 mm light ring.

Frequency-4 geodesic sphere with 0.8 mm translucent panels and 2.0 x 2.6 mm outer struts,
cut flat onto a 10 mm base collar with an 84 mm bore.

Run:  uv run --python 3.12 --with build123d python cad/geodesic_shade.py
"""
import math
from pathlib import Path

import numpy as np
from build123d import *

# --- parameters (mm) ---
ring_od        = 83.0     # light ring OD (82.19 measured, rounded up)
fit_clearance  = 0.5      # radial clearance over ring
collar_wall    = 3.0      # base collar wall thickness
collar_below   = 6.0      # collar height below the dome cut plane
collar_overlap = 4.0      # collar extends up into dome to fuse
sphere_r       = 58.0     # geodesic circumradius
freq           = 4        # geodesic frequency
shell_t        = 2.6      # strut (rib) depth
panel_t        = 0.8      # translucent panel thickness (2 perimeters @0.4)
strut_w        = 2.0      # strut width

bore_r   = ring_od/2 + fit_clearance
cut_r    = bore_r + collar_wall          # dome outer radius at the cut plane
zc       = collar_below + math.sqrt(sphere_r**2 - cut_r**2)   # sphere centre height

# --- geodesic sphere (icosahedron, class I subdivision, vertex at top) ---
phi = (1 + 5**0.5) / 2
V = np.array([(-1, phi, 0), (1, phi, 0), (-1, -phi, 0), (1, -phi, 0),
              (0, -1, phi), (0, 1, phi), (0, -1, -phi), (0, 1, -phi),
              (phi, 0, -1), (phi, 0, 1), (-phi, 0, -1), (-phi, 0, 1)], float)
F = [(0,11,5),(0,5,1),(0,1,7),(0,7,10),(0,10,11),(1,5,9),(5,11,4),(11,10,2),(10,7,6),(7,1,8),
     (3,9,4),(3,4,2),(3,2,6),(3,6,8),(3,8,9),(4,9,5),(2,4,11),(6,2,10),(8,6,7),(9,8,1)]
V /= np.linalg.norm(V, axis=1)[:, None]
# rotate vertex 5 to +Z
a = V[5]; b = np.array([0, 0, 1.0]); ax = np.cross(a, b); s = np.linalg.norm(ax); c = a @ b
K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]]) / s
Rm = np.eye(3) + math.sin(math.acos(c)) * K + (1 - c) * K @ K
V = V @ Rm.T

tris = []
for (i, j, k) in F:
    A, B, C = V[i], V[j], V[k]
    grid = {}
    for u in range(freq + 1):
        for v in range(freq + 1 - u):
            p = A + (B - A) * u / freq + (C - A) * v / freq
            grid[(u, v)] = p / np.linalg.norm(p)
    for u in range(freq):
        for v in range(freq - u):
            tris.append((grid[(u, v)], grid[(u+1, v)], grid[(u, v+1)]))
            if u + v < freq - 1:
                tris.append((grid[(u+1, v)], grid[(u+1, v+1)], grid[(u, v+1)]))
pts = {}
for t in tris:
    for p in t:
        pts[tuple(np.round(p, 9))] = p
unit_pts = list(pts.values())
print(len(tris), "faces", len(unit_pts), "verts", "zc", zc, "top", zc + sphere_r)

ctr = np.array([0, 0, zc])
outer = ConvexPolyhedron([tuple(ctr + sphere_r * p) for p in unit_pts])
s_in = (sphere_r - shell_t) / sphere_r
inner = ConvexPolyhedron([tuple(ctr + sphere_r * s_in * p) for p in unit_pts])
shell = outer - inner
z_cut = collar_below
pockets = []
for t in tris:
    P = [ctr + sphere_r * p for p in t]
    if max(p[2] for p in P) < z_cut + collar_overlap: 
        continue
    n = np.cross(P[1] - P[0], P[2] - P[0]); n /= np.linalg.norm(n)
    if n @ (P[0] - ctr) < 0: n = -n
    d_out = n @ (P[0] - ctr)
    depth = d_out * (1 - s_in) - panel_t
    # incenter inset
    la, lb, lc = (np.linalg.norm(P[1]-P[2]), np.linalg.norm(P[0]-P[2]), np.linalg.norm(P[0]-P[1]))
    inc = (la*P[0] + lb*P[1] + lc*P[2]) / (la+lb+lc)
    area = np.linalg.norm(np.cross(P[1]-P[0], P[2]-P[0])) / 2
    r_in = 2*area/(la+lb+lc)
    k = (r_in - strut_w/2) / r_in
    Q = [inc + (p - inc) * k for p in P]
    verts = [tuple(q + n*1.0) for q in Q] + [tuple(q - n*depth) for q in Q]
    pockets.append(ConvexPolyhedron(verts))
print(len(pockets), "pockets; r_in example", r_in)
pk = Compound(pockets)
dome = shell - pk

keep = Box(300, 300, 300, align=(Align.CENTER, Align.CENTER, Align.MIN)).move(Location((0, 0, z_cut)))
dome_cut = dome & keep
collar_h = collar_below + collar_overlap
collar = Cylinder(cut_r + 0.3, collar_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
bore = Cylinder(bore_r, collar_h + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN)).move(Location((0,0,-0.005)))
# fill the inside of the dome below the collar top so the collar is solid, then re-bore
shade = (dome_cut + collar) - bore

if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "out"
    out.mkdir(exist_ok=True)
    export_step(shade, str(out / "geodesic_shade.step"))
    export_stl(shade, str(out / "geodesic_shade.stl"))
    print(f"valid={shade.is_valid} volume={shade.volume:.0f}")
print(measure(shade)["bbox"])
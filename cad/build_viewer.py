"""Build the shareable viewer pages by embedding each STL into its HTML template.

Run after regenerating an STL:  python3 cad/build_viewer.py
"""
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = {
    "geodesic_shade": "geodesic_template.html",
    "lattice_cylinder": "lattice_template.html",
}

for stem, template in PAGES.items():
    html = (ROOT / "web" / template).read_text()
    stl = base64.b64encode((ROOT / "out" / f"{stem}.stl").read_bytes()).decode()
    out = ROOT / "out" / f"{stem}_viewer.html"
    out.write_text(html.replace("__STL_B64__", stl))
    print(f"{out.relative_to(ROOT)}  {out.stat().st_size / 1024:.0f} KB")

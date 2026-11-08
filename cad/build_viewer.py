"""Build the shareable viewer pages by embedding each STL (and pattern data) into its template.

Run after regenerating an STL:  python3 cad/build_viewer.py
"""
import base64
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = {
    "geodesic_shade": "geodesic_template.html",
    "pixel_cylinder": "pixel_template.html",
    "pipe_shade": "pipe_template.html",
    "scooter_cylinder": "scooter_template.html",
}


def filled_svg(path):
    """The cut shapes as solid white fills, outline and glue-tab marks removed, as base64."""
    svg = path.read_text()
    svg = re.sub(r'<g id="cut-outline".*?</g>', "", svg, flags=re.S)
    svg = re.sub(r'<g id="score-tab".*?</g>', "", svg, flags=re.S)
    svg = svg.replace('<g id="cut-silhouettes" fill="none" stroke="red"',
                      '<g id="cut-silhouettes" fill="#fff" stroke="none"')
    return base64.b64encode(svg.encode()).decode()


def svg_pixels(path):
    svg = path.read_text()
    group = svg[svg.index('id="cut-pixels"'):]
    group = group[:group.index("</g>")]
    num = r"([-\d.]+)"
    return [[round(float(v), 5) for v in m] for m in re.findall(rf"M{num},{num}h{num}v{num}", group)]


for stem, template in PAGES.items():
    html = (ROOT / "web" / template).read_text()
    stl = base64.b64encode((ROOT / "out" / f"{stem}.stl").read_bytes()).decode()
    html = html.replace("__STL_B64__", stl)
    if "__PIXELS__" in html:
        pixels = svg_pixels(ROOT / "patterns" / "arcade_pixels.svg")
        html = html.replace("__PIXELS__", json.dumps(pixels, separators=(",", ":")))
    if "__SVG_DATA__" in html:
        html = html.replace("__SVG_DATA__", filled_svg(ROOT / "patterns" / "scooter.svg"))
    out = ROOT / "out" / f"{stem}_viewer.html"
    out.write_text(html)
    print(f"{out.relative_to(ROOT)}  {out.stat().st_size / 1024:.0f} KB")

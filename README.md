# LightShade

3D-printable shades for an RGB light that sits in a black base ring. The light's chrome ring
measures **82.19 mm OD**. Each shade has an **84.0 mm bore**, which gives about 0.9 mm of
clearance per side. The shade drops over the chrome ring and rests on the black ring.

Both models are parametric [build123d](https://github.com/gumyr/build123d) scripts. All
dimensions are set as named parameters at the top of each file.

## Shades

### Geodesic dome

A frequency-4 geodesic sphere cut flat onto a base collar. It has 0.8 mm translucent panels
between raised struts.

- **Viewer:** [`out/geodesic_shade_viewer.html`](out/geodesic_shade_viewer.html)
  ([shared copy](https://claude.ai/artifact/X6QRciDGakwiVSjTVTLYnA))

| | |
|---|---|
| Height × max diameter | 100.6 × 116.0 mm (3.96 in tall) |
| Panels | 275 triangles, 0.8 mm thick |
| Struts | 2.0 mm wide, 2.6 mm deep, on the outside |
| Collar | 84.0 mm ID, 90.6 mm OD, 10 mm tall |
| Material | 52.8 cm³, about 65 g PLA |
| Supports | Tree supports inside the upper cap, touching the build plate only. They come out through the base opening. |

### Jewel lattice cylinder

A 6-inch tube with a diamond lattice cut into the outside at three depths. The three wall
thicknesses give three light levels.

- **Viewer:** [`out/lattice_cylinder_viewer.html`](out/lattice_cylinder_viewer.html)
  ([shared copy](https://claude.ai/artifact/8NRowLVrYndwGCmYLNB9M8))

| | |
|---|---|
| Height × diameter | 152.4 × 90.0 mm (6.00 in tall) |
| Pattern | 16 diamonds around × 10 rows, 17.7 × 24 mm cells, 2.2 mm ribs |
| Wall thickness | 0.8 mm windows (bright), 2.0 mm jewel frames (mid), 3.0 mm ribs, collar and rim (dark) |
| Bands | Rows of jewel cells alternate with rows of plain windows: 96 jewels, 64 plain windows |
| Material | 84.3 cm³, about 105 g PLA |
| Supports | None. Every pocket ends in a sloped diamond tip. |

## Printing

- Print upright, collar on the bed.
- Use white or natural PLA with a 0.4 mm nozzle. The 0.8 mm windows are exactly two perimeters, so don't add extra walls.

## Repository layout

```
cad/
  geodesic_shade.py     geodesic dome model
  lattice_cylinder.py   jewel lattice cylinder model
  build_viewer.py       embeds each STL into its viewer page
web/
  *_template.html       viewer page templates (three.js)
out/
  *.step / *.stl / *.3mf    exported models (generated; edit the scripts, not these)
  *_viewer.html             self-contained 3D viewers (generated)
```

## Rebuilding

```sh
uv run --python 3.12 --with build123d python cad/geodesic_shade.py
uv run --python 3.12 --with build123d python cad/lattice_cylinder.py
python3 cad/build_viewer.py
```

Each model script writes its STEP and STL files to `out/`. The 3MF files were exported with
the build123d-mcp server.

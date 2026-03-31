# Stonegrid

A parking lot stone pattern generator that creates mosaic patterns (triangles or rectangles) with configurable color gradients per lot.

**Live demo:** https://stonegrid.onrender.com/

## Features

- Visual editor with color pickers, sliders, and gradient toggle per lot
- JSON editor for direct config editing
- Preview patterns as SVG in a web UI
- Export to DXF for use in CAD software
- Shareable URLs that encode the full config
- Triangle and rectangle pattern types with configurable dimensions
- Configurable space dimensions and color palette

## Quick start

```bash
pip install -r requirements.txt
```

### Web UI

```bash
python app.py
```

Open http://localhost:5001 — use the visual editor or edit JSON directly, click Preview, and download DXF.

### CLI

```bash
cp parking_config.sample.json parking_config.json
python generate_parking.py parking_config.json
```

Generates `parking_lot.svg` and `parking_lot.dxf` in the current directory.

### Render.com

Create a new **Web Service** with Python runtime:

| Setting | Value |
|---------|-------|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app:app` |
| Environment variable | `PYTHON_VERSION=3.12.0` |

### Docker

```bash
docker build -t stonegrid .
docker run -p 8080:8080 stonegrid
```

## Project structure

| File | Description |
|------|-------------|
| [`parking_generator.py`](parking_generator.py) | Core generation logic — config parsing, validation, pattern generation, SVG and DXF rendering |
| [`app.py`](app.py) | Flask web app with preview and DXF download API endpoints |
| [`generate_parking.py`](generate_parking.py) | CLI wrapper — reads a config file, writes SVG and DXF to disk |
| [`parking_config.sample.json`](parking_config.sample.json) | Example configuration |

## Configuration

See [`parking_config.sample.json`](parking_config.sample.json) for an example. Key fields:

| Field | Description | Default |
|-------|-------------|---------|
| `pattern` | Pattern type: `"triangles"` or `"rectangles"` | `"triangles"` |
| `side` | Primary side length (mm) | 200 |
| `side2` | Second dimension (mm) — triangle height or rectangle height | equilateral height for triangles, same as `side` for rectangles |
| `space_width` | Width of one parking space (mm) | 2700 |
| `space_height` | Depth of one parking space (mm) | 5000 |
| `seed` | Random seed for reproducibility | 42 |
| `colors` | Color definitions with RGB, DXF layer, and ACI color | light/middle/dark |
| `lots` | Array of lot definitions with color proportions | — |

Each lot can be either a flat proportion (`{"light": 70, "middle": 20, "dark": 10}`) or a gradient with `bottom` and `top` keys.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

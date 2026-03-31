# Stonegrid

A parking lot stone pattern generator that creates triangular mosaic patterns with configurable color gradients per lot.

## Features

- Define color proportions per parking lot with optional bottom-to-top gradients
- Preview patterns as SVG in a web UI
- Export to DXF for use in CAD software
- Configurable triangle size, space dimensions, and color palette

## Quick start

```bash
pip install -r requirements.txt
```

### Web UI

```bash
python app.py
```

Open http://localhost:5001 — edit the JSON config, click Preview, and download DXF.

### CLI

```bash
cp parking_config.sample.json parking_config.json
python generate_parking.py parking_config.json
```

Generates `parking_lot.svg` and `parking_lot.dxf` in the current directory.

### Docker

```bash
docker build -t stonegrid .
docker run -p 8080:8080 stonegrid
```

## Project structure

| File | Description |
|------|-------------|
| [`parking_generator.py`](parking_generator.py) | Core generation logic — config parsing, validation, triangle generation, SVG and DXF rendering |
| [`app.py`](app.py) | Flask web app with preview and DXF download API endpoints |
| [`generate_parking.py`](generate_parking.py) | CLI wrapper — reads a config file, writes SVG and DXF to disk |
| [`parking_config.sample.json`](parking_config.sample.json) | Example configuration |

## Configuration

See [`parking_config.sample.json`](parking_config.sample.json) for an example. Key fields:

| Field | Description | Default |
|-------|-------------|---------|
| `triangle_side` | Side length of each triangle (mm) | 200 |
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

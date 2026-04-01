"""
Core generation logic for stone patterns (triangles and rectangles).
Used by both the CLI (generate.py) and the web app (app.py).
"""

import io
import math
import random
import ezdxf
from ezdxf.enums import TextEntityAlignment


# === Defaults ===
DEFAULTS = {
    'pattern': 'triangles',
    'side': 200,
    'zone_width': 2700,
    'zone_height': 5000,
    'seed': 42,
    'colors': {
        'light':  {'rgb': (200, 200, 200), 'layer': 'STONE_LIGHT',  'aci': 9},
        'middle': {'rgb': (140, 140, 140), 'layer': 'STONE_MIDDLE', 'aci': 8},
        'dark':   {'rgb': (80, 80, 80),    'layer': 'STONE_DARK',   'aci': 251},
    },
}


def parse_config(cfg):
    """Parse a config dict and return resolved settings + zones."""
    pattern = cfg.get('pattern', DEFAULTS['pattern'])
    side = cfg.get('side', DEFAULTS['side'])
    side2 = cfg.get('side2', None)
    zone_width = cfg.get('zone_width', DEFAULTS['zone_width'])
    zone_height = cfg.get('zone_height', DEFAULTS['zone_height'])
    seed = cfg.get('seed', DEFAULTS['seed'])

    if pattern == 'triangles':
        # For triangles: side = horizontal base, side2 = vertical height
        # Default: equilateral triangle height
        if side2 is None:
            side2 = side * math.sqrt(3) / 2
    else:
        # For rectangles: side2 defaults to side (square)
        if side2 is None:
            side2 = side

    colors = dict(DEFAULTS['colors'])
    if 'colors' in cfg:
        colors = {}
        for key, val in cfg['colors'].items():
            colors[key] = {
                'rgb': tuple(val['rgb']),
                'layer': val.get('layer', f'STONE_{key}'),
                'aci': val.get('aci', 7),
            }

    zones = cfg.get('zones', [])

    labels_cfg = cfg.get('labels', {})
    labels = {
        'show': labels_cfg.get('show', True),
        'color': tuple(labels_cfg.get('color', [255, 0, 0])),
        'opacity': labels_cfg.get('opacity', 0.5),
        'size': labels_cfg.get('size', 600),
        'layer': labels_cfg.get('layer', 'LABELS'),
        'aci': labels_cfg.get('aci', 7),
    }

    return {
        'pattern': pattern,
        'side': side,
        'side2': side2,
        'zone_width': zone_width,
        'zone_height': zone_height,
        'seed': seed,
        'colors': colors,
        'zones': zones,
        'labels': labels,
    }


def validate_config(settings):
    """Validate config. Returns list of error strings (empty = OK)."""
    errors = []
    colors = settings['colors']
    zones = settings['zones']

    if settings['pattern'] not in ('triangles', 'rectangles'):
        errors.append(f'Unknown pattern "{settings["pattern"]}" (expected "triangles" or "rectangles")')

    if not zones:
        errors.append('No zones defined')
        return errors

    for i, zone in enumerate(zones):
        part_sets = []
        if _is_gradient(zone):
            part_sets.append((zone['bottom'], f'Zone {i + 1} bottom'))
            part_sets.append((zone['top'], f'Zone {i + 1} top'))
        else:
            part_sets.append((zone, f'Zone {i + 1}'))

        for parts, label in part_sets:
            total = sum(parts.values())
            if total <= 0:
                errors.append(f'{label}: parts must sum to a positive number')
            for key in parts:
                if key not in colors:
                    errors.append(f'{label}: unknown color "{key}" (available: {list(colors.keys())})')
                if parts[key] < 0:
                    errors.append(f'{label}: "{key}" has negative parts')

    return errors


def _is_gradient(zone_def):
    return 'bottom' in zone_def and 'top' in zone_def


def _normalize_zone(zone_def):
    if _is_gradient(zone_def):
        return zone_def
    return {'bottom': dict(zone_def), 'top': dict(zone_def)}


def _triangle_vertices(col, row, x_offset, y_offset, side, side2):
    """Generate vertices for a triangle in a tessellating grid.
    side = horizontal base width, side2 = vertical row height."""
    points_up = (col + row) % 2 == 0
    x_base = col * (side / 2) + x_offset
    y_base = row * side2 + y_offset

    if points_up:
        return [(x_base, y_base),
                (x_base + side, y_base),
                (x_base + side / 2, y_base + side2)]
    else:
        return [(x_base, y_base + side2),
                (x_base + side, y_base + side2),
                (x_base + side / 2, y_base)]


def _rectangle_vertices(col, row, x_offset, y_offset, side, side2):
    """Generate vertices for a rectangle in a simple grid."""
    x = col * side + x_offset
    y = row * side2 + y_offset
    return [(x, y), (x + side, y), (x + side, y + side2), (x, y + side2)]


def _pick_color(zone_def, seed, zone_index, col, row, num_rows):
    grad = _normalize_zone(zone_def)
    bottom = grad['bottom']
    top = grad['top']

    t = row / max(num_rows - 1, 1)
    all_keys = list(dict.fromkeys(list(bottom.keys()) + list(top.keys())))

    # Interpolate parts between bottom and top
    interpolated = {}
    for key in all_keys:
        b = bottom.get(key, 0)
        tp = top.get(key, 0)
        interpolated[key] = b + (tp - b) * t

    # Normalize parts to percentages
    total = sum(interpolated.values())
    if total <= 0:
        return all_keys[0] if all_keys else None

    rng = random.Random(seed + zone_index * 10000 + row * 1000 + col)
    r = rng.random() * total

    cumulative = 0
    for color_key, parts in interpolated.items():
        cumulative += parts
        if r < cumulative:
            return color_key
    return color_key


def generate(settings):
    """Generate all shapes and boundaries from settings. Returns (shapes, boundaries, num_zones)."""
    side = settings['side']
    side2 = settings['side2']
    pattern = settings['pattern']
    zone_width = settings['zone_width']
    zone_height = settings['zone_height']
    seed = settings['seed']
    zones = settings['zones']

    num_zones = len(zones)
    total_width = num_zones * zone_width

    if pattern == 'rectangles':
        num_rows = int(zone_height / side2) + 1
        num_cols = int(total_width / side) + 2
        vert_fn = _rectangle_vertices
    else:
        num_rows = int(zone_height / side2) + 1
        num_cols = int(total_width / (side / 2)) + 2
        vert_fn = _triangle_vertices

    all_shapes = []
    for row in range(num_rows):
        for col in range(num_cols):
            verts = vert_fn(col, row, 0, 0, side, side2)
            n = len(verts)
            cx = sum(v[0] for v in verts) / n
            cy = sum(v[1] for v in verts) / n
            if 0 <= cx <= total_width and 0 <= cy <= zone_height:
                zone_index = min(int(cx / zone_width), num_zones - 1)
                color = _pick_color(zones[zone_index], seed, zone_index, col, row, num_rows)
                all_shapes.append((verts, color))

    boundaries = []
    for i in range(1, num_zones):
        x = i * zone_width
        boundaries.append((x, 0, x, zone_height))
    tw = num_zones * zone_width
    boundaries.append((0, 0, tw, 0))
    boundaries.append((0, zone_height, tw, zone_height))
    boundaries.append((0, 0, 0, zone_height))
    boundaries.append((tw, 0, tw, zone_height))

    return all_shapes, boundaries, num_zones


def render_svg(settings, all_shapes, boundaries, num_zones):
    """Render SVG string."""
    colors = settings['colors']
    zone_width = settings['zone_width']
    zone_height = settings['zone_height']
    total_width = num_zones * zone_width
    total_height = zone_height

    margin = 200
    svg_width = total_width + 2 * margin
    svg_height = total_height + 2 * margin
    scale = 0.15

    lines = []
    lines.append(f'<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
                 f'width="{svg_width * scale:.0f}" height="{svg_height * scale:.0f}" '
                 f'viewBox="{-margin} {-margin} {svg_width} {svg_height}">')
    lines.append(f'<rect x="{-margin}" y="{-margin}" '
                 f'width="{svg_width}" height="{svg_height}" fill="#e8e8e8"/>')

    for verts, color_key in all_shapes:
        r, g, b = colors[color_key]['rgb']
        points_str = ' '.join(f'{v[0]:.1f},{total_height - v[1]:.1f}' for v in verts)
        lines.append(f'<polygon points="{points_str}" '
                     f'fill="rgb({r},{g},{b})" stroke="#888" stroke-width="1"/>')

    labels = settings.get('labels', {})
    if labels.get('show', True):
        lr, lg, lb = labels.get('color', (255, 0, 0))
        opacity = labels.get('opacity', 0.5)
        size = labels.get('size', 600)
        for i in range(num_zones):
            cx = i * zone_width + zone_width / 2
            cy = zone_height / 2
            lines.append(f'<text x="{cx}" y="{total_height - cy}" '
                         f'font-size="{size}" fill="rgb({lr},{lg},{lb})" fill-opacity="{opacity}" '
                         f'text-anchor="middle" dominant-baseline="middle" '
                         f'font-family="Arial" font-weight="bold">{i + 1}</text>')

    lines.append('</svg>')
    return '\n'.join(lines)


def render_dxf_bytes(settings, all_shapes, boundaries, num_zones):
    """Render DXF and return as bytes."""
    colors = settings['colors']
    zone_width = settings['zone_width']
    zone_height = settings['zone_height']
    labels = settings.get('labels', {})

    doc = ezdxf.new('R2010')
    msp = doc.modelspace()

    for key, info in colors.items():
        doc.layers.add(info['layer'], color=info['aci'])
    doc.layers.add('BOUNDARIES', color=7)
    label_layer = labels.get('layer', 'LABELS')
    label_aci = labels.get('aci', 7)
    doc.layers.add(label_layer, color=label_aci)

    for verts, color_key in all_shapes:
        info = colors[color_key]
        layer = info['layer']
        points = list(verts) + [verts[0]]
        msp.add_lwpolyline(points, dxfattribs={'layer': layer})
        hatch = msp.add_hatch(color=info['aci'], dxfattribs={'layer': layer})
        hatch.paths.add_polyline_path([v + (0,) for v in verts], is_closed=True)

    for (x1, y1, x2, y2) in boundaries:
        msp.add_line((x1, y1), (x2, y2), dxfattribs={'layer': 'BOUNDARIES', 'linetype': 'DASHED'})

    if labels.get('show', True):
        for i in range(num_zones):
            cx = i * zone_width + zone_width / 2
            cy = zone_height / 2
            msp.add_text(str(i + 1), height=labels.get('size', 600),
                         dxfattribs={'layer': label_layer, 'color': label_aci}
                         ).set_placement((cx, cy), align=TextEntityAlignment.MIDDLE_CENTER)

    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode('utf-8')

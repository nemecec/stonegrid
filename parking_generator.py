"""
Core generation logic for parking lot stone patterns (triangles and rectangles).
Used by both the CLI (generate_parking.py) and the web app (app.py).
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
    'space_width': 2700,
    'space_height': 5000,
    'seed': 42,
    'colors': {
        'light':  {'rgb': (200, 200, 200), 'layer': 'STONE_LIGHT',  'aci': 9},
        'middle': {'rgb': (140, 140, 140), 'layer': 'STONE_MIDDLE', 'aci': 8},
        'dark':   {'rgb': (80, 80, 80),    'layer': 'STONE_DARK',   'aci': 251},
    },
}


def parse_config(cfg):
    """Parse a config dict and return resolved settings + lots."""
    pattern = cfg.get('pattern', DEFAULTS['pattern'])
    side = cfg.get('side', DEFAULTS['side'])
    side2 = cfg.get('side2', None)
    space_width = cfg.get('space_width', DEFAULTS['space_width'])
    space_height = cfg.get('space_height', DEFAULTS['space_height'])
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

    lots = cfg.get('lots', [])

    return {
        'pattern': pattern,
        'side': side,
        'side2': side2,
        'space_width': space_width,
        'space_height': space_height,
        'seed': seed,
        'colors': colors,
        'lots': lots,
    }


def validate_config(settings):
    """Validate config. Returns list of error strings (empty = OK)."""
    errors = []
    colors = settings['colors']
    lots = settings['lots']

    if settings['pattern'] not in ('triangles', 'rectangles'):
        errors.append(f'Unknown pattern "{settings["pattern"]}" (expected "triangles" or "rectangles")')

    if not lots:
        errors.append('No lots defined')
        return errors

    for i, lot in enumerate(lots):
        prop_sets = []
        if _is_gradient(lot):
            prop_sets.append((lot['bottom'], f'Lot {i + 1} bottom'))
            prop_sets.append((lot['top'], f'Lot {i + 1} top'))
        else:
            prop_sets.append((lot, f'Lot {i + 1}'))

        for props, label in prop_sets:
            total = sum(props.values())
            if abs(total - 100) > 0.5:
                errors.append(f'{label}: proportions sum to {total}, expected 100')
            for key in props:
                if key not in colors:
                    errors.append(f'{label}: unknown color "{key}" (available: {list(colors.keys())})')

    return errors


def _is_gradient(lot_def):
    return 'bottom' in lot_def and 'top' in lot_def


def _normalize_lot(lot_def):
    if _is_gradient(lot_def):
        return lot_def
    return {'bottom': dict(lot_def), 'top': dict(lot_def)}


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


def _pick_color(lot_def, seed, space_index, col, row, num_rows):
    grad = _normalize_lot(lot_def)
    bottom = grad['bottom']
    top = grad['top']

    t = row / max(num_rows - 1, 1)
    all_keys = list(dict.fromkeys(list(bottom.keys()) + list(top.keys())))

    interpolated = {}
    for key in all_keys:
        b = bottom.get(key, 0)
        tp = top.get(key, 0)
        interpolated[key] = b + (tp - b) * t

    rng = random.Random(seed + space_index * 10000 + row * 1000 + col)
    r = rng.random() * 100

    cumulative = 0
    for color_key, pct in interpolated.items():
        cumulative += pct
        if r < cumulative:
            return color_key
    return color_key


def generate(settings):
    """Generate all shapes and boundaries from settings. Returns (shapes, boundaries, num_spaces)."""
    side = settings['side']
    side2 = settings['side2']
    pattern = settings['pattern']
    space_width = settings['space_width']
    space_height = settings['space_height']
    seed = settings['seed']
    lots = settings['lots']

    num_spaces = len(lots)

    if pattern == 'rectangles':
        num_rows = int(space_height / side2) + 1
        num_cols = int(space_width / side) + 1
        vert_fn = _rectangle_vertices
    else:
        num_rows = int(space_height / side2) + 1
        num_cols = int(space_width / (side / 2)) + 1
        vert_fn = _triangle_vertices

    all_shapes = []
    for i, lot_def in enumerate(lots):
        x_offset = i * space_width
        for row in range(num_rows):
            for col in range(num_cols):
                verts = vert_fn(col, row, x_offset, 0, side, side2)
                n = len(verts)
                cx = sum(v[0] for v in verts) / n
                cy = sum(v[1] for v in verts) / n
                if x_offset <= cx <= x_offset + space_width and 0 <= cy <= space_height:
                    color = _pick_color(lot_def, seed, i, col, row, num_rows)
                    all_shapes.append((verts, color))

    boundaries = []
    for i in range(1, num_spaces):
        x = i * space_width
        boundaries.append((x, 0, x, space_height))
    tw = num_spaces * space_width
    boundaries.append((0, 0, tw, 0))
    boundaries.append((0, space_height, tw, space_height))
    boundaries.append((0, 0, 0, space_height))
    boundaries.append((tw, 0, tw, space_height))

    return all_shapes, boundaries, num_spaces


def render_svg(settings, all_shapes, boundaries, num_spaces):
    """Render SVG string."""
    colors = settings['colors']
    space_width = settings['space_width']
    space_height = settings['space_height']
    total_width = num_spaces * space_width
    total_height = space_height

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

    for (x1, y1, x2, y2) in boundaries:
        lines.append(f'<line x1="{x1}" y1="{total_height - y1}" '
                     f'x2="{x2}" y2="{total_height - y2}" '
                     f'stroke="white" stroke-width="8" stroke-dasharray="100,80"/>')

    for i in range(num_spaces):
        cx = i * space_width + space_width / 2
        cy = space_height / 2
        lines.append(f'<text x="{cx}" y="{total_height - cy}" '
                     f'font-size="300" fill="white" fill-opacity="0.4" '
                     f'text-anchor="middle" dominant-baseline="middle" '
                     f'font-family="Arial" font-weight="bold">{i + 1}</text>')

    lines.append('</svg>')
    return '\n'.join(lines)


def render_dxf_bytes(settings, all_shapes, boundaries, num_spaces):
    """Render DXF and return as bytes."""
    colors = settings['colors']
    space_width = settings['space_width']
    space_height = settings['space_height']

    doc = ezdxf.new('R2010')
    msp = doc.modelspace()

    for key, info in colors.items():
        doc.layers.add(info['layer'], color=info['aci'])
    doc.layers.add('BOUNDARIES', color=7)
    doc.layers.add('LABELS', color=7)

    for verts, color_key in all_shapes:
        info = colors[color_key]
        layer = info['layer']
        points = list(verts) + [verts[0]]
        msp.add_lwpolyline(points, dxfattribs={'layer': layer})
        hatch = msp.add_hatch(color=info['aci'], dxfattribs={'layer': layer})
        hatch.paths.add_polyline_path([v + (0,) for v in verts], is_closed=True)

    for (x1, y1, x2, y2) in boundaries:
        msp.add_line((x1, y1), (x2, y2), dxfattribs={'layer': 'BOUNDARIES', 'linetype': 'DASHED'})

    for i in range(num_spaces):
        cx = i * space_width + space_width / 2
        cy = space_height / 2
        msp.add_text(str(i + 1), height=300,
                     dxfattribs={'layer': 'LABELS', 'color': 7}
                     ).set_placement((cx, cy), align=TextEntityAlignment.MIDDLE_CENTER)

    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode('utf-8')

"""CLI wrapper for the stone pattern generator."""

import json
import sys
import generator as gen


def main():
    if len(sys.argv) < 2:
        print('Usage: python generate.py <config.json>')
        sys.exit(1)

    with open(sys.argv[1]) as f:
        cfg = json.load(f)

    settings = gen.parse_config(cfg)
    errors = gen.validate_config(settings)
    if errors:
        for e in errors:
            print(f'ERROR: {e}')
        sys.exit(1)

    shapes, boundaries, num_zones = gen.generate(settings)
    shape_name = settings['pattern']
    print(f'Generated {len(shapes)} {shape_name} across {num_zones} zones')

    for i, zone in enumerate(settings['zones']):
        if 'bottom' in zone and 'top' in zone:
            bp = ', '.join(f'{k}={v}%' for k, v in zone['bottom'].items())
            tp = ', '.join(f'{k}={v}%' for k, v in zone['top'].items())
            print(f'  Zone {i + 1}: bottom({bp}) -> top({tp})')
        else:
            parts = ', '.join(f'{k}={v}%' for k, v in zone.items())
            print(f'  Zone {i + 1}: {parts}')

    svg = gen.render_svg(settings, shapes, boundaries, num_zones)
    with open('stonegrid.svg', 'w') as f:
        f.write(svg)
    print('SVG written to stonegrid.svg')

    dxf_bytes = gen.render_dxf_bytes(settings, shapes, boundaries, num_zones)
    with open('stonegrid.dxf', 'wb') as f:
        f.write(dxf_bytes)
    print('DXF written to stonegrid.dxf')


if __name__ == '__main__':
    main()

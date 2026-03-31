"""CLI wrapper for the parking lot stone pattern generator."""

import json
import sys
import parking_generator as gen


def main():
    if len(sys.argv) < 2:
        print('Usage: python generate_parking.py <config.json>')
        sys.exit(1)

    with open(sys.argv[1]) as f:
        cfg = json.load(f)

    settings = gen.parse_config(cfg)
    errors = gen.validate_config(settings)
    if errors:
        for e in errors:
            print(f'ERROR: {e}')
        sys.exit(1)

    triangles, boundaries, num_spaces = gen.generate(settings)
    print(f'Generated {len(triangles)} triangles across {num_spaces} spaces')

    for i, lot in enumerate(settings['lots']):
        if 'bottom' in lot and 'top' in lot:
            bp = ', '.join(f'{k}={v}%' for k, v in lot['bottom'].items())
            tp = ', '.join(f'{k}={v}%' for k, v in lot['top'].items())
            print(f'  Lot {i + 1}: bottom({bp}) -> top({tp})')
        else:
            parts = ', '.join(f'{k}={v}%' for k, v in lot.items())
            print(f'  Lot {i + 1}: {parts}')

    svg = gen.render_svg(settings, triangles, boundaries, num_spaces)
    with open('parking_lot.svg', 'w') as f:
        f.write(svg)
    print('SVG written to parking_lot.svg')

    dxf_bytes = gen.render_dxf_bytes(settings, triangles, boundaries, num_spaces)
    with open('parking_lot.dxf', 'wb') as f:
        f.write(dxf_bytes)
    print('DXF written to parking_lot.dxf')


if __name__ == '__main__':
    main()

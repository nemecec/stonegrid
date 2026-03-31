"""Tests for the parking lot stone pattern generator."""

import math

import parking_generator as gen


SAMPLE_CONFIG = {
    "pattern": "triangles",
    "side": 200,
    "space_width": 2700,
    "space_height": 5000,
    "seed": 42,
    "colors": {
        "light": {"rgb": [200, 200, 200], "layer": "STONE_LIGHT", "aci": 9},
        "middle": {"rgb": [140, 140, 140], "layer": "STONE_MIDDLE", "aci": 8},
        "dark": {"rgb": [80, 80, 80], "layer": "STONE_DARK", "aci": 251},
    },
    "lots": [
        {
            "bottom": {"light": 100, "middle": 0, "dark": 0},
            "top": {"light": 20, "middle": 50, "dark": 30},
        }
    ],
}

RECT_CONFIG = {
    "pattern": "rectangles",
    "side": 200,
    "side2": 100,
    "space_width": 2700,
    "space_height": 5000,
    "seed": 42,
    "colors": {
        "light": {"rgb": [200, 200, 200], "layer": "STONE_LIGHT", "aci": 9},
        "dark": {"rgb": [80, 80, 80], "layer": "STONE_DARK", "aci": 251},
    },
    "lots": [{"light": 60, "dark": 40}],
}


class TestParseConfig:
    def test_defaults_applied(self):
        settings = gen.parse_config({})
        assert settings["side"] == 200
        assert settings["space_width"] == 2700
        assert settings["space_height"] == 5000
        assert settings["seed"] == 42
        assert settings["pattern"] == "triangles"

    def test_custom_values(self):
        cfg = {"side": 300, "seed": 99}
        settings = gen.parse_config(cfg)
        assert settings["side"] == 300
        assert settings["seed"] == 99

    def test_triangle_side2_defaults_to_equilateral_height(self):
        settings = gen.parse_config({"side": 200})
        expected = 200 * math.sqrt(3) / 2
        assert abs(settings["side2"] - expected) < 0.001

    def test_triangle_custom_side2(self):
        settings = gen.parse_config({"pattern": "triangles", "side": 200, "side2": 150})
        assert settings["side2"] == 150

    def test_rectangle_side2_defaults_to_side(self):
        settings = gen.parse_config({"pattern": "rectangles", "side": 200})
        assert settings["side2"] == 200

    def test_rectangle_custom_side2(self):
        settings = gen.parse_config({"pattern": "rectangles", "side": 200, "side2": 100})
        assert settings["side2"] == 100

    def test_custom_colors(self):
        cfg = {
            "colors": {
                "red": {"rgb": [255, 0, 0], "layer": "RED", "aci": 1},
            },
            "lots": [],
        }
        settings = gen.parse_config(cfg)
        assert "red" in settings["colors"]
        assert settings["colors"]["red"]["rgb"] == (255, 0, 0)

    def test_lots_passed_through(self):
        cfg = {"lots": [{"light": 50, "dark": 50}]}
        settings = gen.parse_config(cfg)
        assert len(settings["lots"]) == 1


class TestValidateConfig:
    def test_no_lots_is_error(self):
        settings = gen.parse_config({"lots": []})
        errors = gen.validate_config(settings)
        assert any("No lots" in e for e in errors)

    def test_valid_flat_lot(self):
        cfg = {"lots": [{"light": 60, "middle": 30, "dark": 10}]}
        settings = gen.parse_config(cfg)
        errors = gen.validate_config(settings)
        assert errors == []

    def test_valid_gradient_lot(self):
        settings = gen.parse_config(SAMPLE_CONFIG)
        errors = gen.validate_config(settings)
        assert errors == []

    def test_proportions_not_100(self):
        cfg = {"lots": [{"light": 50, "middle": 20, "dark": 10}]}
        settings = gen.parse_config(cfg)
        errors = gen.validate_config(settings)
        assert any("sum to 80" in e for e in errors)

    def test_unknown_color(self):
        cfg = {"lots": [{"light": 50, "unknown_color": 50}]}
        settings = gen.parse_config(cfg)
        errors = gen.validate_config(settings)
        assert any("unknown color" in e for e in errors)

    def test_unknown_pattern(self):
        settings = gen.parse_config({"pattern": "hexagons", "lots": [{"light": 100}]})
        errors = gen.validate_config(settings)
        assert any("Unknown pattern" in e for e in errors)


class TestGenerateTriangles:
    def test_generates_triangles(self):
        settings = gen.parse_config(SAMPLE_CONFIG)
        shapes, boundaries, num_spaces = gen.generate(settings)
        assert len(shapes) > 0
        assert num_spaces == 1

    def test_triangle_has_three_vertices(self):
        settings = gen.parse_config(SAMPLE_CONFIG)
        shapes, _, _ = gen.generate(settings)
        verts, color = shapes[0]
        assert len(verts) == 3

    def test_colors_from_palette(self):
        settings = gen.parse_config(SAMPLE_CONFIG)
        shapes, _, _ = gen.generate(settings)
        valid_colors = set(settings["colors"].keys())
        for _, color in shapes:
            assert color in valid_colors

    def test_boundaries_for_single_lot(self):
        settings = gen.parse_config(SAMPLE_CONFIG)
        _, boundaries, _ = gen.generate(settings)
        assert len(boundaries) == 4

    def test_boundaries_for_multiple_lots(self):
        cfg = dict(SAMPLE_CONFIG)
        cfg["lots"] = [
            {"light": 100, "middle": 0, "dark": 0},
            {"light": 0, "middle": 100, "dark": 0},
            {"light": 0, "middle": 0, "dark": 100},
        ]
        settings = gen.parse_config(cfg)
        _, boundaries, num_spaces = gen.generate(settings)
        assert num_spaces == 3
        assert len(boundaries) == 6

    def test_deterministic_with_same_seed(self):
        settings = gen.parse_config(SAMPLE_CONFIG)
        t1, _, _ = gen.generate(settings)
        t2, _, _ = gen.generate(settings)
        assert t1 == t2


class TestGenerateRectangles:
    def test_generates_rectangles(self):
        settings = gen.parse_config(RECT_CONFIG)
        shapes, boundaries, num_spaces = gen.generate(settings)
        assert len(shapes) > 0
        assert num_spaces == 1

    def test_rectangle_has_four_vertices(self):
        settings = gen.parse_config(RECT_CONFIG)
        shapes, _, _ = gen.generate(settings)
        verts, _ = shapes[0]
        assert len(verts) == 4

    def test_square_when_no_side2(self):
        cfg = {"pattern": "rectangles", "side": 200, "lots": [{"light": 100}]}
        settings = gen.parse_config(cfg)
        shapes, _, _ = gen.generate(settings)
        verts, _ = shapes[0]
        width = abs(verts[1][0] - verts[0][0])
        height = abs(verts[2][1] - verts[1][1])
        assert width == height == 200

    def test_rectangle_dimensions(self):
        settings = gen.parse_config(RECT_CONFIG)
        shapes, _, _ = gen.generate(settings)
        verts, _ = shapes[0]
        width = abs(verts[1][0] - verts[0][0])
        height = abs(verts[2][1] - verts[1][1])
        assert width == 200
        assert height == 100

    def test_colors_from_palette(self):
        settings = gen.parse_config(RECT_CONFIG)
        shapes, _, _ = gen.generate(settings)
        valid_colors = set(settings["colors"].keys())
        for _, color in shapes:
            assert color in valid_colors

    def test_deterministic_with_same_seed(self):
        settings = gen.parse_config(RECT_CONFIG)
        r1, _, _ = gen.generate(settings)
        r2, _, _ = gen.generate(settings)
        assert r1 == r2


class TestRenderSvg:
    def test_valid_svg(self):
        settings = gen.parse_config(SAMPLE_CONFIG)
        shapes, boundaries, num_spaces = gen.generate(settings)
        svg = gen.render_svg(settings, shapes, boundaries, num_spaces)
        assert svg.startswith("<?xml")
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_contains_polygons(self):
        settings = gen.parse_config(SAMPLE_CONFIG)
        shapes, boundaries, num_spaces = gen.generate(settings)
        svg = gen.render_svg(settings, shapes, boundaries, num_spaces)
        assert "<polygon" in svg

    def test_rectangles_render_svg(self):
        settings = gen.parse_config(RECT_CONFIG)
        shapes, boundaries, num_spaces = gen.generate(settings)
        svg = gen.render_svg(settings, shapes, boundaries, num_spaces)
        assert "<polygon" in svg
        assert "</svg>" in svg


class TestRenderDxf:
    def test_produces_bytes(self):
        settings = gen.parse_config(SAMPLE_CONFIG)
        shapes, boundaries, num_spaces = gen.generate(settings)
        dxf_bytes = gen.render_dxf_bytes(settings, shapes, boundaries, num_spaces)
        assert isinstance(dxf_bytes, bytes)
        assert len(dxf_bytes) > 0

    def test_rectangles_produce_bytes(self):
        settings = gen.parse_config(RECT_CONFIG)
        shapes, boundaries, num_spaces = gen.generate(settings)
        dxf_bytes = gen.render_dxf_bytes(settings, shapes, boundaries, num_spaces)
        assert isinstance(dxf_bytes, bytes)
        assert len(dxf_bytes) > 0


class TestApp:
    def setup_method(self):
        import app as app_module
        self.app = app_module.app
        self.client = self.app.test_client()

    def test_index_page(self):
        resp = self.client.get("/")
        assert resp.status_code == 200
        assert b"Parking Lot" in resp.data

    def test_index_has_visual_editor_tab(self):
        resp = self.client.get("/")
        assert b"Visual Editor" in resp.data
        assert b"tab-visual" in resp.data

    def test_index_has_json_tab(self):
        resp = self.client.get("/")
        assert b'id="config"' in resp.data
        assert b"tab-json" in resp.data

    def test_index_has_share_button(self):
        resp = self.client.get("/")
        assert b"shareBtn" in resp.data
        assert b"Share Link" in resp.data

    def test_index_has_color_editor(self):
        resp = self.client.get("/")
        assert b"ve-colors" in resp.data
        assert b"Add color" in resp.data

    def test_index_has_lot_editor(self):
        resp = self.client.get("/")
        assert b"ve-lots" in resp.data
        assert b"Add lot" in resp.data

    def test_index_has_dimension_fields(self):
        resp = self.client.get("/")
        assert b"ve-side" in resp.data
        assert b"ve-space_width" in resp.data
        assert b"ve-space_height" in resp.data
        assert b"ve-seed" in resp.data

    def test_index_has_pattern_selector(self):
        resp = self.client.get("/")
        assert b"ve-pattern" in resp.data

    def test_index_has_github_footer(self):
        resp = self.client.get("/")
        assert b"github.com/nemecec/stonegrid" in resp.data

    def test_preview_valid(self):
        resp = self.client.post(
            "/api/preview",
            json=SAMPLE_CONFIG,
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "svg" in data
        assert "<polygon" in data["svg"]

    def test_preview_rectangles(self):
        resp = self.client.post(
            "/api/preview",
            json=RECT_CONFIG,
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "svg" in data
        assert "rectangles" in data["info"]

    def test_preview_no_json(self):
        resp = self.client.post("/api/preview")
        assert resp.status_code in (400, 415)

    def test_preview_invalid_config(self):
        resp = self.client.post(
            "/api/preview",
            json={"lots": []},
            content_type="application/json",
        )
        data = resp.get_json()
        assert "error" in data

    def test_dxf_download(self):
        resp = self.client.post(
            "/api/dxf",
            json=SAMPLE_CONFIG,
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert len(resp.data) > 0

    def test_dxf_invalid_config(self):
        resp = self.client.post(
            "/api/dxf",
            json={"lots": [{"light": 50, "dark": 10}]},
            content_type="application/json",
        )
        assert resp.status_code == 400

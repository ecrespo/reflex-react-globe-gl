"""Tests for the JS helper builders and the imperative actions."""

from __future__ import annotations

import json

import reflex as rx
from reflex_base.event import EventSpec

import reflex_react_globe_gl as rg


class _S(rx.State):
    name: str = "x"
    palette: str = "Viridis"


def test_js_wraps_expression():
    assert str(rg.js("d => d.pop")) == "(d => d.pop)"


def test_js_keeps_state_var_data():
    var = rg.js(f"d => d.name === {_S.name}")
    data = var._get_all_var_data()
    assert data is not None and data.state
    assert "reflex___state" in str(var)
    assert "<reflex.Var>" not in str(var)


def test_constant():
    assert str(rg.constant("red")) == '(() => "red")'
    assert str(rg.constant(3)) == "(() => 3)"


def test_attr_nested_with_default():
    js = str(rg.attr("properties.NAME", "?"))
    assert '?.["properties"]?.["NAME"]' in js and '"?"' in js


def test_color_scale_static_and_var():
    static = str(rg.color_scale("d.sumWeight", "YlOrRd", (0, 1e7), "sqrt"))
    assert 'colorScale("YlOrRd", [0, 10000000.0], "sqrt", 1.0)(d.sumWeight)' in static
    dynamic = rg.color_scale("d.v", _S.palette)
    assert "reflex___state" in str(dynamic)
    assert dynamic._get_all_var_data() is not None


def test_tile_url():
    js = str(rg.tile_url("https://tile.openstreetmap.org/{z}/{x}/{y}.png"))
    assert js.startswith("((x, y, l) =>")
    assert "replace('{z}', l)" in js


def test_three_mesh_and_material():
    mesh = str(rg.three_mesh("BoxGeometry", [1, 2, 3], "MeshBasicMaterial", {"color": "red"}))
    assert "new window.ReflexGlobe.THREE.BoxGeometry(1, 2, 3)" in mesh
    assert 'MeshBasicMaterial({"color": "red"})' in mesh
    assert "MeshLambertMaterial" in str(rg.three_material())


def test_tooltip_template():
    js = str(rg.tooltip("<b>{properties.NAME}</b>"))
    assert js.startswith("(d =>") and "properties.NAME" in js


def _code(spec: EventSpec) -> str:
    return str(dict(spec.args)["javascript_code"]) if isinstance(spec.args, tuple) else str(spec)


def test_actions_are_call_script_specs():
    specs = [
        rg.fly_to("g", 10, 20, 1.5, 500),
        rg.point_of_view("g", altitude=2),
        rg.pause_animation("g"),
        rg.resume_animation("g"),
        rg.set_controls("g", autoRotate=True),
        rg.clear_tile_cache("g"),
        rg.run_js("g", "globe.controls().autoRotate = false"),
    ]
    for spec in specs:
        assert isinstance(spec, EventSpec)
    code = str(specs[0])
    assert "ReflexGlobe" in code and "pointOfView" in code
    assert json.dumps({"lat": 10, "lng": 20, "altitude": 1.5}).replace('"', "") in code.replace('\\"', "").replace(
        '"', ""
    )


def test_query_actions_take_callbacks():
    class Q(rx.State):
        @rx.event
        def got(self, value: dict):
            pass

    for spec in (
        rg.get_point_of_view("g", Q.got),
        rg.get_screen_coords("g", 0, 0, callback=Q.got),
        rg.to_globe_coords("g", 10, 10, callback=Q.got),
        rg.get_coords("g", 0, 0, callback=Q.got),
        rg.get_globe_radius("g", callback=Q.got),
    ):
        assert isinstance(spec, EventSpec)

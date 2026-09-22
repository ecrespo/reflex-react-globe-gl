"""Helpers to build JavaScript values for react-globe.gl accessor props.

Everything here returns an ``rx.Var`` whose JS expression is emitted verbatim
in the compiled page, so the resulting functions run in the browser.

The JS wrapper publishes a global ``ReflexGlobe`` namespace that these
expressions may use:

* ``window.ReflexGlobe.THREE`` – the ThreeJS module used by the globe;
* ``window.ReflexGlobe.colorScale(palette, domain, type, opacity)`` – color scales;
* ``window.ReflexGlobe.PALETTES`` – the built-in palettes.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any, Literal

from reflex_base.vars.base import Var, _decode_var_immutable

ScaleType = Literal["linear", "sqrt", "log", "pow"]

PALETTES = (
    "YlOrRd",
    "YlGnBu",
    "OrRd",
    "Blues",
    "Greens",
    "Reds",
    "Purples",
    "Viridis",
    "Inferno",
    "Magma",
    "Plasma",
    "Turbo",
    "Spectral",
    "RdYlGn",
    "RdBu",
)


def js(expression: str) -> Var[Any]:
    """Wrap a raw JavaScript expression (typically an arrow function).

    State vars may be embedded with f-strings; the resulting accessor is
    re-evaluated whenever those vars change::

        polygon_altitude=js(f"d => d.properties.ISO_A3 === {State.selected} ? 0.12 : 0.06")

    Example:
        ``point_altitude=js("d => d.pop * 1e-7")``

    Args:
        expression: A JavaScript expression.

    Returns:
        A Var rendered as-is in the compiled JSX.
    """
    var_data, expr = _decode_var_immutable(expression)
    return Var(_js_expr=f"({expr})", _var_type=Any, _var_data=var_data)


def constant(value: Any) -> Var[Any]:
    """Accessor that returns the same value for every datum.

    Needed for constant *strings* (e.g. colors): a plain string passed to an
    accessor prop is interpreted by globe.gl as an attribute name.

    Args:
        value: Any JSON-serializable value.

    Returns:
        A ``() => value`` JS function.
    """
    return js(f"() => {json.dumps(value)}")


def attr(path: str, default: Any = None) -> Var[Any]:
    """Accessor reading a (possibly nested) attribute, e.g. ``"properties.NAME"``.

    Args:
        path: Dotted attribute path.
        default: Value returned when the path is missing.

    Returns:
        A ``d => d?.a?.b`` JS function.
    """
    chain = "".join(f"?.[{json.dumps(p)}]" for p in path.split("."))
    return js(f"d => (d{chain} ?? {json.dumps(default)})")


def color_scale(
    value: str = "d",
    palette: str | Sequence[str] | Var = "YlOrRd",
    domain: Sequence[float] | Var = (0, 1),
    scale: ScaleType | Var = "linear",
    opacity: float | Var = 1.0,
) -> Var[Any]:
    """Accessor mapping a numeric expression to a color.

    Example (world population hexbins)::

        hex_top_color=color_scale("d.sumWeight", "YlOrRd", (0, 1e7), "sqrt")

    Args:
        value: JS expression of the value, using ``d`` for the datum
            (e.g. ``"d.properties.POP_EST"``). Use ``"t"``-style expressions for
            ``heatmap_color_fn`` / arc interpolators (the argument is always ``d``).
        palette: Built-in palette name (see ``PALETTES``) or a list of hex colors.
            Any argument may also be a state Var (e.g. ``State.palette``).
        domain: ``(min, max)`` of the input values.
        scale: ``linear``, ``sqrt``, ``log`` or ``pow``.
        opacity: Alpha of the output colors.

    Returns:
        A JS accessor function returning a CSS color string.
    """

    def _arg(v: Any) -> str:
        if isinstance(v, Var):
            return f"{v}"  # f-string formatting keeps the Var's state data
        if isinstance(v, (list, tuple)):
            return json.dumps(list(v))
        return json.dumps(v)

    args = ", ".join(_arg(a) for a in (palette, domain, scale, opacity))
    return js(f"d => window.ReflexGlobe.colorScale({args})({value})")


def tile_url(template: str) -> Var[Any]:
    """Slippy-map URL builder for ``globe_tile_engine_url``.

    Args:
        template: URL template with ``{x}``, ``{y}`` and ``{z}`` (or ``{l}``)
            placeholders, e.g. ``"https://tile.openstreetmap.org/{z}/{x}/{y}.png"``.
            ``{s}`` is replaced by a rotating ``a``/``b``/``c`` subdomain.

    Returns:
        A ``(x, y, l) => url`` JS function.
    """
    tpl = json.dumps(template)
    return js(
        "(x, y, l) => "
        f"{tpl}.replace('{{x}}', x).replace('{{y}}', y)"
        ".replace('{z}', l).replace('{l}', l)"
        ".replace('{s}', 'abc'[(x + y) % 3])"
    )


def three_mesh(
    geometry: str = "SphereGeometry",
    geometry_args: Sequence[Any] = (1, 16, 8),
    material: str = "MeshLambertMaterial",
    material_options: dict[str, Any] | None = None,
) -> Var[Any]:
    """Factory of ThreeJS meshes for ``object_three_object`` / ``custom_three_object``.

    Example::

        object_three_object=three_mesh("OctahedronGeometry", [1.5, 0],
                                       "MeshLambertMaterial",
                                       {"color": "palegreen", "transparent": True, "opacity": 0.7})

    Args:
        geometry: Name of a ``THREE.*Geometry`` class.
        geometry_args: Constructor arguments of the geometry.
        material: Name of a ``THREE.*Material`` class.
        material_options: Constructor options of the material.

    Returns:
        A ``() => new THREE.Mesh(...)`` JS function.
    """
    g_args = ", ".join(json.dumps(a) for a in geometry_args)
    m_opts = json.dumps(material_options or {})
    return js(
        "() => new window.ReflexGlobe.THREE.Mesh("
        f"new window.ReflexGlobe.THREE.{geometry}({g_args}), "
        f"new window.ReflexGlobe.THREE.{material}({m_opts}))"
    )


def three_material(material: str = "MeshLambertMaterial", options: dict[str, Any] | None = None) -> Var[Any]:
    """A ThreeJS material instance (e.g. for ``tile_material`` / ``polygon_cap_material``).

    Args:
        material: Name of a ``THREE.*Material`` class.
        options: Constructor options.

    Returns:
        A JS function returning a new material (usable as an accessor).
    """
    return js(f"() => new window.ReflexGlobe.THREE.{material}({json.dumps(options or {})})")


def tooltip(template: str) -> Var[Any]:
    """Tooltip accessor from an HTML template with ``{field}`` placeholders.

    Nested fields use dots: ``"<b>{properties.NAME}</b>"``. Values are HTML-escaped.

    Args:
        template: HTML template.

    Returns:
        A JS accessor returning the rendered HTML string.
    """
    tpl = json.dumps(template)
    return js(
        f"d => {tpl}.replace(/\\{{([\\w.]+)\\}}/g, (_, k) => "
        "String(k.split('.').reduce((o, p) => (o == null ? o : o[p]), d) ?? '')"
        ".replace(/[&<>\"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#39;'}[c])))"
    )

"""Event actions that call react-globe.gl imperative methods from Reflex.

Each function returns an ``EventSpec`` built with ``rx.call_script`` and can be
used directly as a frontend event trigger (``on_click=fly_to("g", 10, 20)``) or
returned / yielded from a backend event handler.

The globe must have an ``id``; that id is used to look it up in the
``window.ReflexGlobe`` registry maintained by the JS wrapper.
"""

from __future__ import annotations

import json
from typing import Any

import reflex as rx
from reflex_base.event import EventSpec


def _call(globe_id: str, method: str, *args: Any, callback: Any = None) -> EventSpec:
    js_args = ", ".join(json.dumps(a) for a in (globe_id, method, *args))
    code = f"window.ReflexGlobe && window.ReflexGlobe.call({js_args})"
    return rx.call_script(code, callback=callback) if callback is not None else rx.call_script(code)


def point_of_view(
    globe_id: str,
    lat: float | None = None,
    lng: float | None = None,
    altitude: float | None = None,
    transition_ms: int = 1000,
) -> EventSpec:
    """Move the camera to a geographic position.

    Args:
        globe_id: The globe component id.
        lat: Target latitude (omit to keep the current one).
        lng: Target longitude (omit to keep the current one).
        altitude: Target altitude in globe radii (omit to keep the current one).
        transition_ms: Animation duration.

    Returns:
        The event spec.
    """
    pov = {k: v for k, v in (("lat", lat), ("lng", lng), ("altitude", altitude)) if v is not None}
    return _call(globe_id, "pointOfView", pov, transition_ms)


fly_to = point_of_view


def get_point_of_view(globe_id: str, callback: Any) -> EventSpec:
    """Read the current camera position; ``callback`` receives ``{lat, lng, altitude}``.

    Args:
        globe_id: The globe component id.
        callback: Event handler receiving the point of view.

    Returns:
        The event spec.
    """
    return _call(globe_id, "pointOfView", callback=callback)


def pause_animation(globe_id: str) -> EventSpec:
    """Pause the render loop (saves CPU/GPU)."""
    return _call(globe_id, "pauseAnimation")


def resume_animation(globe_id: str) -> EventSpec:
    """Resume the render loop."""
    return _call(globe_id, "resumeAnimation")


def set_controls(globe_id: str, **options: Any) -> EventSpec:
    """Set OrbitControls attributes, e.g. ``set_controls("g", autoRotate=True, autoRotateSpeed=0.5)``.

    Args:
        globe_id: The globe component id.
        **options: OrbitControls attribute values (camelCase names).

    Returns:
        The event spec.
    """
    return _call(globe_id, "setControls", options)


def clear_tile_cache(globe_id: str) -> EventSpec:
    """Clear the slippy-map tile engine cache."""
    return _call(globe_id, "globeTileEngineClearCache")


def get_screen_coords(globe_id: str, lat: float, lng: float, altitude: float = 0, *, callback: Any) -> EventSpec:
    """Project geographic coordinates to viewport pixels; ``callback`` receives ``{x, y}``."""
    return _call(globe_id, "getScreenCoords", lat, lng, altitude, callback=callback)


def to_globe_coords(globe_id: str, x: float, y: float, *, callback: Any) -> EventSpec:
    """Geographic coordinates under a viewport pixel; ``callback`` receives ``{lat, lng}`` or None."""
    return _call(globe_id, "toGlobeCoords", x, y, callback=callback)


def get_coords(globe_id: str, lat: float, lng: float, altitude: float = 0, *, callback: Any) -> EventSpec:
    """Cartesian scene coordinates of a geographic point; ``callback`` receives ``{x, y, z}``."""
    return _call(globe_id, "getCoords", lat, lng, altitude, callback=callback)


def get_globe_radius(globe_id: str, *, callback: Any) -> EventSpec:
    """Globe radius in scene units; ``callback`` receives a number."""
    return _call(globe_id, "getGlobeRadius", callback=callback)


def run_js(globe_id: str, code: str) -> EventSpec:
    """Run arbitrary JS with the globe handle bound to ``globe`` (and ``THREE``).

    Example: ``run_js("g", "globe.scene().fog = null")``.

    Args:
        globe_id: The globe component id.
        code: JavaScript statements.

    Returns:
        The event spec.
    """
    return rx.call_script(
        "(() => { const globe = window.ReflexGlobe && window.ReflexGlobe.get("
        + json.dumps(globe_id)
        + "); if (!globe) return; const THREE = window.ReflexGlobe.THREE; "
        + code
        + " })()"
    )

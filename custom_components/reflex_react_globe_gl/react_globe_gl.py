"""Reflex wrapper for react-globe.gl.

`react-globe.gl <https://github.com/vasturiano/react-globe.gl>`_ renders data
visualization layers on a 3D globe (ThreeJS/WebGL). This module exposes the full
``react-globe.gl`` prop and event API as a Reflex component, through a small JS
wrapper (``globe_wrapper.js``) that adds responsive sizing, JSON-safe events,
stable accessors and a declarative API for camera, controls and material.

Accessor props (``point_lat``, ``hex_top_color``...) accept, like upstream:

* a **string**: the name of the attribute to read from each datum;
* a **number / bool**: a constant;
* a **JS function**: build it with :func:`reflex_react_globe_gl.js`,
  :func:`~reflex_react_globe_gl.constant` or
  :func:`~reflex_react_globe_gl.color_scale`.

Note that a plain string is always interpreted as an attribute name, so a
constant color must be written as ``constant("red")``.
"""

from __future__ import annotations

from typing import Any

import reflex as rx
from reflex_base.components.component import NoSSRComponent, field
from reflex_base.event import EventHandler
from reflex_base.vars.base import Var

REACT_GLOBE_GL_VERSION = "2.38.0"
THREE_VERSION = "0.186.0"

# The wrapper is shipped inside the package and linked into the app's
# ``assets/external`` directory at compile time.
_WRAPPER = rx.asset("globe_wrapper.js", shared=True)


# ---------------------------------------------------------------------------
# Event specs. The JS wrapper sanitizes every argument, so they are plain JSON
# (datum dicts, coords dicts, mouse-event info) by the time Reflex sees them.
# Handlers may accept a prefix of the arguments (e.g. only the datum), and the
# specs deliberately carry no return annotation, which disables Reflex's strict
# argument type check: handlers can annotate them as ``dict``,
# ``dict[str, float]``, ``dict | None``, a TypedDict, etc.
# ---------------------------------------------------------------------------


def _no_args() -> tuple[()]:
    return ()


def _layer_click(obj: Var[Any], event: Var[Any], coords: Var[Any]):
    """JS ``(obj, event, coords)`` -> handler ``(datum, coords, event)``."""
    return obj, coords, event


def _layer_hover(obj: Var[Any], prev: Var[Any]):
    """JS ``(obj, prevObj)`` -> handler ``(datum | None, previous | None)``."""
    return obj, prev


def _globe_click(coords: Var[Any], event: Var[Any]):
    """JS ``({lat, lng}, event)`` -> handler ``(coords, event)``."""
    return coords, event


def _pov(pov: Var[Any]):
    """JS ``({lat, lng, altitude})`` -> handler ``(pov)``."""
    return (pov,)


def _html_click(obj: Var[Any], event: Var[Any]):
    """Wrapper ``(datum, event)`` -> handler ``(datum, event)``."""
    return obj, event


def _html_hover(obj: Var[Any]):
    """Wrapper ``(datum | None)`` -> handler ``(datum | None)``."""
    return (obj,)


class Globe(NoSSRComponent):
    """A 3D data-visualization globe (react-globe.gl).

    Sizing: by default the globe fills its container (100% x 100%, measured
    with a ResizeObserver). Give the container a height (``height="600px"``
    style prop on the component itself or on a parent), or pass explicit
    ``width`` / ``height`` in pixels.

    Imperative methods (``pointOfView``, ``controls``...) are available through
    the helpers in :mod:`reflex_react_globe_gl.actions` using the component
    ``id``.
    """

    library = _WRAPPER.importable_path
    tag = "ReactGlobeGl"
    lib_dependencies: list[str] = [
        f"react-globe.gl@{REACT_GLOBE_GL_VERSION}",
        f"three@{THREE_VERSION}",
    ]

    # --- Canvas size (pixels). Omit both to fill the container. ---
    width: Var[int] = field(doc="Canvas width in pixels. Defaults to the container width.")
    height: Var[int] = field(doc="Canvas height in pixels. Defaults to the container height.")

    # --- Init-only props (only read on mount) ---
    animate_in: Var[bool] = field(doc="Animate the globe initialization (scale + rotate in). Mount only.")
    wait_for_globe_ready: Var[bool] = field(doc="Wait until the globe image loads before rendering layers. Mount only.")
    renderer_config: Var[dict[str, Any]] = field(
        doc="Config passed to the ThreeJS WebGLRenderer constructor. Mount only."
    )

    # --- Container layout ---
    globe_offset: Var[list[float | int]] = field(doc="Position offset of the globe relative to the canvas center.")
    background_color: Var[str] = field(doc="Background color.")
    background_image_url: Var[str | None] = field(
        doc="URL of the image to be used as background to the globe. If no image is provided, the background color is shown instead."
    )

    # --- Globe layer ---
    globe_image_url: Var[str | None] = field(
        doc="URL of the image used in the material that wraps the globe. This image should follow an equirectangular projection. If no image is provided, the globe is represented as a black sphere."
    )
    bump_image_url: Var[str | None] = field(
        doc="URL of the image used to create a bump map in the material, to represent the globe's terrain. This image should follow an equirectangular projection."
    )
    globe_tile_engine_url: Var[Any] = field(
        doc="Function that defines the URL of the slippy map tile engine to cover the globe surface. The slippy map coordinates x, y and l (zoom level) are passed as arguments and the function is expected to return a URL string. A falsy value will disable the tiling engine."
    )
    globe_tile_engine_max_level: Var[int] = field(doc="Maximum zoom level of the tile engine (default 17).")
    show_globe: Var[bool] = field(doc="Whether to show the globe surface itself.")
    show_graticules: Var[bool] = field(
        doc="Whether to show a graticule grid demarking latitude and longitude lines at every 10 degrees."
    )
    show_atmosphere: Var[bool] = field(
        doc="Whether to show a bright halo surrounding the globe, representing the atmosphere."
    )
    atmosphere_color: Var[str] = field(doc="The color of the atmosphere.")
    atmosphere_altitude: Var[float | int] = field(
        doc="The max altitude of the atmosphere, in terms of globe radius units."
    )
    globe_curvature_resolution: Var[float | int] = field(
        doc="Resolution in angular degrees of the sphere curvature. The finer the resolution, the more the globe is fragmented into smaller faces to approximate the spheric surface, at the cost of performance."
    )
    globe_material: Var[Any] = field(
        doc="ThreeJS material used to wrap the globe. Can be used for more advanced styling of the globe, like in this example."
    )

    # --- Points layer ---
    points_data: Var[list[Any]] = field(
        doc="List of points to represent in the points map layer. Each point is displayed as a cylindrical 3D object rising perpendicularly from the surface of the globe."
    )
    point_lat: Var[Any] = field(
        doc="Point object accessor function, attribute or a numeric constant for the cylinder's center latitude coordinate."
    )
    point_lng: Var[Any] = field(
        doc="Point object accessor function, attribute or a numeric constant for the cylinder's center longitude coordinate."
    )
    point_color: Var[Any] = field(doc="Point object accessor function or attribute for the cylinder color.")
    point_altitude: Var[Any] = field(
        doc="Point object accessor function, attribute or a numeric constant for the cylinder's altitude in terms of globe radius units (0 = 0 altitude (flat circle), 1 = globe radius)."
    )
    point_radius: Var[Any] = field(
        doc="Point object accessor function, attribute or a numeric constant for the cylinder's radius, in angular degrees."
    )
    point_resolution: Var[float | int] = field(
        doc="Radial geometric resolution of each cylinder, expressed in how many slice segments to divide the circumference. Higher values yield smoother cylinders."
    )
    points_merge: Var[bool] = field(
        doc="Whether to merge all the point meshes into a single ThreeJS object, for improved rendering performance. Visually both options are equivalent, setting this option only affects the internal organization of the ThreeJS objects."
    )
    points_transition_duration: Var[float | int] = field(
        doc="Duration (ms) of the transition to animate point changes involving geometry modifications. A value of 0 will move the objects immediately to their final position. New objects are animated by scaling them from the ground up. Only works if pointsMerge is disabled."
    )
    point_label: Var[Any] = field(
        doc="Point object accessor function or attribute for label (shown as tooltip). Supports plain text or HTML content."
    )

    # --- Arcs layer ---
    arcs_data: Var[list[Any]] = field(
        doc="List of links to represent in the arcs map layer. Each link is displayed as an arc line that rises from the surface of the globe, connecting the start and end coordinates."
    )
    arc_start_lat: Var[Any] = field(
        doc="Arc object accessor function, attribute or a numeric constant for the line's start latitude coordinate."
    )
    arc_start_lng: Var[Any] = field(
        doc="Arc object accessor function, attribute or a numeric constant for the line's start longitude coordinate."
    )
    arc_start_altitude: Var[Any] = field(
        doc="Arc object accessor function, attribute or a numeric constant for the line's start altitude."
    )
    arc_end_lat: Var[Any] = field(
        doc="Arc object accessor function, attribute or a numeric constant for the line's end latitude coordinate."
    )
    arc_end_lng: Var[Any] = field(
        doc="Arc object accessor function, attribute or a numeric constant for the line's end longitude coordinate."
    )
    arc_end_altitude: Var[Any] = field(
        doc="Arc object accessor function, attribute or a numeric constant for the line's end altitude."
    )
    arc_color: Var[Any] = field(
        doc="Arc object accessor function or attribute for the line's color. Also supports color gradients by passing an array of colors, or a color interpolator function."
    )
    arc_altitude: Var[Any] = field(
        doc="Arc object accessor function, attribute or a numeric constant for the arc's maximum altitude (ocurring at the half-way distance between the two points) in terms of globe radius units (0 = 0 altitude (ground line), 1 = globe radius). If a value of null or undefined is used, the altitude is..."
    )
    arc_altitude_auto_scale: Var[Any] = field(
        doc="Arc object accessor function, attribute or a numeric constant for the scale of the arc's automatic altitude, in terms of units of the great-arc distance between the two points. A value of 1 indicates the arc should be as high as its length on the ground. Only applicable if arcAltitude is not set."
    )
    arc_stroke: Var[Any] = field(
        doc="Arc object accessor function, attribute or a numeric constant for the line's diameter, in angular degrees. A value of null or undefined will render a ThreeJS Line whose width is constant (1px) regardless of the camera distance. Otherwise, a TubeGeometry is used."
    )
    arc_curve_resolution: Var[float | int] = field(
        doc="Arc's curve resolution, expressed in how many straight line segments to divide the curve by. Higher values yield smoother curves."
    )
    arc_circular_resolution: Var[float | int] = field(
        doc="Radial geometric resolution of each line, expressed in how many slice segments to divide the tube's circumference. Only applicable when using Tube geometries (defined arcStroke)."
    )
    arc_dash_length: Var[Any] = field(
        doc="Arc object accessor function, attribute or a numeric constant for the length of the dashed segments in the arc, in terms of relative length of the whole line (1 = full line length)."
    )
    arc_dash_gap: Var[Any] = field(
        doc="Arc object accessor function, attribute or a numeric constant for the length of the gap between dash segments, in terms of relative line length."
    )
    arc_dash_initial_gap: Var[Any] = field(
        doc="Arc object accessor function, attribute or a numeric constant for the length of the initial gap before the first dash segment, in terms of relative line length."
    )
    arc_dash_animate_time: Var[Any] = field(
        doc="Arc object accessor function, attribute or a numeric constant for the time duration (in ms) to animate the motion of dash positions from the start to the end point for a full line length. A value of 0 disables the animation."
    )
    arcs_transition_duration: Var[float | int] = field(
        doc="Duration (ms) of the transition to animate arc changes involving geometry modifications. A value of 0 will move the arcs immediately to their final position. New arcs are animated by rising them from the ground up."
    )
    arc_label: Var[Any] = field(
        doc="Arc object accessor function or attribute for label (shown as tooltip). Supports plain text or HTML content."
    )

    # --- Polygons layer ---
    polygons_data: Var[list[Any]] = field(
        doc="List of polygon shapes to represent in the polygons map layer. Each polygon is displayed as a shaped cone that extrudes from the surface of the globe."
    )
    polygon_geo_json_geometry: Var[Any] = field(
        doc="Polygon object accessor function or attribute for the GeoJson geometry specification of the polygon's shape. The returned value should have a minimum of two fields: type and coordinates. Only GeoJson geometries of type Polygon or MultiPolygon are supported, other types will be skipped."
    )
    polygon_cap_color: Var[Any] = field(
        doc="Polygon object accessor function or attribute for the color of the top surface."
    )
    polygon_cap_material: Var[Any] = field(
        doc="Polygon object accessor function, attribute or material object for the ThreeJS material to use in the top surface. This prop takes precedence over polygonCapColor, which will be ignored if both are defined."
    )
    polygon_side_color: Var[Any] = field(
        doc="Polygon object accessor function or attribute for the color of the cone sides."
    )
    polygon_side_material: Var[Any] = field(
        doc="Polygon object accessor function, attribute or material object for the ThreeJS material to use in the cone sides. This prop takes precedence over polygonSideColor, which will be ignored if both are defined."
    )
    polygon_stroke_color: Var[Any] = field(
        doc="Polygon object accessor function or attribute for the color to stroke the polygon perimeter. A falsy value will disable the stroking."
    )
    polygon_altitude: Var[Any] = field(
        doc="Polygon object accessor function, attribute or a numeric constant for the polygon cone's altitude in terms of globe radius units (0 = 0 altitude (flat polygon), 1 = globe radius)."
    )
    polygon_cap_curvature_resolution: Var[Any] = field(
        doc="Polygon object accessor function, attribute or a numeric constant for the resolution (in angular degrees) of the cap surface curvature. The finer the resolution, the more the polygon is fragmented into smaller faces to approximate the spheric surface, at the cost of performance."
    )
    polygons_transition_duration: Var[float | int] = field(
        doc="Duration (ms) of the transition to animate polygon altitude changes. A value of 0 will size the cone immediately to their final altitude. New polygons are animated by rising them from the ground up."
    )
    polygon_label: Var[Any] = field(
        doc="Polygon object accessor function or attribute for label (shown as tooltip). Supports plain text or HTML content."
    )

    # --- Paths layer ---
    paths_data: Var[list[Any]] = field(
        doc="List of lines to represent in the paths map layer. Each path is displayed as a line that connects all the coordinate pairs in the path array."
    )
    path_points: Var[Any] = field(
        doc="Path object accessor function, attribute or an array for the set of points that define the path line. By default, each path point is assumed to be a 2-position array ([, ]). This default behavior can be modified using the pathPointLat and pathPointLng methods."
    )
    path_point_lat: Var[Any] = field(
        doc="Path point object accessor function, attribute or a numeric constant for the latitude coordinate."
    )
    path_point_lng: Var[Any] = field(
        doc="Path point object accessor function, attribute or a numeric constant for the longitude coordinate."
    )
    path_point_alt: Var[Any] = field(
        doc="Path point object accessor function, attribute or a numeric constant for the point altitude, in terms of globe radius units (0 = 0 altitude (ground), 1 = globe radius)."
    )
    path_resolution: Var[float | int] = field(
        doc="The path's angular resolution, in lat/lng degrees. If the ground distance (excluding altitude) between two adjacent path points is larger than this value, the line segment will be interpolated in order to approximate the curvature of the sphere surface. Lower values yield more perfectly curved..."
    )
    path_color: Var[Any] = field(
        doc="Path object accessor function or attribute for the line's color. Also supports color gradients by passing an array of colors, or a color interpolator function. Transparent colors are not supported in Fat Lines with set width."
    )
    path_stroke: Var[Any] = field(
        doc="Path object accessor function, attribute or a numeric constant for the line's diameter, in angular degrees. A value of null or undefined will render a ThreeJS Line whose width is constant (1px) regardless of the camera distance. Otherwise, a FatLine is used."
    )
    path_dash_length: Var[Any] = field(
        doc="Path object accessor function, attribute or a numeric constant for the length of the dashed segments in the path line, in terms of relative length of the whole line (1 = full line length)."
    )
    path_dash_gap: Var[Any] = field(
        doc="Path object accessor function, attribute or a numeric constant for the length of the gap between dash segments, in terms of relative line length."
    )
    path_dash_initial_gap: Var[Any] = field(
        doc="Path object accessor function, attribute or a numeric constant for the length of the initial gap before the first dash segment, in terms of relative line length."
    )
    path_dash_animate_time: Var[Any] = field(
        doc="Path object accessor function, attribute or a numeric constant for the time duration (in ms) to animate the motion of dash positions from the start to the end point for a full line length. A value of 0 disables the animation."
    )
    path_transition_duration: Var[float | int] = field(
        doc="Duration (ms) of the transition to animate path changes. A value of 0 will move the paths immediately to their final position. New paths are animated from start to end."
    )
    path_label: Var[Any] = field(
        doc="Path object accessor function or attribute for label (shown as tooltip). Supports plain text or HTML content."
    )

    # --- Heatmaps layer ---
    heatmaps_data: Var[list[Any]] = field(
        doc="List of heatmap datasets to represent in the heatmaps map layer. Each set of points is represented as an individual global heatmap with varying color and/or altitude, according to the point density. It uses a Gaussian KDE to perform the density estimation, based on the great-arc distance between..."
    )
    heatmap_points: Var[Any] = field(
        doc="Heatmap object accessor function, attribute or an array for the set of points that define the heatmap. By default, each point is assumed to be a 2-position array ([, ]). This default behavior can be modified using the heatmapPointLat and heatmapPointLng methods."
    )
    heatmap_point_lat: Var[Any] = field(
        doc="Heatmap point object accessor function, attribute or a numeric constant for the latitude coordinate."
    )
    heatmap_point_lng: Var[Any] = field(
        doc="Heatmap point object accessor function, attribute or a numeric constant for the longitude coordinate."
    )
    heatmap_point_weight: Var[Any] = field(
        doc="Heatmap point object accessor function, attribute or a numeric constant for the weight of the point. The weight of a point determines its influence on the density of the surrounding area."
    )
    heatmap_bandwidth: Var[Any] = field(
        doc="Heatmap object accessor function, attribute or a numeric constant for the heatmap bandwidth, in angular degrees. The bandwidth is an internal parameter of the Gaussian kernel function and defines how localized is the influence of a point on distant locations. A narrow bandwidth leads to a more..."
    )
    heatmap_color_fn: Var[Any] = field(
        doc="Heatmap object accessor function or attribute for the color interpolator function to represent density in the heatmap. This function should receive a number between 0 and 1 (or potentially higher if saturation > 1), and return a color string."
    )
    heatmap_color_saturation: Var[Any] = field(
        doc="Heatmap object accessor function, attribute or a numeric constant for the color scale saturation. The saturation is a multiplier of the normalized density value ([0,1]) before passing it to the color interpolation function. It can be used to dampen outlier peaks in density and bring the data..."
    )
    heatmap_base_altitude: Var[Any] = field(
        doc="Heatmap object accessor function, attribute or a numeric constant for the heatmap base floor altitude in terms of globe radius units (0 = 0 altitude, 1 = globe radius)."
    )
    heatmap_top_altitude: Var[Any] = field(
        doc="Heatmap object accessor function, attribute or a numeric constant for the heatmap top peak altitude in terms of globe radius units (0 = 0 altitude, 1 = globe radius). An equal value to the base altitude will yield a surface flat heatmap. If a top altitude is set, the variations in density will..."
    )
    heatmaps_transition_duration: Var[float | int] = field(
        doc="Duration (ms) of the transition to animate heatmap changes. A value of 0 will set the heatmap colors/altitudes immediately in their final position. New heatmaps are animated by rising them from the ground up and gently fading in through the color scale."
    )

    # --- Hex Bin layer ---
    hex_bin_points_data: Var[list[Any]] = field(
        doc="List of points to aggregate using the hex bin map layer. Each point is added to an hexagonal prism 3D object that represents all the points within a tesselated portion of the space."
    )
    hex_bin_point_lat: Var[Any] = field(
        doc="Point object accessor function, attribute or a numeric constant for the latitude coordinate."
    )
    hex_bin_point_lng: Var[Any] = field(
        doc="Point object accessor function, attribute or a numeric constant for the longitude coordinate."
    )
    hex_bin_point_weight: Var[Any] = field(
        doc="Point object accessor function, attribute or a numeric constant for the weight of the point. Weights for points in the same bin are summed and determine the hexagon default altitude."
    )
    hex_bin_resolution: Var[float | int] = field(
        doc="The geographic binning resolution as defined by H3. Determines the area of the hexagons that tesselate the globe's surface. Accepts values between 0 and 15. Level 0 partitions the earth in 122 (mostly) hexagonal cells. Each subsequent level sub-divides the previous in roughly 7 hexagons."
    )
    hex_margin: Var[Any] = field(
        doc="The radial margin of each hexagon. Margins above 0 will create gaps between adjacent hexagons and serve only a visual purpose, as the data points within the margin still contribute to the hexagon's data. The margin is specified in terms of fraction of the hexagon's surface diameter. Values below..."
    )
    hex_altitude: Var[Any] = field(
        doc="The altitude of each hexagon, in terms of globe radius units (0 = 0 altitude (flat hexagon), 1 = globe radius). This property also supports using an accessor method based on the hexagon's aggregated data, following the syntax: hexAltitude(({ points, sumWeight, center: { lat, lng }}) => ...)...."
    )
    hex_top_curvature_resolution: Var[float | int] = field(
        doc="The resolution (in angular degrees) of the top surface curvature. The finer the resolution, the more the top area is fragmented into smaller faces to approximate the spheric surface, at the cost of performance."
    )
    hex_top_color: Var[Any] = field(
        doc="Accessor method for each hexagon's top color. The method should follow the signature: hexTopColor(({ points, sumWeight, center: { lat, lng }}) => ...) and return a color string."
    )
    hex_side_color: Var[Any] = field(
        doc="Accessor method for each hexagon's side color. The method should follow the signature: hexSideColor(({ points, sumWeight, center: { lat, lng }}) => ...) and return a color string."
    )
    hex_bin_merge: Var[bool] = field(
        doc="Whether to merge all the hexagon meshes into a single ThreeJS object, for improved rendering performance. Visually both options are equivalent, setting this option only affects the internal organization of the ThreeJS objects."
    )
    hex_transition_duration: Var[float | int] = field(
        doc="Duration (ms) of the transition to animate hexagon changes related to geometry modifications (altitude, radius). A value of 0 will move the hexagons immediately to their final position. New hexagons are animated by scaling them from the ground up. Only works if hexBinMerge is disabled."
    )
    hex_label: Var[Any] = field(
        doc="Hex object accessor function or attribute for label (shown as tooltip). An hex object includes all points binned, and has the syntax: { points, sumWeight, center: { lat, lng } }. Supports plain text or HTML content."
    )

    # --- Hexed Polygons layer ---
    hex_polygons_data: Var[list[Any]] = field(
        doc="List of polygon shapes to represent in the hexed polygons map layer. Each polygon is displayed as a tesselated group of hexagons that approximate the polygons shape according to the resolution specified in hexPolygonResolution."
    )
    hex_polygon_geo_json_geometry: Var[Any] = field(
        doc="Hexed polygon object accessor function or attribute for the GeoJson geometry specification of the polygon's shape. The returned value should have a minimum of two fields: type and coordinates. Only GeoJson geometries of type Polygon or MultiPolygon are supported, other types will be skipped."
    )
    hex_polygon_color: Var[Any] = field(
        doc="Hexed polygon object accessor function or attribute for the color of each hexagon in the polygon."
    )
    hex_polygon_altitude: Var[Any] = field(
        doc="Hexed polygon object accessor function, attribute or a numeric constant for the polygon's hexagons altitude in terms of globe radius units (0 = 0 altitude, 1 = globe radius)."
    )
    hex_polygon_resolution: Var[Any] = field(
        doc="Hexed polygon object accessor function, attribute or a numeric constant for the geographic binning resolution as defined by H3. Determines the area of the hexagons that tesselate the globe's surface. Accepts values between 0 and 15. Level 0 partitions the earth in 122 (mostly) hexagonal cells...."
    )
    hex_polygon_margin: Var[Any] = field(
        doc="Hexed polygon object accessor function, attribute or a numeric constant for the radial margin of each hexagon. Margins above 0 will create gaps between adjacent hexagons within a polygon. The margin is specified in terms of fraction of the hexagon's surface diameter. Values below 0 or above 1..."
    )
    hex_polygon_use_dots: Var[Any] = field(
        doc="Hexed polygon object accessor function, attribute or a boolean constant for whether to represent each polygon point as a circular dot instead of an hexagon."
    )
    hex_polygon_curvature_resolution: Var[Any] = field(
        doc="Hexed polygon object accessor function, attribute or a numeric constant for the resolution (in angular degrees) of each hexed polygon surface curvature. The finer the resolution, the more the polygon hexes are fragmented into smaller faces to approximate the spheric surface, at the cost of..."
    )
    hex_polygon_dot_resolution: Var[Any] = field(
        doc="Hexed polygon object accessor function, attribute or a numeric constant for the resolution of each circular dot, expressed in how many slice segments to divide the circumference. Higher values yield smoother circles, at the cost of performance. This is only applicable in dot representation mode."
    )
    hex_polygons_transition_duration: Var[float | int] = field(
        doc="Duration (ms) of the transition to animate hexed polygons altitude and margin changes. A value of 0 will move the hexagons immediately to their final state. New hexed polygons are animated by sizing each hexagon from 0 radius."
    )
    hex_polygon_label: Var[Any] = field(
        doc="Hexed polygon object accessor function or attribute for label (shown as tooltip). Supports plain text or HTML content."
    )

    # --- Tiles layer ---
    tiles_data: Var[list[Any]] = field(
        doc="List of tiles to represent in the tiles map layer. Each tile is displayed as a spherical surface segment. The segments can be placed side-by-side for a tiled surface and each can be styled separately."
    )
    tile_lat: Var[Any] = field(
        doc="Tile object accessor function, attribute or a numeric constant for the segment's centroid latitude coordinate."
    )
    tile_lng: Var[Any] = field(
        doc="Tile object accessor function, attribute or a numeric constant for the segment's centroid longitude coordinate."
    )
    tile_altitude: Var[Any] = field(
        doc="Tile object accessor function, attribute or a numeric constant for the segment's altitude in terms of globe radius units."
    )
    tile_width: Var[Any] = field(
        doc="Tile object accessor function, attribute or a numeric constant for the segment's longitudinal width, in angular degrees."
    )
    tile_height: Var[Any] = field(
        doc="Tile object accessor function, attribute or a numeric constant for the segment's latitudinal height, in angular degrees."
    )
    tile_use_globe_projection: Var[Any] = field(
        doc="Tile object accessor function, attribute or a boolean constant for whether to use the globe's projection to shape the segment to its relative tiled position (true), or break free from this projection and shape the segment as if it would be laying directly on the equatorial perimeter (false)."
    )
    tile_material: Var[Any] = field(
        doc="Tile object accessor function, attribute or material object for the ThreeJS material used to style the segment's surface."
    )
    tile_curvature_resolution: Var[Any] = field(
        doc="Tile object accessor function, attribute or a numeric constant for the resolution (in angular degrees) of the surface curvature. The finer the resolution, the more the tile geometry is fragmented into smaller faces to approximate the spheric surface, at the cost of performance."
    )
    tiles_transition_duration: Var[float | int] = field(
        doc="Duration (ms) of the transition to animate tile changes involving geometry modifications. A value of 0 will move the tiles immediately to their final position. New tiles are animated by scaling them from the centroid outwards."
    )
    tile_label: Var[Any] = field(
        doc="Tile object accessor function or attribute for label (shown as tooltip). Supports plain text or HTML content."
    )

    # --- Particles layer ---
    particles_data: Var[list[Any]] = field(
        doc="List of particle sets to represent in the particles map layer. Each particle set is displayed as a group of Points. Each point in the group is a geometry vertex and can be individually positioned anywhere relative to the globe."
    )
    particles_list: Var[Any] = field(
        doc="Particle set accessor function or attribute for the list of particles in the set. By default, the data structure is expected to be an array of arrays of individual particle objects."
    )
    particle_lat: Var[Any] = field(
        doc="Particle object accessor function, attribute or a numeric constant for the latitude coordinate."
    )
    particle_lng: Var[Any] = field(
        doc="Particle object accessor function, attribute or a numeric constant for the longitude coordinate."
    )
    particle_altitude: Var[Any] = field(
        doc="Particle object accessor function, attribute or a numeric constant for the altitude in terms of globe radius units."
    )
    particles_size: Var[Any] = field(
        doc="Particle set accessor function, attribute or a numeric constant for the size of all the particles in the group."
    )
    particles_size_attenuation: Var[Any] = field(
        doc="Particle set accessor function, attribute or a boolean constant for whether the size of each particle on the screen should be attenuated according to the distance to the camera."
    )
    particles_color: Var[Any] = field(
        doc="Particle set accessor function or attribute for the color of all the particles in the group. This setting will be ignored if particlesTexture is defined."
    )
    particles_texture: Var[Any] = field(
        doc="Particle set accessor function or attribute for the Texture to be applied to all the particles in the group."
    )
    particle_label: Var[Any] = field(
        doc="Particle object accessor function or attribute for label (shown as tooltip). Supports plain text or HTML content."
    )

    # --- Rings Layer ---
    rings_data: Var[list[Any]] = field(
        doc="List of self-propagating ripple rings to represent in the rings map layer. Each data point is displayed as an animated set of concentric circles that propagate outwards from (or inwards to) a central point through the spherical surface."
    )
    ring_lat: Var[Any] = field(
        doc="Ring object accessor function, attribute or a numeric constant for each circle's center latitude coordinate."
    )
    ring_lng: Var[Any] = field(
        doc="Ring object accessor function, attribute or a numeric constant for each circle's center longitude coordinate."
    )
    ring_altitude: Var[Any] = field(
        doc="Ring object accessor function, attribute or a numeric constant for the circle's altitude in terms of globe radius units."
    )
    ring_color: Var[Any] = field(
        doc="Ring object accessor function or attribute for the stroke color of each ring. Also supports radial color gradients by passing an array of colors, or a color interpolator function."
    )
    ring_resolution: Var[float | int] = field(
        doc="Geometric resolution of each circle, expressed in how many slice segments to divide the circumference. Higher values yield smoother circles."
    )
    ring_max_radius: Var[Any] = field(
        doc="Ring object accessor function, attribute or a numeric constant for the maximum outer radius of the circles, at which the rings stop propagating and are removed. Defined in angular degrees."
    )
    ring_propagation_speed: Var[Any] = field(
        doc="Ring object accessor function, attribute or a numeric constant for the propagation velocity of the rings, defined in degrees/second. Setting a negative value will invert the direction and cause the rings to propagate inwards from the maxRadius."
    )
    ring_repeat_period: Var[Any] = field(
        doc="Ring object accessor function, attribute or a numeric constant for the interval of time (in ms) to wait between consecutive auto-generated concentric circles. A value less or equal than 0 will disable the repetition and emit a single ring."
    )

    # --- Labels layer ---
    labels_data: Var[list[Any]] = field(doc="List of label objects to represent in the labels map layer.")
    label_lat: Var[Any] = field(
        doc="Label object accessor function, attribute or a numeric constant for the latitude coordinate."
    )
    label_lng: Var[Any] = field(
        doc="Label object accessor function, attribute or a numeric constant for the longitude coordinate."
    )
    label_text: Var[Any] = field(doc="Label object accessor function or attribute for the label text.")
    label_color: Var[Any] = field(doc="Label object accessor function or attribute for the label color.")
    label_altitude: Var[Any] = field(
        doc="Label object accessor function, attribute or a numeric constant for the label altitude in terms of globe radius units."
    )
    label_size: Var[Any] = field(
        doc="Label object accessor function, attribute or a numeric constant for the label text height, in angular degrees."
    )
    label_type_face: Var[Any] = field(
        doc="Text font typeface JSON object. Supports any typeface font generated by Facetype.js."
    )
    label_rotation: Var[Any] = field(
        doc="Label object accessor function, attribute or a numeric constant for the label rotation in degrees. The rotation is performed clockwise along the axis of its latitude parallel plane."
    )
    label_resolution: Var[float | int] = field(
        doc="The text geometric resolution of each label, expressed in how many segments to use in the text curves. Higher values yield smoother labels."
    )
    label_include_dot: Var[Any] = field(
        doc="Label object accessor function, attribute or a bool constant for whether to include a dot marker next to the text indicating the exact lat, lng coordinates of the label. If enabled the text will be rendered offset from the dot."
    )
    label_dot_radius: Var[Any] = field(
        doc="Label object accessor function, attribute or a numeric constant for the radius of the dot marker, in angular degrees."
    )
    label_dot_orientation: Var[Any] = field(
        doc="Label object accessor function or attribute for the orientation of the label if the dot marker is present. Possible values are right, top and bottom."
    )
    labels_transition_duration: Var[float | int] = field(
        doc="Duration (ms) of the transition to animate label changes involving position modifications (lat, lng, altitude, rotation). A value of 0 will move the labels immediately to their final position. New labels are animated by scaling their size."
    )
    label_label: Var[Any] = field(
        doc="Label object accessor function or attribute for its own tooltip label. Supports plain text or HTML content."
    )

    # --- HTML Elements layer ---
    html_elements_data: Var[list[Any]] = field(
        doc="List objects to represent in the HTML elements map layer. Each HTML element is rendered using ThreeJS CSS2DRenderer."
    )
    html_lat: Var[Any] = field(
        doc="HTML element accessor function, attribute or a numeric constant for the latitude coordinate of the element's central position."
    )
    html_lng: Var[Any] = field(
        doc="HTML element accessor function, attribute or a numeric constant for the longitude coordinate of the element's central position."
    )
    html_altitude: Var[Any] = field(
        doc="HTML element accessor function, attribute or a numeric constant for the altitude coordinate of the element's position, in terms of globe radius units."
    )
    html_element: Var[Any] = field(
        doc="Accessor function or attribute to retrieve the DOM element to use. Should return an instance of HTMLElement."
    )
    html_element_visibility_modifier: Var[Any] = field(
        doc="Custom function that defines how elements are shown/hidden according to whether they are in front or behind the globe. The function receives two arguments (elem, isVisible), the HTML element and a boolean indicating if the element should be visible. By default the Three object itself is..."
    )
    html_transition_duration: Var[float | int] = field(
        doc="Duration (ms) of the transition to animate HTML elements position changes. A value of 0 will move the elements immediately to their final position."
    )

    # --- 3D Objects layer ---
    objects_data: Var[list[Any]] = field(
        doc="Getter/setter for the list of custom 3D objects to represent in the objects layer. Each object is rendered according to the objectThreeObject method."
    )
    object_lat: Var[Any] = field(
        doc="Object accessor function, attribute or a numeric constant for the latitude coordinate of the object's position."
    )
    object_lng: Var[Any] = field(
        doc="Object accessor function, attribute or a numeric constant for the longitude coordinate of the object's position."
    )
    object_altitude: Var[Any] = field(
        doc="Object accessor function, attribute or a numeric constant for the altitude coordinate of the object's position, in terms of globe radius units."
    )
    object_rotation: Var[Any] = field(
        doc="Object accessor function, attribute or a {x, y, z} object for the object's rotation (in degrees). Each dimension is optional, allowing for rotation only in some axes. Rotation is applied in the order **X**->**Y**->**Z**."
    )
    object_faces_surface: Var[Any] = field(
        doc="Object accessor function, attribute or a boolean constant for whether the object should be rotated to face (away from) the globe surface (true), or be left in its original universe orientation (false)."
    )
    object_three_object: Var[Any] = field(
        doc="Object accessor function or attribute for defining a custom 3d object to render as part of the objects map layer. Should return an instance of ThreeJS Object3d."
    )
    object_label: Var[Any] = field(
        doc="Object accessor function or attribute for its own tooltip label. Supports plain text or HTML content."
    )

    # --- Custom layer ---
    custom_layer_data: Var[list[Any]] = field(
        doc="List of items to represent in the custom map layer. Each item is rendered according to the customThreeObject method."
    )
    custom_three_object: Var[Any] = field(
        doc="Object accessor function or attribute for generating a custom 3d object to render as part of the custom map layer. Should return an instance of ThreeJS Object3d."
    )
    custom_three_object_update: Var[Any] = field(
        doc="Object accessor function or attribute for updating an existing custom 3d object with new data. This can be used for performance improvement on data updates as the objects don't need to be removed and recreated at each update. The callback method's signature includes the object to be update and..."
    )
    custom_layer_label: Var[Any] = field(
        doc="Object accessor function or attribute for label (shown as tooltip). Supports plain text or HTML content."
    )

    # --- Render control ---
    enable_pointer_interaction: Var[bool] = field(
        doc="Whether to enable the mouse tracking events. This activates an internal tracker of the canvas mouse position and enables the functionality of object hover/click and tooltip labels, at the cost of performance. If you're looking for maximum gain in your globe performance it's recommended to switch..."
    )
    pointer_events_filter: Var[Any] = field(
        doc="Filter function which defines whether a particular object can be the target of pointer interactions. In general, objects that are closer to the camera get precedence in capturing pointer events. This function allows having ignored object layers so that pointer events can be passed through to..."
    )
    line_hover_precision: Var[float | int] = field(
        doc="Precision to use when detecting hover events over Line and Points objects, such as arcs, paths or particles."
    )
    show_pointer_cursor: Var[Any] = field(
        doc="Whether to show a pointer cursor when hovering over clickable portions of the globe. Accepts either a boolean constant or a callback function which receives the object (type and data) currently under the cursor and is expected to return a boolean value."
    )

    # --- Reflex extensions (handled by the JS wrapper) ---
    point_of_view: Var[dict[str, float | int]] = field(
        doc="Declarative camera position {lat, lng, altitude}. The camera moves whenever this changes."
    )
    pov_transition_ms: Var[int] = field(doc="Duration (ms) of the camera transition when point_of_view changes.")
    animation_paused: Var[bool] = field(doc="Pause (True) or resume (False) the render loop.")
    auto_rotate: Var[bool] = field(doc="Enable orbit-controls auto rotation.")
    auto_rotate_speed: Var[float | int] = field(doc="Orbit-controls auto rotation speed (default 2.0 = 30s per orbit).")
    enable_zoom: Var[bool] = field(doc="Allow zooming with the mouse wheel / pinch.")
    enable_rotate: Var[bool] = field(doc="Allow rotating the globe by dragging.")
    enable_pan: Var[bool] = field(doc="Allow panning the camera.")
    controls_options: Var[dict[str, Any]] = field(
        doc="Arbitrary OrbitControls attributes (e.g. minDistance, maxDistance, zoomSpeed, enableDamping)."
    )
    globe_material_options: Var[dict[str, Any]] = field(
        doc="Attributes applied to the globe MeshPhongMaterial (color, emissive, emissiveIntensity, shininess, bumpScale, opacity, transparent, wireframe...)."
    )
    html_markup: Var[Any] = field(
        doc="Attribute name or JS function returning an HTML string for each item of html_elements_data. Simpler alternative to html_element. The string is assigned to innerHTML and is NOT escaped: never build it from untrusted input (use tooltip(), which escapes interpolated values)."
    )
    event_data_exclude: Var[list[str]] = field(
        doc="Keys stripped from datum objects before sending them to event handlers (default ['geometry'] to avoid shipping large GeoJSON)."
    )
    zoom_throttle_ms: Var[int] = field(doc="Throttle interval (ms) for on_zoom events (default 150).")

    # --- Events ---
    on_globe_ready: EventHandler[_no_args] = field(doc="Fired when the globe has finished initializing.")
    on_globe_click: EventHandler[_globe_click] = field(
        doc="Click on the globe surface. Args: coords {lat, lng}, event info."
    )
    on_globe_right_click: EventHandler[_globe_click] = field(
        doc="Right-click on the globe surface. Args: coords {lat, lng}, event info."
    )
    on_point_click: EventHandler[_layer_click] = field(
        doc="Click on a point. Args: datum, coords {lat, lng, altitude}, event info."
    )
    on_point_right_click: EventHandler[_layer_click] = field(
        doc="Right-click on a point. Args: datum, coords, event info."
    )
    on_point_hover: EventHandler[_layer_hover] = field(
        doc="Hover change on a point. Args: datum (or None), previous datum."
    )
    on_arc_click: EventHandler[_layer_click] = field(
        doc="Click on a arc. Args: datum, coords {lat, lng, altitude}, event info."
    )
    on_arc_right_click: EventHandler[_layer_click] = field(doc="Right-click on a arc. Args: datum, coords, event info.")
    on_arc_hover: EventHandler[_layer_hover] = field(
        doc="Hover change on a arc. Args: datum (or None), previous datum."
    )
    on_polygon_click: EventHandler[_layer_click] = field(
        doc="Click on a polygon. Args: datum, coords {lat, lng, altitude}, event info."
    )
    on_polygon_right_click: EventHandler[_layer_click] = field(
        doc="Right-click on a polygon. Args: datum, coords, event info."
    )
    on_polygon_hover: EventHandler[_layer_hover] = field(
        doc="Hover change on a polygon. Args: datum (or None), previous datum."
    )
    on_path_click: EventHandler[_layer_click] = field(
        doc="Click on a path. Args: datum, coords {lat, lng, altitude}, event info."
    )
    on_path_right_click: EventHandler[_layer_click] = field(
        doc="Right-click on a path. Args: datum, coords, event info."
    )
    on_path_hover: EventHandler[_layer_hover] = field(
        doc="Hover change on a path. Args: datum (or None), previous datum."
    )
    on_heatmap_click: EventHandler[_layer_click] = field(
        doc="Click on a heatmap. Args: datum, coords {lat, lng, altitude}, event info."
    )
    on_heatmap_right_click: EventHandler[_layer_click] = field(
        doc="Right-click on a heatmap. Args: datum, coords, event info."
    )
    on_heatmap_hover: EventHandler[_layer_hover] = field(
        doc="Hover change on a heatmap. Args: datum (or None), previous datum."
    )
    on_hex_click: EventHandler[_layer_click] = field(
        doc="Click on a hex. Args: datum, coords {lat, lng, altitude}, event info."
    )
    on_hex_right_click: EventHandler[_layer_click] = field(doc="Right-click on a hex. Args: datum, coords, event info.")
    on_hex_hover: EventHandler[_layer_hover] = field(
        doc="Hover change on a hex. Args: datum (or None), previous datum."
    )
    on_hex_polygon_click: EventHandler[_layer_click] = field(
        doc="Click on a hex polygon. Args: datum, coords {lat, lng, altitude}, event info."
    )
    on_hex_polygon_right_click: EventHandler[_layer_click] = field(
        doc="Right-click on a hex polygon. Args: datum, coords, event info."
    )
    on_hex_polygon_hover: EventHandler[_layer_hover] = field(
        doc="Hover change on a hex polygon. Args: datum (or None), previous datum."
    )
    on_tile_click: EventHandler[_layer_click] = field(
        doc="Click on a tile. Args: datum, coords {lat, lng, altitude}, event info."
    )
    on_tile_right_click: EventHandler[_layer_click] = field(
        doc="Right-click on a tile. Args: datum, coords, event info."
    )
    on_tile_hover: EventHandler[_layer_hover] = field(
        doc="Hover change on a tile. Args: datum (or None), previous datum."
    )
    on_particle_click: EventHandler[_layer_click] = field(
        doc="Click on a particle. Args: datum, coords {lat, lng, altitude}, event info."
    )
    on_particle_right_click: EventHandler[_layer_click] = field(
        doc="Right-click on a particle. Args: datum, coords, event info."
    )
    on_particle_hover: EventHandler[_layer_hover] = field(
        doc="Hover change on a particle. Args: datum (or None), previous datum."
    )
    on_label_click: EventHandler[_layer_click] = field(
        doc="Click on a label. Args: datum, coords {lat, lng, altitude}, event info."
    )
    on_label_right_click: EventHandler[_layer_click] = field(
        doc="Right-click on a label. Args: datum, coords, event info."
    )
    on_label_hover: EventHandler[_layer_hover] = field(
        doc="Hover change on a label. Args: datum (or None), previous datum."
    )
    on_object_click: EventHandler[_layer_click] = field(
        doc="Click on a object. Args: datum, coords {lat, lng, altitude}, event info."
    )
    on_object_right_click: EventHandler[_layer_click] = field(
        doc="Right-click on a object. Args: datum, coords, event info."
    )
    on_object_hover: EventHandler[_layer_hover] = field(
        doc="Hover change on a object. Args: datum (or None), previous datum."
    )
    on_custom_layer_click: EventHandler[_layer_click] = field(
        doc="Click on a custom layer. Args: datum, coords {lat, lng, altitude}, event info."
    )
    on_custom_layer_right_click: EventHandler[_layer_click] = field(
        doc="Right-click on a custom layer. Args: datum, coords, event info."
    )
    on_custom_layer_hover: EventHandler[_layer_hover] = field(
        doc="Hover change on a custom layer. Args: datum (or None), previous datum."
    )
    on_zoom: EventHandler[_pov] = field(doc="Camera point-of-view change {lat, lng, altitude} (throttled).")
    on_html_element_click: EventHandler[_html_click] = field(
        doc="Click on an HTML marker created with html_markup. Args: datum, event info."
    )
    on_html_element_hover: EventHandler[_html_hover] = field(
        doc="Mouse enter / leave on an HTML marker created with html_markup. Args: datum or None."
    )

    @classmethod
    def create(cls, *children, **props) -> Globe:
        """Create the globe component.

        Args:
            *children: Optional children rendered on top of the canvas (overlays).
            **props: Any react-globe.gl prop (snake_case) plus the Reflex extensions.

        Returns:
            The component.
        """
        return super().create(*children, **props)


ReactGlobeGl = Globe
globe = Globe.create

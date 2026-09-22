"""Tests for the Globe component definition and rendering."""

from __future__ import annotations

import reflex as rx
from reflex_base.utils.format import to_camel_case

import reflex_react_globe_gl as rg
from reflex_react_globe_gl import Globe

LAYERS = [
    "point",
    "arc",
    "polygon",
    "path",
    "heatmap",
    "hex",
    "hex_polygon",
    "tile",
    "particle",
    "label",
    "object",
    "custom_layer",
]

# Every prop of react-globe.gl's GlobeProps interface (index.d.ts, v2.38).
UPSTREAM_PROPS = """
    globeOffset backgroundColor backgroundImageUrl globeImageUrl bumpImageUrl globeTileEngineUrl showGlobe
    showGraticules showAtmosphere atmosphereColor atmosphereAltitude globeCurvatureResolution globeMaterial
    pointsData pointLat pointLng pointColor pointAltitude pointRadius pointResolution pointsMerge
    pointsTransitionDuration pointLabel arcsData arcStartLat arcStartLng arcStartAltitude arcEndLat arcEndLng
    arcEndAltitude arcColor arcAltitude arcAltitudeAutoScale arcStroke arcCurveResolution
    arcCircularResolution arcDashLength arcDashGap arcDashInitialGap arcDashAnimateTime arcsTransitionDuration
    arcLabel polygonsData polygonGeoJsonGeometry polygonCapColor polygonCapMaterial polygonSideColor
    polygonSideMaterial polygonStrokeColor polygonAltitude polygonCapCurvatureResolution
    polygonsTransitionDuration polygonLabel pathsData pathPoints pathPointLat pathPointLng pathPointAlt
    pathResolution pathColor pathStroke pathDashLength pathDashGap pathDashInitialGap pathDashAnimateTime
    pathTransitionDuration pathLabel heatmapsData heatmapPoints heatmapPointLat heatmapPointLng
    heatmapPointWeight heatmapBandwidth heatmapColorFn heatmapColorSaturation heatmapBaseAltitude
    heatmapTopAltitude heatmapsTransitionDuration hexBinPointsData hexBinPointLat hexBinPointLng
    hexBinPointWeight hexBinResolution hexMargin hexAltitude hexTopCurvatureResolution hexTopColor
    hexSideColor hexBinMerge hexTransitionDuration hexLabel hexPolygonsData hexPolygonGeoJsonGeometry
    hexPolygonColor hexPolygonAltitude hexPolygonResolution hexPolygonMargin hexPolygonUseDots
    hexPolygonCurvatureResolution hexPolygonDotResolution hexPolygonsTransitionDuration hexPolygonLabel
    tilesData tileLat tileLng tileAltitude tileWidth tileHeight tileUseGlobeProjection tileMaterial
    tileCurvatureResolution tilesTransitionDuration tileLabel particlesData particlesList particleLat
    particleLng particleAltitude particlesSize particlesSizeAttenuation particlesColor particlesTexture
    particleLabel ringsData ringLat ringLng ringAltitude ringColor ringResolution ringMaxRadius
    ringPropagationSpeed ringRepeatPeriod labelsData labelLat labelLng labelText labelColor labelAltitude
    labelSize labelTypeFace labelRotation labelResolution labelIncludeDot labelDotRadius labelDotOrientation
    labelsTransitionDuration labelLabel htmlElementsData htmlLat htmlLng htmlAltitude htmlElement
    htmlElementVisibilityModifier htmlTransitionDuration objectsData objectLat objectLng objectAltitude
    objectRotation objectFacesSurface objectThreeObject objectLabel customLayerData customThreeObject
    customThreeObjectUpdate customLayerLabel enablePointerInteraction pointerEventsFilter lineHoverPrecision
    showPointerCursor width height animateIn waitForGlobeReady rendererConfig
    """.split()


def _props() -> set[str]:
    return {to_camel_case(p) for p in Globe.get_props()}


def _events() -> set[str]:
    return {to_camel_case(e) for e in Globe.get_event_triggers()}


def test_all_upstream_props_are_exposed():
    missing = [p for p in UPSTREAM_PROPS if p not in _props()]
    assert not missing, missing


def test_all_layer_events_are_exposed():
    events = _events()
    for layer in LAYERS:
        for kind in ("click", "right_click", "hover"):
            assert to_camel_case(f"on_{layer}_{kind}") in events
    for name in ("onGlobeReady", "onGlobeClick", "onGlobeRightClick", "onZoom", "onHtmlElementClick"):
        assert name in events


def test_library_is_the_shared_wrapper():
    assert Globe.library.startswith("$/public/external/")
    assert Globe.library.endswith("globe_wrapper.js")
    assert Globe.tag == "ReactGlobeGl"
    assert any(dep.startswith("react-globe.gl@") for dep in Globe.lib_dependencies)
    assert any(dep.startswith("three@") for dep in Globe.lib_dependencies)


def test_render_camel_cases_props():
    comp = rg.globe(
        id="g",
        points_data=[{"lat": 1, "lng": 2}],
        point_altitude=0.1,
        hex_bin_resolution=4,
        auto_rotate=True,
        point_of_view={"lat": 1, "lng": 2, "altitude": 2},
    )
    rendered = comp.render()
    assert rendered["name"] == "ReactGlobeGl"
    props = " ".join(rendered["props"])
    for name in ("pointsData", "pointAltitude", "hexBinResolution", "autoRotate", "pointOfView", 'id:"g"'):
        assert name in props


def test_no_ssr_dynamic_import():
    comp = rg.globe()
    dynamic = " ".join(comp._get_all_dynamic_imports())
    assert "ClientSide" in dynamic
    assert "mod.ReactGlobeGl" in dynamic


class _State(rx.State):
    last: dict = {}

    @rx.event
    def full(self, datum: dict, coords: dict, event: dict):
        self.last = datum

    @rx.event
    def datum_only(self, datum: dict):
        self.last = datum

    @rx.event
    def hover(self, datum: dict | None):
        self.last = datum or {}

    @rx.event
    def zoom(self, pov: dict[str, float]):
        pass


def test_event_handlers_accept_prefixes_and_loose_annotations():
    comp = rg.globe(
        on_point_click=_State.full,
        on_arc_click=_State.datum_only,
        on_polygon_hover=_State.hover,
        on_zoom=_State.zoom,
        on_globe_click=_State.datum_only,
        on_html_element_click=_State.datum_only,
    )
    triggers = comp.event_triggers
    for name in ("on_point_click", "on_arc_click", "on_polygon_hover", "on_zoom", "on_globe_click"):
        assert name in triggers

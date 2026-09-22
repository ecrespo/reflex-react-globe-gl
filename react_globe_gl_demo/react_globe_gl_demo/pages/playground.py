"""Globe playground: globe layer, atmosphere, material, controls and imperative actions."""

from __future__ import annotations

from typing import Any

import reflex as rx

import reflex_react_globe_gl as rg

from .. import data
from ..components import info_row, page, panel, slider, switch
from ..state import DemoState

GID = "playground-globe"

ATMOSPHERE_COLORS = ["lightskyblue", "#22d3ee", "#f472b6", "#fbbf24", "#a3e635", "white"]
BACKGROUNDS = {"Night sky": data.NIGHT_SKY, "Solid color": ""}
PLACES: list[tuple[str, float, float, float]] = [
    ("Rio de Janeiro", -22.91, -43.17, 1.2),
    ("Barcelona", 41.39, 2.17, 1.2),
    ("Tokyo", 35.68, 139.69, 1.2),
    ("Sydney", -33.87, 151.21, 1.2),
    ("New York", 40.71, -74.0, 1.2),
    ("Cape Town", -33.92, 18.42, 1.2),
]


class PlaygroundState(DemoState):
    globe_image: str = "Blue marble"
    bump: bool = True
    background: str = "Night sky"
    background_color: str = "#000011"
    show_globe: bool = True
    show_atmosphere: bool = True
    show_graticules: bool = False
    atmosphere_color: str = "lightskyblue"
    atmosphere_altitude: float = 0.15
    curvature: int = 4
    emissive: str = "#000000"
    emissive_intensity: float = 0.0
    shininess: float = 30.0
    auto_rotate: bool = False
    auto_rotate_speed: float = 1.0
    enable_zoom: bool = True
    paused: bool = False
    offset_x: int = 0
    pov: dict[str, float] = {}
    last_pov: str = ""
    clicks: list[dict[str, Any]] = []
    ready: bool = False

    @rx.var
    def globe_image_url(self) -> str:
        return data.GLOBE_IMAGES.get(self.globe_image, "")

    @rx.var
    def bump_image_url(self) -> str:
        return data.EARTH_TOPOLOGY if self.bump else ""

    @rx.var
    def background_image_url(self) -> str:
        return BACKGROUNDS.get(self.background, "")

    @rx.var
    def material_options(self) -> dict[str, Any]:
        opts: dict[str, Any] = {
            "emissive": self.emissive,
            "emissiveIntensity": self.emissive_intensity,
            "shininess": self.shininess,
        }
        if not self.globe_image_url:
            opts["color"] = "#1e3a8a"
        return opts

    @rx.var
    def zoom_label(self) -> str:
        if not self.pov:
            return "—"
        return f"{self.pov['lat']:.1f}, {self.pov['lng']:.1f} · alt {self.pov['altitude']:.2f}"

    @rx.event
    def set_globe_image(self, v: str):
        self.globe_image = v

    @rx.event
    def set_bump(self, v: bool):
        self.bump = v

    @rx.event
    def set_background(self, v: str):
        self.background = v

    @rx.event
    def set_background_color(self, v: str):
        self.background_color = v

    @rx.event
    def set_show_globe(self, v: bool):
        self.show_globe = v

    @rx.event
    def set_show_atmosphere(self, v: bool):
        self.show_atmosphere = v

    @rx.event
    def set_show_graticules(self, v: bool):
        self.show_graticules = v

    @rx.event
    def set_atmosphere_color(self, v: str):
        self.atmosphere_color = v

    @rx.event
    def set_atmosphere_altitude(self, v: list[float]):
        self.atmosphere_altitude = float(v[0])

    @rx.event
    def set_curvature(self, v: list[float]):
        self.curvature = int(v[0])

    @rx.event
    def set_emissive(self, v: str):
        self.emissive = v

    @rx.event
    def set_emissive_intensity(self, v: list[float]):
        self.emissive_intensity = float(v[0])

    @rx.event
    def set_shininess(self, v: list[float]):
        self.shininess = float(v[0])

    @rx.event
    def set_auto_rotate(self, v: bool):
        self.auto_rotate = v

    @rx.event
    def set_auto_rotate_speed(self, v: list[float]):
        self.auto_rotate_speed = float(v[0])

    @rx.event
    def set_enable_zoom(self, v: bool):
        self.enable_zoom = v

    @rx.event
    def set_paused(self, v: bool):
        self.paused = v

    @rx.event
    def set_offset_x(self, v: list[float]):
        self.offset_x = int(v[0])

    @rx.event
    def on_ready(self):
        self.ready = True
        self._log("globe ready", "onGlobeReady fired")

    @rx.event
    def on_zoom(self, pov: dict[str, Any]):
        self.pov = {k: float(pov[k]) for k in ("lat", "lng", "altitude")}

    @rx.event
    def on_globe_click(self, coords: dict[str, Any], event: dict[str, Any]):
        self.clicks = [*self.clicks[-19:], {"lat": coords["lat"], "lng": coords["lng"]}]
        mods = [k for k in ("shiftKey", "altKey", "ctrlKey", "metaKey") if event.get(k)]
        self._log(
            "globe click", f"{coords['lat']:.2f}, {coords['lng']:.2f} {' '.join(mods)} (x={event.get('clientX')})"
        )

    @rx.event
    def on_globe_right_click(self, coords: dict[str, Any]):
        self.clicks = []
        self._log("right click", "markers cleared")

    @rx.event
    def receive_pov(self, pov: dict[str, Any]):
        self.last_pov = f"{pov['lat']:.2f}, {pov['lng']:.2f} · alt {pov['altitude']:.2f}"
        self._log("pointOfView()", self.last_pov)

    @rx.event
    def receive_screen(self, coords: dict[str, Any]):
        self._log("getScreenCoords", f"(0,0) → x={coords['x']:.0f}, y={coords['y']:.0f}")


S = PlaygroundState


def playground_globe() -> rx.Component:
    return rg.globe(
        id=GID,
        # Container
        background_color=S.background_color,
        background_image_url=S.background_image_url,
        globe_offset=[S.offset_x, 0],
        # Globe layer
        globe_image_url=S.globe_image_url,
        bump_image_url=S.bump_image_url,
        show_globe=S.show_globe,
        show_atmosphere=S.show_atmosphere,
        show_graticules=S.show_graticules,
        atmosphere_color=S.atmosphere_color,
        atmosphere_altitude=S.atmosphere_altitude,
        globe_curvature_resolution=S.curvature,
        globe_material_options=S.material_options,
        # Controls / render (Reflex extensions)
        auto_rotate=S.auto_rotate,
        auto_rotate_speed=S.auto_rotate_speed,
        enable_zoom=S.enable_zoom,
        animation_paused=S.paused,
        controls_options={"minDistance": 101, "maxDistance": 1500},
        # Click markers
        points_data=S.clicks,
        point_color=rg.constant("#f472b6"),
        point_radius=0.6,
        point_altitude=0.02,
        # Events
        on_globe_ready=S.on_ready,
        on_zoom=S.on_zoom,
        on_globe_click=S.on_globe_click,
        on_globe_right_click=S.on_globe_right_click,
        # Init-only props
        animate_in=True,
        wait_for_globe_ready=True,
        renderer_config={"antialias": True, "alpha": True},
        position="absolute",
        inset="0",
    )


def _select(items: list[str], value: Any, on_change: Any) -> rx.Component:
    return rx.select(items, value=value, on_change=on_change, size="1", width="100%")


def playground_panel() -> rx.Component:
    return panel(
        "Globe playground",
        "Every globe-layer prop, material options, orbit controls and the imperative API "
        "(pointOfView, pause/resume, getScreenCoords…) wired to Reflex.",
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("Globe", value="globe"),
                rx.tabs.trigger("Material", value="material"),
                rx.tabs.trigger("Camera", value="camera"),
                size="1",
            ),
            rx.tabs.content(
                rx.vstack(
                    rx.text("Globe image", size="1", weight="medium"),
                    _select(list(data.GLOBE_IMAGES), S.globe_image, S.set_globe_image),
                    rx.text("Background", size="1", weight="medium"),
                    _select(list(BACKGROUNDS), S.background, S.set_background),
                    rx.cond(
                        S.background == "Solid color",
                        rx.input(
                            type="color", value=S.background_color, on_change=S.set_background_color, width="100%"
                        ),
                    ),
                    switch("Bump map (terrain)", S.bump, S.set_bump),
                    switch("Show globe", S.show_globe, S.set_show_globe),
                    switch("Show graticules", S.show_graticules, S.set_show_graticules),
                    switch("Show atmosphere", S.show_atmosphere, S.set_show_atmosphere),
                    rx.text("Atmosphere color", size="1", weight="medium"),
                    _select(ATMOSPHERE_COLORS, S.atmosphere_color, S.set_atmosphere_color),
                    slider("Atmosphere altitude", S.atmosphere_altitude, S.set_atmosphere_altitude, 0, 0.6, 0.01),
                    slider("Curvature resolution (deg)", S.curvature, S.set_curvature, 1, 20, 1),
                    slider("Horizontal offset (px)", S.offset_x, S.set_offset_x, -400, 400, 10),
                    spacing="3",
                    width="100%",
                    padding_top="10px",
                ),
                value="globe",
            ),
            rx.tabs.content(
                rx.vstack(
                    rx.text(
                        "globe_material_options mutates the globe MeshPhongMaterial in place.",
                        size="1",
                        color_scheme="gray",
                    ),
                    rx.text("Emissive color", size="1", weight="medium"),
                    rx.input(type="color", value=S.emissive, on_change=S.set_emissive, width="100%"),
                    slider("Emissive intensity", S.emissive_intensity, S.set_emissive_intensity, 0, 1, 0.05),
                    slider("Shininess", S.shininess, S.set_shininess, 0, 200, 5),
                    spacing="3",
                    width="100%",
                    padding_top="10px",
                ),
                value="material",
            ),
            rx.tabs.content(
                rx.vstack(
                    switch("Auto-rotate", S.auto_rotate, S.set_auto_rotate),
                    slider("Auto-rotate speed", S.auto_rotate_speed, S.set_auto_rotate_speed, -5, 5, 0.25),
                    switch("Enable zoom", S.enable_zoom, S.set_enable_zoom),
                    switch("Pause animation", S.paused, S.set_paused),
                    rx.text("Fly to (rx.call_script actions, no backend round-trip)", size="1", weight="medium"),
                    rx.flex(
                        *[
                            rx.button(name, size="1", variant="soft", on_click=rg.fly_to(GID, lat, lng, alt, 1500))
                            for name, lat, lng, alt in PLACES
                        ],
                        rx.button(
                            "Zoom out",
                            size="1",
                            variant="outline",
                            on_click=rg.fly_to(GID, altitude=2.5, transition_ms=1200),
                        ),
                        wrap="wrap",
                        gap="6px",
                    ),
                    rx.text("Queries (result sent to a backend callback)", size="1", weight="medium"),
                    rx.flex(
                        rx.button(
                            "pointOfView()",
                            size="1",
                            variant="surface",
                            on_click=rg.get_point_of_view(GID, S.receive_pov),
                        ),
                        rx.button(
                            "getScreenCoords(0, 0)",
                            size="1",
                            variant="surface",
                            on_click=rg.get_screen_coords(GID, 0, 0, callback=S.receive_screen),
                        ),
                        rx.button(
                            "Spin fast (set_controls)",
                            size="1",
                            variant="surface",
                            on_click=rg.set_controls(GID, autoRotate=True, autoRotateSpeed=12),
                        ),
                        wrap="wrap",
                        gap="6px",
                    ),
                    info_row("on_zoom (throttled)", S.zoom_label),
                    info_row("Last pointOfView()", rx.cond(S.last_pov != "", S.last_pov, "—")),
                    info_row("Ready", rx.cond(S.ready, "yes", "no")),
                    rx.text("Click: add marker · Right-click: clear markers", size="1", color_scheme="gray"),
                    spacing="3",
                    width="100%",
                    padding_top="10px",
                ),
                value="camera",
            ),
            default_value="globe",
            width="100%",
        ),
    )


def playground_page() -> rx.Component:
    return page(playground_globe(), playground_panel())

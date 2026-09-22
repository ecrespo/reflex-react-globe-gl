"""Space: 3D objects (satellites), custom ThreeJS layer, particles and paths."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import reflex as rx

import reflex_react_globe_gl as rg

from .. import data
from ..components import info_row, page, panel, slider, switch
from ..state import DemoState

MAX_ANIMATION_SECONDS = 120

STATIONS = [
    {"name": "Station Alpha", "lat": 12.0, "lng": -40.0, "alt": 0.9, "radius": 3.0, "color": "#22d3ee"},
    {"name": "Station Beta", "lat": -25.0, "lng": 70.0, "alt": 1.1, "radius": 2.4, "color": "#f472b6"},
    {"name": "Station Gamma", "lat": 48.0, "lng": 150.0, "alt": 0.8, "radius": 2.0, "color": "#a3e635"},
]


class SpaceState(DemoState):
    satellites: list[dict[str, Any]] = []
    particles: list[dict[str, Any]] = []
    paths: list[dict[str, Any]] = []
    show_satellites: bool = True
    show_stations: bool = True
    show_particles: bool = True
    show_paths: bool = True
    animating: bool = False
    speed: float = 2.0
    ticks: int = 0
    selected: dict[str, str] = {}

    @rx.event
    def load(self):
        self.animating = False
        if not self.satellites:
            self.satellites = data.random_satellites(40, seed=7)
            self.particles = data.particle_clouds(seed=3)
            self.paths = data.random_paths(8, seed=11)

    @rx.var
    def sats(self) -> list[dict[str, Any]]:
        return self.satellites if self.show_satellites else []

    @rx.var
    def stations(self) -> list[dict[str, Any]]:
        return STATIONS if self.show_stations else []

    @rx.var
    def particle_sets(self) -> list[dict[str, Any]]:
        return self.particles if self.show_particles else []

    @rx.var
    def path_list(self) -> list[dict[str, Any]]:
        return self.paths if self.show_paths else []

    @rx.event
    def set_show_satellites(self, v: bool):
        self.show_satellites = v

    @rx.event
    def set_show_stations(self, v: bool):
        self.show_stations = v

    @rx.event
    def set_show_particles(self, v: bool):
        self.show_particles = v

    @rx.event
    def set_show_paths(self, v: bool):
        self.show_paths = v

    @rx.event
    def set_speed(self, v: list[float]):
        self.speed = float(v[0])

    @rx.event
    def new_paths(self):
        self.paths = data.random_paths(8)

    @rx.event
    def on_object_click(self, sat: dict[str, Any]):
        self.selected = {
            "name": sat["name"],
            "kind": "satellite (objects layer)",
            "position": f"{sat['lat']:.1f}, {sat['lng']:.1f} @ alt {sat['alt']:.2f}",
        }
        self._log("object click", sat["name"])

    @rx.event
    def on_custom_click(self, station: dict[str, Any]):
        self.selected = {
            "name": station["name"],
            "kind": "station (custom layer)",
            "position": f"{station['lat']:.1f}, {station['lng']:.1f} @ alt {station['alt']:.2f}",
        }
        self._log("custom layer click", station["name"])

    @rx.event
    def on_path_click(self, path: dict[str, Any]):
        self._log("path click", path["name"])

    @rx.event
    def on_particle_click(self, particle_set: dict[str, Any]):
        self._log("particle click", particle_set.get("name", ""))

    @rx.event
    def toggle_animation(self, value: bool):
        self.animating = value
        if value:
            return SpaceState.orbit_loop

    @rx.event(background=True)
    async def orbit_loop(self):
        """Move the satellites from the backend (live data pushed over the websocket)."""
        started = time.monotonic()
        while True:
            async with self:
                if not self.animating or time.monotonic() - started > MAX_ANIMATION_SECONDS:
                    self.animating = False
                    return
                step = self.speed
                self.satellites = [
                    {**s, "lng": ((s["lng"] + step * (1.5 - s["alt"]) + 180) % 360) - 180} for s in self.satellites
                ]
                self.ticks += 1
            await asyncio.sleep(0.25)


S = SpaceState

_SAT_MESH = rg.js(
    "d => new window.ReflexGlobe.THREE.Mesh("
    "new window.ReflexGlobe.THREE.OctahedronGeometry(d.size), "
    "new window.ReflexGlobe.THREE.MeshLambertMaterial({ color: d.color, transparent: true, opacity: 0.9 }))"
)

_STATION_MESH = rg.js(
    "d => new window.ReflexGlobe.THREE.Mesh("
    "new window.ReflexGlobe.THREE.SphereGeometry(d.radius, 24, 16), "
    "new window.ReflexGlobe.THREE.MeshPhongMaterial({ color: d.color, emissive: d.color, emissiveIntensity: 0.35, shininess: 80 }))"
)

# Custom layer objects are positioned manually, using the globe's getCoords utility.
_STATION_UPDATE = rg.js(
    "(obj, d) => { const g = window.ReflexGlobe.get('space-globe'); "
    "if (g) Object.assign(obj.position, g.getCoords(d.lat, d.lng, d.alt)); }"
)


def space_globe() -> rx.Component:
    return rg.globe(
        id="space-globe",
        globe_image_url=data.EARTH_BLUE_MARBLE,
        bump_image_url=data.EARTH_TOPOLOGY,
        background_image_url=data.NIGHT_SKY,
        point_of_view={"lat": 15, "lng": 20, "altitude": 4.2},
        # 3D objects layer
        objects_data=S.sats,
        object_lat="lat",
        object_lng="lng",
        object_altitude="alt",
        object_three_object=_SAT_MESH,
        object_label=rg.tooltip("<b>{name}</b><br/>alt {alt}"),
        on_object_click=S.on_object_click,
        # Custom layer
        custom_layer_data=S.stations,
        custom_three_object=_STATION_MESH,
        custom_three_object_update=_STATION_UPDATE,
        custom_layer_label="name",
        on_custom_layer_click=S.on_custom_click,
        # Particles layer
        particles_data=S.particle_sets,
        particles_list="points",
        particle_lat="lat",
        particle_lng="lng",
        particle_altitude="alt",
        particles_color="color",
        particles_size="size",
        particles_size_attenuation=False,
        particle_label="name",
        on_particle_click=S.on_particle_click,
        # Paths layer
        paths_data=S.path_list,
        path_points="coords",
        path_point_lat=rg.js("p => p[0]"),
        path_point_lng=rg.js("p => p[1]"),
        path_point_alt=rg.js("p => p[2]"),
        path_color="color",
        path_stroke=1.5,
        path_dash_length=0.01,
        path_dash_gap=0.004,
        path_dash_animate_time=100000,
        path_transition_duration=3000,
        path_label="name",
        on_path_click=S.on_path_click,
        # Keep event payloads small: don't ship particle lists / path coordinates.
        event_data_exclude=["points", "coords"],
        position="absolute",
        inset="0",
    )


def space_panel() -> rx.Component:
    return panel(
        "Objects, particles & paths",
        "Satellites use the 3D objects layer with ThreeJS meshes; stations use the fully custom layer; "
        "orbital shells are particle clouds and the random walks are animated dashed paths.",
        switch("Satellites (objects layer)", S.show_satellites, S.set_show_satellites),
        switch("Stations (custom layer)", S.show_stations, S.set_show_stations),
        switch("Orbital shells (particles)", S.show_particles, S.set_show_particles),
        switch("Random walks (paths)", S.show_paths, S.set_show_paths),
        rx.separator(size="4"),
        switch("Animate orbits from the backend", S.animating, S.toggle_animation),
        slider("Orbit speed (deg/tick)", S.speed, S.set_speed, 0.5, 8, 0.5),
        info_row("Backend ticks", S.ticks),
        rx.button(rx.icon("shuffle", size=14), "New random walks", size="1", variant="soft", on_click=S.new_paths),
        rx.cond(
            S.selected.length() > 0,
            rx.card(
                rx.vstack(
                    rx.heading(S.selected["name"], size="3"),
                    info_row("Kind", S.selected["kind"]),
                    info_row("Position", S.selected["position"]),
                    spacing="1",
                    width="100%",
                ),
                width="100%",
                variant="surface",
            ),
        ),
    )


def space_page() -> rx.Component:
    return page(space_globe(), space_panel())

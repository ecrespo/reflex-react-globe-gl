"""Arcs & rings: animated dashed arcs plus "emit arcs on click" driven by a background task."""

from __future__ import annotations

import asyncio
import itertools
from typing import Any

import reflex as rx

import reflex_react_globe_gl as rg

from .. import data
from ..components import info_row, page, panel, slider, switch
from ..state import DemoState

FLIGHT_TIME = 1000  # ms
ARC_REL_LEN = 0.4  # relative to whole arc
NUM_RINGS = 3
RINGS_MAX_R = 5  # deg
RING_PROPAGATION_SPEED = 5  # deg/sec

_ids = itertools.count(1)


class FlightsState(DemoState):
    arcs: list[dict[str, Any]] = []
    emitted: list[dict[str, Any]] = []
    rings: list[dict[str, Any]] = []
    prev_click: dict[str, float] = {}
    n_arcs: int = 20
    show_random: bool = True
    dash_length: float = 0.4
    dash_gap: float = 2.0
    animate_ms: int = 3000
    stroke: float = 0.6
    auto_scale: float = 0.5
    hovered: str = ""
    clicked: str = ""
    emitted_total: int = 0

    @rx.event
    def load(self):
        if not self.arcs:
            self.arcs = data.random_arcs(self.n_arcs)

    @rx.var
    def all_arcs(self) -> list[dict[str, Any]]:
        return (self.arcs if self.show_random else []) + self.emitted

    @rx.var
    def next_departure(self) -> str:
        if not self.prev_click:
            return "click the globe"
        return f"{self.prev_click['lat']:.2f}, {self.prev_click['lng']:.2f}"

    @rx.event
    def regenerate(self):
        self.arcs = data.random_arcs(self.n_arcs)
        self._log("regenerate", f"{self.n_arcs} random arcs")

    @rx.event
    def set_n_arcs(self, value: list[float]):
        self.n_arcs = int(value[0])
        self.arcs = data.random_arcs(self.n_arcs)

    @rx.event
    def set_dash_length(self, value: list[float]):
        self.dash_length = float(value[0])

    @rx.event
    def set_dash_gap(self, value: list[float]):
        self.dash_gap = float(value[0])

    @rx.event
    def set_animate_ms(self, value: list[float]):
        self.animate_ms = int(value[0])

    @rx.event
    def set_stroke(self, value: list[float]):
        self.stroke = float(value[0])

    @rx.event
    def set_auto_scale(self, value: list[float]):
        self.auto_scale = float(value[0])

    @rx.event
    def set_show_random(self, value: bool):
        self.show_random = value

    @rx.event
    def on_arc_hover(self, arc: dict[str, Any] | None):
        self.hovered = arc.get("label", "") if arc else ""

    @rx.event
    def on_arc_click(self, arc: dict[str, Any], coords: dict[str, Any]):
        self.clicked = arc.get("label", "")
        self._log("arc click", f"{arc.get('label')} @ {coords['lat']:.1f}, {coords['lng']:.1f}")

    @rx.event(background=True)
    async def emit_arc(self, coords: dict[str, float]):
        """Upstream "emit arcs on click", orchestrated from the backend."""
        async with self:
            prev = self.prev_click
            self.prev_click = {"lat": coords["lat"], "lng": coords["lng"]}
            self._log("globe click", f"{coords['lat']:.2f}, {coords['lng']:.2f}")
            if not prev:
                return
            arc_id = next(_ids)
            arc = {
                "id": arc_id,
                "emitted": True,
                "label": f"Flight #{arc_id}",
                "startLat": prev["lat"],
                "startLng": prev["lng"],
                "endLat": coords["lat"],
                "endLng": coords["lng"],
                "color": ["#ff9f1c", "#ff9f1c"],
            }
            src_ring = {"id": f"s{arc_id}", "lat": prev["lat"], "lng": prev["lng"]}
            self.emitted = [*self.emitted, arc]
            self.rings = [*self.rings, src_ring]
            self.emitted_total += 1

        await asyncio.sleep(FLIGHT_TIME * ARC_REL_LEN / 1000)
        async with self:
            self.rings = [r for r in self.rings if r["id"] != src_ring["id"]]

        await asyncio.sleep(FLIGHT_TIME * (1 - ARC_REL_LEN) / 1000)
        dst_ring = {"id": f"d{arc_id}", "lat": coords["lat"], "lng": coords["lng"]}
        async with self:
            self.rings = [*self.rings, dst_ring]

        await asyncio.sleep(FLIGHT_TIME * ARC_REL_LEN / 1000)
        async with self:
            self.rings = [r for r in self.rings if r["id"] != dst_ring["id"]]

        await asyncio.sleep(FLIGHT_TIME * (1 - ARC_REL_LEN) / 1000)
        async with self:
            self.emitted = [a for a in self.emitted if a["id"] != arc_id]


S = FlightsState


def flights_globe() -> rx.Component:
    return rg.globe(
        id="flights-globe",
        globe_image_url=data.EARTH_NIGHT,
        background_image_url=data.NIGHT_SKY,
        on_globe_click=S.emit_arc,
        # Arcs
        arcs_data=S.all_arcs,
        arc_label="label",
        arc_color=rg.js(f"d => d.label === {S.hovered} || d.label === {S.clicked} ? ['#ffffff', '#ffffff'] : d.color"),
        arc_stroke=rg.js(f"d => d.emitted ? null : {S.stroke}"),
        arc_altitude_auto_scale=S.auto_scale,
        arc_dash_length=rg.js(f"d => d.emitted ? {ARC_REL_LEN} : {S.dash_length}"),
        arc_dash_gap=rg.js(f"d => d.emitted ? 2 : {S.dash_gap}"),
        arc_dash_initial_gap=rg.js("d => d.emitted ? 1 : (d.startLat + 90) / 45"),
        arc_dash_animate_time=rg.js(f"d => d.emitted ? {FLIGHT_TIME} : {S.animate_ms}"),
        arcs_transition_duration=0,
        on_arc_hover=S.on_arc_hover,
        on_arc_click=S.on_arc_click,
        # Rings
        rings_data=S.rings,
        ring_color=rg.js("() => t => `rgba(255,100,50,${1 - t})`"),
        ring_max_radius=RINGS_MAX_R,
        ring_propagation_speed=RING_PROPAGATION_SPEED,
        ring_repeat_period=FLIGHT_TIME * ARC_REL_LEN / NUM_RINGS,
        position="absolute",
        inset="0",
    )


def flights_panel() -> rx.Component:
    return panel(
        "Arcs & rings",
        "Animated dashed arcs with gradient colors. Click twice on the globe to emit a flight: a backend "
        "background task adds the arc and the ripple rings, then removes them when the flight lands.",
        switch("Random routes", S.show_random, S.set_show_random),
        slider("Number of routes", S.n_arcs, S.set_n_arcs, 5, 100, 5),
        slider("Dash length", S.dash_length, S.set_dash_length, 0.05, 1, 0.05),
        slider("Dash gap", S.dash_gap, S.set_dash_gap, 0, 4, 0.1),
        slider("Animation time (ms)", S.animate_ms, S.set_animate_ms, 500, 10000, 250),
        slider("Stroke width", S.stroke, S.set_stroke, 0.1, 2, 0.1),
        slider("Altitude auto-scale", S.auto_scale, S.set_auto_scale, 0.1, 1, 0.05),
        rx.button(rx.icon("shuffle", size=14), "Regenerate routes", on_click=S.regenerate, size="1", variant="soft"),
        rx.separator(size="4"),
        info_row("Hovered arc", rx.cond(S.hovered != "", S.hovered, "—")),
        info_row("Clicked arc", rx.cond(S.clicked != "", S.clicked, "—")),
        info_row("Flights in the air", S.emitted.length()),
        info_row("Flights emitted", S.emitted_total),
        info_row(
            "Next departure",
            S.next_departure,
        ),
    )


def flights_page() -> rx.Component:
    return page(flights_globe(), flights_panel())

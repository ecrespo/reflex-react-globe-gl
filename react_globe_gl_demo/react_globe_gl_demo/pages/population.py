"""World population as extruded hexagonal bins (upstream "World Population" example)."""

from __future__ import annotations

from typing import Any

import reflex as rx

import reflex_react_globe_gl as rg

from .. import data
from ..components import info_row, page, panel, segmented, slider, switch
from ..state import DemoState


class PopulationState(DemoState):
    points: list[dict[str, float]] = []
    resolution: int = 3
    altitude_scale: float = 1.5
    palette: str = "YlOrRd"
    merge: bool = False
    auto_rotate: bool = True
    hovered: dict[str, str] = {}

    @rx.event
    def load(self):
        if not self.points:
            self.points = data.world_population()

    @rx.event
    def set_resolution(self, value: list[float]):
        self.resolution = int(value[0])

    @rx.event
    def set_altitude_scale(self, value: list[float]):
        self.altitude_scale = float(value[0])

    @rx.event
    def set_palette(self, value: str | list[str]):
        self.palette = value

    @rx.event
    def set_merge(self, value: bool):
        self.merge = value
        self.hovered = {}

    @rx.event
    def set_auto_rotate(self, value: bool):
        self.auto_rotate = value

    @rx.event
    def on_hex_hover(self, hex_bin: dict[str, Any] | None):
        if not hex_bin:
            self.hovered = {}
            return
        points = hex_bin.get("points") or [{"lat": 0, "lng": 0}]
        self.hovered = {
            "h3": str(hex_bin.get("h3Idx", "")),
            "lat": f"{sum(p['lat'] for p in points) / len(points):.2f}",
            "lng": f"{sum(p['lng'] for p in points) / len(points):.2f}",
            "population": f"{int(hex_bin['sumWeight']):,}",
            "cells": str(len(points)),
        }

    @rx.event
    def on_hex_click(self, hex_bin: dict[str, Any], coords: dict[str, Any]):
        self._log("hex click", f"{int(hex_bin['sumWeight']):,} people @ {coords['lat']:.1f}, {coords['lng']:.1f}")


def population_globe() -> rx.Component:
    color = rg.color_scale("d.sumWeight", PopulationState.palette, (0, 1e7), "sqrt")
    return rg.globe(
        id="population-globe",
        globe_image_url=data.EARTH_NIGHT,
        bump_image_url=data.EARTH_TOPOLOGY,
        background_image_url=data.NIGHT_SKY,
        hex_bin_points_data=PopulationState.points,
        hex_bin_point_weight="pop",
        hex_bin_resolution=PopulationState.resolution,
        hex_altitude=rg.js(f"d => d.sumWeight * {PopulationState.altitude_scale} * 1e-8"),
        hex_top_color=color,
        hex_side_color=color,
        hex_bin_merge=PopulationState.merge,
        hex_transition_duration=600,
        hex_label=rg.js(
            "d => `<div style='font: 12px sans-serif'><b>${Math.round(d.sumWeight).toLocaleString()}</b> people"
            "<br/>${d.points.length} cells · H3 ${d.h3Idx}</div>`"
        ),
        on_hex_hover=PopulationState.on_hex_hover,
        on_hex_click=PopulationState.on_hex_click,
        auto_rotate=PopulationState.auto_rotate,
        auto_rotate_speed=0.3,
        point_of_view={"lat": 20, "lng": 10, "altitude": 2.3},
        position="absolute",
        inset="0",
    )


def population_panel() -> rx.Component:
    return panel(
        "World population",
        "11k population cells from the backend state, aggregated client-side into hexagonal bins "
        "whose height and color follow the population sum.",
        slider("Hex resolution (H3)", PopulationState.resolution, PopulationState.set_resolution, 1, 4, 1),
        slider(
            "Altitude scale (×1e-8)", PopulationState.altitude_scale, PopulationState.set_altitude_scale, 0.25, 10, 0.25
        ),
        rx.text("Palette", size="1", weight="medium"),
        segmented(["YlOrRd", "Viridis", "Inferno", "Turbo"], PopulationState.palette, PopulationState.set_palette),
        switch("Merge hexes (faster, no hover)", PopulationState.merge, PopulationState.set_merge),
        switch("Auto-rotate", PopulationState.auto_rotate, PopulationState.set_auto_rotate),
        rx.separator(size="4"),
        rx.text("Hovered hexagon", size="1", weight="bold"),
        rx.cond(
            PopulationState.hovered.length() > 0,
            rx.vstack(
                info_row("Population", PopulationState.hovered["population"]),
                info_row("Source cells", PopulationState.hovered["cells"]),
                info_row("H3 index", PopulationState.hovered["h3"]),
                info_row("Mean position", PopulationState.hovered["lat"] + ", " + PopulationState.hovered["lng"]),
                spacing="1",
                width="100%",
            ),
            rx.text("Hover a hexagon (merge off).", size="1", color_scheme="gray"),
        ),
        rx.hstack(
            rx.button(
                rx.icon("zoom-in", size=14),
                "Europe",
                size="1",
                variant="soft",
                on_click=rg.fly_to("population-globe", 48, 10, 1.2, 1500),
            ),
            rx.button(
                rx.icon("zoom-in", size=14),
                "India",
                size="1",
                variant="soft",
                on_click=rg.fly_to("population-globe", 22, 79, 1.2, 1500),
            ),
            rx.button(
                rx.icon("zoom-out", size=14),
                "Reset",
                size="1",
                variant="soft",
                on_click=rg.fly_to("population-globe", 20, 10, 2.3, 1500),
            ),
            wrap="wrap",
        ),
    )


def population_page() -> rx.Component:
    return page(population_globe(), population_panel())

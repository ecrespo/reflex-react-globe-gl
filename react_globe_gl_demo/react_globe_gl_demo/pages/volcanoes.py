"""Volcanoes: heatmap, hex bins and points on the same dataset."""

from __future__ import annotations

from collections import Counter
from typing import Any

import reflex as rx

import reflex_react_globe_gl as rg

from .. import data
from ..components import info_row, page, panel, segmented, slider
from ..state import DemoState

MODES = ["Heatmap", "Hex bins", "Points"]
TYPE_COLORS = {
    "Stratovolcano": "#ff4d6d",
    "Shield": "#ffd166",
    "Caldera": "#b388ff",
    "Complex": "#06d6a0",
    "Submarine": "#4cc9f0",
}


class VolcanoState(DemoState):
    volcanoes: list[dict[str, Any]] = []
    mode: str = "Heatmap"
    bandwidth: float = 1.35
    saturation: float = 3.2
    top_altitude: float = 0.2
    hex_resolution: int = 3
    selected: dict[str, str] = {}

    @rx.event
    def load(self):
        if not self.volcanoes:
            self.volcanoes = data.volcanoes()

    @rx.var
    def heatmaps(self) -> list[list[dict[str, Any]]]:
        return [self.volcanoes] if self.mode == "Heatmap" else []

    @rx.var
    def hexbin_points(self) -> list[dict[str, Any]]:
        return self.volcanoes if self.mode == "Hex bins" else []

    @rx.var
    def points(self) -> list[dict[str, Any]]:
        return self.volcanoes if self.mode == "Points" else []

    @rx.var
    def top_types(self) -> list[list[str]]:
        return [[t, str(n)] for t, n in Counter(v["type"] for v in self.volcanoes).most_common(6)]

    @rx.event
    def set_mode(self, value: str | list[str]):
        self.mode = str(value)
        self.selected = {}

    @rx.event
    def set_bandwidth(self, value: list[float]):
        self.bandwidth = float(value[0])

    @rx.event
    def set_saturation(self, value: list[float]):
        self.saturation = float(value[0])

    @rx.event
    def set_top_altitude(self, value: list[float]):
        self.top_altitude = float(value[0])

    @rx.event
    def set_hex_resolution(self, value: list[float]):
        self.hex_resolution = int(value[0])

    @rx.event
    def on_volcano_click(self, v: dict[str, Any]):
        self.selected = {
            "name": v["name"],
            "country": v["country"],
            "type": v["type"],
            "elevation": f"{v['elevation']:,} m",
            "coords": f"{v['lat']:.2f}, {v['lng']:.2f}",
        }
        self._log("point click", f"{v['name']} ({v['country']})")

    @rx.event
    def on_hex_click(self, hex_bin: dict[str, Any], coords: dict[str, Any]):
        names = ", ".join(p["name"] for p in hex_bin.get("points", [])[:5])
        self._log("hex click", f"{len(hex_bin.get('points', []))} volcanoes: {names}")

    @rx.event
    def on_heatmap_click(self, _heatmap: dict[str, Any], coords: dict[str, Any]):
        self._log("heatmap click", f"{coords['lat']:.1f}, {coords['lng']:.1f}")


S = VolcanoState


def volcano_globe() -> rx.Component:
    type_color = "({" + ", ".join(f"'{k}': '{v}'" for k, v in TYPE_COLORS.items()) + "})[d.type] || '#e5e7eb'"
    return rg.globe(
        id="volcano-globe",
        globe_image_url=data.EARTH_BLUE_MARBLE,
        bump_image_url=data.EARTH_TOPOLOGY,
        background_image_url=data.NIGHT_SKY,
        # Heatmaps layer (a list of datasets; here a single one)
        heatmaps_data=S.heatmaps,
        heatmap_point_lat="lat",
        heatmap_point_lng="lng",
        heatmap_point_weight=rg.js("d => d.elevation * 5e-5"),
        heatmap_bandwidth=S.bandwidth,
        heatmap_color_saturation=S.saturation,
        heatmap_top_altitude=S.top_altitude,
        heatmaps_transition_duration=800,
        on_heatmap_click=S.on_heatmap_click,
        # Hex bin layer
        hex_bin_points_data=S.hexbin_points,
        hex_bin_resolution=S.hex_resolution,
        hex_margin=0.2,
        hex_altitude=rg.js("d => d.points.length * 0.03"),
        hex_top_color=rg.color_scale("d.points.length", "YlOrRd", (0, 8)),
        hex_side_color=rg.color_scale("d.points.length", "YlOrRd", (0, 8), opacity=0.6),
        hex_label=rg.js(
            "d => `<b>${d.points.length}</b> volcanoes<br/>${d.points.slice(0, 6).map(p => p.name).join('<br/>')}`"
        ),
        hex_transition_duration=600,
        on_hex_click=S.on_hex_click,
        # Points layer
        points_data=S.points,
        point_altitude=rg.js("d => Math.max(0.005, d.elevation * 1.2e-5)"),
        point_radius=0.25,
        point_color=rg.js(f"d => {type_color}"),
        point_label=rg.tooltip("<b>{name}</b> · {type}<br/>{country} · {elevation} m"),
        on_point_click=S.on_volcano_click,
        position="absolute",
        inset="0",
    )


def legend_item(name: str, color: str) -> rx.Component:
    return rx.hstack(
        rx.box(width="10px", height="10px", border_radius="50%", background=color),
        rx.text(name, size="1"),
        align="center",
        spacing="1",
    )


def volcano_panel() -> rx.Component:
    return panel(
        "Heatmap & hexbins",
        "425 volcanoes from a JSON file, shown as a density heatmap weighted by elevation, "
        "aggregated hexagonal bins or individual points.",
        segmented(MODES, S.mode, S.set_mode),
        rx.match(
            S.mode,
            (
                "Heatmap",
                rx.vstack(
                    slider("Bandwidth (deg)", S.bandwidth, S.set_bandwidth, 0.3, 5, 0.05),
                    slider("Color saturation", S.saturation, S.set_saturation, 0.5, 8, 0.1),
                    slider("Top altitude", S.top_altitude, S.set_top_altitude, 0, 0.8, 0.02),
                    width="100%",
                ),
            ),
            (
                "Hex bins",
                slider("Hex resolution", S.hex_resolution, S.set_hex_resolution, 1, 4, 1),
            ),
            rx.flex(*[legend_item(k, v) for k, v in TYPE_COLORS.items()], wrap="wrap", spacing="3"),
        ),
        rx.separator(size="4"),
        rx.text("Most common types", size="1", weight="bold"),
        rx.foreach(S.top_types, lambda t: info_row(t[0], t[1])),
        rx.cond(
            S.selected.length() > 0,
            rx.card(
                rx.vstack(
                    rx.heading(S.selected["name"], size="3"),
                    info_row("Country", S.selected["country"]),
                    info_row("Type", S.selected["type"]),
                    info_row("Elevation", S.selected["elevation"]),
                    info_row("Coordinates", S.selected["coords"]),
                    spacing="1",
                    width="100%",
                ),
                width="100%",
                variant="surface",
            ),
        ),
    )


def volcano_page() -> rx.Component:
    return page(volcano_globe(), volcano_panel())

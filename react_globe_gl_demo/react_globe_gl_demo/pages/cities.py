"""Cities: labels, points and HTML markers layers + declarative camera (point_of_view)."""

from __future__ import annotations

from typing import Any

import reflex as rx

import reflex_react_globe_gl as rg

from .. import data
from ..components import info_row, page, panel, segmented, slider, switch
from ..state import DemoState

MODES = ["Labels", "Points", "HTML markers"]

_MARKER_SVG = (
    "<svg viewBox='-4 0 36 36' width='${Math.round(14 + Math.sqrt(d.pop) / 300)}' "
    "style='filter: drop-shadow(0 1px 2px rgba(0,0,0,.6))'>"
    '<path fill=\'${d.capital ? "#22d3ee" : "#fbbf24"}\' d=\'M14,0 C21.732,0 28,5.641 28,12.6 C28,23.963 14,36 14,36 '
    "C14,36 0,24.064 0,12.6 C0,5.641 6.268,0 14,0 Z'></path>"
    "<circle fill='black' cx='14' cy='14' r='7'></circle></svg>"
)


class CitiesState(DemoState):
    cities: list[dict[str, Any]] = []
    mode: str = "Labels"
    min_pop_m: float = 0.0
    capitals_only: bool = False
    selected: dict[str, Any] = {}
    pov: dict[str, float] = {"lat": 25.0, "lng": 10.0, "altitude": 2.2}
    hovered: str = ""

    @rx.event
    def load(self):
        if not self.cities:
            self.cities = data.cities()

    @rx.var
    def filtered(self) -> list[dict[str, Any]]:
        return [c for c in self.cities if c["pop"] >= self.min_pop_m * 1e6 and (c["capital"] or not self.capitals_only)]

    @rx.var
    def labels(self) -> list[dict[str, Any]]:
        return self.filtered if self.mode == "Labels" else []

    @rx.var
    def points(self) -> list[dict[str, Any]]:
        return self.filtered if self.mode == "Points" else []

    @rx.var
    def markers(self) -> list[dict[str, Any]]:
        return self.filtered if self.mode == "HTML markers" else []

    @rx.var
    def rings(self) -> list[dict[str, Any]]:
        return [self.selected] if self.selected else []

    @rx.var
    def city_names(self) -> list[str]:
        return sorted(c["name"] for c in self.filtered)

    @rx.var
    def selected_coords(self) -> str:
        return f"{self.selected['lat']:.2f}, {self.selected['lng']:.2f}" if self.selected else ""

    @rx.var
    def selected_pop(self) -> str:
        return f"{int(self.selected.get('pop', 0)):,}" if self.selected else ""

    @rx.event
    def set_mode(self, value: str | list[str]):
        self.mode = str(value)

    @rx.event
    def set_min_pop(self, value: list[float]):
        self.min_pop_m = float(value[0])

    @rx.event
    def set_capitals_only(self, value: bool):
        self.capitals_only = value

    def _select(self, city: dict[str, Any], source: str):
        self.selected = {k: city[k] for k in ("name", "country", "lat", "lng", "pop", "capital")}
        self.pov = {"lat": city["lat"], "lng": city["lng"], "altitude": 0.8}
        self._log(source, f"{city['name']} ({city['country']})")

    @rx.event
    def on_city_click(self, city: dict[str, Any]):
        self._select(city, "click")

    @rx.event
    def on_city_hover(self, city: dict[str, Any] | None):
        self.hovered = city["name"] if city else ""

    @rx.event
    def select_by_name(self, name: str):
        city = next((c for c in self.cities if c["name"] == name), None)
        if city:
            self._select(city, "select")

    @rx.event
    def reset_view(self):
        self.selected = {}
        self.pov = {"lat": 25.0, "lng": 10.0, "altitude": 2.2}


S = CitiesState


def cities_globe() -> rx.Component:
    size = "d => Math.sqrt(d.pop) * 4e-4"
    return rg.globe(
        id="cities-globe",
        globe_image_url=data.EARTH_NIGHT,
        background_image_url=data.NIGHT_SKY,
        # Declarative camera: bound to backend state.
        point_of_view=S.pov,
        pov_transition_ms=1500,
        # Labels layer
        labels_data=S.labels,
        label_text="name",
        label_size=rg.js(size),
        label_dot_radius=rg.js(size),
        label_color=rg.js(f"d => d.name === {S.selected['name']} ? '#22d3ee' : 'rgba(255, 165, 0, 0.75)'"),
        label_resolution=2,
        label_label=rg.tooltip("<b>{name}</b><br/>{country}"),
        on_label_click=S.on_city_click,
        on_label_hover=S.on_city_hover,
        # Points layer
        points_data=S.points,
        point_altitude=rg.js("d => Math.sqrt(d.pop) * 1.5e-5"),
        point_radius=0.35,
        point_color=rg.js("d => d.capital ? '#22d3ee' : '#fbbf24'"),
        point_label=rg.tooltip("<b>{name}</b><br/>{country}<br/>pop. {pop}"),
        points_merge=False,
        on_point_click=S.on_city_click,
        on_point_hover=S.on_city_hover,
        # HTML elements layer
        html_elements_data=S.markers,
        html_markup=rg.js(f"d => `{_MARKER_SVG}`"),
        html_transition_duration=500,
        on_html_element_click=S.on_city_click,
        on_html_element_hover=S.on_city_hover,
        # Rings around the selected city
        rings_data=S.rings,
        ring_color=rg.js("() => t => `rgba(34, 211, 238, ${1 - t})`"),
        ring_max_radius=4,
        ring_propagation_speed=3,
        ring_repeat_period=600,
        position="absolute",
        inset="0",
    )


def cities_panel() -> rx.Component:
    return panel(
        "Cities & markers",
        "243 populated places rendered as 3D text labels, extruded points or DOM (HTML) markers. "
        "The camera is driven declaratively by the point_of_view prop bound to backend state.",
        rx.text("Layer", size="1", weight="medium"),
        segmented(MODES, S.mode, S.set_mode),
        slider("Min. population (millions)", S.min_pop_m, S.set_min_pop, 0, 15, 0.5),
        switch("Capitals only", S.capitals_only, S.set_capitals_only),
        rx.select(S.city_names, placeholder="Fly to a city…", on_change=S.select_by_name, size="2", width="100%"),
        info_row("Visible cities", S.filtered.length()),
        info_row("Hovered", rx.cond(S.hovered != "", S.hovered, "—")),
        rx.cond(
            S.selected.length() > 0,
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.heading(S.selected["name"].to(str), size="3"),
                        rx.cond(S.selected["capital"].to(bool), rx.badge("capital", color_scheme="cyan")),
                        width="100%",
                        align="center",
                    ),
                    info_row("Country", S.selected["country"].to(str)),
                    info_row("Population", S.selected_pop),
                    info_row("Lat, Lng", S.selected_coords),
                    rx.button("Reset view", size="1", variant="soft", on_click=S.reset_view),
                    spacing="1",
                    width="100%",
                ),
                width="100%",
                variant="surface",
            ),
            rx.text("Click a label, point or marker.", size="1", color_scheme="gray"),
        ),
    )


def cities_page() -> rx.Component:
    return page(cities_globe(), cities_panel())

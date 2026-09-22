"""Countries: choropleth / elevated polygons / hexed polygons with hover & click."""

from __future__ import annotations

from typing import Any

import reflex as rx

import reflex_react_globe_gl as rg

from .. import data
from ..components import info_row, page, panel, segmented, slider, switch
from ..state import DemoState

METRICS: dict[str, tuple[str, str]] = {
    # label: (property, unit)
    "Population": ("POP_EST", "people"),
    "GDP": ("GDP_MD_EST", "M$"),
    "GDP/capita": ("GDP_PC", "$"),
}


def _features() -> list[dict[str, Any]]:
    feats = []
    for f in data.countries():
        props = dict(f["properties"])
        pop = props.get("POP_EST") or 0
        gdp = props.get("GDP_MD_EST") or 0
        props["GDP_PC"] = round(gdp * 1e6 / pop) if pop else 0
        feats.append({"type": f["type"], "properties": props, "geometry": f["geometry"]})
    return feats


class CountriesState(DemoState):
    features: list[dict[str, Any]] = []
    metric: str = "Population"
    style: str = "Choropleth"
    elevation: float = 0.35
    hex_dots: bool = True
    show_labels: bool = False
    hovered: str = ""
    selected: dict[str, str] = {}

    @rx.event
    def load(self):
        if not self.features:
            self.features = _features()

    @rx.var
    def metric_prop(self) -> str:
        return METRICS[self.metric][0]

    @rx.var
    def metric_max(self) -> float:
        prop = METRICS[self.metric][0]
        values = sorted(f["properties"].get(prop) or 0 for f in self.features)
        # Use the 97th percentile to keep outliers (China, USA...) from flattening the scale.
        return float(values[int(len(values) * 0.97)]) if values else 1.0

    @rx.var
    def polygons(self) -> list[dict[str, Any]]:
        return self.features if self.style != "Hexed" else []

    @rx.var
    def hex_polygons(self) -> list[dict[str, Any]]:
        return self.features if self.style == "Hexed" else []

    @rx.var
    def labels(self) -> list[dict[str, Any]]:
        if not self.show_labels:
            return []
        return [
            {"name": f["properties"]["NAME"], "lat": c[0], "lng": c[1]}
            for f in self.features
            if (f["properties"].get("POP_EST") or 0) > 30_000_000 and (c := _centroid(f["geometry"]))
        ]

    @rx.event
    def set_metric(self, value: str | list[str]):
        self.metric = str(value)

    @rx.event
    def set_style(self, value: str | list[str]):
        self.style = str(value)

    @rx.event
    def set_elevation(self, value: list[float]):
        self.elevation = float(value[0])

    @rx.event
    def set_hex_dots(self, value: bool):
        self.hex_dots = value

    @rx.event
    def set_show_labels(self, value: bool):
        self.show_labels = value

    @rx.event
    def on_hover(self, feature: dict[str, Any] | None):
        self.hovered = feature["properties"]["ADMIN"] if feature else ""

    @rx.event
    def on_click(self, feature: dict[str, Any], coords: dict[str, Any]):
        p = feature["properties"]
        self.selected = {
            "name": p["ADMIN"],
            "iso": p.get("ISO_A2") or "",
            "continent": p.get("CONTINENT") or "",
            "subregion": p.get("SUBREGION") or "",
            "population": f"{p.get('POP_EST') or 0:,}",
            "gdp": f"{p.get('GDP_MD_EST') or 0:,} M$",
            "gdp_pc": f"{p.get('GDP_PC') or 0:,} $",
            "income": (p.get("INCOME_GRP") or "").split(". ")[-1],
        }
        self._log("polygon click", f"{p['ADMIN']} @ {coords['lat']:.1f}, {coords['lng']:.1f}")
        return rg.fly_to("countries-globe", coords["lat"], coords["lng"], 1.7, 1200)

    @rx.event
    def clear_selection(self):
        self.selected = {}
        return rg.fly_to("countries-globe", altitude=2.5, transition_ms=1200)


def _centroid(geometry: dict[str, Any]) -> tuple[float, float] | None:
    """Rough centroid (lat, lng) of the largest ring of a (Multi)Polygon."""
    rings = (
        [geometry["coordinates"][0]] if geometry["type"] == "Polygon" else [poly[0] for poly in geometry["coordinates"]]
    )
    ring = max(rings, key=len, default=None)
    if not ring:
        return None
    return (sum(p[1] for p in ring) / len(ring), sum(p[0] for p in ring) / len(ring))


# Value of the selected metric for a feature, in JS.
_VALUE = f"(d.properties[{CountriesState.metric_prop}] || 0)"
_IS_HOVER = f"d.properties.ADMIN === {CountriesState.hovered}"
_IS_SELECTED = f"d.properties.ADMIN === {CountriesState.selected['name']}"

_TOOLTIP = rg.js(
    'd => `<div style="font:12px sans-serif;padding:4px 6px;background:rgba(0,0,0,.75);border-radius:6px">'
    "<b>${d.properties.ADMIN} (${d.properties.ISO_A2})</b><br/>"
    "Population: <i>${(d.properties.POP_EST || 0).toLocaleString()}</i><br/>"
    "GDP: <i>${(d.properties.GDP_MD_EST || 0).toLocaleString()}</i> M$<br/>"
    "GDP per capita: <i>${(d.properties.GDP_PC || 0).toLocaleString()}</i> $</div>`"
)


def countries_globe() -> rx.Component:
    scale = f"window.ReflexGlobe.colorScale('YlOrRd', [0, {CountriesState.metric_max}], 'sqrt')"
    elevated = CountriesState.style == "Elevated"
    return rg.globe(
        id="countries-globe",
        globe_image_url=data.EARTH_NIGHT,
        background_image_url=data.NIGHT_SKY,
        line_hover_precision=0,
        # Polygons layer (choropleth / elevated)
        polygons_data=CountriesState.polygons,
        polygon_altitude=rg.js(
            f"d => ({_IS_HOVER} || {_IS_SELECTED}) ? 0.12 : ({elevated} "
            f"? Math.max(0.01, Math.sqrt(Math.min(1, {_VALUE} / {CountriesState.metric_max})) * {CountriesState.elevation}) "
            ": 0.06)"
        ),
        polygon_cap_color=rg.js(f"d => {_IS_SELECTED} ? '#22d3ee' : ({_IS_HOVER} ? 'steelblue' : {scale}({_VALUE}))"),
        polygon_side_color=rg.constant("rgba(0, 100, 0, 0.15)"),
        polygon_stroke_color=rg.constant("#111"),
        polygon_label=_TOOLTIP,
        polygons_transition_duration=300,
        on_polygon_hover=CountriesState.on_hover,
        on_polygon_click=CountriesState.on_click,
        # Hexed polygons layer
        hex_polygons_data=CountriesState.hex_polygons,
        hex_polygon_resolution=3,
        hex_polygon_margin=0.3,
        hex_polygon_use_dots=CountriesState.hex_dots,
        hex_polygon_altitude=rg.js(f"d => {_IS_HOVER} ? 0.03 : 0.005"),
        hex_polygon_color=rg.js(f"d => {_IS_HOVER} ? '#ffffff' : {scale}({_VALUE})"),
        hex_polygon_label=_TOOLTIP,
        on_hex_polygon_hover=CountriesState.on_hover,
        on_hex_polygon_click=CountriesState.on_click,
        # Labels layer
        labels_data=CountriesState.labels,
        label_text="name",
        label_size=1.2,
        label_dot_radius=0.4,
        label_altitude=rx.cond(elevated, CountriesState.elevation + 0.03, 0.13),
        label_color=rg.constant("rgba(255, 255, 255, 0.85)"),
        label_resolution=2,
        position="absolute",
        inset="0",
    )


def countries_panel() -> rx.Component:
    return panel(
        "Countries",
        "Natural Earth polygons as a choropleth, elevated by the selected metric or rendered as hexed dots. "
        "Hover highlights through backend state; click flies the camera to the country.",
        rx.text("Metric", size="1", weight="medium"),
        segmented(list(METRICS), CountriesState.metric, CountriesState.set_metric),
        rx.text("Style", size="1", weight="medium"),
        segmented(["Choropleth", "Elevated", "Hexed"], CountriesState.style, CountriesState.set_style),
        rx.cond(
            CountriesState.style == "Elevated",
            slider("Max elevation", CountriesState.elevation, CountriesState.set_elevation, 0.05, 1, 0.05),
        ),
        rx.cond(
            CountriesState.style == "Hexed",
            switch("Dots instead of hexagons", CountriesState.hex_dots, CountriesState.set_hex_dots),
        ),
        switch("Labels (>30M people)", CountriesState.show_labels, CountriesState.set_show_labels),
        rx.separator(size="4"),
        info_row("Hovered", rx.cond(CountriesState.hovered != "", CountriesState.hovered, "—")),
        rx.cond(
            CountriesState.selected.length() > 0,
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.heading(CountriesState.selected["name"], size="3"),
                        rx.badge(CountriesState.selected["iso"]),
                        rx.spacer(),
                        rx.icon_button(
                            rx.icon("x", size=12), size="1", variant="ghost", on_click=CountriesState.clear_selection
                        ),
                        width="100%",
                        align="center",
                    ),
                    info_row("Continent", CountriesState.selected["continent"]),
                    info_row("Subregion", CountriesState.selected["subregion"]),
                    info_row("Population", CountriesState.selected["population"]),
                    info_row("GDP", CountriesState.selected["gdp"]),
                    info_row("GDP per capita", CountriesState.selected["gdp_pc"]),
                    info_row("Income group", CountriesState.selected["income"]),
                    spacing="1",
                    width="100%",
                ),
                width="100%",
                variant="surface",
            ),
            rx.text("Click a country to see its details.", size="1", color_scheme="gray"),
        ),
    )


def countries_page() -> rx.Component:
    return page(countries_globe(), countries_panel())

"""Tiles: slippy-map tile engine and the tiles (lat/lng rectangles) layer."""

from __future__ import annotations

from typing import Any

import reflex as rx

import reflex_react_globe_gl as rg

from .. import data
from ..components import code_note, info_row, page, panel, segmented, slider, switch
from ..state import DemoState

PROVIDERS: dict[str, str] = {
    "OpenStreetMap": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    "CARTO dark": "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
    "ESRI imagery": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
}

MODES = ["Tile engine", "Tiles layer"]


class TilesState(DemoState):
    mode: str = "Tile engine"
    provider: str = "OpenStreetMap"
    max_level: int = 17
    step: int = 30
    tile_altitude: float = 0.02
    margin: float = 0.6
    use_projection: bool = True
    tiles: list[dict[str, Any]] = []
    toggled: list[int] = []

    @rx.event
    def load(self):
        if not self.tiles:
            self.tiles = data.tile_grid(self.step)

    @rx.var
    def template(self) -> str:
        return PROVIDERS.get(self.provider, PROVIDERS["OpenStreetMap"]) if self.mode == "Tile engine" else ""

    @rx.var
    def tile_items(self) -> list[dict[str, Any]]:
        if self.mode != "Tiles layer":
            return []
        return [{**t, "on": t["id"] in self.toggled} for t in self.tiles]

    @rx.event
    def set_mode(self, value: str | list[str]):
        self.mode = str(value)

    @rx.event
    def set_provider(self, value: str | list[str]):
        self.provider = str(value)
        self._log("provider", self.provider)

    @rx.event
    def set_max_level(self, value: list[float]):
        self.max_level = int(value[0])

    @rx.event
    def set_step(self, value: list[float]):
        self.step = int(value[0])
        self.tiles = data.tile_grid(self.step)
        self.toggled = []

    @rx.event
    def set_tile_altitude(self, value: list[float]):
        self.tile_altitude = float(value[0])

    @rx.event
    def set_margin(self, value: list[float]):
        self.margin = float(value[0])

    @rx.event
    def set_use_projection(self, value: bool):
        self.use_projection = value

    @rx.event
    def on_tile_click(self, tile: dict[str, Any]):
        tid = tile["id"]
        self.toggled = [t for t in self.toggled if t != tid] if tid in self.toggled else [*self.toggled, tid]
        self._log("tile click", f"#{tid} @ {tile['lat']}, {tile['lng']}")


S = TilesState


def tiles_globe() -> rx.Component:
    return rg.globe(
        id="tiles-globe",
        background_image_url=data.NIGHT_SKY,
        globe_image_url=rx.cond(S.mode == "Tiles layer", data.EARTH_DARK, ""),
        # Slippy map tile engine: the URL builder is regenerated from a state var.
        # Slippy map tile engine. Each branch is a static JS function, so re-renders
        # caused by other state changes don't reset the tile cache.
        globe_tile_engine_url=rx.match(
            S.template,
            *[(url, rg.tile_url(url)) for url in PROVIDERS.values()],
            rx.Var.create(None),
        ),
        globe_tile_engine_max_level=S.max_level,
        # Tiles layer
        tiles_data=S.tile_items,
        tile_width=S.step - S.margin * S.step / 10,
        tile_height=S.step - S.margin * S.step / 10,
        tile_altitude=rg.js(f"d => d.on ? {S.tile_altitude} * 4 : {S.tile_altitude}"),
        tile_use_globe_projection=S.use_projection,
        tile_material=rg.js(
            "d => new window.ReflexGlobe.THREE.MeshLambertMaterial("
            "{ color: d.on ? '#ffffff' : d.color, opacity: d.on ? 0.95 : 0.55, transparent: true })"
        ),
        tile_label=rg.tooltip("Tile #{id}<br/>{lat}, {lng}"),
        tiles_transition_duration=500,
        on_tile_click=S.on_tile_click,
        point_of_view={"lat": 45, "lng": 5, "altitude": 1.8},
        position="absolute",
        inset="0",
    )


def tiles_panel() -> rx.Component:
    return panel(
        "Tiles & map engine",
        "The globe surface can be a live slippy map (zoom in to load more detail) or a grid of "
        "lat/lng tiles with their own ThreeJS materials.",
        segmented(MODES, S.mode, S.set_mode),
        rx.cond(
            S.mode == "Tile engine",
            rx.vstack(
                rx.text("Provider", size="1", weight="medium"),
                segmented(list(PROVIDERS), S.provider, S.set_provider),
                slider("Max zoom level", S.max_level, S.set_max_level, 2, 19, 1),
                rx.button(
                    rx.icon("refresh-cw", size=14),
                    "Clear tile cache",
                    size="1",
                    variant="soft",
                    on_click=rg.clear_tile_cache("tiles-globe"),
                ),
                info_row("URL template", rx.code(S.template, size="1")),
                code_note('globe_tile_engine_url=rg.tile_url(\n    "https://tile.openstreetmap.org/{z}/{x}/{y}.png")'),
                width="100%",
                spacing="3",
            ),
            rx.vstack(
                slider("Grid step (deg)", S.step, S.set_step, 10, 45, 5),
                slider("Altitude", S.tile_altitude, S.set_tile_altitude, 0, 0.2, 0.005),
                slider("Margin", S.margin, S.set_margin, 0, 3, 0.1),
                switch("Curved (globe projection)", S.use_projection, S.set_use_projection),
                info_row("Tiles", S.tile_items.length()),
                info_row("Highlighted (click to toggle)", S.toggled.length()),
                width="100%",
                spacing="3",
            ),
        ),
    )


def tiles_page() -> rx.Component:
    return page(tiles_globe(), tiles_panel())

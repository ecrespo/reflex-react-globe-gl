"""Demo app for reflex-react-globe-gl: one page per react-globe.gl feature family."""

import reflex as rx

from .pages.cities import CitiesState, cities_page
from .pages.countries import CountriesState, countries_page
from .pages.flights import FlightsState, flights_page
from .pages.playground import playground_page
from .pages.population import PopulationState, population_page
from .pages.space import SpaceState, space_page
from .pages.tiles import TilesState, tiles_page
from .pages.volcanoes import VolcanoState, volcano_page

SUFFIX = " · reflex-react-globe-gl"

app = rx.App(style={"body": {"overflow": "hidden"}})
app.add_page(population_page, route="/", title="World population" + SUFFIX, on_load=PopulationState.load)
app.add_page(countries_page, route="/countries", title="Countries" + SUFFIX, on_load=CountriesState.load)
app.add_page(flights_page, route="/flights", title="Arcs & rings" + SUFFIX, on_load=FlightsState.load)
app.add_page(cities_page, route="/cities", title="Cities & markers" + SUFFIX, on_load=CitiesState.load)
app.add_page(volcano_page, route="/volcanoes", title="Heatmap & hexbins" + SUFFIX, on_load=VolcanoState.load)
app.add_page(space_page, route="/space", title="Objects, particles & paths" + SUFFIX, on_load=SpaceState.load)
app.add_page(tiles_page, route="/tiles", title="Tiles & map engine" + SUFFIX, on_load=TilesState.load)
app.add_page(playground_page, route="/playground", title="Globe playground" + SUFFIX)

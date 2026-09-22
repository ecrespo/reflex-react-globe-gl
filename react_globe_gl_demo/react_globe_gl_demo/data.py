"""Datasets used by the demo (Natural Earth + upstream react-globe.gl samples)."""

from __future__ import annotations

import csv
import json
import math
import os
import random
from functools import cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent / "data"

IMG = os.environ.get("GLOBE_IMG_BASE", "https://cdn.jsdelivr.net/npm/three-globe@2.45.2/example/img")
EARTH_NIGHT = f"{IMG}/earth-night.jpg"
EARTH_DAY = f"{IMG}/earth-day.jpg"
EARTH_BLUE_MARBLE = f"{IMG}/earth-blue-marble.jpg"
EARTH_DARK = f"{IMG}/earth-dark.jpg"
EARTH_WATER = f"{IMG}/earth-water.png"
EARTH_TOPOLOGY = f"{IMG}/earth-topology.png"
NIGHT_SKY = f"{IMG}/night-sky.png"

GLOBE_IMAGES: dict[str, str] = {
    "Night lights": EARTH_NIGHT,
    "Day": EARTH_DAY,
    "Blue marble": EARTH_BLUE_MARBLE,
    "Dark": EARTH_DARK,
    "Water mask": EARTH_WATER,
    "None (material only)": "",
}


@cache
def world_population() -> list[dict[str, float]]:
    """~11k population cells: {lat, lng, pop}."""
    with open(DATA_DIR / "world_population.csv", newline="") as fh:
        return [{"lat": float(r["lat"]), "lng": float(r["lng"]), "pop": float(r["pop"])} for r in csv.DictReader(fh)]


@cache
def countries() -> list[dict[str, Any]]:
    """Natural Earth 1:110m admin-0 country features."""
    with open(DATA_DIR / "ne_110m_admin_0_countries.geojson") as fh:
        feats = json.load(fh)["features"]
    return [f for f in feats if f["properties"]["ISO_A2"] != "AQ"]


@cache
def cities() -> list[dict[str, Any]]:
    """243 populated places: {name, country, lat, lng, pop, capital}."""
    with open(DATA_DIR / "ne_110m_populated_places_simple.geojson") as fh:
        feats = json.load(fh)["features"]
    out = []
    for f in feats:
        p = f["properties"]
        out.append(
            {
                "name": p["name"],
                "country": p["adm0name"],
                "lat": p["latitude"],
                "lng": p["longitude"],
                "pop": p["pop_max"],
                "capital": bool(p["adm0cap"]),
                "megacity": bool(p["megacity"]),
            }
        )
    return out


@cache
def volcanoes() -> list[dict[str, Any]]:
    """World volcanoes: {name, country, type, lat, lng, elevation}."""
    with open(DATA_DIR / "world_volcanoes.json") as fh:
        raw = json.load(fh)
    return [
        {
            "name": v["name"],
            "country": v["country"],
            "type": v["type"],
            "lat": v["lat"],
            "lng": v["lon"],
            "elevation": v["elevation"],
        }
        for v in raw
    ]


def random_arcs(n: int = 20, seed: int | None = None) -> list[dict[str, Any]]:
    rnd = random.Random(seed)
    palette = ["#ff4d6d", "#ffd166", "#06d6a0", "#4cc9f0", "#ffffff"]
    return [
        {
            "startLat": (rnd.random() - 0.5) * 180,
            "startLng": (rnd.random() - 0.5) * 360,
            "endLat": (rnd.random() - 0.5) * 180,
            "endLng": (rnd.random() - 0.5) * 360,
            "color": [rnd.choice(palette), rnd.choice(palette)],
            "label": f"Route #{i + 1}",
        }
        for i in range(n)
    ]


def random_paths(n: int = 10, seed: int | None = None) -> list[dict[str, Any]]:
    """Smooth random-walk paths: {name, coords: [[lat, lng, alt], ...], color}."""
    rnd = random.Random(seed)
    palette = ["#ff4d6d", "#ffd166", "#06d6a0", "#4cc9f0", "#b388ff"]
    paths = []
    for i in range(n):
        lat = (rnd.random() - 0.5) * 90
        lng = (rnd.random() - 0.5) * 360
        alt = 0.0
        heading = rnd.random() * 2 * math.pi
        coords = [[lat, lng, alt]]
        for _ in range(rnd.randint(150, 450)):
            heading += (rnd.random() * 2 - 1) * 0.35
            lat = max(-85.0, min(85.0, lat + math.sin(heading) * 0.8))
            lng += math.cos(heading) * 0.8
            alt = max(0.0, min(0.3, alt + (rnd.random() * 2 - 1) * 0.012))
            coords.append([round(lat, 3), round(lng, 3), round(alt, 4)])
        paths.append({"name": f"Path {i + 1}", "coords": coords, "color": [rnd.choice(palette), rnd.choice(palette)]})
    return paths


def random_satellites(n: int = 60, seed: int | None = None) -> list[dict[str, Any]]:
    rnd = random.Random(seed)
    return [
        {
            "id": i,
            "name": f"SAT-{i:03d}",
            "lat": (rnd.random() - 0.5) * 160,
            "lng": (rnd.random() - 0.5) * 360,
            "alt": 0.15 + rnd.random() * 0.6,
            "size": 0.8 + rnd.random() * 1.6,
            "color": rnd.choice(["#4cc9f0", "#ffd166", "#ff4d6d", "#b8f2e6"]),
        }
        for i in range(n)
    ]


def particle_clouds(seed: int | None = None) -> list[dict[str, Any]]:
    """Two particle sets (a GPS-like shell and a debris belt)."""
    rnd = random.Random(seed)

    def shell(count: int, alt: float, spread: float) -> list[dict[str, float]]:
        pts = []
        for _ in range(count):
            u, v = rnd.random(), rnd.random()
            lat = math.degrees(math.acos(2 * u - 1)) - 90
            pts.append({"lat": lat, "lng": v * 360 - 180, "alt": alt + rnd.random() * spread})
        return pts

    return [
        {"name": "Navigation shell", "color": "#ffd166", "size": 2.0, "points": shell(600, 1.8, 0.3)},
        {"name": "Debris belt", "color": "#aaaaaa", "size": 0.8, "points": shell(3000, 0.12, 0.25)},
    ]


def tile_grid(step: int = 30) -> list[dict[str, Any]]:
    """A checkerboard of lat/lng tiles."""
    tiles = []
    k = 0
    for lat in range(-90 + step // 2, 90, step):
        for lng in range(-180 + step // 2, 180, step):
            tiles.append(
                {
                    "id": k,
                    "lat": lat,
                    "lng": lng,
                    "color": "#4cc9f0" if (lat // step + lng // step) % 2 else "#ff4d6d",
                }
            )
            k += 1
    return tiles

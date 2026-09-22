"""Layout building blocks shared by the demo pages."""

from __future__ import annotations

from typing import Any

import reflex as rx

from .state import DemoState

NAV: list[tuple[str, str, str]] = [
    ("/", "World population", "hexagon"),
    ("/countries", "Countries", "map"),
    ("/flights", "Arcs & rings", "plane"),
    ("/cities", "Cities & markers", "map-pin"),
    ("/volcanoes", "Heatmap & hexbins", "flame"),
    ("/space", "Objects, particles & paths", "satellite"),
    ("/tiles", "Tiles & map engine", "grid-3x3"),
    ("/playground", "Globe playground", "sliders-horizontal"),
]

PANEL_WIDTH = "340px"


def nav_item(href: str, label: str, icon: str) -> rx.Component:
    active = rx.State.router.page.path == href
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=16),
            rx.text(label, size="2"),
            align="center",
            spacing="2",
            padding_x="10px",
            padding_y="7px",
            border_radius="8px",
            width="100%",
            background=rx.cond(active, rx.color("cyan", 4), "transparent"),
            color=rx.cond(active, rx.color("cyan", 11), rx.color("gray", 11)),
            _hover={"background": rx.color("gray", 4)},
        ),
        href=href,
        underline="none",
        width="100%",
    )


def sidebar() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon("globe", size=22, color=rx.color("cyan", 10)),
            rx.vstack(
                rx.heading("reflex-react-globe-gl", size="3"),
                rx.text("react-globe.gl for Reflex", size="1", color_scheme="gray"),
                spacing="0",
            ),
            align="center",
            spacing="2",
            padding_bottom="12px",
        ),
        *[nav_item(*n) for n in NAV],
        rx.spacer(),
        rx.hstack(
            rx.link(
                rx.icon("git-branch", size=16),
                href="https://github.com/ecrespo/reflex-react-globe-gl",
                is_external=True,
            ),
            rx.link(
                rx.text("upstream", size="1"), href="https://github.com/vasturiano/react-globe.gl", is_external=True
            ),
            rx.color_mode.button(size="1", variant="ghost"),
            align="center",
            spacing="3",
        ),
        width="240px",
        min_width="240px",
        height="100vh",
        padding="16px",
        spacing="1",
        border_right=f"1px solid {rx.color('gray', 5)}",
        background=rx.color("gray", 2),
        display=["none", "none", "flex"],
    )


def mobile_nav() -> rx.Component:
    return rx.box(
        rx.menu.root(
            rx.menu.trigger(rx.button(rx.icon("menu"), "Examples", size="2", variant="soft")),
            rx.menu.content(*[rx.menu.item(rx.link(label, href=href, underline="none")) for href, label, _ in NAV]),
        ),
        position="absolute",
        top="12px",
        left="12px",
        z_index="20",
        display=["block", "block", "none"],
    )


def event_log() -> rx.Component:
    return rx.cond(
        DemoState.show_log,
        rx.card(
            rx.hstack(
                rx.icon("activity", size=14),
                rx.text("Events", size="1", weight="bold"),
                rx.spacer(),
                rx.icon_button(rx.icon("trash-2", size=12), size="1", variant="ghost", on_click=DemoState.clear_log),
                rx.icon_button(rx.icon("x", size=12), size="1", variant="ghost", on_click=DemoState.toggle_log),
                align="center",
                width="100%",
            ),
            rx.cond(
                DemoState.events.length() > 0,
                rx.vstack(
                    rx.foreach(
                        DemoState.events,
                        lambda e: rx.hstack(
                            rx.code(e["time"], size="1", variant="ghost"),
                            rx.badge(e["kind"], size="1", variant="soft"),
                            rx.text(e["detail"], size="1", trim="both", style={"word_break": "break-all"}),
                            spacing="2",
                            align="start",
                        ),
                    ),
                    spacing="1",
                    padding_top="6px",
                ),
                rx.text("Hover or click the globe…", size="1", color_scheme="gray", padding_top="6px"),
            ),
            position="absolute",
            bottom="16px",
            left="16px",
            width=["calc(100% - 32px)", "420px"],
            max_height="230px",
            overflow="auto",
            z_index="10",
            style={"backdrop_filter": "blur(8px)", "background": "rgba(10,12,24,0.72)"},
        ),
        rx.icon_button(
            rx.icon("activity"),
            on_click=DemoState.toggle_log,
            position="absolute",
            bottom="16px",
            left="16px",
            z_index="10",
            variant="soft",
        ),
    )


def panel(title: str, description: str, *children: rx.Component) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(title, size="4"),
            rx.text(description, size="2", color_scheme="gray"),
            rx.separator(size="4"),
            *children,
            spacing="3",
            width="100%",
        ),
        position="absolute",
        top="16px",
        right="16px",
        width=["calc(100% - 32px)", PANEL_WIDTH],
        max_height=["45vh", "calc(100vh - 32px)"],
        overflow_y="auto",
        z_index="10",
        style={"backdrop_filter": "blur(8px)", "background": "rgba(10,12,24,0.78)"},
    )


def page(globe: rx.Component, side_panel: rx.Component, legend: rx.Component | None = None) -> rx.Component:
    return rx.hstack(
        sidebar(),
        rx.box(
            globe,
            mobile_nav(),
            side_panel,
            legend if legend is not None else rx.fragment(),
            event_log(),
            position="relative",
            flex="1",
            height="100vh",
            overflow="hidden",
            background="#000011",
        ),
        spacing="0",
        width="100%",
        height="100vh",
        overflow="hidden",
    )


# ---------------------------------------------------------------- controls


def field(label: str, control: rx.Component, value: Any = None) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(label, size="1", weight="medium"),
            rx.spacer(),
            rx.code(value, size="1", variant="ghost") if value is not None else rx.fragment(),
            width="100%",
            align="center",
        ),
        control,
        spacing="1",
        width="100%",
    )


def slider(label: str, value: Any, on_change: Any, min_: float, max_: float, step: float) -> rx.Component:
    return field(
        label,
        rx.slider(
            value=[value],
            min=min_,
            max=max_,
            step=step,
            on_change=on_change,
            size="1",
            width="100%",
        ),
        value,
    )


def switch(label: str, checked: Any, on_change: Any) -> rx.Component:
    return rx.hstack(
        rx.text(label, size="2"),
        rx.spacer(),
        rx.switch(checked=checked, on_change=on_change, size="1"),
        width="100%",
        align="center",
    )


def segmented(options: list[str], value: Any, on_change: Any) -> rx.Component:
    return rx.segmented_control.root(
        *[rx.segmented_control.item(o, value=o) for o in options],
        value=value,
        on_change=on_change,
        size="1",
        width="100%",
    )


def info_row(label: str, value: Any) -> rx.Component:
    return rx.hstack(
        rx.text(label, size="1", color_scheme="gray"),
        rx.spacer(),
        rx.text(value, size="1", weight="medium", align="right"),
        width="100%",
    )


def code_note(text: str) -> rx.Component:
    return rx.code_block(text, language="python", font_size="11px", width="100%", wrap_long_lines=True)

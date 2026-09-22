# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-09-21

First public release.

### Added

- `Globe` component (`rg.globe`) wrapping [react-globe.gl](https://github.com/vasturiano/react-globe.gl)
  2.38 as a Reflex `NoSSRComponent`, exposing every upstream prop and callback: globe surface,
  points, arcs, polygons, paths, heatmaps, hex bins, hexed polygons, tiles, particles, rings,
  labels, HTML elements, 3D objects and custom ThreeJS layers.
- A JS wrapper (`globe_wrapper.js`) providing responsive sizing via `ResizeObserver`,
  JSON-safe event payloads (ThreeJS internals, DOM events and cycles are stripped in the
  browser), stable accessor identities and a declarative camera/controls/material API.
- Reflex extensions as plain props: `point_of_view`, `auto_rotate`, `auto_rotate_speed`,
  `animation_paused`, `globe_material_options`, `event_data_exclude`, `zoom_throttle_ms`,
  `html_markup`.
- Imperative actions usable as event triggers or returned from handlers: `fly_to` /
  `point_of_view`, `get_point_of_view`, `pause_animation`, `resume_animation`,
  `set_controls`, `clear_tile_cache`, `get_screen_coords`, `to_globe_coords`, `get_coords`,
  `get_globe_radius`, `run_js`.
- Accessor helpers: `js`, `constant`, `attr`, `color_scale` (15 built-in palettes),
  `tooltip`, `tile_url`, `three_mesh`, `three_material`.
- Type stubs (`react_globe_gl.pyi`) and `py.typed` for editor autocompletion.
- Demo app (`react_globe_gl_demo`) with eight pages covering every layer.

### Fixed

- Require `reflex>=0.9.12`. Reflex 0.9.11 and earlier ship a `reflex-base` whose
  `reflex_base.components.tags` does not export `CommonTag`, which the published
  `reflex-components-radix` / `reflex-components-core` packages import — any app using
  `rx.plugins` fails at import time with `ImportError: cannot import name 'CommonTag'`.

[Unreleased]: https://github.com/ecrespo/reflex-react-globe-gl/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ecrespo/reflex-react-globe-gl/releases/tag/v0.1.0

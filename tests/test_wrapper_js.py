"""Exercise the pure functions of globe_wrapper.js with Node (skipped without node)."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

WRAPPER = Path(__file__).parents[1] / "custom_components" / "reflex_react_globe_gl" / "globe_wrapper.js"

HARNESS = r"""
const fs = require("fs");
let src = fs.readFileSync(process.argv[process.argv.length - 1], "utf8");
// Strip ESM imports/exports and provide stubs so the module body can run in Node.
src = src.replace(/^import[\s\S]*?from\s+"[^"]+";\n/gm, "");
src = src.replace(/^export default .*$/m, "");
src = src.replace(/^export const /gm, "const ");
const stubs = `
  const React = { createElement: () => null };
  const forwardRef = (f) => f, useCallback = (f) => f, useEffect = () => {}, useImperativeHandle = () => {};
  const useMemo = (f) => f(), useRef = (v) => ({ current: v }), useState = (v) => [v, () => {}];
  const Globe = () => null;
  const THREE = { Color: function (c) { this.c = c; } };
`;
const body = stubs + src + "\n;return { sanitize, colorScale, sameValue, PALETTES };";
const api = new Function(body)();
const out = {};
// sanitize: strips __ keys, THREE objects, functions, cycles and excluded keys
const cyc = { a: 1, __threeObj: { isObject3D: true }, fn: () => 1, geometry: { big: true }, nested: { b: [1, NaN, 2] } };
cyc.self = cyc;
out.sanitized = api.sanitize(cyc, ["geometry"]);
out.sanitizedNull = api.sanitize(undefined);
out.bigArray = api.sanitize(Array.from({ length: 5000 }, (_, i) => i)).length;
// colorScale
const s = api.colorScale("YlOrRd", [0, 100], "linear");
out.scaleLow = s(0);
out.scaleHigh = s(100);
out.scaleClamp = s(1000);
out.scaleCached = api.colorScale("YlOrRd", [0, 100], "linear") === s;
out.scaleAlpha = api.colorScale(["#000000", "#ffffff"], [0, 1], "linear", 0.5)(0.5);
out.sqrt = api.colorScale(["#000000", "#ffffff"], [0, 100], "sqrt")(25);
// sameValue
out.sameFn = api.sameValue((d) => d.x, (d) => d.x);
out.stateFn = api.sameValue((d) => reflex___state.x, (d) => reflex___state.x);
out.sameArr = api.sameValue([{ a: 1 }], [{ a: 1 }]);
out.diffArr = api.sameValue([{ a: 1 }], [{ a: 2 }]);
console.log(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def result() -> dict:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    proc = subprocess.run([node, "-e", HARNESS, str(WRAPPER)], capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def test_sanitize(result):
    s = result["sanitized"]
    assert s == {"a": 1, "nested": {"b": [1, None, 2]}}
    assert result["sanitizedNull"] is None
    assert result["bigArray"] == 2000


def test_color_scale(result):
    assert result["scaleLow"] == "rgb(255,255,204)"
    assert result["scaleHigh"] == "rgb(128,0,38)"
    assert result["scaleClamp"] == result["scaleHigh"]
    assert result["scaleCached"] is True
    assert result["scaleAlpha"] == "rgba(128,128,128,0.5)"
    assert result["sqrt"] == "rgb(128,128,128)"


def test_same_value(result):
    assert result["sameFn"] is True
    assert result["stateFn"] is False
    assert result["sameArr"] is True
    assert result["diffArr"] is False

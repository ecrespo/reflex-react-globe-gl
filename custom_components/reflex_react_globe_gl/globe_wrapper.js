/**
 * ReflexGlobe — a thin React wrapper around `react-globe.gl` tailored for Reflex.
 *
 * What it adds on top of the upstream component:
 *   - Responsive sizing: fills its container (ResizeObserver) unless explicit
 *     `width` / `height` are provided.
 *   - JSON-safe events: every `on*` callback receives sanitized arguments
 *     (no THREE objects, no circular refs, DOM events reduced to plain info),
 *     so Reflex can ship them to the backend over the websocket.
 *   - Stable callbacks and accessors: re-renders caused by unrelated state
 *     changes do not force globe.gl to rebuild its layers.
 *   - Declarative imperative API: `pointOfView`, `animationPaused`,
 *     orbit `controls` options and `globeMaterialOptions` are plain props.
 *   - `htmlMarkup` + `onHtmlElementClick`: HTML markers from an HTML string.
 *   - A global registry (`window.ReflexGlobe`) so that Python helpers can call
 *     globe methods through `rx.call_script`.
 */
import React, {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react";
import Globe from "react-globe.gl";
import * as THREE from "three";

const IS_BROWSER = typeof window !== "undefined";

// ---------------------------------------------------------------------------
// Registry of mounted globes (keyed by the component id).
// ---------------------------------------------------------------------------
const REGISTRY = IS_BROWSER
  ? (window.__reflexGlobes = window.__reflexGlobes || {})
  : {};

// Methods exposed by react-globe.gl through its ref.
const METHOD_NAMES = [
  "pauseAnimation",
  "resumeAnimation",
  "pointOfView",
  "lights",
  "scene",
  "camera",
  "renderer",
  "postProcessingComposer",
  "controls",
  "getGlobeRadius",
  "getCoords",
  "getScreenCoords",
  "toGeoCoords",
  "toGlobeCoords",
  "globeTileEngineClearCache",
];

// ---------------------------------------------------------------------------
// Sanitization of event payloads.
// ---------------------------------------------------------------------------
const MAX_DEPTH = 8;
const MAX_ARRAY = 2000;

function isThreeLike(v) {
  return !!(
    v &&
    (v.isObject3D || v.isMaterial || v.isTexture || v.isBufferGeometry || v.isColor)
  );
}

function eventInfo(ev) {
  const info = { type: ev.type };
  for (const k of [
    "clientX",
    "clientY",
    "pageX",
    "pageY",
    "offsetX",
    "offsetY",
    "button",
    "altKey",
    "ctrlKey",
    "shiftKey",
    "metaKey",
  ]) {
    if (ev[k] !== undefined) info[k] = ev[k];
  }
  return info;
}

function sanitize(value, exclude = [], depth = 0, seen = new WeakSet()) {
  if (value === null || value === undefined) return null;
  const t = typeof value;
  if (t === "number") return Number.isFinite(value) ? value : null;
  if (t === "string" || t === "boolean") return value;
  if (t === "function" || t === "symbol" || t === "bigint") return undefined;
  if (IS_BROWSER && typeof Event !== "undefined" && value instanceof Event) {
    return eventInfo(value);
  }
  if (isThreeLike(value)) return undefined;
  if (IS_BROWSER && typeof Node !== "undefined" && value instanceof Node) {
    return undefined;
  }
  if (depth > MAX_DEPTH || seen.has(value)) return undefined;
  seen.add(value);
  if (Array.isArray(value)) {
    const out = [];
    const n = Math.min(value.length, MAX_ARRAY);
    for (let i = 0; i < n; i++) {
      const s = sanitize(value[i], exclude, depth + 1, seen);
      out.push(s === undefined ? null : s);
    }
    return out;
  }
  const out = {};
  for (const key of Object.keys(value)) {
    if (key.startsWith("__") || exclude.includes(key)) continue;
    const s = sanitize(value[key], exclude, depth + 1, seen);
    if (s !== undefined) out[key] = s;
  }
  return out;
}

// ---------------------------------------------------------------------------
// Color scales usable from accessor functions (see `color_scale` in Python).
// ---------------------------------------------------------------------------
const PALETTES = {
  YlOrRd: ["#ffffcc", "#ffeda0", "#fed976", "#feb24c", "#fd8d3c", "#fc4e2a", "#e31a1c", "#bd0026", "#800026"],
  YlGnBu: ["#ffffd9", "#edf8b1", "#c7e9b4", "#7fcdbb", "#41b6c4", "#1d91c0", "#225ea8", "#253494", "#081d58"],
  OrRd: ["#fff7ec", "#fee8c8", "#fdd49e", "#fdbb84", "#fc8d59", "#ef6548", "#d7301f", "#b30000", "#7f0000"],
  Blues: ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#08519c", "#08306b"],
  Greens: ["#f7fcf5", "#e5f5e0", "#c7e9c0", "#a1d99b", "#74c476", "#41ab5d", "#238b45", "#006d2c", "#00441b"],
  Reds: ["#fff5f0", "#fee0d2", "#fcbba1", "#fc9272", "#fb6a4a", "#ef3b2c", "#cb181d", "#a50f15", "#67000d"],
  Purples: ["#fcfbfd", "#efedf5", "#dadaeb", "#bcbddc", "#9e9ac8", "#807dba", "#6a51a3", "#54278f", "#3f007d"],
  Viridis: ["#440154", "#482878", "#3e4989", "#31688e", "#26828e", "#1f9e89", "#35b779", "#6ece58", "#b5de2b", "#fde725"],
  Inferno: ["#000004", "#1b0c41", "#4a0c6b", "#781c6d", "#a52c60", "#cf4446", "#ed6925", "#fb9b06", "#f7d13d", "#fcffa4"],
  Magma: ["#000004", "#180f3d", "#440f76", "#721f81", "#9e2f7f", "#cd4071", "#f1605d", "#fd9668", "#feca8d", "#fcfdbf"],
  Plasma: ["#0d0887", "#46039f", "#7201a8", "#9c179e", "#bd3786", "#d8576b", "#ed7953", "#fb9f3a", "#fdca26", "#f0f921"],
  Turbo: ["#30123b", "#4662d7", "#36aaf9", "#1ae4b6", "#72fe5e", "#c8ef34", "#faba39", "#f66b19", "#ca2a04", "#7a0403"],
  Spectral: ["#9e0142", "#d53e4f", "#f46d43", "#fdae61", "#fee08b", "#e6f598", "#abdda4", "#66c2a5", "#3288bd", "#5e4fa2"],
  RdYlGn: ["#a50026", "#d73027", "#f46d43", "#fdae61", "#fee08b", "#d9ef8b", "#a6d96a", "#66bd63", "#1a9850", "#006837"],
  RdBu: ["#67001f", "#b2182b", "#d6604d", "#f4a582", "#fddbc7", "#d1e5f0", "#92c5de", "#4393c3", "#2166ac", "#053061"],
};

function hexToRgb(hex) {
  const h = hex.replace("#", "");
  const full = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
  const n = parseInt(full, 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

const SCALE_CACHE = new Map();

function colorScale(palette = "YlOrRd", domain = [0, 1], type = "linear", opacity = 1) {
  const key = JSON.stringify([palette, domain, type, opacity]);
  if (SCALE_CACHE.has(key)) return SCALE_CACHE.get(key);
  const stops = (Array.isArray(palette) ? palette : PALETTES[palette] || PALETTES.YlOrRd).map(hexToRgb);
  const [d0, d1] = domain;
  const tf =
    type === "sqrt"
      ? (v) => Math.sqrt(Math.max(v, 0))
      : type === "log"
        ? (v) => Math.log10(Math.max(v, 1e-12))
        : type === "pow"
          ? (v) => v * v
          : (v) => v;
  const t0 = tf(d0);
  const t1 = tf(d1);
  const fn = (value) => {
    let t = t1 === t0 ? 0 : (tf(+value) - t0) / (t1 - t0);
    if (!Number.isFinite(t)) t = 0;
    t = Math.min(1, Math.max(0, t));
    const pos = t * (stops.length - 1);
    const i = Math.min(Math.floor(pos), stops.length - 2);
    const f = pos - i;
    const a = stops[i];
    const b = stops[i + 1];
    const c = a.map((x, k) => Math.round(x + (b[k] - x) * f));
    return opacity >= 1 ? `rgb(${c[0]},${c[1]},${c[2]})` : `rgba(${c[0]},${c[1]},${c[2]},${opacity})`;
  };
  SCALE_CACHE.set(key, fn);
  return fn;
}

// ---------------------------------------------------------------------------
// Global helper namespace (usable from `rx.call_script` and JS accessors).
// ---------------------------------------------------------------------------
function getGlobe(id) {
  return REGISTRY[id];
}

function callGlobe(id, method, ...args) {
  const g = REGISTRY[id];
  if (!g) {
    console.warn(`[reflex-react-globe-gl] globe "${id}" is not mounted`);
    return undefined;
  }
  const res = g[method] instanceof Function ? g[method](...args) : undefined;
  return res;
}

function setControls(id, options = {}) {
  const g = REGISTRY[id];
  const controls = g && g.controls && g.controls();
  if (!controls) return;
  Object.entries(options).forEach(([k, v]) => {
    controls[k] = v;
  });
  controls.update && controls.update();
}

const HELPERS = {
  THREE,
  PALETTES,
  colorScale,
  sanitize,
  registry: REGISTRY,
  get: getGlobe,
  call: callGlobe,
  setControls,
};

if (IS_BROWSER) {
  window.ReflexGlobe = Object.assign(window.ReflexGlobe || {}, HELPERS);
}

// ---------------------------------------------------------------------------
// Prop stabilization.
// ---------------------------------------------------------------------------
function jsonKey(v) {
  try {
    return JSON.stringify(v, (k, val) => (k.startsWith("__") || isThreeLike(val) ? undefined : val));
  } catch (e) {
    return undefined;
  }
}

// Functions that reference Reflex state must never be treated as "unchanged"
// because their closure may capture fresh state values.
const STATE_REF = /reflex___state|_rx_state_/;

function sameValue(a, b) {
  if (a === b) return true;
  if (a == null || b == null) return false;
  if (typeof a === "function" && typeof b === "function") {
    const sa = a.toString();
    return sa === b.toString() && !STATE_REF.test(sa);
  }
  if (typeof a === "object" && typeof b === "object") {
    if (isThreeLike(a) || isThreeLike(b)) return false;
    if (Array.isArray(a) !== Array.isArray(b)) return false;
    if (Array.isArray(a) && a.length !== b.length) return false;
    const ka = jsonKey(a);
    return ka !== undefined && ka === jsonKey(b);
  }
  return false;
}

function useStableProps(props) {
  const cache = useRef({});
  const out = {};
  for (const key of Object.keys(props)) {
    const prev = cache.current[key];
    const next = props[key];
    out[key] = prev !== undefined && sameValue(prev, next) ? prev : next;
  }
  cache.current = out;
  return out;
}

// ---------------------------------------------------------------------------
// Sizing.
// ---------------------------------------------------------------------------
function useElementSize(ref) {
  const [size, setSize] = useState({ width: 0, height: 0 });
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof ResizeObserver === "undefined") return undefined;
    const update = () => {
      const r = el.getBoundingClientRect();
      const w = Math.floor(r.width);
      const h = Math.floor(r.height);
      setSize((s) => (s.width === w && s.height === h ? s : { width: w, height: h }));
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, [ref]);
  return size;
}

const COLOR_KEYS = new Set(["color", "emissive", "specular", "sheenColor", "attenuationColor"]);

function findGlobeMaterial(globe) {
  const scene = globe && globe.scene && globe.scene();
  if (!scene) return undefined;
  let material;
  scene.traverse((obj) => {
    if (!material && obj.__globeObjType === "globe") {
      const mesh = obj.children.find((c) => c.isMesh);
      material = mesh && mesh.material;
    }
  });
  return material;
}

// ---------------------------------------------------------------------------
// The component.
// ---------------------------------------------------------------------------
const INTERNAL_EVENTS = new Set(["onHtmlElementClick", "onHtmlElementHover"]);

// Callbacks understood by globe.gl. Any other `on*` prop (onClick, onMouseMove,
// onContextMenu...) is a regular DOM event and goes to the container <div>.
const LAYERS = [
  "Point",
  "Arc",
  "Polygon",
  "Path",
  "Heatmap",
  "Hex",
  "HexPolygon",
  "Tile",
  "Particle",
  "Label",
  "Object",
  "CustomLayer",
];
const GLOBE_EVENTS = new Set([
  "onGlobeReady",
  "onGlobeClick",
  "onGlobeRightClick",
  "onZoom",
  ...LAYERS.flatMap((l) => [`on${l}Click`, `on${l}RightClick`, `on${l}Hover`]),
]);

export const ReactGlobeGl = forwardRef(function ReactGlobeGl(allProps, ref) {
  const {
    id,
    className,
    style,
    width,
    height,
    // Declarative extensions
    pointOfView,
    povTransitionMs = 0,
    animationPaused,
    autoRotate,
    autoRotateSpeed,
    enableZoom,
    enableRotate,
    enablePan,
    controlsOptions,
    globeMaterialOptions,
    htmlMarkup,
    eventDataExclude = ["geometry"],
    zoomThrottleMs = 150,
    children,
    ...rest
  } = allProps;

  const containerRef = useRef(null);
  const globeRef = useRef(null);
  const [ready, setReady] = useState(false);
  const measured = useElementSize(containerRef);
  const w = width || measured.width;
  const h = height || measured.height;

  // ------------------------------------------------------------ handlers
  const handlerProps = {};
  const domHandlers = {};
  const passProps = {};
  for (const [k, v] of Object.entries(rest)) {
    if (v === undefined) continue;
    if (/^on[A-Z]/.test(k) && typeof v === "function") {
      if (GLOBE_EVENTS.has(k) || INTERNAL_EVENTS.has(k)) handlerProps[k] = v;
      else domHandlers[k] = v;
    } else passProps[k] = v;
  }
  const handlersRef = useRef(handlerProps);
  handlersRef.current = handlerProps;
  const excludeRef = useRef(eventDataExclude);
  excludeRef.current = eventDataExclude || [];

  const handlerNames = Object.keys(handlerProps)
    .filter((k) => !INTERNAL_EVENTS.has(k))
    .sort()
    .join(",");

  const zoomState = useRef({ last: 0, timer: null, pending: null });

  const stableHandlers = useMemo(() => {
    const out = {};
    handlerNames
      .split(",")
      .filter(Boolean)
      .forEach((name) => {
        if (name === "onZoom") {
          out[name] = (pov) => {
            const zs = zoomState.current;
            const fire = () => {
              zs.last = Date.now();
              zs.timer = null;
              const fn = handlersRef.current.onZoom;
              fn && fn(sanitize(zs.pending));
            };
            zs.pending = pov;
            const elapsed = Date.now() - zs.last;
            if (elapsed >= zoomThrottleMs) fire();
            else if (!zs.timer) zs.timer = setTimeout(fire, zoomThrottleMs - elapsed);
          };
          return;
        }
        if (name === "onGlobeReady") return; // handled below
        out[name] = (...args) => {
          const fn = handlersRef.current[name];
          if (!fn) return;
          fn(...args.map((a) => sanitize(a, excludeRef.current)));
        };
      });
    return out;
  }, [handlerNames, zoomThrottleMs]);

  useEffect(() => () => clearTimeout(zoomState.current.timer), []);

  const onGlobeReady = useCallback(() => {
    setReady(true);
    const fn = handlersRef.current.onGlobeReady;
    fn && fn();
  }, []);

  // ------------------------------------------------------------ html markup
  const hasHtmlClick = typeof handlerProps.onHtmlElementClick === "function";
  const hasHtmlHover = typeof handlerProps.onHtmlElementHover === "function";
  const markupKey =
    typeof htmlMarkup === "function" ? htmlMarkup.toString() : htmlMarkup === undefined ? "" : String(htmlMarkup);
  const markupRef = useRef(htmlMarkup);
  markupRef.current = htmlMarkup;

  const htmlElementFromMarkup = useMemo(() => {
    if (!markupKey) return undefined;
    return (d) => {
      const m = markupRef.current;
      const html = typeof m === "function" ? m(d) : d[m];
      const el = document.createElement("div");
      el.innerHTML = html == null ? "" : String(html);
      el.style.pointerEvents = hasHtmlClick || hasHtmlHover ? "auto" : "none";
      if (hasHtmlClick) {
        el.style.cursor = "pointer";
        el.addEventListener("click", (ev) => {
          const fn = handlersRef.current.onHtmlElementClick;
          fn && fn(sanitize(d, excludeRef.current), sanitize(ev));
        });
      }
      if (hasHtmlHover) {
        el.addEventListener("mouseenter", () => {
          const fn = handlersRef.current.onHtmlElementHover;
          fn && fn(sanitize(d, excludeRef.current));
        });
        el.addEventListener("mouseleave", () => {
          const fn = handlersRef.current.onHtmlElementHover;
          fn && fn(null);
        });
      }
      return el;
    };
  }, [markupKey, hasHtmlClick, hasHtmlHover]);

  // ------------------------------------------------------------ props
  const stable = useStableProps(passProps);
  const globeProps = { ...stable, ...stableHandlers, onGlobeReady };
  if (htmlElementFromMarkup) globeProps.htmlElement = htmlElementFromMarkup;

  // ------------------------------------------------------------ ref & registry
  const handle = useMemo(() => {
    const h = {};
    METHOD_NAMES.forEach((m) => {
      h[m] = (...args) => (globeRef.current && globeRef.current[m] ? globeRef.current[m](...args) : undefined);
    });
    h.globeMaterial = () => findGlobeMaterial(globeRef.current);
    h.setControls = (opts) => {
      const c = h.controls();
      if (!c) return;
      Object.assign(c, opts || {});
      c.update && c.update();
    };
    return h;
  }, []);

  useImperativeHandle(ref, () => handle, [handle]);

  const registryKey = id || allProps.globeId;
  useEffect(() => {
    if (!registryKey) return undefined;
    REGISTRY[registryKey] = handle;
    return () => {
      if (REGISTRY[registryKey] === handle) delete REGISTRY[registryKey];
    };
  }, [registryKey, handle]);

  const setGlobeRef = useCallback((inst) => {
    globeRef.current = inst;
    if (inst) setReady((r) => r || !!inst);
  }, []);

  // ------------------------------------------------------------ controls
  const controlsKey = jsonKey({
    ...(controlsOptions || {}),
    ...(autoRotate !== undefined ? { autoRotate } : {}),
    ...(autoRotateSpeed !== undefined ? { autoRotateSpeed } : {}),
    ...(enableZoom !== undefined ? { enableZoom } : {}),
    ...(enableRotate !== undefined ? { enableRotate } : {}),
    ...(enablePan !== undefined ? { enablePan } : {}),
  });
  useEffect(() => {
    if (!ready || !globeRef.current) return;
    const opts = JSON.parse(controlsKey || "{}");
    if (Object.keys(opts).length) handle.setControls(opts);
  }, [ready, controlsKey, handle]);

  // ------------------------------------------------------------ point of view
  const povKey = pointOfView ? jsonKey(pointOfView) : "";
  useEffect(() => {
    if (!ready || !globeRef.current || !povKey) return;
    globeRef.current.pointOfView(JSON.parse(povKey), povTransitionMs || 0);
  }, [ready, povKey, povTransitionMs]);

  // ------------------------------------------------------------ animation
  useEffect(() => {
    if (!ready || !globeRef.current || animationPaused === undefined) return;
    if (animationPaused) globeRef.current.pauseAnimation();
    else globeRef.current.resumeAnimation();
  }, [ready, animationPaused]);

  // ------------------------------------------------------------ material
  const materialKey = globeMaterialOptions ? jsonKey(globeMaterialOptions) : "";
  useEffect(() => {
    if (!ready || !materialKey) return;
    const material = findGlobeMaterial(globeRef.current);
    if (!material) return;
    const opts = JSON.parse(materialKey);
    Object.entries(opts).forEach(([k, v]) => {
      if (COLOR_KEYS.has(k)) material[k] = v == null ? null : new THREE.Color(v);
      else material[k] = v;
    });
    material.needsUpdate = true;
  }, [ready, materialKey, allProps.globeImageUrl]);

  const containerStyle = {
    position: "relative",
    width: "100%",
    height: "100%",
    minHeight: height ? undefined : 200,
    overflow: "hidden",
    // Own stacking context: keeps globe.gl's HTML layers / tooltips below
    // sibling overlays (panels, legends) that use a z-index.
    isolation: "isolate",
    ...(style || {}),
  };

  return React.createElement(
    "div",
    { ...domHandlers, id, className, style: containerStyle, ref: containerRef, "data-reflex-globe": "" },
    w > 0 && h > 0
      ? React.createElement(Globe, { ...globeProps, ref: setGlobeRef, width: w, height: h })
      : null,
    children,
  );
});

export default ReactGlobeGl;

import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, animate, motion, useMotionValue, useReducedMotion } from "motion/react";

// Plain SVG route diagram: no tiles, no zoom, no scroll capture. Mounted once per sim (keyed on run_id);
// poll ticks only change props, so nothing redraws except the ambulance glide and the text.
const W = 600;
const H = 340;
const PAD_X = 70;
const PAD_Y = 34;

const RING = { r: [8, 22], opacity: [0.5, 0] };
const RING_T = { duration: 1.6, repeat: Infinity, ease: "easeOut" };
const FLASH = { opacity: [0, 1, 0.2, 1] };
const FLASH_T = { duration: 0.6, times: [0, 0.3, 0.6, 1] };

function pairs(ids) {
  const out = [];
  for (let i = 0; i + 1 < (ids || []).length; i++) out.push([ids[i], ids[i + 1]]);
  return out;
}

function useProjection(nodes) {
  const sig = nodes.map((n) => `${n.id}:${n.lat}:${n.lon}`).join("|");
  return useMemo(() => {
    const lats = nodes.map((n) => n.lat);
    const lons = nodes.map((n) => n.lon);
    const meanLat = lats.reduce((a, b) => a + b, 0) / Math.max(lats.length, 1);
    const k = Math.cos((meanLat * Math.PI) / 180);
    const xs = lons.map((l) => l * k);
    const ys = lats.map((l) => -l);
    const minX = Math.min(...xs);
    const minY = Math.min(...ys);
    const spanX = Math.max(Math.max(...xs) - minX, 1e-6);
    const spanY = Math.max(Math.max(...ys) - minY, 1e-6);
    const s = Math.min((W - 2 * PAD_X) / spanX, (H - 2 * PAD_Y) / spanY);
    const offX = (W - spanX * s) / 2 - minX * s;
    const offY = (H - spanY * s) / 2 - minY * s;
    const project = (lat, lon) => [lon * k * s + offX, -lat * s + offY];
    const byId = {};
    nodes.forEach((n) => {
      byId[n.id] = { ...n, xy: project(n.lat, n.lon) };
    });
    return { project, byId };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sig]);
}

function readColors() {
  const cs = getComputedStyle(document.documentElement);
  const g = (n) => cs.getPropertyValue(n).trim();
  return { accent: g("--accent"), amber: g("--amber") };
}

function RouteSeg({ d, mode, index, count, colors }) {
  // mode is fixed at mount: "draw" (initial route, drawn once), "fromAlt" (accepted alternate turns teal).
  const [m] = useState(mode);
  const per = 0.6 / Math.max(count, 1);
  const initial = m === "fromAlt" ? { pathLength: 1, stroke: colors.amber } : { pathLength: 0, stroke: colors.accent };
  return (
    <motion.path
      d={d}
      className="map-route"
      initial={initial}
      animate={{ pathLength: 1, stroke: colors.accent }}
      transition={{
        pathLength: { duration: m === "draw" ? per : 0.3, delay: m === "draw" ? index * per : 0, ease: "linear" },
        stroke: { duration: 0.6 },
      }}
    />
  );
}

function Ambulance({ x, y }) {
  const reduce = useReducedMotion();
  const mx = useMotionValue(x);
  const my = useMotionValue(y);
  useEffect(() => {
    const a = animate(mx, x, { duration: 1, ease: "linear" });
    const b = animate(my, y, { duration: 1, ease: "linear" });
    return () => {
      a.stop();
      b.stop();
    };
  }, [x, y, mx, my]);
  return (
    <g className="map-amb">
      {!reduce && <motion.circle cx={mx} cy={my} r={8} className="amb-ring" animate={RING} transition={RING_T} />}
      <motion.circle cx={mx} cy={my} r={7} className="amb-dot" />
    </g>
  );
}

function Pin({ xy, title, sub, kind }) {
  const [x, y] = xy;
  const right = x > W - 150;
  const tx = right ? x - 13 : x + 13;
  const anchor = right ? "end" : "start";
  return (
    <g className={`map-pin map-pin-${kind}`}>
      {kind === "dest" ? (
        <rect x={x - 7} y={y - 7} width={14} height={14} className="pin-dest" />
      ) : (
        <circle cx={x} cy={y} r={7} className="pin-pickup" />
      )}
      <text x={tx} y={sub ? y - 3 : y + 5} textAnchor={anchor} className="map-label map-label-strong">
        {title}
      </text>
      {sub && (
        <text x={tx} y={y + 13} textAnchor={anchor} className="map-label map-label-sub">
          {sub}
        </text>
      )}
    </g>
  );
}

export default function TrackingMap({ sim, theme, pollNote }) {
  const graph = sim.graph || { nodes: [], segments: [] };
  const { project, byId } = useProjection(graph.nodes || []);
  const colors = useMemo(readColors, [theme]);
  const segById = useMemo(() => {
    const m = {};
    (graph.segments || []).forEach((s) => (m[s.id] = s));
    return m;
  }, [graph.segments]);

  const lineD = (a, b) => {
    const p = byId[a] && byId[a].xy;
    const q = byId[b] && byId[b].xy;
    return p && q ? `M${p[0].toFixed(1)} ${p[1].toFixed(1)} L${q[0].toFixed(1)} ${q[1].toFixed(1)}` : null;
  };
  const polyD = (ids) =>
    (ids || [])
      .map((id, i) => (byId[id] ? `${i ? "L" : "M"}${byId[id].xy[0].toFixed(1)} ${byId[id].xy[1].toFixed(1)}` : ""))
      .join(" ");

  // Remember the last offered alternate, so its segments change colour (amber -> teal) once accepted.
  const altKeys = useRef(new Set());
  const altSig = (sim.alternate || []).join("-");
  useEffect(() => {
    if (sim.alternate) altKeys.current = new Set(pairs(sim.alternate).map(([a, b]) => `${a}>${b}`));
  }, [altSig]); // eslint-disable-line react-hooks/exhaustive-deps

  const firstRoute = useRef(true);
  useEffect(() => {
    firstRoute.current = false;
  }, []);

  const routePairs = pairs(sim.route);
  const pickup = byId[sim.pickup];
  const dest = byId[graph.destination];
  const pos = sim.position;
  const ambXY = pos ? project(pos.lat, pos.lon) : null;

  return (
    <motion.section className="mapwrap" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}>
      <div className="simbar">{sim.label}</div>
      <div className="map-grid">
        <svg className="map" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Simulated route diagram">
          <g className="map-segments">
            {(graph.segments || []).map((s) => {
              const d = lineD(s.from, s.to);
              return d ? <path key={s.id} d={d} className="map-seg" /> : null;
            })}
          </g>

          <g className="map-current">
            {routePairs.map(([a, b], i) => {
              const d = lineD(a, b);
              if (!d) return null;
              const k = `${a}>${b}`;
              const mode = firstRoute.current ? "draw" : altKeys.current.has(k) ? "fromAlt" : "added";
              return <RouteSeg key={k} d={d} mode={mode} index={i} count={routePairs.length} colors={colors} />;
            })}
          </g>

          <AnimatePresence>
            {sim.alternate && altSig && (
              <motion.g key={`alt-${altSig}`} exit={{ opacity: 0, transition: { duration: 0.3 } }}>
                <defs>
                  <mask id={`altmask-${altSig}`} maskUnits="userSpaceOnUse" x="0" y="0" width={W} height={H}>
                    <motion.path
                      d={polyD(sim.alternate)}
                      stroke="#fff"
                      strokeWidth="16"
                      fill="none"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      initial={{ pathLength: 0 }}
                      animate={{ pathLength: 1 }}
                      transition={{ duration: 0.6, ease: "easeOut" }}
                    />
                  </mask>
                </defs>
                <path d={polyD(sim.alternate)} className="map-alt" mask={`url(#altmask-${altSig})`} />
              </motion.g>
            )}
          </AnimatePresence>

          <g className="map-incidents">
            {(sim.incidents || []).map((inc) => {
              const seg = segById[inc.segment];
              const d = seg && lineD(seg.from, seg.to);
              if (!d) return null;
              const p = byId[seg.from].xy;
              const q = byId[seg.to].xy;
              const mx = (p[0] + q[0]) / 2;
              const my = (p[1] + q[1]) / 2;
              return (
                <g key={`${inc.segment}-${inc.kind}`}>
                  <motion.path d={d} className="map-incident" initial={{ opacity: 0 }} animate={FLASH} transition={FLASH_T} />
                  <text x={mx} y={my - 10} textAnchor="middle" className="map-label map-label-incident">
                    {inc.kind === "closed" ? "Closed" : "Heavy traffic"}
                  </text>
                </g>
              );
            })}
          </g>

          {pickup && <Pin xy={pickup.xy} title="Pickup" sub={pickup.name} kind="pickup" />}
          {dest && <Pin xy={dest.xy} title="PIMS" kind="dest" />}
          {ambXY && <Ambulance x={ambXY[0]} y={ambXY[1]} />}
        </svg>

        <div className="map-side">
          <ul className="legend">
            <li><span className="swatch swatch-route" />Current route</li>
            <li><span className="swatch swatch-alt" />Alternate offered</li>
            <li><span className="swatch swatch-incident" />Simulated incident</li>
            <li><span className="swatch swatch-amb" />Ambulance (simulated)</li>
          </ul>
          {(sim.incidents || []).length > 0 && (
            <ul className="incident-list">
              {sim.incidents.map((inc) => (
                <li key={`${inc.segment}-${inc.kind}`}>
                  {inc.kind === "closed" ? "Closed" : "Heavy traffic"} (simulated): {inc.name}
                </li>
              ))}
            </ul>
          )}
          {pollNote && <p className="note note-error">{pollNote}</p>}
        </div>
      </div>
      <p className="caption">Illustrative road graph, not a real road network.</p>
      <p className="caption">Teal: current route · amber: alternate offered · red: simulated incident.</p>
    </motion.section>
  );
}

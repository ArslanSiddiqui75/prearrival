import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { reveal } from "../motion.js";

const DASH = { strokeDashoffset: [24, 0] };
const DASH_T = { duration: 0.7, repeat: Infinity, ease: "linear" };
const SHIMMER = { x: ["-100%", "220%"] };
const SHIMMER_T = { duration: 1.2, repeat: Infinity, ease: "easeInOut" };

function Connector({ active }) {
  return (
    <svg className="conn" viewBox="0 0 100 12" preserveAspectRatio="none" aria-hidden="true">
      <line x1="0" y1="6" x2="100" y2="6" className="conn-base" vectorEffect="non-scaling-stroke" />
      {active && (
        <motion.line
          x1="0" y1="6" x2="100" y2="6"
          className="conn-flow"
          vectorEffect="non-scaling-stroke"
          strokeDasharray="6 18"
          animate={DASH}
          transition={DASH_T}
        />
      )}
    </svg>
  );
}

function Merge({ active }) {
  const paths = ["M0 25 C 55 25, 45 50, 100 50", "M0 75 C 55 75, 45 50, 100 50"];
  return (
    <svg className="conn conn-merge" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
      {paths.map((d) => (
        <g key={d}>
          <path d={d} className="conn-base" vectorEffect="non-scaling-stroke" />
          {active && (
            <motion.path
              d={d}
              className="conn-flow"
              vectorEffect="non-scaling-stroke"
              strokeDasharray="6 18"
              animate={DASH}
              transition={DASH_T}
            />
          )}
        </g>
      ))}
    </svg>
  );
}

function Step({ name, tag, state, style }) {
  return (
    <div className={`step step-${state}`} style={style}>
      <span className="step-name">{name}</span>
      <span className="step-tag">{state === "inflight" ? "in flight" : tag}</span>
      {state === "inflight" && (
        <motion.span
          className="step-shimmer"
          animate={SHIMMER}
          transition={SHIMMER_T}
        />
      )}
    </div>
  );
}

// Empty and in-flight states. Per-step completion is never faked: the three cloud steps stay "in flight"
// until the whole Board arrives, then the result view replaces this with the real request stamps.
export function Pipeline({ running, startedAt }) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    if (!running || startedAt == null) return undefined;
    setElapsed((performance.now() - startedAt) / 1000);
    const id = setInterval(() => setElapsed((performance.now() - startedAt) / 1000), 100);
    return () => clearInterval(id);
  }, [running, startedAt]);

  const cloud = running ? "inflight" : "idle";
  const local = running ? "waiting" : "idle";
  const r1 = { gridRow: 1 };
  const r2 = { gridRow: 2 };
  const both = { gridRow: "1 / span 2" };

  return (
    <section className="pipeline" aria-label="Pipeline">
      <div className="pipe-grid">
        <div className="pipe-cell" style={{ ...r1, gridColumn: 1 }}><Step name="Voice note" tag="input" state="idle" /></div>
        <div className="pipe-cell" style={{ ...r1, gridColumn: 2 }}><Connector active={running} /></div>
        <div className="pipe-cell" style={{ ...r1, gridColumn: 3 }}><Step name="Whisper" tag="cloud" state={cloud} /></div>
        <div className="pipe-cell" style={{ ...r2, gridColumn: 1 }}><Step name="Monitor photo" tag="input" state="idle" /></div>
        <div className="pipe-cell" style={{ ...r2, gridColumn: 2 }}><Connector active={running} /></div>
        <div className="pipe-cell" style={{ ...r2, gridColumn: 3 }}><Step name="Vision" tag="cloud" state={cloud} /></div>
        <div className="pipe-cell pipe-merge" style={{ ...both, gridColumn: 4 }}><Merge active={running} /></div>
        <div className="pipe-cell" style={{ ...both, gridColumn: 5 }}><Step name="Extract" tag="cloud" state={cloud} /></div>
        <div className="pipe-cell" style={{ ...both, gridColumn: 6 }}><Connector active={false} /></div>
        <div className="pipe-cell" style={{ ...both, gridColumn: 7 }}><Step name="NEWS2 rules" tag="rules" state={local} /></div>
        <div className="pipe-cell" style={{ ...both, gridColumn: 8 }}><Connector active={false} /></div>
        <div className="pipe-cell" style={{ ...both, gridColumn: 9 }}><Step name="Decide" tag="rules" state={local} /></div>
        <div className="pipe-cell" style={{ ...both, gridColumn: 10 }}><Connector active={false} /></div>
        <div className="pipe-cell" style={{ ...both, gridColumn: 11 }}><Step name="Board" tag="screen" state={local} /></div>
      </div>
      {running ? (
        <div className="pipe-foot">
          <p>
            Calling the cloud <span className="mono pipe-elapsed">{elapsed.toFixed(1)} s</span>
          </p>
          {elapsed >= 15 && <p className="pipe-wait">The free-tier rate limit may be pausing this. It retries on its own.</p>}
        </div>
      ) : (
        <p className="pipe-foot pipe-hint">Pick a fixture and press Send live.</p>
      )}
    </section>
  );
}

function Check({ delay }) {
  return (
    <motion.svg
      className="check"
      viewBox="0 0 16 16"
      aria-hidden="true"
      initial={{ scale: 0.4, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", stiffness: 600, damping: 22, delay }}
    >
      <motion.path
        d="M3 8.5 L6.5 12 L13 4.5"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.25, delay: delay + 0.05 }}
      />
    </motion.svg>
  );
}

const STEP_NAME = { "speech-to-text": "Whisper", "monitor photo": "Vision", "note extraction": "Extract" };

// Collapsed pipeline after a live Board arrives: the real request timestamps, each with a check.
export function StampStrip({ stamps, source }) {
  return (
    <motion.div className="strip" variants={reveal.fade(0.2)}>
      <span className="strip-label">Cloud requests sent at</span>
      <span className="strip-src">voice: {source === "mic" ? "live mic" : "saved file"}</span>
      {Object.entries(stamps).map(([name, ts], i) => (
        <span key={name} className="stamp" title={STEP_NAME[name] || name}>
          <Check delay={0.25 + i * 0.08} />
          <span className="mono">
            {name}: {ts}
          </span>
        </span>
      ))}
    </motion.div>
  );
}

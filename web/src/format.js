// Display formatting only. No clinical logic lives in the frontend.

// Python's round(): half to even.
function pyRound(x) {
  const f = Math.floor(x);
  const d = x - f;
  if (d > 0.5) return f + 1;
  if (d < 0.5) return f;
  return f % 2 === 0 ? f : f + 1;
}

// Same as app.py fmt_mmss: minutes -> "m:ss", rounded to whole seconds, never negative.
export function fmtMmss(minutes) {
  const secs = Math.max(0, pyRound(minutes * 60));
  return `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, "0")}`;
}

// Python f"{x:g}" for the values we show (11.0 -> "11", 11.5 -> "11.5").
export function fmtNum(x) {
  return String(Number(Number(x).toPrecision(6)));
}

export function fmtValue(v) {
  if (v === null || v === undefined) return "—";
  if (typeof v === "boolean") return v ? "true" : "false";
  return String(v);
}

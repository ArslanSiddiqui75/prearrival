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

// Raw tokens from the API -> words. Anything unknown is shown as sent.
const WORDS = {
  head_injury: "Head injury",
  chest_pain: "Chest pain",
  limb_injury: "Limb injury",
  shortness_of_breath: "Shortness of breath",
  stroke: "Stroke",
  other: "Other",
  alert: "Alert",
  not_alert: "Not alert",
};

export function humanize(v) {
  if (v === null || v === undefined || v === "") return "Not given";
  if (typeof v === "boolean") return v ? "Yes" : "No";
  if (typeof v === "string") return WORDS[v] || v;
  if (typeof v === "number") return fmtNum(v);
  return String(v);
}

// Kept for callers that only want the bare value.
export function fmtValue(v) {
  return humanize(v);
}

const UNITS = {
  hr: "bpm",
  sbp: "mmHg",
  dbp: "mmHg",
  spo2: "%",
  rr: "/min",
  temp_c: "°C",
  eta_min: "min",
};

// Value with its unit, by field key: 105 -> "105 bpm", null -> "Not given".
export function fmtField(key, v) {
  if (v === null || v === undefined || v === "") return "Not given";
  if (typeof v === "number" && UNITS[key]) return `${fmtNum(v)}${UNITS[key] === "%" ? "" : " "}${UNITS[key]}`;
  return humanize(v);
}

// Field keys inside a free-text reason ("red parameter: hr, spo2") -> words.
const FIELD_WORDS = [
  ["hr", "heart rate"],
  ["sbp", "systolic BP"],
  ["dbp", "diastolic BP"],
  ["rr", "resp rate"],
  ["spo2", "SpO2"],
  ["temp_c", "temperature"],
  ["on_oxygen", "on oxygen"],
];

export function humanizeReason(text) {
  let out = String(text);
  for (const [key, word] of FIELD_WORDS) {
    out = out.replace(new RegExp(`(^|[^A-Za-z0-9_])${key}(?![A-Za-z0-9_])`, "g"), `$1${word}`);
  }
  return out;
}

// Reasons as the API sends them (a list, some items joined with ";") -> one readable line each.
export function reasonLines(reasons) {
  return (reasons || [])
    .flatMap((r) => String(r).split(";"))
    .map((r) => humanizeReason(r.trim()))
    .filter(Boolean);
}

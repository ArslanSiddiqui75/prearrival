// Fetch helpers. Any non-2xx response throws Error(detail) so the board can show the server's own message
// (a failed live call is HTTP 502 {"detail": "Live call failed: ..."}). There is no fallback data.

async function request(path, { method = "GET", json, form } = {}) {
  const opts = { method, headers: {} };
  if (json !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(json);
  }
  if (form) opts.body = form;
  const res = await fetch(path, opts);
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = null;
  }
  if (!res.ok) {
    let detail = data && data.detail;
    if (Array.isArray(detail)) detail = detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
    if (detail && typeof detail !== "string") detail = JSON.stringify(detail);
    throw new Error(detail || `HTTP ${res.status} ${res.statusText}`.trim());
  }
  return data;
}

export const getFixtures = () => request("/api/fixtures");

export function runLive({ fixture, source, audioBlob }) {
  const form = new FormData();
  form.append("fixture", fixture);
  form.append("source", source);
  if (audioBlob) form.append("audio", audioBlob, "mic.webm");
  return request("/api/run", { method: "POST", form });
}

export const runFake = (fixture) => request("/api/fake", { method: "POST", json: { fixture } });

export const simStart = (run_id, fixture) => request("/api/sim/start", { method: "POST", json: { run_id, fixture } });
export const simGet = () => request("/api/sim");
export const simInject = (kind) => request("/api/sim/inject", { method: "POST", json: { kind } });
export const simAnswer = (accept) => request("/api/sim/answer", { method: "POST", json: { accept } });
export const simStop = () => request("/api/sim/stop", { method: "POST" });

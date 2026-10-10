import { memo } from "react";
import { fmtValue } from "../format.js";

function EvidenceTable({ rows, transcript }) {
  return (
    <section className="panel">
      <h2 className="section-label">Extracted fields and evidence</h2>
      <table className="evidence">
        <thead>
          <tr>
            <th>Field</th>
            <th>Value</th>
            <th>Evidence</th>
            <th>Check</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.key}>
              <td className="ev-field">{r.label}</td>
              <td className="mono ev-value">{fmtValue(r.value)}</td>
              <td className="ev-quote">{r.evidence ? `“${r.evidence}”` : ""}</td>
              <td className="ev-check">
                {(r.flags || []).map((f) => (
                  <span key={f} className="chip">
                    {f}
                  </span>
                ))}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <details className="transcript">
        <summary>Transcript</summary>
        <p className="mono">{transcript}</p>
      </details>
    </section>
  );
}

export default memo(EvidenceTable);

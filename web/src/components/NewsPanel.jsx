import { memo, useEffect, useState } from "react";
import { animate, motion, useReducedMotion } from "motion/react";
import { fmtField } from "../format.js";

const START = 0.45; // after the hero has landed

function CountUp({ value }) {
  const reduce = useReducedMotion();
  const [n, setN] = useState(reduce ? value : 0);
  useEffect(() => {
    if (reduce) {
      setN(value);
      return undefined;
    }
    const c = animate(0, value, { duration: 0.5, delay: START, ease: "easeOut", onUpdate: (v) => setN(Math.round(v)) });
    return () => c.stop();
  }, [value, reduce]);
  return <span className="tabnum">{n}</span>;
}

// 3 blocks; exactly `points` of them are filled (0 = none, 3 = all), coloured by points.
function TermBar({ points, index }) {
  const p = Math.min(Math.max(points, 0), 3);
  return (
    <span className={`bar bar-p${p}`} aria-label={`${p} of 3`}>
      {[0, 1, 2].map((c) => (
        <motion.span
          key={c}
          className={c < p ? "cell cell-on" : "cell"}
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 0.18, delay: START + index * 0.05 + c * 0.04, ease: "easeOut" }}
        />
      ))}
    </span>
  );
}

function NewsPanel({ terms, points, missing, confirm }) {
  const sum = terms.map((t) => t.points).join(" + ");
  return (
    <section className="panel">
      <h2 className="section-label">Partial NEWS2 (Scale 1)</h2>
      <ul className="terms">
        {terms.map((t, i) => (
          <li key={t.key}>
            <span className="term-text">
              {t.label} <span className="mono">{fmtField(t.key, t.value)}</span> → <span className="mono">{t.points}</span>
            </span>
            <TermBar points={t.points} index={i} />
          </li>
        ))}
      </ul>
      <p className="total">
        Total = {sum ? `${sum} = ` : ""}
        <CountUp value={points} />
      </p>
      {missing.length > 0 && (
        <p className="missing">Not scored (missing, not assumed normal): {missing.map((m) => m.label).join(", ")}</p>
      )}
      {confirm.length > 0 ? (
        <p className="confirm">Confirm with crew: {confirm.join(", ")}</p>
      ) : (
        <p className="confirm-none">Nothing to confirm</p>
      )}
    </section>
  );
}

export default memo(NewsPanel);

import { motion } from "motion/react";

const BREATHE = { opacity: [1, 0.25, 1] };
const BREATHE_T = { duration: 2, repeat: Infinity, ease: "easeInOut" };

export default function TopBar({ result, theme, onToggleTheme }) {
  return (
    <header className="topbar">
      <div className="brand">
        <span className="wordmark">PreArrival</span>
        <span className="topbar-status">Incoming patient</span>
      </div>
      <div className="topbar-right">
        {result &&
          (result.live ? (
            <span className="badge badge-live">
              <motion.span className="badge-dot" animate={BREATHE} transition={BREATHE_T} />
              LIVE
            </span>
          ) : (
            <span className="badge badge-notlive">NOT LIVE</span>
          ))}
        <button type="button" className="textbtn" onClick={onToggleTheme}>
          {theme === "dark" ? "Light" : "Dark"}
        </button>
      </div>
    </header>
  );
}

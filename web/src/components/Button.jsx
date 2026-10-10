import { motion } from "motion/react";
import { press } from "../motion.js";

export default function Button({ variant = "secondary", disabled, className = "", children, ...rest }) {
  return (
    <motion.button
      type="button"
      className={`btn btn-${variant} ${className}`}
      disabled={disabled}
      {...(disabled ? {} : press)}
      {...rest}
    >
      {children}
    </motion.button>
  );
}

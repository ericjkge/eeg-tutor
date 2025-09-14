import { motion } from "framer-motion";
import { cn } from "../utils/cn";

export function AuroraText({
  children,
  className,
  colors = ["#FF0080", "#7928CA", "#0070F3", "#38bdf8"],
  speed = 1,
  ...props
}) {
  return (
    <motion.span
      className={cn("inline-block", className)}
      animate={{
        backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"],
      }}
      transition={{
        duration: 4 / speed,
        repeat: Infinity,
        ease: "linear",
      }}
      style={{
        background: `linear-gradient(90deg, ${colors.join(", ")}, ${colors[0]})`,
        backgroundSize: "200% auto",
        backgroundClip: "text",
        WebkitBackgroundClip: "text",
        color: "transparent",
        fontWeight: "inherit",
      }}
      {...props}
    >
      {children}
    </motion.span>
  );
}

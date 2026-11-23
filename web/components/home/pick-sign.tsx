import { cn } from "@/lib/utils"

/**
 * TSI's pick (roadmap 13.10): a small picket sign with the TSI swan (our own drawing), stuck
 * in beside the logo of the team TSI expects to win. The board is black and white in the
 * theme's own contrast, like the header's TSI badge: a light board with a dark swan in dark
 * mode, the reverse in light mode (never pure white, #171); the stick is wood brown. It
 * leans outward, away from the card's middle: `lean="left"` for the away team on the left,
 * `"right"` for the home team. Decorative: the card says the pick in words for screen
 * readers.
 */
export function PickSign({ lean, className }: { lean: "left" | "right"; className?: string }) {
  return (
    <svg
      viewBox="0 0 20 26"
      aria-hidden
      className={cn(
        "pointer-events-none h-7 w-5.5 origin-bottom",
        lean === "left" ? "-rotate-14" : "rotate-14",
        className,
      )}
    >
      {/* The stick, the board, then the swan cut out of it in the panel color, facing
          the middle of the card (mirrored on the right-hand sign). */}
      <rect
        x="9"
        y="13"
        width="2"
        height="13"
        rx="1"
        className="fill-[#7a4e26] dark:fill-[#a0703f]"
      />
      <rect x="0" y="0" width="20" height="15" rx="2" className="fill-primary" />
      <g
        className="fill-card"
        transform={
          lean === "left"
            ? "translate(4.2 1.9) scale(0.24)"
            : "translate(15.8 1.9) scale(-0.24 0.24)"
        }
      >
        <path d="M3 26.5c4.5 1.6 9 .8 12.5-1.6 5.2-3.6 11.6-3.4 16.8.4 2.4 1.7 5.1 2.4 8.2 1.9-.4 8.6-8 15-18.8 15C11.3 42.2 4.6 35.9 3 26.5Z" />
        <path
          d="M37.5 29c4-4.6 2.8-9.4-1.3-13.4-3-3-3.1-7.3 0-9.4 2.3-1.6 5.3-.9 6.4 1.4"
          fill="none"
          className="stroke-card"
          strokeWidth="4.4"
          strokeLinecap="round"
        />
        <circle cx="40.4" cy="8" r="2.7" />
        <path d="M41.6 6.3 47.6 9.4 41.9 10.4Z" />
      </g>
    </svg>
  )
}

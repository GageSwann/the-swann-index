import { readFile } from "node:fs/promises"
import { join } from "node:path"

import { ImageResponse } from "next/og"

// The site's icons (#173, #175): the header's TSI badge exactly. In the header it is
// 34 x 24 px, 2 px corners, "TSI" at 20 px in condensed bold, in the theme's primary colors:
// a light badge with dark text in the dark theme, a dark one with white text in the light.
const RATIO = 24 / 34 // badge height / width
const RADIUS = 2 / 34 // corner radius / width
const FONT = 20 / 34 // type size / width
export const BADGE = {
  dark: { bg: "#e8e8e8", fg: "#1e1e1e" }, // the dark theme's --primary / --primary-foreground
  light: { bg: "#1f1f1f", fg: "#ffffff" },
} as const
export type BadgeTheme = keyof typeof BADGE

const condensed = readFile(join(process.cwd(), "assets/fonts/InstrumentSansCondensed-Bold.ttf"))

/**
 * A square PNG with the badge `width` px wide, centered, on `backdrop` (transparent for
 * browser tabs; a solid panel for the iPhone Home Screen, which can't be transparent).
 */
export async function tsiBadge(
  size: number,
  width: number,
  theme: BadgeTheme,
  backdrop = "transparent",
): Promise<ImageResponse> {
  const { bg, fg } = BADGE[theme]
  return new ImageResponse(
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: backdrop,
      }}
    >
      <div
        style={{
          width,
          height: Math.round(width * RATIO),
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: bg,
          borderRadius: width * RADIUS,
          color: fg,
          fontFamily: "Instrument Sans Condensed",
          fontSize: width * FONT,
          lineHeight: 1,
        }}
      >
        TSI
      </div>
    </div>,
    {
      width: size,
      height: size,
      fonts: [
        { name: "Instrument Sans Condensed", data: await condensed, weight: 700, style: "normal" },
      ],
    },
  )
}

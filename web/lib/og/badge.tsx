import { readFile } from "node:fs/promises"
import { join } from "node:path"

import { ImageResponse } from "next/og"

// The site's icons (#173): the header's TSI badge, white condensed bold on near-black (the
// dark theme's page color), so it reads on light and dark browser tabs alike.
const BG = "#1e1e1e"
const FG = "#f5f5f5"

const condensed = readFile(join(process.cwd(), "assets/fonts/InstrumentSansCondensed-Bold.ttf"))

/** A square PNG of the badge; `radius` rounds it (0 for iOS, which rounds icons itself). */
export async function tsiBadge(size: number, radius: number): Promise<ImageResponse> {
  return new ImageResponse(
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: BG,
        borderRadius: radius,
        color: FG,
        fontFamily: "Instrument Sans Condensed",
        fontSize: size * 0.5,
        letterSpacing: -size * 0.01,
        lineHeight: 1,
      }}
    >
      TSI
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

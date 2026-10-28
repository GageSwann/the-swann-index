import "server-only"

import { readFile } from "node:fs/promises"
import { join } from "node:path"

import { ImageResponse } from "next/og"
import type { ReactNode } from "react"

// Link-preview images (Open Graph): one branded frame for every page (decision #86).
// Colors mirror the "stadium at night" tokens in app/globals.css (dark theme).
export const OG = {
  night: "#0E1923",
  sideline: "#162532",
  hashmark: "#2A3C4B",
  chalk: "#E6EDF2",
  muted: "#93A6B5",
  amber: "#F2B33D",
  up: "#3CC2A9",
  down: "#F07A6A",
}

export const OG_SIZE = { width: 1200, height: 630 }

// Satori (behind ImageResponse) needs TTF/OTF, not the site's woff2: static Archivo
// instances live in web/assets/fonts (SIL OFL 1.1, see OFL.txt there).
const fonts = Promise.all([
  readFile(join(process.cwd(), "assets/fonts/Archivo-Medium.ttf")),
  readFile(join(process.cwd(), "assets/fonts/Archivo-CondensedExtraBold.ttf")),
]).then(([medium, condensed]) => [
  { name: "Archivo", data: medium, weight: 500 as const, style: "normal" as const },
  { name: "Archivo Condensed", data: condensed, weight: 800 as const, style: "normal" as const },
])

/** A 1200×630 PNG: the TSI score-bug header, the content, and the amber rule. */
export async function ogImage(content: ReactNode, footer?: string): Promise<ImageResponse> {
  return new ImageResponse(
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        background: OG.night,
        color: OG.chalk,
        fontFamily: "Archivo",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 18, padding: "36px 56px 0" }}>
        <div
          style={{
            display: "flex",
            background: OG.amber,
            color: OG.night,
            fontFamily: "Archivo Condensed",
            fontSize: 40,
            padding: "2px 14px",
            borderRadius: 6,
          }}
        >
          TSI
        </div>
        <div style={{ display: "flex", fontSize: 34 }}>The Swann Index</div>
      </div>
      <div style={{ display: "flex", flex: 1, padding: "28px 56px" }}>{content}</div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          borderTop: `4px solid ${OG.amber}`,
          padding: "18px 56px",
          fontSize: 24,
          color: OG.muted,
        }}
      >
        <div style={{ display: "flex" }}>
          {footer ?? "College football ratings and predictions"}
        </div>
        <div style={{ display: "flex" }}>the-swann-index.vercel.app</div>
      </div>
    </div>,
    { ...OG_SIZE, fonts: await fonts },
  )
}

/** A team logo on a white chip (dark logos stay visible on the night background). */
export function OgLogo({ src, size }: { src: string | null | undefined; size: number }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        width: size,
        height: size,
        background: "white",
        borderRadius: size / 8,
      }}
    >
      {src && (
        // eslint-disable-next-line @next/next/no-img-element -- Satori renders plain <img>
        <img src={src} alt="" width={size * 0.8} height={size * 0.8} />
      )}
    </div>
  )
}

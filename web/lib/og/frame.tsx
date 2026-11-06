import "server-only"

import { readFile } from "node:fs/promises"
import { join } from "node:path"

import { ImageResponse } from "next/og"
import type { CSSProperties, ReactNode } from "react"

// Link-preview images (Open Graph): one branded frame for every page (decision #86).
// Colors mirror the "black swan" tokens in app/globals.css (dark theme, decision #137).
export const OG = {
  black: "#000000",
  panel: "#0E0E0F",
  line: "#2B2B2E",
  white: "#F5F5F3",
  muted: "#9A9A9F",
  up: "#3CC2A9",
  down: "#F07A6A",
}

export const OG_SIZE = { width: 1200, height: 630 }

// Satori (behind ImageResponse) needs TTF/OTF, not the site's woff2: static Instrument Sans
// instances live in web/assets/fonts (SIL OFL 1.1, see OFL.txt there).
const fonts = Promise.all([
  readFile(join(process.cwd(), "assets/fonts/InstrumentSans-Medium.ttf")),
  readFile(join(process.cwd(), "assets/fonts/InstrumentSansCondensed-Bold.ttf")),
]).then(([medium, condensed]) => [
  { name: "Instrument Sans", data: medium, weight: 500 as const, style: "normal" as const },
  {
    name: "Instrument Sans Condensed",
    data: condensed,
    weight: 700 as const,
    style: "normal" as const,
  },
])

/** A 1200×630 PNG: the TSI score-bug header, the content, and the white rule. */
export async function ogImage(content: ReactNode, footer?: string): Promise<ImageResponse> {
  return new ImageResponse(
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        background: OG.black,
        color: OG.white,
        fontFamily: "Instrument Sans",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 18, padding: "36px 56px 0" }}>
        <div
          style={{
            display: "flex",
            background: OG.white,
            color: OG.black,
            fontFamily: "Instrument Sans Condensed",
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
          borderTop: `4px solid ${OG.white}`,
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

/** A one-line image for missing or unpicked content ("Team not found"). */
export function ogMessage(text: string): Promise<ImageResponse> {
  return ogImage(<Display size={84}>{text}</Display>)
}

/** Display text in the condensed face. (Satori needs `display: flex` on every div.) */
export function Display({
  size,
  style,
  children,
}: {
  size: number
  style?: CSSProperties
  children: ReactNode
}) {
  return (
    <div
      style={{ display: "flex", fontFamily: "Instrument Sans Condensed", fontSize: size, ...style }}
    >
      {children}
    </div>
  )
}

/** A team logo on a white chip (dark logos stay visible on the black background). */
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

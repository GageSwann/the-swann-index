import { type BadgeTheme, tsiBadge } from "@/lib/og/badge"

// Browser tab icons (#173, #175): the header badge, one per theme (/icon/light,
// /icon/dark). Dark is listed last, so it's the one browsers use before the page runs
// (dark is the default theme); `ThemeColor` switches to the light one in the light theme.
export const contentType = "image/png"
const SIZE = { width: 64, height: 64 }

export function generateImageMetadata() {
  return (["light", "dark"] as const).map((id) => ({ id, size: SIZE, contentType }))
}

export default async function Icon({ id }: { id: Promise<string | number> }) {
  const theme = ((await id) === "light" ? "light" : "dark") as BadgeTheme
  return tsiBadge(64, 64, theme)
}

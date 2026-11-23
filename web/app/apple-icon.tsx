import { tsiBadge } from "@/lib/og/badge"

// The iPhone Home Screen icon (#173, #175): the dark theme's header badge on the dark
// header's panel color (iOS icons can't be transparent; it rounds the corners itself).
export const size = { width: 180, height: 180 }
export const contentType = "image/png"

export default function AppleIcon() {
  return tsiBadge(180, 132, "dark", "#252526")
}

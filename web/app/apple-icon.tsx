import { tsiBadge } from "@/lib/og/badge"

// The iPhone Home Screen icon (#173): square, since iOS rounds the corners itself.
export const size = { width: 180, height: 180 }
export const contentType = "image/png"

export default function AppleIcon() {
  return tsiBadge(180, 0)
}

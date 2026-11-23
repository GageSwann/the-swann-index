import { tsiBadge } from "@/lib/og/badge"

// The browser tab icon (#173; replaces Next's default favicon.ico). Built once at build time.
export const size = { width: 64, height: 64 }
export const contentType = "image/png"

export default function Icon() {
  return tsiBadge(64, 12)
}

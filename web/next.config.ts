import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  cacheComponents: true,
  // The free Render API sleeps when idle and takes up to ~1 minute to wake; give build-time
  // prerendering room for that instead of the 60 s default (decision #80).
  staticPageGenerationTimeout: 180,
  partialPrefetching: true,
  cacheLife: {
    // TSI data changes once a day (the 10:00 UTC nightly run). Pages re-check hourly, and
    // the nightly job calls /api/revalidate so updates land right away.
    tsi: {
      stale: 300, // client may reuse for 5 minutes without asking
      revalidate: 3600, // background refresh at most hourly
      expire: 172800, // never serve data older than 2 days
    },
  },
  poweredByHeader: false,
  // Baseline browser protections on every page (Phase 6 security pass, decision #81).
  // A full Content-Security-Policy needs per-request nonces for Next's inline scripts.
  headers() {
    return Promise.resolve([
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ])
  },
  images: {
    // Team logos come from CFBD's CDN (TeamRef.logo_url).
    remotePatterns: [
      { protocol: "https", hostname: "cdn.collegefootballdata.com", pathname: "/logos/**" },
    ],
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
}

export default nextConfig

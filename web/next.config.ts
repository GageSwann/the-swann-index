import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  cacheLife: {
    // TSI data changes once a day (the 10:00 UTC nightly run). Pages re-check hourly;
    // Phase 6 adds on-demand `revalidateTag` after each run so updates land right away.
    tsi: {
      stale: 300, // client may reuse for 5 minutes without asking
      revalidate: 3600, // background refresh at most hourly
      expire: 172800, // never serve data older than 2 days
    },
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

import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  cacheComponents: true,
  // The free Render API sleeps when idle and takes up to ~1 minute to wake; give build-time
  // prerendering room for that instead of the 60 s default (decision #80).
  staticPageGenerationTimeout: 180,
  experimental: {
    // Render's free tier answers a burst of prerender requests with 429/503 (its proxy, not
    // our API), which failed CI builds: fewer pages at once per worker, and a failed page is
    // retried before the build gives up (decision #131).
    staticGenerationMaxConcurrency: 4,
    staticGenerationRetryCount: 2,
  },
  // Link-preview images read these fonts from disk at runtime; make sure every server
  // function bundles them (decision #86).
  outputFileTracingIncludes: { "/**": ["./assets/fonts/*.ttf"] },
  partialPrefetching: true,
  cacheLife: {
    // TSI data changes once a day (the 11:00 UTC nightly run), and the nightly job calls
    // /api/revalidate so updates land right away. Re-checking hourly re-read identical data
    // up to 24 times a day per page from the API, and so from Neon (#144); the daily
    // re-check is only a safety net for a night whose refresh failed.
    tsi: {
      stale: 300, // client may reuse for 5 minutes without asking
      revalidate: 86400, // background refresh at most daily
      expire: 172800, // never serve data older than 2 days
    },
  },
  poweredByHeader: false,
  // College football moved under /cfb (#183), with the board renamed Schedule and the
  // playoffs plural: every old address keeps working, permanently redirected.
  redirects() {
    return Promise.resolve([
      { source: "/rankings", destination: "/cfb/rankings", permanent: true },
      { source: "/rankings/:path*", destination: "/cfb/rankings/:path*", permanent: true },
      { source: "/week", destination: "/cfb/schedule", permanent: true },
      { source: "/week/:path*", destination: "/cfb/schedule/:path*", permanent: true },
      { source: "/playoff", destination: "/cfb/playoffs", permanent: true },
      { source: "/playoff/:path*", destination: "/cfb/playoffs/:path*", permanent: true },
      { source: "/teams/:path*", destination: "/cfb/teams/:path*", permanent: true },
      { source: "/games/:path*", destination: "/cfb/games/:path*", permanent: true },
    ])
  },
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
    // Each logo × width is one Vercel image transformation, and the default 4-hour TTL
    // re-transforms every logo several times a day (75% of Hobby's 5,000 a month used by
    // 2026-11-09). Logos almost never change: keep the optimized copies for 31 days.
    minimumCacheTTL: 2678400,
    // Logos render at 17–56 px. Next picks the smallest allowed width ≥ 1x and ≥ 2x the
    // rendered size, and the default list (32…384) turned each team into ~5 widths, so ~5
    // transformations (4.7K of 5K by 2026-11-20). With only 64 and 128 every logo needs one
    // or both. Not `unoptimized`: the source PNGs are 500 px and 18–60 KB each.
    imageSizes: [64, 128],
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

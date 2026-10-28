// The site's public URL and indexing switch (server-only values from the environment).
// Vercel sets VERCEL_PROJECT_PRODUCTION_URL ("the-swann-index.vercel.app") on every build.

const vercel = process.env.VERCEL_PROJECT_PRODUCTION_URL

/** Absolute base for metadata URLs (Open Graph images, canonical links, the sitemap). */
export const SITE_URL =
  process.env.SITE_URL ?? (vercel ? `https://${vercel}` : "http://localhost:3000")

/**
 * Search engines stay out until the owner opts in (decision #86): set ALLOW_INDEXING=1 in
 * Vercel and redeploy. Link previews in messages work either way.
 */
export const ALLOW_INDEXING = process.env.ALLOW_INDEXING === "1"

export const SITE_NAME = "The Swann Index"

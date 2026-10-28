import type { Metadata } from "next"

import { SITE_NAME } from "./site"

/**
 * A page's title and description for search results and link previews. Next replaces
 * (not merges) a parent's `openGraph` object, so every page sets the full set here.
 * Images: the route's own `opengraph-image` file, else `image`, else the site card.
 */
export function pageMeta({
  title,
  description,
  image,
  ownImage = false,
}: {
  title: string
  description: string
  image?: string // an image route (e.g. /api/og/matchup?...)
  ownImage?: boolean // the route has an `opengraph-image` file: set no image here
}): Metadata {
  // Setting `images` (even to undefined) overrides a route's `opengraph-image` file, and a
  // page's own `openGraph` drops the image inherited from the root. So: routes with their
  // own file set nothing; every other page names the site card (or its image route).
  const media = ownImage
    ? {}
    : { images: [{ url: image ?? "/opengraph-image", width: 1200, height: 630 }] }
  return {
    title,
    description,
    openGraph: {
      title,
      description,
      siteName: SITE_NAME,
      type: "website",
      locale: "en_US",
      ...media,
    },
    twitter: { card: "summary_large_image", title, description, ...media },
  }
}

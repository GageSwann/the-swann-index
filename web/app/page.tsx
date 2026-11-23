import { redirect } from "next/navigation"

/**
 * The site's own home, for every sport (#182). Until it has a page of its own, it opens
 * college football's home, so links and bookmarks to the site keep working.
 */
export default function HomePage() {
  redirect("/cfb")
}

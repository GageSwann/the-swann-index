import { cacheLife } from "next/cache"

/** This year, cached like the site's data (a page may not read the clock while prerendering). */
async function currentYear(): Promise<number> {
  "use cache"
  cacheLife("tsi")
  return new Date().getFullYear()
}

const NOTICES = [
  "Not affiliated with the NCAA or any conference or school.",
  "Team names and logos belong to their respective owners.",
  "For information and entertainment only. Not betting advice.",
]

/**
 * Every page (#161, #162; centered, owner, 2026-11-24, #193): the header's mark, the notices as
 * short sentences (one row with thin dividers from `md`, stacked on phones), then the copyright.
 * On the panel color, so it reads as the page's frame like the header, not as page text.
 */
export async function SiteFooter() {
  const year = await currentYear()
  return (
    <footer className="border-t border-border bg-card text-muted-foreground">
      <div className="tsi-safe-x mx-auto flex max-w-7xl flex-col items-center gap-3 py-6 text-center">
        <p className="flex items-center gap-2 text-foreground">
          <span className="rounded-sm bg-primary px-1 py-0.5 text-sm leading-none font-bold text-primary-foreground font-stretch-condensed">
            TSI
          </span>
          <span className="text-sm leading-none font-semibold font-stretch-semi-condensed">
            The Swann Index
          </span>
        </p>
        {/* Desktop: one row with a thin divider between the sentences (owner). */}
        <ul className="flex flex-col gap-1 text-xs md:flex-row md:flex-wrap md:justify-center md:gap-y-1">
          {NOTICES.map((notice) => (
            <li key={notice} className="md:border-l md:border-border md:px-4 md:first:border-l-0">
              {notice}
            </li>
          ))}
        </ul>
        <p className="text-xs">© {year} The Swann Index. All rights reserved.</p>
      </div>
    </footer>
  )
}

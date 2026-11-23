import { cacheLife } from "next/cache"
import Link from "next/link"

/** The site's sections, as the footer lists them. */
const SECTIONS: { title: string; links: { href: string; label: string }[] }[] = [
  {
    title: "Rankings",
    links: [
      { href: "/rankings", label: "FBS" },
      { href: "/rankings/fcs", label: "FCS" },
      { href: "/rankings/all", label: "FBS and FCS" },
    ],
  },
  {
    title: "Games",
    links: [{ href: "/week", label: "This week" }],
  },
  {
    title: "Playoffs",
    links: [
      { href: "/playoff", label: "College Football Playoff" },
      { href: "/playoff/fcs", label: "FCS playoff" },
    ],
  },
]

/** This year, cached like the site's data (a page may not read the clock while prerendering). */
async function currentYear(): Promise<number> {
  "use cache"
  cacheLife("tsi")
  return new Date().getFullYear()
}

/**
 * Every page (owner, 2026-11-23, #161): the TSI mark with one line on what the site is, the
 * sections, and a bottom row with the copyright and the notices.
 */
export async function SiteFooter() {
  const year = await currentYear()
  return (
    <footer className="border-t border-border bg-card text-sm text-muted-foreground">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <div className="grid gap-8 py-10 md:grid-cols-[minmax(0,1.4fr)_repeat(3,minmax(0,1fr))]">
          <div className="space-y-3">
            <Link href="/" className="inline-flex items-center gap-2.5 text-foreground">
              <span className="rounded-sm bg-primary px-1.5 py-0.5 text-lg leading-none font-bold text-primary-foreground font-stretch-condensed">
                TSI
              </span>
              <span className="text-base leading-none font-semibold font-stretch-semi-condensed">
                The Swann Index
              </span>
            </Link>
            <p className="max-w-[38ch]">
              Independent college football ratings, rankings and predictions for FBS and FCS,
              updated every morning. Every rating and prediction uses only games played before
              kickoff.
            </p>
          </div>
          {SECTIONS.map((section) => (
            <nav key={section.title} aria-label={`${section.title} (footer)`} className="space-y-3">
              <h2 className="text-xs font-semibold tracking-wide text-foreground uppercase">
                {section.title}
              </h2>
              <ul className="space-y-2">
                {section.links.map((link) => (
                  <li key={link.href}>
                    <Link href={link.href} className="hover:text-foreground hover:underline">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          ))}
        </div>
        <div className="flex flex-col gap-2 border-t border-border py-5 text-xs md:flex-row md:items-baseline md:justify-between md:gap-8">
          <p className="shrink-0">© {year} The Swann Index. All rights reserved.</p>
          <p className="md:text-right">
            Not affiliated with the NCAA or any conference or school; team names and logos belong to
            their owners. For information and entertainment, not betting advice.
          </p>
        </div>
      </div>
    </footer>
  )
}

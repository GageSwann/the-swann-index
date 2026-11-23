import Link from "next/link"

import { SPORTS } from "@/lib/sports"

import { SportMenu } from "./sport-menu"
import { ThemeToggle } from "./theme-toggle"

/**
 * The "score bug": the TSI block, a menu per sport (CFB: Rankings, Schedule, Playoffs), the
 * theme toggle, and a 2 px rule underneath (white or black; a
 * team page's color on team pages, `.tsi-header`). This strip is the site's one bold
 * element; pages stay quiet. The week is stated by each page, not here (owner, #160).
 */
export function SiteHeader() {
  return (
    <header className="tsi-header border-b-2 bg-card pt-[env(safe-area-inset-top)]">
      <div className="tsi-safe-x mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-2 py-2.5">
        <Link href="/" className="flex items-center gap-2.5" aria-label="The Swann Index, home">
          <span className="rounded-sm bg-primary px-1.5 py-0.5 text-xl leading-none font-bold text-primary-foreground font-stretch-condensed">
            TSI
          </span>
          <span className="text-lg leading-none font-semibold font-stretch-semi-condensed">
            The Swann Index
          </span>
        </Link>
        {/* One menu per sport (CFB now); phones keep the bottom bar (BottomNav, #163). */}
        <nav aria-label="Main" className="hidden items-center gap-1 sm:ml-auto sm:flex">
          {SPORTS.map((sport) => (
            <SportMenu key={sport.key} sport={sport} />
          ))}
        </nav>
        <div className="ml-auto sm:ml-0">
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}

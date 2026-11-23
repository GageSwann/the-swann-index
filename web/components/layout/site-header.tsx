import Link from "next/link"

import { MainNav } from "./main-nav"
import { ThemeToggle } from "./theme-toggle"

/**
 * The "score bug": the TSI block, the nav, and a 2 px rule underneath (white or black; a
 * team page's color on team pages, `.tsi-header`). This strip is the site's one bold
 * element; pages stay quiet. The week is stated by each page, not here (owner, #160).
 */
export function SiteHeader() {
  return (
    <header className="tsi-header border-b-2 bg-card">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-2.5 sm:px-6">
        <Link href="/" className="flex items-center gap-2.5" aria-label="The Swann Index, home">
          <span className="rounded-sm bg-primary px-1.5 py-0.5 text-xl leading-none font-bold text-primary-foreground font-stretch-condensed">
            TSI
          </span>
          <span className="text-lg leading-none font-semibold font-stretch-semi-condensed">
            The Swann Index
          </span>
        </Link>
        {/* Phones: the sections live in the bottom bar (BottomNav, #163). */}
        <div className="hidden items-center sm:ml-auto sm:flex">
          <MainNav />
        </div>
        <div className="ml-auto sm:ml-0">
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}

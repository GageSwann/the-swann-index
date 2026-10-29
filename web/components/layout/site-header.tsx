import Link from "next/link"

import { getMeta } from "@/lib/api/queries"

import { MainNav } from "./main-nav"
import { ThemeToggle } from "./theme-toggle"

/**
 * The "score bug": an amber TSI block, the season/week in play, the nav, and a thin
 * amber rule underneath. This strip is the site's one bold element; pages stay quiet.
 */
export async function SiteHeader() {
  const meta = await getMeta().catch(() => null)
  const context =
    meta === null
      ? null
      : meta.season_type === "postseason"
        ? `Bowl season ${meta.season}`
        : meta.week > 0
          ? `Week ${meta.week}, ${meta.season}`
          : `Preseason ${meta.season}`

  return (
    <header className="border-b-2 border-primary bg-card">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-2.5 sm:px-6">
        <Link href="/" className="flex items-center gap-2.5" aria-label="The Swann Index, home">
          <span className="rounded-sm bg-primary px-1.5 py-0.5 text-xl leading-none font-extrabold text-primary-foreground font-stretch-condensed">
            TSI
          </span>
          <span className="text-lg leading-none font-semibold font-stretch-semi-condensed">
            The Swann Index
          </span>
        </Link>
        {/* Hidden on phones so the theme toggle shares the first row; every page states the week. */}
        {context && (
          <span className="hidden text-sm text-muted-foreground font-stretch-semi-condensed sm:inline">
            {context}
          </span>
        )}
        <div className="order-last flex w-full items-center sm:order-0 sm:ml-auto sm:w-auto">
          <MainNav />
        </div>
        <div className="ml-auto sm:ml-0">
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}

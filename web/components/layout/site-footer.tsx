import { cacheLife } from "next/cache"

/** This year, cached like the site's data (a page may not read the clock while prerendering). */
async function currentYear(): Promise<number> {
  "use cache"
  cacheLife("tsi")
  return new Date().getFullYear()
}

/** Every page (owner, 2026-11-23, #161): the copyright and the notices, nothing else. */
export async function SiteFooter() {
  const year = await currentYear()
  return (
    <footer className="border-t border-border text-xs text-muted-foreground">
      <div className="mx-auto flex max-w-7xl flex-col gap-2 px-4 py-5 sm:px-6 md:flex-row md:items-baseline md:justify-between md:gap-8">
        <p className="shrink-0">© {year} The Swann Index. All rights reserved.</p>
        <p className="md:text-right">
          Not affiliated with the NCAA or any conference or school; team names and logos belong to
          their owners. For information and entertainment, not betting advice.
        </p>
      </div>
    </footer>
  )
}

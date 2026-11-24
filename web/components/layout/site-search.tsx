"use client"

import { SearchIcon } from "lucide-react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { useEffect, useId, useMemo, useRef, useState } from "react"
import { flushSync } from "react-dom"

import { TeamLogo } from "@/components/team/team-logo"
import { cfb } from "@/lib/routes"
import { type SearchTeam, searchTeams, sportLabel, teamHref } from "@/lib/search"
import { cn } from "@/lib/utils"

import { setSearchOpen, useSearchLayer } from "./header-layer"

// The team list, fetched once per visit on first use (a cached file, never the API per key).
let index: Promise<SearchTeam[]> | null = null
function loadIndex(): Promise<SearchTeam[]> {
  index ??= fetch(cfb.searchIndex)
    .then((r) => {
      if (!r.ok) throw new Error(`search index: ${r.status}`)
      return r.json() as Promise<SearchTeam[]>
    })
    .catch((error: unknown) => {
      index = null // try again next time
      throw error
    })
  return index
}

/** A key press that should open search: "/" or Ctrl/⌘+K, unless the reader is typing. */
function isShortcut(e: KeyboardEvent): boolean {
  const target = e.target as HTMLElement | null
  const typing =
    !!target && (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName))
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") return true
  return e.key === "/" && !typing && !e.ctrlKey && !e.metaKey && !e.altKey
}

/**
 * The header's team search (owner, 2026-11-24, #193): a magnifying glass that opens a search
 * box; typing lists matching teams (school, mascot or abbreviation), best first, each linking
 * to its team page in its sport (each result says which: "CFB"). Desktop: the box opens over
 * the sport menus' place (they step aside while it's open, so nothing in the header moves) and
 * the list hangs below it, to the right like the sport menus. Phones:
 * a sheet across the top of the screen with Cancel. Keys: "/" or Ctrl/⌘+K opens, ↑/↓ pick,
 * Enter goes, Escape closes.
 */
export function SiteSearch() {
  const pathname = usePathname()
  const router = useRouter()
  // Open on which page: a page change closes it without an effect (like the sport menus).
  // A sport menu opened by a click closes search through the shared layer (#193).
  const [openOn, setOpenOn] = useState<string | null>(null)
  const layer = useSearchLayer()
  const open = openOn === pathname && layer.open
  const [query, setQuery] = useState("")
  const [active, setActive] = useState(0)
  const [teams, setTeams] = useState<SearchTeam[] | null>(null)
  const [failed, setFailed] = useState(false)
  const root = useRef<HTMLDivElement>(null)
  const input = useRef<HTMLInputElement>(null)
  const button = useRef<HTMLButtonElement>(null)
  const listId = useId()

  const results = useMemo(() => (teams ? searchTeams(teams, query) : []), [teams, query])

  const load = () => {
    setFailed(false)
    loadIndex().then(setTeams, () => setFailed(true))
  }
  const openSearch = () => {
    // Render the box and focus it in the same tap, or iPhones don't raise the keyboard.
    setSearchOpen(true) // closes any sport menu (one header dropdown at a time)
    flushSync(() => {
      setQuery("")
      setActive(0)
      setOpenOn(pathname)
    })
    input.current?.focus()
    if (!teams) load()
  }
  const close = (refocus = false) => {
    setSearchOpen(false)
    setOpenOn(null)
    if (refocus) button.current?.focus()
  }
  const go = (entry: SearchTeam | undefined) => {
    if (!entry) return
    close()
    router.push(teamHref(entry))
  }

  // Keep the highlighted team in view as ↑/↓ move through a long, scrolling list.
  useEffect(() => {
    if (open) document.getElementById(optionId(active))?.scrollIntoView({ block: "nearest" })
  })

  // Tell the sport menus, also when a page change closes search (an external store, not state).
  useEffect(() => setSearchOpen(open), [open])
  useEffect(() => () => setSearchOpen(false), [])

  // "/" or Ctrl/⌘+K opens search from anywhere on the page.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (open || !isShortcut(e)) return
      e.preventDefault()
      openSearch()
    }
    document.addEventListener("keydown", onKey)
    return () => document.removeEventListener("keydown", onKey)
  })

  // Close on a click outside the box and its list. A click, not a press: closing shrinks the
  // box and moves the sport menus, so closing on the press made a click on one miss it.
  useEffect(() => {
    if (!open) return
    const onClick = (e: MouseEvent) => {
      if (root.current?.contains(e.target as Node)) return
      setSearchOpen(false)
      setOpenOn(null)
    }
    document.addEventListener("click", onClick)
    return () => document.removeEventListener("click", onClick)
  }, [open])

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Escape") {
      e.preventDefault()
      close(true)
    } else if (e.key === "ArrowDown" && results.length) {
      e.preventDefault()
      setActive((i) => (i + 1) % results.length)
    } else if (e.key === "ArrowUp" && results.length) {
      e.preventDefault()
      setActive((i) => (i - 1 + results.length) % results.length)
    } else if (e.key === "Enter") {
      e.preventDefault()
      go(results[active])
    }
  }

  const typed = query.trim() !== ""
  const message = failed
    ? "Search isn't available right now."
    : !typed
      ? "Search teams by school, mascot or abbreviation."
      : !teams
        ? "Loading teams…"
        : results.length === 0
          ? `No teams match “${query.trim()}”.`
          : null
  const optionId = (i: number) => `${listId}-${i}`

  return (
    <div ref={root} className="relative flex items-center">
      <button
        ref={button}
        type="button"
        onClick={openSearch}
        onPointerEnter={() => !teams && loadIndex().then(setTeams, () => {})}
        aria-label="Search teams"
        aria-keyshortcuts="/ Control+K"
        // Invisible, not removed, while open: the header keeps its layout.
        className={cn(
          "inline-flex size-9 items-center justify-center rounded-md text-muted-foreground hover:text-foreground",
          open && "invisible",
        )}
      >
        <SearchIcon className="size-4" aria-hidden />
      </button>
      {/* Phones: dim the page behind the sheet; a tap there closes it. */}
      <div
        hidden={!open}
        aria-hidden
        onClick={() => close()}
        className="fixed inset-0 z-40 bg-background/70 sm:hidden"
      />
      <div
        hidden={!open}
        className="z-50 max-sm:fixed max-sm:inset-x-0 max-sm:top-0 max-sm:border-b max-sm:border-border max-sm:bg-card max-sm:pt-[env(safe-area-inset-top)] sm:absolute sm:top-1/2 sm:right-0 sm:-translate-y-1/2"
      >
        <div className="flex items-center gap-3 max-sm:py-2.5 max-sm:pr-[max(1rem,env(safe-area-inset-right))] max-sm:pl-[max(1rem,env(safe-area-inset-left))]">
          <div className="relative flex-1 sm:w-60 lg:w-72">
            <SearchIcon
              className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden
            />
            <input
              ref={input}
              type="search"
              role="combobox"
              aria-label="Search teams"
              aria-expanded={open && results.length > 0}
              aria-controls={listId}
              aria-autocomplete="list"
              aria-activedescendant={results.length ? optionId(active) : undefined}
              autoComplete="off"
              autoCorrect="off"
              spellCheck={false}
              enterKeyHint="go"
              placeholder="Search teams"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value)
                setActive(0)
              }}
              onKeyDown={onKeyDown}
              // 16px on phones: smaller text makes iPhones zoom the page on focus.
              className="h-9 w-full rounded-md border border-border bg-background pr-2 pl-8 text-base text-foreground placeholder:text-muted-foreground focus:border-foreground focus:outline-none sm:text-sm [&::-webkit-search-cancel-button]:hidden"
            />
          </div>
          <button
            type="button"
            onClick={() => close(true)}
            className="text-sm font-medium text-muted-foreground hover:text-foreground sm:hidden"
          >
            Cancel
          </button>
        </div>
        {/* Desktop: from the box's left edge to the theme toggle's right edge (size-9). */}
        {/* Every match, so the list scrolls: desktop up to ~28 rem, phones down to the screen's
            bottom (the sheet's input row is ~3.5 rem). */}
        <div className="overflow-y-auto overscroll-contain max-sm:max-h-[calc(100dvh-3.5rem-env(safe-area-inset-top))] max-sm:border-t max-sm:border-border sm:absolute sm:top-full sm:left-0 sm:mt-1.5 sm:max-h-[min(28rem,calc(100dvh-5rem))] sm:w-[calc(100%+2.25rem)] sm:rounded-md sm:border sm:border-border sm:bg-card">
          {message && (
            <p className="px-4 py-3 text-sm text-muted-foreground sm:px-3" role="status">
              {message}
            </p>
          )}
          <ul id={listId} role="listbox" aria-label="Teams" className="p-1.5" hidden={!!message}>
            {results.map((entry, i) => (
              <li key={entry.team.slug} role="presentation">
                <Link
                  id={optionId(i)}
                  role="option"
                  aria-selected={i === active}
                  href={teamHref(entry)}
                  onClick={() => close()}
                  onPointerMove={() => setActive(i)}
                  className={cn(
                    "flex items-center gap-3 rounded-sm px-2.5 py-2",
                    i === active && "bg-muted",
                  )}
                >
                  <TeamLogo team={entry.team} size={28} />
                  <span className="min-w-0 flex-1">
                    {/* School and mascot, as fans say it: "Utah Utes" (owner). */}
                    <span className="block truncate text-sm font-medium text-foreground">
                      {[entry.team.school, entry.team.mascot].filter(Boolean).join(" ")}
                    </span>
                    <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                      {/* Which sport's page this opens (owner: CBB and CBASE pages later). */}
                      <span className="shrink-0 rounded-sm border border-border px-1 text-[0.625rem] leading-4 font-semibold tracking-wide text-foreground">
                        {sportLabel(entry.sport)}
                      </span>
                      <span className="truncate">
                        {[entry.team.division?.toUpperCase(), entry.team.conference]
                          .filter(Boolean)
                          .join(" · ")}
                      </span>
                    </span>
                  </span>
                  {entry.rank !== null && (
                    <span className="text-xs text-muted-foreground tabular-nums">
                      #{entry.rank}
                    </span>
                  )}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}

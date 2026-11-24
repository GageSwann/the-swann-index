"use client"

import { SearchIcon } from "lucide-react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { useEffect, useId, useMemo, useRef, useState } from "react"
import { flushSync } from "react-dom"

import { TeamLogo } from "@/components/team/team-logo"
import { cfb } from "@/lib/routes"
import { type SearchTeam, searchTeams } from "@/lib/search"
import { cn } from "@/lib/utils"

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
 * to its team page. Desktop: the box replaces the button and the list hangs below it. Phones:
 * a sheet across the top of the screen with Cancel. Keys: "/" or Ctrl/⌘+K opens, ↑/↓ pick,
 * Enter goes, Escape closes.
 */
export function SiteSearch() {
  const pathname = usePathname()
  const router = useRouter()
  // Open on which page: a page change closes it without an effect (like the sport menus).
  const [openOn, setOpenOn] = useState<string | null>(null)
  const open = openOn === pathname
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
    flushSync(() => {
      setQuery("")
      setActive(0)
      setOpenOn(pathname)
    })
    input.current?.focus()
    if (!teams) load()
  }
  const close = (refocus = false) => {
    setOpenOn(null)
    if (refocus) button.current?.focus()
  }
  const go = (entry: SearchTeam | undefined) => {
    if (!entry) return
    close()
    router.push(cfb.team(entry.team.slug))
  }

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

  // Close on a press outside the box and its list.
  useEffect(() => {
    if (!open) return
    const onPress = (e: PointerEvent) => {
      if (!root.current?.contains(e.target as Node)) setOpenOn(null)
    }
    document.addEventListener("pointerdown", onPress)
    return () => document.removeEventListener("pointerdown", onPress)
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
    <div ref={root} className="flex items-center">
      <button
        ref={button}
        type="button"
        hidden={open}
        onClick={openSearch}
        onPointerEnter={() => !teams && loadIndex().then(setTeams, () => {})}
        aria-label="Search teams"
        aria-keyshortcuts="/ Control+K"
        className="inline-flex size-9 items-center justify-center rounded-md text-muted-foreground hover:text-foreground"
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
        className="z-50 max-sm:fixed max-sm:inset-x-0 max-sm:top-0 max-sm:border-b max-sm:border-border max-sm:bg-card max-sm:pt-[env(safe-area-inset-top)] sm:relative"
      >
        <div className="flex items-center gap-3 max-sm:py-2.5 max-sm:pr-[max(1rem,env(safe-area-inset-right))] max-sm:pl-[max(1rem,env(safe-area-inset-left))]">
          <div className="relative flex-1 sm:w-56 lg:w-64">
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
        <div className="max-sm:border-t max-sm:border-border sm:absolute sm:top-full sm:right-0 sm:mt-1.5 sm:w-80 sm:rounded-md sm:border sm:border-border sm:bg-card">
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
                  href={cfb.team(entry.team.slug)}
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
                    <span className="block truncate text-xs text-muted-foreground">
                      {[entry.team.division?.toUpperCase(), entry.team.conference]
                        .filter(Boolean)
                        .join(" · ")}
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

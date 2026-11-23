"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useEffect, useId, useRef, useState } from "react"

import { type Sport, inSection } from "@/lib/sports"
import { cn } from "@/lib/utils"

const CLOSE_DELAY_MS = 150 // time to move the pointer from a button into its list
const LIST_WIDTH_PX = 176 // the list's width (min-w-44)
const EDGE_GAP_PX = 8 // keep the list this far from the window's edge

type Opened = { key: string; path: string; leftward: boolean }

/**
 * The header's sport menus (#181, #183): one per sport, and at most one open at a time.
 * Moving from one sport to the next switches menus at once; only leaving the menus
 * altogether waits a moment (so the pointer can travel from a button into its list).
 * Desktop and tablets; phones use the bottom bar (#163).
 */
export function SportMenus({ sports }: { sports: Sport[] }) {
  const pathname = usePathname()
  // Which menu is open, and on which page: a page change closes it without an effect.
  const [opened, setOpened] = useState<Opened | null>(null)
  const openKey = opened?.path === pathname ? opened.key : null
  const nav = useRef<HTMLElement>(null)
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const cancelClose = () => {
    if (closeTimer.current) clearTimeout(closeTimer.current)
    closeTimer.current = null
  }
  const close = () => {
    cancelClose()
    setOpened(null)
  }
  const open = (key: string, menu: HTMLElement | null) => {
    cancelClose()
    const left = menu?.getBoundingClientRect().left ?? 0
    setOpened({
      key,
      path: pathname,
      leftward: left + LIST_WIDTH_PX > window.innerWidth - EDGE_GAP_PX,
    })
  }
  const closeSoon = () => {
    cancelClose()
    closeTimer.current = setTimeout(() => setOpened(null), CLOSE_DELAY_MS)
  }

  // Close on a press anywhere outside the menus.
  useEffect(() => {
    if (!openKey) return
    const onPress = (e: PointerEvent) => {
      if (!nav.current?.contains(e.target as Node)) setOpened(null)
    }
    document.addEventListener("pointerdown", onPress)
    return () => document.removeEventListener("pointerdown", onPress)
  }, [openKey])
  useEffect(() => cancelClose, [])

  return (
    <nav
      ref={nav}
      aria-label="Main"
      className="hidden items-center gap-1 sm:ml-auto sm:flex"
      onPointerLeave={(e) => {
        if (e.pointerType === "mouse") closeSoon()
      }}
    >
      {sports.map((sport) => (
        <SportMenu
          key={sport.key}
          sport={sport}
          open={openKey === sport.key}
          leftward={!!opened?.leftward}
          onOpen={(menu) => open(sport.key, menu)}
          onClose={close}
        />
      ))}
    </nav>
  )
}

/**
 * One sport's menu: the sport's short name ("CFB"), every button the same width with the name centered, so
 * the sports sit evenly spaced; a sport
 * without sections yet says "Coming Soon". Opens when a mouse hovers it, and on click,
 * tap, Enter or Space; closes on Escape (focus back to the button). The list hangs off
 * the button's right side, unless that would run past the window: then it opens leftward.
 * A disclosure (button + list of links) rather than an ARIA menu, so screen readers read
 * it as plain links. The button is underlined while one of the sport's sections is shown.
 */
function SportMenu({
  sport,
  open,
  leftward,
  onOpen,
  onClose,
}: {
  sport: Sport
  open: boolean
  leftward: boolean
  onOpen: (menu: HTMLElement | null) => void
  onClose: () => void
}) {
  const pathname = usePathname()
  const root = useRef<HTMLDivElement>(null)
  const button = useRef<HTMLButtonElement>(null)
  const pointer = useRef<string | null>(null) // the pointer behind the next click, if any
  const listId = useId()
  const active = sport.sections.some((s) => inSection(pathname, s))
  const soon = sport.sections.length === 0 // not built yet: the menu says so

  return (
    <div
      ref={root}
      className="relative"
      onPointerEnter={(e) => {
        if (e.pointerType === "mouse") onOpen(root.current)
      }}
      onKeyDown={(e) => {
        if (e.key === "Escape" && open) {
          onClose()
          button.current?.focus()
        }
      }}
    >
      <button
        ref={button}
        type="button"
        aria-expanded={open}
        aria-controls={listId}
        aria-label={soon ? `${sport.name}: Coming Soon` : `${sport.name} sections`}
        // A mouse already opened it by hovering, so its click only opens (a toggle could
        // close the menu it just opened); a tap or Enter/Space toggles.
        onPointerDown={(e) => {
          pointer.current = e.pointerType
        }}
        onClick={() => {
          const byMouse = pointer.current === "mouse"
          pointer.current = null
          if (byMouse || !open) onOpen(root.current)
          else onClose()
        }}
        className={cn(
          "flex min-w-18 items-center justify-center rounded-sm px-2.5 py-1.5 text-sm font-semibold",
          active || open ? "text-foreground" : "text-muted-foreground hover:text-foreground",
          active && "tsi-nav-active",
        )}
      >
        {sport.label}
      </button>
      {/* pt-1.5 bridges the gap, so the pointer can travel from the button to the list. */}
      <div
        id={listId}
        hidden={!open}
        className={cn("absolute top-full z-50 pt-1.5", leftward ? "right-0" : "left-0")}
      >
        <div className="min-w-44 rounded-md border border-border bg-card p-1.5">
          {/* The sport's name, then a thin divider before its sections (owner). */}
          <p className="mx-1 mb-1 border-b border-border px-1.5 pt-1 pb-1.5 text-xs text-muted-foreground">
            {sport.name}
          </p>
          {soon && <p className="px-2.5 pt-0.5 pb-2 text-sm text-foreground">Coming Soon</p>}
          <ul>
            {sport.sections.map((section) => {
              const { href, label } = section
              const current = inSection(pathname, section)
              return (
                <li key={href}>
                  <Link
                    href={href}
                    aria-current={current ? "page" : undefined}
                    onClick={onClose}
                    className={cn(
                      "block rounded-sm px-2.5 py-2 text-sm font-medium hover:bg-muted",
                      current ? "bg-muted text-foreground" : "text-foreground",
                    )}
                  >
                    {label}
                  </Link>
                </li>
              )
            })}
          </ul>
        </div>
      </div>
    </div>
  )
}

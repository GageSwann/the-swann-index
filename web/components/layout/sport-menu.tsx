"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useEffect, useId, useRef, useState } from "react"

import { type Sport, inSection } from "@/lib/sports"
import { cn } from "@/lib/utils"

const CLOSE_DELAY_MS = 150 // time to move the pointer from the button into the list
const LIST_WIDTH_PX = 176 // the list's width (min-w-44)
const EDGE_GAP_PX = 8 // keep the list this far from the window's edge

/**
 * One sport's menu in the header (desktop and tablets; phones use the bottom bar, #163):
 * the sport's short name and a small emoji after it ("CFB 🏈"); a sport without sections
 * yet says "Coming Soon" in its menu. The list hangs off the button's right side (its
 * left edge under the button's), unless that would run past the window: then it opens
 * leftward instead.
 * Opens when a mouse hovers it, and on click, tap, Enter or Space; closes on Escape (focus
 * back to the button), a click elsewhere, or a page change. A disclosure (button +
 * list of links) rather than an ARIA menu, so screen readers read it as plain links. The
 * button is underlined while one of the sport's sections is shown, like the old tabs.
 */
export function SportMenu({ sport }: { sport: Sport }) {
  const pathname = usePathname()
  // The page the menu was opened on: it counts as open only there, so moving to another
  // page closes it without an effect.
  const [openOn, setOpenOn] = useState<string | null>(null)
  const open = openOn === pathname
  const [leftward, setLeftward] = useState(false) // no room to the right: open leftward
  const root = useRef<HTMLDivElement>(null)
  const setOpen = (value: boolean) => {
    if (value) {
      const left = root.current?.getBoundingClientRect().left ?? 0
      setLeftward(left + LIST_WIDTH_PX > window.innerWidth - EDGE_GAP_PX)
    }
    setOpenOn(value ? pathname : null)
  }
  const button = useRef<HTMLButtonElement>(null)
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const listId = useId()
  const active = sport.sections.some((s) => inSection(pathname, s))
  const soon = sport.sections.length === 0 // not built yet: the menu says so

  const cancelClose = () => {
    if (closeTimer.current) clearTimeout(closeTimer.current)
    closeTimer.current = null
  }
  const closeSoon = () => {
    cancelClose()
    closeTimer.current = setTimeout(() => setOpenOn(null), CLOSE_DELAY_MS)
  }

  // Close on a press anywhere outside the menu.
  useEffect(() => {
    if (!open) return
    const onPress = (e: PointerEvent) => {
      if (!root.current?.contains(e.target as Node)) setOpenOn(null)
    }
    document.addEventListener("pointerdown", onPress)
    return () => document.removeEventListener("pointerdown", onPress)
  }, [open])
  useEffect(() => cancelClose, [])

  return (
    <div
      ref={root}
      className="relative"
      onPointerEnter={(e) => {
        if (e.pointerType !== "mouse") return
        cancelClose()
        setOpen(true)
      }}
      onPointerLeave={(e) => {
        if (e.pointerType === "mouse") closeSoon()
      }}
      onKeyDown={(e) => {
        if (e.key === "Escape" && open) {
          setOpen(false)
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
        onClick={() => setOpen(!open)}
        className={cn(
          "flex items-center gap-1.5 rounded-sm px-2.5 py-1.5 text-sm font-semibold",
          active || open ? "text-foreground" : "text-muted-foreground hover:text-foreground",
          active && "tsi-nav-active",
        )}
      >
        {sport.label}
        <span aria-hidden className="text-xs leading-none">
          {sport.emoji}
        </span>
      </button>
      {/* pt-1.5 bridges the gap, so the pointer can travel from the button to the list. */}
      <div
        id={listId}
        hidden={!open}
        className={cn("absolute top-full z-50 pt-1.5", leftward ? "right-0" : "left-0")}
      >
        <div className="min-w-44 rounded-md border border-border bg-card p-1.5">
          <p className="px-2.5 pt-1 pb-1.5 text-xs text-muted-foreground">{sport.name}</p>
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
                    onClick={() => setOpen(false)}
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

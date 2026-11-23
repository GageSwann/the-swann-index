"use client"

import { CalendarDays, House, ListOrdered, Trophy } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"

import { cn } from "@/lib/utils"

const ITEMS = [
  { href: "/", label: "Home", icon: House, match: (p: string) => p === "/" },
  {
    href: "/rankings",
    label: "Rankings",
    icon: ListOrdered,
    match: (p: string) => p.startsWith("/rankings"),
  },
  {
    href: "/week",
    label: "This week",
    icon: CalendarDays,
    match: (p: string) => p.startsWith("/week"),
  },
  {
    href: "/playoff",
    label: "Playoffs",
    icon: Trophy,
    match: (p: string) => p.startsWith("/playoff"),
  },
]

/**
 * Phones only (owner, 2026-11-23, #163): the site's sections in a fixed bar at the bottom,
 * within thumb reach, like a sports app. The active section is marked by a bar along its top
 * edge, the header's 2 px rule turned around. Wider screens keep the nav in the header.
 */
export function BottomNav() {
  const pathname = usePathname()
  return (
    <nav
      aria-label="Main"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-card pr-[env(safe-area-inset-right)] pb-[env(safe-area-inset-bottom)] pl-[env(safe-area-inset-left)] sm:hidden"
    >
      <ul className="grid grid-cols-4">
        {ITEMS.map(({ href, label, icon: Icon, match }) => {
          const active = match(pathname)
          return (
            <li key={href}>
              <Link
                href={href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "relative flex h-16 flex-col items-center justify-center gap-1 text-[11px] font-medium",
                  active ? "text-foreground" : "text-muted-foreground",
                )}
              >
                {active && (
                  <span
                    aria-hidden
                    className="absolute inset-x-5 top-0 h-0.5 rounded-b bg-primary"
                  />
                )}
                <Icon className="size-5" strokeWidth={active ? 2.25 : 1.75} aria-hidden />
                {label}
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}

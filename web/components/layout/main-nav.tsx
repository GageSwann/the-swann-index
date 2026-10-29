"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

import { cn } from "@/lib/utils"

const LINKS = [
  { href: "/", label: "Rankings", match: (p: string) => p === "/" },
  { href: "/week", label: "This week", match: (p: string) => p.startsWith("/week") },
  { href: "/playoff", label: "Playoff", match: (p: string) => p.startsWith("/playoff") },
  { href: "/book", label: "TSI Book", match: (p: string) => p.startsWith("/book") },
  { href: "/matchup", label: "Matchup", match: (p: string) => p.startsWith("/matchup") },
  { href: "/model", label: "Model", match: (p: string) => p.startsWith("/model") },
]

export function MainNav() {
  const pathname = usePathname()
  return (
    <nav aria-label="Main" className="-mx-1 flex gap-1 overflow-x-auto">
      {LINKS.map(({ href, label, match }) => {
        const active = match(pathname)
        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "shrink-0 rounded-sm px-2.5 py-1.5 text-sm font-medium whitespace-nowrap",
              active
                ? "text-primary shadow-[inset_0_-2px_0_var(--primary)]"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {label}
          </Link>
        )
      })}
    </nav>
  )
}

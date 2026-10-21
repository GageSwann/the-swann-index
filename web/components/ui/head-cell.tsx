import type { ReactNode } from "react"

import { cn } from "@/lib/utils"

/** A column header in the site's tables: muted medium text, left or right aligned. */
export function HeadCell({
  children,
  align = "left",
  title,
  className,
}: {
  children: ReactNode
  align?: "left" | "right"
  title?: string
  className?: string
}) {
  return (
    <th
      scope="col"
      title={title}
      className={cn(
        "px-3 py-2 font-medium",
        align === "right" ? "text-right" : "text-left",
        className,
      )}
    >
      {children}
    </th>
  )
}

"use client"

import type { ReactNode } from "react"

import { cn } from "@/lib/utils"

/** A row of toggle buttons for one choice (aria-pressed marks the current one). */
export function Segmented<T extends string>({
  label,
  value,
  onChange,
  options,
  controls,
  className,
  stretch = false,
}: {
  label: string
  value: T
  onChange: (value: T) => void
  options: { value: T; label: ReactNode }[]
  controls?: string // id of the region the choice changes (aria-controls)
  className?: string
  stretch?: boolean // the options share the control's full width (phones)
}) {
  return (
    <div
      role="group"
      aria-label={label}
      className={cn("inline-flex rounded-md border border-border bg-card p-0.5", className)}
    >
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          aria-pressed={value === o.value}
          aria-controls={controls}
          onClick={() => onChange(o.value)}
          className={cn(
            "rounded-sm px-3 py-1 text-sm font-medium whitespace-nowrap",
            stretch && "flex-1",
            value === o.value
              ? "tsi-lit bg-primary text-primary-foreground"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}

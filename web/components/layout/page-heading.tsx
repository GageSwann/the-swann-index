import type { ReactNode } from "react"

/** Page title in the condensed broadcast voice, with an optional one-line description. */
export function PageHeading({
  title,
  children,
  phoneHidden = false,
}: {
  title: string
  children?: ReactNode
  phoneHidden?: boolean // phones show the title only (#165)
}) {
  return (
    <div className="mb-6 max-w-[70ch]">
      <h1 className="text-4xl leading-tight font-bold font-stretch-condensed sm:text-5xl">
        {title}
      </h1>
      {children && (
        <p className={`mt-2 text-muted-foreground ${phoneHidden ? "max-sm:hidden" : ""}`}>
          {children}
        </p>
      )}
    </div>
  )
}

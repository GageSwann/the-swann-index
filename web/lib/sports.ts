/**
 * The sports TSI covers, each with its sections (owner, 2026-11-23): college football now;
 * college basketball, baseball and others can be added as more entries later. Plain data
 * (no functions), so server components can pass it to the header's client menus.
 */
export type SportSection = {
  href: string
  label: string
  prefix: string // a page belongs to the section when its path starts with this
}

export type Sport = {
  key: string
  label: string // the header button: "CFB"
  emoji: string // after the label, so sports tell apart at a glance (owner)
  name: string // the menu's heading and screen-reader name: "College Football"
  sections: SportSection[] // none yet: the menu says "Coming Soon"
}

export const SPORTS: Sport[] = [
  {
    key: "cfb",
    label: "CFB",
    emoji: "🏈",
    name: "College Football",
    sections: [
      { href: "/cfb", label: "Home", prefix: "/cfb" },
      { href: "/cfb/rankings", label: "Rankings", prefix: "/cfb/rankings" },
      { href: "/cfb/schedule", label: "Schedule", prefix: "/cfb/schedule" },
      { href: "/cfb/playoffs", label: "Playoffs", prefix: "/cfb/playoffs" },
    ],
  },
  { key: "cbb", label: "CBB", emoji: "🏀", name: "College Basketball", sections: [] },
  { key: "cbase", label: "CBASE", emoji: "⚾", name: "College Baseball", sections: [] },
]

/** Is this page one of the section's pages? */
export function inSection(pathname: string, section: SportSection): boolean {
  return pathname.startsWith(section.prefix)
}

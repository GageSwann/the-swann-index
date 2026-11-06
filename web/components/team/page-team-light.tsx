import type { TeamRef } from "@/lib/api/types"
import { teamColor } from "@/lib/format/color"

/**
 * A team page takes on the team's light (decision #137): the header rule, focus and
 * selected-tab glows and the page's bars use the team's contrast-checked color per theme
 * (`--light` in app/globals.css reads these). Rendered inside the page, so it goes away
 * when you navigate off it. `teamColor` only ever returns a #rrggbb value.
 */
export function PageTeamLight({ team }: { team: TeamRef }) {
  const css = `:root{--page-team-dark:${teamColor(team, "dark")};--page-team-light:${teamColor(team, "light")}}`
  return <style>{css}</style>
}

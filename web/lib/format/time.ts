// Times are shown in US Eastern (college football's reference time zone) and formatted
// on the server, so server and browser render identical text.
const ZONE = "America/New_York"

const updatedFormat = new Intl.DateTimeFormat("en-US", {
  timeZone: ZONE,
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit",
  timeZoneName: "short",
})

/** "Oct 21, 6:00 AM EDT" */
export function formatUpdated(iso: string): string {
  return updatedFormat.format(new Date(iso))
}

const dayFormat = new Intl.DateTimeFormat("en-US", {
  timeZone: ZONE,
  weekday: "long",
  month: "short",
  day: "numeric",
})
const kickoffFormat = new Intl.DateTimeFormat("en-US", {
  timeZone: ZONE,
  hour: "numeric",
  minute: "2-digit",
})

/** "Saturday, Oct 24" (groups the board by day). */
export function formatDay(iso: string): string {
  return dayFormat.format(new Date(iso))
}

/** "12:00 PM ET", or "Time TBA" for date-only kickoffs. */
export function formatKickoff(iso: string | null, tbd: boolean): string {
  if (iso === null || tbd) return "Time TBA"
  return `${kickoffFormat.format(new Date(iso))} ET`
}

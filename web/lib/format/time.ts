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

const shortDayFormat = new Intl.DateTimeFormat("en-US", {
  timeZone: ZONE,
  weekday: "short",
  month: "short",
  day: "numeric",
})

/** "Sat, Sep 5" (schedule rows). */
export function formatShortDay(iso: string): string {
  return shortDayFormat.format(new Date(iso))
}

const monthDayFormat = new Intl.DateTimeFormat("en-US", {
  timeZone: ZONE,
  month: "short",
  day: "numeric",
})

/** "Oct 20" (chart axes), in US Eastern like every other time on the site. */
export function formatMonthDay(iso: string): string {
  return monthDayFormat.format(new Date(iso))
}

const calendarDateFormat = new Intl.DateTimeFormat("en-US", {
  timeZone: "UTC",
  month: "short",
  day: "numeric",
  year: "numeric",
})

/** "Oct 11, 2026" for a calendar date ("2026-10-11"); no time zone shift. */
export function formatCalendarDate(isoDate: string): string {
  return calendarDateFormat.format(new Date(isoDate))
}

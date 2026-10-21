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

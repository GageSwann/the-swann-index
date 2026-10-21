import { redirect } from "next/navigation"

import { getMeta } from "@/lib/api/queries"

/** `/week` always means the current week. */
export default async function CurrentWeekPage() {
  const meta = await getMeta()
  redirect(`/week/${meta.season}/${Math.max(1, meta.week)}`)
}

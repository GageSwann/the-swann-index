import { redirect } from "next/navigation"

import { getMeta } from "@/lib/api/queries"
import { cfb } from "@/lib/routes"

/** `/cfb/schedule` always means the current week. */
export default async function CurrentWeekPage() {
  const meta = await getMeta()
  redirect(cfb.schedule(meta.season, Math.max(1, meta.week)))
}

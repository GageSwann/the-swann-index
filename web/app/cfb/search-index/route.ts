import { getRankings } from "@/lib/api/queries"
import type { SearchTeam } from "@/lib/search"

/**
 * The header search's team list (#193): every FBS and FCS team with its Résumé rank, as JSON.
 * Prerendered from the same cached reads as the Rankings pages (same arguments, so the same
 * cache entries: no extra API or Neon reads) and refreshed by the nightly revalidation.
 */
export async function GET() {
  const [fbs, fcs] = await Promise.all(
    (["fbs", "fcs"] as const).map((division) =>
      getRankings({ type: "resume", division }).catch(() => null),
    ),
  )
  const teams: SearchTeam[] = [fbs, fcs].flatMap((rankings) =>
    (rankings?.teams ?? []).map(({ team, rank }) => ({ sport: "cfb" as const, team, rank })),
  )
  return Response.json(teams)
}

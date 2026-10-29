import type { NextRequest } from "next/server"

import { pricedMatchup, readPick } from "@/lib/matchup"
import { ogImage, ogMessage } from "@/lib/og/frame"
import { TwoTeamCard } from "@/lib/og/two-team-card"

/**
 * Link preview for /matchup (the page lives in its query string, which the
 * `opengraph-image` convention can't see): `/api/og/matchup?away=…&home=…&neutral=1`.
 */
export async function GET(request: NextRequest) {
  const pick = readPick(request.nextUrl.searchParams)
  const matchup = await pricedMatchup(pick)
  const image = matchup
    ? await ogImage(
        <TwoTeamCard
          context={`Hypothetical${pick.neutral ? " | neutral site" : ""} | if played today`}
          away={matchup.away}
          home={matchup.home}
          awayScore={matchup.proj_away}
          homeScore={matchup.proj_home}
          neutral={pick.neutral}
          homeWinProb={matchup.home_win_prob}
        />,
        "Pick any two teams on the Matchup page",
      )
    : await ogMessage("Matchup: pick any two teams")
  // Ratings change once a day; let browsers and Vercel's CDN reuse the image for an hour.
  image.headers.set("Cache-Control", "public, max-age=3600, s-maxage=3600")
  return image
}

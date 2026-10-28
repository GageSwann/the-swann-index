import type { NextRequest } from "next/server"

import { getMatchup } from "@/lib/api/queries"
import { ogImage } from "@/lib/og/frame"
import { TwoTeamCard } from "@/lib/og/two-team-card"

/**
 * Link preview for /matchup (the page lives in its query string, which the
 * `opengraph-image` convention can't see): `/api/og/matchup?away=…&home=…&neutral=1`.
 */
export async function GET(request: NextRequest) {
  const q = request.nextUrl.searchParams
  const away = q.get("away")
  const home = q.get("home")
  const neutral = q.get("neutral") === "1"
  const matchup =
    away && home && away !== home ? await getMatchup(home, away, neutral).catch(() => null) : null
  const image = matchup
    ? await ogImage(
        <TwoTeamCard
          context={`Hypothetical${neutral ? " | neutral site" : ""} | if played today`}
          away={matchup.away}
          home={matchup.home}
          awayScore={matchup.proj_away}
          homeScore={matchup.proj_home}
          neutral={neutral}
          homeWinProb={matchup.home_win_prob}
        />,
        "Pick any two teams on the Matchup page",
      )
    : await ogImage(
        <div style={{ display: "flex", fontFamily: "Archivo Condensed", fontSize: 88 }}>
          Matchup: pick any two teams
        </div>,
      )
  // Ratings change once a day; let browsers and Vercel's CDN reuse the image for an hour.
  image.headers.set("Cache-Control", "public, max-age=3600, s-maxage=3600")
  return image
}

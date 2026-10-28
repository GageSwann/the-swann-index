import "server-only"

import type { TeamRef } from "@/lib/api/types"
import { separation, teamColor } from "@/lib/format/color"

import { OG, OgLogo } from "./frame"

type Props = {
  context: string // "Saturday, Oct 31 | TSI projection", "Final", "Hypothetical | neutral site"
  away: TeamRef
  home: TeamRef
  awayScore: number | null | undefined
  homeScore: number | null | undefined
  neutral: boolean
  homeWinProb?: number | null
}

/** Two teams, their (projected or final) scores and the win-probability bar. */
export function TwoTeamCard({
  context,
  away,
  home,
  awayScore,
  homeScore,
  neutral,
  homeWinProb,
}: Props) {
  const homeColor = teamColor(home, "dark")
  const awayColor =
    separation(homeColor, teamColor(away, "dark")) < 15 ? OG.muted : teamColor(away, "dark")
  return (
    <div
      style={{ display: "flex", flexDirection: "column", width: "100%", justifyContent: "center" }}
    >
      <div style={{ display: "flex", fontSize: 30, color: OG.muted }}>{context}</div>
      <div style={{ display: "flex", alignItems: "center", marginTop: 26 }}>
        <Side team={away} score={awayScore} />
        <div
          style={{
            display: "flex",
            width: 90,
            justifyContent: "center",
            fontSize: 34,
            color: OG.muted,
          }}
        >
          {neutral ? "vs" : "at"}
        </div>
        <Side team={home} score={homeScore} alignEnd />
      </div>
      {homeWinProb != null && (
        <div style={{ display: "flex", flexDirection: "column", marginTop: 30 }}>
          <div style={{ display: "flex", height: 18, borderRadius: 9, overflow: "hidden" }}>
            <div
              style={{
                display: "flex",
                width: `${(1 - homeWinProb) * 100}%`,
                background: awayColor,
              }}
            />
            <div style={{ display: "flex", flex: 1, background: homeColor }} />
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontSize: 28,
              color: OG.muted,
              marginTop: 8,
            }}
          >
            <div
              style={{ display: "flex" }}
            >{`${Math.round((1 - homeWinProb) * 100)}% to win`}</div>
            <div style={{ display: "flex" }}>{`${Math.round(homeWinProb * 100)}% to win`}</div>
          </div>
        </div>
      )}
    </div>
  )
}

function Side({
  team,
  score,
  alignEnd = false,
}: {
  team: TeamRef
  score: number | null | undefined
  alignEnd?: boolean
}) {
  return (
    <div
      style={{
        display: "flex",
        flex: 1,
        alignItems: "center",
        gap: 26,
        flexDirection: alignEnd ? "row-reverse" : "row",
      }}
    >
      <OgLogo src={team.logo_url} size={132} />
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: alignEnd ? "flex-end" : "flex-start",
          flex: 1,
        }}
      >
        <div
          style={{
            display: "flex",
            fontFamily: "Archivo Condensed",
            fontSize: team.school.length > 16 ? 46 : 58,
            lineHeight: 1.05,
            textAlign: alignEnd ? "right" : "left",
          }}
        >
          {team.school}
        </div>
        <div
          style={{ display: "flex", fontFamily: "Archivo Condensed", fontSize: 96, lineHeight: 1 }}
        >
          {score == null ? "–" : String(Math.round(score))}
        </div>
      </div>
    </div>
  )
}

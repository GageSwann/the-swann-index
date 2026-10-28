import { getTeam } from "@/lib/api/queries"
import { teamColor } from "@/lib/format/color"
import { record, signed } from "@/lib/format/numbers"
import { OG, OG_SIZE, OgLogo, ogImage } from "@/lib/og/frame"

export const alt = "A team's TSI ratings and ranks"
export const size = OG_SIZE
export const contentType = "image/png"

/** Team link preview: logo, team-color band, record, Power and Résumé ranks, rating. */
export default async function Image({ params }: { params: Promise<{ slug: string }> }) {
  const profile = await getTeam((await params).slug).catch(() => null)
  if (!profile) return ogImage(<Headline text="Team not found" />)
  const { team, ratings: r } = profile
  const stats = r
    ? [
        ["Power", r.rank_power ? `#${r.rank_power}` : "—"],
        ["Résumé", r.rank_resume ? `#${r.rank_resume}` : "—"],
        ["Rating", signed(r.rating)],
      ]
    : [["Rating", "FBS only"]]

  return ogImage(
    <div style={{ display: "flex", width: "100%", alignItems: "center", gap: 48 }}>
      <div
        style={{
          display: "flex",
          width: 14,
          height: 300,
          background: teamColor(team, "dark"),
          borderRadius: 7,
        }}
      />
      <OgLogo src={team.logo_url} size={240} />
      <div style={{ display: "flex", flexDirection: "column", flex: 1 }}>
        <div
          style={{ display: "flex", fontFamily: "Archivo Condensed", fontSize: 92, lineHeight: 1 }}
        >
          {team.school}
        </div>
        <div style={{ display: "flex", fontSize: 32, color: OG.muted, marginTop: 10 }}>
          {[
            team.conference,
            `${record(profile.wins, profile.losses, profile.ties)} in ${profile.season}`,
          ]
            .filter(Boolean)
            .join(" | ")}
        </div>
        <div style={{ display: "flex", gap: 48, marginTop: 34 }}>
          {stats.map(([label, value]) => (
            <div key={label} style={{ display: "flex", flexDirection: "column" }}>
              <div style={{ display: "flex", fontSize: 26, color: OG.muted }}>{label}</div>
              <div
                style={{
                  display: "flex",
                  fontFamily: "Archivo Condensed",
                  fontSize: 72,
                  color: label === "Power" ? OG.amber : OG.chalk,
                }}
              >
                {value}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>,
  )
}

function Headline({ text }: { text: string }) {
  return (
    <div style={{ display: "flex", fontFamily: "Archivo Condensed", fontSize: 80 }}>{text}</div>
  )
}

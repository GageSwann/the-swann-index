import { getRankings } from "@/lib/api/queries"
import { signed } from "@/lib/format/numbers"
import { Display, OG, OG_SIZE, OgLogo, ogImage } from "@/lib/og/frame"

// The site-wide link preview (pages without their own inherit it): the current Top 5.
export const alt = "The Swann Index: the current top five in the TSI Power rankings"
export const size = OG_SIZE
export const contentType = "image/png"

export default async function Image() {
  const rankings = await getRankings().catch(() => null)
  const top = rankings?.teams.slice(0, 5) ?? []
  return ogImage(
    <div style={{ display: "flex", width: "100%", gap: 56 }}>
      <div
        style={{ display: "flex", flexDirection: "column", width: 430, justifyContent: "center" }}
      >
        <Display size={76} style={{ lineHeight: 1 }}>
          Power rankings
        </Display>
        <div
          style={{ display: "flex", fontSize: 30, color: OG.muted, marginTop: 18, lineHeight: 1.3 }}
        >
          {rankings
            ? `Week ${rankings.week}, ${rankings.season}. Ratings from this season's games only.`
            : "College football ratings from this season's games only."}
        </div>
      </div>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          flex: 1,
          justifyContent: "center",
          gap: 10,
        }}
      >
        {top.map((t) => (
          <div
            key={t.team.slug}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 22,
              background: OG.sideline,
              borderRadius: 10,
              padding: "10px 22px",
            }}
          >
            <Display size={40} style={{ width: 44, color: OG.amber }}>
              {t.rank}
            </Display>
            <OgLogo src={t.team.logo_url} size={52} />
            <Display size={40} style={{ flex: 1 }}>
              {t.team.school}
            </Display>
            <div style={{ display: "flex", fontSize: 30, color: OG.muted }}>
              {t.wins}-{t.losses}
            </div>
            <Display size={36} style={{ width: 110, justifyContent: "flex-end" }}>
              {signed(t.rating)}
            </Display>
          </div>
        ))}
      </div>
    </div>,
  )
}

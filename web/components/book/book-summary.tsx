import type { LedgerRecord } from "@/lib/api/types"
import { percent, record, signed } from "@/lib/format/numbers"
import { MARKET_LABEL, units } from "@/lib/format/picks"
import { cn } from "@/lib/utils"

/**
 * The Book's season line: record, units (flat 1u and ¼ Kelly), ROI and closing-line value,
 * then one line per market. Every number comes from the API's graded picks.
 */
export function BookSummary({ records, open }: { records: LedgerRecord[]; open: number }) {
  const all = records.find((r) => r.market === "all" && r.tier === 0)
  const markets = records.filter((r) => r.market !== "all" && r.tier === 0)
  const graded = all ? all.wins + all.losses + all.pushes : 0

  return (
    <section aria-label="Season record" className="rounded-md border border-border bg-card p-5">
      {all && graded > 0 ? (
        <div className="space-y-5">
          <dl className="grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-4">
            <Stat label="Record" value={record(all.wins, all.losses, all.pushes)} />
            <Stat
              label="Units (1u flat)"
              value={units(all.units)}
              note={`¼ Kelly ${units(all.kelly_units)}`}
              tone={all.units}
            />
            <Stat label="ROI" value={signed(all.roi * 100) + "%"} tone={all.roi} />
            <Stat
              label="Closing-line value"
              value={all.clv == null ? "—" : `${signed(all.clv)} pts`}
              note={
                all.beat_close == null ? undefined : `beat the close ${percent(all.beat_close, 0)}`
              }
              tone={all.clv ?? 0}
            />
          </dl>
          {markets.length > 0 && (
            <ul className="flex flex-wrap gap-x-6 gap-y-1 border-t border-border pt-3 text-sm">
              {markets.map((m) => (
                <li key={m.market}>
                  <span className="text-muted-foreground">{MARKET_LABEL[m.market]}</span>{" "}
                  <span className="font-semibold">{record(m.wins, m.losses, m.pushes)}</span>,{" "}
                  {units(m.units)}
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : (
        <div className="space-y-1">
          <p className="text-2xl font-bold font-stretch-condensed">No graded picks yet</p>
          <p className="text-muted-foreground">
            {open > 0
              ? `${open} ${open === 1 ? "pick is" : "picks are"} waiting on games this week. `
              : ""}
            Picks are graded by the nightly run after their games finish.
          </p>
        </div>
      )}
    </section>
  )
}

function Stat({
  label,
  value,
  note,
  tone,
}: {
  label: string
  value: string
  note?: string
  tone?: number
}) {
  return (
    <div>
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd
        className={cn(
          "text-3xl font-bold font-stretch-condensed",
          tone !== undefined && tone > 0 && "text-up",
          tone !== undefined && tone < 0 && "text-down",
        )}
      >
        {value}
      </dd>
      {note && <dd className="text-sm text-muted-foreground">{note}</dd>}
    </div>
  )
}

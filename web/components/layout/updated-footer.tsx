import { getMeta } from "@/lib/api/queries"
import { formatUpdated } from "@/lib/format/time"

/** Every page: "Model updated {time} · TSI {version}" (doc 06). */
export async function UpdatedFooter() {
  const meta = await getMeta().catch(() => null)
  const updated = meta?.ratings_updated_at ? formatUpdated(meta.ratings_updated_at) : null

  return (
    <footer className="border-t border-border text-muted-foreground">
      <div className="mx-auto flex max-w-7xl flex-wrap items-baseline justify-between gap-2 px-4 py-5 text-sm sm:px-6">
        <p>
          {meta === null
            ? "Model status unavailable: the TSI API didn't respond."
            : `Model updated ${updated ?? "not yet this season"} · TSI ${meta.model_version}`}
        </p>
        <p>Ratings and predictions use only games played before kickoff.</p>
      </div>
    </footer>
  )
}

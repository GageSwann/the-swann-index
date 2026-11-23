import type { Division, DivisionView } from "@/lib/divisions"

/**
 * Every page address on the site, built in one place (#183): college football lives under
 * /cfb, so other sports (CBB, CBASE) can sit beside it. FBS is each section's default view;
 * the other divisions add a segment. The old unprefixed addresses redirect here
 * (`next.config.ts`).
 */
const CFB = "/cfb"

export const cfb = {
  home: CFB,
  rankings: (division: DivisionView = "fbs") =>
    division === "fbs" ? `${CFB}/rankings` : `${CFB}/rankings/${division}`,
  /** The board: no season means the current week. */
  schedule: (season?: number | string, week?: number | string, division: DivisionView = "fbs") =>
    season === undefined || week === undefined
      ? `${CFB}/schedule`
      : `${CFB}/schedule/${season}/${week}${division === "fbs" ? "" : `/${division}`}`,
  playoffs: (division: Division = "fbs") =>
    division === "fbs" ? `${CFB}/playoffs` : `${CFB}/playoffs/${division}`,
  /** A team page, optionally at one of its sections (`#resume`, `#projection`). */
  team: (slug: string, section?: string) => `${CFB}/teams/${slug}${section ? `#${section}` : ""}`,
  game: (id: number) => `${CFB}/games/${id}`,
}

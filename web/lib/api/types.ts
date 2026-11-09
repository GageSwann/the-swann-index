// Friendly names for the API's response types, generated from docs/api/openapi.json
// into ./schema.d.ts (`npm run api:types`). Never edit schema.d.ts by hand.
import type { components } from "./schema"

type Schemas = components["schemas"]

export type Meta = Schemas["Meta"]
export type Rankings = Schemas["Rankings"]
export type RankedTeam = Schemas["RankedTeam"]
export type TeamRef = Schemas["TeamRef"]
export type TeamProfile = Schemas["TeamProfile"]
export type RatingPoint = Schemas["RatingPoint"]
export type ScheduleGame = Schemas["ScheduleGame"]
export type WeekBoard = Schemas["WeekBoard"]
export type GameSummary = Schemas["GameSummary"]
export type GameCenter = Schemas["GameCenter"]
export type GamesOfWeek = Schemas["GamesOfWeek"]
export type GameOfWeekView = Schemas["GameOfWeekView"]
// TSI's chances and fair (no-vig) prices; the Book's prices are owner-only (#139).
export type FairMarkets = Schemas["FairMarkets"]
export type FairTwoWay = Schemas["FairTwoWay"]
export type SnapshotPoint = Schemas["SnapshotPoint"]
export type Playoff = Schemas["Playoff"]
export type PlayoffTeam = Schemas["PlayoffTeam"]
export type SnapshotView = Schemas["SnapshotView"]
export type AdjustmentNote = Schemas["AdjustmentNote"]

export type RankingType = "power" | "resume"
export type SeasonType = "regular" | "postseason"

// Friendly names for the API's response types, generated from docs/api/openapi.json
// into ./schema.d.ts (`npm run api:types`). Never edit schema.d.ts by hand.
import type { components } from "./schema"

type Schemas = components["schemas"]

export type Meta = Schemas["Meta"]
export type Rankings = Schemas["Rankings"]
export type RankedTeam = Schemas["RankedTeam"]
export type TeamRef = Schemas["TeamRef"]
export type TeamProfile = Schemas["TeamProfile"]
export type TeamRatings = Schemas["TeamRatings"]
export type RatingPoint = Schemas["RatingPoint"]
export type ScheduleGame = Schemas["ScheduleGame"]
export type WeekBoard = Schemas["WeekBoard"]
export type GameSummary = Schemas["GameSummary"]
export type GameCenter = Schemas["GameCenter"]
export type GameMarkets = Schemas["GameMarkets"]
export type TwoWay = Schemas["TwoWay"]
export type Price = Schemas["Price"]
export type SnapshotView = Schemas["SnapshotView"]
export type SnapshotPoint = Schemas["SnapshotPoint"]
export type PickView = Schemas["PickView"]
export type ConsensusLine = Schemas["ConsensusLine"]
export type Score = Schemas["Score"]
export type Ledger = Schemas["Ledger"]
export type LedgerPick = Schemas["LedgerPick"]
export type LedgerRecord = Schemas["LedgerRecord"]
export type UnitsPoint = Schemas["UnitsPoint"]
export type ModelReport = Schemas["ModelReport"]
export type Matchup = Schemas["Matchup"]

export type RankingType = "power" | "resume"
export type SeasonType = "regular" | "postseason"

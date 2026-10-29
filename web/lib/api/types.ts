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
export type GameMarkets = Schemas["GameMarkets"]
export type TwoWay = Schemas["TwoWay"]
export type SnapshotPoint = Schemas["SnapshotPoint"]
export type PickView = Schemas["PickView"]
export type Ledger = Schemas["Ledger"]
export type LedgerPick = Schemas["LedgerPick"]
export type LedgerRecord = Schemas["LedgerRecord"]
export type UnitsPoint = Schemas["UnitsPoint"]
export type ModelReport = Schemas["ModelReport"]
export type Matchup = Schemas["Matchup"]
export type Playoff = Schemas["Playoff"]
export type PlayoffTeam = Schemas["PlayoffTeam"]
export type BracketFormat = Schemas["BracketFormat"]

export type RankingType = "power" | "resume"
export type SeasonType = "regular" | "postseason"
export type AccuracyRow = Schemas["AccuracyRow"]
export type CalibrationBin = Schemas["CalibrationBin"]
export type AtsRow = Schemas["AtsRow"]
export type TotalsRow = Schemas["TotalsRow"]
export type BookBacktestRow = Schemas["BookBacktestRow"]
export type BookUnitsPoint = Schemas["BookUnitsPoint"]
export type LiveAccuracy = Schemas["LiveAccuracy"]
export type ModelVersion = Schemas["ModelVersion"]

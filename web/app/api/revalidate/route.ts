import { createHash, timingSafeEqual } from "node:crypto"

import { revalidateTag } from "next/cache"
import type { NextRequest } from "next/server"

import * as tags from "@/lib/api/tags"

/**
 * Called by the nightly job after `tsi run` (doc 02, "Caching & revalidation"):
 * `POST /api/revalidate` with `Authorization: Bearer <REVALIDATE_TOKEN>`. Expires every
 * TSI read at once (`expire: 0`, Phase 12.2): the next visit to any page waits for fresh
 * data (~1 s for a team page) instead of getting yesterday's page while the new one builds
 * in the background, which is what `"max"` did and why unvisited team pages kept old
 * schedules. The nightly job then pre-visits the main pages so most readers never wait.
 */
export async function POST(request: NextRequest) {
  const expected = process.env.REVALIDATE_TOKEN
  if (!expected) {
    return Response.json({ error: "Revalidation isn't configured." }, { status: 503 })
  }
  const header = request.headers.get("authorization") ?? ""
  const token = header.startsWith("Bearer ") ? header.slice("Bearer ".length) : ""
  if (!sameSecret(token, expected)) {
    return Response.json({ error: "Unauthorized" }, { status: 401 })
  }
  revalidateTag(tags.ALL, { expire: 0 })
  return Response.json({ revalidated: tags.ALL, at: new Date().toISOString() })
}

/** Constant-time comparison (hashing first makes the lengths equal). */
function sameSecret(given: string, expected: string): boolean {
  const digest = (value: string) => createHash("sha256").update(value).digest()
  return given.length > 0 && timingSafeEqual(digest(given), digest(expected))
}

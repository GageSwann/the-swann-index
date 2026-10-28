import { createHash, timingSafeEqual } from "node:crypto"

import { revalidateTag } from "next/cache"
import type { NextRequest } from "next/server"

import * as tags from "@/lib/api/tags"

/**
 * Called by the nightly job after `tsi run` (doc 02, "Caching & revalidation"):
 * `POST /api/revalidate` with `Authorization: Bearer <REVALIDATE_TOKEN>`. Marks every
 * TSI read stale ("max": the next visit gets the cached page instantly while fresh data
 * loads), so the site shows the new ratings and predictions without a rebuild.
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
  revalidateTag(tags.ALL, "max")
  return Response.json({ revalidated: tags.ALL, at: new Date().toISOString() })
}

/** Constant-time comparison (hashing first makes the lengths equal). */
function sameSecret(given: string, expected: string): boolean {
  const digest = (value: string) => createHash("sha256").update(value).digest()
  return given.length > 0 && timingSafeEqual(digest(given), digest(expected))
}

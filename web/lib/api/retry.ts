import "server-only"

// The API runs on Render's free tier: under a burst (a site build prerenders ~100 pages)
// or while it wakes, a request can fail once and succeed a moment later, and Render
// answers a burst with 429 (too many requests). Every API call is a read-only GET, so
// retrying is safe; any other 4xx (404 = unknown team) is an answer.
const RETRIES = 3
const BACKOFF_MS = 400 // then 800, 1600
const MAX_WAIT_MS = 5000 // cap on a server-requested Retry-After
const TRANSIENT = new Set([429, 500, 502, 503, 504])

/** `fetch` for openapi-fetch: retries transient failures (429, 5xx, network errors). */
export async function fetchWithRetry(request: Request): Promise<Response> {
  for (let attempt = 0; ; attempt++) {
    const last = attempt === RETRIES
    let wait = BACKOFF_MS * 2 ** attempt
    try {
      const response = await fetch(request.clone())
      if (last || !TRANSIENT.has(response.status)) return response
      wait = retryAfterMs(response) ?? wait
    } catch (error) {
      if (last) throw error
    }
    await new Promise((resolve) => setTimeout(resolve, wait))
  }
}

/** The server's Retry-After (seconds form), capped; null when absent or unparsable. */
function retryAfterMs(response: Response): number | null {
  const seconds = Number(response.headers.get("retry-after"))
  if (!Number.isFinite(seconds) || seconds <= 0) return null
  return Math.min(seconds * 1000, MAX_WAIT_MS)
}

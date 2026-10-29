import "server-only"

// The API runs on Render's free tier: under a burst (a site build prerenders ~100 pages)
// or while it wakes, a request can fail once and succeed a moment later. Every API call
// is a read-only GET, so retrying is safe; a 4xx (404 = unknown team) is an answer.
const RETRIES = 2
const BACKOFF_MS = 400 // then 800
const TRANSIENT = new Set([500, 502, 503, 504])

/** `fetch` for openapi-fetch: retries transient failures (5xx, network errors). */
export async function fetchWithRetry(request: Request): Promise<Response> {
  for (let attempt = 0; ; attempt++) {
    const last = attempt === RETRIES
    try {
      const response = await fetch(request.clone())
      if (last || !TRANSIENT.has(response.status)) return response
    } catch (error) {
      if (last) throw error
    }
    await new Promise((resolve) => setTimeout(resolve, BACKOFF_MS * 2 ** attempt))
  }
}

import "server-only"

import createClient from "openapi-fetch"

import type { paths } from "./schema"

/** The TSI API is read on the server only; its URL is never shipped to the browser. */
export function apiClient() {
  const baseUrl = process.env.TSI_API_URL
  if (!baseUrl) {
    throw new Error("TSI_API_URL is not set (copy web/.env.example to web/.env.local).")
  }
  return createClient<paths>({ baseUrl })
}

export class ApiError extends Error {
  constructor(
    readonly path: string,
    readonly status: number,
  ) {
    super(`TSI API ${path} returned ${status}`)
    this.name = "ApiError"
  }
}

type Result<T> = { data?: T; error?: unknown; response: Response }

/** The response body; `null` for 404 (unknown team/game, no rankings yet); throws otherwise. */
export function orNull<T>(path: string, result: Result<T>): T | null {
  if (result.response.status === 404) return null
  if (result.data === undefined) throw new ApiError(path, result.response.status)
  return result.data
}

/** The response body; throws on any error (for endpoints that always exist). */
export function required<T>(path: string, result: Result<T>): T {
  const data = orNull(path, result)
  if (data === null) throw new ApiError(path, 404)
  return data
}

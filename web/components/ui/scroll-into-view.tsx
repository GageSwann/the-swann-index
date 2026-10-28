"use client"

import { useEffect } from "react"

/**
 * Scrolls to `id` when the URL's hash names it. Needed for links like
 * `/teams/auburn#resume`: the section streams in after navigation, when the browser's
 * own jump to the hash has already happened.
 */
export function ScrollIntoView({ id }: { id: string }) {
  useEffect(() => {
    if (window.location.hash === `#${id}`) {
      document.getElementById(id)?.scrollIntoView({ block: "start" })
    }
  }, [id])
  return null
}

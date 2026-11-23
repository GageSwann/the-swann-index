import type { Metadata, Viewport } from "next"
import { Instrument_Sans } from "next/font/google"

import { SiteHeader } from "@/components/layout/site-header"
import { ThemeProvider } from "@/components/layout/theme-provider"
import { BottomNav } from "@/components/layout/bottom-nav"
import { SiteFooter } from "@/components/layout/site-footer"
import { ThemeColor } from "@/components/layout/theme-color"
import { ALLOW_INDEXING, SITE_NAME, SITE_URL } from "@/lib/site"

import "./globals.css"

// One family, two voices (decision #137): condensed widths for broadcast-style names
// and numerals, normal width for reading. Variable font with the width axis (75-100);
// its tabular figures are plain (no slashed zero), and weights run 400-700.
const instrument = Instrument_Sans({
  variable: "--font-instrument",
  subsets: ["latin"],
  axes: ["wdth"],
})

const DESCRIPTION =
  "College football power rankings, game predictions and betting lines from the TSI model."

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: SITE_NAME, template: `%s | ${SITE_NAME}` },
  description: DESCRIPTION,
  openGraph: {
    siteName: SITE_NAME,
    title: SITE_NAME,
    description: DESCRIPTION,
    type: "website",
    locale: "en_US",
  },
  twitter: { card: "summary_large_image", title: SITE_NAME, description: DESCRIPTION },
  // Opened from an iPhone's Home Screen: full screen, the page drawn behind a transparent
  // status bar (the header pads by the safe-area inset), no separate bar above it (#165).
  appleWebApp: { capable: true, statusBarStyle: "black-translucent", title: SITE_NAME },
  // Search engines stay out until ALLOW_INDEXING=1 (decision #86); link previews still work.
  robots: ALLOW_INDEXING ? undefined : { index: false, follow: false },
}

// Edge to edge on every iPhone (owner, 2026-11-23, #165): the page draws under the status
// bar and the home indicator, and the header, bottom bar and sides pad themselves by the
// safe-area insets (0 on phones without a notch or island). theme-color tints the browser's
// own bars; ThemeColor keeps it in step with the light/dark toggle.
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#252526",
}

export default function RootLayout({ children }: LayoutProps<"/">) {
  // The body is the header's panel color: Safari paints the strip behind an iPhone's clock
  // and battery with the body's background (#174). The page color starts below the header,
  // on the wrapper around the content and footer.
  return (
    <html lang="en" className={`${instrument.variable} dark h-full`} suppressHydrationWarning>
      <body className="flex min-h-full flex-col bg-card pb-[calc(4rem+env(safe-area-inset-bottom))] antialiased sm:pb-0">
        <ThemeProvider>
          <a
            href="#main"
            className="sr-only z-50 rounded-sm bg-primary px-3 py-2 text-primary-foreground focus:not-sr-only focus:absolute focus:top-2 focus:left-2"
          >
            Skip to content
          </a>
          <ThemeColor />
          <SiteHeader />
          {/* At least a screen tall: content that streams in (Suspense) can't push a visible
              footer around, which Lighthouse counts as layout shift (decision #87). */}
          <div className="flex flex-1 flex-col bg-background">
            <main id="main" className="tsi-safe-x mx-auto min-h-svh w-full max-w-7xl flex-1 py-8">
              {children}
            </main>
            <SiteFooter />
          </div>
          <BottomNav />
        </ThemeProvider>
      </body>
    </html>
  )
}

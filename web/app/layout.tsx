import type { Metadata } from "next"
import { Archivo } from "next/font/google"

import { SiteHeader } from "@/components/layout/site-header"
import { ThemeProvider } from "@/components/layout/theme-provider"
import { UpdatedFooter } from "@/components/layout/updated-footer"
import { ALLOW_INDEXING, SITE_NAME, SITE_URL } from "@/lib/site"

import "./globals.css"

// One family, two voices: condensed widths for broadcast-style names and numerals,
// normal width for reading. Variable font with the width axis.
const archivo = Archivo({
  variable: "--font-archivo",
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
  // Search engines stay out until ALLOW_INDEXING=1 (decision #86); link previews still work.
  robots: ALLOW_INDEXING ? undefined : { index: false, follow: false },
}

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${archivo.variable} dark h-full`} suppressHydrationWarning>
      <body className="flex min-h-full flex-col antialiased">
        <ThemeProvider>
          <a
            href="#main"
            className="sr-only z-50 rounded-sm bg-primary px-3 py-2 text-primary-foreground focus:not-sr-only focus:absolute focus:top-2 focus:left-2"
          >
            Skip to content
          </a>
          <SiteHeader />
          {/* At least a screen tall: content that streams in (Suspense) can't push a visible
              footer around, which Lighthouse counts as layout shift (decision #87). */}
          <main id="main" className="mx-auto min-h-svh w-full max-w-7xl flex-1 px-4 py-8 sm:px-6">
            {children}
          </main>
          <UpdatedFooter />
        </ThemeProvider>
      </body>
    </html>
  )
}

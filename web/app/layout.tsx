import type { Metadata } from "next"
import { Archivo } from "next/font/google"

import { SiteHeader } from "@/components/layout/site-header"
import { ThemeProvider } from "@/components/layout/theme-provider"
import { UpdatedFooter } from "@/components/layout/updated-footer"

import "./globals.css"

// One family, two voices: condensed widths for broadcast-style names and numerals,
// normal width for reading. Variable font with the width axis.
const archivo = Archivo({
  variable: "--font-archivo",
  subsets: ["latin"],
  axes: ["wdth"],
})

export const metadata: Metadata = {
  title: { default: "The Swann Index", template: "%s | The Swann Index" },
  description:
    "College football power rankings, game predictions and betting lines from the TSI model.",
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
          <main id="main" className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">
            {children}
          </main>
          <UpdatedFooter />
        </ThemeProvider>
      </body>
    </html>
  )
}

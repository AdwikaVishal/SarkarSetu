import type { Metadata, Viewport } from "next";
import { Inter, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { APIProvider } from "@/context/APIProvider";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "SarkarSetu AI — Government Services Simplified for Indian Entrepreneurs",
  description: "From business registration to government schemes, SarkarSetu AI helps Indian entrepreneurs discover opportunities, understand requirements, and complete essential compliance tasks — all in one place.",
  keywords: ["government services", "business registration", "MSME", "Udyam", "GST", "government schemes", "entrepreneurs", "startups", "India"],
  authors: [{ name: "SarkarSetu AI" }],
  creator: "SarkarSetu AI",
  publisher: "SarkarSetu AI",
  robots: "index, follow",
  openGraph: {
    type: "website",
    locale: "en_IN",
    url: "https://sarkarsetu.ai",
    title: "SarkarSetu AI — Government Services Simplified",
    description: "From business registration to government schemes, SarkarSetu AI helps Indian entrepreneurs discover opportunities, understand requirements, and complete essential compliance tasks.",
    siteName: "SarkarSetu AI",
  },
  twitter: {
    card: "summary_large_image",
    title: "SarkarSetu AI — Government Services Simplified",
    description: "From business registration to government schemes, SarkarSetu AI helps Indian entrepreneurs discover opportunities, understand requirements, and complete essential compliance tasks.",
  },
  verification: {
    google: "google-site-verification-code",
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#FAFAF7" },
    { media: "(prefers-color-scheme: dark)", color: "#101010" },
  ],
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${spaceGrotesk.variable} h-full antialiased`}
      data-scroll-behavior="smooth"
    >
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="min-h-full flex flex-col bg-bg-primary text-text-primary">
        <APIProvider>
          <AuthProvider>
            {children}
          </AuthProvider>
        </APIProvider>
      </body>
    </html>
  );
}
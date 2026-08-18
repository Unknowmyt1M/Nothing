import { Outfit, JetBrains_Mono } from 'next/font/google';
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import ErrorBoundary from "@/components/ErrorBoundary";

const outfit = Outfit({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700', '800'],
  variable: '--font-outfit',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-jetbrains',
  display: 'swap',
});

export const metadata = {
  title: "UpDownVid - Futuristic Video Downloader & YouTube Uploader",
  description: "Extract video metadata and download from YouTube, Instagram, TikTok, Facebook in high quality, or auto-upload to YouTube directly.",
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  themeColor: '#060512',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning className={`${outfit.variable} ${jetbrainsMono.variable}`}>
      <body>
        <ErrorBoundary>
          <Sidebar />
          <main className="main-content">
            {children}
          </main>
        </ErrorBoundary>
      </body>
    </html>
  );
}

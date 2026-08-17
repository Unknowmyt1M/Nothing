import "./globals.css";
import Sidebar from "@/components/Sidebar";

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
    <html lang="en" suppressHydrationWarning>
      <body>
        <Sidebar />
        <main className="main-content">
          {children}
        </main>
      </body>
    </html>
  );
}

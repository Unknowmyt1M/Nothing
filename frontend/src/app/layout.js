import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata = {
  title: "UpDownVid - Futuristic Video Downloader & YouTube Uploader",
  description: "Extract video metadata and download from YouTube, Instagram, TikTok, Facebook in high quality, or auto-upload to YouTube directly.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <div style={{ display: "flex", minHeight: "100vh" }}>
          {/* Futuristic Sidebar component */}
          <Sidebar />
          
          {/* Main Content Area */}
          <main style={{ 
            flex: 1, 
            padding: "40px", 
            marginLeft: "280px", 
            minHeight: "100vh",
            display: "flex",
            flexDirection: "column"
          }}>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}

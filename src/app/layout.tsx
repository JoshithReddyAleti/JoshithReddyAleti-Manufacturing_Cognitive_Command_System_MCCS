import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MCCS - Manufacturing Cognitive Command System",
  description: "Real-time disruption intelligence & autonomous replanning",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}

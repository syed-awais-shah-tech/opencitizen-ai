import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OpenCitizen AI - Evidence-Grounded Civic Intelligence",
  description: "Question municipal documents, analyze civic datasets, and inspect the exact source citations and DuckDB calculations behind every answer.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="ambient-glow" />
        {children}
      </body>
    </html>
  );
}

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OpenCitizen AI — Get Answers from Your City's Documents",
  description: "Upload city documents and data, ask questions in plain English, and get verified answers with source citations.",
};

import AppLayout from "./components/AppLayout";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="ambient-glow" />
        <AppLayout>{children}</AppLayout>
      </body>
    </html>
  );
}

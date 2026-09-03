import "./globals.css";
import React from "react";
import { Header } from "@/components/Header";

export const metadata = {
  title: "CosmoHub — Intelligence Engine",
  description: "Grounded Space Economy Intelligence Infrastructure & AI Research Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0a0d12] text-[#eceff3] min-h-screen flex flex-col font-sans">
        <Header />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <footer className="border-t border-[#232838] py-6 text-center text-xs font-mono text-[#8891a3]">
          COSMOHUB INTELLIGENCE ENGINE V1 • SPACE ECONOMY KNOWLEDGE INFRASTRUCTURE
        </footer>
      </body>
    </html>
  );
}

import type { Metadata, Viewport } from "next";
import { GeistMono } from "geist/font/mono";
import { GeistSans } from "geist/font/sans";
import { cn } from "@/lib/utils";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Mathey", template: "%s · Mathey" },
  description:
    "Un mentor de matemàtiques que viu dins d'una placa Arduino, a l'aula i sense internet.",
};

export const viewport: Viewport = {
  themeColor: "#f0f1f0",
};

// Fonts locals (paquet `geist`, next/font/local): la web funciona amb el Wi-Fi apagat.
export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ca" className={cn("h-full", GeistSans.variable, GeistMono.variable)}>
      <body className="flex min-h-full flex-col font-sans">
        <div className="flex flex-1 flex-col">{children}</div>
      </body>
    </html>
  );
}

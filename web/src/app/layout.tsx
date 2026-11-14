import type { Metadata } from "next";
import Header from "@/components/Header";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mentor Cangur",
  description: "Un mentor de matemàtiques que viu dins d'una placa Arduino, sense internet.",
};

// Sense fonts remotes: la web ha de funcionar amb el Wi-Fi apagat.
export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ca" className="h-full antialiased">
      <body className="flex min-h-full flex-col bg-amber-50/40 dark:bg-zinc-950">
        <Header />
        <div className="flex flex-1 flex-col">{children}</div>
      </body>
    </html>
  );
}

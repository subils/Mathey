import type { Metadata } from "next";
import { AppBar } from "@/components/app/app-bar";

export const metadata: Metadata = { title: "Practica" };

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-svh flex-col">
      <AppBar />
      <div className="flex flex-1 flex-col animate-page-enter">{children}</div>
    </div>
  );
}

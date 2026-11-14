"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type Health } from "@/lib/api";

const LINKS = [
  { href: "/practica/", label: "Practica" },
  { href: "/el-meu-problema/", label: "El meu problema" },
  { href: "/perfil/", label: "El meu progrés" },
  { href: "/mestre/", label: "Mestre" },
  { href: "/placa/", label: "La placa" },
];

export default function Header() {
  const pathname = usePathname();
  const [health, setHealth] = useState<Health | null>(null);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    let alive = true;
    const load = () =>
      api
        .health()
        .then((h) => alive && (setHealth(h), setOffline(false)))
        .catch(() => alive && setOffline(true));
    load();
    const timer = setInterval(load, 15000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);

  return (
    <header className="border-b border-zinc-200 bg-white/80 backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/80">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <Link href="/" className="flex items-center gap-2 text-lg font-semibold tracking-tight">
          <span aria-hidden className="text-2xl">🦘</span> Mathey
        </Link>
        <nav className="flex gap-1 text-sm">
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`rounded-full px-3 py-1.5 transition-colors ${
                pathname?.startsWith(link.href.replace(/\/$/, ""))
                  ? "bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-100"
                  : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-900"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-2 text-xs text-zinc-500" title="Estat de la placa">
          <span className={`h-2 w-2 rounded-full ${offline ? "bg-red-500" : health ? "bg-emerald-500" : "bg-zinc-400"}`} />
          {offline
            ? "Sense connexió amb la placa"
            : health
              ? `Sense internet · ${health.host} · IA ${health.llm === "up" ? "activa" : "no disponible"}`
              : "Connectant…"}
        </div>
      </div>
    </header>
  );
}

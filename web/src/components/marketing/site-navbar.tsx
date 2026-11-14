"use client";

import { ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { NavLogo } from "@/components/brand/nav-logo";
import { cn } from "@/lib/utils";

// Rutes absolutes (`/#id`): des de /placa/ també porten a la secció de la landing.
const NAV_LINKS = [
  { href: "/#com-funciona", label: "Com funciona" },
  { href: "/#modes", label: "Modes" },
  { href: "/#placa", label: "La placa" },
];

const EASE = "ease-[cubic-bezier(0.16,1,0.3,1)]";

/**
 * El navbar de Faktu (components/marketing/site-navbar.tsx): píndola de vidre
 * flotant, enllaços centrats amb una píndola de fons en passar el cursor, i dos
 * botons a la dreta. Damunt del hero fosc (el de resend.com) la tinta és blanca i
 * el vidre és el de Faktu sobre el vídeo (`.on-dark`); en passar el hero, tinta
 * fosca i vidre clar (`.scrolled`). Els mateixos jocs de colors que Faktu.
 */
export function SiteNavbar() {
  const pathname = usePathname();
  const hasHero = pathname === "/";
  // A /placa/ no té sentit un botó que porta a /placa/
  const onPlaca = pathname?.startsWith("/placa") ?? false;
  const [heroVisible, setHeroVisible] = useState(true);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!hasHero) return;
    const hero = document.getElementById("hero");
    if (!hero) return;
    const io = new IntersectionObserver(([entry]) => setHeroVisible(entry.isIntersecting), {
      rootMargin: "-80px 0px 0px 0px",
    });
    io.observe(hero);
    return () => io.disconnect();
  }, [hasHero]);

  const overHero = hasHero && heroVisible;
  // Faktu (site-navbar.tsx): els colors canvien segons si és damunt del hero
  const ink = overHero ? "text-white" : "text-[#1c1c1d]";
  const linkHover = overHero ? "before:bg-white/20" : "before:bg-black/[0.06]";
  const ghostBtn = overHero ? "bg-white/10 text-white hover:bg-white/20" : "bg-black/5 text-[#1c1c1d] hover:bg-black/10";
  const solidBtn = overHero ? "bg-white text-[#1c1c1d] hover:bg-white/90" : "bg-[#1c1c1d] text-white hover:opacity-90";

  return (
    <header className="fixed inset-x-0 top-0 z-50 pt-4 md:pt-6">
      <div className="relative mx-auto max-w-5xl px-4 md:px-6">
        <nav
          className={cn(
            "navbar-glass relative flex h-[52px] items-center justify-between px-2 md:px-3",
            overHero ? "on-dark" : "scrolled",
          )}
        >
          <NavLogo className={cn("transition-colors", ink)} />

          <div className="absolute top-1/2 left-1/2 hidden -translate-x-1/2 -translate-y-1/2 items-center gap-5 md:flex">
            {NAV_LINKS.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className={cn(
                  "relative text-[14px] font-medium transition-colors before:pointer-events-none before:absolute before:-inset-x-2 before:-inset-y-1.5 before:rounded-lg before:opacity-0 before:transition-opacity before:content-[''] hover:before:opacity-100",
                  ink,
                  linkHover,
                )}
              >
                {l.label}
              </Link>
            ))}
          </div>

          <div className="flex items-center gap-2.5">
            {!onPlaca && (
              <Link
                href="/placa/"
                className={cn("hidden items-center rounded-lg px-3.5 py-1.5 text-[14px] font-medium transition-colors md:inline-flex", ghostBtn)}
              >
                Veure la placa
              </Link>
            )}
            <Link
              href="/app/"
              className={cn("hidden items-center gap-1 rounded-lg px-3.5 py-1.5 text-[14px] font-medium transition-colors md:inline-flex", solidBtn)}
            >
              Comença <ArrowUpRight className="size-3.5" />
            </Link>
            <button
              type="button"
              aria-label={open ? "Tanca el menú" : "Obre el menú"}
              aria-expanded={open}
              onClick={() => setOpen((o) => !o)}
              className={cn("ml-1 flex size-8 flex-col items-center justify-center gap-[5px] md:hidden", ink)}
            >
              <span className={cn("block h-[1.5px] w-5 origin-center bg-current transition-all duration-150", EASE, open && "translate-y-[6.5px] rotate-45")} />
              <span className={cn("block h-[1.5px] w-5 bg-current transition-all duration-150", EASE, open && "opacity-0")} />
              <span className={cn("block h-[1.5px] w-5 origin-center bg-current transition-all duration-150", EASE, open && "-translate-y-[6.5px] -rotate-45")} />
            </button>
          </div>
        </nav>

        {/* Menú mòbil: sempre muntat perquè també s'animi en tancar */}
        <div className={cn("grid overflow-hidden transition-[grid-template-rows] duration-200 md:hidden", EASE, open ? "grid-rows-[1fr]" : "grid-rows-[0fr]")}>
          <div className="min-h-0 overflow-hidden">
            <div
              className={cn(
                "navbar-glass scrolled mt-2 flex origin-top flex-col gap-4 rounded-2xl px-5 py-5 transition-all duration-200",
                EASE,
                open ? "translate-y-0 scale-100 opacity-100" : "-translate-y-1 scale-[0.97] opacity-0",
              )}
            >
              {NAV_LINKS.map((l) => (
                <Link key={l.href} href={l.href} onClick={() => setOpen(false)} className="text-[15px] font-medium text-[#1c1c1d]">
                  {l.label}
                </Link>
              ))}
              <div className="flex gap-3 border-t border-black/[0.08] pt-3">
                <Link href="/app/" className="flex-1 rounded-lg bg-[#1c1c1d] px-4 py-2.5 text-center text-sm font-medium text-white">
                  Comença
                </Link>
                {!onPlaca && (
                  <Link href="/placa/" className="flex-1 rounded-lg bg-black/[0.06] px-4 py-2.5 text-center text-sm font-medium text-[#1c1c1d]">
                    La placa
                  </Link>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

"use client";

import { ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Logo } from "@/components/brand/logo";
import { cn } from "@/lib/utils";

// Rutes absolutes (`/#id`): des de /mestre/ o /placa/ també porten a la secció de la landing.
const NAV_LINKS = [
  { href: "/#com-funciona", label: "Com funciona" },
  { href: "/#modes", label: "Modes" },
  { href: "/#placa", label: "La placa" },
  { href: "/#mestre", label: "Mestre" },
];

const EASE = "ease-[cubic-bezier(0.16,1,0.3,1)]";

/**
 * El navbar de Faktu (components/marketing/site-navbar.tsx): píndola de vidre
 * flotant, enllaços centrats amb una píndola de fons en passar el cursor, i dos
 * botons a la dreta. Damunt del hero clar de Mathey la tinta és sempre fosca; en
 * passar el hero, el vidre guanya opacitat (`.scrolled`).
 */
export function SiteNavbar() {
  const pathname = usePathname();
  const hasHero = pathname === "/";
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

  return (
    <header className="fixed inset-x-0 top-0 z-50 pt-4 md:pt-6">
      <div className="relative mx-auto max-w-5xl px-4 md:px-6">
        <nav
          className={cn(
            "navbar-glass relative flex h-[52px] items-center justify-between px-2 md:px-3",
            !overHero && "scrolled",
          )}
        >
          <Link href="/" className="flex shrink-0 items-center px-1.5 text-[#1c1c1d]" aria-label="Mathey, inici">
            <Logo className="h-[22px]" />
          </Link>

          <div className="absolute top-1/2 left-1/2 hidden -translate-x-1/2 -translate-y-1/2 items-center gap-5 md:flex">
            {NAV_LINKS.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className="relative text-[14px] font-medium text-[#1c1c1d] transition-colors before:pointer-events-none before:absolute before:-inset-x-2 before:-inset-y-1.5 before:rounded-lg before:bg-black/[0.06] before:opacity-0 before:transition-opacity before:content-[''] hover:before:opacity-100"
              >
                {l.label}
              </Link>
            ))}
          </div>

          <div className="flex items-center gap-2.5">
            <Link
              href="/placa/"
              className="hidden items-center rounded-lg bg-black/5 px-3.5 py-1.5 text-[14px] font-medium text-[#1c1c1d] transition-colors hover:bg-black/10 md:inline-flex"
            >
              Veure la placa
            </Link>
            <Link
              href="/app/"
              className="hidden items-center gap-1 rounded-lg bg-[#1c1c1d] px-3.5 py-1.5 text-[14px] font-medium text-white transition-opacity hover:opacity-90 md:inline-flex"
            >
              Comença <ArrowUpRight className="size-3.5" />
            </Link>
            <button
              type="button"
              aria-label={open ? "Tanca el menú" : "Obre el menú"}
              aria-expanded={open}
              onClick={() => setOpen((o) => !o)}
              className="ml-1 flex size-8 flex-col items-center justify-center gap-[5px] text-[#1c1c1d] md:hidden"
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
                <Link href="/placa/" className="flex-1 rounded-lg bg-black/[0.06] px-4 py-2.5 text-center text-sm font-medium text-[#1c1c1d]">
                  La placa
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

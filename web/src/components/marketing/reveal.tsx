"use client";

import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";

/** useLayoutEffect al navegador (abans de pintar); res al servidor. */
const useBrowserLayoutEffect = typeof window === "undefined" ? useEffect : useLayoutEffect;

/**
 * Revela el contingut amb un fos + pujada + desenfocament (com Faktu), però
 * sense dependre del JavaScript per veure'l:
 *
 * - `immediate` (el hero): animació només de CSS en carregar. Funciona encara
 *   que el JavaScript no arrenqui.
 * - Per defecte: l'HTML surt visible. En hidratar, només s'amaguen els blocs
 *   que encara són sota la pantalla; reapareixen en entrar-hi
 *   (IntersectionObserver) i, per si de cas, al cap de 2,5 s.
 */
export function Reveal({
  children,
  className,
  delay = 0,
  immediate = false,
}: {
  children?: ReactNode;
  className?: string;
  delay?: number;
  immediate?: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [hidden, setHidden] = useState(false);

  useBrowserLayoutEffect(() => {
    if (immediate) return;
    const el = ref.current;
    if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    // Ja és a la pantalla: es deixa tal com està (sense parpelleig)
    if (el.getBoundingClientRect().top < window.innerHeight * 0.92) return;
    setHidden(true);
    const show = () => setHidden(false);
    const io = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          show();
          io.disconnect();
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -8% 0px" },
    );
    io.observe(el);
    const safety = window.setTimeout(show, 2500);
    return () => {
      io.disconnect();
      window.clearTimeout(safety);
    };
  }, [immediate]);

  if (immediate) {
    return (
      <div className={cn("reveal-in", className)} style={{ animationDelay: `${delay}ms` }}>
        {children}
      </div>
    );
  }

  return (
    <div
      ref={ref}
      style={{ transitionDelay: hidden ? "0ms" : `${delay}ms` }}
      className={cn(
        "transition-[opacity,transform,filter] duration-700 ease-out",
        hidden ? "translate-y-6 opacity-0 blur-[3px]" : "translate-y-0 opacity-100 blur-0",
        className,
      )}
    >
      {children}
    </div>
  );
}

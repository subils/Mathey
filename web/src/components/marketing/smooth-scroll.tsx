"use client";

import Lenis from "lenis";
import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";

// El smooth scroll de Faktu (components/smooth-scroll.tsx), amb Lenis.
// Només a les pàgines públiques (landing, /placa/): l'app té els seus propis
// contenidors amb scroll (el xat) i no el fa servir.

/** Alçada aproximada del navbar fix, perquè la secció de destí no quedi tapada. */
const NAVBAR_OFFSET = 96;

/** Més ràpid que el scroll de roda: és un clic deliberat (menú, logo, àncora). */
const CLICK_SCROLL_OPTS = {
  duration: 0.8,
  easing: (t: number) => 1 - Math.pow(1 - t, 3),
};

/** `"#id"` o `"/#id"` → el hash; si no és un enllaç a una secció, null. */
function sectionHash(href: string): string | null {
  if (href.startsWith("#") && href !== "#") return href;
  if (href.startsWith("/#") && href !== "/#") return href.slice(1);
  return null;
}

/**
 * Suavitza el scroll de roda i trackpad. Mou el scroll natiu de la finestra
 * amb requestAnimationFrame, així que IntersectionObserver (Reveal, navbar)
 * continua funcionant. També intercepta els enllaços a seccions perquè el
 * salt sigui animat per Lenis, i el logo a «/» puja a dalt de tot.
 * Respecta prefers-reduced-motion. No pinta res.
 */
export function SmoothScroll() {
  const pathname = usePathname();
  const lenisRef = useRef<Lenis | null>(null);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const lenis = new Lenis({
      duration: 1.1,
      // easeOutExpo: arrencada àgil i frenada llarga i suau
      easing: (t) => (t === 1 ? 1 : 1 - Math.pow(2, -10 * t)),
      smoothWheel: true,
    });
    lenisRef.current = lenis;

    let frame = 0;
    const raf = (time: number) => {
      lenis.raf(time);
      frame = requestAnimationFrame(raf);
    };
    frame = requestAnimationFrame(raf);

    function onNavClick(event: MouseEvent) {
      const link = (event.target as HTMLElement).closest("a");
      if (!link) return;
      const href = link.getAttribute("href");
      if (!href) return;

      const hash = sectionHash(href);
      if (hash) {
        // Des d'una altra pàgina, es deixa navegar Next; l'efecte de sota recull l'àncora
        if (window.location.pathname !== "/") return;
        const target = document.querySelector(hash);
        if (!target) return;
        event.preventDefault();
        lenis.scrollTo(target as HTMLElement, { offset: -NAVBAR_OFFSET, ...CLICK_SCROLL_OPTS });
        return;
      }

      // Logo → «/» ja a la portada: Next no fa res, així que es puja amb suavitat
      if (href === "/" && window.location.pathname === "/") {
        event.preventDefault();
        lenis.scrollTo(0, CLICK_SCROLL_OPTS);
      }
    }
    document.addEventListener("click", onNavClick);

    return () => {
      document.removeEventListener("click", onNavClick);
      cancelAnimationFrame(frame);
      lenisRef.current = null;
      lenis.destroy();
    };
  }, []);

  // En arribar a «/» amb una àncora (des d'una altra pàgina o carregant «/#placa»)
  useEffect(() => {
    if (pathname !== "/") return;
    const hash = window.location.hash;
    if (!hash || hash === "#") return;
    const target = document.querySelector(hash);
    const lenis = lenisRef.current;
    if (!target || !lenis) return;
    lenis.scrollTo(target as HTMLElement, { offset: -NAVBAR_OFFSET, ...CLICK_SCROLL_OPTS });
  }, [pathname]);

  return null;
}

"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * Revela el contingut quan entra a la pantalla (fos + pujada + desenfocament).
 * Còpia de Faktu (components/marketing/reveal.tsx): IntersectionObserver,
 * respecta `prefers-reduced-motion` i admet un retard per escalonar.
 */
export function Reveal({ children, className, delay = 0 }: { children?: ReactNode; className?: string; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [shown, setShown] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          setShown(true);
          io.disconnect();
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -8% 0px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      style={{ transitionDelay: `${delay}ms` }}
      className={cn(
        "transition-all duration-700 ease-out will-change-transform motion-reduce:translate-y-0! motion-reduce:opacity-100! motion-reduce:blur-0! motion-reduce:transition-none",
        shown ? "translate-y-0 opacity-100 blur-0" : "translate-y-6 opacity-0 blur-[3px]",
        className,
      )}
    >
      {children}
    </div>
  );
}

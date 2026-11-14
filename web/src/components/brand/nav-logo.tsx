"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { retryLive, useBackendMode } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Logo } from "./logo";

/**
 * El logo dels navbars. Només en mode demo (sense placa, lib/demo.ts) porta
 * «DEMO» en petit a baix a la dreta; amb la placa connectada no hi ha etiqueta.
 * Hereta el color del pare (`currentColor`), així que va bé damunt del hero fosc
 * i del vidre clar. En clicar-hi, explica que no hi ha placa i deixa tornar-la a buscar.
 */
export function NavLogo({ className }: { className?: string }) {
  return (
    <div className={cn("relative flex shrink-0 items-end gap-1 px-1.5", className)}>
      <Link href="/" className="flex items-center" aria-label="Mathey, inici">
        <Logo className="h-[22px]" />
      </Link>
      <DemoTag />
    </div>
  );
}

const TAG = "text-[8px] leading-none font-semibold tracking-[0.14em] uppercase";

function DemoTag() {
  const demo = useBackendMode() === "demo";
  const [open, setOpen] = useState(false);
  const [checking, setChecking] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (event: MouseEvent | KeyboardEvent) => {
      if (event instanceof KeyboardEvent ? event.key === "Escape" : !ref.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", close);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", close);
    };
  }, [open]);

  // Amb la placa (o mentre encara no se sap si hi és) no hi ha cap etiqueta.
  if (!demo) return null;

  async function retry() {
    setChecking(true);
    setNotFound(false);
    const ok = await retryLive();
    setChecking(false);
    if (ok) window.location.reload();
    else setNotFound(true);
  }

  return (
    <div ref={ref} className="relative mb-[2px] flex">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-label="Mode demo: no hi ha cap placa connectada"
        className={cn(
          TAG,
          "relative opacity-45 transition-opacity duration-200 before:absolute before:-inset-2 before:content-[''] hover:opacity-80 aria-expanded:opacity-80",
        )}
      >
        Demo
      </button>

      <div
        role="dialog"
        aria-label="Mode demo"
        className={cn(
          "absolute top-[calc(100%+14px)] -left-3 z-50 w-64 origin-top-left rounded-xl border border-black/[0.06] bg-popover p-3.5 text-left text-foreground shadow-(--app-popup-shadow) transition-[opacity,scale,translate,filter] duration-200 ease-motion-enter",
          open ? "translate-y-0 scale-100 opacity-100 blur-none" : "pointer-events-none -translate-y-1 scale-[0.97] opacity-0 blur-[2px]",
        )}
      >
        <p className="text-[13px] font-medium">Sense placa connectada</p>
        <p className="mt-1 text-[12px] leading-relaxed font-light text-muted-foreground">
          Problemes d&apos;exemple i una IA simulada. No es desa res.
        </p>
        <button
          type="button"
          onClick={retry}
          disabled={checking}
          className="mt-2.5 text-[12px] font-medium text-foreground underline decoration-black/20 underline-offset-[3px] transition-colors hover:decoration-black/60 disabled:opacity-50"
        >
          {checking ? "Buscant…" : notFound ? "Encara no la trobo. Torna-hi" : "Busca la placa"}
        </button>
      </div>
    </div>
  );
}

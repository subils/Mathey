"use client";

import { RotateCw } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { retryLive, useBackendMode } from "@/lib/api";
import { cn } from "@/lib/utils";

/**
 * «Mode demo»: es veu quan no hi ha cap placa connectada i la web fa servir el
 * backend simulat (lib/demo.ts). En clicar-hi s'explica i es pot tornar a buscar la placa.
 */
export function DemoBadge({ className }: { className?: string }) {
  const mode = useBackendMode();
  const [open, setOpen] = useState(false);
  const [checking, setChecking] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => !ref.current?.contains(e.target as Node) && setOpen(false);
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  if (mode !== "demo") return null;

  async function retry() {
    setChecking(true);
    setNotFound(false);
    const ok = await retryLive();
    setChecking(false);
    if (ok) window.location.reload();
    else setNotFound(true);
  }

  return (
    <div ref={ref} className={cn("relative", className)}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="inline-flex items-center gap-1.5 rounded-lg bg-amber-400/15 px-2.5 py-1 text-[12px] font-semibold text-amber-700 ring-1 ring-amber-500/20 transition-colors hover:bg-amber-400/25"
      >
        <span className="size-1.5 rounded-full bg-amber-500 animate-pulse-soft" />
        Mode demo
      </button>
      <div
        className={cn(
          "absolute top-[calc(100%+8px)] right-0 z-50 w-72 origin-top-right rounded-xl border border-black/[0.06] bg-popover p-4 text-left shadow-(--app-popup-shadow) transition-[opacity,scale] duration-150 ease-motion-enter",
          open ? "scale-100 opacity-100" : "pointer-events-none scale-[0.96] opacity-0",
        )}
      >
        <p className="text-[14px] font-semibold">No hi ha cap placa connectada</p>
        <p className="mt-1 text-[13px] leading-relaxed text-muted-foreground">
          Estàs veient Mathey en mode demo: problemes d&apos;exemple fets per nosaltres i una IA simulada. Res del que
          facis no es desa a cap placa.
        </p>
        <button
          onClick={retry}
          disabled={checking}
          className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-foreground px-3 py-1.5 text-[13px] font-medium text-background transition-opacity hover:opacity-90 disabled:opacity-60"
        >
          <RotateCw className={cn("size-3.5", checking && "animate-spin")} />
          {checking ? "Buscant…" : "Busca la placa"}
        </button>
        {notFound && <p className="mt-2 text-[12px] text-muted-foreground">Encara no la trobo.</p>}
      </div>
    </div>
  );
}

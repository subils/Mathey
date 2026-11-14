"use client";

import { ArrowUpRight, ImagePlus } from "lucide-react";
import Link from "next/link";
import { DoubleCard, Eyebrow } from "@/components/ui/surface";
import { cn } from "@/lib/utils";

/** Les dues portes del producte. Es fan servir al hub, a l'onboarding i a la landing. */
export function ModeCards({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <div className={cn("grid grid-cols-1 gap-px md:grid-cols-2", className)}>
      <ModeCard
        href="/app/repte/"
        index={0}
        eyebrow="Mode 1"
        title="Repte Cangur"
        text="Problemes del Cangur al teu nivell. Si t'equivoques, no et diem la resposta: et fem una pregunta i tens cinc ajudes."
        visual={<ChoicesVisual />}
        compact={compact}
      />
      <ModeCard
        href="/app/xat/"
        index={1}
        eyebrow="Mode 2"
        title="Porta el teu problema"
        text="Fes una foto o escriu un problema dels deures. La IA de la placa el llegeix i el resol pas a pas amb tu."
        visual={<ComposerVisual />}
        compact={compact}
      />
    </div>
  );
}

function ModeCard({
  href,
  index,
  eyebrow,
  title,
  text,
  visual,
  compact,
}: {
  href: string;
  index: number;
  eyebrow: string;
  title: string;
  text: string;
  visual: React.ReactNode;
  compact: boolean;
}) {
  return (
    <Link href={href} className="block rounded-2xl outline-none focus-visible:ring-3 focus-visible:ring-accent/40">
      <DoubleCard
        index={index}
        className={cn(
          "flex h-full flex-col gap-5 p-6 transition-colors hover:bg-foreground/[0.015] md:p-8",
          compact && "md:p-7",
        )}
      >
        <div className="relative h-36 overflow-hidden rounded-xl border border-black/[0.05] bg-white/60">
          {visual}
        </div>
        <div className="flex items-end justify-between gap-4">
          <div className="flex flex-col gap-1.5">
            <Eyebrow>{eyebrow}</Eyebrow>
            <h3 className="text-xl font-medium tracking-[-0.01em] md:text-2xl">{title}</h3>
            <p className="max-w-sm text-sm leading-relaxed font-light text-muted-foreground md:text-[15px]">{text}</p>
          </div>
          <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-foreground text-background transition-transform duration-150 ease-motion-enter group-hover:translate-x-0.5 group-hover:-translate-y-0.5">
            <ArrowUpRight className="size-4" />
          </span>
        </div>
      </DoubleCard>
    </Link>
  );
}

/** Miniatura del mode 1: les cinc opcions, amb la bona encesa. */
function ChoicesVisual() {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 px-6">
      <div className="h-2 w-2/3 rounded-full bg-black/[0.07]" />
      <div className="h-2 w-1/2 rounded-full bg-black/[0.05]" />
      <div className="mt-1 flex gap-2">
        {["A", "B", "C", "D", "E"].map((l) => (
          <span
            key={l}
            className={cn(
              "flex size-9 items-center justify-center rounded-lg border font-mono text-[13px] font-semibold transition-all duration-300",
              l === "C"
                ? "border-success/40 bg-success/10 text-success group-hover:scale-110"
                : l === "B"
                  ? "border-black/10 bg-white text-muted-foreground line-through decoration-destructive/70"
                  : "border-black/10 bg-white text-foreground/70",
            )}
          >
            {l}
          </span>
        ))}
      </div>
    </div>
  );
}

/** Miniatura del mode 2: el compositor amb una foto enganxada. */
function ComposerVisual() {
  return (
    <div className="absolute inset-0 flex items-center justify-center px-6">
      <div className="glass flex w-full max-w-xs flex-col gap-2 rounded-2xl p-2.5">
        <div className="flex items-center gap-2">
          <span className="relative size-11 overflow-hidden rounded-lg bg-[linear-gradient(135deg,#e9eef7,#cfd9ea)] transition-transform duration-300 group-hover:scale-105">
            <span className="absolute inset-x-2 top-2.5 h-1 rounded-full bg-black/15" />
            <span className="absolute inset-x-2 top-5 h-1 w-5 rounded-full bg-black/10" />
          </span>
          <span className="text-[13px] text-muted-foreground">deures-p23.jpg</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[13px] text-muted-foreground/80">On t&apos;encalles?</span>
          <span className="flex size-7 items-center justify-center rounded-full bg-foreground text-background">
            <ImagePlus className="size-3.5" />
          </span>
        </div>
      </div>
    </div>
  );
}

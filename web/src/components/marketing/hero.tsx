import { ArrowUpRight, Check, ChevronDown, Lightbulb, Sparkles, WifiOff } from "lucide-react";
import Link from "next/link";
import { Mark } from "@/components/brand/logo";
import { Pill } from "@/components/ui/surface";
import { Reveal } from "./reveal";

/**
 * El hero de Faktu (sections/hero-section.tsx) en clar: el marc de 8–12 px al
 * voltant d'un panell arrodonit, blanc i net, amb el cangur (quiet) a dalt i
 * quatre xips de vidre als costats que expliquen el producte.
 */
export function Hero() {
  return (
    <section id="hero" className="relative h-[100svh] min-h-[640px] w-full">
      <div className="relative h-full w-full p-2 md:p-3">
        <div className="relative isolate h-full w-full overflow-hidden rounded-2xl bg-white ring-1 ring-black/[0.04]">
          <FloatingChips />

          <div className="absolute inset-0 flex flex-col items-center justify-center px-4 text-center">
            <Reveal immediate>
              <div className="mb-7 flex flex-col items-center gap-5">
                <Mark className="h-16 text-foreground md:h-20" title="Mathey" />
                <Pill>Datathon FME 2026 · Repte Qualcomm</Pill>
              </div>
            </Reveal>
            <Reveal immediate delay={80}>
              <h1
                className="mb-5 max-w-5xl text-foreground"
                style={{ fontSize: "clamp(40px, 7vw, 96px)", fontWeight: 500, letterSpacing: "-0.035em", lineHeight: 1 }}
              >
                Matemàtiques
                <br />
                <span className="text-gradient">socràtiques</span>
              </h1>
            </Reveal>
            <Reveal immediate delay={140}>
              <p className="mx-auto mb-9 max-w-md text-[15px] leading-relaxed font-light text-muted-foreground md:text-[17px]">
                Com Sòcrates, no et donem la resposta: et fem la pregunta justa perquè la trobis tu.
              </p>
            </Reveal>
            <Reveal immediate delay={200}>
              <div className="glass inline-flex items-center gap-1.5 rounded-2xl p-1.5">
                <Link
                  href="/app/"
                  className="inline-flex items-center gap-2 rounded-xl bg-[#1c1c1d] px-5 py-2.5 text-sm font-medium text-white transition-[opacity,transform] duration-150 hover:opacity-90 active:scale-[0.98]"
                >
                  Comença <ArrowUpRight className="size-4" />
                </Link>
                <Link
                  href="/#com-funciona"
                  className="inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-medium text-[#1c1c1d] transition-colors hover:bg-black/5"
                >
                  Com funciona
                </Link>
              </div>
            </Reveal>
          </div>

          <div className="absolute inset-x-0 bottom-6 flex justify-center">
            <ChevronDown className="size-5 animate-bounce text-foreground/40" />
          </div>
        </div>
      </div>
    </section>
  );
}

function FloatingChips() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 hidden lg:block">
      <Chip className="top-[24%] left-[9%]" delay="0s">
        <span className="flex size-6 items-center justify-center rounded-full bg-success text-white">
          <Check className="size-3.5" strokeWidth={3} />
        </span>
        <span>
          <span className="block font-medium text-foreground">Era la C!</span>
          <span className="text-muted-foreground">Al primer intent · Elo +18</span>
        </span>
      </Chip>
      <Chip className="top-[58%] left-[6%]" delay="1.2s">
        <span className="flex size-6 items-center justify-center rounded-full bg-accent/10 text-accent">
          <Lightbulb className="size-3.5" />
        </span>
        <span>
          <span className="block font-medium text-foreground">Pista 2 de 5</span>
          <span className="text-muted-foreground">La dada clau de l&apos;enunciat</span>
        </span>
      </Chip>
      <Chip className="top-[30%] right-[8%]" delay="0.6s">
        <span className="flex size-6 items-center justify-center rounded-full bg-accent/10 text-accent">
          <Sparkles className="size-3.5" />
        </span>
        <span>
          <span className="block font-medium text-foreground">Com ho has pensat?</span>
          <span className="text-muted-foreground">Pregunta de la IA de la placa</span>
        </span>
      </Chip>
      <Chip className="top-[62%] right-[10%]" delay="1.8s">
        <span className="flex size-6 items-center justify-center rounded-full bg-black/[0.06] text-foreground">
          <WifiOff className="size-3.5" />
        </span>
        <span>
          <span className="block font-medium text-foreground">Sense internet</span>
          <span className="text-muted-foreground">Tot passa a la placa</span>
        </span>
      </Chip>
    </div>
  );
}

function Chip({ className, delay, children }: { className: string; delay: string; children: React.ReactNode }) {
  return (
    <div className={`absolute ${className}`}>
      <div
        className="glass flex items-center gap-2.5 rounded-xl px-3 py-2 text-left text-[12px] leading-tight animate-float"
        style={{ animationDelay: delay }}
      >
        {children}
      </div>
    </div>
  );
}

import { ArrowUpRight, Check, ChevronDown, Lightbulb, Sparkles } from "lucide-react";
import Link from "next/link";
import { Mark } from "@/components/brand/logo";
import { Spotlight } from "@/components/ui/spotlight-new";
import { Pill } from "@/components/ui/surface";
import { Reveal } from "./reveal";

// El focus de llum d'Aceternity (gratuït), recolorit de blanc-sobre-negre a blau-sobre-blanc.
const SPOT = {
  first:
    "radial-gradient(68.54% 68.72% at 55.02% 31.46%, hsla(210, 100%, 62%, .20) 0, hsla(210, 100%, 60%, .07) 50%, hsla(210, 100%, 55%, 0) 80%)",
  second:
    "radial-gradient(50% 50% at 50% 50%, hsla(210, 100%, 62%, .14) 0, hsla(210, 100%, 60%, .05) 80%, transparent 100%)",
  third:
    "radial-gradient(50% 50% at 50% 50%, hsla(210, 100%, 62%, .10) 0, hsla(210, 100%, 55%, .04) 80%, transparent 100%)",
};

/**
 * El hero de Faktu (sections/hero-section.tsx) en clar: el mateix marc de
 * 8–12 px al voltant d'un panell arrodonit, però amb llum blava, la reixa
 * emmascarada i el cangur en lloc del vídeo fosc.
 */
export function Hero() {
  return (
    <section id="hero" className="relative h-[100svh] min-h-[640px] w-full">
      <div className="relative h-full w-full p-2 md:p-3">
        <div className="relative isolate h-full w-full overflow-hidden rounded-2xl bg-white ring-1 ring-black/[0.04]">
          {/* Fons: degradat, reixa i focus de llum */}
          <div
            aria-hidden
            className="absolute inset-0 -z-10"
            style={{
              backgroundImage:
                "radial-gradient(120% 70% at 50% 0%, #eef5ff 0%, #ffffff 55%), linear-gradient(to bottom, #ffffff, #f6f7f6)",
            }}
          />
          <div aria-hidden className="hero-grid absolute inset-0 -z-10 opacity-70" />
          <div aria-hidden className="absolute inset-0 -z-10 overflow-hidden motion-reduce:hidden">
            <Spotlight gradientFirst={SPOT.first} gradientSecond={SPOT.second} gradientThird={SPOT.third} duration={9} />
          </div>
          <div
            aria-hidden
            className="absolute inset-x-0 bottom-0 -z-10 h-40 bg-gradient-to-t from-[#f6f7f6] to-transparent"
          />

          {/* Xips flotants: el producte en tres frases */}
          <FloatingChips />

          <div className="absolute inset-0 flex flex-col items-center justify-center px-4 text-center">
            <Reveal>
              <div className="mb-7 flex flex-col items-center gap-5">
                <div className="relative">
                  <Mark className="h-16 text-foreground animate-float md:h-20" title="Mathey" />
                  <span
                    aria-hidden
                    className="absolute -bottom-3 left-1/2 h-2 w-14 -translate-x-1/2 rounded-[50%] bg-black/15 blur-[3px]"
                  />
                </div>
                <Pill>Datathon FME 2026 · Repte Qualcomm</Pill>
              </div>
            </Reveal>
            <Reveal delay={80}>
              <h1
                className="mb-5 max-w-5xl text-foreground"
                style={{ fontSize: "clamp(34px, 6vw, 80px)", fontWeight: 500, letterSpacing: "-0.035em", lineHeight: 1.04 }}
              >
                No et donem la resposta.
                <br />
                T&apos;ajudem a <span className="text-gradient">trobar-la</span>.
              </h1>
            </Reveal>
            <Reveal delay={140}>
              <p className="mx-auto mb-9 max-w-xl text-[15px] leading-relaxed font-light text-muted-foreground md:text-[17px]">
                Un mentor de matemàtiques que viu dins d&apos;una placa a l&apos;aula. Problemes del Cangur al teu nivell,
                pistes quan t&apos;encalles i cap dada que surti de l&apos;escola. Sense internet.
              </p>
            </Reveal>
            <Reveal delay={200}>
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
        <span className="flex size-6 items-center justify-center rounded-full bg-amber-400/20 text-amber-600">
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
        <span className="grid grid-cols-5 gap-[3px] rounded-md bg-[#151515] p-1.5">
          {[0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1].map((on, i) => (
            <span
              key={i}
              className="size-[5px] rounded-full"
              style={{ background: on ? "rgb(255 64 32)" : "rgb(255 255 255 / 0.08)", boxShadow: on ? "0 0 4px rgb(255 80 40 / .7)" : "none" }}
            />
          ))}
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

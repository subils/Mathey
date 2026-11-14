import { ArrowUpRight, ChevronDown } from "lucide-react";
import Link from "next/link";
import { Pill } from "@/components/ui/surface";
import { ResendCube } from "./resend-cube";
import { Reveal } from "./reveal";

/**
 * Hero: el marc de Faktu (8–12 px al voltant d'un panell blanc arrodonit) amb la
 * composició del hero de resend.com a dins, amb autorització de Resend:
 * - text a l'esquerra (píndola, titular, entradeta i botons, alineats a l'esquerra);
 * - el cub 3D de Resend a la dreta, en un espai de 700 × 550 px;
 * - al mòbil, el cub a dalt i el text a sota, centrat.
 */
export function Hero() {
  return (
    <section id="hero" className="relative h-[100svh] min-h-[640px] w-full">
      <div className="relative h-full w-full p-2 md:p-3">
        <div className="relative isolate h-full w-full overflow-hidden rounded-2xl bg-white ring-1 ring-black/[0.04]">
          {/* Composició de resend.com: mx-auto max-w-7xl, dues columnes */}
          <div className="mx-auto flex h-full max-w-5xl flex-col items-center justify-start px-6 pt-24 pb-8 md:max-w-7xl md:flex-row md:justify-between md:pt-16 md:pb-12">
            <div className="order-2 max-w-3xl md:order-1 md:max-w-[36rem] md:shrink-0 lg:pl-16 xl:max-w-[40rem]">
              <Reveal immediate>
                <div className="mb-8 flex justify-center md:justify-start">
                  <Pill>Datathon FME 2026 · Repte Qualcomm</Pill>
                </div>
              </Reveal>
              <Reveal immediate delay={80}>
                <h1
                  className="pb-3 text-center text-foreground md:text-left"
                  style={{ fontSize: "clamp(40px, 5.2vw, 76px)", fontWeight: 500, letterSpacing: "-0.035em", lineHeight: 1.02 }}
                >
                  No et donem
                  <br />
                  la resposta.
                  <br />
                  T&apos;ajudem a <span className="text-gradient whitespace-nowrap">trobar-la</span>.
                </h1>
              </Reveal>
              <Reveal immediate delay={140}>
                <p className="mt-2 mb-8 max-w-[30rem] text-center text-base leading-7 font-light text-muted-foreground md:text-left md:text-[1.125rem] md:leading-[1.5]">
                  Un mentor de matemàtiques que viu dins d&apos;una placa a l&apos;aula. Problemes del Cangur al teu
                  nivell, pistes quan t&apos;encalles i cap dada que surti de l&apos;escola. Sense internet.
                </p>
              </Reveal>
              <Reveal immediate delay={200}>
                <div className="flex flex-col justify-center gap-4 md:flex-row md:justify-start">
                  <Link
                    href="/app/"
                    className="inline-flex h-12 items-center justify-center gap-1 rounded-2xl bg-[#1c1c1d] px-5 text-base font-semibold text-white transition-[opacity,transform] duration-200 hover:opacity-90 active:scale-[0.98]"
                  >
                    Comença <ArrowUpRight className="size-4" />
                  </Link>
                  <Link
                    href="/#com-funciona"
                    className="inline-flex h-12 items-center justify-center gap-1 rounded-2xl px-5 text-base font-semibold text-muted-foreground transition-colors hover:text-foreground"
                  >
                    Com funciona
                  </Link>
                </div>
              </Reveal>
            </div>

            {/* El cub: a dalt al mòbil, a la dreta a l'escriptori (com a resend.com) */}
            <Reveal immediate delay={120} className="order-1 md:order-2 md:ml-10 md:min-w-0 md:flex-1 md:max-w-[700px]">
              <ResendCube className="h-[240px] w-[240px] md:h-[550px] md:w-full" />
            </Reveal>
          </div>

          <div className="absolute inset-x-0 bottom-6 hidden justify-center md:flex">
            <ChevronDown className="size-5 animate-bounce text-foreground/40" />
          </div>
        </div>
      </div>
    </section>
  );
}
